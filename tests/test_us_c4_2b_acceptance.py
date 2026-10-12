"""Test di accettazione di T57 sul CSV di inferenza su ĝ."""

from pathlib import Path

import numpy as np
import pandas as pd

from shk.model.g_hat_inference import G_HAT_INFERENCE_COLUMNS, N_PERMUTATIONS, t57_sequences
from shk.model.scoring import ALL_DEVIG_METHODS, SERIES_NAMES
from shk.model.validation_run import SEED_S10

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "results" / "us_c4_2b_g_hat_inference.csv"
PNG_PATH = REPO_ROOT / "thesis" / "figures" / "us_c4_2b_g_hat_inference.png"
C42_PATH = REPO_ROOT / "results" / "us_c4_2_g_hat.csv"


def test_point_g_hat_matches_c4_2_and_t43():
    """ĝ pooled e per stagione coincidono con C4.2 e T43 entro 1e-12."""
    df = pd.read_csv(CSV_PATH)
    c42 = pd.read_csv(C42_PATH)
    iv = df[df["row_type"] == "interval"]
    summary = c42[c42["level"] == "summary"].set_index(["series", "method"])["g_hat"]
    cum = c42[c42["level"] == "cumulative"]
    for (series, method), g in summary.items():
        row = iv[(iv["series"] == series) & (iv["method"] == method) & (iv["season"] == "pooled")].iloc[0]
        assert abs(row["g_hat"] - g) <= 1e-12
        c = cum[(cum["series"] == series) & (cum["method"] == method)].sort_values("t")
        t, val, seasons = c["t"].to_numpy(), c["g_hat"].to_numpy(), c["season"].to_numpy()
        for s in pd.unique(seasons):
            idx = np.flatnonzero(seasons == s)
            first, last = idx[0], idx[-1]
            prev = val[first - 1] * t[first - 1] if first > 0 else 0.0
            season_mean = (val[last] * t[last] - prev) / (last - first + 1)
            row = iv[(iv["series"] == series) & (iv["method"] == method) & (iv["season"] == s)].iloc[0]
            assert abs(row["g_hat"] - season_mean) <= 1e-12


def test_ar1_coverage_criteria_binding():
    """Criteri sostituiti dal programmatore: φ = 0 in [0.93, 0.97] per block e iid; φ = 0.5 block > iid e vicino a T42."""
    cov = pd.read_csv(CSV_PATH).query("row_type == 'coverage'").set_index("phi")
    assert set(cov.index) == {0.0, 0.1, 0.25, 0.5}
    assert bool(cov.loc[0.0, "criterion"]) and bool(cov.loc[0.5, "criterion"])
    assert 0.93 <= cov.loc[0.0, "coverage_stationary"] <= 0.97 and 0.93 <= cov.loc[0.0, "coverage_iid"] <= 0.97
    assert cov.loc[0.5, "coverage_stationary"] > cov.loc[0.5, "coverage_iid"]


def test_placebo_mean_matches_exact_expectation_binding():
    """Criterio vincolante sulla permutazione: in ogni stagione la media dei ĝ placebo dista dal valore atteso < 3 SE."""
    pl = pd.read_csv(CSV_PATH).query("row_type == 'placebo' and season != 'pooled'")
    assert (pl["placebo_n"] == N_PERMUTATIONS).all()
    assert len(pl) == (19 + 10) * len(ALL_DEVIG_METHODS)
    assert pl["within_3se"].astype(bool).all()


def test_csv_rows_and_figure():
    df = pd.read_csv(CSV_PATH)
    assert tuple(df.columns) == G_HAT_INFERENCE_COLUMNS
    for kind in ("interval", "threshold", "placebo", "placebo_leakage", "rolling", "band", "acf", "coverage"):
        assert (df["row_type"] == kind).any(), kind
    acf = df[df["row_type"] == "acf"]
    assert len(acf) == len(SERIES_NAMES) * len(ALL_DEVIG_METHODS) * 10
    assert PNG_PATH.is_file() and PNG_PATH.stat().st_size > 0


def test_t57_seed_scheme():
    seqs = t57_sequences(SEED_S10)
    child = np.random.SeedSequence(SEED_S10).spawn(5)[2].spawn(3)[1]
    assert np.random.default_rng(seqs[1]).integers(0, 2**62) == np.random.default_rng(child).integers(0, 2**62)


def test_pooled_intervals_t_corrected_for_clusters():
    """Pooled: ĝ ± t_{0.975, S−1}·√(S/(S − 1))·se_boot, con S = stagioni della serie (decisione del 2026-10-12)."""
    import math
    import scipy.stats
    iv = pd.read_csv(CSV_PATH).query("row_type == 'interval' and season == 'pooled'")
    for series, s_count in (("b365_prematch", 19), ("pinnacle_closing", 10)):
        sub = iv[iv["series"] == series]
        assert (sub["interval_method"] == "t_cluster").all()
        half = scipy.stats.t.ppf(0.975, s_count - 1) * math.sqrt(s_count / (s_count - 1)) * sub["se_boot_block"]
        assert np.allclose(sub["ci_block_high"] - sub["g_hat"], half, rtol=1e-9)
        assert sub["ci_block_pct_low"].notna().all()
