"""Agenti delle esecuzioni congelate costruiti solo dai parametri congelati.

A (Kelly pieno) e B_0.25 (quarto di Kelly) sono il lavoratore senza supervisore: non hanno
parametri calibrati. I parametri dello schema del relatore (W, κ, soglia strutturale) vengono
da FrozenParams (shk.model.frozen_params.load_frozen_params). Le costanti che il codice usa al
proprio interno senza riceverle come argomento sono confrontate con il file da
check_frozen_constants, che solleva un errore se non coincidono: metodo di de-vigging,
politica del ripiego, B e α della soglia strutturale.

Catena di Oaxaca-Blinder tagliata alla stagione (decisione del programmatore del 2026-10-12):
un supervisore per stagione, senza storia.
"""

import math
from collections.abc import Sequence
from typing import Final

import numpy as np

from shk.kelly.agents import AGENT_A_LAMBDA, AGENT_B_LAMBDA, Agent, FractionalKellyAgent
from shk.kelly.environment import FALLBACK_POLICIES
from shk.model.agent_c import N_BOOT, Module2Supervisor, SchemeAgent
from shk.model.frozen_params import FrozenParams
from shk.model.season_input import SeasonInput
from shk.stats.false_rejection import ALPHA

AGENT_ORDER: Final[tuple[str, ...]] = ("A", "B_0.25")


def check_frozen_constants(params: FrozenParams) -> None:
    """Verifica che le costanti interne al codice coincidano con il file congelato.

    Solleva
    -------
    ValueError
        Con l'elenco delle costanti che non coincidono.
    """
    f = params.fixed
    expected = {
        "devig_method": "shin",
        "c1_n_boot": N_BOOT,
        "c1_alpha": ALPHA,
        "c1_alarm_count": "onsets",
    }
    bad = [f"{k}: file {f[k]!r}, code {v!r}" for k, v in expected.items() if f[k] != v]
    if f["fallback_policy"] not in FALLBACK_POLICIES:
        bad.append(f"fallback_policy: {f['fallback_policy']!r} not in {FALLBACK_POLICIES}")
    if bad:
        raise ValueError("frozen params differ from code constants: " + "; ".join(bad))


def scheme_window(params: FrozenParams) -> int:
    """W congelata delle finestre A e B dello schema (chiave c1_window)."""
    return int(params.calibrated["c1_window"])


def build_supervisor(params: FrozenParams, inp: SeasonInput, devig_method: str = "shin") -> Module2Supervisor:
    """Il supervisore della stagione alla W congelata, condiviso dai bracci e dalle configurazioni."""
    return Module2Supervisor(inp.season, inp.dates, inp.x, list(params.fixed["covariates"]), scheme_window(params),
                             devig_method=devig_method)


def build_frozen_agents(arms: Sequence[str] = AGENT_ORDER) -> list[Agent]:
    """Agenti nell'ordine dato: A e B_0.25."""
    builders = {
        "A": lambda: FractionalKellyAgent("A", lam=AGENT_A_LAMBDA),
        "B_0.25": lambda: FractionalKellyAgent("B_0.25", lam=AGENT_B_LAMBDA),
    }
    return [builders[a]() for a in arms]


def share_lambda_zero(agent: Agent) -> float:
    """Quota di date con λ = 0 per lo schema; NaN per gli altri agenti."""
    if isinstance(agent, SchemeAgent):
        values = list(agent.lambda_by_date.values())
        return float(np.mean(np.array(values) == 0.0)) if values else math.nan
    return math.nan


def n_alarms(agent: Agent) -> float:
    """Accensioni dell'allarme dello schema; NaN per gli altri agenti."""
    if isinstance(agent, SchemeAgent):
        return float(agent.n_onsets)
    return math.nan
