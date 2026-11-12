"""Test: la versione principale nelle analisi rifatte (us_c29–us_c32), appaiata con gli esperimenti d'origine."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shk.model.main_version import MAIN_POPULATION_ARMS, RULE_ARMS, TEST_ARMS

RESULTS = Path(__file__).resolve().parents[1] / "results"
N_SEASONS, N_CONFIGS = 19, 3


def _needs(name: str):
    return pytest.mark.skipif(not (RESULTS / name).exists(), reason=f"{name} non ancora generato")


@_needs("us_c29_main_rules_seasons.csv")
def test_us_c29_rules():
    seasons = pd.read_csv(RESULTS / "us_c29_main_rules_seasons.csv")
    assert len(seasons) == N_SEASONS * N_CONFIGS * len(RULE_ARMS)
    # Con la regola R1 la versione principale e il quarto di Kelly coincidono con us_c27
    c27 = pd.read_csv(RESULTS / "us_c27_two_fold_seasons.csv").set_index(["config", "agent", "season"])["log_wealth"]
    mine = seasons.set_index(["config", "agent", "season"])["log_wealth"]
    for ours, theirs in (("M", "C3_ref_stop_season_dx"), ("B_0.25", "B_0.25")):
        x = mine.xs(ours, level="agent")
        y = c27.xs(theirs, level="agent").loc[x.index]
        assert np.allclose(x, y, rtol=0, atol=1e-9), ours
    summary = pd.read_csv(RESULTS / "us_c29_main_rules_summary.csv")
    s = summary[summary["config"] == "gbp_0.01"].set_index("agent")
    # La regola dell'esito più probabile punta su meno partite e conserva di più, con e senza schema
    assert s.loc["R3_brake", "mean_n_bets"] < 0.6 * s.loc["B_0.25", "mean_n_bets"]
    assert s.loc["R3_brake", "typical_capital"] > s.loc["B_0.25", "typical_capital"]
    assert s.loc["R3_M", "typical_capital"] > s.loc["M", "typical_capital"]
    # Lo schema si ferma nelle stesse giornate qualunque sia la regola (l'allarme dipende solo da δ)
    assert s.loc["M", "share_days_zero"] == pytest.approx(s.loc["R3_M", "share_days_zero"])


@_needs("us_c30_main_kellybench_summary.csv")
def test_us_c30_kellybench():
    mine = pd.read_csv(RESULTS / "us_c30_main_kellybench_summary.csv")
    assert set(mine["agent"]) == set(TEST_ARMS) and len(mine) == N_CONFIGS * len(TEST_ARMS)
    # Stessi seed di us_c14: A e B_0.25 coincidono
    c14 = pd.read_csv(RESULTS / "us_c14_test_scheme_seeds_summary.csv").set_index(["config", "agent"])
    m = mine.set_index(["config", "agent"])
    for agent in ("A", "B_0.25"):
        for col in ("observed_log_wealth", "median_log_wealth"):
            x, y = m.xs(agent, level="agent")[col], c14.xs(agent, level="agent")[col].loc[m.xs(agent, level="agent").index]
            assert np.allclose(x, y, rtol=0, atol=1e-9), (agent, col)
    # Nella stagione vera la versione principale non si ferma mai e coincide con il quarto di Kelly
    main = m.loc[("gbp_0.01", "M")]
    assert main["observed_share_lambda_zero"] == 0.0
    assert main["observed_log_wealth"] == pytest.approx(m.loc[("gbp_0.01", "B_0.25"), "observed_log_wealth"])


@_needs("us_c31_main_population_summary.csv")
def test_us_c31_population():
    mine = pd.read_csv(RESULTS / "us_c31_main_population_summary.csv")
    assert len(mine) == N_SEASONS * (len(MAIN_POPULATION_ARMS) + 4)
    # Strategie senza supervisore: stessi percorsi della popolazione di us_c21
    c21 = pd.read_csv(RESULTS / "us_c21_population_summary.csv").set_index(["version", "season"])
    m = mine.set_index(["version", "season"])
    for arm in ("A", "B_0.25", "R2_brake", "R3_brake"):
        key = f"member:{arm}"
        for col in ("observed_log_wealth", "median_log_wealth"):
            assert np.allclose(m.loc[key, col], c21.loc[key, col].loc[m.loc[key].index], rtol=0, atol=1e-9), (arm, col)
    # La versione principale da sola: stessa stagione vera di us_c27, senza puntata minima
    c27 = pd.read_csv(RESULTS / "us_c27_two_fold_seasons.csv")
    c27 = c27[(c27["config"] == "none") & (c27["agent"] == "C3_ref_stop_season_dx")].set_index("season")["log_wealth"]
    x = m.loc["member:M", "observed_log_wealth"]
    assert np.allclose(x, c27.loc[x.index], rtol=0, atol=1e-9)


@_needs("us_c32_main_evolution_seasons.csv")
def test_us_c32_evolution():
    seasons = pd.read_csv(RESULTS / "us_c32_main_evolution_seasons.csv")
    genomes = pd.read_csv(RESULTS / "us_c32_main_evolution_genomes.csv")
    assert len(seasons) == 2 * 30 * N_SEASONS and len(genomes) == 2 * 30 * 20 * N_SEASONS
    assert seasons["share_main"].between(0, 1).all()
    # Il genoma "none" con lam 0.25 e regola R1 è il quarto di Kelly: stessa stagione vera
    c21 = pd.read_csv(RESULTS / "us_c21_population_summary.csv")
    b = c21[c21["version"] == "member:B_0.25"].set_index("season")["observed_log_wealth"]
    g = genomes[(genomes["supervisor"] == "none") & (genomes["lam"] == 0.25) & (genomes["rule"] == "R1")]
    assert len(g) > 0
    assert np.allclose(g["log_wealth"], b.loc[g["season"]].to_numpy(), rtol=0, atol=1e-9)
