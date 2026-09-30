"""Test di accettazione per US-C5.2 / Task 29.

Verifica:
- sui test sintetici: calcolo di mu e sigma delle baseline di training, schema delle 14 colonne,
  coerenza degli allarmi (matchday vs summary vs overall), valori attesi;
- sul CSV versionato results/us_c5_2_daily_z_test.csv (eseguibile in CI anche senza dati grezzi):
  schema delle 14 colonne, 722 righe matchday, 57 righe summary, 3 righe overall, coerenza con
  i risultati di C5.1 per ADWIN e Page-Hinkley, assenza di leak della stagione 2023-24;
- sulla figura thesis/figures/us_c5_2_daily_z_test.png: esistenza e dimensione non nulla;
- sui dati reali (saltato se non disponibili): ricalcolo esatto riga per riga contro il CSV versionato.
"""

import csv
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.data.split import load_by_role, read_split_config
from shk.model.elo_fit import ELO_FITS, derive_fit_schedule
from shk.model.monitoring import (
    DAILY_Z_TEST_CSV_COLUMNS,
    EXPECTED_MATCHES_PER_SEASON,
    ScenarioSeries,
    TrainingBaselineStats,
    build_daily_z_test_records,
    compute_training_baseline_stats,
    generate_daily_z_test_records,
)
from shk.model.residuals import compute_model_residuals


def _has_real_data() -> bool:
    """Verifica se i dati grezzi sono presenti sul filesystem."""
    return DEFAULT_DATA_DIR.exists() and len(list(DEFAULT_DATA_DIR.glob("*.csv"))) > 0


def _get_csv_path() -> Path:
    """Restituisce il percorso del file CSV dello Z-test di C5.2."""
    repo_root = Path(__file__).resolve().parents[1]
    return repo_root / "results" / "us_c5_2_daily_z_test.csv"


def _get_c51_csv_path() -> Path:
    """Restituisce il percorso del CSV di C5.1."""
    repo_root = Path(__file__).resolve().parents[1]
    return repo_root / "results" / "us_c5_1_drift_detectors.csv"


def _get_png_path() -> Path:
    """Restituisce il percorso della figura di C5.2."""
    repo_root = Path(__file__).resolve().parents[1]
    return repo_root / "thesis" / "figures" / "us_c5_2_daily_z_test.png"


def _create_synthetic_residuals_df() -> tuple[pd.DataFrame, dict[str, dict[str, list[str]]]]:
    """Crea un DataFrame sintetico di residui con 1 fit di training e 2 stagioni di validazione."""
    n_matches = EXPECTED_MATCHES_PER_SEASON

    dates_tr = pd.date_range("2000-08-19", periods=n_matches, freq="D")
    df_tr = pd.DataFrame({
        "fit_through": ["2000-01"] * n_matches,
        "role": ["training"] * n_matches,
        "season": ["2000-01"] * n_matches,
        "Date": dates_tr,
        "HomeTeam": [f"TeamH_{i % 20}" for i in range(n_matches)],
        "AwayTeam": [f"TeamA_{i % 20}" for i in range(n_matches)],
        "p_home": [0.45] * n_matches,
        "p_draw": [0.28] * n_matches,
        "p_away": [0.27] * n_matches,
        "FTR": ["H"] * n_matches,
        "log_loss": [1.0 + 0.1 * math.sin(i / 10.0) for i in range(n_matches)],
    })

    dates_val1 = pd.date_range("2002-08-17", periods=n_matches, freq="D")
    df_val1 = pd.DataFrame({
        "fit_through": ["2000-01"] * n_matches,
        "role": ["validation"] * n_matches,
        "season": ["2002-03"] * n_matches,
        "Date": dates_val1,
        "HomeTeam": [f"TeamH_{i % 20}" for i in range(n_matches)],
        "AwayTeam": [f"TeamA_{i % 20}" for i in range(n_matches)],
        "p_home": [0.40] * n_matches,
        "p_draw": [0.30] * n_matches,
        "p_away": [0.30] * n_matches,
        "FTR": ["H"] * n_matches,
        "log_loss": [1.0 + 0.1 * math.cos(i / 10.0) for i in range(n_matches)],
    })

    dates_val2 = pd.date_range("2003-08-16", periods=n_matches, freq="D")
    df_val2 = pd.DataFrame({
        "fit_through": ["2000-01"] * n_matches,
        "role": ["validation"] * n_matches,
        "season": ["2003-04"] * n_matches,
        "Date": dates_val2,
        "HomeTeam": [f"TeamH_{i % 20}" for i in range(n_matches)],
        "AwayTeam": [f"TeamA_{i % 20}" for i in range(n_matches)],
        "p_home": [0.40] * n_matches,
        "p_draw": [0.30] * n_matches,
        "p_away": [0.30] * n_matches,
        "FTR": ["H"] * n_matches,
        "log_loss": [1.2 + 0.2 * math.cos(i / 5.0) for i in range(n_matches)],
    })

    df = pd.concat([df_tr, df_val1, df_val2], ignore_index=True)
    schedule = {
        "2000-01": {
            "training": ["2000-01"],
            "validation": ["2002-03", "2003-04"],
        }
    }
    return df, schedule


# ---------------------------------------------------------------------------
# Test Sintetici / Unitari (senza dati reali)
# ---------------------------------------------------------------------------


def test_compute_training_baseline_stats_synthetic():
    """Verifica il calcolo di mu e sigma (ddof=1) e le validazioni difensive."""
    df, schedule = _create_synthetic_residuals_df()
    stats = compute_training_baseline_stats(df, schedule)

    assert "2000-01" in stats
    b = stats["2000-01"]
    assert isinstance(b, TrainingBaselineStats)
    assert b.fit_through == "2000-01"
    assert b.n_matches == EXPECTED_MATCHES_PER_SEASON

    # Verifica calcolo con numpy / pandas diretto
    tr_losses = df[(df["role"] == "training") & (df["fit_through"] == "2000-01")]["log_loss"]
    np.testing.assert_allclose(b.mu, float(tr_losses.mean()), atol=1e-12)
    np.testing.assert_allclose(b.sigma, float(tr_losses.std(ddof=1)), atol=1e-12)

    # Validazione df non pd.DataFrame
    with pytest.raises(TypeError, match="pd.DataFrame"):
        compute_training_baseline_stats("not_a_df")  # type: ignore

    # Validazione schedule non dict
    with pytest.raises(TypeError, match="dict or None"):
        compute_training_baseline_stats(df, schedule=123)  # type: ignore

    # Validazione colonne mancanti
    with pytest.raises(ValueError, match="missing required columns"):
        compute_training_baseline_stats(df.drop(columns=["log_loss"]))

    # Validazione n_matches < 2
    df_too_short = df.iloc[:1].copy()
    with pytest.raises(ValueError, match="minimum required is 2"):
        compute_training_baseline_stats(df_too_short, schedule)


def test_synthetic_records_schema_and_types():
    """Verifica che tutti i record prodotti rispettino lo schema di 14 colonne e i tipi attesi."""
    df, schedule = _create_synthetic_residuals_df()
    records = generate_daily_z_test_records(df, schedule)

    # 2 stagioni di validazione x 38 giornate = 76 matchday
    # 2 stagioni x 3 metodi = 6 summary
    # 3 overall
    assert len(records) == 76 + 6 + 3

    for r in records:
        assert tuple(r.keys()) == DAILY_Z_TEST_CSV_COLUMNS
        row_type = r["row_type"]
        assert row_type in ("matchday", "summary", "overall")

        if row_type == "matchday":
            assert r["method"] == "z_nominal"
            assert r["block_length"] == ""
            assert isinstance(r["threshold"], float)
            assert isinstance(r["matchday"], int)
            assert 1 <= r["matchday"] <= 38
            assert isinstance(r["z"], float)
            assert r["alarm"] in (0, 1)
            assert r["n_alarms"] == ""
            assert r["expected_alarms"] == ""
            assert r["mean_alarms"] == ""
            assert r["n_resamples"] == ""
            assert r["exceedance_rate"] == ""
        elif row_type == "summary":
            assert r["method"] in ("z_nominal", "adwin", "page_hinkley")
            assert r["block_length"] == ""
            assert r["matchday"] == ""
            assert r["z"] == ""
            assert r["alarm"] == ""
            assert isinstance(r["n_alarms"], int)
            assert r["n_alarms"] >= 0
            assert isinstance(r["expected_alarms"], float)
            assert r["mean_alarms"] == ""
            assert r["n_resamples"] == ""
            assert r["exceedance_rate"] == ""
            if r["method"] == "z_nominal":
                assert isinstance(r["threshold"], float)
            else:
                assert r["threshold"] == ""
        else:  # overall
            assert r["season"] == ""
            assert r["fit_through"] == ""
            assert r["method"] in ("z_nominal", "adwin", "page_hinkley")
            assert r["block_length"] == ""
            assert r["matchday"] == ""
            assert r["z"] == ""
            assert r["alarm"] == ""
            assert isinstance(r["n_alarms"], int)
            assert r["n_alarms"] >= 0
            assert isinstance(r["expected_alarms"], float)
            assert isinstance(r["mean_alarms"], float)
            assert r["n_resamples"] == ""
            assert r["exceedance_rate"] == ""


def test_synthetic_records_alarms_coherence():
    """Verifica che gli allarmi siano coerenti fra righe matchday, summary e overall."""
    df, schedule = _create_synthetic_residuals_df()
    records = generate_daily_z_test_records(df, schedule)

    # 1. Per ciascuna stagione, n_alarms in summary di z_nominal == somma degli alarm nelle sue 38 matchday
    for s in ("2002-03", "2003-04"):
        matchday_alarms = sum(
            int(r["alarm"])
            for r in records
            if r["row_type"] == "matchday" and r["season"] == s
        )
        summary_row = next(
            r for r in records
            if r["row_type"] == "summary" and r["season"] == s and r["method"] == "z_nominal"
        )
        assert int(summary_row["n_alarms"]) == matchday_alarms

    # 2. Per ciascun metodo, n_alarms in overall == somma di n_alarms nei summary
    for met in ("z_nominal", "adwin", "page_hinkley"):
        sum_alarms = sum(
            int(r["n_alarms"])
            for r in records
            if r["row_type"] == "summary" and r["method"] == met
        )
        overall_row = next(
            r for r in records
            if r["row_type"] == "overall" and r["method"] == met
        )
        assert int(overall_row["n_alarms"]) == sum_alarms
        np.testing.assert_allclose(float(overall_row["mean_alarms"]), sum_alarms / 2.0, atol=1e-12)


# ---------------------------------------------------------------------------
# Test sul CSV Versionato results/us_c5_2_daily_z_test.csv (non saltati in CI)
# ---------------------------------------------------------------------------


def test_versioned_csv_schema_and_columns():
    """Verifica l'esistenza del file CSV e l'esatta presenza delle 14 colonne prescritte."""
    csv_path = _get_csv_path()
    assert csv_path.exists(), f"File non trovato: {csv_path}"

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert tuple(reader.fieldnames or []) == DAILY_Z_TEST_CSV_COLUMNS


def test_versioned_csv_counts_and_structure():
    """Verifica il conteggio righe (722 matchday, 57 summary, 3 overall) e la conformità dello Z-test."""
    csv_path = _get_csv_path()
    with open(csv_path, mode="r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Nessuna presenza della stagione test bloccata 2023-24
    for r in rows:
        assert r["season"] != "2023-24", "Trovata stagione 2023-24 nel CSV!"

    matchday_rows = [r for r in rows if r["row_type"] == "matchday"]
    summary_rows = [r for r in rows if r["row_type"] == "summary"]
    overall_rows = [r for r in rows if r["row_type"] == "overall"]

    # 19 stagioni di validazione x 38 giornate = 722
    assert len(matchday_rows) == 722
    # 19 stagioni x 3 metodi = 57
    assert len(summary_rows) == 57
    # 3 metodi in overall
    assert len(overall_rows) == 3
    # Totale righe dati
    assert len(rows) == 782

    # Verifica proprietà righe matchday
    for r in matchday_rows:
        assert r["method"] == "z_nominal"
        m_day = int(r["matchday"])
        assert 1 <= m_day <= 38
        z_val = float(r["z"])
        thresh = float(r["threshold"])
        alarm_flag = int(r["alarm"])
        assert alarm_flag in (0, 1)
        expected_flag = 1 if abs(z_val) > thresh else 0
        assert alarm_flag == expected_flag


def test_versioned_csv_alarms_match_c5_1():
    """Verifica che i conteggi di ADWIN e Page-Hinkley sulle 19 stagioni coincidano con C5.1."""
    c52_csv = _get_csv_path()
    c51_csv = _get_c51_csv_path()
    assert c51_csv.exists(), f"File C5.1 non trovato: {c51_csv}"

    with open(c51_csv, mode="r", encoding="utf-8") as f:
        c51_rows = list(csv.DictReader(f))
    with open(c52_csv, mode="r", encoding="utf-8") as f:
        c52_rows = list(csv.DictReader(f))

    # Estrazione summary C5.1 su role == validation
    c51_counts = {
        (r["season"], r["detector"]): int(r["n_alarms"])
        for r in c51_rows
        if r["row_type"] == "summary" and r["role"] == "validation"
    }
    assert len(c51_counts) == 38  # 19 stagioni x 2 detector

    # Estrazione summary C5.2 su adwin e page_hinkley
    c52_counts = {
        (r["season"], r["method"]): int(r["n_alarms"])
        for r in c52_rows
        if r["row_type"] == "summary" and r["method"] in ("adwin", "page_hinkley")
    }
    assert len(c52_counts) == 38

    assert c51_counts == c52_counts


def test_versioned_csv_overall_coherence():
    """Verifica che le 3 righe overall abbiano somme e medie coerenti con le 19 righe summary."""
    csv_path = _get_csv_path()
    with open(csv_path, mode="r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    summary_rows = [r for r in rows if r["row_type"] == "summary"]
    overall_rows = [r for r in rows if r["row_type"] == "overall"]

    assert len(overall_rows) == 3
    overall_by_method = {r["method"]: r for r in overall_rows}

    for met in ("z_nominal", "adwin", "page_hinkley"):
        assert met in overall_by_method
        ov = overall_by_method[met]
        sum_alarms = sum(int(r["n_alarms"]) for r in summary_rows if r["method"] == met)
        assert int(ov["n_alarms"]) == sum_alarms
        np.testing.assert_allclose(float(ov["mean_alarms"]), sum_alarms / 19.0, atol=1e-12)
        np.testing.assert_allclose(float(ov["expected_alarms"]), 1.9, atol=1e-12)


def test_figure_file_exists():
    """Verifica che la figura thesis/figures/us_c5_2_daily_z_test.png sia presente e non vuota."""
    png_path = _get_png_path()
    assert png_path.exists(), f"Figura non trovata: {png_path}"
    assert png_path.stat().st_size > 1024, "La figura generata ha dimensione anomala o nulla"


# ---------------------------------------------------------------------------
# Test sui Dati Reali (saltato se non disponibili)
# ---------------------------------------------------------------------------


def test_real_data_recomputation_matches_csv():
    """Ricalcola end-to-end lo Z-test sui dati reali e verifica la coincidenza col CSV salvato."""
    if not _has_real_data():
        pytest.skip("Dati reali non presenti sul filesystem")

    csv_path = _get_csv_path()
    assert csv_path.exists(), f"CSV versionato non trovato: {csv_path}"

    with open(csv_path, mode="r", encoding="utf-8") as f:
        saved_rows = list(csv.DictReader(f))

    # Caricamento e riesecuzione end-to-end
    cfg = read_split_config()
    df_hist = load_by_role("history")
    df_train = load_by_role("training")
    df_val = load_by_role("validation")

    df = pd.concat([df_hist, df_train, df_val], ignore_index=True)
    df = df.sort_values("Date", kind="stable").reset_index(drop=True)

    schedule = derive_fit_schedule(cfg)
    df_residuals = compute_model_residuals(df, schedule, ELO_FITS)

    recomputed_records = generate_daily_z_test_records(df_residuals, schedule)
    assert len(recomputed_records) == len(saved_rows)

    float_cols = {"threshold", "z", "expected_alarms", "mean_alarms"}
    int_cols = {"matchday", "alarm", "n_alarms"}

    for idx, (rec, saved) in enumerate(zip(recomputed_records, saved_rows, strict=True)):
        for col in DAILY_Z_TEST_CSV_COLUMNS:
            val_rec = rec[col]
            val_saved = saved[col]

            if col in float_cols:
                if val_saved == "":
                    assert val_rec == "", f"Riga {idx}, colonna {col}: atteso vuoto ma ottenuto {val_rec}"
                else:
                    f_rec = float(val_rec)
                    f_saved = float(val_saved)
                    np.testing.assert_allclose(
                        f_rec,
                        f_saved,
                        atol=1e-12,
                        rtol=1e-12,
                        err_msg=f"Discrepanza float riga {idx}, colonna {col}",
                    )
            elif col in int_cols:
                if val_saved == "":
                    assert val_rec == "", f"Riga {idx}, colonna {col}: atteso vuoto ma ottenuto {val_rec}"
                else:
                    assert int(val_rec) == int(val_saved), (
                        f"Discrepanza intero riga {idx}, colonna {col}: {val_rec} vs {val_saved}"
                    )
            else:
                assert str(val_rec) == str(val_saved), (
                    f"Discrepanza stringa riga {idx}, colonna {col}: {val_rec!r} vs {val_saved!r}"
                )
