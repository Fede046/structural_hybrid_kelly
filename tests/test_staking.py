"""Test unitari per il modulo di staking del criterio di Kelly."""

import numpy as np
import pytest

from shk.kelly.core import kelly_fraction
from shk.kelly.staking import StakingMoments, kelly_staking, staking_moments


def test_kelly_staking_positive_edge_and_agreement():
    """Verifica la frazione per edge positivo e la concordanza con kelly_fraction."""
    # Criterio 1: p_hat = 0.60, b = 1.0, lam = 1.0 -> 0.20
    actual = kelly_staking(0.60, 1.0, lam=1.0)
    expected_kf = kelly_fraction(0.60, 1.0)
    assert abs(actual - 0.20) < 1e-12
    assert abs(actual - expected_kf) < 1e-12
    assert actual == expected_kf

    # Accordo su una griglia di valori scalari con edge positivo
    for p_val in [0.55, 0.60, 0.70, 0.80, 0.90]:
        for b_val in [1.0, 1.5, 2.0, 3.0]:
            f_staking = kelly_staking(p_val, b_val, lam=1.0)
            f_core = kelly_fraction(p_val, b_val)
            assert abs(f_staking - f_core) < 1e-12


def test_kelly_staking_negative_and_zero_edge():
    """Verifica che edge negativo o nullo restituisca esattamente zero."""
    # Criterio 2: p_hat = 0.468, b = 1.0 -> edge negativo -> 0.0 esatto
    assert kelly_staking(0.468, 1.0, lam=1.0) == 0.0

    # Edge nullo: p_hat = 0.50, b = 1.0 -> 0.0 esatto
    assert kelly_staking(0.50, 1.0, lam=1.0) == 0.0

    # Troncamento vettoriale elemento per elemento
    p_vec = np.array([0.40, 0.50, 0.60])
    expected_vec = np.array([0.0, 0.0, 0.20])
    actual_vec = kelly_staking(p_vec, 1.0, lam=1.0)
    np.testing.assert_allclose(actual_vec, expected_vec, atol=1e-12)


def test_kelly_staking_fractional_multiplier():
    """Verifica che con lam = 0.25 la frazione sia esattamente un quarto rispetto a lam = 1.0."""
    p_hat = 0.60
    b = 1.0
    f_full = kelly_staking(p_hat, b, lam=1.0)
    f_quarter = kelly_staking(p_hat, b, lam=0.25)

    # Criterio 3: un quarto della frazione piena su scalare
    assert abs(f_quarter - 0.25 * f_full) < 1e-12

    # Verifica su matrice (M, T)
    p_mat = np.array([[0.60, 0.70], [0.45, 0.80]])
    f_mat_full = kelly_staking(p_mat, b, lam=1.0)
    f_mat_quarter = kelly_staking(p_mat, b, lam=0.25)
    np.testing.assert_allclose(f_mat_quarter, 0.25 * f_mat_full, rtol=1e-12)


def test_kelly_staking_output_shapes():
    """Verifica che l'output conservi la forma dell'input (scalare, vettore, matrice)."""
    b = 1.0

    # Scalare Python float -> float Python
    out_scalar = kelly_staking(0.60, b)
    assert isinstance(out_scalar, float)
    assert out_scalar == pytest.approx(0.20)

    # Scalare NumPy -> float Python (Precisazione B)
    out_numpy_scalar = kelly_staking(np.float64(0.60), b)
    assert isinstance(out_numpy_scalar, float)
    assert out_numpy_scalar == pytest.approx(0.20)

    # Array 0D NumPy -> float Python (Precisazione B)
    out_0d = kelly_staking(np.array(0.60), b)
    assert isinstance(out_0d, float)
    assert out_0d == pytest.approx(0.20)

    # Vettore 1D (M,) -> ndarray (M,)
    p_1d = np.array([0.55, 0.60, 0.65])
    out_1d = kelly_staking(p_1d, b)
    assert isinstance(out_1d, np.ndarray)
    assert out_1d.shape == (3,)

    # Matrice 2D (M, T) -> ndarray (M, T)
    p_2d = np.full((4, 7), 0.60)
    out_2d = kelly_staking(p_2d, b)
    assert isinstance(out_2d, np.ndarray)
    assert out_2d.shape == (4, 7)


def test_kelly_staking_allows_fraction_ge_one():
    """Verifica che la regola non limiti la frazione sotto 1 (decisione di design)."""
    # Con p_hat = 1.0 e lam = 1.5 -> f = 1.5
    f_high = kelly_staking(1.0, 1.0, lam=1.5)
    assert f_high == pytest.approx(1.5)

    # Con p_hat = 0.8, b = 1.0 -> f_hat = 0.6; con lam = 2.0 -> f = 1.2
    f_over = kelly_staking(0.80, 1.0, lam=2.0)
    assert f_over == pytest.approx(1.2)


def test_kelly_staking_validation_errors():
    """Verifica che vengano sollevate le opportune eccezioni per parametri non validi."""
    # Moltiplicatore lambda negativo o non finito
    with pytest.raises(ValueError):
        kelly_staking(0.60, 1.0, lam=-0.1)
    with pytest.raises(ValueError):
        kelly_staking(0.60, 1.0, lam=float("nan"))
    with pytest.raises(ValueError):
        kelly_staking(0.60, 1.0, lam=float("inf"))

    # Quota b non positiva o non finita
    with pytest.raises(ValueError):
        kelly_staking(0.60, 0.0)
    with pytest.raises(ValueError):
        kelly_staking(0.60, -1.0)
    with pytest.raises(ValueError):
        kelly_staking(0.60, float("nan"))

    # Probabilità p_hat fuori da [0, 1] per scalari
    with pytest.raises(ValueError):
        kelly_staking(-0.01, 1.0)
    with pytest.raises(ValueError):
        kelly_staking(1.01, 1.0)
    with pytest.raises(ValueError):
        kelly_staking(float("nan"), 1.0)
    with pytest.raises(ValueError):
        kelly_staking(float("inf"), 1.0)

    # Probabilità p_hat fuori da [0, 1] per array
    with pytest.raises(ValueError):
        kelly_staking(np.array([0.60, -0.05]), 1.0)
    with pytest.raises(ValueError):
        kelly_staking(np.array([0.60, 1.10]), 1.0)
    with pytest.raises(ValueError):
        kelly_staking(np.array([0.60, np.nan]), 1.0)


def test_staking_moments_hand_calculated():
    """Verifica il calcolo dei momenti empirici di c su valori noti a mano."""
    # f_star = 0.20
    # f_hat = [0.0, 0.10, 0.20, 0.30] -> c = [0.0, 0.5, 1.0, 1.5]
    # E[c] = (0.0 + 0.5 + 1.0 + 1.5) / 4 = 3.0 / 4 = 0.75
    # E[c^2] = (0.0 + 0.25 + 1.0 + 2.25) / 4 = 3.5 / 4 = 0.875
    # Var(c) = 0.875 - 0.75^2 = 0.875 - 0.5625 = 0.3125
    # fraction_zero = 1 / 4 = 0.25
    f_hat = np.array([0.0, 0.10, 0.20, 0.30])
    moments = staking_moments(f_hat, 0.20)
    assert isinstance(moments, StakingMoments)
    assert abs(moments.mean_c - 0.75) < 1e-12
    assert abs(moments.mean_c2 - 0.875) < 1e-12
    assert abs(moments.var_c - 0.3125) < 1e-12
    assert abs(moments.fraction_zero - 0.25) < 1e-12

    # Verifica forma 2D (pooled su tutte le celle)
    f_hat_2d = f_hat.reshape(2, 2)
    moments_2d = staking_moments(f_hat_2d, 0.20)
    assert abs(moments_2d.mean_c - 0.75) < 1e-12
    assert abs(moments_2d.mean_c2 - 0.875) < 1e-12
    assert abs(moments_2d.var_c - 0.3125) < 1e-12
    assert abs(moments_2d.fraction_zero - 0.25) < 1e-12


def test_staking_moments_validation_errors():
    """Verifica le validazioni di input per staking_moments."""
    # f_star <= 0 oppure non finito
    with pytest.raises(ValueError):
        staking_moments(np.array([0.1]), 0.0)
    with pytest.raises(ValueError):
        staking_moments(np.array([0.1]), -0.2)
    with pytest.raises(ValueError):
        staking_moments(np.array([0.1]), float("nan"))
    with pytest.raises(ValueError):
        staking_moments(np.array([0.1]), float("inf"))

    # f_hat con valori negativi o non finiti
    with pytest.raises(ValueError):
        staking_moments(np.array([-0.05, 0.1]), 0.2)
    with pytest.raises(ValueError):
        staking_moments(np.array([np.nan, 0.1]), 0.2)
    with pytest.raises(ValueError):
        staking_moments(np.array([np.inf, 0.1]), 0.2)

