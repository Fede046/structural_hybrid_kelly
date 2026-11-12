"""Test della versione principale nelle analisi rifatte (shk.model.main_version, shk.model.evolution_main)."""

import numpy as np
import pytest

from shk.model.evolution import LAM_MIN, RULES, STOPS, SUPERVISORS
from shk.model.evolution_main import MainGenome, mutate, next_generation, random_genome
from shk.model.main_version import DIAGNOSES, MAIN_POPULATION_ARMS, RULE_ARMS, RULE_REFERENCES, TEST_ARMS, THRESHOLDS


def test_arm_names():
    assert set(RULE_REFERENCES) <= set(RULE_ARMS) and set(RULE_REFERENCES.values()) <= set(RULE_ARMS)
    assert "M" in TEST_ARMS and "B_0.25" in TEST_ARMS
    assert {"M", "M_clear", "R3_M", "R3_M_clear"} <= set(MAIN_POPULATION_ARMS)


def test_random_genomes_cover_the_new_genes():
    rng = np.random.default_rng(0)
    gs = [random_genome(rng) for _ in range(400)]
    assert all(LAM_MIN <= g.lam <= 1.0 and 0.0 <= g.kappa <= 1.0 for g in gs)
    assert {g.supervisor for g in gs} == set(SUPERVISORS) and {g.stop for g in gs} == set(STOPS)
    assert {g.rule for g in gs} == set(RULES)
    assert {g.thresholds for g in gs} == set(THRESHOLDS) and {g.diagnosis for g in gs} == set(DIAGNOSES)


def test_is_main():
    main = MainGenome(0.25, 0.75, "calibration", "season", "R1", "season", "two")
    assert main.is_main()
    assert not MainGenome(0.25, 0.75, "calibration", "season", "R1", "day", "two").is_main()
    assert not MainGenome(0.25, 0.75, "previous", "season", "R1", "season", "two").is_main()


def test_invalid_genes():
    with pytest.raises(ValueError):
        MainGenome(0.25, 0.75, "calibration", "season", "R1", "week", "two")
    with pytest.raises(ValueError):
        MainGenome(0.25, 0.75, "calibration", "season", "R1", "season", "four")


def test_mutation_switches_new_genes_rarely_and_keeps_fixed_lam():
    rng = np.random.default_rng(1)
    g = MainGenome(0.25, 0.5, "calibration", "season", "R1", "season", "two")
    kids = [mutate(g, rng, fixed_lam=0.25) for _ in range(2000)]
    assert all(k.lam == 0.25 for k in kids)
    for gene in ("thresholds", "diagnosis"):
        changed = np.mean([getattr(k, gene) != getattr(g, gene) for k in kids])
        assert 0.07 < changed < 0.13


def test_next_generation_keeps_best_half():
    rng = np.random.default_rng(2)
    gs = [random_genome(rng) for _ in range(6)]
    nxt = next_generation(gs, np.array([0.1, -2.0, 0.5, -0.3, 0.2, -1.0]), rng)
    assert nxt[:3] == [gs[2], gs[4], gs[0]] and len(nxt) == 6
    with pytest.raises(ValueError):
        next_generation(gs[:5], np.zeros(5), rng)
