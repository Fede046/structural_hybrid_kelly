"""Test: le strategie dei genomi di us_c22 sono le stesse agenti già pubblicati, e il CSV è coerente."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.model.evolution import Genome
from shk.model.evolution_run import season_log_wealth
from shk.model.frozen_params import frozen_params_path, load_frozen_params
from shk.model.module2_data import build_module2_frame
from shk.model.population_run import population_setups
from shk.model.residuals import load_model_residuals
from shk.model.validation_run import validation_inputs

RESULTS = Path(__file__).resolve().parents[1] / "results"
POPULATION_CSV = RESULTS / "us_c21_population_summary.csv"
SEASONS_CSV = RESULTS / "us_c22_evolution_seasons.csv"
GENOMES_CSV = RESULTS / "us_c22_evolution_genomes.csv"
KNOWN = {
    "member:B_0.25": Genome(0.25, 0.75, "none", "clear", "R1"),
    "member:C3_stop": Genome(0.25, 0.75, "previous", "season", "R1"),
    "member:R3_C3_ref_stop": Genome(0.25, 0.75, "calibration", "season", "R3"),
}


@pytest.mark.skipif(not POPULATION_CSV.exists(), reason="us_c21 non ancora eseguito")
@pytest.mark.skipif(not (DEFAULT_DATA_DIR.is_dir() and any(DEFAULT_DATA_DIR.glob("*.csv"))),
                    reason=f"Real data missing: no CSV in {DEFAULT_DATA_DIR}")
def test_known_genomes_reproduce_published_strategies():
    params = load_frozen_params(frozen_params_path())
    frame = build_module2_frame(load_model_residuals())
    setups = population_setups(frame[frame["role"] == "training"], params)
    season = validation_inputs(frame, list(params.fixed["covariates"]))[5]
    lw = season_log_wealth(params, setups, season.inp, season.fit, list(KNOWN.values()))
    ref = pd.read_csv(POPULATION_CSV)
    expected = [float(ref.loc[(ref["version"] == v) & (ref["season"] == season.inp.season),
                              "observed_log_wealth"].iloc[0]) for v in KNOWN]
    assert np.allclose(lw, expected, atol=1e-12)


@pytest.mark.skipif(not SEASONS_CSV.exists(), reason="us_c22 non ancora eseguito")
def test_evolution_outputs_are_consistent():
    seasons = pd.read_csv(SEASONS_CSV)
    genomes = pd.read_csv(GENOMES_CSV)
    assert set(seasons["variant"]) == {"free", "fixed_lam_0.25"}
    assert seasons.groupby(["variant", "run"]).size().eq(19).all()
    fixed = genomes[genomes["variant"] == "fixed_lam_0.25"]
    assert (fixed["lam"] == 0.25).all()
    pop = genomes.groupby(["variant", "run", "season"])["log_wealth"].apply(lambda s: np.log(np.exp(s).mean()))
    merged = seasons.set_index(["variant", "run", "season"])["population_log_wealth"]
    assert np.allclose(merged.loc[pop.index], pop, atol=1e-9)
