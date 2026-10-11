"""Analisi di potenza per il numero di seed di S10 (T53, nota 3.2 §7.3).

Sulle tre stagioni di training, per ogni seed (stagione ricostruita per stationary bootstrap
delle date con L_PW, season_bootstrap.reconstruct_season) si esegue l'ambiente con gli
agenti dell'esecuzione di prova di T52 (training_agents.run_training_season: W = 80,
κ = 0.5, soglia di C1 del fit a L_PW) nella configurazione principale B0/F = 22 000
(£0.01 su £220). Differenze appaiate sulla log-ricchezza finale: d1 = C1 − C0 e
d2 = C2 − C1.

Regola del passo 4 (fissata nel task, non si cambia dopo il risultato):
- σ_s = deviazione standard fra seed di d2 nella stagione s; σ² = media delle σ_s² sulle
  tre stagioni (le stagioni di validazione si suppongono simili a quelle di training);
- Δ = |media di d1 su seed e stagioni|;
- semiampiezza al 95% della differenza C2 − C1 pooled su 19 stagioni con N seed per
  stagione (stagioni come cluster indipendenti, variabilità interna dai seed, decisione
  S10): z·σ/sqrt(19·N), con z = quantile 0.975 della normale;
- N_SEEDS = minimo multiplo di 100 con semiampiezza ≤ 0.2·Δ, cioè 100·ceil(N_min/100) con
  N_min = (z·σ/(0.2·Δ))²/19; se Δ < 1e-6 o N_SEEDS > 5 000, N_SEEDS = 1 000; in ogni caso
  N_SEEDS ≥ 500.

Seed: SeedSequence(SEED_S9).spawn(5)[3] (T53 in posizione 3), spawn(numero di stagioni) in
ordine cronologico, spawn(N_POWER_SEEDS) per seed. Il tempo per esecuzione si misura
dentro evaluate_power, perché il task chiede nel CSV il tempo stimato del run di S10:
(N_SEEDS + 1)·19·3 esecuzioni (seed più realizzazione osservata, tre configurazioni).
"""

import math
import time
from collections.abc import Sequence
from typing import Final

import numpy as np
import pandas as pd
import scipy.stats

from shk.model.module3_synthetic import N_STORY_TASKS, SEED_S9
from shk.model.paired_backtest import CONFIGURATIONS
from shk.model.season_bootstrap import reconstruct_season, season_block_length
from shk.model.training_agents import (
    PROVISIONAL_WINDOW,
    run_training_season,
    season_input_from_frame,
    threshold_records,
    training_seasons,
)

T53_STORY_POSITION: Final[int] = 3
N_POWER_SEEDS: Final[int] = 200
N_VALIDATION_SEASONS: Final[int] = 19
POWER_CONFIG: Final[str] = "gbp_0.01"
EFFECT_FRACTION: Final[float] = 0.2
SEED_MULTIPLE: Final[int] = 100
MIN_SEEDS: Final[int] = 500
MAX_SEEDS: Final[int] = 5000
FALLBACK_SEEDS: Final[int] = 1000
MIN_EFFECT: Final[float] = 1e-6
Z_95: Final[float] = float(scipy.stats.norm.ppf(0.975))
POWER_AGENTS: Final[tuple[str, ...]] = ("C0", "C1", "C2_global", "C2")

POWER_CSV_COLUMNS: Final[tuple[str, ...]] = (
    "row_type", "season", "seed_index", "n_dates", "l_pw", "n_matches",
    "lw_c0", "lw_c1", "lw_c2_global", "lw_c2", "diff_c1_c0", "diff_c2_c1", "any_ruined",
    "n_seeds_power", "mean_c1_c0", "sd_c1_c0", "mean_c2_c1", "sd_c2_c1",
    "z", "effect_fraction", "n_validation_seasons", "n_min", "n_seeds", "n_seeds_rule", "half_width",
    "seconds_per_run", "s10_runs", "s10_hours",
)
TIMING_COLUMNS: Final[tuple[str, ...]] = ("seconds_per_run", "s10_hours")


def spawn_t53_generators(seasons: Sequence[str], n_seeds: int = N_POWER_SEEDS,
                         seed: int = SEED_S9) -> dict[str, list[np.random.Generator]]:
    """Un generatore per seed e stagione (vedi modulo)."""
    if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)):
        raise TypeError(f"seed must be an integer, got {type(seed).__name__}")
    task = np.random.SeedSequence(seed).spawn(N_STORY_TASKS)[T53_STORY_POSITION]
    return {s: [np.random.default_rng(c) for c in s_seq.spawn(n_seeds)]
            for s, s_seq in zip(seasons, task.spawn(len(seasons)))}


def n_seeds_rule(sd_c2_c1: float, mean_c1_c0: float, n_seasons: int = N_VALIDATION_SEASONS) -> tuple[float, int, str]:
    """Regola del passo 4: (N_min, N_SEEDS, motivo) con motivo "rule", "small_effect" o "too_large"."""
    effect = abs(mean_c1_c0)
    if effect < MIN_EFFECT:
        return math.nan, FALLBACK_SEEDS, "small_effect"
    n_min = (Z_95 * sd_c2_c1 / (EFFECT_FRACTION * effect)) ** 2 / n_seasons
    n_seeds = SEED_MULTIPLE * max(1, math.ceil(n_min / SEED_MULTIPLE))
    if n_seeds > MAX_SEEDS:
        return n_min, FALLBACK_SEEDS, "too_large"
    return n_min, max(MIN_SEEDS, n_seeds), "rule"


def _empty() -> dict[str, object]:
    return {c: "" for c in POWER_CSV_COLUMNS}


def evaluate_power(frame: pd.DataFrame, covariates: Sequence[str], seed: int = SEED_S9,
                   n_seeds: int = N_POWER_SEEDS) -> list[dict[str, object]]:
    """Seed ricostruiti, differenze appaiate, regola di N_SEEDS e stima del tempo di S10.

    Solleva
    -------
    ValueError
        Se il DataFrame contiene righe non di training.
    """
    if set(frame["role"]) != {"training"}:
        raise ValueError("frame must contain training rows only")
    min_stake = dict(CONFIGURATIONS)[POWER_CONFIG]
    inputs = [season_input_from_frame(frame, s, covariates) for s in training_seasons(frame)]
    _, thresholds = threshold_records(inputs)
    gens = spawn_t53_generators([inp.season for inp in inputs], n_seeds, seed)
    records: list[dict[str, object]] = []
    variances_d1, variances_d2, means_d1, means_d2 = [], [], [], []
    elapsed, n_runs = 0.0, 0
    for inp in inputs:
        l_pw = season_block_length(inp)
        n_dates = int(np.unique(inp.dates).shape[0])
        d1, d2 = [], []
        for i, rng in enumerate(gens[inp.season]):
            rec_season = reconstruct_season(inp, rng, l_pw, covariates=covariates)
            t0 = time.perf_counter()
            runs, _ = run_training_season(rec_season, covariates, min_stake,
                                          thresholds[(inp.season, PROVISIONAL_WINDOW)])
            elapsed += time.perf_counter() - t0
            n_runs += 1
            by_name = {r.name: r for r in runs}
            final = {a: float(by_name[a].wealth[0, -1]) for a in POWER_AGENTS}
            lw = {a: math.log(w) if w > 0.0 else -math.inf for a, w in final.items()}
            any_ruined = any(bool(by_name[a].ruined[0]) for a in POWER_AGENTS)
            d1.append(lw["C1"] - lw["C0"])
            d2.append(lw["C2"] - lw["C1"])
            records.append({**_empty(), "row_type": "seed", "season": inp.season, "seed_index": i,
                            "n_dates": n_dates, "l_pw": l_pw, "n_matches": int(rec_season.dates.shape[0]),
                            "lw_c0": lw["C0"], "lw_c1": lw["C1"], "lw_c2_global": lw["C2_global"], "lw_c2": lw["C2"],
                            "diff_c1_c0": d1[-1], "diff_c2_c1": d2[-1], "any_ruined": any_ruined})
        a1, a2 = np.array(d1), np.array(d2)
        variances_d1.append(float(np.var(a1, ddof=1)))
        variances_d2.append(float(np.var(a2, ddof=1)))
        means_d1.append(float(a1.mean()))
        means_d2.append(float(a2.mean()))
        records.append({**_empty(), "row_type": "season", "season": inp.season, "n_dates": n_dates, "l_pw": l_pw,
                        "n_seeds_power": n_seeds, "mean_c1_c0": means_d1[-1], "sd_c1_c0": math.sqrt(variances_d1[-1]),
                        "mean_c2_c1": means_d2[-1], "sd_c2_c1": math.sqrt(variances_d2[-1])})
    sd1, sd2 = math.sqrt(float(np.mean(variances_d1))), math.sqrt(float(np.mean(variances_d2)))
    mean1, mean2 = float(np.mean(means_d1)), float(np.mean(means_d2))
    n_min, n_final, rule = n_seeds_rule(sd2, mean1)
    seconds = elapsed / n_runs
    s10_runs = (n_final + 1) * N_VALIDATION_SEASONS * len(CONFIGURATIONS)
    records.append({**_empty(), "row_type": "pooled", "n_seeds_power": n_seeds, "mean_c1_c0": mean1, "sd_c1_c0": sd1,
                    "mean_c2_c1": mean2, "sd_c2_c1": sd2, "z": Z_95, "effect_fraction": EFFECT_FRACTION,
                    "n_validation_seasons": N_VALIDATION_SEASONS, "n_min": n_min, "n_seeds": n_final,
                    "n_seeds_rule": rule,
                    "half_width": Z_95 * sd2 / math.sqrt(N_VALIDATION_SEASONS * n_final),
                    "seconds_per_run": seconds, "s10_runs": s10_runs, "s10_hours": s10_runs * seconds / 3600.0})
    return records
