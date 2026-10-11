"""Modulo per l'analisi dell'eteroschedasticità dei residui del Modulo 1 (US-C6.4 / Task 39).

Implementa la pipeline di test di eteroschedasticità (Breusch-Pagan joint su (H, t) con df=2,
Breusch-Pagan su t con df=1, White su (H, t) con df=5) sui residui del Modulo 1 raw (y = log_loss),
stagione per stagione, confrontando le statistiche LM con le soglie asintotiche nominali chi^2
e con le soglie calibrate mediante moving block bootstrap con lunghezze blocco L in {7, 20, 40}.
"""

from collections.abc import Collection, Mapping, Sequence
import math
from typing import Final, NamedTuple

import numpy as np
import pandas as pd
import scipy.stats

from shk.kelly.floor import SEED_C6
from shk.model.elo_fit import parse_season_start_year
from shk.stats.calibration import moving_block_indices
from shk.stats.heteroskedasticity import (
    HeteroskedasticityBatchResult,
    HeteroskedasticityTestResult,
    bp_statistic,
    bp_statistic_batch,
    nominal_threshold,
    white_statistic,
    white_statistic_batch,
)

# ------------------------------------------------------------------------------
# Costanti di specifica (US-C6.4 / Task 39)
# ------------------------------------------------------------------------------
ALPHA: Final[float] = 0.05
N_BOOT_CALIB: Final[int] = 999
N_VERIF_RESAMPLES: Final[int] = 1_000
BLOCK_LENGTHS: Final[tuple[int, ...]] = (7, 20, 40)
STATISTICS: Final[tuple[str, ...]] = ("bp_joint", "bp_time", "white")
STATISTIC_DFS: Final[dict[str, int]] = {
    "bp_joint": 2,
    "bp_time": 1,
    "white": 5,
}

# Limiti di tolleranza di Bonferroni al 99% per 27 casi di verifica con N = 1000 repliche
BONFERRONI_LOWER: Final[float] = 0.0153
BONFERRONI_UPPER: Final[float] = 0.0847

# Numero di partite per stagione
MATCHES_PER_SEASON: Final[int] = 380

# Schema esatto delle 23 colonne prescritte per il file CSV
HETEROSKEDASTICITY_CSV_COLUMNS: Final[tuple[str, ...]] = (
    "row_type",
    "season",
    "role",
    "fit_through",
    "statistic",
    "df",
    "method",
    "block_length",
    "lm_stat",
    "p_value_nom",
    "threshold_nom",
    "reject_nom",
    "threshold_L7",
    "reject_L7",
    "threshold_L20",
    "reject_L20",
    "threshold_L40",
    "reject_L40",
    "calibrated_threshold",
    "verif_rejection_rate_calib",
    "verif_rejection_rate_nom",
    "n_validation_rejections",
    "p_value_binomial",
)


class ScenarioData(NamedTuple):
    """Contenitore per le variabili di una singola stagione di scenario."""

    season: str
    role: str
    fit_through: str
    log_loss: np.ndarray
    entropy: np.ndarray
    t: np.ndarray
    date: tuple[str, ...]


class TrainingData(NamedTuple):
    """Contenitore per le variabili della serie di training di un fit congelato."""

    fit_through: str
    n_train: int
    log_loss: np.ndarray
    entropy: np.ndarray
    date: tuple[str, ...]


def compute_shannon_entropy(probs: np.ndarray) -> np.ndarray:
    """Calcola l'entropia di Shannon H = -sum(p * ln(p)) per riga.

    Parametri
    ---------
    probs : np.ndarray
        Array 2D float64 di forma (n, 3) con le probabilità previste (p_home, p_draw, p_away).

    Restituisce
    -----------
    np.ndarray
        Array 1D float64 di forma (n,) con i valori di entropia.
    """
    if not isinstance(probs, np.ndarray):
        raise TypeError(f"probs must be a numpy.ndarray, got {type(probs).__name__}")
    if probs.ndim != 2 or probs.shape[1] != 3:
        raise ValueError(f"probs must be 2D of shape (n, 3), got shape {probs.shape}")

    # Clip difensivo a valori strettamente positivi per evitare ln(0)
    safe_p = np.clip(probs, 1e-15, 1.0)
    return -np.sum(safe_p * np.log(safe_p), axis=1)


def extract_scenario_and_training_data(
    df_residuals: pd.DataFrame,
    schedule: dict[str, dict[str, list[str]]],
    expected_matches: int = MATCHES_PER_SEASON,
) -> tuple[list[ScenarioData], dict[str, TrainingData]]:
    """Estrae i 22 scenari cronologici e le 3 serie di training dal DataFrame dei residui.

    Verifica difensivamente che ogni scenario contenga esattamente expected_matches partite,
    che le date non decrescano (ordinamento cronologico stabile) e assegna t = 1..380.
    Estrae analogamente la serie completa di training per ciascun fit congelato (n_train in {380, 760, 1140}).

    Parametri
    ---------
    df_residuals : pd.DataFrame
        DataFrame restituito da compute_model_residuals.
    schedule : dict[str, dict[str, list[str]]]
        Dizionario di schedule dei fit con 'training' e 'validation'.
    expected_matches : int, opzionale
        Partite attese per stagione (default 380).

    Restituisce
    -----------
    tuple[list[ScenarioData], dict[str, TrainingData]]
        I 22 scenari ordinati cronologicamente per anno di inizio stagione e il dizionario dei 3 training.
    """
    if not isinstance(df_residuals, pd.DataFrame):
        raise TypeError(f"df_residuals must be a pd.DataFrame, got {type(df_residuals).__name__}")
    if not isinstance(schedule, dict):
        raise TypeError(f"schedule must be a dict, got {type(schedule).__name__}")

    required_cols = {
        "season",
        "Date",
        "fit_through",
        "role",
        "log_loss",
        "p_home",
        "p_draw",
        "p_away",
    }
    missing = required_cols - set(df_residuals.columns)
    if missing:
        raise ValueError(f"df_residuals missing required columns: {sorted(missing)}")

    ordered_fits = sorted(schedule.keys(), key=parse_season_start_year)

    # 1. Estrazione serie di training per ciascun fit
    training_dict: dict[str, TrainingData] = {}
    for fit_k in ordered_fits:
        sub_train = df_residuals[
            (df_residuals["role"] == "training") & (df_residuals["fit_through"] == fit_k)
        ].copy()

        if sub_train.empty:
            raise ValueError(f"No training data found for fit '{fit_k}'")

        # Verifica monotonicità non decrescente delle date di training
        if not sub_train["Date"].is_monotonic_increasing:
            raise ValueError(f"Training dates for fit '{fit_k}' are not monotonically non-decreasing")

        probs_tr = sub_train[["p_home", "p_draw", "p_away"]].to_numpy(dtype=np.float64)
        h_tr = compute_shannon_entropy(probs_tr)
        losses_tr = sub_train["log_loss"].to_numpy(dtype=np.float64)
        dates_tr = tuple(pd.Timestamp(d).strftime("%Y-%m-%d") for d in sub_train["Date"])

        n_tr = len(sub_train)
        training_dict[fit_k] = TrainingData(
            fit_through=fit_k,
            n_train=n_tr,
            log_loss=losses_tr,
            entropy=h_tr,
            date=dates_tr,
        )

    # 2. Estrazione dei 22 scenari
    raw_scenarios: list[ScenarioData] = []

    # 2a. 3 scenari di training (2000-01, 2010-11, 2020-21)
    for fit_k in ordered_fits:
        sub = df_residuals[
            (df_residuals["role"] == "training")
            & (df_residuals["fit_through"] == fit_k)
            & (df_residuals["season"] == fit_k)
        ].copy()

        if len(sub) != expected_matches:
            raise ValueError(
                f"Training scenario '{fit_k}' has {len(sub)} matches, expected {expected_matches}"
            )

        if not sub["Date"].is_monotonic_increasing:
            raise ValueError(f"Dates for training scenario '{fit_k}' are not monotonically non-decreasing")

        probs = sub[["p_home", "p_draw", "p_away"]].to_numpy(dtype=np.float64)
        h_vals = compute_shannon_entropy(probs)
        losses = sub["log_loss"].to_numpy(dtype=np.float64)
        t_vals = np.arange(1, expected_matches + 1, dtype=np.float64)
        dates_s = tuple(pd.Timestamp(d).strftime("%Y-%m-%d") for d in sub["Date"])

        raw_scenarios.append(
            ScenarioData(
                season=fit_k,
                role="training",
                fit_through=fit_k,
                log_loss=losses,
                entropy=h_vals,
                t=t_vals,
                date=dates_s,
            )
        )

    # 2b. 19 scenari di validazione
    for fit_k in ordered_fits:
        for val_s in schedule[fit_k]["validation"]:
            sub = df_residuals[
                (df_residuals["role"] == "validation")
                & (df_residuals["fit_through"] == fit_k)
                & (df_residuals["season"] == val_s)
            ].copy()

            if len(sub) != expected_matches:
                raise ValueError(
                    f"Validation scenario '{val_s}' has {len(sub)} matches, expected {expected_matches}"
                )

            if not sub["Date"].is_monotonic_increasing:
                raise ValueError(f"Dates for validation scenario '{val_s}' are not monotonically non-decreasing")

            probs = sub[["p_home", "p_draw", "p_away"]].to_numpy(dtype=np.float64)
            h_vals = compute_shannon_entropy(probs)
            losses = sub["log_loss"].to_numpy(dtype=np.float64)
            t_vals = np.arange(1, expected_matches + 1, dtype=np.float64)
            dates_s = tuple(pd.Timestamp(d).strftime("%Y-%m-%d") for d in sub["Date"])

            raw_scenarios.append(
                ScenarioData(
                    season=val_s,
                    role="validation",
                    fit_through=fit_k,
                    log_loss=losses,
                    entropy=h_vals,
                    t=t_vals,
                    date=dates_s,
                )
            )

    # Ordinamento cronologico stabile per anno di inizio stagione
    ordered_scenarios = sorted(raw_scenarios, key=lambda s: parse_season_start_year(s.season))
    return ordered_scenarios, training_dict


def compute_scenario_test_statistics(
    y: np.ndarray,
    entropy: np.ndarray,
    t: np.ndarray,
) -> dict[str, HeteroskedasticityTestResult]:
    """Calcola le tre statistiche di eteroschedasticità su una stagione di 380 partite.

    Modello primario OLS: y ~ 1 + H + t.
    - bp_joint: test BP con regressori ausiliari [H, t] (df = 2);
    - bp_time: test BP con regressore ausiliario [t] (df = 1);
    - white: test di White con termini lineari, quadratici e interazione su [H, t] (df = 5).

    Parametri
    ---------
    y : np.ndarray
        Array 1D float64 (380,) delle log-loss.
    entropy : np.ndarray
        Array 1D float64 (380,) dell'entropia di Shannon.
    t : np.ndarray
        Array 1D float64 (380,) dell'indice temporale 1..380.

    Restituisce
    -----------
    dict[str, HeteroskedasticityTestResult]
        Mappatura statistica ('bp_joint', 'bp_time', 'white') -> HeteroskedasticityTestResult.
    """
    x_joint = np.column_stack([entropy, t])
    z_time = t[:, np.newaxis]

    res_bp_joint = bp_statistic(y, x_joint, z=None)
    res_bp_time = bp_statistic(y, x_joint, z=z_time)
    res_white = white_statistic(y, x_joint)

    return {
        "bp_joint": res_bp_joint,
        "bp_time": res_bp_time,
        "white": res_white,
    }


def spawn_c6_4_generators(
    seed: int = SEED_C6,
    fits: Sequence[str] = ("2000-01", "2010-11", "2020-21"),
    block_lengths: Sequence[int] = BLOCK_LENGTHS,
) -> dict[str, dict[int, tuple[np.random.Generator, np.random.Generator]]]:
    """Costruisce la gerarchia deterministica di generatori di numeri casuali per US-C6.4.

    Gerarchia:
    SeedSequence(SEED_C6).spawn(3)[2] -> spawn(len(fits)) -> per fit, spawn(len(block_lengths)) -> per L, spawn(2)
    restituendo per ciascun (fit, L) la coppia (calib_rng, verif_rng).

    Parametri
    ---------
    seed : int, opzionale
        Seme master C6 (default SEED_C6).
    fits : Sequence[str], opzionale
        Nomi dei fit in ordine cronologico.
    block_lengths : Sequence[int], opzionale
        Lunghezze dei blocchi L in ordine crescente.

    Restituisce
    -----------
    dict[str, dict[int, tuple[np.random.Generator, np.random.Generator]]]
        Mappatura fit -> {L -> (calib_rng, verif_rng)}.
    """
    master_seq = np.random.SeedSequence(seed)
    c6_children = master_seq.spawn(3)
    t39_seq = c6_children[2]

    fit_seqs = t39_seq.spawn(len(fits))
    rng_dict: dict[str, dict[int, tuple[np.random.Generator, np.random.Generator]]] = {}

    for f_idx, fit_k in enumerate(fits):
        rng_dict[fit_k] = {}
        l_seqs = fit_seqs[f_idx].spawn(len(block_lengths))
        for l_idx, blk_len in enumerate(block_lengths):
            task_seqs = l_seqs[l_idx].spawn(2)
            calib_rng = np.random.default_rng(task_seqs[0])
            verif_rng = np.random.default_rng(task_seqs[1])
            rng_dict[fit_k][blk_len] = (calib_rng, verif_rng)

    return rng_dict


def calibrate_block_bootstrap_thresholds(
    training_dict: Mapping[str, TrainingData],
    rng_dict: Mapping[str, Mapping[int, tuple[np.random.Generator, np.random.Generator]]],
    block_lengths: Sequence[int] = BLOCK_LENGTHS,
    n_boot: int = N_BOOT_CALIB,
    target_sample_size: int = MATCHES_PER_SEASON,
) -> dict[tuple[str, int, str], float]:
    """Calcola le soglie calibrate mediante moving block bootstrap su B = 999 repliche.

    Per ciascun fit e ciascun blocco L, estrae B repliche di lunghezza target_sample_size (380)
    dalla serie di training (y, H ricampionati insieme, t = 1..380 fisso).
    La soglia al 95% è la 950-esima statistica d'ordine (indice 949 su array ordinato).

    Parametri
    ---------
    training_dict : Mapping[str, TrainingData]
        Dizionario fit_through -> TrainingData.
    rng_dict : Mapping[str, Mapping[int, tuple[np.random.Generator, np.random.Generator]]]
        Dizionario fit_through -> {L -> (calib_rng, verif_rng)}.
    block_lengths : Sequence[int], opzionale
        Lunghezze dei blocchi L (default 7, 20, 40).
    n_boot : int, opzionale
        Numero di repliche bootstrap (default 999).
    target_sample_size : int, opzionale
        Dimensione delle serie ricampionate (default 380).

    Restituisce
    -----------
    dict[tuple[str, int, str], float]
        Mappatura (fit_through, L, statistic) -> calibrated_threshold.
    """
    thresholds: dict[tuple[str, int, str], float] = {}
    order_idx = int(math.ceil(0.95 * (n_boot + 1))) - 1  # Per B = 999: ceil(0.95 * 1000) - 1 = 949

    t_vec = np.arange(1, target_sample_size + 1, dtype=np.float64)
    t_batch_aux = np.broadcast_to(t_vec[np.newaxis, :, np.newaxis], (n_boot, target_sample_size, 1))

    for fit_k, tr_data in training_dict.items():
        n_tr = tr_data.n_train
        y_tr = tr_data.log_loss
        h_tr = tr_data.entropy

        for blk_len in block_lengths:
            calib_rng, _ = rng_dict[fit_k][blk_len]

            # Estrazione indici e troncamento a 380 osservazioni
            indices = moving_block_indices(n_tr, blk_len, n_boot, calib_rng)[:, :target_sample_size]

            # (y, H) ricampionati insieme
            y_batch = y_tr[indices]
            h_batch = h_tr[indices]

            # Matrice regressori primari: [H, t] per ciascuna replica
            x_batch = np.empty((n_boot, target_sample_size, 2), dtype=np.float64)
            x_batch[:, :, 0] = h_batch
            x_batch[:, :, 1] = np.broadcast_to(t_vec, (n_boot, target_sample_size))

            # Calcolo batch delle tre statistiche
            res_joint = bp_statistic_batch(y_batch, x_batch, z=None)
            res_time = bp_statistic_batch(y_batch, x_batch, z=t_batch_aux)
            res_white = white_statistic_batch(y_batch, x_batch)

            thresh_joint = float(np.sort(res_joint.lm_stats)[order_idx])
            thresh_time = float(np.sort(res_time.lm_stats)[order_idx])
            thresh_white = float(np.sort(res_white.lm_stats)[order_idx])

            thresholds[(fit_k, blk_len, "bp_joint")] = thresh_joint
            thresholds[(fit_k, blk_len, "bp_time")] = thresh_time
            thresholds[(fit_k, blk_len, "white")] = thresh_white

    return thresholds


def verify_calibrated_thresholds(
    training_dict: Mapping[str, TrainingData],
    rng_dict: Mapping[str, Mapping[int, tuple[np.random.Generator, np.random.Generator]]],
    calibrated_thresholds: Mapping[tuple[str, int, str], float],
    block_lengths: Sequence[int] = BLOCK_LENGTHS,
    n_verif: int = N_VERIF_RESAMPLES,
    target_sample_size: int = MATCHES_PER_SEASON,
    alpha: float = ALPHA,
) -> dict[tuple[str, int, str], tuple[float, float]]:
    """Verifica le soglie calibrate su 1 000 ricampionamenti indipendenti per ciascun caso (27 totali).

    Parametri
    ---------
    training_dict : Mapping[str, TrainingData]
        Dizionario fit_through -> TrainingData.
    rng_dict : Mapping[str, Mapping[int, tuple[np.random.Generator, np.random.Generator]]]
        Dizionario fit_through -> {L -> (calib_rng, verif_rng)}.
    calibrated_thresholds : Mapping[tuple[str, int, str], float]
        Soglie calibrate da verificare.
    block_lengths : Sequence[int], opzionale
        Lunghezze dei blocchi L (default 7, 20, 40).
    n_verif : int, opzionale
        Numero di ricampionamenti di verifica (default 1000).
    target_sample_size : int, opzionale
        Dimensione campionaria (default 380).
    alpha : float, opzionale
        Livello nominale (default 0.05).

    Restituisce
    -----------
    dict[tuple[str, int, str], tuple[float, float]]
        Mappatura (fit_through, L, statistic) -> (verif_rejection_rate_calib, verif_rejection_rate_nom).
    """
    results: dict[tuple[str, int, str], tuple[float, float]] = {}

    nom_thresholds = {
        stat: nominal_threshold(STATISTIC_DFS[stat], alpha) for stat in STATISTICS
    }

    t_vec = np.arange(1, target_sample_size + 1, dtype=np.float64)
    t_batch_aux = np.broadcast_to(t_vec[np.newaxis, :, np.newaxis], (n_verif, target_sample_size, 1))

    for fit_k, tr_data in training_dict.items():
        n_tr = tr_data.n_train
        y_tr = tr_data.log_loss
        h_tr = tr_data.entropy

        for blk_len in block_lengths:
            _, verif_rng = rng_dict[fit_k][blk_len]

            indices = moving_block_indices(n_tr, blk_len, n_verif, verif_rng)[:, :target_sample_size]

            y_batch = y_tr[indices]
            h_batch = h_tr[indices]

            x_batch = np.empty((n_verif, target_sample_size, 2), dtype=np.float64)
            x_batch[:, :, 0] = h_batch
            x_batch[:, :, 1] = np.broadcast_to(t_vec, (n_verif, target_sample_size))

            res_joint = bp_statistic_batch(y_batch, x_batch, z=None)
            res_time = bp_statistic_batch(y_batch, x_batch, z=t_batch_aux)
            res_white = white_statistic_batch(y_batch, x_batch)

            for stat_name, batch_res in [
                ("bp_joint", res_joint),
                ("bp_time", res_time),
                ("white", res_white),
            ]:
                c_thresh = calibrated_thresholds[(fit_k, blk_len, stat_name)]
                nom_thresh = nom_thresholds[stat_name]

                rate_calib = float(np.mean(batch_res.lm_stats > c_thresh))
                rate_nom = float(np.mean(batch_res.lm_stats > nom_thresh))

                results[(fit_k, blk_len, stat_name)] = (rate_calib, rate_nom)

    return results


def binomial_exceedance_p_value(k: int, n: int = 19, p: float = ALPHA) -> float:
    """Calcola il p-value esatto P(X >= k) con X ~ Binomiale(n, p)."""
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    return float(scipy.stats.binom.sf(k - 1, n, p))


def evaluate_residual_heteroskedasticity(
    df_residuals: pd.DataFrame,
    schedule: dict[str, dict[str, list[str]]],
    seed: int = SEED_C6,
    alpha: float = ALPHA,
    block_lengths: Sequence[int] = BLOCK_LENGTHS,
) -> list[dict[str, str | int | float | bool]]:
    """Esegue l'intera pipeline di eteroschedasticità e produce i 105 record completi per il CSV.

    Struttura:
    - 66 righe "scenario" (22 stagioni x 3 statistiche) con valori LM, p-value asintotici e flag di rigetto;
    - 27 righe "verification" (3 fit x 3 L x 3 statistiche) con soglie calibrate e tassi di rigetto simulati;
    - 12 righe "summary" (3 statistiche x 4 metodi) con conteggio dei rigetti nelle 19 stagioni di validazione
      e relativo p-value binomiale P(X >= k) con X ~ Binomiale(19, 0.05).

    Parametri
    ---------
    df_residuals : pd.DataFrame
        DataFrame dei residui prodotto da compute_model_residuals.
    schedule : dict[str, dict[str, list[str]]]
        Dizionario dei fit.
    seed : int, opzionale
        Seme master per la gerarchia di generatori.
    alpha : float, opzionale
        Livello di significatività nominale (default 0.05).
    block_lengths : Sequence[int], opzionale
        Lunghezze dei blocchi (default (7, 20, 40)).

    Restituisce
    -----------
    list[dict[str, str | int | float | bool]]
        Lista di esattamente 105 dizionari conformi a HETEROSKEDASTICITY_CSV_COLUMNS.
    """
    scenarios, training_dict = extract_scenario_and_training_data(df_residuals, schedule)

    ordered_fits = sorted(training_dict.keys(), key=parse_season_start_year)
    rng_dict = spawn_c6_4_generators(seed=seed, fits=ordered_fits, block_lengths=block_lengths)

    # 1. Calibrazione delle soglie
    calib_thresholds = calibrate_block_bootstrap_thresholds(
        training_dict=training_dict,
        rng_dict=rng_dict,
        block_lengths=block_lengths,
        n_boot=N_BOOT_CALIB,
    )

    # 2. Verifica delle soglie su 1000 ricampionamenti
    verif_results = verify_calibrated_thresholds(
        training_dict=training_dict,
        rng_dict=rng_dict,
        calibrated_thresholds=calib_thresholds,
        block_lengths=block_lengths,
        n_verif=N_VERIF_RESAMPLES,
        alpha=alpha,
    )

    nom_thresholds = {
        stat: nominal_threshold(STATISTIC_DFS[stat], alpha) for stat in STATISTICS
    }

    records: list[dict[str, str | int | float | bool]] = []

    # Struttura per conteggio dei rigetti nelle sole 19 stagioni di validazione
    # (statistic, method) -> conteggio
    val_rejections: dict[tuple[str, str], int] = {
        (stat, m): 0
        for stat in STATISTICS
        for m in ("nominal", "bootstrap_L7", "bootstrap_L20", "bootstrap_L40")
    }

    # --------------------------------------------------------------------------
    # Parte A: 66 righe "scenario"
    # --------------------------------------------------------------------------
    for sc in scenarios:
        stat_results = compute_scenario_test_statistics(sc.log_loss, sc.entropy, sc.t)

        for stat_name in STATISTICS:
            res = stat_results[stat_name]
            lm_val = float(res.lm_stat)
            p_val = float(res.p_value)
            df_val = int(res.df)

            nom_th = nom_thresholds[stat_name]
            th_l7 = calib_thresholds[(sc.fit_through, 7, stat_name)]
            th_l20 = calib_thresholds[(sc.fit_through, 20, stat_name)]
            th_l40 = calib_thresholds[(sc.fit_through, 40, stat_name)]

            rej_nom = bool(lm_val > nom_th)
            rej_l7 = bool(lm_val > th_l7)
            rej_l20 = bool(lm_val > th_l20)
            rej_l40 = bool(lm_val > th_l40)

            # Conteggio solo se scenario di validazione
            if sc.role == "validation":
                if rej_nom:
                    val_rejections[(stat_name, "nominal")] += 1
                if rej_l7:
                    val_rejections[(stat_name, "bootstrap_L7")] += 1
                if rej_l20:
                    val_rejections[(stat_name, "bootstrap_L20")] += 1
                if rej_l40:
                    val_rejections[(stat_name, "bootstrap_L40")] += 1

            records.append({
                "row_type": "scenario",
                "season": sc.season,
                "role": sc.role,
                "fit_through": sc.fit_through,
                "statistic": stat_name,
                "df": df_val,
                "method": "",
                "block_length": "",
                "lm_stat": lm_val,
                "p_value_nom": p_val,
                "threshold_nom": nom_th,
                "reject_nom": rej_nom,
                "threshold_L7": th_l7,
                "reject_L7": rej_l7,
                "threshold_L20": th_l20,
                "reject_L20": rej_l20,
                "threshold_L40": th_l40,
                "reject_L40": rej_l40,
                "calibrated_threshold": "",
                "verif_rejection_rate_calib": "",
                "verif_rejection_rate_nom": "",
                "n_validation_rejections": "",
                "p_value_binomial": "",
            })

    # --------------------------------------------------------------------------
    # Parte B: 27 righe "verification"
    # --------------------------------------------------------------------------
    for fit_k in ordered_fits:
        for blk_len in block_lengths:
            for stat_name in STATISTICS:
                c_th = calib_thresholds[(fit_k, blk_len, stat_name)]
                v_calib, v_nom = verif_results[(fit_k, blk_len, stat_name)]
                nom_th = nom_thresholds[stat_name]
                df_val = STATISTIC_DFS[stat_name]

                records.append({
                    "row_type": "verification",
                    "season": "",
                    "role": "",
                    "fit_through": fit_k,
                    "statistic": stat_name,
                    "df": df_val,
                    "method": "block_bootstrap",
                    "block_length": blk_len,
                    "lm_stat": "",
                    "p_value_nom": "",
                    "threshold_nom": nom_th,
                    "reject_nom": "",
                    "threshold_L7": "",
                    "reject_L7": "",
                    "threshold_L20": "",
                    "reject_L20": "",
                    "threshold_L40": "",
                    "reject_L40": "",
                    "calibrated_threshold": c_th,
                    "verif_rejection_rate_calib": v_calib,
                    "verif_rejection_rate_nom": v_nom,
                    "n_validation_rejections": "",
                    "p_value_binomial": "",
                })

    # --------------------------------------------------------------------------
    # Parte C: 12 righe "summary"
    # --------------------------------------------------------------------------
    method_specs = [
        ("nominal", ""),
        ("bootstrap_L7", 7),
        ("bootstrap_L20", 20),
        ("bootstrap_L40", 40),
    ]

    for stat_name in STATISTICS:
        df_val = STATISTIC_DFS[stat_name]
        for m_name, m_blk in method_specs:
            k_val = val_rejections[(stat_name, m_name)]
            p_binom = binomial_exceedance_p_value(k_val, n=19, p=alpha)

            records.append({
                "row_type": "summary",
                "season": "",
                "role": "",
                "fit_through": "",
                "statistic": stat_name,
                "df": df_val,
                "method": m_name,
                "block_length": m_blk,
                "lm_stat": "",
                "p_value_nom": "",
                "threshold_nom": "",
                "reject_nom": "",
                "threshold_L7": "",
                "reject_L7": "",
                "threshold_L20": "",
                "reject_L20": "",
                "threshold_L40": "",
                "reject_L40": "",
                "calibrated_threshold": "",
                "verif_rejection_rate_calib": "",
                "verif_rejection_rate_nom": "",
                "n_validation_rejections": k_val,
                "p_value_binomial": p_binom,
            })

    return records
