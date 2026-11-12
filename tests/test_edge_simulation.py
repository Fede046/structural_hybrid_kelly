"""Test: mondo simulato con vantaggio noto (shk.model.edge_simulation), su dati costruiti."""

import numpy as np
import pytest

from shk.model.edge_simulation import (
    SCENARIOS,
    Scenario,
    break_day,
    composition_shift,
    draw_outcomes,
    first_stop_day,
    match_parameter,
    share_of_days,
    simulated_input,
    tilted_probabilities,
)
from shk.model.season_input import SeasonInput

Q = np.array([[0.5, 0.3, 0.2], [0.2, 0.3, 0.5]])
P = np.array([[0.6, 0.25, 0.15], [0.3, 0.3, 0.4]])


def test_tilted_probabilities_interpolate_between_market_and_model():
    assert np.allclose(tilted_probabilities(Q, P, 0.0), Q)
    assert np.allclose(tilted_probabilities(Q, P, 1.0), P)
    mixed = tilted_probabilities(Q, P, np.array([0.0, 1.0]))
    assert np.allclose(mixed[0], Q[0]) and np.allclose(mixed[1], P[1])
    # a = −1: la verità sta dalla parte opposta del modello rispetto al mercato
    opposite = tilted_probabilities(Q, P, -1.0)
    assert np.allclose(opposite.sum(axis=1), 1.0)
    assert opposite[0, 0] < Q[0, 0] < P[0, 0]
    with pytest.raises(ValueError):
        tilted_probabilities(Q, P[:1], 0.0)


def test_draw_outcomes_inverts_the_distribution():
    probs = np.array([[0.5, 0.3, 0.2]] * 4)
    assert list(draw_outcomes(probs, np.array([0.0, 0.49, 0.5, 0.99]))) == [0, 0, 1, 2]
    rng = np.random.default_rng(0)
    big = np.tile([0.5, 0.3, 0.2], (60_000, 1))
    freq = np.bincount(draw_outcomes(big, rng.random(60_000)), minlength=3) / 60_000
    assert np.allclose(freq, [0.5, 0.3, 0.2], atol=0.01)
    with pytest.raises(ValueError):
        draw_outcomes(probs, np.zeros(3))


def test_break_is_at_mid_season_by_date():
    dates = np.repeat(np.arange("2020-01-01", "2020-01-11", dtype="datetime64[D]").astype("datetime64[ns]"), 2)
    a, first = match_parameter(dates, Scenario("x", 1.0, -1.0))
    assert first == break_day(10) == 5
    assert list(a) == [1.0] * 10 + [-1.0] * 10


def test_scenarios_share_outcomes_until_the_break():
    """Stesse estrazioni uniformi: gli scenari con lo stesso a iniziale coincidono prima del cambiamento."""
    rng = np.random.default_rng(1)
    n = 200
    raw = rng.dirichlet([4.0, 3.0, 3.0], size=n)
    probs = rng.dirichlet([4.0, 3.0, 3.0], size=n)
    odds = 1.0 / (raw * 1.05)
    dates = np.repeat(np.arange("2020-01-01", "2020-04-10", dtype="datetime64[D]").astype("datetime64[ns]"), 2)
    inp = SeasonInput("sim", dates, probs, odds, np.zeros((1, n), dtype=np.int64), np.zeros((n, 1)), np.zeros(n))
    u = rng.random(n)
    by_name = {s.name: s for s in SCENARIOS}
    sims = {name: simulated_input(inp, match_parameter(dates, s)[0], u) for name, s in by_name.items()}
    half = n // 2
    for name in ("edge_vanishes", "edge_reverses"):
        assert np.array_equal(sims[name].outcomes[0, :half], sims["stable_edge"].outcomes[0, :half])
        assert not np.array_equal(sims[name].outcomes[0, half:], sims["stable_edge"].outcomes[0, half:])
    assert np.array_equal(sims["edge_vanishes"].outcomes[0, half:], sims["no_edge"].outcomes[0, half:])
    # δ è ricalcolato sugli esiti simulati; date, previsioni e quote restano quelle date
    sim = sims["stable_edge"]
    assert sim.outcomes.shape == (1, n) and sim.delta.shape == (n,) and np.isfinite(sim.delta).all()
    assert sim.probs is inp.probs and sim.odds is inp.odds


def test_model_has_an_edge_only_when_it_is_right():
    """Media di δ positiva con a = 1 (il modello ha ragione), negativa con a = 0 (ha ragione il mercato)."""
    rng = np.random.default_rng(2)
    n = 40_000
    probs = rng.dirichlet([8.0, 6.0, 6.0], size=n)
    market = rng.dirichlet([8.0, 6.0, 6.0], size=n)
    odds = 1.0 / (market * 1.05)
    dates = np.sort(rng.integers(0, 100, size=n)).astype("datetime64[D]").astype("datetime64[ns]")
    inp = SeasonInput("sim", dates, probs, odds, np.zeros((1, n), dtype=np.int64), np.zeros((n, 1)), np.zeros(n))
    u = rng.random(n)
    assert simulated_input(inp, 1.0, u).delta.mean() > 0.02
    assert simulated_input(inp, 0.0, u).delta.mean() < -0.02


def test_schedule_summaries():
    levels = [np.array([2, 2, 0, 0]), np.array([2, 1, 2, 0])]
    assert first_stop_day(levels[0]) == 2 and first_stop_day(np.array([2, 1, 2])) is None
    assert share_of_days(levels, [2, 2]) == (0.0, 0.75)
    assert share_of_days(levels, [2, 2], level=1) == (0.25, 0.0)


def test_composition_shift_moves_the_dispersed_matches_to_the_second_half():
    rng = np.random.default_rng(5)
    n = 20
    x = np.column_stack([rng.normal(size=n), np.linspace(0.0, 1.0, n)])  # seconda colonna: posizione
    probs, odds = rng.dirichlet([3.0, 3.0, 3.0], size=n), rng.uniform(1.5, 5.0, size=(n, 3))
    dates = np.arange("2020-01-01", n, dtype="datetime64[D]").astype("datetime64[ns]")
    inp = SeasonInput("sim", dates, probs, odds, np.zeros((1, n), dtype=np.int64), x, np.zeros(n))
    beta = np.array([0.1, 2.0, 0.0])  # dispersione prevista crescente con la prima covariata
    out = composition_shift(inp, beta, 12, position_index=1)
    assert out.x[:12, 0].max() <= out.x[12:, 0].min()
    assert np.array_equal(out.x[:, 1], x[:, 1]) and np.array_equal(out.dates, dates)
    # Le partite sono le stesse, riordinate insieme a previsioni e quote
    order = [int(np.flatnonzero(x[:, 0] == v)[0]) for v in out.x[:, 0]]
    assert sorted(order) == list(range(n))
    assert np.array_equal(out.probs, probs[order]) and np.array_equal(out.odds, odds[order])
    # Dentro ciascuna metà resta l'ordine originale
    assert order[:12] == sorted(order[:12]) and order[12:] == sorted(order[12:])
