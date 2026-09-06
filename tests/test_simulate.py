"""Test unitari per il modulo di simulazione."""

import numpy as np
import pytest

from shk.kelly.simulate import draw_outcomes, log_wealth_paths


def test_draw_outcomes_shape_and_dtype():
    """Verifica che draw_outcomes restituisca un array booleano con la forma corretta."""
    rng = np.random.default_rng(42)
    m, t = 50, 100
    outcomes = draw_outcomes(0.60, t, m, rng)

    assert isinstance(outcomes, np.ndarray)
    assert outcomes.shape == (m, t)
    assert outcomes.dtype == bool


def test_draw_outcomes_reproducibility():
    """Verifica che lo stesso seed del generatore produca estrazioni identiche."""
    rng1 = np.random.default_rng(12345)
    rng2 = np.random.default_rng(12345)
    outcomes1 = draw_outcomes(0.60, 200, 100, rng1)
    outcomes2 = draw_outcomes(0.60, 200, 100, rng2)

    np.testing.assert_array_equal(outcomes1, outcomes2)


def test_draw_outcomes_empirical_mean():
    """Verifica che la media empirica degli esiti sia vicina alla probabilità teorica p."""
    rng = np.random.default_rng(999)
    p = 0.60
    m, t = 1000, 500
    outcomes = draw_outcomes(p, t, m, rng)

    empirical_p = np.mean(outcomes)
    assert abs(empirical_p - p) < 0.01


def test_draw_outcomes_invalid_inputs():
    """Verifica che vengano sollevate le eccezioni opportune per parametri non validi."""
    rng = np.random.default_rng(42)

    # Probabilità non valida
    with pytest.raises(ValueError):
        draw_outcomes(-0.1, 10, 10, rng)
    with pytest.raises(ValueError):
        draw_outcomes(1.1, 10, 10, rng)

    # Numero di passi non valido
    with pytest.raises(ValueError):
        draw_outcomes(0.60, 0, 10, rng)
    with pytest.raises(ValueError):
        draw_outcomes(0.60, -5, 10, rng)

    # Numero di traiettorie non valido
    with pytest.raises(ValueError):
        draw_outcomes(0.60, 10, 0, rng)
    with pytest.raises(ValueError):
        draw_outcomes(0.60, 10, -3, rng)

    # Generatore non valido
    with pytest.raises(TypeError):
        draw_outcomes(0.60, 10, 10, "not_a_generator")  # type: ignore


def test_log_wealth_paths_hand_calculated_values():
    """Verifica i valori di log-wealth calcolati a mano su una traiettoria semplice.

    Nota: questo test fallirà con NotImplementedError fino a quando la funzione
    non verrà implementata manualmente.
    """
    outcomes = np.array([[True, False]], dtype=bool)
    f = 0.20
    b = 1.0

    # Atteso: [[0.0, ln(1 + b*f), ln(1 + b*f) + ln(1 - f)]]
    expected = np.array([[0.0, np.log(1.2), np.log(1.2) + np.log(0.8)]], dtype=float)

    actual = log_wealth_paths(outcomes, f, b)
    np.testing.assert_allclose(actual, expected, rtol=1e-12)


def test_log_wealth_paths_shape_and_initial_column():
    """Verifica la forma (M, T+1) e che la colonna iniziale al tempo zero sia nulla.

    Nota: questo test fallirà con NotImplementedError fino a quando la funzione
    non verrà implementata manualmente.
    """
    rng = np.random.default_rng(7)
    m, t = 10, 25
    outcomes = draw_outcomes(0.60, t, m, rng)

    paths = log_wealth_paths(outcomes, 0.20, 1.0)
    assert paths.shape == (m, t + 1)
    np.testing.assert_allclose(paths[:, 0], 0.0)

