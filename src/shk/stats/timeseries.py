"""Modulo per la generazione e simulazione di serie temporali stazionarie."""

import math
import numpy as np


def generate_ar1_series(
    phi: float, n: int, m: int, rng: np.random.Generator
) -> np.ndarray:
    """Genera m serie AR(1) stazionarie gaussiane indipendenti di lunghezza n.

    Modello autoregressivo di ordine 1:
        x_t = phi * x_{t-1} + epsilon_t,  per t = 1, ..., n - 1
    con innovazioni indipendenti epsilon_t ~ N(0, 1).

    Partenza stazionaria:
    Affinché la serie sia strettamente e debolmente stazionaria fin dal primo istante,
    la condizione iniziale al tempo t = 0 viene estratta dalla distribuzione stazionaria:
        x_0 ~ N(0, 1 / (1 - phi^2))
    avente varianza stazionaria gamma_0 = 1 / (1 - phi^2) e autocorrelazione
    rho(h) = phi^h a ritardo h.

    Contratto di estrazione dal generatore (RNG):
    Il generatore esegue esattamente due estrazioni casuali nell'ordine seguente:
    1. x_0 per tutte le m serie tramite rng.normal(loc=0.0, scale=1.0 / sqrt(1 - phi^2), size=m);
    2. le innovazioni epsilon per tutti i passi temporali rimanenti tramite
       rng.normal(loc=0.0, scale=1.0, size=(m, n - 1)).

    Forma e convenzione dell'output:
    Restituisce una matrice 2D di forma (m, n) con dtype float64, dove le righe
    rappresentano le serie stocastiche indipendenti e le colonne rappresentano
    il tempo (t = 0, ..., n - 1). L'evoluzione temporale è calcolata tramite un ciclo
    esclusivamente lungo l'asse temporale, vettorizzato lungo tutte le m serie.

    Parametri
    ---------
    phi : float
        Coefficiente autoregressivo della serie, strettamente compreso in (-1.0, 1.0).
    n : int
        Lunghezza temporale di ciascuna serie (numero di passi n >= 2).
    m : int
        Numero di serie stocastiche indipendenti da generare (m >= 1).
    rng : np.random.Generator
        Generatore di numeri casuali di NumPy.

    Restituisce
    -----------
    np.ndarray
        Matrice float64 di forma (m, n) contenente le serie generate.

    Solleva
    -------
    TypeError
        Se n o m sono di tipo booleano o non sono interi (int o np.integer),
        oppure se rng non è un'istanza di np.random.Generator.
    ValueError
        Se phi non è finito, se |phi| >= 1.0, se n < 2 oppure se m < 1.
    """
    if isinstance(n, bool) or not isinstance(n, (int, np.integer)):
        raise TypeError(f"Number of time steps 'n' must be an integer, got {type(n).__name__}")
    if isinstance(m, bool) or not isinstance(m, (int, np.integer)):
        raise TypeError(f"Number of series 'm' must be an integer, got {type(m).__name__}")

    if n < 2:
        raise ValueError(f"Number of time steps 'n' must be at least 2 (n >= 2), got {n}")
    if m < 1:
        raise ValueError(f"Number of series 'm' must be strictly positive (m >= 1), got {m}")

    if not math.isfinite(phi):
        raise ValueError(f"Autoregressive coefficient 'phi' must be finite, got {phi}")
    if not (-1.0 < phi < 1.0):
        raise ValueError(f"Autoregressive coefficient 'phi' must satisfy |phi| < 1, got {phi}")

    if not isinstance(rng, np.random.Generator):
        raise TypeError(f"rng must be an instance of np.random.Generator, got {type(rng)}")

    series = np.empty((int(m), int(n)), dtype=np.float64)

    # 1. Condizione iniziale stazionaria al tempo t = 0
    sigma_0 = 1.0 / math.sqrt(1.0 - phi * phi)
    series[:, 0] = rng.normal(loc=0.0, scale=sigma_0, size=int(m))

    # 2. Innovazioni per t = 1, ..., n - 1
    innovations = rng.normal(loc=0.0, scale=1.0, size=(int(m), int(n) - 1))

    # Evoluzione AR(1) ricorsiva nel tempo vettorizzata su tutte le m serie
    for t in range(1, int(n)):
        series[:, t] = phi * series[:, t - 1] + innovations[:, t - 1]

    return series
