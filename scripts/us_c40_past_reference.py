"""Script: stagione di riferimento (e fit del lavoratore) scelti guardando il passato (shk.model.past_reference).

Esplorativo, sul branch riferimento-dal-passato. L'idea nasce dalla stagione 2023-24 (§5.8: «il
riferimento sbagliava già»), quindi il 2023-24 non può confermarla: è riportato a parte.

Per le 19 stagioni di validazione e per il 2023-24, con la puntata minima di £0,01:
1. supervisore: la versione definitiva F con quattro regole per il riferimento (calibrazione,
   precedente, mediana, migliore), sempre con i residui del fit congelato della stagione;
2. lavoratore: il fit scelto per log-loss sulla stagione precedente (fra i fit anteriori a quella),
   con F riferito alla calibrazione del fit scelto.

Scrive:
- results/us_c40_past_reference_setups.csv: per fit × stagione candidata, media, dispersione e soglie;
- results/us_c40_past_reference_seasons.csv: per stagione × regola, riferimento scelto e capitale;
- results/us_c40_past_reference_summary.csv: per regola, sulle 19 stagioni di validazione.
"""

import csv
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from shk.data.split import read_split_config
from shk.model.frozen_params import frozen_params_path, load_frozen_params
from shk.model.main_version import main_setups
from shk.model.model_age import dispersion
from shk.model.module2_data import build_module2_frame
from shk.model.paired_backtest import CONFIGURATIONS
from shk.model.past_reference import (
    best_choice,
    candidate_setup,
    available_seasons,
    fit_frame,
    median_choice,
    run_with_reference,
    worker_fit_choice,
    year,
)
from shk.model.residuals import load_match_frame, model_residuals_data
from shk.model.season_input import season_input_from_frame

WORKERS = 5
RESULTS = Path(__file__).resolve().parents[1] / "results"
MIN_STAKE = dict(CONFIGURATIONS)["gbp_0.01"]


def _write(name: str, rows: list[dict]) -> None:
    with open(RESULTS / f"us_c40_past_reference_{name}.csv", mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _setup_job(args):
    frame, season, params_path, fit = args
    return (fit, season), candidate_setup(frame, season, load_frozen_params(params_path), fit)


def _run_job(args):
    key, params_path, setup, inp = args
    return key, run_with_reference(params_path, setup, inp, MIN_STAKE)


def run_experiment() -> None:
    params_path = str(frozen_params_path())
    params = load_frozen_params(params_path)
    covariates = list(params.fixed["covariates"])
    cfg = read_split_config()
    df, schedule = load_match_frame(roles=("history", "training", "validation", "test"))
    fits = sorted(schedule, key=year)
    standard = build_module2_frame(model_residuals_data(df, schedule))
    calibration = main_setups(standard[standard["role"] == "training"], params)
    frames = {f: fit_frame(df, schedule, f) for f in fits}

    targets = {s: f for f, e in schedule.items() for s in e["validation"]}
    targets.update({s: fits[-1] for s in cfg.test})
    targets = dict(sorted(targets.items(), key=lambda kv: year(kv[0])))

    def inp(fit: str, season: str):
        return season_input_from_frame(frames[fit], season, covariates)

    def previous(fit: str, season: str) -> str | None:
        past = available_seasons(frames[fit], season)
        return past[-1] if past else None

    # Setup di tutte le stagioni candidate (anteriori all'ultima stagione bersaglio di ciascun fit)
    needed = set()
    for s, f in targets.items():
        for c in available_seasons(frames[f], s):
            if c != f:
                needed.add((f, c))
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        jobs = [(frames[f][frames[f]["season"] == c], c, params_path, f) for f, c in sorted(needed)]
        setups = dict(pool.map(_setup_job, jobs))
    for f in fits:
        setups[(f, f)] = calibration[f]

    disp = {(f, c): dispersion(frames[f].loc[frames[f]["season"] == c, "delta"].to_numpy())
            for f in fits for c in frames[f]["season"].unique()}
    setup_rows = [{"fit": f, "season": c, "n": int(setups[(f, c)].per_date.delta.shape[0]),
                   "mean": float(setups[(f, c)].per_date.delta.mean()), "dispersion": disp[(f, c)],
                   "mean_threshold": setups[(f, c)].per_season.mean_threshold,
                   "dispersion_threshold": setups[(f, c)].per_season.dispersion_threshold}
                  for f, c in sorted(setups, key=lambda k: (year(k[0]), year(k[1])))]

    # Regola "migliore": ogni candidata provata sulla stagione precedente
    probe = {}
    for s, f in targets.items():
        prev = previous(f, s)
        if prev is None:
            continue
        for c in available_seasons(frames[f], prev):
            probe[(f, prev, c)] = (f, prev, c)
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        probe_out = dict(pool.map(_run_job, [(k, params_path, setups[(k[0], k[2])], inp(k[0], k[1]))
                                             for k in probe]))

    # Lavoratore: log-loss di ogni fit su ogni stagione che prevede
    def mean_log_loss(part: pd.DataFrame) -> float:
        p = part[["p_home", "p_draw", "p_away"]].to_numpy()
        k = part["FTR"].map({"H": 0, "D": 1, "A": 2}).to_numpy()
        return float(-np.log(p[np.arange(len(k)), k]).mean())

    log_loss = {(f, c): mean_log_loss(frames[f][frames[f]["season"] == c])
                for f in fits for c in frames[f]["season"].unique()}

    choices = {}
    for s, f in targets.items():
        past = available_seasons(frames[f], s)
        prev = past[-1] if past else None
        scores = {c: probe_out[(f, prev, c)].log_wealth_f for c in available_seasons(frames[f], prev)} if prev else {}
        choices[(s, "calibrazione")] = (f, f)
        choices[(s, "precedente")] = (f, prev or f)
        choices[(s, "mediana")] = (f, median_choice(past, {c: disp[(f, c)] for c in past}) if past else f)
        choices[(s, "migliore")] = (f, best_choice(scores, f))
        prev_any = max((c for c in frames[fits[0]]["season"].unique() if year(c) < year(s)), key=year)
        g = worker_fit_choice(log_loss, fits, prev_any, f)
        choices[(s, "lavoratore")] = (g, g)

    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        out = dict(pool.map(_run_job, [(k, params_path, setups[v], inp(v[0], k[0])) for k, v in choices.items()]))

    season_rows = []
    for (s, rule), (g, ref) in choices.items():
        r = out[(s, rule)]
        season_rows.append({"season": s, "role": "test" if s in cfg.test else "validation", "fit_frozen": targets[s],
                            "rule": rule, "fit_used": g, "reference": ref, "reference_dispersion": disp[(g, ref)],
                            "log_wealth_F": r.log_wealth_f, "log_wealth_B": r.log_wealth_b,
                            "share_days_reduced": r.share_reduced, "days_reduced": r.alarm_days})
    sr = pd.DataFrame(season_rows)
    base = sr[sr["rule"] == "calibrazione"].set_index("season")["log_wealth_B"]
    summary = []
    for rule, g in sr[sr["role"] == "validation"].groupby("rule", sort=False):
        b = base.loc[g["season"]].to_numpy()
        diff = g["log_wealth_F"].to_numpy() - b
        nz = diff[np.abs(diff) > 1e-12]
        summary.append({"rule": rule, "n_seasons": len(g),
                        "typical_capital_F": float(np.exp(g["log_wealth_F"].mean())),
                        "typical_capital_B_frozen": float(np.exp(b.mean())),
                        "typical_capital_B_rule": float(np.exp(g["log_wealth_B"].mean())),
                        "seasons_better": int((diff > 1e-12).sum()), "seasons_worse": int((diff < -1e-12).sum()),
                        "seasons_with_reduction": int((g["days_reduced"] > 0).sum()),
                        "share_days_reduced": float(g["share_days_reduced"].mean()),
                        "wilcoxon_p": float(wilcoxon(nz).pvalue) if nz.size >= 2 else float("nan")})
    _write("setups", setup_rows)
    _write("seasons", season_rows)
    _write("summary", summary)

    pd.set_option("display.width", 220)
    show = sr.assign(cap_F=np.exp(sr["log_wealth_F"]), cap_B=np.exp(sr["log_wealth_B"]))
    print(show[["season", "rule", "fit_used", "reference", "reference_dispersion", "cap_F", "cap_B",
                "days_reduced"]].round(3).to_string(index=False))
    print(pd.DataFrame(summary).round(4).to_string(index=False))


if __name__ == "__main__":
    run_experiment()
