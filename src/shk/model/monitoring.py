"""Modulo di monitoraggio e generazione record per i drift detector (Task 28 / US-C5.1).

Fornisce la NamedTuple ScenarioSeries per rappresentare le serie temporali di log-loss
dei 22 scenari (3 di training e 19 di validazione), la funzione di estrazione delle serie
dai residui del Modulo 1 e la funzione di generazione dei record per il file CSV.
"""

from collections.abc import Collection, Mapping
from typing import Final, NamedTuple

import numpy as np
import pandas as pd
from scipy.stats import norm

from shk.model.elo_fit import parse_season_start_year
from shk.stats.drift import (
    MATCHDAY_SIZE,
    N_VERIFICATION_RESAMPLES,
    SEED_C5,
    calibrate_matchday_z_threshold,
    compute_matchday_z_scores,
    detector_params,
    run_drift_detector,
    spawn_c5_generators,
    verify_matchday_z_thresholds,
)
from shk.stats.false_rejection import ALPHA, BLOCK_LENGTHS, N_BOOT

# Schema delle 12 colonne in snake_case prescritte per il CSV dei detector (C5.1)
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

# Schema delle 14 colonne in snake_case prescritte per il CSV dello Z-test (C5.2 e C5.3)
DAILY_Z_TEST_CSV_COLUMNS: Final[tuple[str, ...]] = (
    "row_type",
    "season",
    "fit_through",
    "method",
    "block_length",
    "threshold",
    "matchday",
    "z",
    "alarm",
    "n_alarms",
    "expected_alarms",
    "mean_alarms",
    "n_resamples",
    "exceedance_rate",
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


class TrainingBaselineStats(NamedTuple):
    """Statistiche di baseline calcolate sulle partite di training di un fit."""

    fit_through: str
    n_matches: int
    mu: float
    sigma: float


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


def compute_training_baseline_stats(
    df_residuals: pd.DataFrame,
    schedule: dict[str, dict[str, list[str]]] | None = None,
) -> dict[str, TrainingBaselineStats]:
    """Calcola mu e sigma (ddof=1) per ciascun fit sulle rispettive partite di training.

    Parametri
    ---------
    df_residuals : pd.DataFrame
        DataFrame dei residui prodotto da compute_model_residuals, contenente almeno
        le colonne 'role', 'fit_through' e 'log_loss'.
    schedule : dict[str, dict[str, list[str]]] | None, opzionale
        Schema dei fit da cui estrarre i nomi dei fit di training. Se None, i fit
        vengono ricavati dai valori unici della colonna 'fit_through' con role == 'training'.

    Restituisce
    -----------
    dict[str, TrainingBaselineStats]
        Dizionario mappante il nome del fit (es. '2000-01') alle sue statistiche
        di baseline (fit_through, n_matches, mu, sigma).

    Solleva
    -------
    TypeError
        Se df_residuals non è un pd.DataFrame o schedule non è un dict / None.
    ValueError
        Se mancano colonne richieste o se per un fit ci sono meno di 2 partite di training.
    """
    if not isinstance(df_residuals, pd.DataFrame):
        raise TypeError(f"df_residuals must be a pd.DataFrame, got {type(df_residuals).__name__}")
    if schedule is not None and not isinstance(schedule, dict):
        raise TypeError(f"schedule must be a dict or None, got {type(schedule).__name__}")

    required_cols = {"role", "fit_through", "log_loss"}
    missing = required_cols - set(df_residuals.columns)
    if missing:
        raise ValueError(f"df_residuals missing required columns: {sorted(missing)}")

    if schedule is not None:
        fit_keys = sorted(schedule.keys(), key=parse_season_start_year)
    else:
        train_fits = df_residuals[df_residuals["role"] == "training"]["fit_through"].unique()
        fit_keys = sorted(train_fits, key=parse_season_start_year)

    stats_dict: dict[str, TrainingBaselineStats] = {}
    for fit_k in fit_keys:
        sub = df_residuals[
            (df_residuals["role"] == "training")
            & (df_residuals["fit_through"] == fit_k)
        ]
        n_matches = len(sub)
        if n_matches < 2:
            raise ValueError(
                f"Fit '{fit_k}' has {n_matches} training matches, minimum required is 2"
            )

        mu_val = float(sub["log_loss"].mean())
        sigma_val = float(sub["log_loss"].std(ddof=1))
        stats_dict[fit_k] = TrainingBaselineStats(
            fit_through=fit_k,
            n_matches=n_matches,
            mu=mu_val,
            sigma=sigma_val,
        )

    return stats_dict


def build_daily_z_test_records(
    validation_series: Collection[ScenarioSeries],
    baseline_stats: Mapping[str, TrainingBaselineStats],
    alpha: float = ALPHA,
    matchday_size: int = MATCHDAY_SIZE,
    detectors: tuple[str, ...] = ("adwin", "page_hinkley"),
    training_series: Mapping[str, np.ndarray] | None = None,
    seed: int = SEED_C5,
) -> list[dict[str, str | int | float]]:
    """Costruisce le righe 'matchday', 'summary', 'overall' e 'verification' per il monitoraggio Z-test.

    Parametri
    ---------
    validation_series : Collection[ScenarioSeries]
        Serie temporali delle stagioni di validazione (es. 19 stagioni).
    baseline_stats : Mapping[str, TrainingBaselineStats]
        Mappatura fit_through -> TrainingBaselineStats calcolate sul training.
    alpha : float, opzionale
        Livello nominale di significatività (default ALPHA = 0.05).
    matchday_size : int, opzionale
        Numero di partite per giornata (default MATCHDAY_SIZE = 10).
    detectors : tuple[str, ...], opzionale
        Nomi dei detector da eseguire a confronto (default ('adwin', 'page_hinkley')).
    training_series : Mapping[str, np.ndarray] | None, opzionale
        Mappatura fit_through -> array 1D di log-loss del training per ciascun fit.
        Se presente, esegue la calibrazione e verifica per ciascuna L in BLOCK_LENGTHS
        e produce le righe 'summary' ed 'overall' per z_block_bootstrap e le righe 'verification'.
    seed : int, opzionale
        Seme master per lo spawn dei generatori di calibrazione e verifica (default SEED_C5 = 20260929).

    Restituisce
    -----------
    list[dict[str, str | int | float]]
        Lista di dizionari conformi alle colonne di DAILY_Z_TEST_CSV_COLUMNS.

    Solleva
    -------
    TypeError
        Se gli argomenti non sono dei tipi attesi.
    ValueError
        Se baseline_stats non contiene le statistiche per uno dei fit richiesti,
        o se una serie non appartiene al ruolo 'validation'.
    """
    if not isinstance(validation_series, Collection):
        raise TypeError(
            f"validation_series must be a Collection, got {type(validation_series).__name__}"
        )
    if not isinstance(baseline_stats, Mapping):
        raise TypeError(
            f"baseline_stats must be a Mapping, got {type(baseline_stats).__name__}"
        )
    if training_series is not None and not isinstance(training_series, Mapping):
        raise TypeError(
            f"training_series must be a Mapping or None, got {type(training_series).__name__}"
        )
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float, np.floating)):
        raise TypeError(f"alpha must be a float, got {type(alpha).__name__}")
    if alpha <= 0.0 or alpha >= 1.0:
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")
    if isinstance(matchday_size, bool) or not isinstance(matchday_size, (int, np.integer)):
        raise TypeError(f"matchday_size must be an integer, got {type(matchday_size).__name__}")
    if matchday_size <= 0:
        raise ValueError(f"matchday_size must be positive, got {matchday_size}")

    # Calcolo soglia nominale z_{1 - alpha/2}
    threshold = float(norm.ppf(1.0 - float(alpha) / 2.0))
    # Allarmi attesi per stagione di 38 giornate
    expected_per_season = 38.0 * float(alpha)

    # Calibrazione e verifica per block bootstrap se training_series è fornito
    calib_thresholds: dict[tuple[str, int], float] = {}
    verif_rates: dict[tuple[str, int], tuple[float, float]] = {}
    ordered_fits: list[str] = []

    if training_series is not None:
        ordered_fits = sorted(training_series.keys(), key=parse_season_start_year)
        n_fits = len(ordered_fits)
        if n_fits > 0:
            rng_matrix = spawn_c5_generators(seed=seed, n_fits=n_fits)
            for f_idx, fit_k in enumerate(ordered_fits):
                if fit_k not in baseline_stats:
                    raise ValueError(f"Missing baseline stats for training fit '{fit_k}'")
                b_stat_tr = baseline_stats[fit_k]
                tr_losses = training_series[fit_k]
                for l_idx, block_len in enumerate(BLOCK_LENGTHS):
                    calib_rng, verif_rng = rng_matrix[f_idx][l_idx]
                    c_thresh = calibrate_matchday_z_threshold(
                        training_log_loss=tr_losses,
                        mu=b_stat_tr.mu,
                        sigma=b_stat_tr.sigma,
                        block_length=block_len,
                        rng=calib_rng,
                        n_boot=N_BOOT,
                        alpha=alpha,
                        matchday_size=matchday_size,
                    )
                    calib_thresholds[(fit_k, block_len)] = c_thresh
                    c_rate, nom_rate = verify_matchday_z_thresholds(
                        training_log_loss=tr_losses,
                        mu=b_stat_tr.mu,
                        sigma=b_stat_tr.sigma,
                        block_length=block_len,
                        calibrated_threshold=c_thresh,
                        nominal_threshold=threshold,
                        rng=verif_rng,
                        n_resamples=N_VERIFICATION_RESAMPLES,
                        matchday_size=matchday_size,
                    )
                    verif_rates[(fit_k, block_len)] = (c_rate, nom_rate)

    records: list[dict[str, str | int | float]] = []

    # Tracciamento allarmi per metodo su ciascuna stagione di validazione
    method_season_alarms: dict[str, list[int]] = {
        "z_nominal": [],
        "adwin": [],
        "page_hinkley": [],
    }
    bootstrap_season_alarms: dict[int, list[int]] = {l_val: [] for l_val in BLOCK_LENGTHS}

    for s in validation_series:
        if s.role != "validation":
            raise ValueError(
                f"Expected series with role 'validation', got '{s.role}' for season '{s.season}'"
            )
        if s.fit_through not in baseline_stats:
            raise ValueError(f"Missing baseline stats for fit '{s.fit_through}'")

        b_stat = baseline_stats[s.fit_through]
        z_scores = compute_matchday_z_scores(
            s.log_loss,
            mu=b_stat.mu,
            sigma=b_stat.sigma,
            matchday_size=matchday_size,
        )

        # 1. Righe "matchday" per z_nominal
        z_alarm_count = 0
        for m_idx, z_val in enumerate(z_scores, start=1):
            alarm_flag = 1 if abs(float(z_val)) > threshold else 0
            if alarm_flag == 1:
                z_alarm_count += 1

            records.append({
                "row_type": "matchday",
                "season": s.season,
                "fit_through": s.fit_through,
                "method": "z_nominal",
                "block_length": "",
                "threshold": threshold,
                "matchday": m_idx,
                "z": float(z_val),
                "alarm": alarm_flag,
                "n_alarms": "",
                "expected_alarms": "",
                "mean_alarms": "",
                "n_resamples": "",
                "exceedance_rate": "",
            })

        method_season_alarms["z_nominal"].append(z_alarm_count)

        # 2. Righe "summary" per la stagione (z_nominal, adwin, page_hinkley)
        # 2a. z_nominal
        records.append({
            "row_type": "summary",
            "season": s.season,
            "fit_through": s.fit_through,
            "method": "z_nominal",
            "block_length": "",
            "threshold": threshold,
            "matchday": "",
            "z": "",
            "alarm": "",
            "n_alarms": z_alarm_count,
            "expected_alarms": expected_per_season,
            "mean_alarms": "",
            "n_resamples": "",
            "exceedance_rate": "",
        })

        # 2b. detectors (adwin, page_hinkley)
        for det_name in detectors:
            params = detector_params(det_name)
            alarm_indices = run_drift_detector(s.log_loss, det_name, params)
            det_count = int(len(alarm_indices))
            method_season_alarms[det_name].append(det_count)

            records.append({
                "row_type": "summary",
                "season": s.season,
                "fit_through": s.fit_through,
                "method": det_name,
                "block_length": "",
                "threshold": "",
                "matchday": "",
                "z": "",
                "alarm": "",
                "n_alarms": det_count,
                "expected_alarms": expected_per_season,
                "mean_alarms": "",
                "n_resamples": "",
                "exceedance_rate": "",
            })

        # 2c. z_block_bootstrap per ciascuna lunghezza L
        if training_series is not None:
            for block_len in BLOCK_LENGTHS:
                c_thresh = calib_thresholds[(s.fit_through, block_len)]
                boot_alarms = int(np.sum(np.abs(z_scores) > c_thresh))
                bootstrap_season_alarms[block_len].append(boot_alarms)

                records.append({
                    "row_type": "summary",
                    "season": s.season,
                    "fit_through": s.fit_through,
                    "method": "z_block_bootstrap",
                    "block_length": block_len,
                    "threshold": c_thresh,
                    "matchday": "",
                    "z": "",
                    "alarm": "",
                    "n_alarms": boot_alarms,
                    "expected_alarms": expected_per_season,
                    "mean_alarms": "",
                    "n_resamples": "",
                    "exceedance_rate": "",
                })

    # 3. Righe "overall" sulle 19 stagioni di validazione
    n_seasons = len(validation_series)
    all_methods = ("z_nominal",) + tuple(detectors)
    for method in all_methods:
        tot_alarms = sum(method_season_alarms[method])
        mean_alarms = float(tot_alarms) / float(n_seasons) if n_seasons > 0 else 0.0
        thresh_val = threshold if method == "z_nominal" else ""

        records.append({
            "row_type": "overall",
            "season": "",
            "fit_through": "",
            "method": method,
            "block_length": "",
            "threshold": thresh_val,
            "matchday": "",
            "z": "",
            "alarm": "",
            "n_alarms": tot_alarms,
            "expected_alarms": expected_per_season,
            "mean_alarms": mean_alarms,
            "n_resamples": "",
            "exceedance_rate": "",
        })

    if training_series is not None:
        for block_len in BLOCK_LENGTHS:
            tot_boot = sum(bootstrap_season_alarms[block_len])
            mean_boot = float(tot_boot) / float(n_seasons) if n_seasons > 0 else 0.0

            records.append({
                "row_type": "overall",
                "season": "",
                "fit_through": "",
                "method": "z_block_bootstrap",
                "block_length": block_len,
                "threshold": "",
                "matchday": "",
                "z": "",
                "alarm": "",
                "n_alarms": tot_boot,
                "expected_alarms": expected_per_season,
                "mean_alarms": mean_boot,
                "n_resamples": "",
                "exceedance_rate": "",
            })

        # 4. Righe "verification" (ordinate per fit cronologico, poi per L, poi metodo)
        for fit_k in ordered_fits:
            for block_len in BLOCK_LENGTHS:
                c_thresh = calib_thresholds[(fit_k, block_len)]
                c_rate, nom_rate = verif_rates[(fit_k, block_len)]

                # 4a. z_block_bootstrap con soglia calibrata
                records.append({
                    "row_type": "verification",
                    "season": "",
                    "fit_through": fit_k,
                    "method": "z_block_bootstrap",
                    "block_length": block_len,
                    "threshold": c_thresh,
                    "matchday": "",
                    "z": "",
                    "alarm": "",
                    "n_alarms": "",
                    "expected_alarms": "",
                    "mean_alarms": "",
                    "n_resamples": N_VERIFICATION_RESAMPLES,
                    "exceedance_rate": c_rate,
                })

                # 4b. z_nominal con soglia nominale
                records.append({
                    "row_type": "verification",
                    "season": "",
                    "fit_through": fit_k,
                    "method": "z_nominal",
                    "block_length": block_len,
                    "threshold": threshold,
                    "matchday": "",
                    "z": "",
                    "alarm": "",
                    "n_alarms": "",
                    "expected_alarms": "",
                    "mean_alarms": "",
                    "n_resamples": N_VERIFICATION_RESAMPLES,
                    "exceedance_rate": nom_rate,
                })

    return records


def generate_daily_z_test_records(
    df_residuals: pd.DataFrame,
    schedule: dict[str, dict[str, list[str]]],
    expected_matches: int = EXPECTED_MATCHES_PER_SEASON,
    alpha: float = ALPHA,
    matchday_size: int = MATCHDAY_SIZE,
    seed: int = SEED_C5,
) -> list[dict[str, str | int | float]]:
    """Estrae le serie dai residui e genera i record completi per il CSV di C5.2."""
    all_series = extract_scenario_series(df_residuals, schedule, expected_matches=expected_matches)
    val_series = [s for s in all_series if s.role == "validation"]
    baseline_stats = compute_training_baseline_stats(df_residuals, schedule=schedule)

    fit_keys = sorted(schedule.keys(), key=parse_season_start_year)
    training_series: dict[str, np.ndarray] = {}
    for fit_k in fit_keys:
        sub_tr = df_residuals[
            (df_residuals["role"] == "training")
            & (df_residuals["fit_through"] == fit_k)
        ].sort_values("Date", kind="stable")
        training_series[fit_k] = sub_tr["log_loss"].to_numpy(dtype=np.float64)

    return build_daily_z_test_records(
        validation_series=val_series,
        baseline_stats=baseline_stats,
        alpha=alpha,
        matchday_size=matchday_size,
        training_series=training_series,
        seed=seed,
    )
