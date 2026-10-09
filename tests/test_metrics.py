"""Test unitari per le metriche su traiettorie di log-wealth."""

import numpy as np
import pytest

from shk.kelly.metrics import (
    final_log_wealth,
    median_growth_rate,
    median_final_wealth,
    mean_final_wealth,
    max_drawdown,
    fraction_below_start,
    wealth_max_drawdown,
    wealth_recovery_time,
)


@pytest.fixture
def sample_paths() -> np.ndarray:
    """Fornisce una matrice di log-wealth costruita a mano con 3 traiettorie e T=4."""
    # Traiettoria 0: picco a t=1 (B=2.0), minimo a t=3 (B=1.0), recupero a t=4 (B=1.8)
    traj0 = [0.0, np.log(2.0), np.log(1.5), np.log(1.0), np.log(1.8)]
    # Traiettoria 1: strettamente crescente (B finale = 2.0)
    traj1 = [0.0, np.log(1.2), np.log(1.4), np.log(1.6), np.log(2.0)]
    # Traiettoria 2: strettamente decrescente (B finale = 0.5)
    traj2 = [0.0, np.log(0.9), np.log(0.8), np.log(0.7), np.log(0.5)]

    return np.array([traj0, traj1, traj2], dtype=float)


def test_final_log_wealth(sample_paths):
    """Verifica l'estrazione corretta dell'ultima colonna del log-wealth."""
    final = final_log_wealth(sample_paths)
    expected = np.array([np.log(1.8), np.log(2.0), np.log(0.5)])
    np.testing.assert_allclose(final, expected)


def test_median_growth_rate(sample_paths):
    """Verifica il calcolo del tasso di crescita mediano per scommessa."""
    t_steps = 4
    final = np.array([np.log(1.8), np.log(2.0), np.log(0.5)])
    expected = float(np.median(final) / t_steps)

    actual = median_growth_rate(sample_paths)
    assert actual == pytest.approx(expected)


def test_median_final_wealth(sample_paths):
    """Verifica la mediana del capitale finale B_T = exp(mediana(ln(B_T)))."""
    final = np.array([np.log(1.8), np.log(2.0), np.log(0.5)])
    expected = float(np.exp(np.median(final)))

    actual = median_final_wealth(sample_paths)
    assert actual == pytest.approx(expected)


def test_mean_final_wealth(sample_paths):
    """Verifica la media aritmetica empirica del capitale finale B_T."""
    # Valori di B_T: 1.8, 2.0, 0.5 -> media = (1.8 + 2.0 + 0.5) / 3 = 4.3 / 3
    expected = (1.8 + 2.0 + 0.5) / 3.0

    actual = mean_final_wealth(sample_paths)
    assert actual == pytest.approx(expected)


def test_max_drawdown_exact_values(sample_paths):
    """Verifica il calcolo esatto del drawdown massimo relativo per ciascuna traiettoria."""
    # Traiettoria 0: picco 2.0, discesa minima a 1.0 -> dd = (2.0 - 1.0) / 2.0 = 0.50
    # Traiettoria 1: monotona crescente -> dd = 0.0
    # Traiettoria 2: picco 1.0 a t=0, minimo a 0.5 -> dd = (1.0 - 0.5) / 1.0 = 0.50
    expected = np.array([0.50, 0.0, 0.50])

    actual = max_drawdown(sample_paths)
    np.testing.assert_allclose(actual, expected, atol=1e-12)


def test_fraction_below_start(sample_paths):
    """Verifica la quota di traiettorie che chiudono al di sotto del capitale iniziale."""
    # Traiettorie con B_T < B_0 (ossia ln(B_T) < 0): solo traiettoria 2 (B_T = 0.5)
    # Frazione = 1 / 3
    expected = 1.0 / 3.0

    actual = fraction_below_start(sample_paths)
    assert actual == pytest.approx(expected)


def test_metrics_error_conditions():
    """Verifica che tutte le funzioni sollevino ValueError per input di forma errata."""
    # Array 1D non consentito
    paths_1d = np.array([0.0, 1.0, 2.0])
    with pytest.raises(ValueError):
        final_log_wealth(paths_1d)
    with pytest.raises(ValueError):
        max_drawdown(paths_1d)
    with pytest.raises(ValueError):
        fraction_below_start(paths_1d)

    # Array con meno di 2 colonne (nessun passo temporale, solo t=0)
    paths_no_steps = np.array([[0.0], [0.0]])
    with pytest.raises(ValueError):
        final_log_wealth(paths_no_steps)
    with pytest.raises(ValueError):
        median_growth_rate(paths_no_steps)
    with pytest.raises(ValueError):
        max_drawdown(paths_no_steps)
    with pytest.raises(ValueError):
        fraction_below_start(paths_no_steps)


def test_wealth_max_drawdown_and_recovery_handcrafted() -> None:
    """Verifica wealth_max_drawdown e wealth_recovery_time su casi noti scritti a mano."""
    # Caso 1: [1, 1.2, 0.6, 0.9, 1.2, 1.0] -> max drawdown 0.5 a t*=2, picco 1.2, recupero a t=4 (tempo 2, recovered True)
    w1 = np.array([[1.0, 1.2, 0.6, 0.9, 1.2, 1.0]], dtype=np.float64)
    dd1 = wealth_max_drawdown(w1)
    np.testing.assert_allclose(dd1, [0.5], atol=1e-12)
    t1, rec1 = wealth_recovery_time(w1)
    np.testing.assert_array_equal(t1, [2])
    np.testing.assert_array_equal(rec1, [True])

    # Caso 2: senza recupero [1.0, 1.2, 0.6, 0.9, 1.0] -> max drawdown 0.5 a t*=2, non recupera (tempo -1, recovered False)
    w2 = np.array([[1.0, 1.2, 0.6, 0.9, 1.0]], dtype=np.float64)
    dd2 = wealth_max_drawdown(w2)
    np.testing.assert_allclose(dd2, [0.5], atol=1e-12)
    t2, rec2 = wealth_recovery_time(w2)
    np.testing.assert_array_equal(t2, [-1])
    np.testing.assert_array_equal(rec2, [False])

    # Caso 3: monotono [1.0, 1.1, 1.2, 1.5] -> drawdown 0.0, tempo 0, recovered True
    w3 = np.array([[1.0, 1.1, 1.2, 1.5]], dtype=np.float64)
    dd3 = wealth_max_drawdown(w3)
    np.testing.assert_allclose(dd3, [0.0], atol=1e-12)
    t3, rec3 = wealth_recovery_time(w3)
    np.testing.assert_array_equal(t3, [0])
    np.testing.assert_array_equal(rec3, [True])

    # Caso 4: con W = 0 [1.0, 0.5, 0.0, 0.0] -> drawdown 1.0, tempo -1, recovered False
    w4 = np.array([[1.0, 0.5, 0.0, 0.0]], dtype=np.float64)
    dd4 = wealth_max_drawdown(w4)
    np.testing.assert_allclose(dd4, [1.0], atol=1e-12)
    t4, rec4 = wealth_recovery_time(w4)
    np.testing.assert_array_equal(t4, [-1])
    np.testing.assert_array_equal(rec4, [False])


def test_wealth_metrics_validation() -> None:
    """Verifica le validazioni di tipo e valore per wealth_max_drawdown e wealth_recovery_time."""
    # Tipo non ndarray
    with pytest.raises(TypeError, match="wealth must be a numpy.ndarray"):
        wealth_max_drawdown([[1.0, 1.2], [1.0, 0.8]])  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="wealth must be a numpy.ndarray"):
        wealth_recovery_time([[1.0, 1.2], [1.0, 0.8]])  # type: ignore[arg-type]

    # Dtype non numerico reale
    with pytest.raises(TypeError, match="wealth must have a real numeric dtype"):
        wealth_max_drawdown(np.array([[True, False], [True, True]]))
    with pytest.raises(TypeError, match="wealth must have a real numeric dtype"):
        wealth_recovery_time(np.array([["1.0", "1.2"], ["1.0", "0.8"]]))

    # Dimensioni non 2D
    with pytest.raises(ValueError, match="wealth must be a 2D array"):
        wealth_max_drawdown(np.array([1.0, 1.2]))
    with pytest.raises(ValueError, match="wealth must be a 2D array"):
        wealth_recovery_time(np.ones((2, 2, 2)))

    # Meno di 2 colonne
    with pytest.raises(ValueError, match="wealth must have at least 2 columns"):
        wealth_max_drawdown(np.array([[1.0], [2.0]]))
    with pytest.raises(ValueError, match="wealth must have at least 2 columns"):
        wealth_recovery_time(np.array([[1.0], [2.0]]))

    # Valori non finiti
    with pytest.raises(ValueError, match="wealth must contain only finite values"):
        wealth_max_drawdown(np.array([[1.0, np.nan], [1.0, 2.0]]))
    with pytest.raises(ValueError, match="wealth must contain only finite values"):
        wealth_recovery_time(np.array([[1.0, np.inf], [1.0, 2.0]]))

    # Valori negativi
    with pytest.raises(ValueError, match="wealth values must be non-negative"):
        wealth_max_drawdown(np.array([[1.0, -0.1], [1.0, 2.0]]))
    with pytest.raises(ValueError, match="wealth values must be non-negative"):
        wealth_recovery_time(np.array([[1.0, -0.5], [1.0, 2.0]]))

    # Colonna 0 <= 0
    with pytest.raises(ValueError, match="Initial wealth \\(column 0\\) must be strictly positive"):
        wealth_max_drawdown(np.array([[0.0, 1.0], [1.0, 2.0]]))
    with pytest.raises(ValueError, match="Initial wealth \\(column 0\\) must be strictly positive"):
        wealth_recovery_time(np.array([[0.0, 1.0], [1.0, 2.0]]))


def test_wealth_max_drawdown_matches_log_max_drawdown() -> None:
    """Verifica che wealth_max_drawdown coincida entro 1e-12 con max_drawdown(np.log(wealth))."""
    rng = np.random.default_rng(20261009)
    # 20 traiettorie positive di lunghezza 30 con W0 = 1.0
    m_paths = 20
    d_steps = 30
    log_increments = rng.normal(loc=0.01, scale=0.05, size=(m_paths, d_steps))
    log_wealth = np.hstack([np.zeros((m_paths, 1)), np.cumsum(log_increments, axis=1)])
    wealth = np.exp(log_wealth)

    w_dd = wealth_max_drawdown(wealth)
    log_dd = max_drawdown(log_wealth)

    np.testing.assert_allclose(w_dd, log_dd, rtol=1e-12, atol=1e-12)


