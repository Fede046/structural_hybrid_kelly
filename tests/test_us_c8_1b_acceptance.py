"""Test di accettazione di T52 sul CSV dell'esecuzione di prova sulle stagioni di training."""

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.model.covariate_inspection import MODULE2_WINDOWS, derive_specification
from shk.model.module2_data import build_module2_frame
from shk.model.module3_synthetic import SEED_S9
from shk.model.paired_backtest import CONFIGURATIONS
from shk.model.residuals import load_model_residuals
from shk.model.training_agents import (
    TRAINING_AGENTS_CSV_COLUMNS,
    evaluate_training_agents,
    spawn_t52_generators,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "results" / "us_c8_1b_agents_training.csv"
TRAINING = ["2000-01", "2010-11", "2020-21"]
AGENTS_F0 = ["A", "B_0.25", "B_0.10", "D_ADWIN", "D_PH", "C0", "C1", "C2_global", "C2"]


def _has_real_data() -> bool:
    return DEFAULT_DATA_DIR.is_dir() and any(DEFAULT_DATA_DIR.glob("*.csv"))


def test_csv_structure_only_training_seasons():
    df = pd.read_csv(CSV_PATH)
    assert tuple(df.columns) == TRAINING_AGENTS_CSV_COLUMNS
    seasons = df[df["row_type"] == "season"]
    assert sorted(set(seasons["season"])) == TRAINING
    for config, f in CONFIGURATIONS:
        expected = AGENTS_F0 + (["E"] if f > 0 else [])
        for s in TRAINING:
            rows = seasons[(seasons["config"] == config) & (seasons["season"] == s)]
            assert list(rows["agent"]) == expected
    assert (seasons["window"] == 80).all() and (seasons["kappa"] == 0.5).all()
    thr = df[df["row_type"] == "threshold"]
    assert len(thr) == len(TRAINING) * len(MODULE2_WINDOWS) * 4
    assert sorted(set(thr["season"])) == TRAINING


def test_c0_equals_b025_on_csv():
    """C0 coincide con B_0.25 entro 1e-12 in ogni stagione e configurazione."""
    seasons = pd.read_csv(CSV_PATH).query("row_type == 'season'")
    for (config, s), g in seasons.groupby(["config", "season"]):
        c0 = g[g["agent"] == "C0"].iloc[0]
        b = g[g["agent"] == "B_0.25"].iloc[0]
        assert abs(c0["final_wealth"] - b["final_wealth"]) <= 1e-12
        assert abs(c0["max_drawdown"] - b["max_drawdown"]) <= 1e-12
        assert c0["n_bets"] == b["n_bets"]


def test_spawn_t52_generators_scheme():
    gens = spawn_t52_generators(TRAINING, SEED_S9)
    assert len(gens) == len(TRAINING) * len(MODULE2_WINDOWS) * 4
    child = np.random.SeedSequence(SEED_S9).spawn(5)[2].spawn(3)[1].spawn(4)[2].spawn(4)[3]
    assert gens[("2010-11", 120, 3)].integers(0, 2**62) == np.random.default_rng(child).integers(0, 2**62)


def test_recalculation_from_real_data_matches_csv():
    if not _has_real_data():
        pytest.skip(f"Real data missing: no CSV in {DEFAULT_DATA_DIR}")
    frame = build_module2_frame(load_model_residuals())
    train = frame[frame["role"] == "training"]
    records = evaluate_training_agents(train, derive_specification(train).covariates)
    df = pd.read_csv(CSV_PATH, dtype=str, keep_default_na=False)
    assert len(df) == len(records)
    for (_, row), rec in zip(df.iterrows(), records):
        for col in TRAINING_AGENTS_CSV_COLUMNS:
            val = rec[col]
            if isinstance(val, float) and not isinstance(val, bool):
                if math.isinf(val):
                    assert float(row[col]) == val, col
                else:
                    assert math.isclose(float(row[col]), val, rel_tol=1e-12, abs_tol=1e-15), col
            else:
                assert row[col] == str(val), col
