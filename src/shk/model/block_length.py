"""Lunghezza dei blocchi sulle serie di log-loss del Modulo 1 e copertura su AR(1).

Due gruppi di record per results/us_c8_3a_block_length.csv:
- row_type = "series": una riga per serie di log-loss del Modulo 1 raw, cioè la serie di
  training di ciascun fit (training <= fit_through, in ordine di Date) e ciascuna stagione
  di validazione; per ogni serie L_PW stationary e circolare (shk.stats.bootstrap), i loro
  arrotondamenti e la più vicina fra le lunghezze fisse BLOCK_LENGTHS = (7, 20, 40),
  confrontata con L_PW circolare perché quelle lunghezze sono di moving block bootstrap;
- row_type = "coverage": copertura Monte Carlo dell'intervallo percentile al 95% della media
  di AR(1) (phi = 0.5, n = 380, 1000 serie, media vera 0) con stationary bootstrap a L_PW
  stationary arrotondata, serie per serie, e con bootstrap iid (L = 1).

Seed: SeedSequence(SEED_S7).spawn(5)[2] (posizione 2), diviso con
spawn(3): figlio 0 per le serie AR(1), figlio 1 per lo stationary bootstrap, figlio 2 per
il bootstrap iid; ogni generatore si usa in sequenza sulle 1000 serie.
"""

import math
from typing import Final

import numpy as np
import pandas as pd

from shk.model.elo_fit import parse_season_start_year
from shk.stats.bootstrap import (
    optimal_block_length,
    round_block_length,
    stationary_bootstrap_mean_interval,
)
from shk.stats.false_rejection import (
    ALPHA,
    BLOCK_LENGTHS,
    N_BOOT,
    N_STORY_TASKS,
    SEED_S7,
)
from shk.stats.timeseries import generate_ar1_series

T42_STORY_POSITION: Final[int] = 2

ROW_TYPE_SERIES: Final[str] = "series"
ROW_TYPE_COVERAGE: Final[str] = "coverage"
SERIES_KIND_TRAINING: Final[str] = "training_fit"
SERIES_KIND_VALIDATION: Final[str] = "validation_season"
METHOD_STATIONARY_L_PW: Final[str] = "stationary_l_pw"
METHOD_IID: Final[str] = "iid"

COVERAGE_PHI: Final[float] = 0.5
COVERAGE_N_OBS: Final[int] = 380
COVERAGE_N_SERIES: Final[int] = 1000
COVERAGE_TRUE_MEAN: Final[float] = 0.0
Z_99: Final[float] = 2.576

BLOCK_LENGTH_CSV_COLUMNS: Final[tuple[str, ...]] = (
    "row_type",
    "series_kind",
    "fit_through",
    "seasons",
    "n_obs",
    "l_pw_stationary",
    "l_pw_circular",
    "l_pw_stationary_rounded",
    "l_pw_circular_rounded",
    "nearest_fixed_block_length",
    "method",
    "phi",
    "n_series",
    "n_boot",
    "covered",
    "coverage",
    "mean_block_length_used",
    "mc_lower_99",
    "mc_upper_99",
)


def nearest_fixed_block_length(
    length: float, candidates: tuple[int, ...] = BLOCK_LENGTHS
) -> int:
    """La lunghezza fissa più vicina a length; a parità di distanza la più piccola.

    Parametri
    ---------
    length : float
        Lunghezza finita e non negativa.
    candidates : tuple[int, ...], opzionale
        Lunghezze fisse (default: BLOCK_LENGTHS = (7, 20, 40)).

    Restituisce
    -----------
    int
        Elemento di candidates a distanza assoluta minima.

    Solleva
    -------
    ValueError
        Se length non è finita o è negativa, o se candidates è vuota.
    """
    value = float(length)
    if not math.isfinite(value) or value < 0.0:
        raise ValueError(f"length must be finite and non-negative, got {length}")
    if len(candidates) == 0:
        raise ValueError("candidates must not be empty")
    return int(min(sorted(candidates), key=lambda c: abs(value - c)))


def _empty_record() -> dict[str, str | int | float]:
    """Record con tutte le colonne vuote."""
    return {col: "" for col in BLOCK_LENGTH_CSV_COLUMNS}


def _series_record(
    series_kind: str, fit_through: str, seasons: list[str], values: np.ndarray
) -> dict[str, str | int | float]:
    """Record di una serie di log-loss con le sue lunghezze dei blocchi."""
    lengths = optimal_block_length(values)
    record = _empty_record()
    record.update(
        {
            "row_type": ROW_TYPE_SERIES,
            "series_kind": series_kind,
            "fit_through": fit_through,
            "seasons": " ".join(seasons),
            "n_obs": int(values.shape[0]),
            "l_pw_stationary": lengths.stationary,
            "l_pw_circular": lengths.circular,
            "l_pw_stationary_rounded": round_block_length(lengths.stationary),
            "l_pw_circular_rounded": round_block_length(lengths.circular),
            "nearest_fixed_block_length": nearest_fixed_block_length(lengths.circular),
        }
    )
    return record


def compute_series_block_length_records(
    residuals: pd.DataFrame,
    schedule: dict[str, dict[str, list[str]]],
) -> list[dict[str, str | int | float]]:
    """Lunghezze dei blocchi per le serie di log-loss di training e di validazione.

    Per ogni fit, in ordine cronologico: prima la serie di training del fit (righe con
    role = "training" e fit_through = fit, nell'ordine di compute_model_residuals), poi
    una serie per ciascuna stagione di validazione del fit.

    Parametri
    ---------
    residuals : pd.DataFrame
        Uscita di compute_model_residuals.
    schedule : dict[str, dict[str, list[str]]]
        Schema dei fit.

    Restituisce
    -----------
    list[dict[str, str | int | float]]
        Un record per serie, con le colonne di BLOCK_LENGTH_CSV_COLUMNS.

    Solleva
    -------
    ValueError
        Se una serie attesa è vuota.
    """
    records: list[dict[str, str | int | float]] = []
    for fit in sorted(schedule.keys(), key=parse_season_start_year):
        train_mask = (residuals["fit_through"] == fit) & (residuals["role"] == "training")
        train_values = residuals.loc[train_mask, "log_loss"].to_numpy(dtype=np.float64)
        if train_values.size == 0:
            raise ValueError(f"No training residuals for fit {fit}")
        records.append(
            _series_record(
                SERIES_KIND_TRAINING, fit, list(schedule[fit]["training"]), train_values
            )
        )
        for season in schedule[fit]["validation"]:
            val_mask = (
                (residuals["fit_through"] == fit)
                & (residuals["role"] == "validation")
                & (residuals["season"] == season)
            )
            val_values = residuals.loc[val_mask, "log_loss"].to_numpy(dtype=np.float64)
            if val_values.size == 0:
                raise ValueError(f"No validation residuals for season {season}")
            records.append(_series_record(SERIES_KIND_VALIDATION, fit, [season], val_values))
    return records


def spawn_t42_generators(
    seed: int = SEED_S7,
) -> tuple[np.random.Generator, np.random.Generator, np.random.Generator]:
    """Generatori per serie AR(1), stationary bootstrap e bootstrap iid (schema nel modulo).

    Solleva
    -------
    TypeError
        Se seed non è un intero valido.
    """
    if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)):
        raise TypeError(f"seed must be an integer, got {type(seed).__name__}")
    task_seed = np.random.SeedSequence(seed).spawn(N_STORY_TASKS)[T42_STORY_POSITION]
    children = task_seed.spawn(3)
    return (
        np.random.default_rng(children[0]),
        np.random.default_rng(children[1]),
        np.random.default_rng(children[2]),
    )


def compute_mean_coverage_records(
    seed: int = SEED_S7,
) -> list[dict[str, str | int | float]]:
    """Copertura dell'intervallo al 95% della media di AR(1): stationary a L_PW contro iid.

    Per ciascuna delle COVERAGE_N_SERIES serie AR(1) (phi = 0.5, n = 380): L_PW stationary
    della serie, arrotondata con round_block_length; intervallo percentile 1 - ALPHA della
    media con N_BOOT ricampionamenti per stationary bootstrap a quella lunghezza e per
    bootstrap iid (lunghezza 1). Una serie è coperta se l'intervallo, estremi inclusi,
    contiene la media vera 0.

    Parametri
    ---------
    seed : int, opzionale
        Seed radice (default: SEED_S7).

    Restituisce
    -----------
    list[dict[str, str | int | float]]
        Due record, METHOD_STATIONARY_L_PW e METHOD_IID.
    """
    rng_series, rng_sb, rng_iid = spawn_t42_generators(seed)
    series = generate_ar1_series(
        COVERAGE_PHI, COVERAGE_N_OBS, COVERAGE_N_SERIES, rng_series
    )
    level = 1.0 - ALPHA
    half_width = Z_99 * math.sqrt(level * ALPHA / COVERAGE_N_SERIES)

    lengths = np.empty(COVERAGE_N_SERIES, dtype=np.float64)
    covered_sb = 0
    covered_iid = 0
    for s in range(COVERAGE_N_SERIES):
        x = series[s]
        length = round_block_length(optimal_block_length(x).stationary)
        lengths[s] = length
        lo, hi = stationary_bootstrap_mean_interval(x, length, N_BOOT, ALPHA, rng_sb)
        covered_sb += int(lo <= COVERAGE_TRUE_MEAN <= hi)
        lo, hi = stationary_bootstrap_mean_interval(x, 1, N_BOOT, ALPHA, rng_iid)
        covered_iid += int(lo <= COVERAGE_TRUE_MEAN <= hi)

    records: list[dict[str, str | int | float]] = []
    for method, covered, mean_length in (
        (METHOD_STATIONARY_L_PW, covered_sb, float(np.mean(lengths))),
        (METHOD_IID, covered_iid, 1.0),
    ):
        record = _empty_record()
        record.update(
            {
                "row_type": ROW_TYPE_COVERAGE,
                "n_obs": COVERAGE_N_OBS,
                "method": method,
                "phi": COVERAGE_PHI,
                "n_series": COVERAGE_N_SERIES,
                "n_boot": N_BOOT,
                "covered": covered,
                "coverage": covered / COVERAGE_N_SERIES,
                "mean_block_length_used": mean_length,
                "mc_lower_99": level - half_width,
                "mc_upper_99": level + half_width,
            }
        )
        records.append(record)
    return records
