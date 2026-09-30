"""Modulo di monitoraggio e generazione record per i drift detector (Task 28 / US-C5.1).

Fornisce la NamedTuple ScenarioSeries per rappresentare le serie temporali di log-loss
dei 22 scenari (3 di training e 19 di validazione), la funzione di estrazione delle serie
dai residui del Modulo 1 e la funzione di generazione dei record per il file CSV.
"""

from collections.abc import Collection
from typing import Final, NamedTuple

import numpy as np
import pandas as pd

from shk.model.elo_fit import parse_season_start_year
from shk.stats.drift import detector_params, run_drift_detector

# Schema delle 12 colonne in snake_case prescritte per il CSV dei detector
DRIFT_DETECTOR_CSV_COLUMNS: Final[tuple[str, ...]] = (
    "row_type",
    "season",
    "role",
    "fit_through",
    "detector",
    "alarm_number",
    "match_index",
    "matchday",
    "date",
    "home_team",
    "away_team",
    "n_alarms",
)

# Numero atteso di partite per stagione
EXPECTED_MATCHES_PER_SEASON: Final[int] = 380


class ScenarioSeries(NamedTuple):
    """Serie temporale di log-loss per una singola stagione di scenario."""

    season: str
    role: str
    fit_through: str
    log_loss: np.ndarray
    date: tuple[str, ...]
    home_team: tuple[str, ...]
    away_team: tuple[str, ...]


def extract_scenario_series(
    df_residuals: pd.DataFrame,
    schedule: dict[str, dict[str, list[str]]],
    expected_matches: int = EXPECTED_MATCHES_PER_SEASON,
) -> list[ScenarioSeries]:
    """Estrae le 22 serie temporali di log-loss in ordine cronologico di stagione.

    Per ciascuno dei 3 scenari di training (2000-01, 2010-11, 2020-21) seleziona le partite
    della singola stagione dal fit corrispondente. Per ciascuna delle 19 stagioni di
    validazione seleziona le partite previste dal rispettivo fit.
    Tutte le 22 serie vengono restituite in ordine cronologico di stagione, ciascuna
    ordinata stabilmente per data.

    Parametri
    ---------
    df_residuals : pd.DataFrame
        DataFrame dei residui prodotto da compute_model_residuals.
    schedule : dict[str, dict[str, list[str]]]
        Schema dei fit con training e validazione.
    expected_matches : int, opzionale
        Numero atteso di partite per stagione (default 380). Se diverso, solleva ValueError.

    Restituisce
    -----------
    list[ScenarioSeries]
        Lista delle 22 serie ordinate cronologicamente per stagione.

    Solleva
    -------
    TypeError
        Se df_residuals o schedule non sono del tipo atteso.
    ValueError
        Se mancano colonne richieste, se le date non sono ordinate o se una serie
        non contiene esattamente il numero atteso di partite.
    """
    if not isinstance(df_residuals, pd.DataFrame):
        raise TypeError(f"df_residuals must be a pd.DataFrame, got {type(df_residuals).__name__}")
    if not isinstance(schedule, dict):
        raise TypeError(f"schedule must be a dict, got {type(schedule).__name__}")

    required_cols = {"season", "Date", "HomeTeam", "AwayTeam", "fit_through", "role", "log_loss"}
    missing = required_cols - set(df_residuals.columns)
    if missing:
        raise ValueError(f"df_residuals missing required columns: {sorted(missing)}")

    raw_series_list: list[ScenarioSeries] = []

    # 1. Scenari di training: 2000-01, 2010-11, 2020-21
    # Per ciascuno, si prendono le sole partite di quella stagione appartenenti al fit che termina in quella stagione
    train_fits = sorted(schedule.keys(), key=parse_season_start_year)
    for fit_k in train_fits:
        sub = df_residuals[
            (df_residuals["role"] == "training")
            & (df_residuals["fit_through"] == fit_k)
            & (df_residuals["season"] == fit_k)
        ].copy()

        if len(sub) != expected_matches:
            raise ValueError(
                f"Training scenario series for season '{fit_k}' has {len(sub)} matches, "
                f"expected {expected_matches}"
            )

        sub = sub.sort_values("Date", kind="stable").reset_index(drop=True)
        dates_iso = tuple(pd.Timestamp(d).strftime("%Y-%m-%d") for d in sub["Date"])
        h_teams = tuple(str(t) for t in sub["HomeTeam"])
        a_teams = tuple(str(t) for t in sub["AwayTeam"])
        losses = sub["log_loss"].to_numpy(dtype=np.float64)

        raw_series_list.append(
            ScenarioSeries(
                season=fit_k,
                role="training",
                fit_through=fit_k,
                log_loss=losses,
                date=dates_iso,
                home_team=h_teams,
                away_team=a_teams,
            )
        )

    # 2. Scenari di validazione: le 19 stagioni previste dai rispettivi fit
    all_val_seasons: list[tuple[str, str]] = []
    for fit_k in train_fits:
        for val_s in schedule[fit_k]["validation"]:
            all_val_seasons.append((val_s, fit_k))

    for val_s, fit_k in all_val_seasons:
        sub = df_residuals[
            (df_residuals["role"] == "validation")
            & (df_residuals["season"] == val_s)
            & (df_residuals["fit_through"] == fit_k)
        ].copy()

        if len(sub) != expected_matches:
            raise ValueError(
                f"Validation scenario series for season '{val_s}' has {len(sub)} matches, "
                f"expected {expected_matches}"
            )

        sub = sub.sort_values("Date", kind="stable").reset_index(drop=True)
        dates_iso = tuple(pd.Timestamp(d).strftime("%Y-%m-%d") for d in sub["Date"])
        h_teams = tuple(str(t) for t in sub["HomeTeam"])
        a_teams = tuple(str(t) for t in sub["AwayTeam"])
        losses = sub["log_loss"].to_numpy(dtype=np.float64)

        raw_series_list.append(
            ScenarioSeries(
                season=val_s,
                role="validation",
                fit_through=fit_k,
                log_loss=losses,
                date=dates_iso,
                home_team=h_teams,
                away_team=a_teams,
            )
        )

    # 3. Ordinamento cronologico complessivo delle 22 serie per anno di inizio stagione
    return sorted(raw_series_list, key=lambda s: parse_season_start_year(s.season))


def build_drift_records(
    series_list: Collection[ScenarioSeries],
    detectors: tuple[str, ...] = ("adwin", "page_hinkley"),
) -> list[dict[str, str | int]]:
    """Esegue i detector tarati su ciascuna serie e produce le righe 'alarm' e 'summary'.

    Parametri
    ---------
    series_list : Collection[ScenarioSeries]
        Collezione delle serie di scenario su cui eseguire il monitoraggio.
    detectors : tuple[str, ...], opzionale
        Tupla dei nomi dei detector da eseguire (default 'adwin', 'page_hinkley').

    Restituisce
    -----------
    list[dict[str, str | int]]
        Lista di dizionari conformi alle colonne di DRIFT_DETECTOR_CSV_COLUMNS.
    """
    records: list[dict[str, str | int]] = []

    for series in series_list:
        for det_name in detectors:
            params = detector_params(det_name)
            alarm_indices = run_drift_detector(series.log_loss, det_name, params)

            # Righe di allarme (una per ciascun allarme rilevato)
            for alarm_no, idx in enumerate(alarm_indices, start=1):
                idx_int = int(idx)
                records.append({
                    "row_type": "alarm",
                    "season": series.season,
                    "role": series.role,
                    "fit_through": series.fit_through,
                    "detector": det_name,
                    "alarm_number": alarm_no,
                    "match_index": idx_int,
                    "matchday": idx_int // 10 + 1,
                    "date": series.date[idx_int],
                    "home_team": series.home_team[idx_int],
                    "away_team": series.away_team[idx_int],
                    "n_alarms": "",
                })

            # Riga di riepilogo per la stagione e il detector (sempre presente)
            records.append({
                "row_type": "summary",
                "season": series.season,
                "role": series.role,
                "fit_through": series.fit_through,
                "detector": det_name,
                "alarm_number": "",
                "match_index": "",
                "matchday": "",
                "date": "",
                "home_team": "",
                "away_team": "",
                "n_alarms": int(len(alarm_indices)),
            })

    return records


def generate_drift_detector_records(
    df_residuals: pd.DataFrame,
    schedule: dict[str, dict[str, list[str]]],
    expected_matches: int = EXPECTED_MATCHES_PER_SEASON,
) -> list[dict[str, str | int]]:
    """Estrae le serie di scenario dai residui e produce i record completi per il CSV."""
    series_list = extract_scenario_series(df_residuals, schedule, expected_matches=expected_matches)
    return build_drift_records(series_list)
