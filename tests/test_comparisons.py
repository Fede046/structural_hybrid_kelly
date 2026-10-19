"""Test su dati sintetici: statistiche per stagione, bootstrap a due livelli, copertura, effect size."""

import math

import numpy as np
import scipy.stats

from shk.model.comparisons import (
    PRIMARY_METRICS,
    SEASON_METRICS,
    BootstrapIndices,
    coverage_simulation,
    effect_sizes,
    percentile_interval,
    pooled_bootstrap,
    season_differences,
    season_statistic,
    season_statistic_batch,
    t_cluster_interval,
    two_level_indices,
)
from shk.model.frozen_agents import AGENT_ORDER
from shk.model.validation_run import METRICS, ValidationResult


def _synthetic_result(n_seasons=6, n_seeds=40, seed=0):
    rng = np.random.default_rng(seed)
    arr = np.full((n_seasons, 3, len(AGENT_ORDER), len(METRICS), n_seeds), np.nan)
    for ai in range(len(AGENT_ORDER)):
        arr[:, :, ai, METRICS.index("final_log_wealth")] = rng.normal(0.01 * ai, 0.3, (n_seasons, 3, n_seeds))
        arr[:, :, ai, METRICS.index("max_drawdown")] = rng.uniform(0.1, 0.6, (n_seasons, 3, n_seeds))
        arr[:, :, ai, METRICS.index("recovery_time")] = rng.integers(0, 50, (n_seasons, 3, n_seeds))
        arr[:, :, ai, METRICS.index("ruined")] = (rng.random((n_seasons, 3, n_seeds)) < 0.02).astype(float)
    lw = arr[:, :, :, METRICS.index("final_log_wealth")]
    lw[arr[:, :, :, METRICS.index("ruined")] > 0.5] = -np.inf
    return ValidationResult(tuple(f"s{i}" for i in range(n_seasons)), tuple("f" for _ in range(n_seasons)),
                            np.full(n_seasons, 100), np.ones(n_seasons, dtype=int), arr, arr[..., 0])


def test_batch_statistics_match_scalar():
    rng = np.random.default_rng(1)
    lw = rng.normal(0.0, 0.3, (4, 50))
    ruined = (rng.random((4, 50)) < 0.1).astype(float)
    lw_r = np.where(ruined > 0.5, -np.inf, lw)
    n_dates = np.full(4, 120.0)
    for metric in SEASON_METRICS:
        for x in (lw, lw_r):
            batch = season_statistic_batch(metric, x, ruined, n_dates)
            scalar = [season_statistic(metric, x[i], ruined[i], 120) for i in range(4)]
            for b, s in zip(batch, scalar):
                assert (math.isinf(b) and b == s) or math.isclose(b, s, rel_tol=1e-12, abs_tol=1e-15)


def test_identity_resample_equals_point_estimate_and_decomposition():
    """Con gli indici identità il bootstrap dà la stima puntuale; C2 − C0 = (C1 − C0) + (C2 − C1) entro 1e-12."""
    res = _synthetic_result()
    s, n = res.seeds.shape[0], res.seeds.shape[-1]
    ident = BootstrapIndices(np.arange(s)[None, :], np.broadcast_to(np.arange(n), (1, s, n)).astype(np.int32))
    for metric in PRIMARY_METRICS:
        point = float(np.mean(season_differences(res, 1, "C2", "C1", metric)))
        boot = pooled_bootstrap(res, 1, "C2", "C1", metric, ident)[0]
        assert (math.isnan(point) and math.isnan(boot)) or math.isclose(boot, point, rel_tol=1e-12, abs_tol=1e-15)
        total = np.mean(season_differences(res, 1, "C2", "C0", metric))
        parts = np.mean(season_differences(res, 1, "C1", "C0", metric)) + np.mean(season_differences(res, 1, "C2", "C1", metric))
        if np.isfinite(total):
            assert abs(total - parts) <= 1e-12


def test_two_level_indices_and_percentiles():
    idx = two_level_indices(19, 7, np.random.default_rng(2), n_boot=11)
    assert idx.seasons.shape == (11, 19) and idx.seeds.shape == (11, 19, 7)
    assert idx.seasons.max() < 19 and idx.seeds.max() < 7
    assert percentile_interval(np.arange(999.0)) == (24.0, 974.0)


def test_effect_sizes():
    e = effect_sizes(0.5, 1.0)
    assert e["d"] == 0.5 and math.isclose(e["r2_upper"], 0.25) and math.isclose(e["r2_canonical"], 0.25 / 4.25)
    assert math.isclose(e["ovl"], 2 * 0.4012936743170763)


def test_coverage_simulation_is_deterministic_fraction():
    """Funzionamento della simulazione di copertura (il criterio vincolante è sul CSV dei confronti fra agenti)."""
    a = coverage_simulation(np.random.default_rng(5), n_replicas=30, n_seeds=50, tau=0.05, sigma=0.3)
    b = coverage_simulation(np.random.default_rng(5), n_replicas=30, n_seeds=50, tau=0.05, sigma=0.3)
    assert a == b and all(0.0 <= v <= 1.0 for v in a)
    # Lo stesso flusso dà la stessa copertura percentile e una copertura t corretta non inferiore
    assert a[1] >= a[0]


def test_t_cluster_interval():
    """D̂ ± t_{0.975, S−1}·√(S/(S − 1))·se_boot: allarga rispetto a ±1.96·se_boot."""
    boot = np.random.default_rng(7).normal(0.0, 0.01, 999)
    lo, hi, se = t_cluster_interval(0.02, boot, 19)
    assert math.isclose(se, float(np.std(boot, ddof=1)))
    half = scipy.stats.t.ppf(0.975, 18) * math.sqrt(19 / 18) * se
    assert math.isclose(hi - 0.02, half) and math.isclose(0.02 - lo, half)
    assert half > 1.96 * se
