"""Esecuzione appaiata di prova degli agenti sulle stagioni di training (T52, US-C8.1).

Ingressi dell'ambiente: dal DataFrame del Modulo 2 di T46 (build_module2_frame), righe di
training della stagione (fit_through = stagione), ordinate per Date in modo stabile come
module2.prepare_module2_data: probabilità p_home, p_draw, p_away, quote odds_* della terna
di T46 (B365, oppure SB nel 2000-01, decisione S8) ed esiti FTR. Le covariate della
specificazione di T46 vanno al supervisore del Modulo 2; gli esiti solo all'ambiente.

Agenti per configurazione (CONFIGURATIONS di paired_backtest.py, come build_season_agents):
A, B_0.25, B_0.10, D_ADWIN e D_PH (BaselineDAgent di T50 con serie δ, parametri del
detector congelati in drift.py e κ provvisorio), C0, C1, C2_global, C2, più E con F > 0.
Parametri provvisori al centro delle griglie: W = 80, κ = 0.5 (non sono una calibrazione).
Soglia di C1: quella del fit della stagione per W, con la lunghezza di Politis-White.

Soglie di C1 (righe "threshold"): per ogni stagione di training (fit), ogni W di
MODULE2_WINDOWS e ogni lunghezza di blocco: L_PW (lunghezza ottima del circular/moving
block bootstrap, correzione di Patton-Politis-White, arrotondata, decisione S7) sulla serie
di δ del fit, e per confronto L ∈ {7, 20, 40}. Seed: SeedSequence(SEED_S9).spawn(5)[2]
(T52 in posizione 2), spawn(numero di stagioni) in ordine cronologico, spawn(4) per W,
spawn(4) per L nell'ordine (L_PW, 7, 20, 40).

Metriche per agente, stagione e configurazione (righe "season"): quelle delle righe di
stagione di C6.2, più la crescita certo-equivalente della decisione S10 sulle traiettorie
della stagione (qui una sola, M = 1), g_CE(γ) per γ ∈ {1, 2, 5}, con −inf se W_T = 0; la
quota di date con λ = 0 (C1, C2_global, C2); gli allarmi (D: allarmi del detector; C1:
accensioni) e le puntate azzerate perché fuori supporto (C2).
"""

import math
from collections.abc import Sequence
from typing import Final, NamedTuple

import numpy as np
import pandas as pd

from shk.kelly.agents import AGENT_A_LAMBDA, AGENT_B_LAMBDAS, Agent, FractionalKellyAgent, MinimumStakeAgent
from shk.kelly.environment import AgentRun, run_paired_backtest
from shk.kelly.metrics import wealth_max_drawdown, wealth_recovery_time
from shk.model.agent_c import C1Agent, GradedAgent, Module2Supervisor, build_c0_agent, calibrate_c1_threshold
from shk.model.covariate_inspection import MODULE2_WINDOWS
from shk.model.elo_fit import parse_season_start_year
from shk.model.module3_synthetic import N_STORY_TASKS, SEED_S9
from shk.model.paired_backtest import CONFIGURATIONS
from shk.model.stateful_agents import SERIES_DELTA, BaselineDAgent
from shk.stats.bootstrap import optimal_block_length, round_block_length
from shk.stats.drift import detector_params

T52_STORY_POSITION: Final[int] = 2
PROVISIONAL_WINDOW: Final[int] = 80
PROVISIONAL_KAPPA: Final[float] = 0.5
C1_COMPARISON_BLOCK_LENGTHS: Final[tuple[int, ...]] = (7, 20, 40)
GAMMAS: Final[tuple[float, ...]] = (1.0, 2.0, 5.0)
_FTR_OUTCOME_MAP: Final[dict[str, int]] = {"H": 0, "D": 1, "A": 2}

TRAINING_AGENTS_CSV_COLUMNS: Final[tuple[str, ...]] = (
    "row_type", "config", "min_stake", "agent", "season", "fit_through", "n_dates",
    "final_wealth", "final_log_wealth", "max_drawdown", "recovery_dates", "recovered", "ruined", "ruin_date",
    "n_bets", "n_forced", "n_floored", "n_dropped", "roi",
    "g_ce_1", "g_ce_2", "g_ce_5", "share_lambda_zero", "n_alarms", "n_abstained",
    "window", "kappa", "block_length_kind", "block_length", "threshold", "n_valid_boot",
)


class SeasonInput(NamedTuple):
    """Ingressi di una stagione per l'ambiente e per il supervisore."""

    season: str
    dates: np.ndarray     # (N,) datetime64[ns]
    probs: np.ndarray     # (N, 3)
    odds: np.ndarray      # (N, 3)
    outcomes: np.ndarray  # (1, N)
    x: np.ndarray         # (N, k) covariate pre-partita
    delta: np.ndarray     # (N,) δ del DataFrame, solo per la soglia di C1 e per i test


def season_input_from_frame(frame: pd.DataFrame, season: str, covariates: Sequence[str]) -> SeasonInput:
    """Righe della stagione ordinate per Date in modo stabile (come prepare_module2_data).

    Solleva
    -------
    ValueError
        Se la stagione non ha righe.
    """
    rows = frame[frame["season"] == season].sort_values("Date", kind="stable")
    if rows.empty:
        raise ValueError(f"Season {season} not in frame")
    outcomes = np.array([_FTR_OUTCOME_MAP[str(v).strip()] for v in rows["FTR"]], dtype=np.int64)[None, :]
    return SeasonInput(
        season=season,
        dates=rows["Date"].to_numpy(dtype="datetime64[ns]"),
        probs=rows[["p_home", "p_draw", "p_away"]].to_numpy(dtype=np.float64),
        odds=rows[["odds_home", "odds_draw", "odds_away"]].to_numpy(dtype=np.float64),
        outcomes=outcomes,
        x=rows[list(covariates)].to_numpy(dtype=np.float64),
        delta=rows["delta"].to_numpy(dtype=np.float64),
    )


def training_seasons(frame: pd.DataFrame) -> list[str]:
    """Stagioni del DataFrame in ordine cronologico."""
    return sorted(set(frame["season"]), key=parse_season_start_year)


def spawn_t52_generators(seasons: Sequence[str], seed: int = SEED_S9) -> dict[tuple[str, int, int], np.random.Generator]:
    """Generatori per (stagione, W, indice della lunghezza di blocco), vedi modulo."""
    if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)):
        raise TypeError(f"seed must be an integer, got {type(seed).__name__}")
    task = np.random.SeedSequence(seed).spawn(N_STORY_TASKS)[T52_STORY_POSITION]
    out: dict[tuple[str, int, int], np.random.Generator] = {}
    for season, s_seq in zip(seasons, task.spawn(len(seasons))):
        for w, w_seq in zip(MODULE2_WINDOWS, s_seq.spawn(len(MODULE2_WINDOWS))):
            for k, l_seq in enumerate(w_seq.spawn(1 + len(C1_COMPARISON_BLOCK_LENGTHS))):
                out[(season, w, k)] = np.random.default_rng(l_seq)
    return out


def _empty_record() -> dict[str, object]:
    return {c: "" for c in TRAINING_AGENTS_CSV_COLUMNS}


def threshold_records(
    inputs: Sequence[SeasonInput], seed: int = SEED_S9
) -> tuple[list[dict[str, object]], dict[tuple[str, int], float]]:
    """Soglie di C1 per stagione (fit), W e lunghezza di blocco; dizionario delle soglie a L_PW."""
    seasons = [inp.season for inp in inputs]
    gens = spawn_t52_generators(seasons, seed)
    records: list[dict[str, object]] = []
    chosen: dict[tuple[str, int], float] = {}
    for inp in inputs:
        l_pw = round_block_length(optimal_block_length(inp.delta).circular)
        lengths = [("l_pw", l_pw)] + [("fixed", L) for L in C1_COMPARISON_BLOCK_LENGTHS]
        for w in MODULE2_WINDOWS:
            for k, (kind, length) in enumerate(lengths):
                thr, n_valid = calibrate_c1_threshold(inp.x, inp.delta, w, length, gens[(inp.season, w, k)])
                if kind == "l_pw":
                    chosen[(inp.season, w)] = thr
                records.append({**_empty_record(), "row_type": "threshold", "season": inp.season,
                                "fit_through": inp.season, "window": w, "block_length_kind": kind,
                                "block_length": length, "threshold": thr, "n_valid_boot": n_valid})
    return records, chosen


def certainty_equivalent_growth(final_wealth: np.ndarray, n_dates: int, gamma: float) -> float:
    """g_CE(γ) della decisione S10 sulle traiettorie della stagione; −inf se una W_T è 0."""
    w = np.asarray(final_wealth, dtype=np.float64)
    if np.any(w <= 0.0):
        return -math.inf
    if gamma == 1.0:
        return float(np.mean(np.log(w)) / n_dates)
    return float(np.log(np.mean(w ** (1.0 - gamma))) / ((1.0 - gamma) * n_dates))


def build_training_agents(
    min_stake: float, supervisor: Module2Supervisor, threshold: float, kappa: float = PROVISIONAL_KAPPA
) -> list[Agent]:
    """Agenti dell'esecuzione di prova nell'ordine A, B, D, C, E (E solo con F > 0)."""
    agents: list[Agent] = [
        FractionalKellyAgent("A", lam=AGENT_A_LAMBDA),
        FractionalKellyAgent("B_0.25", lam=AGENT_B_LAMBDAS[0]),
        FractionalKellyAgent("B_0.10", lam=AGENT_B_LAMBDAS[1]),
        BaselineDAgent("D_ADWIN", "adwin", detector_params("adwin"), kappa, series=SERIES_DELTA),
        BaselineDAgent("D_PH", "page_hinkley", detector_params("page_hinkley"), kappa, series=SERIES_DELTA),
        build_c0_agent("C0"),
        C1Agent("C1", supervisor, kappa, threshold),
        GradedAgent("C2_global", supervisor, abstain=False),
        GradedAgent("C2", supervisor, abstain=True),
    ]
    if min_stake > 0.0:
        agents.append(MinimumStakeAgent("E"))
    return agents


def run_training_season(
    inp: SeasonInput,
    covariates: Sequence[str],
    min_stake: float,
    threshold: float,
    window: int = PROVISIONAL_WINDOW,
    kappa: float = PROVISIONAL_KAPPA,
) -> tuple[tuple[AgentRun, ...], list[Agent]]:
    """Un'esecuzione dell'ambiente su una stagione e una configurazione."""
    supervisor = Module2Supervisor(inp.season, inp.dates, inp.x, covariates, window)
    agents = build_training_agents(min_stake, supervisor, threshold, kappa)
    runs = run_paired_backtest(agents, inp.dates, inp.probs, inp.odds, inp.outcomes, min_stake)
    return runs, agents


def _season_record(run: AgentRun, agent: Agent, config: str, min_stake: float, season: str) -> dict[str, object]:
    w_mat = run.wealth
    final_w = float(w_mat[0, -1])
    t_arr, rec_arr = wealth_recovery_time(w_mat)
    recovered = bool(rec_arr[0])
    ruined = bool(run.ruined[0])
    n_dates = int(run.dates.shape[0])
    rec = {**_empty_record(), "row_type": "season", "config": config, "min_stake": min_stake, "agent": run.name,
           "season": season, "fit_through": season, "n_dates": n_dates, "final_wealth": final_w,
           "final_log_wealth": float(np.log(final_w)) if final_w > 0.0 else "",
           "max_drawdown": float(wealth_max_drawdown(w_mat)[0]),
           "recovery_dates": int(t_arr[0]) if recovered else "", "recovered": recovered, "ruined": ruined,
           "ruin_date": str(run.dates[run.ruin_date_index[0]]) if ruined else "",
           "n_bets": int(run.n_bets[0]), "n_forced": int(run.n_forced[0]), "n_floored": int(run.n_floored[0]),
           "n_dropped": int(run.n_dropped[0]), "roi": float(final_w - 1.0)}
    for gamma, col in zip(GAMMAS, ("g_ce_1", "g_ce_2", "g_ce_5")):
        rec[col] = certainty_equivalent_growth(w_mat[:, -1], n_dates, gamma)
    if isinstance(agent, BaselineDAgent):
        rec["n_alarms"] = agent.n_alarms
    if isinstance(agent, C1Agent):
        lam = np.array(list(agent.lambda_by_date.values()))
        rec["share_lambda_zero"] = float(np.mean(lam == 0.0))
        rec["n_alarms"] = agent.n_onsets
    if isinstance(agent, GradedAgent):
        rec["share_lambda_zero"] = float(np.mean(list(agent.lambda_zero_by_date.values())))
        if agent.name == "C2":
            rec["n_abstained"] = agent.n_abstained
    return rec


def evaluate_training_agents(
    frame: pd.DataFrame,
    covariates: Sequence[str],
    seed: int = SEED_S9,
    window: int = PROVISIONAL_WINDOW,
    kappa: float = PROVISIONAL_KAPPA,
) -> list[dict[str, object]]:
    """Soglie di C1 ed esecuzione appaiata di prova su tutte le stagioni del DataFrame.

    Parametri
    ---------
    frame : pd.DataFrame
        Righe di training del DataFrame del Modulo 2 (nessuna stagione di validazione).
    covariates : Sequence[str]
        Specificazione di T46.

    Solleva
    -------
    ValueError
        Se il DataFrame contiene righe non di training.
    """
    if set(frame["role"]) != {"training"}:
        raise ValueError("frame must contain training rows only")
    inputs = [season_input_from_frame(frame, s, covariates) for s in training_seasons(frame)]
    records, thresholds = threshold_records(inputs, seed)
    for inp in inputs:
        for config, min_stake in CONFIGURATIONS:
            runs, agents = run_training_season(inp, covariates, min_stake, thresholds[(inp.season, window)],
                                               window, kappa)
            for run, agent in zip(runs, agents):
                rec = _season_record(run, agent, config, min_stake, inp.season)
                rec["window"], rec["kappa"] = window, kappa
                records.append(rec)
    return records
