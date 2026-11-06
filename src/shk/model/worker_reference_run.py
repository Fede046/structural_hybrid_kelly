"""Lavoratore R3 (esito più probabile) con lo schema a riferimento fisso, sulle 19 stagioni di validazione.

Combinazione delle due versioni migliori (decisione del 2026-11-05): la regola di scelta dell'esito
R3 (shk.kelly.outcome_rules) e lo schema con riferimento fisso (C3_ref, C3_ref_stop;
scheme_reference_run). Versioni: "R3_brake" (quarto di Kelly fisso, come in worker_run),
"R3_C3_ref" e "R3_C3_ref_stop". Soglie e stagione di calibrazione di
scheme_reference_run.reference_setups; seed dell'esecuzione congelata, quindi i confronti con
us_c11 (R3) e us_c13 (R1 con lo schema a riferimento fisso) sono appaiati. È una combinazione
scelta dopo aver visto la validazione.
"""

from collections.abc import Mapping, Sequence
from typing import Final

import numpy as np

from shk.kelly.agents import AGENT_B_LAMBDA, FractionalKellyAgent
from shk.kelly.environment import run_paired_backtest
from shk.kelly.outcome_rules import with_outcome_rule
from shk.model.agent_c import SCHEME_STOP_CLEAR, SCHEME_STOP_SEASON, Module2Supervisor, ReferenceData, SchemeAgent
from shk.model.frozen_agents import scheme_window
from shk.model.frozen_params import FrozenParams
from shk.model.paired_backtest import CONFIGURATIONS
from shk.model.scheme_reference_run import ReferenceSetup
from shk.model.season_input import SeasonInput
from shk.model.validation_run import METRICS, run_metrics

R3_REFERENCE_ARMS: Final[tuple[str, ...]] = ("R3_brake", "R3_C3_ref", "R3_C3_ref_stop")


def run_r3_reference_instance(params: FrozenParams, setups: Mapping[str, ReferenceSetup], inp: SeasonInput,
                              fit: str, arms: Sequence[str] = R3_REFERENCE_ARMS) -> np.ndarray:
    """Una stagione nelle tre configurazioni: (C, len(arms), M); supervisore condiviso fra le configurazioni."""
    setup = setups[fit]
    supervisor = Module2Supervisor(inp.season, inp.dates, inp.x, list(params.fixed["covariates"]),
                                   scheme_window(params), reference=ReferenceData(setup.x, setup.delta))
    kappa, base = float(params.calibrated["c1_kappa"]), float(params.fixed["c0_lambda"])
    scheme = with_outcome_rule(SchemeAgent, "R3")
    out = np.full((len(CONFIGURATIONS), len(arms), len(METRICS)), np.nan)
    for ci, (_, min_stake) in enumerate(CONFIGURATIONS):
        agents = [
            with_outcome_rule(FractionalKellyAgent, "R3")("R3_brake", lam=AGENT_B_LAMBDA),
            scheme("R3_C3_ref", supervisor, kappa, setup.mean_threshold, setup.dispersion_threshold,
                   setup.structural_threshold, SCHEME_STOP_CLEAR, base_lambda=base, reference=True),
            scheme("R3_C3_ref_stop", supervisor, kappa, setup.mean_threshold, setup.dispersion_threshold,
                   setup.structural_threshold, SCHEME_STOP_SEASON, base_lambda=base, reference=True),
        ]
        runs = run_paired_backtest(agents, inp.dates, inp.probs, inp.odds, inp.outcomes, min_stake,
                                   fallback_policy=params.fixed["fallback_policy"])
        for run, agent in zip(runs, agents):
            out[ci, list(arms).index(run.name)] = run_metrics(run, agent)
    return out
