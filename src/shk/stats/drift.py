"""Modulo per la drift detection tramite ADWIN e Page-Hinkley (US-C5.1 / Task 27).

Fornisce la funzione run_drift_detector per eseguire i detector ADWIN e Page-Hinkley
importati da river su serie 1D, la regola pura di selezione dei parametri e le
funzioni di taratura sulle serie di training di log-loss del Modulo 1.
"""

from collections.abc import Mapping
from typing import Any, Final

import numpy as np
import pandas as pd
from river.drift import ADWIN, PageHinkley

from shk.stats.calibration import calibrate_threshold, moving_block_indices
from shk.stats.false_rejection import ALPHA, BLOCK_LENGTHS, N_BOOT

# Target di allarmi per stagione (38 partite x alpha 0.05)
TARGET_ALARMS_PER_SEASON: Final[float] = 1.9

# Numero di partite per giornata (blocco contiguo)
MATCHDAY_SIZE: Final[int] = 10

# Seme congelato e parametri per la calibrazione e verifica bootstrap C5 (Task 30)
SEED_C5: Final[int] = 20260929
N_VERIFICATION_RESAMPLES: Final[int] = 1000

# ---------------------------------------------------------------------------
# Griglia e parametri di default congelati da river 0.26.1
# ---------------------------------------------------------------------------

# Griglia ADWIN (9 valori di delta)
ADWIN_GRID_DELTA: Final[tuple[float, ...]] = (
    0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 0.8
)

# Parametri di default ADWIN (river 0.26.1)
ADWIN_DEFAULT_DELTA: Final[float] = 0.002
ADWIN_DEFAULT_CLOCK: Final[int] = 32
ADWIN_DEFAULT_MAX_BUCKETS: Final[int] = 5
ADWIN_DEFAULT_MIN_WINDOW_LENGTH: Final[int] = 5
ADWIN_DEFAULT_GRACE_PERIOD: Final[int] = 10

# Griglia Page-Hinkley (3 delta x 6 threshold = 18 combinazioni)
PAGE_HINKLEY_GRID_DELTA: Final[tuple[float, ...]] = (0.005, 0.01, 0.05)
PAGE_HINKLEY_GRID_THRESHOLD: Final[tuple[float, ...]] = (
    1.0, 2.0, 5.0, 10.0, 20.0, 50.0
)

# Parametri di default Page-Hinkley (river 0.26.1)
PAGE_HINKLEY_DEFAULT_MIN_INSTANCES: Final[int] = 30
PAGE_HINKLEY_DEFAULT_DELTA: Final[float] = 0.005
PAGE_HINKLEY_DEFAULT_THRESHOLD: Final[float] = 50.0
PAGE_HINKLEY_DEFAULT_ALPHA: Final[float] = 1.0 - 0.0001
PAGE_HINKLEY_DEFAULT_MODE: Final[str] = "both"

# ---------------------------------------------------------------------------
# Parametri scelti congelati (calibrati sul training)
# ---------------------------------------------------------------------------
ADWIN_DELTA: Final[float] = 0.002
PAGE_HINKLEY_DELTA: Final[float] = 0.05
PAGE_HINKLEY_THRESHOLD: Final[float] = 5.0


def detector_params(detector: str) -> dict[str, float | int | str]:
    """Restituisce una nuova copia dei parametri congelati per il detector specificato.

    Parametri
    ---------
    detector : str
        Nome del detector: 'adwin' oppure 'page_hinkley'.

    Restituisce
    -----------
    dict[str, float | int | str]
        Dizionario con tutti i parametri necessari per inizializzare il detector river.

    Solleva
    -------
    TypeError
        Se detector non è una stringa.
    ValueError
        Se detector non è 'adwin' né 'page_hinkley'.
    """
    if not isinstance(detector, str):
        raise TypeError(f"detector must be a str, got {type(detector).__name__}")

    d_lower = detector.strip().lower()
    if d_lower == "adwin":
        return {
            "delta": ADWIN_DELTA,
            "clock": ADWIN_DEFAULT_CLOCK,
            "max_buckets": ADWIN_DEFAULT_MAX_BUCKETS,
            "min_window_length": ADWIN_DEFAULT_MIN_WINDOW_LENGTH,
            "grace_period": ADWIN_DEFAULT_GRACE_PERIOD,
        }
    elif d_lower == "page_hinkley":
        return {
            "min_instances": PAGE_HINKLEY_DEFAULT_MIN_INSTANCES,
            "delta": PAGE_HINKLEY_DELTA,
            "threshold": PAGE_HINKLEY_THRESHOLD,
            "alpha": PAGE_HINKLEY_DEFAULT_ALPHA,
            "mode": PAGE_HINKLEY_DEFAULT_MODE,
        }
    else:
        raise ValueError(
            f"Unknown detector: {detector!r}, expected 'adwin' or 'page_hinkley'"
        )


def run_drift_detector(
    series: np.ndarray,
    detector: str,
    params: Mapping[str, Any] | None = None,
) -> np.ndarray:
    """Esegue un detector di concept drift su una serie 1D e restituisce gli indici con allarme.

    Crea una nuova istanza del detector river all'interno della funzione per garantire
    che ogni chiamata parta da uno stato iniziale pulito senza memoria pregressa.

    Parametri
    ---------
    series : np.ndarray
        Array 1D contenente i valori numerici della serie da monitorare.
    detector : str
        Nome del detector da eseguire: 'adwin' oppure 'page_hinkley'.
    params : Mapping[str, Any] o None, opzionale
        Dizionario dei parametri da passare al costruttore del detector. Se None,
        vengono utilizzati i parametri di default espliciti di river.

    Restituisce
    -----------
    np.ndarray
        Array 1D int64 con gli indici in base 0 delle osservazioni in cui drift_detected
        è risultato True.

    Solleva
    -------
    TypeError
        Se series non è un np.ndarray, se non ha un dtype reale o se detector/params non
        sono dei tipi corretti.
    ValueError
        Se series non è 1D, è vuota o contiene valori non finiti (NaN, Inf), se detector
        non è uno dei due ammessi, o se params contiene chiavi non riconosciute.
    """
    if not isinstance(series, np.ndarray):
        raise TypeError(f"series must be a numpy.ndarray, got {type(series).__name__}")

    # Verifica dtype reale escludendo bool e complessi
    if series.dtype == bool or not (
        np.issubdtype(series.dtype, np.floating) or np.issubdtype(series.dtype, np.integer)
    ):
        raise TypeError(f"series must have a real numeric dtype, got {series.dtype}")

    if series.ndim != 1:
        raise ValueError(f"series must be 1D, got ndim={series.ndim}")

    if series.size == 0:
        raise ValueError("series cannot be empty")

    if not np.all(np.isfinite(series)):
        raise ValueError("series contains non-finite values (NaN or Inf)")

    if not isinstance(detector, str):
        raise TypeError(f"detector must be a str, got {type(detector).__name__}")

    detector_lower = detector.strip().lower()
    if detector_lower not in ("adwin", "page_hinkley"):
        raise ValueError(
            f"detector must be 'adwin' or 'page_hinkley', got {detector!r}"
        )

    if params is not None and not isinstance(params, Mapping):
        raise TypeError(f"params must be a Mapping or None, got {type(params).__name__}")

    # Costruzione istanza pulita
    if detector_lower == "adwin":
        known_keys = {"delta", "clock", "max_buckets", "min_window_length", "grace_period"}
        if params is None:
            det_obj = ADWIN()
        else:
            unknown = set(params.keys()) - known_keys
            if unknown:
                raise ValueError(f"Unknown params for adwin: {sorted(unknown)}")
            det_obj = ADWIN(
                delta=float(params.get("delta", ADWIN_DEFAULT_DELTA)),
                clock=int(params.get("clock", ADWIN_DEFAULT_CLOCK)),
                max_buckets=int(params.get("max_buckets", ADWIN_DEFAULT_MAX_BUCKETS)),
                min_window_length=int(params.get("min_window_length", ADWIN_DEFAULT_MIN_WINDOW_LENGTH)),
                grace_period=int(params.get("grace_period", ADWIN_DEFAULT_GRACE_PERIOD)),
            )
    else:  # page_hinkley
        known_keys = {"min_instances", "delta", "threshold", "alpha", "mode"}
        if params is None:
            det_obj = PageHinkley()
        else:
            unknown = set(params.keys()) - known_keys
            if unknown:
                raise ValueError(f"Unknown params for page_hinkley: {sorted(unknown)}")
            det_obj = PageHinkley(
                min_instances=int(params.get("min_instances", PAGE_HINKLEY_DEFAULT_MIN_INSTANCES)),
                delta=float(params.get("delta", PAGE_HINKLEY_DEFAULT_DELTA)),
                threshold=float(params.get("threshold", PAGE_HINKLEY_DEFAULT_THRESHOLD)),
                alpha=float(params.get("alpha", PAGE_HINKLEY_DEFAULT_ALPHA)),
                mode=str(params.get("mode", PAGE_HINKLEY_DEFAULT_MODE)),
            )

    alarms: list[int] = []
    for i, val in enumerate(series):
        det_obj.update(float(val))
        if det_obj.drift_detected:
            alarms.append(i)

    return np.array(alarms, dtype=np.int64)


def select_best_candidate(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    """Seleziona la combinazione ottima di parametri secondo la regola a tre criteri.

    Criteri in ordine di priorità decrescente:
    1. Minima distanza intera dal target 1.9: |10*(a + b) - 38|;
    2. Minimo numero totale di allarmi (a + b);
    3. Prima combinazione nell'ordine di definizione della griglia (grid_index).

    Parametri
    ---------
    candidates : list[dict[str, Any]]
        Lista di dizionari, ciascuno contenente 'alarms_2000', 'alarms_2010' e 'grid_index'.

    Restituisce
    -----------
    dict[str, Any]
        Il candidato selezionato.

    Solleva
    -------
    ValueError
        Se candidates è vuota.
    """
    if not candidates:
        raise ValueError("candidates list cannot be empty")

    def sort_key(c: dict[str, Any]) -> tuple[int, int, int]:
        a = int(c["alarms_2000"])
        b = int(c["alarms_2010"])
        dist_int = abs(10 * (a + b) - 38)
        tot_alarms = a + b
        grid_idx = int(c["grid_index"])
        return (dist_int, tot_alarms, grid_idx)

    return min(candidates, key=sort_key)


def calibrate_adwin(
    series_2000: np.ndarray,
    series_2010: np.ndarray,
) -> tuple[dict[str, Any], pd.DataFrame]:
    """Esegue la taratura di ADWIN sulla griglia dei valori di delta.

    Parametri
    ---------
    series_2000 : np.ndarray
        Serie 1D di log-loss per la stagione 2000-01.
    series_2010 : np.ndarray
        Serie 1D di log-loss per la stagione 2010-11.

    Restituisce
    -----------
    tuple[dict[str, Any], pd.DataFrame]
        Tupla con la combinazione ottima selezionata e la tabella completa della griglia.
    """
    rows: list[dict[str, Any]] = []

    for idx, delta_val in enumerate(ADWIN_GRID_DELTA):
        params = {
            "delta": delta_val,
            "clock": ADWIN_DEFAULT_CLOCK,
            "max_buckets": ADWIN_DEFAULT_MAX_BUCKETS,
            "min_window_length": ADWIN_DEFAULT_MIN_WINDOW_LENGTH,
            "grace_period": ADWIN_DEFAULT_GRACE_PERIOD,
        }
        alarms_2000 = len(run_drift_detector(series_2000, "adwin", params))
        alarms_2010 = len(run_drift_detector(series_2010, "adwin", params))
        mean_alarms = (alarms_2000 + alarms_2010) / 2.0
        dist_int = abs(10 * (alarms_2000 + alarms_2010) - 38)
        tot_alarms = alarms_2000 + alarms_2010

        rows.append({
            "grid_index": idx,
            "detector": "adwin",
            "delta": delta_val,
            "alarms_2000": alarms_2000,
            "alarms_2010": alarms_2010,
            "total_alarms": tot_alarms,
            "mean_alarms": mean_alarms,
            "distance_int": dist_int,
            "distance_from_target": abs(mean_alarms - TARGET_ALARMS_PER_SEASON),
        })

    best = select_best_candidate(rows)
    df_grid = pd.DataFrame(rows)
    return best, df_grid


def calibrate_page_hinkley(
    series_2000: np.ndarray,
    series_2010: np.ndarray,
) -> tuple[dict[str, Any], pd.DataFrame]:
    """Esegue la taratura di Page-Hinkley sulla griglia di delta e threshold.

    Parametri
    ---------
    series_2000 : np.ndarray
        Serie 1D di log-loss per la stagione 2000-01.
    series_2010 : np.ndarray
        Serie 1D di log-loss per la stagione 2010-11.

    Restituisce
    -----------
    tuple[dict[str, Any], pd.DataFrame]
        Tupla con la combinazione ottima selezionata e la tabella completa della griglia.
    """
    rows: list[dict[str, Any]] = []
    idx = 0

    for delta_val in PAGE_HINKLEY_GRID_DELTA:
        for thresh_val in PAGE_HINKLEY_GRID_THRESHOLD:
            params = {
                "min_instances": PAGE_HINKLEY_DEFAULT_MIN_INSTANCES,
                "delta": delta_val,
                "threshold": thresh_val,
                "alpha": PAGE_HINKLEY_DEFAULT_ALPHA,
                "mode": PAGE_HINKLEY_DEFAULT_MODE,
            }
            alarms_2000 = len(run_drift_detector(series_2000, "page_hinkley", params))
            alarms_2010 = len(run_drift_detector(series_2010, "page_hinkley", params))
            mean_alarms = (alarms_2000 + alarms_2010) / 2.0
            dist_int = abs(10 * (alarms_2000 + alarms_2010) - 38)
            tot_alarms = alarms_2000 + alarms_2010

            rows.append({
                "grid_index": idx,
                "detector": "page_hinkley",
                "delta": delta_val,
                "threshold": thresh_val,
                "alarms_2000": alarms_2000,
                "alarms_2010": alarms_2010,
                "total_alarms": tot_alarms,
                "mean_alarms": mean_alarms,
                "distance_int": dist_int,
                "distance_from_target": abs(mean_alarms - TARGET_ALARMS_PER_SEASON),
            })
            idx += 1

    best = select_best_candidate(rows)
    df_grid = pd.DataFrame(rows)
    return best, df_grid


def calibrate_drift_detectors(
    series_2000: np.ndarray,
    series_2010: np.ndarray,
) -> tuple[dict[str, Any], dict[str, Any], pd.DataFrame]:
    """Esegue la taratura completa di ADWIN e Page-Hinkley sulle due serie di training.

    Restituisce
    -----------
    tuple[dict[str, Any], dict[str, Any], pd.DataFrame]
        Miglior candidato ADWIN, miglior candidato Page-Hinkley e tabella unificata della griglia.
    """
    best_adwin, df_adwin = calibrate_adwin(series_2000, series_2010)
    best_ph, df_ph = calibrate_page_hinkley(series_2000, series_2010)
    df_combined = pd.concat([df_adwin, df_ph], ignore_index=True)
    return best_adwin, best_ph, df_combined


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
    """Genera i generatori casuali NumPy annidati secondo lo schema di seed di C5.

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
