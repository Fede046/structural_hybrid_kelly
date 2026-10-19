"""Test di src/shk/model/module2.py e di three_fold_batch."""

import math

import numpy as np
import pandas as pd
import pytest

import shk.model.module2 as module2
from shk.model.module2 import (
    STATE_ACTIVE,
    STATE_NOT_ACTIVE,
    matchday_decision_dates,
    module2_at_date,
    module2_bootstrap_interval,
    prepare_module2_data,
    season_chain_ids,
    season_decision_dates,
)
from shk.stats.oaxaca import TWOFOLD_REFERENCES, oaxaca_blinder, three_fold_batch

COVS = ("c1", "c2", "flag_promoted")


def _synthetic_frame(seasons=("2005-06", "2006-07"), n_per_season=380, per_date=4, seed=0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    parts = []
    for s in seasons:
        start = pd.Timestamp(f"{int(s[:4])}-08-10")
        dates = start + pd.to_timedelta(np.arange(n_per_season) // per_date * 3, unit="D")
        c1 = rng.normal(size=n_per_season)
        c2 = rng.normal(size=n_per_season)
        flag = (rng.random(n_per_season) < 0.3).astype(int)
        delta = 0.1 * c1 - 0.05 * flag + rng.normal(scale=0.2, size=n_per_season)
        parts.append(pd.DataFrame({"season": s, "Date": dates, "delta": delta, "c1": c1, "c2": c2,
                                   "flag_promoted": flag, "role": "validation"}))
    return pd.concat(parts, ignore_index=True)


def _same_output(o1, o2) -> bool:
    if (o1.state, o1.n_eligible, o1.n_a, o1.n_b) != (o2.state, o2.n_eligible, o2.n_a, o2.n_b):
        return False
    if o1.result is None or o2.result is None:
        return o1.result is None and o2.result is None
    r1, r2 = o1.result, o2.result
    scalars = ["total", "compositional", "structural", "interaction", "structural_share"]
    if any(getattr(r1, a) != getattr(r2, a) for a in scalars):
        return False
    if any(r1.twofold[r].explained != r2.twofold[r].explained for r in TWOFOLD_REFERENCES):
        return False
    return all(np.array_equal(getattr(r1.detailed, c), getattr(r2.detailed, c))
               for c in ("compositional", "structural", "interaction"))


def test_not_active_until_two_windows():
    """Lo stato "non attivo" vale finché le partite anteriori sono meno di 2W."""
    frame = _synthetic_frame(seasons=("2005-06",))
    data = prepare_module2_data(frame, COVS)
    w = 40
    for d in season_decision_dates(data, "2005-06"):
        out = module2_at_date(data, "2005-06", d, w)
        n_before = int((frame["Date"] < d).sum())
        assert out.n_eligible == n_before
        if n_before < 2 * w:
            assert out.state == STATE_NOT_ACTIVE and out.result is None
        else:
            assert out.state == STATE_ACTIVE
    # Esattamente 2W partite anteriori: attivo; una in meno: non attivo
    d_exact = frame["Date"].iloc[2 * w]
    assert int((frame["Date"] < d_exact).sum()) == 2 * w
    assert module2_at_date(data, "2005-06", d_exact, w).state == STATE_ACTIVE
    small = prepare_module2_data(frame.iloc[: 2 * w - 1], COVS)
    assert module2_at_date(small, "2005-06", pd.Timestamp("2010-01-01"), w).state == STATE_NOT_ACTIVE


def test_components_sum_to_total_every_date():
    """Per ogni data e W le componenti sommano al totale entro 1e-12."""
    data = prepare_module2_data(_synthetic_frame(), COVS)
    for w in (20, 40, 80):
        for season in ("2005-06", "2006-07"):
            for d in season_decision_dates(data, season):
                out = module2_at_date(data, season, d, w)
                if out.result is None:
                    continue
                r = out.result
                assert abs(r.compositional + r.structural + r.interaction - r.total) <= 1e-12
                for tf in r.twofold.values():
                    assert abs(tf.explained + tf.unexplained - r.total) <= 1e-12
                assert math.isclose(r.total, out.mean_b - out.mean_a, abs_tol=1e-12)


def _mutate_from(frame: pd.DataFrame, d: pd.Timestamp) -> pd.DataFrame:
    """Cambia esito (δ), quote e previsioni (covariate) delle partite con Date >= d."""
    mut = frame.copy()
    later = mut["Date"] >= d
    mut.loc[later, "delta"] = -mut.loc[later, "delta"] + 1.0
    mut.loc[later, "c1"] = mut.loc[later, "c1"] * 3.0 + 2.0
    mut.loc[later, "c2"] = -mut.loc[later, "c2"]
    mut.loc[later, "flag_promoted"] = 1 - mut.loc[later, "flag_promoted"]
    return mut


def test_mutant_leakage_strict_anteriority(monkeypatch):
    """Cambiare le partite con Date >= D non cambia l'uscita; con anteriorità non stretta sì."""
    frame = _synthetic_frame()
    data = prepare_module2_data(frame, COVS)
    decision_dates = season_decision_dates(data, "2006-07")[40:60]
    for d in decision_dates:
        mutated = prepare_module2_data(_mutate_from(frame, d), COVS)
        for w in (20, 40):
            assert _same_output(module2_at_date(data, "2006-07", d, w), module2_at_date(mutated, "2006-07", d, w))

    # Mutante del codice: con Date <= D lo stesso controllo deve accorgersene
    monkeypatch.setattr(module2, "eligible_mask", lambda dates, decision: dates <= decision)
    detected = 0
    for d in decision_dates:
        mutated = prepare_module2_data(_mutate_from(frame, d), COVS)
        if not _same_output(module2_at_date(data, "2006-07", d, 20), module2_at_date(mutated, "2006-07", d, 20)):
            detected += 1
    assert detected == len(decision_dates)


def test_chain_breaks_at_missing_season():
    """La finestra attraversa le stagioni consecutive e si ferma dove ne manca una."""
    assert season_chain_ids(["2000-01", "2002-03", "2003-04"]) == {"2000-01": 0, "2002-03": 1, "2003-04": 1}
    frame = _synthetic_frame(seasons=("2000-01", "2002-03"))
    data = prepare_module2_data(frame, COVS)
    first = season_decision_dates(data, "2002-03")[0]
    assert module2_at_date(data, "2002-03", first, 20).n_eligible == 0
    frame2 = _synthetic_frame(seasons=("2001-02", "2002-03"))
    data2 = prepare_module2_data(frame2, COVS)
    first2 = season_decision_dates(data2, "2002-03")[0]
    assert module2_at_date(data2, "2002-03", first2, 20).n_eligible == 380


def test_matchday_decision_dates():
    """38 date per stagione; la data segue la partita 10m e l'ultima è dopo la fine."""
    frame = _synthetic_frame(seasons=("2005-06",))
    data = prepare_module2_data(frame, COVS)
    dates = matchday_decision_dates(data, "2005-06")
    assert len(dates) == 38
    for m, d in enumerate(dates, start=1):
        assert d > frame["Date"].iloc[10 * m - 1]
    assert dates[-1] == frame["Date"].iloc[-1] + pd.Timedelta(days=1)


def test_bootstrap_interval_reproducible():
    """Intervallo riproducibile col seed e con ricampionamenti validi."""
    data = prepare_module2_data(_synthetic_frame(), COVS)
    d = season_decision_dates(data, "2006-07")[50]
    i1 = module2_bootstrap_interval(data, "2006-07", d, 40, np.random.default_rng(3), n_boot=199)
    i2 = module2_bootstrap_interval(data, "2006-07", d, 40, np.random.default_rng(3), n_boot=199)
    assert i1 == i2
    assert i1.n_valid == 199
    for comp in ("total", "compositional", "structural", "interaction"):
        assert i1.lower[comp] <= i1.upper[comp]


def test_three_fold_batch_matches_single():
    """three_fold_batch coincide con oaxaca_blinder elemento per elemento."""
    rng = np.random.default_rng(4)
    xa = rng.normal(size=(6, 50, 3))
    xb = rng.normal(size=(6, 50, 3))
    ya = rng.normal(size=(6, 50))
    yb = rng.normal(size=(6, 50))
    xa[2, :, 1] = 0.0  # rango non pieno
    batch = three_fold_batch(xa, ya, xb, yb)
    assert not batch.valid[2] and math.isnan(batch.total[2])
    for b in (0, 1, 3, 4, 5):
        res = oaxaca_blinder(xa[b], ya[b], xb[b], yb[b])
        assert batch.valid[b]
        for comp in ("total", "compositional", "structural", "interaction"):
            assert math.isclose(getattr(batch, comp)[b], getattr(res, comp), rel_tol=1e-10, abs_tol=1e-12)
