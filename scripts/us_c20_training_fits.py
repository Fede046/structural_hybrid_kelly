"""Script: verifiche sulla scelta delle stagioni di training (Covid e fit aggiuntivo 2015-16).

Vedi shk.model.training_fits. Scrive:
- results/us_c20_training_fits_errors.csv, errori del modello per stagione nelle due verifiche;
- results/raw/us_c20_training_fits_raw.npz, uscite per seed (non versionato);
- results/us_c20_training_fits_summary.csv, sintesi dello schema a riferimento fisso con il fit
  aggiuntivo, per agente × configurazione × stagione.
Con --seeds N usa N seed (prova rapida, uscite in build/training_fits/).
"""

import csv
import sys
from pathlib import Path

from shk.model.frozen_params import frozen_params_path, load_frozen_params
from shk.model.module1_seeds import s10_seed
from shk.model.module2_data import build_module2_frame
from shk.model.residuals import load_match_frame, load_model_residuals
from shk.model.scheme_reference_run import REFERENCE_ARMS, run_reference_instance
from shk.model.scheme_run import evaluate_scheme
from shk.model.training_fits import (
    ERROR_COLUMNS,
    covid_check_frame,
    error_records,
    extra_fit_data,
    extra_fit_params,
    extra_frame_unchanged,
    extra_module2_frame,
    extra_setups,
)
from shk.model.validation_run import SUMMARY_COLUMNS, save_raw, summary_records

WORKERS = 5


def output_paths(quick: bool = False) -> tuple[Path, Path, Path]:
    """CSV degli errori, npz delle uscite per seed e CSV di sintesi."""
    repo_root = Path(__file__).resolve().parents[1]
    base = repo_root / "build" / "training_fits" if quick else repo_root / "results"
    raw = base if quick else base / "raw"
    return (base / "us_c20_training_fits_errors.csv", raw / "us_c20_training_fits_raw.npz",
            base / "us_c20_training_fits_summary.csv")


def _write(path: Path, columns: tuple[str, ...], rows: list[dict]) -> None:
    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(columns))
        writer.writeheader()
        writer.writerows(rows)


def run_experiment(n_seeds: int | None = None) -> None:
    """Fit aggiuntivo, verifica Covid, errori, schema sulla validazione."""
    err_path, raw_path, csv_path = output_paths(quick=n_seeds is not None)
    for p in (err_path, raw_path, csv_path):
        p.parent.mkdir(parents=True, exist_ok=True)
    params_path = frozen_params_path()
    params = load_frozen_params(params_path)
    df, _ = load_match_frame()
    frozen_data = load_model_residuals()
    frozen = build_module2_frame(frozen_data)
    fit = extra_fit_params(df)
    extra = extra_module2_frame(extra_fit_data(df, frozen_data, fit))
    if not extra_frame_unchanged(frozen, extra):
        raise RuntimeError("the extra fit changed seasons outside EXTRA_SEASONS")
    rows = error_records(frozen, covid_check_frame(df), extra, fit)
    _write(err_path, ERROR_COLUMNS, rows)
    for r in rows:
        if r["season"] == "all":
            print(f"{r['check']:<10} {r['model']:<16} g_hat {r['g_hat']:.4f}  expected {r['expected']:.4f}  "
                  f"log_loss {r['log_loss']:.4f}  p_home {r['p_home']:.3f}  home {r['home_rate']:.3f}", flush=True)

    setups = extra_setups(frozen, extra, params)
    result = evaluate_scheme(extra, params_path, setups, n_seeds=n_seeds, workers=WORKERS, seed=s10_seed(),
                             instance=run_reference_instance)
    save_raw(raw_path, result, REFERENCE_ARMS)
    _write(csv_path, SUMMARY_COLUMNS, summary_records(result, REFERENCE_ARMS))


if __name__ == "__main__":
    argv = sys.argv[1:]
    seeds_ = int(argv[argv.index("--seeds") + 1]) if "--seeds" in argv else None
    run_experiment(seeds_)
