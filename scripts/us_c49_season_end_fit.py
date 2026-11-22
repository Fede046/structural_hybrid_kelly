"""Script: i parametri del modello stimati a stagione finita, per controllare la direzione delle ristime.

Controllo del 2026-11-22, deciso scrivendo il bilancio del framework (§5.4 e §7.3 della tesi): la ristima
recente abbassa il vantaggio del campo h sia nel 2020-21 sia nel 2016-17; a stagione finita si può vedere
se andava nella direzione giusta. Per ogni stagione in cui us_c46 ristima il modello almeno una volta,
K, h, ν si stimano con tutte le partite della stagione (data limite: il 1° luglio dopo la stagione) e le
stagioni passate, con tre pesi:
- "uguale": stesso peso per tutte le stagioni (half-life infinita), come la ristima a pesi uguali;
- "recente": il peso si dimezza a ogni stagione di età (half-life 1), come la ristima recente;
- "sola stagione": half-life 0,05, le stagioni passate pesano quasi nulla (0,5^20 la precedente).
Stessi punteggi di partenza, limiti e ottimizzatore di weighted_refit; h ha limite inferiore 0.
Accanto: i parametri di inizio stagione, quelli della prima ristima recente di us_c46 e le frequenze di
vittoria in casa, pareggio e vittoria in trasferta della stagione.

Scrive results/us_c49_season_end_fit.csv.
"""

import os

os.environ["SHK_ELO_ENTRY"] = "plain"  # nuova tesi: nessuna regola per le neopromosse, prima di importare shk

import csv
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from shk.model.full_kelly_test import fit_full_model, weighted_refit
from shk.model.residuals import load_match_frame

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS = REPO_ROOT / "results"
WORKERS: Final[int] = 5
WEIGHTS: Final[dict[str, float]] = {"uguale": float("inf"), "recente": 1.0, "sola stagione": 0.05}


def _df() -> pd.DataFrame:
    df, _ = load_match_frame(roles=("history", "training", "validation", "test"))
    return df


def season_end(season: str) -> np.datetime64:
    return np.datetime64(f"{int(season[:4]) + 1}-07-01", "ns")


def fit_one(task: tuple[str, str]) -> dict:
    season, weight = task
    df = _df()
    if weight == "inizio":
        fit = fit_full_model(df, season)
    else:
        fit = weighted_refit(df, season, season_end(season), WEIGHTS[weight])
    return {"season": season, "fit": weight, "k": fit.k, "h": fit.h, "nu": fit.nu}


def run_experiment() -> None:
    refits = pd.read_csv(RESULTS / "us_c46_strong_refit_refits.csv")
    seasons = sorted(refits["season"].unique())
    tasks = [(s, w) for s in seasons for w in ("inizio", *WEIGHTS)]
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        fits = pd.DataFrame(list(pool.map(fit_one, tasks)))
    df = _df()
    first = refits[(refits["version"] == "recente") & (refits["refit"] == 1)].set_index("season")
    rows = []
    for s in seasons:
        res = df.loc[df["season"] == s, "FTR"].value_counts(normalize=True)
        row = {"season": s, "home_share": res.get("H", 0.0), "draw_share": res.get("D", 0.0),
               "away_share": res.get("A", 0.0), "first_refit_date": first.loc[s, "date"],
               "first_refit_k": first.loc[s, "k"], "first_refit_h": first.loc[s, "h"],
               "first_refit_nu": first.loc[s, "nu"]}
        for _, f in fits[fits["season"] == s].iterrows():
            tag = f["fit"].replace(" ", "_")
            row.update({f"{tag}_k": f["k"], f"{tag}_h": f["h"], f"{tag}_nu": f["nu"]})
        rows.append(row)
    out = RESULTS / "us_c49_season_end_fit.csv"
    with open(out, mode="w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    pd.set_option("display.width", 250)
    print(pd.DataFrame(rows).set_index("season").round(3).T.to_string())


if __name__ == "__main__":
    run_experiment()
