"""Test di accettazione per l'esperimento US-C1.2 (stima e asimmetria di Kelly)."""

import numpy as np
import pytest

from shk.kelly.core import kelly_fraction
from shk.kelly.simulate import log_wealth_paths
from shk.kelly.metrics import median_growth_rate
from shk.kelly.estimation import noisy_estimates
from shk.kelly.staking import kelly_staking, staking_moments
from shk.kelly.scenarios import (
    BASE_SCENARIO,
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


@pytest.mark.slow
def test_acceptance_base_scenario_var_c():
    """Verifica che nello scenario base con rumore sigma_p = 0.0283:
    1. Var(c) disti meno di 0.005 dal riferimento teorico (o*sigma_p/EV)^2;
    2. Var(c) < 1 (il segnale domina l'errore di stima).
    """
    sigma_p = 0.0283
    _, rng_noise = spawn_generators(SEED)
    p_hat = noisy_estimates(
        BASE_SCENARIO.p, sigma_p, BASE_SCENARIO.T, BASE_SCENARIO.M, rng_noise
    )
    f_hat = kelly_staking(p_hat, BASE_SCENARIO.b, lam=1.0)
    f_star = kelly_fraction(BASE_SCENARIO.p, BASE_SCENARIO.b)
    moments = staking_moments(f_hat, f_star)

    # Criterio 1: vicinanza al riferimento calcolato dinamicamente dai parametri dello scenario
    o = BASE_SCENARIO.b + 1.0
    ev = BASE_SCENARIO.p * o - 1.0
    reference = ((o * sigma_p) / ev) ** 2
    assert abs(moments.var_c - reference) < 0.005

    # Criterio 2: Var(c) < 1
    assert moments.var_c < 1.0


@pytest.mark.slow
def test_acceptance_subtle_scenario_var_c_dominance():
    """Verifica che nello scenario sottile con rumore sigma_p = 0.0283:
    3. Var(c) > 1 (l'errore di stima domina il segnale).
    """
    sigma_p = 0.0283
    _, rng_noise = spawn_generators(SEED)
    p_hat = noisy_estimates(
        SUBTLE_SCENARIO.p, sigma_p, SUBTLE_SCENARIO.T, SUBTLE_SCENARIO.M, rng_noise
    )
    f_hat = kelly_staking(p_hat, SUBTLE_SCENARIO.b, lam=1.0)
    f_star = kelly_fraction(SUBTLE_SCENARIO.p, SUBTLE_SCENARIO.b)
    moments = staking_moments(f_hat, f_star)

    # Criterio 3: Var(c) > 1
    assert moments.var_c > 1.0


@pytest.mark.slow
def test_acceptance_base_lambda_star_beats_quarter_kelly():
    """Verifica che nello scenario base con sigma_p = 0.0283, lambda* batta lambda = 0.25."""
    scenario = BASE_SCENARIO
    sigma_p = 0.0283
    rng_outcomes, rng_noise = spawn_generators(SEED)
    outcomes = draw_scenario_outcomes(scenario, rng_outcomes)
    p_hat = noisy_estimates(scenario.p, sigma_p, scenario.T, scenario.M, rng_noise)

    f_hat = kelly_staking(p_hat, scenario.b, lam=1.0)
    f_star = kelly_fraction(scenario.p, scenario.b)
    moments = staking_moments(f_hat, f_star)
    lam_star = 1.0 / (1.0 + moments.var_c)

    paths_star = simulate_scenario(scenario, outcomes, p_hat, lam=lam_star)
    paths_quarter = simulate_scenario(scenario, outcomes, p_hat, lam=0.25)

    g_star = median_growth_rate(paths_star)
    g_quarter = median_growth_rate(paths_quarter)

    assert g_star > g_quarter


@pytest.mark.slow
def test_acceptance_subtle_lambda_star_beats_quarter_kelly():
    """Verifica che nello scenario sottile con sigma_p = 0.0283, lambda* batta lambda = 0.25."""
    scenario = SUBTLE_SCENARIO
    sigma_p = 0.0283
    rng_outcomes, rng_noise = spawn_generators(SEED)
    outcomes = draw_scenario_outcomes(scenario, rng_outcomes)
    p_hat = noisy_estimates(scenario.p, sigma_p, scenario.T, scenario.M, rng_noise)

    f_hat = kelly_staking(p_hat, scenario.b, lam=1.0)
    f_star = kelly_fraction(scenario.p, scenario.b)
    moments = staking_moments(f_hat, f_star)
    lam_star = 1.0 / (1.0 + moments.var_c)

    paths_star = simulate_scenario(scenario, outcomes, p_hat, lam=lam_star)
    paths_quarter = simulate_scenario(scenario, outcomes, p_hat, lam=0.25)

    g_star = median_growth_rate(paths_star)
    g_quarter = median_growth_rate(paths_quarter)

    assert g_star > g_quarter


