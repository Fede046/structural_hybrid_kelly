"""Stagione di riferimento scelta guardando il passato (esplorativo, branch riferimento-dal-passato).

Nella versione definitiva (shk.model.main_version, "F") il supervisore confronta le ultime W partite
con la stagione di calibrazione del fit che prevede la stagione: 2000-01, 2010-11 o 2020-21. Il
riferimento è quindi fissato una volta per tutte, e se la stagione di calibrazione è insolita (il
2020-21, giocato a porte chiuse) l'allarme misura il peggioramento rispetto a una stagione che
sbagliava già molto.

Qui il riferimento di una stagione s, prevista dal fit f, si sceglie fra le stagioni anteriori a s,
con i residui dello stesso modello (parametri del fit f, Elo che scorre su tutte le partite): sono
dati che l'agente avrebbe avuto prima dell'inizio di s. Regole:
- "calibrazione": la stagione di calibrazione f (la versione definitiva, con le sue soglie);
- "precedente": la stagione più recente anteriore a s;
- "mediana": fra le stagioni anteriori a s, quella con la dispersione dei residui più vicina alla
  mediana delle dispersioni (a parità, la più recente): un riferimento «tipico», scelto senza
  guardare il capitale;
- "migliore": la stagione che, usata come riferimento della versione definitiva sulla stagione
  precedente s', avrebbe dato il capitale più alto su s' (fra le stagioni anteriori a s'; a parità
  la più recente; senza candidati, la stagione di calibrazione). È la scelta «ottimale guardando il
  passato», con un solo anno di prova.
Lavoratore, soglie (per stagione) e diagnosi (a due termini) sono quelli della versione definitiva;
per un riferimento diverso dalla calibrazione soglie e diagnosi si ricalibrano sulla stagione scelta,
con lo stesso procedimento e seed propri (SEED_S40).

Le stagioni di training dei fit successivi a f (2010-11 e 2000-01 per f = 2020-21, 2010-11 per
f = 2000-01) non hanno residui con i parametri di f nella catena comune e restano fuori dai candidati.

Lato lavoratore la stessa idea è la scelta del fit: per la stagione s, fra i fit stimati prima di s,
quello con la log-loss migliore sulla stagione precedente (worker_fit_choice).
"""

from collections.abc import Mapping, Sequence
from typing import Final, NamedTuple

import numpy as np
import pandas as pd

from shk.kelly.environment import run_paired_backtest
from shk.model.elo_fit import parse_season_start_year
from shk.model.frozen_params import FrozenParams, load_frozen_params
from shk.model.main_version import MainSetup, build_agents, reference_supervisor
from shk.model.model_age import dispersion
from shk.model.module2_data import build_module2_frame
from shk.model.residuals import model_residuals_data
from shk.model.season_input import SeasonInput, season_input_from_frame
from shk.model.season_thresholds import season_setups
from shk.model.two_fold_diagnosis import diagnosis_setups

SEED_S40: Final[int] = 20261120
FIRST_YEAR: Final[int] = 2002          # prima stagione con la terna B365 dopo il 2000-01
RULES: Final[tuple[str, ...]] = ("calibrazione", "precedente", "mediana", "migliore")
ARMS: Final[tuple[str, ...]] = ("B_0.25", "F")


def year(season: str) -> int:
    return parse_season_start_year(season)


def fit_frame(df: pd.DataFrame, schedule: Mapping[str, Mapping[str, Sequence[str]]], fit: str) -> pd.DataFrame:
    """DataFrame del Modulo 2 con i residui del fit su tutte le stagioni non di training dal 2002-03.

    Le righe del fit sono la sua stagione di calibrazione (ruolo training) e tutte le altre stagioni
    (ruolo validation); le righe di training degli altri fit restano, con i loro parametri.
    """
    training = {s for e in schedule.values() for s in e["training"]}
    seasons = sorted({s for s in df["season"].unique() if year(s) >= FIRST_YEAR and s not in training}, key=year)
    sched = {g: {"training": list(e["training"]), "validation": []} for g, e in schedule.items()}
    sched[fit]["validation"] = seasons
    frame = build_module2_frame(model_residuals_data(df, sched))
    return frame[frame["fit_through"] == fit].reset_index(drop=True)


def available_seasons(frame: pd.DataFrame, before: str) -> list[str]:
    """Stagioni del DataFrame di un fit anteriori a before, in ordine cronologico."""
    return sorted((s for s in frame["season"].unique() if year(s) < year(before)), key=year)


def candidate_setup(frame: pd.DataFrame, season: str, params: FrozenParams, fit: str) -> MainSetup:
    """Soglie per stagione e diagnosi a due termini calibrate sulla stagione season (residui del fit)."""
    part = frame[frame["season"] == season].assign(role="training")
    seed = int(np.random.SeedSequence([SEED_S40, year(fit), year(season)]).generate_state(1)[0])
    per_date, per_season, _ = season_setups(part, params, seed=seed)
    diagnoses, _ = diagnosis_setups(part, params, seed=seed)
    return MainSetup(per_date[season], per_season[season], diagnoses[season])


class RunResult(NamedTuple):
    log_wealth_f: float
    log_wealth_b: float
    share_reduced: float
    alarm_days: int


def run_with_reference(params_path: str, setup: MainSetup, inp: SeasonInput, min_stake: float) -> RunResult:
    """Versione definitiva e quarto di Kelly su una stagione con il riferimento dato."""
    params = load_frozen_params(params_path)
    agents = build_agents(params, setup, reference_supervisor(params, inp, setup), ARMS)
    runs = run_paired_backtest(agents, inp.dates, inp.probs, inp.odds, inp.outcomes, min_stake,
                               fallback_policy=params.fixed["fallback_policy"])
    logw = {}
    for run in runs:
        final = float(run.wealth[0, -1])
        logw[run.name] = float(np.log(final)) if final > 0.0 else -np.inf
    lam = np.array(list(agents[1].lambda_by_date.values()))
    reduced = lam < 0.25 - 1e-12
    return RunResult(logw["F"], logw["B_0.25"], float(reduced.mean()) if lam.size else float("nan"),
                     int(reduced.sum()))


def median_choice(candidates: Sequence[str], disp: Mapping[str, float]) -> str:
    """La stagione con la dispersione più vicina alla mediana (a parità la più recente)."""
    med = float(np.median([disp[c] for c in candidates]))
    return min(reversed(list(candidates)), key=lambda c: abs(disp[c] - med))


def best_choice(scores: Mapping[str, float], fallback: str) -> str:
    """La stagione con il capitale più alto (a parità entro 1e-12 la più recente); fallback se vuoto."""
    if not scores:
        return fallback
    top = max(scores.values())
    return max((c for c, v in scores.items() if v >= top - 1e-12), key=year)


def worker_fit_choice(log_loss: Mapping[tuple[str, str], float], fits: Sequence[str], previous: str,
                      fallback: str) -> str:
    """Fit con la log-loss più bassa sulla stagione previous, fra quelli stimati prima di previous.

    Solo fit anteriori a previous, perché su previous siano fuori campione; a parità il più recente;
    senza candidati, fallback (il fit congelato).
    """
    allowed = [f for f in fits if year(f) < year(previous) and (f, previous) in log_loss]
    if not allowed:
        return fallback
    return min(allowed, key=lambda f: (log_loss[(f, previous)], -year(f)))
