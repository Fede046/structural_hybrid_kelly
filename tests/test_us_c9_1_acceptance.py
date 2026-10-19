"""Test di accettazione su dati reali: anti-leakage, DC_FITS, CSV e figura."""

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.data.split import read_split_config
from shk.model.dixon_coles import (
    DC_FITS,
    SIGMA_GRID,
    XI_GRID,
    DixonColesForecaster,
    provider_leakage_check,
    t59_sequences,
)
from shk.model.dixon_coles_calibration import LEAKAGE_SAMPLE, load_frame

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "results" / "us_c9_1_dixon_coles.csv"
PNG_PATH = REPO_ROOT / "thesis" / "figures" / "us_c9_1_dixon_coles.png"


def _has_real_data() -> bool:
    return DEFAULT_DATA_DIR.is_dir() and any(DEFAULT_DATA_DIR.glob("*.csv"))


@pytest.fixture(scope="module")
def frame():
    if not _has_real_data():
        pytest.skip(f"Real data missing: no CSV in {DEFAULT_DATA_DIR}")
    return load_frame()


class _NonStrictForecaster(DixonColesForecaster):
    """Mutante: storia con Date <= data di previsione (anteriorità non stretta)."""

    def history_rows(self, decision_day: int) -> np.ndarray:
        return super().history_rows(decision_day + 1)


def test_frame_excludes_test_set(frame):
    """Il DataFrame del Dixon-Coles walk-forward contiene storia, training e validazione, mai il test."""
    df, _ = frame
    assert not set(df["season"]) & set(read_split_config().test)


def test_anti_leakage_on_provider_sample_and_mutant(frame):
    """500 partite di training e validazione dal fornitore: 0 violazioni; il mutante viene rilevato."""
    df, schedule = frame
    seasons = sorted({s for v in schedule.values() for s in v["training"] + v["validation"]})
    params = DC_FITS["2020-21"]
    check = provider_leakage_check(DixonColesForecaster(df, params.xi, params.sigma), seasons, LEAKAGE_SAMPLE,
                                   np.random.default_rng(t59_sequences()[1]))
    assert check.n_checked == LEAKAGE_SAMPLE >= 500
    assert check.n_violations == 0
    assert check.n_outside_provider == 0
    mutant = provider_leakage_check(_NonStrictForecaster(df, params.xi, params.sigma), seasons, LEAKAGE_SAMPLE,
                                    np.random.default_rng(t59_sequences()[1]))
    assert mutant.n_violations == LEAKAGE_SAMPLE


def test_csv_matches_frozen_fits_and_reports_convergence():
    """La scelta della calibrazione nel CSV coincide con DC_FITS; mancate convergenze contate."""
    if not CSV_PATH.exists():
        pytest.skip(f"Missing {CSV_PATH}: run scripts/us_c9_1_dixon_coles.py")
    df = pd.read_csv(CSV_PATH)
    cal = df[df["row_type"] == "calibration"]
    assert len(cal) == len(DC_FITS) * len(XI_GRID) * len(SIGMA_GRID)
    assert all(math.isfinite(p.sigma) for p in DC_FITS.values())
    chosen = cal[cal["chosen"].astype(str) == "True"]
    assert {r.fit: (r.xi, r.sigma) for r in chosen.itertuples()} == {f: (p.xi, p.sigma) for f, p in DC_FITS.items()}
    fits = df[df["row_type"].isin(["calibration", "validation_fits"])]
    assert fits["n_not_converged"].notna().all()
    assert (fits["n_not_converged"] >= 0).all()
    check = df[df["row_type"] == "check"].iloc[0]
    assert int(check["n"]) >= 500 and int(check["n_violations"]) == 0
    val = df[(df["row_type"] == "validation") & (df["season"] != "pooled")]
    assert val["season"].nunique() == 19
    assert "2023-24" not in set(df["season"].dropna())
    assert math.isfinite(float(df[(df["row_type"] == "validation") & (df["season"] == "pooled")
                                  & (df["model"] == "dixon_coles") & df["method"].isna()]["log_loss"].iloc[0]))


def test_figure_exists():
    """La figura esiste."""
    if not CSV_PATH.exists():
        pytest.skip(f"Missing {CSV_PATH}: run scripts/us_c9_1_dixon_coles.py")
    assert PNG_PATH.exists() and PNG_PATH.stat().st_size > 0
