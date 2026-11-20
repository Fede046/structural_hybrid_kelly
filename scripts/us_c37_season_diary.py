"""Script: il diario di una stagione della versione definitiva, scommessa per scommessa (capitolo 5).

Per le stagioni di DIARY_SEASONS ricostruisce le scommesse della versione definitiva (F, puntata minima
di £0,01): per ogni partita l'esito scelto dal lavoratore (regola R1, valore atteso stimato più alto),
quota, probabilità del modello e del mercato senza margine (Shin), valore atteso stimato, frazione di
Kelly, moltiplicatore λ della giornata (dalla traccia di us_c33), frazione puntata λ·f* e risultato.
Le frazioni sono del capitale all'inizio della giornata; con la puntata minima l'ambiente aggiunge,
nelle giornate senza scommesse, £0,01 sulla partita con il valore atteso più alto, che qui non compare
(effetto sul capitale al più di qualche decimillesimo). Il capitale ricostruito dalle scommesse è
confrontato con quello della traccia.

Scrive results/us_c37_season_diary.csv (una riga per partita delle stagioni scelte).
"""

import csv
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from shk.model.module2_data import build_module2_frame
from shk.model.residuals import load_model_residuals

DIARY_SEASONS: Final[tuple[str, ...]] = ("2018-19", "2011-12", "2013-14")
REPO_ROOT = Path(__file__).resolve().parents[1]
TRACE_CSV = REPO_ROOT / "results" / "us_c33_main_alarm_trace.csv"
DIARY_CSV = REPO_ROOT / "results" / "us_c37_season_diary.csv"
OUTCOMES: Final[tuple[str, ...]] = ("H", "D", "A")
COLUMNS: Final[tuple[str, ...]] = (
    "season", "day", "date", "home", "away", "result", "pick", "market_favourite", "odds", "p_model", "q_market",
    "expected_value",
    "kelly_fraction", "lambda", "diagnosis", "stake_fraction", "won", "delta", "capital_before", "capital_after",
    "capital_quarter_after",
)
MAX_RECONSTRUCTION_ERROR: Final[float] = 2e-3


def diary_rows(frame: pd.DataFrame, trace: pd.DataFrame, season: str) -> list[dict]:
    rows = frame[(frame["season"] == season) & (frame["role"] == "validation")].sort_values("Date", kind="stable")
    t = trace[trace["season"] == season].sort_values("day").reset_index(drop=True)
    out = []
    capital = 1.0
    for _, d in t.iterrows():
        matches = rows[rows["Date"] == pd.Timestamp(d["date"])]
        p = matches[["p_home", "p_draw", "p_away"]].to_numpy(float)
        q = matches[["q_home", "q_draw", "q_away"]].to_numpy(float)
        o = matches[["odds_home", "odds_draw", "odds_away"]].to_numpy(float)
        ev = p * o - 1.0
        pick = ev.argmax(axis=1)
        k = np.arange(len(matches))
        f_star = np.maximum(0.0, ev[k, pick] / (o[k, pick] - 1.0))
        stake = float(d["lambda"]) * f_star
        won = matches["FTR"].to_numpy() == np.array(OUTCOMES)[pick]
        gain = float(np.sum(np.where(won, stake * (o[k, pick] - 1.0), -stake)))
        before = capital
        capital = capital * (1.0 + gain)
        if abs(np.log(capital) - np.log(d["wealth_main"])) > MAX_RECONSTRUCTION_ERROR:
            raise RuntimeError(f"{season} {d['date']}: capital {capital} vs trace {d['wealth_main']}")
        capital = float(d["wealth_main"])
        for j, (_, m) in enumerate(matches.iterrows()):
            out.append({"season": season, "day": int(d["day"]), "date": d["date"], "home": m["HomeTeam"],
                        "away": m["AwayTeam"], "result": m["FTR"], "pick": OUTCOMES[pick[j]],
                        "market_favourite": OUTCOMES[int(o[j].argmin())],
                        "odds": o[j, pick[j]], "p_model": p[j, pick[j]], "q_market": q[j, pick[j]],
                        "expected_value": ev[j, pick[j]], "kelly_fraction": f_star[j], "lambda": float(d["lambda"]),
                        "diagnosis": d["diagnosis"], "stake_fraction": stake[j], "won": bool(won[j]) and stake[j] > 0,
                        "delta": float(m["delta"]), "capital_before": before, "capital_after": capital,
                        "capital_quarter_after": float(d["wealth_quarter"])})
    return out


def run_experiment() -> None:
    frame = build_module2_frame(load_model_residuals())
    trace = pd.read_csv(TRACE_CSV, dtype={"season": str})
    rows = [r for s in DIARY_SEASONS for r in diary_rows(frame, trace, s)]
    with open(DIARY_CSV, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(COLUMNS))
        writer.writeheader()
        writer.writerows(rows)
    d = pd.DataFrame(rows)
    for season, g in d.groupby("season", sort=False):
        bets = g[g["stake_fraction"] > 0]
        print(f"{season}: {len(g)} partite, {len(bets)} scommesse, contro la favorita del mercato "
              f"{np.mean(bets['pick'] != bets['market_favourite']):.3f}, puntata media "
              f"{100 * bets['stake_fraction'].mean():.2f}%, capitale finale {100 * g['capital_after'].iloc[-1]:.1f}% "
              f"(quarto di Kelly {100 * g['capital_quarter_after'].iloc[-1]:.1f}%)")


if __name__ == "__main__":
    run_experiment()
