"""Script: evoluzione delle strategie con variazione, selezione ed ereditarietà (thesis/disegno_popolazione.md §9).

Per ciascuna di N_RUNS evoluzioni indipendenti (seed da SEED_S22): N_GENOMES genomi casuali
(shk.model.evolution.random_genome) giocano la prima stagione di validazione (2002-03), la metà
migliore sopravvive e genera figli mutati, la nuova generazione gioca la stagione successiva, e così
fino al 2022-23. Ogni stagione si gioca sulla stagione vera, senza puntata minima, partendo da
capitale 1 (shk.model.evolution_run). Nessun parametro è scelto sui dati.

Misure per stagione e per evoluzione:
- popolazione: capitale finale della generazione con il capitale diviso in parti uguali fra i genomi
  (media dei W finali), cioè quanto ottiene chi segue l'evoluzione senza sapere quale genoma vincerà;
- campione: il genoma migliore della stagione precedente (dalla seconda stagione).

Due varianti: "free" (lam evolve) e "fixed_lam_0.25" (lam fisso al quarto di Kelly: si deve
puntare, evolvono supervisore, kappa, stop e regola).

Scrive results/us_c22_evolution_genomes.csv (un genoma per riga: evoluzione, stagione, geni, ln W)
e results/us_c22_evolution_seasons.csv (evoluzione, stagione: ln W della popolazione e del campione,
geni medi). Con --runs R usa R evoluzioni e scrive in build/evolution/ (prova rapida).
"""

import csv
import math
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Final

import numpy as np

from shk.model.evolution import Genome, next_generation, random_genome
from shk.model.evolution_run import season_log_wealth
from shk.model.frozen_params import frozen_params_path, load_frozen_params
from shk.model.module2_data import build_module2_frame
from shk.model.population_run import population_setups
from shk.model.residuals import load_model_residuals
from shk.model.validation_run import validation_inputs

SEED_S22: Final[int] = 20261110
N_RUNS: Final[int] = 30
N_GENOMES: Final[int] = 20
VARIANTS: Final[tuple[tuple[str, float | None], ...]] = (("free", None), ("fixed_lam_0.25", 0.25))
GENOME_COLUMNS: Final[tuple[str, ...]] = ("variant", "run", "season", "fit_through", "index", "lam", "kappa", "supervisor",
                                          "stop", "rule", "log_wealth")
SEASON_COLUMNS: Final[tuple[str, ...]] = ("variant", "run", "season", "fit_through", "population_log_wealth",
                                          "champion_log_wealth", "mean_lam", "share_supervised",
                                          "share_calibration", "share_stop_season", "share_r3")


def output_paths(quick: bool) -> tuple[Path, Path]:
    root = Path(__file__).resolve().parents[1]
    base = root / "build" / "evolution" if quick else root / "results"
    return base / "us_c22_evolution_genomes.csv", base / "us_c22_evolution_seasons.csv"


def run_experiment(n_runs: int = N_RUNS) -> None:
    genomes_path, seasons_path = output_paths(quick=n_runs != N_RUNS)
    genomes_path.parent.mkdir(parents=True, exist_ok=True)
    params = load_frozen_params(frozen_params_path())
    frame = build_module2_frame(load_model_residuals())
    setups = population_setups(frame[frame["role"] == "training"], params)
    seasons = validation_inputs(frame, list(params.fixed["covariates"]))

    genome_rows, season_rows = [], []
    for vi, (variant, fixed_lam) in enumerate(VARIANTS):
        seeds = np.random.SeedSequence([SEED_S22, vi]).spawn(n_runs)
        rngs = [np.random.default_rng(s) for s in seeds]
        pops: list[list[Genome]] = [[random_genome(rng, fixed_lam) for _ in range(N_GENOMES)] for rng in rngs]
        for k, s in enumerate(seasons):
            t0 = time.time()
            flat = [g for pop in pops for g in pop]
            lw = season_log_wealth(params, setups, s.inp, s.fit, flat).reshape(n_runs, N_GENOMES)
            for r, pop in enumerate(pops):
                for i, g in enumerate(pop):
                    genome_rows.append({"variant": variant, "run": r, "season": s.inp.season, "fit_through": s.fit,
                                        "index": i, **asdict(g), "log_wealth": lw[r, i]})
                season_rows.append({
                    "variant": variant, "run": r, "season": s.inp.season, "fit_through": s.fit,
                    "population_log_wealth": math.log(float(np.exp(lw[r]).mean())),
                    "champion_log_wealth": lw[r, 0] if k > 0 else "",
                    "mean_lam": float(np.mean([g.lam for g in pop])),
                    "share_supervised": float(np.mean([g.supervisor != "none" for g in pop])),
                    "share_calibration": float(np.mean([g.supervisor == "calibration" for g in pop])),
                    "share_stop_season": float(np.mean([g.supervisor != "none" and g.stop == "season" for g in pop])),
                    "share_r3": float(np.mean([g.rule == "R3" for g in pop])),
                })
            pops = [next_generation(pop, lw[r], rngs[r], fixed_lam) for r, pop in enumerate(pops)]
            print(f"{variant} {s.inp.season}: {len(set(flat))} genomi distinti, {time.time() - t0:.1f} s", flush=True)

    for path, cols, rows in ((genomes_path, GENOME_COLUMNS, genome_rows), (seasons_path, SEASON_COLUMNS, season_rows)):
        with open(path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(cols))
            writer.writeheader()
            writer.writerows(rows)

    for variant, _ in VARIANTS:
        rows = [row for row in season_rows if row["variant"] == variant]
        pop_typ = [math.exp(np.mean([row["population_log_wealth"] for row in rows if row["run"] == r]))
                   for r in range(n_runs)]
        champ_typ = [math.exp(np.mean([row["champion_log_wealth"] for row in rows
                                       if row["run"] == r and row["champion_log_wealth"] != ""]))
                     for r in range(n_runs)]
        for label, vals in (("popolazione", pop_typ), ("campione", champ_typ)):
            print(f"{variant:<16} {label:<12} capitale tipico mediano {np.median(vals):.3f} "
                  f"(5-95%: {np.quantile(vals, 0.05):.3f}-{np.quantile(vals, 0.95):.3f})")

if __name__ == "__main__":
    argv = sys.argv[1:]
    run_experiment(int(argv[argv.index("--runs") + 1]) if "--runs" in argv else N_RUNS)
