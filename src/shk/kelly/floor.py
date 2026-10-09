"""Modulo per l'analisi del floor su calendario sintetico e soglie di rovina (Task 36).

Questo modulo implementa gli esperimenti sintetici a una partita per data per verificare
la predizione teorica della Nota 2.9: il floor sulle puntate (F > 0) e l'unico meccanismo
che rende possibile la rovina del capitale per un agente Kelly (che con F = 0 non si rovina mai).
"""

from dataclasses import dataclass
import math
from typing import Final, Sequence

import numpy as np

from shk.kelly.agents import FractionalKellyAgent
from shk.kelly.environment import AgentRun, floor_thresholds, run_paired_backtest
from shk.kelly.staking import kelly_staking

# ------------------------------------------------------------------------------
# Semi e gerarchia del generatore
# ------------------------------------------------------------------------------
SEED_C6: Final[int] = 20261009

# ------------------------------------------------------------------------------
# Parametri di ingresso ed evidenze della Nota 2.9
# ------------------------------------------------------------------------------
# Configurazione di riferimento dell'Esperimento A (§5.1-§5.3)
EXP_A_ODDS: Final[float] = 2.5
EXP_A_TRUE_EV: Final[float] = -0.02
EXP_A_ESTIMATED_EDGE: Final[float] = 0.03
EXP_A_LAMBDA: Final[float] = 0.25
EXP_A_M: Final[int] = 10_000
EXP_A_HORIZONS_1000F: Final[tuple[int, ...]] = (150, 400, 1000, 3000)
EXP_A_HORIZONS_50F: Final[tuple[int, ...]] = (150, 400, 1000)
EXP_A_RATIO_1000F: Final[float] = 1000.0
EXP_A_RATIO_50F: Final[float] = 50.0

# Valori della Nota 2.9 §5.2-§5.3 per Esperimento A (M = 80 000)
NOTE_EXP_A_M: Final[int] = 80_000
NOTE_EXP_A_RUIN_RATES_50F: Final[dict[int, float]] = {
    150: 0.00149,
    400: 0.07616,
    1000: 0.35760,
}
NOTE_EXP_A_RUIN_RATES_1000F: Final[dict[int, float]] = {
    150: 0.0,
    400: 0.0,
    1000: 0.0,
    3000: 0.0,
}

# Parametri di ingresso dell'Esperimento B (sweep rapporti B0/F)
EXP_B_M: Final[int] = 10_000
EXP_B_T: Final[int] = 1000
EXP_B_HORIZONS: Final[tuple[int, int]] = (150, 1000)
EXP_B_RATIOS: Final[tuple[float, ...]] = (
    10.0**1.0,
    10.0**1.5,
    10.0**2.0,
    10.0**2.5,
    10.0**3.0,
    10.0**3.5,
    10.0**4.0,
    10.0**4.5,
    10.0**5.0,
    10.0**5.5,
    10.0**6.0,
    10.0**6.5,
    10.0**7.0,
    220.0,
    22000.0,
)

# Parametri di ingresso dell'Esperimento C (tempi di rovina e limite, §6.2)
EXP_C_M: Final[int] = 1_000
EXP_C_ODDS: Final[float] = 2.5


@dataclass(frozen=True)
class ExpCConfig:
    """Configurazione di test per l'Esperimento C sui tempi di rovina."""

    config_id: str
    ev_true: float
    lam: float
    edge_est: float
    ratio: float
    note_mu: float
    note_bound: float
    note_acceleration: float


EXP_C_CONFIGS: Final[tuple[ExpCConfig, ...]] = (
    ExpCConfig("a", -0.02, 0.25, 0.03, 50.0, -0.000119, 32986.0, 23.0),
    ExpCConfig("b", -0.04, 1.00, 0.10, 220.0, -0.005905, 913.0, 1.3),
    ExpCConfig("c", -0.05, 1.00, 0.03, 200.0, -0.001293, 4097.0, 2.2),
)

# Schema delle colonne del file CSV dei risultati
FLOOR_SYNTHETIC_CSV_COLUMNS: Final[tuple[str, ...]] = (
    "experiment",
    "config_id",
    "initial_ratio",
    "min_stake",
    "horizon",
    "with_floor",
    "m_replicas",
    "ev_true",
    "lam",
    "edge_est",
    "p_true",
    "p_hat",
    "odds",
    "f_star",
    "f_desired",
    "b1_ratio",
    "b2_ratio",
    "ruin_rate",
    "note_ruin_rate",
    "mc_tol_99",
    "within_tolerance",
    "mu",
    "bound_limit",
    "mean_ruin_time",
    "median_ruin_time",
    "censored_count",
    "acceleration_factor",
    "note_acceleration_factor",
    "p_regime_0",
    "p_regime_1",
    "p_regime_2",
    "p_regime_3",
)

DEFAULT_CHUNK_SIZE: Final[int] = 2_000


# ------------------------------------------------------------------------------
# Generatori e semi
# ------------------------------------------------------------------------------
def spawn_t36_generators(
    seed: int = SEED_C6,
) -> tuple[
    np.random.Generator,
    np.random.Generator,
    tuple[np.random.Generator, np.random.Generator, np.random.Generator],
]:
    """Genera i generatori casuali indipendenti per gli esperimenti A, B e C di T36.

    Seguendo la gerarchia della specifica:
        ss_c6 = SeedSequence(seed).spawn(2)
        figlio 0 (T36), figlio 1 (T37)
        figlio 0.spawn(3) -> ss_exp_a, ss_exp_b, ss_exp_c
        ss_exp_c.spawn(3) -> ss_c_a, ss_c_b, ss_c_c (un generatore per configurazione)

    Parametri
    ---------
    seed : int, default=SEED_C6
        Seed master.

    Restituisce
    -----------
    tuple[np.random.Generator, np.random.Generator, tuple[np.random.Generator, np.random.Generator, np.random.Generator]]
        Tupla con rng_a per Exp A, rng_b per Exp B e la terna (rng_c_a, rng_c_b, rng_c_c) per Exp C.
    """
    ss_c6 = np.random.SeedSequence(seed)
    children_s6 = ss_c6.spawn(2)
    ss_t36 = children_s6[0]
    children_t36 = ss_t36.spawn(3)
    ss_exp_a = children_t36[0]
    ss_exp_b = children_t36[1]
    ss_exp_c = children_t36[2]
    children_exp_c = ss_exp_c.spawn(3)
    return (
        np.random.default_rng(ss_exp_a),
        np.random.default_rng(ss_exp_b),
        (
            np.random.default_rng(children_exp_c[0]),
            np.random.default_rng(children_exp_c[1]),
            np.random.default_rng(children_exp_c[2]),
        ),
    )


# ------------------------------------------------------------------------------
# Funzioni analitiche e statistiche
# ------------------------------------------------------------------------------
def classify_floor_regime(
    wealth: np.ndarray,
    thresholds: tuple[float, float, float],
) -> np.ndarray:
    """Classifica la ricchezza nei quattro regimi definiti dalla Nota 2.9 §4.

    Regimi:
        0 se W >= B1
        1 se B2 <= W < B1
        2 se F <= W < B2
        3 se W < F (regime di rovina)

    Parametri
    ---------
    wealth : np.ndarray
        Array numerico di ricchezza di qualsiasi forma.
    thresholds : tuple[float, float, float]
        Terna delle soglie analitiche (B1, B2, B3) con B3 = F.

    Restituisce
    -----------
    np.ndarray
        Array int64 della stessa forma di wealth con valori in {0, 1, 2, 3}.

    Solleva
    -------
    TypeError
        Se wealth non e un numpy.ndarray o thresholds non e una tupla di 3 float.
    ValueError
        Se le soglie non rispettano l'ordinamento B1 > B2 > B3 > 0.
    """
    if not isinstance(wealth, np.ndarray):
        raise TypeError(f"wealth must be a numpy.ndarray, got {type(wealth).__name__}")
    if not np.issubdtype(wealth.dtype, np.number) or wealth.dtype == np.bool_:
        raise TypeError(f"wealth must have numeric dtype, got {wealth.dtype}")

    if not isinstance(thresholds, (tuple, list)) or len(thresholds) != 3:
        raise TypeError("thresholds must be a tuple of 3 floats")

    b1, b2, b3 = float(thresholds[0]), float(thresholds[1]), float(thresholds[2])
    for val_name, val in (("B1", b1), ("B2", b2), ("B3", b3)):
        if not math.isfinite(val):
            raise ValueError(f"{val_name} must be finite, got {val}")

    if not (b1 > b2 > b3 > 0.0):
        raise ValueError(f"Thresholds must satisfy B1 > B2 > B3 > 0, got ({b1}, {b2}, {b3})")

    regimes = np.full(wealth.shape, 3, dtype=np.int64)
    regimes[wealth >= b1] = 0
    regimes[(wealth >= b2) & (wealth < b1)] = 1
    regimes[(wealth >= b3) & (wealth < b2)] = 2
    return regimes


def expected_ruin_time_bound(
    rapporto: float,
    p: float,
    f: float,
    o: float,
) -> float:
    """Calcola il limite teorico sul tempo medio di rovina della Nota 2.9 §6.2.

    Formula:
        mu = p * ln(1 + f * (o - 1)) + (1 - p) * ln(1 - f)
        bound = ln(rapporto) / |mu|

    Parametri
    ---------
    rapporto : float
        Rapporto tra capitale iniziale e puntata minima B0 / F > 1.
    p : float
        Probabilita reale di vittoria in (0, 1).
    f : float
        Frazione di capitale puntata in (0, 1).
    o : float
        Quota decimale lorda > 1.

    Restituisce
    -----------
    float
        Limite superiore teorico atteso sul tempo di rovina.

    Solleva
    -------
    TypeError
        Se gli argomenti non sono numerici finiti.
    ValueError
        Se i valori sono fuori dai domini consentiti o se mu >= 0.
    """
    for name, val in (("rapporto", rapporto), ("p", p), ("f", f), ("o", o)):
        if isinstance(val, bool) or not isinstance(val, (int, float, np.floating)):
            raise TypeError(f"{name} must be a float, got {type(val).__name__}")
        if not math.isfinite(float(val)):
            raise ValueError(f"{name} must be finite, got {val}")

    r_val = float(rapporto)
    p_val = float(p)
    f_val = float(f)
    o_val = float(o)

    if r_val <= 1.0:
        raise ValueError(f"rapporto must be strictly greater than 1.0, got {rapporto}")
    if not (0.0 < p_val < 1.0):
        raise ValueError(f"p must be in (0, 1), got {p}")
    if not (0.0 < f_val < 1.0):
        raise ValueError(f"f must be in (0, 1), got {f}")
    if o_val <= 1.0:
        raise ValueError(f"o must be strictly greater than 1.0, got {o}")

    log_win = math.log(1.0 + f_val * (o_val - 1.0))
    log_loss = math.log(1.0 - f_val)
    mu = p_val * log_win + (1.0 - p_val) * log_loss

    if mu >= 0.0:
        raise ValueError(f"Expected log drift must be strictly negative, got mu={mu}")

    return math.log(r_val) / abs(mu)


def two_sample_mc_tolerance(
    r1: float,
    r2: float,
    m1: int,
    m2: int,
    z: float = 2.576,
) -> float:
    """Calcola la tolleranza Monte Carlo a due campioni al 99% di confidenza.

    Formula:
        tol = z * sqrt(r_bar * (1 - r_bar) * (1/M1 + 1/M2))
        con r_bar = (M1 * r1 + M2 * r2) / (M1 + M2)

    Parametri
    ---------
    r1 : float
        Tasso di rovina osservato nel primo campione in [0, 1].
    r2 : float
        Tasso di rovina osservato nel secondo campione in [0, 1].
    m1 : int
        Numero di repliche del primo campione > 0.
    m2 : int
        Numero di repliche del secondo campione > 0.
    z : float, default=2.576
        Valore critico standard (2.576 per livello di confidenza 99%).

    Restituisce
    -----------
    float
        Margine di tolleranza statistica per la differenza |r1 - r2|.
    """
    if not (0.0 <= r1 <= 1.0 and 0.0 <= r2 <= 1.0):
        raise ValueError("Ruin rates r1 and r2 must belong to [0, 1]")
    if m1 <= 0 or m2 <= 0:
        raise ValueError("Sample sizes m1 and m2 must be strictly positive")

    r_bar = (m1 * r1 + m2 * r2) / (m1 + m2)
    var = r_bar * (1.0 - r_bar) * (1.0 / m1 + 1.0 / m2)
    if var <= 0.0:
        return 0.0
    return float(z * math.sqrt(var))


# ------------------------------------------------------------------------------
# Generazione dati sintetici
# ------------------------------------------------------------------------------
def synthetic_calendar(n_dates: int) -> np.ndarray:
    """Genera un calendario sintetico di date giornaliere successive.

    Parametri
    ---------
    n_dates : int
        Numero di date distinte da generare (T >= 1).

    Restituisce
    -----------
    np.ndarray
        Array 1D datetime64[D] non decrescente senza NaT di forma (n_dates,).
    """
    if n_dates < 1:
        raise ValueError(f"n_dates must be strictly positive, got {n_dates}")
    base = np.datetime64("2024-01-01", "D")
    return base + np.arange(n_dates, dtype="timedelta64[D]")


def synthetic_match_data(
    p_hat: float,
    odds_val: float,
    n_dates: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Genera le probabilita stimate e le quote per una partita per data.

    Le quote sono fissate a (o, 2.0, 2.0) e le previsioni a (p_hat, (1 - p_hat)/2, (1 - p_hat)/2).
    In questo modo l'EV stimato su D e A e rigorosamente negativo e l'agente
    seleziona sempre e solo l'esito H (0).

    Parametri
    ---------
    p_hat : float
        Probabilita soggettiva stimata su H in (0, 1).
    odds_val : float
        Quota decimale di H > 1.
    n_dates : int
        Numero di partite (T >= 1).

    Restituisce
    -----------
    tuple[np.ndarray, np.ndarray]
        Coppia (probs, odds) di forma (n_dates, 3).
    """
    if not (0.0 < p_hat < 1.0):
        raise ValueError(f"p_hat must be in (0, 1), got {p_hat}")
    if odds_val <= 1.0:
        raise ValueError(f"odds_val must be strictly greater than 1.0, got {odds_val}")
    if n_dates < 1:
        raise ValueError(f"n_dates must be strictly positive, got {n_dates}")

    p_d_a = (1.0 - p_hat) / 2.0
    probs_row = np.array([p_hat, p_d_a, p_d_a], dtype=np.float64)
    odds_row = np.array([odds_val, 2.0, 2.0], dtype=np.float64)

    probs = np.tile(probs_row, (n_dates, 1))
    odds = np.tile(odds_row, (n_dates, 1))
    return probs, odds


def draw_synthetic_outcomes(
    p: float,
    m_replicas: int,
    n_dates: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Estrae la matrice degli esiti realizzati bernoulliani in {0, 1}.

    L'esito 0 (H) e estratto con probabilita p, mentre l'esito 1 (D) e estratto
    con probabilita 1 - p. L'esito 2 (A) ha probabilita 0.

    Parametri
    ---------
    p : float
        Probabilita reale dell'esito H in [0, 1].
    m_replicas : int
        Numero di repliche simulate (M >= 1).
    n_dates : int
        Numero di date (T >= 1).
    rng : np.random.Generator
        Generatore di numeri casuali.

    Restituisce
    -----------
    np.ndarray
        Matrice int64 di forma (m_replicas, n_dates) con valori in {0, 1}.
    """
    if not (0.0 <= p <= 1.0):
        raise ValueError(f"p must be in [0, 1], got {p}")
    if m_replicas < 1 or n_dates < 1:
        raise ValueError("m_replicas and n_dates must be strictly positive")

    uniform_draws = rng.uniform(0.0, 1.0, size=(m_replicas, n_dates))
    outcomes = np.where(uniform_draws < p, np.int64(0), np.int64(1))
    return outcomes


# ------------------------------------------------------------------------------
# Rovina per orizzonte e tempi di rovina
# ------------------------------------------------------------------------------
def compute_ruin_rates_at_horizons(
    wealth: np.ndarray,
    min_stake: float,
    horizons: Sequence[int],
) -> dict[int, float]:
    """Calcola il tasso di rovina cumulativo ad ogni orizzonte temporale.

    Una replica e considerata rovinata all'orizzonte T se W[:, T] < F (con F > 0)
    oppure se W[:, T] == 0.0 (con F = 0).

    Parametri
    ---------
    wealth : np.ndarray
        Matrice di ricchezza di forma (M, D + 1) con colonna 0 pari alla ricchezza iniziale.
    min_stake : float
        Puntata minima fissa F >= 0.
    horizons : Sequence[int]
        Sequenza di orizzonti temporali (1 <= T <= D).

    Restituisce
    -----------
    dict[int, float]
        Dizionario che mappa ciascun orizzonte T nel relativo tasso di rovina empirico in [0, 1].
    """
    m_count, total_cols = wealth.shape
    d_steps = total_cols - 1
    rates: dict[int, float] = {}

    for h in horizons:
        if not (1 <= h <= d_steps):
            raise ValueError(f"Horizon {h} must be in range [1, {d_steps}]")
        col = wealth[:, h]
        if min_stake > 0.0:
            ruined_mask = (col < min_stake) | (col == 0.0)
        else:
            ruined_mask = col == 0.0
        rates[h] = float(np.mean(ruined_mask))

    return rates


def compute_ruin_times(
    wealth: np.ndarray,
    min_stake: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Determina il primo tempo di rovina e il flag di rovina per ciascuna replica.

    Parametri
    ---------
    wealth : np.ndarray
        Matrice di ricchezza di forma (M, D + 1).
    min_stake : float
        Puntata minima F >= 0.

    Restituisce
    -----------
    tuple[np.ndarray, np.ndarray]
        Coppia (times, ruined) di forme (M,) dove times e il primo indice t in [1, D]
        in cui W_t < F (oppure -1 se non rovinata), e ruined e un array booleano.
    """
    m_count, total_cols = wealth.shape
    d_steps = total_cols - 1

    times = np.full(m_count, -1, dtype=np.int64)
    ruined = np.zeros(m_count, dtype=np.bool_)

    if min_stake > 0.0:
        is_ruined_matrix = (wealth[:, 1:] < min_stake) | (wealth[:, 1:] == 0.0)
    else:
        is_ruined_matrix = wealth[:, 1:] == 0.0

    has_any_ruin = np.any(is_ruined_matrix, axis=1)
    ruined[:] = has_any_ruin

    if np.any(has_any_ruin):
        # argmax trova il primo indice True
        first_indices = np.argmax(is_ruined_matrix[has_any_ruin], axis=1) + 1
        times[has_any_ruin] = first_indices

    return times, ruined


# ------------------------------------------------------------------------------
# Esecuzione a blocchi (chunking) per controllo memoria
# ------------------------------------------------------------------------------
def run_paired_chunked(
    agent: FractionalKellyAgent,
    dates: np.ndarray,
    probs: np.ndarray,
    odds: np.ndarray,
    outcomes: np.ndarray,
    min_stake: float,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    record_stakes: bool = False,
) -> AgentRun:
    """Esegue run_paired_backtest a blocchi di repliche preservando l'identita deterministica.

    Parametri
    ---------
    agent : FractionalKellyAgent
        Agente da eseguire.
    dates : np.ndarray
        Array delle date (T,).
    probs : np.ndarray
        Probabilita (T, 3).
    odds : np.ndarray
        Quote (T, 3).
    outcomes : np.ndarray
        Matrice degli esiti (M, T).
    min_stake : float
        Puntata minima F >= 0.
    chunk_size : int, default=DEFAULT_CHUNK_SIZE
        Dimensione massima del blocco di repliche.
    record_stakes : bool, default=False
        Se True, registra anche staked e desired.

    Restituisce
    -----------
    AgentRun
        Risultato aggregato con le stesse dimensioni e valori di un'esecuzione a blocco unico.
    """
    m_total = outcomes.shape[0]
    if chunk_size <= 0:
        raise ValueError(f"chunk_size must be strictly positive, got {chunk_size}")

    if m_total <= chunk_size:
        runs = run_paired_backtest(
            agents=[agent],
            dates=dates,
            probs=probs,
            odds=odds,
            outcomes=outcomes,
            min_stake=min_stake,
            record_stakes=record_stakes,
        )
        return runs[0]

    wealth_parts: list[np.ndarray] = []
    ruined_parts: list[np.ndarray] = []
    ruin_date_index_parts: list[np.ndarray] = []
    n_bets_parts: list[np.ndarray] = []
    n_forced_parts: list[np.ndarray] = []
    n_floored_parts: list[np.ndarray] = []
    n_dropped_parts: list[np.ndarray] = []
    staked_parts: list[np.ndarray] = []
    desired_parts: list[np.ndarray] = []

    unique_dates = dates
    for start_idx in range(0, m_total, chunk_size):
        end_idx = min(start_idx + chunk_size, m_total)
        chunk_outcomes = outcomes[start_idx:end_idx]
        chunk_run = run_paired_backtest(
            agents=[agent],
            dates=dates,
            probs=probs,
            odds=odds,
            outcomes=chunk_outcomes,
            min_stake=min_stake,
            record_stakes=record_stakes,
        )[0]
        unique_dates = chunk_run.dates
        wealth_parts.append(chunk_run.wealth)
        ruined_parts.append(chunk_run.ruined)
        ruin_date_index_parts.append(chunk_run.ruin_date_index)
        n_bets_parts.append(chunk_run.n_bets)
        n_forced_parts.append(chunk_run.n_forced)
        n_floored_parts.append(chunk_run.n_floored)
        n_dropped_parts.append(chunk_run.n_dropped)
        if record_stakes:
            staked_parts.append(chunk_run.staked)
            desired_parts.append(chunk_run.desired)

    return AgentRun(
        name=agent.name,
        dates=unique_dates,
        wealth=np.concatenate(wealth_parts, axis=0),
        ruined=np.concatenate(ruined_parts, axis=0),
        ruin_date_index=np.concatenate(ruin_date_index_parts, axis=0),
        n_bets=np.concatenate(n_bets_parts, axis=0),
        n_forced=np.concatenate(n_forced_parts, axis=0),
        n_floored=np.concatenate(n_floored_parts, axis=0),
        n_dropped=np.concatenate(n_dropped_parts, axis=0),
        staked=np.concatenate(staked_parts, axis=0) if record_stakes else None,
        desired=np.concatenate(desired_parts, axis=0) if record_stakes else None,
    )


# ------------------------------------------------------------------------------
# Risultati strutturati degli esperimenti
# ------------------------------------------------------------------------------
@dataclass(frozen=True)
class ExperimentARunResult:
    """Risultato completo di una configurazione dell'Esperimento A."""

    ratio: float
    min_stake: float
    max_horizon: int
    horizons: tuple[int, ...]
    run_floor: AgentRun
    run_nofloor: AgentRun
    thresholds: tuple[float, float, float]
    f_star: float
    f_desired: float


@dataclass(frozen=True)
class ExperimentBResult:
    """Risultato dello sweep dei rapporti dell'Esperimento B."""

    ratios: tuple[float, ...]
    ruin_rates_150: dict[float, float]
    ruin_rates_1000: dict[float, float]


@dataclass(frozen=True)
class ExperimentCConfigResult:
    """Risultato di una configurazione dell'Esperimento C."""

    config: ExpCConfig
    p_true: float
    p_hat: float
    f_star: float
    f_desired: float
    min_stake: float
    horizon: int
    mu: float
    bound: float
    mean_ruin_time: float
    median_ruin_time: float
    censored_count: int
    acceleration_factor: float
    run: AgentRun


# ------------------------------------------------------------------------------
# Orchestrazione degli esperimenti A, B e C
# ------------------------------------------------------------------------------
def run_experiment_a(
    rng: np.random.Generator,
    m_replicas: int = EXP_A_M,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> tuple[ExperimentARunResult, ExperimentARunResult]:
    """Esegue l'Esperimento A (confronto con e senza floor su partenze 1000F e 50F).

    Parametri
    ---------
    rng : np.random.Generator
        Generatore casuale per l'Esperimento A.
    m_replicas : int, default=EXP_A_M
        Numero di repliche (10 000).
    chunk_size : int, default=DEFAULT_CHUNK_SIZE
        Dimensione del blocco di repliche per l'esecuzione.

    Restituisce
    -----------
    tuple[ExperimentARunResult, ExperimentARunResult]
        Coppia di risultati (risultato_1000F, risultato_50F).
    """
    odds_val = EXP_A_ODDS
    ev_val = EXP_A_TRUE_EV
    edge_val = EXP_A_ESTIMATED_EDGE
    lam_val = EXP_A_LAMBDA

    p_hat = (1.0 + edge_val) / odds_val
    p_true = (1.0 + ev_val) / odds_val
    f_star = kelly_staking(p_hat, odds_val - 1.0, 1.0)
    f_desired = kelly_staking(p_hat, odds_val - 1.0, lam_val)

    # 1. Partenza 1000F (T_max = 3000)
    t_1000f = max(EXP_A_HORIZONS_1000F)
    ratio_1000f = EXP_A_RATIO_1000F
    f_stake_1000f = 1.0 / ratio_1000f
    thresh_1000f = floor_thresholds(f_stake_1000f, f_star, lam_val)

    dates_1000f = synthetic_calendar(t_1000f)
    probs_1000f, odds_arr_1000f = synthetic_match_data(p_hat, odds_val, t_1000f)
    outcomes_1000f = draw_synthetic_outcomes(p_true, m_replicas, t_1000f, rng)

    agent_a = FractionalKellyAgent("A_floor", lam=lam_val)
    agent_a_nofloor = FractionalKellyAgent("A_nofloor", lam=lam_val)

    run_floor_1000f = run_paired_chunked(
        agent=agent_a,
        dates=dates_1000f,
        probs=probs_1000f,
        odds=odds_arr_1000f,
        outcomes=outcomes_1000f,
        min_stake=f_stake_1000f,
        chunk_size=chunk_size,
        record_stakes=True,
    )
    run_nofloor_1000f = run_paired_chunked(
        agent=agent_a_nofloor,
        dates=dates_1000f,
        probs=probs_1000f,
        odds=odds_arr_1000f,
        outcomes=outcomes_1000f,
        min_stake=0.0,
        chunk_size=chunk_size,
        record_stakes=True,
    )

    res_1000f = ExperimentARunResult(
        ratio=ratio_1000f,
        min_stake=f_stake_1000f,
        max_horizon=t_1000f,
        horizons=EXP_A_HORIZONS_1000F,
        run_floor=run_floor_1000f,
        run_nofloor=run_nofloor_1000f,
        thresholds=thresh_1000f,
        f_star=f_star,
        f_desired=f_desired,
    )

    # 2. Partenza 50F (T_max = 1000)
    t_50f = max(EXP_A_HORIZONS_50F)
    ratio_50f = EXP_A_RATIO_50F
    f_stake_50f = 1.0 / ratio_50f
    thresh_50f = floor_thresholds(f_stake_50f, f_star, lam_val)

    dates_50f = synthetic_calendar(t_50f)
    probs_50f, odds_arr_50f = synthetic_match_data(p_hat, odds_val, t_50f)
    outcomes_50f = draw_synthetic_outcomes(p_true, m_replicas, t_50f, rng)

    run_floor_50f = run_paired_chunked(
        agent=agent_a,
        dates=dates_50f,
        probs=probs_50f,
        odds=odds_arr_50f,
        outcomes=outcomes_50f,
        min_stake=f_stake_50f,
        chunk_size=chunk_size,
        record_stakes=True,
    )
    run_nofloor_50f = run_paired_chunked(
        agent=agent_a_nofloor,
        dates=dates_50f,
        probs=probs_50f,
        odds=odds_arr_50f,
        outcomes=outcomes_50f,
        min_stake=0.0,
        chunk_size=chunk_size,
        record_stakes=True,
    )

    res_50f = ExperimentARunResult(
        ratio=ratio_50f,
        min_stake=f_stake_50f,
        max_horizon=t_50f,
        horizons=EXP_A_HORIZONS_50F,
        run_floor=run_floor_50f,
        run_nofloor=run_nofloor_50f,
        thresholds=thresh_50f,
        f_star=f_star,
        f_desired=f_desired,
    )

    return res_1000f, res_50f


def run_experiment_b(
    rng: np.random.Generator,
    m_replicas: int = EXP_B_M,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> ExperimentBResult:
    """Esegue l'Esperimento B (sweep dei rapporti B0/F sugli stessi esiti estratti).

    Parametri
    ---------
    rng : np.random.Generator
        Generatore casuale per l'Esperimento B.
    m_replicas : int, default=EXP_B_M
        Numero di repliche (10 000).
    chunk_size : int, default=DEFAULT_CHUNK_SIZE
        Dimensione del blocco di repliche per l'esecuzione.

    Restituisce
    -----------
    ExperimentBResult
        Risultati dei tassi di rovina a T=150 e T=1000 per ciascun rapporto.
    """
    odds_val = EXP_A_ODDS
    ev_val = EXP_A_TRUE_EV
    edge_val = EXP_A_ESTIMATED_EDGE
    lam_val = EXP_A_LAMBDA
    t_val = EXP_B_T

    p_hat = (1.0 + edge_val) / odds_val
    p_true = (1.0 + ev_val) / odds_val

    dates = synthetic_calendar(t_val)
    probs, odds_arr = synthetic_match_data(p_hat, odds_val, t_val)
    outcomes = draw_synthetic_outcomes(p_true, m_replicas, t_val, rng)

    agent = FractionalKellyAgent("A_sweep", lam=lam_val)
    rates_150: dict[float, float] = {}
    rates_1000: dict[float, float] = {}

    for ratio in EXP_B_RATIOS:
        f_stake = 1.0 / ratio
        run = run_paired_chunked(
            agent=agent,
            dates=dates,
            probs=probs,
            odds=odds_arr,
            outcomes=outcomes,
            min_stake=f_stake,
            chunk_size=chunk_size,
            record_stakes=False,
        )
        rates = compute_ruin_rates_at_horizons(run.wealth, f_stake, EXP_B_HORIZONS)
        rates_150[ratio] = rates[150]
        rates_1000[ratio] = rates[1000]

    return ExperimentBResult(
        ratios=EXP_B_RATIOS,
        ruin_rates_150=rates_150,
        ruin_rates_1000=rates_1000,
    )


def run_experiment_c(
    rngs_c: Sequence[np.random.Generator],
    m_replicas: int = EXP_C_M,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> tuple[ExperimentCConfigResult, ...]:
    """Esegue l'Esperimento C sui tempi medi di rovina e limite teorico.

    Parametri
    ---------
    rngs_c : Sequence[np.random.Generator]
        Sequenza di tre generatori casuali indipendenti, uno per ciascuna configurazione (a, b, c).
    m_replicas : int, default=EXP_C_M
        Numero di repliche (1 000).
    chunk_size : int, default=DEFAULT_CHUNK_SIZE
        Dimensione del blocco di repliche per l'esecuzione.

    Restituisce
    -----------
    tuple[ExperimentCConfigResult, ...]
        Tupla dei risultati per le tre configurazioni (a, b, c).
    """
    if len(rngs_c) != len(EXP_C_CONFIGS):
        raise ValueError(
            f"Expected {len(EXP_C_CONFIGS)} generators for Experiment C, got {len(rngs_c)}"
        )

    odds_val = EXP_C_ODDS
    results: list[ExperimentCConfigResult] = []

    for cfg, rng in zip(EXP_C_CONFIGS, rngs_c):
        p_hat = (1.0 + cfg.edge_est) / odds_val
        p_true = (1.0 + cfg.ev_true) / odds_val
        f_star = kelly_staking(p_hat, odds_val - 1.0, 1.0)
        f_desired = kelly_staking(p_hat, odds_val - 1.0, cfg.lam)

        f_stake = 1.0 / cfg.ratio
        bound = expected_ruin_time_bound(cfg.ratio, p_true, f_desired, odds_val)
        log_win = math.log(1.0 + f_desired * (odds_val - 1.0))
        log_loss = math.log(1.0 - f_desired)
        mu_val = p_true * log_win + (1.0 - p_true) * log_loss

        horizon_multiplier = 10.0 if cfg.config_id == "b" else 2.0
        horizon_t = int(math.ceil(horizon_multiplier * bound))
        dates = synthetic_calendar(horizon_t)
        probs, odds_arr = synthetic_match_data(p_hat, odds_val, horizon_t)
        outcomes = draw_synthetic_outcomes(p_true, m_replicas, horizon_t, rng)

        agent = FractionalKellyAgent(f"A_exp_c_{cfg.config_id}", lam=cfg.lam)
        run = run_paired_chunked(
            agent=agent,
            dates=dates,
            probs=probs,
            odds=odds_arr,
            outcomes=outcomes,
            min_stake=f_stake,
            chunk_size=chunk_size,
            record_stakes=False,
        )

        times, ruined = compute_ruin_times(run.wealth, f_stake)
        censored = int(np.sum(~ruined))
        if censored == 0:
            mean_time = float(np.mean(times))
            median_time = float(np.median(times))
        elif np.any(ruined):
            mean_time = float(np.mean(times[ruined]))
            median_time = float(np.median(times[ruined]))
        else:
            mean_time = -1.0
            median_time = -1.0

        accel = bound / mean_time if mean_time > 0.0 else 0.0

        results.append(
            ExperimentCConfigResult(
                config=cfg,
                p_true=p_true,
                p_hat=p_hat,
                f_star=f_star,
                f_desired=f_desired,
                min_stake=f_stake,
                horizon=horizon_t,
                mu=mu_val,
                bound=bound,
                mean_ruin_time=mean_time,
                median_ruin_time=median_time,
                censored_count=censored,
                acceleration_factor=accel,
                run=run,
            )
        )

    return tuple(results)


# ------------------------------------------------------------------------------
# Generazione record per il CSV
# ------------------------------------------------------------------------------
def evaluate_all_synthetic_experiments(
    seed: int = SEED_C6,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> tuple[
    list[dict[str, str | float | int | bool]],
    tuple[ExperimentARunResult, ExperimentARunResult],
    ExperimentBResult,
    tuple[ExperimentCConfigResult, ...],
]:
    """Esegue tutti gli esperimenti e restituisce la lista dei record per il CSV e gli oggetti risultato.

    Parametri
    ---------
    seed : int, default=SEED_C6
        Seed master.
    chunk_size : int, default=DEFAULT_CHUNK_SIZE
        Dimensione del blocco di repliche per l'esecuzione.

    Restituisce
    -----------
    tuple[...]
        Quadrupla contenente:
        - records: lista dei record dizionario conformi a FLOOR_SYNTHETIC_CSV_COLUMNS;
        - exp_a_res: coppia dei risultati dell'Esperimento A;
        - exp_b_res: risultato dell'Esperimento B;
        - exp_c_res: risultati dell'Esperimento C.
    """
    rng_a, rng_b, rngs_c = spawn_t36_generators(seed)

    exp_a_res = run_experiment_a(rng_a, chunk_size=chunk_size)
    exp_b_res = run_experiment_b(rng_b, chunk_size=chunk_size)
    exp_c_res = run_experiment_c(rngs_c, chunk_size=chunk_size)

    records: list[dict[str, str | float | int | bool]] = []

    # Record Esperimento A
    for res, note_dict in (
        (exp_a_res[0], NOTE_EXP_A_RUIN_RATES_1000F),
        (exp_a_res[1], NOTE_EXP_A_RUIN_RATES_50F),
    ):
        b1_ratio = res.thresholds[0] / res.min_stake
        b2_ratio = res.thresholds[1] / res.min_stake

        rates_floor = compute_ruin_rates_at_horizons(
            res.run_floor.wealth, res.min_stake, res.horizons
        )
        rates_nofloor = compute_ruin_rates_at_horizons(
            res.run_nofloor.wealth, 0.0, res.horizons
        )

        for h in res.horizons:
            # Con floor
            r_floor = rates_floor[h]
            note_r = note_dict.get(h, 0.0)
            mc_tol = two_sample_mc_tolerance(r_floor, note_r, EXP_A_M, NOTE_EXP_A_M)
            within_tol = abs(r_floor - note_r) <= mc_tol

            regimes_h = classify_floor_regime(
                res.run_floor.wealth[:, : h + 1], res.thresholds
            )
            p0 = float(np.mean(regimes_h == 0))
            p1 = float(np.mean(regimes_h == 1))
            p2 = float(np.mean(regimes_h == 2))
            p3 = float(np.mean(regimes_h == 3))

            records.append(
                {
                    "experiment": "A",
                    "config_id": f"A_ratio_{int(res.ratio)}_floor",
                    "initial_ratio": res.ratio,
                    "min_stake": res.min_stake,
                    "horizon": h,
                    "with_floor": True,
                    "m_replicas": EXP_A_M,
                    "ev_true": EXP_A_TRUE_EV,
                    "lam": EXP_A_LAMBDA,
                    "edge_est": EXP_A_ESTIMATED_EDGE,
                    "p_true": (1.0 + EXP_A_TRUE_EV) / EXP_A_ODDS,
                    "p_hat": (1.0 + EXP_A_ESTIMATED_EDGE) / EXP_A_ODDS,
                    "odds": EXP_A_ODDS,
                    "f_star": res.f_star,
                    "f_desired": res.f_desired,
                    "b1_ratio": b1_ratio,
                    "b2_ratio": b2_ratio,
                    "ruin_rate": r_floor,
                    "note_ruin_rate": note_r,
                    "mc_tol_99": mc_tol,
                    "within_tolerance": within_tol,
                    "mu": "",
                    "bound_limit": "",
                    "mean_ruin_time": "",
                    "median_ruin_time": "",
                    "censored_count": "",
                    "acceleration_factor": "",
                    "note_acceleration_factor": "",
                    "p_regime_0": p0,
                    "p_regime_1": p1,
                    "p_regime_2": p2,
                    "p_regime_3": p3,
                }
            )

            # Senza floor
            r_nofloor = rates_nofloor[h]
            records.append(
                {
                    "experiment": "A",
                    "config_id": f"A_ratio_{int(res.ratio)}_nofloor",
                    "initial_ratio": res.ratio,
                    "min_stake": 0.0,
                    "horizon": h,
                    "with_floor": False,
                    "m_replicas": EXP_A_M,
                    "ev_true": EXP_A_TRUE_EV,
                    "lam": EXP_A_LAMBDA,
                    "edge_est": EXP_A_ESTIMATED_EDGE,
                    "p_true": (1.0 + EXP_A_TRUE_EV) / EXP_A_ODDS,
                    "p_hat": (1.0 + EXP_A_ESTIMATED_EDGE) / EXP_A_ODDS,
                    "odds": EXP_A_ODDS,
                    "f_star": res.f_star,
                    "f_desired": res.f_desired,
                    "b1_ratio": b1_ratio,
                    "b2_ratio": b2_ratio,
                    "ruin_rate": r_nofloor,
                    "note_ruin_rate": 0.0,
                    "mc_tol_99": 0.0,
                    "within_tolerance": r_nofloor == 0.0,
                    "mu": "",
                    "bound_limit": "",
                    "mean_ruin_time": "",
                    "median_ruin_time": "",
                    "censored_count": "",
                    "acceleration_factor": "",
                    "note_acceleration_factor": "",
                    "p_regime_0": "",
                    "p_regime_1": "",
                    "p_regime_2": "",
                    "p_regime_3": "",
                }
            )

    # Record Esperimento B
    p_hat_b = (1.0 + EXP_A_ESTIMATED_EDGE) / EXP_A_ODDS
    p_true_b = (1.0 + EXP_A_TRUE_EV) / EXP_A_ODDS
    f_star_b = kelly_staking(p_hat_b, EXP_A_ODDS - 1.0, 1.0)
    f_desired_b = kelly_staking(p_hat_b, EXP_A_ODDS - 1.0, EXP_A_LAMBDA)

    for ratio in exp_b_res.ratios:
        f_stake_b = 1.0 / ratio
        thresh_b = floor_thresholds(f_stake_b, f_star_b, EXP_A_LAMBDA)
        b1_ratio_b = thresh_b[0] / f_stake_b
        b2_ratio_b = thresh_b[1] / f_stake_b

        for h in EXP_B_HORIZONS:
            r_val = exp_b_res.ruin_rates_150[ratio] if h == 150 else exp_b_res.ruin_rates_1000[ratio]
            records.append(
                {
                    "experiment": "B",
                    "config_id": f"B_ratio_{ratio:.4e}",
                    "initial_ratio": ratio,
                    "min_stake": f_stake_b,
                    "horizon": h,
                    "with_floor": True,
                    "m_replicas": EXP_B_M,
                    "ev_true": EXP_A_TRUE_EV,
                    "lam": EXP_A_LAMBDA,
                    "edge_est": EXP_A_ESTIMATED_EDGE,
                    "p_true": p_true_b,
                    "p_hat": p_hat_b,
                    "odds": EXP_A_ODDS,
                    "f_star": f_star_b,
                    "f_desired": f_desired_b,
                    "b1_ratio": b1_ratio_b,
                    "b2_ratio": b2_ratio_b,
                    "ruin_rate": r_val,
                    "note_ruin_rate": "",
                    "mc_tol_99": "",
                    "within_tolerance": "",
                    "mu": "",
                    "bound_limit": "",
                    "mean_ruin_time": "",
                    "median_ruin_time": "",
                    "censored_count": "",
                    "acceleration_factor": "",
                    "note_acceleration_factor": "",
                    "p_regime_0": "",
                    "p_regime_1": "",
                    "p_regime_2": "",
                    "p_regime_3": "",
                }
            )

    # Record Esperimento C
    for c_res in exp_c_res:
        thresh_c = floor_thresholds(c_res.min_stake, c_res.f_star, c_res.config.lam)
        b1_ratio_c = thresh_c[0] / c_res.min_stake
        b2_ratio_c = thresh_c[1] / c_res.min_stake

        records.append(
            {
                "experiment": "C",
                "config_id": f"C_{c_res.config.config_id}",
                "initial_ratio": c_res.config.ratio,
                "min_stake": c_res.min_stake,
                "horizon": c_res.horizon,
                "with_floor": True,
                "m_replicas": EXP_C_M,
                "ev_true": c_res.config.ev_true,
                "lam": c_res.config.lam,
                "edge_est": c_res.config.edge_est,
                "p_true": c_res.p_true,
                "p_hat": c_res.p_hat,
                "odds": EXP_C_ODDS,
                "f_star": c_res.f_star,
                "f_desired": c_res.f_desired,
                "b1_ratio": b1_ratio_c,
                "b2_ratio": b2_ratio_c,
                "ruin_rate": 1.0 - (c_res.censored_count / EXP_C_M),
                "note_ruin_rate": "",
                "mc_tol_99": "",
                "within_tolerance": "",
                "mu": c_res.mu,
                "bound_limit": c_res.bound,
                "mean_ruin_time": c_res.mean_ruin_time,
                "median_ruin_time": c_res.median_ruin_time,
                "censored_count": c_res.censored_count,
                "acceleration_factor": c_res.acceleration_factor,
                "note_acceleration_factor": c_res.config.note_acceleration,
                "p_regime_0": "",
                "p_regime_1": "",
                "p_regime_2": "",
                "p_regime_3": "",
            }
        )

    return records, exp_a_res, exp_b_res, exp_c_res

