"""Modulo per la calibrazione espansiva dei parametri Elo (K, h, nu) e baseline c.

Questo modulo definisce la funzione obiettivo di log-loss, la procedura di ottimizzazione
deterministica vincolata tramite Nelder-Mead, la derivazione dello schema di partizione
temporale e i parametri ottimi congelati in ELO_FITS.
"""

from collections.abc import Collection
import math
import re
import time
from typing import Any, Final, NamedTuple
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from shk.data.split import SplitConfig
from shk.model.elo import expected_score
from shk.model.elo_predictor import predict_elo_fast

SEASON_REGEX: Final[re.Pattern] = re.compile(r"^(\d{4})-(\d{2})$")

# Limiti di ricerca per i parametri
BOUNDS_K: Final[tuple[float, float]] = (5.0, 80.0)
BOUNDS_H: Final[tuple[float, float]] = (0.0, 200.0)
BOUNDS_NU: Final[tuple[float, float]] = (0.05, 3.0)
PARAM_BOUNDS: Final[list[tuple[float, float]]] = [BOUNDS_K, BOUNDS_H, BOUNDS_NU]

# Punto iniziale deterministico per l'ottimizzatore
INITIAL_PARAMS: Final[tuple[float, float, float]] = (30.0, 60.0, 1.0)

# Opzioni e metodo dell'ottimizzatore
OPTIMIZER_METHOD: Final[str] = "Nelder-Mead"
OPTIMIZER_OPTIONS: Final[dict[str, Any]] = {
    "xatol": 1e-4,
    "fatol": 1e-10,
    "maxiter": 2000,
    "maxfev": 4000,
}

# Tolleranza per rilevare se un ottimo giace sul bordo
BOUNDARY_ABS_TOL: Final[float] = 1e-5

# Griglie a 41 punti per i profili di log-loss
GRID_K: Final[np.ndarray] = np.linspace(5.0, 80.0, 41)
GRID_H: Final[np.ndarray] = np.linspace(0.0, 200.0, 41)

# Colonne dichiarate per il CSV delle previsioni walk-forward
WALKFORWARD_CSV_COLUMNS: Final[list[str]] = [
    "fit_through",
    "role",
    "season",
    "date",
    "home_team",
    "away_team",
    "ftr",
    "home_promotion",
    "away_promotion",
    "rating_home",
    "rating_away",
    "delta",
    "p_home",
    "p_draw",
    "p_away",
]


class EloFitParams(NamedTuple):
    """Parametri congelati di un fit Elo e frequenza di pareggio della baseline."""

    k: float
    h: float
    nu: float
    c: float


class EloCalibrationResult(NamedTuple):
    """Risultato dettagliato della calibrazione di un fit."""

    fit_through: str
    k: float
    h: float
    nu: float
    c: float
    log_loss_train: float
    log_loss_train_baseline: float
    n_train_matches: int
    success: bool
    message: str
    nit: int
    nfev: int
    duration_seconds: float
    is_on_boundary: dict[str, bool]


def parse_season_start_year(season: str) -> int:
    """Valida il formato YYYY-YY e restituisce l'anno iniziale intero."""
    if not isinstance(season, str):
        raise TypeError(f"Season must be a str, got {type(season).__name__}")
    match = SEASON_REGEX.match(season)
    if not match:
        raise ValueError(f"Invalid season format: {season!r}, expected 'YYYY-YY'")
    start_year = int(match.group(1))
    end_year = int(match.group(2))
    if (start_year + 1) % 100 != end_year:
        raise ValueError(
            f"Season year continuity mismatch in '{season}': {start_year} -> {end_year}"
        )
    return start_year


def derive_fit_schedule(
    training: Collection[str] | SplitConfig,
    validation: Collection[str] | None = None,
) -> dict[str, dict[str, list[str]]]:
    """Deriva lo schema dei fit dallo split temporale senza stagioni cablate a mano.

    Parametri
    ---------
    training : Collection[str] o SplitConfig
        Collezione delle stagioni di training, oppure istanza di SplitConfig.
    validation : Collection[str] o None, opzionale
        Collezione delle stagioni di validazione. Obbligatorio se training non è SplitConfig.

    Restituisce
    -----------
    dict[str, dict[str, list[str]]]
        Mappa da ultima stagione di training del fit (chiave) a dizionario con:
        - "training": lista ordinata delle stagioni di training del fit (<= fit_through);
        - "validation": lista ordinata delle stagioni di validazione assegnate al fit.
    """
    if isinstance(training, SplitConfig):
        train_list = list(training.training)
        val_list = list(training.validation)
    else:
        if validation is None:
            raise TypeError("validation must be provided when training is not a SplitConfig")
        train_list = list(training)
        val_list = list(validation)

    train_seasons = sorted(train_list, key=parse_season_start_year)
    val_seasons = sorted(val_list, key=parse_season_start_year)

    schedule: dict[str, dict[str, list[str]]] = {}

    for j in train_seasons:
        j_year = parse_season_start_year(j)
        # Stagioni di training del fit j: tutte le stagioni di training <= j
        fit_train = [s for s in train_seasons if parse_season_start_year(s) <= j_year]

        # Stagioni di validazione assegnate a j: quelle per cui j è la stagione
        # di training più recente strettamente anteriore
        fit_val: list[str] = []
        for v in val_seasons:
            v_year = parse_season_start_year(v)
            earlier_train = [t for t in train_seasons if parse_season_start_year(t) < v_year]
            if earlier_train and max(earlier_train, key=parse_season_start_year) == j:
                fit_val.append(v)

        schedule[j] = {
            "training": fit_train,
            "validation": fit_val,
        }

    return schedule


def compute_training_log_loss(
    df_sub: pd.DataFrame,
    target_train_seasons: list[str],
    k: float,
    h: float,
    nu: float,
    df_ground_truth: pd.DataFrame,
) -> tuple[float, pd.DataFrame]:
    """Calcola la log-loss media delle probabilità Davidson sulle partite di training.

    Verifica riga per riga l'allineamento tra previsioni e ground truth.
    """
    preds = predict_elo_fast(df_sub, target_train_seasons, k=k, h=h, nu=nu)

    if len(preds) != len(df_ground_truth):
        raise ValueError(
            f"Row count mismatch: predictions have {len(preds)} rows, "
            f"ground truth has {len(df_ground_truth)} rows."
        )

    # Verifica coincidenza riga per riga delle chiavi identificative
    for col in ("season", "Date", "HomeTeam", "AwayTeam"):
        if not preds[col].equals(df_ground_truth[col]):
            raise ValueError(f"Key mismatch between predictions and ground truth in column '{col}'")

    p_h = preds["p_home"].to_numpy()
    p_d = preds["p_draw"].to_numpy()
    p_a = preds["p_away"].to_numpy()
    ftr = df_ground_truth["FTR"].to_numpy()

    p_true = np.where(ftr == "H", p_h, np.where(ftr == "D", p_d, p_a))
    # Protezione numerica rigorosa per il logaritmo naturale
    p_true_safe = np.clip(p_true, 1e-15, 1.0)
    log_loss = float(-np.mean(np.log(p_true_safe)))

    return log_loss, preds


def calibrate_single_fit(
    df: pd.DataFrame,
    fit_through: str,
    training_seasons: list[str],
) -> EloCalibrationResult:
    """Calibra un singolo fit Elo tramite ottimizzazione deterministica Nelder-Mead.

    Parametri
    ---------
    df : pd.DataFrame
        DataFrame completo contenente partite storiche e di training ordinate per data.
    fit_through : str
        Ultima stagione di training del fit (es. '2000-01').
    training_seasons : list[str]
        Lista delle stagioni di training del fit (<= fit_through).

    Restituisce
    -----------
    EloCalibrationResult
        Risultato completo della calibrazione con parametri, log-loss, diagnostiche e tempi.
    """
    j_year = parse_season_start_year(fit_through)

    # Riduzione del DataFrame alle stagioni <= j
    season_years = df["season"].map(parse_season_start_year)
    df_sub = df[season_years <= j_year].copy().reset_index(drop=True)

    # Ground truth delle partite di training da verificare riga per riga
    df_ground_truth = df_sub[df_sub["season"].isin(training_seasons)].copy().reset_index(drop=True)
    n_train = len(df_ground_truth)

    # Calcolo frequenza pareggio sulla storia di training del fit
    n_draws = int(np.sum(df_ground_truth["FTR"] == "D"))
    c_baseline = float(n_draws / n_train)

    def objective(params: np.ndarray) -> float:
        k_val, h_val, nu_val = float(params[0]), float(params[1]), float(params[2])
        loss, _ = compute_training_log_loss(
            df_sub, training_seasons, k_val, h_val, nu_val, df_ground_truth
        )
        return loss

    t0 = time.perf_counter()
    opt_res = minimize(
        objective,
        x0=np.array(INITIAL_PARAMS, dtype=np.float64),
        method=OPTIMIZER_METHOD,
        bounds=PARAM_BOUNDS,
        options=OPTIMIZER_OPTIONS,
    )
    duration = time.perf_counter() - t0

    k_opt = float(opt_res.x[0])
    h_opt = float(opt_res.x[1])
    nu_opt = float(opt_res.x[2])
    log_loss_train = float(opt_res.fun)

    # Ricalcolo previsioni con i parametri ottimali per baseline e verifica
    _, best_preds = compute_training_log_loss(
        df_sub, training_seasons, k_opt, h_opt, nu_opt, df_ground_truth
    )

    # Log-loss baseline a pareggio costante sulle stesse partite di training
    delta_vals = best_preds["delta"].to_numpy()
    e_vals = expected_score(delta_vals, s=400.0)
    p_base_h = (1.0 - c_baseline) * e_vals
    p_base_d = np.full_like(e_vals, c_baseline)
    p_base_a = (1.0 - c_baseline) * (1.0 - e_vals)

    ftr = df_ground_truth["FTR"].to_numpy()
    p_base_true = np.where(ftr == "H", p_base_h, np.where(ftr == "D", p_base_d, p_base_a))
    p_base_safe = np.clip(p_base_true, 1e-15, 1.0)
    log_loss_base = float(-np.mean(np.log(p_base_safe)))

    # Verifica se i parametri ottimi toccano i bordi di ricerca
    is_on_boundary = {
        "k_lower": math.isclose(k_opt, BOUNDS_K[0], abs_tol=BOUNDARY_ABS_TOL),
        "k_upper": math.isclose(k_opt, BOUNDS_K[1], abs_tol=BOUNDARY_ABS_TOL),
        "h_lower": math.isclose(h_opt, BOUNDS_H[0], abs_tol=BOUNDARY_ABS_TOL),
        "h_upper": math.isclose(h_opt, BOUNDS_H[1], abs_tol=BOUNDARY_ABS_TOL),
        "nu_lower": math.isclose(nu_opt, BOUNDS_NU[0], abs_tol=BOUNDARY_ABS_TOL),
        "nu_upper": math.isclose(nu_opt, BOUNDS_NU[1], abs_tol=BOUNDARY_ABS_TOL),
    }

    return EloCalibrationResult(
        fit_through=fit_through,
        k=k_opt,
        h=h_opt,
        nu=nu_opt,
        c=c_baseline,
        log_loss_train=log_loss_train,
        log_loss_train_baseline=log_loss_base,
        n_train_matches=n_train,
        success=bool(opt_res.success),
        message=str(opt_res.message),
        nit=int(opt_res.nit),
        nfev=int(opt_res.nfev),
        duration_seconds=duration,
        is_on_boundary=is_on_boundary,
    )


def calibrate_all_fits(
    df: pd.DataFrame,
    schedule: dict[str, dict[str, list[str]]],
) -> dict[str, EloCalibrationResult]:
    """Esegue la calibrazione di tutti i fit definiti nello schema."""
    results: dict[str, EloCalibrationResult] = {}
    for fit_through, entry in schedule.items():
        res = calibrate_single_fit(df, fit_through, entry["training"])
        results[fit_through] = res
    return results


# Parametri congelati della calibrazione US-C4.1 (calibrati il 2026-09-29)
ELO_FITS: Final[dict[str, EloFitParams]] = {
    "2000-01": EloFitParams(
        k=10.318224689650037,
        h=125.54022316884253,
        nu=0.8062246331085681,
        c=0.2657894736842105,
    ),
    "2010-11": EloFitParams(
        k=9.934776455088759,
        h=127.87791672140764,
        nu=0.8775613268630023,
        c=0.2789473684210526,
    ),
    "2020-21": EloFitParams(
        k=7.928543266007228,
        h=78.033626101627,
        nu=0.7603760315281511,
        c=0.25877192982456143,
    ),
}
