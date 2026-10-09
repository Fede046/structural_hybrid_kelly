"""Test unitari per il modulo shk.kelly.floor (Task 36)."""

import math

import numpy as np
import pytest

from shk.kelly.agents import FractionalKellyAgent
from shk.kelly.environment import floor_thresholds
from shk.kelly.floor import (
    classify_floor_regime,
    compute_ruin_rates_at_horizons,
    compute_ruin_times,
    draw_synthetic_outcomes,
    expected_ruin_time_bound,
    run_paired_chunked,
    synthetic_calendar,
    synthetic_match_data,
    two_sample_mc_tolerance,
)


def test_classify_floor_regime_handcrafted() -> None:
    """Verifica che classify_floor_regime assegni correttamente i 4 regimi."""
    thresholds = (200.0, 25.0, 1.0)  # B1=200, B2=25, F=1
    w = np.array([250.0, 200.0, 199.9, 25.0, 24.9, 1.0, 0.99, 0.0])
    regimes = classify_floor_regime(w, thresholds)

    expected = np.array([0, 0, 1, 1, 2, 2, 3, 3], dtype=np.int64)
    assert np.array_equal(regimes, expected)

    # Validazioni errori
    with pytest.raises(TypeError, match="wealth must be a numpy.ndarray"):
        classify_floor_regime([100.0], thresholds)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="thresholds must be a tuple"):
        classify_floor_regime(w, (200.0, 25.0))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Thresholds must satisfy B1 > B2 > B3 > 0"):
        classify_floor_regime(w, (20.0, 25.0, 1.0))


def test_expected_ruin_time_bound_handcrafted() -> None:
    """Verifica il calcolo analitico del tempo medio teorico di rovina."""
    # Test caso con drift negativo noto
    bound = expected_ruin_time_bound(rapporto=50.0, p=0.4, f=0.1, o=2.0)
    # mu = 0.4 * ln(1 + 0.1*1) + 0.6 * ln(1 - 0.1) = 0.4 * ln(1.1) + 0.6 * ln(0.9)
    # mu = 0.4 * 0.095310 - 0.6 * 0.105360 = 0.038124 - 0.063216 = -0.025092
    # bound = ln(50) / 0.025092 = 3.912023 / 0.025092 = 155.9
    expected_mu = 0.4 * math.log(1.1) + 0.6 * math.log(0.9)
    expected_bound = math.log(50.0) / abs(expected_mu)
    assert math.isclose(bound, expected_bound, rel_tol=1e-12)

    # Errore con drift positivo (p=0.6, o=2.0, f=0.1 -> edge positivo)
    with pytest.raises(ValueError, match="Expected log drift must be strictly negative"):
        expected_ruin_time_bound(rapporto=50.0, p=0.6, f=0.1, o=2.0)

    # Validazione ingressi non validi
    with pytest.raises(ValueError, match="rapporto must be strictly greater than 1.0"):
        expected_ruin_time_bound(rapporto=0.5, p=0.4, f=0.1, o=2.0)
    with pytest.raises(ValueError, match="p must be in"):
        expected_ruin_time_bound(rapporto=50.0, p=1.2, f=0.1, o=2.0)


def test_expected_ruin_time_bound_reproduces_note_within_half_percent() -> None:
    """Verifica che expected_ruin_time_bound riproduca i valori della Nota 2.9 §6.2 entro lo 0.5%."""
    # Caso a: o=2.5, EV=-0.02 -> p=0.98/2.5=0.392, edge=0.03 -> p_hat=1.03/2.5, lam=0.25 -> f=0.005, rapporto=50
    p_a = (1.0 - 0.02) / 2.5
    f_a = 0.005
    bound_a = expected_ruin_time_bound(50.0, p_a, f_a, 2.5)
    mu_a = p_a * math.log(1.0 + f_a * 1.5) + (1.0 - p_a) * math.log(1.0 - f_a)

    assert math.isclose(mu_a, -0.000119, rel_tol=0.005)
    assert math.isclose(bound_a, 32986.0, rel_tol=0.005)

    # Caso b (la nota arrotonda e usa f = 0.0667): o=2.5, EV=-0.04 -> p=0.96/2.5=0.384, f=0.0667, rapporto=220
    p_b = (1.0 - 0.04) / 2.5
    f_b_note = 0.0667
    bound_b = expected_ruin_time_bound(220.0, p_b, f_b_note, 2.5)
    mu_b = p_b * math.log(1.0 + f_b_note * 1.5) + (1.0 - p_b) * math.log(1.0 - f_b_note)

    assert math.isclose(mu_b, -0.005905, rel_tol=0.005)
    assert math.isclose(bound_b, 913.0, rel_tol=0.005)

    # Caso c: o=2.5, EV=-0.05 -> p=0.95/2.5=0.38, f=0.02, rapporto=200
    p_c = (1.0 - 0.05) / 2.5
    f_c = 0.02
    bound_c = expected_ruin_time_bound(200.0, p_c, f_c, 2.5)
    mu_c = p_c * math.log(1.0 + f_c * 1.5) + (1.0 - p_c) * math.log(1.0 - f_c)

    assert math.isclose(mu_c, -0.001293, rel_tol=0.005)
    assert math.isclose(bound_c, 4097.0, rel_tol=0.005)


def test_two_sample_mc_tolerance_handcrafted() -> None:
    """Verifica il calcolo della tolleranza Monte Carlo a due campioni."""
    # Test simmetrico
    tol = two_sample_mc_tolerance(0.10, 0.10, 10_000, 80_000, z=2.576)
    r_bar = 0.10
    expected_var = 0.10 * 0.90 * (1.0 / 10_000 + 1.0 / 80_000)
    expected_tol = 2.576 * math.sqrt(expected_var)
    assert math.isclose(tol, expected_tol, rel_tol=1e-12)

    # Casi limite r=0
    assert two_sample_mc_tolerance(0.0, 0.0, 10_000, 80_000) == 0.0


def test_synthetic_calendar_and_match_data() -> None:
    """Verifica calendario e dati di quota/probabilita sintetici."""
    dates = synthetic_calendar(10)
    assert dates.shape == (10,)
    assert np.issubdtype(dates.dtype, np.datetime64)
    assert np.all(dates[1:] > dates[:-1])

    probs, odds = synthetic_match_data(p_hat=0.412, odds_val=2.5, n_dates=10)
    assert probs.shape == (10, 3)
    assert odds.shape == (10, 3)
    assert np.allclose(probs.sum(axis=1), 1.0)
    assert np.all(odds[:, 0] == 2.5)
    assert np.all(odds[:, 1] == 2.0)
    assert np.all(odds[:, 2] == 2.0)

    # EV stimato: H deve essere l'unico positivo
    ev_h = probs[:, 0] * odds[:, 0] - 1.0
    ev_d = probs[:, 1] * odds[:, 1] - 1.0
    ev_a = probs[:, 2] * odds[:, 2] - 1.0
    assert np.all(ev_h > 0.0)
    assert np.all(ev_d < 0.0)
    assert np.all(ev_a < 0.0)


def test_draw_synthetic_outcomes_properties() -> None:
    """Verifica le proprieta degli esiti sintetici estratti."""
    rng = np.random.default_rng(12345)
    outcomes = draw_synthetic_outcomes(p=0.40, m_replicas=5000, n_dates=100, rng=rng)
    assert outcomes.shape == (5000, 100)
    assert set(np.unique(outcomes)).issubset({0, 1})
    p_emp = float(np.mean(outcomes == 0))
    assert math.isclose(p_emp, 0.40, abs_tol=0.01)


def test_compute_ruin_rates_and_times() -> None:
    """Verifica il calcolo di tassi e tempi di rovina."""
    # M=3, D=3 (4 colonne)
    wealth = np.array(
        [
            [1.0, 0.8, 0.015, 0.010],  # F=0.02 -> rovinata a t=2
            [1.0, 1.2, 1.5, 2.0],  # mai rovinata
            [1.0, 0.010, 0.010, 0.010],  # F=0.02 -> rovinata a t=1
        ]
    )
    rates = compute_ruin_rates_at_horizons(wealth, min_stake=0.02, horizons=[1, 2, 3])
    assert math.isclose(rates[1], 1.0 / 3.0)
    assert math.isclose(rates[2], 2.0 / 3.0)
    assert math.isclose(rates[3], 2.0 / 3.0)

    times, ruined = compute_ruin_times(wealth, min_stake=0.02)
    assert np.array_equal(ruined, np.array([True, False, True]))
    assert np.array_equal(times, np.array([2, -1, 1]))


def test_chunked_execution_matches_single_chunk() -> None:
    """Verifica che l'esecuzione a blocchi coincida esattamente con il blocco singolo."""
    rng = np.random.default_rng(20261009)
    m_replicas = 30
    n_dates = 25
    p_true = 0.392
    p_hat = 0.412
    odds_val = 2.5
    min_stake = 0.02

    dates = synthetic_calendar(n_dates)
    probs, odds = synthetic_match_data(p_hat, odds_val, n_dates)
    outcomes = draw_synthetic_outcomes(p_true, m_replicas, n_dates, rng)

    agent = FractionalKellyAgent("TestKelly", lam=0.25)

    run_single = run_paired_chunked(
        agent=agent,
        dates=dates,
        probs=probs,
        odds=odds,
        outcomes=outcomes,
        min_stake=min_stake,
        chunk_size=m_replicas,  # blocco unico
        record_stakes=True,
    )

    run_chunked = run_paired_chunked(
        agent=agent,
        dates=dates,
        probs=probs,
        odds=odds,
        outcomes=outcomes,
        min_stake=min_stake,
        chunk_size=7,  # 5 blocchi (7, 7, 7, 7, 2)
        record_stakes=True,
    )

    assert np.array_equal(run_single.wealth, run_chunked.wealth)
    assert np.array_equal(run_single.ruined, run_chunked.ruined)
    assert np.array_equal(run_single.ruin_date_index, run_chunked.ruin_date_index)
    assert np.array_equal(run_single.n_bets, run_chunked.n_bets)
    assert np.array_equal(run_single.n_forced, run_chunked.n_forced)
    assert np.array_equal(run_single.n_floored, run_chunked.n_floored)
    assert np.array_equal(run_single.n_dropped, run_chunked.n_dropped)
    assert run_single.staked is not None and run_chunked.staked is not None
    assert np.array_equal(run_single.staked, run_chunked.staked)
    assert run_single.desired is not None and run_chunked.desired is not None
    assert np.array_equal(run_single.desired, run_chunked.desired)
