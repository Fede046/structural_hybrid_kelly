"""Modulo per l'esecuzione appaiata degli agenti A, B ed E sulle stagioni di validazione (US-C6.2 / Task 35).

Coordina l'esecuzione degli agenti Kelly pieno (A), Kelly frazionario (B 0.25 e 0.10)
e puntata minima (E) su 19 stagioni di validazione sotto tre configurazioni di floor:
nessun floor (F = 0), floor £0.01 e floor £1.00 (normalizzati rispetto al bankroll iniziale
di KellyBench £220).
"""

from typing import Final, Sequence
import numpy as np
import pandas as pd

from shk.kelly.agents import (
    AGENT_A_LAMBDA,
    AGENT_B_LAMBDAS,
    Agent,
    FractionalKellyAgent,
    MinimumStakeAgent,
)
from shk.kelly.environment import AgentRun, run_paired_backtest
from shk.kelly.metrics import wealth_max_drawdown, wealth_recovery_time
from shk.model.elo_fit import parse_season_start_year
from shk.model.monitoring import assemble_baseline_d_season_input

KELLYBENCH_INITIAL_BANKROLL_GBP: Final[float] = 220.0

CONFIGURATIONS: Final[tuple[tuple[str, float], ...]] = (
    ("none", 0.0),
    ("gbp_0.01", 0.01 / KELLYBENCH_INITIAL_BANKROLL_GBP),
    ("gbp_1", 1.0 / KELLYBENCH_INITIAL_BANKROLL_GBP),
)

_FTR_OUTCOME_MAP: Final[dict[str, int]] = {"H": 0, "D": 1, "A": 2}

PAIRED_BACKTEST_CSV_COLUMNS: Final[tuple[str, ...]] = (
    "row_type",
    "config",
    "min_stake",
    "agent",
    "season",
    "fit_through",
    "n_dates",
    "final_wealth",
    "final_log_wealth",
    "max_drawdown",
    "recovery_dates",
    "recovered",
    "ruined",
    "ruin_date",
    "n_bets",
    "n_forced",
    "n_floored",
    "n_dropped",
    "roi",
    "median_final_wealth",
    "sd_log_wealth",
    "n_unruined",
    "ruin_rate",
    "median_max_drawdown",
    "max_max_drawdown",
    "recovery_rate",
    "median_recovery_dates",
    "sum_final_log_wealth",
    "median_roi",
    "min_roi",
    "max_roi",
)


def build_season_agents(min_stake: float) -> list[Agent]:
    """Costruisce le istanze degli agenti ammesse per una data configurazione di floor.

    Con F = 0 include solo gli agenti volontari: A (Kelly pieno), B_0.25 e B_0.10.
    Con F > 0 include anche l'agente a puntata minima E.

    Parametri
    ---------
    min_stake : float
        Puntata minima fissa F >= 0.

    Restituisce
    -----------
    list[Agent]
        Lista delle istanze degli agenti nell'ordine stabilito.

    Solleva
    -------
    TypeError
        Se min_stake non è un float reale.
    ValueError
        Se min_stake < 0.
    """
    if isinstance(min_stake, bool) or not isinstance(min_stake, (float, np.floating)):
        raise TypeError(f"min_stake must be a float, got {type(min_stake).__name__}")
    if min_stake < 0.0:
        raise ValueError(f"min_stake must be non-negative, got {min_stake}")

    agents: list[Agent] = [
        FractionalKellyAgent("A", lam=AGENT_A_LAMBDA),
        FractionalKellyAgent("B_0.25", lam=AGENT_B_LAMBDAS[0]),
        FractionalKellyAgent("B_0.10", lam=AGENT_B_LAMBDAS[1]),
    ]
    if min_stake > 0.0:
        agents.append(MinimumStakeAgent("E"))
    return agents


def evaluate_validation_seasons(
    df_residuals: pd.DataFrame,
    df: pd.DataFrame,
    schedule: dict[str, dict[str, list[str]]],
) -> list[dict[str, str | int | float]]:
    """Esegue il backtest appaiato su tutte le 19 stagioni di validazione e le 3 configurazioni.

    Parametri
    ---------
    df_residuals : pd.DataFrame
        DataFrame dei residui del Modulo 1 prodotto da compute_model_residuals.
    df : pd.DataFrame
        DataFrame grezzo o consolidato delle partite con quote B365.
    schedule : dict[str, dict[str, list[str]]]
        Schema temporale di calibrazione con le stagioni di validazione per fit.

    Restituisce
    -----------
    list[dict[str, str | int | float]]
        Lista di 220 dizionari (209 righe di stagione e 11 di riepilogo) conformi a
        PAIRED_BACKTEST_CSV_COLUMNS.

    Solleva
    -------
    TypeError
        Se df_residuals o df non sono DataFrame, o se schedule non è un dict.
    """
    if not isinstance(df_residuals, pd.DataFrame):
        raise TypeError(f"df_residuals must be a pd.DataFrame, got {type(df_residuals).__name__}")
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"df must be a pd.DataFrame, got {type(df).__name__}")
    if not isinstance(schedule, dict):
        raise TypeError(f"schedule must be a dict, got {type(schedule).__name__}")

    train_fits = sorted(schedule.keys(), key=parse_season_start_year)
    val_seasons_with_fit: list[tuple[str, str]] = []
    for fit_k in train_fits:
        for val_s in schedule[fit_k]["validation"]:
            val_seasons_with_fit.append((val_s, fit_k))

    val_seasons_with_fit.sort(key=lambda item: parse_season_start_year(item[0]))

    season_rows: list[dict[str, str | int | float]] = []

    # Struttura per accumulare i risultati stagionali per combinazione (config, agent)
    # Chiave: (config_name, agent_name)
    group_data: dict[tuple[str, str], list[dict[str, str | int | float]]] = {}

    for config_name, min_stake_val in CONFIGURATIONS:
        for agent_inst in build_season_agents(min_stake_val):
            group_data[(config_name, agent_inst.name)] = []

    for season, fit_through in val_seasons_with_fit:
        s_input = assemble_baseline_d_season_input(
            df_residuals=df_residuals,
            df_raw=df,
            season=season,
            fit_through=fit_through,
            role="validation",
        )

        n_matches = s_input.ftr.shape[0]
        outcome_integers = np.empty((1, n_matches), dtype=np.int64)
        for idx in range(n_matches):
            ftr_val = str(s_input.ftr[idx])
            outcome_integers[0, idx] = _FTR_OUTCOME_MAP[ftr_val]

        for config_name, min_stake_val in CONFIGURATIONS:
            agents = build_season_agents(min_stake_val)
            runs = run_paired_backtest(
                agents=agents,
                dates=s_input.dates,
                probs=s_input.probs,
                odds=s_input.odds,
                outcomes=outcome_integers,
                min_stake=min_stake_val,
                record_stakes=False,
            )

            for run in runs:
                w_mat = run.wealth
                final_w = float(w_mat[0, -1])
                final_lw: str | float = float(np.log(final_w)) if final_w > 0.0 else ""

                m_dd = float(wealth_max_drawdown(w_mat)[0])
                t_arr, rec_arr = wealth_recovery_time(w_mat)
                is_recovered = bool(rec_arr[0])
                rec_dates: str | int = int(t_arr[0]) if is_recovered else ""

                is_ruined = bool(run.ruined[0])
                ruin_date_str = (
                    str(run.dates[run.ruin_date_index[0]]) if is_ruined else ""
                )

                s_row: dict[str, str | int | float] = {
                    "row_type": "season",
                    "config": config_name,
                    "min_stake": min_stake_val,
                    "agent": run.name,
                    "season": season,
                    "fit_through": fit_through,
                    "n_dates": int(run.dates.shape[0]),
                    "final_wealth": final_w,
                    "final_log_wealth": final_lw,
                    "max_drawdown": m_dd,
                    "recovery_dates": rec_dates,
                    "recovered": is_recovered,
                    "ruined": is_ruined,
                    "ruin_date": ruin_date_str,
                    "n_bets": int(run.n_bets[0]),
                    "n_forced": int(run.n_forced[0]),
                    "n_floored": int(run.n_floored[0]),
                    "n_dropped": int(run.n_dropped[0]),
                    "roi": float(final_w - 1.0),
                    # Campi di riepilogo vuoti nelle righe di stagione
                    "median_final_wealth": "",
                    "sd_log_wealth": "",
                    "n_unruined": "",
                    "ruin_rate": "",
                    "median_max_drawdown": "",
                    "max_max_drawdown": "",
                    "recovery_rate": "",
                    "median_recovery_dates": "",
                    "sum_final_log_wealth": "",
                    "median_roi": "",
                    "min_roi": "",
                    "max_roi": "",
                }
                season_rows.append(s_row)
                group_data[(config_name, run.name)].append(s_row)

    # Costruzione delle 11 righe di riepilogo
    summary_rows: list[dict[str, str | int | float]] = []

    for config_name, min_stake_val in CONFIGURATIONS:
        agent_instances = build_season_agents(min_stake_val)
        for agent_inst in agent_instances:
            agent_name = agent_inst.name
            rows_g = group_data[(config_name, agent_name)]
            n_seasons = len(rows_g)

            w_list = [float(r["final_wealth"]) for r in rows_g]
            ruined_list = [bool(r["ruined"]) for r in rows_g]
            dd_list = [float(r["max_drawdown"]) for r in rows_g]
            rec_list = [bool(r["recovered"]) for r in rows_g]
            roi_list = [float(r["roi"]) for r in rows_g]

            median_w = float(np.median(w_list))
            unruined_w = [w_list[i] for i in range(n_seasons) if not ruined_list[i]]
            n_unruined = len(unruined_w)

            if n_unruined > 1:
                sd_lw: str | float = float(np.std([np.log(uw) for uw in unruined_w], ddof=1))
            else:
                sd_lw = ""

            ruin_r = float(np.mean(ruined_list))
            median_dd = float(np.median(dd_list))
            max_dd = float(np.max(dd_list))
            rec_rate = float(np.mean(rec_list))

            rec_dates_vals = [
                int(rows_g[i]["recovery_dates"])
                for i in range(n_seasons)
                if rec_list[i]
            ]
            if len(rec_dates_vals) > 0:
                median_rec_dates: str | float = float(np.median(rec_dates_vals))
            else:
                median_rec_dates = ""

            tot_bets = int(sum(int(r["n_bets"]) for r in rows_g))
            tot_forced = int(sum(int(r["n_forced"]) for r in rows_g))
            tot_floored = int(sum(int(r["n_floored"]) for r in rows_g))
            tot_dropped = int(sum(int(r["n_dropped"]) for r in rows_g))

            if any(ruined_list):
                sum_lw: str | float = ""
            else:
                sum_lw = float(sum(float(r["final_log_wealth"]) for r in rows_g))

            median_roi = float(np.median(roi_list))
            min_roi = float(np.min(roi_list))
            max_roi = float(np.max(roi_list))

            sum_row: dict[str, str | int | float] = {
                "row_type": "summary",
                "config": config_name,
                "min_stake": min_stake_val,
                "agent": agent_name,
                # Campi di stagione vuoti nelle righe di riepilogo
                "season": "",
                "fit_through": "",
                "n_dates": "",
                "final_wealth": "",
                "final_log_wealth": "",
                "max_drawdown": "",
                "recovery_dates": "",
                "recovered": "",
                "ruined": "",
                "ruin_date": "",
                # Totali dei contatori popolano le rispettive colonne
                "n_bets": tot_bets,
                "n_forced": tot_forced,
                "n_floored": tot_floored,
                "n_dropped": tot_dropped,
                "roi": "",
                # Statistiche di riepilogo
                "median_final_wealth": median_w,
                "sd_log_wealth": sd_lw,
                "n_unruined": n_unruined,
                "ruin_rate": ruin_r,
                "median_max_drawdown": median_dd,
                "max_max_drawdown": max_dd,
                "recovery_rate": rec_rate,
                "median_recovery_dates": median_rec_dates,
                "sum_final_log_wealth": sum_lw,
                "median_roi": median_roi,
                "min_roi": min_roi,
                "max_roi": max_roi,
            }
            summary_rows.append(sum_row)

    return season_rows + summary_rows
