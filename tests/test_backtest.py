"""Test unitari per il motore di backtest su quote reali (Task 31 / US-C5.3)."""

import inspect
import math
import numpy as np
import pytest

from shk.kelly.backtest import BacktestResult, backtest_log_wealth


def test_backtest_synthetic_hand_calculation():
    """Verifica che la log-ricchezza riproduca un calcolo a mano entro 1e-12."""
    dates = np.array(["2010-09-01", "2010-09-05"], dtype="datetime64[D]")
    fractions = np.array([0.10, 0.20], dtype=np.float64)
    odds = np.array([2.50, 3.00], dtype=np.float64)
    won = np.array([True, False], dtype=bool)

    result = backtest_log_wealth(dates, fractions, odds, won)

    assert isinstance(result, BacktestResult)
    assert np.issubdtype(result.dates.dtype, np.datetime64)
    assert len(result.dates) == 2
    assert len(result.log_wealth) == 3

    # Calcolo a mano:
    # Data 1: vincita con r = 2.5 - 1 = 1.5; net_return = 0.10 * 1.5 = 0.15
    # L_1 = 0.0 + ln(1 + 0.15) = ln(1.15)
    # Data 2: perdita con r = -1.0; net_return = 0.20 * (-1.0) = -0.20
    # L_2 = ln(1.15) + ln(1 - 0.20) = ln(1.15 * 0.80) = ln(0.92)
    expected = np.array([0.0, math.log(1.15), math.log(0.92)], dtype=np.float64)
    np.testing.assert_allclose(result.log_wealth, expected, atol=1e-12)


def test_backtest_same_date_simultaneous_settlement():
    """Verifica che partite della stessa data siano regolate simultaneamente sul bankroll di inizio data."""
    # 3 partite tutte sulla stessa data
    dates = np.array(["2010-09-11", "2010-09-11", "2010-09-11"], dtype="datetime64[D]")
    fractions = np.array([0.10, 0.15, 0.05], dtype=np.float64)
    odds = np.array([2.00, 3.00, 4.00], dtype=np.float64)
    won = np.array([True, False, True], dtype=bool)

    result = backtest_log_wealth(dates, fractions, odds, won)

    assert len(result.dates) == 1
    assert len(result.log_wealth) == 2

    # r_1 = 1.0 -> f_1 * r_1 = 0.10
    # r_2 = -1.0 -> f_2 * r_2 = -0.15
    # r_3 = 3.0 -> f_3 * r_3 = 0.15
    # Sum(f_i * r_i) = 0.10 - 0.15 + 0.15 = 0.10
    # L_1 = ln(1 + 0.10) = ln(1.10)
    expected = np.array([0.0, math.log(1.10)], dtype=np.float64)
    np.testing.assert_allclose(result.log_wealth, expected, atol=1e-12)


def test_backtest_zero_fraction_matches_included_without_impact():
    """Verifica che partite con frazione zero non alterino la traiettoria di ricchezza."""
    dates = np.array(["2010-09-11", "2010-09-11", "2010-09-18"], dtype="datetime64[D]")
    fractions = np.array([0.00, 0.10, 0.00], dtype=np.float64)
    odds = np.array([2.50, 2.00, 1.80], dtype=np.float64)
    won = np.array([False, True, True], dtype=bool)

    result = backtest_log_wealth(dates, fractions, odds, won)

    assert len(result.dates) == 2
    assert len(result.log_wealth) == 3

    # Data 1: solo f_2 = 0.10 punta e vince -> L_1 = ln(1.10)
    # Data 2: f_3 = 0.00 -> return = 0.0 -> L_2 = L_1 + ln(1.0) = L_1
    expected = np.array([0.0, math.log(1.10), math.log(1.10)], dtype=np.float64)
    np.testing.assert_allclose(result.log_wealth, expected, atol=1e-12)


def test_backtest_empty_input():
    """Verifica il comportamento con input vuoti."""
    dates = np.empty((0,), dtype="datetime64[D]")
    fractions = np.empty((0,), dtype=np.float64)
    odds = np.empty((0,), dtype=np.float64)
    won = np.empty((0,), dtype=bool)

    result = backtest_log_wealth(dates, fractions, odds, won)
    assert len(result.dates) == 0
    assert len(result.log_wealth) == 1
    assert result.log_wealth[0] == 0.0


def test_backtest_type_and_dtype_validations():
    """Verifica che vengano sollevati TypeError per tipi o dtype errati."""
    valid_dates = np.array(["2010-09-01"], dtype="datetime64[D]")
    valid_fractions = np.array([0.1], dtype=np.float64)
    valid_odds = np.array([2.0], dtype=np.float64)
    valid_won = np.array([True], dtype=bool)

    # dates non ndarray o con dtype non datetime64
    with pytest.raises(TypeError, match="dates must be a numpy.ndarray"):
        backtest_log_wealth(["2010-09-01"], valid_fractions, valid_odds, valid_won)  # type: ignore
    with pytest.raises(TypeError, match="dates must have datetime64 dtype"):
        backtest_log_wealth(np.array(["2010-09-01"]), valid_fractions, valid_odds, valid_won)

    # fractions non ndarray o con dtype non float64
    with pytest.raises(TypeError, match="fractions must be a numpy.ndarray"):
        backtest_log_wealth(valid_dates, [0.1], valid_odds, valid_won)  # type: ignore
    with pytest.raises(TypeError, match="fractions must have float64 dtype"):
        backtest_log_wealth(valid_dates, np.array([0.1], dtype=np.float32), valid_odds, valid_won)

    # odds non ndarray o con dtype non float64
    with pytest.raises(TypeError, match="odds must be a numpy.ndarray"):
        backtest_log_wealth(valid_dates, valid_fractions, [2.0], valid_won)  # type: ignore
    with pytest.raises(TypeError, match="odds must have float64 dtype"):
        backtest_log_wealth(valid_dates, valid_fractions, np.array([2.0], dtype=np.float32), valid_won)

    # won non ndarray o con dtype non bool
    with pytest.raises(TypeError, match="won must be a numpy.ndarray"):
        backtest_log_wealth(valid_dates, valid_fractions, valid_odds, [True])  # type: ignore
    with pytest.raises(TypeError, match="won must have bool dtype"):
        backtest_log_wealth(valid_dates, valid_fractions, valid_odds, np.array([1], dtype=int))


def test_backtest_value_validations():
    """Verifica che vengano sollevati ValueError per violazioni dei vincoli di dominio."""
    valid_dates = np.array(["2010-09-01", "2010-09-05"], dtype="datetime64[D]")
    valid_fractions = np.array([0.1, 0.2], dtype=np.float64)
    valid_odds = np.array([2.0, 2.5], dtype=np.float64)
    valid_won = np.array([True, False], dtype=bool)

    # Dimensioni non 1D
    with pytest.raises(ValueError, match="1-dimensional"):
        backtest_log_wealth(valid_dates.reshape(1, 2), valid_fractions, valid_odds, valid_won)

    # Lunghezze disallineate
    with pytest.raises(ValueError, match="identical lengths"):
        backtest_log_wealth(valid_dates[:1], valid_fractions, valid_odds, valid_won)

    # Date non ordinate cronologicamente
    unordered_dates = np.array(["2010-09-05", "2010-09-01"], dtype="datetime64[D]")
    with pytest.raises(ValueError, match="non-decreasing chronological order"):
        backtest_log_wealth(unordered_dates, valid_fractions, valid_odds, valid_won)

    # Quote non finite o <= 1.0
    bad_odds_le1 = np.array([1.0, 2.5], dtype=np.float64)
    with pytest.raises(ValueError, match="strictly greater than 1.0"):
        backtest_log_wealth(valid_dates, valid_fractions, bad_odds_le1, valid_won)

    bad_odds_inf = np.array([np.inf, 2.5], dtype=np.float64)
    with pytest.raises(ValueError, match="strictly greater than 1.0"):
        backtest_log_wealth(valid_dates, valid_fractions, bad_odds_inf, valid_won)

    # Frazioni negative o >= 1.0
    bad_frac_neg = np.array([-0.05, 0.2], dtype=np.float64)
    with pytest.raises(ValueError, match=r"\[0, 1\)"):
        backtest_log_wealth(valid_dates, bad_frac_neg, valid_odds, valid_won)

    bad_frac_ge1 = np.array([1.0, 0.2], dtype=np.float64)
    with pytest.raises(ValueError, match=r"\[0, 1\)"):
        backtest_log_wealth(valid_dates, bad_frac_ge1, valid_odds, valid_won)

    # Somma delle frazioni per una stessa data >= 1.0
    same_date = np.array(["2010-09-01", "2010-09-01"], dtype="datetime64[D]")
    frac_sum_ge1 = np.array([0.60, 0.50], dtype=np.float64)
    with pytest.raises(ValueError, match="Sum of fractions on date .* is >= 1.0"):
        backtest_log_wealth(same_date, frac_sum_ge1, valid_odds, valid_won)


def test_backtest_does_not_receive_probabilities():
    """Verifica che backtest_log_wealth non accetti argomenti p o p_hat nell'interfaccia."""
    sig = inspect.signature(backtest_log_wealth)
    param_names = list(sig.parameters.keys())
    assert "p" not in param_names
    assert "p_hat" not in param_names
    assert param_names == ["dates", "fractions", "odds", "won"]
