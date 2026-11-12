"""Lo schema con riferimento fisso in un mondo simulato in cui il vantaggio è noto e può sparire.

Sulle stagioni vere il modello non ha un vantaggio sul mercato, quindi non puntare è sempre la scelta
migliore e il capitale non può dire se il supervisore interviene al momento giusto
(shk.model.timing_placebo). Qui si prova lo schema dove la domanda ha una risposta: date, quote,
previsioni p̂ dell'Elo e covariate sono quelle vere, e si simulano solo gli esiti, da una probabilità
vera p* che dipende da un parametro a:

    p*_j ∝ q_j^(1−a) · p̂_j^a        (q di Shin dalle quote)

a = 1: il modello ha ragione (p* = p̂) e il mercato sbaglia, quindi puntare rende; a = 0: ha ragione il
mercato (p* = q), come sulle stagioni vere; a = −1: la verità sta dalla parte opposta del modello
rispetto al mercato. Le previsioni restano quelle dell'Elo vero e non si aggiornano con gli esiti
simulati: prima della partita le stagioni simulate sono identiche, e il cambiamento si può vedere
solo dagli errori, come nello schema.

Scenari (SCENARIOS), con il cambiamento a metà stagione (prima giornata della seconda metà delle date):
- "stable_edge": a = 1 per tutta la stagione. Misura il costo dei falsi allarmi;
- "edge_vanishes": a = 1, poi 0. Il vantaggio sparisce;
- "edge_reverses": a = 1, poi −1. Cambiamento più grande;
- "no_edge": a = 0 per tutta la stagione. Controllo: come sulle stagioni vere;
- "composition_shift": a = 1 per tutta la stagione, ma le partite sono riordinate: nella seconda metà
  finiscono quelle per cui la regressione di riferimento prevede più dispersione di δ
  (composition_shift). Il legame fra modello e realtà non cambia, cambia solo il tipo di partite:
  è il caso che la diagnosi deve chiamare «errore nei dati».
Il riferimento dello schema è una copia indipendente della stessa stagione, simulata con l'a iniziale
dello scenario, e le soglie sono calibrate su di essa con la procedura di sempre
(calibrate_reference_thresholds). Così prima del cambiamento lo schema vede un mondo uguale al suo
riferimento, e l'unica non stazionarietà è quella simulata. Con la stagione di calibrazione vera del
fit lo schema reagirebbe anche alla distanza fra Elo e mercato, che nei dati veri cresce con l'età
del modello e resta nelle previsioni usate come ossatura.

Agenti, senza puntata minima: Kelly pieno, quarto di Kelly, C3_ref e C3_ref_stop come in
scheme_reference_run, le stesse due versioni con le soglie dell'allarme calibrate sull'intera
stagione (C3_ref_season, C3_ref_stop_season; shk.model.season_thresholds), le quattro con la diagnosi a
due termini (shk.model.two_fold_diagnosis.DX_ARMS), e l'«oracolo», che punta il quarto di Kelly
finché a > 0 e poi si ferma.
Gli esiti di tutti gli scenari di una replica usano le stesse estrazioni uniformi, quindi gli scenari
sono appaiati e coincidono fino al cambiamento quando l'a iniziale è lo stesso.

Seed: SeedSequence(SEED_S25).spawn(2) = (riferimento, stagioni); ciascuno
.spawn(numero di stagioni)[stagione].spawn(repliche)[replica]; quello del riferimento
.spawn(4) = (estrazioni uniformi, bootstrap delle soglie per giornata, bootstrap delle soglie per
stagione, bootstrap delle soglie della diagnosi a due termini).
"""

from collections.abc import Mapping, Sequence
from typing import Final, NamedTuple

import numpy as np

from shk.kelly.agents import AGENT_A_LAMBDA, AGENT_B_LAMBDA, FractionalKellyAgent
from shk.kelly.environment import run_paired_backtest
from shk.market.devig import devig_probabilities
from shk.model.agent_c import (
    DIAGNOSIS_NONE,
    DIAGNOSIS_STRUCTURAL,
    Module2Supervisor,
    ReferenceData,
    SchemeAgent,
    calibrate_reference_thresholds,
)
from shk.model.frozen_agents import scheme_window
from shk.model.frozen_params import FrozenParams, load_frozen_params
from shk.model.scheme_reference_run import ReferenceSetup, build_reference_agents
from shk.model.season_thresholds import PER_DATE_ARMS, SEASON_ARMS, season_agents, season_level_setup
from shk.model.season_input import SeasonInput
from shk.model.timing_placebo import (
    LEVEL_BASE,
    LEVEL_ZERO,
    fresh_sequence,
    levels_from_lambda,
    schedule_log_wealth,
)
from shk.model.two_fold_diagnosis import DX_ARMS, ReferenceDiagnosis, calibrate_reference_diagnosis, dx_agents
from shk.stats.bootstrap import optimal_block_length, round_block_length

SEED_S25: Final[int] = 20261112
N_REPLICAS: Final[int] = 25
BREAK_FRACTION: Final[float] = 0.5
SCHEME_ARMS: Final[tuple[str, ...]] = PER_DATE_ARMS + tuple(SEASON_ARMS) + tuple(DX_ARMS)
FIXED_AGENTS: Final[tuple[str, ...]] = ("full_kelly", "quarter_kelly", "oracle")


class Scenario(NamedTuple):
    """Uno scenario: a prima e dopo il cambiamento di metà stagione."""

    name: str
    a_before: float
    a_after: float
    composition: bool = False   # True: nella seconda metà le partite con più dispersione prevista


SCENARIOS: Final[tuple[Scenario, ...]] = (
    Scenario("stable_edge", 1.0, 1.0),
    Scenario("edge_vanishes", 1.0, 0.0),
    Scenario("edge_reverses", 1.0, -1.0),
    Scenario("no_edge", 0.0, 0.0),
    Scenario("composition_shift", 1.0, 1.0, True),
)


def tilted_probabilities(q: np.ndarray, p_hat: np.ndarray, a: np.ndarray | float) -> np.ndarray:
    """p* ∝ q^(1−a) · p̂^a per riga (N, 3); a scalare o (N,)."""
    qq, pp = np.asarray(q, dtype=np.float64), np.asarray(p_hat, dtype=np.float64)
    if qq.shape != pp.shape or qq.ndim != 2:
        raise ValueError(f"q and p_hat must have the same shape (N, k), got {qq.shape}, {pp.shape}")
    aa = np.broadcast_to(np.asarray(a, dtype=np.float64), (qq.shape[0],))[:, None]
    logits = (1.0 - aa) * np.log(qq) + aa * np.log(pp)
    w = np.exp(logits - logits.max(axis=1, keepdims=True))
    return w / w.sum(axis=1, keepdims=True)


def draw_outcomes(probs: np.ndarray, uniforms: np.ndarray) -> np.ndarray:
    """Esiti (N,) per inversione della funzione di ripartizione, dalle estrazioni uniformi date."""
    p = np.asarray(probs, dtype=np.float64)
    u = np.asarray(uniforms, dtype=np.float64)
    if p.ndim != 2 or u.shape != (p.shape[0],):
        raise ValueError(f"probs must be (N, k) and uniforms (N,), got {p.shape}, {u.shape}")
    cdf = np.cumsum(p, axis=1)
    return np.minimum((u[:, None] >= cdf).sum(axis=1), p.shape[1] - 1).astype(np.int64)


def break_day(n_days: int, fraction: float = BREAK_FRACTION) -> int:
    """Indice della prima giornata dopo il cambiamento."""
    return int(np.floor(n_days * fraction))


def match_parameter(dates: np.ndarray, scenario: Scenario) -> tuple[np.ndarray, int]:
    """a per partita (N,) e indice della prima giornata dopo il cambiamento."""
    days, day_index = np.unique(dates, return_inverse=True)
    first = break_day(days.shape[0])
    return np.where(day_index < first, scenario.a_before, scenario.a_after), first


def simulated_input(inp: SeasonInput, a: np.ndarray | float, uniforms: np.ndarray) -> SeasonInput:
    """La stagione con gli esiti simulati da p*(a) e δ ricalcolato; tutto il resto è quello vero."""
    q = devig_probabilities(inp.odds, "shin")
    outcomes = draw_outcomes(tilted_probabilities(q, inp.probs, a), uniforms)
    idx = np.arange(outcomes.shape[0])
    delta = np.log(inp.probs[idx, outcomes]) - np.log(q[idx, outcomes])
    return inp._replace(outcomes=outcomes[None, :], delta=delta)


class SimulatedReference(NamedTuple):
    """Riferimento simulato: stessa stagione e stessa soglia strutturale, soglie dell'allarme per giornata e per stagione."""

    per_date: ReferenceSetup
    per_season: ReferenceSetup
    diagnosis: ReferenceDiagnosis


def calibration_setup(params: FrozenParams, train: SeasonInput, a: float,
                      seq: np.random.SeedSequence) -> SimulatedReference:
    """Stagione di riferimento simulata con a costante e soglie dello schema calibrate su di essa."""
    outcome_seq, boot_seq, season_seq, diagnosis_seq = fresh_sequence(seq).spawn(4)
    sim = simulated_input(train, a, np.random.default_rng(outcome_seq).random(train.dates.shape[0]))
    length = round_block_length(optimal_block_length(sim.delta).circular)
    window = scheme_window(params)
    thresholds = calibrate_reference_thresholds(sim.x, sim.delta, window, length, np.random.default_rng(boot_seq))
    per_date = ReferenceSetup(*thresholds, sim.x, sim.delta)
    per_season = season_level_setup(per_date, sim.dates, window, length, np.random.default_rng(season_seq))
    diagnosis = calibrate_reference_diagnosis(sim.x, sim.delta, window, length, np.random.default_rng(diagnosis_seq))
    return SimulatedReference(per_date, per_season, diagnosis)


def composition_shift(inp: SeasonInput, beta_dispersion: np.ndarray, n_first: int, position_index: int) -> SeasonInput:
    """Riordina le partite: nelle prime n_first posizioni quelle con meno dispersione prevista, poi le altre.

    La dispersione prevista è quella della regressione di riferimento (intercetta e covariate). Dentro
    ciascuna metà resta l'ordine originale; date e covariata «position» restano quelle del calendario.
    """
    predicted = beta_dispersion[0] + inp.x @ beta_dispersion[1:]
    order = np.argsort(predicted, kind="stable")
    new = np.concatenate([np.sort(order[:n_first]), np.sort(order[n_first:])])
    x = inp.x[new].copy()
    x[:, position_index] = inp.x[:, position_index]
    return inp._replace(probs=inp.probs[new], odds=inp.odds[new], x=x)


def calibration_setups(params_path: str, train: SeasonInput, a_values: Sequence[float],
                       seqs: Sequence[np.random.SeedSequence]) -> dict[float, list[SimulatedReference]]:
    """Riferimenti simulati di una stagione: a → uno per replica (stesse estrazioni per ogni a)."""
    params = load_frozen_params(params_path)
    return {a: [calibration_setup(params, train, a, seq) for seq in seqs] for a in a_values}


class SimulatedSeason(NamedTuple):
    """Una stagione simulata di uno scenario: capitale degli agenti e calendario degli schemi."""

    log_wealth: dict[str, float]          # agente → ln W_T (−inf se il capitale va a zero)
    first_day_after: int                  # prima giornata dopo il cambiamento
    levels: dict[str, np.ndarray]         # schema → (D,) livello della giornata
    lambdas: dict[str, np.ndarray]        # schema → (D,) λ della giornata
    gain_before: dict[str, float]         # schema → Σ prima del cambiamento di (ln rendimento schema − quarto di Kelly)
    gain_after: dict[str, float]          # schema → lo stesso dopo il cambiamento
    alarm_days_after: dict[str, int]      # schema → giornate con allarme dopo il cambiamento
    structural_days_after: dict[str, int]  # schema → di cui con diagnosi strutturale


def scenario_season(params: FrozenParams, setup: SimulatedReference, inp: SeasonInput, scenario: Scenario,
                    uniforms: np.ndarray) -> tuple[SeasonInput, int]:
    """La stagione simulata dello scenario e l'indice della prima giornata dopo il cambiamento."""
    a, first = match_parameter(inp.dates, scenario)
    if scenario.composition:
        n_first = int((inp.dates < np.unique(inp.dates)[first]).sum())
        inp = composition_shift(inp, setup.diagnosis.beta_dispersion, n_first,
                                list(params.fixed["covariates"]).index("position"))
    return simulated_input(inp, a, uniforms), first


def run_simulated_season(params: FrozenParams, setup: SimulatedReference, inp: SeasonInput,
                         scenario: Scenario, uniforms: np.ndarray) -> SimulatedSeason:
    """Simula gli esiti dello scenario ed esegue gli agenti senza puntata minima (vedi modulo)."""
    sim, first = scenario_season(params, setup, inp, scenario, uniforms)
    kappa, base = float(params.calibrated["c1_kappa"]), float(params.fixed["c0_lambda"])
    supervisor = Module2Supervisor(sim.season, sim.dates, sim.x, list(params.fixed["covariates"]),
                                   scheme_window(params),
                                   reference=ReferenceData(setup.per_date.x, setup.per_date.delta))
    agents = build_reference_agents(params, setup.per_date, supervisor, ("B_0.25",) + PER_DATE_ARMS)
    agents += season_agents(params, setup.per_season, supervisor)
    agents += dx_agents(params, setup.per_date, setup.per_season, setup.diagnosis, supervisor)
    agents += [FractionalKellyAgent("full_kelly", lam=AGENT_A_LAMBDA),
               FractionalKellyAgent("reduced", lam=AGENT_B_LAMBDA * kappa)]
    runs = {r.name: r for r in run_paired_backtest(agents, sim.dates, sim.probs, sim.odds, sim.outcomes, 0.0,
                                                   fallback_policy=params.fixed["fallback_policy"])}
    by_name = {ag.name: ag for ag in agents}
    with np.errstate(divide="ignore"):
        final = {name: float(np.log(run.wealth[0, -1])) for name, run in runs.items()}
    days = np.unique(sim.dates)
    r_base = np.diff(np.log(runs["B_0.25"].wealth[0]))
    log_returns = np.stack([np.zeros(days.shape[0]), np.diff(np.log(runs["reduced"].wealth[0])), r_base])
    a_day = np.where(np.arange(days.shape[0]) < first, scenario.a_before, scenario.a_after)
    log_wealth = {"full_kelly": final["full_kelly"], "quarter_kelly": final["B_0.25"],
                  "oracle": float(r_base[a_day > 0.0].sum())}
    out = SimulatedSeason(log_wealth, first, {}, {}, {}, {}, {}, {})
    for arm in SCHEME_ARMS:
        agent = by_name[arm]
        assert isinstance(agent, SchemeAgent)
        lam_by_date, diag_by_date = agent.lambda_by_date, agent.diagnosis_by_date
        lam = np.array([lam_by_date[np.datetime64(d, "ns")] for d in days])
        diagnosis = np.array([diag_by_date[np.datetime64(d, "ns")] for d in days])
        levels = levels_from_lambda(lam, base, kappa)
        rebuilt = float(schedule_log_wealth(levels, log_returns))
        if abs(rebuilt - final[arm]) > 1e-9:
            raise RuntimeError(f"{arm}: capital not reproduced by its schedule ({rebuilt} vs {final[arm]})")
        extra = log_returns[levels, np.arange(days.shape[0])] - r_base
        out.log_wealth[arm] = final[arm]
        out.levels[arm], out.lambdas[arm] = levels, lam
        out.gain_before[arm], out.gain_after[arm] = float(extra[:first].sum()), float(extra[first:].sum())
        out.alarm_days_after[arm] = int((diagnosis[first:] != DIAGNOSIS_NONE).sum())
        out.structural_days_after[arm] = int((diagnosis[first:] == DIAGNOSIS_STRUCTURAL).sum())
    return out


def run_replicas(params_path: str, setups: Mapping[float, Sequence[SimulatedReference]], inp: SeasonInput,
                 seqs: Sequence[np.random.SeedSequence],
                 scenarios: Sequence[Scenario] = SCENARIOS) -> list[dict[str, SimulatedSeason]]:
    """Le repliche di una stagione: per replica, scenario → stagione simulata.

    setups[a][replica] è il riferimento simulato della stagione con a iniziale a.
    """
    params = load_frozen_params(params_path)
    out = []
    for k, seq in enumerate(seqs):
        uniforms = np.random.default_rng(seq).random(inp.dates.shape[0])
        out.append({s.name: run_simulated_season(params, setups[s.a_before][k], inp, s, uniforms) for s in scenarios})
    return out


def run_constant(params_path: str, inp: SeasonInput, seqs: Sequence[np.random.SeedSequence],
                 lams: Mapping[str, Mapping[str, float]],
                 setups: Mapping[float, Sequence[SimulatedReference]],
                 scenarios: Sequence[Scenario] = SCENARIOS) -> list[dict[str, dict[str, float]]]:
    """Kelly frazionario a λ costante sugli stessi esiti simulati: per replica, scenario → schema → ln W_T.

    lams[scenario][schema] è il λ medio dello schema nello scenario; uno schema con λ medio nullo vale 0.
    """
    params = load_frozen_params(params_path)
    out = []
    for k, seq in enumerate(seqs):
        uniforms = np.random.default_rng(seq).random(inp.dates.shape[0])
        row = {}
        for s in scenarios:
            sim, _ = scenario_season(params, setups[s.a_before][k], inp, s, uniforms)
            positive = {arm: lam for arm, lam in lams[s.name].items() if lam > 0.0}
            agents = [FractionalKellyAgent(arm, lam=float(lam)) for arm, lam in positive.items()]
            runs = run_paired_backtest(agents, sim.dates, sim.probs, sim.odds, sim.outcomes, 0.0,
                                       fallback_policy=params.fixed["fallback_policy"]) if agents else []
            row[s.name] = {arm: 0.0 for arm in lams[s.name]} | {r.name: float(np.log(r.wealth[0, -1])) for r in runs}
        out.append(row)
    return out


def first_stop_day(levels: np.ndarray) -> int | None:
    """Indice della prima giornata senza puntata, o None."""
    zero = np.flatnonzero(np.asarray(levels) == LEVEL_ZERO)
    return int(zero[0]) if zero.shape[0] else None


def share_of_days(levels: Sequence[np.ndarray], firsts: Sequence[int], level: int = LEVEL_ZERO) -> tuple[float, float]:
    """Quota di giornate al livello dato, prima e dopo il cambiamento, su tutte le stagioni simulate."""
    before = np.concatenate([lv[:f] for lv, f in zip(levels, firsts)])
    after = np.concatenate([lv[f:] for lv, f in zip(levels, firsts)])
    return float((before == level).mean()), float((after == level).mean())


assert LEVEL_BASE == 2  # i livelli indicizzano le righe di log_returns (0 nulla, 1 ridotta, 2 base)
