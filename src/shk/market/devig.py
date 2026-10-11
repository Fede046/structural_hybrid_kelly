"""Metodi di de-vigging per mercati di scommesse a quote decimali."""

from typing import Final
import numpy as np

# Numero massimo di iterazioni per il risolutore Newton-Raphson del metodo power
MAX_NEWTON_ITERATIONS: Final[int] = 50

# Numero massimo di iterazioni delle bisezioni dei metodi Shin e odds ratio: 200 dimezzamenti
# portano qualunque intervallo iniziale sotto la risoluzione dei float64
MAX_BISECTION_ITERATIONS: Final[int] = 200


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


def _check_sums(q: np.ndarray, applicable: np.ndarray, method: str, n_iterations: int) -> None:
    """Solleva RuntimeError se un mercato applicabile ha |sum(q) - 1| > 1e-12."""
    sums = q[applicable].sum(axis=1)
    unconverged_count = int(np.sum(np.abs(sums - 1.0) > 1e-12))
    if unconverged_count > 0:
        raise RuntimeError(
            f"{method} devigging solver failed to converge within tolerance 1e-12 "
            f"for {unconverged_count} of {q.shape[0]} markets after {n_iterations} iterations"
        )


def _shin_probabilities(pi: np.ndarray, s: np.ndarray, z: np.ndarray) -> np.ndarray:
    """Probabilita' di Shin per z in [0, 1): (sqrt(z^2 + 4(1 - z) pi^2 / S) - z) / (2(1 - z))."""
    return (np.sqrt(z**2 + 4.0 * (1.0 - z) * pi**2 / s) - z) / (2.0 * (1.0 - z))


def devig_shin(odds: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Calcola le probabilita' de-viggate con il metodo di Shin e il parametro z di ciascun mercato.

    q_i = (sqrt(z^2 + 4 (1 - z) pi_i^2 / S) - z) / (2 (1 - z)), con z in [0, 1) tale che
    sum(q_i) = 1 (nota 2.1 §6.5; Jullien e Salanie' 1994). z e' la frazione di volume
    attribuita agli scommettitori informati.

    Metodo numerico, a intervallo garantito: f(z) = sum(q_i(z)) - 1 vale sqrt(S) - 1 >= 0
    in z = 0 e tende a sum(pi_i^2) / S - 1 < 0 per z -> 1 (perche' ogni pi_i < 1), quindi
    una radice sta in [0, 1). La bisezione vettorizzata su [0, 1] mantiene f(lo) >= 0 e
    f(hi) < 0, valuta f solo nei punti medi (mai in z = 1) e si ferma quando il punto medio
    coincide con un estremo, oppure dopo MAX_BISECTION_ITERATIONS iterazioni.

    Casi particolari: con S = 1 si ha z = 0 e q = pi. Con S < 1 (mercato sotto la parita')
    non esiste z in [0, 1): la riga di q e lo z del mercato valgono NaN, come le righe non
    applicabili di devig_additive.

    Parametri
    ----------
    odds : np.ndarray
        Array di quote decimali di forma (N, n) con n >= 2.

    Restituisce
    -----------
    tuple[np.ndarray, np.ndarray]
        Tupla (q, z): q di forma (N, n), z di forma (N,); NaN sulle righe con S < 1.

    Solleva
    -------
    RuntimeError
        Se un mercato con S >= 1 ha |sum(q) - 1| > 1e-12 alla fine della bisezione.
    """
    pi = implied_probabilities(odds)
    s = pi.sum(axis=1, keepdims=True)
    applicable = (s >= 1.0)[:, 0]

    lo = np.zeros_like(s)
    hi = np.ones_like(s)
    exact = (s == 1.0)[:, 0]
    n_iterations = 0
    for n_iterations in range(1, MAX_BISECTION_ITERATIONS + 1):
        mid = 0.5 * (lo + hi)
        active = applicable & ~exact & (mid[:, 0] > lo[:, 0]) & (mid[:, 0] < hi[:, 0])
        if not np.any(active):
            break
        f_mid = _shin_probabilities(pi, s, mid).sum(axis=1, keepdims=True) - 1.0
        go_right = (f_mid >= 0.0) & active[:, None]
        go_left = (f_mid < 0.0) & active[:, None]
        lo = np.where(go_right, mid, lo)
        hi = np.where(go_left, mid, hi)

    z = 0.5 * (lo + hi)
    z[exact] = 0.0
    q = _shin_probabilities(pi, s, z)
    q[exact] = pi[exact]
    q[~applicable] = np.nan
    z[~applicable] = np.nan

    _check_sums(q, applicable, "Shin", n_iterations)
    return q, z.flatten()


def _odds_ratio_probabilities(pi: np.ndarray, c: np.ndarray) -> np.ndarray:
    """Probabilita' odds ratio: c pi / (1 - pi + c pi)."""
    return c * pi / (1.0 - pi + c * pi)


def devig_odds_ratio(odds: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Calcola le probabilita' de-viggate con il metodo odds ratio (Cheung 2015) e il parametro c.

    q_i = c pi_i / (1 - pi_i + c pi_i), con c > 0 tale che sum(q_i) = 1 (nota 2.1 §6.3):
    l'odds ratio fra q_i e pi_i e' lo stesso per tutti gli esiti.

    Metodo numerico, a intervallo garantito: f(c) = sum(q_i(c)) - 1 e' strettamente
    crescente in c, con f(0) = -1, f(1) = S - 1 e f(c) -> n - 1 > 0 per c -> infinito.
    Con S > 1 la radice sta in (0, 1); con S < 1 sta in (1, hi), dove hi si raddoppia a
    partire da 2 finche' f(hi) >= 0; con S = 1 vale c = 1 e q = pi. Poi bisezione
    vettorizzata come in devig_shin.

    Parametri
    ----------
    odds : np.ndarray
        Array di quote decimali di forma (N, n) con n >= 2.

    Restituisce
    -----------
    tuple[np.ndarray, np.ndarray]
        Tupla (q, c): q di forma (N, n), c di forma (N,).

    Solleva
    -------
    RuntimeError
        Se un mercato ha |sum(q) - 1| > 1e-12 alla fine della bisezione, o se l'estremo
        superiore non si trova entro MAX_BISECTION_ITERATIONS raddoppi.
    """
    pi = implied_probabilities(odds)
    s = pi.sum(axis=1, keepdims=True)
    n_markets = pi.shape[0]
    exact = (s == 1.0)[:, 0]
    under = (s < 1.0)[:, 0]

    lo = np.where(under[:, None], 1.0, 0.0)
    hi = np.where(under[:, None], 2.0, 1.0)
    for _ in range(MAX_BISECTION_ITERATIONS):
        need = under & (_odds_ratio_probabilities(pi, hi).sum(axis=1) - 1.0 < 0.0)
        if not np.any(need):
            break
        lo = np.where(need[:, None], hi, lo)
        hi = np.where(need[:, None], 2.0 * hi, hi)
    else:
        raise RuntimeError(
            f"Odds ratio devigging: upper bracket not found for some of {n_markets} markets"
        )

    n_iterations = 0
    for n_iterations in range(1, MAX_BISECTION_ITERATIONS + 1):
        mid = 0.5 * (lo + hi)
        active = ~exact & (mid[:, 0] > lo[:, 0]) & (mid[:, 0] < hi[:, 0])
        if not np.any(active):
            break
        f_mid = _odds_ratio_probabilities(pi, mid).sum(axis=1, keepdims=True) - 1.0
        go_right = (f_mid < 0.0) & active[:, None]
        go_left = (f_mid >= 0.0) & active[:, None]
        lo = np.where(go_right, mid, lo)
        hi = np.where(go_left, mid, hi)

    c = 0.5 * (lo + hi)
    c[exact] = 1.0
    q = _odds_ratio_probabilities(pi, c)
    q[exact] = pi[exact]

    _check_sums(q, np.ones(n_markets, dtype=bool), "Odds ratio", n_iterations)
    return q, c.flatten()
