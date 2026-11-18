"""Evoluzione delle strategie: variazione, selezione ed ereditarietà (tesi, §6.2).

Secondo tentativo basato sulla dinamica evolutiva. Nella popolazione di shk.model.population le
strategie sono fisse e cambia solo la quota di capitale; qui cambiano le strategie stesse. Ogni
strategia è un genoma di cinque geni, tutti parametri che lo schema accetta già, così che nessuna
soglia dell'allarme vada ricalibrata:
- lam: frazione di Kelly senza allarme, in [LAM_MIN, 1];
- kappa: riduzione della puntata con errore nei dati (λ = lam · kappa), in [0, 1];
- supervisor: "none" (quarto di Kelly e simili, nessun allarme), "previous" (confronto con le W
  partite precedenti) o "calibration" (confronto con la stagione di calibrazione);
- stop: "clear" (dopo un errore strutturale riprende quando l'allarme si spegne) o "season" (fermo
  fino a fine stagione);
- rule: regola di scelta dell'esito, "R1", "R2" o "R3".
Con supervisor = "none" kappa e stop non hanno effetto (restano nel genoma e possono riattivarsi).

Una generazione è una stagione. Dopo la stagione:
- selezione per troncamento: sopravvive la metà migliore per capitale finale (ln W), a parità
  l'ordine della popolazione;
- variazione: ogni sopravvissuto ha un figlio mutato (lam × exp(N(0, SIGMA_LAM)), kappa + N(0,
  SIGMA_KAPPA), ciascun gene discreto cambiato con probabilità P_SWITCH in un altro valore);
- ereditarietà: sopravvissuti e figli formano la generazione successiva.
Parametri fissati prima di guardare i risultati, nessuno scelto sui dati.

Con fixed_lam (per esempio 0.25, il quarto di Kelly) lam non evolve: si è obbligati a puntare, ed
evolvono solo supervisore, kappa, stop e regola.
"""

from dataclasses import dataclass, replace
from typing import Final

import numpy as np

LAM_MIN: Final[float] = 0.005
SIGMA_LAM: Final[float] = 0.3
SIGMA_KAPPA: Final[float] = 0.1
P_SWITCH: Final[float] = 0.1
SUPERVISORS: Final[tuple[str, ...]] = ("none", "previous", "calibration")
STOPS: Final[tuple[str, ...]] = ("clear", "season")
RULES: Final[tuple[str, ...]] = ("R1", "R2", "R3")


@dataclass(frozen=True)
class Genome:
    """Geni di una strategia (vedi modulo)."""

    lam: float
    kappa: float
    supervisor: str
    stop: str
    rule: str

    def __post_init__(self) -> None:
        if not LAM_MIN <= self.lam <= 1.0:
            raise ValueError(f"lam must be in [{LAM_MIN}, 1], got {self.lam}")
        if not 0.0 <= self.kappa <= 1.0:
            raise ValueError(f"kappa must be in [0, 1], got {self.kappa}")
        for value, allowed in ((self.supervisor, SUPERVISORS), (self.stop, STOPS), (self.rule, RULES)):
            if value not in allowed:
                raise ValueError(f"{value!r} not in {allowed}")


def random_genome(rng: np.random.Generator, fixed_lam: float | None = None) -> Genome:
    """Genoma iniziale: lam log-uniforme in [LAM_MIN, 1] (o fixed_lam), kappa uniforme, geni discreti uniformi."""
    lam = float(np.exp(rng.uniform(np.log(LAM_MIN), 0.0))) if fixed_lam is None else float(fixed_lam)
    return Genome(lam=lam, kappa=float(rng.uniform(0.0, 1.0)), supervisor=str(rng.choice(SUPERVISORS)),
                  stop=str(rng.choice(STOPS)), rule=str(rng.choice(RULES)))


def _switch(value: str, allowed: tuple[str, ...], rng: np.random.Generator) -> str:
    if rng.uniform() >= P_SWITCH:
        return value
    others = [v for v in allowed if v != value]
    return str(others[int(rng.integers(len(others)))])


def mutate(g: Genome, rng: np.random.Generator, fixed_lam: float | None = None) -> Genome:
    """Figlio mutato di g (vedi modulo); con fixed_lam lam resta quello."""
    lam = (float(np.clip(g.lam * np.exp(rng.normal(0.0, SIGMA_LAM)), LAM_MIN, 1.0)) if fixed_lam is None
           else float(fixed_lam))
    kappa = float(np.clip(g.kappa + rng.normal(0.0, SIGMA_KAPPA), 0.0, 1.0))
    return replace(g, lam=lam, kappa=kappa, supervisor=_switch(g.supervisor, SUPERVISORS, rng),
                   stop=_switch(g.stop, STOPS, rng), rule=_switch(g.rule, RULES, rng))


def next_generation(genomes: list[Genome], fitness: np.ndarray, rng: np.random.Generator,
                    fixed_lam: float | None = None) -> list[Genome]:
    """Metà migliore per fitness più un figlio mutato per ciascuno; la dimensione deve essere pari."""
    n = len(genomes)
    f = np.asarray(fitness, dtype=np.float64)
    if n == 0 or n % 2 or f.shape != (n,) or not np.all(np.isfinite(f)):
        raise ValueError("need an even, non-empty population with one finite fitness each")
    order = np.argsort(-f, kind="stable")
    survivors = [genomes[i] for i in order[: n // 2]]
    return survivors + [mutate(g, rng, fixed_lam) for g in survivors]
