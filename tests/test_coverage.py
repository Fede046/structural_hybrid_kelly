"""Test per il modulo src/shk/data/coverage.py."""

import numpy as np
import pandas as pd
import pytest

from shk.data.coverage import (
    COVERAGE_CSV_COLUMNS,
    NON_ODDS_COLUMNS,
    ColumnClassification,
    classify_column,
    compute_coverage,
)


def test_classify_column_known_types():
    """Verifica la classificazione per i principali gruppi di colonne."""
    # 1X2 pre-partita bookmaker
    c_b365 = classify_column("B365H")
    assert c_b365.group_type == "1x2_prematch"
    assert c_b365.source == "B365"
    assert c_b365.market == "1x2"
    assert c_b365.timing == "prematch"
    assert c_b365.kind == "odds"

    # 1X2 chiusura bookmaker
    c_psch = classify_column("PSCH")
    assert c_psch.group_type == "1x2_closing"
    assert c_psch.source == "PS"
    assert c_psch.market == "1x2"
    assert c_psch.timing == "closing"
    assert c_psch.kind == "odds"

    # Altri mercati (Over/Under)
    c_ou = classify_column("B365>2.5")
    assert c_ou.group_type == "other_markets"
    assert c_ou.market == "over_under_2.5"
    assert c_ou.kind == "odds"

    # Linee handicap
    c_ahh = classify_column("AHh")
    assert c_ahh.group_type == "other_markets"
    assert c_ahh.source == "market"
    assert c_ahh.market == "asian_handicap"
    assert c_ahh.timing == "prematch"
    assert c_ahh.kind == "line"

    # Conteggi Betbrain
    c_cnt = classify_column("Bb1X2")
    assert c_cnt.group_type == "aggregators"
    assert c_cnt.source == "Bb"
    assert c_cnt.kind == "count"


def test_classify_column_closing_aggregators():
    """Verifica che MaxCH e AvgCA siano aggregators con timing closing."""
    c_maxch = classify_column("MaxCH")
    assert c_maxch.group_type == "aggregators"
    assert c_maxch.source == "Max"
    assert c_maxch.market == "1x2"
    assert c_maxch.timing == "closing"
    assert c_maxch.kind == "odds"

    c_avgca = classify_column("AvgCA")
    assert c_avgca.group_type == "aggregators"
    assert c_avgca.source == "Avg"
    assert c_avgca.market == "1x2"
    assert c_avgca.timing == "closing"
    assert c_avgca.kind == "odds"


def test_classify_column_non_odds_and_unknown_raises():
    """Verifica che colonne non di quota o sconosciute sollevino ValueError."""
    # Colonne in NON_ODDS_COLUMNS
    for col in ("Div", "Date", "Referee", "FTHG", "Attendance", "HHW", "HTHG"):
        with pytest.raises(ValueError, match="Non-odds column"):
            classify_column(col)

    # Colonna del tutto ignota
    with pytest.raises(ValueError, match="Unknown column cannot be classified"):
        classify_column("UNKNOWN_COLUMN_XYZ")


def test_compute_coverage_string_column_non_numeric_invalid():
    """Verifica che valori non numerici in colonne stringa siano contati come non validi."""
    df = pd.DataFrame(
        {
            "season": ["2002-03", "2002-03"],
            "B365H": ["2.50", "N/A"],  # N/A non e' nullo in origine ma stringa non numerica
            "B365D": ["3.20", "3.10"],
            "B365A": ["2.80", "2.90"],
        }
    )
    cov = compute_coverage(df)
    row = cov[cov["group_name"] == "b365_1x2_prematch"].iloc[0]
    assert row["total_rows"] == 2
    assert row["missing_rows"] == 0
    assert row["invalid_rows"] == 1
    assert row["complete_rows"] == 1
    assert row["is_complete"] == "False"


def test_compute_coverage_inf_is_invalid():
    """Verifica che valori inf siano contati come non validi."""
    df = pd.DataFrame(
        {
            "season": ["2002-03", "2002-03"],
            "B365H": [2.50, np.inf],
            "B365D": [3.20, 3.10],
            "B365A": [2.80, 2.90],
        }
    )
    cov = compute_coverage(df)
    row = cov[cov["group_name"] == "b365_1x2_prematch"].iloc[0]
    assert row["total_rows"] == 2
    assert row["missing_rows"] == 0
    assert row["invalid_rows"] == 1
    assert row["complete_rows"] == 1


def test_compute_coverage_nan_is_missing_not_invalid():
    """Verifica che NaN sia contato tra i mancanti e non tra i non validi."""
    df = pd.DataFrame(
        {
            "season": ["2002-03", "2002-03"],
            "B365H": [2.50, np.nan],
            "B365D": [3.20, 3.10],
            "B365A": [2.80, 2.90],
        }
    )
    cov = compute_coverage(df)
    row = cov[cov["group_name"] == "b365_1x2_prematch"].iloc[0]
    assert row["total_rows"] == 2
    assert row["missing_rows"] == 1
    assert row["invalid_rows"] == 0
    assert row["complete_rows"] == 1


def test_compute_coverage_line_and_count_never_invalid():
    """Verifica che colonne line e count abbiano invalid_rows = 0 anche con valori <= 1."""
    df = pd.DataFrame(
        {
            "season": ["2019-20", "2019-20"],
            "AHh": [-0.5, 0.25],  # valori <= 1, ma e' una linea di handicap
            "Bb1X2": [0, 1],  # valori <= 1, ma e' un conteggio
        }
    )
    cov = compute_coverage(df)

    line_row = cov[cov["group_name"] == "market_asian_handicap_prematch_line"].iloc[0]
    assert line_row["invalid_rows"] == 0
    assert line_row["missing_rows"] == 0
    assert line_row["complete_rows"] == 2

    count_row = cov[cov["group_name"] == "bb_1x2_prematch_count"].iloc[0]
    assert count_row["invalid_rows"] == 0
    assert count_row["missing_rows"] == 0
    assert count_row["complete_rows"] == 2


def test_compute_coverage_row_both_missing_and_invalid():
    """Verifica che una riga sia mancante sia non valida sia contata una sola volta tra le non complete."""
    df = pd.DataFrame(
        {
            "season": ["2002-03", "2002-03"],
            "B365H": [np.nan, 2.50],
            "B365D": [0.80, 3.10],  # riga 0 ha sia NaN su B365H sia 0.80 su B365D
            "B365A": [2.80, 2.90],
        }
    )
    cov = compute_coverage(df)
    row = cov[cov["group_name"] == "b365_1x2_prematch"].iloc[0]
    assert row["total_rows"] == 2
    assert row["missing_rows"] == 1
    assert row["invalid_rows"] == 1
    assert row["complete_rows"] == 1
    assert row["is_complete"] == "False"


def test_compute_coverage_absent_group_omitted():
    """Verifica che una stagione priva di una determinata terna non emetta righe per quel gruppo."""
    df = pd.DataFrame(
        {
            "season": ["2000-01", "2002-03"],
            "B365H": [np.nan, 2.50],
            "B365D": [np.nan, 3.20],
            "B365A": [np.nan, 2.80],
            "GBH": [2.10, 2.20],
            "GBD": [3.10, 3.20],
            "GBA": [3.30, 3.40],
        }
    )
    cov = compute_coverage(df)

    # 2000-01 non ha valori non nulli per B365: nessun record per b365_1x2_prematch in 2000-01
    b365_2000 = cov[(cov["season"] == "2000-01") & (cov["group_name"] == "b365_1x2_prematch")]
    assert len(b365_2000) == 0

    # 2002-03 ha B365 presente
    b365_2002 = cov[(cov["season"] == "2002-03") & (cov["group_name"] == "b365_1x2_prematch")]
    assert len(b365_2002) == 1


def test_compute_coverage_results_validation():
    """Verifica l'audit del gruppo risultati con esiti validi e non validi."""
    df = pd.DataFrame(
        {
            "season": ["1993-94", "1993-94", "1993-94", "1993-94"],
            "FTHG": [2, 1, np.nan, 3],
            "FTAG": [1, 1, 0, 0],
            "FTR": ["H", "D", "H", "A"],  # Riga 3: 3-0 ma FTR='A' (incoerente)
        }
    )
    cov = compute_coverage(df)
    res_row = cov[cov["group_type"] == "results"].iloc[0]
    assert res_row["total_rows"] == 4
    assert res_row["missing_rows"] == 1  # Riga 2
    assert res_row["invalid_rows"] == 1  # Riga 3
    assert res_row["complete_rows"] == 2  # Righe 0 e 1
    assert res_row["is_complete"] == "False"


def test_compute_coverage_csv_columns_and_ordering():
    """Verifica che le colonne e l'ordine dei gruppi rispettino le specifiche."""
    df = pd.DataFrame(
        {
            "season": ["2019-20"],
            "FTHG": [1],
            "FTAG": [0],
            "FTR": ["H"],
            "B365H": [2.10],
            "B365D": [3.20],
            "B365A": [3.40],
            "B365CH": [2.05],
            "B365CD": [3.25],
            "B365CA": [3.50],
            "MaxH": [2.15],
            "MaxD": [3.30],
            "MaxA": [3.60],
            "B365>2.5": [1.90],
            "B365<2.5": [1.90],
        }
    )
    cov = compute_coverage(df)
    assert tuple(cov.columns) == COVERAGE_CSV_COLUMNS
    group_types = list(cov["group_type"])
    assert group_types == [
        "results",
        "1x2_prematch",
        "1x2_closing",
        "aggregators",
        "other_markets",
    ]


def test_compute_coverage_excludes_stats_and_halftime_columns():
    """Verifica che tutte le colonne di statistica e primo tempo siano escluse dall'audit."""
    data = {
        "season": ["2019-20"],
        "Div": ["E0"],
        "Date": ["10/08/2019"],
        "HomeTeam": ["Liverpool"],
        "AwayTeam": ["Norwich"],
        "FTHG": [4],
        "FTAG": [1],
        "FTR": ["H"],
        "B365H": [1.14],
        "B365D": [8.50],
        "B365A": [19.00],
        "HTHG": [4],
        "HTAG": [0],
        "HTR": ["H"],
        "Referee": ["M Oliver"],
        "HS": [15],
        "AS": [12],
        "HST": [7],
        "AST": [5],
        "HF": [9],
        "AF": [9],
        "HC": [11],
        "AC": [2],
        "HY": [0],
        "AY": [2],
        "HR": [0],
        "AR": [0],
        "Attendance": [53333],
        "HHW": [1],
        "AHW": [0],
        "HO": [2],
        "AO": [1],
        "HBP": [0],
        "ABP": [0],
    }
    df = pd.DataFrame(data)
    cov = compute_coverage(df)

    assert len(cov) == 2
    assert set(cov["group_type"]) == {"results", "1x2_prematch"}
    assert set(cov["group_name"]) == {"results", "b365_1x2_prematch"}

    stats_and_halftime_cols = {
        "HTHG",
        "HTAG",
        "HTR",
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
        "Attendance",
        "HHW",
        "AHW",
        "HO",
        "AO",
        "HBP",
        "ABP",
    }
    for cols_str in cov["columns"]:
        col_list = cols_str.split(";")
        for col in col_list:
            assert col not in stats_and_halftime_cols
