"""Test: calendari placebo dello schema (shk.model.timing_placebo), su dati costruiti."""

import numpy as np
import pytest

from shk.model.timing_placebo import (
    LEVEL_BASE,
    LEVEL_REDUCED,
    LEVEL_ZERO,
    all_shifts,
    cross_season_draws,
    fresh_sequence,
    intervention_sums,
    levels_from_lambda,
    one_sided_p,
    permutation_draws,
    resample_schedule,
    schedule_log_wealth,
    shift_draws,
)


def test_levels_from_lambda():
    lam = np.array([0.25, 0.1875, 0.0, 0.25])
    assert list(levels_from_lambda(lam, 0.25, 0.75)) == [LEVEL_BASE, LEVEL_REDUCED, LEVEL_ZERO, LEVEL_BASE]
    with pytest.raises(ValueError):
        levels_from_lambda(np.array([0.25, 0.1]), 0.25, 0.75)


def test_schedule_log_wealth_picks_the_return_of_the_level():
    r = np.array([[0.0, 0.0, 0.0], [0.1, 0.2, 0.3], [1.0, 2.0, 3.0]])
    assert schedule_log_wealth(np.array([2, 1, 0]), r) == pytest.approx(1.2)
    batch = schedule_log_wealth(np.array([[2, 2, 2], [0, 0, 0], [1, 1, 1]]), r)
    assert np.allclose(batch, [6.0, 0.0, 0.6])
    with pytest.raises(ValueError):
        schedule_log_wealth(np.array([2, 1]), r)


def test_intervention_sums_use_reduced_and_zero_days():
    features = np.array([[1.0, 2.0, 4.0], [10.0, 20.0, 40.0]])
    assert np.allclose(intervention_sums(np.array([2, 1, 0]), features), [6.0, 60.0])
    assert np.allclose(intervention_sums(np.array([[2, 2, 2], [0, 2, 2]]), features), [[0.0, 0.0], [1.0, 10.0]])


def test_within_season_draws_keep_the_exposure():
    rng = np.random.default_rng(1)
    levels = np.array([2] * 6 + [1] * 2 + [0] * 4)
    for draws in (permutation_draws(levels, 50, rng), shift_draws(levels, 50, rng), all_shifts(levels)):
        assert np.array_equal(np.sort(draws, axis=1), np.tile(np.sort(levels), (draws.shape[0], 1)))
    assert np.array_equal(all_shifts(levels)[0], levels)
    # Una rotazione conserva l'ordine ciclico: il blocco di giornate ferme resta un blocco
    for row in shift_draws(levels, 50, rng):
        assert any(np.array_equal(np.roll(levels, k), row) for k in range(levels.shape[0]))


def test_resample_schedule_keeps_relative_position():
    levels = np.array([2, 2, 0, 0])
    assert np.array_equal(resample_schedule(levels, 4), levels)
    assert np.array_equal(resample_schedule(levels, 8), [2, 2, 2, 2, 0, 0, 0, 0])
    assert np.array_equal(resample_schedule(levels, 2), [2, 0])


def test_cross_season_draws_assign_each_schedule_once():
    rng = np.random.default_rng(2)
    levels = [np.full(5, 2), np.full(7, 1), np.full(6, 0)]
    draws = cross_season_draws(levels, 40, rng)
    assert [d.shape for d in draws] == [(40, 5), (40, 7), (40, 6)]
    assigned = np.stack([d[:, 0] for d in draws], axis=1)  # il livello identifica il calendario d'origine
    assert np.array_equal(np.sort(assigned, axis=1), np.tile([0, 1, 2], (40, 1)))


def test_fresh_sequence_gives_the_same_children_whatever_was_spawned_before():
    seq = np.random.SeedSequence(7).spawn(3)[1]
    first = [c.generate_state(2).tolist() for c in fresh_sequence(seq).spawn(3)]
    seq.spawn(5)
    assert [c.generate_state(2).tolist() for c in fresh_sequence(seq).spawn(3)] == first


def test_one_sided_p_counts_the_observed_value():
    draws = np.array([0.0, 1.0, 2.0, 3.0, np.nan])
    assert one_sided_p(2.5, draws, greater=True) == pytest.approx(2 / 5)
    assert one_sided_p(2.5, draws, greater=False) == pytest.approx(4 / 5)


def test_informative_schedule_beats_its_placebos():
    """Un calendario che evita le giornate peggiori sta nella coda dei placebo di pari esposizione."""
    rng = np.random.default_rng(3)
    base = rng.normal(-0.01, 0.05, size=100)
    r = np.stack([np.zeros(100), 0.75 * base, base])
    levels = np.where(base < np.quantile(base, 0.3), LEVEL_ZERO, LEVEL_BASE)
    observed = float(schedule_log_wealth(levels, r))
    assert one_sided_p(observed, schedule_log_wealth(permutation_draws(levels, 2000, rng), r), greater=True) < 0.01
    # Una rotazione su D è il calendario stesso: su una sola stagione il p non scende sotto circa 1/D
    assert one_sided_p(observed, schedule_log_wealth(shift_draws(levels, 2000, rng), r), greater=True) < 0.05


def test_within_season_placebo_is_biased_against_a_stop_triggered_by_losses():
    """Rendimenti i.i.d. (nessuna informazione sul futuro) e uno stop che scatta dopo una serie di perdite.

    Lo stop non prevede nulla, eppure lo schema rende meno di un calendario permutato con la stessa
    esposizione nella stessa stagione, perché nelle giornate che fanno scattare lo stop stava
    puntando. Con il calendario di un'altra stagione la differenza sparisce.
    """
    rng = np.random.default_rng(4)
    n_worlds, n_days, look = 4000, 100, 10
    r = rng.normal(-0.005, 0.05, size=(2, n_worlds, n_days))  # due stagioni indipendenti per mondo
    trailing = np.cumsum(r, axis=-1)
    trailing[..., look:] -= trailing[..., :-look].copy()
    triggered = trailing < -0.4
    stop_day = np.where(triggered.any(axis=-1), triggered.argmax(axis=-1) + 1, n_days)  # giornate puntate
    invested = np.arange(n_days) < stop_day[..., None]
    scheme = (r * invested).sum(axis=-1)
    season_total = r.sum(axis=-1)
    same_season = stop_day / n_days * season_total           # valore atteso del placebo "permutation"
    other_season = stop_day[::-1] / n_days * season_total    # calendario dell'altra stagione
    assert 0.2 < (stop_day < n_days).mean() < 0.9

    def z(diff: np.ndarray) -> float:
        return float(diff.mean() / (diff.std(ddof=1) / np.sqrt(diff.size)))

    assert z(scheme - same_season) < -5.0
    assert abs(z(scheme - other_season)) < 3.0
