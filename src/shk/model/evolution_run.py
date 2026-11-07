"""Strategie dai genomi di shk.model.evolution, giocate su una stagione senza puntata minima.

Ogni genoma diventa un agente già esistente, con i parametri congelati per tutto il resto:
- supervisor "none": FractionalKellyAgent con λ = lam e la regola di scelta dell'esito;
- supervisor "previous": SchemeAgent con il supervisore delle W partite precedenti e le soglie di
  scheme_run (come C3), base_lambda = lam, kappa e stop dal genoma;
- supervisor "calibration": SchemeAgent con la stagione di calibrazione come riferimento e le soglie
  di scheme_reference_run (come C3_ref).
Le soglie per fit sono quelle di population_run.population_setups, calibrate sul training.
"""

from collections.abc import Mapping, Sequence

import numpy as np

from shk.kelly.agents import Agent, FractionalKellyAgent
from shk.kelly.environment import run_paired_backtest
from shk.kelly.outcome_rules import with_outcome_rule
from shk.model.agent_c import SCHEME_STOP_CLEAR, SCHEME_STOP_SEASON, Module2Supervisor, ReferenceData, SchemeAgent
from shk.model.evolution import Genome
from shk.model.frozen_agents import build_supervisor, scheme_window
from shk.model.frozen_params import FrozenParams
from shk.model.population_run import PopulationSetup
from shk.model.season_input import SeasonInput

_STOPS = {"clear": SCHEME_STOP_CLEAR, "season": SCHEME_STOP_SEASON}


def genome_agent(name: str, g: Genome, setup: PopulationSetup, structural: float,
                 supervisor: Module2Supervisor, reference_supervisor: Module2Supervisor) -> Agent:
    """Agente del genoma g (vedi modulo)."""
    if g.supervisor == "none":
        return with_outcome_rule(FractionalKellyAgent, g.rule)(name, lam=float(g.lam))
    cls = with_outcome_rule(SchemeAgent, g.rule)
    if g.supervisor == "previous":
        return cls(name, supervisor, float(g.kappa), setup.mean_threshold, setup.dispersion_threshold, structural,
                   _STOPS[g.stop], base_lambda=float(g.lam))
    ref = setup.reference
    return cls(name, reference_supervisor, float(g.kappa), ref.mean_threshold, ref.dispersion_threshold,
               ref.structural_threshold, _STOPS[g.stop], base_lambda=float(g.lam), reference=True)


def season_log_wealth(params: FrozenParams, setups: Mapping[str, PopulationSetup], inp: SeasonInput, fit: str,
                      genomes: Sequence[Genome]) -> np.ndarray:
    """ln del capitale finale di ogni genoma sulla stagione (stagione vera di inp), senza puntata minima."""
    setup = setups[fit]
    supervisor = build_supervisor(params, inp)
    reference_supervisor = Module2Supervisor(inp.season, inp.dates, inp.x, list(params.fixed["covariates"]),
                                             scheme_window(params),
                                             reference=ReferenceData(setup.reference.x, setup.reference.delta))
    structural = float(params.c1_thresholds[fit])
    unique = list(dict.fromkeys(genomes))  # genomi uguali danno lo stesso risultato: si giocano una volta
    agents = [genome_agent(f"g{i}", g, setup, structural, supervisor, reference_supervisor)
              for i, g in enumerate(unique)]
    runs = run_paired_backtest(agents, inp.dates, inp.probs, inp.odds, inp.outcomes, 0.0,
                               fallback_policy=params.fixed["fallback_policy"])
    by_genome = {g: float(np.log(run.wealth[0, -1])) for g, run in zip(unique, runs)}
    return np.array([by_genome[g] for g in genomes])
