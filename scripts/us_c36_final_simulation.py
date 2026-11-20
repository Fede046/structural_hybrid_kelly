"""Script: la versione definitiva dello schema nel mondo simulato di us_c25 (shk.model.edge_simulation).

Stessi scenari, stesse stagioni simulate e stessi seed di us_c25 (SEED_S25, N_REPLICAS repliche per
stagione), senza puntata minima. Le diagnosi della versione definitiva sono quelle dello schema con
soglie per stagione e diagnosi a due termini che riprende quando l'allarme si spegne
(C3_ref_season_dx), perché non dipendono dalle puntate. Senza puntata minima il capitale di un
calendario di λ è la somma dei rendimenti logaritmici giornalieri del Kelly frazionario a quei λ:
- F: λ dalla diagnosi del giorno (0.25, 0.25·κ, STRUCTURAL_LAMBDA = 0.10 con errore strutturale);
- F_season: come F, ma 0.10 dalla prima diagnosi strutturale fino a fine stagione.
Come controllo, lo schema con lo stop fino a fine stagione (C3_ref_stop_season_dx) e quello che
riprende (C3_ref_season_dx) devono dare il capitale di us_c25. Riferimento a pari esposizione: il
Kelly frazionario al λ medio di F nello scenario (edge_simulation.run_constant).

Scrive results/us_c36_final_simulation.csv: righe "capital" per scenario × agente e righe
"detection" per scenario (quota di stagioni con almeno una diagnosi strutturale, prima e dopo il
cambiamento, ritardo tipico, giornate con puntata ridotta). Con --replicas N usa N repliche e scrive
in build/final_simulation/ (prova rapida).
"""

import csv
import math
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Final

import numpy as np

from shk.kelly.agents import AGENT_A_LAMBDA, FractionalKellyAgent
from shk.kelly.environment import run_paired_backtest
from shk.model.agent_c import DIAGNOSIS_COMPOSITIONAL, DIAGNOSIS_STRUCTURAL, Module2Supervisor, ReferenceData
from shk.model.edge_simulation import N_REPLICAS, SCENARIOS, SEED_S25, calibration_setups, run_constant, scenario_season
from shk.model.frozen_agents import scheme_window
from shk.model.frozen_params import frozen_params_path, load_frozen_params
from shk.model.main_version import STRUCTURAL_LAMBDA
from shk.model.module2_data import build_module2_frame
from shk.model.residuals import load_model_residuals
from shk.model.two_fold_diagnosis import dx_agents
from shk.model.validation_run import validation_inputs

WORKERS = 5
CHECKS: Final[dict[str, str]] = {"stop_season": "C3_ref_stop_season_dx", "clear_zero": "C3_ref_season_dx"}
AGENTS: Final[tuple[str, ...]] = ("full_kelly", "quarter_kelly", "F", "F_season", "stop_season", "clear_zero",
                                  "constant:F")
COLUMNS: Final[tuple[str, ...]] = (
    "row_type", "scenario", "agent", "n_units", "typical_capital", "median_capital", "q05_capital", "q95_capital",
    "share_better_than_quarter", "share_worse_than_quarter", "mean_lambda", "share_structural",
    "share_structural_before", "median_delay_days", "share_days_reduced_before", "share_days_reduced_after",
)


def output_path(quick: bool) -> Path:
    root = Path(__file__).resolve().parents[1]
    return (root / "build" / "final_simulation" if quick else root / "results") / "us_c36_final_simulation.csv"


def season_units(params_path: str, setups, inp, seqs) -> list[dict]:
    """Per replica, scenario → capitale degli agenti e calendario di F."""
    params = load_frozen_params(params_path)
    kappa, base = float(params.calibrated["c1_kappa"]), float(params.fixed["c0_lambda"])
    levels = (STRUCTURAL_LAMBDA, base * kappa, base)
    out = []
    for k, seq in enumerate(seqs):
        uniforms = np.random.default_rng(seq).random(inp.dates.shape[0])
        rep = {}
        for sc in SCENARIOS:
            setup = setups[sc.a_before][k]
            sim, first = scenario_season(params, setup, inp, sc, uniforms)
            supervisor = Module2Supervisor(sim.season, sim.dates, sim.x, list(params.fixed["covariates"]),
                                           scheme_window(params),
                                           reference=ReferenceData(setup.per_date.x, setup.per_date.delta))
            schemes = dx_agents(params, setup.per_date, setup.per_season, setup.diagnosis, supervisor)
            fixed = [FractionalKellyAgent(f"lam{i}", lam=lv) for i, lv in enumerate(levels)]
            fixed.append(FractionalKellyAgent("full", lam=AGENT_A_LAMBDA))
            runs = {r.name: r for r in run_paired_backtest(schemes + fixed, sim.dates, sim.probs, sim.odds,
                                                            sim.outcomes, 0.0,
                                                            fallback_policy=params.fixed["fallback_policy"])}
            days = np.unique(sim.dates)
            by_name = {a.name: a for a in schemes}
            diag = np.array([by_name[CHECKS["clear_zero"]].diagnosis_by_date[np.datetime64(d, "ns")] for d in days])
            returns = np.stack([np.diff(np.log(runs[f"lam{i}"].wealth[0])) for i in range(3)])
            structural = diag == DIAGNOSIS_STRUCTURAL
            level = np.where(structural, 0, np.where(diag == DIAGNOSIS_COMPOSITIONAL, 1, 2))
            level_season = np.where(np.cumsum(structural) > 0, 0, level)
            idx = np.arange(days.shape[0])
            with np.errstate(divide="ignore"):
                values = {"full_kelly": float(np.log(runs["full"].wealth[0, -1])),
                          "quarter_kelly": float(np.log(runs["lam2"].wealth[0, -1])),
                          "F": float(returns[level, idx].sum()), "F_season": float(returns[level_season, idx].sum())}
                values.update({key: float(np.log(runs[arm].wealth[0, -1])) for key, arm in CHECKS.items()})
            after = structural[first:]
            rep[sc.name] = {**values, "lambda": np.array(levels)[level], "first": first,
                            "structural": bool(structural.any()), "structural_before": bool(structural[:first].any()),
                            "delay": int(np.argmax(after)) if after.any() else None}
        out.append(rep)
    return out


def _capital(lw: np.ndarray, quarter: np.ndarray) -> dict[str, float]:
    w = np.exp(lw)
    return {"typical_capital": math.exp(float(lw.mean())), "median_capital": float(np.median(w)),
            "q05_capital": float(np.quantile(w, 0.05)), "q95_capital": float(np.quantile(w, 0.95)),
            "share_better_than_quarter": float(np.mean(lw > quarter + 1e-12)),
            "share_worse_than_quarter": float(np.mean(lw < quarter - 1e-12))}


def run_experiment(n_replicas: int | None = None) -> None:
    path = output_path(quick=n_replicas is not None)
    path.parent.mkdir(parents=True, exist_ok=True)
    n_rep = N_REPLICAS if n_replicas is None else n_replicas
    params_path = frozen_params_path()
    params = load_frozen_params(params_path)
    frame = build_module2_frame(load_model_residuals())
    val = validation_inputs(frame, list(params.fixed["covariates"]))
    cal_root, season_root = np.random.SeedSequence(SEED_S25).spawn(2)
    cal_seqs = [s.spawn(n_rep) for s in cal_root.spawn(len(val))]
    season_seqs = [s.spawn(n_rep) for s in season_root.spawn(len(val))]
    a_values = sorted({s.a_before for s in SCENARIOS})
    p, inputs = str(params_path), [s.inp for s in val]
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        setups = list(pool.map(calibration_setups, [p] * len(val), inputs, [a_values] * len(val), cal_seqs))
        runs = list(pool.map(season_units, [p] * len(val), setups, inputs, season_seqs))
        units = {sc.name: [rep[sc.name] for season in runs for rep in season] for sc in SCENARIOS}
        lams = {name: {"F": float(np.concatenate([u["lambda"] for u in us]).mean())} for name, us in units.items()}
        constant = list(pool.map(run_constant, [p] * len(val), inputs, season_seqs, [lams] * len(val), setups))
    rows = []
    for sc in SCENARIOS:
        us = units[sc.name]
        quarter = np.array([u["quarter_kelly"] for u in us])
        const = np.array([rep[sc.name]["F"] for season in constant for rep in season])
        for agent in AGENTS:
            lw = const if agent == "constant:F" else np.array([u[agent] for u in us])
            rows.append({"row_type": "capital", "scenario": sc.name, "agent": agent, "n_units": len(us),
                         **_capital(lw, quarter),
                         "mean_lambda": lams[sc.name]["F"] if agent in ("F", "constant:F") else ""})
        delays = [u["delay"] for u in us if u["delay"] is not None]
        before = np.concatenate([u["lambda"][:u["first"]] for u in us])
        after = np.concatenate([u["lambda"][u["first"]:] for u in us])
        rows.append({"row_type": "detection", "scenario": sc.name, "agent": "F", "n_units": len(us),
                     "share_structural": float(np.mean([u["structural"] for u in us])),
                     "share_structural_before": float(np.mean([u["structural_before"] for u in us])),
                     "median_delay_days": float(np.median(delays)) if delays else "",
                     "share_days_reduced_before": float(np.mean(before < 0.25 - 1e-12)),
                     "share_days_reduced_after": float(np.mean(after < 0.25 - 1e-12))})
    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(COLUMNS), restval="")
        writer.writeheader()
        writer.writerows(rows)
    for r in rows:
        if r["row_type"] == "capital":
            print(f"{r['scenario']:<18} {r['agent']:<14} typical {r['typical_capital']:8.3f}  better/worse "
                  f"{r['share_better_than_quarter']:.2f}/{r['share_worse_than_quarter']:.2f}")
        else:
            print(f"{r['scenario']:<18} detection structural {r['share_structural']:.2f} (before "
                  f"{r['share_structural_before']:.2f}) delay {r['median_delay_days']}  reduced days "
                  f"{r['share_days_reduced_before']:.3f}/{r['share_days_reduced_after']:.3f}")


if __name__ == "__main__":
    args = sys.argv[1:]
    run_experiment(int(args[args.index("--replicas") + 1]) if "--replicas" in args else None)
