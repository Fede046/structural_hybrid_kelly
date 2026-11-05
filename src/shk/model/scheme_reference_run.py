"""Schema del relatore con riferimento fisso (C3_ref, C3_ref_stop) sulle 19 stagioni di validazione.

Variante di scheme_run (decisione del 2026-11-05): la finestra di riferimento dell'allarme e della
diagnosi è la stagione di calibrazione del Modulo 1 (la stagione di training del fit), invece delle
W partite precedenti (agent_c, "Variante con riferimento fisso"). Dal file congelato prende W =
c1_window, κ = c1_kappa, λ base = c0_lambda, politica del ripiego e configurazioni; le soglie di
media, dispersione e componente strutturale sono calibrate qui sul training
(agent_c.calibrate_reference_thresholds), perché il confronto è diverso da quello di C3.

Seed delle soglie: story_task_sequence(SEED_S14, posizione del Modulo 1, N_STORY_TASKS), poi
spawn(numero di fit) in ordine cronologico. Seed delle stagioni: quelli dell'esecuzione congelata
(scheme_run.evaluate_scheme), quindi B_0.25 coincide con l'esecuzione congelata e i confronti sono
appaiati. È una variante scelta dopo aver visto le frequenze d'allarme sulla validazione.
"""

from collections.abc import Mapping, Sequence
from typing import Final, NamedTuple

import numpy as np
import pandas as pd

from shk.kelly.agents import AGENT_B_LAMBDA, Agent, FractionalKellyAgent
from shk.kelly.environment import run_paired_backtest
from shk.model.agent_c import (
    SCHEME_STOP_CLEAR,
    SCHEME_STOP_SEASON,
    Module2Supervisor,
    ReferenceData,
    SchemeAgent,
    calibrate_reference_thresholds,
)
from shk.model.frozen_agents import scheme_window
from shk.model.frozen_params import FrozenParams
from shk.model.module1 import MODULE1_IDS, check_module1
from shk.model.paired_backtest import CONFIGURATIONS
from shk.model.scheme_run import fit_block_length
from shk.model.season_input import SeasonInput, season_input_from_frame, training_seasons
from shk.model.task_seeds import N_STORY_TASKS, story_task_sequence
from shk.model.validation_run import METRICS, run_metrics

SEED_S14: Final[int] = 20261106
REFERENCE_ARMS: Final[tuple[str, ...]] = ("B_0.25", "C3_ref", "C3_ref_stop")
REFERENCE_THRESHOLD_COLUMNS: Final[tuple[str, ...]] = (
    "fit", "window", "block_length", "n_reference", "mean_threshold", "dispersion_threshold", "structural_threshold",
)


class ReferenceSetup(NamedTuple):
    """Soglie e stagione di calibrazione di un fit per la variante con riferimento fisso."""

    mean_threshold: float
    dispersion_threshold: float
    structural_threshold: float
    x: np.ndarray
    delta: np.ndarray


def reference_setups(train: pd.DataFrame, params: FrozenParams,
                     seed: int | np.random.SeedSequence = SEED_S14) -> dict[str, ReferenceSetup]:
    """Stagione di calibrazione e soglie per fit, sulle stagioni di training (vedi modulo)."""
    covariates = list(params.fixed["covariates"])
    inputs = [season_input_from_frame(train, s, covariates) for s in training_seasons(train)]
    position = MODULE1_IDS.index(check_module1(params.module1))
    gens = story_task_sequence(seed, position, N_STORY_TASKS).spawn(len(inputs))
    w = scheme_window(params)
    out = {}
    for inp, g in zip(inputs, gens):
        thr = calibrate_reference_thresholds(inp.x, inp.delta, w, fit_block_length(inp), np.random.default_rng(g))
        out[inp.season] = ReferenceSetup(*thr, inp.x, inp.delta)
    return out


def reference_threshold_records(train: pd.DataFrame, params: FrozenParams,
                                setups: Mapping[str, ReferenceSetup]) -> list[dict[str, object]]:
    """Righe del CSV delle soglie della variante, una per fit."""
    covariates = list(params.fixed["covariates"])
    return [{"fit": fit, "window": scheme_window(params),
             "block_length": fit_block_length(season_input_from_frame(train, fit, covariates)),
             "n_reference": int(s.delta.shape[0]), "mean_threshold": s.mean_threshold,
             "dispersion_threshold": s.dispersion_threshold, "structural_threshold": s.structural_threshold}
            for fit, s in setups.items()]


def build_reference_agents(params: FrozenParams, setup: ReferenceSetup, supervisor: Module2Supervisor,
                           arms: Sequence[str] = REFERENCE_ARMS) -> list[Agent]:
    """B_0.25 come nell'esecuzione congelata, C3_ref e C3_ref_stop con il riferimento fisso."""
    kappa, base = float(params.calibrated["c1_kappa"]), float(params.fixed["c0_lambda"])

    def scheme(name: str, stop: str) -> SchemeAgent:
        return SchemeAgent(name, supervisor, kappa, setup.mean_threshold, setup.dispersion_threshold,
                           setup.structural_threshold, stop, base_lambda=base, reference=True)

    builders = {
        "B_0.25": lambda: FractionalKellyAgent("B_0.25", lam=AGENT_B_LAMBDA),
        "C3_ref": lambda: scheme("C3_ref", SCHEME_STOP_CLEAR),
        "C3_ref_stop": lambda: scheme("C3_ref_stop", SCHEME_STOP_SEASON),
    }
    return [builders[a]() for a in arms]


def run_reference_instance(params: FrozenParams, setups: Mapping[str, ReferenceSetup], inp: SeasonInput,
                           fit: str, arms: Sequence[str] = REFERENCE_ARMS) -> np.ndarray:
    """Una stagione nelle tre configurazioni: (C, len(arms), M); supervisore condiviso fra le configurazioni."""
    setup = setups[fit]
    supervisor = Module2Supervisor(inp.season, inp.dates, inp.x, list(params.fixed["covariates"]),
                                   scheme_window(params), reference=ReferenceData(setup.x, setup.delta))
    out = np.full((len(CONFIGURATIONS), len(arms), len(METRICS)), np.nan)
    for ci, (_, min_stake) in enumerate(CONFIGURATIONS):
        agents = build_reference_agents(params, setup, supervisor, arms)
        runs = run_paired_backtest(agents, inp.dates, inp.probs, inp.odds, inp.outcomes, min_stake,
                                   fallback_policy=params.fixed["fallback_policy"])
        for run, agent in zip(runs, agents):
            out[ci, list(arms).index(run.name)] = run_metrics(run, agent)
    return out
