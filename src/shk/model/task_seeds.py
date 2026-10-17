"""Sequenza di seed di un task di story (T61).

Le procedure di S8 e S9 (T46, T47, T52, T53, T54) ricavano i propri seed da
SeedSequence(seed).spawn(N_STORY_TASKS)[posizione del task]. Con Dixon-Coles come Modulo 1,
T61 le riesegue con seed diversi: per questo accettano anche una SeedSequence già pronta,
che si usa al posto di quella del task. Con un intero il risultato è quello di sempre.

Della SeedSequence data si usa una copia nuova (stessa entropia e stessa spawn_key, nessun
figlio già generato): spawn() avanza un contatore interno, e la stessa sequenza passata due
volte deve dare gli stessi figli, come un intero.
"""

from typing import Final

import numpy as np

N_STORY_TASKS: Final[int] = 5


def task_sequence(seed: int | np.random.SeedSequence, position: int,
                  n_tasks: int = N_STORY_TASKS) -> np.random.SeedSequence:
    """SeedSequence(seed).spawn(n_tasks)[position] per un intero, oppure una copia nuova della SeedSequence data.

    Solleva
    -------
    TypeError
        Se seed non è un intero (bool esclusi) né una SeedSequence.
    """
    if isinstance(seed, np.random.SeedSequence):
        return np.random.SeedSequence(seed.entropy, spawn_key=seed.spawn_key, pool_size=seed.pool_size)
    if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)):
        raise TypeError(f"seed must be an integer or a SeedSequence, got {type(seed).__name__}")
    return np.random.SeedSequence(seed).spawn(n_tasks)[position]
