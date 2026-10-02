"""Modulo per la regola di staking del criterio di Kelly con stima e frazionamento."""

import math
from typing import Final, NamedTuple
import numpy as np


def kelly_staking(
    p_hat: float | np.ndarray, b: float, lam: float = 1.0
) -> float | np.ndarray:
    """Calcola la frazione di scommessa secondo la regola di Kelly con stima e moltiplicatore.

    Data una probabilità stimata p_hat (scalare o array NumPy), calcola la frazione
    ottimale teorica di Kelly troncata a zero per vantaggi non positivi, e la scala
    tramite il moltiplicatore lam (frazione di Kelly lambda):
        q = 1 - p_hat
        f_raw = (b * p_hat - q) / b
        f_hat = max(0, f_raw)
        f = lam * f_hat

    La regola non limita la frazione al di sotto di 1. Con p_hat = 1.0 e b > 0,
    la frazione vale lam * 1. Eventuali frazioni >= 1 vengono deliberatamente
    restituite e saranno eventualmente rifiutate a valle da simulate_growth con ValueError.

    Parametri
    ---------
    p_hat : float | np.ndarray
        Stima di probabilità di vincita in [0, 1], scalare o array NumPy.
    b : float
        Quota decimale netta (b a 1), strettamente positiva (b > 0).
    lam : float, opzionale
        Moltiplicatore di Kelly non negativo (lam >= 0), default pari a 1.0.

    Restituisce
    -----------
    float | np.ndarray
        Frazione di capitale da scommettere. Se p_hat è uno scalare Python, uno scalare
        NumPy o un array 0-dimensionale, restituisce un float Python. Se p_hat ha almeno
        una dimensione (1D o 2D), restituisce un np.ndarray con la stessa forma di p_hat.

    Solleva
    -------
    ValueError
        Se b <= 0 o non finito, se lam < 0 o non finito, oppure se p_hat contiene
        valori non finiti (NaN o Inf) o non compresi in [0, 1].
    """
    if not math.isfinite(b) or b <= 0.0:
        raise ValueError(f"Odds 'b' must be strictly positive (b > 0), got {b}")

    if not math.isfinite(lam):
        raise ValueError(f"Multiplier 'lam' must be finite, got {lam}")
    if lam < 0.0:
        raise ValueError(f"Multiplier 'lam' must be non-negative (lam >= 0), got {lam}")

    p_arr = np.asarray(p_hat, dtype=float)

    if not np.all(np.isfinite(p_arr)):
        raise ValueError("All elements of 'p_hat' must be finite (no NaN or Inf allowed)")
    if np.any(p_arr < 0.0) or np.any(p_arr > 1.0):
        raise ValueError(
            f"All elements of 'p_hat' must be in [0, 1], got min={np.min(p_arr)}, max={np.max(p_arr)}"
        )

    # Stesso ordine di operazioni di core.py (righe 42-43) per concordanza bit-a-bit
    q = 1.0 - p_arr
    f_raw = (b * p_arr - q) / b
    f_hat = np.maximum(0.0, f_raw)
    f = lam * f_hat

    if np.ndim(p_hat) == 0:
        return float(f)

    return f


class StakingMoments(NamedTuple):
    """Momenti campionari e statistiche descrittive per il moltiplicatore c = f_hat / f_star.

    Campi
    -----
    mean_c : float
        Valore atteso empirico E[c].
    mean_c2 : float
        Momento secondo empirico E[c^2].
    var_c : float
        Varianza empirica Var(c) = E[c^2] - (E[c])^2.
    fraction_zero : float
        Quota pooled di scommesse in cui la frazione f_hat è pari a 0.0.
    """

    mean_c: float
    mean_c2: float
    var_c: float
    fraction_zero: float


def staking_moments(f_hat: np.ndarray, f_star: float) -> StakingMoments:
    """Calcola i momenti empirici di c = f_hat / f_star e la quota di puntate nulle.

    Tutte le stime sono calcolate in forma pooled sull'insieme di tutte le scommesse
    presenti nell'array f_hat.

    Parametri
    ---------
    f_hat : np.ndarray
        Array (1D o 2D) contenente le frazioni di scommessa stimate.
    f_star : float
        Frazione ottimale teorica di Kelly (deve essere strettamente positiva, f_star > 0).

    Restituisce
    -----------
    StakingMoments
        NamedTuple contenente (mean_c, mean_c2, var_c, fraction_zero).

    Solleva
    -------
    ValueError
        Se f_star <= 0 o non finito, oppure se f_hat contiene valori non finiti o negativi.
    """
    if not math.isfinite(f_star) or f_star <= 0.0:
        raise ValueError(f"Optimal fraction 'f_star' must be strictly positive (f_star > 0), got {f_star}")

    f_arr = np.asarray(f_hat, dtype=float)
    if not np.all(np.isfinite(f_arr)):
        raise ValueError("All elements of 'f_hat' must be finite (no NaN or Inf allowed)")
    if np.any(f_arr < 0.0):
        raise ValueError(f"Elements of 'f_hat' must be non-negative, got min={np.min(f_arr)}")

    c = f_arr / f_star
    mean_c = float(np.mean(c))
    mean_c2 = float(np.mean(c ** 2))
    var_c = float(np.var(c))
    fraction_zero = float(np.mean(f_arr == 0.0))

    return StakingMoments(
        mean_c=mean_c,
        mean_c2=mean_c2,
        var_c=var_c,
        fraction_zero=fraction_zero,
    )


def plugin_staking(
    p_hat: float | np.ndarray, b: float, sigma_p: float
) -> float | np.ndarray:
    """Calcola la frazione di scommessa secondo la regola di Kelly plug-in per scommessa.

    Per ciascuna scommessa, calcola il vantaggio atteso stimato EV_hat = p_hat * o - 1
    (con quota lorda o = b + 1). Se EV_hat <= 0, la frazione è pari a 0.0 esatto.
    Se EV_hat > 0, calcola il moltiplicatore adattivo locale:
        lambda_t = 1 / (1 + (o * sigma_p / EV_hat)^2)
    e restituisce lambda_t * kelly_staking(p_hat, b, lam=1.0).

    Parametri
    ---------
    p_hat : float | np.ndarray
        Stima di probabilità di vincita in [0, 1], scalare o array NumPy.
    b : float
        Quota decimale netta (b a 1), strettamente positiva (b > 0).
    sigma_p : float
        Deviazione standard del rumore di stima, non negativa (sigma_p >= 0).

    Restituisce
    -----------
    float | np.ndarray
        Frazione di capitale da scommettere, con la stessa forma di p_hat.

    Solleva
    -------
    ValueError
        Se b <= 0 o non finito, se sigma_p < 0 o non finito, oppure se p_hat
        contiene valori non finiti o non compresi in [0, 1].
    """
    if not math.isfinite(sigma_p):
        raise ValueError(f"Noise parameter 'sigma_p' must be finite, got {sigma_p}")
    if sigma_p < 0.0:
        raise ValueError(f"Noise parameter 'sigma_p' must be non-negative (sigma_p >= 0), got {sigma_p}")

    # Validazione di b e p_hat ed estrazione di f_base tramite kelly_staking (Correzione A)
    f_base = kelly_staking(p_hat, b, lam=1.0)

    # Se sigma_p == 0, lambda_t = 1 ovunque, quindi la frazione coincide con f_base
    if sigma_p == 0.0:
        return f_base

    o = b + 1.0

    # Gestione scalare / array 0-dimensionale
    if np.ndim(p_hat) == 0:
        if f_base == 0.0:
            return 0.0
        ev_hat = float(p_hat) * o - 1.0
        if ev_hat <= 0.0:
            return 0.0
        ratio = (o * sigma_p) / ev_hat
        lam_t = 1.0 / (1.0 + ratio * ratio)
        return float(lam_t * f_base)

    # Gestione array NumPy (1D, 2D) con maschera protettiva contro divisione per zero (Correzione B)
    p_arr = np.asarray(p_hat, dtype=float)
    ev_hat = p_arr * o - 1.0
    positive_mask = ev_hat > 0.0

    result = np.zeros_like(p_arr, dtype=float)
    if np.any(positive_mask):
        ratio = np.divide(
            o * sigma_p,
            ev_hat,
            out=np.zeros_like(ev_hat, dtype=float),
            where=positive_mask,
        )
        lam_t = np.divide(
            1.0,
            1.0 + ratio * ratio,
            out=np.zeros_like(ratio, dtype=float),
            where=positive_mask,
        )
        result[positive_mask] = lam_t[positive_mask] * f_base[positive_mask]

    return result


# Costanti di riferimento per la regola della Baseline D (Task 31 / US-C5.3)
BASE_LAMBDA: Final[float] = 0.25
KAPPA_GRID: Final[tuple[float, ...]] = (0.0, 0.25, 0.5, 0.75, 1.0)
KAPPA_ADWIN: Final[float] = 1.0
KAPPA_PAGE_HINKLEY: Final[float] = 1.0

OUTCOME_LABELS: Final[tuple[str, ...]] = ("H", "D", "A")


class BaselineDBets(NamedTuple):
    """Scommesse selezionate e frazioni di capitale per le partite di una stagione.

    Attributi
    ---------
    outcomes : np.ndarray
        Array 1D contenente l'esito considerato ('H', 'D', 'A') per ciascuna partita.
    odds : np.ndarray
        Array 1D float64 contenente la quota decimale lorda dell'esito considerato.
    fractions : np.ndarray
        Array 1D float64 contenente la frazione di Kelly da scommettere (0.0 se edge non positivo).
    """

    outcomes: np.ndarray
    odds: np.ndarray
    fractions: np.ndarray


def compute_adaptive_lambda(
    match_dates: np.ndarray,
    alarm_dates: np.ndarray,
    kappa: float,
    base_lambda: float = BASE_LAMBDA,
) -> np.ndarray:
    """Calcola il moltiplicatore lambda_j per ciascuna partita della stagione.

    Per ciascuna partita j alla data D_j:
        lambda_j = base_lambda * (kappa ** n_alarms_anteriori)
    dove n_alarms_anteriori è il numero di allarmi con data strettamente anteriore a D_j.
    Un allarme verificatosi alla data d modifica lambda solo a partire dalle partite con Date > d.

    Parametri
    ---------
    match_dates : np.ndarray
        Array 1D datetime64 con la data di ciascuna partita.
    alarm_dates : np.ndarray
        Array 1D datetime64 con la data di ciascun allarme rilevato nella stagione.
    kappa : float
        Fattore moltiplicativo di riduzione del capitale per allarme (kappa >= 0).
    base_lambda : float, opzionale
        Frazione di Kelly iniziale a inizio stagione (default BASE_LAMBDA = 0.25).

    Restituisce
    -----------
    np.ndarray
        Array 1D float64 di moltiplicatori lambda_j di lunghezza pari a len(match_dates).

    Solleva
    -------
    TypeError
        Se match_dates o alarm_dates non sono np.ndarray con dtype datetime64,
        oppure se kappa o base_lambda non sono float.
    ValueError
        Se match_dates o alarm_dates non sono 1D, o se kappa o base_lambda sono non finiti o negativi.
    """
    if not isinstance(match_dates, np.ndarray):
        raise TypeError(f"match_dates must be a numpy.ndarray, got {type(match_dates).__name__}")
    if not np.issubdtype(match_dates.dtype, np.datetime64):
        raise TypeError(f"match_dates must have datetime64 dtype, got {match_dates.dtype}")

    if not isinstance(alarm_dates, np.ndarray):
        raise TypeError(f"alarm_dates must be a numpy.ndarray, got {type(alarm_dates).__name__}")
    if not np.issubdtype(alarm_dates.dtype, np.datetime64):
        raise TypeError(f"alarm_dates must have datetime64 dtype, got {alarm_dates.dtype}")

    if isinstance(kappa, bool) or not isinstance(kappa, (float, np.floating)):
        raise TypeError(f"kappa must be a float, got {type(kappa).__name__}")
    if not math.isfinite(kappa) or kappa < 0.0:
        raise ValueError(f"kappa must be finite and non-negative, got {kappa}")

    if isinstance(base_lambda, bool) or not isinstance(base_lambda, (float, np.floating)):
        raise TypeError(f"base_lambda must be a float, got {type(base_lambda).__name__}")
    if not math.isfinite(base_lambda) or base_lambda < 0.0:
        raise ValueError(f"base_lambda must be finite and non-negative, got {base_lambda}")

    if match_dates.ndim != 1 or alarm_dates.ndim != 1:
        raise ValueError("match_dates and alarm_dates must be 1-dimensional arrays")

    n_matches = len(match_dates)
    if n_matches == 0:
        return np.empty((0,), dtype=np.float64)

    lambdas = np.empty(n_matches, dtype=np.float64)
    kappa_val = float(kappa)
    base_val = float(base_lambda)

    for j in range(n_matches):
        d_j = match_dates[j]
        k_j = int(np.sum(alarm_dates < d_j))
        if kappa_val == 0.0:
            multiplier = 1.0 if k_j == 0 else 0.0
        else:
            multiplier = kappa_val ** k_j
        lambdas[j] = base_val * multiplier

    return lambdas


def select_baseline_d_bets(
    probs: np.ndarray,
    odds: np.ndarray,
    lambdas: np.ndarray,
) -> BaselineDBets:
    """Seleziona l'esito considerato e calcola la frazione di Kelly per ciascuna partita.

    Per ciascuna partita:
    - Calcola l'edge atteso: EV = p_hat * o - 1 per gli esiti Home, Draw, Away.
    - Seleziona l'esito con EV massimo (argmax). A parità di EV vince il primo
      nell'ordine H, D, A.
    - Se il massimo EV > 0, calcola la frazione chiamando kelly_staking(p_hat, o - 1, lam=lambda_j).
    - Se il massimo EV <= 0, la frazione è pari a 0.0 esatto.

    Il detector dice quando, non quanto né di che tipo; κ è un iperparametro fisso, uguale per ogni allarme.

    Parametri
    ---------
    probs : np.ndarray
        Array 2D di probabilità stimate di forma (N, 3) con valori in [0, 1].
    odds : np.ndarray
        Array 2D di quote decimali lorde di forma (N, 3) con valori strettamente > 1.0.
    lambdas : np.ndarray
        Array 1D di moltiplicatori di Kelly lambda di forma (N,) con valori non negativi.

    Restituisce
    -----------
    BaselineDBets
        NamedTuple contenente gli array 1D (outcomes, odds, fractions).

    Solleva
    -------
    TypeError
        Se probs, odds o lambdas non sono np.ndarray, oppure se hanno dtype errato.
    ValueError
        Se le forme non corrispondono (probs e odds (N, 3), lambdas (N,)), se le probabilità
        non sono in [0, 1], se le quote sono <= 1.0 o non finite, o se lambdas contiene valori negativi.
    """
    if not isinstance(probs, np.ndarray):
        raise TypeError(f"probs must be a numpy.ndarray, got {type(probs).__name__}")
    if not np.issubdtype(probs.dtype, np.floating):
        raise TypeError(f"probs must have floating dtype, got {probs.dtype}")

    if not isinstance(odds, np.ndarray):
        raise TypeError(f"odds must be a numpy.ndarray, got {type(odds).__name__}")
    if not np.issubdtype(odds.dtype, np.floating):
        raise TypeError(f"odds must have floating dtype, got {odds.dtype}")

    if not isinstance(lambdas, np.ndarray):
        raise TypeError(f"lambdas must be a numpy.ndarray, got {type(lambdas).__name__}")
    if not np.issubdtype(lambdas.dtype, np.floating):
        raise TypeError(f"lambdas must have floating dtype, got {lambdas.dtype}")

    if probs.ndim != 2 or probs.shape[1] != 3:
        raise ValueError(f"probs must have 2D shape (N, 3), got {probs.shape}")
    if odds.ndim != 2 or odds.shape != probs.shape:
        raise ValueError(f"odds must have shape {probs.shape}, got {odds.shape}")
    if lambdas.ndim != 1 or len(lambdas) != probs.shape[0]:
        raise ValueError(f"lambdas must have 1D shape ({probs.shape[0]},), got {lambdas.shape}")

    if not np.all(np.isfinite(probs)) or np.any(probs < 0.0) or np.any(probs > 1.0):
        raise ValueError("All probabilities in probs must be finite and in [0, 1]")
    if not np.all(np.isfinite(odds)) or np.any(odds <= 1.0):
        raise ValueError("All odds must be finite and strictly greater than 1.0")
    if not np.all(np.isfinite(lambdas)) or np.any(lambdas < 0.0):
        raise ValueError("All multipliers in lambdas must be finite and non-negative")

    n_matches = probs.shape[0]
    outcomes = np.empty(n_matches, dtype=object)
    selected_odds = np.empty(n_matches, dtype=np.float64)
    fractions = np.empty(n_matches, dtype=np.float64)

    for j in range(n_matches):
        p_row = probs[j]
        o_row = odds[j]
        ev_row = p_row * o_row - 1.0
        best_idx = int(np.argmax(ev_row))
        outcomes[j] = OUTCOME_LABELS[best_idx]
        best_o = float(o_row[best_idx])
        selected_odds[j] = best_o

        if ev_row[best_idx] > 0.0:
            best_p = float(p_row[best_idx])
            b = best_o - 1.0
            lam_j = float(lambdas[j])
            f_val = kelly_staking(best_p, b, lam=lam_j)
            fractions[j] = float(f_val)
        else:
            fractions[j] = 0.0

    return BaselineDBets(
        outcomes=outcomes,
        odds=selected_odds,
        fractions=fractions,
    )


