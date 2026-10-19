"""Stagione 2023-24 giocata come in KellyBench, con un bankroll iniziale di £100 000.

KellyBench fa vivere a ogni modello la stagione 2023-24 della Premier League giorno per giorno,
e nella Tabella 2 del paper riporta i risultati riscalati a un bankroll iniziale di £100 000
(nota 2.9 §0). Qui gli agenti del progetto, con il Modulo 1 Elo e i parametri congelati di
config/frozen_params.toml, giocano la realizzazione osservata del 2023-24: gli esiti veri, nello
stesso ordine di date, con lo stesso ambiente delle altre esecuzioni.

Il floor di puntata di KellyBench non è certo (£0.01 o £1, nota 2.9): si eseguono tre
configurazioni, senza floor, £0.01 e £1. L'ambiente lavora in unità del bankroll iniziale,
quindi F = F_£ / £100 000; i rapporti B0/F sono 10^7 e 10^5, contro 22 000 e 220 delle
configurazioni con B0 = £220.

È un'esecuzione descrittiva aggiuntiva sul test set, con gli stessi agenti, lo stesso fit (2020-21)
e gli stessi parametri dell'esecuzione unica: nessun parametro si sceglie o si cambia qui. Senza
floor la log-ricchezza non dipende dalla scala, e coincide con quella della realizzazione
osservata dell'esecuzione unica.

Uscite (KELLYBENCH_COLUMNS):
- righe "summary", per configurazione e agente: bankroll iniziale e finale in £, rendimento della
  stagione, log-ricchezza finale, drawdown massimo, numero di puntate (totali, forzate, alzate al
  floor, scartate), totale puntato in £, rendimento per sterlina puntata, rovina e data di rovina;
- righe "path": bankroll in £ dopo ogni data, per configurazione e agente.
E esiste solo con F > 0, come nelle altre esecuzioni.
"""

import math
from collections.abc import Sequence
from typing import Final

import numpy as np

from shk.kelly.environment import run_paired_backtest
from shk.kelly.metrics import wealth_max_drawdown
from shk.model.frozen_agents import AGENT_ORDER, build_frozen_agents, build_supervisors, check_frozen_constants
from shk.model.frozen_params import load_frozen_params
from shk.model.module1 import MODULE1_ELO
from shk.model.test_run import TEST_FIT, TEST_SEASON, SeasonData, load_season_data, season_params_path
from shk.model.training_calibration import SharedShin

KELLYBENCH_BANKROLL_GBP: Final[float] = 100_000.0
FLOORS_GBP: Final[tuple[tuple[str, float], ...]] = (("none", 0.0), ("gbp_0.01", 0.01), ("gbp_1", 1.0))
KELLYBENCH_COLUMNS: Final[tuple[str, ...]] = (
    "row_type", "config", "floor_gbp", "min_stake", "agent", "date", "initial_bankroll_gbp", "bankroll_gbp",
    "season_return", "final_log_wealth", "max_drawdown", "n_bets", "n_forced", "n_floored", "n_dropped",
    "total_staked_gbp", "return_per_gbp_staked", "ruined", "ruin_date",
)


def _date(value: np.datetime64) -> str:
    return str(np.datetime_as_string(value, unit="D"))


def kellybench_records(sd: SeasonData, floors: Sequence[tuple[str, float]] = FLOORS_GBP,
                       bankroll_gbp: float = KELLYBENCH_BANKROLL_GBP) -> list[dict[str, object]]:
    """Righe "summary" e "path" della stagione per ogni configurazione di floor.

    Solleva
    -------
    ValueError
        Se il bankroll non è positivo o un floor è negativo.
    """
    if not bankroll_gbp > 0.0:
        raise ValueError(f"bankroll_gbp must be positive, got {bankroll_gbp}")
    params = load_frozen_params(season_params_path(sd))
    check_frozen_constants(params)
    supervisors = build_supervisors(params, sd.inp, None, sd.devig_method)
    shin = SharedShin(sd.devig_method)
    records: list[dict[str, object]] = []
    for config, floor_gbp in floors:
        if floor_gbp < 0.0:
            raise ValueError(f"floor must be non-negative, got {floor_gbp}")
        min_stake = floor_gbp / bankroll_gbp
        agents = build_frozen_agents(params, min_stake, supervisors, shin, sd.fit, AGENT_ORDER)
        runs = run_paired_backtest(agents, sd.inp.dates, sd.inp.probs, sd.inp.odds, sd.inp.outcomes, min_stake,
                                   record_stakes=True, fallback_policy=params.fixed["fallback_policy"])
        for run in runs:
            wealth = run.wealth[0]
            staked = float(run.staked[0].sum()) * bankroll_gbp
            final = float(wealth[-1]) * bankroll_gbp
            ruined = bool(run.ruined[0])
            base = {"config": config, "floor_gbp": floor_gbp, "min_stake": min_stake, "agent": run.name,
                    "initial_bankroll_gbp": bankroll_gbp}
            records.append({
                **base, "row_type": "summary", "date": "", "bankroll_gbp": final,
                "season_return": float(wealth[-1]) - 1.0,
                "final_log_wealth": math.log(float(wealth[-1])) if wealth[-1] > 0.0 else -math.inf,
                "max_drawdown": float(wealth_max_drawdown(run.wealth)[0]),
                "n_bets": int(run.n_bets[0]), "n_forced": int(run.n_forced[0]), "n_floored": int(run.n_floored[0]),
                "n_dropped": int(run.n_dropped[0]), "total_staked_gbp": staked,
                "return_per_gbp_staked": (final - bankroll_gbp) / staked if staked > 0.0 else "",
                "ruined": ruined,
                "ruin_date": _date(run.dates[int(run.ruin_date_index[0])]) if ruined else "",
            })
            for date, w in zip(run.dates, wealth[1:]):
                records.append({**base, "row_type": "path", "date": _date(date), "bankroll_gbp": float(w) * bankroll_gbp})
    return records


def evaluate_kellybench(module1: str = MODULE1_ELO) -> list[dict[str, object]]:
    """Carica il 2023-24 con il fit 2020-21 ed esegue le tre configurazioni di floor."""
    return kellybench_records(load_season_data(TEST_SEASON, TEST_FIT, module1))
