"""Script: diagnosi di Blinder-Oaxaca a due termini su media e dispersione (shk.model.two_fold_diagnosis).

Sulle 19 stagioni vere di validazione:
1. calibra per ogni fit le regressioni di riferimento e le soglie delle parti non spiegate;
2. confronta le due diagnosi a ogni giornata di decisione, per tipo di allarme;
3. scompone, stagione intera contro stagione di calibrazione, il cambiamento della media e della
   dispersione di δ, con intervalli bootstrap;
4. esegue le versioni di DX_ARMS accanto a quelle con la diagnosi a tre termini, nelle tre
   configurazioni di puntata minima, con i confronti appaiati e il controllo placebo.
Scrive in results/ i file us_c27_two_fold_*.csv: thresholds, diagnosis, components, decomposition,
seasons, summary, placebo. Con --draws N usa N estrazioni placebo e scrive in build/two_fold/ (prova rapida).
"""

import csv
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from shk.model.frozen_agents import scheme_window
from shk.model.frozen_params import frozen_params_path, load_frozen_params
from shk.model.module2_data import build_module2_frame
from shk.model.paired_inference import paired_statistics
from shk.model.residuals import load_model_residuals
from shk.model.season_thresholds import season_setups, summary_rows
from shk.model.timing_placebo import COLUMNS, N_DRAWS, mean_lambda, placebo_tables, run_constant_season
from shk.model.two_fold_diagnosis import (
    DIAGNOSIS_COLUMNS,
    DX_ARMS,
    RUN_ARMS,
    SEED_S27,
    component_summary,
    decision_records,
    diagnosis_setups,
    diagnosis_table,
    run_real_season,
    run_schedule_season,
    season_decomposition,
)
from shk.model.validation_run import validation_inputs

WORKERS = 5
NAMES: Final[tuple[str, ...]] = ("thresholds", "diagnosis", "components", "decomposition", "seasons", "summary",
                                 "placebo")
TABLE_COLUMNS: Final[tuple[str, ...]] = ("alarm", "n_days", "share_structural_three_fold", "share_structural_two_fold")
DECOMPOSITION_COLUMNS: Final[tuple[str, ...]] = ("season", "fit_through", "response", "component", "value", "low",
                                                 "high")
SEASON_COLUMNS: Final[tuple[str, ...]] = ("season", "fit_through", "config", "agent", "log_wealth", "n_alarms",
                                          "share_days_zero")
SUMMARY_COLUMNS: Final[tuple[str, ...]] = (
    "config", "agent", "n_seasons", "typical_capital", "seasons_better", "seasons_worse", "seasons_with_stop",
    "mean_alarms", "share_days_zero", "sign_test_p", "wilcoxon_p", "capital_ratio", "capital_ratio_low",
    "capital_ratio_high",
)
PAIRED: Final[tuple[str, ...]] = ("sign_test_p", "wilcoxon_p", "capital_ratio", "capital_ratio_low",
                                  "capital_ratio_high")


def output_paths(quick: bool) -> dict[str, Path]:
    root = Path(__file__).resolve().parents[1]
    base = root / "build" / "two_fold" if quick else root / "results"
    return {name: base / f"us_c27_two_fold_{name}.csv" for name in NAMES}


def _write(path: Path, columns: tuple[str, ...], rows: list[dict]) -> None:
    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(columns), restval="")
        writer.writeheader()
        writer.writerows(rows)


def run_experiment(n_draws: int | None = None) -> None:
    paths = output_paths(quick=n_draws is not None)
    paths["summary"].parent.mkdir(parents=True, exist_ok=True)
    draws = N_DRAWS if n_draws is None else n_draws
    params_path = frozen_params_path()
    params = load_frozen_params(params_path)
    frame = build_module2_frame(load_model_residuals())
    train = frame[frame["role"] == "training"]
    per_date, per_season, threshold_rows = season_setups(train, params)
    diagnoses, diagnosis_rows = diagnosis_setups(train, params)
    blocks = {r["fit"]: int(r["block_length"]) for r in threshold_rows}
    val = validation_inputs(frame, list(params.fixed["covariates"]))
    n, p, w = len(val), str(params_path), scheme_window(params)

    decisions = [r for s in val for r in decision_records(s, per_date[s.fit], diagnoses[s.fit], w)]
    table = diagnosis_table(decisions)
    components = component_summary(decisions)
    decomposition = []
    for s, seq in zip(val, np.random.SeedSequence(SEED_S27).spawn(2)[1].spawn(n)):
        rows = season_decomposition(per_date[s.fit], s.inp, blocks[s.fit], np.random.default_rng(seq))
        decomposition += [{**r, "fit_through": s.fit} for r in rows]

    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        shared = ([p] * n, [per_date] * n, [per_season] * n, [diagnoses] * n, val)
        season_rows = [r for rows in pool.map(run_real_season, *shared) for r in rows]
        schedules = list(pool.map(run_schedule_season, *shared))
        lams = {arm: mean_lambda(schedules, arm) for arm in DX_ARMS}
        constant = list(pool.map(run_constant_season, [p] * n, val, [lams] * n, [DX_ARMS] * n))

    summary = summary_rows(season_rows, RUN_ARMS)
    df = pd.DataFrame(season_rows)
    paired = [r for r in summary if r["agent"] != "B_0.25"]
    for row, seq in zip(paired, np.random.SeedSequence([SEED_S27, 2]).spawn(len(paired))):
        rows = df[df["config"] == row["config"]]
        x = rows[rows["agent"] == row["agent"]].set_index("season")["log_wealth"]
        y = rows[rows["agent"] == "B_0.25"].set_index("season")["log_wealth"].loc[x.index]
        stats = paired_statistics(x.to_numpy(float), y.to_numpy(float), np.random.default_rng(seq))
        row.update({k: stats[k] for k in PAIRED})
    placebo_rows, _ = placebo_tables(schedules, constant, lams, draws, np.random.SeedSequence([SEED_S27, 1]), DX_ARMS)

    _write(paths["thresholds"], DIAGNOSIS_COLUMNS, diagnosis_rows)
    _write(paths["diagnosis"], TABLE_COLUMNS, table)
    _write(paths["components"], ("statistic", "value"), components)
    _write(paths["decomposition"], DECOMPOSITION_COLUMNS, decomposition)
    _write(paths["seasons"], SEASON_COLUMNS, season_rows)
    _write(paths["summary"], SUMMARY_COLUMNS, summary)
    _write(paths["placebo"], COLUMNS, placebo_rows)

    for r in diagnosis_rows:
        print(f"fit {r['fit']}: R2 mean {r['r2_mean']:.3f}, dispersion {r['r2_dispersion']:.3f}; thresholds "
              f"{r['unexplained_mean_threshold']:.3f}, {r['unexplained_dispersion_threshold']:.3f}")
    print({r["statistic"]: round(r["value"], 3) for r in components})
    for r in table:
        print(f"alarm {r['alarm']:<16} days {r['n_days']:>5}  structural: three-fold "
              f"{r['share_structural_three_fold']:.2f}, two-fold {r['share_structural_two_fold']:.2f}")
    dec = pd.DataFrame(decomposition)
    wide = dec[dec["response"] == "dispersion"].pivot(index="season", columns="component", values="value")
    low = dec[dec["response"] == "dispersion"].pivot(index="season", columns="component", values="low")
    wide["structure_low"] = low["structure"]
    print(wide[["total", "composition", "structure", "structure_low", "interaction"]].round(4).to_string())
    for r in summary:
        if r["config"] != "gbp_0.01":
            continue
        tail = "" if r["agent"] == "B_0.25" else (
            f"  better/worse {r['seasons_better']}/{r['seasons_worse']}  stops in {r['seasons_with_stop']}  "
            f"zero days {r['share_days_zero']:.2f}  wilcoxon p {r['wilcoxon_p']:.3f}  ratio {r['capital_ratio']:.3f}")
        print(f"{r['agent']:<22} typical {r['typical_capital']:.3f}{tail}")
    for r in placebo_rows:
        if r["placebo"] == "cross_season" and r["row_type"] in ("capital", "expected_delta"):
            print(f"{r['agent']:<22} {r['row_type']:<15} cross_season observed {r['observed']:>8.4f}  "
                  f"placebo {r['placebo_median']:>8.4f}  p {r['p_value']:.3f}")


if __name__ == "__main__":
    argv = sys.argv[1:]
    draws_ = int(argv[argv.index("--draws") + 1]) if "--draws" in argv else None
    run_experiment(draws_)
