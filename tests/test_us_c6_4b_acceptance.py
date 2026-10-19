"""Test di accettazione: diagnostiche della varianza nel tempo."""

import csv
import hashlib
import math
from pathlib import Path

import numpy as np
import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.model.residuals import load_model_residuals
from shk.model.variance_change import (
    CALIBRATED_METHODS,
    METHOD_NOMINAL,
    STAT_ARCH_LM,
    STAT_BROWN_FORSYTHE,
    STAT_GOLDFELD_QUANDT,
    STAT_ROLLING,
    TIME_STATISTICS,
    VARIANCE_CHANGE_CSV_COLUMNS,
    evaluate_variance_change,
    spawn_t44_generators,
)
from shk.model.residual_heteroskedasticity import BONFERRONI_LOWER, BONFERRONI_UPPER
from shk.stats.false_rejection import SEED_S7

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "results" / "us_c6_4b_variance_change.csv"
PNG_PATH = REPO_ROOT / "thesis" / "figures" / "us_c6_4b_variance_change.png"
C6_4_CSV_PATH = REPO_ROOT / "results" / "us_c6_4_heteroskedasticity.csv"
C6_4_SHA256 = "c98a6c96c7e561b8caafdddeabc56c9493414c6ba56cd4680bfe37485397b7fd"
N_SCENARIOS = 22
FLOAT_COLUMNS = (
    "statistic_value", "statistic_aux", "threshold", "threshold_lower", "rejection_rate",
    "mc_lower", "mc_upper", "p_value_binomial", "z_mean", "z_var",
)


def _has_real_data() -> bool:
    """Vero se data/raw/E0/ contiene almeno un CSV."""
    return DEFAULT_DATA_DIR.is_dir() and any(DEFAULT_DATA_DIR.glob("*.csv"))


def _read_csv() -> list[dict[str, str]]:
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert tuple(reader.fieldnames or ()) == VARIANCE_CHANGE_CSV_COLUMNS
        return list(reader)


def test_csv_structure_one_row_per_season_statistic_method():
    """Una riga per stagione x statistica x metodo di soglia, più verifica e riepiloghi."""
    rows = _read_csv()
    by_type: dict[str, list[dict[str, str]]] = {}
    for r in rows:
        by_type.setdefault(r["row_type"], []).append(r)

    assert len(by_type["z_moments"]) == N_SCENARIOS
    scenario = by_type["scenario"]
    keys = {(r["season"], r["statistic"], r["method"]) for r in scenario}
    assert len(keys) == len(scenario)
    seasons = {r["season"] for r in scenario}
    assert len(seasons) == N_SCENARIOS
    for season in seasons:
        for stat in TIME_STATISTICS:
            methods = {r["method"] for r in scenario if r["season"] == season and r["statistic"] == stat}
            expected = set(CALIBRATED_METHODS)
            if stat != STAT_ROLLING:
                expected.add(METHOD_NOMINAL)
            assert methods == expected
    assert len(by_type["verification"]) == 3 * len(TIME_STATISTICS) * len(CALIBRATED_METHODS) + len(CALIBRATED_METHODS)
    assert len(by_type["summary"]) == 14
    assert [r["method"] for r in by_type["between_seasons"]] == [METHOD_NOMINAL, *CALIBRATED_METHODS]


def test_verification_within_bonferroni_interval():
    """La verifica delle soglie calibrate sta nell'intervallo con Bonferroni (criterio vincolante)."""
    rows = [r for r in _read_csv() if r["row_type"] == "verification"]
    time_rows = [r for r in rows if r["statistic"] in TIME_STATISTICS]
    assert len(time_rows) == 36
    for r in time_rows:
        rate = int(r["rejections"]) / int(r["n_resamples"])
        assert math.isclose(rate, float(r["rejection_rate"]))
        assert BONFERRONI_LOWER <= rate <= BONFERRONI_UPPER, (r["fit_through"], r["statistic"], r["method"])
        assert r["within_interval"] == "True"


def test_summary_counts_match_scenario_rows():
    """I rigetti di riepilogo contano le stagioni di validazione con reject = True."""
    rows = _read_csv()
    scenario = [r for r in rows if r["row_type"] == "scenario" and r["role"] == "validation"]
    for r in (x for x in rows if x["row_type"] == "summary"):
        count = sum(
            s["reject"] == "True" for s in scenario
            if s["statistic"] == r["statistic"] and s["method"] == r["method"]
        )
        assert int(r["rejections"]) == count
        assert int(r["n_validation"]) == 19


def test_goldfeld_quandt_rows_consistent():
    """Per Goldfeld-Quandt statistic_value = |ln F| e statistic_aux = F."""
    for r in _read_csv():
        if r["row_type"] == "scenario" and r["statistic"] == STAT_GOLDFELD_QUANDT:
            assert math.isclose(float(r["statistic_value"]), abs(math.log(float(r["statistic_aux"]))), rel_tol=1e-12)


def test_figure_exists_and_c6_4_csv_unchanged():
    """La figura esiste e il CSV del test di eteroschedasticità non è cambiato."""
    assert PNG_PATH.is_file() and PNG_PATH.stat().st_size > 0
    assert hashlib.sha256(C6_4_CSV_PATH.read_bytes()).hexdigest() == C6_4_SHA256


def test_spawn_t44_generators_scheme():
    """Generatori da SeedSequence(SEED_S7).spawn(5)[4].spawn(4), poi 4 L e (calibrazione, verifica)."""
    groups = spawn_t44_generators(SEED_S7)
    assert len(groups) == 4 and all(len(g) == 4 for g in groups)
    child = np.random.SeedSequence(SEED_S7).spawn(5)[4].spawn(4)[3].spawn(4)[2].spawn(2)[1]
    assert groups[3][2][1].integers(0, 2**62) == np.random.default_rng(child).integers(0, 2**62)


def test_recalculation_from_real_data_matches_csv():
    """Ricalcolo dai dati reali: coincide col CSV (float entro 1e-12); saltato senza dati."""
    if not _has_real_data():
        pytest.skip(f"Real data missing: no CSV in {DEFAULT_DATA_DIR}")
    data = load_model_residuals()
    records = evaluate_variance_change(data.residuals, data.schedule, seed=SEED_S7)
    rows = _read_csv()
    assert len(rows) == len(records)
    for row, rec in zip(rows, records):
        for col in VARIANCE_CHANGE_CSV_COLUMNS:
            expected = rec[col]
            if col in FLOAT_COLUMNS and expected != "":
                assert math.isclose(float(row[col]), float(expected), rel_tol=1e-12, abs_tol=1e-15), col
            else:
                assert row[col] == str(expected), col
    assert any(r["statistic"] == STAT_ARCH_LM for r in rows)
    assert any(r["statistic"] == STAT_BROWN_FORSYTHE for r in rows)
