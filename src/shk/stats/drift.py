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

# Target di allarmi per stagione (38 partite x alpha 0.05)
TARGET_ALARMS_PER_SEASON: Final[float] = 1.9

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
