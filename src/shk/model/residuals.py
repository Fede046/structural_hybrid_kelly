"""Modulo per il calcolo delle serie dei residui (log-loss per partita) del Modulo 1.

Fornisce la funzione compute_model_residuals che restituisce la log-loss per partita
delle previsioni walk-forward del Modulo 1 raw, sia per le partite di training
di ciascun fit congelato sia per le rispettive stagioni di validazione assegnate.

Fornisce anche load_model_residuals, la catena comune sui dati reali (split, caricamento
per ruolo, schema dei fit, residui) che script e test nuovi usano al posto di copiarla,
e load_match_frame, la sua prima parte (DataFrame delle partite e schema dei fit).

Il Modulo 1 è un parametro (T60, shk.model.module1): "elo" (ELO_FITS, percorso invariato)
oppure "dixon_coles" (DC_FITS, T59). Le colonne restituite sono le stesse per entrambi.
Con Dixon-Coles le previsioni di training e di validazione si calcolano sul DataFrame
completo, come nella calibrazione di T59: la storia usata a ogni data è comunque solo
quella con Date strettamente anteriore.
"""

from collections.abc import Collection
from pathlib import Path
from typing import Final, NamedTuple

import numpy as np
import pandas as pd

from shk.data.loading import DEFAULT_DATA_DIR
from shk.data.split import DEFAULT_SPLIT_CONFIG_PATH, load_by_role, read_split_config
from shk.model.elo_fit import (
    ELO_FITS,
    EloFitParams,
    compute_training_log_loss,
    derive_fit_schedule,
    parse_season_start_year,
)
from shk.model.module1 import MODULE1_ELO, check_module1
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


# Gol attesi delle previsioni Dixon-Coles (λ di casa e μ in trasferta), conservati a parte (T61)
RATE_COLUMNS: Final[tuple[str, ...]] = ("lambda_home", "lambda_away")


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


def _dixon_coles_predictions(df: pd.DataFrame, params, seasons: list[str]) -> pd.DataFrame:
    """Previsioni walk-forward Dixon-Coles delle stagioni con (ξ, σ) del fit, sul DataFrame completo."""
    # Import locale: dixon_coles importa module2_data, che importa questo modulo
    from shk.model.dixon_coles import DixonColesForecaster

    forecaster = DixonColesForecaster(df, params.xi, params.sigma)
    return pd.concat([forecaster.predict_season(s) for s in seasons], ignore_index=True)


def _dixon_coles_validation_predictions(
    df: pd.DataFrame, fits: dict, schedule: dict[str, dict[str, list[str]]]
) -> pd.DataFrame:
    """Previsioni Dixon-Coles di tutte le stagioni di validazione, ciascuna con il suo fit."""
    frames = [
        _dixon_coles_predictions(df, fits[fit_key], list(entry["validation"]))
        for fit_key, entry in sorted(schedule.items(), key=lambda kv: parse_season_start_year(kv[0]))
        if entry["validation"]
    ]
    if not frames:
        raise ValueError("No validation predictions were generated")
    return pd.concat(frames, ignore_index=True).sort_values("Date", kind="stable").reset_index(drop=True)


def default_fits(module1: str) -> dict:
    """Parametri congelati del Modulo 1: ELO_FITS oppure DC_FITS."""
    if check_module1(module1) == MODULE1_ELO:
        return ELO_FITS
    from shk.model.dixon_coles import DC_FITS

    return DC_FITS


def _model_residuals_frame(
    df: pd.DataFrame,
    schedule: dict[str, dict[str, list[str]]],
    fits: dict | None,
    module1: str,
) -> pd.DataFrame:
    """Corpo di compute_model_residuals: tutte le colonne, comprese quelle in più delle previsioni
    (per Dixon-Coles i gol attesi di RATE_COLUMNS)."""
    is_elo = check_module1(module1) == MODULE1_ELO
    effective_fits = default_fits(module1) if fits is None else fits
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
        if is_elo:
            df_val_preds = generate_validation_predictions(df, effective_fits, schedule)
        else:
            df_val_preds = _dixon_coles_validation_predictions(df, effective_fits, schedule)
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
            if is_elo:
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
            else:
                preds_train = _dixon_coles_predictions(df, params, train_seasons)

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

    return df_combined


def compute_model_residuals(
    df: pd.DataFrame,
    schedule: dict[str, dict[str, list[str]]],
    fits: dict[str, EloFitParams] | None = None,
    module1: str = MODULE1_ELO,
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
    fits : dict o None, opzionale
        Dizionario dei parametri congelati dei fit. Se None, ELO_FITS per l'Elo e DC_FITS
        per Dixon-Coles.
    module1 : str, opzionale
        Identificatore del Modulo 1, "elo" (default) o "dixon_coles".

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
    # Selezione e ordinamento esatto delle 11 colonne richieste
    return _model_residuals_frame(df, schedule, fits, module1)[list(RESIDUALS_COLUMNS)].copy()


class ModelResidualsData(NamedTuple):
    """Uscita della catena comune sui dati reali.

    Attributi
    ---------
    df : pd.DataFrame
        Partite dei ruoli history, training e validation, ordinate per Date in modo stabile.
    schedule : dict[str, dict[str, list[str]]]
        Schema dei fit da derive_fit_schedule sulla configurazione dello split.
    residuals : pd.DataFrame
        Uscita di compute_model_residuals (11 colonne di RESIDUALS_COLUMNS).
    module1 : str
        Identificatore del Modulo 1 che ha prodotto i residui ("elo" di default).
    rates : pd.DataFrame o None
        Per Dixon-Coles, gol attesi (RATE_COLUMNS) delle stesse righe di residuals, con lo
        stesso indice; None per l'Elo (T61).
    """

    df: pd.DataFrame
    schedule: dict[str, dict[str, list[str]]]
    residuals: pd.DataFrame
    module1: str = MODULE1_ELO
    rates: pd.DataFrame | None = None


def model_residuals_data(
    df: pd.DataFrame,
    schedule: dict[str, dict[str, list[str]]],
    fits: dict | None = None,
    module1: str = MODULE1_ELO,
) -> ModelResidualsData:
    """Residui del Modulo 1 con DataFrame e schema dati; per Dixon-Coles anche i gol attesi."""
    full = _model_residuals_frame(df, schedule, fits, check_module1(module1))
    residuals = full[list(RESIDUALS_COLUMNS)].copy()
    rates = None if module1 == MODULE1_ELO else full[list(RATE_COLUMNS)].copy()
    return ModelResidualsData(df=df, schedule=schedule, residuals=residuals, module1=module1, rates=rates)


DEFAULT_ROLES: Final[tuple[str, ...]] = ("history", "training", "validation")


def load_match_frame(
    config_path: Path | str = DEFAULT_SPLIT_CONFIG_PATH,
    data_dir: Path | str = DEFAULT_DATA_DIR,
    roles: tuple[str, ...] = DEFAULT_ROLES,
) -> tuple[pd.DataFrame, dict[str, dict[str, list[str]]]]:
    """Prima parte della catena comune: DataFrame delle partite e schema dei fit.

    Passi: read_split_config; load_by_role per ciascun ruolo, nell'ordine dato;
    concatenazione e ordinamento stabile per Date; derive_fit_schedule. Di default il
    ruolo test non si carica.

    Parametri
    ---------
    config_path : Path o str, opzionale
        File di configurazione dello split (default: DEFAULT_SPLIT_CONFIG_PATH).
    data_dir : Path o str, opzionale
        Directory dei CSV E0 (default: DEFAULT_DATA_DIR).
    roles : tuple[str, ...], opzionale
        Ruoli da caricare (default: history, training, validation).

    Restituisce
    -----------
    tuple[pd.DataFrame, dict[str, dict[str, list[str]]]]
        DataFrame ordinato per Date e schema dei fit.
    """
    cfg = read_split_config(config_path)
    frames = [load_by_role(role, config_path=config_path, data_dir=data_dir) for role in roles]
    df = pd.concat(frames, ignore_index=True)
    df = df.sort_values("Date", kind="stable").reset_index(drop=True)
    return df, derive_fit_schedule(cfg)


def load_model_residuals(
    config_path: Path | str = DEFAULT_SPLIT_CONFIG_PATH,
    data_dir: Path | str = DEFAULT_DATA_DIR,
    fits: dict | None = None,
    module1: str = MODULE1_ELO,
) -> ModelResidualsData:
    """Catena comune sui dati reali, per script e test nuovi (decisione del 2026-10-11; T60).

    Passi, gli stessi degli script di C5 e C6: load_match_frame (read_split_config;
    load_by_role per history, training e validation; concatenazione e ordinamento stabile
    per Date; derive_fit_schedule); compute_model_residuals con il Modulo 1 dato. Il ruolo
    test non si carica.

    Parametri
    ---------
    config_path : Path o str, opzionale
        File di configurazione dello split (default: DEFAULT_SPLIT_CONFIG_PATH).
    data_dir : Path o str, opzionale
        Directory dei CSV E0 (default: DEFAULT_DATA_DIR).
    fits : dict o None, opzionale
        Parametri dei fit; se None, ELO_FITS o DC_FITS secondo il Modulo 1.
    module1 : str, opzionale
        Identificatore del Modulo 1, "elo" (default) o "dixon_coles".

    Restituisce
    -----------
    ModelResidualsData
        DataFrame delle partite, schema dei fit, residui, Modulo 1 e, per Dixon-Coles, gol attesi.

    Solleva
    -------
    TypeError, ValueError, FileNotFoundError
        Come read_split_config, load_by_role e compute_model_residuals.
    """
    df, schedule = load_match_frame(config_path, data_dir)
    return model_residuals_data(df, schedule, fits, module1)
