"""Seed delle procedure di specificazione e calibrazione per Modulo 1 (T61, US-C9.2).

Con l'Elo le procedure usano i seed di sempre: SEED_S8 per T46 e T47, SEED_S9 per T52, T53 e
T54 (ciascuna prende SeedSequence(seed).spawn(5)[posizione del suo task]).

Con Dixon-Coles T61 le riesegue con SeedSequence(SEED_S11).spawn(5)[2] (T61 in posizione 2
di S11), diviso con spawn(5), un figlio per procedura nell'ordine T46, T47, T52, T53, T54.
Ogni procedura usa il suo figlio al posto della sequenza del task (task_seeds.task_sequence).
"""

from typing import Final

import numpy as np

from shk.model.dixon_coles import SEED_S11
from shk.model.module1 import MODULE1_ELO, check_module1
from shk.model.module3_synthetic import SEED_S9
from shk.model.task_seeds import N_STORY_TASKS
from shk.stats.oaxaca_synthetic import SEED_S8

T61_STORY_POSITION: Final[int] = 2
PROCEDURES: Final[tuple[str, ...]] = ("t46", "t47", "t52", "t53", "t54")
DC_SEED_SCHEME: Final[str] = "SeedSequence(SEED_S11).spawn(5)[2].spawn(5)[k], k = T46, T47, T52, T53, T54"


def t61_sequences(seed: int = SEED_S11) -> dict[str, np.random.SeedSequence]:
    """Un figlio di SeedSequence(seed).spawn(5)[2] per procedura (vedi modulo)."""
    children = np.random.SeedSequence(seed).spawn(N_STORY_TASKS)[T61_STORY_POSITION].spawn(len(PROCEDURES))
    return dict(zip(PROCEDURES, children))


def procedure_seeds(module1: str = MODULE1_ELO) -> dict[str, int | np.random.SeedSequence]:
    """Seed di T46, T47, T52, T53 e T54 per il Modulo 1 dato."""
    if check_module1(module1) == MODULE1_ELO:
        return {"t46": SEED_S8, "t47": SEED_S8, "t52": SEED_S9, "t53": SEED_S9, "t54": SEED_S9}
    return t61_sequences()
