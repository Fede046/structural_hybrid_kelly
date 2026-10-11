"""Test di src/shk/stats/nopo.py e della regola fuori supporto alla data (T49)."""

import math

import numpy as np
import pandas as pd
import pytest

from shk.model.did_support import _did_from_sums, out_of_support_at_date
from shk.model.module2 import prepare_module2_data
from shk.stats.nopo import (
    MIN_CELL_COUNT,
    cell_ids,
    did_2x2,
    nopo_decomposition,
    nopo_from_covariates,
    out_of_support_mask,
    quintile_edges,
)


def test_nopo_parts_sum_to_total():
    """Le quattro parti sommano al totale entro 1e-12 su dati casuali."""
    rng = np.random.default_rng(1)
    for _ in range(50):
        ca = rng.integers(0, 12, size=150)
        cb = rng.integers(3, 15, size=170)
        ya, yb = rng.normal(size=150), rng.normal(0.2, 1.0, size=170)
        r = nopo_decomposition(ca, ya, cb, yb)
        assert abs(r.out_of_support_a + r.out_of_support_b + r.composition + r.structure - r.total) <= 1e-12
        assert 0.0 < r.share_unmatched_a < 1.0 and 0.0 < r.share_unmatched_b < 1.0


def test_nopo_full_support_has_zero_out_of_support():
    """Supporto pieno: le due parti fuori supporto valgono 0 (criterio T49)."""
    rng = np.random.default_rng(2)
    ca = np.repeat(np.arange(6), 30)
    cb = np.repeat(np.arange(6), 25)
    r = nopo_decomposition(ca, rng.normal(size=ca.size), cb, rng.normal(size=cb.size))
    assert r.out_of_support_a == 0.0 and r.out_of_support_b == 0.0
    assert r.share_unmatched_a == 0.0 and r.share_unmatched_b == 0.0
    assert abs(r.composition + r.structure - r.total) <= 1e-12


def test_nopo_hand_example():
    """Esempio a mano: celle {0, 1} in A, {1, 2} in B."""
    ca, ya = np.array([0, 0, 1, 1]), np.array([1.0, 3.0, 2.0, 4.0])
    cb, yb = np.array([1, 1, 2, 2]), np.array([5.0, 7.0, 0.0, 2.0])
    r = nopo_decomposition(ca, ya, cb, yb)
    # ȳ_A = 2.5, ȳ_B = 3.5; comune la cella 1: ȳ_A^m = 3, ȳ_B^m = 6; p_A^u = p_B^u = 0.5
    assert math.isclose(r.total, 1.0)
    assert math.isclose(r.out_of_support_a, -0.5 * (2.0 - 3.0))
    assert math.isclose(r.out_of_support_b, 0.5 * (1.0 - 6.0))
    assert math.isclose(r.composition, 0.0)
    assert math.isclose(r.structure, 3.0)


def test_cells_and_quintiles():
    x = np.column_stack([np.arange(100, dtype=float), np.r_[np.zeros(50), np.ones(50)]])
    edges = quintile_edges(x, [1])
    assert edges[1] is None and len(edges[0]) == 4
    ids = cell_ids(x, edges)
    assert len(np.unique(ids)) == 6  # 5 quintili x 2 livelli, con i livelli allineati alle metà
    with pytest.raises(ValueError, match="Dummy column"):
        cell_ids(np.column_stack([x[:, 0], x[:, 1] * 2]), edges)
    r = nopo_from_covariates(x[:50], np.ones(50), x[50:], np.zeros(50), [1])
    assert r.share_unmatched_a == 1.0 and r.share_unmatched_b == 1.0


def test_did_hand_example():
    """DiD a mano: (E tardi 4 − E presto 1) − (NE tardi 2 − NE presto 1) = 2."""
    y = np.array([1.0, 1.0, 4.0, 4.0, 1.0, 1.0, 2.0, 2.0])
    treated = np.array([1, 1, 1, 1, 0, 0, 0, 0], dtype=bool)
    late = np.array([0, 0, 1, 1, 0, 0, 1, 1], dtype=bool)
    assert did_2x2(y, treated, late) == 2.0
    sums = np.array([[8.0, 2.0, 4.0, 2.0]])
    counts = np.array([[2.0, 2.0, 2.0, 2.0]])
    assert _did_from_sums(sums, counts)[0] == 2.0
    with pytest.raises(ValueError, match="Empty DiD cell"):
        did_2x2(y, np.ones(8, dtype=bool), late)


def _support_frame(seed: int = 3) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = 380
    dates = pd.Timestamp("2006-08-10") + pd.to_timedelta(np.arange(n) // 4 * 3, unit="D")
    return pd.DataFrame({
        "season": "2006-07", "Date": dates, "delta": rng.normal(size=n),
        "c1": rng.integers(0, 3, size=n).astype(float), "flag_promoted": (rng.random(n) < 0.3).astype(int),
    })


def test_out_of_support_uses_only_window_a():
    """Mutante: cambiare partite fuori dalla finestra A non cambia la regola; cambiare A sì."""
    frame = _support_frame()
    covs = ("c1", "flag_promoted")
    data = prepare_module2_data(frame, covs)
    w = 40
    d = np.datetime64(frame["Date"].iloc[200], "ns")
    match_x = frame[list(covs)].to_numpy(float)[200:210]
    base = out_of_support_at_date(data, "2006-07", d, w, match_x, [1])
    assert base is not None
    eligible = np.flatnonzero(data.dates < d)
    window_a = eligible[-2 * w:-w]
    outside = np.setdiff1d(np.arange(len(frame)), window_a)

    mutated = frame.copy()
    mutated.loc[outside, "c1"] = 0.0
    mutated.loc[outside, "flag_promoted"] = 1
    mutated.loc[outside, "delta"] = 99.0
    same = out_of_support_at_date(prepare_module2_data(mutated, covs), "2006-07", d, w, match_x, [1])
    np.testing.assert_array_equal(same, base)

    inside = frame.copy()
    inside.loc[window_a, "c1"] = 2.0
    inside.loc[window_a, "flag_promoted"] = 1
    changed = out_of_support_at_date(prepare_module2_data(inside, covs), "2006-07", d, w, match_x, [1])
    assert not np.array_equal(changed, base)


def test_out_of_support_threshold():
    """Una cella con almeno MIN_CELL_COUNT partite di A è nel supporto, con meno è fuori."""
    a = np.column_stack([np.r_[np.zeros(MIN_CELL_COUNT), np.ones(MIN_CELL_COUNT - 1)], np.zeros(2 * MIN_CELL_COUNT - 1)])
    m = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]])
    assert out_of_support_mask(a, m, [0, 1]).tolist() == [False, True, True]
