"""Test di accettazione: DiD, placebo, Ñopo e supporto comune."""

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.model.covariate_inspection import derive_specification
from shk.model.did_support import DID_SUPPORT_CSV_COLUMNS, evaluate_did_support, spawn_t49_generators
from shk.model.known_scenarios import add_no_objective_flag
from shk.model.module2_data import build_module2_frame
from shk.model.residuals import load_model_residuals
from shk.stats.oaxaca_synthetic import SEED_S8

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "results" / "us_c7_4_did_support.csv"
PNG_PATH = REPO_ROOT / "thesis" / "figures" / "us_c7_4_did_support.png"


def _has_real_data() -> bool:
    return DEFAULT_DATA_DIR.is_dir() and any(DEFAULT_DATA_DIR.glob("*.csv"))


def test_csv_structure_and_nopo_identity():
    df = pd.read_csv(CSV_PATH)
    assert tuple(df.columns) == DID_SUPPORT_CSV_COLUMNS
    counts = df["row_type"].value_counts().to_dict()
    assert counts["did"] == 23 and counts["placebo"] == 22
    nopo = df[df["row_type"] == "nopo"]
    parts = nopo["out_of_support_a"] + nopo["out_of_support_b"] + nopo["composition"] + nopo["structure"]
    assert ((parts - nopo["total"]).abs() <= 1e-12).all()
    assert set(nopo["scenario"]) == {"1_transition", "3_end_season"}
    assert PNG_PATH.is_file() and PNG_PATH.stat().st_size > 0


def test_spawn_t49_generators_scheme():
    boot, placebo = spawn_t49_generators(["a", "b", "c"], SEED_S8)
    assert len(boot) == 4 and len(placebo) == 3
    child = np.random.SeedSequence(SEED_S8).spawn(5)[4].spawn(2)[1].spawn(3)[2]
    assert placebo[2].integers(0, 2**62) == np.random.default_rng(child).integers(0, 2**62)


def test_recalculation_from_real_data_matches_csv():
    if not _has_real_data():
        pytest.skip(f"Real data missing: no CSV in {DEFAULT_DATA_DIR}")
    data = load_model_residuals()
    frame = add_no_objective_flag(build_module2_frame(data), data.df)
    spec = derive_specification(frame[frame["role"] == "training"])
    records = evaluate_did_support(frame, spec.covariates, data.df, seed=SEED_S8)
    df = pd.read_csv(CSV_PATH, dtype=str, keep_default_na=False)
    assert len(df) == len(records)
    for (_, row), rec in zip(df.iterrows(), records):
        for col in DID_SUPPORT_CSV_COLUMNS:
            val = rec[col]
            if isinstance(val, float):
                assert math.isclose(float(row[col]), val, rel_tol=1e-12, abs_tol=1e-15), col
            else:
                assert row[col] == str(val), col
