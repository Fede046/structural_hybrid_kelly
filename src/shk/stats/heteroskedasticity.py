"""Modulo per i test di eteroschedasticita' di Breusch-Pagan (Koenker) e White (US-C6.4 / Task 38).

Implementa:
- ols_residuals: calcolo dei residui OLS via fattorizzazione QR (senza inversa di X'X);
- breusch_pagan_lm: test moltiplicatore di Lagrange (LM) nella variante robusta di Koenker (1981);
- white_lm: test LM di White (1980) con termini quadratici e prodotti incrociati;
- bp_statistic e white_statistic: pipeline completa OLS + LM;
- bp_statistic_batch e white_statistic_batch: versioni vettorizzate a lotti su B campioni;
- nominal_threshold: calcolo del valore critico asintotico chi-quadro.

Tutte le regressioni (primaria e ausiliaria) impiegano la fattorizzazione QR. Per il test di White,
le colonne dei regressori possono essere standardizzate internamente prima di costruire i termini
di secondo grado: data la presenza della costante nel disegno ausiliario, lo span lineare dello spazio
{1, x, x^2, x_i * x_j} e' invariante rispetto a trasformazioni affini di x, preservando esattamente
il valore di R^2 e della statistica LM migliorando al contempo il condizionamento numerico.
"""

import math
from typing import NamedTuple
import numpy as np
import scipy.stats


class HeteroskedasticityTestResult(NamedTuple):
    """Risultato immutabile di un test di eteroschedasticita'.

    Campi
    -----
    lm_stat : float
        Statistica moltiplicatore di Lagrange (LM = n * R^2).
    p_value : float
        P-value asintotico calcolato sulla distribuzione Chi-quadro con df gradi di liberta'.
    df : int
        Gradi di liberta' del test (numero di regressori ausiliari non costanti).
    """

    lm_stat: float
    p_value: float
    df: int


class HeteroskedasticityBatchResult(NamedTuple):
    """Risultato immutabile di un test di eteroschedasticita' calcolato a lotti su B campioni.

    Campi
    -----
    lm_stats : np.ndarray
        Array 1D float64 di forma (B,) con le statistiche LM.
    p_values : np.ndarray
        Array 1D float64 di forma (B,) con i rispettivi p-value.
    df : int
        Gradi di liberta' comuni al lotto.
    """

    lm_stats: np.ndarray
    p_values: np.ndarray
    df: int


def _validate_1d_array(arr: np.ndarray, name: str) -> np.ndarray:
    """Valida che arr sia un ndarray 1D reale, finito e non vuoto."""
    if not isinstance(arr, np.ndarray):
        raise TypeError(f"'{name}' must be a numpy.ndarray, got {type(arr).__name__}")
    if arr.dtype == bool or not (
        np.issubdtype(arr.dtype, np.integer) or np.issubdtype(arr.dtype, np.floating)
    ):
        raise TypeError(f"'{name}' must have real numeric dtype, got {arr.dtype}")
    if arr.ndim != 1:
        raise ValueError(f"'{name}' must be 1-dimensional, got {arr.ndim}D with shape {arr.shape}")
    if arr.size == 0:
        raise ValueError(f"'{name}' must not be empty")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"'{name}' must contain only finite values")
    return arr.astype(np.float64, copy=False)


def _validate_2d_or_1d_regressors(arr: np.ndarray, name: str, expected_n: int) -> np.ndarray:
    """Valida che arr sia un ndarray (n, k) o (n,) reale e finito, restituendolo come (n, k)."""
    if not isinstance(arr, np.ndarray):
        raise TypeError(f"'{name}' must be a numpy.ndarray, got {type(arr).__name__}")
    if arr.dtype == bool or not (
        np.issubdtype(arr.dtype, np.integer) or np.issubdtype(arr.dtype, np.floating)
    ):
        raise TypeError(f"'{name}' must have real numeric dtype, got {arr.dtype}")
    if arr.ndim == 1:
        arr_2d = arr[:, np.newaxis]
    elif arr.ndim == 2:
        arr_2d = arr
    else:
        raise ValueError(f"'{name}' must be 1D or 2D, got {arr.ndim}D with shape {arr.shape}")

    if arr_2d.shape[0] != expected_n:
        raise ValueError(
            f"'{name}' rows ({arr_2d.shape[0]}) do not match sample size ({expected_n})"
        )
    if arr_2d.shape[1] == 0:
        raise ValueError(f"'{name}' must have at least one regressor column")
    if not np.all(np.isfinite(arr_2d)):
        raise ValueError(f"'{name}' must contain only finite values")

    return arr_2d.astype(np.float64, copy=False)


def nominal_threshold(df: int, alpha: float) -> float:
    """Restituisce il valore critico chi2.ppf(1 - alpha, df).

    Parametri
    ---------
    df : int
        Gradi di liberta' (intero >= 1).
    alpha : float
        Livello di significativita' nominale in (0, 1).

    Restituisce
    -----------
    float
        Quantile (1 - alpha) della distribuzione Chi-quadro con df gradi di liberta'.

    Solleva
    -------
    TypeError
        Se df non e' intero o alpha non e' float/np.floating.
    ValueError
        Se df < 1 oppure alpha non appartiene a (0, 1).
    """
    if isinstance(df, bool) or not isinstance(df, (int, np.integer)):
        raise TypeError(f"df must be an integer, got {type(df).__name__}")
    if isinstance(alpha, bool) or not isinstance(alpha, (float, np.floating)):
        raise TypeError(f"alpha must be a float, got {type(alpha).__name__}")
    if df < 1:
        raise ValueError(f"df must be at least 1, got {df}")
    if not (0.0 < alpha < 1.0):
        raise ValueError(f"alpha must be strictly in (0, 1), got {alpha}")

    return float(scipy.stats.chi2.ppf(1.0 - float(alpha), int(df)))


def ols_residuals(y: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Calcola i residui OLS della regressione lineare y ~ 1 + x via fattorizzazione QR.

    I regressori si passano senza colonna costante, che la funzione aggiunge automaticamente.

    Parametri
    ---------
    y : np.ndarray
        Vettore float64 (n,) della variabile dipendente.
    x : np.ndarray
        Matrice float64 (n, k) o vettore (n,) dei regressori esplicativi.

    Restituisce
    -----------
    np.ndarray
        Array 1D float64 (n,) contenente i residui OLS e = y - X * beta_hat.

    Solleva
    -------
    TypeError
        Se y o x non sono array NumPy reali.
    ValueError
        Se le dimensioni non corrispondono, se compaiono valori non finiti,
        oppure se la matrice di disegno [1, x] non ha rango colonna pieno (k + 1).
    """
    y_arr = _validate_1d_array(y, "y")
    n = y_arr.shape[0]
    x_arr = _validate_2d_or_1d_regressors(x, "x", n)
    k = x_arr.shape[1]

    if n <= k + 1:
        raise ValueError(
            f"Sample size n={n} must exceed number of parameters k+1={k+1} for full rank"
        )

    # Costruzione matrice di disegno con costante: X = [1, x]
    X = np.empty((n, k + 1), dtype=np.float64)
    X[:, 0] = 1.0
    X[:, 1:] = x_arr

    # Controllo di rango pieno
    rank = np.linalg.matrix_rank(X)
    if rank < k + 1:
        raise ValueError(
            f"Design matrix [1, x] does not have full column rank: rank={rank} < {k+1}"
        )

    # Proiezione OLS via fattorizzazione QR senza mai invertire X'X
    Q, _ = np.linalg.qr(X)
    y_hat = Q @ (Q.T @ y_arr)
    residuals = y_arr - y_hat
    return residuals


def breusch_pagan_lm(resid: np.ndarray, z: np.ndarray) -> HeteroskedasticityTestResult:
    """Calcola il test moltiplicatore di Lagrange di Breusch-Pagan (variante Koenker 1981).

    Regredisce i residui al quadrato resid^2 sulla matrice ausiliaria Z = [1, z].
    La statistica moltiplicatore di Lagrange e' definita come LM = n * R^2, asintoticamente
    distribuita come Chi-quadro con df = ncol(z) gradi di liberta'.

    Parametri
    ---------
    resid : np.ndarray
        Array 1D float64 (n,) dei residui del modello primario.
    z : np.ndarray
        Matrice (n, p) o vettore (n,) delle variabili esplicative dell'eteroschedasticita'
        (senza colonna costante, aggiunta internamente).

    Restituisce
    -----------
    HeteroskedasticityTestResult
        NamedTuple contenente la statistica LM, il relativo p-value e i gradi di liberta'.

    Solleva
    -------
    TypeError
        Se resid o z non sono array NumPy reali.
    ValueError
        Se le dimensioni non corrispondono, contengono NaN/Inf, o se Z = [1, z]
        non ha rango pieno.
    """
    resid_arr = _validate_1d_array(resid, "resid")
    n = resid_arr.shape[0]
    z_arr = _validate_2d_or_1d_regressors(z, "z", n)
    p = z_arr.shape[1]

    if n <= p + 1:
        raise ValueError(
            f"Sample size n={n} must exceed auxiliary parameters p+1={p+1} for full rank"
        )

    # Matrice ausiliaria Z = [1, z]
    Z = np.empty((n, p + 1), dtype=np.float64)
    Z[:, 0] = 1.0
    Z[:, 1:] = z_arr

    rank = np.linalg.matrix_rank(Z)
    if rank < p + 1:
        raise ValueError(
            f"Auxiliary design matrix [1, z] does not have full column rank: rank={rank} < {p+1}"
        )

    g = resid_arr ** 2
    g_bar = float(np.mean(g))
    tss = float(np.sum((g - g_bar) ** 2))

    # Se resid^2 e' costante (TSS == 0), LM vale esattamente 0
    if tss <= 0.0 or math.isclose(tss, 0.0, abs_tol=1e-15):
        return HeteroskedasticityTestResult(lm_stat=0.0, p_value=1.0, df=p)

    Q_z, _ = np.linalg.qr(Z)
    g_hat = Q_z @ (Q_z.T @ g)
    ssr = float(np.sum((g - g_hat) ** 2))

    r2 = max(0.0, min(1.0, 1.0 - ssr / tss))
    lm_val = float(n * r2)
    p_val = float(scipy.stats.chi2.sf(lm_val, p))

    return HeteroskedasticityTestResult(lm_stat=lm_val, p_value=p_val, df=p)


def _build_white_auxiliary_matrix(x_arr: np.ndarray, n: int, standardize: bool = True) -> tuple[np.ndarray, int]:
    """Costruisce la matrice ausiliaria del test di White con termini lineari, quadrati e interazioni.

    Se standardize=True, le colonne di x vengono standardizzate internamente (media 0, dev.std 1)
    prima di calcolare quadrati e prodotti incrociati. Poiche' la costante e' inclusa nel disegno,
    lo spazio generato dai regressori ausiliari {1, x, x^2, x_i*x_j} e' invariante per trasformazioni
    affini, preservando R^2 e LM e migliorando il condizionamento numerico.
    """
    k = x_arr.shape[1]
    if standardize:
        means = np.mean(x_arr, axis=0, keepdims=True)
        stds = np.std(x_arr, axis=0, keepdims=True, ddof=0)
        # Se una colonna ha std 0, non e' a rango pieno
        if np.any(stds <= 0.0):
            raise ValueError("At least one column of x has zero variance")
        x_scaled = (x_arr - means) / stds
    else:
        x_scaled = x_arr

    terms: list[np.ndarray] = [np.ones((n, 1), dtype=np.float64), x_scaled]
    for i in range(k):
        for j in range(i, k):
            terms.append(x_scaled[:, [i]] * x_scaled[:, [j]])

    Z_white = np.hstack(terms)
    p_white = Z_white.shape[1] - 1  # Gradi di liberta' escludendo la costante
    return Z_white, p_white


def white_lm(resid: np.ndarray, x: np.ndarray) -> HeteroskedasticityTestResult:
    """Calcola il test moltiplicatore di Lagrange di White (1980).

    Regredisce resid^2 su [1, x, quadrati e prodotti incrociati delle colonne di x].
    La statistica LM e' definita come n * R^2 con gradi di liberta' pari al numero di
    regressori ausiliari esclusa la costante: p = k + k*(k+1)/2.

    Parametri
    ---------
    resid : np.ndarray
        Array 1D float64 (n,) dei residui del modello primario.
    x : np.ndarray
        Matrice (n, k) o vettore (n,) dei regressori esplicativi primari.

    Restituisce
    -----------
    HeteroskedasticityTestResult
        NamedTuple contenente la statistica LM, il relativo p-value e i gradi di liberta'.

    Solleva
    -------
    TypeError
        Se resid o x non sono array NumPy reali.
    ValueError
        Se le dimensioni non corrispondono, contengono NaN/Inf, o se il disegno ausiliario
        di White non ha rango pieno.
    """
    resid_arr = _validate_1d_array(resid, "resid")
    n = resid_arr.shape[0]
    x_arr = _validate_2d_or_1d_regressors(x, "x", n)

    Z_white, df_white = _build_white_auxiliary_matrix(x_arr, n, standardize=True)

    if n <= df_white + 1:
        raise ValueError(
            f"Sample size n={n} must exceed White parameters {df_white + 1} for full rank"
        )

    rank = np.linalg.matrix_rank(Z_white)
    if rank < df_white + 1:
        raise ValueError(
            f"White auxiliary design matrix does not have full column rank: rank={rank} < {df_white + 1}"
        )

    g = resid_arr ** 2
    g_bar = float(np.mean(g))
    tss = float(np.sum((g - g_bar) ** 2))

    if tss <= 0.0 or math.isclose(tss, 0.0, abs_tol=1e-15):
        return HeteroskedasticityTestResult(lm_stat=0.0, p_value=1.0, df=df_white)

    Q_w, _ = np.linalg.qr(Z_white)
    g_hat = Q_w @ (Q_w.T @ g)
    ssr = float(np.sum((g - g_hat) ** 2))

    r2 = max(0.0, min(1.0, 1.0 - ssr / tss))
    lm_val = float(n * r2)
    p_val = float(scipy.stats.chi2.sf(lm_val, df_white))

    return HeteroskedasticityTestResult(lm_stat=lm_val, p_value=p_val, df=df_white)


def bp_statistic(
    y: np.ndarray, x: np.ndarray, z: np.ndarray | None = None
) -> HeteroskedasticityTestResult:
    """Calcola OLS su y ~ 1 + x e quindi il test di Breusch-Pagan su z (o x se z e' None).

    Parametri
    ---------
    y : np.ndarray
        Array 1D (n,) della variabile dipendente.
    x : np.ndarray
        Matrice (n, k) dei regressori primari.
    z : np.ndarray, opzionale
        Matrice (n, p) dei regressori ausiliari di eteroschedasticita'. Se None, usa x.

    Restituisce
    -----------
    HeteroskedasticityTestResult
        Risultato del test di Breusch-Pagan.
    """
    resid = ols_residuals(y, x)
    z_use = x if z is None else z
    return breusch_pagan_lm(resid, z_use)


def white_statistic(y: np.ndarray, x: np.ndarray) -> HeteroskedasticityTestResult:
    """Calcola OLS su y ~ 1 + x e quindi il test di White su x.

    Parametri
    ---------
    y : np.ndarray
        Array 1D (n,) della variabile dipendente.
    x : np.ndarray
        Matrice (n, k) dei regressori primari.

    Restituisce
    -----------
    HeteroskedasticityTestResult
        Risultato del test di White.
    """
    resid = ols_residuals(y, x)
    return white_lm(resid, x)


def _validate_batch_inputs(
    y: np.ndarray, x: np.ndarray, z: np.ndarray | None
) -> tuple[np.ndarray, np.ndarray, np.ndarray, int, int]:
    """Valida gli input a lotti su B campioni."""
    if not isinstance(y, np.ndarray):
        raise TypeError(f"'y' must be a numpy.ndarray, got {type(y).__name__}")
    if y.dtype == bool or not (np.issubdtype(y.dtype, np.integer) or np.issubdtype(y.dtype, np.floating)):
        raise TypeError(f"'y' must have real numeric dtype, got {y.dtype}")
    if y.ndim != 2:
        raise ValueError(f"'y' must be 2D of shape (B, n), got {y.ndim}D with shape {y.shape}")
    if not np.all(np.isfinite(y)):
        raise ValueError("'y' must contain only finite values")

    b_count, n = y.shape
    if b_count < 1 or n < 3:
        raise ValueError(f"Invalid batch dimensions: B={b_count}, n={n}")

    if not isinstance(x, np.ndarray):
        raise TypeError(f"'x' must be a numpy.ndarray, got {type(x).__name__}")
    if x.dtype == bool or not (np.issubdtype(x.dtype, np.integer) or np.issubdtype(x.dtype, np.floating)):
        raise TypeError(f"'x' must have real numeric dtype, got {x.dtype}")
    if not np.all(np.isfinite(x)):
        raise ValueError("'x' must contain only finite values")

    if x.ndim == 2:
        if x.shape[0] != n:
            raise ValueError(f"'x' shape (n, k) rows {x.shape[0]} do not match y sample size n={n}")
        x_batch = np.broadcast_to(x[np.newaxis, :, :], (b_count, n, x.shape[1]))
    elif x.ndim == 3:
        if x.shape[0] != b_count or x.shape[1] != n:
            raise ValueError(
                f"'x' shape (B, n, k) ({x.shape}) does not match y shape ({b_count}, {n})"
            )
        x_batch = x
    else:
        raise ValueError(f"'x' must be 2D (n, k) or 3D (B, n, k), got {x.ndim}D")

    if z is None:
        z_batch = x_batch
    else:
        if not isinstance(z, np.ndarray):
            raise TypeError(f"'z' must be a numpy.ndarray, got {type(z).__name__}")
        if z.dtype == bool or not (np.issubdtype(z.dtype, np.integer) or np.issubdtype(z.dtype, np.floating)):
            raise TypeError(f"'z' must have real numeric dtype, got {z.dtype}")
        if not np.all(np.isfinite(z)):
            raise ValueError("'z' must contain only finite values")

        if z.ndim == 2:
            if z.shape[0] != n:
                raise ValueError(f"'z' shape (n, p) rows {z.shape[0]} do not match y sample size n={n}")
            z_batch = np.broadcast_to(z[np.newaxis, :, :], (b_count, n, z.shape[1]))
        elif z.ndim == 3:
            if z.shape[0] != b_count or z.shape[1] != n:
                raise ValueError(
                    f"'z' shape (B, n, p) ({z.shape}) does not match y shape ({b_count}, {n})"
                )
            z_batch = z
        else:
            raise ValueError(f"'z' must be 2D (n, p) or 3D (B, n, p), got {z.ndim}D")

    return (
        y.astype(np.float64, copy=False),
        x_batch.astype(np.float64, copy=False),
        z_batch.astype(np.float64, copy=False),
        b_count,
        n,
    )


def bp_statistic_batch(
    y: np.ndarray, x: np.ndarray, z: np.ndarray | None = None
) -> HeteroskedasticityBatchResult:
    """Versione a lotti del test di Breusch-Pagan su B campioni: y (B, n), x (B, n, k) o (n, k).

    Parametri
    ---------
    y : np.ndarray
        Array 2D (B, n) delle risposte per i B campioni.
    x : np.ndarray
        Array 3D (B, n, k) o 2D (n, k) dei regressori primari.
    z : np.ndarray, opzionale
        Array 3D (B, n, p) o 2D (n, p) dei regressori ausiliari. Se None, usa x.

    Restituisce
    -----------
    HeteroskedasticityBatchResult
        Statistiche LM (B,), p-values (B,) e gradi di liberta' comuni df.
    """
    y_arr, x_batch, z_batch, b_count, n = _validate_batch_inputs(y, x, z)
    k = x_batch.shape[2]
    p = z_batch.shape[2]

    # Matrice primaria X per tutti i batch: [1, x]
    X_batch = np.empty((b_count, n, k + 1), dtype=np.float64)
    X_batch[:, :, 0] = 1.0
    X_batch[:, :, 1:] = x_batch

    # Verifica rango per ogni campione nel batch
    for b in range(b_count):
        if np.linalg.matrix_rank(X_batch[b]) < k + 1:
            raise ValueError(f"Design matrix [1, x] at batch index {b} is rank deficient")

    # QR impilato batch su X: Q ha forma (B, n, k+1)
    Q_x, _ = np.linalg.qr(X_batch)
    # y_arr: (B, n, 1)
    y_3d = y_arr[:, :, np.newaxis]
    # y_hat: (B, n, 1) = Q @ (Q.T @ y)
    y_hat_3d = Q_x @ (Q_x.swapaxes(-2, -1) @ y_3d)
    resid_batch = y_arr - y_hat_3d[:, :, 0]

    # Matrice ausiliaria Z per tutti i batch: [1, z]
    Z_batch = np.empty((b_count, n, p + 1), dtype=np.float64)
    Z_batch[:, :, 0] = 1.0
    Z_batch[:, :, 1:] = z_batch

    for b in range(b_count):
        if np.linalg.matrix_rank(Z_batch[b]) < p + 1:
            raise ValueError(f"Auxiliary matrix [1, z] at batch index {b} is rank deficient")

    Q_z, _ = np.linalg.qr(Z_batch)

    g_batch = resid_batch ** 2
    g_bar = np.mean(g_batch, axis=1, keepdims=True)
    tss_batch = np.sum((g_batch - g_bar) ** 2, axis=1)

    g_3d = g_batch[:, :, np.newaxis]
    g_hat_3d = Q_z @ (Q_z.swapaxes(-2, -1) @ g_3d)
    ssr_batch = np.sum((g_batch - g_hat_3d[:, :, 0]) ** 2, axis=1)

    r2_batch = np.zeros(b_count, dtype=np.float64)
    valid_mask = tss_batch > 1e-15
    r2_batch[valid_mask] = np.clip(1.0 - ssr_batch[valid_mask] / tss_batch[valid_mask], 0.0, 1.0)

    lm_batch = n * r2_batch
    p_batch = scipy.stats.chi2.sf(lm_batch, p)

    return HeteroskedasticityBatchResult(lm_stats=lm_batch, p_values=p_batch, df=p)


def white_statistic_batch(
    y: np.ndarray, x: np.ndarray
) -> HeteroskedasticityBatchResult:
    """Versione a lotti del test di White su B campioni: y (B, n), x (B, n, k) o (n, k).

    Parametri
    ---------
    y : np.ndarray
        Array 2D (B, n) delle risposte per i B campioni.
    x : np.ndarray
        Array 3D (B, n, k) o 2D (n, k) dei regressori primari.

    Restituisce
    -----------
    HeteroskedasticityBatchResult
        Statistiche LM (B,), p-values (B,) e gradi di liberta' comuni df.
    """
    y_arr, x_batch, _, b_count, n = _validate_batch_inputs(y, x, None)
    k = x_batch.shape[2]

    # Matrice primaria X per tutti i batch: [1, x]
    X_batch = np.empty((b_count, n, k + 1), dtype=np.float64)
    X_batch[:, :, 0] = 1.0
    X_batch[:, :, 1:] = x_batch

    for b in range(b_count):
        if np.linalg.matrix_rank(X_batch[b]) < k + 1:
            raise ValueError(f"Design matrix [1, x] at batch index {b} is rank deficient")

    Q_x, _ = np.linalg.qr(X_batch)
    y_3d = y_arr[:, :, np.newaxis]
    y_hat_3d = Q_x @ (Q_x.swapaxes(-2, -1) @ y_3d)
    resid_batch = y_arr - y_hat_3d[:, :, 0]

    # Costruzione delle matrici di White per ciascun campione
    df_white = k + (k * (k + 1)) // 2
    Z_white_batch = np.empty((b_count, n, df_white + 1), dtype=np.float64)
    for b in range(b_count):
        Z_b, df_b = _build_white_auxiliary_matrix(x_batch[b], n, standardize=True)
        if np.linalg.matrix_rank(Z_b) < df_b + 1:
            raise ValueError(f"White auxiliary matrix at batch index {b} is rank deficient")
        Z_white_batch[b] = Z_b

    Q_w, _ = np.linalg.qr(Z_white_batch)

    g_batch = resid_batch ** 2
    g_bar = np.mean(g_batch, axis=1, keepdims=True)
    tss_batch = np.sum((g_batch - g_bar) ** 2, axis=1)

    g_3d = g_batch[:, :, np.newaxis]
    g_hat_3d = Q_w @ (Q_w.swapaxes(-2, -1) @ g_3d)
    ssr_batch = np.sum((g_batch - g_hat_3d[:, :, 0]) ** 2, axis=1)

    r2_batch = np.zeros(b_count, dtype=np.float64)
    valid_mask = tss_batch > 1e-15
    r2_batch[valid_mask] = np.clip(1.0 - ssr_batch[valid_mask] / tss_batch[valid_mask], 0.0, 1.0)

    lm_batch = n * r2_batch
    p_batch = scipy.stats.chi2.sf(lm_batch, df_white)

    return HeteroskedasticityBatchResult(lm_stats=lm_batch, p_values=p_batch, df=df_white)
