"""Test: lavoratore R3 con lo schema a riferimento fisso, appaiato con us_c11 e us_c13."""

from pathlib import Path

import numpy as np
import pandas as pd

from shk.model.frozen_params import load_frozen_params
from shk.model.validation_run import CONFIG_NAMES, SUMMARY_COLUMNS
from shk.model.worker_reference_run import R3_REFERENCE_ARMS

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "results" / "us_c17_r3_reference_summary.csv"
WORKER_CSV = REPO_ROOT / "results" / "us_c11_worker_rules_summary.csv"
REFERENCE_CSV = REPO_ROOT / "results" / "us_c13_scheme_reference_summary.csv"
N_SEASONS = 19


def _sum_median(df: pd.DataFrame, agent: str) -> float:
    rows = df[(df["agent"] == agent) & (df["config"] == "gbp_0.01")]
    assert len(rows) == N_SEASONS
    return float(rows["median_log_wealth"].sum())


def test_summary_structure():
    df = pd.read_csv(CSV_PATH)
    assert tuple(df.columns) == SUMMARY_COLUMNS
    assert len(df) == N_SEASONS * len(CONFIG_NAMES) * len(R3_REFERENCE_ARMS)
    assert (df["n_seeds"] == int(load_frozen_params().fixed["n_seeds"])).all()


def test_r3_brake_matches_worker_rules_run():
    """Stessi seed di us_c11: R3_brake ha le stesse sintesi."""
    df = pd.read_csv(CSV_PATH, dtype=str)
    ref = pd.read_csv(WORKER_CSV, dtype=str)
    a = df[df["agent"] == "R3_brake"].reset_index(drop=True)
    b = ref[ref["agent"] == "R3_brake"].reset_index(drop=True)
    assert len(a) == len(b)
    for col in ("season", "config", "median_log_wealth", "q05_log_wealth", "ruin_rate", "observed_log_wealth"):
        assert list(a[col]) == list(b[col]), col


def test_scheme_helps_r3_and_r3_helps_the_scheme():
    df = pd.read_csv(CSV_PATH)
    ref = pd.read_csv(REFERENCE_CSV)
    assert _sum_median(df, "R3_C3_ref_stop") > _sum_median(df, "R3_C3_ref") > _sum_median(df, "R3_brake")
    for arm in ("C3_ref", "C3_ref_stop"):
        assert _sum_median(df, f"R3_{arm}") > _sum_median(ref, arm)
    assert np.isfinite(df["median_log_wealth"]).all()
