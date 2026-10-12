"""Calibrazione di ξ e σ e valutazione di validazione del Dixon-Coles contro l'Elo (T59).

Calibrazione (schema espansivo dell'Elo, derive_fit_schedule): per ogni combinazione
(ξ, σ) ∈ XI_GRID × SIGMA_GRID, previsioni walk-forward delle stagioni di training; per ogni fit
l'obiettivo è la log-loss media sulle partite delle stagioni di training del fit. Vince il
minimo; a parità entro TIE_TOLERANCE il σ maggiore (prior più debole, decisione del
programmatore del 2026-10-12), poi il ξ minore (ordine della griglia).

Validazione: ogni stagione di validazione con il (ξ, σ) del suo fit (DC_FITS); log-loss e ĝ
dei cinque metodi su b365_prematch, accanto all'Elo (stesse partite, stesso de-vigging di C4.2).

Neopromosse mai viste: log-loss delle partite che coinvolgono una squadra mai vista nei primi
NEW_TEAM_MATCHDAYS matchday della stagione (matchday: blocco contiguo di MATCHDAY_SIZE partite
nell'ordine cronologico stabile della stagione, decisione S5), Dixon-Coles contro Elo, sul
training (per combinazione) e sulla validazione.
"""

import math
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor
from typing import Final

import numpy as np
import pandas as pd

from shk.model.dixon_coles import (
    DC_FITS,
    SIGMA_GRID,
    XI_GRID,
    DixonColesForecaster,
    LeakageCheck,
    WalkForwardStats,
    log_loss,
    provider_leakage_check,
)
from shk.model.elo_fit import ELO_FITS, parse_season_start_year
from shk.model.elo_predictor import predict_elo_fast
from shk.model.module2 import MATCHDAY_SIZE
from shk.model.module2_data import STATUS_NEW, entry_status_by_team_season
from shk.model.residuals import load_match_frame
from shk.model.scoring import (
    ALL_DEVIG_METHODS,
    MATCH_KEYS,
    align_predictions_with_odds,
    compute_g_hat_terms,
    generate_validation_predictions,
    prepare_series_evaluation,
)

TIE_TOLERANCE: Final[float] = 1e-12
NEW_TEAM_MATCHDAYS: Final[int] = 10
LEAKAGE_SAMPLE: Final[int] = 500
SERIES: Final[str] = "b365_prematch"

DC_CSV_COLUMNS: Final[tuple[str, ...]] = (
    "row_type", "fit", "xi", "sigma", "season", "model", "method", "n", "log_loss", "g_hat",
    "n_new_early", "log_loss_new_early", "chosen", "n_fits", "n_not_converged", "max_iter", "n_violations",
)


def load_frame() -> tuple[pd.DataFrame, dict[str, dict[str, list[str]]]]:
    """Storia, training e validazione (mai il test) ordinati per Date, e schema dei fit."""
    return load_match_frame()


def _sorted_seasons(seasons) -> list[str]:
    return sorted(set(seasons), key=parse_season_start_year)


def predict_dc(df: pd.DataFrame, xi: float, sigma: float,
               seasons: Sequence[str]) -> tuple[pd.DataFrame, WalkForwardStats]:
    """Previsioni walk-forward delle stagioni con (ξ, σ) e diagnostica dei fit."""
    fc = DixonColesForecaster(df, xi, sigma)
    preds = pd.concat([fc.predict_season(s) for s in seasons], ignore_index=True)
    return preds, fc.stats


def _map(func, args: list[tuple], workers: int) -> list:
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            return list(pool.map(func, *zip(*args)))
    return [func(*a) for a in args]


def with_outcomes(preds: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    """Aggiunge FTR alle previsioni (abbinamento per chiave di partita), se manca."""
    if "FTR" in preds.columns:
        return preds
    out = preds.merge(df[list(MATCH_KEYS) + ["FTR"]], on=list(MATCH_KEYS), how="left", validate="one_to_one")
    if out["FTR"].isna().any():
        raise ValueError("Predictions without outcome after merge")
    return out


def new_team_early_mask(preds: pd.DataFrame, status: dict[tuple[str, str], str],
                        n_matchdays: int = NEW_TEAM_MATCHDAYS) -> np.ndarray:
    """Partite con una squadra mai vista nei primi n_matchdays matchday della stagione.

    Le previsioni devono essere nell'ordine cronologico stabile della stagione.
    """
    position = preds.groupby("season", sort=False).cumcount().to_numpy()
    new = np.array([status.get((s, h)) == STATUS_NEW or status.get((s, a)) == STATUS_NEW
                    for s, h, a in zip(preds["season"], preds["HomeTeam"], preds["AwayTeam"])], dtype=bool)
    return new & (position < n_matchdays * MATCHDAY_SIZE)


def _loss_summary(preds: pd.DataFrame, seasons: Sequence[str], status: dict) -> dict:
    sel = preds[preds["season"].isin(list(seasons))].sort_values("Date", kind="stable")
    ll = log_loss(sel)
    early = new_team_early_mask(sel, status)
    return {"n": len(sel), "log_loss": float(ll.mean()), "n_new_early": int(early.sum()),
            "log_loss_new_early": float(ll[early].mean()) if early.any() else math.nan}


def choose(objective: Sequence[float], combos: Sequence[tuple[float, float]]) -> int:
    """Indice della combinazione scelta: minimo; parità entro TIE_TOLERANCE → σ maggiore, poi ξ minore."""
    best = min(objective)
    tied = [i for i, o in enumerate(objective) if o - best <= TIE_TOLERANCE]
    return min(tied, key=lambda i: (-combos[i][1], combos[i][0]))


def calibration_records(df: pd.DataFrame, schedule: dict,
                        workers: int = 1) -> tuple[list[dict], dict[str, tuple[float, float]]]:
    """Righe "calibration" per fit × ξ × σ, righe "calibration_elo" di riferimento e la scelta per fit."""
    status = entry_status_by_team_season(df)
    training = _sorted_seasons(s for v in schedule.values() for s in v["training"])
    combos = [(xi, sigma) for xi in XI_GRID for sigma in SIGMA_GRID]
    outs = _map(predict_dc, [(df, xi, sigma, training) for xi, sigma in combos], workers)
    records, chosen = [], {}
    for fit in _sorted_seasons(schedule):
        seasons = schedule[fit]["training"]
        summaries = [_loss_summary(preds, seasons, status) for preds, _ in outs]
        win = choose([s["log_loss"] for s in summaries], combos)
        chosen[fit] = combos[win]
        for i, ((xi, sigma), (_, stats)) in enumerate(zip(combos, outs)):
            records.append({"row_type": "calibration", "fit": fit, "xi": xi, "sigma": sigma, "model": "dixon_coles",
                            **summaries[i], "chosen": i == win, "n_fits": stats.n_fits,
                            "n_not_converged": stats.n_not_converged, "max_iter": stats.max_iter})
        p = ELO_FITS[fit]
        elo = with_outcomes(predict_elo_fast(df, seasons, k=p.k, h=p.h, nu=p.nu), df)
        records.append({"row_type": "calibration_elo", "fit": fit, "model": "elo", **_loss_summary(elo, seasons, status)})
    return records, chosen


def validation_predictions(df: pd.DataFrame, schedule: dict, fits: dict | None = None,
                           workers: int = 1) -> tuple[pd.DataFrame, list[dict]]:
    """Previsioni di validazione per fit con il suo (ξ, σ) (DC_FITS), con la diagnostica dei fit."""
    fits = DC_FITS if fits is None else fits
    order = [f for f in _sorted_seasons(schedule) if schedule[f]["validation"]]
    outs = _map(predict_dc, [(df, fits[f].xi, fits[f].sigma, schedule[f]["validation"]) for f in order], workers)
    diag, frames = [], []
    for f, (preds, stats) in zip(order, outs):
        frames.append(preds)
        diag.append({"row_type": "validation_fits", "fit": f, "xi": fits[f].xi, "sigma": fits[f].sigma,
                     "model": "dixon_coles", "n": len(preds), "n_fits": stats.n_fits,
                     "n_not_converged": stats.n_not_converged, "max_iter": stats.max_iter})
    out = pd.concat(frames, ignore_index=True).sort_values("Date", kind="stable").reset_index(drop=True)
    return out, diag


def comparison_records(df: pd.DataFrame, schedule: dict, dc_preds: pd.DataFrame,
                       elo_preds: pd.DataFrame) -> list[dict]:
    """Log-loss e ĝ (cinque metodi, b365_prematch) per stagione e pooled, Elo e Dixon-Coles."""
    records = []
    for model, preds in (("elo", elo_preds), ("dixon_coles", dc_preds)):
        cols = list(MATCH_KEYS) + ["p_home", "p_draw", "p_away"]
        ev = prepare_series_evaluation(align_predictions_with_odds(preds[cols], df), SERIES, schedule)
        seasons = ev.df_used["season"].astype(str).to_numpy()
        y = pd.Series(ev.outcomes).map({"H": 0, "D": 1, "A": 2}).to_numpy()
        ll = -np.log(ev.p_model[np.arange(y.size), y])
        terms = {m: compute_g_hat_terms(ev.p_model, getattr(ev, f"q_{m}"), ev.outcomes) for m in ALL_DEVIG_METHODS}
        for s in _sorted_seasons(seasons.tolist()) + ["pooled"]:
            sel = np.ones(y.size, dtype=bool) if s == "pooled" else seasons == s
            records.append({"row_type": "validation", "season": s, "model": model, "method": "",
                            "n": int(sel.sum()), "log_loss": float(ll[sel].mean())})
            for m in ALL_DEVIG_METHODS:
                records.append({"row_type": "validation", "season": s, "model": model, "method": m,
                                "n": int(sel.sum()), "g_hat": float(terms[m][sel].mean())})
    return records


def new_team_records(df: pd.DataFrame, schedule: dict, dc_preds: pd.DataFrame,
                     elo_preds: pd.DataFrame) -> list[dict]:
    """Neopromosse mai viste nei primi NEW_TEAM_MATCHDAYS matchday, validazione: Elo e Dixon-Coles."""
    status = entry_status_by_team_season(df)
    seasons = [s for f in schedule.values() for s in f["validation"]]
    records = []
    for model, preds in (("elo", with_outcomes(elo_preds, df)), ("dixon_coles", dc_preds)):
        summary = _loss_summary(preds, seasons, status)
        records.append({"row_type": "new_teams_early", "season": "pooled", "model": model,
                        "n": summary["n_new_early"], "log_loss": summary["log_loss_new_early"]})
    return records


def leakage_record(df: pd.DataFrame, schedule: dict, rng: np.random.Generator) -> tuple[dict, LeakageCheck]:
    """Controllo anti-leakage su LEAKAGE_SAMPLE partite di training e validazione (ξ e σ del fit 2020-21)."""
    seasons = _sorted_seasons(s for v in schedule.values() for s in v["training"] + v["validation"])
    last = _sorted_seasons(schedule)[-1]
    fc = DixonColesForecaster(df, DC_FITS[last].xi, DC_FITS[last].sigma)
    check = provider_leakage_check(fc, seasons, LEAKAGE_SAMPLE, rng)
    return ({"row_type": "check", "model": "dixon_coles", "xi": DC_FITS[last].xi, "sigma": DC_FITS[last].sigma,
             "n": check.n_checked, "n_violations": check.n_violations + check.n_outside_provider}, check)


def elo_validation_predictions(df: pd.DataFrame, schedule: dict) -> pd.DataFrame:
    """Previsioni Elo di validazione con ELO_FITS (codice dell'Elo invariato)."""
    return generate_validation_predictions(df, ELO_FITS, schedule)
