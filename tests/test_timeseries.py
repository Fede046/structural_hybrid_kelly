"""Test unitari e di conformità statistica per il generatore di serie AR(1)."""

import numpy as np
import pytest

from shk.stats.timeseries import generate_ar1_series


# ---------------------------------------------------------------------------
# Criterio 1: Forma dell'output e dtype float64
# ---------------------------------------------------------------------------


def test_generate_ar1_shape_and_dtype():
    """Verifica che l'output abbia forma (m, n) e tipo float64."""
    rng = np.random.default_rng(42)
    m, n = 15, 60
    series = generate_ar1_series(phi=0.4, n=n, m=m, rng=rng)

    assert isinstance(series, np.ndarray)
    assert series.shape == (m, n)
    assert series.dtype == np.float64


# ---------------------------------------------------------------------------
# Criterio 2: Riproducibilità rispetto al seed
# ---------------------------------------------------------------------------


def test_generate_ar1_reproducibility():
    """Verifica che lo stesso seed generi array identici e seed diversi generino array diversi."""
    phi = 0.5
    m, n = 20, 100

    rng1 = np.random.default_rng(12345)
    rng2 = np.random.default_rng(12345)
    rng3 = np.random.default_rng(54321)

    series1 = generate_ar1_series(phi=phi, n=n, m=m, rng=rng1)
    series2 = generate_ar1_series(phi=phi, n=n, m=m, rng=rng2)
    series3 = generate_ar1_series(phi=phi, n=n, m=m, rng=rng3)

    np.testing.assert_array_equal(series1, series2)
    assert not np.array_equal(series1, series3)


# ---------------------------------------------------------------------------
# Criterio 3: Proprietà statistiche empiriche (varianze e autocorrelazione pooled)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("phi", [0.0, 0.3, 0.7])
def test_generate_ar1_statistical_properties(phi: float):
    """Verifica varianza empirica prima/ultima colonna (errore < 15%) e autocorrelazione lag-1 (|diff| < 0.02)."""
    m = 2000
    n = 380
    seed = 20260928
    rng = np.random.default_rng(seed)

    series = generate_ar1_series(phi=phi, n=n, m=m, rng=rng)

    # Varianza teorica del processo AR(1) stazionario standard
    theoretical_var = 1.0 / (1.0 - phi * phi)

    var_first = float(np.var(series[:, 0], ddof=0))
    var_last = float(np.var(series[:, -1], ddof=0))

    # Varianza alla prima colonna entro il 15% relativo
    rel_err_first = abs(var_first - theoretical_var) / theoretical_var
    assert rel_err_first < 0.15, (
        f"phi={phi}: var_first={var_first}, theoretical={theoretical_var}, rel_err={rel_err_first}"
    )

    # Varianza all'ultima colonna entro il 15% relativo
    rel_err_last = abs(var_last - theoretical_var) / theoretical_var
    assert rel_err_last < 0.15, (
        f"phi={phi}: var_last={var_last}, theoretical={theoretical_var}, rel_err={rel_err_last}"
    )

    # Autocorrelazione pooled a ritardo 1: num = sum(x_t * x_{t+1}), den = sum(x_t^2)
    numerator = np.sum(series[:, :-1] * series[:, 1:])
    denominator = np.sum(series[:, :-1] ** 2)
    pooled_rho1 = float(numerator / denominator)

    err_autocorr = abs(pooled_rho1 - phi)
    assert err_autocorr < 0.02, (
        f"phi={phi}: pooled_rho1={pooled_rho1}, expected={phi}, abs_err={err_autocorr}"
    )


# ---------------------------------------------------------------------------
# Test delle condizioni di validazione
# ---------------------------------------------------------------------------


def test_generate_ar1_validation_phi_bounds():
    """Valori di phi non compresi in (-1, 1) sollevano ValueError."""
    rng = np.random.default_rng(42)
    with pytest.raises(ValueError, match="satisfy \\|phi\\| < 1"):
        generate_ar1_series(phi=1.0, n=10, m=5, rng=rng)
    with pytest.raises(ValueError, match="satisfy \\|phi\\| < 1"):
        generate_ar1_series(phi=-1.0, n=10, m=5, rng=rng)
    with pytest.raises(ValueError, match="satisfy \\|phi\\| < 1"):
        generate_ar1_series(phi=1.2, n=10, m=5, rng=rng)
    with pytest.raises(ValueError, match="satisfy \\|phi\\| < 1"):
        generate_ar1_series(phi=-2.0, n=10, m=5, rng=rng)


def test_generate_ar1_validation_phi_non_finite():
    """Valori di phi non finiti (NaN, Inf) sollevano ValueError."""
    rng = np.random.default_rng(42)
    with pytest.raises(ValueError, match="phi.*must be finite"):
        generate_ar1_series(phi=float("nan"), n=10, m=5, rng=rng)
    with pytest.raises(ValueError, match="phi.*must be finite"):
        generate_ar1_series(phi=float("inf"), n=10, m=5, rng=rng)
    with pytest.raises(ValueError, match="phi.*must be finite"):
        generate_ar1_series(phi=float("-inf"), n=10, m=5, rng=rng)


def test_generate_ar1_validation_n_below_minimum():
    """Valori di n < 2 sollevano ValueError."""
    rng = np.random.default_rng(42)
    with pytest.raises(ValueError, match="Number of time steps 'n' must be at least 2"):
        generate_ar1_series(phi=0.3, n=1, m=5, rng=rng)
    with pytest.raises(ValueError, match="Number of time steps 'n' must be at least 2"):
        generate_ar1_series(phi=0.3, n=0, m=5, rng=rng)
    with pytest.raises(ValueError, match="Number of time steps 'n' must be at least 2"):
        generate_ar1_series(phi=0.3, n=-5, m=5, rng=rng)


def test_generate_ar1_validation_m_below_minimum():
    """Valori di m < 1 sollevano ValueError."""
    rng = np.random.default_rng(42)
    with pytest.raises(ValueError, match="Number of series 'm' must be strictly positive"):
        generate_ar1_series(phi=0.3, n=10, m=0, rng=rng)
    with pytest.raises(ValueError, match="Number of series 'm' must be strictly positive"):
        generate_ar1_series(phi=0.3, n=10, m=-2, rng=rng)


def test_generate_ar1_validation_n_type():
    """Valori di n non interi o booleani sollevano TypeError."""
    rng = np.random.default_rng(42)
    with pytest.raises(TypeError, match="Number of time steps 'n' must be an integer, got float"):
        generate_ar1_series(phi=0.3, n=2.5, m=5, rng=rng)  # type: ignore
    with pytest.raises(TypeError, match="Number of time steps 'n' must be an integer, got bool"):
        generate_ar1_series(phi=0.3, n=True, m=5, rng=rng)  # type: ignore
    with pytest.raises(TypeError, match="Number of time steps 'n' must be an integer, got bool"):
        generate_ar1_series(phi=0.3, n=False, m=5, rng=rng)  # type: ignore


def test_generate_ar1_validation_m_type():
    """Valori di m non interi o booleani sollevano TypeError."""
    rng = np.random.default_rng(42)
    with pytest.raises(TypeError, match="Number of series 'm' must be an integer, got float"):
        generate_ar1_series(phi=0.3, n=10, m=2.5, rng=rng)  # type: ignore
    with pytest.raises(TypeError, match="Number of series 'm' must be an integer, got bool"):
        generate_ar1_series(phi=0.3, n=10, m=True, rng=rng)  # type: ignore
    with pytest.raises(TypeError, match="Number of series 'm' must be an integer, got bool"):
        generate_ar1_series(phi=0.3, n=10, m=False, rng=rng)  # type: ignore


def test_generate_ar1_validation_numpy_integer_types():
    """Tipi interi di NumPy (es. np.int64) vengono accettati correttamente."""
    rng = np.random.default_rng(42)
    n = np.int64(10)
    m = np.int64(3)
    series = generate_ar1_series(phi=0.3, n=n, m=m, rng=rng)
    assert series.shape == (3, 10)


def test_generate_ar1_validation_rng_type():
    """rng diverso da np.random.Generator solleva TypeError."""
    with pytest.raises(TypeError, match="rng must be an instance of np.random.Generator"):
        generate_ar1_series(phi=0.3, n=10, m=5, rng="not_an_rng")  # type: ignore
    with pytest.raises(TypeError, match="rng must be an instance of np.random.Generator"):
        generate_ar1_series(phi=0.3, n=10, m=5, rng=123)  # type: ignore
