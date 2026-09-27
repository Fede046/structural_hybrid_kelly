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


def simulate_growth(
    outcomes: np.ndarray, fractions: float | np.ndarray, b: float
) -> np.ndarray:
    """Simula le traiettorie temporali del logaritmo del bankroll normalizzato.

    Calcola l'evoluzione temporale del logaritmo del bankroll da una matrice di esiti
    bernoulliani e da frazioni di scommessa ricevute dall'esterno. Le frazioni possono
    essere scalari o variare per traiettoria e per passo temporale.
    Alla scommessa t della traiettoria m, il bankroll viene moltiplicato per
    (1 + b * f_{m,t}) se outcomes[m, t] è True (vincita), e per (1 - f_{m,t})
    se outcomes[m, t] è False (perdita).
    La funzione accumula i logaritmi dei fattori di crescita a partire da un capitale
    iniziale normalizzato B0 = 1, pertanto la colonna 0 è interamente pari a 0.

    Forme ammesse per fractions (broadcastabili a outcomes.shape (M, T)):
    - scalare: float, int o array 0D (), frazione costante per tutte le traiettorie e passi;
    - vettore 1D (T,): frazione per passo temporale t, identica per tutte le traiettorie;
    - matrice 2D (1, T): frazione per passo temporale t;
    - matrice 2D (M, 1): frazione costante nel tempo per ciascuna traiettoria m;
    - matrice 2D (M, T): frazione specifica per traiettoria m e passo t.
    Nota: un vettore 1D di lunghezza M con M != T non è broadcastabile a (M, T) secondo
    le regole di NumPy e solleva ValueError (per frazioni per traiettoria usare la forma (M, 1)).

    Vincolo computazionale: nessun ciclo Python sulle M traiettorie; il calcolo
    è interamente vettorizzato.

    Parametri
    ---------
    outcomes : np.ndarray
        Array booleano di shape (M, T) contenente gli esiti (True = vincita).
    fractions : float | np.ndarray
        Frazione/i di capitale scommessa in [0, 1), scalare o broadcastabile a (M, T).
    b : float
        Quota decimale netta (b a 1), strettamente positiva (b > 0).

    Restituisce
    -----------
    np.ndarray
        Array float64 di shape (M, T + 1) contenente il logaritmo del bankroll
        normalizzato per ciascuna delle M traiettorie (colonna 0 interamente nulla).

    Solleva
    -------
    ValueError
        Se b <= 0, se una frazione non è finita (NaN o Inf), se una frazione non è in [0, 1),
        se fractions ha una forma non broadcastabile a (M, T),
        oppure se outcomes non è un array bidimensionale con dimensioni positive.
    TypeError
        Se outcomes non è un'istanza di np.ndarray o se non ha dtype booleano.
    """
    if not isinstance(outcomes, np.ndarray):
        raise TypeError(f"outcomes must be an instance of np.ndarray, got {type(outcomes)}")
    if outcomes.dtype != bool:
        raise TypeError(f"outcomes must have boolean dtype, got {outcomes.dtype}")
    if outcomes.ndim != 2:
        raise ValueError(f"outcomes must be a 2D array, got {outcomes.ndim}D")
    if outcomes.shape[0] <= 0 or outcomes.shape[1] <= 0:
        raise ValueError(f"outcomes dimensions M and T must be strictly positive, got shape {outcomes.shape}")

    if b <= 0.0:
        raise ValueError(f"Odds 'b' must be strictly positive (b > 0), got {b}")

    fractions_arr = np.asarray(fractions, dtype=float)

    if not np.all(np.isfinite(fractions_arr)):
        raise ValueError("All elements of fractions must be finite (no NaN or Inf allowed)")

    m, t = outcomes.shape
    f_shape = fractions_arr.shape

    if fractions_arr.ndim == 0:
        pass
    elif fractions_arr.ndim == 1:
        if f_shape[0] != t:
            raise ValueError(
                f"1D fractions array with length {f_shape[0]} cannot be broadcast to outcomes shape ({m}, {t}); "
                f"expected length {t}"
            )
    elif fractions_arr.ndim == 2:
        if f_shape[0] not in (1, m) or f_shape[1] not in (1, t):
            raise ValueError(
                f"2D fractions array with shape {f_shape} cannot be broadcast to outcomes shape ({m}, {t})"
            )
    else:
        raise ValueError(
            f"fractions array has {fractions_arr.ndim} dimensions, but at most 2 dimensions are allowed"
        )

    if np.any(fractions_arr < 0.0) or np.any(fractions_arr >= 1.0):
        raise ValueError(
            f"All elements of fractions must be in [0, 1), got min={np.min(fractions_arr)}, max={np.max(fractions_arr)}"
        )

    log_win = np.log(1 + (b * fractions_arr))
    log_loss = np.log(1 - fractions_arr)

    log_factors = np.where(outcomes, log_win, log_loss)

    cumulative = np.cumsum(log_factors, axis=1)

    row, column = cumulative.shape

    paths = np.zeros((row, column + 1))

    paths[:, 1:] = cumulative

    return paths


def log_wealth_paths(outcomes: np.ndarray, f: float, b: float) -> np.ndarray:
    """Calcola le traiettorie temporali del logaritmo del bankroll normalizzato.

    Caso particolare di simulate_growth con frazione di scommessa costante scalare.
    Alla scommessa t il bankroll viene moltiplicato per (1 + b*f) se outcomes[m, t] è
    True (vincita), e per (1 - f) se outcomes[m, t] è False (perdita).
    La funzione accumula i logaritmi di questi fattori di crescita a partire da un
    capitale iniziale normalizzato B0 = 1, pertanto la colonna 0 è interamente pari a 0.

    Vincolo computazionale: nessun ciclo Python sulle M traiettorie; il calcolo
    è interamente vettorizzato.

    Parametri
    ---------
    outcomes : np.ndarray
        Array booleano di shape (M, T) contenente gli esiti (True = vincita).
    f : float
        Frazione costante di capitale scommessa, in [0, 1).
    b : float
        Quota decimale netta (b a 1), strettamente positiva (b > 0).

    Restituisce
    -----------
    np.ndarray
        Array float64 di shape (M, T + 1) contenente il logaritmo del bankroll
        normalizzato per ciascuna delle M traiettorie (colonna 0 interamente nulla).

    Solleva
    -------
    ValueError
        Se f non è compreso in [0, 1), se non è finito, se b <= 0, oppure se outcomes
        non è un array bidimensionale con dimensioni positive.
    TypeError
        Se outcomes non è un'istanza di np.ndarray o se non ha dtype booleano.
    """
    return simulate_growth(outcomes, f, b)

