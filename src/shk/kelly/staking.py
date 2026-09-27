"""Modulo per la regola di staking del criterio di Kelly con stima e frazionamento."""

import math
from typing import NamedTuple
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


class StakingMoments(NamedTuple):
    """Momenti campionari e statistiche descrittive per il moltiplicatore c = f_hat / f_star.

    Campi
    -----
    mean_c : float
        Valore atteso empirico E[c].
    mean_c2 : float
        Momento secondo empirico E[c^2].
    var_c : float
        Varianza empirica Var(c) = E[c^2] - (E[c])^2.
    fraction_zero : float
        Quota pooled di scommesse in cui la frazione f_hat è pari a 0.0.
    """

    mean_c: float
    mean_c2: float
    var_c: float
    fraction_zero: float


def staking_moments(f_hat: np.ndarray, f_star: float) -> StakingMoments:
    """Calcola i momenti empirici di c = f_hat / f_star e la quota di puntate nulle.

    Tutte le stime sono calcolate in forma pooled sull'insieme di tutte le scommesse
    presenti nell'array f_hat.

    Parametri
    ---------
    f_hat : np.ndarray
        Array (1D o 2D) contenente le frazioni di scommessa stimate.
    f_star : float
        Frazione ottimale teorica di Kelly (deve essere strettamente positiva, f_star > 0).

    Restituisce
    -----------
    StakingMoments
        NamedTuple contenente (mean_c, mean_c2, var_c, fraction_zero).

    Solleva
    -------
    ValueError
        Se f_star <= 0 o non finito, oppure se f_hat contiene valori non finiti o negativi.
    """
    if not math.isfinite(f_star) or f_star <= 0.0:
        raise ValueError(f"Optimal fraction 'f_star' must be strictly positive (f_star > 0), got {f_star}")

    f_arr = np.asarray(f_hat, dtype=float)
    if not np.all(np.isfinite(f_arr)):
        raise ValueError("All elements of 'f_hat' must be finite (no NaN or Inf allowed)")
    if np.any(f_arr < 0.0):
        raise ValueError(f"Elements of 'f_hat' must be non-negative, got min={np.min(f_arr)}")

    c = f_arr / f_star
    mean_c = float(np.mean(c))
    mean_c2 = float(np.mean(c ** 2))
    var_c = float(np.var(c))
    fraction_zero = float(np.mean(f_arr == 0.0))

    return StakingMoments(
        mean_c=mean_c,
        mean_c2=mean_c2,
        var_c=var_c,
        fraction_zero=fraction_zero,
    )


def plugin_staking(
    p_hat: float | np.ndarray, b: float, sigma_p: float
) -> float | np.ndarray:
    """Calcola la frazione di scommessa secondo la regola di Kelly plug-in per scommessa.

    Per ciascuna scommessa, calcola il vantaggio atteso stimato EV_hat = p_hat * o - 1
    (con quota lorda o = b + 1). Se EV_hat <= 0, la frazione è pari a 0.0 esatto.
    Se EV_hat > 0, calcola il moltiplicatore adattivo locale:
        lambda_t = 1 / (1 + (o * sigma_p / EV_hat)^2)
    e restituisce lambda_t * kelly_staking(p_hat, b, lam=1.0).

    Parametri
    ---------
    p_hat : float | np.ndarray
        Stima di probabilità di vincita in [0, 1], scalare o array NumPy.
    b : float
        Quota decimale netta (b a 1), strettamente positiva (b > 0).
    sigma_p : float
        Deviazione standard del rumore di stima, non negativa (sigma_p >= 0).

    Restituisce
    -----------
    float | np.ndarray
        Frazione di capitale da scommettere, con la stessa forma di p_hat.

    Solleva
    -------
    ValueError
        Se b <= 0 o non finito, se sigma_p < 0 o non finito, oppure se p_hat
        contiene valori non finiti o non compresi in [0, 1].
    """
    if not math.isfinite(sigma_p):
        raise ValueError(f"Noise parameter 'sigma_p' must be finite, got {sigma_p}")
    if sigma_p < 0.0:
        raise ValueError(f"Noise parameter 'sigma_p' must be non-negative (sigma_p >= 0), got {sigma_p}")

    # Validazione di b e p_hat ed estrazione di f_base tramite kelly_staking (Correzione A)
    f_base = kelly_staking(p_hat, b, lam=1.0)

    # Se sigma_p == 0, lambda_t = 1 ovunque, quindi la frazione coincide con f_base
    if sigma_p == 0.0:
        return f_base

    o = b + 1.0

    # Gestione scalare / array 0-dimensionale
    if np.ndim(p_hat) == 0:
        if f_base == 0.0:
            return 0.0
        ev_hat = float(p_hat) * o - 1.0
        if ev_hat <= 0.0:
            return 0.0
        ratio = (o * sigma_p) / ev_hat
        lam_t = 1.0 / (1.0 + ratio * ratio)
        return float(lam_t * f_base)

    # Gestione array NumPy (1D, 2D) con maschera protettiva contro divisione per zero (Correzione B)
    p_arr = np.asarray(p_hat, dtype=float)
    ev_hat = p_arr * o - 1.0
    positive_mask = ev_hat > 0.0

    result = np.zeros_like(p_arr, dtype=float)
    if np.any(positive_mask):
        ratio = np.divide(
            o * sigma_p,
            ev_hat,
            out=np.zeros_like(ev_hat, dtype=float),
            where=positive_mask,
        )
        lam_t = np.divide(
            1.0,
            1.0 + ratio * ratio,
            out=np.zeros_like(ratio, dtype=float),
            where=positive_mask,
        )
        result[positive_mask] = lam_t[positive_mask] * f_base[positive_mask]

    return result


