"""La versione principale dello schema nelle analisi fatte prima che esistesse.

Versione principale (TESI §4.8): riferimento = stagione di calibrazione, soglie dell'allarme per
stagione (shk.model.season_thresholds.season_setups, SEED_S26), allarme se basta una delle due
statistiche, diagnosi a due termini (shk.model.two_fold_diagnosis.diagnosis_setups, SEED_S27), fermo
fino a fine stagione dopo un errore strutturale. È C3_ref_stop_season_dx di us_c27, ricostruita qui
con le stesse soglie: con la regola R1 sulle stagioni vere coincide con quella pubblicata.

Le analisi dei capitoli 5 e 6 fatte prima della versione principale usavano le versioni iniziali
(soglie per giornata, diagnosi a tre termini). Qui la versione principale le sostituisce:
- us_c29: regole di scelta dell'esito R1, R2, R3 sulle 19 stagioni vere (rule_agents);
- us_c30: stagione 2023-24, vera e ricostruite con i seed di us_c14 (run_test_instance);
- us_c31: popolazione di strategie (MAIN_POPULATION_ARMS, run_main_population_season);
- us_c32: evoluzione con due geni in più (shk.model.evolution_main).

Nomi degli agenti:
- "M": versione principale; "M_clear": come M, ma riprende quando l'allarme si spegne;
- "M_day": come M, con le soglie dell'allarme per giornata («soglie per giornata» nella tesi);
- prefisso "R2_" o "R3_": stessa versione con la regola di scelta dell'esito R2 o R3;
- "B_0.25", "R2_brake", "R3_brake": quarto di Kelly senza supervisore con le regole R1, R2, R3.
"""

from collections.abc import Mapping, Sequence
from typing import Final, NamedTuple

import numpy as np
import pandas as pd

from shk.kelly.agents import AGENT_A_LAMBDA, AGENT_B_LAMBDA, Agent, FractionalKellyAgent
from shk.kelly.environment import run_paired_backtest
from shk.kelly.outcome_rules import with_outcome_rule
from shk.model.agent_c import SCHEME_STOP_CLEAR, SCHEME_STOP_SEASON, Module2Supervisor, ReferenceData, SchemeAgent
from shk.model.frozen_agents import check_frozen_constants, n_alarms, scheme_window, share_lambda_zero
from shk.model.frozen_params import FrozenParams, load_frozen_params
from shk.model.paired_backtest import CONFIGURATIONS
from shk.model.scheme_reference_run import ReferenceSetup
from shk.model.season_bootstrap import reconstruct_season, season_block_length
from shk.model.season_input import SeasonInput
from shk.model.season_thresholds import season_setups
from shk.model.two_fold_diagnosis import ReferenceDiagnosis, TwoFoldSchemeAgent, diagnosis_setups
from shk.model.validation_run import METRICS, ValidationSeason, run_metrics

THRESHOLDS: Final[tuple[str, ...]] = ("day", "season")
DIAGNOSES: Final[tuple[str, ...]] = ("three", "two")
RULE_ARMS: Final[tuple[str, ...]] = ("B_0.25", "R2_brake", "R3_brake", "M", "R2_M", "R3_M")
RULE_REFERENCES: Final[dict[str, str]] = {"M": "B_0.25", "R2_M": "R2_brake", "R3_M": "R3_brake"}
TEST_ARMS: Final[tuple[str, ...]] = ("A", "B_0.25", "M", "M_clear", "M_day")
MAIN_POPULATION_ARMS: Final[tuple[str, ...]] = (
    "A", "B_0.25", "R2_brake", "R3_brake", "M", "M_clear", "R3_M", "R3_M_clear",
)


class MainSetup(NamedTuple):
    """Soglie di un fit: per giornata, per stagione e della diagnosi a due termini."""

    per_date: ReferenceSetup
    per_season: ReferenceSetup
    diagnosis: ReferenceDiagnosis


def main_setups(train: pd.DataFrame, params: FrozenParams) -> dict[str, MainSetup]:
    """Per fit, le soglie della versione principale e delle sue varianti, con i seed di us_c26 e us_c27."""
    per_date, per_season, _ = season_setups(train, params)
    diagnoses, _ = diagnosis_setups(train, params)
    return {fit: MainSetup(per_date[fit], per_season[fit], diagnoses[fit]) for fit in per_date}


def reference_supervisor(params: FrozenParams, inp: SeasonInput, setup: MainSetup,
                         devig_method: str = "shin") -> Module2Supervisor:
    """Supervisore con la stagione di calibrazione come riferimento, condiviso dagli agenti di una stagione."""
    return Module2Supervisor(inp.season, inp.dates, inp.x, list(params.fixed["covariates"]), scheme_window(params),
                             devig_method=devig_method,
                             reference=ReferenceData(setup.per_date.x, setup.per_date.delta))


def main_agent(name: str, params: FrozenParams, setup: MainSetup, supervisor: Module2Supervisor, rule: str = "R1",
               stop: str = SCHEME_STOP_SEASON, thresholds: str = "season", diagnosis: str = "two",
               base_lambda: float | None = None, kappa: float | None = None) -> Agent:
    """Schema con riferimento alla stagione di calibrazione; i default sono la versione principale.

    thresholds "season" o "day" sceglie le soglie dell'allarme; diagnosis "two" o "three" la diagnosi
    (a tre termini con la soglia strutturale di scheme_reference_run, come C3_ref).
    """
    if thresholds not in THRESHOLDS or diagnosis not in DIAGNOSES:
        raise ValueError(f"thresholds must be in {THRESHOLDS} and diagnosis in {DIAGNOSES}")
    k = float(params.calibrated["c1_kappa"]) if kappa is None else float(kappa)
    base = float(params.fixed["c0_lambda"]) if base_lambda is None else float(base_lambda)
    thr = setup.per_season if thresholds == "season" else setup.per_date
    if diagnosis == "two":
        return with_outcome_rule(TwoFoldSchemeAgent, rule)(name, supervisor, k, thr.mean_threshold,
                                                           thr.dispersion_threshold, setup.diagnosis, stop,
                                                           base_lambda=base)
    return with_outcome_rule(SchemeAgent, rule)(name, supervisor, k, thr.mean_threshold, thr.dispersion_threshold,
                                                setup.per_date.structural_threshold, stop, base_lambda=base,
                                                reference=True)


def build_agents(params: FrozenParams, setup: MainSetup, supervisor: Module2Supervisor,
                 arms: Sequence[str]) -> list[Agent]:
    """Agenti dei nomi in arms (vedi modulo)."""
    out = []
    for name in arms:
        if name in ("A", "B_0.25", "R2_brake", "R3_brake"):
            rule = name[:2] if name.startswith("R") else "R1"
            lam = AGENT_A_LAMBDA if name == "A" else AGENT_B_LAMBDA
            out.append(with_outcome_rule(FractionalKellyAgent, rule)(name, lam=lam))
            continue
        rule, base = (name[:2], name[3:]) if name[:3] in ("R2_", "R3_") else ("R1", name)
        variants = {"M": {}, "M_clear": {"stop": SCHEME_STOP_CLEAR}, "M_day": {"thresholds": "day"}}
        if base not in variants:
            raise ValueError(f"unknown arm {name!r}")
        out.append(main_agent(name, params, setup, supervisor, rule=rule, **variants[base]))
    return out


def run_rules_season(params_path: str, setups: Mapping[str, MainSetup], season: ValidationSeason,
                     arms: Sequence[str] = RULE_ARMS) -> list[dict]:
    """La stagione vera nelle tre configurazioni di puntata minima: una riga per configurazione × agente."""
    params = load_frozen_params(params_path)
    inp, setup = season.inp, setups[season.fit]
    rows = []
    for config, min_stake in CONFIGURATIONS:
        agents = build_agents(params, setup, reference_supervisor(params, inp, setup), arms)
        runs = run_paired_backtest(agents, inp.dates, inp.probs, inp.odds, inp.outcomes, min_stake,
                                   fallback_policy=params.fixed["fallback_policy"])
        for run, agent in zip(runs, agents):
            final = float(run.wealth[0, -1])
            rows.append({"season": inp.season, "fit_through": season.fit, "config": config, "agent": run.name,
                         "log_wealth": float(np.log(final)) if final > 0.0 else -np.inf,
                         "n_bets": int(run.n_bets[0]), "n_alarms": n_alarms(agent),
                         "share_days_zero": share_lambda_zero(agent)})
    return rows


def run_test_instance(params: FrozenParams, setups: Mapping[str, MainSetup], inp: SeasonInput, fit: str,
                      devig_method: str = "shin", arms: Sequence[str] = TEST_ARMS) -> np.ndarray:
    """Una stagione (vera o ricostruita) nelle tre configurazioni: (C, len(arms), M) come validation_run."""
    setup = setups[fit]
    out = np.full((len(CONFIGURATIONS), len(arms), len(METRICS)), np.nan)
    for ci, (_, min_stake) in enumerate(CONFIGURATIONS):
        agents = build_agents(params, setup, reference_supervisor(params, inp, setup, devig_method), arms)
        runs = run_paired_backtest(agents, inp.dates, inp.probs, inp.odds, inp.outcomes, min_stake,
                                   fallback_policy=params.fixed["fallback_policy"])
        for run, agent in zip(runs, agents):
            out[ci, list(arms).index(run.name)] = run_metrics(run, agent)
    return out


def run_test_chunk(params_path: str, setups: Mapping[str, MainSetup], inp: SeasonInput, fit: str,
                   seed_seqs: Sequence[np.random.SeedSequence], block_length: float,
                   devig_method: str = "shin") -> np.ndarray:
    """Stagioni ricostruite di inp per i seed dati: (C, A, M, len(seed_seqs))."""
    params = load_frozen_params(params_path)
    covariates = list(params.fixed["covariates"])
    outs = []
    for ss in seed_seqs:
        rec = reconstruct_season(inp, np.random.default_rng(ss), block_length, covariates=covariates)
        outs.append(run_test_instance(params, setups, rec, fit, devig_method))
    return np.stack(outs, axis=-1)


def run_main_population_instance(params: FrozenParams, setups: Mapping[str, MainSetup], inp: SeasonInput, fit: str,
                                 arms: Sequence[str] = MAIN_POPULATION_ARMS) -> np.ndarray:
    """Una stagione senza puntata minima: capitale (len(arms), D+1) giornata per giornata, W(0) = 1."""
    setup = setups[fit]
    agents = build_agents(params, setup, reference_supervisor(params, inp, setup), arms)
    runs = run_paired_backtest(agents, inp.dates, inp.probs, inp.odds, inp.outcomes, 0.0,
                               fallback_policy=params.fixed["fallback_policy"])
    return np.stack([run.wealth[0] for run in runs])


def run_main_population_season(params_path: str, setups: Mapping[str, MainSetup], season: ValidationSeason,
                               seed_seqs: Sequence[np.random.SeedSequence]) -> tuple[np.ndarray, np.ndarray, int]:
    """Stagione vera e ricostruite (seed come in us_c21): (osservata (A, D+1), ricostruite (N, A, D+1), L_PW)."""
    params = load_frozen_params(params_path)
    check_frozen_constants(params)
    covariates = list(params.fixed["covariates"])
    l_pw = season_block_length(season.inp)
    observed = run_main_population_instance(params, setups, season.inp, season.fit)
    recs = np.full((len(seed_seqs),) + observed.shape, np.nan)
    for k, ss in enumerate(seed_seqs):
        rec = reconstruct_season(season.inp, np.random.default_rng(ss), l_pw, covariates=covariates)
        recs[k] = run_main_population_instance(params, setups, rec, season.fit)
    return observed, recs, l_pw
