"""Script: lavoratore R3 (esito più probabile) con lo schema a riferimento fisso, sulle 19 stagioni di validazione.

Versioni R3_brake, R3_C3_ref e R3_C3_ref_stop (shk.model.worker_reference_run), con gli stessi seed
dell'esecuzione congelata. Scrive:
- results/raw/us_c17_r3_reference_raw.npz, uscite per seed (non versionato);
- results/us_c17_r3_reference_summary.csv, sintesi per agente × configurazione × stagione.
Stampa la somma sulle stagioni della mediana sui seed di ln W_T e il capitale tipico. Con --seeds N
usa N seed (prova rapida, uscite in build/r3_reference/).
"""

import csv
import math
import sys
from pathlib import Path

import numpy as np

from shk.model.frozen_params import frozen_params_path, load_frozen_params
from shk.model.module1_seeds import s10_seed
from shk.model.module2_data import build_module2_frame
from shk.model.residuals import load_model_residuals
from shk.model.scheme_reference_run import reference_setups
from shk.model.scheme_run import evaluate_scheme
from shk.model.validation_run import CONFIG_NAMES, METRICS, SUMMARY_COLUMNS, save_raw, summary_records
from shk.model.worker_reference_run import R3_REFERENCE_ARMS, run_r3_reference_instance

WORKERS = 5


def output_paths(quick: bool = False) -> tuple[Path, Path]:
    """npz delle uscite per seed e CSV di sintesi."""
    repo_root = Path(__file__).resolve().parents[1]
    base = repo_root / "build" / "r3_reference" if quick else repo_root / "results"
    raw = base if quick else base / "raw"
    return raw / "us_c17_r3_reference_raw.npz", base / "us_c17_r3_reference_summary.csv"


def run_experiment(n_seeds: int | None = None) -> None:
    """Soglie sul training, esecuzione sulla validazione, sintesi."""
    raw_path, csv_path = output_paths(quick=n_seeds is not None)
    for p in (raw_path, csv_path):
        p.parent.mkdir(parents=True, exist_ok=True)
    params_path = frozen_params_path()
    params = load_frozen_params(params_path)
    frame = build_module2_frame(load_model_residuals())
    setups = reference_setups(frame[frame["role"] == "training"], params)
    result = evaluate_scheme(frame, params_path, setups, n_seeds=n_seeds, workers=WORKERS, seed=s10_seed(),
                             instance=run_r3_reference_instance)
    save_raw(raw_path, result, R3_REFERENCE_ARMS)
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(SUMMARY_COLUMNS))
        writer.writeheader()
        writer.writerows(summary_records(result, R3_REFERENCE_ARMS))
    main, lw = CONFIG_NAMES.index("gbp_0.01"), METRICS.index("final_log_wealth")
    for ai, agent in enumerate(R3_REFERENCE_ARMS):
        total = np.median(result.seeds[:, main, ai, lw], axis=-1).sum()
        print(f"{agent:<16} sum median lnW {total:9.4f}  typical capital {math.exp(total / len(result.seasons)):.3f}")


if __name__ == "__main__":
    argv = sys.argv[1:]
    seeds_ = int(argv[argv.index("--seeds") + 1]) if "--seeds" in argv else None
    run_experiment(seeds_)
