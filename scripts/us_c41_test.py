"""Script: il test della nuova tesi sul 2023-24 (thesis/TESI_kellybench.md, capitolo 4), eseguito una volta.

Legge la calibrazione di us_c41_calibration (parametri del modello e soglie, fissati prima del test)
e gioca il 2023-24 con la puntata minima di £0,01 e il capitale di £220:
- Kelly pieno senza freno e Kelly pieno con il freno (λ = 1 / 0,75 / 0,40, finché dura l'allarme);
- il vantaggio sul mercato (ĝ, log-loss del modello e del mercato senza margine);
- il freno casuale: N_CALENDARS calendari con gli stessi allarmi (numero, tipo, durata) in momenti
  casuali, e due controlli più semplici (giornate rimescolate una per una, frazione costante);
- N_RECON stagioni ricostruite (stationary bootstrap delle giornate): Kelly pieno, freno e, in
  ciascuna, un freno casuale costruito dal calendario del freno in quella stagione.

Scrive in results/: us_c41_test_trace.csv (una riga per giornata), us_c41_test_summary.csv,
us_c41_test_random_brake.csv (una riga per calendario casuale) e us_c41_test_reconstructed.csv.
"""

import os

os.environ["SHK_ELO_ENTRY"] = "plain"  # nuova tesi: nessuna regola per le neopromosse, prima di importare shk

import csv
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from shk.kelly.agents import FractionalKellyAgent
from shk.kelly.environment import run_paired_backtest
from shk.kelly.outcome_rules import with_outcome_rule
from shk.model.agent_c import SCHEME_STOP_CLEAR, Module2Supervisor, ReferenceData
from shk.model.elo_fit import EloFitParams
from shk.model.frozen_agents import scheme_window
from shk.model.frozen_params import frozen_params_path, load_frozen_params
from shk.model.full_kelly_test import (
    DATA_LAMBDA, FREE_LAMBDA, KAPPA, LEVELS, SEED_S41, STRUCTURAL_LAMBDA, ScheduledKellyAgent, episodes, full_frame,
    full_residuals, lambda_schedule, pooled_block_length, pooled_reference, random_calendar, test_input,
)
from shk.model.paired_backtest import CONFIGURATIONS
from shk.model.residuals import load_match_frame
from shk.model.season_bootstrap import reconstruct_season, season_block_length
from shk.model.season_input import SeasonInput, season_input_from_frame
from shk.model.season_thresholds import decision_ends
from shk.model.two_fold_diagnosis import TwoFoldSchemeAgent, calibrate_reference_diagnosis

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS = REPO_ROOT / "results"
CALIBRATION_CSV = RESULTS / "us_c41_calibration.csv"
N_CALENDARS: Final[int] = 10_000
N_RECON: Final[int] = 500
WORKERS: Final[int] = 5
KELLYBENCH_SCALE: Final[float] = 100_000.0
MIN_STAKE: Final[float] = dict(CONFIGURATIONS)["gbp_0.01"]
DRY_RUN_SEASON: Final[str] = "2020-21"


def _setup():
    params = load_frozen_params(frozen_params_path())
    cov = list(params.fixed["covariates"])
    w = scheme_window(params)
    c = pd.read_csv(CALIBRATION_CSV).iloc[0]
    df, _ = load_match_frame(roles=("history", "training", "validation", "test"))
    fit = EloFitParams(k=float(c.k), h=float(c.h), nu=float(c.nu), c=float(c.c))
    frame = full_frame(full_residuals(df, fit, include_test=True))
    ref = pooled_reference(frame, cov)
    length = pooled_block_length(ref)
    diag_seq = np.random.SeedSequence(SEED_S41).spawn(4)[1]
    diag = calibrate_reference_diagnosis(ref.x, ref.delta, w, length, np.random.default_rng(diag_seq))
    if not (int(c.n_reference) == ref.delta.shape[0] and int(c.block_length) == length
            and np.isclose(diag.mean_threshold, c.unexplained_mean_threshold, rtol=0, atol=1e-12)
            and np.isclose(diag.dispersion_threshold, c.unexplained_dispersion_threshold, rtol=0, atol=1e-12)):
        raise RuntimeError("the reference differs from the calibration of us_c41_calibration")
    return params, cov, w, c, frame, ref, diag


def _agents(params, cov, w, c, ref, diag, inp: SeasonInput):
    sup = Module2Supervisor(inp.season, inp.dates, inp.x, cov, w, devig_method="shin",
                            reference=ReferenceData(ref.x, ref.delta))
    full = with_outcome_rule(FractionalKellyAgent, "R1")("kelly_pieno", lam=FREE_LAMBDA)
    brake = with_outcome_rule(TwoFoldSchemeAgent, "R1")("freno", sup, KAPPA, float(c.mean_threshold),
                                                       float(c.dispersion_threshold), diag, SCHEME_STOP_CLEAR,
                                                       base_lambda=FREE_LAMBDA, structural_lambda=STRUCTURAL_LAMBDA)
    return sup, full, brake


def _run(agents, inp: SeasonInput, fallback: str):
    return run_paired_backtest(agents, inp.dates, inp.probs, inp.odds, inp.outcomes, MIN_STAKE,
                               fallback_policy=fallback)


def _final(run) -> float:
    return float(run.wealth[0, -1])


def _calendar(brake, days: np.ndarray) -> np.ndarray:
    d = brake.diagnosis_by_date
    return np.array([d.get(np.datetime64(x, "ns"), "none") for x in days], dtype=object)


def _first_day(inp: SeasonInput, w: int) -> int:
    days = np.unique(inp.dates)
    ends = decision_ends(inp.dates, w)
    counts = np.searchsorted(inp.dates, days, side="left")
    return int(np.flatnonzero(counts >= w)[0]) if ends.shape[0] else len(days)


def _shuffled_days(cal: np.ndarray, first: int, rng: np.random.Generator) -> np.ndarray:
    out = cal.copy()
    out[first:] = cal[first:][rng.permutation(cal.shape[0] - first)]
    return out


def _random_chunk(args) -> list[dict]:
    inp, cal, first, seeds, kind, fallback = args
    eps = episodes(list(cal))
    days = np.unique(inp.dates)
    agents, rows = [], []
    for k, ss in enumerate(seeds):
        rng = np.random.default_rng(ss)
        rc = random_calendar(eps, len(days), first, rng) if kind == "episodes" else _shuffled_days(cal, first, rng)
        agents.append(ScheduledKellyAgent(f"{kind}_{k}", lambda_schedule(days, rc)))
        rows.append({"kind": kind, "calendar": k, "reduced_days": int((rc != "none").sum())})
    runs = _run(agents, inp, fallback)
    for r, run in zip(rows, runs):
        r["final_capital"] = _final(run)
        r["ruined"] = bool(run.ruined[0])
    return rows


def _recon_chunk(args) -> list[dict]:
    seeds, block, params_path, cov, w, c, ref, diag, inp0 = args
    params = load_frozen_params(params_path)
    fallback = params.fixed["fallback_policy"]
    out = []
    for ss in seeds:
        rng_rec, rng_cal = (np.random.default_rng(s) for s in ss.spawn(2))
        inp = reconstruct_season(inp0, rng_rec, block, covariates=cov)
        _, full, brake = _agents(params, cov, w, c, ref, diag, inp)
        r_full, r_brake = _run([full, brake], inp, fallback)
        days = np.unique(inp.dates)
        cal = _calendar(brake, days)
        rc = random_calendar(episodes(list(cal)), len(days), _first_day(inp, w), rng_cal)
        r_rand = _run([ScheduledKellyAgent("freno_casuale", lambda_schedule(days, rc))], inp, fallback)[0]
        out.append({"full_kelly": _final(r_full), "brake": _final(r_brake), "random_brake": _final(r_rand),
                    "full_ruined": bool(r_full.ruined[0]), "brake_ruined": bool(r_brake.ruined[0]),
                    "random_ruined": bool(r_rand.ruined[0]), "alarm_days": int((cal != "none").sum()),
                    "structural_days": int((cal == "structural").sum()), "n_alarms": len(episodes(list(cal)))})
    return out


def _write(path: Path, rows: list[dict]) -> None:
    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run_experiment(dry_run: bool = False) -> None:
    """dry_run: stessa catena su una stagione del riferimento con allarmi (2020-21, nel campione), con pochi
    calendari e poche ricostruzioni, uscite in build/scratch: serve solo a provare il codice senza
    guardare il 2023-24."""
    global RESULTS
    params, cov, w, c, frame, ref, diag = _setup()
    fallback = params.fixed["fallback_policy"]
    if dry_run:
        RESULTS = REPO_ROOT / "build" / "scratch" / "us_c41_dry_run"
        RESULTS.mkdir(parents=True, exist_ok=True)
        inp = season_input_from_frame(frame[frame["season"] == DRY_RUN_SEASON], DRY_RUN_SEASON, cov)
        n_calendars, n_recon = 200, 20
    else:
        inp = test_input(frame, cov)
        n_calendars, n_recon = N_CALENDARS, N_RECON
    days = np.unique(inp.dates)
    seq_cal, seq_shuffle, seq_recon = np.random.SeedSequence(SEED_S41).spawn(4)[2].spawn(3)

    # 1. La stagione vera
    sup, full, brake = _agents(params, cov, w, c, ref, diag, inp)
    r_full, r_brake = _run([full, brake], inp, fallback)
    cal = _calendar(brake, days)
    first = _first_day(inp, w)
    # Controllo: il calendario del freno, giocato come calendario fisso, riproduce il freno
    own = _run([ScheduledKellyAgent("controllo", lambda_schedule(days, cal))], inp, fallback)[0]
    if abs(np.log(_final(own)) - np.log(_final(r_brake))) > 1e-9:
        raise RuntimeError(f"scheduled replay {_final(own)} differs from the brake {_final(r_brake)}")
    trace = []
    for j, d in enumerate(days):
        stats = sup.reference_diagnostics(np.datetime64(d, "ns"))
        trace.append({"day": j + 1, "date": str(pd.Timestamp(d).date()), "n_matches": int((inp.dates == d).sum()),
                      "f_mean_ratio": stats[0] / float(c.mean_threshold) if stats else np.nan,
                      "f_dispersion_ratio": stats[1] / float(c.dispersion_threshold) if stats else np.nan,
                      "diagnosis": cal[j], "lambda": LEVELS[str(cal[j])],
                      "wealth_full_kelly": float(r_full.wealth[0, j + 1]),
                      "wealth_brake": float(r_brake.wealth[0, j + 1])})
    _write(RESULTS / "us_c41_test_trace.csv", trace)

    # 2. Il vantaggio sul mercato
    rows = frame[frame["season"] == inp.season]
    y = rows["FTR"].map({"H": 0, "D": 1, "A": 2}).to_numpy()
    k = np.arange(y.shape[0])
    p = rows[["p_home", "p_draw", "p_away"]].to_numpy(float)
    q = rows[["q_home", "q_draw", "q_away"]].to_numpy(float)
    summary = [
        {"measure": "g_hat", "value": float(rows["delta"].mean())},
        {"measure": "log_loss_model", "value": float(-np.log(p[k, y]).mean())},
        {"measure": "log_loss_market_shin", "value": float(-np.log(q[k, y]).mean())},
        {"measure": "decision_days", "value": len(days)},
        {"measure": "first_possible_day", "value": first + 1},
        {"measure": "alarm_days", "value": int((cal != "none").sum())},
        {"measure": "data_error_days", "value": int((cal == "compositional").sum())},
        {"measure": "structural_days", "value": int((cal == "structural").sum())},
        {"measure": "n_alarms", "value": len(episodes(list(cal)))},
    ]
    for name, run in (("full_kelly", r_full), ("brake", r_brake)):
        summary += [{"measure": f"{name}_final_capital", "value": _final(run)},
                    {"measure": f"{name}_final_gbp_100k", "value": KELLYBENCH_SCALE * _final(run)},
                    {"measure": f"{name}_ruined", "value": bool(run.ruined[0])},
                    {"measure": f"{name}_ruin_day", "value": int(run.ruin_date_index[0]) + 1 if run.ruined[0] else ""},
                    {"measure": f"{name}_n_bets", "value": int(run.n_bets[0])}]
    print(pd.DataFrame(summary).to_string(index=False))

    # 3. Il freno casuale e i controlli semplici
    random_rows: list[dict] = []
    if (cal != "none").any():
        with ProcessPoolExecutor(max_workers=WORKERS) as pool:
            jobs = []
            for kind, seq in (("episodes", seq_cal), ("days", seq_shuffle)):
                seeds = seq.spawn(n_calendars)
                for chunk in np.array_split(np.arange(n_calendars), WORKERS * 4):
                    jobs.append((inp, cal, first, [seeds[i] for i in chunk], kind, fallback))
            for rows_chunk in pool.map(_random_chunk, jobs):
                random_rows += rows_chunk
        _write(RESULTS / "us_c41_test_random_brake.csv", random_rows)
        mean_lam = float(np.mean([LEVELS[str(x)] for x in cal]))
        const = _run([ScheduledKellyAgent("costante", {d: mean_lam for d in days})], inp, fallback)[0]
        rb = pd.DataFrame(random_rows)
        for kind in ("episodes", "days"):
            g = rb[rb["kind"] == kind]
            summary += [{"measure": f"random_{kind}_median_capital", "value": float(g["final_capital"].median())},
                        {"measure": f"random_{kind}_p_value",
                         "value": float((g["final_capital"] >= _final(r_brake) - 1e-15).mean())},
                        {"measure": f"random_{kind}_ruin_rate", "value": float(g["ruined"].mean())}]
        summary += [{"measure": "constant_lambda", "value": mean_lam},
                    {"measure": "constant_final_capital", "value": _final(const)}]
    else:
        summary.append({"measure": "random_brake", "value": "no alarm in the true season: not computable"})

    # 4. Le stagioni ricostruite
    block = season_block_length(inp)
    recon_seeds = seq_recon.spawn(n_recon)
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        chunks = [([recon_seeds[i] for i in ch], block, str(frozen_params_path()), cov, w, c, ref, diag, inp)
                  for ch in np.array_split(np.arange(n_recon), WORKERS * 4)]
        recon = [r for rows_chunk in pool.map(_recon_chunk, chunks) for r in rows_chunk]
    _write(RESULTS / "us_c41_test_reconstructed.csv", recon)
    rc = pd.DataFrame(recon)
    for name in ("full_kelly", "brake", "random_brake"):
        v = rc[name] * KELLYBENCH_SCALE
        ruined = {"full_kelly": "full_ruined", "brake": "brake_ruined", "random_brake": "random_ruined"}[name]
        summary += [{"measure": f"recon_{name}_median_gbp_100k", "value": float(v.median())},
                    {"measure": f"recon_{name}_q05_gbp_100k", "value": float(v.quantile(0.05))},
                    {"measure": f"recon_{name}_q95_gbp_100k", "value": float(v.quantile(0.95))},
                    {"measure": f"recon_{name}_ruin_rate", "value": float(rc[ruined].mean())}]
    with_alarm = rc[rc["alarm_days"] > 0]
    summary += [{"measure": "recon_block_length", "value": block},
                {"measure": "recon_share_with_alarm", "value": float((rc["alarm_days"] > 0).mean())},
                {"measure": "recon_brake_better_than_full", "value": float((rc["brake"] > rc["full_kelly"]).mean())},
                {"measure": "recon_brake_worse_than_full", "value": float((rc["brake"] < rc["full_kelly"]).mean())},
                {"measure": "recon_with_alarm_brake_better_than_random",
                 "value": float((with_alarm["brake"] > with_alarm["random_brake"]).mean()) if len(with_alarm) else ""},
                {"measure": "recon_with_alarm_brake_worse_than_random",
                 "value": float((with_alarm["brake"] < with_alarm["random_brake"]).mean()) if len(with_alarm) else ""}]
    _write(RESULTS / "us_c41_test_summary.csv", summary)
    print(pd.DataFrame(summary).to_string(index=False))


if __name__ == "__main__":
    import sys
    run_experiment(dry_run="--dry-run" in sys.argv)
