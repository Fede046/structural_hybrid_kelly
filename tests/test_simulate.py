"""Test unitari per il modulo di simulazione."""

import numpy as np
import pytest

from shk.kelly.simulate import draw_outcomes, log_wealth_paths, simulate_growth


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
    """Verifica i valori di log-wealth calcolati a mano su una traiettoria semplice."""
    outcomes = np.array([[True, False]], dtype=bool)
    f = 0.20
    b = 1.0

    # Atteso: [[0.0, ln(1 + b*f), ln(1 + b*f) + ln(1 - f)]]
    expected = np.array([[0.0, np.log(1.2), np.log(1.2) + np.log(0.8)]], dtype=float)

    actual = log_wealth_paths(outcomes, f, b)
    np.testing.assert_allclose(actual, expected, rtol=1e-12)


def test_log_wealth_paths_shape_and_initial_column():
    """Verifica la forma (M, T+1) e che la colonna iniziale al tempo zero sia nulla."""
    rng = np.random.default_rng(7)
    m, t = 10, 25
    outcomes = draw_outcomes(0.60, t, m, rng)

    paths = log_wealth_paths(outcomes, 0.20, 1.0)
    assert paths.shape == (m, t + 1)
    np.testing.assert_allclose(paths[:, 0], 0.0)


def test_simulate_growth_broadcast_shapes():
    """Verifica che simulate_growth accetti forme scalari, (T,), (1, T), (M, 1) e (M, T)."""
    rng = np.random.default_rng(21)
    m, t = 8, 15
    outcomes = draw_outcomes(0.60, t, m, rng)
    b = 1.0

    shapes_to_test = [
        0.15,                        # Scalare float
        np.full((t,), 0.15),         # 1D per passo (T,)
        np.full((1, t), 0.15),       # 2D riga (1, T)
        np.full((m, 1), 0.15),       # 2D colonna per traiettoria (M, 1)
        np.full((m, t), 0.15),       # 2D matrice completa (M, T)
    ]

    for fractions in shapes_to_test:
        paths = simulate_growth(outcomes, fractions, b)
        assert isinstance(paths, np.ndarray)
        assert paths.shape == (m, t + 1)
        assert paths.dtype == np.float64
        np.testing.assert_allclose(paths[:, 0], 0.0)


def test_simulate_growth_hand_calculated_case():
    """Verifica il caso analitico calcolato a mano con M=1, T=3 e frazioni variabili nel tempo."""
    outcomes = np.array([[True, False, True]], dtype=bool)
    fractions = np.array([0.1, 0.2, 0.3])
    b = 1.0

    # Atteso: 0, ln(1.1), ln(1.1) + ln(0.8), ln(1.1) + ln(0.8) + ln(1.3)
    expected = np.array(
        [[0.0, np.log(1.1), np.log(1.1) + np.log(0.8), np.log(1.1) + np.log(0.8) + np.log(1.3)]],
        dtype=float,
    )

    actual = simulate_growth(outcomes, fractions, b)
    np.testing.assert_allclose(actual, expected, rtol=1e-12)


def test_simulate_growth_scalar_matrix_equivalence():
    """Verifica che una frazione scalare e una matrice costante (M, T) producano lo stesso risultato."""
    rng = np.random.default_rng(101)
    m, t = 20, 50
    outcomes = draw_outcomes(0.55, t, m, rng)
    f_scalar = 0.18
    f_matrix = np.full((m, t), f_scalar)
    b = 1.2

    paths_scalar = simulate_growth(outcomes, f_scalar, b)
    paths_matrix = simulate_growth(outcomes, f_matrix, b)

    np.testing.assert_allclose(paths_scalar, paths_matrix, rtol=1e-12)


def test_simulate_growth_validation_errors():
    """Verifica che simulate_growth sollevi le eccezioni previste per input non validi."""
    outcomes = np.array([[True, False, True], [False, True, False]], dtype=bool)  # Shape (2, 3)
    b = 1.0

    # Frazioni inferiori a 0
    with pytest.raises(ValueError, match="All elements of fractions must be in \\[0, 1\\)"):
        simulate_growth(outcomes, -0.05, b)
    with pytest.raises(ValueError, match="All elements of fractions must be in \\[0, 1\\)"):
        simulate_growth(outcomes, np.array([0.1, -0.2, 0.1]), b)

    # Frazioni maggiori o uguali a 1
    with pytest.raises(ValueError, match="All elements of fractions must be in \\[0, 1\\)"):
        simulate_growth(outcomes, 1.0, b)
    with pytest.raises(ValueError, match="All elements of fractions must be in \\[0, 1\\)"):
        simulate_growth(outcomes, 1.2, b)
    with pytest.raises(ValueError, match="All elements of fractions must be in \\[0, 1\\)"):
        simulate_growth(outcomes, np.array([0.1, 1.0, 0.2]), b)

    # Frazioni non finite (NaN o Inf)
    with pytest.raises(ValueError, match="All elements of fractions must be finite"):
        simulate_growth(outcomes, np.nan, b)
    with pytest.raises(ValueError, match="All elements of fractions must be finite"):
        simulate_growth(outcomes, np.inf, b)
    with pytest.raises(ValueError, match="All elements of fractions must be finite"):
        simulate_growth(outcomes, np.array([0.1, np.nan, 0.2]), b)

    # Quota b non positiva
    with pytest.raises(ValueError, match="Odds 'b' must be strictly positive"):
        simulate_growth(outcomes, 0.1, 0.0)
    with pytest.raises(ValueError, match="Odds 'b' must be strictly positive"):
        simulate_growth(outcomes, 0.1, -1.0)

    # Forma frazioni non broadcastabile: vettore 1D di lunghezza M con M != T
    with pytest.raises(ValueError, match="cannot be broadcast to outcomes shape"):
        simulate_growth(outcomes, np.array([0.1, 0.2]), b)  # Lunghezza 2 != T (3)

    # Forma frazioni non broadcastabile: 2D incompatibile
    with pytest.raises(ValueError, match="cannot be broadcast to outcomes shape"):
        simulate_growth(outcomes, np.full((3, 3), 0.1), b)
    with pytest.raises(ValueError, match="cannot be broadcast to outcomes shape"):
        simulate_growth(outcomes, np.full((2, 4), 0.1), b)

    # Frazioni con più di 2 dimensioni
    with pytest.raises(ValueError, match="at most 2 dimensions are allowed"):
        simulate_growth(outcomes, np.full((1, 2, 3), 0.1), b)

    # Outcomes non ndarray
    with pytest.raises(TypeError, match="outcomes must be an instance of np.ndarray"):
        simulate_growth([[True, False, True], [False, True, False]], 0.1, b)  # type: ignore

    # Outcomes non booleano
    with pytest.raises(TypeError, match="outcomes must have boolean dtype"):
        simulate_growth(np.array([[1, 0, 1], [0, 1, 0]]), 0.1, b)
    with pytest.raises(TypeError, match="outcomes must have boolean dtype"):
        simulate_growth(np.array([[1.0, 0.0, 1.0], [0.0, 1.0, 0.0]]), 0.1, b)

    # Outcomes non 2D
    with pytest.raises(ValueError, match="outcomes must be a 2D array"):
        simulate_growth(np.array([True, False, True]), 0.1, b)
    with pytest.raises(ValueError, match="outcomes must be a 2D array"):
        simulate_growth(np.ones((2, 3, 2), dtype=bool), 0.1, b)

    # Outcomes con dimensioni non positive
    with pytest.raises(ValueError, match="dimensions M and T must be strictly positive"):
        simulate_growth(np.zeros((0, 3), dtype=bool), 0.1, b)
    with pytest.raises(ValueError, match="dimensions M and T must be strictly positive"):
        simulate_growth(np.zeros((2, 0), dtype=bool), 0.1, b)


def test_log_wealth_paths_delegation_and_validation():
    """Verifica che log_wealth_paths deleghi a simulate_growth e ne erediti la validazione."""
    outcomes = np.array([[True, False], [False, True]], dtype=bool)

    # Risultato identico a simulate_growth
    actual_lwp = log_wealth_paths(outcomes, 0.20, 1.0)
    actual_sg = simulate_growth(outcomes, 0.20, 1.0)
    np.testing.assert_array_equal(actual_lwp, actual_sg)

    # Validazione propagata
    with pytest.raises(ValueError):
        log_wealth_paths(outcomes, -0.1, 1.0)
    with pytest.raises(ValueError):
        log_wealth_paths(outcomes, 1.0, 1.0)
    with pytest.raises(ValueError):
        log_wealth_paths(outcomes, np.nan, 1.0)
    with pytest.raises(ValueError):
        log_wealth_paths(outcomes, 0.20, 0.0)
    with pytest.raises(TypeError):
        log_wealth_paths(np.array([[1, 0], [0, 1]]), 0.20, 1.0)
    with pytest.raises(ValueError):
        log_wealth_paths(np.array([True, False]), 0.20, 1.0)

