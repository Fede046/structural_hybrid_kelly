"""Test: età del modello e tempo di calendario (shk.model.model_age), su dati costruiti."""

import numpy as np
import pandas as pd
import pytest

from shk.model.model_age import (
    age_tests,
    dispersion,
    first_season_after,
    paired_season_records,
    rank_correlation,
    stratified_trend,
)


def test_dispersion_is_the_mean_absolute_deviation_from_the_median():
    assert dispersion(np.array([0.0, 1.0, 5.0])) == pytest.approx((1.0 + 0.0 + 4.0) / 3)
    batch = dispersion(np.array([[0.0, 1.0, 5.0], [2.0, 2.0, 2.0]]))
    assert np.allclose(batch, [5 / 3, 0.0])


def test_rank_correlation():
    assert rank_correlation(np.array([1, 2, 3, 4]), np.array([10, 20, 25, 90])) == pytest.approx(1.0)
    assert rank_correlation(np.array([1, 2, 3, 4]), np.array([4, 3, 2, 1])) == pytest.approx(-1.0)
    assert rank_correlation(np.array([1, 2, 3]), np.array([5, 5, 5])) == 0.0


def test_stratified_trend_looks_inside_the_groups():
    """Una tendenza che esiste solo fra i gruppi non conta; una dentro i gruppi sì."""
    rng = np.random.default_rng(0)
    groups = np.repeat(["a", "b", "c"], 8)
    x = np.tile(np.arange(8.0), 3)
    between = np.repeat([0.0, 10.0, 20.0], 8) + rng.normal(size=24)   # livelli diversi, nessuna tendenza dentro
    stat, p = stratified_trend(x, between, groups, np.random.default_rng(1), n_perm=2000)
    assert abs(stat) < 0.5 and p > 0.05
    within = between + 2.0 * x
    stat, p = stratified_trend(x, within, groups, np.random.default_rng(1), n_perm=2000)
    assert stat > 0.8 and p < 0.01
    with pytest.raises(ValueError):
        stratified_trend(x[:2], within[:2], groups[:2], rng)


def test_first_season_after_takes_the_earliest_season_of_each_fit():
    fits = {"2003-04": "2000-01", "2002-03": "2000-01", "2012-13": "2010-11", "2011-12": "2010-11"}
    assert first_season_after(fits) == {"2002-03": "2000-01", "2011-12": "2010-11"}


def _frame(rng: np.random.Generator, seasons: dict[str, str], scale: dict[str, float]) -> pd.DataFrame:
    rows = []
    for season, fit in seasons.items():
        n = 120
        dates = pd.date_range(f"{season[:4]}-08-15", periods=n, freq="2D")
        q = rng.dirichlet([5.0, 3.0, 3.0], size=n)
        p = q * np.exp(rng.normal(scale=scale[season], size=(n, 3)))
        p /= p.sum(axis=1, keepdims=True)
        outcome = np.array([rng.choice(3, p=row) for row in q])
        rows.append(pd.DataFrame({
            "season": season, "Date": dates, "HomeTeam": [f"H{i}" for i in range(n)],
            "AwayTeam": [f"A{i}" for i in range(n)], "role": "validation", "fit_through": fit,
            "p_home": p[:, 0], "p_draw": p[:, 1], "p_away": p[:, 2],
            "q_home": q[:, 0], "q_draw": q[:, 1], "q_away": q[:, 2],
            "delta": np.log(p[np.arange(n), outcome]) - np.log(q[np.arange(n), outcome])}))
    return pd.concat(rows, ignore_index=True)


def test_paired_records_measure_the_model_farther_from_the_market():
    """Stesse partite e stesse quote: il modello più lontano dal mercato ha più dispersione ed errore atteso."""
    seasons = {"2011-12": "2010-11", "2012-13": "2010-11", "2013-14": "2010-11", "2014-15": "2010-11"}
    refit_fits = {"2011-12": "2010-11", "2012-13": "2011-12", "2013-14": "2012-13", "2014-15": "2013-14"}
    noise = {s: 0.05 + 0.05 * i for i, s in enumerate(seasons)}          # il congelato si allontana con l'età
    frozen = _frame(np.random.default_rng(1), seasons, noise)
    refit = _frame(np.random.default_rng(1), refit_fits, {s: 0.05 for s in seasons})   # stesse q ed esiti
    refit[["season", "Date", "HomeTeam", "AwayTeam"]] = frozen[["season", "Date", "HomeTeam", "AwayTeam"]]
    rows = paired_season_records(frozen, refit, n_boot=199)
    assert [r["age"] for r in rows] == [1, 2, 3, 4] and [r["refit_age"] for r in rows] == [1, 1, 1, 1]
    last = rows[-1]
    assert last["dispersion_low"] > 0 and last["expected_high"] < 0      # più disperso, errore atteso più negativo
    for r in rows:
        assert r["dispersion_low"] <= r["dispersion_difference"] <= r["dispersion_high"]
    tests = {(t["test"], t["measure"]): t for t in age_tests(rows, n_perm=500)}
    assert tests[("paired_difference", "expected")]["n_seasons"] == 3    # il 2011-12 ha lo stesso modello
    assert tests[("difference_vs_age", "dispersion")]["statistic"] > 0.9
    with pytest.raises(ValueError):
        paired_season_records(frozen, refit.iloc[:-1])
