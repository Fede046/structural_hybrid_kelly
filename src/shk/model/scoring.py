"""Modulo per il calcolo di log-loss, termini di gap g_hat e valutazione empirica."""

from typing import Any, Final, NamedTuple
import numpy as np
import pandas as pd

from shk.market.devig import devig_additive, devig_power, devig_proportional
from shk.model.elo_fit import (
    EloFitParams,
    parse_season_start_year,
)
from shk.model.elo_predictor import predict_elo_fast

# Stagione iniziale e anno iniziale per la serie Pinnacle closing
PINNACLE_CLOSING_START_SEASON: Final[str] = "2012-13"
PINNACLE_START_YEAR: Final[int] = 2012

# Metodi di de-vigging ammessi
DEVIG_METHODS: Final[tuple[str, ...]] = ("proportional", "additive", "power")

# Serie di quote ammesse
SERIES_NAMES: Final[tuple[str, ...]] = ("b365_prematch", "pinnacle_closing")

# Chiavi identificative di partita per l'allineamento semantico
MATCH_KEYS: Final[tuple[str, ...]] = ("season", "Date", "HomeTeam", "AwayTeam")

# Colonne del CSV di output results/us_c4_2_g_hat.csv
CSV_COLUMNS: Final[tuple[str, ...]] = (
    "level",
    "series",
    "method",
    "t",
    "season",
    "date",
    "matches_used",
    "matches_excluded",
    "log_loss_model",
    "log_loss_market",
    "g_hat",
)


def _validate_probs(probs: np.ndarray) -> np.ndarray:
    """Valida la matrice di probabilità di forma (N, 3)."""
    if not isinstance(probs, np.ndarray):
        raise TypeError(f"probs must be a numpy.ndarray, got {type(probs).__name__}")
    if probs.dtype == bool or not (
        np.issubdtype(probs.dtype, np.integer) or np.issubdtype(probs.dtype, np.floating)
    ):
        raise TypeError(f"probs must have a real numeric dtype, got {probs.dtype}")
    if probs.ndim != 2 or probs.shape[1] != 3:
        raise ValueError(f"probs must have shape (N, 3), got {probs.shape}")
    if not np.all(np.isfinite(probs)):
        raise ValueError("probs must contain only finite values")
    if np.any(probs < 0.0) or np.any(probs > 1.0):
        raise ValueError("probs must have values in [0, 1]")
    sums = probs.sum(axis=1)
    if np.any(np.abs(sums - 1.0) > 1e-9):
        raise ValueError("Each row of probs must sum to 1.0 within 1e-9")
    return probs.astype(np.float64, copy=False)


def _validate_outcomes(outcomes: np.ndarray, expected_n: int) -> np.ndarray:
    """Valida l'array 1D degli esiti realizzati ('H', 'D', 'A')."""
    if not isinstance(outcomes, np.ndarray):
        raise TypeError(f"outcomes must be a numpy.ndarray, got {type(outcomes).__name__}")
    if outcomes.ndim != 1 or outcomes.shape[0] != expected_n:
        raise ValueError(
            f"outcomes must be a 1D array of length {expected_n}, got shape {outcomes.shape}"
        )
    outcomes_str = outcomes.astype(str)
    valid_chars = {"H", "D", "A"}
    invalid = set(np.unique(outcomes_str)) - valid_chars
    if invalid:
        raise ValueError(f"outcomes must only contain 'H', 'D', 'A', got invalid: {invalid}")
    return outcomes_str


def compute_log_loss(probs: np.ndarray, outcomes: np.ndarray) -> np.ndarray:
    """Calcola la log-loss puntuale con logaritmo naturale per ciascuna partita.

    Parametri
    ---------
    probs : np.ndarray
        Matrice di forma (N, 3) contenente le probabilità (p_home, p_draw, p_away).
    outcomes : np.ndarray
        Array 1D di stringhe di lunghezza N con i risultati realizzati ('H', 'D', 'A').

    Restituisce
    -----------
    np.ndarray
        Array 1D float64 di forma (N,) contenente -ln(p_t(x_t)).

    Solleva
    -------
    TypeError
        Se probs o outcomes non sono ndarray con tipi appropriati.
    ValueError
        Se le dimensioni non corrispondono, se i valori non sommano a 1 entro 1e-9,
        se contengono valori fuori da [0, 1] o se la probabilità dell'esito realizzato è <= 0.
    """
    p = _validate_probs(probs)
    y = _validate_outcomes(outcomes, p.shape[0])

    if len(p) == 0:
        return np.empty((0,), dtype=np.float64)

    idx_map = {"H": 0, "D": 1, "A": 2}
    col_indices = np.array([idx_map[c] for c in y], dtype=np.intp)
    row_indices = np.arange(len(p), dtype=np.intp)

    realized_probs = p[row_indices, col_indices]

    if np.any(realized_probs <= 0.0):
        raise ValueError("Probability of realized outcome must be strictly positive")

    return -np.log(realized_probs)


def compute_mean_log_loss(probs: np.ndarray, outcomes: np.ndarray) -> float:
    """Calcola la log-loss media con logaritmo naturale.

    Parametri
    ---------
    probs : np.ndarray
        Matrice di forma (N, 3).
    outcomes : np.ndarray
        Array 1D di lunghezza N ('H', 'D', 'A').

    Restituisce
    -----------
    float
        Media aritmetica della log-loss.
    """
    losses = compute_log_loss(probs, outcomes)
    if len(losses) == 0:
        raise ValueError("Cannot compute mean log loss of empty array")
    return float(np.mean(losses))


def compute_g_hat_terms(
    p_model: np.ndarray, q_market: np.ndarray, outcomes: np.ndarray
) -> np.ndarray:
    """Calcola i termini di g_hat per partita: ln p_t(x_t) - ln q_t(x_t) = LL(q)_t - LL(p)_t.

    Parametri
    ---------
    p_model : np.ndarray
        Probabilità del modello di forma (N, 3).
    q_market : np.ndarray
        Probabilità de-viggati del mercato di forma (N, 3).
    outcomes : np.ndarray
        Array 1D di risultati ('H', 'D', 'A').

    Restituisce
    -----------
    np.ndarray
        Array 1D float64 di forma (N,) contenente ln(p) - ln(q).
    """
    ll_p = compute_log_loss(p_model, outcomes)
    ll_q = compute_log_loss(q_market, outcomes)
    return ll_q - ll_p


def compute_g_hat(
    p_model: np.ndarray, q_market: np.ndarray, outcomes: np.ndarray
) -> float:
    """Calcola l'edge empirico g_hat medio col segno: LL(q) - LL(p).

    Parametri
    ---------
    p_model : np.ndarray
        Probabilità del modello di forma (N, 3).
    q_market : np.ndarray
        Probabilità de-viggati del mercato di forma (N, 3).
    outcomes : np.ndarray
        Array 1D di risultati ('H', 'D', 'A').

    Restituisce
    -----------
    float
        Media aritmetica di g_hat su tutte le partite.
    """
    terms = compute_g_hat_terms(p_model, q_market, outcomes)
    if len(terms) == 0:
        raise ValueError("Cannot compute g_hat of empty array")
    return float(np.mean(terms))


def compute_cumulative_g_hat(terms: np.ndarray) -> np.ndarray:
    """Calcola la serie delle medie cumulative g_hat_cum, t = (1/t) sum_{i=1}^t g_i.

    Parametri
    ---------
    terms : np.ndarray
        Array 1D di termini g_i in ordine cronologico.

    Restituisce
    -----------
    np.ndarray
        Array 1D float64 di medie cumulative di lunghezza T.
    """
    if not isinstance(terms, np.ndarray):
        raise TypeError(f"terms must be a numpy.ndarray, got {type(terms).__name__}")
    if terms.dtype == bool or not (
        np.issubdtype(terms.dtype, np.integer) or np.issubdtype(terms.dtype, np.floating)
    ):
        raise TypeError(f"terms must have a real numeric dtype, got {terms.dtype}")
    if terms.ndim != 1:
        raise ValueError(f"terms must be a 1D array, got shape {terms.shape}")
    if len(terms) == 0:
        raise ValueError("terms cannot be empty")

    t_arr = np.arange(1, len(terms) + 1, dtype=np.float64)
    return np.cumsum(terms.astype(np.float64, copy=False)) / t_arr


def generate_validation_predictions(
    df: pd.DataFrame,
    fits: dict[str, EloFitParams],
    schedule: dict[str, dict[str, list[str]]],
) -> pd.DataFrame:
    """Genera le previsioni walk-forward di validazione per ciascun fit da ELO_FITS.

    Parametri
    ---------
    df : pd.DataFrame
        DataFrame completo contenente storia, training e validazione ordinato per Date.
    fits : dict[str, EloFitParams]
        Dizionario dei parametri congelati dei fit.
    schedule : dict[str, dict[str, list[str]]]
        Schema dei fit derivato da derive_fit_schedule.

    Restituisce
    -----------
    pd.DataFrame
        DataFrame contenente tutte le partite di validazione previste dal rispettivo fit.
    """
    for col in MATCH_KEYS:
        if col not in df.columns:
            raise ValueError(f"df missing required key column '{col}'")

    val_seasons_all = []
    for fit_key, entry in schedule.items():
        val_seasons_all.extend(entry["validation"])

    unique_val_seasons = set(val_seasons_all)
    if len(unique_val_seasons) != len(val_seasons_all):
        raise ValueError("Validation seasons are duplicated across fits in schedule")

    preds_list: list[pd.DataFrame] = []
    for fit_through, params in fits.items():
        if fit_through not in schedule:
            raise ValueError(f"Fit '{fit_through}' not found in schedule")
        val_seasons = schedule[fit_through]["validation"]
        if not val_seasons:
            continue
        sub_preds = predict_elo_fast(
            df, val_seasons, k=params.k, h=params.h, nu=params.nu
        )
        preds_list.append(sub_preds)

    if not preds_list:
        raise ValueError("No validation predictions were generated")

    df_preds = pd.concat(preds_list, ignore_index=True)

    # Controllo che ogni stagione di validazione compaia una sola volta
    seen_seasons = list(df_preds["season"].unique())
    if set(seen_seasons) != unique_val_seasons:
        raise ValueError(
            f"Mismatch between predicted validation seasons ({set(seen_seasons)}) "
            f"and expected ({unique_val_seasons})"
        )

    # Controllo che per ogni stagione di validazione il numero di partite coincida con df
    for s in seen_seasons:
        n_pred = int((df_preds["season"] == s).sum())
        n_raw = int((df["season"] == s).sum())
        if n_pred != n_raw:
            raise ValueError(
                f"Match count mismatch for validation season '{s}': {n_pred} vs {n_raw}"
            )

    # Ordinamento cronologico stabile per Date
    df_preds = df_preds.sort_values("Date", kind="stable").reset_index(drop=True)
    return df_preds


def align_predictions_with_odds(
    df_preds: pd.DataFrame,
    df_raw: pd.DataFrame,
) -> pd.DataFrame:
    """Abbina le previsioni del modello alle righe originali sulle chiavi di partita.

    Parametri
    ---------
    df_preds : pd.DataFrame
        Previsioni di validazione restituite da generate_validation_predictions.
    df_raw : pd.DataFrame
        DataFrame grezzo o consolidato contenente quote e FTR.

    Restituisce
    -----------
    pd.DataFrame
        DataFrame unito e ordinato cronologicamente, privo di duplicati.
    """
    for col in MATCH_KEYS:
        if col not in df_preds.columns:
            raise ValueError(f"df_preds missing required key column '{col}'")
        if col not in df_raw.columns:
            raise ValueError(f"df_raw missing required key column '{col}'")

    if df_preds.duplicated(subset=list(MATCH_KEYS)).any():
        raise ValueError("df_preds contains duplicate match keys")
    if df_raw.duplicated(subset=list(MATCH_KEYS)).any():
        raise ValueError("df_raw contains duplicate match keys")

    raw_cols = [c for c in df_raw.columns if c not in df_preds.columns or c in MATCH_KEYS]
    merged = pd.merge(
        df_preds,
        df_raw[raw_cols],
        on=list(MATCH_KEYS),
        how="inner",
    )

    if len(merged) != len(df_preds):
        raise ValueError(
            f"Merge row count mismatch: {len(merged)} matches aligned out of {len(df_preds)} predictions"
        )

    merged = merged.sort_values("Date", kind="stable").reset_index(drop=True)
    return merged


class SeriesEvaluationData(NamedTuple):
    """Dati di valutazione per una serie di quote e i tre metodi di de-vigging."""

    series: str
    seasons: list[str]
    matches_total: int
    matches_used: int
    missing_odds: int
    invalid_odds: int
    additive_inapplicable: int
    matches_excluded: int
    df_used: pd.DataFrame
    p_model: np.ndarray
    q_proportional: np.ndarray
    q_additive: np.ndarray
    q_power: np.ndarray
    outcomes: np.ndarray


def prepare_series_evaluation(
    df_aligned: pd.DataFrame,
    series: str,
    schedule: dict[str, dict[str, list[str]]],
) -> SeriesEvaluationData:
    """Estrae le quote H, D, A, applica le esclusioni e calcola q dei tre metodi.

    Parametri
    ---------
    df_aligned : pd.DataFrame
        DataFrame delle previsioni allineate alle quote originali.
    series : str
        Identificativo della serie: 'b365_prematch' o 'pinnacle_closing'.
    schedule : dict[str, dict[str, list[str]]]
        Schema dei fit derivato da derive_fit_schedule.

    Restituisce
    -----------
    SeriesEvaluationData
        Tupla con conteggi di esclusione, DataFrame filtrato, probabilità p e matrici q.
    """
    if series == "b365_prematch":
        odds_cols = ("B365H", "B365D", "B365A")
        val_seasons_all = []
        for entry in schedule.values():
            val_seasons_all.extend(entry["validation"])
        target_seasons = sorted(val_seasons_all, key=parse_season_start_year)
    elif series == "pinnacle_closing":
        odds_cols = ("PSCH", "PSCD", "PSCA")
        val_seasons_all = []
        for entry in schedule.values():
            val_seasons_all.extend(entry["validation"])
        target_seasons = sorted(
            [s for s in val_seasons_all if parse_season_start_year(s) >= PINNACLE_START_YEAR],
            key=parse_season_start_year,
        )
    else:
        raise ValueError(f"Unknown series '{series}', expected one of {SERIES_NAMES}")

    for c in odds_cols:
        if c not in df_aligned.columns:
            raise ValueError(f"Column '{c}' not found in aligned DataFrame")
    if "FTR" not in df_aligned.columns:
        raise ValueError("Column 'FTR' not found in aligned DataFrame")

    df_series = df_aligned[df_aligned["season"].isin(target_seasons)].copy()
    df_series = df_series.sort_values("Date", kind="stable").reset_index(drop=True)
    matches_total = len(df_series)

    # Conversione numerica
    odds_raw = df_series[list(odds_cols)].apply(pd.to_numeric, errors="coerce")

    # Gerarchia delle esclusioni:
    # 1. Quota mancante
    missing_mask = df_series[list(odds_cols)].isna().any(axis=1)

    # 2. Quota non valida (tra le non mancanti)
    invalid_mask = (~missing_mask) & (
        odds_raw.isna().any(axis=1)
        | (odds_raw <= 1.0).any(axis=1)
        | (~np.isfinite(odds_raw)).any(axis=1)
    )

    valid_odds_mask = (~missing_mask) & (~invalid_mask)

    # 3. Additivo non applicabile (tra le valide in 1 e 2)
    additive_inapplicable_mask = pd.Series(False, index=df_series.index)
    if valid_odds_mask.any():
        valid_odds_arr = odds_raw.loc[valid_odds_mask].to_numpy(dtype=np.float64)
        q_add_candidate = devig_additive(valid_odds_arr)
        has_nan = np.isnan(q_add_candidate).any(axis=1)
        additive_inapplicable_mask.loc[valid_odds_mask] = has_nan

    used_mask = valid_odds_mask & (~additive_inapplicable_mask)

    missing_count = int(missing_mask.sum())
    invalid_count = int(invalid_mask.sum())
    additive_count = int(additive_inapplicable_mask.sum())
    excluded_count = missing_count + invalid_count + additive_count
    used_count = int(used_mask.sum())

    if used_count + excluded_count != matches_total:
        raise RuntimeError("Inconsistent partition between used and excluded matches")

    df_used = df_series.loc[used_mask].copy().reset_index(drop=True)
    odds_used = odds_raw.loc[used_mask].to_numpy(dtype=np.float64)

    # Calcolo q per i tre metodi sullo stesso insieme di partite
    q_prop = devig_proportional(odds_used)
    q_add = devig_additive(odds_used)
    q_pow, _ = devig_power(odds_used)

    p_model = df_used[["p_home", "p_draw", "p_away"]].to_numpy(dtype=np.float64)
    outcomes = df_used["FTR"].astype(str).str.strip().to_numpy()

    # Validazione di conformità
    _validate_probs(p_model)
    _validate_probs(q_prop)
    _validate_probs(q_add)
    _validate_probs(q_pow)
    _validate_outcomes(outcomes, len(df_used))

    return SeriesEvaluationData(
        series=series,
        seasons=target_seasons,
        matches_total=matches_total,
        matches_used=used_count,
        missing_odds=missing_count,
        invalid_odds=invalid_count,
        additive_inapplicable=additive_count,
        matches_excluded=excluded_count,
        df_used=df_used,
        p_model=p_model,
        q_proportional=q_prop,
        q_additive=q_add,
        q_power=q_pow,
        outcomes=outcomes,
    )
