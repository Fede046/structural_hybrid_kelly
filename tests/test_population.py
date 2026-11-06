"""Test della dinamica del replicatore con mutazione (shk.model.population)."""

import numpy as np
import pytest

from shk.model.population import evolve, evolve_generations, gross_returns, replicator_step, with_cash


def _random_returns(shape: tuple[int, ...], seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return np.exp(rng.normal(-0.005, 0.05, size=shape))


def test_gross_returns_rebuilds_wealth() -> None:
    w = np.array([[1.0, 1.1, 0.99, 1.2]])
    r = gross_returns(w)
    assert np.allclose(np.cumprod(r, axis=-1), w[:, 1:])


def test_gross_returns_rejects_non_positive() -> None:
    with pytest.raises(ValueError):
        gross_returns(np.array([1.0, 0.0, 1.0]))


def test_shares_sum_to_one_and_respect_floor() -> None:
    r = _random_returns((7, 5, 60))
    mu = 0.02
    shares, _ = evolve(r, mu)
    assert np.allclose(shares.sum(axis=-2), 1.0)
    assert np.all(shares[..., 1:] >= mu / 5 - 1e-15)


def test_pure_selection_is_buy_and_hold() -> None:
    r = _random_returns((4, 6, 80), seed=1)
    s0 = np.array([0.1, 0.2, 0.3, 0.1, 0.2, 0.1])
    _, wealth = evolve(r, 0.0, s0)
    member_wealth = np.cumprod(r, axis=-1)
    expected = (s0[:, None] * member_wealth).sum(axis=-2)
    assert np.allclose(wealth[..., 1:], expected)


def test_single_strategy_returns_its_own_wealth() -> None:
    r = _random_returns((3, 50), seed=2)
    s0 = np.array([0.0, 1.0, 0.0])
    _, wealth = evolve(r, 0.0, s0)
    assert np.allclose(wealth[1:], np.cumprod(r[1]))


def test_full_mutation_is_equal_rebalancing() -> None:
    r = _random_returns((4, 30), seed=3)
    _, wealth = evolve(r, 1.0)
    assert np.allclose(wealth[1:], np.cumprod(r.mean(axis=0)))


def test_replicator_step_keeps_shares_when_all_lose_everything() -> None:
    s = np.array([0.5, 0.5])
    assert np.allclose(replicator_step(s, np.zeros(2), 0.0), s)


def test_generations_pass_final_shares() -> None:
    seasons = [_random_returns((2, 5, n), seed=k) for k, n in enumerate((20, 25, 30))]
    out = evolve_generations(seasons, 0.01)
    for (prev, _), (nxt, _) in zip(out[:-1], out[1:]):
        assert np.allclose(nxt[..., 0], prev[..., -1])
    first, _ = evolve(seasons[0], 0.01)
    assert np.allclose(out[0][0], first)


def test_with_cash_appends_constant_strategy() -> None:
    r = _random_returns((2, 3, 10))
    rc = with_cash(r)
    assert rc.shape == (2, 4, 10)
    assert np.all(rc[:, -1] == 1.0)


def test_invalid_mu_and_initial() -> None:
    r = _random_returns((3, 10))
    with pytest.raises(ValueError):
        evolve(r, -0.1)
    with pytest.raises(ValueError):
        evolve(r, 0.1, np.array([0.5, 0.5, 0.5]))
