"""Script: ri-parametrizzazione annuale dell'Elo e schema a riferimento fisso sulle 19 stagioni di validazione.

Seconda opzione del relatore per l'errore strutturale (shk.model.elo_refit): prima di ogni stagione
di validazione K, h e ν si ricalibrano sulla stagione precedente con quote B365. Poi B_0.25, C3_ref e
C3_ref_stop (shk.model.scheme_reference_run) girano sul modello ricalibrato, con soglie calibrate
sulle stagioni di calibrazione e gli stessi seed dell'esecuzione congelata (confronto appaiato con
us_c13). Scrive:
- results/us_c18_elo_refit_params.csv, parametri per stagione di calibrazione;
- results/us_c18_elo_refit_aging.csv, ĝ, errore atteso e log-loss per stagione, congelato e ricalibrato;
- results/us_c18_elo_refit_thresholds.csv, soglie dello schema per fit;
- results/raw/us_c18_elo_refit_raw.npz, uscite per seed (non versionato);
- results/us_c18_elo_refit_summary.csv, sintesi per agente × configurazione × stagione.
Stampa il capitale tipico per agente. Con --seeds N usa N seed (prova rapida, uscite in
build/elo_refit/).
"""

import csv
import math
import sys
from pathlib import Path

import numpy as np

from shk.model.elo_refit import (
    REFIT_AGING_COLUMNS,
    REFIT_PARAM_COLUMNS,
    refit_aging_records,
    refit_module2_frame,
    refit_param_records,
    refit_residuals,
)
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
NAMES = ("params", "aging", "thresholds", "summary")


def output_paths(quick: bool = False) -> tuple[dict[str, Path], Path]:
    """CSV per nome e npz delle uscite per seed."""
    repo_root = Path(__file__).resolve().parents[1]
    base = repo_root / "build" / "elo_refit" if quick else repo_root / "results"
    raw = base if quick else base / "raw"
    return {n: base / f"us_c18_elo_refit_{n}.csv" for n in NAMES}, raw / "us_c18_elo_refit_raw.npz"


def _write(path: Path, columns: tuple[str, ...], rows: list[dict]) -> None:
    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(columns))
        writer.writeheader()
        writer.writerows(rows)


def run_experiment(n_seeds: int | None = None) -> None:
    """Ricalibrazione, confronto dell'invecchiamento, soglie sul training, esecuzione sulla validazione."""
    csvs, raw_path = output_paths(quick=n_seeds is not None)
    for p in (*csvs.values(), raw_path):
        p.parent.mkdir(parents=True, exist_ok=True)
    params_path = frozen_params_path()
    params = load_frozen_params(params_path)
    data, fits = refit_residuals(workers=WORKERS)
    frame = refit_module2_frame(data)
    _write(csvs["params"], REFIT_PARAM_COLUMNS, refit_param_records(data, fits))
    _write(csvs["aging"], REFIT_AGING_COLUMNS, refit_aging_records(build_module2_frame(load_model_residuals()), frame))

    train = frame[frame["role"] == "training"]
    setups = reference_setups(train, params)
    _write(csvs["thresholds"], REFERENCE_THRESHOLD_COLUMNS, reference_threshold_records(train, params, setups))
    result = evaluate_scheme(frame, params_path, setups, n_seeds=n_seeds, workers=WORKERS, seed=s10_seed(),
                             instance=run_reference_instance)
    save_raw(raw_path, result, REFERENCE_ARMS)
    _write(csvs["summary"], SUMMARY_COLUMNS, summary_records(result, REFERENCE_ARMS))
    main, lw = CONFIG_NAMES.index("gbp_0.01"), METRICS.index("final_log_wealth")
    for ai, agent in enumerate(REFERENCE_ARMS):
        total = np.median(result.seeds[:, main, ai, lw], axis=-1).sum()
        print(f"{agent:<12} sum median lnW {total:9.4f}  typical capital {math.exp(total / len(result.seasons)):.3f}")


if __name__ == "__main__":
    argv = sys.argv[1:]
    seeds_ = int(argv[argv.index("--seeds") + 1]) if "--seeds" in argv else None
    run_experiment(seeds_)
