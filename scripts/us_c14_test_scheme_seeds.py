"""Script: lo schema del relatore sul 2023-24 su 500 stagioni ricostruite (esplorativo).

Gli agenti A, B_0.25, C3, C3_stop, C3_and, C3_ref e C3_ref_stop giocano il 2023-24 su stagioni
ricostruite con i seed "block" dell'esecuzione unica (shk.model.scheme_test_run), oltre alla
realizzazione osservata. Scrive:
- results/raw/us_c14_test_scheme_seeds_raw.npz, uscite per seed (non versionato);
- results/us_c14_test_scheme_seeds_summary.csv, sintesi per agente × configurazione.
Stampa, per la configurazione principale, mediana e quantili 5% e 95% di ln W_T, il capitale tipico
e il confronto appaiato con B_0.25. Con --seeds N usa N seed (prova rapida, uscite in build/test_scheme/).
"""

import csv
import math
import sys
from pathlib import Path

import numpy as np

from shk.model.module1_seeds import s10_seed
from shk.model.scheme_test_run import TEST_SCHEME_ARMS, evaluate_test_scheme
from shk.model.test_run import TEST_FIT, TEST_SEASON, load_season_data
from shk.model.validation_run import CONFIG_NAMES, METRICS, SUMMARY_COLUMNS, save_raw, summary_records

WORKERS = 5


def output_paths(quick: bool = False) -> tuple[Path, Path]:
    """npz delle uscite per seed e CSV di sintesi."""
    repo_root = Path(__file__).resolve().parents[1]
    base = repo_root / "build" / "test_scheme" if quick else repo_root / "results"
    raw = base if quick else base / "raw"
    return raw / "us_c14_test_scheme_seeds_raw.npz", base / "us_c14_test_scheme_seeds_summary.csv"


def run_experiment(n_seeds: int | None = None) -> None:
    """Esegue gli agenti sulle stagioni ricostruite del 2023-24 e scrive raw e sintesi."""
    raw_path, csv_path = output_paths(quick=n_seeds is not None)
    for p in (raw_path, csv_path):
        p.parent.mkdir(parents=True, exist_ok=True)
    sd = load_season_data(TEST_SEASON, TEST_FIT)
    result = evaluate_test_scheme(sd, workers=WORKERS, seed=s10_seed(), n_seeds=n_seeds)
    save_raw(raw_path, result, TEST_SCHEME_ARMS)
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(SUMMARY_COLUMNS))
        writer.writeheader()
        writer.writerows(summary_records(result, TEST_SCHEME_ARMS))

    main = CONFIG_NAMES.index("gbp_0.01")
    lw = METRICS.index("final_log_wealth")
    b = result.seeds[0, main, TEST_SCHEME_ARMS.index("B_0.25"), lw]
    print(f"{'agent':<12} {'median lnW':>11} {'q05':>8} {'q95':>8} {'capital':>8} {'>B_0.25':>8}")
    for ai, agent in enumerate(TEST_SCHEME_ARMS):
        x = result.seeds[0, main, ai, lw]
        print(f"{agent:<12} {np.median(x):>11.4f} {np.quantile(x, 0.05):>8.3f} {np.quantile(x, 0.95):>8.3f} "
              f"{math.exp(np.median(x)):>8.3f} {np.mean(x > b):>8.2f}")


if __name__ == "__main__":
    argv = sys.argv[1:]
    seeds_ = int(argv[argv.index("--seeds") + 1]) if "--seeds" in argv else None
    run_experiment(seeds_)
