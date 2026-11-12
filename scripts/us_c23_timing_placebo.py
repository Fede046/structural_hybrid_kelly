"""Script: controllo placebo sul momento degli interventi dello schema (shk.model.timing_placebo).

Sulle 19 stagioni vere di validazione, senza puntata minima:
1. esegue gli schemi di PLACEBO_ARMS con i loro riferimenti e ne estrae il calendario delle puntate;
2. confronta il capitale e il segnale dello schema con N_DRAWS calendari placebo di pari esposizione
   (permutation, shift, cross_season);
3. esegue il Kelly frazionario a λ costante uguale al λ medio di ogni schema.
Scrive:
- results/us_c23_timing_placebo.csv: per schema, righe "capital" e "delta"/"expected_delta" per
  placebo, e una riga "constant" per il riferimento a esposizione costante;
- results/us_c23_timing_placebo_seasons.csv: per schema e stagione.
Con --draws N usa N estrazioni e scrive in build/timing_placebo/ (prova rapida).
"""

import csv
import math
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from shk.model.frozen_params import frozen_params_path, load_frozen_params
from shk.model.module2_data import build_module2_frame
from shk.model.population_run import population_setups
from shk.model.residuals import load_model_residuals
from shk.model.timing_placebo import (
    COLUMNS,
    N_DRAWS,
    PLACEBO_ARMS,
    PLACEBOS,
    SEASON_COLUMNS,
    mean_lambda,
    placebo_tables,
    run_constant_season,
    run_placebo_season,
)
from shk.model.validation_run import validation_inputs

WORKERS = 5
def output_paths(quick: bool) -> tuple[Path, Path]:
    root = Path(__file__).resolve().parents[1]
    base = root / "build" / "timing_placebo" if quick else root / "results"
    return base / "us_c23_timing_placebo.csv", base / "us_c23_timing_placebo_seasons.csv"


def _write(path: Path, columns: tuple[str, ...], rows: list[dict]) -> None:
    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(columns), restval="")
        writer.writeheader()
        writer.writerows(rows)


def run_experiment(n_draws: int | None = None) -> None:
    summary_path, seasons_path = output_paths(quick=n_draws is not None)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    draws = N_DRAWS if n_draws is None else n_draws
    params_path = frozen_params_path()
    params = load_frozen_params(params_path)
    frame = build_module2_frame(load_model_residuals())
    setups = population_setups(frame[frame["role"] == "training"], params)
    val = validation_inputs(frame, list(params.fixed["covariates"]))
    n = len(val)

    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        seasons = list(pool.map(run_placebo_season, [str(params_path)] * n, [setups] * n, val))
        lams = {arm: mean_lambda(seasons, arm) for arm in PLACEBO_ARMS}
        constant = list(pool.map(run_constant_season, [str(params_path)] * n, val, [lams] * n))

    rows, season_rows = placebo_tables(seasons, constant, lams, draws)
    _write(summary_path, COLUMNS, rows)
    _write(seasons_path, SEASON_COLUMNS, season_rows)

    print(f"{'agent':<15} {'placebo':<13} {'capital':>7} {'base':>6} {'plac.':>6} {'p':>6}   "
          f"{'gap d':>8} {'p':>6}   {'gap E':>8} {'p':>6}")
    by = {(r["agent"], r["placebo"], r["row_type"]): r for r in rows}
    for arm in PLACEBO_ARMS:
        for placebo in PLACEBOS:
            c, d, e = (by[(arm, placebo, t)] for t in ("capital", "delta", "expected_delta"))
            print(f"{arm:<15} {placebo:<13} {c['observed']:>7.3f} {c['baseline_value']:>6.3f} "
                  f"{c['placebo_median']:>6.3f} {c['p_value']:>6.3f}   {d['observed']:>8.4f} {d['p_value']:>6.3f}   "
                  f"{e['observed']:>8.4f} {e['p_value']:>6.3f}")
        c = by[(arm, "constant_exposure", "constant")]
        print(f"{arm:<15} {'constant':<13} {c['observed']:>7.3f} {c['baseline_value']:>6.3f} "
              f"{c['placebo_mean']:>6.3f}  lambda {c['mean_lambda']:.3f}  better/worse "
              f"{c['seasons_better']}/{c['seasons_worse']}")
    assert math.isfinite(sum(r["observed"] for r in rows))


if __name__ == "__main__":
    argv = sys.argv[1:]
    draws_ = int(argv[argv.index("--draws") + 1]) if "--draws" in argv else None
    run_experiment(draws_)
