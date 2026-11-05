"""Esecuzione appaiata congelata sulle 19 stagioni di validazione.

Parametri solo da config/frozen_params.toml (load_frozen_params; costanti interne verificate
con check_frozen_constants). Agenti in AGENT_ORDER (A e B_0.25), configurazioni
CONFIGURATIONS (F = 0, £0.01, £1). Lo schema del relatore si esegue sugli stessi seed in
shk.model.scheme_run.

Seed (decisione di progetto): stagione ricostruita per stationary bootstrap delle date a L_PW della
serie per data della media di δ della stagione. Gli stessi seed per tutti gli agenti
e le configurazioni. In più la realizzazione osservata. SEED_S10 = 20261014 (definito qui, primo modulo che lo usa):
SeedSequence(SEED_S10).spawn(5)[0] (posizione 0), spawn(19) per stagione in ordine
cronologico, spawn(N_SEEDS) per seed.

Metriche per agente (METRICS): log-ricchezza finale (−inf se W_T = 0), rovina e indice
della data di rovina (−1 se nessuna), drawdown massimo, tempo di recupero con la censura
(se il picco non è recuperato vale D − t*, durata osservata senza recupero, con recovered =
0), numero di puntate, forzate, alzate al floor e scartate, quota di date con λ = 0 e
accensioni dell'allarme (solo schema). NaN dove la metrica non si applica.

Sintesi per agente × configurazione × stagione: mediana, quantili 5% e 95% e media della
log-ricchezza finale sui seed, tasso di rovina, g_CE(γ) per γ ∈ {1, 2, 5} (decisione di progetto:
(1/D)·mean(ln W_T) per γ = 1, (1/D)·(1/(1 − γ))·ln mean(W_T^(1 − γ)) per γ > 1, −inf con
W_T = 0), più i valori della realizzazione osservata.
"""

import math
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Final, NamedTuple

import numpy as np
import pandas as pd
from scipy.special import logsumexp

from shk.kelly.environment import AgentRun, run_paired_backtest
from shk.kelly.metrics import wealth_max_drawdown, wealth_recovery_time
from shk.model.elo_fit import parse_season_start_year
from shk.model.frozen_agents import AGENT_ORDER, build_frozen_agents, check_frozen_constants, n_alarms, share_lambda_zero
from shk.model.frozen_params import FROZEN_PARAMS_PATH, FrozenParams, load_frozen_params
from shk.model.paired_backtest import CONFIGURATIONS
from shk.model.season_bootstrap import reconstruct_season, season_block_length
from shk.model.task_seeds import N_STORY_TASKS, story_task_sequence
from shk.model.season_input import SeasonInput, season_input_from_frame

SEED_S10: Final[int] = 20261014
T55_STORY_POSITION: Final[int] = 0
CONFIG_NAMES: Final[tuple[str, ...]] = tuple(c for c, _ in CONFIGURATIONS)
METRICS: Final[tuple[str, ...]] = (
    "final_log_wealth", "ruined", "ruin_date_index", "max_drawdown", "recovery_time", "recovered",
    "n_bets", "n_forced", "n_floored", "n_dropped", "share_lambda_zero", "n_alarms",
)
GAMMAS: Final[tuple[float, ...]] = (1.0, 2.0, 5.0)

SUMMARY_COLUMNS: Final[tuple[str, ...]] = (
    "row_type", "season", "fit_through", "config", "min_stake", "agent", "n_dates", "l_pw", "n_seeds",
    "median_log_wealth", "q05_log_wealth", "q95_log_wealth", "mean_log_wealth", "ruin_rate",
    "g_ce_1", "g_ce_2", "g_ce_5", "median_max_drawdown", "mean_n_bets", "mean_share_lambda_zero", "mean_n_alarms",
    "observed_log_wealth", "observed_max_drawdown", "observed_n_bets", "observed_ruined",
    "observed_share_lambda_zero", "observed_n_alarms",
)
class ValidationSeason(NamedTuple):
    """Stagione di validazione con il fit che la prevede."""

    inp: SeasonInput
    fit: str


class ValidationResult(NamedTuple):
    """Uscite dell'esecuzione congelata sulla validazione: metriche per seed (S, C, A, M, N) e sulla realizzazione osservata (S, C, A, M)."""

    seasons: tuple[str, ...]
    fits: tuple[str, ...]
    n_dates: np.ndarray
    l_pw: np.ndarray
    seeds: np.ndarray
    observed: np.ndarray


def validation_inputs(frame: pd.DataFrame, covariates: Sequence[str]) -> list[ValidationSeason]:
    """Stagioni di validazione del DataFrame del Modulo 2, in ordine cronologico, con il loro fit.

    Solleva
    -------
    ValueError
        Se una stagione ha più fit.
    """
    val = frame[frame["role"] == "validation"]
    out = []
    for season in sorted(set(val["season"]), key=parse_season_start_year):
        fits = set(val.loc[val["season"] == season, "fit_through"])
        if len(fits) != 1:
            raise ValueError(f"Season {season} must have a single fit, got {sorted(fits)}")
        out.append(ValidationSeason(season_input_from_frame(val, season, covariates), fits.pop()))
    return out


def spawn_t55_sequences(n_seasons: int, n_seeds: int,
                        seed: int | np.random.SeedSequence = SEED_S10) -> list[list[np.random.SeedSequence]]:
    """SeedSequence per stagione e seed (vedi modulo); seed è la radice (intero o SeedSequence)."""
    task = story_task_sequence(seed, T55_STORY_POSITION, N_STORY_TASKS)
    return [s.spawn(n_seeds) for s in task.spawn(n_seasons)]


def run_metrics(run: AgentRun, agent: object) -> np.ndarray:
    """Vettore delle METRICS per un'esecuzione con M = 1."""
    w = run.wealth
    final_w = float(w[0, -1])
    times, rec = wealth_recovery_time(w)
    if bool(rec[0]):
        recovery = float(times[0])
    else:
        drawdown = 1.0 - w[0] / np.maximum.accumulate(w[0])
        recovery = float(w.shape[1] - 1 - int(np.argmax(drawdown)))
    return np.array([
        math.log(final_w) if final_w > 0.0 else -math.inf,
        float(run.ruined[0]), float(run.ruin_date_index[0]), float(wealth_max_drawdown(w)[0]),
        recovery, float(rec[0]), float(run.n_bets[0]), float(run.n_forced[0]), float(run.n_floored[0]),
        float(run.n_dropped[0]), share_lambda_zero(agent), n_alarms(agent),
    ])


def run_instance(params: FrozenParams, inp: SeasonInput, arms: Sequence[str] = AGENT_ORDER) -> np.ndarray:
    """Una stagione (seed o realizzazione osservata) nelle tre configurazioni: (C, len(arms), M)."""
    out = np.full((len(CONFIGURATIONS), len(arms), len(METRICS)), np.nan)
    for ci, (_, min_stake) in enumerate(CONFIGURATIONS):
        agents = build_frozen_agents(arms)
        runs = run_paired_backtest(agents, inp.dates, inp.probs, inp.odds, inp.outcomes, min_stake,
                                   fallback_policy=params.fixed["fallback_policy"])
        for run, agent in zip(runs, agents):
            out[ci, list(arms).index(run.name)] = run_metrics(run, agent)
    return out


def run_validation_season(params_path: str, season: ValidationSeason,
                          seed_seqs: Sequence[np.random.SeedSequence]) -> tuple[np.ndarray, np.ndarray, int]:
    """Seed e realizzazione osservata di una stagione; (seed (C, A, M, N), osservata (C, A, M), L_PW)."""
    params = load_frozen_params(params_path)
    check_frozen_constants(params)
    covariates = list(params.fixed["covariates"])
    l_pw = season_block_length(season.inp)
    seeds = np.full((len(CONFIGURATIONS), len(AGENT_ORDER), len(METRICS), len(seed_seqs)), np.nan)
    for k, ss in enumerate(seed_seqs):
        rec = reconstruct_season(season.inp, np.random.default_rng(ss), l_pw, covariates=covariates)
        seeds[..., k] = run_instance(params, rec)
    observed = run_instance(params, season.inp)
    return seeds, observed, l_pw


def evaluate_validation(frame: pd.DataFrame, params_path: Path | str = FROZEN_PARAMS_PATH,
                        n_seeds: int | None = None, workers: int = 1,
                        seed: int | np.random.SeedSequence = SEED_S10) -> ValidationResult:
    """Tutte le stagioni di validazione; con workers > 1 le stagioni vanno su processi separati."""
    params = load_frozen_params(params_path)
    check_frozen_constants(params)
    seasons = validation_inputs(frame, list(params.fixed["covariates"]))
    n = int(params.fixed["n_seeds"]) if n_seeds is None else n_seeds
    seqs = spawn_t55_sequences(len(seasons), n, seed)
    args = [(str(params_path), s, q) for s, q in zip(seasons, seqs)]
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            outputs = list(pool.map(run_validation_season, *zip(*args)))
    else:
        outputs = [run_validation_season(*a) for a in args]
    return ValidationResult(
        seasons=tuple(s.inp.season for s in seasons),
        fits=tuple(s.fit for s in seasons),
        n_dates=np.array([np.unique(s.inp.dates).shape[0] for s in seasons]),
        l_pw=np.array([o[2] for o in outputs]),
        seeds=np.stack([o[0] for o in outputs]),
        observed=np.stack([o[1] for o in outputs]),
    )


def certainty_equivalent(log_wealth: np.ndarray, n_dates: int, gamma: float) -> float:
    """g_CE(γ) sulle traiettorie (decisione di progetto), con −inf se una W_T è 0."""
    lw = np.asarray(log_wealth, dtype=np.float64)
    if np.any(np.isneginf(lw)):
        return -math.inf
    if gamma == 1.0:
        return float(lw.mean() / n_dates)
    return float((logsumexp((1.0 - gamma) * lw) - math.log(lw.size)) / ((1.0 - gamma) * n_dates))


def _value(x: float) -> object:
    return "" if isinstance(x, float) and math.isnan(x) else x


def summary_records(result: ValidationResult, agents: Sequence[str] = AGENT_ORDER) -> list[dict[str, object]]:
    """Righe "summary" per agente × configurazione × stagione; agents nell'ordine del terzo asse delle metriche."""
    m = {name: i for i, name in enumerate(METRICS)}
    records = []
    for si, season in enumerate(result.seasons):
        for ci, (config, min_stake) in enumerate(CONFIGURATIONS):
            for ai, agent in enumerate(agents):
                seeds = result.seeds[si, ci, ai]
                obs = result.observed[si, ci, ai]
                lw = seeds[m["final_log_wealth"]]
                if np.all(np.isnan(lw)):
                    continue
                d = int(result.n_dates[si])
                rec = {c: "" for c in SUMMARY_COLUMNS}
                rec.update(
                    row_type="summary", season=season, fit_through=result.fits[si], config=config,
                    min_stake=min_stake, agent=agent, n_dates=d, l_pw=int(result.l_pw[si]), n_seeds=int(lw.size),
                    median_log_wealth=float(np.median(lw)), q05_log_wealth=float(np.quantile(lw, 0.05)),
                    q95_log_wealth=float(np.quantile(lw, 0.95)), mean_log_wealth=float(np.mean(lw)),
                    ruin_rate=float(np.mean(seeds[m["ruined"]])),
                    median_max_drawdown=float(np.median(seeds[m["max_drawdown"]])),
                    mean_n_bets=float(np.mean(seeds[m["n_bets"]])),
                    mean_share_lambda_zero=_value(float(np.mean(seeds[m["share_lambda_zero"]]))),
                    mean_n_alarms=_value(float(np.mean(seeds[m["n_alarms"]]))),
                    observed_log_wealth=float(obs[m["final_log_wealth"]]),
                    observed_max_drawdown=float(obs[m["max_drawdown"]]),
                    observed_n_bets=int(obs[m["n_bets"]]), observed_ruined=bool(obs[m["ruined"]]),
                    observed_share_lambda_zero=_value(float(obs[m["share_lambda_zero"]])),
                    observed_n_alarms=_value(float(obs[m["n_alarms"]])),
                )
                for gamma, col in zip(GAMMAS, ("g_ce_1", "g_ce_2", "g_ce_5")):
                    rec[col] = certainty_equivalent(lw, d, gamma)
                records.append(rec)
    return records


def save_raw(path: Path | str, result: ValidationResult, agents: tuple[str, ...] = AGENT_ORDER) -> None:
    """Uscite per seed e realizzazione osservata in un file npz compresso; agents nell'ordine dell'asse agente."""
    np.savez_compressed(
        path, seeds=result.seeds, observed=result.observed, seasons=np.array(result.seasons),
        fits=np.array(result.fits), n_dates=result.n_dates, l_pw=result.l_pw,
        configs=np.array(CONFIG_NAMES), agents=np.array(agents), metrics=np.array(METRICS),
    )


def load_raw(path: Path | str) -> ValidationResult:
    """Rilegge il file npz di save_raw."""
    with np.load(path) as z:
        return ValidationResult(tuple(str(s) for s in z["seasons"]), tuple(str(f) for f in z["fits"]),
                                z["n_dates"], z["l_pw"], z["seeds"], z["observed"])
