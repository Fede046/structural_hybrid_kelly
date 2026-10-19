"""Test di accettazione sulle uscite dell'esecuzione unica sul 2023-24."""

from pathlib import Path

import numpy as np
import pandas as pd

from shk.model.frozen_agents import AGENT_ORDER
from shk.model.frozen_params import load_frozen_params
from shk.model.test_run import FROZEN_COMMIT_SHA256, TEST_RUN_COLUMNS, TEST_SEASON
from shk.model.validation_run import METRICS, load_raw

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "results" / "us_c8_5_test_run.csv"
RAW_PATH = REPO_ROOT / "results" / "raw" / "us_c8_5_test_raw.npz"
RAW_IID_PATH = REPO_ROOT / "results" / "raw" / "us_c8_5_test_raw_iid.npz"
PNG_PATH = REPO_ROOT / "thesis" / "figures" / "us_c8_5_test_run.png"


def test_frozen_hash_matches_freeze_commit():
    """L'hash di frozen_params.toml letto dal loader coincide con quello del commit di congelamento."""
    check = pd.read_csv(CSV_PATH).query("row_type == 'check'").iloc[0]
    assert check["frozen_sha256"] == check["frozen_commit_sha256"] == FROZEN_COMMIT_SHA256


def test_anti_leakage_on_test_season():
    """Anti-leakage del fornitore su tutte le partite del 2023-24, nessuna violazione."""
    check = pd.read_csv(CSV_PATH).query("row_type == 'check'").iloc[0]
    assert check["season"] == TEST_SEASON
    assert int(check["n_matches_checked"]) == int(check["n"]) == 380
    assert int(check["leakage_violations"]) == 0
    assert bool(check["b365_complete"])


def test_c0_equals_b025():
    """C0 coincide con B_0.25 entro 1e-12, su seed block, seed iid e realizzazione osservata."""
    b, c0 = AGENT_ORDER.index("B_0.25"), AGENT_ORDER.index("C0")
    for path in (RAW_PATH, RAW_IID_PATH):
        res = load_raw(path)
        assert res.seasons == (TEST_SEASON,)
        for arr in (res.seeds, res.observed):
            diff = np.abs(arr[:, :, c0] - arr[:, :, b])
            assert np.nanmax(np.where(np.isinf(arr[:, :, b]), 0.0, diff)) <= 1e-12


def test_csv_and_figure_exist_with_all_parts():
    df = pd.read_csv(CSV_PATH)
    assert tuple(df.columns) == TEST_RUN_COLUMNS
    for kind in ("check", "g_hat", "log_loss", "drift", "module2", "summary", "comparison", "stratum", "e_roi"):
        assert (df["row_type"] == kind).any(), kind
    n_seeds = int(load_frozen_params().fixed["n_seeds"])
    assert (df.query("row_type == 'summary'")["n_seeds"] == n_seeds).all()
    res = load_raw(RAW_PATH)
    assert res.seeds.shape[-1] == n_seeds and res.seeds.shape[3] == len(METRICS)
    assert PNG_PATH.is_file() and PNG_PATH.stat().st_size > 0
