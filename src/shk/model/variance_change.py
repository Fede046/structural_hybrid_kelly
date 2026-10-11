"""Diagnostiche della varianza nel tempo sui residui del Modulo 1 raw (T44, seguito di C6.4).

Serie: z_t = residui della log-loss standardizzati per varentropia
(shk.stats.variance_change.varentropy_standardized_residuals), calcolati dalle
probabilità p_home, p_draw, p_away e dall'esito FTR di compute_model_residuals.

Scenari, come in C5 e C6.4: i 3 di training (la stagione j prevista dal fit che termina
in j, 380 partite, in campione) e le 19 stagioni di validazione (ciascuna dal suo fit), in
ordine cronologico.

Statistiche nel tempo, per scenario (parametri fissati dal task: terzi, q = 10, finestra
80, passo 10):
- goldfeld_quandt: F = var(ultimo terzo) / var(primo terzo); test bilaterale. La
  statistica calibrata è |ln F| (rigetto se supera la soglia); quella nominale usa F con
  i quantili alpha/2 e 1 - alpha/2 della F(n3 - 1, n1 - 1). Nel CSV statistic_value è
  |ln F| e statistic_aux è F;
- arch_lm: (n - q) R^2 di z_t^2 sui 10 ritardi; nominale chi quadro con 10 gradi di libertà;
- rolling_log_variance: massimo di |ln(var finestra / var stagione)|; nessuna soglia
  nominale.

Soglie calibrate come in T39: moving block bootstrap della serie di training del fit che
prevede la stagione (z di tutte le righe di training del fit, 380, 760 o 1140 partite),
prime 380 posizioni, B = 999, soglia = 950-esima statistica d'ordine, rigetto stretto;
L in (7, 20, 40) più L_PW = lunghezza di Politis-White circolare (T42) della serie
ricampionata, arrotondata con round_block_length. Verifica su 1 000 ricampionamenti
indipendenti per fit x L x statistica contro l'intervallo con Bonferroni di T39
[BONFERRONI_LOWER, BONFERRONI_UPPER], estremi inclusi.

Varianza fra stagioni: Brown-Forsythe sulle 19 stagioni di validazione di z_t, nominale
F(18, 7201). Soglia calibrata ricampionando la serie di training concatenata, cioè i tre
scenari di training in ordine cronologico (1140 partite), in 19 pseudo-stagioni da 380:
moving block bootstrap di lunghezza 7220 (moving_block_indices_of_length), stesse L.

Seed: SeedSequence(SEED_S7).spawn(5)[4] (T44 è in posizione 4 della story S7), diviso con
spawn(4): figli 0, 1, 2 per i fit in ordine cronologico, figlio 3 per Brown-Forsythe; ogni
figlio con spawn(4), uno per L nell'ordine (7, 20, 40, L_PW); ogni L con spawn(2):
calibrazione, verifica.
"""

from typing import Final, NamedTuple

import numpy as np
import pandas as pd

from shk.model.elo_fit import parse_season_start_year
from shk.model.residual_heteroskedasticity import (
    BONFERRONI_LOWER,
    BONFERRONI_UPPER,
    binomial_exceedance_p_value,
)
from shk.stats.bootstrap import optimal_block_length, round_block_length
from shk.stats.calibration import compute_order_statistic_index, moving_block_indices
from shk.stats.false_rejection import (
    ALPHA,
    BLOCK_LENGTHS,
    N_BOOT,
    N_STORY_TASKS,
    SEED_S7,
)
from shk.stats.variance_change import (
    ARCH_LAGS,
    ROLLING_STEP,
    ROLLING_WINDOW,
    arch_lm,
    arch_lm_nominal_threshold,
    brown_forsythe,
    brown_forsythe_nominal_threshold,
    goldfeld_quandt_nominal_bounds,
    goldfeld_quandt_thirds,
    moving_block_indices_of_length,
    rolling_log_variance_max,
    varentropy_standardized_residuals,
)

T44_STORY_POSITION: Final[int] = 4
MATCHES_PER_SEASON: Final[int] = 380
N_VERIF_RESAMPLES: Final[int] = 1_000
N_VALIDATION_SEASONS: Final[int] = 19

STAT_GOLDFELD_QUANDT: Final[str] = "goldfeld_quandt"
STAT_ARCH_LM: Final[str] = "arch_lm"
STAT_ROLLING: Final[str] = "rolling_log_variance"
STAT_BROWN_FORSYTHE: Final[str] = "brown_forsythe"
TIME_STATISTICS: Final[tuple[str, ...]] = (STAT_GOLDFELD_QUANDT, STAT_ARCH_LM, STAT_ROLLING)

METHOD_NOMINAL: Final[str] = "nominal"
METHOD_LPW: Final[str] = "mbb_LPW"
CALIBRATED_METHODS: Final[tuple[str, ...]] = tuple(f"mbb_L{l}" for l in BLOCK_LENGTHS) + (
    METHOD_LPW,
)
BF_REFERENCE_LABEL: Final[str] = "training_concatenated"

_FTR_TO_INDEX: Final[dict[str, int]] = {"H": 0, "D": 1, "A": 2}

VARIANCE_CHANGE_CSV_COLUMNS: Final[tuple[str, ...]] = (
    "row_type",
    "season",
    "role",
    "fit_through",
    "statistic",
    "method",
    "block_length",
    "n_obs",
    "statistic_value",
    "statistic_aux",
    "threshold",
    "threshold_lower",
    "reject",
    "n_resamples",
    "rejections",
    "rejection_rate",
    "mc_lower",
    "mc_upper",
    "within_interval",
    "n_validation",
    "p_value_binomial",
    "z_mean",
    "z_var",
)


class VarianceScenario(NamedTuple):
    """Serie z di uno scenario (stagione)."""

    season: str
    role: str
    fit_through: str
    z: np.ndarray


class VarianceData(NamedTuple):
    """Serie z degli scenari, delle serie di training per fit e del riferimento fra stagioni."""

    scenarios: tuple[VarianceScenario, ...]
    training_by_fit: dict[str, np.ndarray]
    bf_reference: np.ndarray


def standardized_residuals_from_frame(frame: pd.DataFrame) -> np.ndarray:
    """z_t per le righe di un DataFrame di compute_model_residuals.

    Solleva
    -------
    ValueError
        Se mancano colonne o FTR non è in H, D, A.
    """
    for col in ("p_home", "p_draw", "p_away", "FTR"):
        if col not in frame.columns:
            raise ValueError(f"Column '{col}' not found in residuals")
    ftr = frame["FTR"].astype(str).str.strip()
    if not ftr.isin(list(_FTR_TO_INDEX)).all():
        raise ValueError("FTR must contain only H, D, A")
    probs = frame[["p_home", "p_draw", "p_away"]].to_numpy(dtype=np.float64)
    outcomes = ftr.map(_FTR_TO_INDEX).to_numpy(dtype=np.int64)
    return varentropy_standardized_residuals(probs, outcomes)


def extract_variance_data(
    residuals: pd.DataFrame,
    schedule: dict[str, dict[str, list[str]]],
    expected_matches: int = MATCHES_PER_SEASON,
) -> VarianceData:
    """Scenari, serie di training per fit e riferimento di Brown-Forsythe.

    Solleva
    -------
    ValueError
        Se uno scenario non ha expected_matches partite.
    """
    fits = sorted(schedule.keys(), key=parse_season_start_year)
    scenarios: list[VarianceScenario] = []
    training_by_fit: dict[str, np.ndarray] = {}
    for fit in fits:
        fit_rows = residuals[residuals["fit_through"] == fit]
        train_rows = fit_rows[fit_rows["role"] == "training"]
        training_by_fit[fit] = standardized_residuals_from_frame(train_rows)
        own = train_rows[train_rows["season"] == fit]
        scenarios.append(
            VarianceScenario(fit, "training", fit, standardized_residuals_from_frame(own))
        )
        for season in schedule[fit]["validation"]:
            rows = fit_rows[(fit_rows["role"] == "validation") & (fit_rows["season"] == season)]
            scenarios.append(
                VarianceScenario(season, "validation", fit, standardized_residuals_from_frame(rows))
            )
    scenarios.sort(key=lambda s: parse_season_start_year(s.season))
    for sc in scenarios:
        if sc.z.shape[0] != expected_matches:
            raise ValueError(
                f"Scenario {sc.season} has {sc.z.shape[0]} matches, expected {expected_matches}"
            )
    bf_reference = np.concatenate([sc.z for sc in scenarios if sc.role == "training"])
    return VarianceData(tuple(scenarios), training_by_fit, bf_reference)


def time_statistics(z: np.ndarray) -> dict[str, np.ndarray | float]:
    """Statistiche calibrabili nel tempo: |ln F| di Goldfeld-Quandt, ARCH-LM, rolling."""
    gq = goldfeld_quandt_thirds(z)
    return {
        STAT_GOLDFELD_QUANDT: np.abs(np.log(gq)),
        STAT_ARCH_LM: arch_lm(z, ARCH_LAGS),
        STAT_ROLLING: rolling_log_variance_max(z, ROLLING_WINDOW, ROLLING_STEP),
    }


def spawn_t44_generators(
    seed: int = SEED_S7,
) -> tuple[list[list[tuple[np.random.Generator, np.random.Generator]]], ...]:
    """Generatori (calibrazione, verifica) per 3 fit e Brown-Forsythe, 4 L ciascuno.

    Restituisce
    -----------
    tuple
        4 elementi (fit 0, 1, 2 e Brown-Forsythe); ciascuno lista di 4 coppie, una per L.

    Solleva
    -------
    TypeError
        Se seed non è un intero valido.
    """
    if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)):
        raise TypeError(f"seed must be an integer, got {type(seed).__name__}")
    task_seed = np.random.SeedSequence(seed).spawn(N_STORY_TASKS)[T44_STORY_POSITION]
    groups = []
    for child in task_seed.spawn(4):
        pairs = []
        for l_seed in child.spawn(len(CALIBRATED_METHODS)):
            calib, verif = l_seed.spawn(2)
            pairs.append((np.random.default_rng(calib), np.random.default_rng(verif)))
        groups.append(pairs)
    return tuple(groups)


def _block_lengths_for(series: np.ndarray) -> tuple[int, ...]:
    """(7, 20, 40, L_PW circolare arrotondata della serie)."""
    return tuple(BLOCK_LENGTHS) + (round_block_length(optimal_block_length(series).circular),)


def _time_threshold_and_rate(
    series: np.ndarray, block_length: int, calib_rng: np.random.Generator,
    verif_rng: np.random.Generator,
) -> tuple[dict[str, float], dict[str, int]]:
    """Soglie (B = N_BOOT) e rigetti di verifica (N_VERIF_RESAMPLES) per le tre statistiche."""
    k_order = compute_order_statistic_index(N_BOOT, ALPHA)
    n = series.shape[0]
    calib_idx = moving_block_indices(n, block_length, N_BOOT, calib_rng)[:, :MATCHES_PER_SEASON]
    calib_stats = time_statistics(series[calib_idx])
    thresholds = {s: float(np.sort(calib_stats[s])[k_order - 1]) for s in TIME_STATISTICS}
    verif_idx = moving_block_indices(n, block_length, N_VERIF_RESAMPLES, verif_rng)[
        :, :MATCHES_PER_SEASON
    ]
    verif_stats = time_statistics(series[verif_idx])
    rejections = {s: int(np.sum(verif_stats[s] > thresholds[s])) for s in TIME_STATISTICS}
    return thresholds, rejections


def _bf_threshold_and_rate(
    reference: np.ndarray, block_length: int, calib_rng: np.random.Generator,
    verif_rng: np.random.Generator,
) -> tuple[float, int]:
    """Soglia e rigetti di verifica di Brown-Forsythe su 19 pseudo-stagioni da 380."""
    k_order = compute_order_statistic_index(N_BOOT, ALPHA)
    length = N_VALIDATION_SEASONS * MATCHES_PER_SEASON
    n = reference.shape[0]
    shape = (N_VALIDATION_SEASONS, MATCHES_PER_SEASON)

    idx = moving_block_indices_of_length(n, length, block_length, N_BOOT, calib_rng)
    calib = brown_forsythe(reference[idx].reshape((N_BOOT,) + shape))
    threshold = float(np.sort(calib)[k_order - 1])
    idx = moving_block_indices_of_length(n, length, block_length, N_VERIF_RESAMPLES, verif_rng)
    verif = brown_forsythe(reference[idx].reshape((N_VERIF_RESAMPLES,) + shape))
    return threshold, int(np.sum(verif > threshold))


def _record(**fields: object) -> dict[str, object]:
    """Record con tutte le colonne, vuote dove non indicate."""
    record: dict[str, object] = {col: "" for col in VARIANCE_CHANGE_CSV_COLUMNS}
    for key, value in fields.items():
        if key not in record:
            raise KeyError(key)
        record[key] = value
    return record


def evaluate_variance_change(
    residuals: pd.DataFrame,
    schedule: dict[str, dict[str, list[str]]],
    seed: int = SEED_S7,
) -> list[dict[str, object]]:
    """Calcola tutti i record del CSV results/us_c6_4b_variance_change.csv.

    Tipi di riga, nell'ordine: "z_moments" (22), "scenario" (22 scenari x righe per
    statistica e metodo: 5 per Goldfeld-Quandt e ARCH-LM, 4 per la rolling), "verification"
    (3 fit x 3 statistiche x 4 L, poi 4 righe di Brown-Forsythe), "summary" (rigetti sulle
    19 stagioni di validazione per statistica e metodo, con P(X >= k) sotto
    Binomiale(19, ALPHA)), "between_seasons" (Brown-Forsythe, nominale e 4 L).

    Solleva
    -------
    ValueError
        Se le stagioni di validazione non sono N_VALIDATION_SEASONS o uno scenario non ha
        380 partite.
    """
    data = extract_variance_data(residuals, schedule)
    validation = [sc for sc in data.scenarios if sc.role == "validation"]
    if len(validation) != N_VALIDATION_SEASONS:
        raise ValueError(f"Expected {N_VALIDATION_SEASONS} validation seasons, got {len(validation)}")

    fits = sorted(schedule.keys(), key=parse_season_start_year)
    generators = spawn_t44_generators(seed)

    # Soglie calibrate e verifica per fit, L e statistica
    thresholds: dict[tuple[str, str], dict[str, float]] = {}
    block_used: dict[tuple[str, str], int] = {}
    verification_records: list[dict[str, object]] = []
    for fit, pairs in zip(fits, generators[:3]):
        series = data.training_by_fit[fit]
        for method, l_val, (calib_rng, verif_rng) in zip(
            CALIBRATED_METHODS, _block_lengths_for(series), pairs
        ):
            thr, rej = _time_threshold_and_rate(series, l_val, calib_rng, verif_rng)
            thresholds[(fit, method)] = thr
            block_used[(fit, method)] = l_val
            for stat in TIME_STATISTICS:
                rate = rej[stat] / N_VERIF_RESAMPLES
                verification_records.append(
                    _record(
                        row_type="verification", fit_through=fit, statistic=stat,
                        method=method, block_length=l_val, n_obs=int(series.shape[0]),
                        threshold=thr[stat], n_resamples=N_VERIF_RESAMPLES,
                        rejections=rej[stat], rejection_rate=rate,
                        mc_lower=BONFERRONI_LOWER, mc_upper=BONFERRONI_UPPER,
                        within_interval=bool(BONFERRONI_LOWER <= rate <= BONFERRONI_UPPER),
                    )
                )

    bf_thresholds: dict[str, tuple[int, float]] = {}
    for method, l_val, (calib_rng, verif_rng) in zip(
        CALIBRATED_METHODS, _block_lengths_for(data.bf_reference), generators[3]
    ):
        thr, rej = _bf_threshold_and_rate(data.bf_reference, l_val, calib_rng, verif_rng)
        bf_thresholds[method] = (l_val, thr)
        rate = rej / N_VERIF_RESAMPLES
        verification_records.append(
            _record(
                row_type="verification", fit_through=BF_REFERENCE_LABEL,
                statistic=STAT_BROWN_FORSYTHE, method=method, block_length=l_val,
                n_obs=int(data.bf_reference.shape[0]), threshold=thr,
                n_resamples=N_VERIF_RESAMPLES, rejections=rej, rejection_rate=rate,
                mc_lower=BONFERRONI_LOWER, mc_upper=BONFERRONI_UPPER,
                within_interval=bool(BONFERRONI_LOWER <= rate <= BONFERRONI_UPPER),
            )
        )

    gq_lower, gq_upper = goldfeld_quandt_nominal_bounds(MATCHES_PER_SEASON, ALPHA)
    arch_nominal = arch_lm_nominal_threshold(ARCH_LAGS, ALPHA)

    moment_records: list[dict[str, object]] = []
    scenario_records: list[dict[str, object]] = []
    rejection_counts: dict[tuple[str, str], int] = {}
    for sc in data.scenarios:
        moment_records.append(
            _record(
                row_type="z_moments", season=sc.season, role=sc.role, fit_through=sc.fit_through,
                n_obs=int(sc.z.shape[0]), z_mean=float(sc.z.mean()), z_var=float(sc.z.var(ddof=1)),
            )
        )
        stats = time_statistics(sc.z)
        gq_ratio = float(goldfeld_quandt_thirds(sc.z))
        base = {"season": sc.season, "role": sc.role, "fit_through": sc.fit_through,
                "n_obs": int(sc.z.shape[0])}
        for stat in TIME_STATISTICS:
            value = float(stats[stat])
            aux = gq_ratio if stat == STAT_GOLDFELD_QUANDT else ""
            rows: list[tuple[str, object, object, object, bool]] = []
            if stat == STAT_GOLDFELD_QUANDT:
                rows.append((METHOD_NOMINAL, "", gq_upper, gq_lower,
                             bool(gq_ratio > gq_upper or gq_ratio < gq_lower)))
            elif stat == STAT_ARCH_LM:
                rows.append((METHOD_NOMINAL, "", arch_nominal, "", bool(value > arch_nominal)))
            for method in CALIBRATED_METHODS:
                thr = thresholds[(sc.fit_through, method)][stat]
                rows.append((method, block_used[(sc.fit_through, method)], thr, "",
                             bool(value > thr)))
            for method, l_val, thr, thr_lower, reject in rows:
                scenario_records.append(
                    _record(row_type="scenario", statistic=stat, method=method,
                            block_length=l_val, statistic_value=value, statistic_aux=aux,
                            threshold=thr, threshold_lower=thr_lower, reject=reject, **base)
                )
                if sc.role == "validation":
                    key = (stat, method)
                    rejection_counts[key] = rejection_counts.get(key, 0) + int(reject)

    summary_records = [
        _record(
            row_type="summary", statistic=stat, method=method, n_validation=N_VALIDATION_SEASONS,
            rejections=count, p_value_binomial=binomial_exceedance_p_value(count),
        )
        for (stat, method), count in rejection_counts.items()
    ]

    groups = np.stack([sc.z for sc in validation])
    bf_value = float(brown_forsythe(groups))
    bf_nominal = brown_forsythe_nominal_threshold(N_VALIDATION_SEASONS, MATCHES_PER_SEASON, ALPHA)
    between_records = [
        _record(row_type="between_seasons", statistic=STAT_BROWN_FORSYTHE, method=METHOD_NOMINAL,
                n_obs=int(groups.size), statistic_value=bf_value, threshold=bf_nominal,
                reject=bool(bf_value > bf_nominal), n_validation=N_VALIDATION_SEASONS)
    ]
    for method in CALIBRATED_METHODS:
        l_val, thr = bf_thresholds[method]
        between_records.append(
            _record(row_type="between_seasons", statistic=STAT_BROWN_FORSYTHE, method=method,
                    block_length=l_val, n_obs=int(groups.size), statistic_value=bf_value,
                    threshold=thr, reject=bool(bf_value > thr), n_validation=N_VALIDATION_SEASONS)
        )

    return moment_records + scenario_records + verification_records + summary_records + between_records
