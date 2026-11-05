"""Regole di scelta dell'esito del lavoratore (disegno del lavoratore, opzione A).

Una regola riceve probabilità stimate p̂ (n, 3) e quote lorde o (n, 3) e restituisce l'esito
candidato di ogni partita; Agent.decide lo seleziona solo se il suo EV stimato p̂·o − 1 è > 0,
quindi una regola cambia quale esito si punta, mai la formula della frazione. Nessuna regola
ha parametri liberi:
- R1, valore atteso massimo: argmax(p̂·o − 1), il default di Agent.candidate_outcomes;
- R2, maggior vantaggio sul mercato: argmax(p̂ − q), con q le probabilità di Shin dalle
  quote della data (usa il mercato nella scelta);
- R3, esito più probabile: argmax(p̂).
Parità risolte da np.argmax nell'ordine H, D, A.

with_outcome_rule(cls, rule) costruisce la sottoclasse di un agente che usa la regola in
candidate_outcomes ed espone la regola come attributo di classe outcome_rule.
"""

from collections.abc import Callable
from typing import Final

import numpy as np

from shk.kelly.agents import Agent, DateView, estimated_expected_values
from shk.market.devig import devig_probabilities

OutcomeRule = Callable[[np.ndarray, np.ndarray], np.ndarray]


def max_ev_outcomes(probs: np.ndarray, odds: np.ndarray) -> np.ndarray:
    """R1: esito con EV stimato massimo."""
    return np.argmax(estimated_expected_values(probs, odds), axis=1)


# q di Shin per terna di quote: la stessa terna torna nei ricampionamenti e fra gli agenti
_SHIN_CACHE: dict[bytes, np.ndarray] = {}
_SHIN_CACHE_MAX: Final[int] = 200_000


def _shin_rows(odds: np.ndarray) -> np.ndarray:
    """q di Shin riga per riga, con la cache per terna di quote (stesso valore di devig_probabilities)."""
    o = np.ascontiguousarray(odds, dtype=np.float64)
    keys = [row.tobytes() for row in o]
    missing = [i for i, k in enumerate(keys) if k not in _SHIN_CACHE]
    if missing:
        if len(_SHIN_CACHE) + len(missing) > _SHIN_CACHE_MAX:
            _SHIN_CACHE.clear()
        q_missing = devig_probabilities(o[missing], "shin")
        for i, q in zip(missing, q_missing):
            _SHIN_CACHE[keys[i]] = q
    return np.stack([_SHIN_CACHE[k] for k in keys])


def max_edge_outcomes(probs: np.ndarray, odds: np.ndarray) -> np.ndarray:
    """R2: esito con p̂ − q massimo, q di Shin."""
    p = np.asarray(probs, dtype=np.float64)
    if p.shape[0] == 0:
        return np.zeros(0, dtype=np.int64)
    return np.argmax(p - _shin_rows(odds), axis=1)


def max_prob_outcomes(probs: np.ndarray, odds: np.ndarray) -> np.ndarray:
    """R3: esito con p̂ massimo."""
    return np.argmax(np.asarray(probs, dtype=np.float64), axis=1)


OUTCOME_RULES: Final[dict[str, OutcomeRule]] = {
    "R1": max_ev_outcomes,
    "R2": max_edge_outcomes,
    "R3": max_prob_outcomes,
}


def with_outcome_rule(agent_cls: type[Agent], rule_name: str) -> type[Agent]:
    """Sottoclasse di agent_cls con l'esito candidato della regola rule_name (vedi modulo)."""
    if rule_name not in OUTCOME_RULES:
        raise ValueError(f"rule_name must be one of {tuple(OUTCOME_RULES)}, got {rule_name!r}")
    rule = OUTCOME_RULES[rule_name]

    def candidate_outcomes(self: Agent, view: DateView) -> np.ndarray:
        """Esito candidato della regola del lavoratore."""
        return rule(view.probs, view.odds)

    return type(f"{agent_cls.__name__}{rule_name}", (agent_cls,),
                {"candidate_outcomes": candidate_outcomes, "outcome_rule": staticmethod(rule),
                 "__doc__": f"{agent_cls.__name__} con la regola {rule_name} di scelta dell'esito."})
