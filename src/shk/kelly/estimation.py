"""Modulo per la generazione di stime di probabilità perturbate e rumorose."""

import math
import numpy as np


def relative_perturbation(p: float, delta: float) -> float:
    """Calcola una stima perturbata di p tramite perturbazione relativa deterministica.

    La stima è definita come:
        p_hat = p * (1 + delta)
    Il risultato viene riportato all'intervallo [0, 1] tramite saturazione (clipping).

    Parametri
    ---------
    p : float
        Probabilità di vincita reale, in [0, 1].
    delta : float
        Fattore di perturbazione relativa. Deve essere un valore finito.

    Restituisce
    -----------
    float
        Probabilità perturbata p_hat vincolata a [0, 1].

    Solleva
    -------
    ValueError
        Se p non è in [0, 1], oppure se delta non è finito (NaN o Inf).
    """
    if not (0.0 <= p <= 1.0):
        raise ValueError(f"Probability 'p' must be in [0, 1], got {p}")
    if not math.isfinite(delta):
        raise ValueError(f"Perturbation 'delta' must be finite, got {delta}")

    p_hat = p * (1.0 + delta)
    return float(min(max(p_hat, 0.0), 1.0))


def noisy_estimates(
    p: float, sigma_p: float, T: int, M: int, rng: np.random.Generator
) -> np.ndarray:
    """Genera una matrice di stime di probabilità con rumore gaussiano per scommessa.

    Per ciascuna delle M traiettorie e T scommesse, aggiunge a p un disturbo
    gaussiano i.i.d. con media zero e deviazione standard sigma_p:
        p_hat_{m, t} = p + epsilon_{m, t},  con epsilon_{m, t} ~ N(0, sigma_p^2)
    Tutti i valori generati vengono riportati all'intervallo [0, 1] tramite saturazione
    (clipping). Se sigma_p = 0, restituisce una matrice con tutti i valori pari a p.

    Parametri
    ---------
    p : float
        Probabilità di vincita reale, in [0, 1].
    sigma_p : float
        Deviazione standard del rumore di stima (sigma_p >= 0).
    T : int
        Numero di scommesse per ogni traiettoria (T > 0).
    M : int
        Numero di traiettorie indipendenti (M > 0).
    rng : np.random.Generator
        Generatore di numeri casuali di NumPy.

    Restituisce
    -----------
    np.ndarray
        Matrice float64 di shape (M, T) con valori vincolati in [0, 1].

    Solleva
    -------
    ValueError
        Se p non è in [0, 1], se sigma_p < 0 o non finito, se T <= 0, oppure se M <= 0.
    TypeError
        Se rng non è un'istanza di np.random.Generator.
    """
    if not (0.0 <= p <= 1.0):
        raise ValueError(f"Probability 'p' must be in [0, 1], got {p}")
    if not math.isfinite(sigma_p) or sigma_p < 0.0:
        raise ValueError(f"Standard deviation 'sigma_p' must be non-negative (sigma_p >= 0), got {sigma_p}")
    if T <= 0:
        raise ValueError(f"Number of steps 'T' must be strictly positive (T > 0), got {T}")
    if M <= 0:
        raise ValueError(f"Number of trajectories 'M' must be strictly positive (M > 0), got {M}")
    if not isinstance(rng, np.random.Generator):
        raise TypeError(f"rng must be an instance of np.random.Generator, got {type(rng)}")

    if sigma_p == 0.0:
        return np.full((M, T), float(p), dtype=np.float64)

    noise = rng.normal(loc=0.0, scale=sigma_p, size=(M, T))
    p_hat = p + noise
    return np.clip(p_hat, 0.0, 1.0)
