"""Modulo di monitoraggio e generazione record per i drift detector (Task 28 / US-C5.1).

Fornisce la NamedTuple ScenarioSeries per rappresentare le serie temporali di log-loss
dei 22 scenari (3 di training e 19 di validazione), la funzione di estrazione delle serie
dai residui del Modulo 1 e la funzione di generazione dei record per il file CSV.
"""

from collections.abc import Collection, Mapping, Sequence
from typing import Final, NamedTuple

import numpy as np
import pandas as pd
from scipy.stats import norm

from shk.kelly.backtest import BacktestResult, backtest_log_wealth
from shk.kelly.metrics import max_drawdown
from shk.kelly.staking import (
    BASE_LAMBDA,
    KAPPA_ADWIN,
    KAPPA_GRID,
    KAPPA_PAGE_HINKLEY,
    BaselineDBets,
    compute_adaptive_lambda,
    select_baseline_d_bets,
)
from shk.model.elo_fit import parse_season_start_year
from shk.model.scoring import align_predictions_with_odds
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


# --- Funzioni di calibrazione e backtest per la Baseline D (Task 31 / US-C5.3) ---

class BaselineDSeasonInput(NamedTuple):
    """Input completi di una stagione per il backtest della Baseline D.

    Attributi
    ---------
    season : str
        Stagione di riferimento.
    dates : np.ndarray
        Array 1D datetime64 contenente le date di ciascuna partita.
    probs : np.ndarray
        Array 2D float64 di forma (N, 3) con le probabilità stimate [p_home, p_draw, p_away].
    odds : np.ndarray
        Array 2D float64 di forma (N, 3) con le quote decimali [B365H, B365D, B365A].
    ftr : np.ndarray
        Array 1D contenente l'esito reale della partita ('H', 'D', 'A').
    log_loss : np.ndarray
        Array 1D float64 contenente la serie di log-loss del modello.
    """

    season: str
    dates: np.ndarray
    probs: np.ndarray
    odds: np.ndarray
    ftr: np.ndarray
    log_loss: np.ndarray


class KappaCalibrationRow(NamedTuple):
    """Riga dettagliata della tabella di calibrazione di kappa per la Baseline D.

    Attributi
    ---------
    detector : str
        Nome del detector ('adwin' o 'page_hinkley').
    kappa : float
        Valore del moltiplicatore kappa testato.
    season : str
        Stagione di training valutata ('2010-11' o '2020-21').
    final_log_wealth : float
        Log-ricchezza finale della stagione ottenuta dal motore di backtest.
    n_bets : int
        Numero di partite in cui è stata piazzata una scommessa (frazione > 0).
    n_alarms : int
        Numero di allarmi rilevati dal detector nella stagione.
    """

    detector: str
    kappa: float
    season: str
    final_log_wealth: float
    n_bets: int
    n_alarms: int


class KappaCalibrationResult(NamedTuple):
    """Risultato complessivo della calibrazione di kappa per la Baseline D.

    Attributi
    ---------
    chosen_kappas : dict[str, float]
        Dizionario avente come chiavi i detector ('adwin', 'page_hinkley') e come valori
        i kappa ottimali scelti (che massimizzano la somma della log-ricchezza finale).
    table : tuple[KappaCalibrationRow, ...]
        Tupla contenente le righe dettagliate di ciascuna combinazione (detector, kappa, stagione).
    """

    chosen_kappas: dict[str, float]
    table: tuple[KappaCalibrationRow, ...]


def assemble_baseline_d_season_input(
    df_residuals: pd.DataFrame,
    df_raw: pd.DataFrame,
    season: str,
    fit_through: str,
    role: str = "training",
    expected_matches: int = EXPECTED_MATCHES_PER_SEASON,
) -> BaselineDSeasonInput:
    """Assembla gli input completi di una stagione per il backtest della Baseline D.

    Estrae le previsioni del modello, le allinea alle quote B365 pre-partita dai dati grezzi
    e restituisce matrici e array ordinati stabilmente per data cronologica.

    Parametri
    ---------
    df_residuals : pd.DataFrame
        DataFrame dei residui prodotto da compute_model_residuals.
    df_raw : pd.DataFrame
        DataFrame grezzo o consolidato contenente le quote B365.
    season : str
        Stagione da estrarre (es. '2010-11').
    fit_through : str
        Fit temporale associato (es. '2010-11').
    role : str, opzionale
        Ruolo delle partite ('training' o 'validation', default 'training').
    expected_matches : int, opzionale
        Numero atteso di partite nella stagione (default 380).

    Restituisce
    -----------
    BaselineDSeasonInput
        NamedTuple con le informazioni complete della stagione (season, dates, probs, odds, ftr, log_loss).

    Solleva
    -------
    TypeError
        Se df_residuals o df_raw non sono pd.DataFrame, o se season/fit_through/role non sono str.
    ValueError
        Se le righe estratte o allineate non corrispondono a expected_matches o se mancano quote B365.
    """
    if not isinstance(df_residuals, pd.DataFrame):
        raise TypeError(f"df_residuals must be a pd.DataFrame, got {type(df_residuals).__name__}")
    if not isinstance(df_raw, pd.DataFrame):
        raise TypeError(f"df_raw must be a pd.DataFrame, got {type(df_raw).__name__}")
    if not isinstance(season, str):
        raise TypeError(f"season must be a str, got {type(season).__name__}")
    if not isinstance(fit_through, str):
        raise TypeError(f"fit_through must be a str, got {type(fit_through).__name__}")
    if not isinstance(role, str):
        raise TypeError(f"role must be a str, got {type(role).__name__}")

    sub = df_residuals[
        (df_residuals["role"] == role)
        & (df_residuals["fit_through"] == fit_through)
        & (df_residuals["season"] == season)
    ].copy()

    if len(sub) != expected_matches:
        raise ValueError(
            f"Expected {expected_matches} matches for season {season} (fit {fit_through}, role {role}), "
            f"got {len(sub)}"
        )

    sub = sub.sort_values("Date", kind="stable").reset_index(drop=True)

    merged = align_predictions_with_odds(sub, df_raw)
    if len(merged) != expected_matches:
        raise ValueError(
            f"Aligned matches count {len(merged)} differs from expected {expected_matches}"
        )
    merged = merged.sort_values("Date", kind="stable").reset_index(drop=True)

    odds_cols = ["B365H", "B365D", "B365A"]
    for c in odds_cols:
        if c not in merged.columns:
            raise ValueError(f"Merged dataframe missing required odds column '{c}'")

    dates = pd.to_datetime(merged["Date"]).to_numpy(dtype="datetime64[ns]")
    probs = merged[["p_home", "p_draw", "p_away"]].to_numpy(dtype=np.float64)
    odds = merged[odds_cols].to_numpy(dtype=np.float64)
    ftr = merged["FTR"].to_numpy(dtype=object)
    log_loss = merged["log_loss"].to_numpy(dtype=np.float64)

    return BaselineDSeasonInput(
        season=season,
        dates=dates,
        probs=probs,
        odds=odds,
        ftr=ftr,
        log_loss=log_loss,
    )


def calibrate_baseline_d_kappa(
    df_residuals: pd.DataFrame,
    df_raw: pd.DataFrame,
    detectors: Sequence[str] = ("adwin", "page_hinkley"),
    calibration_seasons: Sequence[str] = ("2010-11", "2020-21"),
    kappa_grid: Sequence[float] = KAPPA_GRID,
    base_lambda: float = BASE_LAMBDA,
) -> KappaCalibrationResult:
    """Calibra kappa per ciascun detector sulle stagioni di training (2010-11 e 2020-21).

    Massimizza la somma delle log-ricchezze finali sulle stagioni di training considerate.
    A parità esatta di float, vince il kappa più grande:
        max(kappa_grid, key=lambda k: (total_log_wealth[k], k))

    Parametri
    ---------
    df_residuals : pd.DataFrame
        DataFrame dei residui prodotto da compute_model_residuals.
    df_raw : pd.DataFrame
        DataFrame grezzo o consolidato contenente le quote B365.
    detectors : Sequence[str], opzionale
        Nomi dei detector da calibrare (default: 'adwin', 'page_hinkley').
    calibration_seasons : Sequence[str], opzionale
        Stagioni di training per la calibrazione (default: '2010-11', '2020-21').
    kappa_grid : Sequence[float], opzionale
        Griglia di valori candidati per kappa (default KAPPA_GRID).
    base_lambda : float, opzionale
        Frazione di Kelly iniziale (default BASE_LAMBDA = 0.25).

    Restituisce
    -----------
    KappaCalibrationResult
        NamedTuple contenente:
        - chosen_kappas: dict[str, float] con il kappa ottimale per ciascun detector;
        - table: tuple[KappaCalibrationRow, ...] con i risultati dettagliati per riga
          (detector, kappa, season, final_log_wealth, n_bets, n_alarms).
    """
    if not isinstance(df_residuals, pd.DataFrame):
        raise TypeError(f"df_residuals must be a pd.DataFrame, got {type(df_residuals).__name__}")
    if not isinstance(df_raw, pd.DataFrame):
        raise TypeError(f"df_raw must be a pd.DataFrame, got {type(df_raw).__name__}")

    # Assemblaggio degli input per ciascuna stagione di calibrazione
    season_inputs: dict[str, BaselineDSeasonInput] = {}
    for s in calibration_seasons:
        season_inputs[s] = assemble_baseline_d_season_input(
            df_residuals=df_residuals,
            df_raw=df_raw,
            season=s,
            fit_through=s,
            role="training",
        )

    rows: list[KappaCalibrationRow] = []
    chosen_kappas: dict[str, float] = {}

    for det in detectors:
        # Calcolo allarmi per ciascuna stagione
        # Gli allarmi si calcolano con run_drift_detector e detector_params sulla log-loss
        params = detector_params(det)
        season_alarms: dict[str, np.ndarray] = {}
        for s in calibration_seasons:
            inp = season_inputs[s]
            alarm_indices = run_drift_detector(inp.log_loss, det, params)
            season_alarms[s] = inp.dates[alarm_indices]

        # Valutazione su ciascun kappa della griglia
        total_wealth_by_kappa: dict[float, float] = {}
        for k in kappa_grid:
            k_float = float(k)
            season_wealths: list[float] = []

            for s in calibration_seasons:
                inp = season_inputs[s]
                alarm_dates = season_alarms[s]
                lambdas = compute_adaptive_lambda(
                    inp.dates,
                    alarm_dates,
                    kappa=k_float,
                    base_lambda=base_lambda,
                )
                bets = select_baseline_d_bets(inp.probs, inp.odds, lambdas)
                won = (inp.ftr == bets.outcomes)
                backtest_res = backtest_log_wealth(
                    inp.dates,
                    bets.fractions,
                    bets.odds,
                    won,
                )
                final_lw = float(backtest_res.log_wealth[-1])
                n_bets = int(np.sum(bets.fractions > 0.0))
                n_alarms = len(alarm_dates)

                rows.append(
                    KappaCalibrationRow(
                        detector=det,
                        kappa=k_float,
                        season=s,
                        final_log_wealth=final_lw,
                        n_bets=n_bets,
                        n_alarms=n_alarms,
                    )
                )
                season_wealths.append(final_lw)

            total_wealth_by_kappa[k_float] = sum(season_wealths)

        # Regola di parità: a parità di somma esatta vince il kappa più grande
        best_k = max(kappa_grid, key=lambda k: (total_wealth_by_kappa[float(k)], float(k)))
        chosen_kappas[det] = float(best_k)

    return KappaCalibrationResult(
        chosen_kappas=chosen_kappas,
        table=tuple(rows),
    )


# --- Esecuzione appaiata della Baseline D sulle stagioni di validazione (Task 32 / US-C5.3) ---

# Schema delle 9 colonne in snake_case prescritte per il CSV della Baseline D (US-C5.3)
BASELINE_D_CSV_COLUMNS: Final[tuple[str, ...]] = (
    "row_type",
    "season",
    "fit_through",
    "agent",
    "kappa",
    "final_log_wealth",
    "n_bets",
    "n_alarms",
    "max_drawdown",
)


class BaselineDValidationSeasonData(NamedTuple):
    """Dati assemblati per una singola stagione di validazione per i tre agenti Baseline D.

    Attributi
    ---------
    season : str
        Stagione di validazione (es. '2002-03').
    fit_through : str
        Fit temporale associato (es. '2000-01').
    season_input : BaselineDSeasonInput
        Input completi della stagione (partite, quote, esiti, probabilità, log-loss).
    adwin_alarm_dates : np.ndarray
        Array 1D datetime64 con le date degli allarmi rilevati da ADWIN.
    page_hinkley_alarm_dates : np.ndarray
        Array 1D datetime64 con le date degli allarmi rilevati da Page-Hinkley.
    """

    season: str
    fit_through: str
    season_input: BaselineDSeasonInput
    adwin_alarm_dates: np.ndarray
    page_hinkley_alarm_dates: np.ndarray


class BaselineDAgentResult(NamedTuple):
    """Risultato dell'esecuzione di un agente su una stagione di validazione.

    Attributi
    ---------
    agent : str
        Nome identificativo dell'agente ('reference', 'd_adwin', 'd_page_hinkley').
    kappa : float
        Valore del moltiplicatore kappa applicato.
    final_log_wealth : float
        Log-ricchezza cumulativa finale al termine della stagione.
    n_bets : int
        Numero di partite in cui è stata piazzata una scommessa (frazione > 0).
    n_alarms : int | None
        Numero di allarmi (None per l'agente di riferimento).
    max_drawdown : float
        Massimo drawdown relativo della stagione in [0, 1).
    backtest_result : BacktestResult
        Risultato completo del motore di backtest.
    bets : BaselineDBets
        Scommesse e frazioni calcolate per ciascuna partita.
    """

    agent: str
    kappa: float
    final_log_wealth: float
    n_bets: int
    n_alarms: int | None
    max_drawdown: float
    backtest_result: BacktestResult
    bets: BaselineDBets


def build_baseline_d_season_data(
    df_residuals: pd.DataFrame,
    df_raw: pd.DataFrame,
    season: str,
    fit_through: str,
    expected_matches: int = EXPECTED_MATCHES_PER_SEASON,
) -> BaselineDValidationSeasonData:
    """Costruisce una sola volta per la stagione di validazione gli input e gli allarmi dei due detector.

    Parametri
    ---------
    df_residuals : pd.DataFrame
        DataFrame dei residui del Modulo 1.
    df_raw : pd.DataFrame
        DataFrame grezzo o consolidato contenente le quote B365.
    season : str
        Stagione di validazione da analizzare.
    fit_through : str
        Fit temporale associato alla stagione.
    expected_matches : int, opzionale
        Numero atteso di partite per stagione (default 380).

    Restituisce
    -----------
    BaselineDValidationSeasonData
        NamedTuple contenente gli input e le date degli allarmi dei due detector.

    Solleva
    -------
    TypeError
        Se df_residuals o df_raw non sono pd.DataFrame o se season/fit_through non sono str.
    ValueError
        Se le partite non corrispondono a expected_matches o mancano colonne.
    """
    if not isinstance(df_residuals, pd.DataFrame):
        raise TypeError(f"df_residuals must be a pd.DataFrame, got {type(df_residuals).__name__}")
    if not isinstance(df_raw, pd.DataFrame):
        raise TypeError(f"df_raw must be a pd.DataFrame, got {type(df_raw).__name__}")
    if not isinstance(season, str):
        raise TypeError(f"season must be a str, got {type(season).__name__}")
    if not isinstance(fit_through, str):
        raise TypeError(f"fit_through must be a str, got {type(fit_through).__name__}")

    season_input = assemble_baseline_d_season_input(
        df_residuals=df_residuals,
        df_raw=df_raw,
        season=season,
        fit_through=fit_through,
        role="validation",
        expected_matches=expected_matches,
    )

    # Allarmi ADWIN
    adwin_params = detector_params("adwin")
    adwin_indices = run_drift_detector(season_input.log_loss, "adwin", adwin_params)
    adwin_alarm_dates = season_input.dates[adwin_indices]

    # Allarmi Page-Hinkley
    ph_params = detector_params("page_hinkley")
    ph_indices = run_drift_detector(season_input.log_loss, "page_hinkley", ph_params)
    ph_alarm_dates = season_input.dates[ph_indices]

    return BaselineDValidationSeasonData(
        season=season,
        fit_through=fit_through,
        season_input=season_input,
        adwin_alarm_dates=adwin_alarm_dates,
        page_hinkley_alarm_dates=ph_alarm_dates,
    )


def evaluate_baseline_d_agents(
    season_data: BaselineDValidationSeasonData,
    base_lambda: float = BASE_LAMBDA,
    kappa_adwin: float = KAPPA_ADWIN,
    kappa_page_hinkley: float = KAPPA_PAGE_HINKLEY,
) -> tuple[BaselineDAgentResult, BaselineDAgentResult, BaselineDAgentResult]:
    """Esegue i tre agenti (reference, d_adwin, d_page_hinkley) sugli stessi oggetti di stagione.

    Restituisce i risultati nell'ordine esatto: reference, d_adwin, d_page_hinkley.

    Parametri
    ---------
    season_data : BaselineDValidationSeasonData
        Dati della stagione di validazione con input e date degli allarmi.
    base_lambda : float, opzionale
        Frazione di Kelly iniziale (default BASE_LAMBDA = 0.25).
    kappa_adwin : float, opzionale
        Moltiplicatore kappa congelato per ADWIN (default KAPPA_ADWIN = 1.0).
    kappa_page_hinkley : float, opzionale
        Moltiplicatore kappa congelato per Page-Hinkley (default KAPPA_PAGE_HINKLEY = 1.0).

    Restituisce
    -----------
    tuple[BaselineDAgentResult, BaselineDAgentResult, BaselineDAgentResult]
        Tupla con i risultati dei tre agenti nell'ordine (reference, d_adwin, d_page_hinkley).

    Solleva
    -------
    TypeError
        Se season_data non è un'istanza di BaselineDValidationSeasonData.
    """
    if not isinstance(season_data, BaselineDValidationSeasonData):
        raise TypeError(
            f"season_data must be a BaselineDValidationSeasonData, got {type(season_data).__name__}"
        )

    inp = season_data.season_input

    # 1. Agente reference: kappa = 1.0, nessun allarme (nessuna riduzione)
    empty_alarm_dates = np.empty(0, dtype=inp.dates.dtype)
    ref_lambdas = compute_adaptive_lambda(
        inp.dates,
        empty_alarm_dates,
        kappa=1.0,
        base_lambda=base_lambda,
    )
    ref_bets = select_baseline_d_bets(inp.probs, inp.odds, ref_lambdas)
    ref_won = (inp.ftr == ref_bets.outcomes)
    ref_backtest = backtest_log_wealth(inp.dates, ref_bets.fractions, ref_bets.odds, ref_won)
    ref_mdd = float(max_drawdown(ref_backtest.log_wealth.reshape(1, -1))[0])
    ref_result = BaselineDAgentResult(
        agent="reference",
        kappa=1.0,
        final_log_wealth=float(ref_backtest.log_wealth[-1]),
        n_bets=int(np.sum(ref_bets.fractions > 0.0)),
        n_alarms=None,
        max_drawdown=ref_mdd,
        backtest_result=ref_backtest,
        bets=ref_bets,
    )

    # 2. Agente d_adwin: kappa = kappa_adwin, allarmi di ADWIN
    adwin_lambdas = compute_adaptive_lambda(
        inp.dates,
        season_data.adwin_alarm_dates,
        kappa=kappa_adwin,
        base_lambda=base_lambda,
    )
    adwin_bets = select_baseline_d_bets(inp.probs, inp.odds, adwin_lambdas)
    adwin_won = (inp.ftr == adwin_bets.outcomes)
    adwin_backtest = backtest_log_wealth(inp.dates, adwin_bets.fractions, adwin_bets.odds, adwin_won)
    adwin_mdd = float(max_drawdown(adwin_backtest.log_wealth.reshape(1, -1))[0])
    adwin_result = BaselineDAgentResult(
        agent="d_adwin",
        kappa=kappa_adwin,
        final_log_wealth=float(adwin_backtest.log_wealth[-1]),
        n_bets=int(np.sum(adwin_bets.fractions > 0.0)),
        n_alarms=len(season_data.adwin_alarm_dates),
        max_drawdown=adwin_mdd,
        backtest_result=adwin_backtest,
        bets=adwin_bets,
    )

    # 3. Agente d_page_hinkley: kappa = kappa_page_hinkley, allarmi di Page-Hinkley
    ph_lambdas = compute_adaptive_lambda(
        inp.dates,
        season_data.page_hinkley_alarm_dates,
        kappa=kappa_page_hinkley,
        base_lambda=base_lambda,
    )
    ph_bets = select_baseline_d_bets(inp.probs, inp.odds, ph_lambdas)
    ph_won = (inp.ftr == ph_bets.outcomes)
    ph_backtest = backtest_log_wealth(inp.dates, ph_bets.fractions, ph_bets.odds, ph_won)
    ph_mdd = float(max_drawdown(ph_backtest.log_wealth.reshape(1, -1))[0])
    ph_result = BaselineDAgentResult(
        agent="d_page_hinkley",
        kappa=kappa_page_hinkley,
        final_log_wealth=float(ph_backtest.log_wealth[-1]),
        n_bets=int(np.sum(ph_bets.fractions > 0.0)),
        n_alarms=len(season_data.page_hinkley_alarm_dates),
        max_drawdown=ph_mdd,
        backtest_result=ph_backtest,
        bets=ph_bets,
    )

    return (ref_result, adwin_result, ph_result)


def generate_baseline_d_records(
    df_residuals: pd.DataFrame,
    df_raw: pd.DataFrame,
    schedule: dict[str, dict[str, list[str]]],
    base_lambda: float = BASE_LAMBDA,
    kappa_adwin: float = KAPPA_ADWIN,
    kappa_page_hinkley: float = KAPPA_PAGE_HINKLEY,
) -> list[dict[str, str | int | float]]:
    """Genera tutti i 60 record prescritti per il CSV di US-C5.3 (57 season e 3 total).

    Parametri
    ---------
    df_residuals : pd.DataFrame
        DataFrame dei residui del Modulo 1.
    df_raw : pd.DataFrame
        DataFrame grezzo o consolidato contenente le quote B365.
    schedule : dict[str, dict[str, list[str]]]
        Schema dei fit con training e validazione.
    base_lambda : float, opzionale
        Frazione di Kelly iniziale (default BASE_LAMBDA = 0.25).
    kappa_adwin : float, opzionale
        Moltiplicatore kappa congelato per ADWIN (default KAPPA_ADWIN = 1.0).
    kappa_page_hinkley : float, opzionale
        Moltiplicatore kappa congelato per Page-Hinkley (default KAPPA_PAGE_HINKLEY = 1.0).

    Restituisce
    -----------
    list[dict[str, str | int | float]]
        Lista di 60 dizionari conformi a BASELINE_D_CSV_COLUMNS.
    """
    if not isinstance(df_residuals, pd.DataFrame):
        raise TypeError(f"df_residuals must be a pd.DataFrame, got {type(df_residuals).__name__}")
    if not isinstance(df_raw, pd.DataFrame):
        raise TypeError(f"df_raw must be a pd.DataFrame, got {type(df_raw).__name__}")
    if not isinstance(schedule, dict):
        raise TypeError(f"schedule must be a dict, got {type(schedule).__name__}")

    train_fits = sorted(schedule.keys(), key=parse_season_start_year)
    val_seasons_with_fit: list[tuple[str, str]] = []
    for fit_k in train_fits:
        for val_s in schedule[fit_k]["validation"]:
            val_seasons_with_fit.append((val_s, fit_k))

    val_seasons_with_fit.sort(key=lambda item: parse_season_start_year(item[0]))

    season_rows: list[dict[str, str | int | float]] = []
    agent_totals: dict[str, dict[str, float | int]] = {
        "reference": {"final_log_wealth": 0.0, "n_bets": 0, "n_alarms": 0, "kappa": 1.0},
        "d_adwin": {"final_log_wealth": 0.0, "n_bets": 0, "n_alarms": 0, "kappa": kappa_adwin},
        "d_page_hinkley": {"final_log_wealth": 0.0, "n_bets": 0, "n_alarms": 0, "kappa": kappa_page_hinkley},
    }

    for season, fit_through in val_seasons_with_fit:
        s_data = build_baseline_d_season_data(
            df_residuals=df_residuals,
            df_raw=df_raw,
            season=season,
            fit_through=fit_through,
        )
        agent_results = evaluate_baseline_d_agents(
            season_data=s_data,
            base_lambda=base_lambda,
            kappa_adwin=kappa_adwin,
            kappa_page_hinkley=kappa_page_hinkley,
        )

        for res in agent_results:
            n_alarms_val = "" if res.n_alarms is None else res.n_alarms
            season_rows.append({
                "row_type": "season",
                "season": season,
                "fit_through": fit_through,
                "agent": res.agent,
                "kappa": res.kappa,
                "final_log_wealth": res.final_log_wealth,
                "n_bets": res.n_bets,
                "n_alarms": n_alarms_val,
                "max_drawdown": res.max_drawdown,
            })
            agent_totals[res.agent]["final_log_wealth"] += res.final_log_wealth
            agent_totals[res.agent]["n_bets"] += res.n_bets
            if res.n_alarms is not None:
                agent_totals[res.agent]["n_alarms"] += res.n_alarms

    total_rows: list[dict[str, str | int | float]] = []
    for agent_name in ("reference", "d_adwin", "d_page_hinkley"):
        tot = agent_totals[agent_name]
        n_alarms_tot = "" if agent_name == "reference" else tot["n_alarms"]
        total_rows.append({
            "row_type": "total",
            "season": "",
            "fit_through": "",
            "agent": agent_name,
            "kappa": tot["kappa"],
            "final_log_wealth": tot["final_log_wealth"],
            "n_bets": tot["n_bets"],
            "n_alarms": n_alarms_tot,
            "max_drawdown": "",
        })

    return season_rows + total_rows


