"""Modulo di simulazione per traiettorie di bankroll sotto il criterio di Kelly."""

import numpy as np


def draw_outcomes(
    p: float, T: int, M: int, rng: np.random.Generator
) -> np.ndarray:
    """Genera una matrice di esiti bernoulliani per M traiettorie e T scommesse.

    Ogni scommessa ha probabilità p di successo (True) e 1 - p di fallimento (False).
    Le estrazioni sono i.i.d. e generate tramite il generatore casuale specificato.

    Parametri
    ---------
    p : float
        Probabilità di vincita, in [0, 1].
    T : int
        Numero di scommesse per ogni traiettoria (T > 0).
    M : int
        Numero di traiettorie indipendenti da generare (M > 0).
    rng : np.random.Generator
        Generatore di numeri casuali di NumPy.

    Restituisce
    -----------
    np.ndarray
        Matrice booleana di shape (M, T) dove True rappresenta una vincita.

    Solleva
    -------
    ValueError
        Se p non è in [0, 1], se T <= 0 oppure se M <= 0.
    TypeError
        Se rng non è un'istanza di np.random.Generator.
    """
    if not (0.0 <= p <= 1.0):
        raise ValueError(f"Probability 'p' must be in [0, 1], got {p}")
    if T <= 0:
        raise ValueError(f"Number of steps 'T' must be strictly positive (T > 0), got {T}")
    if M <= 0:
        raise ValueError(f"Number of trajectories 'M' must be strictly positive (M > 0), got {M}")
    if not isinstance(rng, np.random.Generator):
        raise TypeError(f"rng must be an instance of np.random.Generator, got {type(rng)}")

    return rng.random(size=(M, T)) < p


def log_wealth_paths(outcomes: np.ndarray, f: float, b: float) -> np.ndarray:
    """Calcola le traiettorie temporali del logaritmo del bankroll normalizzato.

    Dato un insieme di esiti bernoulliani, calcola l'evoluzione temporale del logaritmo
    del bankroll per una frazione costante f e una quota decimale netta b.
    Alla scommessa t il bankroll viene moltiplicato per (1 + b*f) se outcomes[m, t] è
    True (vincita), e per (1 - f) se outcomes[m, t] è False (perdita).
    La funzione accumula i logaritmi di questi fattori di crescita a partire da un
    capitale iniziale normalizzato B0 = 1, pertanto la colonna 0 è interamente pari a 0.

    Vincolo computazionale: nessun ciclo Python sulle M traiettorie; il calcolo
    deve essere interamente vettorizzato.

    Parametri
    ---------
    outcomes : np.ndarray
        Array booleano di shape (M, T) contenente gli esiti (True = vincita).
    f : float
        Frazione di capitale scommessa, in [0, 1).
    b : float
        Quota decimale netta (b a 1), strettamente positiva (b > 0).

    Restituisce
    -----------
    np.ndarray
        Array float64 di shape (M, T + 1) contenente il logaritmo del bankroll
        normalizzato per ciascuna delle M traiettorie (colonna 0 interamente nulla).

    Solleva
    -------
    NotImplementedError
        Questa funzione è deliberatamente lasciata non implementata per essere
        scritta manualmente.
    """

    log_win = np.log(1+(b*f))
    log_loss = np.log(1-f)

    # np.where(condizione, valore_se_vero, valore_se_falso)

    log_factors = np.where(outcomes,log_win,log_loss)

    cumulative = np.cumsum(log_factors, axis=1)

    row, column = cumulative.shape

    paths = np.zeros((row, column +1))

    paths[:,1:] = cumulative



    return paths

