"""Test di accettazione per l'esperimento US-C1.1.

Tutti i test in questo modulo richiedono l'esecuzione della simulazione completa
e sono marcati con @pytest.mark.slow. Vengono deselezionati per impostazione
predefinita durante la normale esecuzione della suite di test.
"""

import numpy as np
import pytest

from shk.kelly.core import kelly_fraction
from shk.kelly.simulate import draw_outcomes, log_wealth_paths
from shk.kelly.metrics import median_growth_rate, max_drawdown


@pytest.mark.slow
def test_acceptance_median_growth_argmax_at_kelly():
    """Verifica che l'argmax del tasso di crescita mediano sulla griglia cada a lambda = 1."""
    p: float = 0.60
    b: float = 1.0
    t_steps: int = 1000
    m_trajectories: int = 10000
    rng = np.random.default_rng(20260905)

    f_star = kelly_fraction(p, b)
    lambdas = np.linspace(0.0, 2.5, 51)
    outcomes = draw_outcomes(p, t_steps, m_trajectories, rng)

    growth_rates = []
    for lam in lambdas:
        f_val = float(lam * f_star)
        paths = log_wealth_paths(outcomes, f_val, b)
        growth_rates.append(median_growth_rate(paths))
        del paths

    best_lambda = lambdas[int(np.argmax(growth_rates))]
    assert abs(best_lambda - 1.0) < 1e-6


@pytest.mark.slow
def test_acceptance_median_drawdown_non_decreasing():
    """Verifica che il drawdown mediano sia non decrescente in lambda (tolleranza MC < 0.01)."""
    p: float = 0.60
    b: float = 1.0
    t_steps: int = 1000
    m_trajectories: int = 10000
    rng = np.random.default_rng(20260905)

    f_star = kelly_fraction(p, b)
    lambdas = np.linspace(0.0, 2.5, 51)
    outcomes = draw_outcomes(p, t_steps, m_trajectories, rng)

    median_dds = []
    for lam in lambdas:
        f_val = float(lam * f_star)
        paths = log_wealth_paths(outcomes, f_val, b)
        dd = max_drawdown(paths)
        median_dds.append(float(np.median(dd)))
        del paths

    diffs = np.diff(median_dds)
    # Nessuna discesa locale deve essere più profonda di 0.01 dovuta al rumore campionario
    assert np.all(diffs >= -0.01)


@pytest.mark.slow
def test_acceptance_median_growth_at_zero_crossing():
    """Verifica che la crescita mediana a lambda = 1.946 soddisfi |g| < 0.002."""
    p: float = 0.60
    b: float = 1.0
    t_steps: int = 1000
    m_trajectories: int = 10000
    rng = np.random.default_rng(20260905)

    f_star = kelly_fraction(p, b)
    outcomes = draw_outcomes(p, t_steps, m_trajectories, rng)

    f_val = 1.946 * f_star
    paths = log_wealth_paths(outcomes, f_val, b)
    g_med = median_growth_rate(paths)

    assert abs(g_med) < 0.002


@pytest.mark.slow
def test_acceptance_median_growth_negative_at_lambda_2_5():
    """Verifica che la crescita mediana a lambda = 2.5 sia strettamente negativa."""
    p: float = 0.60
    b: float = 1.0
    t_steps: int = 1000
    m_trajectories: int = 10000
    rng = np.random.default_rng(20260905)

    f_star = kelly_fraction(p, b)
    outcomes = draw_outcomes(p, t_steps, m_trajectories, rng)

    f_val = 2.5 * f_star
    paths = log_wealth_paths(outcomes, f_val, b)
    g_med = median_growth_rate(paths)

    assert g_med < 0.0

