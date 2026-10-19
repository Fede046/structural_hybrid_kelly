"""Test di accettazione: Modulo 2 su finestre scorrevoli."""

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.model.covariate_inspection import MODULE2_WINDOWS, derive_specification
from shk.model.module2 import MODULE2_CI_COLUMNS, evaluate_module2, module2_record_columns
from shk.model.module2_data import build_module2_frame
from shk.model.residuals import load_model_residuals
from shk.stats.oaxaca import TWOFOLD_REFERENCES
from shk.stats.oaxaca_synthetic import SEED_S8

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "results" / "us_c7_3_module2.csv"
CI_PATH = REPO_ROOT / "results" / "us_c7_3_module2_ci.csv"
PNG_PATH = REPO_ROOT / "thesis" / "figures" / "us_c7_3_module2.png"
FINAL_COVARIATES = ("log_odds_ratio", "market_entropy", "flag_promoted", "position", "model_entropy")


def _has_real_data() -> bool:
    return DEFAULT_DATA_DIR.is_dir() and any(DEFAULT_DATA_DIR.glob("*.csv"))


@pytest.fixture(scope="module")
def versioned():
    return pd.read_csv(CSV_PATH, dtype=str, keep_default_na=False), pd.read_csv(CI_PATH, dtype=str, keep_default_na=False)


def test_csv_structure(versioned):
    """Una riga per stagione x data x W, colonne prescritte, 22 stagioni e 4 W."""
    main, ci = versioned
    assert tuple(main.columns) == module2_record_columns(FINAL_COVARIATES)
    assert tuple(ci.columns) == MODULE2_CI_COLUMNS
    assert main["season"].nunique() == 22
    assert sorted(main["window"].astype(int).unique()) == list(MODULE2_WINDOWS)
    assert not main.duplicated(["season", "decision_date", "window"]).any()
    counts = main.groupby("window").size()
    assert counts.nunique() == 1
    assert PNG_PATH.is_file() and PNG_PATH.stat().st_size > 0


def test_components_sum_to_total_in_csv(versioned):
    """Per ogni data e W attivi le componenti sommano al totale entro 1e-12."""
    main, _ = versioned
    act = main[main["state"] == "active"]
    total = act["total"].astype(float)
    three = act["compositional"].astype(float) + act["structural"].astype(float) + act["interaction"].astype(float)
    assert (three - total).abs().max() <= 1e-12
    for r in TWOFOLD_REFERENCES:
        two = act[f"explained_{r}"].astype(float) + act[f"unexplained_{r}"].astype(float)
        assert (two - total).abs().max() <= 1e-12


def test_recalculation_subset_matches_csv(versioned):
    """Ricalcolo di 2000-01, 2002-03 e 2003-04 con W = 80, dati reali: righe e intervalli uguali."""
    if not _has_real_data():
        pytest.skip(f"Real data missing: no CSV in {DEFAULT_DATA_DIR}")
    main, ci = versioned
    data = load_model_residuals()
    frame = build_module2_frame(data)
    spec = derive_specification(frame[frame["role"] == "training"])
    assert spec.covariates == FINAL_COVARIATES
    seasons = ["2000-01", "2002-03", "2003-04"]
    records, ci_records = evaluate_module2(frame[frame["season"].isin(seasons)], spec.covariates,
                                           seed=SEED_S8, windows=(80,))
    sel = main[main["season"].isin(seasons) & (main["window"] == "80")]
    sel_ci = ci[ci["season"].isin(seasons) & (ci["window"] == "80")]
    assert len(sel) == len(records) and len(sel_ci) == len(ci_records)
    for rows, recs in ((sel, records), (sel_ci, ci_records)):
        for (_, row), rec in zip(rows.iterrows(), recs):
            for col, val in rec.items():
                if isinstance(val, float):
                    assert math.isclose(float(row[col]), val, rel_tol=1e-12, abs_tol=1e-15), col
                else:
                    assert row[col] == str(val), col
