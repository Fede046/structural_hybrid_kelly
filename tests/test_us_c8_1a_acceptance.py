"""Test di accettazione: tabella del criterio, regola di scelta e trappola sul CSV."""

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shk.model.module3 import CANDIDATES, CHOSEN_CANDIDATE
from shk.model.module3_synthetic import (
    MODULE3_SYNTHETIC_CSV_COLUMNS,
    REGIMES,
    SEED_S9,
    choose_candidate,
    evaluate_module3_synthetic,
    spawn_t51_generators,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "results" / "us_c8_1a_module3_synthetic.csv"
PNG_PATH = REPO_ROOT / "thesis" / "figures" / "us_c8_1a_module3_synthetic.png"


def test_csv_structure_has_every_candidate_per_regime():
    df = pd.read_csv(CSV_PATH)
    assert tuple(df.columns) == MODULE3_SYNTHETIC_CSV_COLUMNS
    crit = df[df["row_type"] == "criterion"]
    for regime in (*REGIMES, "mean"):
        assert sorted(crit[crit["regime"] == regime]["candidate"]) == sorted(CANDIDATES)
    assert (crit[crit["regime"] != "mean"]["n_replicas"] == 500).all()
    arms = df[df["row_type"] == "arm"]
    for regime in REGIMES:
        assert sorted(arms[arms["regime"] == regime]["arm"]) == sorted(("C0", "C1", *CANDIDATES))
    assert sorted(df[df["row_type"] == "trap"]["arm"]) == ["C0", "P1", "P2"]
    assert PNG_PATH.is_file() and PNG_PATH.stat().st_size > 0


def test_choice_follows_rule_on_csv():
    """La scelta del CSV è quella della regola del passo 4 applicata alla tabella, ed è la funzione del Modulo 3."""
    df = pd.read_csv(CSV_PATH)
    crit = df[df["row_type"] == "criterion"]
    by_regime = [{c: float(crit[(crit["regime"] == r) & (crit["candidate"] == c)]["mse"].iloc[0])
                  for c in CANDIDATES} for r in REGIMES]
    chosen = choose_candidate(by_regime)
    flagged = crit[crit["chosen"].astype(str) == "True"]
    assert set(flagged["candidate"]) == {chosen}
    assert chosen != "P1"
    assert CHOSEN_CANDIDATE == chosen
    for c in CANDIDATES:
        mean_row = float(crit[(crit["regime"] == "mean") & (crit["candidate"] == c)]["mse"].iloc[0])
        assert math.isclose(mean_row, float(np.mean([m[c] for m in by_regime])), rel_tol=1e-12)


def test_trap_p2_dominates_p1_on_csv():
    """Criterio vincolante (nota 3.2 §7.5) sui valori del CSV: R = 2000."""
    trap = pd.read_csv(CSV_PATH).query("row_type == 'trap'").set_index("arm")
    assert trap.loc["P2", "median_final_wealth"] > trap.loc["P1", "median_final_wealth"]
    assert trap.loc["P2", "mean_max_drawdown"] < trap.loc["P1", "mean_max_drawdown"]


def test_detect_grade_shares_sum_to_one():
    dg = pd.read_csv(CSV_PATH).query("row_type == 'detect_grade'")
    assert len(dg) == 2 * len(REGIMES)
    finite = dg[np.isfinite(dg["share_detect"])]
    assert ((finite["share_detect"] + finite["share_grade"] - 1.0).abs() <= 1e-9).all()


def test_spawn_t51_generators_scheme():
    rngs = spawn_t51_generators(SEED_S9)
    assert len(rngs) == 5
    child = np.random.SeedSequence(SEED_S9).spawn(5)[1].spawn(5)[3]
    assert rngs[3].integers(0, 2**62) == np.random.default_rng(child).integers(0, 2**62)


@pytest.mark.slow
def test_recalculation_matches_csv():
    """Ricalcolo completo (R = 500, trappola 2000) contro il CSV versionato."""
    _, _, _, records = evaluate_module3_synthetic()
    df = pd.read_csv(CSV_PATH, dtype=str, keep_default_na=False)
    assert len(df) == len(records)
    for (_, row), rec in zip(df.iterrows(), records):
        for col in MODULE3_SYNTHETIC_CSV_COLUMNS:
            val = rec[col]
            if isinstance(val, float):
                if math.isnan(val):
                    assert row[col].lower() == "nan", col
                else:
                    assert math.isclose(float(row[col]), val, rel_tol=1e-12, abs_tol=1e-15), col
            else:
                assert row[col] == str(val), col
