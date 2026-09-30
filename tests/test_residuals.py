"""Test per il modulo shk.model.residuals (Task 26).

Verifica sia con test sintetici deterministici sia con test sui dati reali E0
(saltati se assenti) la correttezza di schema, ordinamento, log-loss puntuale,
ripetizione del training tra fit, validazioni difensive e riproduzione esatta
delle log-loss medie di riferimento di C4.1.
"""

import math
import time
from typing import Final

import numpy as np
import pandas as pd
import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.data.split import load_by_role, read_split_config
from shk.model.elo_fit import (
    ELO_FITS,
    EloFitParams,
    compute_training_log_loss,
    derive_fit_schedule,
    parse_season_start_year,
)
from shk.model.residuals import RESIDUALS_COLUMNS, compute_model_residuals


def _has_real_data() -> bool:
    """Verifica se i dati grezzi sono presenti sul filesystem."""
    return DEFAULT_DATA_DIR.exists() and len(list(DEFAULT_DATA_DIR.glob("*.csv"))) > 0


def _create_synthetic_dataset() -> pd.DataFrame:
    """Crea un dataset sintetico a 3 stagioni consecutive (2000-01, 2001-02, 2002-03)."""
    d1 = [
        {"Date": pd.Timestamp("2000-08-15"), "season": "2000-01", "HomeTeam": "A", "AwayTeam": "B", "FTR": "H", "FTHG": 2, "FTAG": 0},
        {"Date": pd.Timestamp("2000-08-15"), "season": "2000-01", "HomeTeam": "C", "AwayTeam": "D", "FTR": "A", "FTHG": 0, "FTAG": 1},
        {"Date": pd.Timestamp("2000-08-22"), "season": "2000-01", "HomeTeam": "A", "AwayTeam": "C", "FTR": "H", "FTHG": 3, "FTAG": 0},
        {"Date": pd.Timestamp("2000-08-22"), "season": "2000-01", "HomeTeam": "B", "AwayTeam": "D", "FTR": "D", "FTHG": 1, "FTAG": 1},
    ]
    d2 = [
        {"Date": pd.Timestamp("2001-08-18"), "season": "2001-02", "HomeTeam": "A", "AwayTeam": "B", "FTR": "H", "FTHG": 2, "FTAG": 1},
        {"Date": pd.Timestamp("2001-08-18"), "season": "2001-02", "HomeTeam": "C", "AwayTeam": "D", "FTR": "A", "FTHG": 0, "FTAG": 2},
        {"Date": pd.Timestamp("2001-08-25"), "season": "2001-02", "HomeTeam": "B", "AwayTeam": "C", "FTR": "D", "FTHG": 1, "FTAG": 1},
        {"Date": pd.Timestamp("2001-08-25"), "season": "2001-02", "HomeTeam": "A", "AwayTeam": "D", "FTR": "H", "FTHG": 3, "FTAG": 1},
    ]
    d3 = [
        {"Date": pd.Timestamp("2002-08-17"), "season": "2002-03", "HomeTeam": "A", "AwayTeam": "C", "FTR": "D", "FTHG": 1, "FTAG": 1},
        {"Date": pd.Timestamp("2002-08-17"), "season": "2002-03", "HomeTeam": "B", "AwayTeam": "D", "FTR": "H", "FTHG": 2, "FTAG": 0},
        {"Date": pd.Timestamp("2002-08-24"), "season": "2002-03", "HomeTeam": "C", "AwayTeam": "D", "FTR": "H", "FTHG": 3, "FTAG": 1},
        {"Date": pd.Timestamp("2002-08-24"), "season": "2002-03", "HomeTeam": "A", "AwayTeam": "B", "FTR": "H", "FTHG": 2, "FTAG": 1},
    ]
    df = pd.DataFrame(d1 + d2 + d3)
    df["Date"] = pd.to_datetime(df["Date"])
    return df


# ---------------------------------------------------------------------------
# Test Sintetici (senza dati reali)
# ---------------------------------------------------------------------------


def test_residuals_schema_and_dtypes():
    """Verifica le 11 colonne restituite, l'ordine delle colonne e la conservazione del dtype di Date."""
    df = _create_synthetic_dataset()
    schedule = {
        "2001-02": {
            "training": ["2000-01", "2001-02"],
            "validation": ["2002-03"],
        }
    }
    fits = {
        "2001-02": EloFitParams(k=10.0, h=50.0, nu=0.3, c=0.25),
    }

    res = compute_model_residuals(df, schedule, fits)

    assert list(res.columns) == list(RESIDUALS_COLUMNS)
    assert len(res) == (4 + 4) + 4  # 8 training + 4 validation = 12 partite
    assert res["Date"].dtype == df["Date"].dtype
    assert set(res["role"].unique()) == {"training", "validation"}
    assert set(res["fit_through"].unique()) == {"2001-02"}
    assert res["log_loss"].dtype == np.float64
    assert res["p_home"].dtype == np.float64
    assert res["p_draw"].dtype == np.float64
    assert res["p_away"].dtype == np.float64


def test_residuals_ordering():
    """Verifica l'ordinamento: fit cronologico, poi training prima di validazione, poi Date stabile."""
    df = _create_synthetic_dataset()
    schedule = {
        "2000-01": {
            "training": ["2000-01"],
            "validation": ["2001-02"],
        },
        "2001-02": {
            "training": ["2000-01", "2001-02"],
            "validation": ["2002-03"],
        },
    }
    fits = {
        "2000-01": EloFitParams(k=10.0, h=50.0, nu=0.3, c=0.25),
        "2001-02": EloFitParams(k=15.0, h=60.0, nu=0.25, c=0.25),
    }

    res = compute_model_residuals(df, schedule, fits)

    # I fit devono essere ordinati cronologicamente
    unique_fits_in_order = list(dict.fromkeys(res["fit_through"]))
    assert unique_fits_in_order == ["2000-01", "2001-02"]

    # Per ciascun fit, prima le righe training poi validation
    for fit_k in ["2000-01", "2001-02"]:
        sub = res[res["fit_through"] == fit_k].reset_index(drop=True)
        roles = list(sub["role"])
        first_val_idx = roles.index("validation") if "validation" in roles else len(roles)
        # Tutte le righe prima di first_val_idx devono essere training
        assert all(r == "training" for r in roles[:first_val_idx])
        # Tutte le righe da first_val_idx in poi devono essere validation
        assert all(r == "validation" for r in roles[first_val_idx:])

        # Le date all'interno di ciascun ruolo devono essere monotone non decrescenti
        train_dates = sub[sub["role"] == "training"]["Date"]
        assert train_dates.is_monotonic_increasing
        val_dates = sub[sub["role"] == "validation"]["Date"]
        assert val_dates.is_monotonic_increasing


def test_residuals_log_loss_pointwise_accuracy():
    """Verifica che log_loss sia esattamente uguale a -ln(p_realized) calcolato a mano."""
    df = _create_synthetic_dataset()
    schedule = {
        "2000-01": {
            "training": ["2000-01"],
            "validation": ["2001-02"],
        }
    }
    fits = {
        "2000-01": EloFitParams(k=10.0, h=50.0, nu=0.3, c=0.25),
    }

    res = compute_model_residuals(df, schedule, fits)

    for _, row in res.iterrows():
        ftr = row["FTR"]
        if ftr == "H":
            p_realized = row["p_home"]
        elif ftr == "D":
            p_realized = row["p_draw"]
        else:
            p_realized = row["p_away"]

        expected_loss = -math.log(p_realized)
        assert math.isclose(row["log_loss"], expected_loss, rel_tol=1e-12, abs_tol=1e-12)


def test_residuals_repeated_training_seasons():
    """Verifica che una stagione di training presente in più fit compaia in ciascun fit con i rispettivi parametri."""
    df = _create_synthetic_dataset()
    schedule = {
        "2000-01": {
            "training": ["2000-01"],
            "validation": ["2001-02"],
        },
        "2001-02": {
            "training": ["2000-01", "2001-02"],
            "validation": ["2002-03"],
        },
    }
    # Parametri diversi per i due fit per verificare che le quote/probabilità differiscano
    fits = {
        "2000-01": EloFitParams(k=10.0, h=50.0, nu=0.3, c=0.25),
        "2001-02": EloFitParams(k=25.0, h=100.0, nu=0.5, c=0.28),
    }

    res = compute_model_residuals(df, schedule, fits)

    s2000_fit1 = res[(res["fit_through"] == "2000-01") & (res["season"] == "2000-01") & (res["role"] == "training")]
    s2000_fit2 = res[(res["fit_through"] == "2001-02") & (res["season"] == "2000-01") & (res["role"] == "training")]

    assert len(s2000_fit1) == 4
    assert len(s2000_fit2) == 4

    # Le probabilità devono differire perché K e h sono diversi
    assert not np.allclose(s2000_fit1["p_home"].to_numpy(), s2000_fit2["p_home"].to_numpy())


def test_residuals_input_validations():
    """Verifica il sollevamento di TypeError e ValueError in apertura di funzione su input invalidi."""
    df = _create_synthetic_dataset()
    schedule = {
        "2001-02": {
            "training": ["2000-01", "2001-02"],
            "validation": ["2002-03"],
        }
    }
    fits = {
        "2001-02": EloFitParams(k=10.0, h=50.0, nu=0.3, c=0.25),
    }

    # TypeError per df non DataFrame
    with pytest.raises(TypeError, match="DataFrame"):
        compute_model_residuals([1, 2, 3], schedule, fits)  # type: ignore

    # TypeError per schedule non dict
    with pytest.raises(TypeError, match="dict"):
        compute_model_residuals(df, "not_a_dict", fits)  # type: ignore

    # TypeError per fits non dict
    with pytest.raises(TypeError, match="dict"):
        compute_model_residuals(df, schedule, "not_a_dict")  # type: ignore

    # ValueError per df vuoto
    with pytest.raises(ValueError, match="empty"):
        compute_model_residuals(pd.DataFrame(), schedule, fits)

    # ValueError per colonna obbligatoria mancante
    df_missing = df.drop(columns=["FTR"])
    with pytest.raises(ValueError, match="missing required columns"):
        compute_model_residuals(df_missing, schedule, fits)

    # ValueError per Date non monotone
    df_unsorted = df.copy()
    df_unsorted.iloc[0, df_unsorted.columns.get_loc("Date")] = pd.Timestamp("2099-01-01")
    with pytest.raises(ValueError, match="monotonically non-decreasing"):
        compute_model_residuals(df_unsorted, schedule, fits)

    # ValueError per fit_through in schedule non presente in fits
    schedule_bad_fit = {
        "1999-00": {
            "training": ["1999-00"],
            "validation": ["2000-01"],
        }
    }
    with pytest.raises(ValueError, match="not present in fits"):
        compute_model_residuals(df, schedule_bad_fit, fits)


# ---------------------------------------------------------------------------
# Test sui Dati Reali E0 (saltati se non presenti)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def real_data_computation():
    """Carica i dati reali E0, calcola compute_model_residuals e misura il tempo di esecuzione."""
    if not _has_real_data():
        pytest.skip("Real data in data/raw/E0 not available")

    cfg = read_split_config()
    df_hist = load_by_role("history")
    df_train = load_by_role("training")
    df_val = load_by_role("validation")

    df = pd.concat([df_hist, df_train, df_val], ignore_index=True)
    df = df.sort_values("Date", kind="stable").reset_index(drop=True)

    schedule = derive_fit_schedule(cfg)

    t0 = time.perf_counter()
    df_residuals = compute_model_residuals(df, schedule, ELO_FITS)
    duration_s = time.perf_counter() - t0

    return {
        "df_residuals": df_residuals,
        "duration_s": duration_s,
        "schedule": schedule,
        "df": df,
    }


def test_residuals_real_data_match_counts(real_data_computation):
    """Verifica i conteggi esatti delle partite: 380, 760, 1140 (training) e 3040, 3420, 760 (validazione)."""
    res = real_data_computation["df_residuals"]

    # 1. Righe di training per fit
    n_tr_2000 = len(res[(res["fit_through"] == "2000-01") & (res["role"] == "training")])
    n_tr_2010 = len(res[(res["fit_through"] == "2010-11") & (res["role"] == "training")])
    n_tr_2020 = len(res[(res["fit_through"] == "2020-21") & (res["role"] == "training")])

    assert n_tr_2000 == 380
    assert n_tr_2010 == 760
    assert n_tr_2020 == 1140

    # 2. Righe di validazione per fit
    n_val_2000 = len(res[(res["fit_through"] == "2000-01") & (res["role"] == "validation")])
    n_val_2010 = len(res[(res["fit_through"] == "2010-11") & (res["role"] == "validation")])
    n_val_2020 = len(res[(res["fit_through"] == "2020-21") & (res["role"] == "validation")])

    assert n_val_2000 == 3040
    assert n_val_2010 == 3420
    assert n_val_2020 == 760

    # 3. Totale righe: 2280 training + 7220 validazione = 9500
    assert len(res) == 9500


def test_residuals_real_data_log_loss_benchmarks(real_data_computation):
    """Verifica la coincidenza delle medie di log-loss con i riferimenti di C4.1 entro 5e-7 e con compute_training_log_loss entro 1e-12."""
    res = real_data_computation["df_residuals"]
    schedule = real_data_computation["schedule"]
    df = real_data_computation["df"]

    # Benchmark C4.1 di training
    m_tr_2000 = float(res[(res["fit_through"] == "2000-01") & (res["role"] == "training")]["log_loss"].mean())
    m_tr_2010 = float(res[(res["fit_through"] == "2010-11") & (res["role"] == "training")]["log_loss"].mean())
    m_tr_2020 = float(res[(res["fit_through"] == "2020-21") & (res["role"] == "training")]["log_loss"].mean())

    assert m_tr_2000 == pytest.approx(1.008189, abs=5e-7)
    assert m_tr_2010 == pytest.approx(1.008987, abs=5e-7)
    assert m_tr_2020 == pytest.approx(1.020937, abs=5e-7)

    # Benchmark C4.1 di validazione
    m_val_2000 = float(res[(res["fit_through"] == "2000-01") & (res["role"] == "validation")]["log_loss"].mean())
    m_val_2010 = float(res[(res["fit_through"] == "2010-11") & (res["role"] == "validation")]["log_loss"].mean())
    m_val_2020 = float(res[(res["fit_through"] == "2020-21") & (res["role"] == "validation")]["log_loss"].mean())

    assert m_val_2000 == pytest.approx(0.973761, abs=5e-7)
    assert m_val_2010 == pytest.approx(0.983832, abs=5e-7)
    assert m_val_2020 == pytest.approx(0.983300, abs=5e-7)

    # Validazione aggregata su tutte le 7220 partite
    m_val_all = float(res[res["role"] == "validation"]["log_loss"].mean())
    assert m_val_all == pytest.approx(0.979536, abs=5e-7)

    # Controllo punto (f): coincidenza entro 1e-12 con compute_training_log_loss per ciascun fit
    for fit_k, params in ELO_FITS.items():
        train_seasons = schedule[fit_k]["training"]
        j_year = parse_season_start_year(fit_k)
        season_years = df["season"].map(parse_season_start_year)
        df_sub = df[season_years <= j_year].copy().reset_index(drop=True)
        df_gt = df_sub[df_sub["season"].isin(train_seasons)].copy().reset_index(drop=True)

        ref_loss, _ = compute_training_log_loss(
            df_sub,
            train_seasons,
            params.k,
            params.h,
            params.nu,
            df_gt,
        )
        actual_loss = float(res[(res["fit_through"] == fit_k) & (res["role"] == "training")]["log_loss"].mean())
        assert math.isclose(actual_loss, ref_loss, rel_tol=1e-12, abs_tol=1e-12)


def test_residuals_real_data_properties(real_data_computation):
    """Verifica che log_loss sia finita e strettamente positiva (> 0) e che le date siano monotone."""
    res = real_data_computation["df_residuals"]

    # log_loss finita e strettamente positiva su tutte le 9500 righe
    losses = res["log_loss"].to_numpy()
    assert np.all(np.isfinite(losses))
    assert np.all(losses > 0.0)

    # Monotonicità per ciascun blocco (fit_through, role)
    for fit_k in ["2000-01", "2010-11", "2020-21"]:
        for r in ["training", "validation"]:
            sub = res[(res["fit_through"] == fit_k) & (res["role"] == r)]
            assert sub["Date"].is_monotonic_increasing


def test_residuals_no_test_leakage(real_data_computation):
    """Verifica che la stagione di test '2023-24' non compaia in nessuna riga."""
    res = real_data_computation["df_residuals"]
    assert "2023-24" not in res["season"].values
