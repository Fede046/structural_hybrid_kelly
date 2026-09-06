"""Modulo per il calcolo delle metriche statistiche su traiettorie di log-wealth."""

import numpy as np


def final_log_wealth(paths: np.ndarray) -> np.ndarray:
    """Estrae il logaritmo del capitale finale per ciascuna traiettoria.

    Dalla matrice delle traiettorie di log-wealth di shape (M, T + 1), estrae
    l'ultima colonna corrispondente al tempo T.

    Parametri
    ---------
    paths : np.ndarray
        Matrice di log-wealth di shape (M, T + 1).

    Restituisce
    -----------
    np.ndarray
        Vettore unidimensionale di shape (M,) con i valori finali di log-wealth.

    Solleva
    -------
    ValueError
        Se paths non è una matrice bidimensionale o se ha meno di 2 colonne.
    """
    paths_arr = np.asarray(paths)
    if paths_arr.ndim != 2:
        raise ValueError(f"paths must be a 2D array, got {paths_arr.ndim}D")
    if paths_arr.shape[1] < 2:
        raise ValueError(f"paths must have at least 2 columns (T >= 1), got shape {paths_arr.shape}")

    return paths_arr[:, -1]


def median_growth_rate(paths: np.ndarray) -> float:
    """Calcola il tasso di crescita mediano per singola scommessa.

    È definito come la mediana del logaritmo del capitale finale divisa per
    il numero di scommesse T (con T = paths.shape[1] - 1):
        g_mediana = mediana(ln(B_T)) / T

    Parametri
    ---------
    paths : np.ndarray
        Matrice di log-wealth di shape (M, T + 1).

    Restituisce
    -----------
    float
        Tasso di crescita logaritmico mediano per scommessa.

    Solleva
    -------
    ValueError
        Se paths non è una matrice bidimensionale o se ha meno di 2 colonne.
    """
    paths_arr = np.asarray(paths)
    final = final_log_wealth(paths_arr)
    t_steps = paths_arr.shape[1] - 1
    return float(np.median(final) / t_steps)


def median_final_wealth(paths: np.ndarray) -> float:
    """Calcola la mediana del capitale finale su tutte le traiettorie.

    È definita come l'esponenziale della mediana del log-wealth finale:
        mediana(B_T) = exp(mediana(ln(B_T)))

    Parametri
    ---------
    paths : np.ndarray
        Matrice di log-wealth di shape (M, T + 1).

    Restituisce
    -----------
    float
        Mediana del capitale finale B_T.

    Solleva
    -------
    ValueError
        Se paths non è una matrice bidimensionale o se ha meno di 2 colonne.
    """
    final = final_log_wealth(paths)
    return float(np.exp(np.median(final)))


def mean_final_wealth(paths: np.ndarray) -> float:
    """Calcola la stima Monte Carlo della media aritmetica del capitale finale.

    È definita come la media empirica del capitale finale B_T = exp(ln(B_T))
    calcolata sulle M traiettorie simulate:
        media(B_T) = (1 / M) * somma_{m=1}^M exp(ln(B_{T, m}))

    Parametri
    ---------
    paths : np.ndarray
        Matrice di log-wealth di shape (M, T + 1).

    Restituisce
    -----------
    float
        Media aritmetica empirica del capitale finale B_T.

    Solleva
    -------
    ValueError
        Se paths non è una matrice bidimensionale o se ha meno di 2 colonne.
    """
    final = final_log_wealth(paths)
    return float(np.mean(np.exp(final)))


def max_drawdown(paths: np.ndarray) -> np.ndarray:
    """Calcola il massimo drawdown relativo per ciascuna traiettoria.

    Per ciascuna traiettoria determina il massimo calo rispetto al picco storico:
        dd_log(t) = max_{0 <= s <= t} ln(B_s) - ln(B_t)
        max_dd_rel = 1 - exp(-max_t dd_log(t))
    Il calcolo è interamente vettorizzato lungo l'asse temporale senza alcun ciclo Python.

    Parametri
    ---------
    paths : np.ndarray
        Matrice di log-wealth di shape (M, T + 1).

    Restituisce
    -----------
    np.ndarray
        Vettore di shape (M,) con il massimo drawdown relativo in [0, 1) per ciascuna traiettoria.

    Solleva
    -------
    ValueError
        Se paths non è una matrice bidimensionale o se ha meno di 2 colonne.
    """
    paths_arr = np.asarray(paths)
    if paths_arr.ndim != 2:
        raise ValueError(f"paths must be a 2D array, got {paths_arr.ndim}D")
    if paths_arr.shape[1] < 2:
        raise ValueError(f"paths must have at least 2 columns (T >= 1), got shape {paths_arr.shape}")

    running_max = np.maximum.accumulate(paths_arr, axis=1)
    max_dd_log = np.max(running_max - paths_arr, axis=1)
    return 1.0 - np.exp(-max_dd_log)


def fraction_below_start(paths: np.ndarray) -> float:
    """Calcola la frazione di traiettorie che terminano al di sotto del capitale iniziale.

    Determina la percentuale di traiettorie per cui il capitale finale B_T è
    strettamente inferiore al capitale iniziale B_0 (equivalente a ln(B_T) < ln(B_0)):
        frazione = (1 / M) * somma_{m=1}^M I(ln(B_{T, m}) < ln(B_{0, m}))

    Parametri
    ---------
    paths : np.ndarray
        Matrice di log-wealth di shape (M, T + 1).

    Restituisce
    -----------
    float
        Frazione in [0, 1] delle traiettorie con capitale finale inferiore a quello iniziale.

    Solleva
    -------
    ValueError
        Se paths non è una matrice bidimensionale o se ha meno di 2 colonne.
    """
    paths_arr = np.asarray(paths)
    if paths_arr.ndim != 2:
        raise ValueError(f"paths must be a 2D array, got {paths_arr.ndim}D")
    if paths_arr.shape[1] < 2:
        raise ValueError(f"paths must have at least 2 columns (T >= 1), got shape {paths_arr.shape}")

    return float(np.mean(paths_arr[:, -1] < paths_arr[:, 0]))

