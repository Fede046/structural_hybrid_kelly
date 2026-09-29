"""Test di accettazione e unita' per la divergenza di de-vigging (US-C3.2)."""

import csv
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.data.split import load_by_role, read_split_config
from shk.market.divergence import (
    DIVERGENCE_CSV_COLUMNS,
    ODDS_BIN_LABELS,
    ODDS_BINS,
    REFERENCE_EDGE,
    assign_odds_bin,
    compute_divergence_table,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "results" / "us_c3_2_devig_divergence.csv"
PNG_PATH = REPO_ROOT / "thesis" / "figures" / "us_c3_2_devig_divergence.png"


# =============================================================================
# Test Unitari Sintetici (sempre eseguiti, indipendenti dai dati reali)
# =============================================================================


def test_assign_odds_bin_boundaries() -> None:
    """Verifica l'assegnazione corretta delle fasce di quota sugli estremi."""
    assert assign_odds_bin(1.0) == "[1, 1.5)"
    assert assign_odds_bin(1.4999) == "[1, 1.5)"
    assert assign_odds_bin(1.5) == "[1.5, 2)"
    assert assign_odds_bin(1.9999) == "[1.5, 2)"
    assert assign_odds_bin(2.0) == "[2, 3)"
    assert assign_odds_bin(2.9999) == "[2, 3)"
    assert assign_odds_bin(3.0) == "[3, 5)"
    assert assign_odds_bin(4.9999) == "[3, 5)"
    assert assign_odds_bin(5.0) == "[5, 10)"
    assert assign_odds_bin(9.9999) == "[5, 10)"
    assert assign_odds_bin(10.0) == "[10, inf)"
    assert assign_odds_bin(100.0) == "[10, inf)"


def test_assign_odds_bin_invalid_inputs() -> None:
    """Verifica che quote non valide o <= 1.0 sollevino ValueError."""
    with pytest.raises(ValueError):
        assign_odds_bin(0.99)
    with pytest.raises(ValueError):
        assign_odds_bin(-1.5)
    with pytest.raises(ValueError):
        assign_odds_bin(float("nan"))
    with pytest.raises(ValueError):
        assign_odds_bin(float("inf"))


def test_compute_divergence_table_synthetic() -> None:
    """Verifica il calcolo della tabella su un dataset sintetico controllato."""
    df_synthetic = pd.DataFrame(
        {
            "season": ["2010-11", "2010-11", "2010-11", "2020-21"],
            "B365H": [1.25, 2.00, np.nan, 2.50],
            "B365D": [6.00, 3.50, 3.50, 3.40],
            "B365A": [11.00, 3.80, 4.00, 2.80],
        }
    )
    seasons_order = ["2010-11", "2020-21"]
    res = compute_divergence_table(df_synthetic, seasons_order)

    assert list(res.columns) == list(DIVERGENCE_CSV_COLUMNS)
    # 6 bin + 2 season + 1 overall = 9 righe
    assert len(res) == 9

    s2010 = res[(res["level"] == "season") & (res["category"] == "2010-11")].iloc[0]
    assert s2010["matches_used"] == 2
    assert s2010["matches_excluded"] == 1
    assert s2010["additive_nan_matches"] == 0

    s2020 = res[(res["level"] == "season") & (res["category"] == "2020-21")].iloc[0]
    assert s2020["matches_used"] == 1
    assert s2020["matches_excluded"] == 0
    assert s2020["additive_nan_matches"] == 0

    overall = res[res["level"] == "overall"].iloc[0]
    assert overall["matches_used"] == 3
    assert overall["matches_excluded"] == 1
    assert overall["additive_nan_matches"] == 0


def test_compute_divergence_table_additive_nan_handling() -> None:
    """Verifica che mercati con additivo non applicabile siano esclusi e contati."""
    # Mercato estremo con overround enorme tale che l'additivo produce q <= 0
    # Es. quote [1.05, 1.05, 1.05]: overround = 3*(1/1.05) - 1 = 1.857
    # q_add = 1/1.05 - 1.857/3 = 0.952 - 0.619 = 0.333 (ancora positivo)
    # Es. quote [1.02, 100.0, 100.0]: overround = 1/1.02 + 0.02 - 1 = 0.000392 (troppo piccolo)
    # Consideriamo quote [1.05, 50.0, 50.0] con overround elevato:
    # 1/1.05 + 1/50 + 1/50 = 0.95238 + 0.04 = 0.99238 (S < 1, overround negativo)
    # Per produrre q <= 0 nell'additivo serve 1/O_i - (S - 1)/3 <= 0
    # ovvero (S - 1)/3 >= 1/O_i. Con O_i grande (es. 100, 1/O_i = 0.01),
    # basta che (S - 1)/3 >= 0.01, cioe' S >= 1.03.
    # Con quote [1.10, 100.0, 100.0]: 1/1.10 = 0.909, 2/100 = 0.02, S = 0.929.
    # Con quote [1.01, 1.10, 100.0]: 1/1.01 = 0.990, 1/1.10 = 0.909, 1/100 = 0.01.
    # S = 1.909, (S-1)/3 = 0.303 > 0.01 (1/100). Quindi q_add sull'esito 3 e' <= 0!
    df_nan_add = pd.DataFrame(
        {
            "season": ["2010-11"],
            "B365H": [1.01],
            "B365D": [1.10],
            "B365A": [100.0],
        }
    )
    res = compute_divergence_table(df_nan_add, ["2010-11"])
    s_row = res[(res["level"] == "season") & (res["category"] == "2010-11")].iloc[0]
    assert s_row["matches_used"] == 0
    assert s_row["matches_excluded"] == 0
    assert s_row["additive_nan_matches"] == 1


# =============================================================================
# Test di Accettazione sul CSV Versionato (sempre eseguiti, mai skippati)
# =============================================================================


def test_acceptance_csv_and_figure_exist() -> None:
    """Verifica che il file CSV e la figura del report esistano e non siano vuoti."""
    assert CSV_PATH.is_file(), f"CSV non trovato: {CSV_PATH}"
    assert CSV_PATH.stat().st_size > 0, "Il file CSV e' vuoto."
    assert PNG_PATH.is_file(), f"Figura non trovata: {PNG_PATH}"
    assert PNG_PATH.stat().st_size > 0, "Il file PNG e' vuoto."


def test_acceptance_csv_structure_and_columns() -> None:
    """Verifica la struttura, le colonne e il numero di righe del CSV."""
    with open(CSV_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    assert header == list(DIVERGENCE_CSV_COLUMNS)
    # 6 bin + 22 stagioni + 1 overall = 29 righe dati
    assert len(rows) == 29

    levels = [r[0] for r in rows]
    assert levels.count("bin") == 6
    assert levels.count("season") == 22
    assert levels.count("overall") == 1


def test_acceptance_sum_to_one_error() -> None:
    """Criterio: |sum(q) - 1| <= 1e-12 per ogni metodo su tutte le partite usate."""
    df_csv = pd.read_csv(CSV_PATH)
    overall = df_csv[df_csv["level"] == "overall"].iloc[0]

    err_prop = float(overall["max_abs_sum_error_proportional"])
    err_add = float(overall["max_abs_sum_error_additive"])
    err_pow = float(overall["max_abs_sum_error_power"])

    assert err_prop <= 1e-12, f"Errore proporzionale {err_prop} > 1e-12"
    assert err_add <= 1e-12, f"Errore additivo {err_add} > 1e-12"
    assert err_pow <= 1e-12, f"Errore power {err_pow} > 1e-12"


def test_acceptance_overall_mean_overround_bounds() -> None:
    """Criterio: overround medio complessivo compreso fra 1% e 15%."""
    df_csv = pd.read_csv(CSV_PATH)
    overall = df_csv[df_csv["level"] == "overall"].iloc[0]
    ovr = float(overall["mean_overround"])

    assert 0.01 <= ovr <= 0.15, f"Overround complessivo {ovr} fuori da [0.01, 0.15]"


def test_acceptance_mean_relative_spread_maximum_in_extreme_bin() -> None:
    """Criterio: lo spread relativo medio e' massimo nella fascia [10, inf)."""
    df_csv = pd.read_csv(CSV_PATH)
    bins = df_csv[df_csv["level"] == "bin"].set_index("category")

    extreme_rel_spread = float(bins.loc["[10, inf)", "mean_relative_spread"])
    for b_label in ODDS_BIN_LABELS:
        if b_label != "[10, inf)":
            other_rel_spread = float(bins.loc[b_label, "mean_relative_spread"])
            assert extreme_rel_spread > other_rel_spread, (
                f"Spread relativo in [10, inf) ({extreme_rel_spread}) non e' strettamente "
                f"superiore a {b_label} ({other_rel_spread})"
            )


def test_acceptance_seasons_strictly_non_test() -> None:
    """Criterio: le stagioni usate appartengono a training/validation e nessuna a test."""
    cfg = read_split_config()
    allowed_seasons = set(cfg.training) | set(cfg.validation)
    test_seasons = set(cfg.test)

    df_csv = pd.read_csv(CSV_PATH)
    season_rows = df_csv[df_csv["level"] == "season"]
    csv_seasons = set(season_rows["category"])

    # Tutte le stagioni nel CSV devono essere esattamente l'unione di training e validation
    assert csv_seasons == allowed_seasons
    # Nessuna stagione di test deve essere presente
    assert len(csv_seasons & test_seasons) == 0

    # Verifica specifica della stagione 2000-01 (senza quote B365)
    s2000 = season_rows[season_rows["category"] == "2000-01"].iloc[0]
    assert s2000["matches_used"] == 0
    assert s2000["matches_excluded"] == 380


# =============================================================================
# Test di Ricalcolo con Dati Reali (skippato se i CSV grezzi non ci sono)
# =============================================================================


def test_recomputation_against_raw_data() -> None:
    """Verifica che i valori nel CSV corrispondano al ricalcolo con tolleranza 1e-12."""
    if not (DEFAULT_DATA_DIR.is_dir() and list(DEFAULT_DATA_DIR.glob("*.csv"))):
        pytest.skip("Directory data/raw/E0/ non presente o priva di file CSV.")

    cfg = read_split_config()
    seasons_order = sorted(list(cfg.training) + list(cfg.validation))

    df_train = load_by_role("training")
    df_val = load_by_role("validation")
    df_all = pd.concat([df_train, df_val], ignore_index=True)

    recomputed_df = compute_divergence_table(df_all, seasons_order=seasons_order)

    with open(CSV_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        csv_records = list(reader)

    recomp_records = recomputed_df.to_dict(orient="records")
    assert len(csv_records) == len(recomp_records)

    for i, (csv_row, rec_row) in enumerate(zip(csv_records, recomp_records, strict=True)):
        for col in DIVERGENCE_CSV_COLUMNS:
            val_csv = csv_row[col]
            val_rec = rec_row[col]

            if val_csv == "":
                assert val_rec == "", f"Riga {i} col {col}: atteso vuoto, ottenuto {val_rec}"
            else:
                try:
                    f_csv = float(val_csv)
                    f_rec = float(val_rec)
                    assert math.isclose(f_csv, f_rec, rel_tol=1e-12, abs_tol=1e-12), (
                        f"Discrepanza float riga {i} ({csv_row['level']}:{csv_row['category']}) "
                        f"col {col}: CSV={f_csv} vs ricalcolo={f_rec}"
                    )
                except ValueError:
                    assert val_csv == str(val_rec), (
                        f"Discrepanza stringa riga {i} col {col}: "
                        f"CSV={val_csv} vs ricalcolo={val_rec}"
                    )
