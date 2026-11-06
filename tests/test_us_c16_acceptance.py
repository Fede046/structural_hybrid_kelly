"""Test: Oaxaca-Blinder dello schema sull'errore atteso E_q[δ]."""

from pathlib import Path

import pandas as pd

from shk.model.oaxaca_expected import EXPECTED_ARMS, EXPECTED_COLUMNS
from shk.model.oaxaca_position import N_CHECK_SEEDS

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "results" / "us_c16_oaxaca_expected.csv"


def test_versioned_csv_structure_and_findings():
    df = pd.read_csv(CSV_PATH)
    assert tuple(df.columns) == EXPECTED_COLUMNS
    r2 = df[df["row_type"] == "r2"].groupby("response")["value"].median()
    # Le covariate spiegano molto più dell'errore atteso che di quello realizzato
    assert r2["expected"] > 5 * r2["realized"]
    diag = df[df["row_type"] == "diagnosis"].set_index("arm")
    # Finestre vicine: quasi solo composizione; contro la calibrazione: molta struttura
    assert diag.loc["C3_ed", "share_structural"] < diag.loc["C3_ref_ed", "share_structural"]
    wealth = df[df["row_type"] == "wealth"]
    assert list(wealth["arm"]) == list(EXPECTED_ARMS)
    assert (wealth["n_seeds"] == N_CHECK_SEEDS).all()
    assert len(df[df["row_type"] == "component_sd"]) == 8 and len(df[df["row_type"] == "threshold"]) == 6
