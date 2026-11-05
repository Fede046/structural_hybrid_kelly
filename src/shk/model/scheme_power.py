"""Verifica dell'allarme ANOVA dello schema del relatore: frequenza sui dati reali e potenza.

Tre domande, sulle 19 stagioni di validazione (realizzazione osservata), con W congelata e le
soglie dell'allarme "o" di scheme_run.scheme_thresholds (decisione del 2026-11-05):
- frequenza (righe "rate"): quota di date di decisione con allarme sulla media, sulla dispersione
  e in tutto, fra le date con almeno 2W partite anteriori; sotto H₀ è α/2, α/2 e circa α;
- potenza (righe "power"): da BREAK_INDEX in poi la serie di δ della stagione si trasforma in
  m + s·(δ − m) + Δ, con m la media della parte trasformata, Δ lo spostamento della media e s² il
  fattore della varianza (SCENARIOS); è una stagione con allarme se l'allarme scatta in almeno una
  delle prime HORIZON_DATES date di decisione dopo la partita BREAK_INDEX. Nessun ricampionamento:
  il risultato è deterministico;
- peggioramento minimo della media rilevabile (righe "mde"): √(soglia della media) · sd(δ del fit)
  · √(2/W), il peggioramento al quale la F della media raggiunge la soglia;
- la stessa frequenza con la log-loss del modello al posto di δ (righe "rate_log_loss"), con soglie
  calibrate allo stesso modo sulla log-loss del fit: seed SeedSequence(SEED_S13).spawn(numero di fit).
"""

import math
from collections.abc import Mapping, Sequence
from typing import Final, NamedTuple

import numpy as np
import pandas as pd

from shk.model.agent_c import calibrate_scheme_thresholds, scheme_statistics
from shk.model.elo_fit import parse_season_start_year
from shk.model.frozen_agents import scheme_window
from shk.model.frozen_params import FrozenParams
from shk.model.scheme_run import fit_block_length
from shk.model.season_input import season_input_from_frame

SEED_S13: Final[int] = 20261105
BREAK_INDEX: Final[int] = 190
HORIZON_DATES: Final[int] = 10
_FTR_OUTCOME_MAP: Final[dict[str, int]] = {"H": 0, "D": 1, "A": 2}


class Scenario(NamedTuple):
    """Cambiamento inserito nella serie di δ dalla partita BREAK_INDEX in poi."""

    name: str
    mean_shift: float
    variance_factor: float


SCENARIOS: Final[tuple[Scenario, ...]] = (
    Scenario("none", 0.0, 1.0),
    Scenario("mean_-0.05", -0.05, 1.0),
    Scenario("mean_-0.10", -0.10, 1.0),
    Scenario("mean_-0.20", -0.20, 1.0),
    Scenario("variance_x1.5", 0.0, 1.5),
    Scenario("variance_x2", 0.0, 2.0),
    Scenario("mean_-0.10_variance_x2", -0.10, 2.0),
)
POWER_COLUMNS: Final[tuple[str, ...]] = (
    "row_type", "series", "season", "fit_through", "scenario", "mean_shift", "variance_factor", "window",
    "n_dates", "share_mean_alarm", "share_dispersion_alarm", "share_alarm", "n_seasons", "share_seasons_with_alarm",
    "sd", "mean_threshold", "dispersion_threshold", "min_detectable_worsening",
)


def alarm_flags(y: np.ndarray, dates: np.ndarray, window: int, mean_threshold: float,
                dispersion_threshold: float) -> np.ndarray:
    """(n_date, 2) bool: allarme sulla media e sulla dispersione alle date con almeno 2W partite anteriori."""
    values = np.asarray(y, dtype=np.float64)
    days = np.asarray(dates).astype("datetime64[ns]")
    out = []
    for d in np.unique(days):
        idx = np.flatnonzero(days < d)
        if idx.shape[0] < 2 * window:
            continue
        f_mean, f_disp = scheme_statistics(values[idx[-2 * window:-window]], values[idx[-window:]])
        out.append((f_mean > mean_threshold, f_disp > dispersion_threshold))
    return np.array(out, dtype=bool).reshape(-1, 2)


def inject_change(y: np.ndarray, start: int, mean_shift: float, variance_factor: float) -> np.ndarray:
    """Copia di y con y[start:] → m + √variance_factor·(y − m) + mean_shift, m la media di y[start:]."""
    out = np.asarray(y, dtype=np.float64).copy()
    tail = out[start:]
    m = tail.mean()
    out[start:] = m + math.sqrt(variance_factor) * (tail - m) + mean_shift
    return out


def alarm_after_break(y: np.ndarray, dates: np.ndarray, window: int, mean_threshold: float,
                      dispersion_threshold: float, start: int = BREAK_INDEX, horizon: int = HORIZON_DATES) -> bool:
    """True se l'allarme "o" scatta in una delle prime `horizon` date di decisione dopo la partita `start`."""
    values = np.asarray(y, dtype=np.float64)
    days = np.asarray(dates).astype("datetime64[ns]")
    later = np.unique(days)
    later = later[later > days[start]][:horizon]
    for d in later:
        idx = np.flatnonzero(days < d)
        f_mean, f_disp = scheme_statistics(values[idx[-2 * window:-window]], values[idx[-window:]])
        if f_mean > mean_threshold or f_disp > dispersion_threshold:
            return True
    return False


def _row(**fields: object) -> dict[str, object]:
    rec = {c: "" for c in POWER_COLUMNS}
    rec.update(fields)
    return rec


def _seasons(val: pd.DataFrame) -> list[tuple[str, str, pd.DataFrame]]:
    out = []
    for season in sorted(set(val["season"]), key=parse_season_start_year):
        rows = val[val["season"] == season].sort_values("Date", kind="stable")
        out.append((season, str(rows["fit_through"].iloc[0]), rows))
    return out


def with_log_loss(frame: pd.DataFrame) -> pd.DataFrame:
    """Il DataFrame con la colonna log_loss = −ln p̂(esito realizzato)."""
    probs = frame[["p_home", "p_draw", "p_away"]].to_numpy(dtype=np.float64)
    outcome = frame["FTR"].map(_FTR_OUTCOME_MAP).to_numpy(dtype=np.int64)
    return frame.assign(log_loss=-np.log(probs[np.arange(len(frame)), outcome]))


def log_loss_thresholds(train: pd.DataFrame, params: FrozenParams,
                        seed: int | np.random.SeedSequence = SEED_S13) -> dict[str, tuple[float, float]]:
    """Soglie "o" calibrate sulla log-loss del fit come quelle di δ (vedi modulo)."""
    covariates = list(params.fixed["covariates"])
    train = with_log_loss(train)
    fits = sorted(set(train["season"]), key=parse_season_start_year)
    gens = np.random.SeedSequence(seed).spawn(len(fits))
    out = {}
    for fit, g in zip(fits, gens):
        rows = train[train["season"] == fit].sort_values("Date", kind="stable")
        length = fit_block_length(season_input_from_frame(train, fit, covariates))
        out[fit] = calibrate_scheme_thresholds(rows["log_loss"].to_numpy(), scheme_window(params), length,
                                               np.random.default_rng(g))
    return out


def power_records(frame: pd.DataFrame, params: FrozenParams, thresholds: Mapping[str, Sequence[float]],
                  scenarios: Sequence[Scenario] = SCENARIOS) -> list[dict[str, object]]:
    """Righe "rate", "power", "mde" e "rate_log_loss" (vedi modulo)."""
    w = scheme_window(params)
    train = frame[frame["role"] == "training"]
    val = frame[frame["role"] == "validation"]
    records = []
    for fit, thr in thresholds.items():
        sd = float(train.loc[train["season"] == fit, "delta"].std(ddof=1))
        records.append(_row(row_type="mde", series="delta", fit_through=fit, window=w, sd=sd,
                            mean_threshold=float(thr[0]), dispersion_threshold=float(thr[1]),
                            min_detectable_worsening=math.sqrt(float(thr[0])) * sd * math.sqrt(2.0 / w)))
    seasons = _seasons(val)
    for season, fit, rows in seasons:
        flags = alarm_flags(rows["delta"].to_numpy(), rows["Date"].to_numpy(), w, *thresholds[fit][:2])
        records.append(_row(row_type="rate", series="delta", season=season, fit_through=fit, window=w,
                            n_dates=int(flags.shape[0]), share_mean_alarm=float(flags[:, 0].mean()),
                            share_dispersion_alarm=float(flags[:, 1].mean()),
                            share_alarm=float((flags[:, 0] | flags[:, 1]).mean())))
    for sc in scenarios:
        hits = [alarm_after_break(inject_change(rows["delta"].to_numpy(), BREAK_INDEX, sc.mean_shift, sc.variance_factor),
                                  rows["Date"].to_numpy(), w, *thresholds[fit][:2]) for _, fit, rows in seasons]
        records.append(_row(row_type="power", series="delta", scenario=sc.name, mean_shift=sc.mean_shift,
                            variance_factor=sc.variance_factor, window=w, n_seasons=len(hits),
                            share_seasons_with_alarm=float(np.mean(hits))))
    ll_thr = log_loss_thresholds(train, params)
    val_ll = with_log_loss(val)
    for season, fit, rows in _seasons(val_ll):
        flags = alarm_flags(rows["log_loss"].to_numpy(), rows["Date"].to_numpy(), w, *ll_thr[fit])
        records.append(_row(row_type="rate_log_loss", series="log_loss", season=season, fit_through=fit, window=w,
                            n_dates=int(flags.shape[0]), share_mean_alarm=float(flags[:, 0].mean()),
                            share_dispersion_alarm=float(flags[:, 1].mean()),
                            share_alarm=float((flags[:, 0] | flags[:, 1]).mean()),
                            mean_threshold=float(ll_thr[fit][0]), dispersion_threshold=float(ll_thr[fit][1])))
    return records
