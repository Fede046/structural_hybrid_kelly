"""Metodi di de-vigging per mercati di scommesse a quote decimali."""

from typing import Final
import numpy as np

# Numero massimo di iterazioni per il risolutore Newton-Raphson del metodo power
MAX_NEWTON_ITERATIONS: Final[int] = 50


def _validate_odds(odds: np.ndarray) -> np.ndarray:
    """Valida l'array delle quote decimali e lo converte in float64.

    Parametri
    ----------
    odds : np.ndarray
        Array bidimensionale di quote decimali di forma (N, n) con n >= 2.

    Restituisce
    -----------
    np.ndarray
        Array convertito in np.float64 di forma (N, n).

    Solleva
    -------
    TypeError
        Se odds non e' un ndarray, oppure se ha tipo booleano, complesso,
        stringa o oggetto non numerico.
    ValueError
        Se odds non ha due dimensioni, se il numero di esiti n e' minore di 2,
        se contiene valori non finiti (NaN, inf), oppure se include quote
        non strettamente maggiori di 1.0.
    """
    if not isinstance(odds, np.ndarray):
        raise TypeError(f"odds must be a numpy.ndarray, got {type(odds).__name__}")

    if odds.dtype == bool or not (
        np.issubdtype(odds.dtype, np.integer) or np.issubdtype(odds.dtype, np.floating)
    ):
        raise TypeError(
            f"odds must have a real integer or floating dtype, got {odds.dtype}"
        )

    if odds.ndim != 2 or odds.shape[1] < 2:
        raise ValueError(f"odds must have shape (N, n) with n >= 2, got {odds.shape}")

    if not np.all(np.isfinite(odds)):
        raise ValueError("odds must contain only finite values")

    if np.any(odds <= 1.0):
        raise ValueError("odds must be strictly greater than 1.0")

    return odds.astype(np.float64, copy=False)


def implied_probabilities(odds: np.ndarray) -> np.ndarray:
    """Calcola le probabilita' implicite grezze (reciproci delle quote).

    Parametri
    ----------
    odds : np.ndarray
        Array di quote decimali di forma (N, n) con n >= 2.

    Restituisce
    -----------
    np.ndarray
        Array di forma (N, n) contenente pi_i = 1 / o_i.
    """
    o = _validate_odds(odds)
    return 1.0 / o


def overround(odds: np.ndarray) -> np.ndarray:
    """Calcola l'overround di ciascun mercato (somma delle probabilita' implicite meno 1).

    Parametri
    ----------
    odds : np.ndarray
        Array di quote decimali di forma (N, n) con n >= 2.

    Restituisce
    -----------
    np.ndarray
        Array monodimensionale di forma (N,) contenente S - 1 = sum(pi_i) - 1.
    """
    pi = implied_probabilities(odds)
    return pi.sum(axis=1) - 1.0


def devig_proportional(odds: np.ndarray) -> np.ndarray:
    """Calcola le probabilita' de-viggati con il metodo proporzionale (normalizzazione).

    q_i = pi_i / S, dove S = sum(pi_i).

    Parametri
    ----------
    odds : np.ndarray
        Array di quote decimali di forma (N, n) con n >= 2.

    Restituisce
    -----------
    np.ndarray
        Array di forma (N, n) contenente le probabilita' q_i che sommano a 1.
    """
    pi = implied_probabilities(odds)
    s = pi.sum(axis=1, keepdims=True)
    return pi / s


def devig_additive(odds: np.ndarray) -> np.ndarray:
    """Calcola le probabilita' de-viggati con il metodo additivo (sottrazione uniforme dell'aggio).

    q_i = pi_i - (S - 1) / n, dove n e' il numero di esiti e S = sum(pi_i).
    Se per un dato mercato anche un solo q_i risulta minore o uguale a zero,
    l'intera riga viene impostata a NaN, indicando che il metodo non e' applicabile.

    Parametri
    ----------
    odds : np.ndarray
        Array di quote decimali di forma (N, n) con n >= 2.

    Restituisce
    -----------
    np.ndarray
        Array di forma (N, n) contenente le probabilita' q_i, oppure NaN per mercati
        con probabilita' non positive.
    """
    pi = implied_probabilities(odds)
    n = odds.shape[1]
    s = pi.sum(axis=1, keepdims=True)
    q = pi - (s - 1.0) / n
    invalid_mask = np.any(q <= 0.0, axis=1)
    q = np.where(invalid_mask[:, None], np.nan, q)
    return q


def devig_power(odds: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Calcola le probabilita' de-viggati con il metodo power e l'esponente k di ciascun mercato.

    q_i = pi_i^k con k > 0 tale che sum(pi_i^k) = 1.

    Giustificazione teorica del metodo numerico:
    Definendo f(k) = sum(pi_i^k) - 1, per k > 0 si ha f'(k) = sum(pi_i^k * ln(pi_i)) < 0
    (strettamente decrescente poiche' pi_i in (0, 1) implica ln(pi_i) < 0) e
    f''(k) = sum(pi_i^k * (ln(pi_i))^2) > 0 (strettamente convessa). Pertanto, la radice k*
    e' unica. L'iterazione di Newton-Raphson parte da k_0 = 1.0, che corrisponde al caso
    esatto per mercati senza aggio (S = 1 => f(1) = 0) ed e' vicina alla radice per gli aggi
    tipici di mercato (k in [0.9, 1.2]). La stretta decrescenza e convessita' assicurano
    una rapida convergenza quadratica. Per salvaguardare la positivita' k > 0 su mercati
    con quote arbitrarie o S molto piccolo, ogni passo adotta k_next = max(k - step, k / 2).

    Parametri
    ----------
    odds : np.ndarray
        Array di quote decimali di forma (N, n) con n >= 2.

    Restituisce
    -----------
    tuple[np.ndarray, np.ndarray]
        Tupla (q, k) dove q e' un array di forma (N, n) contenente le probabilita'
        de-viggati e k e' un array 1D di forma (N,) contenente l'esponente stimato.

    Solleva
    -------
    RuntimeError
        Se il risolutore non converge entro la tolleranza 1e-12 per uno o piu' mercati
        entro MAX_NEWTON_ITERATIONS iterazioni.
    """
    pi = implied_probabilities(odds)
    n_markets = pi.shape[0]
    log_pi = np.log(pi)

    k = np.ones((n_markets, 1), dtype=np.float64)

    for _ in range(MAX_NEWTON_ITERATIONS):
        pi_k = pi**k
        f = pi_k.sum(axis=1, keepdims=True) - 1.0
        if np.all(np.abs(f) < 1e-13):
            break
        f_prime = (pi_k * log_pi).sum(axis=1, keepdims=True)
        step = f / f_prime
        k_next = k - step
        # Salvaguardia positiva
        k = np.maximum(k_next, k * 0.5)

    q = pi**k
    sums = q.sum(axis=1)
    discrepancies = np.abs(sums - 1.0)
    unconverged_count = int(np.sum(discrepancies > 1e-12))
    if unconverged_count > 0:
        raise RuntimeError(
            f"Power devigging solver failed to converge within tolerance 1e-12 "
            f"for {unconverged_count} of {n_markets} markets after {MAX_NEWTON_ITERATIONS} iterations"
        )

    return q, k.flatten()
