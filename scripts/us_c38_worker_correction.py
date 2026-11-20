"""Script: un lavoratore che corregge le proprie previsioni imparando dagli errori passati (esplorativo).

Prima di ogni giornata il lavoratore stima, sulle ultime N_PAST partite già giocate e previste dallo
stesso fit (Date < giornata), un logit multinomiale che ricalibra le proprie probabilità:
utilità dell'esito k = alpha · ln p̂_k + a_k + b_k · elo_diff / 100, con a_A = b_A = 0. Usa soltanto
le previsioni del modello, la differenza Elo e i risultati, mai le quote. Le probabilità corrette
della giornata sono quelle del logit stimato.

Sulle 19 stagioni vere, con la puntata minima di £0,01, il quarto di Kelly gioca con le previsioni
originali e con quelle corrette (regola R1). Per ogni stagione: capitale finale, numero di scommesse,
quota media del capitale puntata per giornata, quota di scommesse sulla favorita del mercato, scarto
medio dal mercato (ĝ) e log-loss, con e senza correzione.

Scrive results/us_c38_worker_correction_seasons.csv e results/us_c38_worker_correction_summary.csv.
È una prova esplorativa, fatta dopo aver visto le stagioni di valutazione.
"""

import csv
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from shk.kelly.agents import AGENT_B_LAMBDA, FractionalKellyAgent
from shk.kelly.environment import run_paired_backtest
from shk.kelly.outcome_rules import with_outcome_rule
from shk.market.devig import devig_probabilities
from shk.model.frozen_params import frozen_params_path, load_frozen_params
from shk.model.module2_data import build_module2_frame
from shk.model.paired_backtest import CONFIGURATIONS
from shk.model.residuals import load_model_residuals
from shk.model.validation_run import ValidationSeason, validation_inputs

N_PAST: Final[int] = 760
WORKERS = 5
OUTCOMES: Final[dict[str, int]] = {"H": 0, "D": 1, "A": 2}
REPO_ROOT = Path(__file__).resolve().parents[1]
SEASONS_CSV = REPO_ROOT / "results" / "us_c38_worker_correction_seasons.csv"
SUMMARY_CSV = REPO_ROOT / "results" / "us_c38_worker_correction_summary.csv"
SEASON_COLUMNS: Final[tuple[str, ...]] = (
    "season", "fit_through", "probabilities", "log_wealth", "n_bets", "share_staked", "share_on_favourite",
    "g_hat", "log_loss",
)
SUMMARY_COLUMNS: Final[tuple[str, ...]] = (
    "probabilities", "typical_capital", "mean_n_bets", "share_staked", "share_on_favourite", "g_hat", "log_loss",
    "seasons_better", "seasons_worse", "median_alpha",
)


def _utilities(theta: np.ndarray, logp: np.ndarray, elo: np.ndarray) -> np.ndarray:
    alpha, a_h, a_d, b_h, b_d = theta
    u = alpha * logp
    u[:, 0] += a_h + b_h * elo
    u[:, 1] += a_d + b_d * elo
    return u - u.max(axis=1, keepdims=True)


def _nll(theta: np.ndarray, logp: np.ndarray, elo: np.ndarray, y: np.ndarray) -> float:
    u = _utilities(theta, logp, elo)
    return float(-(u[np.arange(len(y)), y] - np.log(np.exp(u).sum(axis=1))).sum())


def corrected_probabilities(frame: pd.DataFrame, season: str, fit: str) -> tuple[np.ndarray, np.ndarray]:
    """Probabilità corrette della stagione (N, 3), in ordine di stagione, e alpha stimato per giornata."""
    same_fit = frame[frame["fit_through"] == fit].sort_values("Date", kind="stable")
    rows = frame[(frame["season"] == season) & (frame["role"] == "validation")].sort_values("Date", kind="stable")
    probs = rows[["p_home", "p_draw", "p_away"]].to_numpy(float)
    out, alphas = probs.copy(), []
    theta = np.array([1.0, 0.0, 0.0, 0.0, 0.0])
    for day in rows["Date"].unique():
        past = same_fit[same_fit["Date"] < day].tail(N_PAST)
        logp = np.log(past[["p_home", "p_draw", "p_away"]].to_numpy(float))
        elo = past["elo_diff"].to_numpy(float) / 100.0
        y = past["FTR"].map(OUTCOMES).to_numpy(int)
        theta = minimize(_nll, theta, args=(logp, elo, y), method="BFGS").x
        alphas.append(theta[0])
        today = (rows["Date"] == day).to_numpy()
        u = _utilities(theta, np.log(probs[today]), rows.loc[today, "elo_diff"].to_numpy(float) / 100.0)
        e = np.exp(u)
        out[today] = e / e.sum(axis=1, keepdims=True)
    return out, np.array(alphas)


def run_season(params_path: str, frame: pd.DataFrame, season: ValidationSeason) -> tuple[list[dict], np.ndarray]:
    params = load_frozen_params(params_path)
    inp = season.inp
    corrected, alphas = corrected_probabilities(frame, inp.season, season.fit)
    q = devig_probabilities(np.asarray(inp.odds, dtype=np.float64), "shin")
    y = inp.outcomes[0]
    k = np.arange(y.shape[0])
    favourite = np.asarray(inp.odds).argmin(axis=1)
    rows = []
    for name, probs in (("original", inp.probs), ("corrected", corrected)):
        agent = with_outcome_rule(FractionalKellyAgent, "R1")(name, lam=AGENT_B_LAMBDA)
        run = run_paired_backtest([agent], inp.dates, probs, inp.odds, inp.outcomes,
                                  dict(CONFIGURATIONS)["gbp_0.01"], record_stakes=True,
                                  fallback_policy=params.fixed["fallback_policy"])[0]
        ev = probs * inp.odds - 1.0
        bet = ev.max(axis=1) > 0
        rows.append({"season": inp.season, "fit_through": season.fit, "probabilities": name,
                     "log_wealth": float(np.log(run.wealth[0, -1])), "n_bets": int(run.n_bets[0]),
                     "share_staked": float(np.mean(run.staked[0] / run.wealth[0, :-1])),
                     "share_on_favourite": float(np.mean(ev.argmax(axis=1)[bet] == favourite[bet])),
                     "g_hat": float(np.mean(np.log(probs[k, y]) - np.log(q[k, y]))),
                     "log_loss": float(-np.mean(np.log(probs[k, y])))})
    return rows, alphas


def run_experiment() -> None:
    params_path = frozen_params_path()
    params = load_frozen_params(params_path)
    frame = build_module2_frame(load_model_residuals())
    val = validation_inputs(frame, list(params.fixed["covariates"]))
    n = len(val)
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        results = list(pool.map(run_season, [str(params_path)] * n, [frame] * n, val))
    season_rows = [r for rows, _ in results for r in rows]
    alpha = float(np.median(np.concatenate([a for _, a in results])))
    df = pd.DataFrame(season_rows)
    base = df[df["probabilities"] == "original"].set_index("season")["log_wealth"]
    summary = []
    for name, g in df.groupby("probabilities", sort=False):
        lw = g.set_index("season")["log_wealth"]
        summary.append({"probabilities": name, "typical_capital": float(np.exp(lw.mean())),
                        "mean_n_bets": float(g["n_bets"].mean()), "share_staked": float(g["share_staked"].mean()),
                        "share_on_favourite": float(g["share_on_favourite"].mean()), "g_hat": float(g["g_hat"].mean()),
                        "log_loss": float(g["log_loss"].mean()),
                        "seasons_better": int((lw > base + 1e-12).sum()), "seasons_worse": int((lw < base - 1e-12).sum()),
                        "median_alpha": alpha if name == "corrected" else ""})
    for path, columns, rows in ((SEASONS_CSV, SEASON_COLUMNS, season_rows), (SUMMARY_CSV, SUMMARY_COLUMNS, summary)):
        with open(path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(columns), restval="")
            writer.writeheader()
            writer.writerows(rows)
    for r in summary:
        print(r)


if __name__ == "__main__":
    run_experiment()
