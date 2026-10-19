"""Test di accettazione: Oaxaca-Blinder su verità nota."""

import csv
import math
from pathlib import Path

import numpy as np
import pytest

from shk.stats.oaxaca_synthetic import (
    CASES,
    COMPONENTS,
    OB_SYNTHETIC_CSV_COLUMNS,
    SEED_S8,
    evaluate_synthetic_cases,
    spawn_t45_generators,
    true_components,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "results" / "us_c7_1_ob_synthetic.csv"
PNG_PATH = REPO_ROOT / "thesis" / "figures" / "us_c7_1_ob_synthetic.png"
BIAS_CASES = ("a_mixed", "b_composition", "c_structure", "e_ar1")


def _read_csv() -> list[dict[str, str]]:
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert tuple(reader.fieldnames or ()) == OB_SYNTHETIC_CSV_COLUMNS
        return list(reader)


@pytest.fixture(scope="module")
def simulation():
    """Esegue una volta i cinque casi con R = 1 000 (circa 10 s)."""
    return evaluate_synthetic_cases(seed=SEED_S8)


def test_identity_every_replica(simulation):
    """In ogni replica three-fold e two-fold sommano al totale entro 1e-12."""
    reps, _ = simulation
    for rep in reps:
        assert rep.max_threefold_residual <= 1e-12
        assert rep.max_twofold_residual <= 1e-12


def test_mean_estimates_within_three_mc_se(simulation):
    """Casi (a), (b), (c), (e): media di ogni componente entro 3 e.s. Monte Carlo dalla verità."""
    reps, _ = simulation
    for rep in reps:
        if rep.case.name not in BIAS_CASES:
            continue
        truth = true_components(rep.case)
        for comp in COMPONENTS:
            est = rep.components[comp]
            mc_se = est.std(ddof=1) / math.sqrt(est.size)
            assert abs(est.mean() - truth[comp]) < 3.0 * mc_se, (rep.case.name, comp)


def test_composition_and_structure_only_cases(simulation):
    """(b): strutturale media compatibile con 0; (c): compositiva media compatibile con 0."""
    reps, _ = simulation
    by_name = {rep.case.name: rep for rep in reps}
    s_b = by_name["b_composition"].components["structural"]
    c_c = by_name["c_structure"].components["compositional"]
    assert abs(s_b.mean()) < 3.0 * s_b.std(ddof=1) / math.sqrt(s_b.size)
    assert abs(c_c.mean()) < 3.0 * c_c.std(ddof=1) / math.sqrt(c_c.size)


def test_csv_matches_simulation(simulation):
    """Il CSV versionato coincide con la simulazione (float entro 1e-12)."""
    _, records = simulation
    rows = _read_csv()
    assert len(rows) == len(records)
    for row, rec in zip(rows, records):
        for col in OB_SYNTHETIC_CSV_COLUMNS:
            if isinstance(rec[col], float):
                assert math.isclose(float(row[col]), rec[col], rel_tol=1e-12, abs_tol=1e-15), col
            else:
                assert row[col] == str(rec[col]), col


def test_csv_structure_and_figure():
    """Righe per caso e componente, residui d'identità e figura."""
    rows = _read_csv()
    for case in CASES:
        comps = [r["component"] for r in rows if r["row_type"] == "component" and r["case"] == case.name]
        assert comps == list(COMPONENTS)
        ident = [float(r["max_abs_residual"]) for r in rows if r["row_type"] == "identity" and r["case"] == case.name]
        assert len(ident) == 2 and max(ident) <= 1e-12
    assert PNG_PATH.is_file() and PNG_PATH.stat().st_size > 0


def test_spawn_t45_generators_scheme():
    """Un generatore per caso da SeedSequence(SEED_S8).spawn(5)[0].spawn(5)."""
    rngs = spawn_t45_generators(SEED_S8)
    children = np.random.SeedSequence(SEED_S8).spawn(5)[0].spawn(len(CASES))
    for rng, child in zip(rngs, children):
        assert rng.integers(0, 2**62) == np.random.default_rng(child).integers(0, 2**62)
