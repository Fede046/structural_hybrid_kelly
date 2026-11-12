"""Test: lo schema con soglie dell'allarme per stagione sulle 19 stagioni vere (us_c26), appaiato con us_c13."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shk.model.season_thresholds import PER_DATE_ARMS, RUN_ARMS, SEASON_ARMS
from shk.model.timing_placebo import PLACEBOS, RESPONSES

RESULTS = Path(__file__).resolve().parents[1] / "results"
THRESHOLDS_CSV = RESULTS / "us_c26_season_thresholds.csv"
SEASONS_CSV = RESULTS / "us_c26_season_thresholds_seasons.csv"
SUMMARY_CSV = RESULTS / "us_c26_season_thresholds_summary.csv"
PLACEBO_CSV = RESULTS / "us_c26_season_thresholds_placebo.csv"
REFERENCE_CSV = RESULTS / "us_c13_scheme_reference_summary.csv"
REFERENCE_THRESHOLDS_CSV = RESULTS / "us_c13_scheme_reference_thresholds.csv"
N_SEASONS, N_CONFIGS = 19, 3

pytestmark = pytest.mark.skipif(not SUMMARY_CSV.exists(), reason="us_c26 non ancora eseguito")


def test_structure():
    assert len(pd.read_csv(THRESHOLDS_CSV)) == 3
    assert len(pd.read_csv(SEASONS_CSV)) == N_SEASONS * N_CONFIGS * len(RUN_ARMS)
    assert len(pd.read_csv(SUMMARY_CSV)) == N_CONFIGS * len(RUN_ARMS)
    assert len(pd.read_csv(PLACEBO_CSV)) == len(SEASON_ARMS) * (len(PLACEBOS) * (1 + len(RESPONSES)) + 1)


def test_thresholds_are_higher_over_a_season_and_per_date_ones_are_those_of_us_c13():
    thr = pd.read_csv(THRESHOLDS_CSV).set_index("fit")
    assert (thr["season_mean_threshold"] > 2 * thr["mean_threshold"]).all()
    assert (thr["season_dispersion_threshold"] > 2 * thr["dispersion_threshold"]).all()
    ref = pd.read_csv(REFERENCE_THRESHOLDS_CSV).set_index("fit").loc[thr.index]
    for col in ("mean_threshold", "dispersion_threshold", "structural_threshold"):
        assert np.allclose(thr[col], ref[col], rtol=1e-12, atol=0), col


def test_per_date_versions_match_us_c13():
    """Stesse soglie e stesse stagioni vere: B_0.25, C3_ref e C3_ref_stop coincidono con us_c13."""
    mine = pd.read_csv(SEASONS_CSV).set_index(["config", "agent", "season"])["log_wealth"]
    ref = pd.read_csv(REFERENCE_CSV)
    ref = ref[ref["row_type"] == "summary"].set_index(["config", "agent", "season"])["observed_log_wealth"]
    for agent in ("B_0.25",) + PER_DATE_ARMS:
        ours = mine[mine.index.get_level_values("agent") == agent]
        assert np.allclose(ours, ref.loc[ours.index], rtol=0, atol=1e-9), agent


def test_findings():
    summary = pd.read_csv(SUMMARY_CSV)
    main = summary[summary["config"] == "gbp_0.01"].set_index("agent")
    # Le soglie per stagione fermano lo schema in meno stagioni e in meno giornate
    assert main.loc["C3_ref_stop", "seasons_with_stop"] == 16
    assert main.loc["C3_ref_stop_season", "seasons_with_stop"] == 11
    assert main.loc["C3_ref_stop_season", "share_days_zero"] < main.loc["C3_ref_stop", "share_days_zero"] - 0.15
    # Con un vantaggio negativo fermarsi meno conserva meno capitale: la differenza dal quarto di Kelly
    # non è più distinguibile dal caso
    assert main.loc["B_0.25", "typical_capital"] < main.loc["C3_ref_stop_season", "typical_capital"] \
        < main.loc["C3_ref_stop", "typical_capital"]
    assert main.loc["C3_ref_stop_season", "sign_test_p"] > 0.3
    assert main.loc["C3_ref_stop_season", "capital_ratio_low"] < 1.0 < main.loc["C3_ref_stop_season", "capital_ratio_high"]
    # Con il modello calibrato sul 2000-01 lo schema si ferma solo nelle ultime due stagioni, le più lontane
    seasons = pd.read_csv(SEASONS_CSV)
    old = seasons[(seasons["config"] == "gbp_0.01") & (seasons["agent"] == "C3_ref_stop_season")
                  & (seasons["fit_through"] == "2000-01")].set_index("season")["share_days_zero"]
    assert set(old[old > 0.5].index) == {"2008-09", "2009-10"}
    assert old.drop(["2008-09", "2009-10"]).max() < 0.05
    # Il segnale resta: lo schema si ferma nelle stagioni in cui il modello è più lontano dal mercato
    placebo = pd.read_csv(PLACEBO_CSV).set_index(["row_type", "agent", "placebo"])
    for agent in SEASON_ARMS:
        assert placebo.loc[("expected_delta", agent, "cross_season"), "observed"] < 0
        assert placebo.loc[("expected_delta", agent, "cross_season"), "p_value"] < 0.01
        # ...ma il capitale non supera quello di un calendario di pari esposizione
        assert placebo.loc[("capital", agent, "cross_season"), "p_value"] > 0.5
