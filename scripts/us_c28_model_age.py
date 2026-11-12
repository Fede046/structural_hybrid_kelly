"""Script: età del modello e tempo di calendario; sensibilità dello schema al riferimento (shk.model.model_age).

1. Sulle 19 stagioni vere di validazione confronta, sulle stesse partite, il modello congelato e quello
   ricalibrato sulla stagione precedente (us_c18): differenze appaiate e test sulle tendenze.
2. Riesegue lo schema con un riferimento diverso dalla stagione di calibrazione (la prima stagione di
   validazione dopo la calibrazione) e confronta le due varianti sulle 16 stagioni che restano.
Scrive:
- results/us_c28_model_age_seasons.csv, per stagione;
- results/us_c28_model_age_tests.csv, i test;
- results/us_c28_reference_setups.csv, dispersione e soglie dei due riferimenti per fit;
- results/us_c28_reference_seasons.csv, lo schema con i due riferimenti, per stagione × configurazione × agente;
- results/us_c28_reference_summary.csv, lo stesso per configurazione × agente.
"""

import csv
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Final

import pandas as pd

from shk.model.elo_refit import refit_module2_frame, refit_residuals
from shk.model.frozen_params import frozen_params_path, load_frozen_params
from shk.model.model_age import (
    SEASON_COLUMNS,
    TEST_COLUMNS,
    age_tests,
    dispersion,
    first_season_after,
    paired_season_records,
)
from shk.model.module2_data import build_module2_frame
from shk.model.residuals import load_model_residuals
from shk.model.season_thresholds import season_setups, summary_rows
from shk.model.two_fold_diagnosis import RUN_ARMS, diagnosis_setups, run_real_season
from shk.model.validation_run import validation_inputs

WORKERS = 5
RESULTS = Path(__file__).resolve().parents[1] / "results"
SETUP_COLUMNS: Final[tuple[str, ...]] = (
    "reference", "fit", "reference_season", "n_reference", "dispersion", "mean",
    "mean_threshold", "dispersion_threshold", "season_mean_threshold", "season_dispersion_threshold",
)
REFERENCE_SEASON_COLUMNS: Final[tuple[str, ...]] = ("reference", "season", "fit_through", "config", "agent",
                                                    "log_wealth", "n_alarms", "share_days_zero")
SUMMARY_COLUMNS: Final[tuple[str, ...]] = (
    "reference", "config", "agent", "n_seasons", "typical_capital", "seasons_better", "seasons_worse",
    "seasons_with_stop", "mean_alarms", "share_days_zero",
)


def _write(name: str, columns: tuple[str, ...], rows: list[dict]) -> None:
    with open(RESULTS / f"us_c28_{name}.csv", mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(columns), restval="", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run_experiment() -> None:
    params_path = frozen_params_path()
    params = load_frozen_params(params_path)
    frame = build_module2_frame(load_model_residuals())
    refit_data, _ = refit_residuals(WORKERS)
    season_rows = paired_season_records(frame, refit_module2_frame(refit_data))
    tests = age_tests(season_rows)
    _write("model_age_seasons", SEASON_COLUMNS, season_rows)
    _write("model_age_tests", TEST_COLUMNS, tests)

    val = validation_inputs(frame, list(params.fixed["covariates"]))
    alternative = first_season_after({s.inp.season: s.fit for s in val})
    frames = {"calibration": frame[frame["role"] == "training"],
              "first_after": frame[(frame["role"] == "validation") & frame["season"].isin(list(alternative))]}
    evaluated = [s for s in val if s.inp.season not in alternative]
    setup_rows, summary, reference_seasons = [], [], []
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        for reference, ref_frame in frames.items():
            per_date, per_season, _ = season_setups(ref_frame, params)
            diagnoses, _ = diagnosis_setups(ref_frame, params)
            to_fit = alternative if reference == "first_after" else {f: f for f in per_date}
            by_fit = [{to_fit[k]: v for k, v in d.items()} for d in (per_date, per_season, diagnoses)]
            for season, fit in to_fit.items():
                setup_rows.append({
                    "reference": reference, "fit": fit, "reference_season": season,
                    "n_reference": int(per_date[season].delta.shape[0]),
                    "dispersion": dispersion(per_date[season].delta), "mean": float(per_date[season].delta.mean()),
                    "mean_threshold": per_date[season].mean_threshold,
                    "dispersion_threshold": per_date[season].dispersion_threshold,
                    "season_mean_threshold": per_season[season].mean_threshold,
                    "season_dispersion_threshold": per_season[season].dispersion_threshold})
            n = len(evaluated)
            runs = pool.map(run_real_season, [str(params_path)] * n, [by_fit[0]] * n, [by_fit[1]] * n,
                            [by_fit[2]] * n, evaluated)
            rows = [r for season_out in runs for r in season_out]
            reference_seasons += [{"reference": reference, **r} for r in rows]
            summary += [{"reference": reference, **r} for r in summary_rows(rows, RUN_ARMS)]
    _write("reference_setups", SETUP_COLUMNS, setup_rows)
    _write("reference_seasons", REFERENCE_SEASON_COLUMNS, reference_seasons)
    _write("reference_summary", SUMMARY_COLUMNS, summary)

    pd.set_option("display.width", 220)
    df = pd.DataFrame(season_rows)
    print(df[["season", "age", "frozen_dispersion", "refit_dispersion", "dispersion_difference", "dispersion_low",
              "dispersion_high", "expected_difference", "expected_low", "expected_high"]].round(4).to_string(index=False))
    print(pd.DataFrame(tests).round(4).to_string(index=False))
    print(pd.DataFrame(setup_rows).round(3).to_string(index=False))
    s = pd.DataFrame(summary)
    print(s[s["config"] == "gbp_0.01"].round(3).to_string(index=False))


if __name__ == "__main__":
    run_experiment()
