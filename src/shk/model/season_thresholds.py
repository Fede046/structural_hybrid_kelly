"""Soglie dell'allarme calibrate sull'intera stagione, per lo schema con riferimento fisso.

Le soglie di scheme_reference_run (agent_c.calibrate_reference_thresholds) danno all'allarme il
livello α = 0.05 a ogni giornata di decisione. In una stagione le decisioni sono un centinaio, su
finestre che si sovrappongono: la probabilità di almeno un falso allarme nella stagione è molto più
alta di α, e con lo stop fino a fine stagione un solo falso allarme con diagnosi strutturale ferma
lo schema per il resto della stagione. Nel mondo simulato senza alcun cambiamento
(shk.model.edge_simulation) lo schema si ferma così in più di metà delle stagioni.

Qui il livello α vale per l'intera stagione: su ogni ricampionamento a blocchi della stagione di
calibrazione si calcolano le due F con segno (media e Brown-Forsythe, agent_c.reference_statistics)
a tutte le giornate di decisione del calendario della stagione di calibrazione, cioè sulle finestre
delle ultime W partite con Date < d, per ogni data d con almeno W partite precedenti, e si prende il
massimo sulla stagione. Le soglie sono le statistiche d'ordine dei due massimi al livello α/2
ciascuna (Bonferroni): la probabilità di almeno un allarme in una stagione senza cambiamenti è al
più α. La soglia strutturale della diagnosi resta quella di scheme_reference_run.

Versioni: "C3_ref_season" e "C3_ref_stop_season", uguali a C3_ref e C3_ref_stop tranne che per le
due soglie dell'allarme. È una variante introdotta dopo la simulazione di us_c25, non dopo aver
visto il capitale sulle stagioni di validazione; resta comunque successiva alle altre versioni.

Seed delle soglie: SeedSequence(SEED_S26).spawn(numero di fit) in ordine cronologico.
"""

from collections.abc import Mapping, Sequence
from typing import Final

import numpy as np
import pandas as pd

from shk.kelly.agents import Agent
from shk.kelly.environment import run_paired_backtest
from shk.model.agent_c import (
    N_BOOT,
    SCHEME_STOP_CLEAR,
    SCHEME_STOP_SEASON,
    Module2Supervisor,
    ReferenceData,
    SchemeAgent,
    reference_statistics,
)
from shk.model.frozen_agents import n_alarms, scheme_window, share_lambda_zero
from shk.model.frozen_params import FrozenParams, load_frozen_params
from shk.model.paired_backtest import CONFIGURATIONS
from shk.model.scheme_reference_run import ReferenceSetup, build_reference_agents, reference_setups
from shk.model.scheme_run import fit_block_length
from shk.model.season_input import season_input_from_frame, training_seasons
from shk.model.timing_placebo import SeasonSchedules, extract_schedules
from shk.model.validation_run import ValidationSeason
from shk.stats.calibration import compute_order_statistic_index, moving_block_indices
from shk.stats.false_rejection import ALPHA

SEED_S26: Final[int] = 20261113
SEASON_ARMS: Final[dict[str, str]] = {"C3_ref_season": "R1", "C3_ref_stop_season": "R1"}
PER_DATE_ARMS: Final[tuple[str, ...]] = ("C3_ref", "C3_ref_stop")
RUN_ARMS: Final[tuple[str, ...]] = ("B_0.25",) + PER_DATE_ARMS + tuple(SEASON_ARMS)
SEASON_THRESHOLD_COLUMNS: Final[tuple[str, ...]] = (
    "fit", "window", "block_length", "n_reference", "n_decisions", "structural_threshold",
    "mean_threshold", "dispersion_threshold", "season_mean_threshold", "season_dispersion_threshold",
)


def decision_ends(dates: np.ndarray, window: int) -> np.ndarray:
    """Per ogni data di decisione, il numero di partite con Date < d, quando sono almeno window.

    dates è non decrescente. La finestra della decisione è fatta delle ultime window partite precedenti.
    """
    d = np.asarray(dates).astype("datetime64[ns]")
    if d.ndim != 1 or np.any(d[1:] < d[:-1]):
        raise ValueError("dates must be 1-dimensional and non-decreasing")
    counts = np.searchsorted(d, np.unique(d), side="left")
    return counts[counts >= window]


def calibrate_season_alarm_thresholds(delta: np.ndarray, dates: np.ndarray, window: int, block_length: int,
                                      rng: np.random.Generator, n_boot: int = N_BOOT,
                                      alpha: float = ALPHA) -> tuple[float, float]:
    """Soglie (media, dispersione) dell'allarme con livello α sull'intera stagione (vedi modulo)."""
    y = np.asarray(delta, dtype=np.float64)
    ends = decision_ends(dates, window)
    if y.ndim != 1 or y.shape[0] != np.asarray(dates).shape[0] or ends.shape[0] == 0:
        raise ValueError("need delta and dates with the same length and at least one decision with W earlier matches")
    idx = moving_block_indices(y.shape[0], block_length, n_boot, rng)
    windows = idx[:, (ends[:, None] - window + np.arange(window)[None, :])]      # (n_boot, decisioni, W)
    f_mean, f_disp = reference_statistics(y, y[windows].reshape(-1, window))
    k = compute_order_statistic_index(n_boot, alpha / 2.0)
    max_mean = np.sort(f_mean.reshape(n_boot, -1).max(axis=1))
    max_disp = np.sort(f_disp.reshape(n_boot, -1).max(axis=1))
    return float(max_mean[k - 1]), float(max_disp[k - 1])


def season_level_setup(setup: ReferenceSetup, dates: np.ndarray, window: int, block_length: int,
                       rng: np.random.Generator) -> ReferenceSetup:
    """La stessa calibrazione con le due soglie dell'allarme al livello α sull'intera stagione."""
    mean_thr, disp_thr = calibrate_season_alarm_thresholds(setup.delta, dates, window, block_length, rng)
    return setup._replace(mean_threshold=mean_thr, dispersion_threshold=disp_thr)


def season_setups(train: pd.DataFrame, params: FrozenParams,
                  seed: int = SEED_S26) -> tuple[dict[str, ReferenceSetup], dict[str, ReferenceSetup], list[dict]]:
    """Per fit: calibrazione per giornata (quella di scheme_reference_run), per stagione e righe delle soglie."""
    covariates = list(params.fixed["covariates"])
    per_date = reference_setups(train, params)
    fits = training_seasons(train)
    w = scheme_window(params)
    per_season, records = {}, []
    for fit, seq in zip(fits, np.random.SeedSequence(seed).spawn(len(fits))):
        inp = season_input_from_frame(train, fit, covariates)
        length = fit_block_length(inp)
        per_season[fit] = season_level_setup(per_date[fit], inp.dates, w, length, np.random.default_rng(seq))
        records.append({
            "fit": fit, "window": w, "block_length": length, "n_reference": int(inp.delta.shape[0]),
            "n_decisions": int(decision_ends(inp.dates, w).shape[0]),
            "structural_threshold": per_date[fit].structural_threshold,
            "mean_threshold": per_date[fit].mean_threshold, "dispersion_threshold": per_date[fit].dispersion_threshold,
            "season_mean_threshold": per_season[fit].mean_threshold,
            "season_dispersion_threshold": per_season[fit].dispersion_threshold})
    return per_date, per_season, records


def season_agents(params: FrozenParams, setup: ReferenceSetup, supervisor: Module2Supervisor) -> list[Agent]:
    """C3_ref_season e C3_ref_stop_season: lo schema con riferimento fisso e le soglie di setup."""
    kappa, base = float(params.calibrated["c1_kappa"]), float(params.fixed["c0_lambda"])
    return [SchemeAgent(name, supervisor, kappa, setup.mean_threshold, setup.dispersion_threshold,
                        setup.structural_threshold, stop, base_lambda=base, reference=True)
            for name, stop in zip(SEASON_ARMS, (SCHEME_STOP_CLEAR, SCHEME_STOP_SEASON))]


def _agents(params: FrozenParams, per_date: ReferenceSetup, per_season: ReferenceSetup,
            season: ValidationSeason) -> list[Agent]:
    inp = season.inp
    supervisor = Module2Supervisor(inp.season, inp.dates, inp.x, list(params.fixed["covariates"]),
                                   scheme_window(params), reference=ReferenceData(per_date.x, per_date.delta))
    return (build_reference_agents(params, per_date, supervisor, ("B_0.25",) + PER_DATE_ARMS)
            + season_agents(params, per_season, supervisor))


def run_real_season(params_path: str, per_date: Mapping[str, ReferenceSetup],
                    per_season: Mapping[str, ReferenceSetup], season: ValidationSeason) -> list[dict]:
    """La stagione vera nelle tre configurazioni di puntata minima: una riga per configurazione × agente."""
    params = load_frozen_params(params_path)
    inp = season.inp
    rows = []
    for config, min_stake in CONFIGURATIONS:
        agents = _agents(params, per_date[season.fit], per_season[season.fit], season)
        runs = run_paired_backtest(agents, inp.dates, inp.probs, inp.odds, inp.outcomes, min_stake,
                                   fallback_policy=params.fixed["fallback_policy"])
        for run, agent in zip(runs, agents):
            final = float(run.wealth[0, -1])
            rows.append({"season": inp.season, "fit_through": season.fit, "config": config, "agent": run.name,
                         "log_wealth": float(np.log(final)) if final > 0.0 else -np.inf,
                         "n_alarms": n_alarms(agent), "share_days_zero": share_lambda_zero(agent)})
    return rows


def run_schedule_season(params_path: str, per_date: Mapping[str, ReferenceSetup],
                        per_season: Mapping[str, ReferenceSetup], season: ValidationSeason) -> SeasonSchedules:
    """Calendari senza puntata minima delle due versioni con soglie per stagione (per il controllo placebo)."""
    params = load_frozen_params(params_path)
    agents = [a for a in _agents(params, per_date[season.fit], per_season[season.fit], season)
              if a.name == "B_0.25" or a.name in SEASON_ARMS]
    return extract_schedules(params, season, agents, SEASON_ARMS)




def summary_rows(season_rows: Sequence[Mapping], arms: Sequence[str] = RUN_ARMS) -> list[dict]:
    """Per configurazione × agente di arms: capitale tipico, stagioni meglio e peggio del quarto di Kelly, allarmi."""
    df = pd.DataFrame(list(season_rows))
    out = []
    for config in df["config"].unique():
        rows = df[df["config"] == config]
        base = rows[rows["agent"] == "B_0.25"].set_index("season")["log_wealth"]
        for agent in arms:
            g = rows[rows["agent"] == agent].set_index("season")
            d = g["log_wealth"] - base.loc[g.index]
            out.append({"config": config, "agent": agent, "n_seasons": len(g),
                        "typical_capital": float(np.exp(g["log_wealth"].mean())),
                        "seasons_better": int((d > 1e-12).sum()), "seasons_worse": int((d < -1e-12).sum()),
                        "seasons_with_stop": int((g["share_days_zero"] > 0).sum()) if agent != "B_0.25" else "",
                        "mean_alarms": float(g["n_alarms"].mean()) if agent != "B_0.25" else "",
                        "share_days_zero": float(g["share_days_zero"].mean()) if agent != "B_0.25" else ""})
    return out
