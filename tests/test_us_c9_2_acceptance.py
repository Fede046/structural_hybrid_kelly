"""Test: τ di Kendall, statistica di ranking, C0 = B_0.25 con Dixon-Coles, CSV e figura."""

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import scipy.stats

from shk.model.comparisons import season_statistic
from shk.model.frozen_agents import AGENT_ORDER
from shk.model.robustness import agent_statistics, inverted_pairs, kendall_tau_b, ranks
from shk.model.validation_run import CONFIG_NAMES, METRICS, ValidationResult, load_raw

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW = REPO_ROOT / "results" / "raw"
CSV_PATH = REPO_ROOT / "results" / "us_c9_2_robustness.csv"
PNG_PATH = REPO_ROOT / "thesis" / "figures" / "us_c9_2_robustness.png"


def test_kendall_tau_b_hand_examples():
    """Esempi minimi calcolati a mano.

    [1, 2, 3, 4] contro [1, 3, 2, 4]: 6 coppie, 5 concordi e 1 discorde, τ = (5 − 1)/6 = 2/3.
    [1, 1, 2] contro [1, 2, 3]: la coppia (1, 2) è in parità nel primo, le altre due concordi;
    n_0 = 3, n_1 = 1, n_2 = 0, τ_b = 2/√(2·3) = 2/√6.
    """
    assert kendall_tau_b([1, 2, 3, 4], [1, 3, 2, 4]) == pytest.approx(2.0 / 3.0, abs=1e-15)
    assert kendall_tau_b([1, 1, 2], [1, 2, 3]) == pytest.approx(2.0 / math.sqrt(6.0), abs=1e-15)
    assert kendall_tau_b([1, 2, 3], [3, 2, 1]) == pytest.approx(-1.0, abs=1e-15)
    assert math.isnan(kendall_tau_b([1, 1, 1], [1, 2, 3]))
    rng = np.random.default_rng(0)
    x = rng.normal(size=12)
    y = x + rng.normal(size=12)
    x[5], y[5] = x[6], y[6]
    assert kendall_tau_b(x, y) == pytest.approx(scipy.stats.kendalltau(x, y).statistic, abs=1e-12)


def test_inverted_pairs_and_ranks():
    """Coppie con differenze di segno opposto; rango 1 al valore più alto, parità al rango minimo."""
    assert inverted_pairs([1, 2, 3, 4], [1, 3, 2, 4]) == [(1, 2)]
    assert inverted_pairs([1, 1, 2], [2, 1, 3]) == []
    assert ranks([0.3, 0.1, 0.3, 0.5]).tolist() == [2, 4, 2, 1]


def _synthetic_result(n_seasons: int = 3, n_seeds: int = 5) -> ValidationResult:
    rng = np.random.default_rng(1)
    shape = (n_seasons, len(CONFIG_NAMES), len(AGENT_ORDER), len(METRICS), n_seeds)
    seeds = rng.normal(size=shape)
    seeds[..., METRICS.index("ruined"), :] = (rng.random(size=shape[:3] + (n_seeds,)) < 0.2).astype(float)
    return ValidationResult(tuple(f"{2001 + s}-{(2 + s) % 100:02d}" for s in range(n_seasons)), ("x",) * n_seasons,
                            np.array([110, 115, 120][:n_seasons]), np.ones(n_seasons), seeds,
                            np.zeros(shape[:4]))


def test_agent_statistics_definition():
    """Mediana sui seed per stagione e media sulle stagioni; per le metriche per stagione la media sulle stagioni."""
    res = _synthetic_result()
    config, agent = 1, AGENT_ORDER.index("C2")
    got = agent_statistics(res, config, "final_log_wealth")[agent]
    by_season = [np.median(res.seeds[s, config, agent, METRICS.index("final_log_wealth")]) for s in range(3)]
    assert got == pytest.approx(float(np.mean(by_season)), abs=1e-15)
    got = agent_statistics(res, config, "g_ce_2")[agent]
    lw, ru = METRICS.index("final_log_wealth"), METRICS.index("ruined")
    expected = np.mean([season_statistic("g_ce_2", res.seeds[s, config, agent, lw], res.seeds[s, config, agent, ru],
                                         int(res.n_dates[s])) for s in range(3)])
    assert got == pytest.approx(float(expected), abs=1e-12)
    s_idx, k_idx = np.array([2, 2, 0]), np.array([[0, 0, 1, 2, 3], [4, 4, 4, 0, 1], [1, 2, 3, 3, 3]])
    got = agent_statistics(res, config, "max_drawdown", s_idx, k_idx)[agent]
    m = METRICS.index("max_drawdown")
    expected = np.mean([np.median(res.seeds[s, config, agent, m][k]) for s, k in zip(s_idx, k_idx)])
    assert got == pytest.approx(float(expected), abs=1e-15)


@pytest.mark.parametrize("name", ["us_c8_3_validation_raw_dc.npz", "us_c8_5_test_raw_dc.npz"])
def test_c0_equals_b025_with_dixon_coles(name):
    """Con Dixon-Coles C0 coincide con B_0.25 entro 1e-12, sui seed e sulla realizzazione osservata."""
    path = RAW / name
    if not path.exists():
        pytest.skip(f"Missing {path}: run the Dixon-Coles validation and test executions")
    res = load_raw(path)
    c0, b = AGENT_ORDER.index("C0"), AGENT_ORDER.index("B_0.25")
    for arr in (res.seeds, res.observed):
        x, y = arr[:, :, c0], arr[:, :, b]
        assert np.array_equal(np.isnan(x), np.isnan(y))
        assert np.nanmax(np.abs(x - y)) <= 1e-12


def test_csv_and_figure_exist():
    """CSV e figura della robustezza del ranking esistono, con τ per validazione e test e confronti affiancati."""
    if not CSV_PATH.exists():
        pytest.skip(f"Missing {CSV_PATH}: run scripts/us_c9_2_robustness.py")
    df = pd.read_csv(CSV_PATH)
    tau = df[df["row_type"] == "tau"]
    assert set(tau["dataset"]) == {"validation", "test"}
    assert len(tau) == 2 * len(CONFIG_NAMES) * 8
    assert set(df["row_type"]) >= {"tau", "statistic", "comparison"}
    assert PNG_PATH.exists() and PNG_PATH.stat().st_size > 0
