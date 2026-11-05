"""Script: schema del relatore con riferimento fisso (C3_ref, C3_ref_stop) sulle 19 stagioni di validazione.

L'allarme ANOVA e la diagnosi di Oaxaca confrontano le ultime W partite con la stagione di
calibrazione del Modulo 1, invece che con le W precedenti (shk.model.scheme_reference_run). Soglie
calibrate sul training, poi esecuzione appaiata con gli stessi seed dell'esecuzione congelata, con
B_0.25 come riferimento. Scrive:
- results/us_c13_scheme_reference_thresholds.csv, soglie per fit;
- results/raw/us_c13_scheme_reference_raw.npz, uscite per seed (non versionato);
- results/us_c13_scheme_reference_summary.csv, sintesi per agente × configurazione × stagione.
Stampa la somma sulle stagioni della mediana sui seed di ln W_T, gli allarmi medi e la quota di
date con λ = 0, per la configurazione principale. Con --seeds N usa N seed (prova rapida, uscite in
build/scheme_reference/).
"""

import csv
import sys
from pathlib import Path

import numpy as np

from shk.model.frozen_params import frozen_params_path, load_frozen_params
from shk.model.module1_seeds import s10_seed
from shk.model.module2_data import build_module2_frame
from shk.model.residuals import load_model_residuals
from shk.model.scheme_reference_run import (
    REFERENCE_ARMS,
    REFERENCE_THRESHOLD_COLUMNS,
    reference_setups,
    reference_threshold_records,
    run_reference_instance,
)
from shk.model.scheme_run import evaluate_scheme
from shk.model.validation_run import CONFIG_NAMES, METRICS, SUMMARY_COLUMNS, save_raw, summary_records

WORKERS = 5


def output_paths(quick: bool = False) -> tuple[Path, Path, Path]:
    """CSV delle soglie, npz delle uscite per seed e CSV di sintesi."""
    repo_root = Path(__file__).resolve().parents[1]
    base = repo_root / "build" / "scheme_reference" if quick else repo_root / "results"
    raw = base if quick else base / "raw"
    return (base / "us_c13_scheme_reference_thresholds.csv", raw / "us_c13_scheme_reference_raw.npz",
            base / "us_c13_scheme_reference_summary.csv")


def run_experiment(n_seeds: int | None = None) -> None:
    """Soglie sul training, esecuzione sulla validazione, sintesi."""
    thr_path, raw_path, csv_path = output_paths(quick=n_seeds is not None)
    for p in (thr_path, raw_path, csv_path):
        p.parent.mkdir(parents=True, exist_ok=True)
    params_path = frozen_params_path()
    params = load_frozen_params(params_path)
    frame = build_module2_frame(load_model_residuals())
    train = frame[frame["role"] == "training"]
    setups = reference_setups(train, params)
    with open(thr_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(REFERENCE_THRESHOLD_COLUMNS))
        writer.writeheader()
        writer.writerows(reference_threshold_records(train, params, setups))

    result = evaluate_scheme(frame, params_path, setups, n_seeds=n_seeds, workers=WORKERS, seed=s10_seed(),
                             instance=run_reference_instance)
    save_raw(raw_path, result, REFERENCE_ARMS)
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(SUMMARY_COLUMNS))
        writer.writeheader()
        writer.writerows(summary_records(result, REFERENCE_ARMS))

    main = CONFIG_NAMES.index("gbp_0.01")
    lw, alarms, zero = (METRICS.index(m) for m in ("final_log_wealth", "n_alarms", "share_lambda_zero"))
    print(f"{'agent':<12} {'sum median lnW':>15} {'sum observed lnW':>17} {'mean alarms':>12} {'share lam=0':>11}")
    for ai, agent in enumerate(REFERENCE_ARMS):
        seeds = result.seeds[:, main, ai]
        print(f"{agent:<12} {np.median(seeds[:, lw], axis=-1).sum():>15.4f} "
              f"{result.observed[:, main, ai, lw].sum():>17.4f} {np.nanmean(seeds[:, alarms]):>12.3f} "
              f"{np.nanmean(seeds[:, zero]):>11.4f}")


if __name__ == "__main__":
    argv = sys.argv[1:]
    seeds_ = int(argv[argv.index("--seeds") + 1]) if "--seeds" in argv else None
    run_experiment(seeds_)
