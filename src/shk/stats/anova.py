"""Modulo per il calcolo dell'analisi della varianza (ANOVA) a una via.

Fornisce l'implementazione esatta delle formule dell'ANOVA a una via calcolate
a partire dalle definizioni per un singolo dataset e in forma vettorizzata
su insiemi multidimensionali di serie temporali.
"""

from collections.abc import Sequence
from typing import NamedTuple
import numpy as np
import scipy.stats


class OneWayAnovaResult(NamedTuple):
    """Risultato immutabile dell'ANOVA a una via per singolo dataset.

    Campi
    -----
    ss_between : float
        Somma dei quadrati tra i gruppi (devianza tra gruppi).
    ss_within : float
        Somma dei quadrati entro i gruppi (devianza residua).
    ss_total : float
        Somma dei quadrati totale (devianza totale).
    df_between : int
        Gradi di libertà tra i gruppi (k - 1).
    df_within : int
        Gradi di libertà entro i gruppi (N - k).
    ms_between : float
        Varianza (quadrato medio) tra i gruppi: ss_between / df_between.
    ms_within : float
        Varianza (quadrato medio) entro i gruppi: ss_within / df_within.
    f_statistic : float
        Statistica F di Fisher: ms_between / ms_within.
    p_value : float
        Valore p associato alla statistica F (coda destra).
    """

    ss_between: float
    ss_within: float
    ss_total: float
    df_between: int
    df_within: int
    ms_between: float
    ms_within: float
    f_statistic: float
    p_value: float


def oneway_anova(
    groups: Sequence[Sequence[float] | np.ndarray],
) -> OneWayAnovaResult:
    """Calcola l'ANOVA a una via da definizioni per una sequenza di gruppi.

    Calcola la devianza tra gruppi (ss_between), la devianza residua entro i gruppi
    (ss_within), la devianza totale (ss_total), i rispettivi gradi di libertà,
    i quadrati medi, la statistica F e il p-value della distribuzione F di Fisher.

    Parametri
    ---------
    groups : Sequence[Sequence[float] | np.ndarray]
        Sequenza di almeno due gruppi unidimensionali contenenti osservazioni numeriche.

    Restituisce
    -----------
    OneWayAnovaResult
        Oggetto immutabile contenente tutti i valori calcolati dell'ANOVA.

    Solleva
    -------
    TypeError
        Se groups non è una sequenza o se un gruppo non contiene dati numerici reali.
    ValueError
        Se il numero di gruppi è inferiore a 2, se un gruppo è vuoto o non è 1D,
        se sono presenti valori non finiti (NaN o Inf), oppure se il numero totale
        di osservazioni N non supera il numero di gruppi k (df_within <= 0).
    """
    if not isinstance(groups, Sequence) or isinstance(groups, (str, bytes)):
        raise TypeError(f"groups must be a sequence of groups, got {type(groups)}")

    k = len(groups)
    if k < 2:
        raise ValueError(f"At least 2 groups must be provided, got {k}")

    group_arrays: list[np.ndarray] = []
    group_sizes: list[int] = []
    group_means: list[float] = []

    for i, g in enumerate(groups):
        if not isinstance(g, (list, tuple, np.ndarray)):
            raise TypeError(f"Group at index {i} must be a numerical sequence or 1D array, got {type(g)}")
        g_arr = np.asarray(g)

        if not np.issubdtype(g_arr.dtype, np.number) or np.issubdtype(g_arr.dtype, np.complexfloating):
            raise TypeError(f"Group at index {i} must have real numeric dtype, got {g_arr.dtype}")

        if g_arr.ndim != 1:
            raise ValueError(f"Group at index {i} must be a 1D sequence, got {g_arr.ndim}D")

        n_j = g_arr.size
        if n_j == 0:
            raise ValueError(f"Group at index {i} is empty; each group must contain at least one observation")

        if not np.all(np.isfinite(g_arr)):
            raise ValueError(f"Group at index {i} contains non-finite values (NaN or Inf)")

        g_float = g_arr.astype(np.float64)
        group_arrays.append(g_float)
        group_sizes.append(n_j)
        group_means.append(float(np.mean(g_float)))

    total_n = sum(group_sizes)
    if total_n <= k:
        raise ValueError(
            f"Total number of observations N ({total_n}) must be strictly greater than number of groups k ({k})"
        )

    all_obs = np.concatenate(group_arrays)
    grand_mean = float(np.mean(all_obs))

    # Devianza totale calcolata direttamente dalla definizione
    ss_total = float(np.sum((all_obs - grand_mean) ** 2))

    # Devianza tra i gruppi
    ss_between = float(sum(n_j * ((m_j - grand_mean) ** 2) for n_j, m_j in zip(group_sizes, group_means)))

    # Devianza entro i gruppi (scarti dai rispettivi valori medi di gruppo)
    ss_within = float(sum(np.sum((g - m_j) ** 2) for g, m_j in zip(group_arrays, group_means)))

    df_between = k - 1
    df_within = total_n - k

    ms_between = ss_between / df_between
    ms_within = ss_within / df_within

    f_statistic = ms_between / ms_within
    p_value = float(scipy.stats.f.sf(f_statistic, df_between, df_within))

    return OneWayAnovaResult(
        ss_between=ss_between,
        ss_within=ss_within,
        ss_total=ss_total,
        df_between=df_between,
        df_within=df_within,
        ms_between=ms_between,
        ms_within=ms_within,
        f_statistic=f_statistic,
        p_value=p_value,
    )


def oneway_anova_vectorized(
    values: np.ndarray,
    labels: np.ndarray,
) -> float | np.ndarray:
    """Calcola la statistica F dell'ANOVA a una via in modo vettorizzato su serie multiple.

    Riceve una matrice di osservazioni multidimensionale in cui l'ultimo asse
    rappresenta il tempo o le unità statistiche N, e un vettore unidimensionale di etichette
    intere di lunghezza N con valori 0..k-1 tutti presenti.
    Calcola la statistica F di Fisher per ciascuna serie lungo gli assi iniziali
    senza utilizzare cicli Python.

    Parametri
    ---------
    values : np.ndarray
        Array NumPy di forma (..., N) contenente i valori numerici reali delle serie.
    labels : np.ndarray
        Array NumPy 1D di lunghezza N di interi con valori in 0..k-1 (tutti presenti).

    Restituisce
    -----------
    float | np.ndarray
        Se values è 1D (N,), restituisce un float Python rappresentante la F della serie.
        Se values è multidimensionale (..., N), restituisce un np.ndarray float64
        di forma (...) con la statistica F calcolata per ciascuna serie.

    Solleva
    -------
    TypeError
        Se values o labels non sono istanze di np.ndarray, se values non ha dtype
        numerico reale, o se labels non ha dtype intero.
    ValueError
        Se values ha meno di 1 dimensione, se values contiene valori non finiti,
        se labels non è 1D o contiene interi negativi, se la lunghezza di labels non
        coincide con l'ultimo asse di values, se le etichette non contengono tutti i valori
        tra 0 e k-1 compresi, se k < 2, oppure se N <= k (df_within <= 0).
    """
    if not isinstance(values, np.ndarray):
        raise TypeError(f"values must be an instance of np.ndarray, got {type(values)}")

    if not np.issubdtype(values.dtype, np.number) or np.issubdtype(values.dtype, np.complexfloating):
        raise TypeError(f"values must have real numeric dtype, got {values.dtype}")

    if values.ndim < 1:
        raise ValueError(f"values must have at least 1 dimension, got {values.ndim}D")

    if not np.all(np.isfinite(values)):
        raise ValueError("All elements of values must be finite (no NaN or Inf allowed)")

    if not isinstance(labels, np.ndarray):
        raise TypeError(f"labels must be an instance of np.ndarray, got {type(labels)}")

    if labels.ndim != 1:
        raise ValueError(f"labels must be a 1D array, got {labels.ndim}D")

    if not np.issubdtype(labels.dtype, np.integer):
        raise TypeError(f"labels must have integer dtype, got {labels.dtype}")

    n_obs = values.shape[-1]
    if labels.shape[0] != n_obs:
        raise ValueError(
            f"Length of labels ({labels.shape[0]}) must match the last dimension of values ({n_obs})"
        )

    if np.any(labels < 0):
        raise ValueError("labels cannot contain negative integers")

    if labels.size == 0:
        raise ValueError("labels array cannot be empty")

    k = int(np.max(labels)) + 1
    group_sizes = np.bincount(labels, minlength=k)

    if np.any(group_sizes == 0):
        missing = np.where(group_sizes == 0)[0].tolist()
        raise ValueError(f"All group labels from 0 to k-1 must be present; missing: {missing}")

    if k < 2:
        raise ValueError(f"At least 2 distinct group labels required, got {k}")

    if n_obs <= k:
        raise ValueError(
            f"Total observations N ({n_obs}) must be strictly greater than number of groups k ({k})"
        )

    # Conversione float64 per stabilità numerica
    val_float = np.asarray(values, dtype=np.float64)

    # Matrice di incidenza normalizzata W di forma (N, k)
    w_mat = np.zeros((n_obs, k), dtype=np.float64)
    w_mat[np.arange(n_obs), labels] = 1.0 / group_sizes[labels]

    # Medie di gruppo: forma (..., k)
    group_means = val_float @ w_mat

    # Media generale per serie: forma (..., 1)
    grand_mean = np.mean(val_float, axis=-1, keepdims=True)

    # Devianza tra gruppi: forma (...)
    diff_between = group_means - grand_mean
    ss_between = np.sum(group_sizes * (diff_between ** 2), axis=-1)

    # Devianza entro i gruppi: forma (...)
    fitted_values = group_means[..., labels]
    residuals = val_float - fitted_values
    ss_within = np.sum(residuals ** 2, axis=-1)

    df_between = k - 1
    df_within = n_obs - k

    ms_between = ss_between / df_between
    ms_within = ss_within / df_within

    f_stat = ms_between / ms_within

    if values.ndim == 1:
        return float(f_stat)

    return f_stat
