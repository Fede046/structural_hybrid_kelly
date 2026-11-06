"""Script: lavoratori classici che scelgono l'esito (R1, R2, R3) sulle 19 stagioni di validazione.

Per ogni regola tre versioni: da solo (Kelly pieno), freno costante 0.25, schema del relatore C3
(shk.model.worker_run). Soglie dell'allarme di C3 come in us_c10; stessi seed dell'esecuzione
congelata, quindi tutto è appaiato con us_c8_3 (R1 la riproduce bit per bit). Scrive:
- results/raw/us_c11_worker_rules_raw.npz, uscite per seed (non versionato);
- results/us_c11_worker_rules_summary.csv, sintesi per agente × configurazione × stagione,
  nel formato di us_c8_3_validation_summary.csv.
Stampa la somma sulle stagioni della mediana sui seed di ln W_T per la configurazione
principale. Con --module1 dixon_coles usa il Modulo 1 Dixon-Coles (suffisso _dc). Con --seeds N
usa N seed (prova rapida, uscite in build/worker/).
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
from shk.model.scheme_run import evaluate_scheme, scheme_thresholds
from shk.model.worker_run import WORKER_ARMS, run_worker_instance
from shk.model.validation_run import CONFIG_NAMES, METRICS, SUMMARY_COLUMNS, save_raw, summary_records

WORKERS = 5


def output_paths(module1: str = MODULE1_ELO, quick: bool = False) -> tuple[Path, Path]:
    """npz delle uscite per seed e CSV di sintesi del Modulo 1."""
    repo_root = Path(__file__).resolve().parents[1]
    base = repo_root / "build" / "worker" if quick else repo_root / "results"
    raw = base if quick else base / "raw"
    return (with_module1_suffix(raw / "us_c11_worker_rules_raw.npz", module1),
            with_module1_suffix(base / "us_c11_worker_rules_summary.csv", module1))


def run_experiment(module1: str = MODULE1_ELO, n_seeds: int | None = None) -> None:
    """Soglie di C3 sul training, esecuzione sulla validazione, sintesi."""
    raw_path, csv_path = output_paths(module1, quick=n_seeds is not None)
    for p in (raw_path, csv_path):
        p.parent.mkdir(parents=True, exist_ok=True)
    params_path = frozen_params_path(module1)
    params = load_frozen_params(params_path)
    frame = build_module2_frame(load_model_residuals(module1=module1))
    thresholds = scheme_thresholds(frame[frame["role"] == "training"], params)
    result = evaluate_scheme(frame, params_path, thresholds, n_seeds=n_seeds, workers=WORKERS,
                             seed=s10_seed(module1), instance=run_worker_instance)
    save_raw(raw_path, result, WORKER_ARMS)
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(SUMMARY_COLUMNS))
        writer.writeheader()
        writer.writerows(summary_records(result, WORKER_ARMS))

    main = CONFIG_NAMES.index("gbp_0.01")
    lw, bets = METRICS.index("final_log_wealth"), METRICS.index("n_bets")
    print(f"{'agent':<10} {'sum median lnW':>15} {'sum observed lnW':>17} {'mean bets':>10}")
    for ai, agent in enumerate(WORKER_ARMS):
        seeds = result.seeds[:, main, ai]
        print(f"{agent:<10} {np.median(seeds[:, lw], axis=-1).sum():>15.4f} "
              f"{result.observed[:, main, ai, lw].sum():>17.4f} {np.mean(seeds[:, bets]):>10.1f}")


if __name__ == "__main__":
    argv = sys.argv[1:]
    seeds_ = int(argv[argv.index("--seeds") + 1]) if "--seeds" in argv else None
    run_experiment(module1_from_argv(argv), seeds_)
