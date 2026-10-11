"""Test di accettazione di T53: regola di N_SEEDS sui valori del CSV dell'analisi di potenza."""

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.model.covariate_inspection import derive_specification
from shk.model.module2_data import build_module2_frame
from shk.model.module3_synthetic import SEED_S9
from shk.model.power import (
    N_POWER_SEEDS,
    POWER_CSV_COLUMNS,
    TIMING_COLUMNS,
    Z_95,
    evaluate_power,
    n_seeds_rule,
    spawn_t53_generators,
)
from shk.model.residuals import load_model_residuals

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "results" / "us_c8_3b_power.csv"
TRAINING = ["2000-01", "2010-11", "2020-21"]


def test_n_seeds_rule_cases():
    """Multiplo di 100, minimo 500, ripiego a 1 000 con effetto < 1e-6 o con più di 5 000."""
    for effect in (0.0, 5e-7, -5e-7):
        n_min, n, rule = n_seeds_rule(0.2, effect)
        assert math.isnan(n_min) and (n, rule) == (1000, "small_effect")
    n_min, n, rule = n_seeds_rule(0.2, 0.05)
    assert rule == "rule" and n == max(500, 100 * math.ceil(n_min / 100))
    assert n_seeds_rule(0.001, 0.05)[1] == 500
    n_min, n, rule = n_seeds_rule(3.0, 0.01)
    assert n_min > 5000 and (n, rule) == (1000, "too_large")
    # Al valore scelto la semiampiezza è entro 0.2·|C1 − C0|, al multiplo precedente no
    n_min, n, _ = n_seeds_rule(0.5, 0.02)
    assert Z_95 * 0.5 / math.sqrt(19 * n) <= 0.2 * 0.02 < Z_95 * 0.5 / math.sqrt(19 * (n - 100))


def test_n_seeds_follows_rule_on_csv():
    """N_SEEDS del CSV segue meccanicamente la regola del passo 4 dai valori per seed del CSV."""
    df = pd.read_csv(CSV_PATH)
    assert tuple(df.columns) == POWER_CSV_COLUMNS
    seeds = df[df["row_type"] == "seed"]
    assert sorted(set(seeds["season"])) == TRAINING
    assert (seeds.groupby("season").size() == N_POWER_SEEDS).all()
    var2 = [float(np.var(g["diff_c2_c1"], ddof=1)) for _, g in seeds.groupby("season")]
    mean1 = float(np.mean([g["diff_c1_c0"].mean() for _, g in seeds.groupby("season")]))
    sd2 = math.sqrt(float(np.mean(var2)))
    pooled = df[df["row_type"] == "pooled"].iloc[0]
    assert math.isclose(pooled["sd_c2_c1"], sd2, rel_tol=1e-12)
    assert math.isclose(pooled["mean_c1_c0"], mean1, rel_tol=1e-12, abs_tol=1e-15)
    _, n, rule = n_seeds_rule(sd2, mean1)
    assert int(pooled["n_seeds"]) == n and pooled["n_seeds_rule"] == rule
    assert n >= 500 and n % 100 == 0
    assert int(pooled["s10_runs"]) == (n + 1) * 19 * 3


def test_spawn_t53_generators_scheme():
    gens = spawn_t53_generators(TRAINING, 4, SEED_S9)
    child = np.random.SeedSequence(SEED_S9).spawn(5)[3].spawn(3)[2].spawn(4)[1]
    assert gens["2020-21"][1].integers(0, 2**62) == np.random.default_rng(child).integers(0, 2**62)


@pytest.mark.slow
def test_recalculation_from_real_data_matches_csv():
    """Ricalcolo completo (600 esecuzioni) contro il CSV, colonne dei tempi escluse."""
    if not (DEFAULT_DATA_DIR.is_dir() and any(DEFAULT_DATA_DIR.glob("*.csv"))):
        pytest.skip(f"Real data missing: no CSV in {DEFAULT_DATA_DIR}")
    frame = build_module2_frame(load_model_residuals())
    train = frame[frame["role"] == "training"]
    records = evaluate_power(train, derive_specification(train).covariates)
    df = pd.read_csv(CSV_PATH, dtype=str, keep_default_na=False)
    assert len(df) == len(records)
    for (_, row), rec in zip(df.iterrows(), records):
        for col in POWER_CSV_COLUMNS:
            if col in TIMING_COLUMNS:
                continue
            val = rec[col]
            if isinstance(val, float) and not isinstance(val, bool):
                if math.isnan(val) or math.isinf(val):
                    assert row[col] == str(val), col
                else:
                    assert math.isclose(float(row[col]), val, rel_tol=1e-12, abs_tol=1e-15), col
            else:
                assert row[col] == str(val), col
