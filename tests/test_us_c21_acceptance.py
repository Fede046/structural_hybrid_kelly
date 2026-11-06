"""Test: popolazione di strategie (us_c21), appaiata con gli esperimenti d'origine delle strategie."""

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shk.model.frozen_params import load_frozen_params
from shk.model.population_run import POPULATION_ARMS

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS = REPO_ROOT / "results"
SUMMARY_CSV = RESULTS / "us_c21_population_summary.csv"
SHARES_CSV = RESULTS / "us_c21_population_shares.csv"
MU_CSV = RESULTS / "us_c21_population_mu.csv"
N_SEASONS = 19
VERSIONS = ("main", "cash", "generations", "generations_cash")
# Strategia → (CSV d'origine, nome dell'agente in quel CSV), configurazione senza puntata minima
SOURCES = {
    "A": ("us_c11_worker_rules_summary.csv", "R1_alone"),
    "B_0.25": ("us_c13_scheme_reference_summary.csv", "B_0.25"),
    "R2_brake": ("us_c11_worker_rules_summary.csv", "R2_brake"),
    "R3_brake": ("us_c11_worker_rules_summary.csv", "R3_brake"),
    "C3": ("us_c10_scheme_validation_summary.csv", "C3"),
    "R3_C3": ("us_c11_worker_rules_summary.csv", "R3_C3"),
    "C3_stop": ("us_c10_scheme_validation_summary.csv", "C3_stop"),
    "C3_ref": ("us_c13_scheme_reference_summary.csv", "C3_ref"),
    "C3_ref_stop": ("us_c13_scheme_reference_summary.csv", "C3_ref_stop"),
    "R3_C3_ref": ("us_c17_r3_reference_summary.csv", "R3_C3_ref"),
    "R3_C3_ref_stop": ("us_c17_r3_reference_summary.csv", "R3_C3_ref_stop"),
}

pytestmark = pytest.mark.skipif(not SUMMARY_CSV.exists(), reason="us_c21 non ancora eseguito")


def test_summary_structure():
    df = pd.read_csv(SUMMARY_CSV)
    assert len(df) == N_SEASONS * (len(POPULATION_ARMS) + len(VERSIONS))
    assert (df["n_seeds"] == int(load_frozen_params().fixed["n_seeds"])).all()
    assert np.isfinite(df["observed_log_wealth"]).all()


@pytest.mark.parametrize("arm", POPULATION_ARMS)
def test_members_match_their_original_experiment(arm: str):
    """Stessi seed: ogni strategia ha lo stesso capitale finale, vero e mediano, del suo esperimento d'origine."""
    df = pd.read_csv(SUMMARY_CSV)
    mine = df[df["version"] == f"member:{arm}"].set_index("season")
    file, agent = SOURCES[arm]
    src = pd.read_csv(RESULTS / file)
    src = src[(src["agent"] == agent) & (src["config"] == "none")].set_index("season")
    assert len(mine) == len(src) == N_SEASONS
    for col in ("observed_log_wealth", "median_log_wealth"):
        assert np.allclose(mine[col], src.loc[mine.index, col], rtol=0, atol=1e-9), col


def test_pure_selection_is_average_of_members():
    """Con μ = 0 la popolazione senza cassa vale la media dei capitali finali delle strategie."""
    mu = pd.read_csv(MU_CSV)
    if float(mu.loc[(mu["version"] == "main") & mu["selected"], "mu"].iloc[0]) != 0.0:
        pytest.skip("μ scelto diverso da 0")
    df = pd.read_csv(SUMMARY_CSV)
    members = df[df["version"].str.startswith("member:")]
    expected = members.groupby("season")["observed_log_wealth"].apply(lambda s: math.log(np.exp(s).mean()))
    main = df[df["version"] == "main"].set_index("season")["observed_log_wealth"]
    assert np.allclose(main, expected.loc[main.index], atol=1e-9)


def test_shares_sum_to_one():
    sh = pd.read_csv(SHARES_CSV)
    for col in ("start_share", "mean_share", "end_share"):
        sums = sh.groupby(["version", "season"])[col].sum()
        assert np.allclose(sums, 1.0), col


def test_one_mu_selected_per_version():
    mu = pd.read_csv(MU_CSV)
    assert mu.groupby("version")["selected"].sum().eq(1).all()
