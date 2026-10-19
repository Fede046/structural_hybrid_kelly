"""Test di covariate_inspection.py e di accettazione della specificazione delle covariate."""

import csv
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from statsmodels.stats.outliers_influence import variance_inflation_factor

from shk.data.loading import DEFAULT_DATA_DIR
from shk.model.covariate_inspection import (
    ANOVA_COVARIATES,
    COVARIATES_CSV_COLUMNS,
    VIF_MAX,
    apply_flag_rule,
    cohen_d_and_ovl,
    derive_specification,
    evaluate_covariates,
    quintile_labels,
    spawn_t46_generators,
    variance_inflation_factors,
    vif_elimination,
)
from shk.model.module2_data import build_module2_frame, select_triple_2000_01
from shk.model.residuals import load_model_residuals
from shk.stats.oaxaca_synthetic import SEED_S8

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "results" / "us_c7_2_covariates.csv"
PNG_PATH = REPO_ROOT / "thesis" / "figures" / "us_c7_2_covariates.png"


def _has_real_data() -> bool:
    return DEFAULT_DATA_DIR.is_dir() and any(DEFAULT_DATA_DIR.glob("*.csv"))


def _read_csv() -> list[dict[str, str]]:
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert tuple(reader.fieldnames or ()) == COVARIATES_CSV_COLUMNS
        return list(reader)


def test_vif_matches_statsmodels():
    """VIF a mano = statsmodels variance_inflation_factor con costante, entro 1e-10."""
    rng = np.random.default_rng(1)
    x = rng.normal(size=(300, 4))
    x[:, 3] = x[:, 0] + 0.5 * x[:, 1] + 0.1 * rng.normal(size=300)
    ours = variance_inflation_factors(x)
    exog = np.column_stack([np.ones(300), x])
    ref = [variance_inflation_factor(exog, j + 1) for j in range(4)]
    np.testing.assert_allclose(ours, ref, rtol=1e-10)


def test_vif_elimination_removes_max_until_below_threshold():
    """Si toglie una alla volta la covariata col VIF massimo, poi tutti i VIF sono <= 5."""
    rng = np.random.default_rng(2)
    n = 500
    a = rng.normal(size=n)
    frame = pd.DataFrame({
        "a": a, "b": a + 0.05 * rng.normal(size=n), "c": rng.normal(size=n), "d": a + 0.2 * rng.normal(size=n),
    })
    steps = vif_elimination(frame, ("a", "b", "c", "d"))
    for step in steps[:-1]:
        assert step.removed == max(step.vifs, key=step.vifs.get)
        assert step.vifs[step.removed] > VIF_MAX
    assert steps[-1].removed is None
    assert max(steps[-1].vifs.values()) <= VIF_MAX
    assert "c" in steps[-1].vifs


def test_flag_rule():
    """Flag distinti solo se entrambi hanno in media almeno 30 partite per stagione."""
    seasons = np.repeat(["s1", "s2", "s3"], 380)
    frame = pd.DataFrame({"season": seasons, "flag_new": 0, "flag_returning": 0})
    frame.loc[frame.index % 10 == 0, "flag_new"] = 1          # 38 per stagione
    frame.loc[frame.index % 10 == 1, "flag_returning"] = 1    # 38 per stagione
    assert apply_flag_rule(frame).flags == ("flag_new", "flag_returning")
    frame.loc[frame.index % 20 == 0, "flag_new"] = 0          # 19 per stagione
    res = apply_flag_rule(frame)
    assert res.flags == ("flag_promoted",)
    assert math.isclose(res.mean_new_per_season, 19.0)


def test_quintiles_and_cohen_d():
    """Quintili con 5 gruppi uguali e OVL = 2 Φ(−|d|/2)."""
    labels = quintile_labels(np.arange(100, dtype=float))
    assert np.bincount(labels).tolist() == [20] * 5
    y = np.r_[np.zeros(50), np.ones(50)]
    flag = np.r_[np.zeros(50, dtype=int), np.ones(50, dtype=int)]
    y = y + np.tile([0.1, -0.1], 50)
    d, ovl = cohen_d_and_ovl(y, flag)
    assert d > 0 and 0.0 < ovl < 1.0


def test_csv_structure_and_specification_rows():
    """Il CSV ha tutte le tabelle e la specificazione come righe; la figura esiste."""
    rows = _read_csv()
    types = {r["row_type"] for r in rows}
    for t in ("triple_2000_01", "delta_season", "flag_rule", "vif", "specification", "distribution",
              "cell_count", "window_count", "elo_window_sd", "correlation", "vif_full", "vif_final", "anova"):
        assert t in types, t
    spec = [r for r in rows if r["row_type"] == "specification"]
    assert len(spec) == 8
    assert sum(r["included"] == "True" for r in spec) >= 1
    anova = [r for r in rows if r["row_type"] == "anova"]
    assert {(r["dataset"], r["covariate"]) for r in anova} == {
        (d, c) for d in ("training", "validation") for c in ANOVA_COVARIATES
    }
    assert PNG_PATH.is_file() and PNG_PATH.stat().st_size > 0


def test_spawn_t46_generators_scheme():
    rngs = spawn_t46_generators(SEED_S8)
    child = np.random.SeedSequence(SEED_S8).spawn(5)[1].spawn(2)[1].spawn(len(ANOVA_COVARIATES))[3]
    assert rngs[1][3].integers(0, 2**62) == np.random.default_rng(child).integers(0, 2**62)


@pytest.fixture(scope="module")
def real_frame():
    if not _has_real_data():
        pytest.skip(f"Real data missing: no CSV in {DEFAULT_DATA_DIR}")
    data = load_model_residuals()
    return build_module2_frame(data, triple_2000_01=select_triple_2000_01(data.df).source)


def test_specification_derives_mechanically_from_rules(real_frame):
    """La specificazione del CSV coincide con le regole riapplicate al training (dati reali)."""
    spec = derive_specification(real_frame[real_frame["role"] == "training"])
    rows = [r for r in _read_csv() if r["row_type"] == "specification"]
    included = {r["covariate"] for r in rows if r["included"] == "True"}
    assert included == set(spec.covariates)
    for r in rows:
        if r["included"] == "False":
            assert r["reason"] == spec.excluded[r["covariate"]]


def test_csv_recomputed_from_real_data(real_frame):
    """I record di evaluate_covariates coincidono col CSV (float entro 1e-12)."""
    _, records = evaluate_covariates(real_frame, seed=SEED_S8)
    rows = [r for r in _read_csv() if r["row_type"] not in ("triple_2000_01", "delta_season")]
    assert len(rows) == len(records)
    for row, rec in zip(rows, records):
        for col in COVARIATES_CSV_COLUMNS:
            if isinstance(rec[col], float):
                assert math.isclose(float(row[col]), rec[col], rel_tol=1e-12, abs_tol=1e-15), col
            else:
                assert row[col] == str(rec[col]), col
