"""Test suite per l'ambiente di simulazione passo-passo del criterio di Kelly (Task 34)."""

import ast
import inspect
from pathlib import Path

import numpy as np
import pytest

from shk.kelly.agents import (
    NO_BET,
    Agent,
    AgentDecision,
    DateView,
    FractionalKellyAgent,
    MinimumStakeAgent,
    estimated_expected_values,
)
from shk.kelly.backtest import backtest_log_wealth
from shk.kelly.environment import (
    AgentRun,
    PlacedBets,
    floor_thresholds,
    place_date_stakes,
    run_paired_backtest,
)


# ==============================================================================
# Helper per la generazione di dati sintetici
# ==============================================================================


def _make_dummy_view(
    date_str: str = "2024-01-01",
    n_matches: int = 2,
    p_home: float = 0.60,
    odds_home: float = 2.0,
) -> DateView:
    """Costruisce una DateView valida per i test."""
    p_rem = (1.0 - p_home) / 2.0
    probs = np.tile(np.array([[p_home, p_rem, p_rem]], dtype=np.float64), (n_matches, 1))
    odds = np.tile(np.array([[odds_home, 3.5, 3.5]], dtype=np.float64), (n_matches, 1))
    return DateView(date=np.datetime64(date_str), probs=probs, odds=odds)


# ==============================================================================
# Criterio 1: Validazioni di tipi e valori
# ==============================================================================


def test_c01_floor_thresholds_type_validation() -> None:
    """Verifica che floor_thresholds rifiuti tipi non float finiti."""
    # bool
    with pytest.raises(TypeError, match="min_stake must be a float"):
        floor_thresholds(True, 0.02, 0.25)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="f_star must be a float"):
        floor_thresholds(1.0, False, 0.25)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="lam must be a float"):
        floor_thresholds(1.0, 0.02, True)  # type: ignore[arg-type]

    # int
    with pytest.raises(TypeError, match="min_stake must be a float"):
        floor_thresholds(1, 0.02, 0.25)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="f_star must be a float"):
        floor_thresholds(1.0, 1, 0.25)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="lam must be a float"):
        floor_thresholds(1.0, 0.02, 1)  # type: ignore[arg-type]

    # stringhe
    with pytest.raises(TypeError, match="min_stake must be a float"):
        floor_thresholds("1.0", 0.02, 0.25)  # type: ignore[arg-type]


def test_c01_floor_thresholds_value_validation() -> None:
    """Verifica che floor_thresholds rifiuti valori infiniti o fuori intervallo."""
    # Non finiti
    with pytest.raises(ValueError, match="min_stake must be finite"):
        floor_thresholds(float("nan"), 0.02, 0.25)
    with pytest.raises(ValueError, match="f_star must be finite"):
        floor_thresholds(1.0, float("inf"), 0.25)
    with pytest.raises(ValueError, match="lam must be finite"):
        floor_thresholds(1.0, 0.02, float("-inf"))

    # Range
    with pytest.raises(ValueError, match="min_stake must be strictly positive"):
        floor_thresholds(0.0, 0.02, 0.25)
    with pytest.raises(ValueError, match="min_stake must be strictly positive"):
        floor_thresholds(-1.0, 0.02, 0.25)

    with pytest.raises(ValueError, match="f_star must be in \\(0, 1\\)"):
        floor_thresholds(1.0, 0.0, 0.25)
    with pytest.raises(ValueError, match="f_star must be in \\(0, 1\\)"):
        floor_thresholds(1.0, 1.0, 0.25)

    with pytest.raises(ValueError, match="lam must be in \\(0, 1\\]"):
        floor_thresholds(1.0, 0.02, 0.0)
    with pytest.raises(ValueError, match="lam must be in \\(0, 1\\]"):
        floor_thresholds(1.0, 0.02, 1.0001)


def test_c01_place_date_stakes_type_validation() -> None:
    """Verifica che place_date_stakes convalidi rigorosamente i tipi degli argomenti."""
    view = _make_dummy_view()
    agent = FractionalKellyAgent("AgentA", lam=1.0)
    decision = agent.decide(view)
    wealth = np.array([10.0, 20.0], dtype=np.float64)

    # wealth non ndarray o dtype errato
    with pytest.raises(TypeError, match="wealth must be a numpy.ndarray"):
        place_date_stakes([10.0, 20.0], view, decision, 1.0)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="wealth must have float64 dtype"):
        place_date_stakes(np.array([10, 20], dtype=np.int64), view, decision, 1.0)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="wealth must have float64 dtype"):
        place_date_stakes(np.array([10.0, 20.0], dtype=np.float32), view, decision, 1.0)

    # view non DateView
    with pytest.raises(TypeError, match="view must be a DateView"):
        place_date_stakes(wealth, "not_a_view", decision, 1.0)  # type: ignore[arg-type]

    # decision non AgentDecision
    with pytest.raises(TypeError, match="decision must be an AgentDecision"):
        place_date_stakes(wealth, view, "not_a_decision", 1.0)  # type: ignore[arg-type]

    # min_stake non float (bool o int)
    with pytest.raises(TypeError, match="min_stake must be a float"):
        place_date_stakes(wealth, view, decision, True)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="min_stake must be a float"):
        place_date_stakes(wealth, view, decision, 1)  # type: ignore[arg-type]


def test_c01_place_date_stakes_value_validation() -> None:
    """Verifica che place_date_stakes controlli forme e valori di ammissibilità."""
    view = _make_dummy_view(n_matches=2)
    agent = FractionalKellyAgent("AgentA", lam=1.0)
    decision = agent.decide(view)

    # wealth non 1D o M < 1
    with pytest.raises(ValueError, match="wealth must be 1-dimensional"):
        place_date_stakes(np.ones((2, 2), dtype=np.float64), view, decision, 1.0)
    with pytest.raises(ValueError, match="wealth must contain at least one replica \\(M >= 1\\)"):
        place_date_stakes(np.empty((0,), dtype=np.float64), view, decision, 1.0)

    # wealth non finita
    with pytest.raises(ValueError, match="wealth must contain only finite values"):
        place_date_stakes(np.array([10.0, float("nan")], dtype=np.float64), view, decision, 1.0)

    # wealth contiene repliche sotto il floor F > 0
    with pytest.raises(ValueError, match="wealth must be >= min_stake"):
        place_date_stakes(np.array([10.0, 0.99], dtype=np.float64), view, decision, 1.0)

    # wealth contiene repliche non positive con F == 0
    with pytest.raises(ValueError, match="wealth must be strictly positive"):
        place_date_stakes(np.array([10.0, 0.0], dtype=np.float64), view, decision, 0.0)

    # mismatch tra n partite di decision e view
    view_other = _make_dummy_view(n_matches=3)
    with pytest.raises(ValueError, match="do not match view matches"):
        place_date_stakes(np.array([10.0], dtype=np.float64), view_other, decision, 1.0)

    # min_stake negativo o non finito
    with pytest.raises(ValueError, match="min_stake must be finite and >= 0"):
        place_date_stakes(np.array([10.0], dtype=np.float64), view, decision, -0.01)
    with pytest.raises(ValueError, match="min_stake must be finite and >= 0"):
        place_date_stakes(np.array([10.0], dtype=np.float64), view, decision, float("inf"))


def test_c01_run_paired_backtest_type_validation() -> None:
    """Verifica le validazioni di tipo di run_paired_backtest."""
    dates = np.array(["2024-01-01"], dtype="datetime64[D]")
    probs = np.array([[0.6, 0.2, 0.2]], dtype=np.float64)
    odds = np.array([[2.0, 3.5, 3.5]], dtype=np.float64)
    outcomes = np.array([[0]], dtype=np.int64)
    agent = MinimumStakeAgent("E")

    # agents
    with pytest.raises(TypeError, match="agents must be a tuple or list"):
        run_paired_backtest("not_a_list", dates, probs, odds, outcomes, 0.0)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="Each agent must be an instance of Agent"):
        run_paired_backtest([agent, "not_an_agent"], dates, probs, odds, outcomes, 0.0)  # type: ignore[list-item]

    # dates
    with pytest.raises(TypeError, match="dates must be a numpy.ndarray"):
        run_paired_backtest([agent], ["2024-01-01"], probs, odds, outcomes, 0.0)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="dates must have datetime64 dtype"):
        run_paired_backtest([agent], np.array([1]), probs, odds, outcomes, 0.0)  # type: ignore[arg-type]

    # outcomes dtype intero non bool
    with pytest.raises(TypeError, match="outcomes must have an integer dtype"):
        run_paired_backtest([agent], dates, probs, odds, np.array([[True]]), 0.0)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="outcomes must have an integer dtype"):
        run_paired_backtest([agent], dates, probs, odds, np.array([[0.0]]), 0.0)  # type: ignore[arg-type]

    # min_stake float non bool e non int
    with pytest.raises(TypeError, match="min_stake must be a float"):
        run_paired_backtest([agent], dates, probs, odds, outcomes, 1)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="min_stake must be a float"):
        run_paired_backtest([agent], dates, probs, odds, outcomes, False)  # type: ignore[arg-type]

    # record_stakes bool
    with pytest.raises(TypeError, match="record_stakes must be a bool"):
        run_paired_backtest([agent], dates, probs, odds, outcomes, 0.0, record_stakes=1)  # type: ignore[arg-type]


def test_c01_run_paired_backtest_value_validation() -> None:
    """Verifica le validazioni sui valori di run_paired_backtest."""
    dates = np.array(["2024-01-01", "2024-01-02"], dtype="datetime64[D]")
    probs = np.array([[0.6, 0.2, 0.2], [0.5, 0.3, 0.2]], dtype=np.float64)
    odds = np.array([[2.0, 3.5, 3.5], [2.1, 3.0, 3.0]], dtype=np.float64)
    outcomes = np.array([[0, 1], [2, 0]], dtype=np.int64)
    agent1 = MinimumStakeAgent("E1")
    agent2 = MinimumStakeAgent("E2")

    # agents vuoto
    with pytest.raises(ValueError, match="agents must contain at least one Agent"):
        run_paired_backtest([], dates, probs, odds, outcomes, 0.0)

    # nomi duplicati
    with pytest.raises(ValueError, match="All agent names must be distinct"):
        run_paired_backtest([agent1, MinimumStakeAgent("E1")], dates, probs, odds, outcomes, 0.0)

    # dates con NaT
    dates_nat = np.array(["2024-01-01", "NaT"], dtype="datetime64[D]")
    with pytest.raises(ValueError, match="dates must not contain NaT"):
        run_paired_backtest([agent1], dates_nat, probs, odds, outcomes, 0.0)

    # dates non ordinate in modo non decrescente
    dates_unsorted = np.array(["2024-01-02", "2024-01-01"], dtype="datetime64[D]")
    with pytest.raises(ValueError, match="dates must be in non-decreasing order"):
        run_paired_backtest([agent1], dates_unsorted, probs, odds, outcomes, 0.0)

    # outcomes M < 1
    with pytest.raises(ValueError, match="outcomes must contain at least one replica \\(M >= 1\\)"):
        run_paired_backtest([agent1], dates, probs, odds, np.empty((0, 2), dtype=np.int64), 0.0)

    # outcomes valori fuori da {0, 1, 2}
    with pytest.raises(ValueError, match="outcomes must contain only values in \\{0, 1, 2\\}"):
        run_paired_backtest([agent1], dates, probs, odds, np.array([[0, 3]], dtype=np.int64), 0.0)

    # probs riga non somma a 1
    probs_bad = np.array([[0.6, 0.2, 0.3], [0.5, 0.3, 0.2]], dtype=np.float64)
    with pytest.raises(ValueError, match="Each row of probs must sum to 1"):
        run_paired_backtest([agent1], dates, probs_bad, odds, outcomes, 0.0)

    # odds <= 1.0
    odds_bad = np.array([[1.0, 3.5, 3.5], [2.1, 3.0, 3.0]], dtype=np.float64)
    with pytest.raises(ValueError, match="odds must be strictly greater than 1.0"):
        run_paired_backtest([agent1], dates, probs, odds_bad, outcomes, 0.0)


# ==============================================================================
# Criterio 2: Soglie analitiche del floor
# ==============================================================================


def test_c02_floor_thresholds_exact_values_and_invariants() -> None:
    """Verifica le soglie (200, 25, 1), l'indipendenza di B2 da lambda e B1 = B2 * 2 / lambda."""
    b1, b2, b3 = floor_thresholds(1.0, 0.02, 0.25)
    assert pytest.approx(200.0, rel=1e-12, abs=1e-12) == b1
    assert pytest.approx(25.0, rel=1e-12, abs=1e-12) == b2
    assert pytest.approx(1.0, rel=1e-12, abs=1e-12) == b3

    # B2 non dipende da lambda
    for lam in (0.10, 0.25, 0.50, 1.0):
        _, b2_lam, _ = floor_thresholds(1.0, 0.02, lam)
        assert pytest.approx(25.0, rel=1e-12, abs=1e-12) == b2_lam

    # B1 = B2 * 2 / lambda
    for lam in (0.10, 0.25, 0.50, 0.80, 1.0):
        b1_val, b2_val, _ = floor_thresholds(1.5, 0.03, lam)
        assert pytest.approx(b2_val * 2.0 / lam, rel=1e-12, abs=1e-12) == b1_val


# ==============================================================================
# Criterio 3: Equivalenza con backtest_log_wealth (F = 0)
# ==============================================================================


def test_c03_equivalence_with_backtest_log_wealth_f_zero() -> None:
    """Con F = 0 e FractionalKellyAgent(0.25) e sum(f) < 1, ln(W) coincide con log_wealth."""
    # Costruzione di un calendario con 3 date distinte e 2 partite per data (N = 6)
    dates = np.array(
        ["2024-01-01", "2024-01-01", "2024-01-02", "2024-01-02", "2024-01-03", "2024-01-03"],
        dtype="datetime64[D]",
    )
    # p_home = 0.55, odds_home = 2.0 -> b = 1.0, EV = 0.55 * 2 - 1 = 0.10 > 0
    # kelly piena = (1 * 0.55 - 0.45)/1 = 0.10
    # lam = 0.25 -> f = 0.025 per partita; per data 2 partite -> sum(f) = 0.05 < 1
    probs = np.tile(np.array([[0.55, 0.25, 0.20]], dtype=np.float64), (6, 1))
    odds = np.tile(np.array([[2.0, 3.2, 3.2]], dtype=np.float64), (6, 1))

    # M = 4 repliche di esiti sintetici
    m_replicas = 4
    rng = np.random.default_rng(20261009)
    outcomes = rng.integers(0, 3, size=(m_replicas, 6), dtype=np.int64)

    agent = FractionalKellyAgent("B_0.25", lam=0.25)
    runs = run_paired_backtest([agent], dates, probs, odds, outcomes, min_stake=0.0)
    agent_run = runs[0]

    # Confronto con backtest_log_wealth per ciascuna replica m
    # Prepara le frazioni e le quote dell'esito selezionato (H = 0)
    selected_fractions = np.full(6, 0.025, dtype=np.float64)
    selected_odds = np.full(6, 2.0, dtype=np.float64)

    for m in range(m_replicas):
        won_m = outcomes[m, :] == 0
        bw_res = backtest_log_wealth(
            dates=dates,
            fractions=selected_fractions,
            odds=selected_odds,
            won=won_m,
        )
        env_log_wealth = np.log(agent_run.wealth[m, :])
        np.testing.assert_allclose(env_log_wealth, bw_res.log_wealth, rtol=1e-12, atol=1e-12)


# ==============================================================================
# Criterio 4: F = 0, nessuna rovina, W > 0, scarto con sum(f) >= 1
# ==============================================================================


def test_c04_f_zero_no_ruin_and_prefix_truncation_when_sum_f_ge_one() -> None:
    """Con F = 0 e lam = 1.0 su date con sum(f) >= 1, regola c scarta i surplus e W > 0."""
    # 2 date, 3 partite ciascuna
    dates = np.array(
        ["2024-01-01", "2024-01-01", "2024-01-01", "2024-01-02", "2024-01-02", "2024-01-02"],
        dtype="datetime64[D]",
    )
    # Partite con diverso edge:
    # m0: p = 0.70, o = 2.0 -> EV = 0.40, f = 0.40
    # m1: p = 0.65, o = 2.0 -> EV = 0.30, f = 0.30
    # m2: p = 0.75, o = 2.0 -> EV = 0.50, f = 0.50
    # Somma delle frazioni: 0.40 + 0.30 + 0.50 = 1.20 >= 1.0!
    # Ordine per EV decrescente: m2 (0.50), m0 (0.40), m1 (0.30)
    # Somma cumulativa:
    # Bet 1 (m2): 0.50 * W <= W -> tenuta
    # Bet 2 (m0): (0.50 + 0.40) * W = 0.90 * W <= W -> tenuta
    # Bet 3 (m1): (0.90 + 0.30) * W = 1.20 * W > W -> scartata!
    probs_row = [
        [0.70, 0.15, 0.15],
        [0.65, 0.20, 0.15],
        [0.75, 0.15, 0.10],
    ] * 2
    odds_row = [[2.0, 3.0, 3.0]] * 6

    probs = np.array(probs_row, dtype=np.float64)
    odds = np.array(odds_row, dtype=np.float64)

    # Esiti in cui perdono tutte le partite scommesse (esito 1 invece di 0)
    # Così testiamo che la ricchezza non va a 0 e resta > 0
    m_replicas = 3
    outcomes = np.ones((m_replicas, 6), dtype=np.int64)

    agent = FractionalKellyAgent("KellyFull", lam=1.0)
    runs = run_paired_backtest(
        [agent], dates, probs, odds, outcomes, min_stake=0.0, record_stakes=True
    )
    run = runs[0]

    # Nessuna rovina
    assert not np.any(run.ruined)
    assert np.all(run.ruin_date_index == -1)
    # W > 0 ovunque
    assert np.all(run.wealth > 0.0)

    # La terza puntata è stata scartata su entrambe le date (2 scartate in totale per replica)
    assert np.all(run.n_dropped == 2)
    assert np.all(run.n_bets == 4)  # 2 puntate tenute per data * 2 date = 4
    # Somma piazzata <= W
    assert run.staked is not None
    assert np.all(run.staked <= run.wealth[:, :-1])


# ==============================================================================
# Criterio 5: Proprietà con F > 0
# ==============================================================================


def test_c05_placed_bets_ge_floor_and_every_date_bet() -> None:
    """Con F > 0, su repliche non rovinate ogni puntata piazzata è >= F e ogni data ha >= 1 puntata."""
    dates = np.array(["2024-01-01", "2024-01-02", "2024-01-03"], dtype="datetime64[D]")
    probs = np.array([[0.6, 0.2, 0.2], [0.6, 0.2, 0.2], [0.6, 0.2, 0.2]], dtype=np.float64)
    odds = np.array([[2.0, 3.0, 3.0], [2.0, 3.0, 3.0], [2.0, 3.0, 3.0]], dtype=np.float64)
    outcomes = np.zeros((2, 3), dtype=np.int64)  # tutte vinte

    agent = FractionalKellyAgent("B_0.25", lam=0.25)
    f_stake = 0.5
    runs = run_paired_backtest([agent], dates, probs, odds, outcomes, min_stake=f_stake)
    run = runs[0]

    assert not np.any(run.ruined)
    # Almeno 1 puntata per data: totale >= 3
    assert np.all(run.n_bets >= 3)


def test_c05_fallback_and_minimum_stake_agent() -> None:
    """Senza puntate volontarie c'è 1 puntata da F sul ripiego, e MinimumStakeAgent punta F a data."""
    dates = np.array(["2024-01-01", "2024-01-02"], dtype="datetime64[D]")
    probs = np.array([[0.33, 0.33, 0.34], [0.33, 0.34, 0.33]], dtype=np.float64)
    odds = np.array([[2.0, 2.0, 2.0], [2.0, 2.0, 2.0]], dtype=np.float64)
    # Quote 2.0 con probs <= 0.5 -> EV <= 0 ovunque, nessuna puntata volontaria
    outcomes = np.array([[2, 1]], dtype=np.int64)

    agent_kelly = FractionalKellyAgent("A", lam=1.0)
    agent_min = MinimumStakeAgent("E")

    f_stake = 0.10
    runs = run_paired_backtest(
        [agent_kelly, agent_min],
        dates,
        probs,
        odds,
        outcomes,
        min_stake=f_stake,
        record_stakes=True,
    )

    for run in runs:
        # 1 puntata per data, esattamente forzata da F
        assert np.all(run.n_bets == 2)
        assert np.all(run.n_forced == 2)
        assert np.all(run.n_floored == 0)
        assert np.all(run.n_dropped == 0)
        assert run.staked is not None
        np.testing.assert_allclose(run.staked, [[0.10, 0.10]])


def test_c05_ruin_condition_and_absorbing_state() -> None:
    """Rovina se e solo se a inizio data W < F o W = 0; ricchezza costante e zero puntate dopo."""
    dates = np.array(["2024-01-01", "2024-01-02", "2024-01-03"], dtype="datetime64[D]")
    probs = np.array([[0.6, 0.2, 0.2], [0.6, 0.2, 0.2], [0.6, 0.2, 0.2]], dtype=np.float64)
    odds = np.array([[2.0, 3.0, 3.0], [2.0, 3.0, 3.0], [2.0, 3.0, 3.0]], dtype=np.float64)

    # Replica 0: vince sempre -> non rovina
    # Replica 1: perde alla data 0 -> con F = 0.6, puntata 0.6 -> W passa da 1.0 a 0.4 < F -> rovina a data 1
    outcomes = np.array(
        [[0, 0, 0], [1, 0, 0]],  # replica 0: vincente  # replica 1: perde data 0
        dtype=np.int64,
    )

    agent = FractionalKellyAgent("A", lam=1.0)
    f_stake = 0.6
    runs = run_paired_backtest([agent], dates, probs, odds, outcomes, min_stake=f_stake)
    run = runs[0]

    assert not run.ruined[0]
    assert run.ruin_date_index[0] == -1

    assert run.ruined[1]
    assert run.ruin_date_index[1] == 1  # rovinata all'inizio della data 1 (indice 1)

    # Ricchezza costante dopo la rovina
    # Data 0: W passa da 1.0 a 0.4; a data 1 e 2 resta 0.4
    np.testing.assert_allclose(run.wealth[1, 1:], [0.4, 0.4, 0.4])
    # Numero di puntate della replica rovinata è 1 (solo sulla prima data)
    assert run.n_bets[1] == 1


def test_c05_dyadic_exact_w_equals_f_and_delayed_ruin() -> None:
    """Caso a valori diadici: W = F esatto non è rovina; una perdita da F porta a W = 0 e rovina a data dopo."""
    dates = np.array(["2024-01-01", "2024-01-02", "2024-01-03"], dtype="datetime64[D]")
    probs = np.array([[0.6, 0.2, 0.2], [0.6, 0.2, 0.2], [0.6, 0.2, 0.2]], dtype=np.float64)
    odds = np.array([[2.0, 3.0, 3.0], [2.0, 3.0, 3.0], [2.0, 3.0, 3.0]], dtype=np.float64)

    # Iniziamo con W0 = 1.0 e F = 1.0 -> W0 = F esatto
    # Replica perde alla data 0 (esito 1)
    outcomes = np.array([[1, 0, 0]], dtype=np.int64)

    agent = FractionalKellyAgent("A", lam=1.0)
    runs = run_paired_backtest([agent], dates, probs, odds, outcomes, min_stake=1.0)
    run = runs[0]

    # A inizio data 0: W = 1.0 == F -> NON è rovina, punta F = 1.0
    # Esito perso: return = -1.0 -> W a fine data 0 è 1.0 - 1.0 = 0.0
    # A inizio data 1: W = 0.0 -> ROVINA, registrata a data_idx = 1
    assert run.ruined[0]
    assert run.ruin_date_index[0] == 1
    assert run.wealth[0, 0] == 1.0
    assert run.wealth[0, 1] == 0.0
    assert run.wealth[0, 2] == 0.0
    assert run.wealth[0, 3] == 0.0
    assert run.n_bets[0] == 1


def test_c05_all_replicas_ruin_before_end() -> None:
    """Verifica che quando tutte le repliche si rovinano, place_date_stakes non si chiama e la simulazione termina regolarmente."""
    dates = np.array(["2024-01-01", "2024-01-02", "2024-01-03"], dtype="datetime64[D]")
    probs = np.array([[0.6, 0.2, 0.2], [0.6, 0.2, 0.2], [0.6, 0.2, 0.2]], dtype=np.float64)
    odds = np.array([[2.0, 3.0, 3.0], [2.0, 3.0, 3.0], [2.0, 3.0, 3.0]], dtype=np.float64)

    # Tutte e due le repliche perdono alla prima data
    outcomes = np.array([[1, 0, 0], [1, 0, 0]], dtype=np.int64)

    agent = MinimumStakeAgent("E")
    # Con F = 1.0, puntano 1.0 alla data 0, perdono, finiscono a 0.0, entrambe rovinate a data 1
    runs = run_paired_backtest([agent], dates, probs, odds, outcomes, min_stake=1.0)
    run = runs[0]

    assert np.all(run.ruined)
    assert np.all(run.ruin_date_index == 1)
    # Entrambe hanno piazzato solo 1 puntata (sulla data 0)
    assert np.all(run.n_bets == 1)
    # Wealth resta costante a 0.0 dopo la data 0
    np.testing.assert_array_equal(run.wealth[:, 1], [0.0, 0.0])
    np.testing.assert_array_equal(run.wealth[:, 2], [0.0, 0.0])
    np.testing.assert_array_equal(run.wealth[:, 3], [0.0, 0.0])


# ==============================================================================
# Criterio 6: Floor invisibile sopra la soglia e divergenza
# ==============================================================================


def test_c06_invisible_floor_above_threshold() -> None:
    """Se ogni data ha una puntata volontaria e f_i * W >= F ovunque, traiettorie identiche a F = 0."""
    dates = np.array(["2024-01-01", "2024-01-02"], dtype="datetime64[D]")
    # p = 0.6, o = 2.0 -> lam = 0.25 -> f = 0.05
    # Con W0 = 1.0, f * W = 0.05.
    # Se F = 0.01, f * W >= F sempre (anche se raddoppia o se W resta >= 0.2)
    probs = np.array([[0.6, 0.2, 0.2], [0.6, 0.2, 0.2]], dtype=np.float64)
    odds = np.array([[2.0, 3.0, 3.0], [2.0, 3.0, 3.0]], dtype=np.float64)
    outcomes = np.array([[0, 0]], dtype=np.int64)  # entrambe vinte

    agent = FractionalKellyAgent("B_0.25", lam=0.25)
    run_f0 = run_paired_backtest([agent], dates, probs, odds, outcomes, min_stake=0.0)[0]
    run_f_pos = run_paired_backtest([agent], dates, probs, odds, outcomes, min_stake=0.01)[0]

    np.testing.assert_array_equal(run_f_pos.wealth, run_f0.wealth)
    assert np.all(run_f_pos.n_floored == 0)


def test_c06_floor_divergence_at_first_sub_floor_date() -> None:
    """Divergenza a partire dalla prima data in cui f_i * W < F e non prima (con puntata volontaria presente a ogni data)."""
    dates = np.array(["2024-01-01", "2024-01-02", "2024-01-03"], dtype="datetime64[D]")
    # Data 0: p = 0.8, o = 2.0 -> b = 1, EV = 0.6, kelly = 0.60
    # Data 1: p = 0.55, o = 2.0 -> b = 1, EV = 0.1, kelly = 0.10
    # Data 2: p = 0.8, o = 2.0 -> b = 1, EV = 0.6, kelly = 0.60
    probs = np.array([[0.8, 0.1, 0.1], [0.55, 0.25, 0.20], [0.8, 0.1, 0.1]], dtype=np.float64)
    odds = np.array([[2.0, 3.0, 3.0], [2.0, 3.0, 3.0], [2.0, 3.0, 3.0]], dtype=np.float64)
    outcomes = np.array([[0, 0, 0]], dtype=np.int64)  # tutte vinte

    agent = FractionalKellyAgent("A", lam=1.0)
    # Impostiamo F = 0.20
    # A data 0: W0 = 1.0, f0 = 0.60 -> f0 * W = 0.60 >= F (non floored!)
    # Fine data 0: W1 = 1.0 + 0.60 * 1.0 = 1.60
    # A data 1: W1 = 1.60, f1 = 0.10 -> f1 * W = 0.16 < F = 0.20! (FLOORED al floor 0.20!)
    f_stake = 0.20

    run_f0 = run_paired_backtest([agent], dates, probs, odds, outcomes, min_stake=0.0)[0]
    run_f_pos = run_paired_backtest([agent], dates, probs, odds, outcomes, min_stake=f_stake)[0]

    # Colonne wealth:
    # colonna 0 (inizio data 0) e colonna 1 (fine data 0 / inizio data 1) sono identiche
    assert run_f_pos.wealth[0, 0] == run_f0.wealth[0, 0]
    assert run_f_pos.wealth[0, 1] == run_f0.wealth[0, 1]

    # A colonna 2 (dopo la data 1 dove è scattato il floor), divergono!
    assert run_f_pos.wealth[0, 2] != run_f0.wealth[0, 2]


# ==============================================================================
# Criterio 7: Input identici e condivisione DateView
# ==============================================================================


class _RecordingAgent(Agent):
    """Agente di test che registra gli oggetti DateView ricevuti."""

    def __init__(self, name: str, fraction: float = 0.1) -> None:
        super().__init__(name)
        self.fraction = fraction
        self.received_views: list[DateView] = []

    def stake_fractions(
        self, view: DateView, p_hat: np.ndarray, b: np.ndarray
    ) -> np.ndarray:
        self.received_views.append(view)
        return np.full(p_hat.shape[0], self.fraction, dtype=np.float64)


def test_c07_identical_date_view_passed_to_all_agents_even_when_ruined() -> None:
    """Agenti ricevono lo stesso oggetto DateView (stesso id), anche se un agente è rovinato."""
    dates = np.array(["2024-01-01", "2024-01-02", "2024-01-03"], dtype="datetime64[D]")
    probs = np.array([[0.6, 0.2, 0.2], [0.6, 0.2, 0.2], [0.6, 0.2, 0.2]], dtype=np.float64)
    odds = np.array([[2.0, 3.0, 3.0], [2.0, 3.0, 3.0], [2.0, 3.0, 3.0]], dtype=np.float64)

    # 1 sola replica: perde a data 0
    outcomes = np.array([[1, 0, 0]], dtype=np.int64)

    # Agente 1: frazione alta, va in rovina subito a data 1 con F = 1.0
    rec_agent1 = _RecordingAgent("AgentRuining", fraction=0.9)
    # Agente 2: frazione 0.0
    rec_agent2 = _RecordingAgent("AgentSurvivor", fraction=0.0)

    runs = run_paired_backtest([rec_agent1, rec_agent2], dates, probs, odds, outcomes, min_stake=1.0)

    # AgentRuining deve essere andato in rovina
    assert runs[0].ruined[0]
    assert runs[0].ruin_date_index[0] == 1

    # Ma decide è stato chiamato a tutte e 3 le date per entrambi gli agenti
    assert len(rec_agent1.received_views) == 3
    assert len(rec_agent2.received_views) == 3

    # Per ogni data, lo stesso identico oggetto DateView (stesso id in memoria)
    for d in range(3):
        v1 = rec_agent1.received_views[d]
        v2 = rec_agent2.received_views[d]
        assert v1 is v2
        assert id(v1) == id(v2)
        assert v1.date == dates[d]
        np.testing.assert_array_equal(v1.probs[0], probs[d])
        np.testing.assert_array_equal(v1.odds[0], odds[d])


# ==============================================================================
# Criterio 8: Agente nuovo e verifica AST specifica 6
# ==============================================================================


class _CustomTestAgent(Agent):
    """Nuova sottoclasse di Agent per verificare che l'ambiente sia agnostico."""

    def stake_fractions(
        self, view: DateView, p_hat: np.ndarray, b: np.ndarray
    ) -> np.ndarray:
        return np.full(p_hat.shape[0], 0.05, dtype=np.float64)


def test_c08_new_agent_subclass_runs_in_environment() -> None:
    """Una sottoclasse di Agent definita nel test gira in run_paired_backtest senza problemi."""
    dates = np.array(["2024-01-01"], dtype="datetime64[D]")
    probs = np.array([[0.6, 0.2, 0.2]], dtype=np.float64)
    odds = np.array([[2.0, 3.0, 3.0]], dtype=np.float64)
    outcomes = np.array([[0]], dtype=np.int64)

    agent = _CustomTestAgent("CustomAgent")
    runs = run_paired_backtest([agent], dates, probs, odds, outcomes, min_stake=0.01)
    assert len(runs) == 1
    assert runs[0].name == "CustomAgent"
    assert not runs[0].ruined[0]


def test_c08_ast_check_specification_point_6() -> None:
    """Verifica AST che environment.py non importi da shk.model/shk.data né nomini sottoclassi concrete di Agent."""
    env_path = Path(__file__).resolve().parents[1] / "src" / "shk" / "kelly" / "environment.py"
    with open(env_path, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source, filename=str(env_path))

    concrete_agent_names = {"FractionalKellyAgent", "MinimumStakeAgent"}

    for node in ast.walk(tree):
        # Nessun import da shk.model o shk.data
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert not mod.startswith("shk.model"), f"Import forbidden: {mod}"
            assert not mod.startswith("shk.data"), f"Import forbidden: {mod}"
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("shk.model"), f"Import forbidden: {alias.name}"
                assert not alias.name.startswith("shk.data"), f"Import forbidden: {alias.name}"

        # Nessuna menzione di sottoclassi concrete di Agent
        if isinstance(node, ast.Name):
            assert node.id not in concrete_agent_names, f"Forbidden concrete agent name referenced: {node.id}"


# ==============================================================================
# Criterio 9: Vettorizzazione ed equivalenza riga per riga
# ==============================================================================


def test_c09_vectorization_matches_single_row_run() -> None:
    """Con outcomes a M righe, ogni riga coincide (np.array_equal) col run della sola riga."""
    dates = np.array(
        ["2024-01-01", "2024-01-01", "2024-01-02", "2024-01-02", "2024-01-03", "2024-01-03"],
        dtype="datetime64[D]",
    )
    probs = np.tile(np.array([[0.6, 0.2, 0.2]], dtype=np.float64), (6, 1))
    odds = np.tile(np.array([[2.0, 3.0, 3.0]], dtype=np.float64), (6, 1))

    m_replicas = 5
    rng = np.random.default_rng(42)
    outcomes = rng.integers(0, 3, size=(m_replicas, 6), dtype=np.int64)

    agent_a = FractionalKellyAgent("A", lam=1.0)
    agent_b = FractionalKellyAgent("B", lam=0.25)
    agent_e = MinimumStakeAgent("E")
    agents = [agent_a, agent_b, agent_e]

    f_stake = 0.05
    multi_runs = run_paired_backtest(
        agents, dates, probs, odds, outcomes, min_stake=f_stake, record_stakes=True
    )

    for m in range(m_replicas):
        single_outcome = outcomes[m : m + 1, :]
        single_runs = run_paired_backtest(
            agents, dates, probs, odds, single_outcome, min_stake=f_stake, record_stakes=True
        )
        for a_idx in range(len(agents)):
            m_run = multi_runs[a_idx]
            s_run = single_runs[a_idx]
            np.testing.assert_array_equal(m_run.wealth[m : m + 1, :], s_run.wealth)
            np.testing.assert_array_equal(m_run.ruined[m : m + 1], s_run.ruined)
            np.testing.assert_array_equal(m_run.ruin_date_index[m : m + 1], s_run.ruin_date_index)
            np.testing.assert_array_equal(m_run.n_bets[m : m + 1], s_run.n_bets)
            np.testing.assert_array_equal(m_run.n_forced[m : m + 1], s_run.n_forced)
            np.testing.assert_array_equal(m_run.n_floored[m : m + 1], s_run.n_floored)
            np.testing.assert_array_equal(m_run.n_dropped[m : m + 1], s_run.n_dropped)
            if m_run.staked is not None and s_run.staked is not None:
                np.testing.assert_array_equal(m_run.staked[m : m + 1, :], s_run.staked)
            if m_run.desired is not None and s_run.desired is not None:
                np.testing.assert_array_equal(m_run.desired[m : m + 1, :], s_run.desired)


# ==============================================================================
# Criterio 10: Qualità del codice, convenzioni e controlli AST su environment.py
# ==============================================================================


def test_c10_ast_code_quality_and_conventions() -> None:
    """Verifica divieti di print/log/try/assert, presenza di docstring e annotazioni su environment.py."""
    env_path = Path(__file__).resolve().parents[1] / "src" / "shk" / "kelly" / "environment.py"
    with open(env_path, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source, filename=str(env_path))

    for node in ast.walk(tree):
        # Nessun try
        assert not isinstance(node, ast.Try), "try statement forbidden in environment.py"
        # Nessun assert
        assert not isinstance(node, ast.Assert), "assert statement forbidden in environment.py"

        # Nessuna chiamata a print, logging, warn
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id != "print", "print() forbidden in environment.py"
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {
                    "warn",
                    "warning",
                    "info",
                    "error",
                    "debug",
                }, f"logging/warn forbidden: {node.func.attr}"

        # Docstring e annotazioni per funzioni e classi pubbliche
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                doc = ast.get_docstring(node)
                assert doc is not None and len(doc) > 0, f"Public function {node.name} must have a docstring"
                assert node.returns is not None, f"Public function {node.name} must have a return type annotation"
        if isinstance(node, ast.ClassDef):
            if not node.name.startswith("_"):
                doc = ast.get_docstring(node)
                assert doc is not None and len(doc) > 0, f"Public class {node.name} must have a docstring"
