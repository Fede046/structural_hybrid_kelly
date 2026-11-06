"""Script: confronto delle previsioni dell'LLM con il mercato, a partite giocate (esplorativo).

Legge le previsioni (--predictions, CSV di llm_live_predict.py: Date, HomeTeam, AwayTeam, p_home, p_draw,
p_away) e il CSV della stagione di football-data.co.uk con risultati e quote Bet365 prima della partita
(--results). Per ogni partita giocata:
- q, probabilità del mercato senza margine (metodo di Shin, come nel resto del progetto);
- δ = ln p_LLM(esito reale) − ln q(esito reale), la stessa misura usata per l'Elo (−0,022 sulla validazione):
  positiva se l'LLM ha dato più probabilità del mercato all'esito vero.
Riporta la media di δ con intervallo bootstrap al 95% (ricampionando le partite), la log-loss di LLM e
mercato, quante volte l'esito più probabile è quello vero, e una prova «sulla carta»: 1 unità sull'esito
con valore atteso stimato p_LLM · quota − 1 più alto, se positivo (nessuna scommessa vera).
Scrive accanto alle previsioni evaluation.csv (una riga per partita).
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from shk.market.devig import devig_probabilities

SEED = 20261109
N_BOOT = 10_000


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--predictions", required=True)
    p.add_argument("--results", required=True)
    args = p.parse_args(argv)

    pred = pd.read_csv(args.predictions, parse_dates=["Date"])
    res = pd.read_csv(args.results, encoding="utf-8-sig")
    res["Date"] = pd.to_datetime(res["Date"], dayfirst=True)
    keys = ["Date", "HomeTeam", "AwayTeam"]
    df = pred.merge(res[keys + ["FTHG", "FTAG", "FTR", "B365H", "B365D", "B365A"]], on=keys, how="left")
    missing = df["FTR"].isna()
    if missing.any():
        print(f"Partite non ancora nel file dei risultati: {int(missing.sum())} (escluse)")
    df = df[~missing].reset_index(drop=True)
    if df.empty:
        print("Nessuna partita giocata da valutare.")
        return 1

    p_llm = df[["p_home", "p_draw", "p_away"]].to_numpy(dtype=float)
    odds = df[["B365H", "B365D", "B365A"]].to_numpy(dtype=float)
    q = devig_probabilities(odds, "shin")
    y = df["FTR"].map({"H": 0, "D": 1, "A": 2}).to_numpy()
    idx = np.arange(len(df))
    lp, lq = np.log(p_llm[idx, y]), np.log(q[idx, y])
    delta = lp - lq

    ev = p_llm * odds - 1.0
    pick = ev.argmax(axis=1)
    bet = ev[idx, pick] > 0.0
    profit = np.where(bet, np.where(pick == y, odds[idx, pick] - 1.0, -1.0), 0.0)

    df["q_home"], df["q_draw"], df["q_away"] = q[:, 0], q[:, 1], q[:, 2]
    df["delta"] = delta
    df["llm_pick_ok"] = p_llm.argmax(axis=1) == y
    df["market_pick_ok"] = q.argmax(axis=1) == y
    df["paper_bet"] = np.where(bet, np.array(list("HDA"))[pick], "")
    df["paper_profit"] = profit
    out = Path(args.predictions).parent / "evaluation.csv"
    df.to_csv(out, index=False)

    rng = np.random.default_rng(SEED)
    boot = delta[rng.integers(0, len(delta), size=(N_BOOT, len(delta)))].mean(axis=1)
    lo, hi = np.quantile(boot, [0.025, 0.975])
    n = len(df)
    print(f"Partite valutate: {n}")
    print(f"delta medio (LLM - mercato): {delta.mean():+.4f}   IC 95% bootstrap [{lo:+.4f}, {hi:+.4f}]")
    print(f"Partite in cui l'LLM dà più probabilità del mercato all'esito vero: {(delta > 0).mean():.0%}")
    print(f"Log-loss  LLM {-lp.mean():.4f}   mercato {-lq.mean():.4f}")
    print(f"Esito più probabile giusto  LLM {df['llm_pick_ok'].mean():.0%}   mercato {df['market_pick_ok'].mean():.0%}")
    n_bets = int(bet.sum())
    roi = profit.sum() / n_bets if n_bets else float("nan")
    print(f"Sulla carta: {n_bets} puntate da 1 unità, guadagno {profit.sum():+.2f}, rendimento per unità {roi:+.1%}")
    print(f"File: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
