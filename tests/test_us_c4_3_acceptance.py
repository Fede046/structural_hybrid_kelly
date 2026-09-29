"""Test di accettazione per ricalibrazione, reliability e Brier (US-C4.3)."""

import csv
import math
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.data.split import load_by_role, read_split_config
from shk.model.elo_fit import ELO_FITS, derive_fit_schedule
from shk.model.recalibration import (
    CALIBRATION_CSV_COLUMNS,
    brier_score,
    compute_reliability_table,
    fit_all_calibration_maps,
    recalibrate_series_predictions,
)
from shk.model.scoring import (
    DEVIG_METHODS,
    SERIES_NAMES,
    align_predictions_with_odds,
    compute_g_hat,
    compute_mean_log_loss,
    generate_validation_predictions,
    prepare_series_evaluation,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "results" / "us_c4_3_calibration.csv"
PNG_PATH = REPO_ROOT / "thesis" / "figures" / "us_c4_3_calibration.png"
T23_CSV_PATH = REPO_ROOT / "results" / "us_c4_2_g_hat.csv"


def _has_real_data() -> bool:
    """Verifica se i file CSV dei dati reali sono presenti."""
    return DEFAULT_DATA_DIR.exists() and len(list(DEFAULT_DATA_DIR.glob("*.csv"))) > 0


def test_csv_schema_and_counts():
    """Verifica colonne, 120 righe di reliability e 24 righe di score nel CSV versionato."""
    assert CSV_PATH.exists(), f"File {CSV_PATH} not found"

    with open(CSV_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = tuple(next(reader))
        assert header == CALIBRATION_CSV_COLUMNS

    df = pd.read_csv(CSV_PATH, dtype=str)
    assert len(df) == 144

    df_rel = df[df["level"] == "reliability"]
    df_score = df[df["level"] == "score"]

    assert len(df_rel) == 120
    assert len(df_score) == 24

    # Controllo ordine reliability: version -> outcome -> bin crescente
    expected_rel_versions = ["raw", "isotonic", "platt"]
    expected_rel_outcomes = ["all", "H", "D", "A"]

    rel_idx = 0
    for v in expected_rel_versions:
        for out in expected_rel_outcomes:
            for b in range(10):
                row = df_rel.iloc[rel_idx]
                assert row["version"] == v
                assert row["outcome"] == out
                assert math.isclose(float(row["bin_lower"]), b * 0.1, abs_tol=1e-6)
                assert math.isclose(float(row["bin_upper"]), (b + 1) * 0.1, abs_tol=1e-6)
                assert row["matches_used"] == "7220"
                # Campi vuoti
                assert pd.isna(row["log_loss"]) or row["log_loss"] == ""
                assert pd.isna(row["brier"]) or row["brier"] == ""
                assert pd.isna(row["g_hat"]) or row["g_hat"] == ""
                rel_idx += 1


def test_reliability_z_scores_and_bounds():
    """Verifica la correttezza della formula di z e coerenza su ciascun bin popolato."""
    df = pd.read_csv(CSV_PATH)
    df_rel = df[df["level"] == "reliability"]

    for _, row in df_rel.iterrows():
        count = int(row["count"])
        if count == 0:
            assert pd.isna(row["mean_predicted"])
            assert pd.isna(row["observed_frequency"])
            assert pd.isna(row["gap"])
            assert pd.isna(row["z"])
        else:
            p_bar = float(row["mean_predicted"])
            y_bar = float(row["observed_frequency"])
            gap = float(row["gap"])
            z_val = float(row["z"])

            assert 0.0 <= p_bar <= 1.0
            assert 0.0 <= y_bar <= 1.0
            assert math.isclose(gap, y_bar - p_bar, abs_tol=1e-12)

            denom = math.sqrt(p_bar * (1.0 - p_bar) / count)
            if denom > 0:
                assert math.isclose(z_val, gap / denom, rel_tol=1e-12, abs_tol=1e-12)


def test_raw_g_hat_matches_t23():
    """Criterio di accettazione: con la versione raw, g_hat coincide con T23 entro 1e-12."""
    assert CSV_PATH.exists()
    assert T23_CSV_PATH.exists()

    df_t24 = pd.read_csv(CSV_PATH)
    df_t23 = pd.read_csv(T23_CSV_PATH)

    df_t24_raw = df_t24[(df_t24["level"] == "score") & (df_t24["version"] == "raw")]
    df_t23_sum = df_t23[df_t23["level"] == "summary"]

    for s_name in SERIES_NAMES:
        for m in DEVIG_METHODS:
            row_24 = df_t24_raw[(df_t24_raw["series"] == s_name) & (df_t24_raw["method"] == m)].iloc[0]
            row_23 = df_t23_sum[(df_t23_sum["series"] == s_name) & (df_t23_sum["method"] == m)].iloc[0]

            assert math.isclose(
                float(row_24["log_loss"]), float(row_23["log_loss_model"]), rel_tol=1e-12, abs_tol=1e-12
            )
            assert math.isclose(
                float(row_24["g_hat"]), float(row_23["g_hat"]), rel_tol=1e-12, abs_tol=1e-12
            )


def test_figure_exists():
    """Verifica che la figura thesis/figures/us_c4_3_calibration.png esista e sia non vuota."""
    assert PNG_PATH.exists()
    assert PNG_PATH.stat().st_size > 1000


@pytest.mark.skipif(not _has_real_data(), reason="Raw CSV data not available in data/raw/E0/")
@pytest.mark.skipif(not CSV_PATH.exists(), reason="Requires results/us_c4_3_calibration.csv")
def test_recalculation_from_real_data_matches_csv():
    """Ricalcolo da zero sui dati reali coincide con il CSV entro 1e-12."""
    cfg = read_split_config()
    schedule = derive_fit_schedule(cfg)

    df_hist = load_by_role("history")
    df_train = load_by_role("training")
    df_val = load_by_role("validation")

    df_full = pd.concat([df_hist, df_train, df_val], ignore_index=True)
    df_full = df_full.sort_values("Date", kind="stable").reset_index(drop=True)

    fit_maps = fit_all_calibration_maps(df_full, ELO_FITS, schedule)

    df_preds = generate_validation_predictions(df_full, ELO_FITS, schedule)
    df_aligned = align_predictions_with_odds(df_preds, df_full)

    eval_b365 = prepare_series_evaluation(df_aligned, "b365_prematch", schedule)
    eval_psc = prepare_series_evaluation(df_aligned, "pinnacle_closing", schedule)

    eval_map = {
        "b365_prematch": eval_b365,
        "pinnacle_closing": eval_psc,
    }

    df_csv = pd.read_csv(CSV_PATH)
    df_score = df_csv[df_csv["level"] == "score"]

    for s_name, ev_data in eval_map.items():
        p_iso, n_clip_iso, _ = recalibrate_series_predictions(ev_data, fit_maps, "isotonic", schedule)
        p_platt, n_clip_platt, _ = recalibrate_series_predictions(ev_data, fit_maps, "platt", schedule)

        # Somme a 1 entro 1e-12
        np.testing.assert_allclose(p_iso.sum(axis=1), 1.0, atol=1e-12)
        np.testing.assert_allclose(p_platt.sum(axis=1), 1.0, atol=1e-12)

        ver_probs = {
            "raw": ev_data.p_model,
            "isotonic": p_iso,
            "platt": p_platt,
        }

        methods_q = {
            "proportional": ev_data.q_proportional,
            "additive": ev_data.q_additive,
            "power": ev_data.q_power,
        }

        for ver, p_curr in ver_probs.items():
            ll_mod = compute_mean_log_loss(p_curr, ev_data.outcomes)
            bs_mod = brier_score(p_curr, ev_data.outcomes)

            for m in DEVIG_METHODS:
                q_mkt = methods_q[m]
                g_hat_val = compute_g_hat(p_curr, q_mkt, ev_data.outcomes)

                row_csv = df_score[
                    (df_score["version"] == ver)
                    & (df_score["series"] == s_name)
                    & (df_score["method"] == m)
                ].iloc[0]

                assert math.isclose(ll_mod, float(row_csv["log_loss"]), rel_tol=1e-12, abs_tol=1e-12)
                assert math.isclose(bs_mod, float(row_csv["brier"]), rel_tol=1e-12, abs_tol=1e-12)
                assert math.isclose(g_hat_val, float(row_csv["g_hat"]), rel_tol=1e-12, abs_tol=1e-12)
