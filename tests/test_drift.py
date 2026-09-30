"""Test unitari per il modulo shk.stats.drift (Task 27).

Verifica sia con test sintetici deterministici sia con test sui dati reali E0
(saltati se assenti) la correttezza di esecuzione, le proprietà degli indici,
l'idempotenza, le validazioni difensive, la regola pura di selezione e la
riproduzione esatta della taratura dei parametri congelati di ADWIN e Page-Hinkley.
"""

from typing import Any

import numpy as np
import pandas as pd
import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.data.split import load_by_role, read_split_config
from shk.model.elo_fit import ELO_FITS, derive_fit_schedule
from shk.model.residuals import compute_model_residuals
from shk.stats.drift import (
    ADWIN_DELTA,
    MATCHDAY_SIZE,
    PAGE_HINKLEY_DELTA,
    PAGE_HINKLEY_THRESHOLD,
    calibrate_drift_detectors,
    compute_matchday_z_scores,
    run_drift_detector,
    select_best_candidate,
)


def _has_real_data() -> bool:
    """Verifica se i dati grezzi sono presenti sul filesystem."""
    return DEFAULT_DATA_DIR.exists() and len(list(DEFAULT_DATA_DIR.glob("*.csv"))) > 0


# ---------------------------------------------------------------------------
# Test Sintetici (senza dati reali)
# ---------------------------------------------------------------------------


def test_run_drift_detector_synthetic_jump():
    """Verifica la rilevazione del drift su un salto di 5 deviazioni standard con i default di river."""
    # Seed fisso prescritto dal protocollo per il test sintetico del salto
    rng = np.random.default_rng(20260930)
    part1 = rng.normal(loc=0.0, scale=1.0, size=200)
    part2 = rng.normal(loc=5.0, scale=1.0, size=200)
    series = np.concatenate([part1, part2])

    alarms_adwin = run_drift_detector(series, "adwin", params=None)
    alarms_ph = run_drift_detector(series, "page_hinkley", params=None)

    # Entrambi i detector devono segnalare almeno un allarme con indice >= 200 (dopo il salto)
    post_jump_adwin = alarms_adwin[alarms_adwin >= 200]
    post_jump_ph = alarms_ph[alarms_ph >= 200]

    assert len(post_jump_adwin) >= 1, f"ADWIN did not detect drift post-jump: {alarms_adwin}"
    assert len(post_jump_ph) >= 1, f"Page-Hinkley did not detect drift post-jump: {alarms_ph}"


def test_run_drift_detector_indices_properties():
    """Verifica che gli indici restituiti siano un ndarray int64, in [0, n) e strettamente crescenti."""
    rng = np.random.default_rng(42)
    series = np.concatenate([rng.normal(0, 1, 100), rng.normal(4, 1, 100)])

    alarms = run_drift_detector(series, "adwin", params={"delta": 0.002})

    assert isinstance(alarms, np.ndarray)
    assert alarms.dtype == np.int64
    if len(alarms) > 0:
        assert np.all(alarms >= 0)
        assert np.all(alarms < len(series))
        # Strettamente crescenti (nessun duplicato)
        assert np.all(np.diff(alarms) > 0)


def test_run_drift_detector_idempotence():
    """Verifica che due chiamate successive sulla stessa serie producano lo stesso risultato senza stato residuo."""
    rng = np.random.default_rng(123)
    series = np.concatenate([rng.normal(0, 1, 150), rng.normal(3, 1, 150)])

    res1_adwin = run_drift_detector(series, "adwin", params={"delta": 0.01})
    res2_adwin = run_drift_detector(series, "adwin", params={"delta": 0.01})
    np.testing.assert_array_equal(res1_adwin, res2_adwin)

    res1_ph = run_drift_detector(series, "page_hinkley", params={"delta": 0.01, "threshold": 10.0})
    res2_ph = run_drift_detector(series, "page_hinkley", params={"delta": 0.01, "threshold": 10.0})
    np.testing.assert_array_equal(res1_ph, res2_ph)


def test_run_drift_detector_validations():
    """Verifica il sollevamento rigoroso di TypeError e ValueError su input non conformi."""
    valid_series = np.array([1.0, 2.0, 3.0], dtype=np.float64)

    # TypeError su tipo series
    with pytest.raises(TypeError, match="numpy.ndarray"):
        run_drift_detector([1.0, 2.0, 3.0], "adwin")  # type: ignore

    # TypeError su dtype non reale
    with pytest.raises(TypeError, match="real numeric"):
        run_drift_detector(np.array([True, False]), "adwin")

    # ValueError su dimensioni non 1D
    with pytest.raises(ValueError, match="1D"):
        run_drift_detector(np.array([[1.0, 2.0], [3.0, 4.0]]), "adwin")

    # ValueError su serie vuota
    with pytest.raises(ValueError, match="empty"):
        run_drift_detector(np.array([], dtype=np.float64), "adwin")

    # ValueError su valori non finiti
    with pytest.raises(ValueError, match="non-finite"):
        run_drift_detector(np.array([1.0, np.nan, 3.0]), "adwin")

    with pytest.raises(ValueError, match="non-finite"):
        run_drift_detector(np.array([1.0, np.inf, 3.0]), "adwin")

    # TypeError su detector non stringa
    with pytest.raises(TypeError, match="str"):
        run_drift_detector(valid_series, 123)  # type: ignore

    # ValueError su detector non ammesso
    with pytest.raises(ValueError, match="detector must be"):
        run_drift_detector(valid_series, "unknown_detector")

    # TypeError su params non Mapping
    with pytest.raises(TypeError, match="Mapping"):
        run_drift_detector(valid_series, "adwin", params=[1, 2])  # type: ignore

    # ValueError su parametri sconosciuti
    with pytest.raises(ValueError, match="Unknown params for adwin"):
        run_drift_detector(valid_series, "adwin", params={"unknown_param": 1.0})

    with pytest.raises(ValueError, match="Unknown params for page_hinkley"):
        run_drift_detector(valid_series, "page_hinkley", params={"clock": 32})


def test_select_best_candidate_pure_rule():
    """Verifica la logica pura di spareggio su distanza intera, totale allarmi e ordine griglia."""
    # Errore su lista vuota
    with pytest.raises(ValueError, match="empty"):
        select_best_candidate([])

    # Caso 1: distanza intera minima vince
    candidates_1 = [
        {"alarms_2000": 1, "alarms_2010": 1, "grid_index": 0},  # total=2, dist=|20-38|=18
        {"alarms_2000": 0, "alarms_2010": 0, "grid_index": 1},  # total=0, dist=|0-38|=38
    ]
    assert select_best_candidate(candidates_1)["grid_index"] == 0

    # Caso 2: a parità di distanza, vince il minor numero totale di allarmi
    # Esempio: totale 1 (dist=|10-38|=28) contro totale 3 (dist=|30-38|=8)? No, cerchiamo distanze uguali:
    # Per avere |10*T - 38| uguale:
    # 38 - 10*T1 = 10*T2 - 38 => 10*(T1 + T2) = 76 (non ha soluzioni intere).
    # Quindi non ci possono essere due somme intere distinte con la stessa distanza da 3.8 / 1.9!
    # Tuttavia, a parità di somma (es. 2 allarmi distribuiti diversamente: (2, 0) vs (1, 1)):
    candidates_2 = [
        {"alarms_2000": 2, "alarms_2010": 0, "grid_index": 5},
        {"alarms_2000": 1, "alarms_2010": 1, "grid_index": 2},
    ]
    # Entrambi hanno dist_int=18 e total_alarms=2: vince grid_index 2
    assert select_best_candidate(candidates_2)["grid_index"] == 2


# ---------------------------------------------------------------------------
# Test sui Dati Reali E0 (saltati se non presenti)
# ---------------------------------------------------------------------------


def test_compute_matchday_z_scores_hand_calculated():
    """Verifica che lo Z per giornata coincida con il calcolo analitico a mano entro 1e-12."""
    # Blocco 1: 10 elementi da 1.1 a 2.0 (media 1.55)
    b1 = np.linspace(1.1, 2.0, 10)
    # Blocco 2: 10 elementi tutti a 0.5 (media 0.5)
    b2 = np.full(10, 0.5)
    series = np.concatenate([b1, b2])

    mu = 1.0
    sigma = 0.5
    # Z1 = (1.55 - 1.0) / (0.5 / sqrt(10)) = 0.55 * sqrt(10) / 0.5 = 1.1 * sqrt(10)
    expected_z1 = 1.1 * np.sqrt(10)
    # Z2 = (0.5 - 1.0) / (0.5 / sqrt(10)) = -0.5 / (0.5 / sqrt(10)) = -sqrt(10)
    expected_z2 = -np.sqrt(10)

    z_scores = compute_matchday_z_scores(series, mu=mu, sigma=sigma, matchday_size=10)
    assert len(z_scores) == 2
    assert z_scores.dtype == np.float64
    np.testing.assert_allclose(z_scores, [expected_z1, expected_z2], atol=1e-12, rtol=1e-12)


def test_compute_matchday_z_scores_exact_zero():
    """Verifica che un blocco con media esattamente uguale a mu dia Z pari a 0.0."""
    series = np.full(30, 1.25)
    z_scores = compute_matchday_z_scores(series, mu=1.25, sigma=0.8, matchday_size=10)
    assert len(z_scores) == 3
    np.testing.assert_allclose(z_scores, np.zeros(3), atol=1e-12)


def test_compute_matchday_z_scores_validations():
    """Verifica le eccezioni TypeError e ValueError su argomenti invalidi."""
    valid_series = np.ones(20, dtype=np.float64)

    # series non ndarray
    with pytest.raises(TypeError, match="series must be a np.ndarray"):
        compute_matchday_z_scores([1.0] * 20, mu=1.0, sigma=0.5)  # type: ignore

    # series booleana o non numerica
    with pytest.raises(TypeError, match="numeric dtype"):
        compute_matchday_z_scores(np.ones(20, dtype=bool), mu=1.0, sigma=0.5)

    # series non 1D
    with pytest.raises(ValueError, match="1D"):
        compute_matchday_z_scores(np.ones((2, 10)), mu=1.0, sigma=0.5)

    # series vuota
    with pytest.raises(ValueError, match="empty"):
        compute_matchday_z_scores(np.array([], dtype=np.float64), mu=1.0, sigma=0.5)

    # lunghezza non multiplo di matchday_size
    with pytest.raises(ValueError, match="multiple of matchday_size"):
        compute_matchday_z_scores(np.ones(25), mu=1.0, sigma=0.5, matchday_size=10)

    # valori non finiti
    nan_series = np.ones(20)
    nan_series[5] = np.nan
    with pytest.raises(ValueError, match="non-finite"):
        compute_matchday_z_scores(nan_series, mu=1.0, sigma=0.5)

    # mu non float / bool
    with pytest.raises(TypeError, match="mu must be a real number"):
        compute_matchday_z_scores(valid_series, mu=True, sigma=0.5)  # type: ignore
    with pytest.raises(ValueError, match="mu must be finite"):
        compute_matchday_z_scores(valid_series, mu=float("inf"), sigma=0.5)

    # sigma non float / bool / non positivo / non finito
    with pytest.raises(TypeError, match="sigma must be a real number"):
        compute_matchday_z_scores(valid_series, mu=1.0, sigma=False)  # type: ignore
    with pytest.raises(ValueError, match="sigma must be strictly positive"):
        compute_matchday_z_scores(valid_series, mu=1.0, sigma=0.0)
    with pytest.raises(ValueError, match="sigma must be strictly positive"):
        compute_matchday_z_scores(valid_series, mu=1.0, sigma=-0.5)
    with pytest.raises(ValueError, match="sigma must be finite"):
        compute_matchday_z_scores(valid_series, mu=1.0, sigma=float("nan"))

    # matchday_size invalido
    with pytest.raises(TypeError, match="matchday_size must be an integer"):
        compute_matchday_z_scores(valid_series, mu=1.0, sigma=0.5, matchday_size=True)  # type: ignore
    with pytest.raises(TypeError, match="matchday_size must be an integer"):
        compute_matchday_z_scores(valid_series, mu=1.0, sigma=0.5, matchday_size=10.0)  # type: ignore
    with pytest.raises(ValueError, match="matchday_size must be positive"):
        compute_matchday_z_scores(valid_series, mu=1.0, sigma=0.5, matchday_size=0)


@pytest.fixture(scope="module")
def real_data_calibration():
    """Carica i dati reali E0, calcola le serie 2000-01 e 2010-11 ed esegue la taratura."""
    if not _has_real_data():
        pytest.skip("Real data in data/raw/E0 not available")

    cfg = read_split_config()
    df_hist = load_by_role("history")
    df_train = load_by_role("training")
    df_val = load_by_role("validation")

    df = pd.concat([df_hist, df_train, df_val], ignore_index=True)
    df = df.sort_values("Date", kind="stable").reset_index(drop=True)

    schedule = derive_fit_schedule(cfg)
    df_res = compute_model_residuals(df, schedule, ELO_FITS)

    s2000 = df_res[
        (df_res["role"] == "training")
        & (df_res["fit_through"] == "2000-01")
        & (df_res["season"] == "2000-01")
    ]["log_loss"].to_numpy()

    s2010 = df_res[
        (df_res["role"] == "training")
        & (df_res["fit_through"] == "2010-11")
        & (df_res["season"] == "2010-11")
    ]["log_loss"].to_numpy()

    best_adwin, best_ph, df_grid = calibrate_drift_detectors(s2000, s2010)

    return {
        "s2000": s2000,
        "s2010": s2010,
        "best_adwin": best_adwin,
        "best_ph": best_ph,
        "df_grid": df_grid,
    }


def test_real_data_calibration_matches_frozen_constants(real_data_calibration):
    """Verifica che la taratura ricalcolata sui dati reali coincida con i parametri congelati."""
    best_adwin = real_data_calibration["best_adwin"]
    best_ph = real_data_calibration["best_ph"]

    # ADWIN: delta congelato deve coincidere con l'ottimo selezionato (0.002)
    assert best_adwin["delta"] == ADWIN_DELTA

    # Page-Hinkley: delta e threshold congelati devono coincidere con l'ottimo selezionato (0.05, 5.0)
    assert best_ph["delta"] == PAGE_HINKLEY_DELTA
    assert best_ph["threshold"] == PAGE_HINKLEY_THRESHOLD


def test_real_data_alarm_counts_reproducible(real_data_calibration):
    """Verifica la riproducibilità esatta dei conteggi di allarmi con i parametri congelati."""
    s2000 = real_data_calibration["s2000"]
    s2010 = real_data_calibration["s2010"]

    assert len(s2000) == 380
    assert len(s2010) == 380

    # ADWIN con parametri congelati: 0 allarmi su entrambe le stagioni
    alarms_adwin_2000 = run_drift_detector(s2000, "adwin", {"delta": ADWIN_DELTA})
    alarms_adwin_2010 = run_drift_detector(s2010, "adwin", {"delta": ADWIN_DELTA})
    assert len(alarms_adwin_2000) == 0
    assert len(alarms_adwin_2010) == 0

    # Page-Hinkley con parametri congelati: 1 allarme su 2000-01 e 1 allarme su 2010-11
    alarms_ph_2000 = run_drift_detector(
        s2000, "page_hinkley", {"delta": PAGE_HINKLEY_DELTA, "threshold": PAGE_HINKLEY_THRESHOLD}
    )
    alarms_ph_2010 = run_drift_detector(
        s2010, "page_hinkley", {"delta": PAGE_HINKLEY_DELTA, "threshold": PAGE_HINKLEY_THRESHOLD}
    )
    assert len(alarms_ph_2000) == 1
    assert len(alarms_ph_2010) == 1
