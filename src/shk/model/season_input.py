"""Ingressi di una stagione per l'ambiente e per il supervisore.

Dal DataFrame del Modulo 2 (build_module2_frame), righe della stagione ordinate per Date in modo
stabile come module2.prepare_module2_data: probabilità p_home, p_draw, p_away, quote odds_* della
terna scelta per il Modulo 2 (B365, oppure SB nel 2000-01, decisione di progetto) ed esiti FTR.
Le covariate della specificazione vanno al supervisore; gli esiti solo all'ambiente.
"""

from collections.abc import Sequence
from typing import Final, NamedTuple

import numpy as np
import pandas as pd

from shk.model.elo_fit import parse_season_start_year

_FTR_OUTCOME_MAP: Final[dict[str, int]] = {"H": 0, "D": 1, "A": 2}


class SeasonInput(NamedTuple):
    """Ingressi di una stagione per l'ambiente e per il supervisore."""

    season: str
    dates: np.ndarray     # (N,) datetime64[ns]
    probs: np.ndarray     # (N, 3)
    odds: np.ndarray      # (N, 3)
    outcomes: np.ndarray  # (1, N)
    x: np.ndarray         # (N, k) covariate pre-partita
    delta: np.ndarray     # (N,) δ del DataFrame, per le soglie dello schema e per i test


def season_input_from_frame(frame: pd.DataFrame, season: str, covariates: Sequence[str]) -> SeasonInput:
    """Righe della stagione ordinate per Date in modo stabile (come prepare_module2_data).

    Solleva
    -------
    ValueError
        Se la stagione non ha righe.
    """
    rows = frame[frame["season"] == season].sort_values("Date", kind="stable")
    if rows.empty:
        raise ValueError(f"Season {season} not in frame")
    outcomes = np.array([_FTR_OUTCOME_MAP[str(v).strip()] for v in rows["FTR"]], dtype=np.int64)[None, :]
    return SeasonInput(
        season=season,
        dates=rows["Date"].to_numpy(dtype="datetime64[ns]"),
        probs=rows[["p_home", "p_draw", "p_away"]].to_numpy(dtype=np.float64),
        odds=rows[["odds_home", "odds_draw", "odds_away"]].to_numpy(dtype=np.float64),
        outcomes=outcomes,
        x=rows[list(covariates)].to_numpy(dtype=np.float64),
        delta=rows["delta"].to_numpy(dtype=np.float64),
    )


def training_seasons(frame: pd.DataFrame) -> list[str]:
    """Stagioni del DataFrame in ordine cronologico."""
    return sorted(set(frame["season"]), key=parse_season_start_year)
