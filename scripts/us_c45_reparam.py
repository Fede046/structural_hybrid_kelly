"""Script: «riduce e riparametrizza», il ricalibratore che dopo un errore strutturale ristima il modello.

Variante chiesta il 2026-11-21 dopo aver visto i risultati di us_c42 (esplorativa), con le regole fissate
prima di eseguirla:
- per ogni stagione S dal 2003-04 al 2023-24 si parte come in us_c42: modello θ0 stimato sulle stagioni
  dal 2000-01 alla precedente, riferimento delle stagioni dal 2002-03 alla precedente, soglie e diagnosi
  con gli stessi seed;
- il giorno d in cui inizia un errore strutturale (diagnosi strutturale, dopo almeno una giornata senza
  allarme dall'ultima ristima), prima delle partite, il modello viene ristimato: K, h, ν minimizzano la
  log-loss sulle stagioni passate più le partite della stagione S giocate prima di d. Quel giorno si
  punta con il modello nuovo e λ = 0,40;
- dal giorno dopo il supervisore controlla il modello nuovo: residui della stagione e riferimento
  ricalcolati con i nuovi parametri, soglie e diagnosi ricalibrate con gli stessi seed; λ segue la
  diagnosi del giorno (1, 0,75, 0,40) come nel freno;
- ambiente come us_c42: puntata minima £0,01 su £220, regola R1; Elo senza regola per le neopromosse
  (SHK_ELO_ENTRY=plain, decisione del 2026-11-21);
- freno casuale: stesse ristime e stesse previsioni, riduzioni della puntata con gli stessi episodi
  spostati a caso (N_CALENDARS calendari), e una frazione costante con la stessa puntata media.

Scrive results/us_c45_reparam_seasons.csv (una riga per stagione), results/us_c45_reparam_refits.csv
(una riga per ristima, con i parametri), results/us_c45_reparam_random.csv (capitale dei calendari
casuali) e results/raw/us_c45/<stagione>.npz (previsioni, λ e diagnosi, per la popolazione di us_c43).
"""

import os

os.environ["SHK_ELO_ENTRY"] = "plain"  # nuova tesi: nessuna regola per le neopromosse, prima di importare shk

import csv
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from shk.kelly.environment import run_paired_backtest
from shk.kelly.outcome_rules import with_outcome_rule
from shk.model.agent_c import SCHEME_STOP_CLEAR, Module2Supervisor, ReferenceData
from shk.model.elo_fit import EloFitParams, calibrate_single_fit, parse_season_start_year
from shk.model.frozen_agents import scheme_window
from shk.model.frozen_params import frozen_params_path, load_frozen_params
from shk.model.full_kelly_test import (
    FREE_LAMBDA, KAPPA, LEVELS, SEED_S41, STRUCTURAL_LAMBDA, ScheduledKellyAgent, episodes, fit_full_model,
    full_frame, full_residuals, lambda_schedule, past_reference, past_training, pooled_alarm_thresholds,
    pooled_block_length, pooled_reference, previous_season, random_calendar, test_input,
)
from shk.model.paired_backtest import CONFIGURATIONS
from shk.model.residuals import load_match_frame
from shk.model.two_fold_diagnosis import TwoFoldSchemeAgent, calibrate_reference_diagnosis

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS = REPO_ROOT / "results"
MIN_STAKE: Final[float] = dict(CONFIGURATIONS)["gbp_0.01"]
SEED_S45: Final[int] = 20261124
N_CALENDARS: Final[int] = 2000
RAW = RESULTS / "raw" / "us_c45"
SEASONS: Final[tuple[str, ...]] = tuple(f"{y}-{str(y + 1)[-2:]}" for y in range(2003, 2024))


def refit(df: pd.DataFrame, season: str, before: np.datetime64) -> EloFitParams:
    """K, h, ν sulle stagioni passate più le partite di `season` giocate prima di `before`."""
    keep = (df["season"] != season) | (df["Date"].to_numpy("datetime64[ns]") < before)
    sub = df[keep].reset_index(drop=True)
    res = calibrate_single_fit(sub, season, list(past_training(season)) + [season])
    return EloFitParams(k=res.k, h=res.h, nu=res.nu, c=res.c)


def model_setup(df: pd.DataFrame, season: str, fit: EloFitParams, cov: list[str], w: int, fallback: str):
    """Ingressi della stagione e diagnosi giorno per giorno del supervisore con i parametri `fit`."""
    frame = full_frame(full_residuals(df, fit, True, season), season)
    ref = pooled_reference(frame, cov, past_reference(season))
    length = pooled_block_length(ref)
    thr_seq, diag_seq = np.random.SeedSequence(SEED_S41).spawn(4)[:2]
    calendar = frame[frame["season"] == previous_season(season)]["Date"].to_numpy("datetime64[ns]")
    mt, dt = pooled_alarm_thresholds(ref, calendar, w, length, np.random.default_rng(thr_seq))
    diag = calibrate_reference_diagnosis(ref.x, ref.delta, w, length, np.random.default_rng(diag_seq))
    inp = test_input(frame, cov, season)
    sup = Module2Supervisor(inp.season, inp.dates, inp.x, cov, w, devig_method="shin",
                            reference=ReferenceData(ref.x, ref.delta))
    brake = with_outcome_rule(TwoFoldSchemeAgent, "R1")("freno", sup, KAPPA, mt, dt, diag, SCHEME_STOP_CLEAR,
                                                       base_lambda=FREE_LAMBDA, structural_lambda=STRUCTURAL_LAMBDA)
    run_paired_backtest([brake], inp.dates, inp.probs, inp.odds, inp.outcomes, MIN_STAKE, fallback_policy=fallback)
    days = np.unique(inp.dates)
    d = brake.diagnosis_by_date
    stats = [sup.reference_diagnostics(np.datetime64(x, "ns")) for x in days]
    ratios = np.array([[s[0] / mt, s[1] / dt] if s else [np.nan, np.nan] for s in stats])
    return inp, np.array([d.get(np.datetime64(x, "ns"), "none") for x in days], dtype=object), ratios


def run_season(season: str) -> tuple[dict, list[dict]]:
    params = load_frozen_params(frozen_params_path())
    cov = list(params.fixed["covariates"])
    w = scheme_window(params)
    fallback = params.fixed["fallback_policy"]
    df, _ = load_match_frame(roles=("history", "training", "validation", "test"))
    fit = fit_full_model(df, season)
    inp0, diag0, ratios0 = model_setup(df, season, fit, cov, w, fallback)
    ratios = ratios0.copy()
    days = np.unique(inp0.dates)
    n_days = len(days)
    probs = inp0.probs.copy()
    lam = np.array([LEVELS[g] for g in diag0], dtype=np.float64)
    current_diag, start, refits = diag0, 0, []
    while True:
        # Inizio di un nuovo errore strutturale: dopo almeno una giornata senza allarme dall'ultima ristima
        seen_clear = start == 0
        onset = None
        for j in range(start + (0 if start == 0 else 1), n_days):
            if current_diag[j] == "none":
                seen_clear = True
            elif current_diag[j] == "structural" and seen_clear:
                onset = j
                break
        if onset is None:
            break
        fit = refit(df, season, np.datetime64(days[onset], "ns"))
        inp, new_diag, new_ratios = model_setup(df, season, fit, cov, w, fallback)
        if not (np.array_equal(inp.dates, inp0.dates) and np.array_equal(inp.outcomes, inp0.outcomes)
                and np.allclose(inp.odds, inp0.odds)):
            raise RuntimeError(f"{season}: the season rows differ between models")
        rows = inp.dates >= days[onset]
        probs[rows] = inp.probs[rows]
        lam[onset] = STRUCTURAL_LAMBDA
        lam[onset + 1:] = [LEVELS[g] for g in new_diag[onset + 1:]]
        ratios[onset + 1:] = new_ratios[onset + 1:]
        refits.append({"season": season, "refit": len(refits) + 1, "day": onset + 1,
                       "date": str(pd.Timestamp(days[onset]).date()), "k": fit.k, "h": fit.h, "nu": fit.nu})
        current_diag, start = new_diag, onset
    sched = {np.datetime64(d, "ns"): v for d, v in zip(days, lam)}
    run = run_paired_backtest([ScheduledKellyAgent("riparametrizza", sched)], inp0.dates, probs, inp0.odds,
                              inp0.outcomes, MIN_STAKE, fallback_policy=fallback)[0]
    k = np.arange(probs.shape[0])
    y = inp0.outcomes[0]
    row = {"season": season, "n_refits": len(refits), "reduced_days": int((lam < 1).sum()),
           "final_capital": float(run.wealth[0, -1]), "ruined": bool(run.ruined[0]),
           "log_loss_used": float(-np.log(probs[k, y]).mean()), "log_loss_original": float(-np.log(inp0.probs[k, y]).mean())}
    # Freno casuale della versione definitiva: stesse ristime, stesse previsioni (probs), riduzioni della
    # puntata con gli stessi episodi (numero, tipo, durata) spostati a caso fra le giornate possibili
    labels = np.array(["none" if v == FREE_LAMBDA else "structural" if v == STRUCTURAL_LAMBDA else "compositional"
                       for v in lam], dtype=object)
    counts = np.searchsorted(inp0.dates, days, side="left")
    first = int(np.flatnonzero(counts >= w)[0])
    random_rows: list[dict] = []
    eps = episodes(list(labels))
    if eps:
        seeds = np.random.SeedSequence([SEED_S45, parse_season_start_year(season)]).spawn(N_CALENDARS)
        agents = [ScheduledKellyAgent(f"casuale_{i}", lambda_schedule(days, random_calendar(eps, n_days, first,
                                                                                         np.random.default_rng(s))))
                  for i, s in enumerate(seeds)]
        mean_lam = float(lam.mean())
        agents.append(ScheduledKellyAgent("costante", {d: mean_lam for d in days}))
        runs = run_paired_backtest(agents, inp0.dates, probs, inp0.odds, inp0.outcomes, MIN_STAKE,
                                   fallback_policy=fallback)
        finals = np.array([float(r.wealth[0, -1]) for r in runs[:-1]])
        random_rows = [{"season": season, "calendar": i, "final_capital": v} for i, v in enumerate(finals)]
        row.update({"random_median": float(np.median(finals)),
                    "random_p_value": float(np.mean(finals >= row["final_capital"] - 1e-15)),
                    "constant_lambda": mean_lam, "constant": float(runs[-1].wealth[0, -1])})
    RAW.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(RAW / f"{season}.npz", dates=inp0.dates, probs0=inp0.probs, probs=probs, odds=inp0.odds,
                        outcomes=inp0.outcomes, lam=lam, labels=labels.astype(str), diag0=diag0.astype(str),
                        first=first, ratios=ratios, ratios0=ratios0,
                        wealth=run.wealth[0], refit_days=np.array([r["day"] - 1 for r in refits], dtype=np.int64))
    return row, refits, random_rows


def _write(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, restval="")
        writer.writeheader()
        writer.writerows(rows)


def run_experiment(seasons=SEASONS) -> None:
    with ProcessPoolExecutor(max_workers=5) as pool:
        out = list(pool.map(run_season, seasons))
    rows = [r for r, _, _ in out]
    refits = [x for _, rr, _ in out for x in rr]
    random_rows = [x for _, _, rr in out for x in rr]
    _write(RESULTS / "us_c45_reparam_seasons.csv", rows)
    _write(RESULTS / "us_c45_reparam_refits.csv", refits)
    _write(RESULTS / "us_c45_reparam_random.csv", random_rows)
    s = pd.DataFrame(rows).set_index("season")
    if random_rows:
        rr = pd.DataFrame(random_rows)
        alarm = s[s["reduced_days"] > 0]
        joint = np.log(rr.pivot(index="calendar", columns="season", values="final_capital")[alarm.index]).sum(axis=1)
        obs = float(np.log(alarm["final_capital"]).sum())
        print(f"joint: definitive {obs:.2f} random median {joint.median():.2f} constant "
              f"{np.log(alarm['constant']).sum():.2f} p {(joint >= obs - 1e-12).mean():.4f}")
        for drop in alarm.index:
            idx = [x for x in alarm.index if x != drop]
            j = joint - np.log(rr.pivot(index="calendar", columns="season", values="final_capital")[drop])
            o = obs - np.log(alarm.loc[drop, "final_capital"])
            print(f"  without {drop}: p {(j >= o - 1e-12).mean():.4f}")
    base = pd.read_csv(RESULTS / "us_c42_rolling_seasons.csv").set_index("season").loc[s.index]
    s["full_kelly"], s["brake"] = base["full_kelly"], base["brake"]
    pd.set_option("display.width", 250)
    print(s.round(5).to_string())
    for name in ("full_kelly", "brake", "final_capital"):
        print(name, "typical", float(np.exp(np.log(s[name]).mean())))
    for ref in ("full_kelly", "brake"):
        d = np.log(s["final_capital"]) - np.log(s[ref])
        nz = d[d.abs() > 1e-12]
        print(f"vs {ref}: better {(d > 1e-12).sum()} worse {(d < -1e-12).sum()} "
              f"wilcoxon p {wilcoxon(nz).pvalue if len(nz) else float('nan'):.3f}")
    print(pd.DataFrame(refits).to_string())


if __name__ == "__main__":
    run_experiment(tuple(sys.argv[1:]) or SEASONS)
