"""Test: diagnosi di Blinder-Oaxaca a due termini sulle 19 stagioni vere (us_c27), appaiata con us_c13 e us_c26."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shk.model.season_thresholds import PER_DATE_ARMS, SEASON_ARMS
from shk.model.timing_placebo import PLACEBOS, RESPONSES
from shk.model.two_fold_diagnosis import DX_ARMS, RUN_ARMS

RESULTS = Path(__file__).resolve().parents[1] / "results"
N_SEASONS, N_CONFIGS = 19, 3


def _csv(name: str) -> pd.DataFrame:
    return pd.read_csv(RESULTS / f"us_c27_two_fold_{name}.csv")


pytestmark = pytest.mark.skipif(not (RESULTS / "us_c27_two_fold_summary.csv").exists(), reason="us_c27 non ancora eseguito")


def test_structure():
    assert len(_csv("thresholds")) == 3
    assert list(_csv("diagnosis")["alarm"]) == ["none", "mean_only", "dispersion_only", "both"]
    assert len(_csv("decomposition")) == N_SEASONS * 2 * 4
    assert len(_csv("components")) == 8
    assert len(_csv("seasons")) == N_SEASONS * N_CONFIGS * len(RUN_ARMS)
    assert len(_csv("summary")) == N_CONFIGS * len(RUN_ARMS)
    assert len(_csv("placebo")) == len(DX_ARMS) * (len(PLACEBOS) * (1 + len(RESPONSES)) + 1)


def test_other_versions_match_their_experiments():
    """Stesse soglie e stesse stagioni vere: le versioni con la diagnosi a tre termini coincidono con us_c13 e us_c26."""
    mine = _csv("seasons").set_index(["config", "agent", "season"])["log_wealth"]
    ref = pd.read_csv(RESULTS / "us_c13_scheme_reference_summary.csv")
    ref = ref[ref["row_type"] == "summary"].set_index(["config", "agent", "season"])["observed_log_wealth"]
    c26 = pd.read_csv(RESULTS / "us_c26_season_thresholds_seasons.csv").set_index(["config", "agent", "season"])["log_wealth"]
    for agent in ("B_0.25",) + PER_DATE_ARMS:
        ours = mine[mine.index.get_level_values("agent") == agent]
        assert np.allclose(ours, ref.loc[ours.index], rtol=0, atol=1e-9), agent
    for agent in SEASON_ARMS:
        ours = mine[mine.index.get_level_values("agent") == agent]
        assert np.allclose(ours, c26.loc[ours.index], rtol=0, atol=1e-9), agent


def test_decomposition_adds_up():
    dec = _csv("decomposition").pivot(index=["season", "response"], columns="component", values="value")
    assert np.allclose(dec["total"], dec["composition"] + dec["structure"] + dec["interaction"], atol=1e-12)
    rows = _csv("decomposition")
    assert (rows["low"] <= rows["high"]).all()


def test_findings():
    thr = _csv("thresholds")
    # Le covariate spiegano la dispersione di δ molto più della sua media
    assert (thr["r2_dispersion"] > 3 * thr["r2_mean"]).all()
    # Nella scomposizione a tre termini su 40 partite struttura e interazione sono grandi e opposte: la
    # struttura, su cui decideva la diagnosi, quasi non segue lo scarto che deve spiegare
    comp = _csv("components").set_index("statistic")["value"]
    assert comp["sd_structure"] > 5 * comp["sd_total"]
    assert comp["corr_structure_interaction"] < -0.95
    assert comp["corr_structure_total"] < 0.3 < 0.8 < comp["corr_structure_plus_interaction_total"]
    table = _csv("diagnosis").set_index("alarm")
    # Senza allarme la diagnosi a tre termini direbbe «strutturale» in una giornata su tre, quella a due
    # termini resta al livello nominale
    assert table.loc["none", "share_structural_three_fold"] > 0.25
    assert table.loc["none", "share_structural_two_fold"] < 0.08
    # Con l'allarme sulla media il peggioramento non è quasi mai spiegato dal tipo di partite; con
    # l'allarme sulla dispersione lo è in una parte dei casi
    assert table.loc["mean_only", "share_structural_two_fold"] > 0.7
    assert 0.4 < table.loc["dispersion_only", "share_structural_two_fold"] < table.loc["mean_only", "share_structural_two_fold"]
    # L'aumento di dispersione ha una parte strutturale distinguibile da zero nelle stagioni lontane
    # dalla calibrazione, non in quelle vicine
    dec = _csv("decomposition")
    s = dec[(dec["response"] == "dispersion") & (dec["component"] == "structure")].set_index("season")
    significant = set(s[s["low"] > 0].index)
    assert "2009-10" in significant and {"2016-17", "2017-18", "2018-19", "2019-20"} <= significant
    assert not significant & {"2002-03", "2003-04", "2004-05", "2021-22", "2022-23"}
    assert len(significant) >= 7
    # Il capitale non cambia quadro: come con l'altra diagnosi, non supera un calendario di pari esposizione
    summary = _csv("summary")
    main = summary[summary["config"] == "gbp_0.01"].set_index("agent")
    assert main.loc["C3_ref_stop_dx", "typical_capital"] > main.loc["B_0.25", "typical_capital"] + 0.1
    placebo = _csv("placebo").set_index(["row_type", "agent", "placebo"])
    for agent in DX_ARMS:
        assert placebo.loc[("capital", agent, "cross_season"), "p_value"] > 0.5
        assert placebo.loc[("expected_delta", agent, "cross_season"), "p_value"] < 0.05
