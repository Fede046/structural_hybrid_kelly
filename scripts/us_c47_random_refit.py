"""Script: la ricalibrazione contro le ristime fatte in giorni scelti a caso (controllo del momento giusto).

Per ogni versione della ricalibrazione di us_c46 ("uguale", "recente") e per ogni stagione in cui quella
versione ristima il modello almeno una volta:
1. precalcolo: il modello viene ristimato in ogni giornata d in cui il supervisore può già fare il
   confronto (almeno 40 partite giocate), con la stessa ristima della versione (stagioni passate più le
   partite della stagione prima di d), e si salvano le previsioni dell'intera stagione con quei
   parametri (results/raw/us_c47/<versione>_<stagione>_<d>.npy; se il file esiste non si ricalcola);
2. calendari: il calendario vero ristima nei giorni scelti dal supervisore; ogni calendario casuale
   ristima lo stesso numero di volte, in giornate estratte a caso fra quelle possibili. Le previsioni
   di una partita sono quelle dell'ultima ristima fatta prima della sua giornata (il modello iniziale se
   non ce n'è). Una ristima dipende solo dalle partite precedenti, quindi le previsioni precalcolate
   compongono esattamente qualunque calendario; il calendario vero deve riprodurre us_c46.
   Si gioca il Kelly pieno con la puntata minima di £0,01 su £220, N_CALENDARS calendari per stagione.

Il valore p di una stagione è la quota di calendari casuali che conservano almeno quanto il calendario
vero; quello complessivo somma il logaritmo del capitale finale sulle stagioni, calendario per calendario.

Scrive results/us_c47_random_refit_seasons.csv, results/us_c47_random_refit_calendars.csv e
results/us_c47_random_refit_summary.csv. Con --precompute-only esegue solo il punto 1.
"""

import os

os.environ["SHK_ELO_ENTRY"] = "plain"  # nuova tesi: nessuna regola per le neopromosse, prima di importare shk

import csv
import importlib.util
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from shk.kelly.environment import run_paired_backtest
from shk.model.frozen_params import frozen_params_path, load_frozen_params
from shk.model.full_kelly_test import ScheduledKellyAgent, previous_season, weighted_refit
from shk.model.paired_backtest import CONFIGURATIONS
from shk.model.residuals import load_match_frame, model_residuals_data

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS = REPO_ROOT / "results"
RAW46 = RESULTS / "raw" / "us_c46"
RAW = RESULTS / "raw" / "us_c47"
SEED_S47: Final[int] = 20261125
N_CALENDARS: Final[int] = 2000
WORKERS: Final[int] = 5
WINDOW: Final[int] = 40
HALF_LIFE: Final[float] = 1.0
MIN_STAKE: Final[float] = dict(CONFIGURATIONS)["gbp_0.01"]
VERSIONS: Final[tuple[str, ...]] = ("uguale", "recente")

_spec = importlib.util.spec_from_file_location("us_c45", REPO_ROOT / "scripts" / "us_c45_reparam.py")
us_c45 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(us_c45)

_DF: pd.DataFrame | None = None


def _df() -> pd.DataFrame:
    global _DF
    if _DF is None:
        _DF, _ = load_match_frame(roles=("history", "training", "validation", "test"))
    return _DF


def eligible_days(dates: np.ndarray) -> tuple[np.ndarray, int]:
    days = np.unique(dates)
    counts = np.searchsorted(dates, days, side="left")
    return days, int(np.flatnonzero(counts >= WINDOW)[0])


def grid_path(version: str, season: str, j: int) -> Path:
    return RAW / f"{version}_{season}_{j:03d}.npy"


def precompute_one(task: tuple[str, str, int]) -> str:
    version, season, j = task
    path = grid_path(version, season, j)
    if path.exists():
        return "skip"
    z = np.load(RAW46 / f"{version}_{season}.npz")
    days, _ = eligible_days(z["dates"])
    before = np.datetime64(days[j], "ns")
    df = _df()
    fit = us_c45.refit(df, season, before) if version == "uguale" else weighted_refit(df, season, before, HALF_LIFE)
    res = model_residuals_data(df, {previous_season(season): {"training": [], "validation": [season]}},
                               {previous_season(season): fit}).residuals
    res = res[res["season"] == season]
    if not np.array_equal(res["Date"].to_numpy("datetime64[ns]"), z["dates"]):
        raise RuntimeError(f"{season}: prediction rows differ from us_c46")
    RAW.mkdir(parents=True, exist_ok=True)
    np.save(path, res[["p_home", "p_draw", "p_away"]].to_numpy(np.float64))
    return "done"


def compose(z, grid: dict[int, np.ndarray], refit_days: np.ndarray, days: np.ndarray) -> np.ndarray:
    probs = z["probs0"].copy()
    for j in np.sort(refit_days):
        rows = z["dates"] >= days[j]
        probs[rows] = grid[int(j)][rows]
    return probs


def calendars_one(task: tuple[str, str]) -> tuple[dict, list[dict]]:
    version, season = task
    fallback = load_frozen_params(frozen_params_path()).fixed["fallback_policy"]
    z = np.load(RAW46 / f"{version}_{season}.npz")
    days, first = eligible_days(z["dates"])
    possible = np.arange(first, len(days))
    grid = {int(j): np.load(grid_path(version, season, int(j))) for j in possible}
    real_days = z["refit_days"]
    ones = {np.datetime64(d, "ns"): 1.0 for d in days}

    def play(refit_days: np.ndarray) -> float:
        probs = compose(z, grid, refit_days, days)
        run = run_paired_backtest([ScheduledKellyAgent("k", ones)], z["dates"], probs, z["odds"], z["outcomes"],
                                  MIN_STAKE, fallback_policy=fallback)[0]
        return float(run.wealth[0, -1])

    real = play(real_days)
    if abs(np.log(real) - np.log(float(z["wealth"][-1]))) > 1e-9:
        raise RuntimeError(f"{version} {season}: the composed real calendar differs from us_c46")
    rng = np.random.default_rng(np.random.SeedSequence([SEED_S47, VERSIONS.index(version), int(season[:4])]))
    finals = np.array([play(rng.choice(possible, size=len(real_days), replace=False)) for _ in range(N_CALENDARS)])
    row = {"version": version, "season": season, "n_refits": int(len(real_days)), "full_kelly": float(z["wealth_full"][-1]),
           "real": real, "random_median": float(np.median(finals)),
           "p_value": float(np.mean(finals >= real - 1e-15))}
    return row, [{"version": version, "season": season, "calendar": i, "final_capital": v} for i, v in enumerate(finals)]


def _write(path: Path, rows: list[dict]) -> None:
    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run_experiment(precompute_only: bool = False) -> None:
    seasons = pd.read_csv(RESULTS / "us_c46_strong_refit_seasons.csv")
    pairs = [(r.version, r.season) for r in seasons.itertuples() if r.n_refits > 0]
    tasks = []
    for version, season in pairs:
        z = np.load(RAW46 / f"{version}_{season}.npz")
        days, first = eligible_days(z["dates"])
        tasks += [(version, season, j) for j in range(first, len(days))]
    print(f"{len(pairs)} stagioni-versione, {len(tasks)} ristime da precalcolare", flush=True)
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        for k, status in enumerate(pool.map(precompute_one, tasks, chunksize=4), 1):
            if k % 50 == 0:
                print(f"  {k}/{len(tasks)}", flush=True)
    if precompute_only:
        return
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        out = list(pool.map(calendars_one, pairs))
    rows = [r for r, _ in out]
    cal = [x for _, rr in out for x in rr]
    _write(RESULTS / "us_c47_random_refit_seasons.csv", rows)
    _write(RESULTS / "us_c47_random_refit_calendars.csv", cal)
    s = pd.DataFrame(rows)
    c = pd.DataFrame(cal)
    summary = []
    for version in VERSIONS:
        sv = s[s["version"] == version].set_index("season")
        piv = np.log(c[c["version"] == version].pivot(index="calendar", columns="season", values="final_capital")[sv.index])
        joint = piv.sum(axis=1)
        obs = float(np.log(sv["real"]).sum())
        summary.append({"version": version, "seasons": len(sv), "joint_real": obs, "joint_random_median": float(joint.median()),
                        "joint_p_value": float((joint >= obs - 1e-12).mean()),
                        "seasons_above_random_median": int((sv["real"] > sv["random_median"]).sum())})
        for drop in sv.index:
            j = joint - piv[drop]
            o = obs - np.log(sv.loc[drop, "real"])
            summary.append({"version": version, "seasons": f"senza {drop}", "joint_real": o,
                            "joint_random_median": float(j.median()), "joint_p_value": float((j >= o - 1e-12).mean()),
                            "seasons_above_random_median": ""})
    _write(RESULTS / "us_c47_random_refit_summary.csv", summary)
    pd.set_option("display.width", 250)
    print(s.round(5).to_string())
    print(pd.DataFrame(summary).round(4).to_string())


if __name__ == "__main__":
    run_experiment(precompute_only="--precompute-only" in sys.argv)
