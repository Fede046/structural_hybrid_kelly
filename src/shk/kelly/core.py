"""Funzioni analitiche di base per il criterio di Kelly.

Questo modulo fornisce le formulazioni analitiche pure per il criterio di
Kelly classico, inclusi la frazione ottimale e il tasso di crescita logaritmico
atteso. Entrambe le funzioni accettano valori scalari float.
"""

import math


def kelly_fraction(p: float, b: float) -> float:
    """Calcola la frazione di scommessa ottimale di Kelly per una scommessa binaria.

    La frazione ottimale è definita come:
        f* = (b * p - q) / b
    dove q = 1 - p. Se il vantaggio non è positivo (f* <= 0), viene restituito 0.0,
    a indicare che non deve essere scommesso alcun capitale.

    Parametri
    ---------
    p : float
        Probabilità di vincita, in [0, 1].
    b : float
        Quota decimale netta (b a 1). Deve essere strettamente positiva (b > 0).

    Restituisce
    -----------
    float
        Frazione ottimale di capitale da scommettere, vincolata a [0, 1].
        Restituisce 0.0 se il vantaggio atteso non è positivo.

    Solleva
    -------
    ValueError
        Se p non è compreso in [0, 1] oppure se b <= 0.
    """
    if not (0.0 <= p <= 1.0):
        raise ValueError(f"Probability 'p' must be in [0, 1], got {p}")
    if b <= 0.0:
        raise ValueError(f"Odds 'b' must be strictly positive (b > 0), got {b}")

    q = 1.0 - p
    f_star = (b * p - q) / b

    if f_star <= 0.0:
        return 0.0

    return float(f_star)


def log_growth_rate(f: float, p: float, b: float) -> float:
    """Calcola il tasso di crescita logaritmico atteso per una data frazione di scommessa.

    Il tasso di crescita logaritmico atteso è definito come:
        g(f) = p * ln(1 + b * f) + (1 - p) * ln(1 - f)

    Questa funzione accetta input scalari di tipo float.

    Parametri
    ---------
    f : float
        Frazione di capitale scommessa, in [0, 1).
    p : float
        Probabilità di vincita, in [0, 1].
    b : float
        Quota decimale netta (b a 1). Deve essere strettamente positiva (b > 0).

    Restituisce
    -----------
    float
        Tasso di crescita logaritmico atteso g(f).

    Solleva
    -------
    ValueError
        Se f non è compreso in [0, 1), se p non è compreso in [0, 1], se b <= 0,
        oppure se un argomento di un logaritmo non è positivo (<= 0).
    """
    if not (0.0 <= p <= 1.0):
        raise ValueError(f"Probability 'p' must be in [0, 1], got {p}")
    if b <= 0.0:
        raise ValueError(f"Odds 'b' must be strictly positive (b > 0), got {b}")
    if not (0.0 <= f < 1.0):
        raise ValueError(f"Fraction 'f' must be in [0, 1), got {f}")

    arg_win = 1.0 + b * f
    arg_loss = 1.0 - f

    if arg_win <= 0.0 or arg_loss <= 0.0:
        raise ValueError(
            f"Logarithm arguments must be strictly positive, got 1 + b*f = {arg_win} and 1 - f = {arg_loss}"
        )

    return float(p * math.log(arg_win) + (1.0 - p) * math.log(arg_loss))


def expected_final_wealth(
    f: float, p: float, b: float, T: int, b0: float = 1.0
) -> float:
    """Calcola il valore atteso analitico del capitale finale.

    La media aritmetica analitica del bankroll al tempo T è definita come:
        E[B_T] = b0 * (1 + f * (b * p - (1 - p)))^T

    Questa funzione fornisce la soluzione esatta per scommesse binarie i.i.d.

    Parametri
    ---------
    f : float
        Frazione di capitale scommessa, in [0, 1).
    p : float
        Probabilità di vincita, in [0, 1].
    b : float
        Quota decimale netta (b a 1). Deve essere strettamente positiva (b > 0).
    T : int
        Numero di scommesse/passi temporali (T >= 0).
    b0 : float, opzionale
        Capitale iniziale, strettamente positivo (default pari a 1.0).

    Restituisce
    -----------
    float
        Media aritmetica attesa del capitale finale E[B_T].

    Solleva
    -------
    ValueError
        Se p non è compreso in [0, 1], se b <= 0, se f non è compreso in [0, 1),
        se T < 0 oppure se b0 <= 0.
    """
    if not (0.0 <= p <= 1.0):
        raise ValueError(f"Probability 'p' must be in [0, 1], got {p}")
    if b <= 0.0:
        raise ValueError(f"Odds 'b' must be strictly positive (b > 0), got {b}")
    if not (0.0 <= f < 1.0):
        raise ValueError(f"Fraction 'f' must be in [0, 1), got {f}")
    if T < 0:
        raise ValueError(f"Number of steps 'T' must be non-negative (T >= 0), got {T}")
    if b0 <= 0.0:
        raise ValueError(f"Initial wealth 'b0' must be strictly positive (b0 > 0), got {b0}")

    factor = 1.0 + f * (b * p - (1.0 - p))
    return float(b0 * (factor ** T))

