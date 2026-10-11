"""Test per il modulo src/shk/market/devig.py."""

import numpy as np
import pytest

import shk.market.devig
from shk.market.devig import (
    devig_additive,
    devig_odds_ratio,
    devig_power,
    devig_proportional,
    devig_shin,
    implied_probabilities,
    overround,
)


def test_reference_values():
    """Verifica che i tre mercati di riferimento delle note di tesi 2.1 §7 siano riprodotti entro le tolleranze."""
    # Mercato 1: (8.0, 5.5, 1.33)
    m1 = np.array([[8.0, 5.5, 1.33]])
    ref_p1 = np.array([0.11807, 0.17174, 0.71019])
    ref_a1 = np.array([0.10543, 0.16225, 0.73231])
    ref_pow1 = np.array([0.10603, 0.15887, 0.73510])
    ref_k1 = 1.0791

    qp1 = devig_proportional(m1)[0]
    qa1 = devig_additive(m1)[0]
    qpow1, k1 = devig_power(m1)

    assert np.all(np.abs(qp1 - ref_p1) < 5e-6)
    assert np.all(np.abs(qa1 - ref_a1) < 5e-6)
    assert np.all(np.abs(qpow1[0] - ref_pow1) < 5e-6)
    assert abs(k1[0] - ref_k1) < 5e-5

    # Mercato 2: (1.25, 6.00, 11.0)
    m2 = np.array([[1.25, 6.00, 11.0]])
    ref_p2 = np.array([0.75645, 0.15759, 0.08596])
    ref_a2 = np.array([0.78081, 0.14747, 0.07172])
    ref_pow2 = np.array([0.78432, 0.14218, 0.07349])
    ref_k2 = 1.0887

    qp2 = devig_proportional(m2)[0]
    qa2 = devig_additive(m2)[0]
    qpow2, k2 = devig_power(m2)

    assert np.all(np.abs(qp2 - ref_p2) < 5e-6)
    assert np.all(np.abs(qa2 - ref_a2) < 5e-6)
    assert np.all(np.abs(qpow2[0] - ref_pow2) < 5e-6)
    assert abs(k2[0] - ref_k2) < 5e-5

    # Mercato 3: (1.67, 2.2)
    m3 = np.array([[1.67, 2.2]])
    ref_p3 = np.array([0.56848, 0.43152])
    ref_a3 = np.array([0.57213, 0.42787])
    ref_pow3 = np.array([0.57404, 0.42596])
    ref_k3 = 1.0824

    qp3 = devig_proportional(m3)[0]
    qa3 = devig_additive(m3)[0]
    qpow3, k3 = devig_power(m3)

    assert np.all(np.abs(qp3 - ref_p3) < 5e-6)
    assert np.all(np.abs(qa3 - ref_a3) < 5e-6)
    assert np.all(np.abs(qpow3[0] - ref_pow3) < 5e-6)
    assert abs(k3[0] - ref_k3) < 5e-5

    # Verifica della somma a 1 entro 1e-12 per tutti i mercati di riferimento
    for q in (qp1, qa1, qpow1[0], qp2, qa2, qpow2[0], qp3, qa3, qpow3[0]):
        assert abs(np.sum(q) - 1.0) <= 1e-12


def test_random_markets_sum_to_one():
    """Verifica la somma a 1 entro 1e-12 su 10 000 mercati casuali a tre esiti.

    I mercati con S <= 1 sono inclusi di proposito per verificare la convergenza
    del risolutore power nei diversi regimi (S > 1, S = 1, S < 1).
    """
    rng = np.random.default_rng(20260929)
    odds = rng.uniform(1.1, 10.0, size=(10000, 3))

    # 1. Proporzionale
    q_prop = devig_proportional(odds)
    err_prop = np.max(np.abs(q_prop.sum(axis=1) - 1.0))
    assert err_prop <= 1e-12

    # 2. Additivo (sui mercati applicabili / non NaN)
    q_add = devig_additive(odds)
    valid_mask = ~np.isnan(q_add[:, 0])
    assert np.any(valid_mask)
    q_add_valid = q_add[valid_mask]
    err_add = np.max(np.abs(q_add_valid.sum(axis=1) - 1.0))
    assert err_add <= 1e-12

    # 3. Power
    q_pow, k = devig_power(odds)
    err_pow = np.max(np.abs(q_pow.sum(axis=1) - 1.0))
    assert err_pow <= 1e-12
    assert np.all(k > 0)


def test_case_s_equals_one():
    """Verifica che per mercati con S = 1 i tre metodi restituiscano esattamente pi e k = 1."""
    # (2.0, 2.0), (2.0, 4.0, 4.0), (3.0, 3.0, 3.0)
    m = np.array(
        [
            [2.0, 2.0, np.nan],  # testato separatamente a 2 esiti
            [2.0, 4.0, 4.0],
            [3.0, 3.0, 3.0],
        ]
    )
    # Test a 2 esiti
    m_2 = np.array([[2.0, 2.0]])
    pi_2 = implied_probabilities(m_2)
    assert np.allclose(devig_proportional(m_2), pi_2, atol=1e-15)
    assert np.allclose(devig_additive(m_2), pi_2, atol=1e-15)
    q_pow_2, k_2 = devig_power(m_2)
    assert np.allclose(q_pow_2, pi_2, atol=1e-15)
    assert np.allclose(k_2, 1.0, atol=1e-15)

    # Test a 3 esiti
    m_3 = np.array([[2.0, 4.0, 4.0], [3.0, 3.0, 3.0]])
    pi_3 = implied_probabilities(m_3)
    assert np.allclose(devig_proportional(m_3), pi_3, atol=1e-15)
    assert np.allclose(devig_additive(m_3), pi_3, atol=1e-15)
    q_pow_3, k_3 = devig_power(m_3)
    assert np.allclose(q_pow_3, pi_3, atol=1e-15)
    assert np.allclose(k_3, 1.0, atol=1e-15)


def test_additive_negative_produces_nan_row():
    """Verifica che un mercato con q additivo negativo produca una riga di soli NaN."""
    # Con quote (1.05, 10.0, 50.0), pi_3 = 0.02 e (S-1)/3 = 0.0241 => q_3 < 0
    m = np.array([[1.05, 10.0, 50.0]])
    q_add = devig_additive(m)
    assert q_add.shape == (1, 3)
    assert np.all(np.isnan(q_add))


def test_property_proportional_over_power_decreases_with_pi():
    """Verifica che q_proporzionale / q_power decresca al crescere di pi nei mercati con S > 1.

    Poiche' q_prop / q_pow = pi^(1-k) / S, per S > 1 si ha k > 1 e l'esponente (1 - k) e'
    strettamente negativo, rendendo il rapporto strettamente decrescente rispetto a pi.
    La proprieta' e' valida specificamente quando S > 1.
    """
    # 1. Verifica sui tre mercati di riferimento (tutti con S > 1)
    ref_markets = [
        np.array([[8.0, 5.5, 1.33]]),
        np.array([[1.25, 6.00, 11.0]]),
        np.array([[1.67, 2.2]]),
    ]
    for m in ref_markets:
        pi = implied_probabilities(m)[0]
        qp = devig_proportional(m)[0]
        qpow, _ = devig_power(m)
        ratio = qp / qpow[0]

        order = np.argsort(pi)  # pi crescente
        ordered_ratio = ratio[order]
        # Il rapporto deve essere strettamente decrescente
        assert np.all(np.diff(ordered_ratio) < 0)

    # 2. Verifica su un campione di mercati casuali con S > 1 e pi distinti
    rng = np.random.default_rng(20260929)
    odds = rng.uniform(1.1, 10.0, size=(1000, 3))
    s = overround(odds) + 1.0
    mask_s_gt_1 = s > 1.02  # margine significativo per evitare uguaglianze numeriche
    odds_gt_1 = odds[mask_s_gt_1]

    pi_all = implied_probabilities(odds_gt_1)
    qp_all = devig_proportional(odds_gt_1)
    qpow_all, _ = devig_power(odds_gt_1)
    ratio_all = qp_all / qpow_all

    for i in range(len(odds_gt_1)):
        row_pi = pi_all[i]
        row_ratio = ratio_all[i]
        order = np.argsort(row_pi)
        # Se le pi sono strettamente crescenti, ratio deve essere strettamente decrescente
        if np.all(np.diff(row_pi[order]) > 1e-8):
            assert np.all(np.diff(row_ratio[order]) < 0)


def test_extreme_markets():
    """Verifica che mercati con quote estreme convergano entro 1e-12 e k > 0."""
    # 2 mercati a 3 esiti: (1.01, 100.0, 100.0) e (50.0, 50.0, 50.0)
    m_3 = np.array([[1.01, 100.0, 100.0], [50.0, 50.0, 50.0]])
    qp3 = devig_proportional(m_3)
    qa3 = devig_additive(m_3)
    qpow3, k3 = devig_power(m_3)

    assert np.all(np.abs(qp3.sum(axis=1) - 1.0) <= 1e-12)
    # Per l'additivo, sui mercati non NaN
    for row in qa3:
        if not np.all(np.isnan(row)):
            assert abs(np.sum(row) - 1.0) <= 1e-12
    assert np.all(np.abs(qpow3.sum(axis=1) - 1.0) <= 1e-12)
    assert np.all(k3 > 0)

    # 1 mercato a 2 esiti estremo: (1.001, 1000.0)
    m_2 = np.array([[1.001, 1000.0]])
    qp2 = devig_proportional(m_2)
    qa2 = devig_additive(m_2)
    qpow2, k2 = devig_power(m_2)

    assert np.all(np.abs(qp2.sum(axis=1) - 1.0) <= 1e-12)
    for row in qa2:
        if not np.all(np.isnan(row)):
            assert abs(np.sum(row) - 1.0) <= 1e-12
    assert np.all(np.abs(qpow2.sum(axis=1) - 1.0) <= 1e-12)
    assert np.all(k2 > 0)


def test_type_and_value_validations():
    """Verifica tutte le condizioni di errore e sollevamento eccezioni per input errati."""
    # Non ndarray -> TypeError
    with pytest.raises(TypeError, match="odds must be a numpy.ndarray"):
        implied_probabilities([[2.0, 3.0]])  # type: ignore

    # Dtype non numerico reale: bool, complex, object, string -> TypeError
    with pytest.raises(TypeError, match="real integer or floating"):
        implied_probabilities(np.array([[True, False]]))
    with pytest.raises(TypeError, match="real integer or floating"):
        implied_probabilities(np.array([[2.0 + 1j, 3.0]]))
    with pytest.raises(TypeError, match="real integer or floating"):
        implied_probabilities(np.array([["2.0", "3.0"]]))
    with pytest.raises(TypeError, match="real integer or floating"):
        implied_probabilities(np.array([[object(), object()]]))

    # Dtype intero reale -> accettato
    int_odds = np.array([[2, 4, 4]])
    pi_int = implied_probabilities(int_odds)
    assert pi_int.dtype == np.float64
    assert np.allclose(pi_int, [0.5, 0.25, 0.25])

    # Forma errata: 1D o 3D -> ValueError
    with pytest.raises(ValueError, match="shape"):
        implied_probabilities(np.array([2.0, 3.0]))
    with pytest.raises(ValueError, match="shape"):
        implied_probabilities(np.ones((2, 2, 2)))

    # n < 2 -> ValueError
    with pytest.raises(ValueError, match="shape"):
        implied_probabilities(np.array([[2.0]]))

    # Valori non finiti: NaN, inf -> ValueError
    with pytest.raises(ValueError, match="finite"):
        implied_probabilities(np.array([[np.nan, 2.0]]))
    with pytest.raises(ValueError, match="finite"):
        implied_probabilities(np.array([[np.inf, 2.0]]))
    with pytest.raises(ValueError, match="finite"):
        implied_probabilities(np.array([[-np.inf, 2.0]]))

    # Quote <= 1.0 -> ValueError
    with pytest.raises(ValueError, match="strictly greater than 1.0"):
        implied_probabilities(np.array([[1.0, 2.0]]))
    with pytest.raises(ValueError, match="strictly greater than 1.0"):
        implied_probabilities(np.array([[0.9, 2.0]]))
    with pytest.raises(ValueError, match="strictly greater than 1.0"):
        implied_probabilities(np.array([[-1.5, 2.0]]))


def test_overround_computation():
    """Verifica il calcolo dell'overround."""
    odds = np.array([[2.0, 2.0], [2.0, 4.0]])
    s_minus_1 = overround(odds)
    assert s_minus_1.shape == (2,)
    assert np.allclose(s_minus_1, [0.0, 0.75 - 1.0])


# ---------------------------------------------------------------------------
# T43: metodi Shin e odds ratio
# ---------------------------------------------------------------------------

# Valori della nota 2.1 §7 (percentuali a 3 decimali, parametri a 4 decimali)
NOTE_MARKETS = {
    "7.1": ([8.0, 5.5, 1.33], 0.0301, [10.880, 16.457, 72.663], 0.8749, [11.110, 16.278, 72.612]),
    "7.2": ([1.67, 2.2], 0.0534, [57.213, 42.787], 0.8967, [57.234, 42.766]),
    "7.3": ([2.08, 3.45, 3.55], 0.0262, [46.167, 27.320, 26.514], 0.9227, [46.072, 27.358, 26.570]),
    "7.4": ([1.25, 6.00, 11.0], 0.0300, [77.455, 14.983, 7.563], 0.8583, [77.444, 14.652, 7.905]),
}


@pytest.mark.parametrize("market", sorted(NOTE_MARKETS))
def test_shin_and_odds_ratio_note_examples(market):
    """Gli esempi della nota 2.1 §7 si riproducono alla precisione con cui la nota li riporta."""
    odds, z_ref, q_shin_ref, c_ref, q_or_ref = NOTE_MARKETS[market]
    q_shin, z = devig_shin(np.array([odds]))
    q_or, c = devig_odds_ratio(np.array([odds]))

    # Mezza unità dell'ultima cifra riportata, più un margine di arrotondamento binario
    assert abs(z[0] - z_ref) <= 5e-5 + 1e-12
    assert abs(c[0] - c_ref) <= 5e-5 + 1e-12
    np.testing.assert_array_less(np.abs(q_shin[0] * 100 - np.array(q_shin_ref)), 5e-4 + 1e-9)
    np.testing.assert_array_less(np.abs(q_or[0] * 100 - np.array(q_or_ref)), 5e-4 + 1e-9)


def test_shin_and_odds_ratio_random_markets_sum_to_one():
    """Somma a 1 entro 1e-12 su 10 000 mercati casuali, con overround realistici e no."""
    rng = np.random.default_rng(20261011)
    # 1. Mercati con overround fra 0 e 15%: probabilità di Dirichlet con margine proporzionale
    true_p = rng.dirichlet(np.ones(3), size=10000)
    true_p = np.clip(true_p, 0.01, None)
    true_p /= true_p.sum(axis=1, keepdims=True)
    margin = 1.0 + rng.uniform(0.0, 0.15, size=(10000, 1))
    odds = 1.0 / (true_p * margin)
    odds = np.where(odds <= 1.0, 1.0001, odds)

    q_shin, z = devig_shin(odds)
    q_or, c = devig_odds_ratio(odds)
    booksum = (1.0 / odds).sum(axis=1)
    applicable = booksum >= 1.0
    assert applicable.sum() >= 9900
    assert np.max(np.abs(q_shin[applicable].sum(axis=1) - 1.0)) <= 1e-12
    assert np.max(np.abs(q_or.sum(axis=1) - 1.0)) <= 1e-12
    assert np.all((z[applicable] >= 0.0) & (z[applicable] < 1.0))
    assert np.all(c > 0.0)
    assert np.all((q_or > 0.0) & (q_or < 1.0))

    # 2. Quote uniformi in [1.1, 10] come in test_random_markets_sum_to_one, con S < 1 inclusi
    odds_u = np.random.default_rng(20260929).uniform(1.1, 10.0, size=(10000, 3))
    q_shin_u, z_u = devig_shin(odds_u)
    q_or_u, c_u = devig_odds_ratio(odds_u)
    s_u = (1.0 / odds_u).sum(axis=1)
    ok = s_u >= 1.0
    assert np.max(np.abs(q_shin_u[ok].sum(axis=1) - 1.0)) <= 1e-12
    assert np.all(np.isnan(q_shin_u[~ok])) and np.all(np.isnan(z_u[~ok]))
    assert np.max(np.abs(q_or_u.sum(axis=1) - 1.0)) <= 1e-12
    assert np.all(c_u[s_u < 1.0] > 1.0) and np.all(c_u[s_u > 1.0] < 1.0)


def test_shin_and_odds_ratio_no_overround_returns_implied():
    """Mercato senza overround (S = 1): q = pi, z = 0 e c = 1."""
    m = np.array([[2.0, 4.0, 4.0], [4.0, 2.0, 4.0]])
    pi = implied_probabilities(m)
    assert np.all(pi.sum(axis=1) == 1.0)
    q_shin, z = devig_shin(m)
    q_or, c = devig_odds_ratio(m)
    np.testing.assert_array_equal(q_shin, pi)
    np.testing.assert_array_equal(q_or, pi)
    np.testing.assert_array_equal(z, [0.0, 0.0])
    np.testing.assert_array_equal(c, [1.0, 1.0])

    m2 = np.array([[2.0, 2.0]])
    np.testing.assert_array_equal(devig_shin(m2)[0], implied_probabilities(m2))
    np.testing.assert_array_equal(devig_odds_ratio(m2)[0], implied_probabilities(m2))


def test_shin_outsider_below_proportional_with_favourite_longshot():
    """Con overround, Shin dà all'outsider una q minore del proporzionale (favourite-longshot)."""
    m = np.array([[1.25, 6.00, 11.0], [8.0, 5.5, 1.33], [1.5, 4.2, 7.5], [2.08, 3.45, 3.55]])
    q_prop = devig_proportional(m)
    q_shin, _ = devig_shin(m)
    q_or, _ = devig_odds_ratio(m)
    outsider = np.argmax(m, axis=1)
    favourite = np.argmin(m, axis=1)
    rows = np.arange(m.shape[0])
    assert np.all(q_shin[rows, outsider] < q_prop[rows, outsider])
    assert np.all(q_shin[rows, favourite] > q_prop[rows, favourite])
    assert np.all(q_or[rows, outsider] < q_prop[rows, outsider])


def test_shin_and_odds_ratio_extreme_markets():
    """Mercati estremi: convergenza entro 1e-12; S < 1 dà NaN per Shin e c > 1 per odds ratio."""
    for m in (np.array([[1.001, 1000.0], [1.01, 30.0]]), np.array([[1.01, 100.0, 100.0]])):
        for fn in (devig_shin, devig_odds_ratio):
            q, param = fn(m)
            assert np.all(np.abs(q.sum(axis=1) - 1.0) <= 1e-12)
            assert np.all(np.isfinite(param))

    # S = 0.06 e S = 0.857: mercati sotto la parità
    m_under = np.array([[50.0, 50.0, 50.0], [3.5, 3.5, 3.5]])
    q_shin, z = devig_shin(m_under)
    assert np.all(np.isnan(q_shin)) and np.all(np.isnan(z))
    q_or, c = devig_odds_ratio(m_under)
    assert np.all(np.abs(q_or.sum(axis=1) - 1.0) <= 1e-12)
    assert np.all(c > 1.0)


def test_shin_and_odds_ratio_input_validation():
    """Stesse validazioni d'ingresso degli altri metodi."""
    for fn in (devig_shin, devig_odds_ratio):
        with pytest.raises(TypeError, match="odds must be a numpy.ndarray"):
            fn([[2.0, 3.0]])  # type: ignore
        with pytest.raises(TypeError, match="real integer or floating"):
            fn(np.array([[True, False]]))
        with pytest.raises(ValueError, match="shape"):
            fn(np.array([2.0, 3.0]))
        with pytest.raises(ValueError, match="finite"):
            fn(np.array([[np.nan, 2.0]]))
        with pytest.raises(ValueError, match="strictly greater than 1.0"):
            fn(np.array([[1.0, 2.0]]))
        q, param = fn(np.array([[2, 4, 4]]))
        assert q.dtype == np.float64 and param.shape == (1,)


def test_shin_and_odds_ratio_runtime_error_when_unconverged(monkeypatch):
    """Lo stesso RuntimeError di devig_power oltre 1e-12 se la bisezione non converge."""
    monkeypatch.setattr(shk.market.devig, "MAX_BISECTION_ITERATIONS", 3)
    m = np.array([[1.9, 3.6, 4.1]])
    with pytest.raises(RuntimeError, match="Shin devigging solver failed to converge within tolerance 1e-12"):
        devig_shin(m)
    with pytest.raises(RuntimeError, match="Odds ratio devigging solver failed to converge within tolerance 1e-12"):
        devig_odds_ratio(m)
