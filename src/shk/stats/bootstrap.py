"""Lunghezza ottima dei blocchi e stationary bootstrap (T42).

Contenuto:
- optimal_block_length: lunghezza ottima dei blocchi di Politis e White (2004) con la
  correzione di Patton, Politis e White (2009), per lo stationary bootstrap e per il
  circular block bootstrap; la seconda vale anche per il moving block bootstrap, che ha
  la stessa costante asintotica;
- round_block_length: arrotondamento della decisione S7 (intero più vicino, almeno 1);
- stationary_bootstrap_indices: indici dello stationary bootstrap di Politis e Romano
  (1994), con lo stesso contratto di forma e tipo di
  shk.stats.calibration.moving_block_indices;
- stationary_bootstrap_mean_interval: intervallo percentile della media per stationary
  bootstrap.

Algoritmo della lunghezza ottima, per una serie x_1..x_n con e_t = x_t - media:
1. autocovarianze gamma_k = (1/n) * sum_{t=k+1}^{n} e_t e_{t-k} per k = 0..m_max, con
   m_max = ceil(sqrt(n)) + K_n e K_n = max(5, floor(log10(n)));
2. lag di troncamento di Politis (2003): m_hat è il primo lag j >= 0 tale che i K_n
   valori assoluti delle autocorrelazioni ai lag j..j+K_n-1 stanno tutti sotto la banda
   c * sqrt(log10(n)/n), con c = 2; M = min(2 * max(m_hat, 1), m_max), e M = m_max se
   nessun gruppo di K_n lag è sotto la banda;
3. kernel flat-top trapezoidale di Politis e Romano (1995):
   lambda(s) = 1 per |s| <= 1/2, 2 * (1 - |s|) per 1/2 < |s| <= 1;
4. G = sum_{k=-M}^{M} lambda(k/M) |k| gamma_k e
   sigma2 = sum_{k=-M}^{M} lambda(k/M) gamma_k (varianza di lungo periodo);
5. correzione del 2009: D_SB = 2 * sigma2^2 per lo stationary bootstrap,
   D_CB = (4/3) * sigma2^2 per il circular bootstrap;
6. b = (2 G^2 / D)^(1/3) * n^(1/3), limitata superiormente da
   b_max = ceil(min(3 * sqrt(n), n / 3)).

Le costanti K_n, c, m_max e b_max e la normalizzazione delle autocorrelazioni seguono
il programma MATLAB di Andrew Patton, come la funzione arch.bootstrap.optimal_block_length
(arch 8.0.0, base.py, _single_optimal_block), a cui l'implementazione è allineata. Le
autocovarianze usano l'intero campione invece di una lunghezza comune a tutti i lag, e
l'autocorrelazione al lag k è |sum_{t=k+1}^{n} e_t e_{t-k}| divisa per
sqrt(sum_{t=k+2}^{n} e_t^2 * sum_{t=1}^{n-k-1} e_t^2), come in arch.

Riferimenti:
- D. N. Politis, H. White (2004), Automatic Block-Length Selection for the Dependent
  Bootstrap, Econometric Reviews 23(1), 53-70;
- A. Patton, D. N. Politis, H. White (2009), Correction to "Automatic Block-Length
  Selection for the Dependent Bootstrap", Econometric Reviews 28(4), 372-375;
- D. N. Politis (2003), Adaptive bandwidth choice, Journal of Nonparametric Statistics
  15(4-5), 517-533;
- D. N. Politis, J. P. Romano (1994), The Stationary Bootstrap, JASA 89(428), 1303-1313.
"""

import math
from typing import Final, NamedTuple

import numpy as np

from shk.stats.calibration import compute_order_statistic_index

PW_MIN_KN: Final[int] = 5
PW_BAND_CONSTANT: Final[float] = 2.0
PW_D_STATIONARY_FACTOR: Final[float] = 2.0
PW_D_CIRCULAR_FACTOR: Final[float] = 4.0 / 3.0


class OptimalBlockLength(NamedTuple):
    """Lunghezze ottime dei blocchi (float, non arrotondate).

    Attributi
    ---------
    stationary : float
        Lunghezza media ottima dei blocchi dello stationary bootstrap.
    circular : float
        Lunghezza ottima dei blocchi del circular (e moving) block bootstrap.
    """

    stationary: float
    circular: float


def _check_integer(value: object, name: str) -> int:
    """Converte un intero Python o NumPy, con TypeError per bool e non interi."""
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
        raise TypeError(f"{name} must be an integer, got {type(value).__name__}")
    return int(value)


def _check_real(value: object, name: str) -> float:
    """Converte un reale Python o NumPy, con TypeError per bool e non numerici."""
    if isinstance(value, bool) or not isinstance(
        value, (int, float, np.integer, np.floating)
    ):
        raise TypeError(f"{name} must be a real number, got {type(value).__name__}")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite, got {result}")
    return result


def optimal_block_length(x: np.ndarray) -> OptimalBlockLength:
    """Lunghezza ottima dei blocchi di Politis-White corretta da Patton-Politis-White (2009).

    Vedi la docstring del modulo per l'algoritmo, le costanti e le fonti.

    Parametri
    ---------
    x : np.ndarray
        Serie 1D con dtype reale e valori finiti, non costante, con più di
        ceil(sqrt(n)) + max(5, floor(log10(n))) + 1 osservazioni.

    Restituisce
    -----------
    OptimalBlockLength
        Lunghezze (float) per stationary bootstrap e circular bootstrap.

    Solleva
    -------
    TypeError
        Se x non è np.ndarray con dtype reale.
    ValueError
        Se x non è 1D, contiene valori non finiti, è costante o è troppo corta.
    """
    if not isinstance(x, np.ndarray):
        raise TypeError(f"x must be an instance of np.ndarray, got {type(x)}")
    if (
        not np.issubdtype(x.dtype, np.number)
        or np.issubdtype(x.dtype, np.complexfloating)
        or np.issubdtype(x.dtype, np.bool_)
    ):
        raise TypeError(f"x must have real numeric dtype, got {x.dtype}")
    if x.ndim != 1:
        raise ValueError(f"x must be 1D, got {x.ndim}D")
    if not np.all(np.isfinite(x)):
        raise ValueError("All elements of x must be finite (no NaN or Inf allowed)")

    nobs = x.shape[0]
    if nobs < 2:
        raise ValueError(f"x must have at least 2 observations, got {nobs}")
    kn = max(PW_MIN_KN, int(np.log10(nobs)))
    m_max = int(np.ceil(np.sqrt(nobs))) + kn
    if nobs <= m_max + 1:
        raise ValueError(
            f"x must have more than {m_max + 1} observations for the lag search, got {nobs}"
        )

    values = x.astype(np.float64)
    eps = values - values.mean(0)
    if not np.any(eps != 0.0):
        raise ValueError("x must not be constant")

    b_max = np.ceil(min(3 * np.sqrt(nobs), nobs / 3))
    band = PW_BAND_CONSTANT * np.sqrt(np.log10(nobs) / nobs)

    acv = np.zeros(m_max + 1)
    abs_acorr = np.zeros(m_max + 1)
    opt_m: int | None = None
    for i in range(m_max + 1):
        v1 = eps[i + 1 :] @ eps[i + 1 :]
        v2 = eps[: -(i + 1)] @ eps[: -(i + 1)]
        cross_prod = eps[i:] @ eps[: nobs - i]
        acv[i] = cross_prod / nobs
        abs_acorr[i] = np.abs(cross_prod) / np.sqrt(v1 * v2)
        # Primo gruppo di K_n lag consecutivi con autocorrelazione dentro la banda
        if i >= kn and opt_m is None and np.all(abs_acorr[i - kn : i] < band):
            opt_m = i - kn
    m = 2 * max(opt_m, 1) if opt_m is not None else m_max
    m = min(m, m_max)

    g = 0.0
    long_run_var = acv[0]
    for k in range(1, m + 1):
        lam = 1 if k / m <= 1 / 2 else 2 * (1 - k / m)
        g += 2 * lam * k * acv[k]
        long_run_var += 2 * lam * acv[k]
    # Una stima negativa resta ammessa, come in arch: D usa il suo quadrato
    if long_run_var == 0.0:
        raise ValueError("Estimated long-run variance is zero: block length undefined")
    d_sb = PW_D_STATIONARY_FACTOR * long_run_var**2
    d_cb = PW_D_CIRCULAR_FACTOR * long_run_var**2
    b_sb = ((2 * g**2) / d_sb) ** (1 / 3) * nobs ** (1 / 3)
    b_cb = ((2 * g**2) / d_cb) ** (1 / 3) * nobs ** (1 / 3)
    return OptimalBlockLength(
        stationary=float(min(b_sb, b_max)),
        circular=float(min(b_cb, b_max)),
    )


def round_block_length(length: float) -> int:
    """Arrotonda una lunghezza dei blocchi all'intero più vicino, almeno 1 (decisione S7).

    Le metà si arrotondano per eccesso: floor(length + 0.5).

    Parametri
    ---------
    length : float
        Lunghezza non negativa e finita (int o float, Python o NumPy).

    Restituisce
    -----------
    int
        max(1, floor(length + 0.5)).

    Solleva
    -------
    TypeError
        Se length è bool o non numerico.
    ValueError
        Se length è negativa o non finita.
    """
    value = _check_real(length, "length")
    if value < 0.0:
        raise ValueError(f"length must be non-negative, got {value}")
    return max(1, int(math.floor(value + 0.5)))


def _stationary_block_layout(
    n: int,
    mean_block_length: float,
    n_boot: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Struttura a blocchi dello stationary bootstrap, senza validazione degli argomenti.

    Estrazioni, nell'ordine: rng.random((n_boot, n)) per gli inizi di blocco (una posizione
    apre un blocco con probabilità p = 1 / mean_block_length; la posizione 0 lo apre
    sempre), poi rng.integers(0, n, size=(n_boot, n)) per il punto di partenza di ciascun
    blocco possibile. Le lunghezze dei blocchi sono geometriche di media mean_block_length,
    troncate alla fine del ricampionamento.

    Restituisce
    -----------
    tuple[np.ndarray, np.ndarray, np.ndarray]
        indices int64 (n_boot, n); new_block bool (n_boot, n), True dove inizia un blocco;
        starts int64 (n_boot, n), il punto di partenza estratto per ogni posizione (usato
        solo dove new_block è True).
    """
    p = 1.0 / mean_block_length
    new_block = rng.random((n_boot, n)) < p
    new_block[:, 0] = True
    starts = rng.integers(0, n, size=(n_boot, n), dtype=np.int64)

    positions = np.arange(n, dtype=np.int64)
    block_origin = np.maximum.accumulate(
        np.where(new_block, positions[None, :], 0), axis=1
    )
    offsets = positions[None, :] - block_origin
    origin_values = np.take_along_axis(starts, block_origin, axis=1)
    indices = (origin_values + offsets) % n
    return indices, new_block, starts


def stationary_bootstrap_indices(
    n: int,
    mean_block_length: float,
    n_boot: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Indici dello stationary bootstrap di Politis-Romano (1994).

    Ogni ricampionamento concatena blocchi di lunghezza geometrica di media
    mean_block_length, con inizio uniforme in [0, n) e avvolgimento circolare, troncati a
    n osservazioni. Con mean_block_length = 1 ogni posizione apre un blocco e si ottiene
    il bootstrap iid. Stesso contratto di forma e tipo di moving_block_indices; l'ordine
    delle estrazioni è descritto in _stationary_block_layout.

    Parametri
    ---------
    n : int
        Lunghezza della serie (n >= 1).
    mean_block_length : float
        Lunghezza media dei blocchi, reale in [1, n].
    n_boot : int
        Numero di ricampionamenti (n_boot >= 1).
    rng : np.random.Generator
        Generatore di numeri casuali.

    Restituisce
    -----------
    np.ndarray
        Indici int64 di forma (n_boot, n), in [0, n).

    Solleva
    -------
    TypeError
        Se n o n_boot non sono interi, se mean_block_length non è reale, o se rng non è
        np.random.Generator.
    ValueError
        Se n < 1, n_boot < 1, o mean_block_length non è in [1, n] o non è finita.
    """
    n_val = _check_integer(n, "n")
    b_val = _check_integer(n_boot, "n_boot")
    length = _check_real(mean_block_length, "mean_block_length")
    if not isinstance(rng, np.random.Generator):
        raise TypeError(f"rng must be an instance of np.random.Generator, got {type(rng)}")
    if n_val < 1:
        raise ValueError(f"n must be at least 1, got {n_val}")
    if b_val < 1:
        raise ValueError(f"n_boot must be at least 1, got {b_val}")
    if not (1.0 <= length <= n_val):
        raise ValueError(
            f"mean_block_length must satisfy 1 <= mean_block_length <= n ({n_val}), got {length}"
        )

    indices, _, _ = _stationary_block_layout(n_val, length, b_val, rng)
    return indices


def stationary_bootstrap_mean_interval(
    x: np.ndarray,
    mean_block_length: float,
    n_boot: int,
    alpha: float,
    rng: np.random.Generator,
) -> tuple[float, float]:
    """Intervallo percentile 1 - alpha della media per stationary bootstrap.

    Estremi = statistiche d'ordine ceil((alpha/2)(B + 1)) e ceil((1 - alpha/2)(B + 1))
    delle medie ricampionate (per B = 999 e alpha = 0.05: la 25-esima e la 975-esima),
    con compute_order_statistic_index.

    Parametri
    ---------
    x : np.ndarray
        Serie 1D reale e finita.
    mean_block_length : float
        Lunghezza media dei blocchi in [1, len(x)]; 1 dà il bootstrap iid.
    n_boot : int
        Numero di ricampionamenti.
    alpha : float
        Livello, in (0, 1).
    rng : np.random.Generator
        Generatore degli indici.

    Restituisce
    -----------
    tuple[float, float]
        (estremo inferiore, estremo superiore).

    Solleva
    -------
    TypeError
        Se x non è np.ndarray reale, o per i tipi degli altri argomenti.
    ValueError
        Se x non è 1D o non è finita, o per i valori degli altri argomenti.
    """
    if not isinstance(x, np.ndarray):
        raise TypeError(f"x must be an instance of np.ndarray, got {type(x)}")
    if (
        not np.issubdtype(x.dtype, np.number)
        or np.issubdtype(x.dtype, np.complexfloating)
        or np.issubdtype(x.dtype, np.bool_)
    ):
        raise TypeError(f"x must have real numeric dtype, got {x.dtype}")
    if x.ndim != 1:
        raise ValueError(f"x must be 1D, got {x.ndim}D")
    if not np.all(np.isfinite(x)):
        raise ValueError("All elements of x must be finite (no NaN or Inf allowed)")
    alpha_val = _check_real(alpha, "alpha")
    if not (0.0 < alpha_val < 1.0):
        raise ValueError(f"alpha must be strictly between 0 and 1, got {alpha_val}")
    b_val = _check_integer(n_boot, "n_boot")

    upper_k = compute_order_statistic_index(b_val, alpha_val / 2.0)
    lower_k = compute_order_statistic_index(b_val, 1.0 - alpha_val / 2.0)
    indices = stationary_bootstrap_indices(x.shape[0], mean_block_length, b_val, rng)
    means = np.sort(x.astype(np.float64)[indices].mean(axis=1))
    return float(means[lower_k - 1]), float(means[upper_k - 1])
