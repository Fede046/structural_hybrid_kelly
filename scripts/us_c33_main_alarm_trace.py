"""Script: la versione definitiva dello schema giornata per giornata (shk.model.main_version, "F").

Sulle 19 stagioni vere di validazione giocano, con la puntata minima di £0,01, il quarto di Kelly
senza supervisore e la versione definitiva (F: 0.10 dopo un errore strutturale, finché dura
l'allarme). A ogni giornata di decisione si registrano le due
statistiche dell'allarme contro la stagione di calibrazione e le loro soglie per stagione, le due
parti non spiegate della diagnosi a due termini e le loro soglie, la diagnosi, il moltiplicatore λ,
il capitale dei due agenti e l'errore atteso medio (E_q[δ]) delle partite della giornata. Per leggere
le statistiche: media del residuo e scarto tipico (distanza assoluta media dalla mediana della stagione
di calibrazione) nelle ultime 40 partite e nella stagione di calibrazione; la differenza fra i due
scarti tipici meno la parte non spiegata è la parte spiegata dalle caratteristiche delle partite.

Le statistiche sono quelle che lo schema usa: allarme se l'F della media o l'F di Brown-Forsythe
supera la soglia per stagione; diagnosi strutturale se, per la grandezza che ha fatto scattare
l'allarme, la parte non spiegata dalle caratteristiche delle partite supera la sua soglia. Il
capitale finale coincide con quello di us_c35 (agente F, configurazione gbp_0.01). Le diagnosi non
dipendono dalle puntate, quindi sono le stesse di ogni versione dello schema.

Scrive results/us_c33_main_alarm_trace.csv (stagione × giornata) e
results/us_c33_main_alarm_seasons.csv (una riga per stagione: primo allarme, statistica che lo fa
scattare, diagnosi, prima diagnosi strutturale, giornate con la puntata ridotta, capitale dei due
agenti).
"""

import csv
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Final

import numpy as np

from shk.kelly.environment import run_paired_backtest
from shk.market.devig import devig_probabilities
from shk.model.agent_c import expected_delta
from shk.model.frozen_params import frozen_params_path, load_frozen_params
from shk.model.main_version import MainSetup, build_agents, main_setups, reference_supervisor
from shk.model.module2_data import build_module2_frame
from shk.model.paired_backtest import CONFIGURATIONS
from shk.model.residuals import load_model_residuals
from shk.model.two_fold_diagnosis import unexplained_parts
from shk.model.validation_run import ValidationSeason, validation_inputs

WORKERS = 5
CONFIG: Final[str] = "gbp_0.01"
REPO_ROOT = Path(__file__).resolve().parents[1]
TRACE_CSV = REPO_ROOT / "results" / "us_c33_main_alarm_trace.csv"
SEASONS_CSV = REPO_ROOT / "results" / "us_c33_main_alarm_seasons.csv"
TRACE_COLUMNS: Final[tuple[str, ...]] = (
    "season", "fit_through", "day", "date", "n_matches", "matches_before", "f_mean", "f_mean_threshold",
    "f_dispersion", "f_dispersion_threshold", "u_mean", "u_mean_threshold", "u_dispersion",
    "u_dispersion_threshold", "alarm_mean", "alarm_dispersion", "diagnosis", "lambda", "wealth_main",
    "wealth_quarter", "expected_delta", "mean_window", "mean_reference", "spread_window", "spread_reference",
)
SEASON_COLUMNS: Final[tuple[str, ...]] = (
    "season", "fit_through", "n_days", "n_alarm_days", "first_alarm_day", "first_alarm_date",
    "first_alarm_matches_before", "first_alarm_trigger", "first_alarm_diagnosis", "first_structural_day",
    "first_structural_date", "first_structural_matches_before", "first_structural_trigger", "n_structural_days",
    "n_compositional_days", "share_days_reduced", "capital_main", "capital_quarter", "expected_delta_reduced",
    "expected_delta_other",
)


def _trigger(by_mean: bool, by_dispersion: bool) -> str:
    return {(True, True): "both", (True, False): "mean", (False, True): "dispersion"}.get((by_mean, by_dispersion), "")


def trace_season(params_path: str, setups: dict[str, MainSetup], season: ValidationSeason) -> list[dict]:
    """Una riga per giornata di decisione della stagione vera (versione definitiva e quarto di Kelly)."""
    params = load_frozen_params(params_path)
    inp, setup = season.inp, setups[season.fit]
    min_stake = dict(CONFIGURATIONS)[CONFIG]
    supervisor = reference_supervisor(params, inp, setup)
    agents = build_agents(params, setup, supervisor, ("B_0.25", "F"))
    runs = run_paired_backtest(agents, inp.dates, inp.probs, inp.odds, inp.outcomes, min_stake,
                               fallback_policy=params.fixed["fallback_policy"])
    quarter, main = runs
    scheme = agents[1]
    lambdas, diagnoses = scheme.lambda_by_date, scheme.diagnosis_by_date
    thr, diag = setup.per_season, setup.diagnosis
    ref_delta = np.asarray(setup.per_date.delta, dtype=np.float64)
    mean_ref, spread_ref = float(ref_delta.mean()), float(np.abs(ref_delta - diag.median).mean())
    q = devig_probabilities(np.asarray(inp.odds, dtype=np.float64), "shin")
    expected = expected_delta(np.asarray(inp.probs, dtype=np.float64), q)
    rows = []
    for k, day in enumerate(main.dates):
        day = np.datetime64(day, "ns")
        today = inp.dates == day
        stats = supervisor.reference_diagnostics(day)
        window = supervisor.reference_window(day)
        f_mean = f_disp = u_mean = u_disp = mean_w = spread_w = np.nan
        if window is not None:
            mean_w = float(window[1].mean())
            spread_w = float(np.abs(window[1] - diag.median).mean())
        if stats is not None and window is not None:
            f_mean, f_disp = stats[0], stats[1]
            u_mean, u_disp = unexplained_parts(window[0], window[1], diag.median, diag.beta_mean,
                                               diag.beta_dispersion)
        rows.append({
            "season": inp.season, "fit_through": season.fit, "day": k + 1, "date": str(day)[:10],
            "n_matches": int(today.sum()), "matches_before": int((inp.dates < day).sum()),
            "f_mean": f_mean, "f_mean_threshold": thr.mean_threshold,
            "f_dispersion": f_disp, "f_dispersion_threshold": thr.dispersion_threshold,
            "u_mean": u_mean, "u_mean_threshold": diag.mean_threshold,
            "u_dispersion": u_disp, "u_dispersion_threshold": diag.dispersion_threshold,
            "alarm_mean": bool(f_mean > thr.mean_threshold), "alarm_dispersion": bool(f_disp > thr.dispersion_threshold),
            "diagnosis": diagnoses[day], "lambda": lambdas[day],
            "wealth_main": float(main.wealth[0, k + 1]), "wealth_quarter": float(quarter.wealth[0, k + 1]),
            "expected_delta": float(expected[today].mean()),
            "mean_window": mean_w, "mean_reference": mean_ref, "spread_window": spread_w,
            "spread_reference": spread_ref,
        })
    return rows


def season_rows(trace: list[dict]) -> list[dict]:
    """Riassunto per stagione della traccia."""
    out = []
    for season in dict.fromkeys(r["season"] for r in trace):
        days = [r for r in trace if r["season"] == season]
        alarms = [r for r in days if r["diagnosis"] != "none"]
        structural = [r for r in days if r["diagnosis"] == "structural"]
        first, stop = (alarms[0] if alarms else None), (structural[0] if structural else None)
        reduced = [r for r in days if r["lambda"] < 0.25 - 1e-12]
        other = [r for r in days if r["lambda"] >= 0.25 - 1e-12]
        out.append({
            "season": season, "fit_through": days[0]["fit_through"], "n_days": len(days),
            "n_alarm_days": len(alarms),
            "first_alarm_day": first["day"] if first else "", "first_alarm_date": first["date"] if first else "",
            "first_alarm_matches_before": first["matches_before"] if first else "",
            "first_alarm_trigger": _trigger(first["alarm_mean"], first["alarm_dispersion"]) if first else "",
            "first_alarm_diagnosis": first["diagnosis"] if first else "",
            "first_structural_day": stop["day"] if stop else "",
            "first_structural_date": stop["date"] if stop else "",
            "first_structural_matches_before": stop["matches_before"] if stop else "",
            "first_structural_trigger": _trigger(stop["alarm_mean"], stop["alarm_dispersion"]) if stop else "",
            "n_structural_days": len(structural),
            "n_compositional_days": sum(r["diagnosis"] == "compositional" for r in days),
            "share_days_reduced": len(reduced) / len(days),
            "capital_main": days[-1]["wealth_main"], "capital_quarter": days[-1]["wealth_quarter"],
            "expected_delta_reduced": float(np.mean([r["expected_delta"] for r in reduced])) if reduced else "",
            "expected_delta_other": float(np.mean([r["expected_delta"] for r in other])) if other else "",
        })
    return out


def _write(path: Path, columns: tuple[str, ...], rows: list[dict]) -> None:
    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(columns), restval="")
        writer.writeheader()
        writer.writerows(rows)


def run_experiment() -> None:
    params_path = frozen_params_path()
    params = load_frozen_params(params_path)
    frame = build_module2_frame(load_model_residuals())
    setups = main_setups(frame[frame["role"] == "training"], params)
    val = validation_inputs(frame, list(params.fixed["covariates"]))
    n = len(val)
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        trace = [r for rows in pool.map(trace_season, [str(params_path)] * n, [setups] * n, val) for r in rows]
    seasons = season_rows(trace)
    _write(TRACE_CSV, TRACE_COLUMNS, trace)
    _write(SEASONS_CSV, SEASON_COLUMNS, seasons)
    for r in seasons:
        print(f"{r['season']}  alarm day {r['first_alarm_day']!s:>3} ({r['first_alarm_trigger']:<10}) "
              f"{r['first_alarm_diagnosis']:<13} first structural day {r['first_structural_day']!s:>3}  reduced {r['share_days_reduced']:.2f}  "
              f"M {100 * r['capital_main']:.0f}%  B {100 * r['capital_quarter']:.0f}%")


if __name__ == "__main__":
    run_experiment()
