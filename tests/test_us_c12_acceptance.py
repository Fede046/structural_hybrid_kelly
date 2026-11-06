"""Test: verifica dell'allarme ANOVA dello schema (frequenza sui dati reali e potenza)."""

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.model.frozen_params import load_frozen_params
from shk.model.module2_data import build_module2_frame
from shk.model.residuals import load_model_residuals
from shk.model.scheme_power import (
    POWER_COLUMNS,
    SCENARIOS,
    alarm_after_break,
    alarm_flags,
    inject_change,
    power_records,
)
from shk.model.scheme_run import scheme_thresholds

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "results" / "us_c12_anova_power.csv"


def _days(n_dates: int, per_date: int) -> np.ndarray:
    base = np.datetime64("2010-08-14") + np.arange(n_dates) * np.timedelta64(7, "D")
    return np.repeat(base, per_date).astype("datetime64[ns]")


def test_inject_change_moves_mean_and_scales_variance():
    y = np.random.default_rng(0).normal(0.0, 0.2, 300)
    z = inject_change(y, 100, -0.1, 4.0)
    np.testing.assert_array_equal(z[:100], y[:100])
    assert math.isclose(z[100:].mean(), y[100:].mean() - 0.1, abs_tol=1e-12)
    assert math.isclose(z[100:].std(), 2.0 * y[100:].std(), rel_tol=1e-12)


def test_alarm_flags_and_alarm_after_break_on_synthetic_series():
    rng = np.random.default_rng(1)
    dates = _days(40, 10)
    y = rng.normal(0.0, 0.2, 400)
    flags = alarm_flags(y, dates, 20, 4.0, 4.0)
    # Le date con almeno 2W = 40 partite anteriori sono 36 su 40
    assert flags.shape == (36, 2)
    assert not alarm_after_break(y, dates, 20, 1e9, 1e9, start=200)
    assert alarm_after_break(inject_change(y, 200, -1.0, 1.0), dates, 20, 4.0, 4.0, start=200)


def test_versioned_csv_structure_and_findings():
    df = pd.read_csv(CSV_PATH)
    assert tuple(df.columns) == POWER_COLUMNS
    rate = df[df["row_type"] == "rate"]
    assert len(rate) == 19 and len(df[df["row_type"] == "rate_log_loss"]) == 19
    assert len(df[df["row_type"] == "mde"]) == 3
    power = df[df["row_type"] == "power"].set_index("scenario")["share_seasons_with_alarm"]
    assert list(power.index) == [s.name for s in SCENARIOS]
    # Più grande il peggioramento della media, più stagioni con allarme
    assert power["none"] <= power["mean_-0.05"] <= power["mean_-0.10"] <= power["mean_-0.20"]
    assert power["mean_-0.20"] >= 0.9
    # Sui dati reali la quota di date con allarme è vicina al livello del caso (5%)
    assert 0.02 < rate["share_alarm"].mean() < 0.08


@pytest.mark.skipif(not (DEFAULT_DATA_DIR.is_dir() and any(DEFAULT_DATA_DIR.glob("*.csv"))),
                    reason=f"Real data missing: no CSV in {DEFAULT_DATA_DIR}")
def test_recomputation_matches_versioned_csv():
    params = load_frozen_params()
    frame = build_module2_frame(load_model_residuals())
    thresholds = scheme_thresholds(frame[frame["role"] == "training"], params)
    fresh = pd.DataFrame(power_records(frame, params, thresholds))[list(POWER_COLUMNS)]
    saved = pd.read_csv(CSV_PATH)
    numeric = ["share_mean_alarm", "share_dispersion_alarm", "share_alarm", "share_seasons_with_alarm",
               "min_detectable_worsening", "mean_threshold", "dispersion_threshold"]
    for col in numeric:
        np.testing.assert_allclose(pd.to_numeric(fresh[col], errors="coerce").to_numpy(dtype=float),
                                   saved[col].to_numpy(dtype=float), rtol=1e-12, atol=0.0, equal_nan=True)
