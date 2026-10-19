"""Agenti di S10 costruiti solo dai parametri congelati (T55).

Tutti i parametri di C0, C1, C2_global, C2, D_ADWIN e D_PH e del Modulo 2 vengono da
FrozenParams (shk.model.frozen_params.load_frozen_params). Le costanti che il codice usa al
proprio interno senza riceverle come argomento sono confrontate con il file da
check_frozen_constants, che solleva un errore se non coincidono: λ non attivo e candidata
del Modulo 3, limiti di λ, soglia della regola fuori supporto, metodo di de-vigging, serie di
D, politica del ripiego, B e α della soglia di C1.

A, B_0.25, B_0.10 ed E sono le baseline di C6 (agents.py): non hanno parametri di S9.

Catena del Modulo 2 tagliata alla stagione, come nella calibrazione T52–T54 (decisione del
programmatore del 2026-10-12): build_supervisors senza storia. Con history si ottiene la
catena che attraversa le stagioni, solo per la sensibilità di T55.
"""

import math
from collections.abc import Mapping, Sequence
from typing import Final

import numpy as np

from shk.kelly.agents import (
    AGENT_A_LAMBDA,
    AGENT_B_LAMBDAS,
    Agent,
    DateView,
    FractionalKellyAgent,
    MinimumStakeAgent,
)
from shk.kelly.environment import FALLBACK_POLICIES
from shk.model.agent_c import C1_N_BOOT, C1Agent, GradedAgent, Module2Supervisor, SupervisorHistory
from shk.model.frozen_params import FrozenParams
from shk.model.module3 import CHOSEN_CANDIDATE, INACTIVE_LAMBDA
from shk.model.training_agents import SeasonInput
from shk.model.training_calibration import SharedShin, SharedShinBaselineDAgent
from shk.stats.false_rejection import ALPHA
from shk.stats.nopo import MIN_CELL_COUNT

AGENT_ORDER: Final[tuple[str, ...]] = ("A", "B_0.25", "B_0.10", "D_ADWIN", "D_PH", "C0", "C1", "C2_global", "C2", "E")
SUPERVISED_ARMS: Final[tuple[str, ...]] = ("C1", "C2_global", "C2")


class RecordingDAgent(SharedShinBaselineDAgent):
    """Baseline D che registra λ a ogni data di decisione (per la quota di date con λ = 0)."""

    def __init__(self, name: str, detector: str, params: dict, kappa: float, shin: SharedShin,
                 base_lambda: float) -> None:
        super().__init__(name, detector, params, kappa, shin, base_lambda=base_lambda)
        self.lambda_by_date: dict[np.datetime64, float] = {}

    def stake_fractions(self, view: DateView, p_hat: np.ndarray, b: np.ndarray) -> np.ndarray:
        """Come BaselineDAgent, registrando λ della data."""
        self.lambda_by_date[np.datetime64(view.date, "ns")] = self.current_lambda
        return super().stake_fractions(view, p_hat, b)


def check_frozen_constants(params: FrozenParams) -> None:
    """Verifica che le costanti interne al codice coincidano con il file congelato.

    Solleva
    -------
    ValueError
        Con l'elenco delle costanti che non coincidono.
    """
    f = params.fixed
    expected = {
        "inactive_lambda": INACTIVE_LAMBDA,
        "module3_candidate": CHOSEN_CANDIDATE,
        "lambda_min": 0.0,
        "lambda_max": 1.0,
        "out_of_support_min_count": MIN_CELL_COUNT,
        "devig_method": "shin",
        "d_series": "delta",
        "c1_n_boot": C1_N_BOOT,
        "c1_alpha": ALPHA,
        "c1_alarm_count": "onsets",
    }
    bad = [f"{k}: file {f[k]!r}, code {v!r}" for k, v in expected.items() if f[k] != v]
    if f["fallback_policy"] not in FALLBACK_POLICIES:
        bad.append(f"fallback_policy: {f['fallback_policy']!r} not in {FALLBACK_POLICIES}")
    if bad:
        raise ValueError("frozen params differ from code constants: " + "; ".join(bad))


def arm_windows(params: FrozenParams) -> dict[str, int]:
    """W congelata per C1, C2_global e C2."""
    c = params.calibrated
    return {"C1": int(c["c1_window"]), "C2_global": int(c["c2_global_window"]), "C2": int(c["c2_window"])}


def build_supervisors(params: FrozenParams, inp: SeasonInput, history: SupervisorHistory | None = None,
                      devig_method: str = "shin") -> dict[int, Module2Supervisor]:
    """Un supervisore del Modulo 2 per ogni W congelata, condiviso dai bracci e dalle configurazioni."""
    covariates = list(params.fixed["covariates"])
    return {w: Module2Supervisor(inp.season, inp.dates, inp.x, covariates, w, history=history,
                                 devig_method=devig_method)
            for w in sorted(set(arm_windows(params).values()))}


def build_frozen_agents(params: FrozenParams, min_stake: float, supervisors: Mapping[int, Module2Supervisor],
                        shin: SharedShin, fit: str, arms: Sequence[str] = AGENT_ORDER) -> list[Agent]:
    """Agenti nell'ordine AGENT_ORDER (E solo con F > 0), con i parametri del solo file congelato."""
    c, f = params.calibrated, params.fixed
    windows = arm_windows(params)
    builders = {
        "A": lambda: FractionalKellyAgent("A", lam=AGENT_A_LAMBDA),
        "B_0.25": lambda: FractionalKellyAgent("B_0.25", lam=AGENT_B_LAMBDAS[0]),
        "B_0.10": lambda: FractionalKellyAgent("B_0.10", lam=AGENT_B_LAMBDAS[1]),
        "D_ADWIN": lambda: RecordingDAgent("D_ADWIN", "adwin", params.adwin_params(), float(c["d_adwin_kappa"]),
                                           shin, float(f["d_base_lambda"])),
        "D_PH": lambda: RecordingDAgent("D_PH", "page_hinkley", params.page_hinkley_params(),
                                        float(c["d_page_hinkley_kappa"]), shin, float(f["d_base_lambda"])),
        "C0": lambda: FractionalKellyAgent("C0", lam=float(f["c0_lambda"])),
        "C1": lambda: C1Agent("C1", supervisors[windows["C1"]], float(c["c1_kappa"]),
                              float(params.c1_thresholds[fit]), base_lambda=float(f["c0_lambda"])),
        "C2_global": lambda: GradedAgent("C2_global", supervisors[windows["C2_global"]], abstain=False),
        "C2": lambda: GradedAgent("C2", supervisors[windows["C2"]], abstain=True),
        "E": lambda: MinimumStakeAgent("E"),
    }
    return [builders[a]() for a in arms if a != "E" or min_stake > 0.0]


def share_lambda_zero(agent: Agent) -> float:
    """Quota di date con λ = 0 per C1, C2_global, C2 e D; NaN per gli altri agenti."""
    if isinstance(agent, C1Agent):
        values = list(agent.lambda_by_date.values())
        return float(np.mean(np.array(values) == 0.0)) if values else math.nan
    if isinstance(agent, GradedAgent):
        values = list(agent.lambda_zero_by_date.values())
        return float(np.mean(values)) if values else math.nan
    if isinstance(agent, RecordingDAgent):
        values = list(agent.lambda_by_date.values())
        return float(np.mean(np.array(values) == 0.0)) if values else math.nan
    return math.nan


def n_alarms(agent: Agent) -> float:
    """Allarmi: accensioni per C1, allarmi del detector per D; NaN per gli altri agenti."""
    if isinstance(agent, C1Agent):
        return float(agent.n_onsets)
    if isinstance(agent, RecordingDAgent):
        return float(agent.n_alarms)
    return math.nan
