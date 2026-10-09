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


def _validate_wealth_matrix(wealth: np.ndarray) -> np.ndarray:
    """Valida la matrice delle traiettorie di ricchezza in livelli.

    Parametri
    ---------
    wealth : np.ndarray
        Matrice candidata di ricchezza di shape (M, D + 1).

    Restituisce
    -----------
    np.ndarray
        Array validato con dtype float64.

    Solleva
    -------
    TypeError
        Se wealth non è un np.ndarray o non ha dtype numerico reale.
    ValueError
        Se wealth non è 2D, ha meno di 2 colonne, contiene valori non finiti,
        valori negativi, o valori iniziali non strettamente positivi (colonna 0 <= 0).
    """
    if not isinstance(wealth, np.ndarray):
        raise TypeError(f"wealth must be a numpy.ndarray, got {type(wealth).__name__}")
    if wealth.dtype == np.bool_ or not (
        np.issubdtype(wealth.dtype, np.integer) or np.issubdtype(wealth.dtype, np.floating)
    ):
        raise TypeError(f"wealth must have a real numeric dtype, got {wealth.dtype}")
    if wealth.ndim != 2:
        raise ValueError(f"wealth must be a 2D array, got {wealth.ndim}D")
    if wealth.shape[1] < 2:
        raise ValueError(f"wealth must have at least 2 columns (D >= 1), got shape {wealth.shape}")
    if not np.all(np.isfinite(wealth)):
        raise ValueError("wealth must contain only finite values")
    if np.any(wealth < 0.0):
        raise ValueError("wealth values must be non-negative")
    if np.any(wealth[:, 0] <= 0.0):
        raise ValueError("Initial wealth (column 0) must be strictly positive")
    return np.asarray(wealth, dtype=np.float64)


def wealth_max_drawdown(wealth: np.ndarray) -> np.ndarray:
    """Calcola il massimo drawdown relativo in livelli di ricchezza per ciascuna traiettoria.

    Per ciascuna traiettoria determina il massimo calo relativo rispetto al picco storico:
        P_t = max_{0 <= s <= t} W_s
        DD(t) = 1 - W_t / P_t
        max_dd = max_t DD(t)

    Parametri
    ---------
    wealth : np.ndarray
        Matrice di ricchezza di shape (M, D + 1) con valori >= 0 e colonna 0 > 0.

    Restituisce
    -----------
    np.ndarray
        Array float64 unidimensionale di shape (M,) con il massimo drawdown relativo in [0, 1].

    Solleva
    -------
    TypeError
        Se wealth non è un np.ndarray o non ha un dtype numerico reale.
    ValueError
        Se wealth non è 2D, ha meno di 2 colonne, contiene valori non finiti,
        valori negativi o valori iniziali non strettamente positivi.
    """
    w = _validate_wealth_matrix(wealth)
    running_max = np.maximum.accumulate(w, axis=1)
    drawdowns = 1.0 - w / running_max
    return np.max(drawdowns, axis=1)


def wealth_recovery_time(wealth: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Calcola il tempo di recupero dal massimo drawdown e l'indicatore di avvenuto recupero.

    t* è il primo indice temporale in cui il drawdown raggiunge il valore massimo;
    P è il picco storico raggiunto nell'intervallo [0, t*].
    Il tempo di recupero è il numero di passi t - t* dove t è il primo indice t > t*
    tale che W_t >= P.
    Se il drawdown massimo è pari a 0, il tempo è 0 e recovered è True.
    Se il livello P non viene mai recuperato dopo t*, il tempo vale -1 e recovered è False.

    Parametri
    ---------
    wealth : np.ndarray
        Matrice di ricchezza di shape (M, D + 1) con valori >= 0 e colonna 0 > 0.

    Restituisce
    -----------
    tuple[np.ndarray, np.ndarray]
        Tupla (times, recovered) dove:
        - times è un array int64 (M,) dei tempi di recupero (-1 se non recuperato, 0 se drawdown nullo);
        - recovered è un array bool (M,) che indica se la traiettoria ha recuperato il picco.

    Solleva
    -------
    TypeError
        Se wealth non è un np.ndarray o non ha un dtype numerico reale.
    ValueError
        Se wealth non è 2D, ha meno di 2 colonne, contiene valori non finiti,
        valori negativi o valori iniziali non strettamente positivi.
    """
    w = _validate_wealth_matrix(wealth)
    m_count, _ = w.shape
    times = np.full(m_count, -1, dtype=np.int64)
    recovered = np.zeros(m_count, dtype=np.bool_)

    running_max = np.maximum.accumulate(w, axis=1)
    drawdowns = 1.0 - w / running_max

    for i in range(m_count):
        row_dd = drawdowns[i]
        max_dd = float(np.max(row_dd))
        if max_dd == 0.0:
            times[i] = 0
            recovered[i] = True
            continue

        t_star = int(np.argmax(row_dd))
        p_peak = float(running_max[i, t_star])

        rec_indices = np.flatnonzero(w[i, t_star + 1 :] >= p_peak)
        if rec_indices.size > 0:
            t_first_rec = int(rec_indices[0]) + t_star + 1
            times[i] = t_first_rec - t_star
            recovered[i] = True
        else:
            times[i] = -1
            recovered[i] = False

    return times, recovered

