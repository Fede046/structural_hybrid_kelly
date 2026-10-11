"""Test di known_scenarios.py e di accettazione di T48 (US-C7.3, parte 2)."""

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.model.covariate_inspection import derive_specification
from shk.model.known_scenarios import (
    KNOWN_SCENARIOS_CSV_COLUMNS,
    add_no_objective_flag,
    decomposition_absent_in_a_batch,
    decomposition_batch,
    evaluate_known_scenarios,
    suspension_split,
)
from shk.model.module2_data import build_module2_frame
from shk.model.residuals import load_model_residuals
from shk.stats.oaxaca import oaxaca_blinder
from shk.stats.oaxaca_synthetic import SEED_S8

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "results" / "us_c7_3b_known_scenarios.csv"
PNG_PATH = REPO_ROOT / "thesis" / "figures" / "us_c7_3b_known_scenarios.png"


def _has_real_data() -> bool:
    return DEFAULT_DATA_DIR.is_dir() and any(DEFAULT_DATA_DIR.glob("*.csv"))


def _groups(seed: int):
    rng = np.random.default_rng(seed)
    xa = rng.normal(size=(1, 120, 3))
    xb = rng.normal(0.3, 1.0, size=(1, 90, 3))
    ya = xa[0] @ [0.1, -0.2, 0.05] + rng.normal(size=120)
    flag = (rng.random(90) < 0.3).astype(float)
    yb = xb[0] @ [0.2, -0.1, 0.05] + 0.4 * flag + rng.normal(size=90)
    return xa, ya[None], xb, flag[None], yb[None]


def test_decomposition_batch_matches_oaxaca():
    xa, ya, xb, _, yb = _groups(1)
    q, valid = decomposition_batch(xa, ya, xb, yb)
    res = oaxaca_blinder(xa[0], ya[0], xb[0], yb[0])
    assert valid[0]
    for name in ("total", "compositional", "structural", "interaction"):
        assert math.isclose(q[name][0], getattr(res, name), rel_tol=1e-10, abs_tol=1e-12)
    assert math.isclose(q["structural_share"][0], res.structural_share, rel_tol=1e-10)
    assert math.isclose(q["explained_b"][0], res.twofold["beta_b"].explained, rel_tol=1e-10, abs_tol=1e-12)


def test_flag_absent_in_a_assumptions():
    """S e C+I non dipendono dall'ipotesi su β_A,flag; (a) e (e) spostano il flag fra I e C."""
    xa, ya, xb, flag, yb = _groups(2)
    qa, _ = decomposition_absent_in_a_batch(xa, ya, xb, flag, yb, assume_equal=False)
    qe, _ = decomposition_absent_in_a_batch(xa, ya, xb, flag, yb, assume_equal=True)
    for name in ("total", "structural", "explained_b", "structural_share_b"):
        assert qa[name][0] == qe[name][0]
    for q in (qa, qe):
        assert abs(q["compositional"][0] + q["structural"][0] + q["interaction"][0] - q["total"][0]) <= 1e-12
        assert abs(q["explained_b"][0] + q["structural"][0] - q["total"][0]) <= 1e-12
    # Differenza fra (e) e (a): β_B,flag · x̄_B,flag passa dall'interazione alla composizione
    design_b = np.column_stack([np.ones(90), xb[0], flag[0]])
    beta_b = np.linalg.lstsq(design_b, yb[0], rcond=None)[0]
    shift = beta_b[-1] * flag[0].mean()
    assert math.isclose(qe["compositional"][0] - qa["compositional"][0], shift, rel_tol=1e-8)
    assert math.isclose(qa["interaction"][0] - qe["interaction"][0], shift, rel_tol=1e-8)


def test_suspension_split_longest_gap():
    dates = pd.to_datetime(["2020-01-01", "2020-01-05", "2020-03-09", "2020-06-17", "2020-06-20"])
    frame = pd.DataFrame({"season": "2019-20", "Date": dates})
    assert suspension_split(frame) == (pd.Timestamp("2020-03-09"), pd.Timestamp("2020-06-17"))


def test_csv_structure_sums_and_figure():
    df = pd.read_csv(CSV_PATH)
    assert tuple(df.columns) == KNOWN_SCENARIOS_CSV_COLUMNS
    assert set(df["scenario"]) == {"1_transition", "2_covid", "2_covid_detail", "3_end_season"}
    pt = df[df["quantity"].isin(["total", "compositional", "structural", "interaction", "explained_b"])]
    wide = pt.pivot_table(index=["scenario", "season_a", "season_b", "window", "version"], columns="quantity",
                          values="estimate", dropna=False).dropna(subset=["total"])
    assert ((wide["compositional"] + wide["structural"] + wide["interaction"] - wide["total"]).abs() <= 1e-12).all()
    assert ((wide["explained_b"] + wide["structural"] - wide["total"]).abs() <= 1e-12).all()
    assert PNG_PATH.is_file() and PNG_PATH.stat().st_size > 0


def test_recalculation_from_real_data_matches_csv():
    if not _has_real_data():
        pytest.skip(f"Real data missing: no CSV in {DEFAULT_DATA_DIR}")
    data = load_model_residuals()
    frame = add_no_objective_flag(build_module2_frame(data), data.df)
    spec = derive_specification(frame[frame["role"] == "training"])
    records = evaluate_known_scenarios(frame, spec.covariates, seed=SEED_S8)
    df = pd.read_csv(CSV_PATH, dtype=str, keep_default_na=False)
    assert len(df) == len(records)
    for (_, row), rec in zip(df.iterrows(), records):
        for col in KNOWN_SCENARIOS_CSV_COLUMNS:
            val = rec[col]
            if isinstance(val, float):
                if math.isnan(val):
                    assert row[col] in ("", "nan"), col
                else:
                    assert math.isclose(float(row[col]), val, rel_tol=1e-12, abs_tol=1e-15), col
            else:
                assert row[col] == str(val), col
