"""Script: lo schema con riferimento fisso in un mondo simulato con vantaggio noto (shk.model.edge_simulation).

Per ogni scenario di SCENARIOS, sulle 19 stagioni di validazione come ossatura (date, quote, previsioni
e covariate vere, esiti simulati) e N_REPLICAS repliche per stagione, senza puntata minima:
1. simula il riferimento di ogni stagione (una copia indipendente della stagione) e calibra le soglie;
2. esegue Kelly pieno, quarto di Kelly, le versioni dello schema di SCHEME_ARMS e l'oracolo;
3. esegue il Kelly frazionario a λ costante uguale al λ medio di ogni schema nello scenario.
Scrive results/us_c25_edge_simulation.csv: righe "capital" per scenario × agente e righe "detection"
per scenario × schema. Con --replicas N usa N repliche e scrive in build/edge_simulation/ (prova rapida).
"""

import csv
import math
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Final

import numpy as np

from shk.model.edge_simulation import (
    N_REPLICAS,
    SCENARIOS,
    SCHEME_ARMS,
    SEED_S25,
    calibration_setups,
    first_stop_day,
    run_constant,
    run_replicas,
    share_of_days,
)
from shk.model.frozen_params import frozen_params_path, load_frozen_params
from shk.model.module2_data import build_module2_frame
from shk.model.residuals import load_model_residuals
from shk.model.timing_placebo import LEVEL_REDUCED, LEVEL_ZERO
from shk.model.validation_run import validation_inputs

WORKERS = 5
TOL: Final[float] = 1e-12
COLUMNS: Final[tuple[str, ...]] = (
    "row_type", "scenario", "a_before", "a_after", "agent", "n_units", "n_replicas",
    "typical_capital", "median_capital", "q05_capital", "q95_capital", "share_ruined",
    "share_better_than_quarter", "share_worse_than_quarter", "mean_lambda",
    "share_stopped", "share_stopped_before", "median_delay_days",
    "share_days_zero_before", "share_days_zero_after", "share_days_reduced_before", "share_days_reduced_after",
    "mean_log_gain_before", "mean_log_gain_after", "share_structural_after",
)


def output_path(quick: bool) -> Path:
    root = Path(__file__).resolve().parents[1]
    return (root / "build" / "edge_simulation" if quick else root / "results") / "us_c25_edge_simulation.csv"


def _capital_row(lw: np.ndarray, quarter: np.ndarray) -> dict[str, float]:
    ruined = ~np.isfinite(lw)
    wealth = np.where(ruined, 0.0, np.exp(np.where(ruined, 0.0, lw)))
    return {"typical_capital": 0.0 if ruined.any() else math.exp(float(lw.mean())),
            "median_capital": float(np.median(wealth)), "q05_capital": float(np.quantile(wealth, 0.05)),
            "q95_capital": float(np.quantile(wealth, 0.95)), "share_ruined": float(ruined.mean()),
            "share_better_than_quarter": float((lw > quarter + TOL).mean()),
            "share_worse_than_quarter": float((lw < quarter - TOL).mean())}


def run_experiment(n_replicas: int | None = None) -> None:
    path = output_path(quick=n_replicas is not None)
    path.parent.mkdir(parents=True, exist_ok=True)
    n_rep = N_REPLICAS if n_replicas is None else n_replicas
    params_path = frozen_params_path()
    params = load_frozen_params(params_path)
    covariates = list(params.fixed["covariates"])
    frame = build_module2_frame(load_model_residuals())
    val = validation_inputs(frame, covariates)
    cal_root, season_root = np.random.SeedSequence(SEED_S25).spawn(2)
    cal_seqs = [s.spawn(n_rep) for s in cal_root.spawn(len(val))]
    season_seqs = [s.spawn(n_rep) for s in season_root.spawn(len(val))]
    a_values = sorted({s.a_before for s in SCENARIOS})
    p = str(params_path)

    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        inputs = [s.inp for s in val]
        setups = list(pool.map(calibration_setups, [p] * len(val), inputs, [a_values] * len(val), cal_seqs))
        runs = list(pool.map(run_replicas, [p] * len(val), setups, inputs, season_seqs))
        units = {sc.name: [rep[sc.name] for season in runs for rep in season] for sc in SCENARIOS}
        lams = {name: {arm: float(np.concatenate([u.lambdas[arm] for u in us]).mean()) for arm in SCHEME_ARMS}
                for name, us in units.items()}
        constant = list(pool.map(run_constant, [p] * len(val), inputs, season_seqs, [lams] * len(val), setups))

    rows = []
    for sc in SCENARIOS:
        us = units[sc.name]
        common = {"scenario": sc.name, "a_before": sc.a_before, "a_after": sc.a_after, "n_units": len(us),
                  "n_replicas": n_rep}
        quarter = np.array([u.log_wealth["quarter_kelly"] for u in us])
        const = {arm: np.array([rep[sc.name][arm] for season in constant for rep in season]) for arm in SCHEME_ARMS}
        series = [("full_kelly", None), ("quarter_kelly", None)] + [(arm, lams[sc.name][arm]) for arm in SCHEME_ARMS]
        series += [(f"constant:{arm}", lams[sc.name][arm]) for arm in SCHEME_ARMS] + [("oracle", None)]
        for agent, lam in series:
            lw = (const[agent.split(":")[1]] if agent.startswith("constant:")
                  else np.array([u.log_wealth[agent] for u in us]))
            rows.append({**common, "row_type": "capital", "agent": agent, **_capital_row(lw, quarter),
                         "mean_lambda": "" if lam is None else lam})
        for arm in SCHEME_ARMS:
            stops = [first_stop_day(u.levels[arm]) for u in us]
            firsts = [u.first_day_after for u in us]
            delays = [s - f for s, f in zip(stops, firsts) if s is not None and s >= f]
            levels = [u.levels[arm] for u in us]
            zero_before, zero_after = share_of_days(levels, firsts, LEVEL_ZERO)
            red_before, red_after = share_of_days(levels, firsts, LEVEL_REDUCED)
            alarms = sum(u.alarm_days_after[arm] for u in us)
            rows.append({
                **common, "row_type": "detection", "agent": arm,
                "share_stopped": float(np.mean([s is not None for s in stops])),
                "share_stopped_before": float(np.mean([s is not None and s < f for s, f in zip(stops, firsts)])),
                "median_delay_days": float(np.median(delays)) if delays else "",
                "share_days_zero_before": zero_before, "share_days_zero_after": zero_after,
                "share_days_reduced_before": red_before, "share_days_reduced_after": red_after,
                "mean_log_gain_before": float(np.mean([u.gain_before[arm] for u in us])),
                "mean_log_gain_after": float(np.mean([u.gain_after[arm] for u in us])),
                "share_structural_after": sum(u.structural_days_after[arm] for u in us) / alarms if alarms else ""})
    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(COLUMNS), restval="")
        writer.writeheader()
        writer.writerows(rows)

    for sc in SCENARIOS:
        print(f"\n{sc.name} (a {sc.a_before:+.0f} -> {sc.a_after:+.0f})")
        for r in rows:
            if r["scenario"] != sc.name:
                continue
            if r["row_type"] == "capital":
                lam = "" if r["mean_lambda"] == "" else f"lambda {r['mean_lambda']:.3f}"
                print(f"  {r['agent']:<22} typical {r['typical_capital']:>7.3f}  median {r['median_capital']:>7.3f}  "
                      f"better/worse than quarter {r['share_better_than_quarter']:.2f}/{r['share_worse_than_quarter']:.2f}  {lam}")
            else:
                print(f"  detection {r['agent']:<12} stopped {r['share_stopped']:.2f} (before {r['share_stopped_before']:.2f})  "
                      f"delay {r['median_delay_days']}  zero days {r['share_days_zero_before']:.2f}/{r['share_days_zero_after']:.2f}  "
                      f"gain {r['mean_log_gain_before']:+.3f}/{r['mean_log_gain_after']:+.3f}  structural {r['share_structural_after']}")


if __name__ == "__main__":
    argv = sys.argv[1:]
    replicas_ = int(argv[argv.index("--replicas") + 1]) if "--replicas" in argv else None
    run_experiment(replicas_)
