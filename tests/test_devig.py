"""Test per il modulo src/shk/market/devig.py."""

import numpy as np
import pytest

from shk.market.devig import (
    devig_additive,
    devig_power,
    devig_proportional,
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
