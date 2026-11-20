"""Test: la versione definitiva dello schema (shk.model.main_version "F", us_c33, us_c35, us_c36, us_c30)."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shk.model.main_version import STRUCTURAL_LAMBDA, TEST_ARMS
from shk.model.timing_placebo import LEVEL_BASE, LEVEL_REDUCED, LEVEL_ZERO, levels_from_lambda

RESULTS = Path(__file__).resolve().parents[1] / "results"
N_SEASONS = 19
KAPPA_LAMBDA = 0.1875


def _needs(name: str):
    return pytest.mark.skipif(not (RESULTS / name).exists(), reason=f"{name} non ancora generato")


def test_levels_with_floor():
    lam = np.array([0.25, KAPPA_LAMBDA, STRUCTURAL_LAMBDA, 0.25])
    assert list(levels_from_lambda(lam, 0.25, 0.75, floor=STRUCTURAL_LAMBDA)) == [
        LEVEL_BASE, LEVEL_REDUCED, LEVEL_ZERO, LEVEL_BASE]
    with pytest.raises(ValueError):
        levels_from_lambda(lam, 0.25, 0.75)


def test_final_version_is_tested_on_2023_24():
    assert "F" in TEST_ARMS and STRUCTURAL_LAMBDA == pytest.approx(0.10)


@_needs("us_c33_main_alarm_trace.csv")
def test_trace_lambda_follows_the_daily_diagnosis():
    t = pd.read_csv(RESULTS / "us_c33_main_alarm_trace.csv")
    expected = t["diagnosis"].map({"none": 0.25, "compositional": KAPPA_LAMBDA, "structural": STRUCTURAL_LAMBDA})
    assert np.allclose(t["lambda"], expected, rtol=0, atol=1e-12)
    assert t["season"].nunique() == N_SEASONS


@_needs("us_c35_final_version_seasons.csv")
def test_us_c35_reproduces_the_previous_versions():
    mine = pd.read_csv(RESULTS / "us_c35_final_version_seasons.csv").set_index(["config", "agent", "season"])
    c29 = pd.read_csv(RESULTS / "us_c29_main_rules_seasons.csv").set_index(["config", "agent", "season"])
    for agent in ("M", "B_0.25"):
        x = mine.xs(agent, level="agent")["log_wealth"]
        assert np.allclose(x, c29.xs(agent, level="agent")["log_wealth"].loc[x.index], rtol=0, atol=1e-9), agent
    g = mine.xs("gbp_0.01", level="config")["log_wealth"]
    # Con λ = 0 dopo un errore strutturale la regola di F coincide con M_clear
    assert np.allclose(g.xs("F_0", level="agent"), g.xs("M_clear", level="agent"), rtol=0, atol=1e-12)
    summary = pd.read_csv(RESULTS / "us_c35_final_version_summary.csv")
    s = summary[summary["config"] == "gbp_0.01"].set_index("agent")
    # La versione definitiva riduce la puntata in poche giornate e resta vicina al quarto di Kelly
    assert s.loc["F", "share_days_reduced"] < 0.10
    assert abs(np.log(s.loc["F", "typical_capital"] / s.loc["B_0.25", "typical_capital"])) < 0.02
    assert s.loc["F_season", "typical_capital"] > s.loc["F", "typical_capital"]
    placebo = pd.read_csv(RESULTS / "us_c35_final_version_placebo.csv")
    gap = placebo[(placebo["row_type"] == "expected_delta") & (placebo["placebo"] == "cross_season")].iloc[0]
    # Le giornate con la puntata ridotta sono quelle in cui il modello è più lontano dal mercato
    assert gap["observed"] < 0 and gap["p_value"] < 0.01


@_needs("us_c36_final_simulation.csv")
def test_us_c36_reproduces_us_c25():
    mine = pd.read_csv(RESULTS / "us_c36_final_simulation.csv")
    cap = mine[mine["row_type"] == "capital"].set_index(["scenario", "agent"])["typical_capital"]
    c25 = pd.read_csv(RESULTS / "us_c25_edge_simulation.csv")
    c25 = c25[c25["row_type"] == "capital"].set_index(["scenario", "agent"])["typical_capital"]
    for ours, theirs in (("stop_season", "C3_ref_stop_season_dx"), ("clear_zero", "C3_ref_season_dx"),
                         ("quarter_kelly", "quarter_kelly"), ("full_kelly", "full_kelly")):
        for scenario in cap.xs(ours, level="agent").index:
            assert cap[(scenario, ours)] == pytest.approx(c25[(scenario, theirs)], rel=1e-9), (ours, scenario)
    # Quando il vantaggio si rovescia la versione definitiva fa meglio del quarto di Kelly e della
    # frazione fissa di pari esposizione; quando nulla cambia costa poco
    assert cap[("edge_reverses", "F")] > cap[("edge_reverses", "constant:F")] > cap[("edge_reverses", "quarter_kelly")]
    assert cap[("stable_edge", "F")] > 0.99 * cap[("stable_edge", "quarter_kelly")]


@_needs("us_c30_main_kellybench_summary.csv")
def test_us_c30_final_version_never_alarms_in_the_true_season():
    m = pd.read_csv(RESULTS / "us_c30_main_kellybench_summary.csv").set_index(["config", "agent"])
    if ("gbp_0.01", "F") not in m.index:
        pytest.skip("us_c30 non ancora rieseguito con la versione definitiva")
    assert m.loc[("gbp_0.01", "F"), "observed_log_wealth"] == pytest.approx(
        m.loc[("gbp_0.01", "B_0.25"), "observed_log_wealth"])
