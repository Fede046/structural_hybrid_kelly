"""Lavoratori classici che scelgono l'esito (R1, R2, R3) sulle 19 stagioni di validazione.

Disegno del lavoratore, opzione A (thesis/disegno_lavoratore.md): il lavoratore propone per
ogni partita esito e frazione f_w = Kelly pieno sull'esito della sua regola
(shk.kelly.outcome_rules); il supervisore agisce solo sulla puntata, f = λ·f_w. Per ogni
regola cinque versioni, sulle stesse partite e quote:
- "<R>_alone": f = f_w (λ = 1);
- "<R>_brake": f = 0.25·f_w, freno costante (come B_0.25);
- "<R>_C1", "<R>_C2", "<R>_C3": λ di C1, C2 e C3 (schema del relatore) con i parametri congelati.
Con R1 le cinque versioni coincidono con A, B_0.25, C1, C2 dell'esecuzione congelata e con C3
di us_c10_scheme_validation.

Il Modulo 2 lavora su δ, che non dipende dalla regola, quindi finestre, soglie e supervisori
(uno per W congelata) restano quelli di oggi e si condividono fra le regole; solo il Modulo 3
di C2 usa l'EV̂ dell'esito candidato della regola sulla finestra B
(Module2Supervisor.window_candidate_ev). Soglie dell'allarme di C3 e seed: come in scheme_run.
"""

from collections.abc import Mapping, Sequence
from typing import Final

import numpy as np

from shk.kelly.agents import AGENT_A_LAMBDA, AGENT_B_LAMBDAS, Agent, FractionalKellyAgent
from shk.kelly.environment import run_paired_backtest
from shk.kelly.outcome_rules import OUTCOME_RULES, with_outcome_rule
from shk.model.agent_c import SCHEME_STOP_CLEAR, C1Agent, GradedAgent, Module2Supervisor, SchemeAgent
from shk.model.frozen_agents import arm_windows
from shk.model.frozen_params import FrozenParams
from shk.model.paired_backtest import CONFIGURATIONS
from shk.model.training_agents import SeasonInput
from shk.model.validation_run import METRICS, run_metrics

WORKER_RULES: Final[tuple[str, ...]] = tuple(OUTCOME_RULES)
WORKER_VERSIONS: Final[tuple[str, ...]] = ("alone", "brake", "C1", "C2", "C3")
WORKER_ARMS: Final[tuple[str, ...]] = tuple(f"{r}_{v}" for r in WORKER_RULES for v in WORKER_VERSIONS)


def build_worker_agents(params: FrozenParams, thresholds: Mapping[str, tuple[float, ...]],
                        supervisors: Mapping[int, Module2Supervisor], fit: str,
                        arms: Sequence[str] = WORKER_ARMS) -> list[Agent]:
    """Agenti di WORKER_ARMS (vedi modulo), con i parametri congelati e le soglie di C3."""
    c, f = params.calibrated, params.fixed
    windows = arm_windows(params)
    kappa, base = float(c["c1_kappa"]), float(f["c0_lambda"])
    structural = float(params.c1_thresholds[fit])
    mean_thr, disp_thr = thresholds[fit][:2]
    out: list[Agent] = []
    for arm in arms:
        rule, version = arm.split("_", 1)
        if version == "alone":
            out.append(with_outcome_rule(FractionalKellyAgent, rule)(arm, lam=AGENT_A_LAMBDA))
        elif version == "brake":
            out.append(with_outcome_rule(FractionalKellyAgent, rule)(arm, lam=AGENT_B_LAMBDAS[0]))
        elif version == "C1":
            out.append(with_outcome_rule(C1Agent, rule)(arm, supervisors[windows["C1"]], kappa, structural,
                                                        base_lambda=base))
        elif version == "C2":
            out.append(with_outcome_rule(GradedAgent, rule)(arm, supervisors[windows["C2"]], abstain=True))
        elif version == "C3":
            out.append(with_outcome_rule(SchemeAgent, rule)(arm, supervisors[windows["C1"]], kappa, mean_thr,
                                                            disp_thr, structural, SCHEME_STOP_CLEAR,
                                                            base_lambda=base))
        else:
            raise ValueError(f"unknown worker arm {arm!r}")
    return out


def run_worker_instance(params: FrozenParams, thresholds: Mapping[str, tuple[float, ...]], inp: SeasonInput,
                        fit: str, arms: Sequence[str] = WORKER_ARMS) -> np.ndarray:
    """Una stagione nelle tre configurazioni: (C, len(arms), M); supervisori condivisi fra regole e configurazioni."""
    covariates = list(params.fixed["covariates"])
    windows = arm_windows(params)
    supervisors = {w: Module2Supervisor(inp.season, inp.dates, inp.x, covariates, w)
                   for w in sorted({windows["C1"], windows["C2"]})}
    out = np.full((len(CONFIGURATIONS), len(arms), len(METRICS)), np.nan)
    for ci, (_, min_stake) in enumerate(CONFIGURATIONS):
        agents = build_worker_agents(params, thresholds, supervisors, fit, arms)
        runs = run_paired_backtest(agents, inp.dates, inp.probs, inp.odds, inp.outcomes, min_stake,
                                   fallback_policy=params.fixed["fallback_policy"])
        for run, agent in zip(runs, agents):
            out[ci, list(arms).index(run.name)] = run_metrics(run, agent)
    return out
