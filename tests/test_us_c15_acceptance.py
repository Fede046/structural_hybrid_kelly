"""Test: verifica di robustezza di Oaxaca-Blinder con e senza la covariata "position"."""

from pathlib import Path

import numpy as np
import pandas as pd

from shk.model.oaxaca_position import CHECK_ARMS, N_CHECK_SEEDS, POSITION_COLUMNS, adjacent_structural_threshold

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "results" / "us_c15_oaxaca_position.csv"


def test_adjacent_structural_threshold_is_an_order_statistic():
    rng = np.random.default_rng(0)
    x = rng.normal(size=(200, 2))
    delta = 0.1 * x[:, 0] + rng.normal(0.0, 0.3, 200)
    thr = adjacent_structural_threshold(x, delta, 30, 5, np.random.default_rng(1))
    assert np.isfinite(thr)
    assert thr == adjacent_structural_threshold(x, delta, 30, 5, np.random.default_rng(1))


def test_versioned_csv_structure_and_findings():
    df = pd.read_csv(CSV_PATH)
    assert tuple(df.columns) == POSITION_COLUMNS
    r2 = df[df["row_type"] == "r2"]
    # Le covariate spiegano poco di δ
    assert r2["value"].median() < 0.1
    sd = df[df["row_type"] == "component_sd"].set_index(["covariates", "component"])["value"]
    assert len(sd) == 8
    # Il totale non dipende dalle covariate; senza "position" le componenti sono meno rumorose
    assert np.isclose(sd["with_position", "total"], sd["without_position", "total"], rtol=1e-9)
    for comp in ("compositional", "interaction"):
        assert sd["without_position", comp] < sd["with_position", comp]
    diag = df[df["row_type"] == "diagnosis"].set_index(["design", "covariates"])
    assert len(diag) == 4
    for design in ("adjacent", "fixed_reference"):
        # Stessi allarmi (l'ANOVA non usa le covariate), meno diagnosi strutturali senza "position"
        assert diag.loc[(design, "with_position"), "n_alarm_dates"] == diag.loc[(design, "without_position"), "n_alarm_dates"]
        assert diag.loc[(design, "without_position"), "share_structural"] < diag.loc[(design, "with_position"), "share_structural"]
    wealth = df[df["row_type"] == "wealth"]
    assert list(wealth["arm"]) == list(CHECK_ARMS)
    assert (wealth["n_seeds"] == N_CHECK_SEEDS).all()
    assert len(df[df["row_type"] == "threshold"]) == 12
