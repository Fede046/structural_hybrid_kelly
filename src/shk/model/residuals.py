"""Modulo per il calcolo delle serie dei residui (log-loss per partita) del Modulo 1.

Fornisce la funzione compute_model_residuals che restituisce la log-loss per partita
delle previsioni walk-forward Elo del Modulo 1 raw, sia per le partite di training
di ciascun fit congelato sia per le rispettive stagioni di validazione assegnate.
"""

from collections.abc import Collection
from typing import Final

import numpy as np
import pandas as pd

from shk.model.elo_fit import (
    ELO_FITS,
    EloFitParams,
    compute_training_log_loss,
    parse_season_start_year,
)
from shk.model.scoring import (
    MATCH_KEYS,
    align_predictions_with_odds,
    compute_log_loss,
    generate_validation_predictions,
)

# Colonne richieste nel DataFrame di input
REQUIRED_INPUT_COLUMNS: Final[frozenset[str]] = frozenset(
    {"season", "Date", "HomeTeam", "AwayTeam", "FTR", "FTHG", "FTAG"}
)

# Schema esatto delle 11 colonne restituite
RESIDUALS_COLUMNS: Final[tuple[str, ...]] = (
    "fit_through",
    "role",
    "season",
    "Date",
    "HomeTeam",
    "AwayTeam",
    "p_home",
    "p_draw",
    "p_away",
    "FTR",
    "log_loss",
)


def _validate_inputs(
    df: pd.DataFrame,
    schedule: dict[str, dict[str, list[str]]],
    fits: dict[str, EloFitParams],
) -> None:
    """Valida difensivamente gli input di compute_model_residuals."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"df must be a pandas DataFrame, got {type(df).__name__}")
    if isinstance(schedule, (str, bytes)) or not isinstance(schedule, dict):
        raise TypeError(f"schedule must be a dict, got {type(schedule).__name__}")
    if isinstance(fits, (str, bytes)) or not isinstance(fits, dict):
        raise TypeError(f"fits must be a dict, got {type(fits).__name__}")

    if df.empty:
        raise ValueError("df cannot be empty")

    missing_cols = REQUIRED_INPUT_COLUMNS - set(df.columns)
    if missing_cols:
        raise ValueError(f"df is missing required columns: {sorted(missing_cols)}")

    # Verifica monotonicità non decrescente delle date
    if not df["Date"].is_monotonic_increasing:
        raise ValueError("df['Date'] must be monotonically non-decreasing")

    if not schedule:
        raise ValueError("schedule cannot be empty")

    for fit_key, entry in schedule.items():
        if fit_key not in fits:
            raise ValueError(f"Fit '{fit_key}' in schedule is not present in fits")
        if not isinstance(entry, dict):
            raise TypeError(f"Schedule entry for '{fit_key}' must be a dict")
        if "training" not in entry or "validation" not in entry:
            raise ValueError(
                f"Schedule entry for '{fit_key}' must contain 'training' and 'validation' keys"
            )
        if not isinstance(entry["training"], Collection) or isinstance(entry["training"], (str, bytes)):
            raise TypeError(f"'training' in schedule['{fit_key}'] must be a non-string Collection")
        if not isinstance(entry["validation"], Collection) or isinstance(entry["validation"], (str, bytes)):
            raise TypeError(f"'validation' in schedule['{fit_key}'] must be a non-string Collection")


def compute_model_residuals(
    df: pd.DataFrame,
    schedule: dict[str, dict[str, list[str]]],
    fits: dict[str, EloFitParams] | None = None,
) -> pd.DataFrame:
    """Calcola la serie di log-loss per partita del Modulo 1 raw su training e validazione.

    Per ciascun fit temporale, calcola le previsioni walk-forward e la relativa log-loss
    puntuale con logaritmo naturale per tutte le partite delle stagioni di training
    (tramite compute_training_log_loss) e per le stagioni di validazione assegnate
    (tramite generate_validation_predictions).

    Parametri
    ---------
    df : pd.DataFrame
        DataFrame consolidato contenente storia, training e validazione ordinato
        per Date in modo non decrescente, con colonne identificative, quote ed esiti.
    schedule : dict[str, dict[str, list[str]]]
        Schema dei fit con le stagioni di training e di validazione per ciascun fit.
    fits : dict[str, EloFitParams] o None, opzionale
        Dizionario dei parametri congelati dei fit. Se None, utilizza ELO_FITS.

    Restituisce
    -----------
    pd.DataFrame
        DataFrame contenente le 11 colonne prescritte ordinate per fit_through
        cronologico, ruolo ('training' poi 'validation') e data stabile:
        fit_through, role, season, Date, HomeTeam, AwayTeam, p_home, p_draw,
        p_away, FTR, log_loss.

    Solleva
    -------
    TypeError
        Se i tipi degli argomenti non sono conformi.
    ValueError
        Se df è vuoto, privo delle colonne richieste, non ordinato per Date,
        oppure se schedule contiene fit non presenti in fits.
    """
    effective_fits = ELO_FITS if fits is None else fits
    _validate_inputs(df, schedule, effective_fits)

    date_dtype = df["Date"].dtype
    ordered_fits = sorted(schedule.keys(), key=parse_season_start_year)

    # 1. Previsioni di validazione complessive
    val_season_to_fit: dict[str, str] = {}
    has_any_validation = False
    for fit_key in ordered_fits:
        val_seasons = list(schedule[fit_key]["validation"])
        if val_seasons:
            has_any_validation = True
            for s in val_seasons:
                val_season_to_fit[s] = fit_key

    df_val_aligned: pd.DataFrame | None = None
    if has_any_validation:
        df_val_preds = generate_validation_predictions(df, effective_fits, schedule)
        aligned_v = align_predictions_with_odds(df_val_preds, df).copy()
        fit_col = aligned_v["season"].map(val_season_to_fit)
        role_col = pd.Series(["validation"] * len(aligned_v), index=aligned_v.index, dtype=object)
        df_val_aligned = aligned_v.assign(fit_through=fit_col, role=role_col)

    # 2. Generazione blocchi ordinati per fit (training prima, poi validazione)
    blocks: list[pd.DataFrame] = []

    for fit_through in ordered_fits:
        params = effective_fits[fit_through]
        train_seasons = list(schedule[fit_through]["training"])

        # Blocco training
        if train_seasons:
            j_year = parse_season_start_year(fit_through)
            season_years = df["season"].map(parse_season_start_year)
            df_sub = df[season_years <= j_year].copy().reset_index(drop=True)
            df_gt = df_sub[df_sub["season"].isin(train_seasons)].copy().reset_index(drop=True)

            _, preds_train = compute_training_log_loss(
                df_sub,
                train_seasons,
                k=params.k,
                h=params.h,
                nu=params.nu,
                df_ground_truth=df_gt,
            )

            aligned_t = align_predictions_with_odds(preds_train, df).copy()
            fit_t = pd.Series([fit_through] * len(aligned_t), index=aligned_t.index, dtype=object)
            role_t = pd.Series(["training"] * len(aligned_t), index=aligned_t.index, dtype=object)
            train_aligned = aligned_t.assign(fit_through=fit_t, role=role_t)
            train_aligned = train_aligned.sort_values("Date", kind="stable").reset_index(drop=True)
            blocks.append(train_aligned)

        # Blocco validazione per questo fit
        if df_val_aligned is not None:
            sub_val = df_val_aligned[df_val_aligned["fit_through"] == fit_through].copy()
            if not sub_val.empty:
                sub_val = sub_val.sort_values("Date", kind="stable").reset_index(drop=True)
                blocks.append(sub_val)

    if not blocks:
        raise ValueError("No matches generated for the provided schedule")

    df_combined = pd.concat(blocks, ignore_index=True).copy()

    # 3. Calcolo log-loss puntuale con compute_log_loss
    probs = df_combined[["p_home", "p_draw", "p_away"]].to_numpy(dtype=np.float64)
    outcomes = df_combined["FTR"].to_numpy()
    loss_series = pd.Series(compute_log_loss(probs, outcomes), index=df_combined.index, dtype=np.float64)
    df_combined = df_combined.assign(log_loss=loss_series)

    # 4. Conservazione rigorosa del dtype originario di Date
    df_combined["Date"] = df_combined["Date"].astype(date_dtype)

    # 5. Selezione e ordinamento esatto delle 11 colonne richieste
    return df_combined[list(RESIDUALS_COLUMNS)].copy()
