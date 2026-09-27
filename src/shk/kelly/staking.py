"""Modulo per la regola di staking del criterio di Kelly con stima e frazionamento."""

import math
import numpy as np


def kelly_staking(
    p_hat: float | np.ndarray, b: float, lam: float = 1.0
) -> float | np.ndarray:
    """Calcola la frazione di scommessa secondo la regola di Kelly con stima e moltiplicatore.

    Data una probabilità stimata p_hat (scalare o array NumPy), calcola la frazione
    ottimale teorica di Kelly troncata a zero per vantaggi non positivi, e la scala
    tramite il moltiplicatore lam (frazione di Kelly lambda):
        q = 1 - p_hat
        f_raw = (b * p_hat - q) / b
        f_hat = max(0, f_raw)
        f = lam * f_hat

    La regola non limita la frazione al di sotto di 1. Con p_hat = 1.0 e b > 0,
    la frazione vale lam * 1. Eventuali frazioni >= 1 vengono deliberatamente
    restituite e saranno eventualmente rifiutate a valle da simulate_growth con ValueError.

    Parametri
    ---------
    p_hat : float | np.ndarray
        Stima di probabilità di vincita in [0, 1], scalare o array NumPy.
    b : float
        Quota decimale netta (b a 1), strettamente positiva (b > 0).
    lam : float, opzionale
        Moltiplicatore di Kelly non negativo (lam >= 0), default pari a 1.0.

    Restituisce
    -----------
    float | np.ndarray
        Frazione di capitale da scommettere. Se p_hat è uno scalare Python, uno scalare
        NumPy o un array 0-dimensionale, restituisce un float Python. Se p_hat ha almeno
        una dimensione (1D o 2D), restituisce un np.ndarray con la stessa forma di p_hat.

    Solleva
    -------
    ValueError
        Se b <= 0 o non finito, se lam < 0 o non finito, oppure se p_hat contiene
        valori non finiti (NaN o Inf) o non compresi in [0, 1].
    """
    if not math.isfinite(b) or b <= 0.0:
        raise ValueError(f"Odds 'b' must be strictly positive (b > 0), got {b}")

    if not math.isfinite(lam):
        raise ValueError(f"Multiplier 'lam' must be finite, got {lam}")
    if lam < 0.0:
        raise ValueError(f"Multiplier 'lam' must be non-negative (lam >= 0), got {lam}")

    p_arr = np.asarray(p_hat, dtype=float)

    if not np.all(np.isfinite(p_arr)):
        raise ValueError("All elements of 'p_hat' must be finite (no NaN or Inf allowed)")
    if np.any(p_arr < 0.0) or np.any(p_arr > 1.0):
        raise ValueError(
            f"All elements of 'p_hat' must be in [0, 1], got min={np.min(p_arr)}, max={np.max(p_arr)}"
        )

    # Stesso ordine di operazioni di core.py (righe 42-43) per concordanza bit-a-bit
    q = 1.0 - p_arr
    f_raw = (b * p_arr - q) / b
    f_hat = np.maximum(0.0, f_raw)
    f = lam * f_hat

    if np.ndim(p_hat) == 0:
        return float(f)

    return f
