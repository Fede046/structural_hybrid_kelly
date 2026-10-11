"""Seed di backtest: stagione ricostruita per stationary bootstrap delle date (T53, decisione S9).

Un seed è una ricostruzione della stagione. Si estrae una sequenza di n_date indici di data
con lo stationary bootstrap di Politis-Romano sulle date: la posizione 0 apre sempre un
blocco, ogni posizione successiva ne apre uno nuovo con probabilità p = 1/L, ogni blocco
parte da una data uniforme in [0, n_date) (o da start, per la prima posizione) e prosegue
con avvolgimento circolare. Ordine delle estrazioni come bootstrap._stationary_block_layout
con un solo ricampionamento: rng.random(n_date) per gli inizi di blocco, poi
rng.integers(0, n_date, size=n_date) per i punti di partenza.

Ogni data estratta porta con sé tutte le sue partite, con previsioni, quote, esiti,
covariate e δ. Al passo k la data assegnata è la k-esima data originale, così il
calendario resta ordinato. La covariata "position" (posizione della partita nella
stagione) si ricalcola sull'ordine ricostruito, perché descrive il calendario.

Lunghezza media dei blocchi: L_PW stationary (Politis-White con la correzione del 2009,
arrotondata come nella decisione S7) della serie per data della media di δ della stagione
stessa. Con L = 1 ogni posizione apre un blocco: è la versione iid.
"""

from collections.abc import Sequence
from typing import NamedTuple

import numpy as np

from shk.model.training_agents import SeasonInput
from shk.stats.bootstrap import optimal_block_length, round_block_length

POSITION_COVARIATE = "position"


class DateLayout(NamedTuple):
    """Sequenza ricostruita di indici di data e inizi di blocco."""

    date_indices: np.ndarray  # (n_date,) int64, indice della data originale a ogni passo
    new_block: np.ndarray     # (n_date,) bool, True dove inizia un blocco


def season_dates(inp: SeasonInput) -> tuple[np.ndarray, list[np.ndarray]]:
    """Date distinte in ordine e righe delle partite di ciascuna data."""
    unique = np.unique(inp.dates)
    return unique, [np.flatnonzero(inp.dates == d) for d in unique]


def per_date_mean_delta(inp: SeasonInput) -> np.ndarray:
    """Serie per data della media di δ."""
    _, groups = season_dates(inp)
    return np.array([inp.delta[g].mean() for g in groups])


def season_block_length(inp: SeasonInput) -> int:
    """L_PW stationary della serie per data della media di δ, arrotondata (almeno 1)."""
    return round_block_length(optimal_block_length(per_date_mean_delta(inp)).stationary)


def date_layout(n_dates: int, mean_block_length: float, rng: np.random.Generator,
                start: int | None = None) -> DateLayout:
    """Layout dello stationary bootstrap sulle date (vedi modulo).

    Solleva
    -------
    ValueError
        Se mean_block_length non è in [1, n_dates] o start non è in [0, n_dates).
    """
    if not 1.0 <= float(mean_block_length) <= n_dates:
        raise ValueError(f"mean_block_length must be in [1, {n_dates}], got {mean_block_length}")
    if start is not None and not 0 <= start < n_dates:
        raise ValueError(f"start must be in [0, {n_dates}), got {start}")
    new_block = rng.random(n_dates) < 1.0 / float(mean_block_length)
    new_block[0] = True
    starts = rng.integers(0, n_dates, size=n_dates, dtype=np.int64)
    if start is not None:
        starts[0] = start
    positions = np.arange(n_dates, dtype=np.int64)
    origin = np.maximum.accumulate(np.where(new_block, positions, 0))
    return DateLayout((starts[origin] + positions - origin) % n_dates, new_block)


def reconstruct_from_layout(inp: SeasonInput, date_indices: np.ndarray,
                            covariates: Sequence[str] | None = None) -> SeasonInput:
    """Stagione ricostruita: al passo k le partite della data date_indices[k] con la k-esima data."""
    unique, groups = season_dates(inp)
    rows = np.concatenate([groups[j] for j in date_indices])
    new_dates = np.concatenate([np.full(groups[j].shape[0], unique[k]) for k, j in enumerate(date_indices)])
    x = inp.x[rows].copy()
    if covariates is not None and POSITION_COVARIATE in covariates:
        x[:, list(covariates).index(POSITION_COVARIATE)] = np.arange(1, rows.shape[0] + 1, dtype=np.float64)
    return SeasonInput(
        season=inp.season,
        dates=new_dates.astype("datetime64[ns]"),
        probs=inp.probs[rows],
        odds=inp.odds[rows],
        outcomes=inp.outcomes[:, rows],
        x=x,
        delta=inp.delta[rows],
    )


def reconstruct_season(inp: SeasonInput, rng: np.random.Generator, mean_block_length: float | None = None,
                       start: int | None = None, covariates: Sequence[str] | None = None) -> SeasonInput:
    """Un seed: ricostruzione con L = mean_block_length (default L_PW della stagione); L = 1 è iid."""
    n_dates = np.unique(inp.dates).shape[0]
    length = season_block_length(inp) if mean_block_length is None else mean_block_length
    layout = date_layout(n_dates, length, rng, start)
    return reconstruct_from_layout(inp, layout.date_indices, covariates)
