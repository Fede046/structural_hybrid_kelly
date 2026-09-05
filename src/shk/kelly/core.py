"""Core analytical functions for the Kelly criterion.

This module provides pure analytical formulations for the classical Kelly
criterion, including the optimal fraction and expected logarithmic growth rate.
Both functions accept scalar floats.
"""

import math


def kelly_fraction(p: float, b: float) -> float:
    """Calculate the optimal Kelly betting fraction for a binary bet.

    The optimal fraction is defined as:
        f* = (b * p - q) / b
    where q = 1 - p. If the edge is non-positive (f* <= 0), 0.0 is returned,
    indicating that no capital should be wagered.

    Parameters
    ----------
    p : float
        Probability of winning, in [0, 1].
    b : float
        Net decimal odds (b to 1). Must be strictly positive (b > 0).

    Returns
    -------
    float
        Optimal fraction of wealth to wager, constrained to [0, 1].
        Returns 0.0 if the expected edge is non-positive.

    Raises
    ------
    ValueError
        If p is not in [0, 1] or if b <= 0.
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
    """Calculate the expected logarithmic growth rate for a given betting fraction.

    The expected logarithmic growth rate is defined as:
        g(f) = p * ln(1 + b * f) + (1 - p) * ln(1 - f)

    This function accepts scalar float inputs.

    Parameters
    ----------
    f : float
        Fraction of wealth wagered, in [0, 1).
    p : float
        Probability of winning, in [0, 1].
    b : float
        Net decimal odds (b to 1). Must be strictly positive (b > 0).

    Returns
    -------
    float
        Expected logarithmic growth rate g(f).

    Raises
    ------
    ValueError
        If f is not in [0, 1), if p is not in [0, 1], if b <= 0,
        or if an argument of a logarithm is non-positive (<= 0).
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

