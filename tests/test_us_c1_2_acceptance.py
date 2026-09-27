"""Test di accettazione per l'esperimento US-C1.2 (stima e asimmetria di Kelly)."""

import numpy as np
import pytest

from shk.kelly.core import kelly_fraction
from shk.kelly.simulate import log_wealth_paths
from shk.kelly.metrics import median_growth_rate
from shk.kelly.scenarios import (
    Scenario,
    SUBTLE_SCENARIO,
    SEED,
    spawn_generators,
    draw_scenario_outcomes,
    simulate_scenario,
)


def test_acceptance_outcomes_independent_of_p_hat():
    """Verifica che gli esiti siano determinati dal seed e che simulate_scenario non muti outcomes."""
    small_scenario = Scenario(name="small", p=0.60, b=1.0, T=50, M=100)

    # Due generatori creati dallo stesso seed producono la stessa matrice di esiti
    rng1, _ = spawn_generators(SEED)
    rng2, _ = spawn_generators(SEED)
    outcomes1 = draw_scenario_outcomes(small_scenario, rng1)
    outcomes2 = draw_scenario_outcomes(small_scenario, rng2)
    np.testing.assert_array_equal(outcomes1, outcomes2)

    # Verifica che simulate_scenario non modifichi la matrice outcomes
    outcomes_copy = outcomes1.copy()
    _ = simulate_scenario(small_scenario, outcomes1, p_hat=0.50)
    np.testing.assert_array_equal(outcomes1, outcomes_copy)

    _ = simulate_scenario(small_scenario, outcomes1, p_hat=0.70)
    np.testing.assert_array_equal(outcomes1, outcomes_copy)


def test_acceptance_exact_agreement_when_p_hat_equals_p():
    """Verifica che con p_hat = p le traiettorie coincidano con log_wealth_paths teorico."""
    small_scenario = Scenario(name="small", p=0.60, b=1.0, T=50, M=100)
    rng, _ = spawn_generators(SEED)
    outcomes = draw_scenario_outcomes(small_scenario, rng)

    paths_scenario = simulate_scenario(small_scenario, outcomes, p_hat=small_scenario.p)
    f_star = kelly_fraction(small_scenario.p, small_scenario.b)
    paths_expected = log_wealth_paths(outcomes, f_star, small_scenario.b)

    np.testing.assert_allclose(paths_scenario, paths_expected, rtol=1e-12)


@pytest.mark.slow
def test_acceptance_subtle_scenario_overestimation_asymmetry():
    """Verifica che nello scenario sottile la sovrastima del 10% danneggi più della sottostima del 10%."""
    rng_outcomes, _ = spawn_generators(SEED)
    outcomes = draw_scenario_outcomes(SUBTLE_SCENARIO, rng_outcomes)

    # Sovrastima: p_hat = 1.1 * p = 0.572
    p_hat_over = 1.1 * SUBTLE_SCENARIO.p
    paths_over = simulate_scenario(SUBTLE_SCENARIO, outcomes, p_hat=p_hat_over)
    g_over = median_growth_rate(paths_over)

    # Sottostima: p_hat = 0.9 * p = 0.468 (frazione troncata a 0)
    p_hat_under = 0.9 * SUBTLE_SCENARIO.p
    paths_under = simulate_scenario(SUBTLE_SCENARIO, outcomes, p_hat=p_hat_under)
    g_under = median_growth_rate(paths_under)

    # Criterio 3: con sovrastima crescita negativa, con sottostima esattamente 0
    assert g_over < 0.0
    assert g_under == 0.0
    assert g_over < g_under
