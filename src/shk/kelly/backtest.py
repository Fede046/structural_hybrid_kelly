"""Modulo per il motore di backtest su quote reali del criterio di Kelly."""

import math
from typing import NamedTuple
import numpy as np


class BacktestResult(NamedTuple):
    """Risultato del backtest di una stagione su quote reali.

    Attributi
    ---------
    dates : np.ndarray
        Array 1D datetime64 contenente le date distinte della stagione in ordine cronologico.
    log_wealth : np.ndarray
        Array 1D float64 contenente la log-ricchezza cumulativa all'inizio della stagione (0.0)
        e dopo ciascuna data distinta. Ha lunghezza pari a len(dates) + 1.
    """

    dates: np.ndarray
    log_wealth: np.ndarray


def backtest_log_wealth(
    dates: np.ndarray,
    fractions: np.ndarray,
    odds: np.ndarray,
    won: np.ndarray,
) -> BacktestResult:
    """Calcola la traiettoria di log-ricchezza dopo ciascuna data distinta della stagione.

    Per ciascuna data distinta d, tutte le scommesse pianificate per quella data vengono
    decise sul bankroll di inizio data e regolate simultaneamente:
        r_i = o_i - 1  se l'esito è vinto, -1  se perso
        B_t = B_{t-1} * (1 + sum_{i in d} f_i * r_i)
        L_t = L_{t-1} + ln(1 + sum_{i in d} f_i * r_i)
    con log-ricchezza iniziale L_0 = 0.0 (corrispondente a bankroll unitario B_0 = 1.0).

    Parametri
    ---------
    dates : np.ndarray
        Array 1D con dtype datetime64 contenente la data di ciascuna partita della stagione.
        Deve essere ordinato in modo non decrescente.
    fractions : np.ndarray
        Array 1D con dtype float64 contenente la frazione di capitale scommessa per partita.
        Ciascun valore deve appartenere all'intervallo [0, 1). Per ciascuna data distinta,
        la somma delle frazioni deve essere strettamente inferiore a 1.
    odds : np.ndarray
        Array 1D con dtype float64 contenente la quota decimale lorda dell'esito considerato
        per ciascuna partita. Tutti i valori devono essere finiti e strettamente superiori a 1.0.
    won : np.ndarray
        Array 1D con dtype bool indicante se l'esito considerato è risultato vincente (True)
        o perdente (False).

    Restituisce
    -----------
    BacktestResult
        NamedTuple contenente l'array 1D datetime64 delle date distinte e l'array 1D float64
        della log-ricchezza cumulativa dopo ciascuna data (di lunghezza len(dates) + 1).

    Solleva
    -------
    TypeError
        Se uno qualsiasi degli argomenti non è un np.ndarray, oppure se ha un dtype diverso da
        quello prescritto (datetime64 per dates, float64 per fractions e odds, bool per won).
    ValueError
        Se gli array non sono unidimensionali o hanno lunghezze diverse; se dates non è ordinato
        in modo non decrescente; se odds contiene valori non finiti o <= 1.0; se fractions
        contiene valori non finiti, negativi o >= 1.0; oppure se per una qualunque data la somma
        delle frazioni risulta >= 1.0.
    """
    if not isinstance(dates, np.ndarray):
        raise TypeError(f"dates must be a numpy.ndarray, got {type(dates).__name__}")
    if not np.issubdtype(dates.dtype, np.datetime64):
        raise TypeError(f"dates must have datetime64 dtype, got {dates.dtype}")

    if not isinstance(fractions, np.ndarray):
        raise TypeError(f"fractions must be a numpy.ndarray, got {type(fractions).__name__}")
    if fractions.dtype != np.float64:
        raise TypeError(f"fractions must have float64 dtype, got {fractions.dtype}")

    if not isinstance(odds, np.ndarray):
        raise TypeError(f"odds must be a numpy.ndarray, got {type(odds).__name__}")
    if odds.dtype != np.float64:
        raise TypeError(f"odds must have float64 dtype, got {odds.dtype}")

    if not isinstance(won, np.ndarray):
        raise TypeError(f"won must be a numpy.ndarray, got {type(won).__name__}")
    if won.dtype != np.bool_:
        raise TypeError(f"won must have bool dtype, got {won.dtype}")

    if dates.ndim != 1 or fractions.ndim != 1 or odds.ndim != 1 or won.ndim != 1:
        raise ValueError("All input arrays must be 1-dimensional")

    n_matches = len(dates)
    if not (len(fractions) == n_matches and len(odds) == n_matches and len(won) == n_matches):
        raise ValueError(
            f"Input arrays must have identical lengths: dates={n_matches}, "
            f"fractions={len(fractions)}, odds={len(odds)}, won={len(won)}"
        )

    if n_matches > 1 and np.any(dates[1:] < dates[:-1]):
        raise ValueError("dates array must be in non-decreasing chronological order")

    if not np.all(np.isfinite(odds)) or np.any(odds <= 1.0):
        raise ValueError("All odds must be finite and strictly greater than 1.0")

    if not np.all(np.isfinite(fractions)) or np.any(fractions < 0.0) or np.any(fractions >= 1.0):
        raise ValueError("All fractions must be finite and in [0, 1)")

    if n_matches == 0:
        return BacktestResult(
            dates=np.empty((0,), dtype=dates.dtype),
            log_wealth=np.array([0.0], dtype=np.float64),
        )

    # Identificazione delle date distinte in ordine cronologico
    unique_dates, split_indices = np.unique(dates, return_index=True)
    sort_order = np.argsort(split_indices)
    unique_dates = unique_dates[sort_order]

    log_wealth_list = [0.0]
    current_log_wealth = 0.0

    for d in unique_dates:
        mask = (dates == d)
        d_fracs = fractions[mask]
        sum_fracs = float(np.sum(d_fracs))
        if sum_fracs >= 1.0:
            raise ValueError(
                f"Sum of fractions on date {d} is >= 1.0 ({sum_fracs})"
            )

        d_odds = odds[mask]
        d_won = won[mask]
        r_i = np.where(d_won, d_odds - 1.0, -1.0)
        net_return = float(np.sum(d_fracs * r_i))
        current_log_wealth += math.log(1.0 + net_return)
        log_wealth_list.append(current_log_wealth)

    return BacktestResult(
        dates=unique_dates,
        log_wealth=np.array(log_wealth_list, dtype=np.float64),
    )
