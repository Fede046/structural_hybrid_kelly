"""Test per il fornitore walk-forward e controlli anti-leakage (US-C3.4)."""

from collections.abc import Iterator
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.data.split import load_by_role, read_split_config
from shk.data.walkforward import (
    LeakageError,
    assert_no_leakage,
    check_leakage,
    get_prematch_whitelist,
    walkforward_split,
)

# Elenco dei campi esplicitamente vietati nella whitelist della partita
FORBIDDEN_FIELDS_TO_CHECK: tuple[str, ...] = (
    # Risultati finali e parziali
    "FTHG",
    "FTAG",
    "FTR",
    "HTHG",
    "HTAG",
    "HTR",
    # Arbitro e statistiche
    "Referee",
    "HS",
    "AS",
    "HST",
    "AST",
    "HF",
    "AF",
    "HC",
    "AC",
    "HY",
    "AY",
    "HR",
    "AR",
    # Quote e linee di chiusura (closing)
    "PSCH",
    "PSCD",
    "PSCA",
    "B365CH",
    "B365CD",
    "B365CA",
    "MaxCH",
    "AvgCH",
    "B365CAHH",
    "PC>2.5",
    "AHCh",
    # Linee di handicap e conteggi
    "AHh",
    "BbAHh",
    "B365AH",
    "Bb1X2",
    "BbOU",
    "BbAH",
)


# =============================================================================
# Fornitori Mutanti (ciascuno con un solo difetto deliberato)
# =============================================================================


def mutant_1_side_right(
    df: pd.DataFrame,
    seasons_to_predict: list[str],
) -> Iterator[tuple[pd.DataFrame, pd.Series]]:
    """Mutante 1: usa side='right' invece di side='left' in searchsorted."""
    target_seasons = set(seasons_to_predict)
    whitelist_cols = list(get_prematch_whitelist(df.columns))
    df_whitelist = df[whitelist_cols]
    dates = df["Date"].to_numpy()

    for idx in range(len(df)):
        season_val = df["season"].iloc[idx]
        if season_val not in target_seasons:
            continue

        match_date = dates[idx]
        # DIFETTO: side='right' include nella storia le partite della stessa data
        cutoff = int(np.searchsorted(dates, match_date, side="right"))
        history = df.iloc[:cutoff]
        match = df_whitelist.iloc[idx]
        yield history, match


def mutant_2_history_includes_match(
    df: pd.DataFrame,
    seasons_to_predict: list[str],
) -> Iterator[tuple[pd.DataFrame, pd.Series]]:
    """Mutante 2: la storia include esplicitamente la partita corrente stessa."""
    target_seasons = set(seasons_to_predict)
    whitelist_cols = list(get_prematch_whitelist(df.columns))
    df_whitelist = df[whitelist_cols]
    dates = df["Date"].to_numpy()

    for idx in range(len(df)):
        season_val = df["season"].iloc[idx]
        if season_val not in target_seasons:
            continue

        match_date = dates[idx]
        cutoff = int(np.searchsorted(dates, match_date, side="left"))
        # DIFETTO: la riga della partita stessa viene concatenata in coda alla storia
        history = pd.concat([df.iloc[:cutoff], df.iloc[[idx]]], ignore_index=True)
        match = df_whitelist.iloc[idx]
        yield history, match


def mutant_3_match_exposes_forbidden(
    df: pd.DataFrame,
    seasons_to_predict: list[str],
) -> Iterator[tuple[pd.DataFrame, pd.Series]]:
    """Mutante 3: la partita espone l'intera riga senza restrizione alla whitelist."""
    target_seasons = set(seasons_to_predict)
    dates = df["Date"].to_numpy()

    for idx in range(len(df)):
        season_val = df["season"].iloc[idx]
        if season_val not in target_seasons:
            continue

        match_date = dates[idx]
        cutoff = int(np.searchsorted(dates, match_date, side="left"))
        history = df.iloc[:cutoff]
        # DIFETTO: la partita non viene filtrata con la whitelist (espone FTR, FTHG, etc.)
        match = df.iloc[idx]
        yield history, match


# =============================================================================
# Fixture e Helper Sintetici
# =============================================================================


def _make_synthetic_df() -> pd.DataFrame:
    """Costruisce un DataFrame sintetico con stagioni consecutive e date multiple."""
    return pd.DataFrame(
        {
            "Div": ["E0"] * 7,
            "Date": pd.to_datetime(
                [
                    "2021-08-14",  # Match 1 (primo giorno stagione 1)
                    "2021-08-14",  # Match 2 (stesso giorno)
                    "2021-08-14",  # Match 3 (stesso giorno)
                    "2021-08-15",  # Match 4 (giorno successivo)
                    "2021-08-15",  # Match 5 (stesso giorno)
                    "2022-08-13",  # Match 6 (stagione successiva)
                    "2022-08-13",  # Match 7 (stesso giorno)
                ]
            ),
            "Time": ["15:00"] * 7,
            "HomeTeam": ["Arsenal", "Aston Villa", "Everton", "Tottenham", "West Ham", "Crystal Palace", "Fulham"],
            "AwayTeam": ["Chelsea", "Newcastle", "Southampton", "Man City", "Leicester", "Arsenal", "Liverpool"],
            "season": ["2021-22", "2021-22", "2021-22", "2021-22", "2021-22", "2022-23", "2022-23"],
            # Quote pre-partita lecite
            "B365H": [2.50, 1.80, 2.10, 3.20, 2.40, 4.00, 7.50],
            "B365D": [3.40, 3.50, 3.30, 3.40, 3.30, 3.60, 4.80],
            "B365A": [2.90, 4.50, 3.60, 2.25, 3.00, 1.90, 1.40],
            "MaxH": [2.55, 1.85, 2.15, 3.30, 2.45, 4.10, 7.80],
            # Risultati finali e parziali (vietati)
            "FTHG": [0, 2, 3, 1, 4, 0, 2],
            "FTAG": [2, 0, 1, 0, 1, 2, 2],
            "FTR": ["A", "H", "H", "H", "H", "A", "D"],
            "HTHG": [0, 1, 1, 0, 2, 0, 1],
            "HTAG": [1, 0, 0, 0, 0, 1, 0],
            "HTR": ["A", "H", "H", "D", "H", "A", "H"],
            # Arbitro e statistiche (vietati)
            "Referee": ["Oliver", "Taylor", "Dean", "Pawson", "Atkinson", "Tierney", "Madley"],
            "HS": [10, 14, 12, 11, 15, 8, 9],
            "AS": [15, 8, 9, 13, 10, 14, 18],
            # Quote closing (vietate)
            "PSCH": [2.45, 1.82, 2.12, 3.25, 2.38, 4.05, 7.60],
            "MaxCH": [2.50, 1.86, 2.16, 3.35, 2.42, 4.15, 7.90],
            "AvgCH": [2.43, 1.81, 2.11, 3.22, 2.36, 4.01, 7.55],
            "B365CAHH": [1.95, 1.90, 1.92, 1.88, 1.91, 1.89, 1.93],
            "PC>2.5": [1.85, 2.05, 1.90, 1.75, 1.80, 2.10, 1.65],
            "AHCh": [0.0, -0.5, -0.25, 0.25, 0.0, 0.5, 1.25],
            # Linee e conteggi (vietati)
            "AHh": [0.0, -0.5, -0.25, 0.25, 0.0, 0.5, 1.25],
            "BbAHh": [0.0, -0.5, -0.25, 0.25, 0.0, 0.5, 1.25],
            "B365AH": [0.0, -0.5, -0.25, 0.25, 0.0, 0.5, 1.25],
            "Bb1X2": [35, 36, 35, 37, 36, 38, 38],
            "BbOU": [30, 31, 30, 32, 31, 33, 33],
            "BbAH": [25, 26, 25, 27, 26, 28, 28],
        }
    )


# =============================================================================
# Test Unitari di Validazione
# =============================================================================


def test_walkforward_validations() -> None:
    """Verifica le validazioni in ingresso di walkforward_split."""
    df_valid = _make_synthetic_df()

    # df non DataFrame
    with pytest.raises(TypeError, match="df must be a pandas DataFrame"):
        list(walkforward_split("not_a_df", ["2021-22"]))  # type: ignore

    # Mancanza Date
    with pytest.raises(ValueError, match="Missing required columns: Date, season"):
        list(walkforward_split(df_valid.drop(columns=["Date"]), ["2021-22"]))

    # Mancanza season
    with pytest.raises(ValueError, match="Missing required columns: Date, season"):
        list(walkforward_split(df_valid.drop(columns=["season"]), ["2021-22"]))

    # Date non monotonicamente non decrescente
    df_unsorted = df_valid.copy()
    df_unsorted.loc[0, "Date"] = pd.to_datetime("2023-01-01")
    with pytest.raises(ValueError, match="DataFrame must be sorted by Date"):
        list(walkforward_split(df_unsorted, ["2021-22"]))

    # seasons_to_predict di tipo str
    with pytest.raises(TypeError, match="seasons_to_predict must be a non-string Collection"):
        list(walkforward_split(df_valid, "2021-22"))  # type: ignore

    # seasons_to_predict con elementi non str
    with pytest.raises(TypeError, match="All items in seasons_to_predict must be str"):
        list(walkforward_split(df_valid, [2021]))  # type: ignore

    # seasons_to_predict vuoto
    with pytest.raises(ValueError, match="seasons_to_predict cannot be empty"):
        list(walkforward_split(df_valid, []))

    # seasons_to_predict con stagione non presente
    with pytest.raises(ValueError, match="Seasons not found in DataFrame"):
        list(walkforward_split(df_valid, ["2099-00"]))


# =============================================================================
# Test del Fornitore Vero su Dati Sintetici
# =============================================================================


def test_walkforward_split_synthetic_true_provider() -> None:
    """Verifica il comportamento del fornitore vero su dati sintetici controllati."""
    df = _make_synthetic_df()
    pairs = list(walkforward_split(df, ["2021-22", "2022-23"]))

    assert len(pairs) == 7

    # Match 1 (primo giorno della prima stagione): storia vuota
    h0, m0 = pairs[0]
    assert len(h0) == 0
    assert isinstance(h0, pd.DataFrame)
    assert isinstance(m0, pd.Series)

    # Match 2 e 3 (stesso giorno del Match 1): storia ancora vuota
    h1, _ = pairs[1]
    h2, _ = pairs[2]
    assert len(h1) == 0
    assert len(h2) == 0

    # Match 4 e 5 (giorno 2021-08-15): storia contiene esattamente i 3 match del giorno precedente
    h3, _ = pairs[3]
    h4, _ = pairs[4]
    assert len(h3) == 3
    assert len(h4) == 3
    assert set(h3["HomeTeam"]) == {"Arsenal", "Aston Villa", "Everton"}

    # Match 6 e 7 (stagione 2022-08-13): storia contiene tutti i 5 match della stagione precedente
    h5, _ = pairs[5]
    h6, _ = pairs[6]
    assert len(h5) == 5
    assert len(h6) == 5

    # Nessuna coppia produce violazioni con assert_no_leakage
    for history, match in pairs:
        assert_no_leakage(history, match)


# =============================================================================
# Test Funzione check_leakage
# =============================================================================


def test_check_leakage_violations_detection() -> None:
    """Verifica che check_leakage rilevi singolarmente ciascuna violazione."""
    df = _make_synthetic_df()
    whitelist = get_prematch_whitelist(df.columns)

    # Caso pulito: nessuna violazione
    history_clean = df.iloc[:3]
    match_clean = df[list(whitelist)].iloc[3]  # Data 2021-08-15, history ha solo 2021-08-14
    assert check_leakage(history_clean, match_clean) == []

    # Violazione temporale: storia include data uguale o successiva
    history_future = df.iloc[:4]  # Include riga 3 (2021-08-15)
    violations_temp = check_leakage(history_future, match_clean)
    assert any("Temporal leakage" in v for v in violations_temp)

    # Violazione d'identita': la partita stessa e' presente nella storia
    history_with_match = df.iloc[[3]]
    violations_ident = check_leakage(history_with_match, match_clean)
    assert any("Identity leakage" in v for v in violations_ident)

    # Violazione colonne: partita espone un campo vietato (FTR)
    match_with_ftr = df[list(whitelist) + ["FTR"]].iloc[3]
    violations_col = check_leakage(history_clean, match_with_ftr, whitelist=whitelist)
    assert any("Forbidden columns" in v and "FTR" in v for v in violations_col)


# =============================================================================
# Test dei Tre Mutanti (ciascun difetto deliberato solleva LeakageError)
# =============================================================================


def test_mutant_1_detected() -> None:
    """Verifica che il Mutante 1 (side='right', leakage stesso giorno) sia rilevato."""
    df = _make_synthetic_df()
    detected = False

    for history, match in mutant_1_side_right(df, ["2021-22"]):
        try:
            assert_no_leakage(history, match)
        except LeakageError:
            detected = True
            break

    assert detected, "Mutante 1 non rilevato: LeakageError non sollevato."


def test_mutant_2_detected() -> None:
    """Verifica che il Mutante 2 (storia include la partita stessa) sia rilevato."""
    df = _make_synthetic_df()
    detected = False

    for history, match in mutant_2_history_includes_match(df, ["2021-22"]):
        try:
            assert_no_leakage(history, match)
        except LeakageError:
            detected = True
            break

    assert detected, "Mutante 2 non rilevato: LeakageError non sollevato."


def test_mutant_3_detected() -> None:
    """Verifica che il Mutante 3 (partita espone campi vietati) sia rilevato."""
    df = _make_synthetic_df()
    detected = False

    for history, match in mutant_3_match_exposes_forbidden(df, ["2021-22"]):
        try:
            assert_no_leakage(history, match)
        except LeakageError:
            detected = True
            break

    assert detected, "Mutante 3 non rilevato: LeakageError non sollevato."


# =============================================================================
# Test sui Campi Vietati
# =============================================================================


def test_forbidden_fields_synthetic() -> None:
    """Verifica che nessun campo vietato compaia nella whitelist su dati sintetici."""
    df = _make_synthetic_df()
    whitelist = set(get_prematch_whitelist(df.columns))

    for field in FORBIDDEN_FIELDS_TO_CHECK:
        assert field not in whitelist, f"Campo vietato '{field}' presente nella whitelist."

    # Verifica che i campi lecite siano invece presenti
    allowed_expected = {"Div", "Date", "Time", "HomeTeam", "AwayTeam", "season", "B365H", "B365D", "B365A", "MaxH"}
    assert allowed_expected.issubset(whitelist)


def test_forbidden_fields_real_data() -> None:
    """Verifica che nessun campo vietato compaia nella whitelist sulle colonne reali."""
    if not (DEFAULT_DATA_DIR.is_dir() and list(DEFAULT_DATA_DIR.glob("*.csv"))):
        pytest.skip("Directory data/raw/E0/ non presente o priva di file CSV.")

    df_hist = load_by_role("history")
    df_train = load_by_role("training")
    df_val = load_by_role("validation")

    all_real_columns = set(df_hist.columns) | set(df_train.columns) | set(df_val.columns)
    real_whitelist = set(get_prematch_whitelist(all_real_columns))

    for field in FORBIDDEN_FIELDS_TO_CHECK:
        assert field not in real_whitelist, (
            f"Campo vietato '{field}' compare nella whitelist reale."
        )


# =============================================================================
# Test sui Dati Reali (senza marker slow)
# =============================================================================


def test_walkforward_real_data_no_leakage() -> None:
    """Verifica l'assenza totale di leakage sulle stagioni reali di training e validation."""
    if not (DEFAULT_DATA_DIR.is_dir() and list(DEFAULT_DATA_DIR.glob("*.csv"))):
        pytest.skip("Directory data/raw/E0/ non presente o priva di file CSV.")

    df_hist = load_by_role("history")
    df_train = load_by_role("training")
    df_val = load_by_role("validation")

    df = pd.concat([df_hist, df_train, df_val], ignore_index=True)
    df = df.sort_values(by="Date", kind="stable").reset_index(drop=True)

    cfg = read_split_config()
    training_set = set(cfg.training)
    validation_set = set(cfg.validation)
    seasons_to_predict = list(training_set | validation_set)

    count_training = 0
    count_validation = 0

    for history, match in walkforward_split(df, seasons_to_predict):
        assert_no_leakage(history, match)

        match_season = match["season"]
        if match_season in training_set:
            count_training += 1
        elif match_season in validation_set:
            count_validation += 1

    # Verifica conteggio esatto delle partite verificate per ruolo
    assert count_training == 1140, f"Attese 1140 partite training, trovate {count_training}"
    assert count_validation == 7220, f"Attese 7220 partite validation, trovate {count_validation}"
    assert count_training + count_validation == 8360
