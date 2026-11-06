"""Test: agenti e supervisore dal solo loader, uscite per seed e sintesi."""

import dataclasses
import math
from pathlib import Path
from types import MappingProxyType

import numpy as np
import pandas as pd
import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.model.frozen_agents import AGENT_ORDER, build_frozen_agents, build_supervisor, check_frozen_constants
from shk.model.frozen_params import load_frozen_params
from shk.model.module2_data import build_module2_frame
from shk.model.residuals import load_model_residuals
from shk.model.validation_run import (
    METRICS,
    SEED_S10,
    SUMMARY_COLUMNS,
    certainty_equivalent,
    load_raw,
    spawn_t55_sequences,
    validation_inputs,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = REPO_ROOT / "results" / "raw" / "us_c8_3_validation_raw.npz"
SUMMARY_PATH = REPO_ROOT / "results" / "us_c8_3_validation_summary.csv"
C62_PATH = REPO_ROOT / "results" / "us_c6_2_paired_backtest.csv"


def _has_real_data() -> bool:
    return DEFAULT_DATA_DIR.is_dir() and any(DEFAULT_DATA_DIR.glob("*.csv"))


@pytest.fixture(scope="module")
def frame():
    if not _has_real_data():
        pytest.skip(f"Real data missing: no CSV in {DEFAULT_DATA_DIR}")
    return build_module2_frame(load_model_residuals())


def test_agents_and_supervisor_built_only_from_frozen_params(frame):
    """Agenti A e B_0.25; la W del supervisore viene dal file; le costanti interne sono confrontate col file."""
    params = load_frozen_params()
    check_frozen_constants(params)
    assert [a.name for a in build_frozen_agents()] == list(AGENT_ORDER) == ["A", "B_0.25"]
    val = validation_inputs(frame, list(params.fixed["covariates"]))[0]
    assert build_supervisor(params, val.inp).window == int(params.calibrated["c1_window"])
    changed = dict(params.calibrated)
    changed["c1_window"] = 60
    other = dataclasses.replace(params, calibrated=MappingProxyType(changed))
    assert build_supervisor(other, val.inp).window == 60
    bad = dict(params.fixed)
    bad["c1_n_boot"] = 500
    with pytest.raises(ValueError):
        check_frozen_constants(dataclasses.replace(params, fixed=MappingProxyType(bad)))


def test_certainty_equivalent():
    lw = np.log(np.array([1.2, 0.8, 1.0]))
    assert math.isclose(certainty_equivalent(lw, 10, 1.0), lw.mean() / 10)
    assert math.isclose(certainty_equivalent(lw, 10, 2.0), -math.log(np.mean(1 / np.exp(lw))) / 10)
    assert certainty_equivalent(np.r_[lw, -np.inf], 10, 5.0) == -math.inf


def test_spawn_t55_sequences_scheme():
    seqs = spawn_t55_sequences(19, 3, SEED_S10)
    child = np.random.SeedSequence(SEED_S10).spawn(5)[0].spawn(19)[7].spawn(3)[2]
    assert np.random.default_rng(seqs[7][2]).integers(0, 2**62) == np.random.default_rng(child).integers(0, 2**62)


def test_raw_file_seeds():
    """Ogni agente ha N_SEEDS seed per stagione e configurazione, senza valori mancanti."""
    params = load_frozen_params()
    if not RAW_PATH.exists():
        pytest.skip(f"Missing {RAW_PATH}: results/raw non è versionato (si rigenera con gli script)")
    res = load_raw(RAW_PATH)
    n_seeds = int(params.fixed["n_seeds"])
    assert res.seeds.shape == (19, 3, len(AGENT_ORDER), len(METRICS), n_seeds)
    lw = METRICS.index("final_log_wealth")
    assert not np.any(np.isnan(res.seeds[:, :, :, lw]))


def test_observed_b025_reproduces_c6_2():
    """Con F = 0, B_0.25 sulla realizzazione osservata riproduce il backtest appaiato (−10.580 su 6 234 puntate)."""
    if not RAW_PATH.exists():
        pytest.skip(f"Missing {RAW_PATH}: results/raw non è versionato (si rigenera con gli script)")
    res = load_raw(RAW_PATH)
    c62 = pd.read_csv(C62_PATH)
    ref = c62[(c62["row_type"] == "summary") & (c62["config"] == "none") & (c62["agent"] == "B_0.25")].iloc[0]
    b = AGENT_ORDER.index("B_0.25")
    total = float(res.observed[:, 0, b, METRICS.index("final_log_wealth")].sum())
    bets = int(res.observed[:, 0, b, METRICS.index("n_bets")].sum())
    assert math.isclose(total, float(ref["sum_final_log_wealth"]), rel_tol=1e-12)
    assert bets == int(ref["n_bets"]) == 6234
    assert round(total, 3) == -10.580


def test_summary_csv_structure():
    df = pd.read_csv(SUMMARY_PATH)
    assert tuple(df.columns) == SUMMARY_COLUMNS
    assert set(df["row_type"]) == {"summary"}
    assert len(df) == 19 * 3 * len(AGENT_ORDER)
    assert (df["n_seeds"] == int(load_frozen_params().fixed["n_seeds"])).all()
