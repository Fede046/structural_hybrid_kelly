"""Test di accettazione per g_hat del Modulo 1 contro il mercato de-viggato (US-C4.2)."""

import csv
import math
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.data.split import load_by_role, read_split_config
from shk.model.elo_fit import ELO_FITS, derive_fit_schedule
from shk.model.scoring import (
    CSV_COLUMNS,
    DEVIG_METHODS,
    SERIES_NAMES,
    align_predictions_with_odds,
    compute_g_hat,
    compute_mean_log_loss,
    generate_validation_predictions,
    prepare_series_evaluation,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "results" / "us_c4_2_g_hat.csv"
PNG_PATH = REPO_ROOT / "thesis" / "figures" / "us_c4_2_g_hat.png"


def _has_real_data() -> bool:
    """Verifica se i file CSV dei dati reali sono presenti."""
    return DEFAULT_DATA_DIR.exists() and len(list(DEFAULT_DATA_DIR.glob("*.csv"))) > 0


def test_csv_schema_and_summary_structure():
    """Verifica colonne, 6 righe di summary e relazione esatta g_hat = LL(q) - LL(p)."""
    assert CSV_PATH.exists(), f"File {CSV_PATH} not found"

    with open(CSV_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = tuple(next(reader))
        assert header == CSV_COLUMNS, f"Header mismatch: {header} vs {CSV_COLUMNS}"

    df = pd.read_csv(CSV_PATH, dtype=str)
    df_sum = df[df["level"] == "summary"]

    assert len(df_sum) == 6, f"Expected 6 summary rows, got {len(df_sum)}"

    expected_pairs = [
        (s, m) for s in SERIES_NAMES for m in DEVIG_METHODS
    ]
    actual_pairs = list(zip(df_sum["series"], df_sum["method"]))
    assert actual_pairs == expected_pairs, f"Order mismatch: {actual_pairs} vs {expected_pairs}"

    for _, row in df_sum.iterrows():
        # Campi che devono essere vuoti nel summary
        assert pd.isna(row["t"]) or row["t"] == ""
        assert pd.isna(row["season"]) or row["season"] == ""
        assert pd.isna(row["date"]) or row["date"] == ""

        # Campi valorizzati
        n_used = int(row["matches_used"])
        n_excl = int(row["matches_excluded"])
        ll_model = float(row["log_loss_model"])
        ll_market = float(row["log_loss_market"])
        g_hat = float(row["g_hat"])

        assert n_used > 0
        assert n_excl >= 0
        # g_hat = log_loss_market - log_loss_model entro 1e-12
        assert math.isclose(g_hat, ll_market - ll_model, rel_tol=1e-12, abs_tol=1e-12)


def test_csv_cumulative_consistency():
    """Verifica che le righe cumulative siano coerenti con matches_used e convergano a g_hat."""
    assert CSV_PATH.exists()
    df = pd.read_csv(CSV_PATH)

    df_sum = df[df["level"] == "summary"]
    df_cum = df[df["level"] == "cumulative"]

    for series_name in SERIES_NAMES:
        for method in DEVIG_METHODS:
            sum_row = df_sum[(df_sum["series"] == series_name) & (df_sum["method"] == method)].iloc[0]
            n_used = int(sum_row["matches_used"])
            expected_g_hat = float(sum_row["g_hat"])

            cum_rows = df_cum[(df_cum["series"] == series_name) & (df_cum["method"] == method)]
            assert len(cum_rows) == n_used, (
                f"Mismatch in cumulative row count for {series_name} {method}: {len(cum_rows)} vs {n_used}"
            )

            # Controllo sequenza t da 1 a n_used
            t_values = cum_rows["t"].to_numpy(dtype=int)
            np.testing.assert_array_equal(t_values, np.arange(1, n_used + 1))

            # Ultimo valore della serie cumulativa coincide con summary g_hat entro 1e-12
            last_g_cum = float(cum_rows["g_hat"].iloc[-1])
            assert math.isclose(last_g_cum, expected_g_hat, rel_tol=1e-12, abs_tol=1e-12)


def test_figure_file_exists():
    """Verifica che la figura us_c4_2_g_hat.png esista e non sia vuota."""
    assert PNG_PATH.exists(), f"Figure file {PNG_PATH} does not exist"
    assert PNG_PATH.stat().st_size > 1000, "Figure file appears too small or empty"


@pytest.mark.skipif(not _has_real_data(), reason="Raw CSV data not available in data/raw/E0/")
@pytest.mark.skipif(not CSV_PATH.exists(), reason="Requires results/us_c4_2_g_hat.csv")
def test_recalculation_from_real_data_matches_csv():
    """Ricalcolo dai dati: coincide con il CSV entro rel_tol e abs_tol 1e-12."""
    cfg = read_split_config()
    schedule = derive_fit_schedule(cfg)

    df_hist = load_by_role("history")
    df_train = load_by_role("training")
    df_val = load_by_role("validation")

    df_full = pd.concat([df_hist, df_train, df_val], ignore_index=True)
    df_full = df_full.sort_values("Date", kind="stable").reset_index(drop=True)

    df_preds = generate_validation_predictions(df_full, ELO_FITS, schedule)
    df_aligned = align_predictions_with_odds(df_preds, df_full)

    df_csv = pd.read_csv(CSV_PATH)
    df_sum = df_csv[df_csv["level"] == "summary"]

    for series_name in SERIES_NAMES:
        eval_data = prepare_series_evaluation(df_aligned, series_name, schedule)

        # Criterio di accettazione 1: esclusioni per causa identiche per tutti i metodi
        assert eval_data.missing_odds == 0
        assert eval_data.invalid_odds == 0
        assert eval_data.additive_inapplicable == 0
        assert eval_data.matches_excluded == 0

        if series_name == "b365_prematch":
            assert eval_data.matches_used == 7220
        else:
            assert eval_data.matches_used == 3800

        ll_model = compute_mean_log_loss(eval_data.p_model, eval_data.outcomes)

        methods_q = {
            "proportional": eval_data.q_proportional,
            "additive": eval_data.q_additive,
            "power": eval_data.q_power,
        }

        for method in DEVIG_METHODS:
            row_csv = df_sum[
                (df_sum["series"] == series_name) & (df_sum["method"] == method)
            ].iloc[0]

            q_market = methods_q[method]
            ll_market = compute_mean_log_loss(q_market, eval_data.outcomes)
            g_hat_val = compute_g_hat(eval_data.p_model, q_market, eval_data.outcomes)

            assert math.isclose(
                ll_model, float(row_csv["log_loss_model"]), rel_tol=1e-12, abs_tol=1e-12
            )
            assert math.isclose(
                ll_market, float(row_csv["log_loss_market"]), rel_tol=1e-12, abs_tol=1e-12
            )
            assert math.isclose(
                g_hat_val, float(row_csv["g_hat"]), rel_tol=1e-12, abs_tol=1e-12
            )
