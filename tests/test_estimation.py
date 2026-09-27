"""Test unitari per il modulo di stima delle probabilità perturbate."""

import numpy as np
import pytest

from shk.kelly.estimation import relative_perturbation, noisy_estimates


def test_relative_perturbation_values():
    """Verifica la perturbazione relativa con delta positivo e negativo e il clipping agli estremi."""
    p = 0.60
    # Criterio 1: delta = +0.10 -> 0.66, delta = -0.10 -> 0.54 entro 1e-12
    assert abs(relative_perturbation(p, 0.10) - 0.66) < 1e-12
    assert abs(relative_perturbation(p, -0.10) - 0.54) < 1e-12

    # Verifica clipping su estremi [0, 1]
    assert relative_perturbation(0.95, 0.20) == 1.0
    assert relative_perturbation(0.10, -1.5) == 0.0


def test_noisy_estimates_reproducibility():
    """Verifica che lo stesso seed generi stime identiche e seed diversi generino matrici diverse."""
    p = 0.52
    sigma_p = 0.0283
    m, t = 10, 20

    rng1 = np.random.default_rng(42)
    rng2 = np.random.default_rng(42)
    rng3 = np.random.default_rng(43)

    estimates1 = noisy_estimates(p, sigma_p, t, m, rng1)
    estimates2 = noisy_estimates(p, sigma_p, t, m, rng2)
    estimates3 = noisy_estimates(p, sigma_p, t, m, rng3)

    np.testing.assert_array_equal(estimates1, estimates2)
    assert not np.array_equal(estimates1, estimates3)


def test_noisy_estimates_empirical_moments():
    """Verifica media e deviazione standard empiriche con p=0.52, sigma_p=0.0283, M=T=1000."""
    p = 0.52
    sigma_p = 0.0283
    m, t = 1000, 1000
    rng = np.random.default_rng(20260927)

    estimates = noisy_estimates(p, sigma_p, t, m, rng)

    mean_emp = float(np.mean(estimates))
    std_emp = float(np.std(estimates))

    # Criterio 3: media empirica entro 0.001 da p e std empirica entro 0.001 da sigma_p
    assert abs(mean_emp - p) < 0.001
    assert abs(std_emp - sigma_p) < 0.001


def test_noisy_estimates_bounds():
    """Verifica che tutti i valori generati ricadano rigorosamente nell'intervallo [0, 1]."""
    rng = np.random.default_rng(999)
    # Test con sigma elevata per forzare valori sia sotto 0 che sopra 1 prima del clipping
    estimates = noisy_estimates(0.50, 0.50, 100, 100, rng)

    assert np.all(estimates >= 0.0)
    assert np.all(estimates <= 1.0)
    assert np.any(estimates == 0.0)
    assert np.any(estimates == 1.0)


def test_noisy_estimates_zero_sigma():
    """Verifica che sigma_p = 0 restituisca una matrice con tutti i valori identici a p."""
    rng = np.random.default_rng(123)
    p = 0.58
    m, t = 5, 8
    estimates = noisy_estimates(p, 0.0, t, m, rng)

    assert estimates.shape == (m, t)
    assert estimates.dtype == np.float64
    np.testing.assert_array_equal(estimates, np.full((m, t), p))


def test_estimation_validation_errors():
    """Verifica che vengano sollevate le eccezioni appropriate per parametri non validi."""
    rng = np.random.default_rng(42)

    # Validazione per relative_perturbation
    with pytest.raises(ValueError):
        relative_perturbation(-0.01, 0.10)
    with pytest.raises(ValueError):
        relative_perturbation(1.01, 0.10)
    with pytest.raises(ValueError):
        relative_perturbation(0.60, float("nan"))
    with pytest.raises(ValueError):
        relative_perturbation(0.60, float("inf"))

    # Validazione p per noisy_estimates
    with pytest.raises(ValueError):
        noisy_estimates(-0.1, 0.02, 10, 10, rng)
    with pytest.raises(ValueError):
        noisy_estimates(1.1, 0.02, 10, 10, rng)

    # Validazione sigma_p per noisy_estimates
    with pytest.raises(ValueError):
        noisy_estimates(0.50, -0.01, 10, 10, rng)
    with pytest.raises(ValueError):
        noisy_estimates(0.50, float("nan"), 10, 10, rng)
    with pytest.raises(ValueError):
        noisy_estimates(0.50, float("inf"), 10, 10, rng)

    # Validazione dimensioni temporali e spaziali
    with pytest.raises(ValueError):
        noisy_estimates(0.50, 0.02, 0, 10, rng)
    with pytest.raises(ValueError):
        noisy_estimates(0.50, 0.02, -5, 10, rng)
    with pytest.raises(ValueError):
        noisy_estimates(0.50, 0.02, 10, 0, rng)
    with pytest.raises(ValueError):
        noisy_estimates(0.50, 0.02, 10, -5, rng)

    # Validazione tipo di rng
    with pytest.raises(TypeError):
        noisy_estimates(0.50, 0.02, 10, 10, "not_an_rng")  # type: ignore
