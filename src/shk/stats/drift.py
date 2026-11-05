"""Z-test per giornata sulle serie di log-loss del Modulo 1.

Z della giornata (blocchi contigui di MATCHDAY_SIZE partite) rispetto alla media e alla
deviazione standard del training, soglia calibrata per moving block bootstrap e sua verifica.
"""

from typing import Final

import numpy as np

from shk.stats.calibration import calibrate_threshold, moving_block_indices
from shk.stats.false_rejection import ALPHA, BLOCK_LENGTHS, N_BOOT

# Numero di partite per giornata (blocco contiguo)
MATCHDAY_SIZE: Final[int] = 10

# Seme congelato e parametri per la calibrazione e verifica bootstrap del monitoraggio dei residui
SEED_C5: Final[int] = 20260929
N_VERIFICATION_RESAMPLES: Final[int] = 1000


def compute_matchday_z_scores(
    series: np.ndarray,
    mu: float,
    sigma: float,
    matchday_size: int = MATCHDAY_SIZE,
) -> np.ndarray:
    """Calcola lo Z-test per ciascun blocco contiguo (giornata) di partite.

    Per ciascun blocco g di lunghezza matchday_size (default 10 partite):
        Z_g = (media(log_loss_g) - mu) / (sigma / sqrt(matchday_size))

    Parametri
    ---------
    series : np.ndarray
        Array 1D contenente la sequenza di log-loss (es. 380 partite di una stagione).
    mu : float
        Media di riferimento delle partite di training del fit.
    sigma : float
        Deviazione standard campionaria (ddof=1) del training del fit.
    matchday_size : int, opzionale
        Numero di partite per blocco contiguo (default MATCHDAY_SIZE = 10).

    Restituisce
    -----------
    np.ndarray
        Array 1D di float64 contenente i valori di Z per ciascuna giornata (lunghezza N // matchday_size).

    Solleva
    -------
    TypeError
        Se series non è un np.ndarray numerico, se mu o sigma non sono numeri reali
        (escludendo i booleani), o se matchday_size non è un intero nativo (escludendo bool).
    ValueError
        Se series non è 1D, se la lunghezza non è un multiplo positivo di matchday_size,
        se mu o sigma contengono valori non finiti, se sigma <= 0, o se matchday_size <= 0.
    """
    if isinstance(matchday_size, bool) or not isinstance(matchday_size, (int, np.integer)):
        raise TypeError(f"matchday_size must be an integer, got {type(matchday_size).__name__}")
    if matchday_size <= 0:
        raise ValueError(f"matchday_size must be positive, got {matchday_size}")

    if not isinstance(series, np.ndarray):
        raise TypeError(f"series must be a np.ndarray, got {type(series).__name__}")
    if series.dtype == bool or not np.issubdtype(series.dtype, np.number):
        raise TypeError(f"series must have a numeric dtype, got {series.dtype}")
    if series.ndim != 1:
        raise ValueError(f"series must be 1D, got ndim={series.ndim}")
    if len(series) == 0:
        raise ValueError("series must not be empty")
    if len(series) % matchday_size != 0:
        raise ValueError(
            f"series length ({len(series)}) must be a positive multiple of matchday_size ({matchday_size})"
        )
    if not np.all(np.isfinite(series)):
        raise ValueError("series contains non-finite values (NaN or Inf)")

    if isinstance(mu, bool) or not isinstance(mu, (int, float, np.floating, np.integer)):
        raise TypeError(f"mu must be a real number, got {type(mu).__name__}")
    if not np.isfinite(mu):
        raise ValueError(f"mu must be finite, got {mu}")

    if isinstance(sigma, bool) or not isinstance(sigma, (int, float, np.floating, np.integer)):
        raise TypeError(f"sigma must be a real number, got {type(sigma).__name__}")
    if not np.isfinite(sigma):
        raise ValueError(f"sigma must be finite, got {sigma}")
    if sigma <= 0.0:
        raise ValueError(f"sigma must be strictly positive, got {sigma}")

    mu_val = float(mu)
    sigma_val = float(sigma)
    blocks = series.reshape(-1, matchday_size)
    block_means = blocks.mean(axis=1)
    denom = sigma_val / np.sqrt(matchday_size)
    z_scores = (block_means - mu_val) / denom

    return np.asarray(z_scores, dtype=np.float64)


def compute_resampled_matchday_abs_z(
    resampled_data: np.ndarray,
    mu: float,
    sigma: float,
    matchday_size: int = MATCHDAY_SIZE,
) -> float | np.ndarray:
    """Calcola |Z| delle prime matchday_size posizioni di serie ricampionate.

    Supporta sia un singolo ricampionamento 1D di forma (n,) che un batch 2D di forma
    (B, n) per la valutazione vettorizzata in calibrate_threshold.
    Z = (|media(prime matchday_size) - mu|) / (sigma / sqrt(matchday_size)).

    Parametri
    ---------
    resampled_data : np.ndarray
        Array 1D (n,) o 2D (B, n) di log-loss ricampionata.
    mu : float
        Media della serie originale di training del fit.
    sigma : float
        Deviazione standard campionaria (ddof=1) della serie originale di training del fit.
    matchday_size : int, opzionale
        Numero di partite per giornata (default MATCHDAY_SIZE = 10).

    Restituisce
    -----------
    float | np.ndarray
        Scalare float se resampled_data è 1D; array 1D float64 di forma (B,) se 2D.

    Solleva
    -------
    TypeError
        Se resampled_data non è un np.ndarray numerico reale, se mu o sigma non sono numeri reali,
        o se matchday_size non è un intero (escludendo bool).
    ValueError
        Se resampled_data ha ndim diverso da 1 o 2, se la dimensione temporale è inferiore a
        matchday_size, se contiene valori non finiti, se mu non è finito, se sigma non è finito
        o <= 0, o se matchday_size <= 0.
    """
    if isinstance(matchday_size, bool) or not isinstance(matchday_size, (int, np.integer)):
        raise TypeError(f"matchday_size must be an integer, got {type(matchday_size).__name__}")
    if matchday_size <= 0:
        raise ValueError(f"matchday_size must be strictly positive, got {matchday_size}")

    if not isinstance(resampled_data, np.ndarray):
        raise TypeError(f"resampled_data must be a np.ndarray, got {type(resampled_data).__name__}")
    if resampled_data.dtype == bool or not np.issubdtype(resampled_data.dtype, np.number) or np.issubdtype(resampled_data.dtype, np.complexfloating):
        raise TypeError(f"resampled_data must have a real numeric dtype, got {resampled_data.dtype}")
    if resampled_data.ndim not in (1, 2):
        raise ValueError(f"resampled_data must be 1D or 2D, got ndim={resampled_data.ndim}")
    if not np.all(np.isfinite(resampled_data)):
        raise ValueError("resampled_data contains non-finite values (NaN or Inf)")

    if isinstance(mu, bool) or not isinstance(mu, (int, float, np.floating, np.integer)):
        raise TypeError(f"mu must be a real number, got {type(mu).__name__}")
    if not np.isfinite(mu):
        raise ValueError(f"mu must be finite, got {mu}")

    if isinstance(sigma, bool) or not isinstance(sigma, (int, float, np.floating, np.integer)):
        raise TypeError(f"sigma must be a real number, got {type(sigma).__name__}")
    if not np.isfinite(sigma):
        raise ValueError(f"sigma must be finite, got {sigma}")
    if sigma <= 0.0:
        raise ValueError(f"sigma must be strictly positive, got {sigma}")

    mu_val = float(mu)
    sigma_val = float(sigma)
    m_size = int(matchday_size)
    denom = sigma_val / np.sqrt(m_size)

    if resampled_data.ndim == 1:
        if len(resampled_data) < m_size:
            raise ValueError(
                f"resampled_data length ({len(resampled_data)}) is smaller than matchday_size ({m_size})"
            )
        mean_val = float(np.mean(resampled_data[:m_size]))
        z_val = (mean_val - mu_val) / denom
        return float(abs(z_val))
    else:
        if resampled_data.shape[1] < m_size:
            raise ValueError(
                f"resampled_data time dimension ({resampled_data.shape[1]}) is smaller than matchday_size ({m_size})"
            )
        means = np.mean(resampled_data[:, :m_size], axis=1)
        z_scores = (means - mu_val) / denom
        return np.asarray(np.abs(z_scores), dtype=np.float64)


def calibrate_matchday_z_threshold(
    training_log_loss: np.ndarray,
    mu: float,
    sigma: float,
    block_length: int,
    rng: np.random.Generator,
    n_boot: int = N_BOOT,
    alpha: float = ALPHA,
    matchday_size: int = MATCHDAY_SIZE,
) -> float:
    """Calcola la soglia critica calibrata per moving block bootstrap della log-loss di training.

    Parametri
    ---------
    training_log_loss : np.ndarray
        Serie 1D di log-loss delle partite di training del fit.
    mu : float
        Media della serie originale di training del fit.
    sigma : float
        Deviazione standard campionaria (ddof=1) della serie originale di training del fit.
    block_length : int
        Lunghezza del blocco per il moving block bootstrap (L).
    rng : np.random.Generator
        Generatore di numeri casuali NumPy.
    n_boot : int, opzionale
        Numero di replicazioni bootstrap (default N_BOOT = 999).
    alpha : float, opzionale
        Livello di significatività nominale (default ALPHA = 0.05).
    matchday_size : int, opzionale
        Numero di partite per giornata (default MATCHDAY_SIZE = 10).

    Restituisce
    -----------
    float
        Soglia critica calibrata per |Z|.

    Solleva
    -------
    TypeError
        Se rng non è un'istanza di np.random.Generator o se i tipi non sono conformi.
    ValueError
        Se i valori non sono conformi.
    """
    if not isinstance(rng, np.random.Generator):
        raise TypeError(f"rng must be an instance of np.random.Generator, got {type(rng).__name__}")

    stat_fn = lambda d: compute_resampled_matchday_abs_z(
        d, mu=mu, sigma=sigma, matchday_size=matchday_size
    )
    return calibrate_threshold(
        data=training_log_loss,
        statistic=stat_fn,
        block_length=block_length,
        n_boot=n_boot,
        alpha=alpha,
        rng=rng,
        vectorized=True,
    )


def verify_matchday_z_thresholds(
    training_log_loss: np.ndarray,
    mu: float,
    sigma: float,
    block_length: int,
    calibrated_threshold: float,
    nominal_threshold: float,
    rng: np.random.Generator,
    n_resamples: int = N_VERIFICATION_RESAMPLES,
    matchday_size: int = MATCHDAY_SIZE,
) -> tuple[float, float]:
    """Calcola i tassi di superamento su ricampionamenti indipendenti per le soglie calibrata e nominale.

    Parametri
    ---------
    training_log_loss : np.ndarray
        Serie 1D di log-loss delle partite di training del fit.
    mu : float
        Media della serie originale di training del fit.
    sigma : float
        Deviazione standard campionaria (ddof=1) della serie originale di training del fit.
    block_length : int
        Lunghezza del blocco per il moving block bootstrap (L).
    calibrated_threshold : float
        Soglia critica calibrata ottenuta con calibrate_matchday_z_threshold.
    nominal_threshold : float
        Soglia critica nominale gaussiana (es. norm.ppf(1 - alpha/2)).
    rng : np.random.Generator
        Generatore di numeri casuali NumPy dedicato alla verifica.
    n_resamples : int, opzionale
        Numero di replicazioni indipendenti di verifica (default N_VERIFICATION_RESAMPLES = 1000).
    matchday_size : int, opzionale
        Numero di partite per giornata (default MATCHDAY_SIZE = 10).

    Restituisce
    -----------
    tuple[float, float]
        Tupla (tasso_calibrato, tasso_nominale), cioè le quote di ricampionamenti in cui
        |Z| supera strettamente la rispettiva soglia.

    Solleva
    -------
    TypeError
        Se rng non è np.random.Generator o se i tipi non sono conformi.
    ValueError
        Se le soglie o i parametri non sono validi.
    """
    if not isinstance(rng, np.random.Generator):
        raise TypeError(f"rng must be an instance of np.random.Generator, got {type(rng).__name__}")
    if isinstance(calibrated_threshold, bool) or not isinstance(
        calibrated_threshold, (int, float, np.floating, np.integer)
    ):
        raise TypeError(f"calibrated_threshold must be a real number, got {type(calibrated_threshold).__name__}")
    if not np.isfinite(calibrated_threshold) or calibrated_threshold < 0:
        raise ValueError(f"calibrated_threshold must be non-negative and finite, got {calibrated_threshold}")

    if isinstance(nominal_threshold, bool) or not isinstance(
        nominal_threshold, (int, float, np.floating, np.integer)
    ):
        raise TypeError(f"nominal_threshold must be a real number, got {type(nominal_threshold).__name__}")
    if not np.isfinite(nominal_threshold) or nominal_threshold < 0:
        raise ValueError(f"nominal_threshold must be non-negative and finite, got {nominal_threshold}")

    n_res = int(n_resamples)
    if isinstance(n_resamples, bool) or not isinstance(n_resamples, (int, np.integer)):
        raise TypeError(f"n_resamples must be an integer, got {type(n_resamples).__name__}")
    if n_res < 1:
        raise ValueError(f"n_resamples must be at least 1, got {n_res}")

    indices = moving_block_indices(
        n=len(training_log_loss),
        block_length=block_length,
        n_boot=n_res,
        rng=rng,
    )
    boot_data = training_log_loss[indices]
    abs_z_scores = compute_resampled_matchday_abs_z(
        boot_data, mu=mu, sigma=sigma, matchday_size=matchday_size
    )

    calib_rate = float(np.mean(abs_z_scores > float(calibrated_threshold)))
    nominal_rate = float(np.mean(abs_z_scores > float(nominal_threshold)))

    return calib_rate, nominal_rate


def spawn_c5_generators(
    seed: int = SEED_C5,
    n_fits: int = 3,
) -> tuple[tuple[tuple[np.random.Generator, np.random.Generator], ...], ...]:
    """Genera i generatori casuali NumPy annidati secondo lo schema di seed del monitoraggio dei residui.

    Struttura:
    SeedSequence(seed).spawn(n_fits) -> per ciascun fit .spawn(len(BLOCK_LENGTHS))
    -> per ciascuna L .spawn(2) -> (calib_rng, verif_rng).

    Parametri
    ---------
    seed : int, opzionale
        Seme master per la sequenza (default SEED_C5 = 20260929).
    n_fits : int, opzionale
        Numero di fit da istanziare (default 3 per 2000-01, 2010-11, 2020-21).

    Restituisce
    -----------
    tuple[tuple[tuple[np.random.Generator, np.random.Generator], ...], ...]
        Tuple annidate [fit_idx][l_idx] -> (calib_rng, verif_rng).

    Solleva
    -------
    TypeError
        Se seed o n_fits non sono interi (escludendo bool).
    ValueError
        Se n_fits < 1.
    """
    if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)):
        raise TypeError(f"seed must be an integer, got {type(seed).__name__}")
    if isinstance(n_fits, bool) or not isinstance(n_fits, (int, np.integer)):
        raise TypeError(f"n_fits must be an integer, got {type(n_fits).__name__}")
    if n_fits < 1:
        raise ValueError(f"n_fits must be at least 1, got {n_fits}")

    seed_seq = np.random.SeedSequence(int(seed))
    fit_seeds = seed_seq.spawn(int(n_fits))

    fits_res = []
    for f_seed in fit_seeds:
        l_seeds = f_seed.spawn(len(BLOCK_LENGTHS))
        l_res = []
        for l_seed in l_seeds:
            c_seed, v_seed = l_seed.spawn(2)
            l_res.append((np.random.default_rng(c_seed), np.random.default_rng(v_seed)))
        fits_res.append(tuple(l_res))

    return tuple(fits_res)
