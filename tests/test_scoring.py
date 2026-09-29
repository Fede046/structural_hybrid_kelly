"""Test unitari per il modulo shk.model.scoring."""

import math
import numpy as np
import pandas as pd
import pytest

from shk.model.elo_fit import EloFitParams
from shk.model.scoring import (
    align_predictions_with_odds,
    compute_cumulative_g_hat,
    compute_g_hat,
    compute_g_hat_terms,
    compute_log_loss,
    compute_mean_log_loss,
    generate_validation_predictions,
    prepare_series_evaluation,
)


def test_compute_log_loss_basic():
    """Verifica il calcolo esatto della log-loss puntuale con logaritmo naturale."""
    probs = np.array([
        [0.6, 0.3, 0.1],
        [0.2, 0.5, 0.3],
        [0.1, 0.2, 0.7],
    ], dtype=np.float64)
    outcomes = np.array(["H", "D", "A"])

    expected = np.array([
        -math.log(0.6),
        -math.log(0.5),
        -math.log(0.7),
    ], dtype=np.float64)

    actual = compute_log_loss(probs, outcomes)
    np.testing.assert_allclose(actual, expected, rtol=1e-14, atol=1e-14)


def test_compute_log_loss_validations():
    """Verifica il sollevamento di TypeError e ValueError su input non conformi."""
    valid_probs = np.array([[0.5, 0.3, 0.2]], dtype=np.float64)
    valid_outcomes = np.array(["H"])

    # TypeError
    with pytest.raises(TypeError, match="numpy.ndarray"):
        compute_log_loss([[0.5, 0.3, 0.2]], valid_outcomes)  # type: ignore

    with pytest.raises(TypeError, match="real numeric"):
        compute_log_loss(np.array([[True, False, False]]), valid_outcomes)

    with pytest.raises(TypeError, match="numpy.ndarray"):
        compute_log_loss(valid_probs, ["H"])  # type: ignore

    # ValueError: forma probs
    with pytest.raises(ValueError, match="shape"):
        compute_log_loss(np.array([0.5, 0.3, 0.2]), valid_outcomes)

    with pytest.raises(ValueError, match="shape"):
        compute_log_loss(np.array([[0.5, 0.5]]), valid_outcomes)

    # ValueError: somma riga != 1
    with pytest.raises(ValueError, match="sum to 1.0"):
        compute_log_loss(np.array([[0.5, 0.5, 0.5]]), valid_outcomes)

    # ValueError: valori non finiti o fuori intervallo
    with pytest.raises(ValueError, match="finite"):
        compute_log_loss(np.array([[np.nan, 0.5, 0.5]]), valid_outcomes)

    with pytest.raises(ValueError, match="values in"):
        compute_log_loss(np.array([[-0.1, 0.6, 0.5]]), valid_outcomes)

    # ValueError: probabilità esito realizzato <= 0
    with pytest.raises(ValueError, match="strictly positive"):
        compute_log_loss(np.array([[0.0, 0.5, 0.5]]), valid_outcomes)

    # ValueError: outcomes forma e valori
    with pytest.raises(ValueError, match="1D array"):
        compute_log_loss(valid_probs, np.array([["H"]]))

    with pytest.raises(ValueError, match="length"):
        compute_log_loss(valid_probs, np.array(["H", "D"]))

    with pytest.raises(ValueError, match="only contain 'H', 'D', 'A'"):
        compute_log_loss(valid_probs, np.array(["X"]))


def test_compute_mean_log_loss():
    """Verifica il calcolo della log-loss media e gestione array vuoto."""
    probs = np.array([
        [0.5, 0.3, 0.2],
        [0.2, 0.4, 0.4],
    ])
    outcomes = np.array(["H", "D"])
    expected = (-math.log(0.5) - math.log(0.4)) / 2.0
    assert math.isclose(compute_mean_log_loss(probs, outcomes), expected, rel_tol=1e-14)

    empty_p = np.empty((0, 3), dtype=np.float64)
    empty_o = np.empty((0,), dtype=str)
    with pytest.raises(ValueError, match="empty"):
        compute_mean_log_loss(empty_p, empty_o)


def test_g_hat_terms_and_mean():
    """Criterio di accettazione: p = q dà g_hat = 0 entro 1e-15; caso a mano torna entro 1e-12."""
    probs = np.array([
        [0.5, 0.3, 0.2],
        [0.2, 0.6, 0.2],
        [0.1, 0.2, 0.7],
    ])
    outcomes = np.array(["H", "D", "A"])

    # Con p = q, g_hat = 0 entro 1e-15
    terms_equal = compute_g_hat_terms(probs, probs, outcomes)
    np.testing.assert_allclose(terms_equal, 0.0, atol=1e-15)
    assert abs(compute_g_hat(probs, probs, outcomes)) < 1e-15

    # Caso piccolo a mano
    p_model = np.array([
        [0.6, 0.25, 0.15],
        [0.3, 0.4, 0.3],
        [0.2, 0.3, 0.5],
    ])
    q_market = np.array([
        [0.5, 0.3, 0.2],
        [0.25, 0.5, 0.25],
        [0.15, 0.25, 0.6],
    ])
    # Termini g_t = ln p(x_t) - ln q(x_t) = -ln q(x_t) - (-ln p(x_t)) = LL(q) - LL(p)
    term0 = math.log(0.6) - math.log(0.5)  # H
    term1 = math.log(0.4) - math.log(0.5)  # D
    term2 = math.log(0.5) - math.log(0.6)  # A
    expected_terms = np.array([term0, term1, term2])
    expected_mean = float(np.mean(expected_terms))

    actual_terms = compute_g_hat_terms(p_model, q_market, outcomes)
    actual_mean = compute_g_hat(p_model, q_market, outcomes)

    np.testing.assert_allclose(actual_terms, expected_terms, rtol=1e-12, atol=1e-12)
    assert math.isclose(actual_mean, expected_mean, rel_tol=1e-12, abs_tol=1e-12)


def test_compute_cumulative_g_hat():
    """Verifica che g_hat_cum, t sia la media dei primi t termini e coincida col riepilogo a fine serie."""
    terms = np.array([0.1, -0.05, 0.2, -0.15, 0.08], dtype=np.float64)
    cum = compute_cumulative_g_hat(terms)

    assert len(cum) == len(terms)
    for t in range(1, len(terms) + 1):
        expected_t = float(np.mean(terms[:t]))
        assert math.isclose(cum[t - 1], expected_t, rel_tol=1e-14, abs_tol=1e-14)

    # Ultimo valore coincide esattamente con la media complessiva
    assert math.isclose(cum[-1], float(np.mean(terms)), rel_tol=1e-14, abs_tol=1e-14)

    # Validazioni
    with pytest.raises(TypeError, match="numpy.ndarray"):
        compute_cumulative_g_hat([0.1, 0.2])  # type: ignore

    with pytest.raises(TypeError, match="real numeric"):
        compute_cumulative_g_hat(np.array([True, False]))

    with pytest.raises(ValueError, match="1D"):
        compute_cumulative_g_hat(np.array([[0.1, 0.2]]))

    with pytest.raises(ValueError, match="empty"):
        compute_cumulative_g_hat(np.array([], dtype=np.float64))


def test_prepare_series_evaluation_synthetic():
    """Verifica la gerarchia delle esclusioni e conteggi su dati sintetici controllati."""
    # 4 partite di test per una stagione di validazione
    df_aligned = pd.DataFrame({
        "season": ["2015-16"] * 4,
        "Date": pd.to_datetime(["2015-09-01", "2015-09-02", "2015-09-03", "2015-09-04"]),
        "HomeTeam": ["TeamA", "TeamB", "TeamC", "TeamD"],
        "AwayTeam": ["TeamW", "TeamX", "TeamY", "TeamZ"],
        "FTR": ["H", "D", "A", "H"],
        "p_home": [0.5, 0.4, 0.3, 0.6],
        "p_draw": [0.3, 0.3, 0.4, 0.2],
        "p_away": [0.2, 0.3, 0.3, 0.2],
        # Partita 0: quote perfette
        # Partita 1: quota B365D mancante (missing_odds)
        # Partita 2: quota B365A <= 1.0 (invalid_odds)
        # Partita 3: quote normali
        "B365H": ["2.0", "2.1", "2.0", "1.8"],
        "B365D": ["3.2", None, "3.0", "3.4"],
        "B365A": ["4.0", "3.5", "0.95", "4.5"],
    })

    schedule = {
        "2010-11": {
            "training": ["2000-01", "2010-11"],
            "validation": ["2015-16"],
        }
    }

    eval_data = prepare_series_evaluation(df_aligned, "b365_prematch", schedule)

    assert eval_data.matches_total == 4
    assert eval_data.missing_odds == 1
    assert eval_data.invalid_odds == 1
    assert eval_data.additive_inapplicable == 0
    assert eval_data.matches_excluded == 2
    assert eval_data.matches_used == 2
    assert len(eval_data.df_used) == 2
    assert eval_data.p_model.shape == (2, 3)
    assert eval_data.q_proportional.shape == (2, 3)
    assert eval_data.q_additive.shape == (2, 3)
    assert eval_data.q_power.shape == (2, 3)


def test_align_predictions_key_validations():
    """Verifica che chiavi mancanti o duplicate sollevino ValueError nell'allineamento."""
    df_preds = pd.DataFrame({
        "season": ["2015-16", "2015-16"],
        "Date": pd.to_datetime(["2015-09-01", "2015-09-01"]),
        "HomeTeam": ["TeamA", "TeamA"],  # Chiave duplicata!
        "AwayTeam": ["TeamB", "TeamB"],
        "p_home": [0.5, 0.5],
        "p_draw": [0.3, 0.3],
        "p_away": [0.2, 0.2],
    })
    df_raw = pd.DataFrame({
        "season": ["2015-16"],
        "Date": pd.to_datetime(["2015-09-01"]),
        "HomeTeam": ["TeamA"],
        "AwayTeam": ["TeamB"],
        "FTR": ["H"],
    })

    with pytest.raises(ValueError, match="duplicate match keys"):
        align_predictions_with_odds(df_preds, df_raw)
