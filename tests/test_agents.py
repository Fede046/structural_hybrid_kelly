"""Test per il modulo shk.kelly.agents: viste di data, decisioni e agenti A, B, E (Task 33 / US-C6.1)."""

import ast
import dataclasses
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pytest

from shk.kelly.agents import (
    AGENT_A_LAMBDA,
    AGENT_B_LAMBDAS,
    NO_BET,
    Agent,
    AgentDecision,
    DateView,
    FractionalKellyAgent,
    MinimumStakeAgent,
    estimated_expected_values,
)
from shk.kelly.staking import OUTCOME_LABELS, select_baseline_d_bets

REPO_ROOT = Path(__file__).resolve().parents[1]
KELLY_DIR = REPO_ROOT / "src" / "shk" / "kelly"
AGENTS_PATH = KELLY_DIR / "agents.py"

# Seed e numero di viste casuali per l'equivalenza con C5.3 e la coerenza fra agenti
SEED_T33 = 20261009
N_MIXED_VIEWS = 160
N_NON_POSITIVE_VIEWS = 80

DATE = np.datetime64("2015-09-12")


# ---------------------------------------------------------------------------
# Funzioni di supporto
# ---------------------------------------------------------------------------


def _make_view(probs: list[list[float]], odds: list[list[float]]) -> DateView:
    """Costruisce una DateView da liste annidate di probabilità e quote."""
    return DateView(
        date=DATE,
        probs=np.array(probs, dtype=np.float64),
        odds=np.array(odds, dtype=np.float64),
    )


def _random_views(seed: int = SEED_T33) -> list[DateView]:
    """Genera viste casuali: prima viste miste, poi viste senza esiti a EV stimato positivo.

    Viste miste: probabilità Dirichlet(2, 2, 2) e quote uniformi in (1.05, 10).
    Viste senza EV > 0: quote o = 1 / (p + r (1 - p)) con r uniforme in (0.02, 0.2),
    per cui p * o < 1 e o > 1.
    """
    rng = np.random.default_rng(seed)
    views: list[DateView] = []
    for i in range(N_MIXED_VIEWS + N_NON_POSITIVE_VIEWS):
        n_matches = int(rng.integers(1, 11))
        probs = rng.dirichlet((2.0, 2.0, 2.0), size=n_matches)
        if i < N_MIXED_VIEWS:
            odds = rng.uniform(1.05, 10.0, size=(n_matches, 3))
        else:
            r = rng.uniform(0.02, 0.2, size=(n_matches, 3))
            odds = 1.0 / (probs + r * (1.0 - probs))
        views.append(DateView(date=DATE + np.timedelta64(i, "D"), probs=probs, odds=odds))
    return views


def _valid_decision_kwargs() -> dict[str, object]:
    """Restituisce argomenti validi per AgentDecision su tre partite."""
    return {
        "outcomes": np.array([0, NO_BET, 2], dtype=np.int64),
        "fractions": np.array([0.1, 0.0, 0.2], dtype=np.float64),
        "fallback_match": 0,
        "fallback_outcome": 2,
    }


class _SpyAgent(Agent):
    """Agente che registra gli argomenti ricevuti da stake_fractions e restituisce zeri."""

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.calls: list[tuple[DateView, np.ndarray, np.ndarray]] = []

    def stake_fractions(self, view: DateView, p_hat: np.ndarray, b: np.ndarray) -> np.ndarray:
        self.calls.append((view, p_hat, b))
        return np.zeros(p_hat.shape[0], dtype=np.float64)


class _WritingAgent(Agent):
    """Agente che tenta di scrivere su uno degli input di stake_fractions."""

    def __init__(self, name: str, target: str) -> None:
        super().__init__(name)
        self.target = target

    def stake_fractions(self, view: DateView, p_hat: np.ndarray, b: np.ndarray) -> np.ndarray:
        if self.target == "p_hat":
            p_hat[0] = 0.5
        elif self.target == "b":
            b[0] = 1.0
        elif self.target == "view_probs":
            view.probs[0, 0] = 0.0
        elif self.target == "view_odds":
            view.odds[0, 0] = 2.0
        elif self.target == "view_probs_setflags":
            view.probs.setflags(write=True)
        elif self.target == "p_hat_setflags":
            p_hat.setflags(write=True)
        return np.zeros(p_hat.shape[0], dtype=np.float64)


class _FixedOutputAgent(Agent):
    """Agente che restituisce da stake_fractions il valore prodotto da una funzione di k."""

    def __init__(self, name: str, factory: Callable[[int], object]) -> None:
        super().__init__(name)
        self.factory = factory

    def stake_fractions(self, view: DateView, p_hat: np.ndarray, b: np.ndarray) -> np.ndarray:
        return self.factory(p_hat.shape[0])  # type: ignore[return-value]


# Vista con due partite, entrambe con un esito a EV stimato positivo (k = 2)
POSITIVE_VIEW_PROBS = [[0.5, 0.25, 0.25], [0.25, 0.25, 0.5]]
POSITIVE_VIEW_ODDS = [[2.5, 2.0, 2.0], [2.0, 2.0, 2.5]]


# ---------------------------------------------------------------------------
# Criterio 1: validazioni di DateView
# ---------------------------------------------------------------------------


def test_date_view_validations() -> None:
    """Verifica TypeError e ValueError del costruttore di DateView."""
    probs = np.array([[0.5, 0.25, 0.25]])
    odds = np.array([[2.0, 4.0, 4.0]])

    # Tipi errati
    with pytest.raises(TypeError, match="date must be a numpy.datetime64"):
        DateView(date="2015-09-12", probs=probs, odds=odds)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="probs must be a numpy.ndarray"):
        DateView(date=DATE, probs=[[0.5, 0.25, 0.25]], odds=odds)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="odds must be a numpy.ndarray"):
        DateView(date=DATE, probs=probs, odds=[[2.0, 4.0, 4.0]])  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="probs must have a real integer or floating dtype"):
        DateView(date=DATE, probs=np.array([[True, False, False]]), odds=odds)
    with pytest.raises(TypeError, match="odds must have a real integer or floating dtype"):
        DateView(date=DATE, probs=probs, odds=odds.astype(np.complex128))
    with pytest.raises(TypeError, match="odds must have a real integer or floating dtype"):
        DateView(date=DATE, probs=probs, odds=np.array([["2.0", "4.0", "4.0"]]))

    # Data NaT
    with pytest.raises(ValueError, match="NaT"):
        DateView(date=np.datetime64("NaT", "D"), probs=probs, odds=odds)

    # Forme
    with pytest.raises(ValueError, match="shape \\(n, 3\\)"):
        DateView(date=DATE, probs=np.array([0.5, 0.25, 0.25]), odds=odds)
    with pytest.raises(ValueError, match="shape \\(n, 3\\)"):
        DateView(date=DATE, probs=np.array([[0.5, 0.5]]), odds=np.array([[2.0, 2.0]]))
    with pytest.raises(ValueError, match="at least one match"):
        DateView(date=DATE, probs=np.empty((0, 3)), odds=np.empty((0, 3)))
    with pytest.raises(ValueError, match="same shape"):
        DateView(date=DATE, probs=probs, odds=np.vstack([odds, odds]))

    # Valori non finiti
    with pytest.raises(ValueError, match="probs must contain only finite values"):
        DateView(date=DATE, probs=np.array([[np.nan, 0.5, 0.5]]), odds=odds)
    with pytest.raises(ValueError, match="odds must contain only finite values"):
        DateView(date=DATE, probs=probs, odds=np.array([[np.inf, 4.0, 4.0]]))

    # Probabilità fuori da [0, 1] e righe che non sommano a 1
    with pytest.raises(ValueError, match="values in \\[0, 1\\]"):
        DateView(date=DATE, probs=np.array([[1.2, -0.1, -0.1]]), odds=odds)
    with pytest.raises(ValueError, match="sum to 1"):
        DateView(date=DATE, probs=np.array([[0.5, 0.25, 0.25 + 2e-9]]), odds=odds)
    # Entro 1e-9 la riga è accettata; probabilità 0 e 1 ammesse
    DateView(date=DATE, probs=np.array([[0.5, 0.25, 0.25 + 5e-10]]), odds=odds)
    DateView(date=DATE, probs=np.array([[1.0, 0.0, 0.0]]), odds=odds)

    # Quote <= 1
    with pytest.raises(ValueError, match="strictly greater than 1.0"):
        DateView(date=DATE, probs=probs, odds=np.array([[1.0, 4.0, 4.0]]))
    with pytest.raises(ValueError, match="strictly greater than 1.0"):
        DateView(date=DATE, probs=probs, odds=np.array([[0.5, 4.0, 4.0]]))


# ---------------------------------------------------------------------------
# Criterio 2: copie non scrivibili di DateView
# ---------------------------------------------------------------------------


def test_date_view_copies_read_only() -> None:
    """Verifica che DateView salvi copie float64 non scrivibili e senza memoria condivisa."""
    probs_in = np.array([[0.5, 0.25, 0.25], [0.25, 0.5, 0.25]], dtype=np.float32)
    odds_in = np.array([[2, 4, 4], [4, 2, 4]], dtype=np.int64)
    view = DateView(date=DATE, probs=probs_in, odds=odds_in)

    for field in (view.probs, view.odds):
        assert field.dtype == np.float64
        assert field.flags.writeable is False
    assert not np.shares_memory(view.probs, probs_in)
    assert not np.shares_memory(view.odds, odds_in)

    # La modifica degli array originali non si propaga alla vista
    probs_in[0, 0] = 0.0
    odds_in[0, 0] = 9
    assert view.probs[0, 0] == 0.5
    assert view.odds[0, 0] == 2.0

    # Scrittura diretta e riattivazione della scrittura sollevano l'errore di NumPy
    with pytest.raises(ValueError, match="read-only"):
        view.probs[0, 0] = 0.1
    with pytest.raises(ValueError, match="WRITEABLE"):
        view.odds.setflags(write=True)

    # Campi non riassegnabili
    with pytest.raises(dataclasses.FrozenInstanceError):
        view.probs = np.array([[1.0, 0.0, 0.0]])  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Specifica 2: EV stimato
# ---------------------------------------------------------------------------


def test_estimated_expected_values_values_and_validations() -> None:
    """Verifica la formula p_hat * o - 1, il dtype e le validazioni."""
    probs = np.array([[0.5, 0.25, 0.25], [0.25, 0.375, 0.375]])
    odds = np.array([[2.5, 5.0, 2.0], [2.0, 4.0, 4.0]])

    ev = estimated_expected_values(probs, odds)
    assert ev.dtype == np.float64
    assert ev.shape == (2, 3)
    assert np.array_equal(ev, np.array([[0.25, 0.25, -0.5], [-0.5, 0.5, 0.5]]))

    with pytest.raises(TypeError, match="probs must be a numpy.ndarray"):
        estimated_expected_values(probs.tolist(), odds)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="odds must have a real integer or floating dtype"):
        estimated_expected_values(probs, odds.astype(bool))
    with pytest.raises(ValueError, match="shape \\(n, 3\\)"):
        estimated_expected_values(probs[:, :2], odds[:, :2])
    with pytest.raises(ValueError, match="at least one match"):
        estimated_expected_values(np.empty((0, 3)), np.empty((0, 3)))
    with pytest.raises(ValueError, match="same shape"):
        estimated_expected_values(probs, odds[:1])
    with pytest.raises(ValueError, match="finite"):
        estimated_expected_values(probs, np.array([[np.nan, 4.0, 4.0], [2.0, 4.0, 4.0]]))


# ---------------------------------------------------------------------------
# Criterio 1: validazioni di AgentDecision
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field, value, match",
    [
        ("outcomes", [0, -1, 2], "outcomes must be a numpy.ndarray"),
        ("outcomes", np.array([0.0, -1.0, 2.0]), "outcomes must have an integer dtype"),
        ("outcomes", np.array([True, False, True]), "outcomes must have an integer dtype"),
        ("fractions", [0.1, 0.0, 0.2], "fractions must be a numpy.ndarray"),
        ("fractions", np.array([0, 0, 0]), "fractions must have a floating dtype"),
        ("fallback_match", 1.0, "fallback_match must be an int"),
        ("fallback_match", True, "fallback_match must be an int"),
        ("fallback_outcome", "0", "fallback_outcome must be an int"),
    ],
)
def test_agent_decision_type_validations(field: str, value: object, match: str) -> None:
    """Verifica i TypeError di AgentDecision per ciascun campo di tipo errato."""
    kwargs = _valid_decision_kwargs()
    kwargs[field] = value
    with pytest.raises(TypeError, match=match):
        AgentDecision(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "field, value, match",
    [
        ("outcomes", np.array([[0, -1, 2]]), "1-dimensional"),
        ("outcomes", np.array([], dtype=np.int64), "at least one match"),
        ("fractions", np.array([0.1, 0.0]), "fractions must have shape"),
        ("outcomes", np.array([0, 3, 2]), "only -1, 0, 1, 2"),
        ("outcomes", np.array([0, -2, 2]), "only -1, 0, 1, 2"),
        ("fractions", np.array([0.1, 0.0, np.nan]), "finite"),
        ("fractions", np.array([0.1, 0.0, np.inf]), "finite"),
        ("fractions", np.array([-0.1, 0.0, 0.2]), "\\[0, 1\\)"),
        ("fractions", np.array([1.0, 0.0, 0.2]), "\\[0, 1\\)"),
        ("fractions", np.array([0.1, 0.3, 0.2]), "zero where outcomes is -1"),
        ("fallback_match", 3, "fallback_match must be in"),
        ("fallback_match", -1, "fallback_match must be in"),
        ("fallback_outcome", 3, "fallback_outcome must be 0, 1 or 2"),
        ("fallback_outcome", -1, "fallback_outcome must be 0, 1 or 2"),
    ],
)
def test_agent_decision_value_validations(field: str, value: object, match: str) -> None:
    """Verifica i ValueError di AgentDecision per forme e valori non ammessi."""
    kwargs = _valid_decision_kwargs()
    kwargs[field] = value
    with pytest.raises(ValueError, match=match):
        AgentDecision(**kwargs)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Criterio 2: copie non scrivibili di AgentDecision
# ---------------------------------------------------------------------------


def test_agent_decision_read_only_copies() -> None:
    """Verifica che AgentDecision salvi copie int64 e float64 non scrivibili e interi Python."""
    outcomes_in = np.array([0, NO_BET, 2], dtype=np.int32)
    fractions_in = np.array([0.1, 0.0, 0.2], dtype=np.float32)
    decision = AgentDecision(
        outcomes=outcomes_in,
        fractions=fractions_in,
        fallback_match=np.int64(1),
        fallback_outcome=np.int32(2),
    )

    assert decision.outcomes.dtype == np.int64
    assert decision.fractions.dtype == np.float64
    assert type(decision.fallback_match) is int
    assert type(decision.fallback_outcome) is int
    for field in (decision.outcomes, decision.fractions):
        assert field.flags.writeable is False
    assert not np.shares_memory(decision.outcomes, outcomes_in)
    assert not np.shares_memory(decision.fractions, fractions_in)

    with pytest.raises(ValueError, match="read-only"):
        decision.fractions[0] = 0.5
    with pytest.raises(ValueError, match="WRITEABLE"):
        decision.outcomes.setflags(write=True)
    with pytest.raises(dataclasses.FrozenInstanceError):
        decision.fallback_match = 2  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Criterio 1: Agent.__init__ e FractionalKellyAgent
# ---------------------------------------------------------------------------


def test_agent_name_validations() -> None:
    """Verifica la validazione del nome, la proprietà in sola lettura e l'astrattezza di Agent."""
    with pytest.raises(TypeError):
        Agent("abstract")  # type: ignore[abstract]

    for bad_name in (123, None, b"E"):
        with pytest.raises(TypeError, match="name must be a str"):
            MinimumStakeAgent(bad_name)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="non-empty"):
        MinimumStakeAgent("")
    with pytest.raises(ValueError, match="non-empty"):
        FractionalKellyAgent("", 0.25)

    agent = MinimumStakeAgent("E")
    assert agent.name == "E"
    with pytest.raises(AttributeError):
        agent.name = "F"  # type: ignore[misc]


def test_decide_rejects_non_date_view() -> None:
    """Verifica che decide sollevi TypeError se non riceve una DateView."""
    agent = MinimumStakeAgent("E")
    with pytest.raises(TypeError, match="view must be a DateView"):
        agent.decide((DATE, np.array([[0.5, 0.25, 0.25]]), np.array([[2.0, 4.0, 4.0]])))  # type: ignore[arg-type]


def test_fractional_kelly_lam_validations() -> None:
    """Verifica i tipi e l'intervallo (0, 1] del moltiplicatore lam."""
    for bad_lam in (True, 1, "0.25", None):
        with pytest.raises(TypeError, match="lam must be a float"):
            FractionalKellyAgent("B", bad_lam)  # type: ignore[arg-type]
    for bad_lam in (float("nan"), float("inf"), 0.0, -0.25, 1.5, np.float64(1.0000001)):
        with pytest.raises(ValueError, match="lam must be finite and in \\(0, 1\\]"):
            FractionalKellyAgent("B", bad_lam)

    assert FractionalKellyAgent("A", 1.0).lam == 1.0
    agent_b = FractionalKellyAgent("B", np.float64(0.25))
    assert agent_b.lam == 0.25
    assert type(agent_b.lam) is float
    with pytest.raises(AttributeError):
        agent_b.lam = 0.5  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Criterio 3: scritture vietate e uscite non conformi di stake_fractions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "target, match",
    [
        ("p_hat", "read-only"),
        ("b", "read-only"),
        ("view_probs", "read-only"),
        ("view_odds", "read-only"),
        ("view_probs_setflags", "WRITEABLE"),
        ("p_hat_setflags", "WRITEABLE"),
    ],
)
def test_stake_fractions_write_raises(target: str, match: str) -> None:
    """Verifica che una scrittura su p_hat, b o sugli array della vista faccia fallire decide."""
    view = _make_view(POSITIVE_VIEW_PROBS, POSITIVE_VIEW_ODDS)
    probs_before = np.array(view.probs)
    agent = _WritingAgent("writer", target)
    with pytest.raises(ValueError, match=match):
        agent.decide(view)
    assert np.array_equal(view.probs, probs_before)


@pytest.mark.parametrize(
    "factory, error",
    [
        (lambda k: [0.1] * k, TypeError),
        (lambda k: np.zeros(k, dtype=np.int64), TypeError),
        (lambda k: np.zeros(k, dtype=bool), TypeError),
        (lambda k: np.zeros(k + 1, dtype=np.float64), ValueError),
        (lambda k: np.zeros((k, 1), dtype=np.float64), ValueError),
        (lambda k: np.full(k, np.nan), ValueError),
        (lambda k: np.full(k, np.inf), ValueError),
        (lambda k: np.full(k, -0.1), ValueError),
        (lambda k: np.full(k, 1.0), ValueError),
        (lambda k: np.full(k, 1.5), ValueError),
    ],
)
def test_stake_fractions_invalid_output_raises(
    factory: Callable[[int], object], error: type[Exception]
) -> None:
    """Verifica TypeError per uscite non ndarray o non float e ValueError per forma e valori."""
    view = _make_view(POSITIVE_VIEW_PROBS, POSITIVE_VIEW_ODDS)
    agent = _FixedOutputAgent("fixed", factory)
    with pytest.raises(error):
        agent.decide(view)


def test_stake_fractions_inputs_shape_and_flags() -> None:
    """Verifica forma (k,), valori e sola lettura di p_hat e b, anche con k = 0."""
    agent = _SpyAgent("spy")

    # k = 2: entrambe le partite hanno un esito selezionato
    view = _make_view(POSITIVE_VIEW_PROBS, POSITIVE_VIEW_ODDS)
    agent.decide(view)
    received_view, p_hat, b = agent.calls[-1]
    assert received_view is view
    assert p_hat.shape == (2,) and b.shape == (2,)
    assert p_hat.dtype == np.float64 and b.dtype == np.float64
    assert p_hat.flags.writeable is False and b.flags.writeable is False
    assert np.array_equal(p_hat, np.array([0.5, 0.5]))
    assert np.array_equal(b, np.array([1.5, 1.5]))

    # k = 0: nessun esito a EV stimato positivo
    view_none = _make_view([[0.5, 0.25, 0.25]], [[1.5, 3.0, 3.0]])
    agent.decide(view_none)
    _, p_hat_0, b_0 = agent.calls[-1]
    assert p_hat_0.shape == (0,) and b_0.shape == (0,)
    assert p_hat_0.flags.writeable is False and b_0.flags.writeable is False


def test_full_kelly_with_certain_probability_raises() -> None:
    """Documenta la scelta approvata: con lam = 1 e p_hat = 1 la frazione vale 1 e decide fallisce."""
    view = _make_view([[1.0, 0.0, 0.0]], [[1.5, 3.0, 3.0]])
    with pytest.raises(ValueError, match="\\[0, 1\\)"):
        FractionalKellyAgent("A", AGENT_A_LAMBDA).decide(view)
    decision_b = FractionalKellyAgent("B", 0.25).decide(view)
    assert np.array_equal(decision_b.fractions, np.array([0.25]))


# ---------------------------------------------------------------------------
# Criterio 4: ridefinizioni vietate
# ---------------------------------------------------------------------------


class _DecideMixin:
    """Mixin che fornisce un proprio decide, usato per verificare il vincolo via MRO."""

    def decide(self, view: DateView) -> None:
        return None


def _define_overriding_decide() -> type:
    class BadAgent(Agent):
        def decide(self, view: DateView) -> AgentDecision:  # type: ignore[override]
            raise NotImplementedError

        def stake_fractions(self, view: DateView, p_hat: np.ndarray, b: np.ndarray) -> np.ndarray:
            return np.zeros(p_hat.shape[0])

    return BadAgent


def _define_overriding_name() -> type:
    class BadAgent(Agent):
        @property
        def name(self) -> str:  # type: ignore[override]
            return "other"

        def stake_fractions(self, view: DateView, p_hat: np.ndarray, b: np.ndarray) -> np.ndarray:
            return np.zeros(p_hat.shape[0])

    return BadAgent


def _define_overriding_init_subclass() -> type:
    class BadAgent(Agent):
        def __init_subclass__(cls, **kwargs: object) -> None:
            super().__init_subclass__()

        def stake_fractions(self, view: DateView, p_hat: np.ndarray, b: np.ndarray) -> np.ndarray:
            return np.zeros(p_hat.shape[0])

    return BadAgent


def _define_decide_as_attribute() -> type:
    class BadAgent(Agent):
        decide = None  # type: ignore[assignment]

        def stake_fractions(self, view: DateView, p_hat: np.ndarray, b: np.ndarray) -> np.ndarray:
            return np.zeros(p_hat.shape[0])

    return BadAgent


def _define_decide_from_mixin() -> type:
    class BadAgent(_DecideMixin, Agent):  # type: ignore[misc]
        def stake_fractions(self, view: DateView, p_hat: np.ndarray, b: np.ndarray) -> np.ndarray:
            return np.zeros(p_hat.shape[0])

    return BadAgent


def _define_kelly_subclass_overriding_decide() -> type:
    class BadAgent(FractionalKellyAgent):
        def decide(self, view: DateView) -> AgentDecision:  # type: ignore[override]
            raise NotImplementedError

    return BadAgent


@pytest.mark.parametrize(
    "definer, member",
    [
        (_define_overriding_decide, "decide"),
        (_define_overriding_name, "name"),
        (_define_overriding_init_subclass, "__init_subclass__"),
        (_define_decide_as_attribute, "decide"),
        (_define_decide_from_mixin, "decide"),
        (_define_kelly_subclass_overriding_decide, "decide"),
    ],
)
def test_subclass_override_forbidden(definer: Callable[[], type], member: str) -> None:
    """Verifica che ridefinire un membro di Agent non ammesso dia TypeError alla definizione."""
    with pytest.raises(TypeError, match=f"must not override Agent.{member}"):
        definer()


def test_subclass_allowed_overrides() -> None:
    """Verifica che __init__, stake_fractions e nuovi metodi e proprietà siano ammessi."""

    class GoodAgent(Agent):
        def __init__(self, name: str, scale: float) -> None:
            super().__init__(name)
            self._scale = scale

        @property
        def scale(self) -> float:
            return self._scale

        def helper(self) -> float:
            return self._scale

        def stake_fractions(self, view: DateView, p_hat: np.ndarray, b: np.ndarray) -> np.ndarray:
            return np.full(p_hat.shape[0], self.helper())

    agent = GoodAgent("good", 0.01)
    decision = agent.decide(_make_view(POSITIVE_VIEW_PROBS, POSITIVE_VIEW_ODDS))
    assert np.array_equal(decision.fractions, np.array([0.01, 0.01]))
    assert agent.scale == 0.01


# ---------------------------------------------------------------------------
# Criterio 5: equivalenza con select_baseline_d_bets (C5.3)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("lam", [AGENT_A_LAMBDA, *AGENT_B_LAMBDAS])
def test_equivalence_with_baseline_d(lam: float) -> None:
    """Verifica esiti e frazioni identici a select_baseline_d_bets con lambda costante.

    Codifica allineata: l'esito stringa di BaselineDBets diventa il suo indice in
    OUTCOME_LABELS (H = 0, D = 1, A = 2), e NO_BET dove l'EV stimato dell'esito scelto,
    probs[j, idx] * bets.odds[j] - 1, non è positivo.
    """
    views = _random_views()
    agent = FractionalKellyAgent("kelly", lam)
    n_views_with_bets = 0
    n_views_without_bets = 0
    mismatches: list[int] = []

    for view_index, view in enumerate(views):
        decision = agent.decide(view)
        n_matches = view.probs.shape[0]
        bets = select_baseline_d_bets(
            np.array(view.probs), np.array(view.odds), np.full(n_matches, lam, dtype=np.float64)
        )
        label_index = np.array([OUTCOME_LABELS.index(o) for o in bets.outcomes], dtype=np.int64)
        chosen_ev = view.probs[np.arange(n_matches), label_index] * bets.odds - 1.0
        expected_outcomes = np.where(chosen_ev > 0.0, label_index, NO_BET)

        if not (
            np.array_equal(decision.outcomes, expected_outcomes)
            and np.array_equal(decision.fractions, bets.fractions)
        ):
            mismatches.append(view_index)

        if np.any(decision.outcomes != NO_BET):
            n_views_with_bets += 1
        else:
            n_views_without_bets += 1

    assert len(views) >= 200
    assert mismatches == [], f"Views differing from select_baseline_d_bets: {mismatches}"
    assert n_views_with_bets > 0
    assert n_views_without_bets >= N_NON_POSITIVE_VIEWS


# ---------------------------------------------------------------------------
# Criterio 6: coerenza fra A, B ed E
# ---------------------------------------------------------------------------


def test_agents_consistency_on_random_views() -> None:
    """Verifica esiti e ripiego identici, frazioni di B = lam * frazioni di A, frazioni di E nulle."""
    agent_a = FractionalKellyAgent("A", AGENT_A_LAMBDA)
    agents_b = [FractionalKellyAgent(f"B_{lam}", lam) for lam in AGENT_B_LAMBDAS]
    agent_e = MinimumStakeAgent("E")

    for view in _random_views():
        decision_a = agent_a.decide(view)
        decision_e = agent_e.decide(view)
        assert np.array_equal(decision_e.outcomes, decision_a.outcomes)
        assert np.array_equal(decision_e.fractions, np.zeros_like(decision_a.fractions))
        assert (decision_e.fallback_match, decision_e.fallback_outcome) == (
            decision_a.fallback_match,
            decision_a.fallback_outcome,
        )
        for agent_b in agents_b:
            decision_b = agent_b.decide(view)
            assert np.array_equal(decision_b.outcomes, decision_a.outcomes)
            assert np.array_equal(decision_b.fractions, agent_b.lam * decision_a.fractions)
            assert (decision_b.fallback_match, decision_b.fallback_outcome) == (
                decision_a.fallback_match,
                decision_a.fallback_outcome,
            )


# ---------------------------------------------------------------------------
# Criterio 7: parità e data senza EV stimato positivo
# ---------------------------------------------------------------------------


def test_tie_within_match_selection_order() -> None:
    """Verifica che a parità di EV fra esiti della stessa partita vinca l'ordine H, D, A."""
    view = _make_view(
        # EV: (0.25, 0.25, -0.5), (-0.5, 0.5, 0.5), (0.25, 0.25, 0.25)
        [[0.5, 0.25, 0.25], [0.25, 0.375, 0.375], [0.25, 0.25, 0.5]],
        [[2.5, 5.0, 2.0], [2.0, 4.0, 4.0], [5.0, 5.0, 2.5]],
    )
    for agent in (
        FractionalKellyAgent("A", AGENT_A_LAMBDA),
        FractionalKellyAgent("B", AGENT_B_LAMBDAS[0]),
        MinimumStakeAgent("E"),
    ):
        decision = agent.decide(view)
        assert np.array_equal(decision.outcomes, np.array([0, 1, 0]))
        # Ripiego: EV massimo 0.5 nella partita 1, parità D-A risolta su D
        assert (decision.fallback_match, decision.fallback_outcome) == (1, 1)


def test_tie_across_matches_fallback_order() -> None:
    """Verifica che a parità di EV fra partite diverse il ripiego scelga la prima partita."""
    agent = FractionalKellyAgent("A", AGENT_A_LAMBDA)

    # Tutti gli EV pari a -0.25 su due partite: ripiego sulla partita 0, esito H
    view_all_tied = _make_view(
        [[0.5, 0.25, 0.25], [0.25, 0.5, 0.25]],
        [[1.5, 3.0, 3.0], [3.0, 1.5, 3.0]],
    )
    decision = agent.decide(view_all_tied)
    assert (decision.fallback_match, decision.fallback_outcome) == (0, 0)

    # EV massimo -0.125 sull'esito A della partita 1
    view_second = _make_view(
        [[0.5, 0.25, 0.25], [0.25, 0.25, 0.5]],
        [[1.5, 3.0, 3.0], [2.0, 2.0, 1.75]],
    )
    decision = agent.decide(view_second)
    assert (decision.fallback_match, decision.fallback_outcome) == (1, 2)

    # EV positivi pari a 0.25 su due partite: selezione per partita, ripiego sulla prima
    view_positive = _make_view(POSITIVE_VIEW_PROBS, POSITIVE_VIEW_ODDS)
    decision = agent.decide(view_positive)
    assert np.array_equal(decision.outcomes, np.array([0, 2]))
    assert (decision.fallback_match, decision.fallback_outcome) == (0, 0)


def test_date_without_positive_ev() -> None:
    """Verifica esiti tutti -1, frazioni nulle e ripiego definito su una data senza EV > 0."""
    # EV della partita 0 tutti esattamente 0, della partita 1 tutti -0.25
    view = _make_view(
        [[0.5, 0.25, 0.25], [0.25, 0.5, 0.25]],
        [[2.0, 4.0, 4.0], [3.0, 1.5, 3.0]],
    )
    for agent in (
        FractionalKellyAgent("A", AGENT_A_LAMBDA),
        FractionalKellyAgent("B", AGENT_B_LAMBDAS[1]),
        MinimumStakeAgent("E"),
    ):
        decision = agent.decide(view)
        assert np.array_equal(decision.outcomes, np.array([NO_BET, NO_BET]))
        assert np.array_equal(decision.fractions, np.zeros(2))
        assert (decision.fallback_match, decision.fallback_outcome) == (0, 0)


# ---------------------------------------------------------------------------
# Criterio 8: decide non modifica la vista ed è deterministico
# ---------------------------------------------------------------------------


def test_decide_does_not_modify_view_and_is_deterministic() -> None:
    """Verifica che decide lasci la vista invariata e dia decisioni uguali su due chiamate."""
    views = _random_views()[::20] + [_make_view(POSITIVE_VIEW_PROBS, POSITIVE_VIEW_ODDS)]
    agents = (
        FractionalKellyAgent("A", AGENT_A_LAMBDA),
        FractionalKellyAgent("B", AGENT_B_LAMBDAS[0]),
        MinimumStakeAgent("E"),
    )
    for view in views:
        probs_before = np.array(view.probs)
        odds_before = np.array(view.odds)
        date_before = view.date
        for agent in agents:
            first = agent.decide(view)
            second = agent.decide(view)
            assert np.array_equal(first.outcomes, second.outcomes)
            assert np.array_equal(first.fractions, second.fractions)
            assert first.fallback_match == second.fallback_match
            assert first.fallback_outcome == second.fallback_outcome
        assert np.array_equal(view.probs, probs_before)
        assert np.array_equal(view.odds, odds_before)
        assert view.date == date_before
        assert view.probs.flags.writeable is False
        assert view.odds.flags.writeable is False


# ---------------------------------------------------------------------------
# Criterio 9: convenzioni del pacchetto kelly e del modulo agents
# ---------------------------------------------------------------------------


def test_kelly_imports_and_agents_style() -> None:
    """Verifica import di kelly/, assenza di try, print e logging, annotazioni e docstring in agents.py."""
    forbidden_prefixes = ("shk.model", "shk.data")
    for py_path in sorted(KELLY_DIR.glob("*.py")):
        tree = ast.parse(py_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                assert not node.module.startswith(forbidden_prefixes), f"{py_path.name}: {node.module}"
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith(forbidden_prefixes), f"{py_path.name}: {alias.name}"

    agents_tree = ast.parse(AGENTS_PATH.read_text(encoding="utf-8"))
    assert ast.get_docstring(agents_tree) is not None
    for node in ast.walk(agents_tree):
        assert not isinstance(node, ast.Try), "agents.py must not contain try blocks"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "print", "agents.py must not call print"
        if isinstance(node, ast.Import):
            assert all(alias.name != "logging" for alias in node.names), "agents.py must not import logging"
        if isinstance(node, ast.ClassDef):
            assert ast.get_docstring(node) is not None, f"class {node.name} lacks a docstring"
        if isinstance(node, ast.FunctionDef):
            assert ast.get_docstring(node) is not None, f"function {node.name} lacks a docstring"
            assert node.returns is not None, f"function {node.name} lacks a return annotation"
            all_args = node.args.posonlyargs + node.args.args + node.args.kwonlyargs
            for arg in all_args:
                if arg.arg in ("self", "cls"):
                    continue
                assert arg.annotation is not None, f"{node.name}: argument {arg.arg} lacks an annotation"
            if node.args.kwarg is not None:
                assert node.args.kwarg.annotation is not None, f"{node.name}: **kwargs lacks an annotation"
