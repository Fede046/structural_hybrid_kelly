"""Script: la popolazione di strategie con la dinamica del replicatore, nella nuova tesi (21 stagioni).

Legge, per ogni stagione S dal 2003-04 al 2023-24, i dati salvati da us_c46
(results/raw/us_c46/<versione>_<stagione>.npz): previsioni del modello iniziale (probs0) e delle due
ricalibrazioni (probs). Le strategie, tutte con la stessa scelta dell'esito (regola R1):
- kelly_pieno: probs0, Kelly pieno;
- ristima_uguale: la ricalibrazione con la ristima a pesi uguali, Kelly pieno;
- ristima_recente: la ricalibrazione con la ristima che pesa di più il presente, Kelly pieno;
- cassa (non nella versione con i soli tre agenti): non punta mai.
La strategia della puntata minima (£0,01 su £220 ogni giornata) è stata tolta il 2026-11-22: rischia così poco
che coincide in pratica con la cassa (risultati precedenti in results/archive_puntata_minima/).

Come nella tesi precedente la popolazione gira senza puntata minima nell'ambiente, così il rendimento
di una strategia non dipende dal capitale che le è affidato e il replicatore è esatto
(shk.model.population). μ = 0. Tre versioni: quote uguali a ogni stagione con la cassa, generazioni
(le quote iniziali sono le finali della stagione prima) con la cassa, e generazioni con i soli tre
agenti che puntano il Kelly pieno.

Scrive results/us_c43_population_members.csv, results/us_c43_population_seasons.csv e
results/us_c43_population_shares.csv.
"""

import os

os.environ["SHK_ELO_ENTRY"] = "plain"  # nuova tesi: nessuna regola per le neopromosse, prima di importare shk

import csv
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from shk.kelly.environment import run_paired_backtest
from shk.model.frozen_params import frozen_params_path, load_frozen_params
from shk.model.full_kelly_test import ScheduledKellyAgent
from shk.model.population import evolve, evolve_generations, gross_returns, with_cash

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS = REPO_ROOT / "results"
RAW = RESULTS / "raw" / "us_c46"
MU: Final[float] = 0.0
WORKERS: Final[int] = 5
KELLY_MEMBERS: Final[tuple[str, ...]] = ("kelly_pieno", "ristima_uguale", "ristima_recente")
MEMBERS: Final[tuple[str, ...]] = KELLY_MEMBERS
SEASONS: Final[tuple[str, ...]] = tuple(f"{y}-{str(y + 1)[-2:]}" for y in range(2003, 2024))


def season_paths(season: str) -> tuple[str, np.ndarray]:
    """Capitale giornata per giornata (N, D+1) delle strategie, senza puntata minima nell'ambiente."""
    fallback = load_frozen_params(frozen_params_path()).fixed["fallback_policy"]
    u = np.load(RAW / f"uguale_{season}.npz", allow_pickle=False)
    r = np.load(RAW / f"recente_{season}.npz", allow_pickle=False)
    dates, odds, outcomes = u["dates"], u["odds"], u["outcomes"]
    days = np.unique(dates)
    ones = {d: 1.0 for d in days}

    def run(agent, p):
        return run_paired_backtest([agent], dates, p, odds, outcomes, 0.0, fallback_policy=fallback)[0].wealth[0]

    paths = [run(ScheduledKellyAgent("kelly_pieno", ones), u["probs0"]),
             run(ScheduledKellyAgent("ristima_uguale", ones), u["probs"]),
             run(ScheduledKellyAgent("ristima_recente", ones), r["probs"])]
    return season, np.stack(paths)


def _write(path: Path, rows: list[dict]) -> None:
    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run_experiment() -> None:
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        out = list(pool.map(season_paths, SEASONS))
    members = [{"season": s, "agent": m, "final_capital": float(p[i, -1])} for s, p in out for i, m in enumerate(MEMBERS)]
    _write(RESULTS / "us_c43_population_members.csv", members)
    returns = [gross_returns(p) for _, p in out]
    cash = [with_cash(r) for r in returns]
    versions = {"quote_uguali_cassa": ([evolve(r, MU) for r in cash], MEMBERS + ("cassa",)),
                "generazioni_cassa": (evolve_generations(cash, MU), MEMBERS + ("cassa",)),
                "generazioni_solo_kelly": (evolve_generations(returns, MU), KELLY_MEMBERS)}
    seasons_rows, share_rows = [], []
    for version, (res, names) in versions.items():
        for (s, _), (sh, w) in zip(out, res):
            seasons_rows.append({"version": version, "season": s, "final_capital": float(w[-1])})
            for i, n in enumerate(names):
                share_rows.append({"version": version, "season": s, "agent": n, "start_share": float(sh[i, 0]),
                                   "end_share": float(sh[i, -1])})
    _write(RESULTS / "us_c43_population_seasons.csv", seasons_rows)
    _write(RESULTS / "us_c43_population_shares.csv", share_rows)
    pd.set_option("display.width", 250)
    m = pd.DataFrame(members).pivot(index="season", columns="agent", values="final_capital")
    print(m.round(4).to_string())
    print("typical (geometric mean):", np.exp(np.log(m).mean()).round(4).to_dict())
    sr = pd.DataFrame(seasons_rows).pivot(index="season", columns="version", values="final_capital")
    print("typical population:", np.exp(np.log(sr).mean()).round(4).to_dict())
    sh = pd.DataFrame(share_rows)
    for v in versions:
        start = sh[(sh.version == v)].pivot(index="season", columns="agent", values="start_share")
        last = sh[(sh.version == v) & (sh.season == SEASONS[-1])].set_index("agent")["end_share"]
        print(v, "end shares:", last.round(4).to_dict())
        print(start.round(3).to_string())


if __name__ == "__main__":
    run_experiment()
