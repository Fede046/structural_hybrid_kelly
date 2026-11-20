"""Evoluzione delle strategie con le scelte della versione principale fra i geni (rifà shk.model.evolution).

Il genoma di shk.model.evolution ha cinque geni (lam, kappa, supervisor, stop, rule) e, con il
supervisore "calibration", usa le soglie dell'allarme per giornata e la diagnosi a tre termini delle
versioni iniziali. Qui il genoma ha due geni in più, che valgono solo con supervisor = "calibration":
- thresholds: "day" (soglie dell'allarme per giornata) o "season" (per stagione);
- diagnosis: "three" (diagnosi a tre termini sulla media) o "two" (a due termini sulla grandezza che
  ha fatto scattare l'allarme).
Con supervisor "calibration" l'errore strutturale riduce la puntata a STRUCTURAL_LAMBDA = 0.10 (versione
definitiva, decisione del 2026-11-20) invece di azzerarla; stop "clear" la riduce finché dura l'allarme,
"season" fino a fine stagione. Con supervisor "calibration", thresholds "season", diagnosis "two", stop
"clear" e rule "R1" il genoma è la versione definitiva (con λ = lam e κ = kappa). Con "previous" e "none" i due geni non
hanno effetto, come kappa e stop con "none". Selezione, variazione ed ereditarietà sono quelle di
shk.model.evolution, con gli stessi parametri; i due geni nuovi cambiano con probabilità P_SWITCH.

Una generazione è una stagione vera, senza puntata minima (season_log_wealth).
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace

import numpy as np

from shk.kelly.agents import Agent, FractionalKellyAgent
from shk.kelly.environment import run_paired_backtest
from shk.kelly.outcome_rules import with_outcome_rule
from shk.model.agent_c import SCHEME_STOP_CLEAR, SCHEME_STOP_SEASON, SchemeAgent
from shk.model.evolution import LAM_MIN, P_SWITCH, RULES, SIGMA_KAPPA, SIGMA_LAM, STOPS, SUPERVISORS
from shk.model.frozen_agents import build_supervisor
from shk.model.frozen_params import FrozenParams
from shk.model.main_version import DIAGNOSES, STRUCTURAL_LAMBDA, THRESHOLDS, MainSetup, main_agent
from shk.model.main_version import reference_supervisor
from shk.model.population_run import PopulationSetup
from shk.model.season_input import SeasonInput

_STOPS = {"clear": SCHEME_STOP_CLEAR, "season": SCHEME_STOP_SEASON}


@dataclass(frozen=True)
class MainGenome:
    """Geni di una strategia (vedi modulo)."""

    lam: float
    kappa: float
    supervisor: str
    stop: str
    rule: str
    thresholds: str
    diagnosis: str

    def __post_init__(self) -> None:
        if not LAM_MIN <= self.lam <= 1.0:
            raise ValueError(f"lam must be in [{LAM_MIN}, 1], got {self.lam}")
        if not 0.0 <= self.kappa <= 1.0:
            raise ValueError(f"kappa must be in [0, 1], got {self.kappa}")
        for value, allowed in ((self.supervisor, SUPERVISORS), (self.stop, STOPS), (self.rule, RULES),
                               (self.thresholds, THRESHOLDS), (self.diagnosis, DIAGNOSES)):
            if value not in allowed:
                raise ValueError(f"{value!r} not in {allowed}")

    def is_main(self) -> bool:
        """Le scelte discrete della versione definitiva (lam e kappa a parte)."""
        return (self.supervisor == "calibration" and self.thresholds == "season" and self.diagnosis == "two"
                and self.stop == "clear")


def random_genome(rng: np.random.Generator, fixed_lam: float | None = None) -> MainGenome:
    """Genoma iniziale: lam log-uniforme in [LAM_MIN, 1] (o fixed_lam), kappa uniforme, geni discreti uniformi."""
    lam = float(np.exp(rng.uniform(np.log(LAM_MIN), 0.0))) if fixed_lam is None else float(fixed_lam)
    return MainGenome(lam=lam, kappa=float(rng.uniform(0.0, 1.0)), supervisor=str(rng.choice(SUPERVISORS)),
                      stop=str(rng.choice(STOPS)), rule=str(rng.choice(RULES)),
                      thresholds=str(rng.choice(THRESHOLDS)), diagnosis=str(rng.choice(DIAGNOSES)))


def _switch(value: str, allowed: tuple[str, ...], rng: np.random.Generator) -> str:
    if rng.uniform() >= P_SWITCH:
        return value
    others = [v for v in allowed if v != value]
    return str(others[int(rng.integers(len(others)))])


def mutate(g: MainGenome, rng: np.random.Generator, fixed_lam: float | None = None) -> MainGenome:
    """Figlio mutato di g, come in shk.model.evolution, con i due geni nuovi."""
    lam = (float(np.clip(g.lam * np.exp(rng.normal(0.0, SIGMA_LAM)), LAM_MIN, 1.0)) if fixed_lam is None
           else float(fixed_lam))
    kappa = float(np.clip(g.kappa + rng.normal(0.0, SIGMA_KAPPA), 0.0, 1.0))
    return replace(g, lam=lam, kappa=kappa, supervisor=_switch(g.supervisor, SUPERVISORS, rng),
                   stop=_switch(g.stop, STOPS, rng), rule=_switch(g.rule, RULES, rng),
                   thresholds=_switch(g.thresholds, THRESHOLDS, rng), diagnosis=_switch(g.diagnosis, DIAGNOSES, rng))


def next_generation(genomes: list[MainGenome], fitness: np.ndarray, rng: np.random.Generator,
                    fixed_lam: float | None = None) -> list[MainGenome]:
    """Metà migliore per fitness più un figlio mutato per ciascuno; la dimensione deve essere pari."""
    n = len(genomes)
    f = np.asarray(fitness, dtype=np.float64)
    if n == 0 or n % 2 or f.shape != (n,) or not np.all(np.isfinite(f)):
        raise ValueError("need an even, non-empty population with one finite fitness each")
    order = np.argsort(-f, kind="stable")
    survivors = [genomes[i] for i in order[: n // 2]]
    return survivors + [mutate(g, rng, fixed_lam) for g in survivors]


def genome_agent(name: str, g: MainGenome, params: FrozenParams, previous: PopulationSetup, main: MainSetup,
                 structural: float, supervisor, ref_supervisor) -> Agent:
    """Agente del genoma g: Kelly frazionario, schema con le 40 precedenti (come C3) o con la calibrazione."""
    if g.supervisor == "none":
        return with_outcome_rule(FractionalKellyAgent, g.rule)(name, lam=float(g.lam))
    if g.supervisor == "previous":
        return with_outcome_rule(SchemeAgent, g.rule)(name, supervisor, float(g.kappa), previous.mean_threshold,
                                                      previous.dispersion_threshold, structural, _STOPS[g.stop],
                                                      base_lambda=float(g.lam))
    return main_agent(name, params, main, ref_supervisor, rule=g.rule, stop=_STOPS[g.stop], thresholds=g.thresholds,
                      diagnosis=g.diagnosis, base_lambda=float(g.lam), kappa=float(g.kappa),
                      structural_lambda=STRUCTURAL_LAMBDA)


def season_log_wealth(params: FrozenParams, previous: Mapping[str, PopulationSetup], main: Mapping[str, MainSetup],
                      inp: SeasonInput, fit: str, genomes: Sequence[MainGenome]) -> np.ndarray:
    """ln del capitale finale di ogni genoma sulla stagione vera di inp, senza puntata minima."""
    supervisor = build_supervisor(params, inp)
    ref_supervisor = reference_supervisor(params, inp, main[fit])
    structural = float(params.c1_thresholds[fit])
    unique = list(dict.fromkeys(genomes))  # genomi uguali danno lo stesso risultato: si giocano una volta
    agents = [genome_agent(f"g{i}", g, params, previous[fit], main[fit], structural, supervisor, ref_supervisor)
              for i, g in enumerate(unique)]
    runs = run_paired_backtest(agents, inp.dates, inp.probs, inp.odds, inp.outcomes, 0.0,
                               fallback_policy=params.fixed["fallback_policy"])
    by_genome = {g: float(np.log(run.wealth[0, -1])) for g, run in zip(unique, runs)}
    return np.array([by_genome[g] for g in genomes])
