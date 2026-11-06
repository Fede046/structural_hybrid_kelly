"""Strategie della popolazione (thesis/disegno_popolazione.md): percorsi del capitale senza puntata minima.

Le strategie sono quelle già valutate, con il modello Elo e i parametri congelati:
- "A": Kelly pieno, regola R1 (agente A);
- "B_0.25", "R2_brake", "R3_brake": quarto di Kelly con le regole R1, R2, R3;
- "C3", "R3_C3": schema con confronto con le W partite precedenti, riprende quando l'allarme si
  spegne, regole R1 e R3 (scheme_run, worker_run);
- "C3_stop": come C3, fermo fino a fine stagione dopo un errore strutturale;
- "C3_ref", "C3_ref_stop", "R3_C3_ref", "R3_C3_ref_stop": schema con confronto con la stagione di
  calibrazione, riprende o fermo, regole R1 e R3 (scheme_reference_run, worker_reference_run).
Ogni strategia è costruita come nel suo esperimento d'origine, quindi con gli stessi seed le metriche
coincidono con quelle pubblicate (configurazione "none"). Tutte giocano in un unico backtest appaiato
con puntata minima 0: le puntate sono frazioni del capitale e i rendimenti giornalieri non dipendono
dal capitale affidato a ciascuna (shk.model.population).
"""

from collections.abc import Mapping, Sequence
from typing import Final, NamedTuple

import numpy as np
import pandas as pd

from shk.kelly.agents import AGENT_A_LAMBDA, AGENT_B_LAMBDA, Agent, FractionalKellyAgent
from shk.kelly.environment import run_paired_backtest
from shk.kelly.outcome_rules import with_outcome_rule
from shk.model.agent_c import (
    SCHEME_STOP_CLEAR,
    SCHEME_STOP_SEASON,
    Module2Supervisor,
    ReferenceData,
    SchemeAgent,
)
from shk.model.frozen_agents import build_supervisor, check_frozen_constants, scheme_window
from shk.model.frozen_params import FrozenParams, load_frozen_params
from shk.model.scheme_reference_run import ReferenceSetup, reference_setups
from shk.model.scheme_run import scheme_thresholds
from shk.model.season_bootstrap import reconstruct_season, season_block_length
from shk.model.season_input import SeasonInput
from shk.model.validation_run import ValidationSeason

POPULATION_ARMS: Final[tuple[str, ...]] = (
    "A", "B_0.25", "R2_brake", "R3_brake",
    "C3", "R3_C3", "C3_stop",
    "C3_ref", "C3_ref_stop", "R3_C3_ref", "R3_C3_ref_stop",
)


class PopulationSetup(NamedTuple):
    """Soglie di un fit: allarme dello schema con le W partite precedenti (media, dispersione) e riferimento fisso."""

    mean_threshold: float
    dispersion_threshold: float
    reference: ReferenceSetup


def population_setups(train: pd.DataFrame, params: FrozenParams) -> dict[str, PopulationSetup]:
    """Soglie per fit, con gli stessi seed degli esperimenti d'origine (scheme_thresholds, reference_setups)."""
    scheme = scheme_thresholds(train, params)
    reference = reference_setups(train, params)
    return {fit: PopulationSetup(scheme[fit][0], scheme[fit][1], reference[fit]) for fit in scheme}


def build_population_agents(params: FrozenParams, setup: PopulationSetup, structural: float,
                            supervisor: Module2Supervisor, reference_supervisor: Module2Supervisor,
                            arms: Sequence[str] = POPULATION_ARMS) -> list[Agent]:
    """Agenti di POPULATION_ARMS (vedi modulo)."""
    kappa, base = float(params.calibrated["c1_kappa"]), float(params.fixed["c0_lambda"])
    ref = setup.reference

    def kelly(name: str, rule: str, lam: float) -> Agent:
        return with_outcome_rule(FractionalKellyAgent, rule)(name, lam=lam)

    def scheme(name: str, rule: str, stop: str) -> Agent:
        return with_outcome_rule(SchemeAgent, rule)(name, supervisor, kappa, setup.mean_threshold,
                                                    setup.dispersion_threshold, structural, stop, base_lambda=base)

    def scheme_ref(name: str, rule: str, stop: str) -> Agent:
        return with_outcome_rule(SchemeAgent, rule)(name, reference_supervisor, kappa, ref.mean_threshold,
                                                    ref.dispersion_threshold, ref.structural_threshold, stop,
                                                    base_lambda=base, reference=True)

    builders = {
        "A": lambda: kelly("A", "R1", AGENT_A_LAMBDA),
        "B_0.25": lambda: kelly("B_0.25", "R1", AGENT_B_LAMBDA),
        "R2_brake": lambda: kelly("R2_brake", "R2", AGENT_B_LAMBDA),
        "R3_brake": lambda: kelly("R3_brake", "R3", AGENT_B_LAMBDA),
        "C3": lambda: scheme("C3", "R1", SCHEME_STOP_CLEAR),
        "R3_C3": lambda: scheme("R3_C3", "R3", SCHEME_STOP_CLEAR),
        "C3_stop": lambda: scheme("C3_stop", "R1", SCHEME_STOP_SEASON),
        "C3_ref": lambda: scheme_ref("C3_ref", "R1", SCHEME_STOP_CLEAR),
        "C3_ref_stop": lambda: scheme_ref("C3_ref_stop", "R1", SCHEME_STOP_SEASON),
        "R3_C3_ref": lambda: scheme_ref("R3_C3_ref", "R3", SCHEME_STOP_CLEAR),
        "R3_C3_ref_stop": lambda: scheme_ref("R3_C3_ref_stop", "R3", SCHEME_STOP_SEASON),
    }
    return [builders[a]() for a in arms]


def run_population_instance(params: FrozenParams, setups: Mapping[str, PopulationSetup], inp: SeasonInput,
                            fit: str, arms: Sequence[str] = POPULATION_ARMS) -> np.ndarray:
    """Una stagione senza puntata minima: capitale (len(arms), D+1) giornata per giornata, W(0) = 1."""
    setup = setups[fit]
    supervisor = build_supervisor(params, inp)
    reference_supervisor = Module2Supervisor(inp.season, inp.dates, inp.x, list(params.fixed["covariates"]),
                                             scheme_window(params),
                                             reference=ReferenceData(setup.reference.x, setup.reference.delta))
    agents = build_population_agents(params, setup, float(params.c1_thresholds[fit]), supervisor,
                                     reference_supervisor, arms)
    runs = run_paired_backtest(agents, inp.dates, inp.probs, inp.odds, inp.outcomes, 0.0,
                               fallback_policy=params.fixed["fallback_policy"])
    return np.stack([run.wealth[0] for run in runs])


def run_population_season(params_path: str, setups: Mapping[str, PopulationSetup], season: ValidationSeason,
                          seed_seqs: Sequence[np.random.SeedSequence]) -> tuple[np.ndarray, np.ndarray, int]:
    """Stagione vera e ricostruite: (osservata (A, D+1), ricostruite (N, A, D+1), L_PW).

    Le ricostruzioni sono quelle di scheme_run.run_scheme_season con gli stessi seed.
    """
    params = load_frozen_params(params_path)
    check_frozen_constants(params)
    covariates = list(params.fixed["covariates"])
    l_pw = season_block_length(season.inp)
    observed = run_population_instance(params, setups, season.inp, season.fit)
    recs = np.full((len(seed_seqs),) + observed.shape, np.nan)
    for k, ss in enumerate(seed_seqs):
        rec = reconstruct_season(season.inp, np.random.default_rng(ss), l_pw, covariates=covariates)
        recs[k] = run_population_instance(params, setups, rec, season.fit)
    return observed, recs, l_pw
