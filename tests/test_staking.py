"""Test unitari per il modulo di staking del criterio di Kelly."""

import numpy as np
import pytest

from shk.kelly.core import kelly_fraction
from shk.kelly.staking import (
    BASE_LAMBDA,
    KAPPA_GRID,
    BaselineDBets,
    StakingMoments,
    compute_adaptive_lambda,
    kelly_staking,
    plugin_staking,
    select_baseline_d_bets,
    staking_moments,
)


def test_kelly_staking_positive_edge_and_agreement():
    """Verifica la frazione per edge positivo e la concordanza con kelly_fraction."""
    # Criterio 1: p_hat = 0.60, b = 1.0, lam = 1.0 -> 0.20
    actual = kelly_staking(0.60, 1.0, lam=1.0)
    expected_kf = kelly_fraction(0.60, 1.0)
    assert abs(actual - 0.20) < 1e-12
    assert abs(actual - expected_kf) < 1e-12
    assert actual == expected_kf

    # Accordo su una griglia di valori scalari con edge positivo
    for p_val in [0.55, 0.60, 0.70, 0.80, 0.90]:
        for b_val in [1.0, 1.5, 2.0, 3.0]:
            f_staking = kelly_staking(p_val, b_val, lam=1.0)
            f_core = kelly_fraction(p_val, b_val)
            assert abs(f_staking - f_core) < 1e-12


def test_kelly_staking_negative_and_zero_edge():
    """Verifica che edge negativo o nullo restituisca esattamente zero."""
    # Criterio 2: p_hat = 0.468, b = 1.0 -> edge negativo -> 0.0 esatto
    assert kelly_staking(0.468, 1.0, lam=1.0) == 0.0

    # Edge nullo: p_hat = 0.50, b = 1.0 -> 0.0 esatto
    assert kelly_staking(0.50, 1.0, lam=1.0) == 0.0

    # Troncamento vettoriale elemento per elemento
    p_vec = np.array([0.40, 0.50, 0.60])
    expected_vec = np.array([0.0, 0.0, 0.20])
    actual_vec = kelly_staking(p_vec, 1.0, lam=1.0)
    np.testing.assert_allclose(actual_vec, expected_vec, atol=1e-12)


def test_kelly_staking_fractional_multiplier():
    """Verifica che con lam = 0.25 la frazione sia esattamente un quarto rispetto a lam = 1.0."""
    p_hat = 0.60
    b = 1.0
    f_full = kelly_staking(p_hat, b, lam=1.0)
    f_quarter = kelly_staking(p_hat, b, lam=0.25)

    # Criterio 3: un quarto della frazione piena su scalare
    assert abs(f_quarter - 0.25 * f_full) < 1e-12

    # Verifica su matrice (M, T)
    p_mat = np.array([[0.60, 0.70], [0.45, 0.80]])
    f_mat_full = kelly_staking(p_mat, b, lam=1.0)
    f_mat_quarter = kelly_staking(p_mat, b, lam=0.25)
    np.testing.assert_allclose(f_mat_quarter, 0.25 * f_mat_full, rtol=1e-12)


def test_kelly_staking_output_shapes():
    """Verifica che l'output conservi la forma dell'input (scalare, vettore, matrice)."""
    b = 1.0

    # Scalare Python float -> float Python
    out_scalar = kelly_staking(0.60, b)
    assert isinstance(out_scalar, float)
    assert out_scalar == pytest.approx(0.20)

    # Scalare NumPy -> float Python (Precisazione B)
    out_numpy_scalar = kelly_staking(np.float64(0.60), b)
    assert isinstance(out_numpy_scalar, float)
    assert out_numpy_scalar == pytest.approx(0.20)

    # Array 0D NumPy -> float Python (Precisazione B)
    out_0d = kelly_staking(np.array(0.60), b)
    assert isinstance(out_0d, float)
    assert out_0d == pytest.approx(0.20)

    # Vettore 1D (M,) -> ndarray (M,)
    p_1d = np.array([0.55, 0.60, 0.65])
    out_1d = kelly_staking(p_1d, b)
    assert isinstance(out_1d, np.ndarray)
    assert out_1d.shape == (3,)

    # Matrice 2D (M, T) -> ndarray (M, T)
    p_2d = np.full((4, 7), 0.60)
    out_2d = kelly_staking(p_2d, b)
    assert isinstance(out_2d, np.ndarray)
    assert out_2d.shape == (4, 7)


def test_kelly_staking_allows_fraction_ge_one():
    """Verifica che la regola non limiti la frazione sotto 1 (decisione di design)."""
    # Con p_hat = 1.0 e lam = 1.5 -> f = 1.5
    f_high = kelly_staking(1.0, 1.0, lam=1.5)
    assert f_high == pytest.approx(1.5)

    # Con p_hat = 0.8, b = 1.0 -> f_hat = 0.6; con lam = 2.0 -> f = 1.2
    f_over = kelly_staking(0.80, 1.0, lam=2.0)
    assert f_over == pytest.approx(1.2)


def test_kelly_staking_validation_errors():
    """Verifica che vengano sollevate le opportune eccezioni per parametri non validi."""
    # Moltiplicatore lambda negativo o non finito
    with pytest.raises(ValueError):
        kelly_staking(0.60, 1.0, lam=-0.1)
    with pytest.raises(ValueError):
        kelly_staking(0.60, 1.0, lam=float("nan"))
    with pytest.raises(ValueError):
        kelly_staking(0.60, 1.0, lam=float("inf"))

    # Quota b non positiva o non finita
    with pytest.raises(ValueError):
        kelly_staking(0.60, 0.0)
    with pytest.raises(ValueError):
        kelly_staking(0.60, -1.0)
    with pytest.raises(ValueError):
        kelly_staking(0.60, float("nan"))

    # Probabilità p_hat fuori da [0, 1] per scalari
    with pytest.raises(ValueError):
        kelly_staking(-0.01, 1.0)
    with pytest.raises(ValueError):
        kelly_staking(1.01, 1.0)
    with pytest.raises(ValueError):
        kelly_staking(float("nan"), 1.0)
    with pytest.raises(ValueError):
        kelly_staking(float("inf"), 1.0)

    # Probabilità p_hat fuori da [0, 1] per array
    with pytest.raises(ValueError):
        kelly_staking(np.array([0.60, -0.05]), 1.0)
    with pytest.raises(ValueError):
        kelly_staking(np.array([0.60, 1.10]), 1.0)
    with pytest.raises(ValueError):
        kelly_staking(np.array([0.60, np.nan]), 1.0)


def test_staking_moments_hand_calculated():
    """Verifica il calcolo dei momenti empirici di c su valori noti a mano."""
    # f_star = 0.20
    # f_hat = [0.0, 0.10, 0.20, 0.30] -> c = [0.0, 0.5, 1.0, 1.5]
    # E[c] = (0.0 + 0.5 + 1.0 + 1.5) / 4 = 3.0 / 4 = 0.75
    # E[c^2] = (0.0 + 0.25 + 1.0 + 2.25) / 4 = 3.5 / 4 = 0.875
    # Var(c) = 0.875 - 0.75^2 = 0.875 - 0.5625 = 0.3125
    # fraction_zero = 1 / 4 = 0.25
    f_hat = np.array([0.0, 0.10, 0.20, 0.30])
    moments = staking_moments(f_hat, 0.20)
    assert isinstance(moments, StakingMoments)
    assert abs(moments.mean_c - 0.75) < 1e-12
    assert abs(moments.mean_c2 - 0.875) < 1e-12
    assert abs(moments.var_c - 0.3125) < 1e-12
    assert abs(moments.fraction_zero - 0.25) < 1e-12

    # Verifica forma 2D (pooled su tutte le celle)
    f_hat_2d = f_hat.reshape(2, 2)
    moments_2d = staking_moments(f_hat_2d, 0.20)
    assert abs(moments_2d.mean_c - 0.75) < 1e-12
    assert abs(moments_2d.mean_c2 - 0.875) < 1e-12
    assert abs(moments_2d.var_c - 0.3125) < 1e-12
    assert abs(moments_2d.fraction_zero - 0.25) < 1e-12


def test_staking_moments_validation_errors():
    """Verifica le validazioni di input per staking_moments."""
    # f_star <= 0 oppure non finito
    with pytest.raises(ValueError):
        staking_moments(np.array([0.1]), 0.0)
    with pytest.raises(ValueError):
        staking_moments(np.array([0.1]), -0.2)
    with pytest.raises(ValueError):
        staking_moments(np.array([0.1]), float("nan"))
    with pytest.raises(ValueError):
        staking_moments(np.array([0.1]), float("inf"))

    # f_hat con valori negativi o non finiti
    with pytest.raises(ValueError):
        staking_moments(np.array([-0.05, 0.1]), 0.2)
    with pytest.raises(ValueError):
        staking_moments(np.array([np.nan, 0.1]), 0.2)
    with pytest.raises(ValueError):
        staking_moments(np.array([np.inf, 0.1]), 0.2)


def test_plugin_staking_hand_calculated_and_edge_cases():
    """Verifica la regola plug-in con calcoli a mano, casi limite e forme di output."""
    # 1. Caso a mano con edge positivo:
    # p = 0.60, b = 1.0, sigma_p = 0.0283
    # o = 2.0, EV_hat = 0.20, f_base = 0.20
    # ratio = 2.0 * 0.0283 / 0.20 = 0.283
    # lambda_t = 1 / (1 + 0.283^2) = 1 / (1 + 0.080089) = 1 / 1.080089
    # f = lambda_t * 0.20
    b = 1.0
    sigma_p = 0.0283
    expected_lam = 1.0 / (1.0 + (2.0 * sigma_p / 0.20) ** 2)
    expected_f = expected_lam * 0.20
    actual_f = plugin_staking(0.60, b, sigma_p)
    assert isinstance(actual_f, float)
    assert abs(actual_f - expected_f) < 1e-12

    # 2. Casi EV_hat <= 0: restituiscono 0.0 esatto senza RuntimeWarning
    assert plugin_staking(0.468, b, sigma_p) == 0.0
    assert plugin_staking(0.500, b, sigma_p) == 0.0

    # Vettore con valori negativi, nulli e positivi
    p_vec = np.array([0.40, 0.50, 0.60])
    actual_vec = plugin_staking(p_vec, b, sigma_p)
    expected_vec = np.array([0.0, 0.0, expected_f])
    np.testing.assert_allclose(actual_vec, expected_vec, atol=1e-12)

    # 3. Caso sigma_p = 0.0: coincide esattamente con kelly_staking lam = 1.0
    f_zero_sigma = plugin_staking(0.60, b, 0.0)
    assert f_zero_sigma == kelly_staking(0.60, b, lam=1.0)
    f_zero_sigma_vec = plugin_staking(p_vec, b, 0.0)
    np.testing.assert_allclose(f_zero_sigma_vec, kelly_staking(p_vec, b, lam=1.0), atol=1e-12)

    # 4. Forme di output: scalare NumPy e array 0D -> float Python; 1D e 2D -> ndarray
    out_numpy_scalar = plugin_staking(np.float64(0.60), b, sigma_p)
    assert isinstance(out_numpy_scalar, float)
    assert abs(out_numpy_scalar - expected_f) < 1e-12

    out_0d = plugin_staking(np.array(0.60), b, sigma_p)
    assert isinstance(out_0d, float)
    assert abs(out_0d - expected_f) < 1e-12

    out_1d = plugin_staking(p_vec, b, sigma_p)
    assert isinstance(out_1d, np.ndarray)
    assert out_1d.shape == (3,)

    p_2d = np.full((3, 5), 0.60)
    out_2d = plugin_staking(p_2d, b, sigma_p)
    assert isinstance(out_2d, np.ndarray)
    assert out_2d.shape == (3, 5)


def test_plugin_staking_validation_errors():
    """Verifica le validazioni dei parametri per plugin_staking."""
    # sigma_p negativo o non finito
    with pytest.raises(ValueError):
        plugin_staking(0.60, 1.0, -0.01)
    with pytest.raises(ValueError):
        plugin_staking(0.60, 1.0, float("nan"))
    with pytest.raises(ValueError):
        plugin_staking(0.60, 1.0, float("inf"))

    # b <= 0 o non finito
    with pytest.raises(ValueError):
        plugin_staking(0.60, 0.0, 0.0283)
    with pytest.raises(ValueError):
        plugin_staking(0.60, -1.0, 0.0283)
    with pytest.raises(ValueError):
        plugin_staking(0.60, float("nan"), 0.0283)

    # p_hat non valido
    with pytest.raises(ValueError):
        plugin_staking(-0.1, 1.0, 0.0283)
    with pytest.raises(ValueError):
        plugin_staking(1.1, 1.0, 0.0283)
    with pytest.raises(ValueError):
        plugin_staking(np.array([0.60, np.nan]), 1.0, 0.0283)


# --- Test per la regola della Baseline D (Task 31 / US-C5.3) ---

def test_select_baseline_d_bets_positive_edge():
    """Verifica la selezione dell'esito con EV massimo positivo e il calcolo della frazione."""
    probs = np.array([
        [0.60, 0.25, 0.15],  # EV: H = 0.60*2.0 - 1 = 0.20; D = 0.25*3.0 - 1 = -0.25; A = 0.15*4.0 - 1 = -0.40
        [0.20, 0.50, 0.30],  # EV: H = 0.20*3.0 - 1 = -0.40; D = 0.50*2.5 - 1 = 0.25; A = 0.30*3.0 - 1 = -0.10
    ], dtype=np.float64)
    odds = np.array([
        [2.00, 3.00, 4.00],
        [3.00, 2.50, 3.00],
    ], dtype=np.float64)
    lambdas = np.array([0.25, 0.50], dtype=np.float64)

    bets = select_baseline_d_bets(probs, odds, lambdas)

    assert isinstance(bets, BaselineDBets)
    assert list(bets.outcomes) == ["H", "D"]
    np.testing.assert_allclose(bets.odds, [2.00, 2.50])

    # Per partita 0: p = 0.60, b = 1.0, lam = 0.25 -> kelly_staking(0.60, 1.0, 0.25) = 0.25 * 0.20 = 0.05
    expected_f0 = kelly_staking(0.60, 1.0, lam=0.25)
    # Per partita 1: p = 0.50, b = 1.5, lam = 0.50 -> kelly_staking(0.50, 1.5, 0.50)
    expected_f1 = kelly_staking(0.50, 1.5, lam=0.50)

    np.testing.assert_allclose(bets.fractions, [expected_f0, expected_f1], atol=1e-12)


def test_select_baseline_d_bets_negative_or_zero_edge():
    """Verifica che con edge negativo o nullo la frazione sia esattamente 0.0."""
    # Tutte quote egee negative
    probs = np.array([[0.30, 0.30, 0.40]], dtype=np.float64)
    odds = np.array([[2.00, 2.00, 2.00]], dtype=np.float64)
    # EV: 0.6 - 1 = -0.4, 0.6 - 1 = -0.4, 0.8 - 1 = -0.2 (max è A con -0.2 <= 0)
    lambdas = np.array([0.25], dtype=np.float64)

    bets = select_baseline_d_bets(probs, odds, lambdas)
    assert bets.outcomes[0] == "A"
    assert bets.odds[0] == 2.00
    assert bets.fractions[0] == 0.0


def test_select_baseline_d_bets_tie_breaking_synthetic():
    """Verifica sintetica della regola di parità tra esiti: a parità di EV vince H > D > A."""
    # Caso 1: EV_H == EV_D = 0.25 esatto > EV_A
    probs_1 = np.array([[0.50, 0.25, 0.125]], dtype=np.float64)
    odds_1 = np.array([[2.50, 5.00, 2.00]], dtype=np.float64)
    # EV_H = 0.50*2.5 - 1 = 0.25; EV_D = 0.25*5.0 - 1 = 0.25; EV_A = 0.125*2.0 - 1 = -0.75
    bets_1 = select_baseline_d_bets(probs_1, odds_1, np.array([0.25]))
    assert bets_1.outcomes[0] == "H"
    assert bets_1.odds[0] == 2.50

    # Caso 2: EV_D == EV_A = 0.25 esatto > EV_H
    probs_2 = np.array([[0.125, 0.50, 0.25]], dtype=np.float64)
    odds_2 = np.array([[2.00, 2.50, 5.00]], dtype=np.float64)
    # EV_H = -0.75; EV_D = 0.25; EV_A = 0.25
    bets_2 = select_baseline_d_bets(probs_2, odds_2, np.array([0.25]))
    assert bets_2.outcomes[0] == "D"
    assert bets_2.odds[0] == 2.50

    # Caso 3: EV_H == EV_D == EV_A = 0.25 esatto
    probs_3 = np.array([[0.50, 0.50, 0.50]], dtype=np.float64)
    odds_3 = np.array([[2.50, 2.50, 2.50]], dtype=np.float64)
    bets_3 = select_baseline_d_bets(probs_3, odds_3, np.array([0.25]))
    assert bets_3.outcomes[0] == "H"
    assert bets_3.odds[0] == 2.50


def test_adaptive_lambda_alarm_timing():
    """Verifica che un allarme alla data d modifichi lambda solo dalle date successive (Date > d)."""
    match_dates = np.array([
        "2010-09-01",  # prima dell'allarme -> lambda = 0.25
        "2010-09-10",  # data dell'allarme -> lambda = 0.25 (stessa data, non anteriore)
        "2010-09-10",  # altra partita stessa data -> lambda = 0.25
        "2010-09-11",  # data successiva -> lambda = 0.25 * kappa
        "2010-09-15",  # data successiva -> lambda = 0.25 * kappa
    ], dtype="datetime64[D]")

    alarm_dates = np.array(["2010-09-10"], dtype="datetime64[D]")
    kappa = 0.50

    lambdas = compute_adaptive_lambda(match_dates, alarm_dates, kappa=kappa, base_lambda=0.25)

    assert lambdas[0] == pytest.approx(0.25)
    assert lambdas[1] == pytest.approx(0.25)
    assert lambdas[2] == pytest.approx(0.25)
    assert lambdas[3] == pytest.approx(0.25 * 0.50)
    assert lambdas[4] == pytest.approx(0.25 * 0.50)


def test_adaptive_lambda_multiple_alarms_accumulate():
    """Verifica che allarmi multipli si accumulino come kappa^k per partite successive."""
    match_dates = np.array([
        "2010-09-01",  # k = 0 -> 0.25
        "2010-09-11",  # k = 1 -> 0.25 * 0.5
        "2010-09-21",  # k = 2 -> 0.25 * 0.25
    ], dtype="datetime64[D]")

    alarm_dates = np.array(["2010-09-05", "2010-09-15"], dtype="datetime64[D]")
    kappa = 0.50

    lambdas = compute_adaptive_lambda(match_dates, alarm_dates, kappa=kappa, base_lambda=0.25)
    expected = [0.25, 0.25 * 0.5, 0.25 * 0.25]
    np.testing.assert_allclose(lambdas, expected)


def test_adaptive_lambda_kappa_one_matches_quarter_kelly():
    """Con kappa = 1.0 le frazioni e lambda coincidono costantemente con quarto-Kelly senza detector."""
    match_dates = np.array(["2010-09-01", "2010-09-10", "2010-09-20"], dtype="datetime64[D]")
    alarm_dates = np.array(["2010-09-05", "2010-09-15"], dtype="datetime64[D]")

    lambdas = compute_adaptive_lambda(match_dates, alarm_dates, kappa=1.0, base_lambda=0.25)
    np.testing.assert_allclose(lambdas, np.full(3, 0.25))

    probs = np.array([[0.60, 0.20, 0.20]] * 3, dtype=np.float64)
    odds = np.array([[2.00, 3.00, 3.00]] * 3, dtype=np.float64)

    bets_adaptive = select_baseline_d_bets(probs, odds, lambdas)
    expected_f = kelly_staking(0.60, 1.0, lam=0.25)
    np.testing.assert_allclose(bets_adaptive.fractions, np.full(3, expected_f))


def test_adaptive_lambda_zero_kappa():
    """Con kappa = 0.0 dopo il primo allarme lambda scende a 0.0 esatto per le date successive."""
    match_dates = np.array(["2010-09-01", "2010-09-10"], dtype="datetime64[D]")
    alarm_dates = np.array(["2010-09-05"], dtype="datetime64[D]")

    lambdas = compute_adaptive_lambda(match_dates, alarm_dates, kappa=0.0, base_lambda=0.25)
    assert lambdas[0] == pytest.approx(0.25)
    assert lambdas[1] == pytest.approx(0.0)


def test_baseline_d_rule_docstring_content():
    """Verifica che la docstring di select_baseline_d_bets contenga il testo prescritto."""
    doc = select_baseline_d_bets.__doc__
    assert doc is not None
    assert "Il detector dice quando, non quanto né di che tipo" in doc
    assert "iperparametro fisso" in doc


