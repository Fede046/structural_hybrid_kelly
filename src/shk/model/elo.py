"""Modulo per il calcolo dei rating Elo, punteggio atteso e mapping 1X2."""

import math
from typing import Any
import numpy as np


def _validate_scalar_real(val: object, name: str) -> float:
    """Valida che un argomento scalare sia numerico reale e finito."""
    if isinstance(val, (bool, np.bool_)) or not isinstance(
        val, (int, float, np.integer, np.floating)
    ):
        raise TypeError(
            f"'{name}' must be a real scalar number, got {type(val).__name__}"
        )
    if not math.isfinite(val):
        raise ValueError(f"'{name}' must be finite, got {val}")
    return float(val)


def _validate_delta(
    delta: object,
) -> tuple[bool, float | np.ndarray]:
    """Valida delta (scalare o np.ndarray reale) e restituisce un indicatore e il dato convertito."""
    if isinstance(delta, (bool, np.bool_)):
        raise TypeError(f"'delta' cannot be a boolean, got {type(delta).__name__}")

    if isinstance(delta, np.ndarray):
        if delta.dtype == bool or not (
            np.issubdtype(delta.dtype, np.integer)
            or np.issubdtype(delta.dtype, np.floating)
        ):
            raise TypeError(
                f"'delta' ndarray must have a real integer or floating dtype, got {delta.dtype}"
            )
        if not np.all(np.isfinite(delta)):
            raise ValueError("'delta' ndarray must contain only finite values")
        return True, delta.astype(np.float64, copy=False)

    if isinstance(delta, (int, float, np.integer, np.floating)):
        if not math.isfinite(delta):
            raise ValueError(f"'delta' must be finite, got {delta}")
        return False, float(delta)

    raise TypeError(
        f"'delta' must be a real scalar number or numpy.ndarray, got {type(delta).__name__}"
    )


def _validate_s(s: object) -> float:
    """Valida il parametro di scala s."""
    s_val = _validate_scalar_real(s, "s")
    if s_val <= 0.0:
        raise ValueError(f"Scale parameter 's' must be strictly positive (s > 0), got {s}")
    return s_val


def _validate_nu(nu: object) -> float:
    """Valida il parametro nu di Davidson."""
    nu_val = _validate_scalar_real(nu, "nu")
    if nu_val <= 0.0:
        raise ValueError(f"Draw parameter 'nu' must be strictly positive (nu > 0), got {nu}")
    return nu_val


def _validate_c(c: object) -> float:
    """Valida la probabilità di pareggio c."""
    c_val = _validate_scalar_real(c, "c")
    if c_val <= 0.0 or c_val >= 1.0:
        raise ValueError(f"Draw probability 'c' must be strictly in (0, 1), got {c}")
    return c_val


def _validate_k(k: object) -> float:
    """Valida il fattore di aggiornamento k."""
    k_val = _validate_scalar_real(k, "k")
    if k_val < 0.0:
        raise ValueError(f"Update factor 'k' must be non-negative (k >= 0), got {k}")
    return k_val


def _validate_outcome(outcome: object) -> str:
    """Valida l'esito della partita."""
    if not isinstance(outcome, str):
        raise TypeError(f"Outcome must be a str, got {type(outcome).__name__}")
    if outcome not in ("H", "D", "A"):
        raise ValueError(f"Outcome must be one of 'H', 'D', 'A', got {outcome!r}")
    return outcome


def elo_delta(
    r_home: float | int | np.integer | np.floating,
    r_away: float | int | np.integer | np.floating,
    h: float | int | np.integer | np.floating = 0.0,
) -> float:
    """Calcola il differenziale di rating Elo con vantaggio campo.

    Formula:
        delta = r_home - r_away + h

    Parametri
    ---------
    r_home : float | int | np.integer | np.floating
        Rating Elo della squadra di casa (scalare reale e finito).
    r_away : float | int | np.integer | np.floating
        Rating Elo della squadra in trasferta (scalare reale e finito).
    h : float | int | np.integer | np.floating, opzionale
        Vantaggio campo in punti Elo (scalare reale e finito, default 0.0).

    Restituisce
    -----------
    float
        Differenziale di rating scalare.

    Solleva
    -------
    TypeError
        Se uno dei parametri è di tipo booleano o non è uno scalare reale.
    ValueError
        Se uno dei parametri non è un valore finito.
    """
    r_h = _validate_scalar_real(r_home, "r_home")
    r_a = _validate_scalar_real(r_away, "r_away")
    h_val = _validate_scalar_real(h, "h")
    return float(r_h - r_a + h_val)


def expected_score(
    delta: float | int | np.integer | np.floating | np.ndarray,
    s: float | int | np.integer | np.floating = 400.0,
) -> float | np.ndarray:
    """Calcola il punteggio atteso logistico del modello Elo.

    Formula:
        E = 1 / (1 + 10^(-delta / s))

    Parametri
    ---------
    delta : float | int | np.integer | np.floating | np.ndarray
        Differenziale di rating Elo (scalare reale o ndarray reale di qualsiasi dimensione).
    s : float | int | np.integer | np.floating, opzionale
        Parametro di scala Elo, strettamente positivo (default 400.0).

    Restituisce
    -----------
    float | np.ndarray
        Punteggio atteso compreso in (0, 1). Se delta è uno scalare, restituisce un float
        Python nativo. Se delta è un np.ndarray (incluso quello a 0 dimensioni),
        restituisce un np.ndarray float64 con la stessa forma di delta.

    Solleva
    -------
    TypeError
        Se s o delta sono booleani, se delta non è uno scalare reale né un ndarray,
        se delta è un ndarray con dtype bool o non reale, oppure se s non è uno scalare reale.
    ValueError
        Se s <= 0, se s non è finito, oppure se delta contiene valori non finiti.
    """
    s_val = _validate_s(s)
    is_arr, d = _validate_delta(delta)

    if is_arr:
        assert isinstance(d, np.ndarray)
        exponent = -d / s_val
        denom = 1.0 + np.power(10.0, exponent, dtype=np.float64)
        return np.asarray(1.0 / denom, dtype=np.float64)
    else:
        assert isinstance(d, float)
        exponent = -d / s_val
        if exponent > 308.0:
            return 0.0
        if exponent < -308.0:
            return 1.0
        return float(1.0 / (1.0 + math.pow(10.0, exponent)))


def elo_update(
    r_home: float | int | np.integer | np.floating,
    r_away: float | int | np.integer | np.floating,
    outcome: str,
    k: float | int | np.integer | np.floating,
    h: float | int | np.integer | np.floating = 0.0,
    s: float | int | np.integer | np.floating = 400.0,
) -> tuple[float, float]:
    """Aggiorna i rating Elo a somma zero in base all'esito osservato.

    Formule:
        delta = elo_delta(r_home, r_away, h)
        E = expected_score(delta, s)
        S = 1.0 (se outcome == 'H'), 0.5 (se outcome == 'D'), 0.0 (se outcome == 'A')
        r_home' = r_home + k * (S - E)
        r_away' = r_away - k * (S - E)

    Parametri
    ---------
    r_home : float | int | np.integer | np.floating
        Rating Elo iniziale della squadra di casa.
    r_away : float | int | np.integer | np.floating
        Rating Elo iniziale della squadra in trasferta.
    outcome : str
        Esito della partita: 'H' (vittoria casa), 'D' (pareggio), 'A' (vittoria trasferta).
    k : float | int | np.integer | np.floating
        Fattore di aggiornamento Elo non negativo (k >= 0).
    h : float | int | np.integer | np.floating, opzionale
        Vantaggio campo in punti Elo (default 0.0).
    s : float | int | np.integer | np.floating, opzionale
        Parametro di scala Elo, strettamente positivo (default 400.0).

    Restituisce
    -----------
    tuple[float, float]
        Coppia (r_home_new, r_away_new) con i rating aggiornati.

    Solleva
    -------
    TypeError
        Se i rating, h, k o s sono booleani o non scalari reali, oppure se outcome non è str.
    ValueError
        Se un parametro non è finito, se k < 0, se s <= 0, oppure se outcome non è in {'H', 'D', 'A'}.
    """
    r_h = _validate_scalar_real(r_home, "r_home")
    r_a = _validate_scalar_real(r_away, "r_away")
    out = _validate_outcome(outcome)
    k_val = _validate_k(k)
    h_val = _validate_scalar_real(h, "h")
    s_val = _validate_s(s)

    delta = elo_delta(r_h, r_a, h_val)
    e = expected_score(delta, s=s_val)
    assert isinstance(e, float)

    s_score = 1.0 if out == "H" else (0.5 if out == "D" else 0.0)
    delta_r = k_val * (s_score - e)

    return float(r_h + delta_r), float(r_a - delta_r)


def davidson_probabilities(
    delta: float | int | np.integer | np.floating | np.ndarray,
    nu: float | int | np.integer | np.floating,
    s: float | int | np.integer | np.floating = 400.0,
) -> tuple[float | np.ndarray, float | np.ndarray, float | np.ndarray]:
    """Calcola le probabilità 1X2 secondo il mapping di Davidson per differenziali Elo.

    Formule:
        r = 10^(delta / s)
        D = r + 1 + nu * sqrt(r)
        p_home = r / D
        p_draw = nu * sqrt(r) / D
        p_away = 1 / D

    Parametri
    ---------
    delta : float | int | np.integer | np.floating | np.ndarray
        Differenziale di rating Elo (scalare reale o ndarray reale di qualsiasi dimensione).
    nu : float | int | np.integer | np.floating
        Parametro di frequenza del pareggio, strettamente positivo (nu > 0).
    s : float | int | np.integer | np.floating, opzionale
        Parametro di scala Elo, strettamente positivo (default 400.0).

    Restituisce
    -----------
    tuple[float | np.ndarray, float | np.ndarray, float | np.ndarray]
        Terna (p_home, p_draw, p_away). Se delta è uno scalare reale, ciascun elemento
        è un float Python nativo. Se delta è un np.ndarray, ciascun elemento è un
        np.ndarray float64 con la stessa forma di delta.

    Solleva
    -------
    TypeError
        Se nu, s o delta sono booleani, se delta non è uno scalare reale né un ndarray,
        se delta ha dtype bool o non reale, oppure se nu o s non sono scalari reali.
    ValueError
        Se nu <= 0, se s <= 0, se nu o s non sono finiti, oppure se delta contiene valori non finiti.
    """
    nu_val = _validate_nu(nu)
    s_val = _validate_s(s)
    is_arr, d = _validate_delta(delta)

    if is_arr:
        assert isinstance(d, np.ndarray)
        r = np.power(10.0, d / s_val, dtype=np.float64)
        sqrt_r = np.sqrt(r)
        denom = r + 1.0 + nu_val * sqrt_r
        p_home = np.asarray(r / denom, dtype=np.float64)
        p_draw = np.asarray((nu_val * sqrt_r) / denom, dtype=np.float64)
        p_away = np.asarray(1.0 / denom, dtype=np.float64)
        return p_home, p_draw, p_away
    else:
        assert isinstance(d, float)
        scaled = d / s_val
        if scaled > 308.0:
            return 1.0, 0.0, 0.0
        if scaled < -308.0:
            return 0.0, 0.0, 1.0
        r = math.pow(10.0, scaled)
        sqrt_r = math.sqrt(r)
        denom = r + 1.0 + nu_val * sqrt_r
        return float(r / denom), float((nu_val * sqrt_r) / denom), float(1.0 / denom)


def constant_draw_probabilities(
    delta: float | int | np.integer | np.floating | np.ndarray,
    c: float | int | np.integer | np.floating,
    s: float | int | np.integer | np.floating = 400.0,
) -> tuple[float | np.ndarray, float | np.ndarray, float | np.ndarray]:
    """Calcola le probabilità 1X2 secondo la baseline a probabilità di pareggio costante.

    Formule:
        E = expected_score(delta, s)
        p_draw = c
        p_home = (1 - c) * E
        p_away = (1 - c) * (1 - E)

    Parametri
    ---------
    delta : float | int | np.integer | np.floating | np.ndarray
        Differenziale di rating Elo (scalare reale o ndarray reale di qualsiasi dimensione).
    c : float | int | np.integer | np.floating
        Probabilità fissa di pareggio, strettamente compresa in (0, 1).
    s : float | int | np.integer | np.floating, opzionale
        Parametro di scala Elo, strettamente positivo (default 400.0).

    Restituisce
    -----------
    tuple[float | np.ndarray, float | np.ndarray, float | np.ndarray]
        Terna (p_home, p_draw, p_away). Se delta è uno scalare reale, ciascun elemento
        è un float Python nativo. Se delta è un np.ndarray, ciascun elemento è un
        np.ndarray float64 con la stessa forma di delta.

    Solleva
    -------
    TypeError
        Se c, s o delta sono booleani, se delta non è uno scalare reale né un ndarray,
        se delta ha dtype bool o non reale, oppure se c o s non sono scalari reali.
    ValueError
        Se c <= 0 o c >= 1, se c non è finito, se s <= 0, se s non è finito,
        oppure se delta contiene valori non finiti.
    """
    c_val = _validate_c(c)
    s_val = _validate_s(s)
    is_arr, d = _validate_delta(delta)

    if is_arr:
        assert isinstance(d, np.ndarray)
        e = expected_score(d, s=s_val)
        assert isinstance(e, np.ndarray)
        p_draw = np.full(d.shape, float(c_val), dtype=np.float64)
        one_minus_c = 1.0 - c_val
        p_home = np.asarray(one_minus_c * e, dtype=np.float64)
        p_away = np.asarray(one_minus_c * (1.0 - e), dtype=np.float64)
        return p_home, p_draw, p_away
    else:
        assert isinstance(d, float)
        e = expected_score(d, s=s_val)
        assert isinstance(e, float)
        p_draw = float(c_val)
        one_minus_c = 1.0 - c_val
        p_home = float(one_minus_c * e)
        p_away = float(one_minus_c * (1.0 - e))
        return p_home, p_draw, p_away
