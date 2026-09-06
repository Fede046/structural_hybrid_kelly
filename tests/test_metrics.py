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

