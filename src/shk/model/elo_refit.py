"""Ri-parametrizzazione annuale dell'Elo: prima di ogni stagione di validazione si ricalibra il Modulo 1.

Seconda opzione del relatore per l'errore strutturale («finché il modello non viene
ri-parametrizzato»; decisione del 2026-11-05). Nel progetto il Modulo 1 si calibra solo ai fit
2000-01, 2010-11, 2020-21 (ELO_FITS) e invecchia: la distanza dal mercato cresce con gli anni dal
fit. Qui, prima di ogni stagione di validazione s, K, h e ν si ricalibrano con
elo_fit.calibrate_single_fit sulla stagione precedente con quote B365 complete (solo dati
anteriori a s; per il 2002-03 è il 2000-01, perché il 2001-02 non ha B365), e la stagione s si
prevede con quei parametri. Lo schema dei fit (refit_schedule) ha una chiave per stagione di
calibrazione, con quella sola stagione come training e la stagione successiva come validazione.
"""

from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor
from typing import Final

import numpy as np
import pandas as pd

from shk.data.split import read_split_config
from shk.model.agent_c import expected_delta
from shk.model.elo_fit import EloFitParams, calibrate_single_fit, parse_season_start_year
from shk.model.residuals import ModelResidualsData, load_match_frame, model_residuals_data

# Stagioni senza la terna B365 completa: non possono fare da stagione di calibrazione dello schema
NO_B365_SEASONS: Final[frozenset[str]] = frozenset({"2001-02"})


def refit_schedule(validation: Sequence[str], available: Sequence[str]) -> dict[str, dict[str, list[str]]]:
    """Per ogni stagione di validazione, la stagione di calibrazione: la più recente anteriore con B365."""
    ordered = sorted(available, key=parse_season_start_year)
    schedule: dict[str, dict[str, list[str]]] = {}
    for season in sorted(validation, key=parse_season_start_year):
        year = parse_season_start_year(season)
        prior = [s for s in ordered if parse_season_start_year(s) < year and s not in NO_B365_SEASONS]
        if not prior:
            raise ValueError(f"no calibration season before {season}")
        fit = prior[-1]
        entry = schedule.setdefault(fit, {"training": [fit], "validation": []})
        entry["validation"].append(season)
    return schedule


def _calibrate(df: pd.DataFrame, fit: str) -> tuple[str, EloFitParams]:
    res = calibrate_single_fit(df, fit, [fit])
    return fit, EloFitParams(k=res.k, h=res.h, nu=res.nu, c=res.c)


def refit_fits(df: pd.DataFrame, schedule: dict[str, dict[str, list[str]]],
               workers: int = 1) -> dict[str, EloFitParams]:
    """Parametri Elo ricalibrati per ogni chiave dello schema (una stagione di training ciascuna)."""
    fits = sorted(schedule, key=parse_season_start_year)
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            return dict(pool.map(_calibrate, [df] * len(fits), fits))
    return dict(_calibrate(df, f) for f in fits)


def refit_residuals(workers: int = 1) -> tuple[ModelResidualsData, dict[str, EloFitParams]]:
    """Residui del Modulo 1 con la ri-parametrizzazione annuale sulle stagioni di validazione, e i parametri."""
    df, _ = load_match_frame()
    cfg = read_split_config()
    available = sorted(set(df["season"]), key=parse_season_start_year)
    schedule = refit_schedule(cfg.validation, available)
    fits = refit_fits(df, schedule, workers)
    return model_residuals_data(df, schedule, fits), fits


def refit_module2_frame(data: ModelResidualsData) -> pd.DataFrame:
    """DataFrame del Modulo 2 con la ri-parametrizzazione: righe "training" delle stagioni di calibrazione
    e righe "validation" delle stagioni previste, costruite separatamente (una stagione di validazione
    può essere anche la stagione di calibrazione della successiva)."""
    from shk.model.module2_data import build_module2_frame

    res = data.residuals
    parts = [build_module2_frame(data._replace(residuals=res[res["role"] == role].reset_index(drop=True)))
             for role in ("training", "validation")]
    return pd.concat(parts, ignore_index=True)


REFIT_PARAM_COLUMNS: Final[tuple[str, ...]] = ("fit", "validation", "k", "h", "nu", "c")
REFIT_AGING_COLUMNS: Final[tuple[str, ...]] = (
    "season", "n_matches", "frozen_fit", "refit_fit", "frozen_g_hat", "refit_g_hat",
    "frozen_expected", "refit_expected", "frozen_log_loss", "refit_log_loss",
)


def refit_param_records(data: ModelResidualsData, fits: dict[str, EloFitParams]) -> list[dict]:
    """Una riga per stagione di calibrazione: stagioni previste e parametri Elo ricalibrati."""
    return [{"fit": fit, "validation": ";".join(entry["validation"]), "k": fits[fit].k, "h": fits[fit].h,
             "nu": fits[fit].nu, "c": fits[fit].c}
            for fit, entry in sorted(data.schedule.items(), key=lambda kv: parse_season_start_year(kv[0]))]


def _season_stats(frame: pd.DataFrame) -> pd.DataFrame:
    probs = frame[["p_home", "p_draw", "p_away"]].to_numpy()
    q = frame[["q_home", "q_draw", "q_away"]].to_numpy()
    p_obs = np.where(frame["FTR"].to_numpy()[:, None] == np.array(["H", "D", "A"]), probs, 0.0).sum(axis=1)
    out = pd.DataFrame({"season": frame["season"].to_numpy(), "fit": frame["fit_through"].to_numpy(),
                        "g_hat": frame["delta"].to_numpy(), "expected": expected_delta(probs, q),
                        "log_loss": -np.log(p_obs)})
    return out.groupby("season", sort=False).agg(n_matches=("g_hat", "size"), fit=("fit", "first"),
                                                 g_hat=("g_hat", "mean"), expected=("expected", "mean"),
                                                 log_loss=("log_loss", "mean"))


def refit_aging_records(frozen_frame: pd.DataFrame, refit_frame: pd.DataFrame) -> list[dict]:
    """Per stagione di validazione: ĝ, errore atteso medio e log-loss del modello congelato e ricalibrato."""
    fz = _season_stats(frozen_frame[frozen_frame["role"] == "validation"])
    rf = _season_stats(refit_frame[refit_frame["role"] == "validation"])
    if list(fz.index) != list(rf.index) or not (fz["n_matches"] == rf["n_matches"]).all():
        raise ValueError("frozen and refit validation frames cover different matches")
    return [{"season": s, "n_matches": int(fz.at[s, "n_matches"]), "frozen_fit": fz.at[s, "fit"],
             "refit_fit": rf.at[s, "fit"], "frozen_g_hat": fz.at[s, "g_hat"], "refit_g_hat": rf.at[s, "g_hat"],
             "frozen_expected": fz.at[s, "expected"], "refit_expected": rf.at[s, "expected"],
             "frozen_log_loss": fz.at[s, "log_loss"], "refit_log_loss": rf.at[s, "log_loss"]}
            for s in fz.index]
