"""Sequenza di seed di una procedura.

Le procedure del Modulo 2 e della calibrazione degli agenti ricavano i propri seed da
SeedSequence(seed).spawn(N_STORY_TASKS)[posizione della procedura]. Con Dixon-Coles come
Modulo 1 la calibrazione si riesegue con seed diversi: per questo accettano anche una
SeedSequence già pronta, che si usa al posto di quella della procedura. Con un intero il
risultato è quello di sempre.

Della SeedSequence data si usa una copia nuova (stessa entropia e stessa spawn_key, nessun
figlio già generato): spawn() avanza un contatore interno, e la stessa sequenza passata due
volte deve dare gli stessi figli, come un intero.

Le esecuzioni congelate usano invece il seed come radice: con Dixon-Coles la robustezza del
ranking passa la radice R = SeedSequence(SEED_S11).spawn(5)[3], e ogni procedura prende
R.spawn(5)[posizione] con la stessa forma di SEED_S10 (story_task_sequence).
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


def story_task_sequence(seed: int | np.random.SeedSequence, position: int,
                        n_tasks: int = N_STORY_TASKS) -> np.random.SeedSequence:
    """Sequenza della procedura dalla radice: SeedSequence(seed) per un intero, una copia nuova
    della SeedSequence data altrimenti; poi spawn(n_tasks)[position].

    Solleva
    -------
    TypeError
        Se seed non è un intero (bool esclusi) né una SeedSequence.
    """
    if isinstance(seed, np.random.SeedSequence):
        root = np.random.SeedSequence(seed.entropy, spawn_key=seed.spawn_key, pool_size=seed.pool_size)
        return root.spawn(n_tasks)[position]
    if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)):
        raise TypeError(f"seed must be an integer or a SeedSequence, got {type(seed).__name__}")
    return np.random.SeedSequence(seed).spawn(n_tasks)[position]
