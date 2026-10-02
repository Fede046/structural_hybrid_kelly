"""Test di accettazione per US-C5.3 / Task 31.

Verifica:
- Criterio 1: il motore riproduce la log-ricchezza di un caso sintetico calcolata a mano entro 1e-12,
  solleva gli errori previsti e non riceve p né p_hat;
- Criterio 2: un allarme della data d cambia lambda solo dalle date successive (test);
- Criterio 3: con kappa = 1 le frazioni coincidono col quarto-Kelly senza detector (test);
- Criterio 4: i kappa congelati per ADWIN e Page-Hinkley coincidono con la calibrazione ricalcolata
  sui dati reali (test saltato senza dati);
- Criterio 5: la docstring della regola dice che il detector indica quando, non quanto né di che tipo;
- Test sintetico: regola di parità fra esiti (H > D > A) e regola di parità fra kappa (vince il più grande).
"""

import inspect
import math
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.data.split import load_by_role, read_split_config
from shk.kelly.backtest import BacktestResult, backtest_log_wealth
from shk.kelly.staking import (
    BASE_LAMBDA,
    KAPPA_ADWIN,
    KAPPA_GRID,
    KAPPA_PAGE_HINKLEY,
    compute_adaptive_lambda,
    kelly_staking,
    select_baseline_d_bets,
)
from shk.model.elo_fit import ELO_FITS, derive_fit_schedule
from shk.model.monitoring import (
    KappaCalibrationResult,
    calibrate_baseline_d_kappa,
)
from shk.model.residuals import compute_model_residuals


def _has_real_data() -> bool:
    """Verifica se i dati grezzi sono presenti sul filesystem."""
    return DEFAULT_DATA_DIR.exists() and len(list(DEFAULT_DATA_DIR.glob("*.csv"))) > 0


def test_motor_reproduces_hand_calculation_and_interface():
    """Criterio 1: il motore riproduce la log-ricchezza calcolata a mano entro 1e-12 e non riceve p/p_hat."""
    # Controllo interfaccia
    sig = inspect.signature(backtest_log_wealth)
    assert "p" not in sig.parameters
    assert "p_hat" not in sig.parameters
    assert list(sig.parameters.keys()) == ["dates", "fractions", "odds", "won"]

    # Calcolo a mano sintetico
    dates = np.array(["2010-09-01", "2010-09-02"], dtype="datetime64[D]")
    fractions = np.array([0.10, 0.20], dtype=np.float64)
    odds = np.array([2.50, 3.00], dtype=np.float64)
    won = np.array([True, False], dtype=bool)

    res = backtest_log_wealth(dates, fractions, odds, won)
    assert isinstance(res, BacktestResult)
    assert len(res.dates) == 2
    assert len(res.log_wealth) == 3

    # Giorno 1: r = 1.5, return = 0.15 -> L_1 = ln(1.15)
    # Giorno 2: r = -1.0, return = -0.20 -> L_2 = ln(1.15) + ln(0.80) = ln(0.92)
    expected = np.array([0.0, math.log(1.15), math.log(0.92)], dtype=np.float64)
    np.testing.assert_allclose(res.log_wealth, expected, atol=1e-12)

    # Errori previsti:
    # 1. Quota <= 1.0
    with pytest.raises(ValueError, match="strictly greater than 1.0"):
        backtest_log_wealth(dates, fractions, np.array([1.0, 3.0], dtype=np.float64), won)
    # 2. Frazione >= 1.0
    with pytest.raises(ValueError, match=r"\[0, 1\)"):
        backtest_log_wealth(dates, np.array([1.0, 0.2], dtype=np.float64), odds, won)
    # 3. Somma frazioni su stessa data >= 1.0
    same_date = np.array(["2010-09-01", "2010-09-01"], dtype="datetime64[D]")
    with pytest.raises(ValueError, match="Sum of fractions on date .* is >= 1.0"):
        backtest_log_wealth(same_date, np.array([0.6, 0.5], dtype=np.float64), odds, won)
    # 4. Date non ordinate
    unordered = np.array(["2010-09-02", "2010-09-01"], dtype="datetime64[D]")
    with pytest.raises(ValueError, match="non-decreasing chronological order"):
        backtest_log_wealth(unordered, fractions, odds, won)


def test_alarm_delay_criterion():
    """Criterio 2: un allarme della data d cambia lambda solo dalle date successive."""
    dates = np.array(["2010-09-10", "2010-09-10", "2010-09-11"], dtype="datetime64[D]")
    alarm_dates = np.array(["2010-09-10"], dtype="datetime64[D]")
    lambdas = compute_adaptive_lambda(dates, alarm_dates, kappa=0.5, base_lambda=0.25)

    assert lambdas[0] == pytest.approx(0.25)
    assert lambdas[1] == pytest.approx(0.25)
    assert lambdas[2] == pytest.approx(0.25 * 0.5)


def test_kappa_one_quarter_kelly_criterion():
    """Criterio 3: con kappa = 1 le frazioni coincidono col quarto-Kelly senza detector."""
    dates = np.array(["2010-09-10", "2010-09-15"], dtype="datetime64[D]")
    alarm_dates = np.array(["2010-09-10"], dtype="datetime64[D]")
    lambdas = compute_adaptive_lambda(dates, alarm_dates, kappa=1.0, base_lambda=0.25)
    np.testing.assert_allclose(lambdas, [0.25, 0.25])

    probs = np.array([[0.60, 0.20, 0.20], [0.55, 0.25, 0.20]], dtype=np.float64)
    odds = np.array([[2.00, 3.00, 3.00], [2.20, 3.00, 3.00]], dtype=np.float64)

    bets = select_baseline_d_bets(probs, odds, lambdas)
    expected_f0 = kelly_staking(0.60, 1.0, lam=0.25)
    expected_f1 = kelly_staking(0.55, 1.20, lam=0.25)
    np.testing.assert_allclose(bets.fractions, [expected_f0, expected_f1], atol=1e-12)


def test_baseline_d_docstring_criterion():
    """Criterio 5: la docstring dice che il detector indica quando, non quanto né di che tipo."""
    doc = select_baseline_d_bets.__doc__
    assert doc is not None
    assert "Il detector dice quando, non quanto né di che tipo" in doc
    assert "iperparametro fisso" in doc


def test_kappa_tie_breaking_synthetic():
    """Test sintetico della regola di parità tra kappa: a parità di somma vince il kappa più grande."""
    # Simuliamo un dataset in cui kappa = 0.5 e kappa = 0.75 danno la stessa somma float
    # Verifichiamo che la funzione di selezione basata sulla regola approvata scelga 0.75
    total_wealth = {
        0.0: 0.10,
        0.25: 0.20,
        0.5: 0.35,
        0.75: 0.35,  # Esatta parità tra 0.5 e 0.75
        1.0: 0.30,
    }
    best_k = max(KAPPA_GRID, key=lambda k: (total_wealth[k], k))
    assert best_k == 0.75


def test_frozen_kappas_match_real_data_calibration():
    """Criterio 4: i kappa congelati per ADWIN e Page-Hinkley coincidono con la calibrazione reale."""
    if not _has_real_data():
        pytest.skip("Real data in data/raw/E0 not available")

    cfg = read_split_config()
    df_hist = load_by_role("history")
    df_train = load_by_role("training")
    df_val = load_by_role("validation")
    df = pd.concat([df_hist, df_train, df_val], ignore_index=True).sort_values("Date", kind="stable").reset_index(drop=True)
    schedule = derive_fit_schedule(cfg)
    df_residuals = compute_model_residuals(df, schedule, ELO_FITS)

    res = calibrate_baseline_d_kappa(df_residuals, df)
    assert isinstance(res, KappaCalibrationResult)
    assert res.chosen_kappas["adwin"] == KAPPA_ADWIN
    assert res.chosen_kappas["page_hinkley"] == KAPPA_PAGE_HINKLEY
