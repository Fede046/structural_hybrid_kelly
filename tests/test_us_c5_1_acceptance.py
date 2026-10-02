"""Test di accettazione per US-C5.1 / Task 28.

Verifica:
- sui test sintetici: schema dei record, matchday == match_index // 10 + 1, stringhe vuote,
  coerenza conteggi allarmi e passaggio parametri da detector_params tramite monkeypatch;
- sul CSV versionato results/us_c5_1_drift_detectors.csv (non saltato in CI):
  schema delle 12 colonne, 44 righe summary, coerenza allarmi/summary, matchday, no test leakage;
- sui dati reali (saltato senza dati grezzi): ricalcolo esatto riga per riga contro il CSV salvato.
"""

import csv
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.data.split import load_by_role, read_split_config
from shk.model.elo_fit import ELO_FITS, derive_fit_schedule
from shk.model.monitoring import (
    DRIFT_DETECTOR_CSV_COLUMNS,
    EXPECTED_MATCHES_PER_SEASON,
    ScenarioSeries,
    build_drift_records,
    extract_scenario_series,
    generate_drift_detector_records,
)
from shk.model.residuals import compute_model_residuals
from shk.stats.drift import detector_params


def _has_real_data() -> bool:
    """Verifica se i dati grezzi sono presenti sul filesystem."""
    return DEFAULT_DATA_DIR.exists() and len(list(DEFAULT_DATA_DIR.glob("*.csv"))) > 0


def _get_csv_path() -> Path:
    """Restituisce il percorso del CSV dei detector."""
    repo_root = Path(__file__).resolve().parents[1]
    return repo_root / "results" / "us_c5_1_drift_detectors.csv"


def _create_synthetic_residuals_df() -> tuple[pd.DataFrame, dict[str, dict[str, list[str]]]]:
    """Crea un DataFrame sintetico di residui per una stagione di training e una di validazione."""
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
        "log_loss": [1.0 + 0.1 * (i % 5) for i in range(n_matches)],
    })

    dates_val = pd.date_range("2002-08-17", periods=n_matches, freq="D")
    df_val = pd.DataFrame({
        "fit_through": ["2000-01"] * n_matches,
        "role": ["validation"] * n_matches,
        "season": ["2002-03"] * n_matches,
        "Date": dates_val,
        "HomeTeam": [f"TeamH_{i % 20}" for i in range(n_matches)],
        "AwayTeam": [f"TeamA_{i % 20}" for i in range(n_matches)],
        "p_home": [0.45] * n_matches,
        "p_draw": [0.28] * n_matches,
        "p_away": [0.27] * n_matches,
        "FTR": ["H"] * n_matches,
        "log_loss": [0.95 + 0.05 * (i % 3) for i in range(n_matches)],
    })

    df = pd.concat([df_tr, df_val], ignore_index=True)
    schedule = {
        "2000-01": {
            "training": ["2000-01"],
            "validation": ["2002-03"],
        }
    }
    return df, schedule


# ---------------------------------------------------------------------------
# Test Sintetici (senza dipendenza da dati grezzi né CSV)
# ---------------------------------------------------------------------------


def test_synthetic_records_schema_and_types():
    """Verifica lo schema dei record generati e la corrispondenza delle 12 colonne."""
    df, schedule = _create_synthetic_residuals_df()
    records = generate_drift_detector_records(df, schedule)

    assert len(records) > 0
    for r in records:
        assert tuple(r.keys()) == DRIFT_DETECTOR_CSV_COLUMNS
        assert r["row_type"] in ("alarm", "summary")
        assert r["detector"] in ("adwin", "page_hinkley")
        assert r["season"] in ("2000-01", "2002-03")
        assert r["role"] in ("training", "validation")
        assert r["fit_through"] == "2000-01"


def test_synthetic_records_matchday_and_blank_fields():
    """Verifica che matchday == match_index // 10 + 1 e che i campi non applicabili siano vuoti."""
    df, schedule = _create_synthetic_residuals_df()
    records = generate_drift_detector_records(df, schedule)

    for r in records:
        if r["row_type"] == "alarm":
            assert isinstance(r["match_index"], int)
            assert isinstance(r["matchday"], int)
            assert isinstance(r["alarm_number"], int)
            assert r["matchday"] == r["match_index"] // 10 + 1
            assert r["date"] != ""
            assert r["home_team"] != ""
            assert r["away_team"] != ""
            assert r["n_alarms"] == ""
        else:  # summary
            assert r["alarm_number"] == ""
            assert r["match_index"] == ""
            assert r["matchday"] == ""
            assert r["date"] == ""
            assert r["home_team"] == ""
            assert r["away_team"] == ""
            assert isinstance(r["n_alarms"], int)
            assert r["n_alarms"] >= 0


def test_synthetic_records_n_alarms_coherence():
    """Verifica che n_alarms nella riga summary coincida esattamente con il conteggio delle righe alarm."""
    df, schedule = _create_synthetic_residuals_df()
    records = generate_drift_detector_records(df, schedule)

    for season in ("2000-01", "2002-03"):
        for det in ("adwin", "page_hinkley"):
            alarms = [
                r for r in records
                if r["row_type"] == "alarm" and r["season"] == season and r["detector"] == det
            ]
            summary = [
                r for r in records
                if r["row_type"] == "summary" and r["season"] == season and r["detector"] == det
            ]
            assert len(summary) == 1
            assert summary[0]["n_alarms"] == len(alarms)


def test_synthetic_records_uses_detector_params(monkeypatch):
    """Verifica che i parametri passati ai detector siano esattamente quelli di detector_params."""
    df, schedule = _create_synthetic_residuals_df()
    calls: list[tuple[str, dict[str, Any]]] = []

    import shk.model.monitoring

    orig_run = shk.model.monitoring.run_drift_detector

    def spy_run(series, detector, params):
        calls.append((detector, dict(params) if params is not None else {}))
        return orig_run(series, detector, params)

    monkeypatch.setattr(shk.model.monitoring, "run_drift_detector", spy_run)

    _ = generate_drift_detector_records(df, schedule)

    assert len(calls) > 0
    for det, p in calls:
        expected_p = detector_params(det)
        assert p == expected_p


# ---------------------------------------------------------------------------
# Test sul CSV Versionato results/us_c5_1_drift_detectors.csv (non saltati in CI)
# ---------------------------------------------------------------------------


def test_versioned_csv_schema_and_columns():
    """Verifica le 12 colonne del file CSV versionato."""
    csv_path = _get_csv_path()
    assert csv_path.exists(), f"CSV file not found: {csv_path}"

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert tuple(reader.fieldnames or []) == DRIFT_DETECTOR_CSV_COLUMNS


def test_versioned_csv_summary_counts_and_structure():
    """Verifica esattamente 44 righe summary (22 stagioni x 2 detector) nel CSV versionato."""
    csv_path = _get_csv_path()
    with open(csv_path, mode="r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    summary_rows = [r for r in rows if r["row_type"] == "summary"]
    assert len(summary_rows) == 44

    # 22 stagioni uniche
    seasons = {r["season"] for r in summary_rows}
    assert len(seasons) == 22

    # Per ciascuna stagione devono esserci esattamente 2 righe summary (adwin e page_hinkley)
    for s in seasons:
        s_dets = {r["detector"] for r in summary_rows if r["season"] == s}
        assert s_dets == {"adwin", "page_hinkley"}


def test_versioned_csv_alarm_summary_coherence_and_matchday():
    """Verifica coerenza allarmi, matchday = match_index // 10 + 1 e no leakage del test."""
    csv_path = _get_csv_path()
    with open(csv_path, mode="r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    for r in rows:
        assert r["season"] != "2023-24", "Found test season 2023-24 in CSV!"
        if r["row_type"] == "alarm":
            m_idx = int(r["match_index"])
            m_day = int(r["matchday"])
            assert m_day == m_idx // 10 + 1
            assert 0 <= m_idx < 380
            assert 1 <= m_day <= 38
            assert r["date"] != ""
            assert r["home_team"] != ""
            assert r["away_team"] != ""
            assert r["n_alarms"] == ""
        else:
            assert r["row_type"] == "summary"
            n_al = int(r["n_alarms"])
            assert n_al >= 0

    # Coerenza conteggi tra alarm e summary
    summary_rows = [r for r in rows if r["row_type"] == "summary"]
    for s_row in summary_rows:
        s = s_row["season"]
        d = s_row["detector"]
        n_expected = int(s_row["n_alarms"])
        n_actual = sum(
            1 for r in rows
            if r["row_type"] == "alarm" and r["season"] == s and r["detector"] == d
        )
        assert n_actual == n_expected


# ---------------------------------------------------------------------------
# Test sui Dati Reali (saltati se non presenti)
# ---------------------------------------------------------------------------


def test_real_data_recomputation_matches_csv():
    """Verifica che il ricalcolo dai dati grezzi coincida esattamente riga per riga con il CSV."""
    if not _has_real_data():
        pytest.skip("Real data in data/raw/E0 not available")

    csv_path = _get_csv_path()
    assert csv_path.exists(), f"CSV file not found: {csv_path}"

    with open(csv_path, mode="r", encoding="utf-8") as f:
        csv_rows = list(csv.DictReader(f))

    cfg = read_split_config()
    df_hist = load_by_role("history")
    df_train = load_by_role("training")
    df_val = load_by_role("validation")

    df = pd.concat([df_hist, df_train, df_val], ignore_index=True)
    df = df.sort_values("Date", kind="stable").reset_index(drop=True)

    schedule = derive_fit_schedule(cfg)
    df_residuals = compute_model_residuals(df, schedule, ELO_FITS)

    recomputed_records = generate_drift_detector_records(df_residuals, schedule)

    assert len(recomputed_records) == len(csv_rows)
    for i, (rec, csv_r) in enumerate(zip(recomputed_records, csv_rows, strict=True)):
        for col in DRIFT_DETECTOR_CSV_COLUMNS:
            val_rec = str(rec[col])
            val_csv = str(csv_r[col])
            assert val_rec == val_csv, (
                f"Mismatch at row {i}, column '{col}': recomputed '{val_rec}' vs csv '{val_csv}'"
            )
