"""Script: evoluzione delle strategie con le scelte della versione principale fra i geni (rifà us_c22).

Come us_c22 (N_RUNS evoluzioni indipendenti di N_GENOMES genomi, una generazione per stagione dal
2002-03 al 2022-23, stagione vera senza puntata minima, varianti "free" e "fixed_lam_0.25"), ma con il
genoma di shk.model.evolution_main: due geni in più, soglie dell'allarme ("day" o "season") e diagnosi
("three" o "two"), attivi con il supervisore che confronta con la stagione di calibrazione. Nessun
parametro è scelto sui dati; i seed sono nuovi (SEED_S32).

Scrive results/us_c32_main_evolution_genomes.csv (un genoma per riga) e
results/us_c32_main_evolution_seasons.csv (evoluzione × stagione: ln W della popolazione e del
campione, geni medi, quota di genomi con le scelte della versione principale). Con --runs R usa R
evoluzioni e scrive in build/main_evolution/ (prova rapida).
"""

import csv
import math
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Final

import numpy as np

from shk.model.evolution_main import MainGenome, next_generation, random_genome, season_log_wealth
from shk.model.frozen_params import frozen_params_path, load_frozen_params
from shk.model.main_version import main_setups
from shk.model.module2_data import build_module2_frame
from shk.model.population_run import population_setups
from shk.model.residuals import load_model_residuals
from shk.model.validation_run import validation_inputs

SEED_S32: Final[int] = 20261117
N_RUNS: Final[int] = 30
N_GENOMES: Final[int] = 20
VARIANTS: Final[tuple[tuple[str, float | None], ...]] = (("free", None), ("fixed_lam_0.25", 0.25))
GENOME_COLUMNS: Final[tuple[str, ...]] = ("variant", "run", "season", "fit_through", "index", "lam", "kappa",
                                          "supervisor", "stop", "rule", "thresholds", "diagnosis", "log_wealth")
SEASON_COLUMNS: Final[tuple[str, ...]] = (
    "variant", "run", "season", "fit_through", "population_log_wealth", "champion_log_wealth", "mean_lam",
    "share_supervised", "share_calibration", "share_stop_season", "share_r3", "share_season_thresholds",
    "share_two_fold", "share_main",
)


def output_paths(quick: bool) -> tuple[Path, Path]:
    root = Path(__file__).resolve().parents[1]
    base = root / "build" / "main_evolution" if quick else root / "results"
    return base / "us_c32_main_evolution_genomes.csv", base / "us_c32_main_evolution_seasons.csv"


def _share(pop: list[MainGenome], test) -> float:
    return float(np.mean([test(g) for g in pop]))


def run_experiment(n_runs: int = N_RUNS) -> None:
    genomes_path, seasons_path = output_paths(quick=n_runs != N_RUNS)
    genomes_path.parent.mkdir(parents=True, exist_ok=True)
    params = load_frozen_params(frozen_params_path())
    frame = build_module2_frame(load_model_residuals())
    train = frame[frame["role"] == "training"]
    previous, main = population_setups(train, params), main_setups(train, params)
    seasons = validation_inputs(frame, list(params.fixed["covariates"]))

    genome_rows, season_rows = [], []
    for vi, (variant, fixed_lam) in enumerate(VARIANTS):
        rngs = [np.random.default_rng(s) for s in np.random.SeedSequence([SEED_S32, vi]).spawn(n_runs)]
        pops: list[list[MainGenome]] = [[random_genome(rng, fixed_lam) for _ in range(N_GENOMES)] for rng in rngs]
        for k, s in enumerate(seasons):
            t0 = time.time()
            flat = [g for pop in pops for g in pop]
            lw = season_log_wealth(params, previous, main, s.inp, s.fit, flat).reshape(n_runs, N_GENOMES)
            for r, pop in enumerate(pops):
                for i, g in enumerate(pop):
                    genome_rows.append({"variant": variant, "run": r, "season": s.inp.season, "fit_through": s.fit,
                                        "index": i, **asdict(g), "log_wealth": lw[r, i]})
                calib = [g for g in pop if g.supervisor == "calibration"]
                season_rows.append({
                    "variant": variant, "run": r, "season": s.inp.season, "fit_through": s.fit,
                    "population_log_wealth": math.log(float(np.exp(lw[r]).mean())),
                    "champion_log_wealth": lw[r, 0] if k > 0 else "",
                    "mean_lam": float(np.mean([g.lam for g in pop])),
                    "share_supervised": _share(pop, lambda g: g.supervisor != "none"),
                    "share_calibration": _share(pop, lambda g: g.supervisor == "calibration"),
                    "share_stop_season": _share(pop, lambda g: g.supervisor != "none" and g.stop == "season"),
                    "share_r3": _share(pop, lambda g: g.rule == "R3"),
                    "share_season_thresholds": _share(calib, lambda g: g.thresholds == "season") if calib else "",
                    "share_two_fold": _share(calib, lambda g: g.diagnosis == "two") if calib else "",
                    "share_main": _share(pop, MainGenome.is_main),
                })
            pops = [next_generation(pop, lw[r], rngs[r], fixed_lam) for r, pop in enumerate(pops)]
            print(f"{variant} {s.inp.season}: {len(set(flat))} genomi distinti, {time.time() - t0:.1f} s", flush=True)

    for path, cols, rows in ((genomes_path, GENOME_COLUMNS, genome_rows), (seasons_path, SEASON_COLUMNS, season_rows)):
        with open(path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(cols))
            writer.writeheader()
            writer.writerows(rows)

    last = seasons[-1].inp.season
    for variant, _ in VARIANTS:
        rows = [row for row in season_rows if row["variant"] == variant]
        pop_typ = [math.exp(np.mean([row["population_log_wealth"] for row in rows if row["run"] == r]))
                   for r in range(n_runs)]
        print(f"{variant:<16} popolazione: capitale tipico mediano {np.median(pop_typ):.3f} "
              f"(5-95%: {np.quantile(pop_typ, 0.05):.3f}-{np.quantile(pop_typ, 0.95):.3f})")
        end = [row for row in rows if row["season"] == last]
        for col in ("mean_lam", "share_supervised", "share_calibration", "share_stop_season", "share_r3",
                    "share_season_thresholds", "share_two_fold", "share_main"):
            vals = [row[col] for row in end if row[col] != ""]
            print(f"  {last} {col:<24} media {np.mean(vals):.2f}" if vals else f"  {last} {col:<24} -")


if __name__ == "__main__":
    argv = sys.argv[1:]
    run_experiment(int(argv[argv.index("--runs") + 1]) if "--runs" in argv else N_RUNS)
