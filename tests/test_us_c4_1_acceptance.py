"""Test di accettazione e di unità per la calibrazione Elo e previsioni walk-forward (US-C4.1)."""

import csv
import math
from pathlib import Path
from typing import Final
import numpy as np
import pandas as pd
import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.data.split import load_by_role, read_split_config
from shk.model.elo_fit import (
    ELO_FITS,
    WALKFORWARD_CSV_COLUMNS,
    calibrate_single_fit,
    compute_training_log_loss,
    derive_fit_schedule,
    parse_season_start_year,
)
from shk.model.elo_predictor import predict_elo_fast

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
CSV_PATH: Final[Path] = REPO_ROOT / "results" / "us_c4_1_elo_walkforward.csv"
PNG_PATH: Final[Path] = REPO_ROOT / "thesis" / "figures" / "us_c4_1_elo_walkforward.png"


def _has_real_data() -> bool:
    """Verifica se i file CSV dei dati reali sono presenti."""
    return DEFAULT_DATA_DIR.exists() and len(list(DEFAULT_DATA_DIR.glob("*.csv"))) > 0


def _create_synthetic_multiseason_data() -> pd.DataFrame:
    """Crea un dataset sintetico a 3 stagioni per verificare l'invarianza del training."""
    records = [
        # Stagione 2000-01 (training)
        {"Date": pd.Timestamp("2000-08-15"), "season": "2000-01", "HomeTeam": "A", "AwayTeam": "B", "FTR": "H", "FTHG": 2, "FTAG": 0},
        {"Date": pd.Timestamp("2000-08-15"), "season": "2000-01", "HomeTeam": "C", "AwayTeam": "D", "FTR": "A", "FTHG": 0, "FTAG": 1},
        {"Date": pd.Timestamp("2000-08-22"), "season": "2000-01", "HomeTeam": "A", "AwayTeam": "C", "FTR": "H", "FTHG": 3, "FTAG": 0},
        {"Date": pd.Timestamp("2000-08-22"), "season": "2000-01", "HomeTeam": "B", "AwayTeam": "D", "FTR": "D", "FTHG": 1, "FTAG": 1},
        # Stagione 2001-02 (non-training posteriore)
        {"Date": pd.Timestamp("2001-08-18"), "season": "2001-02", "HomeTeam": "A", "AwayTeam": "B", "FTR": "H", "FTHG": 1, "FTAG": 0},
        {"Date": pd.Timestamp("2001-08-18"), "season": "2001-02", "HomeTeam": "C", "AwayTeam": "D", "FTR": "H", "FTHG": 2, "FTAG": 1},
        # Stagione 2002-03 (non-training posteriore)
        {"Date": pd.Timestamp("2002-08-17"), "season": "2002-03", "HomeTeam": "A", "AwayTeam": "C", "FTR": "D", "FTHG": 1, "FTAG": 1},
        {"Date": pd.Timestamp("2002-08-17"), "season": "2002-03", "HomeTeam": "B", "AwayTeam": "D", "FTR": "A", "FTHG": 0, "FTAG": 2},
    ]
    df = pd.DataFrame(records)
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def test_calibration_training_only_synthetic():
    """Criterio: alterare partite non di training posteriori non cambia il terno stimato."""
    df_orig = _create_synthetic_multiseason_data()
    fit_through = "2000-01"
    training_seasons = ["2000-01"]

    res_orig = calibrate_single_fit(df_orig, fit_through, training_seasons)

    # Alterazione dei risultati delle stagioni posteriori 2001-02 e 2002-03
    df_alt = df_orig.copy()
    mask_posterior = df_alt["season"] > fit_through
    for idx in df_alt[mask_posterior].index:
        df_alt.at[idx, "FTR"] = "A" if df_alt.at[idx, "FTR"] == "H" else "H"
        df_alt.at[idx, "FTHG"] = 5
        df_alt.at[idx, "FTAG"] = 4

    res_alt = calibrate_single_fit(df_alt, fit_through, training_seasons)

    assert math.isclose(res_orig.k, res_alt.k, rel_tol=1e-12, abs_tol=1e-12)
    assert math.isclose(res_orig.h, res_alt.h, rel_tol=1e-12, abs_tol=1e-12)
    assert math.isclose(res_orig.nu, res_alt.nu, rel_tol=1e-12, abs_tol=1e-12)
    assert math.isclose(res_orig.c, res_alt.c, rel_tol=1e-12, abs_tol=1e-12)
    assert math.isclose(res_orig.log_loss_train, res_alt.log_loss_train, rel_tol=1e-12, abs_tol=1e-12)


def test_calibration_objective_matches_count_real_data():
    """Criterio: l'obiettivo di ogni fit è una media esattamente sulle partite di training (380, 760, 1140)."""
    if not _has_real_data():
        pytest.skip("Dati reali non presenti in data/raw/E0/")

    cfg = read_split_config()
    df_hist = load_by_role("history")
    df_train = load_by_role("training")
    df = pd.concat([df_hist, df_train], ignore_index=True)
    df = df.sort_values("Date", kind="stable").reset_index(drop=True)

    schedule = derive_fit_schedule(cfg)

    expected_counts = {
        "2000-01": 380,
        "2010-11": 760,
        "2020-21": 1140,
    }

    for fit_through, expected_n in expected_counts.items():
        train_seasons = schedule[fit_through]["training"]
        j_year = parse_season_start_year(fit_through)
        df_sub = df[df["season"].map(parse_season_start_year) <= j_year]
        df_gt = df_sub[df_sub["season"].isin(train_seasons)]
        assert len(df_gt) == expected_n


def test_csv_validation_leakage_and_uniqueness():
    """Criterio: nessuna riga di validazione usa fit posteriore/uguale e ogni stagione di validazione compare una volta."""
    if not CSV_PATH.exists():
        pytest.skip(f"CSV versionato non trovato: {CSV_PATH}")

    df_csv = pd.read_csv(CSV_PATH)
    val_rows = df_csv[df_csv["role"] == "validation"].copy()

    # Verifica assenza leakage: season > fit_through per tutte le righe di validazione
    for _, row in val_rows.iterrows():
        season_year = parse_season_start_year(row["season"])
        fit_year = parse_season_start_year(row["fit_through"])
        assert season_year > fit_year, f"Leakage detected: season {row['season']} <= fit {row['fit_through']}"

    # Conteggio per stagione di validazione: ciascuna deve avere esattamente 380 righe
    season_counts = val_rows["season"].value_counts()
    assert len(season_counts) == 19
    for season, count in season_counts.items():
        assert count == 380, f"Stagione {season} ha {count} righe di validazione, attese 380"

    # Nessuna stagione di validazione compare in più di un fit
    for season, group in val_rows.groupby("season"):
        unique_fits = group["fit_through"].unique()
        assert len(unique_fits) == 1, f"Stagione {season} prevista da più fit: {unique_fits}"


def test_versioned_csv_schema_and_probabilities():
    """Criterio: colonne nell'ordine dichiarato, conteggi per fit e ruolo, somma a 1."""
    if not CSV_PATH.exists():
        pytest.skip(f"CSV versionato non trovato: {CSV_PATH}")

    with open(CSV_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == WALKFORWARD_CSV_COLUMNS

    df_csv = pd.read_csv(CSV_PATH)

    # Conteggio totale
    assert len(df_csv) == 9500

    # Conteggi per fit e ruolo
    counts = df_csv.groupby(["fit_through", "role"]).size().to_dict()
    assert counts[("2000-01", "training")] == 380
    assert counts[("2000-01", "validation")] == 3040
    assert counts[("2010-11", "training")] == 760
    assert counts[("2010-11", "validation")] == 3420
    assert counts[("2020-21", "training")] == 1140
    assert counts[("2020-21", "validation")] == 760

    # Somma delle probabilità a 1 entro 1e-12 e limiti (0, 1)
    prob_sums = df_csv["p_home"] + df_csv["p_draw"] + df_csv["p_away"]
    assert np.all(np.abs(prob_sums - 1.0) <= 1e-12)
    assert np.all((df_csv["p_home"] > 0.0) & (df_csv["p_home"] < 1.0))
    assert np.all((df_csv["p_draw"] > 0.0) & (df_csv["p_draw"] < 1.0))
    assert np.all((df_csv["p_away"] > 0.0) & (df_csv["p_away"] < 1.0))

    # Formato date e valori categorici
    assert df_csv["date"].str.match(r"^\d{4}-\d{2}-\d{2}$").all()
    assert set(df_csv["ftr"].unique()).issubset({"H", "D", "A"})
    assert set(df_csv["home_promotion"].fillna("").unique()).issubset({"", "returning", "new"})
    assert set(df_csv["away_promotion"].fillna("").unique()).issubset({"", "returning", "new"})


def test_recomputed_predictions_match_csv():
    """Criterio: il ricalcolo dai dati coincide con il CSV versionato entro 1e-12."""
    if not _has_real_data():
        pytest.skip("Dati reali non presenti in data/raw/E0/")
    if not CSV_PATH.exists():
        pytest.skip(f"CSV versionato non trovato: {CSV_PATH}")

    df_csv = pd.read_csv(CSV_PATH)
    cfg = read_split_config()
    df_hist = load_by_role("history")
    df_train = load_by_role("training")
    df_val = load_by_role("validation")

    df = pd.concat([df_hist, df_train, df_val], ignore_index=True)
    df = df.sort_values("Date", kind="stable").reset_index(drop=True)

    schedule = derive_fit_schedule(cfg)
    ordered_fits = sorted(schedule.keys(), key=parse_season_start_year)

    recomputed_rows = []
    for fit_through in ordered_fits:
        params = ELO_FITS[fit_through]
        train_seasons = schedule[fit_through]["training"]
        val_seasons = schedule[fit_through]["validation"]
        target_seasons = train_seasons + val_seasons

        preds = predict_elo_fast(df, target_seasons, k=params.k, h=params.h, nu=params.nu)

        for role, role_seasons in (("training", train_seasons), ("validation", val_seasons)):
            sub_preds = preds[preds["season"].isin(role_seasons)].copy().reset_index(drop=True)
            sub_gt = df[df["season"].isin(role_seasons)].copy().reset_index(drop=True)

            for i in range(len(sub_preds)):
                p = sub_preds.iloc[i]
                g = sub_gt.iloc[i]
                recomputed_rows.append({
                    "fit_through": fit_through,
                    "role": role,
                    "season": p["season"],
                    "date": pd.Timestamp(p["Date"]).strftime("%Y-%m-%d"),
                    "home_team": p["HomeTeam"],
                    "away_team": p["AwayTeam"],
                    "ftr": g["FTR"],
                    "home_promotion": p["home_promotion"],
                    "away_promotion": p["away_promotion"],
                    "rating_home": float(p["rating_home"]),
                    "rating_away": float(p["rating_away"]),
                    "delta": float(p["delta"]),
                    "p_home": float(p["p_home"]),
                    "p_draw": float(p["p_draw"]),
                    "p_away": float(p["p_away"]),
                })

    df_recomputed = pd.DataFrame(recomputed_rows)
    assert len(df_recomputed) == len(df_csv)

    # Confronto esatto su stringhe
    for col in ("fit_through", "role", "season", "date", "home_team", "away_team", "ftr"):
        assert df_recomputed[col].equals(df_csv[col]), f"Mismatch in string column '{col}'"

    for col in ("home_promotion", "away_promotion"):
        assert df_recomputed[col].fillna("").equals(df_csv[col].fillna("")), f"Mismatch in column '{col}'"

    # Confronto numerico entro 1e-12
    for col in ("rating_home", "rating_away", "delta", "p_home", "p_draw", "p_away"):
        diff = np.abs(df_recomputed[col].to_numpy() - df_csv[col].to_numpy())
        max_diff = float(np.max(diff))
        assert max_diff <= 1e-12, f"Numeric mismatch in '{col}': max_diff = {max_diff}"


@pytest.mark.slow
def test_elo_fits_matches_data_recalibration():
    """Criterio: ELO_FITS coincide con la ricalibrazione dai dati entro rel_tol 1e-9 (marcato slow)."""
    if not _has_real_data():
        pytest.skip("Dati reali non presenti in data/raw/E0/")

    cfg = read_split_config()
    df_hist = load_by_role("history")
    df_train = load_by_role("training")
    df_val = load_by_role("validation")

    df = pd.concat([df_hist, df_train, df_val], ignore_index=True)
    df = df.sort_values("Date", kind="stable").reset_index(drop=True)

    schedule = derive_fit_schedule(cfg)

    for fit_through, params in ELO_FITS.items():
        res = calibrate_single_fit(df, fit_through, schedule[fit_through]["training"])
        assert res.success is True
        assert math.isclose(res.k, params.k, rel_tol=1e-9)
        assert math.isclose(res.h, params.h, rel_tol=1e-9)
        assert math.isclose(res.nu, params.nu, rel_tol=1e-9)
        assert math.isclose(res.c, params.c, rel_tol=1e-9)


def test_elo_fit_validations():
    """Test unitari di validazione per le funzioni del modulo elo_fit."""
    with pytest.raises(TypeError, match="Season must be a str"):
        parse_season_start_year(1999)

    with pytest.raises(ValueError, match="Invalid season format"):
        parse_season_start_year("2000/01")

    with pytest.raises(ValueError, match="Season year continuity mismatch"):
        parse_season_start_year("2000-02")

    with pytest.raises(TypeError, match="validation must be provided"):
        derive_fit_schedule(["2000-01"])

    # Verifica errore allineamento chiavi in compute_training_log_loss
    df_sub = pd.DataFrame([
        {"Date": pd.Timestamp("2000-08-15"), "season": "2000-01", "HomeTeam": "A", "AwayTeam": "B", "FTR": "H", "FTHG": 2, "FTAG": 0},
    ])
    df_mismatched_gt = pd.DataFrame([
        {"Date": pd.Timestamp("2000-08-15"), "season": "2000-01", "HomeTeam": "A", "AwayTeam": "C", "FTR": "H", "FTHG": 2, "FTAG": 0},
    ])
    with pytest.raises(ValueError, match="Key mismatch"):
        compute_training_log_loss(df_sub, ["2000-01"], 20.0, 50.0, 1.0, df_mismatched_gt)
