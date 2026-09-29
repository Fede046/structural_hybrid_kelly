"""Test unitari e criteri di accettazione per il previsore Elo walk-forward (Task 21)."""

from collections.abc import Collection
from pathlib import Path
from typing import Any, Callable, Final
import numpy as np
import pandas as pd
import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.data.split import load_by_role
from shk.model.elo_predictor import (
    _EloTracker,
    compute_season_standings,
    diagnose_season_transitions,
    predict_elo_fast,
    predict_elo_walkforward,
)

# Parametri convenzionali di test (non stimati / non del modello)
TEST_K: Final[float] = 20.0
TEST_H: Final[float] = 60.0
TEST_NU: Final[float] = 1.0
TEST_S: Final[float] = 400.0
TEST_INITIAL_RATING: Final[float] = 1500.0


def _has_real_data() -> bool:
    """Verifica se i dati grezzi sono presenti sul filesystem."""
    return DEFAULT_DATA_DIR.exists() and len(list(DEFAULT_DATA_DIR.glob("*.csv"))) > 0


def _create_synthetic_dataset() -> pd.DataFrame:
    """Crea un dataset sintetico a 3 stagioni consecutive con partite contemporanee, nuove e tornanti."""
    # Stagione 1: 2000-01 (4 squadre: A, B, C, D)
    # Date con più partite nello stesso giorno
    d1 = [
        {"Date": pd.Timestamp("2000-08-15"), "season": "2000-01", "HomeTeam": "A", "AwayTeam": "B", "FTR": "H", "FTHG": 2, "FTAG": 0, "B365H": 1.8, "B365D": 3.4, "B365A": 4.5},
        {"Date": pd.Timestamp("2000-08-15"), "season": "2000-01", "HomeTeam": "C", "AwayTeam": "D", "FTR": "A", "FTHG": 0, "FTAG": 1, "B365H": 2.5, "B365D": 3.2, "B365A": 2.8},
        {"Date": pd.Timestamp("2000-08-22"), "season": "2000-01", "HomeTeam": "A", "AwayTeam": "C", "FTR": "H", "FTHG": 3, "FTAG": 0, "B365H": 1.5, "B365D": 4.0, "B365A": 6.5},
        {"Date": pd.Timestamp("2000-08-22"), "season": "2000-01", "HomeTeam": "B", "AwayTeam": "D", "FTR": "D", "FTHG": 1, "FTAG": 1, "B365H": 2.2, "B365D": 3.1, "B365A": 3.3},
        {"Date": pd.Timestamp("2000-08-29"), "season": "2000-01", "HomeTeam": "A", "AwayTeam": "D", "FTR": "H", "FTHG": 1, "FTAG": 0, "B365H": 1.6, "B365D": 3.6, "B365A": 5.0},
        {"Date": pd.Timestamp("2000-08-29"), "season": "2000-01", "HomeTeam": "B", "AwayTeam": "C", "FTR": "D", "FTHG": 2, "FTAG": 2, "B365H": 2.1, "B365D": 3.2, "B365A": 3.5},
    ]

    # Stagione 2: 2001-02 (A, D rimangono; B, C escono; E, F nuove promosse)
    d2 = [
        {"Date": pd.Timestamp("2001-08-18"), "season": "2001-02", "HomeTeam": "A", "AwayTeam": "E", "FTR": "H", "FTHG": 2, "FTAG": 1, "B365H": 1.7, "B365D": 3.5, "B365A": 4.8},
        {"Date": pd.Timestamp("2001-08-18"), "season": "2001-02", "HomeTeam": "D", "AwayTeam": "F", "FTR": "A", "FTHG": 0, "FTAG": 2, "B365H": 2.3, "B365D": 3.2, "B365A": 3.0},
        {"Date": pd.Timestamp("2001-08-25"), "season": "2001-02", "HomeTeam": "E", "AwayTeam": "F", "FTR": "D", "FTHG": 1, "FTAG": 1, "B365H": 2.6, "B365D": 3.1, "B365A": 2.7},
        {"Date": pd.Timestamp("2001-08-25"), "season": "2001-02", "HomeTeam": "A", "AwayTeam": "D", "FTR": "H", "FTHG": 3, "FTAG": 1, "B365H": 1.5, "B365D": 3.8, "B365A": 6.0},
    ]

    # Stagione 3: 2002-03 (A, E rimangono; B ritorna [returning]; G nuova promossa [new])
    d3 = [
        {"Date": pd.Timestamp("2002-08-17"), "season": "2002-03", "HomeTeam": "A", "AwayTeam": "B", "FTR": "D", "FTHG": 1, "FTAG": 1, "B365H": 1.9, "B365D": 3.3, "B365A": 4.0},
        {"Date": pd.Timestamp("2002-08-17"), "season": "2002-03", "HomeTeam": "E", "AwayTeam": "G", "FTR": "H", "FTHG": 2, "FTAG": 0, "B365H": 2.0, "B365D": 3.2, "B365A": 3.7},
        {"Date": pd.Timestamp("2002-08-24"), "season": "2002-03", "HomeTeam": "B", "AwayTeam": "G", "FTR": "H", "FTHG": 3, "FTAG": 1, "B365H": 1.8, "B365D": 3.4, "B365A": 4.2},
        {"Date": pd.Timestamp("2002-08-24"), "season": "2002-03", "HomeTeam": "A", "AwayTeam": "E", "FTR": "H", "FTHG": 2, "FTAG": 1, "B365H": 1.6, "B365D": 3.7, "B365A": 5.5},
    ]

    df = pd.DataFrame(d1 + d2 + d3)
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def predict_elo_mutant_update_before_predict(
    df: pd.DataFrame,
    seasons_to_predict: Collection[str],
    k: float,
    h: float,
    nu: float,
    s: float = 400.0,
    initial_rating: float = 1500.0,
) -> pd.DataFrame:
    """Mutante che aggiorna i rating con la partita prima di prevederla (leakage)."""
    target_seasons = set(seasons_to_predict)
    tracker = _EloTracker(k=k, h=h, nu=nu, s=s, initial_rating=initial_rating)
    predictions = []

    for _, group in df.groupby("Date", sort=False):
        records = [row._asdict() for row in group.itertuples(index=False)]
        for rec in records:
            # ERRORE DELIBERATO: aggiorna con l'esito prima di prevedere la partita
            tracker.consume_match(rec)
            if rec["season"] in target_seasons:
                predictions.append(tracker.predict_match(rec))

    return pd.DataFrame(predictions)


def verify_future_invariance(
    predict_fn: Callable[..., pd.DataFrame],
    df: pd.DataFrame,
    seasons_to_predict: Collection[str],
    cut_off_dates: list[pd.Timestamp],
) -> bool:
    """Verifica se predict_fn rispetta l'invarianza al futuro per tutte le date di taglio."""
    preds_orig = predict_fn(
        df,
        seasons_to_predict,
        k=TEST_K,
        h=TEST_H,
        nu=TEST_NU,
        s=TEST_S,
        initial_rating=TEST_INITIAL_RATING,
    )

    for d in cut_off_dates:
        # Alterazione coerente per Date >= d
        df_pert = df.copy()
        mask_future = df_pert["Date"] >= d

        for idx in df_pert[mask_future].index:
            ftr = df_pert.at[idx, "FTR"]
            fthg = df_pert.at[idx, "FTHG"]
            ftag = df_pert.at[idx, "FTAG"]

            if ftr == "H":
                df_pert.at[idx, "FTR"] = "A"
                df_pert.at[idx, "FTHG"] = ftag
                df_pert.at[idx, "FTAG"] = fthg if fthg > ftag else ftag + 1
            elif ftr == "A":
                df_pert.at[idx, "FTR"] = "H"
                df_pert.at[idx, "FTHG"] = ftag if ftag > fthg else fthg + 1
                df_pert.at[idx, "FTAG"] = fthg
            else:  # 'D'
                df_pert.at[idx, "FTR"] = "H"
                df_pert.at[idx, "FTHG"] = ftag + 1

        preds_pert = predict_fn(
            df_pert,
            seasons_to_predict,
            k=TEST_K,
            h=TEST_H,
            nu=TEST_NU,
            s=TEST_S,
            initial_rating=TEST_INITIAL_RATING,
        )

        sub_orig = preds_orig[preds_orig["Date"] <= d].reset_index(drop=True)
        sub_pert = preds_pert[preds_pert["Date"] <= d].reset_index(drop=True)

        if not sub_orig.equals(sub_pert):
            return False

    return True


# ==============================================================================
# 1. Invarianza al futuro e test del mutante
# ==============================================================================


def test_future_invariance_and_mutant():
    """Criterio Invarianza al futuro: fornitore e percorso veloce invarianti, mutante rilevato."""
    df = _create_synthetic_dataset()
    seasons = ["2001-02", "2002-03"]
    # Include il primo giorno di una stagione successiva alla prima (2001-08-18) e date intermedie
    cut_off_dates = [
        pd.Timestamp("2001-08-18"),
        pd.Timestamp("2001-08-25"),
        pd.Timestamp("2002-08-17"),
    ]

    # 1. Percorso via fornitore: invariante
    assert verify_future_invariance(predict_elo_walkforward, df, seasons, cut_off_dates)

    # 2. Percorso veloce: invariante
    assert verify_future_invariance(predict_elo_fast, df, seasons, cut_off_dates)

    # 3. Mutante: la violazione viene rilevata
    assert not verify_future_invariance(
        predict_elo_mutant_update_before_predict, df, seasons, cut_off_dates
    )


# ==============================================================================
# 2. Invarianza alle quote
# ==============================================================================


def test_odds_invariance():
    """Criterio Invarianza quote: alterare o rimuovere le quote non modifica le previsioni."""
    df = _create_synthetic_dataset()
    seasons = ["2001-02", "2002-03"]

    pred_baseline = predict_elo_fast(
        df, seasons, k=TEST_K, h=TEST_H, nu=TEST_NU, s=TEST_S
    )

    # Rimuovi tutte le quote
    odds_cols = [c for c in df.columns if c.startswith("B365")]
    df_no_odds = df.drop(columns=odds_cols)
    pred_no_odds = predict_elo_fast(
        df_no_odds, seasons, k=TEST_K, h=TEST_H, nu=TEST_NU, s=TEST_S
    )
    assert pred_baseline.equals(pred_no_odds)

    # Altera le quote
    df_altered = df.copy()
    for col in odds_cols:
        df_altered[col] = df_altered[col] * 2.5 + 1.0
    pred_altered = predict_elo_fast(
        df_altered, seasons, k=TEST_K, h=TEST_H, nu=TEST_NU, s=TEST_S
    )
    assert pred_baseline.equals(pred_altered)


# ==============================================================================
# 3. Regola delle neopromosse e calcoli a mano
# ==============================================================================


def test_promotion_rules_hand_calculated():
    """Criterio Regola neopromosse: verifica esatta conservazione, returning, new e parità."""
    df = _create_synthetic_dataset()
    seasons = ["2000-01", "2001-02", "2002-03"]

    preds = predict_elo_fast(
        df,
        seasons,
        k=TEST_K,
        h=TEST_H,
        nu=TEST_NU,
        s=TEST_S,
        initial_rating=TEST_INITIAL_RATING,
    )

    # 1. Prima stagione (2000-01): tutte partono da 1500.0 con stato ""
    s1_preds = preds[preds["season"] == "2000-01"]
    first_row = s1_preds.iloc[0]
    assert first_row["rating_home"] == 1500.0
    assert first_row["rating_away"] == 1500.0
    assert first_row["home_promotion"] == ""
    assert first_row["away_promotion"] == ""

    # Verifica classifica stagione 2000-01 calcolata da compute_season_standings
    s1_matches = df[df["season"] == "2000-01"]
    standings_s1 = compute_season_standings(s1_matches)
    # A: 3 V -> 9 pt
    # D: 1 V, 1 N, 1 P -> 4 pt
    # B: 2 N, 1 P -> 2 pt (GF: 3, GS: 5, DR: -2)
    # C: 2 N, 1 P -> 1 pt? (0-1 vs D, 0-3 vs A, 2-2 vs B -> 1 N, 2 P -> 1 pt)
    expected_order = ["A", "D", "B", "C"]
    assert standings_s1["team"].tolist() == expected_order

    # Ultime tre squadre di s1: D, B, C
    # In s2 (2001-02): E e F sono "new". Devono ricevere media dei rating finali di D, B, C.
    s2_preds = preds[preds["season"] == "2001-02"]
    # Team E gioca la prima partita in s2 alla riga 0
    row_s2_0 = s2_preds.iloc[0]
    assert row_s2_0["HomeTeam"] == "A"
    assert row_s2_0["AwayTeam"] == "E"
    assert row_s2_0["home_promotion"] == ""  # A è rimasta
    assert row_s2_0["away_promotion"] == "new"  # E è nuova

    row_s2_1 = s2_preds.iloc[1]
    assert row_s2_1["HomeTeam"] == "D"
    assert row_s2_1["AwayTeam"] == "F"
    assert row_s2_1["home_promotion"] == ""  # D è rimasta
    assert row_s2_1["away_promotion"] == "new"  # F è nuova

    # In s3 (2002-03): B ritorna ("returning") e deve riprendere il rating di fine s1
    s3_preds = preds[preds["season"] == "2002-03"]
    row_s3_0 = s3_preds.iloc[0]
    assert row_s3_0["HomeTeam"] == "A"
    assert row_s3_0["AwayTeam"] == "B"
    assert row_s3_0["home_promotion"] == ""
    assert row_s3_0["away_promotion"] == "returning"

    row_s3_1 = s3_preds.iloc[1]
    assert row_s3_1["HomeTeam"] == "E"
    assert row_s3_1["AwayTeam"] == "G"
    assert row_s3_1["home_promotion"] == ""  # E è rimasta da s2
    assert row_s3_1["away_promotion"] == "new"  # G è nuova debuttante


# ==============================================================================
# 4. Equivalenza percorso via fornitore vs percorso veloce
# ==============================================================================


def test_fast_vs_provider_path_synthetic():
    """Criterio Equivalenza: percorso fornitore e veloce coincidono entro 1e-12 su dati sintetici."""
    df = _create_synthetic_dataset()
    seasons = ["2001-02", "2002-03"]

    pred_fast = predict_elo_fast(
        df, seasons, k=TEST_K, h=TEST_H, nu=TEST_NU, s=TEST_S
    )
    pred_wf = predict_elo_walkforward(
        df, seasons, k=TEST_K, h=TEST_H, nu=TEST_NU, s=TEST_S
    )

    assert len(pred_fast) == len(pred_wf)
    float_cols = ["rating_home", "rating_away", "delta", "p_home", "p_draw", "p_away"]
    for col in float_cols:
        diff = np.abs(pred_fast[col].to_numpy() - pred_wf[col].to_numpy())
        assert np.max(diff) <= 1e-12, f"Discrepancy on column {col}"

    str_cols = ["season", "HomeTeam", "AwayTeam", "home_promotion", "away_promotion"]
    for col in str_cols:
        assert (pred_fast[col] == pred_wf[col]).all()

    assert (pred_fast["Date"] == pred_wf["Date"]).all()


@pytest.mark.skipif(not _has_real_data(), reason="Raw CSV data not available in data/raw/E0/")
def test_fast_vs_provider_path_real_data():
    """Criterio Equivalenza su dati reali: concordanza entro 1e-12 su training e validation."""
    df_h = load_by_role("history")
    df_t = load_by_role("training")
    df_v = load_by_role("validation")

    df_full = (
        pd.concat([df_h, df_t, df_v], ignore_index=True)
        .sort_values(by="Date", kind="stable")
        .reset_index(drop=True)
    )

    seasons_to_predict = sorted(
        set(df_t["season"].unique()).union(set(df_v["season"].unique())),
        key=lambda s: int(s[:4]),
    )

    pred_fast = predict_elo_fast(
        df_full, seasons_to_predict, k=TEST_K, h=TEST_H, nu=TEST_NU, s=TEST_S
    )
    pred_wf = predict_elo_walkforward(
        df_full, seasons_to_predict, k=TEST_K, h=TEST_H, nu=TEST_NU, s=TEST_S
    )

    assert len(pred_fast) == len(pred_wf)
    float_cols = ["rating_home", "rating_away", "delta", "p_home", "p_draw", "p_away"]
    for col in float_cols:
        diff = np.abs(pred_fast[col].to_numpy() - pred_wf[col].to_numpy())
        assert np.max(diff) <= 1e-12, f"Discrepancy on real data column {col}"

    str_cols = ["season", "HomeTeam", "AwayTeam", "home_promotion", "away_promotion"]
    for col in str_cols:
        assert (pred_fast[col] == pred_wf[col]).all()


# ==============================================================================
# 5. Transizioni di stagione sui dati reali
# ==============================================================================


@pytest.mark.skipif(not _has_real_data(), reason="Raw CSV data not available in data/raw/E0/")
def test_real_data_season_transitions():
    """Criterio Transizioni reali: 22 squadre in 93-95, poi 20; 2 in e 4 out nel 95, 3 e 3 nelle altre."""
    df_h = load_by_role("history")
    df_t = load_by_role("training")
    df_v = load_by_role("validation")

    df_full = (
        pd.concat([df_h, df_t, df_v], ignore_index=True)
        .sort_values(by="Date", kind="stable")
        .reset_index(drop=True)
    )

    diag = diagnose_season_transitions(df_full)

    # 29 transizioni da 1993-94 a 2022-23
    assert len(diag) == 29

    for _, row in diag.iterrows():
        s = row["season"]
        n_teams = row["n_teams"]
        n_prom = row["promoted_total"]
        n_rel = row["n_relegated_actual"]

        # Verifica conteggio squadre
        if s == "1994-95":
            assert n_teams == 22
        else:
            assert n_teams == 20, f"Expected 20 teams in {s}, got {n_teams}"

        # Verifica entrate e uscite
        if s == "1995-96":
            assert n_prom == 2, f"Expected 2 promoted in {s}, got {n_prom} ({row['promoted_new']}, {row['promoted_returning']})"
            assert n_rel == 4, f"Expected 4 relegated in {s}, got {n_rel} ({row['relegated_actual']})"
        else:
            assert n_prom == 3, f"Expected 3 promoted in {s}, got {n_prom} ({row['promoted_new']}, {row['promoted_returning']})"
            assert n_rel == 3, f"Expected 3 relegated in {s}, got {n_rel} ({row['relegated_actual']})"


# ==============================================================================
# 6. Validazioni
# ==============================================================================


def test_elo_predictor_validations():
    """Verifica tutte le validazioni di tipo e valore per il previsore."""
    df = _create_synthetic_dataset()

    # 1. df non DataFrame
    with pytest.raises(TypeError):
        predict_elo_fast("not_df", ["2001-02"], k=20, h=60, nu=1.0)

    # 2. Colonne mancanti
    for col in ["Date", "season", "HomeTeam", "AwayTeam", "FTR", "FTHG", "FTAG"]:
        df_bad = df.drop(columns=[col])
        with pytest.raises(ValueError):
            predict_elo_fast(df_bad, ["2001-02"], k=20, h=60, nu=1.0)

    # 3. Date non ordinate
    df_unsorted = df.copy()
    df_unsorted.iloc[0, df.columns.get_loc("Date")] = pd.Timestamp("2005-01-01")
    with pytest.raises(ValueError):
        predict_elo_fast(df_unsorted, ["2001-02"], k=20, h=60, nu=1.0)

    # 4. Stagioni non consecutive
    df_gap = df.copy()
    df_gap["season"] = df_gap["season"].replace({"2002-03": "2004-05"})
    with pytest.raises(ValueError):
        predict_elo_fast(df_gap, ["2001-02"], k=20, h=60, nu=1.0)

    # 5. Stagione decrescente lungo Date
    df_rev = df.copy()
    df_rev.iloc[-1, df.columns.get_loc("season")] = "2000-01"
    with pytest.raises(ValueError):
        predict_elo_fast(df_rev, ["2001-02"], k=20, h=60, nu=1.0)

    # 6. seasons_to_predict non valida
    with pytest.raises(TypeError):
        predict_elo_fast(df, "2001-02", k=20, h=60, nu=1.0)  # str anziché Collection
    with pytest.raises(TypeError):
        predict_elo_fast(df, [123], k=20, h=60, nu=1.0)  # non-str
    with pytest.raises(ValueError):
        predict_elo_fast(df, [], k=20, h=60, nu=1.0)  # vuota
    with pytest.raises(ValueError):
        predict_elo_fast(df, ["1999-00"], k=20, h=60, nu=1.0)  # stagione assente

    # 7. FTR non valido
    df_bad_ftr = df.copy()
    df_bad_ftr.iloc[0, df.columns.get_loc("FTR")] = "X"
    with pytest.raises(ValueError):
        predict_elo_fast(df_bad_ftr, ["2001-02"], k=20, h=60, nu=1.0)

    # 8. Parametri numerici non validi
    with pytest.raises(ValueError):
        predict_elo_fast(df, ["2001-02"], k=-1.0, h=60, nu=1.0)
    with pytest.raises(ValueError):
        predict_elo_fast(df, ["2001-02"], k=20, h=60, nu=0.0)
    with pytest.raises(ValueError):
        predict_elo_fast(df, ["2001-02"], k=20, h=60, nu=1.0, s=-10)
    with pytest.raises(TypeError):
        predict_elo_fast(df, ["2001-02"], k="20", h=60, nu=1.0)


# ==============================================================================
# 7. Determinismo
# ==============================================================================


def test_predictions_deterministic():
    """Criterio Determinismo: due esecuzioni producono output identici."""
    df = _create_synthetic_dataset()
    seasons = ["2001-02", "2002-03"]

    pred1 = predict_elo_fast(df, seasons, k=TEST_K, h=TEST_H, nu=TEST_NU, s=TEST_S)
    pred2 = predict_elo_fast(df, seasons, k=TEST_K, h=TEST_H, nu=TEST_NU, s=TEST_S)
    assert pred1.equals(pred2)
