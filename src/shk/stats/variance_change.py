"""Statistiche di varianza che cambia nel tempo e fra stagioni, su array.

Contenuto:
- varentropy_standardized_residuals: residui z_t = (l_t - H_t) / sqrt(V_t) della log-loss
  l_t = -ln p(x_t), con H_t = -sum p ln p (entropia) e V_t = sum p (ln p)^2 - H_t^2
  (varentropia): sotto calibrazione perfetta hanno media 0 e varianza 1;
- goldfeld_quandt_thirds: rapporto fra la varianza (ddof = 1) dell'ultimo terzo e quella
  del primo terzo della serie, scartando il terzo centrale; coincide con l'F di
  statsmodels het_goldfeldquandt con regressore costante, split = n // 3 e
  drop = n - 2 (n // 3);
- arch_lm: statistica LM di Engle, (n - q) R^2 della regressione di z_t^2 sui suoi q
  ritardi con costante, come statsmodels het_arch(z, nlags=q);
- rolling_log_variance_max: massimo su finestre mobili (lunghezza w, passo s) di
  |ln(varianza della finestra / varianza della serie)|, varianze con ddof = 1;
- brown_forsythe: statistica di Levene centrata sulla mediana (Brown-Forsythe), cioè l'F
  dell'ANOVA a una via sulle deviazioni assolute dalla mediana di gruppo;
- moving_block_indices_of_length: moving block bootstrap con lunghezza del ricampionamento
  diversa dalla lunghezza della serie;
- soglie nominali.

Le funzioni di statistica accettano una serie (n,) o un lotto (B, n) e lavorano
sull'ultimo asse, per calcolare in blocco le statistiche dei ricampionamenti.
"""

import math
from typing import Final

import numpy as np
import scipy.stats

ARCH_LAGS: Final[int] = 10
ROLLING_WINDOW: Final[int] = 80
ROLLING_STEP: Final[int] = 10


def _check_integer(value: object, name: str) -> int:
    """Converte un intero Python o NumPy, con TypeError per bool e non interi."""
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
        raise TypeError(f"{name} must be an integer, got {type(value).__name__}")
    return int(value)


def _as_real_array(x: np.ndarray, name: str, min_ndim: int = 1) -> np.ndarray:
    """Valida un ndarray reale e finito e lo converte in float64."""
    if not isinstance(x, np.ndarray):
        raise TypeError(f"{name} must be an instance of np.ndarray, got {type(x)}")
    if (
        not np.issubdtype(x.dtype, np.number)
        or np.issubdtype(x.dtype, np.complexfloating)
        or np.issubdtype(x.dtype, np.bool_)
    ):
        raise TypeError(f"{name} must have real numeric dtype, got {x.dtype}")
    if x.ndim < min_ndim:
        raise ValueError(f"{name} must have at least {min_ndim} dimension(s), got {x.ndim}D")
    if not np.all(np.isfinite(x)):
        raise ValueError(f"All elements of {name} must be finite (no NaN or Inf allowed)")
    return x.astype(np.float64, copy=False)


def varentropy_standardized_residuals(
    probs: np.ndarray, outcomes: np.ndarray
) -> np.ndarray:
    """Residui della log-loss standardizzati per varentropia.

    Parametri
    ---------
    probs : np.ndarray
        Probabilità (N, k) strettamente positive, righe a somma 1 entro 1e-9.
    outcomes : np.ndarray
        Esiti realizzati (N,), interi in 0..k-1.

    Restituisce
    -----------
    np.ndarray
        z_t = (l_t - H_t) / sqrt(V_t), forma (N,).

    Solleva
    -------
    TypeError
        Se probs non è reale o outcomes non è intero.
    ValueError
        Per forme incoerenti, probabilità non positive o righe che non sommano a 1, esiti
        fuori intervallo, o varentropia non superiore a 1e-12 volte sum p (ln p)^2
        (distribuzione uniforme o quasi).
    """
    p = _as_real_array(probs, "probs", min_ndim=2)
    if p.ndim != 2:
        raise ValueError(f"probs must be 2D (N, k), got {p.ndim}D")
    if not isinstance(outcomes, np.ndarray):
        raise TypeError(f"outcomes must be an instance of np.ndarray, got {type(outcomes)}")
    if not np.issubdtype(outcomes.dtype, np.integer) or np.issubdtype(outcomes.dtype, np.bool_):
        raise TypeError(f"outcomes must have integer dtype, got {outcomes.dtype}")
    if outcomes.shape != (p.shape[0],):
        raise ValueError(f"outcomes must have shape ({p.shape[0]},), got {outcomes.shape}")
    if np.any(p <= 0.0):
        raise ValueError("probs must be strictly positive")
    if np.any(np.abs(p.sum(axis=1) - 1.0) > 1e-9):
        raise ValueError("Each row of probs must sum to 1 within 1e-9")
    if np.any((outcomes < 0) | (outcomes >= p.shape[1])):
        raise ValueError(f"outcomes must be in 0..{p.shape[1] - 1}")

    log_p = np.log(p)
    entropy = -(p * log_p).sum(axis=1)
    second_moment = (p * log_p**2).sum(axis=1)
    varentropy = second_moment - entropy**2
    # Con p uniforme V è nulla in aritmetica esatta ma può uscire positiva per arrotondamento
    if np.any(varentropy <= 1e-12 * second_moment):
        raise ValueError("Varentropy must be strictly positive (relative 1e-12) for every row")
    loss = -log_p[np.arange(p.shape[0]), outcomes]
    return (loss - entropy) / np.sqrt(varentropy)


def goldfeld_quandt_split(n: int) -> tuple[int, int]:
    """Terzi della serie: (lunghezza del primo terzo, inizio dell'ultimo terzo).

    Primo e ultimo terzo hanno n // 3 osservazioni; il centrale le restanti
    (per n = 380: 126, 128, 126).

    Solleva
    -------
    TypeError
        Se n non è intero.
    ValueError
        Se n < 6.
    """
    n_val = _check_integer(n, "n")
    if n_val < 6:
        raise ValueError(f"n must be at least 6, got {n_val}")
    third = n_val // 3
    return third, n_val - third


def goldfeld_quandt_thirds(z: np.ndarray) -> np.ndarray | float:
    """Rapporto var(ultimo terzo) / var(primo terzo), ddof = 1, sull'ultimo asse.

    Restituisce
    -----------
    float per z 1D, altrimenti ndarray di forma z.shape[:-1].
    """
    x = _as_real_array(z, "z")
    first_len, last_start = goldfeld_quandt_split(x.shape[-1])
    var_first = x[..., :first_len].var(axis=-1, ddof=1)
    var_last = x[..., last_start:].var(axis=-1, ddof=1)
    if np.any(var_first <= 0.0):
        raise ValueError("Variance of the first third must be positive")
    ratio = var_last / var_first
    return float(ratio) if x.ndim == 1 else ratio


def arch_lm(z: np.ndarray, n_lags: int = ARCH_LAGS) -> np.ndarray | float:
    """Statistica ARCH-LM di Engle (1982): (n - q) R^2 di z_t^2 sui q ritardi, con costante.

    Le regressioni del lotto si risolvono con la fattorizzazione QR, mai con l'inversa.

    Parametri
    ---------
    z : np.ndarray
        Serie (n,) o lotto (B, n).
    n_lags : int, opzionale
        Numero di ritardi q (default ARCH_LAGS = 10).

    Restituisce
    -----------
    float per z 1D, altrimenti ndarray di forma z.shape[:-1].
    """
    x = _as_real_array(z, "z")
    q = _check_integer(n_lags, "n_lags")
    n = x.shape[-1]
    if q < 1:
        raise ValueError(f"n_lags must be at least 1, got {q}")
    if n - q <= q + 1:
        raise ValueError(f"z must have more than {2 * q + 1} observations, got {n}")

    batch = x.reshape(-1, n) ** 2
    m = n - q
    y = batch[:, q:]
    design = np.empty((batch.shape[0], m, q + 1), dtype=np.float64)
    design[:, :, 0] = 1.0
    for lag in range(1, q + 1):
        design[:, :, lag] = batch[:, q - lag : n - lag]

    q_mat, _ = np.linalg.qr(design)
    fitted = q_mat @ np.einsum("bij,bi->bj", q_mat, y)[:, :, None]
    ssr = ((y - fitted[:, :, 0]) ** 2).sum(axis=1)
    sst = ((y - y.mean(axis=1, keepdims=True)) ** 2).sum(axis=1)
    if np.any(sst <= 0.0):
        raise ValueError("z^2 must not be constant")
    lm = m * (1.0 - ssr / sst)
    lm = lm.reshape(x.shape[:-1])
    return float(lm) if x.ndim == 1 else lm


def rolling_log_variance_max(
    z: np.ndarray, window: int = ROLLING_WINDOW, step: int = ROLLING_STEP
) -> np.ndarray | float:
    """max_w |ln(var(finestra w) / var(serie))|, finestre di window osservazioni con passo step.

    Le finestre iniziano in 0, step, 2·step, ... finché stanno nella serie (per n = 380,
    window = 80 e step = 10: 31 finestre); varianze con ddof = 1.

    Restituisce
    -----------
    float per z 1D, altrimenti ndarray di forma z.shape[:-1].
    """
    x = _as_real_array(z, "z")
    w = _check_integer(window, "window")
    s = _check_integer(step, "step")
    n = x.shape[-1]
    if not (2 <= w <= n):
        raise ValueError(f"window must satisfy 2 <= window <= n ({n}), got {w}")
    if s < 1:
        raise ValueError(f"step must be at least 1, got {s}")

    starts = np.arange(0, n - w + 1, s)
    windows = x[..., starts[:, None] + np.arange(w)[None, :]]
    var_windows = windows.var(axis=-1, ddof=1)
    var_total = x.var(axis=-1, ddof=1)
    if np.any(var_windows <= 0.0) or np.any(var_total <= 0.0):
        raise ValueError("Window and series variances must be positive")
    stat = np.abs(np.log(var_windows / var_total[..., None])).max(axis=-1)
    return float(stat) if x.ndim == 1 else stat


def brown_forsythe(groups: np.ndarray) -> np.ndarray | float:
    """Statistica di Brown-Forsythe su k gruppi di uguale numerosità m.

    È l'F dell'ANOVA a una via sulle deviazioni assolute |x - mediana del gruppo|, con
    gradi di libertà (k - 1, k m - k); coincide con scipy.stats.levene(center="median").

    Parametri
    ---------
    groups : np.ndarray
        Gruppi (k, m) oppure lotto (B, k, m), con k >= 2 e m >= 2.

    Restituisce
    -----------
    float per groups 2D, altrimenti ndarray di forma groups.shape[:-2].
    """
    g = _as_real_array(groups, "groups", min_ndim=2)
    k, m = g.shape[-2], g.shape[-1]
    if k < 2 or m < 2:
        raise ValueError(f"groups must have k >= 2 groups of m >= 2 observations, got {g.shape}")
    dev = np.abs(g - np.median(g, axis=-1, keepdims=True))
    group_means = dev.mean(axis=-1)
    grand_mean = group_means.mean(axis=-1)
    ss_between = m * ((group_means - grand_mean[..., None]) ** 2).sum(axis=-1)
    ss_within = ((dev - group_means[..., None]) ** 2).sum(axis=(-2, -1))
    if np.any(ss_within <= 0.0):
        raise ValueError("Within-group dispersion must be positive")
    w = (ss_between / (k - 1)) / (ss_within / (k * m - k))
    return float(w) if g.ndim == 2 else w


def moving_block_indices_of_length(
    n: int, length: int, block_length: int, n_boot: int, rng: np.random.Generator
) -> np.ndarray:
    """Indici del moving block bootstrap con ricampionamenti di lunghezza arbitraria.

    Come shk.stats.calibration.moving_block_indices, ma ogni ricampionamento concatena
    ceil(length / L) blocchi (inizio uniforme in [0, n - L]) e si tronca a length
    osservazioni, anche con length > n. Estrazione unica:
    rng.integers(0, n - L + 1, size=(n_boot, ceil(length / L))).

    Restituisce
    -----------
    np.ndarray
        Indici int64 (n_boot, length) in [0, n).

    Solleva
    -------
    TypeError
        Se un argomento intero non è intero o rng non è np.random.Generator.
    ValueError
        Se n < 1, length < 1, n_boot < 1 o non 1 <= block_length <= n.
    """
    n_val = _check_integer(n, "n")
    len_val = _check_integer(length, "length")
    l_val = _check_integer(block_length, "block_length")
    b_val = _check_integer(n_boot, "n_boot")
    if not isinstance(rng, np.random.Generator):
        raise TypeError(f"rng must be an instance of np.random.Generator, got {type(rng)}")
    if n_val < 1 or len_val < 1 or b_val < 1:
        raise ValueError("n, length and n_boot must be at least 1")
    if not (1 <= l_val <= n_val):
        raise ValueError(f"block_length must satisfy 1 <= block_length <= n ({n_val}), got {l_val}")

    k_blocks = math.ceil(len_val / l_val)
    starts = rng.integers(0, n_val - l_val + 1, size=(b_val, k_blocks), dtype=np.int64)
    blocks = starts[:, :, None] + np.arange(l_val, dtype=np.int64)[None, None, :]
    return blocks.reshape(b_val, k_blocks * l_val)[:, :len_val]


def goldfeld_quandt_nominal_bounds(n: int, alpha: float) -> tuple[float, float]:
    """Quantili alpha/2 e 1 - alpha/2 della F(n_last - 1, n_first - 1) (test bilaterale)."""
    first_len, last_start = goldfeld_quandt_split(n)
    dfn, dfd = n - last_start - 1, first_len - 1
    return (
        float(scipy.stats.f.ppf(alpha / 2.0, dfn, dfd)),
        float(scipy.stats.f.ppf(1.0 - alpha / 2.0, dfn, dfd)),
    )


def arch_lm_nominal_threshold(n_lags: int, alpha: float) -> float:
    """Quantile 1 - alpha della chi quadro con n_lags gradi di libertà."""
    return float(scipy.stats.chi2.ppf(1.0 - alpha, _check_integer(n_lags, "n_lags")))


def brown_forsythe_nominal_threshold(k: int, m: int, alpha: float) -> float:
    """Quantile 1 - alpha della F(k - 1, k m - k)."""
    k_val = _check_integer(k, "k")
    m_val = _check_integer(m, "m")
    return float(scipy.stats.f.ppf(1.0 - alpha, k_val - 1, k_val * m_val - k_val))
