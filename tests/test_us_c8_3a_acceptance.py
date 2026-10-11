"""Test di accettazione di T42: lunghezza dei blocchi sulle serie del Modulo 1 e copertura."""

import csv
import math
from pathlib import Path

import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.model.block_length import (
    BLOCK_LENGTH_CSV_COLUMNS,
    METHOD_IID,
    METHOD_STATIONARY_L_PW,
    ROW_TYPE_COVERAGE,
    ROW_TYPE_SERIES,
    SERIES_KIND_TRAINING,
    SERIES_KIND_VALIDATION,
    compute_mean_coverage_records,
    compute_series_block_length_records,
    nearest_fixed_block_length,
    spawn_t42_generators,
)
from shk.model.residuals import load_model_residuals
from shk.stats.bootstrap import round_block_length
from shk.stats.false_rejection import SEED_S7

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "results" / "us_c8_3a_block_length.csv"
PNG_PATH = REPO_ROOT / "thesis" / "figures" / "us_c8_3a_block_length.png"
N_TRAINING_SERIES = 3
N_VALIDATION_SERIES = 19
FLOAT_COLUMNS = (
    "l_pw_stationary",
    "l_pw_circular",
    "phi",
    "coverage",
    "mean_block_length_used",
    "mc_lower_99",
    "mc_upper_99",
)


def _has_real_data() -> bool:
    """Vero se data/raw/E0/ contiene almeno un CSV."""
    return DEFAULT_DATA_DIR.is_dir() and any(DEFAULT_DATA_DIR.glob("*.csv"))


def _read_csv() -> list[dict[str, str]]:
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert tuple(reader.fieldnames or ()) == BLOCK_LENGTH_CSV_COLUMNS
        return list(reader)


def _assert_rows_match(csv_rows: list[dict[str, str]], records: list[dict]) -> None:
    """Confronto campo per campo: float entro rel 1e-12, gli altri come stringa."""
    assert len(csv_rows) == len(records)
    for csv_row, rec in zip(csv_rows, records):
        for col in BLOCK_LENGTH_CSV_COLUMNS:
            expected = rec[col]
            if col in FLOAT_COLUMNS and expected != "":
                assert math.isclose(float(csv_row[col]), float(expected), rel_tol=1e-12), col
            else:
                assert csv_row[col] == str(expected), col


def test_nearest_fixed_block_length():
    """La più vicina fra 7, 20 e 40; a parità la più piccola."""
    assert nearest_fixed_block_length(0.2) == 7
    assert nearest_fixed_block_length(13.5) == 7
    assert nearest_fixed_block_length(13.6) == 20
    assert nearest_fixed_block_length(30.0) == 20
    assert nearest_fixed_block_length(31.0) == 40
    with pytest.raises(ValueError):
        nearest_fixed_block_length(-1.0)


def test_spawn_t42_generators_scheme():
    """I generatori vengono da SeedSequence(SEED_S7).spawn(5)[2].spawn(3)."""
    import numpy as np

    rngs = spawn_t42_generators(SEED_S7)
    children = np.random.SeedSequence(SEED_S7).spawn(5)[2].spawn(3)
    for rng, child in zip(rngs, children):
        assert rng.integers(0, 2**62) == np.random.default_rng(child).integers(0, 2**62)
    with pytest.raises(TypeError, match="seed must be an integer"):
        spawn_t42_generators(1.0)  # type: ignore


def test_csv_one_row_per_series_and_coverage_rows():
    """Una riga per serie (3 di training, 19 di validazione) e due righe di copertura."""
    rows = _read_csv()
    series = [r for r in rows if r["row_type"] == ROW_TYPE_SERIES]
    coverage = [r for r in rows if r["row_type"] == ROW_TYPE_COVERAGE]
    assert len(series) == N_TRAINING_SERIES + N_VALIDATION_SERIES
    assert len(coverage) == 2
    assert len(rows) == len(series) + len(coverage)

    training = [r for r in series if r["series_kind"] == SERIES_KIND_TRAINING]
    validation = [r for r in series if r["series_kind"] == SERIES_KIND_VALIDATION]
    assert [int(r["n_obs"]) for r in training] == [380, 760, 1140]
    assert len(validation) == N_VALIDATION_SERIES
    assert all(int(r["n_obs"]) == 380 for r in validation)
    assert len({r["seasons"] for r in validation}) == N_VALIDATION_SERIES

    for r in series:
        l_sb = float(r["l_pw_stationary"])
        l_cb = float(r["l_pw_circular"])
        assert int(r["l_pw_stationary_rounded"]) == round_block_length(l_sb)
        assert int(r["l_pw_circular_rounded"]) == round_block_length(l_cb)
        assert int(r["nearest_fixed_block_length"]) == nearest_fixed_block_length(l_cb)

    assert [r["method"] for r in coverage] == [METHOD_STATIONARY_L_PW, METHOD_IID]
    for r in coverage:
        assert int(r["covered"]) / int(r["n_series"]) == float(r["coverage"])


def test_figure_exists():
    """La figura esiste e non è vuota."""
    assert PNG_PATH.is_file()
    assert PNG_PATH.stat().st_size > 0


def test_coverage_rows_recomputed():
    """Le righe di copertura si ricalcolano identiche dal seed (senza dati reali)."""
    rows = [r for r in _read_csv() if r["row_type"] == ROW_TYPE_COVERAGE]
    _assert_rows_match(rows, compute_mean_coverage_records(seed=SEED_S7))


def test_series_rows_recomputed_from_real_data():
    """Le righe per serie si ricalcolano dai dati reali (saltato senza data/raw/E0/)."""
    if not _has_real_data():
        pytest.skip(f"Real data missing: no CSV in {DEFAULT_DATA_DIR}")
    data = load_model_residuals()
    records = compute_series_block_length_records(data.residuals, data.schedule)
    rows = [r for r in _read_csv() if r["row_type"] == ROW_TYPE_SERIES]
    _assert_rows_match(rows, records)
