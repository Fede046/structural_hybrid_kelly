"""Script: le 21 stagioni giornata per giornata, per le figure della nuova tesi (versione definitiva).

Legge i dati salvati da us_c45 (results/raw/us_c45/<stagione>.npz) e, per ogni stagione dal 2003-04 al
2023-24, scrive una riga per giornata: data, diagnosi e λ della versione definitiva («riduce e
riparametrizza»), statistiche dell'ANOVA sulla media e sulla dispersione divise per la soglia (del modello
in uso quel giorno), se quel giorno il modello è stato ristimato, capitale dopo la giornata del Kelly
pieno, della sola riduzione e della versione definitiva (puntata minima £0,01 su £220). Controlla che il
capitale finale della versione definitiva coincida con us_c45 e quello del Kelly pieno con us_c42.

Scrive results/us_c44_traces.csv.
"""

import os

os.environ["SHK_ELO_ENTRY"] = "plain"  # nuova tesi: nessuna regola per le neopromosse, prima di importare shk

import csv
from pathlib import Path

import numpy as np
import pandas as pd

from shk.kelly.environment import run_paired_backtest
from shk.model.frozen_params import frozen_params_path, load_frozen_params
from shk.model.full_kelly_test import ScheduledKellyAgent, season_lambda
from shk.model.paired_backtest import CONFIGURATIONS

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW = REPO_ROOT / "results" / "raw" / "us_c45"
TRACES_CSV = REPO_ROOT / "results" / "us_c44_traces.csv"
SEASONS = tuple(f"{y}-{str(y + 1)[-2:]}" for y in range(2003, 2024))
MIN_STAKE = dict(CONFIGURATIONS)["gbp_0.01"]


def season_trace(season: str, fallback: str) -> list[dict]:
    z = np.load(RAW / f"{season}.npz", allow_pickle=False)
    dates, probs0, odds, outcomes = z["dates"], z["probs0"], z["odds"], z["outcomes"]
    days = np.unique(dates)
    full, solo = run_paired_backtest(
        [ScheduledKellyAgent("kelly_pieno", {d: 1.0 for d in days}),
         ScheduledKellyAgent("solo_riduzione", dict(zip(days, season_lambda(z["diag0"], False))))],
        dates, probs0, odds, outcomes, MIN_STAKE, fallback_policy=fallback)
    refit = set(int(x) for x in z["refit_days"])
    rows = []
    for j, day in enumerate(days):
        rows.append({"season": season, "day": j + 1, "date": str(pd.Timestamp(day).date()),
                     "diagnosis": str(z["labels"][j]), "lambda": float(z["lam"][j]),
                     "f_mean_ratio": float(z["ratios"][j, 0]), "f_dispersion_ratio": float(z["ratios"][j, 1]),
                     "refit": j in refit, "wealth_full_kelly": float(full.wealth[0, j + 1]),
                     "wealth_reduce_only": float(solo.wealth[0, j + 1]), "wealth_definitive": float(z["wealth"][j + 1])})
    return rows


def run_experiment() -> None:
    fallback = load_frozen_params(frozen_params_path()).fixed["fallback_policy"]
    rows = [r for s in SEASONS for r in season_trace(s, fallback)]
    with open(TRACES_CSV, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    t = pd.DataFrame(rows).groupby("season").last()
    c45 = pd.read_csv(REPO_ROOT / "results" / "us_c45_reparam_seasons.csv").set_index("season")
    c42 = pd.read_csv(REPO_ROOT / "results" / "us_c42_rolling_seasons.csv").set_index("season")
    if not (np.allclose(t["wealth_definitive"], c45.loc[t.index, "final_capital"], rtol=1e-9)
            and np.allclose(t["wealth_full_kelly"], c42.loc[t.index, "full_kelly"], rtol=1e-9)
            and np.allclose(t["wealth_reduce_only"], c42.loc[t.index, "brake"], rtol=1e-9)):
        raise RuntimeError("traces differ from us_c45 / us_c42")
    print("ok", len(rows))


if __name__ == "__main__":
    run_experiment()
