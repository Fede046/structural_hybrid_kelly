"""Script: popolazione di strategie con dinamica del replicatore (thesis/disegno_popolazione.md).

1. Esegue le strategie di shk.model.population_run senza puntata minima, sulle 3 stagioni di training
   e sulle 19 di validazione, stagione vera e ricostruite (seed di validazione dell'esecuzione congelata;
   seed del training da SEED_S21), e salva i percorsi del capitale in results/raw/us_c21_population_raw.npz
   (non versionato).
2. Sceglie μ sul training per ogni versione: la media sulle 3 stagioni della media su ricostruite di
   ln W della popolazione, sulla griglia MU_GRID.
3. Valuta sulla validazione e scrive:
   - results/us_c21_population_mu.csv, obiettivo sul training per versione e μ;
   - results/us_c21_population_summary.csv, per versione (e per strategia singola) e stagione;
   - results/us_c21_population_shares.csv, quote delle strategie nella stagione vera.
Versioni: "main" (strategie di POPULATION_ARMS, quote uguali a inizio stagione), "cash" (più la cassa),
"generations" e "generations_cash" (quote iniziali = finali della stagione precedente, μ della
versione senza generazioni).
Con --seeds N usa N seed e scrive in build/population/ (prova rapida).
"""

import csv
import math
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Final

import numpy as np

from shk.model.frozen_params import frozen_params_path, load_frozen_params
from shk.model.module1_seeds import s10_seed
from shk.model.module2_data import build_module2_frame
from shk.model.population import evolve, evolve_generations, gross_returns, with_cash
from shk.model.population_run import POPULATION_ARMS, population_setups, run_population_season
from shk.model.residuals import load_model_residuals
from shk.model.season_input import season_input_from_frame, training_seasons
from shk.model.validation_run import ValidationSeason, spawn_t55_sequences, validation_inputs

SEED_S21: Final[int] = 20261107
MU_GRID: Final[tuple[float, ...]] = (0.0, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1)
VERSIONS: Final[tuple[str, ...]] = ("main", "cash", "generations", "generations_cash")
WORKERS = 5
SUMMARY_COLUMNS: Final[tuple[str, ...]] = (
    "version", "season", "fit_through", "mu", "n_seeds", "observed_log_wealth", "median_log_wealth",
    "q05_log_wealth", "q95_log_wealth", "mean_log_wealth",
)
SHARE_COLUMNS: Final[tuple[str, ...]] = ("version", "season", "agent", "start_share", "mean_share", "end_share")
MU_COLUMNS: Final[tuple[str, ...]] = ("version", "mu", "objective", "selected")


def output_paths(quick: bool) -> dict[str, Path]:
    root = Path(__file__).resolve().parents[1]
    base = root / "build" / "population" if quick else root / "results"
    raw = base if quick else base / "raw"
    return {"raw": raw / "us_c21_population_raw.npz", "mu": base / "us_c21_population_mu.csv",
            "summary": base / "us_c21_population_summary.csv", "shares": base / "us_c21_population_shares.csv"}


def _returns(observed: np.ndarray, recs: np.ndarray, cash: bool) -> tuple[np.ndarray, np.ndarray]:
    ro, rr = gross_returns(observed), gross_returns(recs)
    return (with_cash(ro), with_cash(rr)) if cash else (ro, rr)


def _log_summary(obs_w: float, rec_w: np.ndarray) -> dict[str, float]:
    lw = np.log(rec_w)
    return {"observed_log_wealth": math.log(obs_w), "median_log_wealth": float(np.median(lw)),
            "q05_log_wealth": float(np.quantile(lw, 0.05)), "q95_log_wealth": float(np.quantile(lw, 0.95)),
            "mean_log_wealth": float(lw.mean())}


def select_mu(train_runs: list[tuple[np.ndarray, np.ndarray, int]]) -> tuple[dict[str, float], list[dict]]:
    """μ per "main" e "cash" sul training (vedi modulo); le versioni con generazioni usano lo stesso μ."""
    rows, chosen = [], {}
    for version, cash in (("main", False), ("cash", True)):
        objective = []
        for mu in MU_GRID:
            vals = [evolve(_returns(o, r, cash)[1], mu)[1][..., -1] for o, r, _ in train_runs]
            objective.append(float(np.mean([np.log(v).mean() for v in vals])))
        best = MU_GRID[int(np.argmax(objective))]
        chosen[version] = chosen[f"generations{'_cash' if cash else ''}"] = best
        rows += [{"version": version, "mu": mu, "objective": obj, "selected": mu == best}
                 for mu, obj in zip(MU_GRID, objective)]
    return chosen, rows


def evaluate(val_seasons: list[ValidationSeason], val_runs: list[tuple[np.ndarray, np.ndarray, int]],
             mus: dict[str, float]) -> tuple[list[dict], list[dict]]:
    """Righe di sintesi e delle quote sulla validazione."""
    summary, shares_rows = [], []
    n_seeds = val_runs[0][1].shape[0]
    for s, (obs, recs, _) in zip(val_seasons, val_runs):
        for ai, arm in enumerate(POPULATION_ARMS):
            summary.append({"version": f"member:{arm}", "season": s.inp.season, "fit_through": s.fit, "mu": "",
                            "n_seeds": n_seeds, **_log_summary(float(obs[ai, -1]), recs[:, ai, -1])})
    for version in VERSIONS:
        cash, mu = version.endswith("cash"), mus[version]
        names = list(POPULATION_ARMS) + (["cash"] if cash else [])
        rets = [_returns(o, r, cash) for o, r, _ in val_runs]
        if version.startswith("generations"):
            obs_out = evolve_generations([ro for ro, _ in rets], mu)
            rec_out = evolve_generations([rr for _, rr in rets], mu)
        else:
            obs_out = [evolve(ro, mu) for ro, _ in rets]
            rec_out = [evolve(rr, mu) for _, rr in rets]
        for s, (osh, ow), (_, rw) in zip(val_seasons, obs_out, rec_out):
            summary.append({"version": version, "season": s.inp.season, "fit_through": s.fit, "mu": mu,
                            "n_seeds": n_seeds, **_log_summary(float(ow[-1]), rw[..., -1])})
            for ai, name in enumerate(names):
                shares_rows.append({"version": version, "season": s.inp.season, "agent": name,
                                    "start_share": float(osh[ai, 0]), "mean_share": float(osh[ai, :-1].mean()),
                                    "end_share": float(osh[ai, -1])})
    return summary, shares_rows


def _write(path: Path, columns: tuple[str, ...], rows: list[dict]) -> None:
    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(columns))
        writer.writeheader()
        writer.writerows(rows)


def run_experiment(n_seeds: int | None = None) -> None:
    paths = output_paths(quick=n_seeds is not None)
    for p in paths.values():
        p.parent.mkdir(parents=True, exist_ok=True)
    params_path = frozen_params_path()
    params = load_frozen_params(params_path)
    n = int(params.fixed["n_seeds"]) if n_seeds is None else n_seeds
    covariates = list(params.fixed["covariates"])
    frame = build_module2_frame(load_model_residuals())
    train = frame[frame["role"] == "training"]
    setups = population_setups(train, params)

    train_seasons = [ValidationSeason(season_input_from_frame(train, s, covariates), s) for s in training_seasons(train)]
    train_seqs = [q.spawn(n) for q in np.random.SeedSequence(SEED_S21).spawn(len(train_seasons))]
    val_seasons = validation_inputs(frame, covariates)
    val_seqs = spawn_t55_sequences(len(val_seasons), n, s10_seed())

    seasons = train_seasons + val_seasons
    seqs = train_seqs + val_seqs
    args = [(str(params_path), setups, s, q) for s, q in zip(seasons, seqs)]
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        runs = list(pool.map(run_population_season, *zip(*args)))
    train_runs, val_runs = runs[:len(train_seasons)], runs[len(train_seasons):]

    raw = {"agents": np.array(POPULATION_ARMS)}
    for s, (obs, recs, l_pw) in zip(seasons, runs):
        key = s.inp.season.replace("-", "_")
        raw[f"observed_{key}"], raw[f"reconstructed_{key}"] = obs, recs
    np.savez_compressed(paths["raw"], **raw)

    mus, mu_rows = select_mu(train_runs)
    summary, share_rows = evaluate(val_seasons, val_runs, mus)
    _write(paths["mu"], MU_COLUMNS, mu_rows)
    _write(paths["summary"], SUMMARY_COLUMNS, summary)
    _write(paths["shares"], SHARE_COLUMNS, share_rows)

    print("mu:", mus)
    by: dict[str, list[float]] = {}
    for row in summary:
        by.setdefault(row["version"], []).append(row["observed_log_wealth"])
    for version, vals in by.items():
        print(f"{version:<24} typical capital {math.exp(np.mean(vals)):.3f}")


if __name__ == "__main__":
    argv = sys.argv[1:]
    seeds_ = int(argv[argv.index("--seeds") + 1]) if "--seeds" in argv else None
    run_experiment(seeds_)
