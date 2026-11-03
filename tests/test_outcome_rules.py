"""Test: punto di estensione candidate_outcomes di Agent e regole R1, R2, R3 del lavoratore."""

import numpy as np
import pytest

from shk.kelly.agents import Agent, DateResults, DateView, FractionalKellyAgent, NO_BET, estimated_expected_values
from shk.kelly.outcome_rules import (
    OUTCOME_RULES,
    max_edge_outcomes,
    max_ev_outcomes,
    max_prob_outcomes,
    with_outcome_rule,
)
from shk.market.devig import devig_probabilities
from shk.model.agent_c import C1Agent, GradedAgent, Module2Supervisor

DAY = np.datetime64("2010-08-14", "ns")
# Partita 0: EV massimo sul pareggio, p̂ massima sulla casa (EV casa < 0); partita 1: nessun EV > 0
PROBS = np.array([[0.50, 0.30, 0.20], [0.40, 0.30, 0.30]])
ODDS = np.array([[1.90, 3.80, 4.50], [2.20, 3.10, 3.00]])


class _ConstantCandidate(Agent):
    """Agente con esito candidato prefissato e frazione 0.01."""

    def __init__(self, name: str, candidates: object) -> None:
        super().__init__(name)
        self._candidates = candidates

    def candidate_outcomes(self, view: DateView) -> np.ndarray:
        return self._candidates

    def stake_fractions(self, view: DateView, p_hat: np.ndarray, b: np.ndarray) -> np.ndarray:
        return np.full(p_hat.shape[0], 0.01)


def test_default_candidate_is_max_ev():
    ev = estimated_expected_values(PROBS, ODDS)
    agent = FractionalKellyAgent("B", lam=0.25)
    view = DateView(DAY, PROBS, ODDS)
    np.testing.assert_array_equal(agent.candidate_outcomes(view), ev.argmax(axis=1))
    decision = agent.decide(view)
    assert list(decision.outcomes) == [1, NO_BET]


def test_override_selects_candidate_only_with_positive_ev():
    view = DateView(DAY, PROBS, ODDS)
    # Casa nella partita 0 ha EV 0.5·1.9 − 1 < 0: non selezionata; pareggio nella partita 1: 0.3·3.1 − 1 < 0
    decision = _ConstantCandidate("x", np.array([0, 1])).decide(view)
    assert list(decision.outcomes) == [NO_BET, NO_BET]
    decision = _ConstantCandidate("x", np.array([2, 0])).decide(view)
    assert list(decision.outcomes) == [NO_BET, NO_BET]
    decision = _ConstantCandidate("x", np.array([1, 1])).decide(view)
    assert list(decision.outcomes) == [1, NO_BET]
    # Il ripiego resta l'EV massimo sulla data, qualunque sia la regola
    assert (decision.fallback_match, decision.fallback_outcome) == (0, 1)


@pytest.mark.parametrize("bad, error", [
    ([1, 1], TypeError),
    (np.array([1.0, 1.0]), TypeError),
    (np.array([1]), ValueError),
    (np.array([1, 3]), ValueError),
    (np.array([-1, 0]), ValueError),
])
def test_invalid_candidates_raise(bad, error):
    with pytest.raises(error):
        _ConstantCandidate("x", bad).decide(DateView(DAY, PROBS, ODDS))


def test_rules():
    np.testing.assert_array_equal(max_ev_outcomes(PROBS, ODDS), [1, 1])
    np.testing.assert_array_equal(max_prob_outcomes(PROBS, ODDS), [0, 0])
    q = devig_probabilities(ODDS, "shin")
    np.testing.assert_array_equal(max_edge_outcomes(PROBS, ODDS), np.argmax(PROBS - q, axis=1))
    assert max_edge_outcomes(np.zeros((0, 3)), np.zeros((0, 3))).shape == (0,)
    assert tuple(OUTCOME_RULES) == ("R1", "R2", "R3")


def test_with_outcome_rule_builds_agent_subclass():
    cls = with_outcome_rule(FractionalKellyAgent, "R3")
    assert issubclass(cls, FractionalKellyAgent)
    assert cls.outcome_rule is max_prob_outcomes
    agent = cls("R3_brake", lam=0.25)
    # R3 sceglie la casa nella partita 0, ma l'EV è negativo: nessuna puntata volontaria
    assert list(agent.decide(DateView(DAY, PROBS, ODDS)).outcomes) == [NO_BET, NO_BET]
    with pytest.raises(ValueError):
        with_outcome_rule(FractionalKellyAgent, "R4")
    # Funziona con gli agenti del supervisore (candidate_outcomes è ammesso dalla base)
    assert issubclass(with_outcome_rule(C1Agent, "R2"), C1Agent)
    assert issubclass(with_outcome_rule(GradedAgent, "R2"), GradedAgent)


def test_window_candidate_ev_follows_rule():
    """EV̂ candidato della finestra B: con R1 coincide con quello del Modulo 3, con R3 è l'EV di argmax p̂."""
    rng = np.random.default_rng(4)
    days = (np.datetime64("2010-08-14") + np.arange(9) * np.timedelta64(7, "D")).astype("datetime64[ns]")
    sup = Module2Supervisor("s", days, rng.normal(size=(9, 1)), ["c"], 3)
    probs = rng.dirichlet([4, 3, 3], size=9)
    odds = 1.0 / (rng.dirichlet([4, 3, 3], size=9) * 1.05)
    for i, d in enumerate(days):
        sup.observe(DateResults(d, probs[i:i + 1], odds[i:i + 1], np.array([[i % 3]])))
    ev = estimated_expected_values(probs, odds)
    rows = np.arange(5, 8)
    np.testing.assert_array_equal(sup.window_candidate_ev(days[8], max_ev_outcomes), ev[rows].max(axis=1))
    np.testing.assert_array_equal(sup.window_candidate_ev(days[8], max_prob_outcomes),
                                  ev[rows, probs[rows].argmax(axis=1)])
    assert sup.window_candidate_ev(days[5], max_ev_outcomes) is None
