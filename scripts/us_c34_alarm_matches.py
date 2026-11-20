"""Script: le partite dietro gli allarmi della versione principale e le favorite nette.

Due tabelle partita per partita, per gli esempi concreti del capitolo 5:

- results/us_c34_alarm_windows.csv: per ogni stagione in cui la versione principale si ferma
  (results/us_c33_main_alarm_seasons.csv), le 40 partite che il supervisore confronta con la
  stagione di calibrazione nella giornata della prima diagnosi strutturale, cioè le ultime 40 partite giocate prima di
  quella data, nell'ordine della stagione (season_input_from_frame). Per ciascuna: squadre, quote,
  probabilità del modello e del mercato senza margine (Shin) per i tre esiti e per l'esito
  realizzato, il residuo δ, e se è entrata nella finestra dopo la giornata di decisione precedente.
- results/us_c34_clear_favourites.csv: le partite con una favorita netta (quota più bassa sotto
  1,5) nelle stagioni di validazione, per calibrazione del modello e per campo della favorita
  (casa, trasferta, tutte): numero di partite, probabilità media della favorita secondo il modello
  e secondo il mercato, quota di vittorie della favorita, δ medio.
- results/us_c34_alarm_summary.csv: nelle finestre delle prime diagnosi strutturali, la quota di partite con la favorita
  del mercato in trasferta, quante sono fra le 5 partite con |δ| maggiore di ogni finestra, e |δ|
  medio con e senza la favorita in trasferta.
"""

import csv
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from shk.model.module2_data import build_module2_frame
from shk.model.residuals import load_model_residuals

REPO_ROOT = Path(__file__).resolve().parents[1]
SEASONS_CSV = REPO_ROOT / "results" / "us_c33_main_alarm_seasons.csv"
TRACE_CSV = REPO_ROOT / "results" / "us_c33_main_alarm_trace.csv"
WINDOWS_CSV = REPO_ROOT / "results" / "us_c34_alarm_windows.csv"
FAVOURITES_CSV = REPO_ROOT / "results" / "us_c34_clear_favourites.csv"
SUMMARY_CSV = REPO_ROOT / "results" / "us_c34_alarm_summary.csv"
WINDOW: Final[int] = 40
TOP: Final[int] = 5
CLEAR_ODDS: Final[float] = 1.5
OUTCOMES: Final[dict[str, int]] = {"H": 0, "D": 1, "A": 2}
WINDOW_COLUMNS: Final[tuple[str, ...]] = (
    "season", "fit_through", "structural_date", "structural_trigger", "date", "home", "away", "result", "odds_home", "odds_draw",
    "odds_away", "p_home", "p_draw", "p_away", "q_home", "q_draw", "q_away", "p_realized", "q_realized", "delta",
    "entered",
)
FAVOURITE_COLUMNS: Final[tuple[str, ...]] = ("fit_through", "favourite", "n_matches", "p_favourite",
                                             "q_favourite", "favourite_won", "mean_delta")


def _probabilities(rows: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    p = rows[["p_home", "p_draw", "p_away"]].to_numpy(float)
    q = rows[["q_home", "q_draw", "q_away"]].to_numpy(float)
    odds = rows[["odds_home", "odds_draw", "odds_away"]].to_numpy(float)
    realized = rows["FTR"].map(OUTCOMES).to_numpy(int)
    return p, q, odds, realized


def alarm_windows(frame: pd.DataFrame, seasons: pd.DataFrame, trace: pd.DataFrame) -> list[dict]:
    """Le 40 partite della finestra del supervisore nella giornata della prima diagnosi strutturale, per stagione."""
    out = []
    for _, s in seasons[seasons["first_structural_date"].notna()].iterrows():
        rows = frame[(frame["season"] == s["season"]) & (frame["role"] == "validation")]
        rows = rows.sort_values("Date", kind="stable").reset_index(drop=True)
        days = trace[trace["season"] == s["season"]].sort_values("day")
        stop = pd.Timestamp(s["first_structural_date"])
        previous = pd.Timestamp(days.loc[days["day"] == int(s["first_structural_day"]) - 1, "date"].iloc[0])
        window = rows[rows["Date"] < stop].tail(WINDOW)
        before = set(rows[rows["Date"] < previous].tail(WINDOW).index)
        p, q, odds, realized = _probabilities(window)
        k = np.arange(len(window))
        for j, (i, r) in enumerate(window.iterrows()):
            out.append({
                "season": s["season"], "fit_through": s["fit_through"], "structural_date": s["first_structural_date"],
                "structural_trigger": s["first_structural_trigger"], "date": str(r["Date"])[:10], "home": r["HomeTeam"],
                "away": r["AwayTeam"], "result": r["FTR"],
                "odds_home": odds[j, 0], "odds_draw": odds[j, 1], "odds_away": odds[j, 2],
                "p_home": p[j, 0], "p_draw": p[j, 1], "p_away": p[j, 2],
                "q_home": q[j, 0], "q_draw": q[j, 1], "q_away": q[j, 2],
                "p_realized": p[k[j], realized[j]], "q_realized": q[k[j], realized[j]], "delta": float(r["delta"]),
                "entered": i not in before,
            })
    return out


def clear_favourites(frame: pd.DataFrame) -> list[dict]:
    """Favorite nette nelle stagioni di validazione, per calibrazione e campo della favorita."""
    val = frame[frame["role"] == "validation"]
    p, q, odds, realized = _probabilities(val)
    favourite = odds.argmin(axis=1)
    k = np.arange(len(val))
    d = pd.DataFrame({
        "fit_through": val["fit_through"].to_numpy(), "clear": odds.min(axis=1) < CLEAR_ODDS,
        "favourite": np.where(favourite == 0, "home", np.where(favourite == 2, "away", "draw")),
        "p": p[k, favourite], "q": q[k, favourite], "won": realized == favourite, "delta": val["delta"].to_numpy(),
    })
    d = d[d["clear"]]
    out = []
    for fit in [*sorted(d["fit_through"].unique()), "all"]:
        by_fit = d if fit == "all" else d[d["fit_through"] == fit]
        for side in ("home", "away", "all"):
            g = by_fit if side == "all" else by_fit[by_fit["favourite"] == side]
            out.append({"fit_through": fit, "favourite": side, "n_matches": len(g), "p_favourite": g["p"].mean(),
                        "q_favourite": g["q"].mean(), "favourite_won": g["won"].mean(),
                        "mean_delta": g["delta"].mean()})
    return out


def window_summary(windows: list[dict], top: int = TOP) -> list[dict]:
    """Peso delle partite con la favorita in trasferta nelle finestre delle prime diagnosi strutturali (vedi modulo)."""
    w = pd.DataFrame(windows)
    w["away_favourite"] = w["odds_away"] < w["odds_home"]
    w["abs_delta"] = w["delta"].abs()
    largest = w.sort_values("abs_delta", ascending=False, kind="stable").groupby("season").head(top)
    return [{"statistic": k, "value": v} for k, v in (
        ("n_windows", w["season"].nunique()), ("n_matches", len(w)),
        ("share_away_favourite", w["away_favourite"].mean()),
        ("n_largest", len(largest)), ("n_largest_away_favourite", int(largest["away_favourite"].sum())),
        ("mean_abs_delta_away_favourite", w.loc[w["away_favourite"], "abs_delta"].mean()),
        ("mean_abs_delta_other", w.loc[~w["away_favourite"], "abs_delta"].mean()),
    )]


def _write(path: Path, columns: tuple[str, ...], rows: list[dict]) -> None:
    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(columns), restval="")
        writer.writeheader()
        writer.writerows(rows)


def run_experiment() -> None:
    frame = build_module2_frame(load_model_residuals())
    seasons = pd.read_csv(SEASONS_CSV, dtype={"season": str, "fit_through": str})
    trace = pd.read_csv(TRACE_CSV, dtype={"season": str, "fit_through": str})
    windows = alarm_windows(frame, seasons, trace)
    favourites = clear_favourites(frame)
    _write(WINDOWS_CSV, WINDOW_COLUMNS, windows)
    _write(FAVOURITES_CSV, FAVOURITE_COLUMNS, favourites)
    summary = window_summary(windows)
    _write(SUMMARY_CSV, ("statistic", "value"), summary)
    for r in summary:
        print(f"{r['statistic']:<32} {r['value']}")
    for r in favourites:
        print(f"{r['fit_through']:<8} {r['favourite']:<5} n {r['n_matches']:>4}  model {r['p_favourite']:.3f}  "
              f"market {r['q_favourite']:.3f}  won {r['favourite_won']:.3f}  delta {r['mean_delta']:+.3f}")
    w = pd.DataFrame(windows)
    for season, g in w.groupby("season"):
        top = g.reindex(g["delta"].abs().sort_values(ascending=False).index).head(3)
        print(season, " | ".join(f"{r.home}-{r.away} {r.result} delta {r.delta:+.2f}{' *' if r.entered else ''}"
                                 for r in top.itertuples()))


if __name__ == "__main__":
    run_experiment()
