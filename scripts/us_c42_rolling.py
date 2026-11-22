"""Script: il test della nuova tesi ripetuto su ogni stagione, calibrando sulle stagioni passate.

Per ogni stagione S dal 2003-04 al 2023-24, con le regole del capitolo 4 di thesis/TESI_kellybench.md:
- il modello Elo-Davidson è stimato sulle stagioni dal 2000-01 alla stagione prima di S;
- il riferimento del supervisore sono tutte le partite dal 2002-03 alla stagione prima di S, con le
  soglie per stagione calibrate sul calendario della stagione prima di S e la diagnosi a due termini
  (stessi seed di us_c41: per il 2023-24 la calibrazione coincide con us_c41_calibration);
- S si gioca una volta: Kelly pieno senza freno e con il freno (λ = 1 / 0,75 / 0,40), puntata minima
  £0,01 su £220;
- se il freno frena, N_CALENDARS freni casuali con gli stessi allarmi (numero, tipo, durata) in
  momenti casuali, e una frazione costante con la stessa puntata media.

Il confronto del momento giusto si fa anche su tutte le stagioni insieme: per il calendario casuale k
si somma il logaritmo del capitale nelle stagioni con allarmi, e il valore p è la quota di k in cui la
somma è almeno quella del freno.

Scrive in results/: us_c42_rolling_seasons.csv (una riga per stagione), us_c42_rolling_random.csv
(capitale di ogni calendario casuale) e us_c42_rolling_summary.csv.
"""

import os

os.environ["SHK_ELO_ENTRY"] = "plain"  # nuova tesi: nessuna regola per le neopromosse, prima di importare shk

import csv
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from shk.kelly.agents import FractionalKellyAgent
from shk.kelly.environment import run_paired_backtest
from shk.kelly.outcome_rules import with_outcome_rule
from shk.model.agent_c import SCHEME_STOP_CLEAR, Module2Supervisor, ReferenceData
from shk.model.elo_fit import parse_season_start_year
from shk.model.frozen_agents import scheme_window
from shk.model.frozen_params import frozen_params_path, load_frozen_params
from shk.model.full_kelly_test import (
    FIRST_ROLLING_TEST, FREE_LAMBDA, KAPPA, LEVELS, SEED_S41, STRUCTURAL_LAMBDA, TEST_SEASON, ScheduledKellyAgent,
    episodes, fit_full_model, full_frame, full_residuals, lambda_schedule, past_reference, pooled_alarm_thresholds,
    pooled_block_length, pooled_reference, previous_season, random_calendar, season_label, test_input,
)
from shk.model.paired_backtest import CONFIGURATIONS
from shk.model.residuals import load_match_frame
from shk.model.season_thresholds import decision_ends
from shk.model.two_fold_diagnosis import TwoFoldSchemeAgent, calibrate_reference_diagnosis

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS = REPO_ROOT / "results"
SEED_S42: Final[int] = 20261122
N_CALENDARS: Final[int] = 2000
WORKERS: Final[int] = 5
KELLYBENCH_SCALE: Final[float] = 100_000.0
MIN_STAKE: Final[float] = dict(CONFIGURATIONS)["gbp_0.01"]
TEST_SEASONS: Final[tuple[str, ...]] = tuple(
    season_label(y) for y in range(parse_season_start_year(FIRST_ROLLING_TEST), parse_season_start_year(TEST_SEASON) + 1))


def _final(run) -> float:
    return float(run.wealth[0, -1])


def run_season(test_season: str, n_calendars: int = N_CALENDARS) -> tuple[dict, list[dict]]:
    """Una stagione di test con calibrazione sulle stagioni passate: riga della stagione e calendari casuali."""
    params = load_frozen_params(frozen_params_path())
    cov = list(params.fixed["covariates"])
    w = scheme_window(params)
    fallback = params.fixed["fallback_policy"]
    df, _ = load_match_frame(roles=("history", "training", "validation", "test"))
    fit = fit_full_model(df, test_season)
    frame = full_frame(full_residuals(df, fit, True, test_season), test_season)
    reference = past_reference(test_season)
    ref = pooled_reference(frame, cov, reference)
    length = pooled_block_length(ref)
    thr_seq, diag_seq = np.random.SeedSequence(SEED_S41).spawn(4)[:2]
    calendar = frame[frame["season"] == previous_season(test_season)]["Date"].to_numpy("datetime64[ns]")
    mean_thr, disp_thr = pooled_alarm_thresholds(ref, calendar, w, length, np.random.default_rng(thr_seq))
    diag = calibrate_reference_diagnosis(ref.x, ref.delta, w, length, np.random.default_rng(diag_seq))

    inp = test_input(frame, cov, test_season)
    sup = Module2Supervisor(inp.season, inp.dates, inp.x, cov, w, devig_method="shin",
                            reference=ReferenceData(ref.x, ref.delta))
    full = with_outcome_rule(FractionalKellyAgent, "R1")("kelly_pieno", lam=FREE_LAMBDA)
    brake = with_outcome_rule(TwoFoldSchemeAgent, "R1")("freno", sup, KAPPA, mean_thr, disp_thr, diag,
                                                       SCHEME_STOP_CLEAR, base_lambda=FREE_LAMBDA,
                                                       structural_lambda=STRUCTURAL_LAMBDA)
    r_full, r_brake = run_paired_backtest([full, brake], inp.dates, inp.probs, inp.odds, inp.outcomes, MIN_STAKE,
                                          fallback_policy=fallback)
    days = np.unique(inp.dates)
    diagnoses = brake.diagnosis_by_date
    cal = np.array([diagnoses.get(np.datetime64(d, "ns"), "none") for d in days], dtype=object)
    counts = np.searchsorted(inp.dates, days, side="left")
    first = int(np.flatnonzero(counts >= w)[0])
    ratios = [sup.reference_diagnostics(np.datetime64(d, "ns")) for d in days]
    ratios = [r for r in ratios if r is not None]

    rows = frame[frame["season"] == test_season]
    y = rows["FTR"].map({"H": 0, "D": 1, "A": 2}).to_numpy()
    k = np.arange(y.shape[0])
    p = rows[["p_home", "p_draw", "p_away"]].to_numpy(float)
    q = rows[["q_home", "q_draw", "q_away"]].to_numpy(float)
    row = {"season": test_season, "reference_first": reference[0], "reference_last": reference[-1],
           "n_reference": int(ref.delta.shape[0]), "k": fit.k, "h": fit.h, "nu": fit.nu,
           "mean_threshold": mean_thr, "dispersion_threshold": disp_thr,
           "g_hat": float(rows["delta"].mean()), "log_loss_model": float(-np.log(p[k, y]).mean()),
           "log_loss_market": float(-np.log(q[k, y]).mean()),
           "decision_days": len(days), "first_possible_day": first + 1,
           "max_mean_ratio": max(r[0] for r in ratios) / mean_thr,
           "max_dispersion_ratio": max(r[1] for r in ratios) / disp_thr,
           "alarm_days": int((cal != "none").sum()), "structural_days": int((cal == "structural").sum()),
           "data_error_days": int((cal == "compositional").sum()), "n_alarms": len(episodes(list(cal))),
           "first_alarm_day": int(np.flatnonzero(cal != "none")[0]) + 1 if (cal != "none").any() else "",
           "full_kelly": _final(r_full), "brake": _final(r_brake),
           "full_ruined": bool(r_full.ruined[0]), "brake_ruined": bool(r_brake.ruined[0])}

    random_rows: list[dict] = []
    if (cal != "none").any():
        own = run_paired_backtest([ScheduledKellyAgent("controllo", lambda_schedule(days, cal))], inp.dates, inp.probs,
                                  inp.odds, inp.outcomes, MIN_STAKE, fallback_policy=fallback)[0]
        if abs(np.log(_final(own)) - np.log(_final(r_brake))) > 1e-9:
            raise RuntimeError(f"{test_season}: scheduled replay differs from the brake")
        eps = episodes(list(cal))
        seeds = np.random.SeedSequence([SEED_S42, parse_season_start_year(test_season)]).spawn(n_calendars)
        agents = [ScheduledKellyAgent(f"casuale_{i}", lambda_schedule(days, random_calendar(eps, len(days), first,
                                                                                         np.random.default_rng(s))))
                  for i, s in enumerate(seeds)]
        mean_lam = float(np.mean([LEVELS[str(x)] for x in cal]))
        agents.append(ScheduledKellyAgent("costante", {d: mean_lam for d in days}))
        runs = run_paired_backtest(agents, inp.dates, inp.probs, inp.odds, inp.outcomes, MIN_STAKE,
                                   fallback_policy=fallback)
        finals = np.array([_final(r) for r in runs[:-1]])
        random_rows = [{"season": test_season, "calendar": i, "final_capital": v, "ruined": bool(r.ruined[0])}
                       for i, (v, r) in enumerate(zip(finals, runs[:-1]))]
        row.update({"random_median": float(np.median(finals)),
                    "random_p_value": float(np.mean(finals >= _final(r_brake) - 1e-15)),
                    "random_ruin_rate": float(np.mean([r["ruined"] for r in random_rows])),
                    "constant_lambda": mean_lam, "constant": _final(runs[-1])})
    return row, random_rows


def _write(path: Path, rows: list[dict]) -> None:
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, restval="")
        writer.writeheader()
        writer.writerows(rows)


def run_experiment() -> None:
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        results = list(pool.map(run_season, TEST_SEASONS))
    seasons = [r for r, _ in results]
    random_rows = [x for _, rr in results for x in rr]
    _write(RESULTS / "us_c42_rolling_seasons.csv", seasons)
    if random_rows:
        _write(RESULTS / "us_c42_rolling_random.csv", random_rows)

    s = pd.DataFrame(seasons).set_index("season")
    c41 = RESULTS / "us_c41_test_summary.csv"
    if c41.exists():
        m = pd.read_csv(c41).set_index("measure")["value"]
        if not np.isclose(float(m["brake_final_capital"]), s.loc[TEST_SEASON, "brake"], rtol=1e-6):
            raise RuntimeError("2023-24 differs from us_c41")
    lf, lb = np.log(s["full_kelly"]), np.log(s["brake"])
    d = lb - lf
    summary = [
        {"measure": "n_seasons", "value": len(s)},
        {"measure": "seasons_with_alarm", "value": int((s["alarm_days"] > 0).sum())},
        {"measure": "share_days_reduced", "value": float(s["alarm_days"].sum() / s["decision_days"].sum())},
        {"measure": "seasons_g_hat_negative", "value": int((s["g_hat"] < 0).sum())},
        {"measure": "typical_full_kelly", "value": float(np.exp(lf.mean()))},
        {"measure": "typical_brake", "value": float(np.exp(lb.mean()))},
        {"measure": "median_full_kelly_gbp_100k", "value": float(KELLYBENCH_SCALE * s["full_kelly"].median())},
        {"measure": "median_brake_gbp_100k", "value": float(KELLYBENCH_SCALE * s["brake"].median())},
        {"measure": "seasons_full_ruined", "value": int(s["full_ruined"].sum())},
        {"measure": "seasons_brake_ruined", "value": int(s["brake_ruined"].sum())},
        {"measure": "seasons_brake_better", "value": int((d > 1e-12).sum())},
        {"measure": "seasons_brake_worse", "value": int((d < -1e-12).sum())},
        {"measure": "wilcoxon_p", "value": float(wilcoxon(d[d.abs() > 1e-12]).pvalue) if (d.abs() > 1e-12).sum() else ""},
    ]
    if random_rows:
        rr = pd.DataFrame(random_rows)
        alarm = s[s["alarm_days"] > 0]
        joint = np.log(rr.pivot(index="calendar", columns="season", values="final_capital")[alarm.index]).sum(axis=1)
        observed = float(np.log(alarm["brake"]).sum())
        const = float(np.log(alarm["constant"]).sum())
        summary += [
            {"measure": "joint_brake_log_capital", "value": observed},
            {"measure": "joint_random_median_log_capital", "value": float(joint.median())},
            {"measure": "joint_constant_log_capital", "value": const},
            {"measure": "joint_random_p_value", "value": float((joint >= observed - 1e-12).mean())},
            {"measure": "seasons_brake_beats_median_random", "value": int((alarm["brake"] > alarm["random_median"]).sum())},
        ]
    _write(RESULTS / "us_c42_rolling_summary.csv", summary)
    pd.set_option("display.width", 250)
    print(s[["n_reference", "k", "h", "g_hat", "max_mean_ratio", "max_dispersion_ratio", "alarm_days",
             "structural_days", "full_kelly", "brake", "random_median", "random_p_value"]].round(4).to_string())
    print(pd.DataFrame(summary).to_string(index=False))


if __name__ == "__main__":
    run_experiment()
