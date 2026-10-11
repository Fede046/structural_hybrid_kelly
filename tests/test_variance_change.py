"""Test di src/shk/stats/variance_change.py (T44)."""

import math
import warnings

import numpy as np
import pytest
import scipy.stats
from statsmodels.stats.diagnostic import het_arch, het_goldfeldquandt

from shk.stats.variance_change import (
    arch_lm,
    arch_lm_nominal_threshold,
    brown_forsythe,
    brown_forsythe_nominal_threshold,
    goldfeld_quandt_nominal_bounds,
    goldfeld_quandt_split,
    goldfeld_quandt_thirds,
    moving_block_indices_of_length,
    rolling_log_variance_max,
    varentropy_standardized_residuals,
)


def _draw_outcomes(probs: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Esiti estratti da probs per inversione della cumulata."""
    u = rng.random(probs.shape[0])
    return (u[:, None] > np.cumsum(probs, axis=1)[:, :-1]).sum(axis=1).astype(np.int64)


def test_standardized_residuals_mean_zero_variance_one():
    """Con esiti estratti da p̂, z ha media 0 e varianza 1 entro 4 errori standard Monte Carlo."""
    rng = np.random.default_rng(20261011)
    n = 200_000
    probs = rng.dirichlet([4.0, 3.0, 3.0], size=n)
    outcomes = _draw_outcomes(probs, rng)
    z = varentropy_standardized_residuals(probs, outcomes)

    se_mean = z.std(ddof=1) / math.sqrt(n)
    se_var = math.sqrt(np.mean((z - z.mean()) ** 4) - z.var() ** 2) / math.sqrt(n)
    assert abs(z.mean()) < 4.0 * se_mean
    assert abs(z.var(ddof=1) - 1.0) < 4.0 * se_var


def test_standardized_residuals_formula():
    """z = (l - H) / sqrt(V) su un caso a mano."""
    probs = np.array([[0.5, 0.3, 0.2]])
    z = varentropy_standardized_residuals(probs, np.array([2]))
    h = -np.sum(probs * np.log(probs))
    v = np.sum(probs * np.log(probs) ** 2) - h**2
    assert math.isclose(z[0], (-math.log(0.2) - h) / math.sqrt(v), rel_tol=1e-14)


def test_standardized_residuals_validation():
    """Tipi e valori non validi, compresa la varentropia nulla."""
    probs = np.array([[0.5, 0.3, 0.2]])
    with pytest.raises(TypeError, match="outcomes must have integer dtype"):
        varentropy_standardized_residuals(probs, np.array([1.0]))
    with pytest.raises(ValueError, match="outcomes must have shape"):
        varentropy_standardized_residuals(probs, np.array([1, 2]))
    with pytest.raises(ValueError, match="strictly positive"):
        varentropy_standardized_residuals(np.array([[1.0, 0.0, 0.0]]), np.array([0]))
    with pytest.raises(ValueError, match="sum to 1"):
        varentropy_standardized_residuals(np.array([[0.5, 0.3, 0.3]]), np.array([0]))
    with pytest.raises(ValueError, match="outcomes must be in"):
        varentropy_standardized_residuals(probs, np.array([3]))
    with pytest.raises(ValueError, match="Varentropy"):
        varentropy_standardized_residuals(np.full((1, 3), 1.0 / 3.0), np.array([0]))


def test_arch_lm_matches_statsmodels():
    """ARCH-LM coincide con statsmodels het_arch(nlags=10) entro 1e-10 (criterio T44)."""
    rng = np.random.default_rng(1)
    for _ in range(30):
        z = rng.standard_t(5, size=380)
        ref = het_arch(z, nlags=10, result_object=False)[0]
        assert math.isclose(arch_lm(z), ref, rel_tol=1e-10, abs_tol=1e-10)
    batch = rng.normal(size=(4, 380))
    np.testing.assert_allclose(arch_lm(batch), [arch_lm(b) for b in batch], rtol=1e-12)


def test_goldfeld_quandt_matches_statsmodels():
    """Il rapporto dei terzi coincide con het_goldfeldquandt (costante, split e drop dei terzi)."""
    rng = np.random.default_rng(2)
    first, last_start = goldfeld_quandt_split(380)
    assert (first, last_start) == (126, 254)
    for _ in range(30):
        z = rng.normal(size=380) * np.linspace(0.8, 1.2, 380)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            fval, pval, _ = het_goldfeldquandt(
                z, np.ones((380, 1)), split=first, drop=last_start - first,
                alternative="two-sided",
            )
        assert math.isclose(goldfeld_quandt_thirds(z), fval, rel_tol=1e-10, abs_tol=1e-10)
        lower, upper = goldfeld_quandt_nominal_bounds(380, 0.05)
        reject = goldfeld_quandt_thirds(z) > upper or goldfeld_quandt_thirds(z) < lower
        assert reject == (pval < 0.05)


def test_brown_forsythe_matches_scipy():
    """Brown-Forsythe coincide con scipy.stats.levene(center="median")."""
    rng = np.random.default_rng(3)
    groups = rng.normal(size=(19, 380)) * rng.uniform(0.9, 1.1, size=(19, 1))
    ref = scipy.stats.levene(*groups, center="median").statistic
    assert math.isclose(brown_forsythe(groups), ref, rel_tol=1e-12)
    batch = np.stack([groups, groups[::-1]])
    np.testing.assert_allclose(brown_forsythe(batch), [ref, ref], rtol=1e-12)
    assert math.isclose(
        brown_forsythe_nominal_threshold(19, 380, 0.05),
        scipy.stats.f.ppf(0.95, 18, 7201),
        rel_tol=1e-15,
    )


def test_rolling_log_variance_max():
    """31 finestre per n = 380; statistica nulla se le finestre hanno la varianza della serie."""
    rng = np.random.default_rng(4)
    z = rng.normal(size=380)
    starts = np.arange(0, 301, 10)
    assert starts.size == 31
    expected = max(
        abs(math.log(z[s : s + 80].var(ddof=1) / z.var(ddof=1))) for s in starts
    )
    assert math.isclose(rolling_log_variance_max(z), expected, rel_tol=1e-12)
    periodic = np.tile([1.0, -1.0], 190)
    assert rolling_log_variance_max(periodic) < 0.02
    with pytest.raises(ValueError, match="window must satisfy"):
        rolling_log_variance_max(z, window=400)


def test_nominal_thresholds():
    """Chi quadro con 10 gradi di libertà e quantili della F(125, 125)."""
    assert math.isclose(arch_lm_nominal_threshold(10, 0.05), scipy.stats.chi2.ppf(0.95, 10))
    lower, upper = goldfeld_quandt_nominal_bounds(380, 0.05)
    assert math.isclose(upper, scipy.stats.f.ppf(0.975, 125, 125))
    assert math.isclose(lower, scipy.stats.f.ppf(0.025, 125, 125))


def test_moving_block_indices_of_length():
    """Forma, tipo, intervallo e blocchi consecutivi anche con lunghezza maggiore di n."""
    rng = np.random.default_rng(5)
    idx = moving_block_indices_of_length(1140, 7220, 20, 50, rng)
    assert idx.shape == (50, 7220) and idx.dtype == np.int64
    assert idx.min() >= 0 and idx.max() < 1140
    blocks = idx[:, :7220 - 7220 % 20].reshape(50, -1, 20)
    assert np.all(np.diff(blocks, axis=2) == 1)
    with pytest.raises(ValueError, match="block_length must satisfy"):
        moving_block_indices_of_length(10, 20, 11, 5, rng)
    with pytest.raises(TypeError, match="rng must be"):
        moving_block_indices_of_length(10, 20, 2, 5, 1)  # type: ignore


def test_statistics_input_validation():
    """Tipi e forme non validi."""
    with pytest.raises(TypeError, match="z must be an instance of np.ndarray"):
        arch_lm([1.0] * 50)  # type: ignore
    with pytest.raises(ValueError, match="z must have more than"):
        arch_lm(np.arange(20, dtype=float))
    with pytest.raises(ValueError, match="n must be at least 6"):
        goldfeld_quandt_thirds(np.arange(5, dtype=float))
    with pytest.raises(ValueError, match="groups must have"):
        brown_forsythe(np.ones((1, 10)))
