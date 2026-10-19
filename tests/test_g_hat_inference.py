"""Test di unità: permutazione, autocorrelazioni, valore atteso del placebo, intervalli."""

import math

import numpy as np
import pandas as pd

from shk.model.g_hat_inference import (
    autocorrelations,
    percentile_interval,
    permute_outcomes,
    pooled_bootstrap_means,
    season_bootstrap_means,
)


def test_permute_outcomes_within_season_only():
    rng = np.random.default_rng(0)
    df = pd.DataFrame({
        "season": ["2004-05"] * 6 + ["2005-06"] * 4,
        "FTR": list("HHDAAH") + list("DDAH"),
        "FTHG": [2, 1, 0, 0, 1, 3, 1, 0, 0, 2],
        "FTAG": [0, 0, 0, 1, 2, 1, 1, 0, 1, 0],
        "HomeTeam": list("abcdefghij"),
    })
    out = permute_outcomes(df, rng)
    for s in ("2004-05", "2005-06"):
        before = sorted(map(tuple, df.loc[df["season"] == s, ["FTR", "FTHG", "FTAG"]].to_numpy().tolist()))
        after = sorted(map(tuple, out.loc[out["season"] == s, ["FTR", "FTHG", "FTAG"]].to_numpy().tolist()))
        assert before == after
    assert (out["HomeTeam"] == df["HomeTeam"]).all()


def test_autocorrelations_of_ar1():
    rng = np.random.default_rng(1)
    x = np.zeros(20000)
    for t in range(1, x.size):
        x[t] = 0.5 * x[t - 1] + rng.normal()
    acf = autocorrelations(x, 3)
    assert np.allclose(acf, [0.5, 0.25, 0.125], atol=0.03)


def test_expected_placebo_value_formula():
    """Con previsioni fisse, la media di ĝ su permutazioni uniformi è Σ_k π_k (ln p − ln q) mediato sulle partite."""
    rng = np.random.default_rng(2)
    n = 12
    p = rng.dirichlet([3, 2, 2], size=n)
    q = rng.dirichlet([3, 2, 2], size=n)
    y = np.array([0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 2])
    pi = np.bincount(y, minlength=3) / n
    expected = float(((pi * (np.log(p) - np.log(q))).sum(axis=1)).mean())
    sims = [float(np.mean(np.log(p[np.arange(n), yy]) - np.log(q[np.arange(n), yy])))
            for yy in (rng.permutation(y) for _ in range(20000))]
    assert math.isclose(float(np.mean(sims)), expected, abs_tol=4 * np.std(sims) / math.sqrt(len(sims)))


def test_bootstrap_helpers():
    rng = np.random.default_rng(3)
    x = rng.normal(0.1, 1.0, 380)
    means = season_bootstrap_means(x, 3.0, rng, 999)
    assert means.shape == (999,)
    lo, hi = percentile_interval(means)
    assert lo < x.mean() < hi
    pooled = pooled_bootstrap_means([x[:200], x[200:]], [3.0, 1.0], rng, 50)
    assert pooled.shape == (50,)
