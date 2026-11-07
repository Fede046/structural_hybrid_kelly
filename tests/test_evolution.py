"""Test di variazione e selezione delle strategie (shk.model.evolution)."""

import numpy as np
import pytest

from shk.model.evolution import (
    LAM_MIN,
    RULES,
    STOPS,
    SUPERVISORS,
    Genome,
    mutate,
    next_generation,
    random_genome,
)


def test_random_genomes_are_valid_and_varied():
    rng = np.random.default_rng(0)
    gs = [random_genome(rng) for _ in range(300)]
    assert all(LAM_MIN <= g.lam <= 1.0 and 0.0 <= g.kappa <= 1.0 for g in gs)
    assert {g.supervisor for g in gs} == set(SUPERVISORS)
    assert {g.stop for g in gs} == set(STOPS)
    assert {g.rule for g in gs} == set(RULES)


def test_mutation_stays_in_bounds_and_mostly_keeps_discrete_genes():
    rng = np.random.default_rng(1)
    g = Genome(lam=1.0, kappa=0.0, supervisor="none", stop="clear", rule="R1")
    kids = [mutate(g, rng) for _ in range(2000)]
    assert all(LAM_MIN <= k.lam <= 1.0 and 0.0 <= k.kappa <= 1.0 for k in kids)
    changed = np.mean([k.rule != g.rule for k in kids])
    assert 0.07 < changed < 0.13
    assert any(k.lam < 1.0 for k in kids)


def test_next_generation_keeps_best_half_and_adds_children():
    rng = np.random.default_rng(2)
    gs = [random_genome(rng) for _ in range(6)]
    fitness = np.array([0.1, -2.0, 0.5, -0.3, 0.2, -1.0])
    new = next_generation(gs, fitness, rng)
    assert new[:3] == [gs[2], gs[4], gs[0]]
    assert len(new) == 6


def test_next_generation_rejects_bad_input():
    rng = np.random.default_rng(3)
    gs = [random_genome(rng) for _ in range(3)]
    with pytest.raises(ValueError):
        next_generation(gs, np.zeros(3), rng)
    with pytest.raises(ValueError):
        next_generation(gs[:2], np.array([0.0, np.nan]), rng)


def test_genome_validation():
    with pytest.raises(ValueError):
        Genome(lam=0.0, kappa=0.5, supervisor="none", stop="clear", rule="R1")
    with pytest.raises(ValueError):
        Genome(lam=0.5, kappa=0.5, supervisor="other", stop="clear", rule="R1")


def test_fixed_lam_never_changes():
    rng = np.random.default_rng(4)
    gs = [random_genome(rng, fixed_lam=0.25) for _ in range(10)]
    assert all(g.lam == 0.25 for g in gs)
    for _ in range(20):
        gs = next_generation(gs, rng.normal(size=10), rng, fixed_lam=0.25)
    assert all(g.lam == 0.25 for g in gs)
