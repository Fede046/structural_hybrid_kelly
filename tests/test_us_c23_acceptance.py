"""Test: controllo placebo sul momento degli interventi dello schema (us_c23), appaiato con us_c19 e us_c21."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shk.model.timing_placebo import BASELINES, N_DRAWS, PLACEBO_ARMS, PLACEBOS, RESPONSES

RESULTS = Path(__file__).resolve().parents[1] / "results"
CSV_PATH = RESULTS / "us_c23_timing_placebo.csv"
SEASONS_CSV = RESULTS / "us_c23_timing_placebo_seasons.csv"
POPULATION_CSV = RESULTS / "us_c21_population_summary.csv"
REAL_CSV = RESULTS / "us_c19_real_seasons.csv"
N_SEASONS = 19
# Schema → sintesi di us_c19 con la sua quota di giornate ferme
REAL_SOURCE = {"C3": "scheme", "C3_stop": "scheme", "C3_ref": "reference", "C3_ref_stop": "reference",
               "R3_C3": "worker_rules", "R3_C3_ref": "r3_reference", "R3_C3_ref_stop": "r3_reference"}

pytestmark = pytest.mark.skipif(not CSV_PATH.exists(), reason="us_c23 non ancora eseguito")


def _rows(row_type: str) -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH)
    return df[df["row_type"] == row_type].set_index(["agent", "placebo"])


def test_structure():
    df = pd.read_csv(CSV_PATH)
    assert len(df) == len(PLACEBO_ARMS) * (len(PLACEBOS) * (1 + len(RESPONSES)) + 1)
    drawn = df[df["row_type"] != "constant"]
    assert (drawn["n_draws"] == N_DRAWS).all()
    assert drawn["p_value"].between(1 / (N_DRAWS + 1), 1.0).all()
    seasons = pd.read_csv(SEASONS_CSV)
    assert len(seasons) == len(PLACEBO_ARMS) * N_SEASONS
    assert seasons["shift_share_not_worse"].between(0.0, 1.0).all()


def test_capital_is_reproduced_by_the_schedule():
    assert pd.read_csv(SEASONS_CSV)["reconstruction_error"].max() < 1e-9


@pytest.mark.skipif(not POPULATION_CSV.exists(), reason="us_c21 non ancora eseguito")
@pytest.mark.parametrize("arm", PLACEBO_ARMS)
def test_matches_the_population_runs(arm: str):
    """Stesse esecuzioni senza puntata minima di us_c21: stesso capitale, dello schema e del riferimento."""
    mine = pd.read_csv(SEASONS_CSV)
    mine = mine[mine["agent"] == arm].set_index("season")
    pop = pd.read_csv(POPULATION_CSV).set_index(["version", "season"])["observed_log_wealth"]
    assert np.allclose(mine["log_wealth"], pop.loc[f"member:{arm}"].loc[mine.index], rtol=0, atol=1e-9)
    baseline = BASELINES[PLACEBO_ARMS[arm]]
    assert np.allclose(mine["baseline_log_wealth"], pop.loc[f"member:{baseline}"].loc[mine.index], rtol=0, atol=1e-9)


@pytest.mark.parametrize("arm", PLACEBO_ARMS)
def test_share_of_stopped_days_matches_real_seasons(arm: str):
    real = pd.read_csv(REAL_CSV)
    real = real[(real["config"] == "none") & (real["source"] == REAL_SOURCE[arm]) & (real["agent"] == arm)]
    seasons = pd.read_csv(SEASONS_CSV)
    mine = seasons[seasons["agent"] == arm]["share_days_zero"].mean()
    assert mine == pytest.approx(float(real["share_lambda_zero_real"].iloc[0]), abs=1e-9)


def test_schedule_does_not_depend_on_the_outcome_rule():
    """Il supervisore guarda δ di tutte le partite: R1 e R3 hanno lo stesso calendario."""
    seasons = pd.read_csv(SEASONS_CSV).set_index(["agent", "season"])
    for r1, r3 in (("C3", "R3_C3"), ("C3_ref", "R3_C3_ref"), ("C3_ref_stop", "R3_C3_ref_stop")):
        for col in ("share_days_zero", "share_days_reduced"):
            assert np.allclose(seasons.loc[r1, col], seasons.loc[r3, col])


def test_findings():
    capital, expected, constant = _rows("capital"), _rows("expected_delta"), _rows("constant")
    within = _rows("expected_delta_within")
    main = "C3_ref_stop"
    # Lo schema conserva più capitale del quarto di Kelly...
    assert capital.loc[(main, "shift"), "observed"] > capital.loc[(main, "shift"), "baseline_value"] + 0.1
    # ...ma non più di un calendario di pari esposizione, né dentro la stagione né fra le stagioni
    for placebo in PLACEBOS:
        assert capital.loc[(main, placebo), "p_value"] > 0.5
        assert capital.loc[(main, placebo), "placebo_median"] > capital.loc[(main, placebo), "observed"]
    # Una frazione costante con la stessa esposizione media conserva più capitale
    assert constant.loc[(main, "constant_exposure"), "placebo_mean"] > constant.loc[(main, "constant_exposure"), "observed"]
    # Il segnale c'è: nelle giornate in cui lo schema si ferma il modello è più lontano dal mercato prima
    # della partita, e lo schema si ferma nelle stagioni giuste (placebo fra stagioni)
    for agent in ("C3_ref", "C3_ref_stop"):
        row = expected.loc[(agent, "cross_season")]
        assert row["observed"] < 0 and row["mean_intervention"] < row["mean_other"]
        assert row["p_value"] < 0.01
    # Dentro la stagione, a parità di posizione, il momento dell'allarme non aggiunge un segnale distinguibile
    assert within.loc[(main, "cross_season"), "p_value"] > 0.1
    # Il confronto con le 40 partite precedenti non mostra lo stesso segnale
    assert expected.loc[("C3", "cross_season"), "p_value"] > 0.1
