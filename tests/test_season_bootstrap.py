"""Test: generatore dei seed (stationary bootstrap delle date)."""

import numpy as np
import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.model.covariate_inspection import derive_specification
from shk.model.module2_data import build_module2_frame
from shk.model.residuals import load_model_residuals
from shk.model.season_bootstrap import (
    date_layout,
    per_date_mean_delta,
    reconstruct_from_layout,
    reconstruct_season,
    season_block_length,
    season_dates,
)
from shk.model.training_agents import SeasonInput, season_input_from_frame, training_seasons
from shk.stats.bootstrap import stationary_bootstrap_indices

COVS = ("c1", "position", "flag_x")


def _synthetic_season(n_dates: int = 100, seed: int = 0) -> SeasonInput:
    """Stagione con 1–10 partite per data e δ autocorrelato fra date."""
    rng = np.random.default_rng(seed)
    counts = rng.integers(1, 11, size=n_dates)
    n = int(counts.sum())
    day = np.repeat(np.arange(n_dates), counts)
    dates = (np.datetime64("2010-08-14") + day * np.timedelta64(3, "D")).astype("datetime64[ns]")
    level = np.zeros(n_dates)
    for t in range(1, n_dates):
        level[t] = 0.6 * level[t - 1] + rng.normal(0.0, 0.05)
    delta = level[day] + rng.normal(0.0, 0.3, n)
    raw = rng.dirichlet([4, 3, 3], size=n)
    x = np.column_stack([rng.normal(size=n), np.arange(1, n + 1, dtype=float), (rng.random(n) < 0.3).astype(float)])
    return SeasonInput("s", dates, raw, 1.0 / (raw * 1.05), rng.integers(0, 3, size=(1, n)), x, delta)


def _per_date_counts(n_dates: int, length: float, reps: int, rng: np.random.Generator) -> np.ndarray:
    return np.stack([np.bincount(date_layout(n_dates, length, rng).date_indices, minlength=n_dates) for _ in range(reps)])


def test_date_layout_matches_stationary_bootstrap_indices():
    """Stesse estrazioni dello stationary bootstrap della scelta della lunghezza dei blocchi con un solo ricampionamento."""
    for n, length in ((50, 1.0), (97, 3.0), (135, 7.5)):
        a = date_layout(n, length, np.random.default_rng(11)).date_indices
        b = stationary_bootstrap_indices(n, length, 1, np.random.default_rng(11))[0]
        np.testing.assert_array_equal(a, b)
    # L = 1: ogni posizione apre un blocco (versione iid)
    assert date_layout(40, 1.0, np.random.default_rng(3)).new_block.all()


def test_reconstruction_reproduces_season_without_new_blocks():
    """L = n_date e inizio 0 (decisione del programmatore): le ricostruzioni senza blocchi nuovi
    riproducono la stagione, e la loro quota è (1 − 1/n)^(n − 1) entro l'errore Monte Carlo."""
    inp = _synthetic_season()
    n = np.unique(inp.dates).shape[0]
    rng = np.random.default_rng(7)
    reps, n_single, n_broken_equal = 4000, 0, 0
    for _ in range(reps):
        layout = date_layout(n, float(n), rng, start=0)
        if layout.new_block[1:].any():
            continue
        n_single += 1
        rec = reconstruct_from_layout(inp, layout.date_indices, COVS)
        np.testing.assert_array_equal(rec.dates, inp.dates)
        for field in ("probs", "odds", "outcomes", "x", "delta"):
            np.testing.assert_array_equal(getattr(rec, field), getattr(inp, field))
    p = (1.0 - 1.0 / n) ** (n - 1)
    se = np.sqrt(p * (1.0 - p) / reps)
    assert abs(n_single / reps - p) <= 4.0 * se
    # Con almeno un blocco nuovo la stagione cambia
    layout = date_layout(n, 2.0, np.random.default_rng(1), start=0)
    rec = reconstruct_from_layout(inp, layout.date_indices, COVS)
    assert rec.delta.shape != inp.delta.shape or not np.array_equal(rec.delta, inp.delta)


def test_reconstruction_keeps_calendar_and_date_blocks():
    """La k-esima data ricostruita è la k-esima originale, con tutte le partite della data estratta."""
    inp = _synthetic_season()
    unique, groups = season_dates(inp)
    layout = date_layout(unique.shape[0], 3.0, np.random.default_rng(5))
    rec = reconstruct_from_layout(inp, layout.date_indices, COVS)
    rec_unique, rec_groups = season_dates(rec)
    np.testing.assert_array_equal(rec_unique, unique)
    for k, j in enumerate(layout.date_indices):
        np.testing.assert_array_equal(rec.delta[rec_groups[k]], inp.delta[groups[j]])
        np.testing.assert_array_equal(rec.probs[rec_groups[k]], inp.probs[groups[j]])
    np.testing.assert_array_equal(rec.x[:, 1], np.arange(1, rec.delta.shape[0] + 1))
    assert np.all(rec.dates[1:] >= rec.dates[:-1])


def test_date_frequencies_uniform_over_10000_reconstructions():
    """Su 10 000 ricostruzioni ogni data compare in media una volta per ricostruzione, entro l'errore MC."""
    for length in (1.0, 3.0, 8.0):
        counts = _per_date_counts(100, length, 10_000, np.random.default_rng(int(length * 10)))
        mean = counts.mean(axis=0)
        se = counts.std(axis=0, ddof=1) / np.sqrt(counts.shape[0])
        assert np.all(np.abs(mean - 1.0) <= 4.5 * se)


def _mean_delta_bias(inp: SeasonInput, length: float, reps: int, rng: np.random.Generator):
    unique, groups = season_dates(inp)
    sums = np.array([inp.delta[g].sum() for g in groups])
    counts = np.array([g.shape[0] for g in groups])
    pdm = per_date_mean_delta(inp)
    per_match, per_date = np.empty(reps), np.empty(reps)
    for r in range(reps):
        idx = date_layout(unique.shape[0], length, rng).date_indices
        per_match[r] = sums[idx].sum() / counts[idx].sum()
        per_date[r] = pdm[idx].mean()
    z_match = (per_match.mean() - inp.delta.mean()) / (per_match.std(ddof=1) / np.sqrt(reps))
    z_date = (per_date.mean() - pdm.mean()) / (per_date.std(ddof=1) / np.sqrt(reps))
    return z_match, z_date


def test_mean_delta_unbiased_synthetic():
    """Media di δ per partita e media della serie per data non distorte, entro 4 errori standard MC."""
    inp = _synthetic_season()
    for length in (1.0, 4.0):
        z_match, z_date = _mean_delta_bias(inp, length, 10_000, np.random.default_rng(int(length)))
        assert abs(z_match) <= 4.0 and abs(z_date) <= 4.0


def test_mean_delta_unbiased_training_seasons():
    if not (DEFAULT_DATA_DIR.is_dir() and any(DEFAULT_DATA_DIR.glob("*.csv"))):
        pytest.skip(f"Real data missing: no CSV in {DEFAULT_DATA_DIR}")
    frame = build_module2_frame(load_model_residuals())
    train = frame[frame["role"] == "training"]
    covs = derive_specification(train).covariates
    rng = np.random.default_rng(5)
    for s in training_seasons(train):
        inp = season_input_from_frame(train, s, covs)
        rec = reconstruct_season(inp, np.random.default_rng(1), covariates=covs)
        assert rec.x.shape[1] == len(covs)
        z_match, z_date = _mean_delta_bias(inp, season_block_length(inp), 10_000, rng)
        assert abs(z_match) <= 4.0 and abs(z_date) <= 4.0
