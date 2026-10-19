"""Test della stagione 2023-24 giocata come in KellyBench, con £100 000 iniziali.

I controlli sul CSV versionato girano senza dati grezzi; il ricalcolo si salta se data/raw/E0/
non contiene CSV.
"""

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shk.model.frozen_agents import AGENT_ORDER
from shk.model.kellybench_run import (
    FLOORS_GBP,
    KELLYBENCH_BANKROLL_GBP,
    KELLYBENCH_COLUMNS,
    evaluate_kellybench,
    kellybench_records,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "results" / "kellybench_2023_24.csv"
TEST_RUN_CSV = REPO_ROOT / "results" / "us_c8_5_test_run.csv"
RAW_DIR = REPO_ROOT / "data" / "raw" / "E0"


@pytest.fixture(scope="module")
def frame() -> pd.DataFrame:
    return pd.read_csv(CSV_PATH)


def test_csv_shape_and_bankroll(frame):
    assert list(frame.columns) == list(KELLYBENCH_COLUMNS)
    summary = frame[frame["row_type"] == "summary"]
    for config, floor in FLOORS_GBP:
        part = summary[summary["config"] == config]
        expected = [a for a in AGENT_ORDER if a != "E" or floor > 0.0]
        assert part["agent"].tolist() == expected
    assert (summary["initial_bankroll_gbp"] == KELLYBENCH_BANKROLL_GBP).all()
    final = KELLYBENCH_BANKROLL_GBP * np.exp(summary["final_log_wealth"])
    assert np.allclose(summary["bankroll_gbp"], final, rtol=1e-9)
    paths = frame[frame["row_type"] == "path"]
    last = paths.groupby(["config", "agent"], sort=False)["bankroll_gbp"].last()
    merged = summary.set_index(["config", "agent"])["bankroll_gbp"]
    assert np.allclose(last.loc[merged.index], merged, rtol=1e-12)


def test_without_floor_matches_the_single_test_run(frame):
    """Senza floor la log-ricchezza non dipende dalla scala: coincide con l'esecuzione unica."""
    summary = frame[(frame["row_type"] == "summary") & (frame["config"] == "none")].set_index("agent")
    test_run = pd.read_csv(TEST_RUN_CSV)
    observed = test_run[(test_run["row_type"] == "summary") & (test_run["config"] == "none")].set_index("agent")
    for agent in summary.index:
        assert math.isclose(summary.loc[agent, "final_log_wealth"], observed.loc[agent, "observed_log_wealth"],
                            rel_tol=0.0, abs_tol=1e-12)


def test_invalid_bankroll_is_rejected():
    with pytest.raises(ValueError):
        kellybench_records(None, bankroll_gbp=0.0)


def test_recomputation_matches_csv(frame):
    if not any(RAW_DIR.glob("*.csv")):
        pytest.skip("Raw E0 CSV files not available in data/raw/E0/")
    fresh = pd.DataFrame(evaluate_kellybench())
    fresh = fresh[[c for c in KELLYBENCH_COLUMNS]]
    numeric = ["bankroll_gbp", "final_log_wealth", "max_drawdown", "total_staked_gbp"]
    summary_new = fresh[fresh["row_type"] == "summary"].reset_index(drop=True)
    summary_old = frame[frame["row_type"] == "summary"].reset_index(drop=True)
    assert summary_new["agent"].tolist() == summary_old["agent"].tolist()
    for column in numeric:
        assert np.allclose(summary_new[column].astype(float), summary_old[column].astype(float), rtol=1e-12, atol=0.0)
    assert len(fresh[fresh["row_type"] == "path"]) == len(frame[frame["row_type"] == "path"])
