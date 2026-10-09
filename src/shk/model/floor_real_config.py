"""Modulo per l'analisi Monte Carlo del floor nella configurazione reale (US-C6.3 / Task 37).

Questo modulo implementa il test di US-C6.3 sul calendario e sulle quote reali delle
19 stagioni di validazione: gli agenti A, B_0.25, B_0.10 ed E giocano sulle previsioni
e quote B365 reali, ma gli esiti sono estratti dalle probabilita' de-viggati proporzionali
del mercato (verita').
"""

from dataclasses import dataclass
import math
from typing import Final, Sequence

import numpy as np
import pandas as pd

from shk.kelly.agents import MinimumStakeAgent
from shk.kelly.environment import AgentRun, DateView, run_paired_backtest
from shk.kelly.floor import SEED_C6
from shk.kelly.metrics import wealth_max_drawdown
from shk.market.devig import devig_proportional
from shk.model.elo_fit import parse_season_start_year
from shk.model.monitoring import assemble_baseline_d_season_input
from shk.model.paired_backtest import CONFIGURATIONS, build_season_agents

M_REPLICAS: Final[int] = 1_000
Z_99: Final[float] = 2.576
THETA_THRESHOLDS: Final[tuple[float, ...]] = (0.5, 0.1)

FLOOR_REAL_CSV_COLUMNS: Final[tuple[str, ...]] = (
    "row_type",
    "config",
    "min_stake",
    "agent",
    "season",
    "fit_through",
    "m_replicas",
    "ruin_rate",
    "ruin_rate_ci_lower",
    "ruin_rate_ci_upper",
    "median_final_wealth",
    "p05_final_wealth",
    "p95_final_wealth",
    "mean_roi",
    "prob_min_wealth_le_0_5",
    "prob_min_wealth_le_0_1",
    "min_wealth",
    "median_max_drawdown",
    "floored_bets_share",
    "prob_replica_floored",
    "analytic_expected_roi",
    "se_roi",
)


def outcomes_by_inversion(q: np.ndarray, u: np.ndarray) -> np.ndarray:
    """Mappa variabili uniformi u in [0, 1] in esiti {0, 1, 2} secondo q.

    Regola di inversione:
    - 0 (Home) se u < q_H;
    - 1 (Draw) se u < q_H + q_D (e u >= q_H);
    - 2 (Away) altrimenti.

    Parametri
    ---------
    q : np.ndarray
        Matrice float64 (N, 3) delle probabilita' di mercato de-viggati.
    u : np.ndarray
        Matrice float64 (M, N) di campioni uniformi in [0, 1].

    Restituisce
    -----------
    np.ndarray
        Matrice int64 (M, N) con valori in {0, 1, 2}.

    Solleva
    -------
    TypeError
        Se q o u non sono ndarray con tipo numerico reale.
    ValueError
        Se le forme non sono compatibili ((N, 3) e (M, N)) o valori non finiti.
    """
    if not isinstance(q, np.ndarray) or not isinstance(u, np.ndarray):
        raise TypeError("q and u must be numpy.ndarray")
    if q.ndim != 2 or q.shape[1] != 3:
        raise ValueError(f"q must have shape (N, 3), got {q.shape}")
    if u.ndim != 2 or u.shape[1] != q.shape[0]:
        raise ValueError(f"u must have shape (M, N) with N={q.shape[0]}, got {u.shape}")
    if not np.all(np.isfinite(q)) or not np.all(np.isfinite(u)):
        raise ValueError("q and u must contain only finite values")

    q_h = q[:, 0]
    q_hd = q_h + q[:, 1]
    return np.where(u < q_h, 0, np.where(u < q_hd, 1, 2)).astype(np.int64)


def sample_match_outcomes(
    odds: np.ndarray,
    rng: np.random.Generator,
    m_replicas: int = M_REPLICAS,
) -> np.ndarray:
    """Estrae la matrice (M, N) degli esiti per inversione con probabilita' de-viggati proporzionali.

    Parametri
    ---------
    odds : np.ndarray
        Matrice float64 (N, 3) di quote decimali per le N partite della stagione.
    rng : np.random.Generator
        Generatore di numeri casuali NumPy.
    m_replicas : int
        Numero di repliche Monte Carlo (default 1000).

    Restituisce
    -----------
    np.ndarray
        Matrice int64 (M, N) con esiti in {0, 1, 2} (Home=0, Draw=1, Away=2).

    Solleva
    -------
    TypeError
        Se gli argomenti non rispettano i tipi attesi.
    ValueError
        Se odds ha forma non valida o m_replicas < 1.
    """
    if not isinstance(odds, np.ndarray):
        raise TypeError(f"odds must be a numpy.ndarray, got {type(odds).__name__}")
    if odds.ndim != 2 or odds.shape[1] != 3:
        raise ValueError(f"odds must have shape (N, 3), got {odds.shape}")
    if not isinstance(rng, np.random.Generator):
        raise TypeError(f"rng must be a numpy.random.Generator, got {type(rng).__name__}")
    if isinstance(m_replicas, bool) or not isinstance(m_replicas, int) or m_replicas < 1:
        raise ValueError(f"m_replicas must be a positive integer, got {m_replicas}")

    q = devig_proportional(odds)
    u = rng.random((m_replicas, odds.shape[0]))
    return outcomes_by_inversion(q, u)


def compute_agent_e_analytic_roi(
    dates: np.ndarray,
    odds: np.ndarray,
    probs: np.ndarray,
    min_stake: float,
) -> float:
    """Calcola il ROI atteso analitico di E su una stagione: F * sum_d (1 / S_d - 1).

    Per ogni data distinta, identifica la partita di ripiego scelta da E
    (l'esito con massimo EV stimato), calcola l'overround S_d della partita,
    e accumula F * (1 / S_d - 1).

    Parametri
    ---------
    dates : np.ndarray
        Array 1D datetime64 con le date delle partite.
    odds : np.ndarray
        Matrice (N, 3) con le quote decimali lorde.
    probs : np.ndarray
        Matrice (N, 3) con le probabilita' stimate dal modello.
    min_stake : float
        Puntata minima fissa F >= 0.

    Restituisce
    -----------
    float
        ROI atteso analitico della stagione.

    Solleva
    -------
    TypeError
        Se gli argomenti non rispettano i tipi attesi.
    ValueError
        Se min_stake < 0.
    """
    if not isinstance(dates, np.ndarray) or not np.issubdtype(dates.dtype, np.datetime64):
        raise TypeError("dates must be a numpy.ndarray with datetime64 dtype")
    if not isinstance(odds, np.ndarray) or not isinstance(probs, np.ndarray):
        raise TypeError("odds and probs must be numpy.ndarray")
    if isinstance(min_stake, bool) or not isinstance(min_stake, (float, np.floating)):
        raise TypeError(f"min_stake must be a float, got {type(min_stake).__name__}")
    if min_stake < 0.0:
        raise ValueError(f"min_stake must be non-negative, got {min_stake}")

    if min_stake == 0.0 or dates.shape[0] == 0:
        return 0.0

    agent_e = MinimumStakeAgent("E")
    unique_dates, split_indices = np.unique(dates, return_index=True)
    sort_order = np.argsort(split_indices)
    unique_dates = unique_dates[sort_order]

    roi_sum = 0.0
    for d in unique_dates:
        mask = dates == d
        view = DateView(date=d, probs=probs[mask], odds=odds[mask])
        decision = agent_e.decide(view)
        fallback_match = decision.fallback_match
        fallback_odds = view.odds[fallback_match, :]
        s_d = float(np.sum(1.0 / fallback_odds))
        roi_sum += min_stake * (1.0 / s_d - 1.0)

    return float(roi_sum)


@dataclass(frozen=True)
class SeasonRunArtifact:
    """Artefatto contenente i risultati di simulazione per una stagione."""

    season: str
    fit_through: str
    config_name: str
    min_stake: float
    agent_name: str
    final_wealth: np.ndarray
    min_wealth_trajectory: np.ndarray
    min_overall_wealth: float
    ruined: np.ndarray
    max_drawdown: np.ndarray
    n_bets: np.ndarray
    n_floored: np.ndarray
    analytic_expected_roi: float | None


def compute_season_metrics(
    artifact: SeasonRunArtifact,
) -> dict[str, str | int | float]:
    """Calcola le metriche della riga di stagione per una combinazione (config, agent).

    Parametri
    ---------
    artifact : SeasonRunArtifact
        Artefatto dei risultati della stagione.

    Restituisce
    -----------
    dict[str, str | int | float]
        Dizionario con le metriche per la riga stagionale del CSV.
    """
    m_count = artifact.final_wealth.shape[0]
    ruin_r = float(np.mean(artifact.ruined))
    w_final = artifact.final_wealth
    roi_arr = w_final - 1.0
    mean_r = float(np.mean(roi_arr))

    med_w = float(np.median(w_final))
    p05_w = float(np.percentile(w_final, 5))
    p95_w = float(np.percentile(w_final, 95))

    min_w_traj = artifact.min_wealth_trajectory
    p_min_05 = float(np.mean(min_w_traj <= 0.5))
    p_min_01 = float(np.mean(min_w_traj <= 0.1))

    med_dd = float(np.median(artifact.max_drawdown))

    tot_bets = int(np.sum(artifact.n_bets))
    tot_floored = int(np.sum(artifact.n_floored))
    floored_share = float(tot_floored / tot_bets) if tot_bets > 0 else 0.0
    prob_floored = float(np.mean(artifact.n_floored > 0))

    if artifact.agent_name == "E" and artifact.analytic_expected_roi is not None:
        analytic_roi_val: str | float = float(artifact.analytic_expected_roi)
        se_roi_val: str | float = float(np.std(roi_arr, ddof=1) / math.sqrt(m_count))
    else:
        analytic_roi_val = ""
        se_roi_val = ""

    return {
        "row_type": "season",
        "config": artifact.config_name,
        "min_stake": artifact.min_stake,
        "agent": artifact.agent_name,
        "season": artifact.season,
        "fit_through": artifact.fit_through,
        "m_replicas": m_count,
        "ruin_rate": ruin_r,
        "ruin_rate_ci_lower": "",
        "ruin_rate_ci_upper": "",
        "median_final_wealth": med_w,
        "p05_final_wealth": p05_w,
        "p95_final_wealth": p95_w,
        "mean_roi": mean_r,
        "prob_min_wealth_le_0_5": p_min_05,
        "prob_min_wealth_le_0_1": p_min_01,
        "min_wealth": artifact.min_overall_wealth,
        "median_max_drawdown": med_dd,
        "floored_bets_share": floored_share,
        "prob_replica_floored": prob_floored,
        "analytic_expected_roi": analytic_roi_val,
        "se_roi": se_roi_val,
    }


def compute_aggregate_metrics(
    artifacts: Sequence[SeasonRunArtifact],
) -> dict[str, str | int | float]:
    """Calcola le metriche aggregate sulle 19·M traiettorie individuali.

    Parametri
    ---------
    artifacts : Sequence[SeasonRunArtifact]
        Sequenza dei 19 artefatti stagionali per la stessa combinazione (config, agent).

    Restituisce
    -----------
    dict[str, str | int | float]
        Dizionario con le metriche per la riga aggregata del CSV.
    """
    if len(artifacts) == 0:
        raise ValueError("artifacts must not be empty")

    first = artifacts[0]
    config_name = first.config_name
    min_stake = first.min_stake
    agent_name = first.agent_name

    all_w_final = np.concatenate([a.final_wealth for a in artifacts])
    all_min_w_traj = np.concatenate([a.min_wealth_trajectory for a in artifacts])
    all_ruined = np.concatenate([a.ruined for a in artifacts])
    all_dd = np.concatenate([a.max_drawdown for a in artifacts])
    all_n_bets = np.concatenate([a.n_bets for a in artifacts])
    all_n_floored = np.concatenate([a.n_floored for a in artifacts])

    total_trajectories = all_w_final.shape[0]
    ruin_r = float(np.mean(all_ruined))

    margin = Z_99 * math.sqrt(ruin_r * (1.0 - ruin_r) / total_trajectories)
    ci_lower = max(0.0, ruin_r - margin)
    ci_upper = min(1.0, ruin_r + margin)

    med_w = float(np.median(all_w_final))
    p05_w = float(np.percentile(all_w_final, 5))
    p95_w = float(np.percentile(all_w_final, 95))

    roi_arr = all_w_final - 1.0
    mean_r = float(np.mean(roi_arr))

    p_min_05 = float(np.mean(all_min_w_traj <= 0.5))
    p_min_01 = float(np.mean(all_min_w_traj <= 0.1))

    min_overall_w = min(a.min_overall_wealth for a in artifacts)
    med_dd = float(np.median(all_dd))

    tot_bets = int(np.sum(all_n_bets))
    tot_floored = int(np.sum(all_n_floored))
    floored_share = float(tot_floored / tot_bets) if tot_bets > 0 else 0.0
    prob_floored = float(np.mean(all_n_floored > 0))

    if agent_name == "E" and first.analytic_expected_roi is not None:
        analytic_roi_val: str | float = float(
            np.mean([float(a.analytic_expected_roi) for a in artifacts])
        )
        se_roi_val: str | float = float(
            np.std(roi_arr, ddof=1) / math.sqrt(total_trajectories)
        )
    else:
        analytic_roi_val = ""
        se_roi_val = ""

    return {
        "row_type": "aggregate",
        "config": config_name,
        "min_stake": min_stake,
        "agent": agent_name,
        "season": "",
        "fit_through": "",
        "m_replicas": total_trajectories,
        "ruin_rate": ruin_r,
        "ruin_rate_ci_lower": ci_lower,
        "ruin_rate_ci_upper": ci_upper,
        "median_final_wealth": med_w,
        "p05_final_wealth": p05_w,
        "p95_final_wealth": p95_w,
        "mean_roi": mean_r,
        "prob_min_wealth_le_0_5": p_min_05,
        "prob_min_wealth_le_0_1": p_min_01,
        "min_wealth": min_overall_w,
        "median_max_drawdown": med_dd,
        "floored_bets_share": floored_share,
        "prob_replica_floored": prob_floored,
        "analytic_expected_roi": analytic_roi_val,
        "se_roi": se_roi_val,
    }


def evaluate_floor_real_config(
    df_residuals: pd.DataFrame,
    df: pd.DataFrame,
    schedule: dict[str, dict[str, list[str]]],
    m_replicas: int = M_REPLICAS,
    seed: int = SEED_C6,
) -> tuple[list[dict[str, str | int | float]], dict[tuple[str, str], list[SeasonRunArtifact]]]:
    """Esegue la simulazione Monte Carlo con esiti da verita' proporzionale su 19 stagioni.

    Parametri
    ---------
    df_residuals : pd.DataFrame
        DataFrame dei residui del Modulo 1.
    df : pd.DataFrame
        DataFrame grezzo o consolidato delle partite con quote B365.
    schedule : dict[str, dict[str, list[str]]]
        Schema temporale di calibrazione.
    m_replicas : int
        Numero di repliche Monte Carlo per stagione (default 1000).
    seed : int
        Seme radice di C6 (default SEED_C6).

    Restituisce
    -----------
    tuple[list[dict[str, str | int | float]], dict[tuple[str, str], list[SeasonRunArtifact]]]
        - Lista di 220 record conformi a FLOOR_REAL_CSV_COLUMNS;
        - Mappa dei risultati per (config, agent) con la lista dei 19 artefatti stagionali.

    Solleva
    -------
    TypeError
        Se df_residuals o df non sono DataFrame, o se schedule non e' dict.
    ValueError
        Se m_replicas < 1.
    """
    if not isinstance(df_residuals, pd.DataFrame):
        raise TypeError(f"df_residuals must be a pd.DataFrame, got {type(df_residuals).__name__}")
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"df must be a pd.DataFrame, got {type(df).__name__}")
    if not isinstance(schedule, dict):
        raise TypeError(f"schedule must be a dict, got {type(schedule).__name__}")
    if isinstance(m_replicas, bool) or not isinstance(m_replicas, int) or m_replicas < 1:
        raise ValueError(f"m_replicas must be a positive integer, got {m_replicas}")

    train_fits = sorted(schedule.keys(), key=parse_season_start_year)
    val_seasons_with_fit: list[tuple[str, str]] = []
    for fit_k in train_fits:
        for val_s in schedule[fit_k]["validation"]:
            val_seasons_with_fit.append((val_s, fit_k))

    val_seasons_with_fit.sort(key=lambda item: parse_season_start_year(item[0]))
    n_val_seasons = len(val_seasons_with_fit)
    if n_val_seasons != 19:
        raise ValueError(f"Expected 19 validation seasons, got {n_val_seasons}")

    # Gerarchia semi: SeedSequence(SEED_C6).spawn(2)[1].spawn(19)
    root_ss = np.random.SeedSequence(seed)
    c6_children = root_ss.spawn(2)
    val_seeds = c6_children[1].spawn(19)

    group_artifacts: dict[tuple[str, str], list[SeasonRunArtifact]] = {}
    for config_name, min_stake_val in CONFIGURATIONS:
        for agent_inst in build_season_agents(min_stake_val):
            group_artifacts[(config_name, agent_inst.name)] = []

    season_rows: list[dict[str, str | int | float]] = []

    for s_idx, (season, fit_through) in enumerate(val_seasons_with_fit):
        s_input = assemble_baseline_d_season_input(
            df_residuals=df_residuals,
            df_raw=df,
            season=season,
            fit_through=fit_through,
            role="validation",
        )

        season_rng = np.random.default_rng(val_seeds[s_idx])
        outcomes = sample_match_outcomes(
            s_input.odds, season_rng, m_replicas=m_replicas
        )

        for config_name, min_stake_val in CONFIGURATIONS:
            agents = build_season_agents(min_stake_val)
            runs = run_paired_backtest(
                agents=agents,
                dates=s_input.dates,
                probs=s_input.probs,
                odds=s_input.odds,
                outcomes=outcomes,
                min_stake=min_stake_val,
                record_stakes=False,
            )

            for run in runs:
                w_mat = run.wealth  # (M, D+1)
                final_w = w_mat[:, -1].copy()
                min_w_traj = np.min(w_mat, axis=1)  # (M,)
                min_overall_w = float(np.min(w_mat))
                max_dd = wealth_max_drawdown(w_mat)

                if run.name == "E":
                    analytic_roi_val = compute_agent_e_analytic_roi(
                        dates=s_input.dates,
                        odds=s_input.odds,
                        probs=s_input.probs,
                        min_stake=min_stake_val,
                    )
                else:
                    analytic_roi_val = None

                art = SeasonRunArtifact(
                    season=season,
                    fit_through=fit_through,
                    config_name=config_name,
                    min_stake=min_stake_val,
                    agent_name=run.name,
                    final_wealth=final_w,
                    min_wealth_trajectory=min_w_traj,
                    min_overall_wealth=min_overall_w,
                    ruined=run.ruined.copy(),
                    max_drawdown=max_dd,
                    n_bets=run.n_bets.copy(),
                    n_floored=run.n_floored.copy(),
                    analytic_expected_roi=analytic_roi_val,
                )

                group_artifacts[(config_name, run.name)].append(art)
                s_record = compute_season_metrics(art)
                season_rows.append(s_record)

    aggregate_rows: list[dict[str, str | int | float]] = []
    for config_name, min_stake_val in CONFIGURATIONS:
        for agent_inst in build_season_agents(min_stake_val):
            artifacts = group_artifacts[(config_name, agent_inst.name)]
            agg_record = compute_aggregate_metrics(artifacts)
            aggregate_rows.append(agg_record)

    all_records = season_rows + aggregate_rows
    return all_records, group_artifacts
