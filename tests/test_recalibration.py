"""Test unitari per il modulo shk.model.recalibration."""

import math
import numpy as np
import pandas as pd
import pytest

from shk.model.recalibration import (
    PROB_LOWER_CLIP,
    PROB_UPPER_CLIP,
    brier_score,
    compute_brier_scores,
    compute_reliability_table,
    fit_all_calibration_maps,
    fit_isotonic_single,
    fit_platt_single,
    predict_isotonic_single,
    predict_platt_single,
    recalibrate_series_predictions,
)
from shk.model.scoring import SeriesEvaluationData


def test_brier_score_hand_calculated():
    """Verifica il calcolo esatto del Brier score multiclasse su un caso a mano."""
    probs = np.array([
        [0.6, 0.3, 0.1],
        [0.2, 0.5, 0.3],
    ], dtype=np.float64)
    outcomes = np.array(["H", "D"])

    # Partita 1 (H): (0.6 - 1)^2 + (0.3 - 0)^2 + (0.1 - 0)^2 = 0.16 + 0.09 + 0.01 = 0.26
    # Partita 2 (D): (0.2 - 0)^2 + (0.5 - 1)^2 + (0.3 - 0)^2 = 0.04 + 0.25 + 0.09 = 0.38
    expected_scores = np.array([0.26, 0.38], dtype=np.float64)
    expected_mean = float(np.mean(expected_scores))

    actual_scores = compute_brier_scores(probs, outcomes)
    actual_mean = brier_score(probs, outcomes)

    np.testing.assert_allclose(actual_scores, expected_scores, rtol=1e-14, atol=1e-14)
    assert math.isclose(actual_mean, expected_mean, rel_tol=1e-14, abs_tol=1e-14)


def test_brier_score_validations():
    """Verifica il sollevamento di eccezioni su tipi e forme non conformi."""
    with pytest.raises(TypeError, match="numpy.ndarray"):
        brier_score([[0.5, 0.3, 0.2]], np.array(["H"]))  # type: ignore

    with pytest.raises(TypeError, match="numpy.ndarray"):
        brier_score(np.array([[0.5, 0.3, 0.2]]), ["H"])  # type: ignore

    with pytest.raises(ValueError, match="shape"):
        brier_score(np.array([[0.5, 0.5]]), np.array(["H"]))

    with pytest.raises(ValueError, match="length"):
        brier_score(np.array([[0.5, 0.3, 0.2]]), np.array(["H", "D"]))

    with pytest.raises(ValueError, match="Invalid outcome"):
        brier_score(np.array([[0.5, 0.3, 0.2]]), np.array(["X"]))


def test_reliability_table_properties():
    """Verifica 10 bin, formula di z e trattamento dei bin vuoti."""
    probs = np.array([
        [0.05, 0.45, 0.50],
        [0.15, 0.35, 0.50],
        [0.25, 0.35, 0.40],
        [0.95, 0.03, 0.02],
    ], dtype=np.float64)
    outcomes = np.array(["D", "H", "A", "H"])

    table_h = compute_reliability_table(probs, outcomes, outcome_filter="H", n_bins=10)
    assert len(table_h) == 10

    total_count = sum(b["count"] for b in table_h)
    assert total_count == 4

    # Bin 0: [0.0, 0.1) -> include p=0.05 (esito D -> y=0)
    b0 = table_h[0]
    assert b0["count"] == 1
    assert math.isclose(b0["mean_predicted"], 0.05)
    assert math.isclose(b0["observed_frequency"], 0.0)
    assert math.isclose(b0["gap"], -0.05)
    expected_z0 = -0.05 / math.sqrt(0.05 * 0.95 / 1)
    assert math.isclose(b0["z"], expected_z0, rel_tol=1e-12)

    # Bin vuoto (es. bin 4: [0.4, 0.5))
    b4 = table_h[4]
    assert b4["count"] == 0
    assert b4["mean_predicted"] is None
    assert b4["observed_frequency"] is None
    assert b4["gap"] is None
    assert b4["z"] is None


def test_isotonic_fit_predict_properties():
    """Verifica la stima isotonica con ties aggregati, interpolazione ed estrapolazione costante."""
    # Dati di addestramento con legami
    p_train = np.array([0.2, 0.2, 0.4, 0.6, 0.8, 0.8], dtype=np.float64)
    y_train = np.array([0.0, 1.0, 0.0, 1.0, 1.0, 1.0], dtype=np.float64)

    model = fit_isotonic_single(p_train, y_train)

    # Monotonia non decrescente sui punti di supporto
    assert np.all(np.diff(model.p_support) > 0)
    assert np.all(np.diff(model.q_support) >= 0)

    # Punti di test: dentro, a sinistra e a destra
    p_test = np.array([0.1, 0.2, 0.3, 0.8, 0.95], dtype=np.float64)
    q_pred = predict_isotonic_single(model, p_test)

    # Monotonia dell'output
    assert np.all(np.diff(q_pred) >= 0)
    # Estrapolazione costante a sinistra e destra
    assert math.isclose(q_pred[0], model.q_support[0])
    assert math.isclose(q_pred[-1], model.q_support[-1])


def test_platt_fit_predict_properties():
    """Verifica la stima deterministica di Platt scaling e convergenza da (1, 0)."""
    p_train = np.linspace(0.1, 0.9, 20)
    y_train = (p_train > 0.5).astype(np.float64)

    model = fit_platt_single(p_train, y_train)

    assert model.success is True
    assert model.nit > 0
    assert model.a > 0  # Direzione positiva di regressione

    p_test = np.array([0.2, 0.5, 0.8])
    q_pred = predict_platt_single(model, p_test)
    assert np.all(q_pred >= 0.0)
    assert np.all(q_pred <= 1.0)
    assert np.all(np.diff(q_pred) > 0)


def test_out_of_sample_invariance_synthetic():
    """Verifica che alterare gli esiti di validazione non cambi le mappe di ricalibrazione."""
    # Creiamo un DataFrame sintetico con storia, training e validazione (stagioni consecutive)
    df_synth = pd.DataFrame({
        "season": ["2000-01"] * 4 + ["2001-02"] * 2,
        "Date": pd.date_range("2000-09-01", periods=6, freq="D"),
        "HomeTeam": ["T1", "T2", "T1", "T3", "T1", "T2"],
        "AwayTeam": ["T2", "T1", "T3", "T1", "T2", "T1"],
        "FTR": ["H", "D", "A", "H", "H", "A"],
        "FTHG": [1, 0, 0, 2, 1, 0],
        "FTAG": [0, 0, 1, 0, 0, 1],
        "B365H": [2.0] * 6,
        "B365D": [3.0] * 6,
        "B365A": [4.0] * 6,
    })

    schedule = {
        "2000-01": {
            "training": ["2000-01"],
            "validation": ["2001-02"],
        }
    }

    from shk.model.elo_fit import EloFitParams
    fit_params = {"2000-01": EloFitParams(k=20.0, h=60.0, nu=1.0, c=0.25)}

    maps1 = fit_all_calibration_maps(df_synth, fit_params, schedule)

    # Alteriamo solo gli esiti delle partite di validazione (2001-02)
    df_synth_altered = df_synth.copy()
    df_synth_altered.loc[df_synth_altered["season"] == "2001-02", "FTR"] = ["D", "D"]

    maps2 = fit_all_calibration_maps(df_synth_altered, fit_params, schedule)

    # Le mappe stimate sul training devono coincidere esattamente
    for out in ("H", "D", "A"):
        np.testing.assert_array_equal(
            maps1["2000-01"].isotonic[out].q_support,
            maps2["2000-01"].isotonic[out].q_support,
        )
        assert math.isclose(maps1["2000-01"].platt[out].a, maps2["2000-01"].platt[out].a)
        assert math.isclose(maps1["2000-01"].platt[out].b, maps2["2000-01"].platt[out].b)
