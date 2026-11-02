"""Schema del relatore (C3, C3_stop) sulle 19 stagioni di validazione, accanto all'esecuzione congelata.

Gli agenti di agent_c.SchemeAgent si aggiungono dopo il congelamento e non toccano
config/frozen_params.toml né le uscite dell'esecuzione congelata. Dal file congelato prendono:
W = c1_window e κ = c1_kappa (C3 è la versione dello schema del relatore di C1: cambiano solo
l'allarme e la risposta), la soglia di C1 del fit come soglia della componente strutturale,
λ base = c0_lambda, politica del ripiego e configurazioni. Le sole quantità nuove sono le soglie
dell'allarme ANOVA, calibrate sul training (scheme_thresholds) come la soglia di C1: serie di δ
del fit, lunghezza di blocco L_PW, B = 999.

Seed delle soglie: story_task_sequence(SEED_S12, posizione del Modulo 1, N_STORY_TASKS), poi
spawn(numero di fit) in ordine cronologico. Seed delle stagioni: gli stessi dell'esecuzione
congelata (spawn_t55_sequences dalla radice s10_seed del Modulo 1), quindi le esecuzioni sono
appaiate con quelle congelate; B_0.25 e C1 si rieseguono come riferimento e coincidono con
l'esecuzione congelata.
"""

from collections.abc import Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from shk.kelly.agents import AGENT_B_LAMBDAS, Agent, FractionalKellyAgent
from shk.kelly.environment import run_paired_backtest
from shk.model.agent_c import (
    SCHEME_STOP_CLEAR,
    SCHEME_STOP_SEASON,
    C1Agent,
    Module2Supervisor,
    SchemeAgent,
    calibrate_scheme_thresholds,
)
from shk.model.frozen_agents import check_frozen_constants
from shk.model.frozen_params import FrozenParams, load_frozen_params
from shk.model.module1 import MODULE1_IDS, check_module1
from shk.model.module3_synthetic import N_STORY_TASKS
from shk.model.paired_backtest import CONFIGURATIONS
from shk.model.season_bootstrap import reconstruct_season, season_block_length
from shk.model.task_seeds import story_task_sequence
from shk.model.training_agents import SeasonInput, season_input_from_frame, training_seasons
from shk.model.validation_run import (
    METRICS,
    SEED_S10,
    ValidationResult,
    ValidationSeason,
    run_metrics,
    spawn_t55_sequences,
    validation_inputs,
)
from shk.stats.bootstrap import optimal_block_length, round_block_length

SEED_S12: Final[int] = 20261102
SCHEME_ARMS: Final[tuple[str, ...]] = ("B_0.25", "C1", "C3", "C3_stop")
THRESHOLD_COLUMNS: Final[tuple[str, ...]] = (
    "fit", "window", "block_length", "mean_threshold", "dispersion_threshold", "structural_threshold",
)


def scheme_window(params: FrozenParams) -> int:
    """W di C3: quella congelata di C1."""
    return int(params.calibrated["c1_window"])


def scheme_thresholds(train: pd.DataFrame, params: FrozenParams,
                      seed: int | np.random.SeedSequence = SEED_S12) -> dict[str, tuple[float, float]]:
    """Soglie (media, dispersione) dell'allarme di C3 per fit, sulle stagioni di training (vedi modulo)."""
    covariates = list(params.fixed["covariates"])
    inputs = [season_input_from_frame(train, s, covariates) for s in training_seasons(train)]
    position = MODULE1_IDS.index(check_module1(params.module1))
    gens = story_task_sequence(seed, position, N_STORY_TASKS).spawn(len(inputs))
    w = scheme_window(params)
    return {inp.season: calibrate_scheme_thresholds(inp.delta, w, _fit_block_length(inp), np.random.default_rng(g))
            for inp, g in zip(inputs, gens)}


def _fit_block_length(inp: SeasonInput) -> int:
    return round_block_length(optimal_block_length(inp.delta).circular)


def threshold_records(train: pd.DataFrame, params: FrozenParams,
                      thresholds: Mapping[str, tuple[float, float]]) -> list[dict[str, object]]:
    """Righe del CSV delle soglie di C3, una per fit."""
    covariates = list(params.fixed["covariates"])
    out = []
    for fit, (mean_thr, disp_thr) in thresholds.items():
        inp = season_input_from_frame(train, fit, covariates)
        out.append({"fit": fit, "window": scheme_window(params), "block_length": _fit_block_length(inp),
                    "mean_threshold": mean_thr, "dispersion_threshold": disp_thr,
                    "structural_threshold": float(params.c1_thresholds[fit])})
    return out


def build_scheme_agents(params: FrozenParams, thresholds: Mapping[str, tuple[float, float]],
                        supervisor: Module2Supervisor, fit: str, arms: Sequence[str] = SCHEME_ARMS) -> list[Agent]:
    """Agenti di SCHEME_ARMS: B_0.25 e C1 come nell'esecuzione congelata, C3 e C3_stop."""
    c, f = params.calibrated, params.fixed
    kappa, base = float(c["c1_kappa"]), float(f["c0_lambda"])
    structural = float(params.c1_thresholds[fit])
    mean_thr, disp_thr = thresholds[fit]

    def scheme(name: str, stop: str) -> SchemeAgent:
        return SchemeAgent(name, supervisor, kappa, mean_thr, disp_thr, structural, stop, base_lambda=base)

    builders = {
        "B_0.25": lambda: FractionalKellyAgent("B_0.25", lam=AGENT_B_LAMBDAS[0]),
        "C1": lambda: C1Agent("C1", supervisor, kappa, structural, base_lambda=base),
        "C3": lambda: scheme("C3", SCHEME_STOP_CLEAR),
        "C3_stop": lambda: scheme("C3_stop", SCHEME_STOP_SEASON),
    }
    return [builders[a]() for a in arms]


def run_scheme_instance(params: FrozenParams, thresholds: Mapping[str, tuple[float, float]], inp: SeasonInput,
                        fit: str, arms: Sequence[str] = SCHEME_ARMS) -> np.ndarray:
    """Una stagione nelle tre configurazioni: (C, len(arms), M); supervisore condiviso fra le configurazioni."""
    supervisor = Module2Supervisor(inp.season, inp.dates, inp.x, list(params.fixed["covariates"]),
                                   scheme_window(params))
    out = np.full((len(CONFIGURATIONS), len(arms), len(METRICS)), np.nan)
    for ci, (_, min_stake) in enumerate(CONFIGURATIONS):
        agents = build_scheme_agents(params, thresholds, supervisor, fit, arms)
        runs = run_paired_backtest(agents, inp.dates, inp.probs, inp.odds, inp.outcomes, min_stake,
                                   fallback_policy=params.fixed["fallback_policy"])
        for run, agent in zip(runs, agents):
            out[ci, list(arms).index(run.name)] = run_metrics(run, agent)
    return out


def run_scheme_season(params_path: str, thresholds: Mapping[str, tuple[float, float]], season: ValidationSeason,
                      seed_seqs: Sequence[np.random.SeedSequence]) -> tuple[np.ndarray, np.ndarray, int]:
    """Seed e realizzazione osservata di una stagione: (seed (C, A, M, N), osservata (C, A, M), L_PW)."""
    params = load_frozen_params(params_path)
    check_frozen_constants(params)
    covariates = list(params.fixed["covariates"])
    l_pw = season_block_length(season.inp)
    seeds = np.full((len(CONFIGURATIONS), len(SCHEME_ARMS), len(METRICS), len(seed_seqs)), np.nan)
    for k, ss in enumerate(seed_seqs):
        rec = reconstruct_season(season.inp, np.random.default_rng(ss), l_pw, covariates=covariates)
        seeds[..., k] = run_scheme_instance(params, thresholds, rec, season.fit)
    observed = run_scheme_instance(params, thresholds, season.inp, season.fit)
    return seeds, observed, l_pw


def evaluate_scheme(frame: pd.DataFrame, params_path: Path | str, thresholds: Mapping[str, tuple[float, float]],
                    n_seeds: int | None = None, workers: int = 1,
                    seed: int | np.random.SeedSequence = SEED_S10,
                    seasons: Sequence[str] | None = None) -> ValidationResult:
    """Stagioni di validazione (tutte, o quelle date) con gli stessi seed dell'esecuzione congelata."""
    params = load_frozen_params(params_path)
    check_frozen_constants(params)
    all_seasons = validation_inputs(frame, list(params.fixed["covariates"]))
    n = int(params.fixed["n_seeds"]) if n_seeds is None else n_seeds
    seqs = spawn_t55_sequences(len(all_seasons), n, seed)
    chosen = [(s, q) for s, q in zip(all_seasons, seqs) if seasons is None or s.inp.season in seasons]
    args = [(str(params_path), dict(thresholds), s, q) for s, q in chosen]
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            outputs = list(pool.map(run_scheme_season, *zip(*args)))
    else:
        outputs = [run_scheme_season(*a) for a in args]
    return ValidationResult(
        seasons=tuple(s.inp.season for s, _ in chosen),
        fits=tuple(s.fit for s, _ in chosen),
        n_dates=np.array([np.unique(s.inp.dates).shape[0] for s, _ in chosen]),
        l_pw=np.array([o[2] for o in outputs]),
        seeds=np.stack([o[0] for o in outputs]),
        observed=np.stack([o[1] for o in outputs]),
    )

