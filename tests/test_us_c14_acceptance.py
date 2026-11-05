"""Test: lo schema sul 2023-24 su stagioni ricostruite, appaiato con l'esecuzione unica."""

from pathlib import Path

import numpy as np
import pandas as pd

from shk.model.frozen_params import load_frozen_params
from shk.model.scheme_test_run import TEST_SCHEME_ARMS
from shk.model.validation_run import CONFIG_NAMES, SUMMARY_COLUMNS

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "results" / "us_c14_test_scheme_seeds_summary.csv"
TEST_RUN_CSV = REPO_ROOT / "results" / "us_c8_5_test_run.csv"


def test_summary_structure():
    df = pd.read_csv(CSV_PATH)
    assert tuple(df.columns) == SUMMARY_COLUMNS
    assert len(df) == len(CONFIG_NAMES) * len(TEST_SCHEME_ARMS)
    assert set(df["season"]) == {"2023-24"} and set(df["fit_through"]) == {"2020-21"}
    assert (df["n_seeds"] == int(load_frozen_params().fixed["n_seeds"])).all()
    assert list(df[df["config"] == "gbp_0.01"]["agent"]) == list(TEST_SCHEME_ARMS)


def test_a_and_b025_match_the_single_test_run():
    """A e B_0.25 hanno gli stessi seed dell'esecuzione unica: stesse sintesi."""
    df = pd.read_csv(CSV_PATH, dtype=str)
    ref = pd.read_csv(TEST_RUN_CSV, dtype=str)
    ref = ref[ref["row_type"] == "summary"]
    for agent in ("A", "B_0.25"):
        for config in CONFIG_NAMES:
            a = df[(df["agent"] == agent) & (df["config"] == config)].iloc[0]
            b = ref[(ref["agent"] == agent) & (ref["config"] == config)].iloc[0]
            for col in ("median_log_wealth", "q05_log_wealth", "q95_log_wealth", "mean_log_wealth", "ruin_rate",
                        "observed_log_wealth"):
                assert np.isclose(float(a[col]), float(b[col]), rtol=0.0, atol=0.0), (agent, config, col)
