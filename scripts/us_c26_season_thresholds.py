"""Script: lo schema con riferimento fisso e soglie dell'allarme per stagione (shk.model.season_thresholds).

Sulle 19 stagioni vere di validazione:
1. calibra per ogni fit le soglie dell'allarme con livello α sull'intera stagione, accanto a quelle
   per giornata di us_c13;
2. esegue B_0.25, C3_ref, C3_ref_stop e le due versioni con le soglie per stagione, nelle tre
   configurazioni di puntata minima, con i confronti appaiati contro il quarto di Kelly;
3. senza puntata minima, passa le due versioni nuove per il controllo placebo di us_c23.
Scrive:
- results/us_c26_season_thresholds.csv, soglie per fit;
- results/us_c26_season_thresholds_seasons.csv, per stagione × configurazione × agente;
- results/us_c26_season_thresholds_summary.csv, per configurazione × agente;
- results/us_c26_season_thresholds_placebo.csv, righe come us_c23 per le due versioni nuove.
Con --draws N usa N estrazioni placebo e scrive in build/season_thresholds/ (prova rapida).
"""

import csv
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from shk.model.frozen_params import frozen_params_path, load_frozen_params
from shk.model.module2_data import build_module2_frame
from shk.model.paired_inference import paired_statistics
from shk.model.residuals import load_model_residuals
from shk.model.season_thresholds import (
    RUN_ARMS,
    SEASON_ARMS,
    SEASON_THRESHOLD_COLUMNS,
    SEED_S26,
    run_real_season,
    run_schedule_season,
    season_setups,
    summary_rows,
)
from shk.model.timing_placebo import COLUMNS, N_DRAWS, mean_lambda, placebo_tables, run_constant_season
from shk.model.validation_run import validation_inputs

WORKERS = 5
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
    base = root / "build" / "season_thresholds" if quick else root / "results"
    return {name: base / f"us_c26_season_thresholds{suffix}.csv"
            for name, suffix in (("thresholds", ""), ("seasons", "_seasons"), ("summary", "_summary"),
                                 ("placebo", "_placebo"))}


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
    per_date, per_season, threshold_rows = season_setups(frame[frame["role"] == "training"], params)
    val = validation_inputs(frame, list(params.fixed["covariates"]))
    n, p = len(val), str(params_path)

    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        season_rows = [r for rows in pool.map(run_real_season, [p] * n, [per_date] * n, [per_season] * n, val)
                       for r in rows]
        schedules = list(pool.map(run_schedule_season, [p] * n, [per_date] * n, [per_season] * n, val))
        lams = {arm: mean_lambda(schedules, arm) for arm in SEASON_ARMS}
        constant = list(pool.map(run_constant_season, [p] * n, val, [lams] * n, [SEASON_ARMS] * n))

    summary = summary_rows(season_rows)
    df = pd.DataFrame(season_rows)
    paired = [r for r in summary if r["agent"] != "B_0.25"]
    for row, seq in zip(paired, np.random.SeedSequence([SEED_S26, 2]).spawn(len(paired))):
        rows = df[df["config"] == row["config"]]
        x = rows[rows["agent"] == row["agent"]].set_index("season")["log_wealth"]
        y = rows[rows["agent"] == "B_0.25"].set_index("season")["log_wealth"].loc[x.index]
        stats = paired_statistics(x.to_numpy(float), y.to_numpy(float), np.random.default_rng(seq))
        row.update({k: stats[k] for k in PAIRED})
    placebo_rows, _ = placebo_tables(schedules, constant, lams, draws, np.random.SeedSequence([SEED_S26, 1]),
                                     SEASON_ARMS)

    _write(paths["thresholds"], SEASON_THRESHOLD_COLUMNS, threshold_rows)
    _write(paths["seasons"], SEASON_COLUMNS, season_rows)
    _write(paths["summary"], SUMMARY_COLUMNS, summary)
    _write(paths["placebo"], COLUMNS, placebo_rows)

    for r in threshold_rows:
        print(f"fit {r['fit']}: mean {r['mean_threshold']:.2f} -> {r['season_mean_threshold']:.2f}, "
              f"dispersion {r['dispersion_threshold']:.2f} -> {r['season_dispersion_threshold']:.2f} "
              f"({r['n_decisions']} decisions)")
    for r in summary:
        if r["config"] != "gbp_0.01":
            continue
        tail = "" if r["agent"] == "B_0.25" else (
            f"  better/worse {r['seasons_better']}/{r['seasons_worse']}  stops in {r['seasons_with_stop']} seasons  "
            f"zero days {r['share_days_zero']:.2f}  sign p {r['sign_test_p']:.3f}  wilcoxon p {r['wilcoxon_p']:.3f}  "
            f"ratio {r['capital_ratio']:.3f} [{r['capital_ratio_low']:.3f}, {r['capital_ratio_high']:.3f}]")
        print(f"{r['agent']:<19} typical {r['typical_capital']:.3f}{tail}")
    for r in placebo_rows:
        if r["row_type"] in ("capital", "expected_delta", "expected_delta_within"):
            print(f"{r['agent']:<19} {r['row_type']:<22} {r['placebo']:<13} observed {r['observed']:>8.4f}  "
                  f"placebo {r['placebo_median']:>8.4f}  p {r['p_value']:.3f}")
        elif r["row_type"] == "constant":
            print(f"{r['agent']:<19} constant exposure lambda {r['mean_lambda']:.3f}: scheme {r['observed']:.3f}, "
                  f"constant {r['placebo_mean']:.3f}")
    assert set(df["agent"]) == set(RUN_ARMS)


if __name__ == "__main__":
    argv = sys.argv[1:]
    draws_ = int(argv[argv.index("--draws") + 1]) if "--draws" in argv else None
    run_experiment(draws_)
