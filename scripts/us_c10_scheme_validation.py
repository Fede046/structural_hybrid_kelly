"""Script: schema del relatore (C3, C3_stop) sulle 19 stagioni di validazione.

Soglie dell'allarme ANOVA calibrate sul training (shk.model.scheme_run), poi esecuzione
appaiata con gli stessi seed dell'esecuzione congelata, con B_0.25 e C1 come riferimento.
Non tocca config/frozen_params.toml né le uscite di us_c8_3. Scrive:
- results/us_c10_scheme_thresholds.csv, soglie per fit;
- results/raw/us_c10_scheme_validation_raw.npz, uscite per seed (non versionato);
- results/us_c10_scheme_validation_summary.csv, sintesi per agente × configurazione × stagione,
  nel formato di us_c8_3_validation_summary.csv.
Stampa la somma sulle stagioni della mediana sui seed di ln W_T e gli allarmi medi, per la
configurazione principale. Con --module1 dixon_coles usa il Modulo 1 Dixon-Coles e scrive le
uscite con il suffisso _dc. Con --seeds N usa N seed (prova rapida, uscite in build/scheme/).
"""

import csv
import sys
from pathlib import Path

import numpy as np

from shk.model.frozen_params import frozen_params_path, load_frozen_params
from shk.model.module1 import MODULE1_ELO, module1_from_argv, with_module1_suffix
from shk.model.module1_seeds import s10_seed
from shk.model.module2_data import build_module2_frame
from shk.model.residuals import load_model_residuals
from shk.model.scheme_run import SCHEME_ARMS, THRESHOLD_COLUMNS, evaluate_scheme, scheme_thresholds, threshold_records
from shk.model.validation_run import CONFIG_NAMES, METRICS, SUMMARY_COLUMNS, save_raw, summary_records

WORKERS = 5


def output_paths(module1: str = MODULE1_ELO, quick: bool = False) -> tuple[Path, Path, Path]:
    """CSV delle soglie, npz delle uscite per seed e CSV di sintesi del Modulo 1."""
    repo_root = Path(__file__).resolve().parents[1]
    base = repo_root / "build" / "scheme" if quick else repo_root / "results"
    raw = base if quick else base / "raw"
    return (with_module1_suffix(base / "us_c10_scheme_thresholds.csv", module1),
            with_module1_suffix(raw / "us_c10_scheme_validation_raw.npz", module1),
            with_module1_suffix(base / "us_c10_scheme_validation_summary.csv", module1))


def run_experiment(module1: str = MODULE1_ELO, n_seeds: int | None = None) -> None:
    """Soglie sul training, esecuzione sulla validazione, sintesi."""
    thr_path, raw_path, csv_path = output_paths(module1, quick=n_seeds is not None)
    for p in (thr_path, raw_path, csv_path):
        p.parent.mkdir(parents=True, exist_ok=True)
    params_path = frozen_params_path(module1)
    params = load_frozen_params(params_path)
    frame = build_module2_frame(load_model_residuals(module1=module1))
    train = frame[frame["role"] == "training"]
    thresholds = scheme_thresholds(train, params)
    with open(thr_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(THRESHOLD_COLUMNS))
        writer.writeheader()
        writer.writerows(threshold_records(train, params, thresholds))

    result = evaluate_scheme(frame, params_path, thresholds, n_seeds=n_seeds, workers=WORKERS,
                             seed=s10_seed(module1))
    save_raw(raw_path, result)
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(SUMMARY_COLUMNS))
        writer.writeheader()
        writer.writerows(summary_records(result, SCHEME_ARMS))

    main = CONFIG_NAMES.index("gbp_0.01")
    lw, alarms, zero = (METRICS.index(m) for m in ("final_log_wealth", "n_alarms", "share_lambda_zero"))
    print(f"{'agent':<8} {'sum median lnW':>15} {'sum observed lnW':>17} {'mean alarms':>12} {'share lam=0':>11}")
    for ai, agent in enumerate(SCHEME_ARMS):
        seeds = result.seeds[:, main, ai]
        print(f"{agent:<8} {np.median(seeds[:, lw], axis=-1).sum():>15.4f} "
              f"{result.observed[:, main, ai, lw].sum():>17.4f} {np.nanmean(seeds[:, alarms]):>12.3f} "
              f"{np.nanmean(seeds[:, zero]):>11.4f}")


if __name__ == "__main__":
    argv = sys.argv[1:]
    seeds_ = int(argv[argv.index("--seeds") + 1]) if "--seeds" in argv else None
    run_experiment(module1_from_argv(argv), seeds_)
