"""Test di T63 (US-C9.3): metodo di de-vigging come parametro, Shin uguale a T55, T56 e T58, tabella completa."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.market.devig import DEVIG_METHOD_NAMES, devig_odds_ratio, devig_power, devig_probabilities, devig_shin
from shk.model.devig_runs import test_raw_path as season_raw_path
from shk.model.devig_runs import validation_raw_path
from shk.model.frozen_agents import AGENT_ORDER
from shk.model.module2_data import build_module2_frame
from shk.model.residuals import load_model_residuals
from shk.model.scoring import ALL_DEVIG_METHODS
from shk.model.validation_run import CONFIG_NAMES, load_raw

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW = REPO_ROOT / "results" / "raw"
CSV_PATH = REPO_ROOT / "results" / "us_c9_3_devig_sensitivity.csv"
PNG_PATH = REPO_ROOT / "thesis" / "figures" / "us_c9_3_devig_sensitivity.png"


def _has_real_data() -> bool:
    return DEFAULT_DATA_DIR.is_dir() and any(DEFAULT_DATA_DIR.glob("*.csv"))


def test_devig_probabilities_by_name():
    """Stessi q delle funzioni dei metodi; q sommano a 1; metodo sconosciuto rifiutato."""
    odds = np.array([[2.1, 3.4, 3.6], [1.5, 4.2, 6.5], [3.0, 3.1, 2.5]])
    assert DEVIG_METHOD_NAMES == ALL_DEVIG_METHODS
    assert np.array_equal(devig_probabilities(odds, "shin"), devig_shin(odds)[0])
    assert np.array_equal(devig_probabilities(odds, "power"), devig_power(odds)[0])
    assert np.array_equal(devig_probabilities(odds, "odds_ratio"), devig_odds_ratio(odds)[0])
    for method in DEVIG_METHOD_NAMES:
        assert np.allclose(devig_probabilities(odds, method).sum(axis=1), 1.0, atol=1e-12)
    with pytest.raises(ValueError, match="Unknown devig method"):
        devig_probabilities(odds, "basic")


def test_module2_frame_with_devig_method():
    """Dati reali: Shin esplicito uguale al default; con un altro metodo δ cambia e shin_z è NaN."""
    if not _has_real_data():
        pytest.skip(f"Real data missing: no CSV in {DEFAULT_DATA_DIR}")
    data = load_model_residuals()
    default = build_module2_frame(data)
    pd.testing.assert_frame_equal(default, build_module2_frame(data, devig_method="shin"))
    prop = build_module2_frame(data, devig_method="proportional")
    assert prop["shin_z"].isna().all()
    assert np.abs(prop["delta"] - default["delta"]).max() > 0.0
    for col in ("season", "Date", "HomeTeam", "AwayTeam", "p_home", "odds_home", "log_odds_ratio", "position"):
        assert prop[col].equals(default[col])


@pytest.mark.parametrize("ours, theirs", [
    (validation_raw_path("shin"), RAW / "us_c8_3_validation_raw.npz"),
    (season_raw_path("shin"), RAW / "us_c8_5_test_raw.npz"),
    (season_raw_path("shin", iid=True), RAW / "us_c8_5_test_raw_iid.npz"),
])
def test_shin_runs_equal_t55_and_t58(ours, theirs):
    """Con Shin le uscite per seed e la realizzazione osservata coincidono con T55 e T58 entro 1e-12."""
    if not ours.exists() or not theirs.exists():
        pytest.skip(f"Missing {ours} or {theirs}")
    a, b = load_raw(ours), load_raw(theirs)
    assert a.seasons == b.seasons and np.array_equal(a.l_pw, b.l_pw)
    for x, y in ((a.seeds, b.seeds), (a.observed, b.observed)):
        assert np.array_equal(np.isnan(x), np.isnan(y))
        assert np.nanmax(np.abs(x - y)) <= 1e-12


def test_shin_comparisons_equal_t56_and_t58():
    """Con Shin i confronti della tabella coincidono con T56 (intervallo block) e T58 entro 1e-12."""
    if not CSV_PATH.exists():
        pytest.skip(f"Missing {CSV_PATH}: run scripts/us_c9_3_devig_sensitivity.py")
    df = pd.read_csv(CSV_PATH)
    shin = df[(df["row_type"] == "comparison") & (df["method"] == "shin")]
    keys = ["config", "comparison", "metric"]
    t56 = pd.read_csv(REPO_ROOT / "results" / "us_c8_4_comparisons.csv")
    m = shin[shin["dataset"] == "validation"].merge(t56[t56["row_type"] == "comparison"], on=keys, suffixes=("", "_ref"))
    assert len(m) == 160
    assert np.nanmax(np.abs(m["estimate"] - m["estimate_ref"])) <= 1e-12
    assert np.nanmax(np.abs(m["ci_low"] - m["ci_block_low"])) <= 1e-12
    assert np.nanmax(np.abs(m["ci_high"] - m["ci_block_high"])) <= 1e-12
    t58 = pd.read_csv(REPO_ROOT / "results" / "us_c8_5_test_run.csv")
    m = shin[shin["dataset"] == "test"].merge(t58[t58["row_type"] == "comparison"], on=keys, suffixes=("", "_ref"))
    assert len(m) == 160
    for col in ("estimate", "ci_low", "ci_high"):
        assert np.nanmax(np.abs(m[col] - m[f"{col}_ref"])) <= 1e-12


def test_table_covers_methods_agents_configs():
    """La tabella copre i cinque metodi, tutti gli agenti e le tre configurazioni, su validazione e test."""
    if not CSV_PATH.exists():
        pytest.skip(f"Missing {CSV_PATH}: run scripts/us_c9_3_devig_sensitivity.py")
    df = pd.read_csv(CSV_PATH)
    agents = df[df["row_type"] == "agent"]
    assert set(agents["method"]) == set(DEVIG_METHOD_NAMES)
    assert set(agents["dataset"]) == {"validation", "test"}
    assert set(agents["config"]) == set(CONFIG_NAMES)
    assert set(agents["agent"]) == set(AGENT_ORDER)
    counts = agents.groupby(["method", "dataset"]).size()
    assert (counts == counts.iloc[0]).all()
    assert set(df.loc[df["row_type"] == "g_hat", "method"]) == set(DEVIG_METHOD_NAMES)
    assert (df["row_type"] == "conclusion").sum() > 0
    assert PNG_PATH.exists() and PNG_PATH.stat().st_size > 0
