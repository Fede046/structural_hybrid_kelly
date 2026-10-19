"""Test di accettazione sul CSV dei confronti e sulle uscite per seed."""

import math
from pathlib import Path

import numpy as np
import pandas as pd

from shk.model.comparisons import COMPARISONS, PRIMARY_METRICS, season_differences
from shk.model.comparisons_run import COMPARISON_COLUMNS, t56_sequences
from shk.model.validation_run import CONFIG_NAMES, SEED_S10, load_raw

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "results" / "us_c8_4_comparisons.csv"
RAW_PATH = REPO_ROOT / "results" / "raw" / "us_c8_3_validation_raw.npz"


def test_every_difference_has_estimate_and_both_intervals():
    df = pd.read_csv(CSV_PATH)
    assert tuple(df.columns) == COMPARISON_COLUMNS
    comp = df[df["row_type"] == "comparison"]
    # C2 − E manca solo con F = 0
    expected = sum(len(PRIMARY_METRICS) * sum(1 for a, b in COMPARISONS if not (b == "E" and c == "none"))
                   for c in CONFIG_NAMES)
    assert len(comp) == expected
    for col in ("estimate", "ci_block_low", "ci_block_high", "ci_iid_low", "ci_iid_high",
                "ci_block_pct_low", "ci_block_pct_high", "ci_iid_pct_low", "ci_iid_pct_high"):
        assert comp[col].notna().all(), col
    finite = comp[np.isfinite(comp["estimate"])]
    assert (finite["ci_block_low"] <= finite["ci_block_high"]).all()


def test_two_level_bootstrap_coverage_binding():
    """Criterio vincolante (decisione del 2026-10-12): la procedura t corretta per il numero di cluster
    copre fra 0.93 e 0.97 su 1 000 repliche, disegno e seed prescritti."""
    cov = pd.read_csv(CSV_PATH).query("row_type == 'coverage' and source == 'seeds_resampled'").iloc[0]
    assert int(cov["n_replicas"]) == 1000
    assert 0.93 <= float(cov["coverage_corrected"]) <= 0.97


def test_main_interval_is_t_corrected():
    """Intervallo principale = stima ± t_{0.975, 18}·√(19/18)·se_boot; il percentile resta come secondario."""
    import math
    import scipy.stats
    comp = pd.read_csv(CSV_PATH).query("row_type == 'comparison'")
    half = scipy.stats.t.ppf(0.975, 18) * math.sqrt(19 / 18) * comp["se_boot_block"]
    ok = comp["se_boot_block"] > 0
    assert np.allclose((comp["ci_block_high"] - comp["estimate"])[ok], half[ok], rtol=1e-9)
    assert comp["ci_block_pct_low"].notna().all() and comp["ci_iid_pct_high"].notna().all()


def test_decomposition_of_c2_minus_c0():
    """C2 − C0 = (C1 − C0) + (C2 − C1) entro 1e-12 sulle stime puntuali; il CSV riporta le stesse stime."""
    block = load_raw(RAW_PATH)
    comp = pd.read_csv(CSV_PATH).query("row_type == 'comparison'")
    for ci, config in enumerate(CONFIG_NAMES):
        for metric in PRIMARY_METRICS:
            total = float(np.mean(season_differences(block, ci, "C2", "C0", metric)))
            d10 = float(np.mean(season_differences(block, ci, "C1", "C0", metric)))
            d21 = float(np.mean(season_differences(block, ci, "C2", "C1", metric)))
            if math.isfinite(total):
                assert abs(total - (d10 + d21)) <= 1e-12
            row = comp[(comp["config"] == config) & (comp["comparison"] == "C1-C0") & (comp["metric"] == metric)]
            if math.isfinite(d10):
                assert math.isclose(float(row["estimate"].iloc[0]), d10, rel_tol=1e-12, abs_tol=1e-15)


def test_alarm_and_pi_lambda_rows():
    df = pd.read_csv(CSV_PATH)
    assert len(df[df["row_type"] == "alarms"]) == 19 * 3
    pl = df[df["row_type"] == "pi_lambda"]
    assert set(pl["quantity"]) == {"pi", "lambda"} and set(pl["source"]) == {"h0", "observed"}
    assert "pooled" in set(pl["season"])


def test_t56_seed_scheme():
    seqs = t56_sequences(SEED_S10)
    child = np.random.SeedSequence(SEED_S10).spawn(5)[1].spawn(3)[2]
    assert np.random.default_rng(seqs[2]).integers(0, 2**62) == np.random.default_rng(child).integers(0, 2**62)
