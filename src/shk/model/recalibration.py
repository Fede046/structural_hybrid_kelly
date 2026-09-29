"""Modulo per la ricalibrazione del Modulo 1: isotonic regression, Platt scaling, reliability e Brier."""

import math
from typing import Any, Final, NamedTuple
import numpy as np
import pandas as pd
from scipy.optimize import isotonic_regression, minimize

from shk.model.elo_fit import (
    ELO_FITS,
    EloFitParams,
    derive_fit_schedule,
    parse_season_start_year,
)
from shk.model.elo_predictor import predict_elo_fast
from shk.model.scoring import (
    MATCH_KEYS,
    SeriesEvaluationData,
    align_predictions_with_odds,
)

# Soglie per il clipping di probabilità prima della rinormalizzazione
PROB_LOWER_CLIP: Final[float] = 1e-6
PROB_UPPER_CLIP: Final[float] = 1.0 - 1e-6

# Esiti canonici 1X2
OUTCOMES: Final[tuple[str, ...]] = ("H", "D", "A")

# Colonne del CSV di output results/us_c4_3_calibration.csv
CALIBRATION_CSV_COLUMNS: Final[tuple[str, ...]] = (
    "level",
    "version",
    "series",
    "method",
    "outcome",
    "bin_lower",
    "bin_upper",
    "count",
    "mean_predicted",
    "observed_frequency",
    "gap",
    "z",
    "matches_used",
    "log_loss",
    "brier",
    "g_hat",
)


class IsotonicModel(NamedTuple):
    """Modello di regressione isotonica univariata."""

    p_support: np.ndarray
    q_support: np.ndarray


class PlattModel(NamedTuple):
    """Parametri del modello di Platt scaling: sigma(a * logit(p) + b)."""

    a: float
    b: float
    success: bool
    nit: int
    nfev: int


class FitCalibrationMaps(NamedTuple):
    """Mappe di ricalibrazione one-vs-rest per un fit Elo."""

    fit_through: str
    isotonic: dict[str, IsotonicModel]
    platt: dict[str, PlattModel]


def compute_brier_scores(probs: np.ndarray, outcomes: np.ndarray) -> np.ndarray:
    """Calcola il Brier score multiclasse per ciascuna partita.

    BS_t = sum_{k in {H, D, A}} (p_{t, k} - I(x_t = k))^2.

    Parametri
    ---------
    probs : np.ndarray
        Matrice di probabilità di forma (N, 3).
    outcomes : np.ndarray
        Array 1D di esiti ('H', 'D', 'A') di lunghezza N.

    Restituisce
    -----------
    np.ndarray
        Array 1D float64 di Brier score per partita.
    """
    if not isinstance(probs, np.ndarray):
        raise TypeError(f"probs must be a numpy.ndarray, got {type(probs).__name__}")
    if probs.dtype == bool or not (
        np.issubdtype(probs.dtype, np.integer) or np.issubdtype(probs.dtype, np.floating)
    ):
        raise TypeError(f"probs must have a real numeric dtype, got {probs.dtype}")
    if probs.ndim != 2 or probs.shape[1] != 3:
        raise ValueError(f"probs must have shape (N, 3), got {probs.shape}")

    if not isinstance(outcomes, np.ndarray):
        raise TypeError(f"outcomes must be a numpy.ndarray, got {type(outcomes).__name__}")
    if outcomes.ndim != 1 or outcomes.shape[0] != probs.shape[0]:
        raise ValueError(
            f"outcomes length ({len(outcomes)}) must match probs rows ({probs.shape[0]})"
        )

    outcomes_str = outcomes.astype(str)
    n = len(outcomes_str)
    if n == 0:
        return np.empty((0,), dtype=np.float64)

    target_matrix = np.zeros((n, 3), dtype=np.float64)
    idx_map = {"H": 0, "D": 1, "A": 2}
    for i, out in enumerate(outcomes_str):
        if out not in idx_map:
            raise ValueError(f"Invalid outcome: '{out}', expected one of {OUTCOMES}")
        target_matrix[i, idx_map[out]] = 1.0

    diff = probs - target_matrix
    return np.sum(diff * diff, axis=1)


def brier_score(probs: np.ndarray, outcomes: np.ndarray) -> float:
    """Calcola il Brier score multiclasse medio su tutte le partite.

    Parametri
    ---------
    probs : np.ndarray
        Matrice di probabilità di forma (N, 3).
    outcomes : np.ndarray
        Array 1D di esiti ('H', 'D', 'A') di lunghezza N.

    Restituisce
    -----------
    float
        Media aritmetica del Brier score.
    """
    scores = compute_brier_scores(probs, outcomes)
    if len(scores) == 0:
        raise ValueError("Cannot compute brier score of empty array")
    return float(np.mean(scores))


def compute_reliability_table(
    probs: np.ndarray,
    outcomes: np.ndarray,
    outcome_filter: str = "all",
    n_bins: int = 10,
) -> list[dict[str, Any]]:
    """Calcola la tabella di reliability su 10 bin di ampiezza 0.1 in [0, 1].

    Parametri
    ---------
    probs : np.ndarray
        Matrice di probabilità di forma (N, 3) relative a (H, D, A).
    outcomes : np.ndarray
        Array 1D di esiti realizzati ('H', 'D', 'A') di lunghezza N.
    outcome_filter : str
        'all' per la forma aggregata (3 coppie per partita), oppure 'H', 'D', 'A'.
    n_bins : int
        Numero di bin (default 10).

    Restituisce
    -----------
    list[dict[str, Any]]
        Lista di dizionari per ciascun bin con conteggio, probabilità media,
        frequenza osservata, scarto e statistica z di Wald.
    """
    if outcome_filter not in ("all", "H", "D", "A"):
        raise ValueError(f"Unknown outcome_filter '{outcome_filter}', expected 'all', 'H', 'D', or 'A'")

    n = len(outcomes)
    outcomes_str = outcomes.astype(str)

    if outcome_filter == "all":
        p_list = []
        y_list = []
        idx_map = {"H": 0, "D": 1, "A": 2}
        for i, out in enumerate(outcomes_str):
            for k_str, col_idx in idx_map.items():
                p_list.append(float(probs[i, col_idx]))
                y_list.append(1.0 if out == k_str else 0.0)
        p_arr = np.array(p_list, dtype=np.float64)
        y_arr = np.array(y_list, dtype=np.float64)
    else:
        col_idx = {"H": 0, "D": 1, "A": 2}[outcome_filter]
        p_arr = probs[:, col_idx].astype(np.float64)
        y_arr = (outcomes_str == outcome_filter).astype(np.float64)

    bin_width = 1.0 / n_bins
    table: list[dict[str, Any]] = []

    for b in range(n_bins):
        b_lower = b * bin_width
        b_upper = (b + 1) * bin_width

        if b == n_bins - 1:
            # Ultimo bin chiuso anche a destra: [0.9, 1.0]
            mask = (p_arr >= b_lower) & (p_arr <= b_upper)
        else:
            # Chiuso a sinistra, aperto a destra: [lower, upper)
            mask = (p_arr >= b_lower) & (p_arr < b_upper)

        count = int(np.sum(mask))
        if count == 0:
            table.append({
                "bin_lower": b_lower,
                "bin_upper": b_upper,
                "count": 0,
                "mean_predicted": None,
                "observed_frequency": None,
                "gap": None,
                "z": None,
            })
        else:
            mean_p = float(np.mean(p_arr[mask]))
            obs_y = float(np.mean(y_arr[mask]))
            gap = obs_y - mean_p

            denom_var = mean_p * (1.0 - mean_p) / count
            if denom_var <= 0.0:
                z_val = 0.0 if gap == 0.0 else None
            else:
                z_val = float(gap / math.sqrt(denom_var))

            table.append({
                "bin_lower": b_lower,
                "bin_upper": b_upper,
                "count": count,
                "mean_predicted": mean_p,
                "observed_frequency": obs_y,
                "gap": gap,
                "z": z_val,
            })

    return table


def fit_isotonic_single(p_train: np.ndarray, y_train: np.ndarray) -> IsotonicModel:
    """Stima una mappa isotonica non decrescente aggregando i ties con pesi."""
    if len(p_train) != len(y_train):
        raise ValueError("p_train and y_train must have the same length")

    p_unique, inverse_indices = np.unique(p_train, return_inverse=True)
    weights = np.bincount(inverse_indices).astype(np.float64)
    y_sums = np.bincount(inverse_indices, weights=y_train.astype(np.float64))
    y_means = y_sums / weights

    res = isotonic_regression(y_means, weights=weights, increasing=True)
    q_iso = res.x.astype(np.float64)

    return IsotonicModel(p_support=p_unique, q_support=q_iso)


def predict_isotonic_single(model: IsotonicModel, p_new: np.ndarray) -> np.ndarray:
    """Applica la mappa isotonica con interpolazione lineare ed estrapolazione costante."""
    return np.interp(
        p_new,
        model.p_support,
        model.q_support,
        left=float(model.q_support[0]),
        right=float(model.q_support[-1]),
    )


def fit_platt_single(p_train: np.ndarray, y_train: np.ndarray) -> PlattModel:
    """Stima i parametri a, b di Platt scaling sigma(a * logit(p) + b) per massima verosimiglianza."""
    if len(p_train) != len(y_train):
        raise ValueError("p_train and y_train must have the same length")

    p_clipped = np.clip(p_train, 1e-12, 1.0 - 1e-12)
    z = np.log(p_clipped / (1.0 - p_clipped))
    y = y_train.astype(np.float64)
    n = len(z)

    def objective_and_grad(params: np.ndarray) -> tuple[float, np.ndarray]:
        a, b = float(params[0]), float(params[1])
        eta = a * z + b
        # Forma stabile: logaddexp(0, eta) - y * eta
        loss = float(np.mean(np.logaddexp(0.0, eta) - y * eta))

        # Gradiente analitico
        # sigma(eta) = 1 / (1 + exp(-eta))
        # Per evitare overflow:
        sig = np.where(eta >= 0, 1.0 / (1.0 + np.exp(-eta)), np.exp(eta) / (1.0 + np.exp(eta)))
        diff = sig - y
        grad_a = float(np.mean(diff * z))
        grad_b = float(np.mean(diff))
        return loss, np.array([grad_a, grad_b], dtype=np.float64)

    res = minimize(
        objective_and_grad,
        x0=np.array([1.0, 0.0], dtype=np.float64),
        method="L-BFGS-B",
        jac=True,
        options={"gtol": 1e-8, "ftol": 1e-12},
    )

    if not res.success:
        raise RuntimeError(
            f"Platt scaling optimization failed to converge: {res.message} (nit={res.nit})"
        )

    return PlattModel(
        a=float(res.x[0]),
        b=float(res.x[1]),
        success=bool(res.success),
        nit=int(res.nit),
        nfev=int(res.nfev),
    )


def predict_platt_single(model: PlattModel, p_new: np.ndarray) -> np.ndarray:
    """Applica il modello di Platt scaling sigma(a * logit(p) + b)."""
    p_clipped = np.clip(p_new, 1e-12, 1.0 - 1e-12)
    z = np.log(p_clipped / (1.0 - p_clipped))
    eta = model.a * z + model.b
    return np.where(eta >= 0, 1.0 / (1.0 + np.exp(-eta)), np.exp(eta) / (1.0 + np.exp(eta)))


def generate_fit_training_predictions(
    df: pd.DataFrame,
    fit_through: str,
    train_seasons: list[str],
    params: EloFitParams,
) -> pd.DataFrame:
    """Genera le previsioni walk-forward sulle stagioni di training del fit con esito FTR."""
    preds = predict_elo_fast(
        df,
        train_seasons,
        k=params.k,
        h=params.h,
        nu=params.nu,
    )
    return align_predictions_with_odds(preds, df)


def fit_all_calibration_maps(
    df: pd.DataFrame,
    fits: dict[str, EloFitParams],
    schedule: dict[str, dict[str, list[str]]],
) -> dict[str, FitCalibrationMaps]:
    """Stima le mappe di ricalibrazione one-vs-rest per tutti i fit dello schedule."""
    all_maps: dict[str, FitCalibrationMaps] = {}

    for fit_through, params in fits.items():
        if fit_through not in schedule:
            raise ValueError(f"Fit '{fit_through}' missing from schedule")
        train_seasons = schedule[fit_through]["training"]
        df_train = generate_fit_training_predictions(df, fit_through, train_seasons, params)

        iso_dict: dict[str, IsotonicModel] = {}
        platt_dict: dict[str, PlattModel] = {}

        outcome_col_map = {"H": "p_home", "D": "p_draw", "A": "p_away"}
        for out in OUTCOMES:
            p_train = df_train[outcome_col_map[out]].to_numpy(dtype=np.float64)
            y_train = (df_train["FTR"].astype(str).str.strip() == out).astype(np.float64).to_numpy()

            iso_dict[out] = fit_isotonic_single(p_train, y_train)
            platt_dict[out] = fit_platt_single(p_train, y_train)

        all_maps[fit_through] = FitCalibrationMaps(
            fit_through=fit_through,
            isotonic=iso_dict,
            platt=platt_dict,
        )

    return all_maps


def recalibrate_series_predictions(
    eval_data: SeriesEvaluationData,
    fit_maps: dict[str, FitCalibrationMaps],
    method: str,
    schedule: dict[str, dict[str, list[str]]],
) -> tuple[np.ndarray, int, dict[str, int]]:
    """Punto d'ingresso unico: ricalibra le probabilità p_model di SeriesEvaluationData per fit.

    Applica le mappe one-vs-rest del fit che serve ciascuna stagione, limita le probabilità
    a [1e-6, 1 - 1e-6], e rinormalizza a somma 1 riga per riga.

    Parametri
    ---------
    eval_data : SeriesEvaluationData
        Oggetto contenente le partite di validazione filtrate e p_model (N, 3).
    fit_maps : dict[str, FitCalibrationMaps]
        Dizionario delle mappe stimate sul training per ciascun fit.
    method : str
        'isotonic' oppure 'platt'.
    schedule : dict[str, dict[str, list[str]]]
        Schema dei fit per ricavare la mappatura stagione -> fit.

    Restituisce
    -----------
    tuple[np.ndarray, int, dict[str, int]]
        - Matrice ricalibrata di forma (N, 3) con somme a 1 entro 1e-12;
        - Conteggio totale dei valori singoli limitati;
        - Conteggio dei valori limitati per esito ('H', 'D', 'A').
    """
    if method not in ("isotonic", "platt"):
        raise ValueError(f"Unknown recalibration method '{method}', expected 'isotonic' or 'platt'")

    # Mappatura stagione di validazione -> fit_through di riferimento
    season_to_fit: dict[str, str] = {}
    for fit_key, entry in schedule.items():
        for val_s in entry["validation"]:
            season_to_fit[val_s] = fit_key

    df_used = eval_data.df_used
    p_raw = eval_data.p_model
    n_matches = len(df_used)

    p_recal = np.empty((n_matches, 3), dtype=np.float64)
    total_clipped = 0
    clipped_by_outcome: dict[str, int] = {"H": 0, "D": 0, "A": 0}

    for i in range(n_matches):
        season = df_used.at[i, "season"]
        if season not in season_to_fit:
            raise ValueError(f"Season '{season}' not found in validation schedule")
        fit_key = season_to_fit[season]
        if fit_key not in fit_maps:
            raise ValueError(f"Fit '{fit_key}' missing from fit_maps")

        maps_for_fit = fit_maps[fit_key]
        raw_row = p_raw[i]  # [p_H, p_D, p_A]

        # 1. Applicazione mappe one-vs-rest per esito
        unnorm_row = np.empty(3, dtype=np.float64)
        for out_idx, out in enumerate(OUTCOMES):
            p_val = raw_row[out_idx]
            if method == "isotonic":
                mapped_val = float(predict_isotonic_single(maps_for_fit.isotonic[out], np.array([p_val]))[0])
            else:
                mapped_val = float(predict_platt_single(maps_for_fit.platt[out], np.array([p_val]))[0])

            # 2. Verifica se il valore cade fuori dall'intervallo [1e-6, 1 - 1e-6]
            if mapped_val < PROB_LOWER_CLIP or mapped_val > PROB_UPPER_CLIP:
                total_clipped += 1
                clipped_by_outcome[out] += 1
                clipped_val = min(max(mapped_val, PROB_LOWER_CLIP), PROB_UPPER_CLIP)
            else:
                clipped_val = mapped_val

            unnorm_row[out_idx] = clipped_val

        # 3. Rinormalizzazione a somma 1
        s_row = float(np.sum(unnorm_row))
        p_recal[i] = unnorm_row / s_row

    # Controllo che le probabilità ricalibrate sommino a 1 entro 1e-12
    row_sums = np.sum(p_recal, axis=1)
    if np.any(np.abs(row_sums - 1.0) > 1e-12):
        raise ValueError("Recalibrated probabilities do not sum to 1.0 within 1e-12")

    return p_recal, total_clipped, clipped_by_outcome
