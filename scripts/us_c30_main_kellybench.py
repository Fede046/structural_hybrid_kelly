"""Script: la versione principale dello schema sulla stagione 2023-24 di KellyBench (esplorativo).

La stagione di test era stata sbloccata una volta sola, e lo schema è stato costruito dopo; le versioni
iniziali vi sono state eseguite in us_c14. Qui vi gioca, una volta, la versione principale con due
varianti (TEST_ARMS di shk.model.main_version: M, M_clear, M_day) accanto ad A e B_0.25, con i
parametri congelati, il fit 2020-21 e le soglie calibrate sul training, nessuna scelta sui dati del
2023-24. Stagione vera e N stagioni ricostruite con i seed "block" dell'esecuzione unica, gli stessi di
us_c14: A e B_0.25 coincidono con quell'esecuzione e i confronti sono appaiati.

Scrive results/raw/us_c30_main_kellybench_raw.npz (non versionato) e
results/us_c30_main_kellybench_summary.csv (righe "summary" di validation_run.summary_records).
Con --seeds N usa N seed e scrive in build/main_kellybench/ (prova rapida).
"""

import csv
import math
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from shk.model.frozen_agents import check_frozen_constants
from shk.model.frozen_params import load_frozen_params
from shk.model.main_version import TEST_ARMS, main_setups, run_test_chunk, run_test_instance
from shk.model.module1_seeds import s10_seed
from shk.model.module2_data import build_module2_frame
from shk.model.season_bootstrap import season_block_length
from shk.model.test_run import TEST_FIT, TEST_SEASON, load_season_data, season_params_path, t58_sequences
from shk.model.validation_run import (
    CONFIG_NAMES,
    METRICS,
    SUMMARY_COLUMNS,
    ValidationResult,
    save_raw,
    summary_records,
)

WORKERS = 5
CHUNK = 25
BANKROLL_GBP = 100_000.0


def output_paths(quick: bool) -> tuple[Path, Path]:
    root = Path(__file__).resolve().parents[1]
    base = root / "build" / "main_kellybench" if quick else root / "results"
    raw = base if quick else base / "raw"
    return raw / "us_c30_main_kellybench_raw.npz", base / "us_c30_main_kellybench_summary.csv"


def run_experiment(n_seeds: int | None = None) -> None:
    raw_path, csv_path = output_paths(quick=n_seeds is not None)
    for p in (raw_path, csv_path):
        p.parent.mkdir(parents=True, exist_ok=True)
    sd = load_season_data(TEST_SEASON, TEST_FIT)
    params_path = str(season_params_path(sd))
    params = load_frozen_params(params_path)
    check_frozen_constants(params)
    frame = build_module2_frame(sd.residuals, devig_method=sd.devig_method)
    setups = main_setups(frame[frame["role"] == "training"], params)
    total = int(params.fixed["n_seeds"])
    n = total if n_seeds is None else n_seeds
    seqs = t58_sequences(s10_seed())[0].spawn(total)[:n]
    l_pw = season_block_length(sd.inp)
    parts = [seqs[i:i + CHUNK] for i in range(0, len(seqs), CHUNK)]
    args = [(params_path, setups, sd.inp, sd.fit, p, l_pw, sd.devig_method) for p in parts]
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        seeds = np.concatenate(list(pool.map(run_test_chunk, *zip(*args))), axis=-1)
    observed = run_test_instance(params, setups, sd.inp, sd.fit, sd.devig_method)
    result = ValidationResult((sd.season,), (sd.fit,), np.array([np.unique(sd.inp.dates).shape[0]]),
                              np.array([l_pw]), seeds[None], observed[None])
    save_raw(raw_path, result, TEST_ARMS)
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(SUMMARY_COLUMNS))
        writer.writeheader()
        writer.writerows(summary_records(result, TEST_ARMS))

    main, lw = CONFIG_NAMES.index("gbp_0.01"), METRICS.index("final_log_wealth")
    zero = METRICS.index("share_lambda_zero")
    b = seeds[main, TEST_ARMS.index("B_0.25"), lw]
    print(f"{'agent':<8} {'real £':>9} {'median £':>9} {'q05 £':>9} {'q95 £':>9} {'>B_0.25':>8} {'zero days':>9}")
    for ai, agent in enumerate(TEST_ARMS):
        x = seeds[main, ai, lw]
        obs = observed[main, ai, lw]
        print(f"{agent:<8} {BANKROLL_GBP * math.exp(obs):>9.0f} {BANKROLL_GBP * math.exp(np.median(x)):>9.0f} "
              f"{BANKROLL_GBP * math.exp(np.quantile(x, 0.05)):>9.0f} "
              f"{BANKROLL_GBP * math.exp(np.quantile(x, 0.95)):>9.0f} {np.mean(x > b):>8.2f} "
              f"{observed[main, ai, zero]:>9.3f}")


if __name__ == "__main__":
    argv = sys.argv[1:]
    run_experiment(int(argv[argv.index("--seeds") + 1]) if "--seeds" in argv else None)
