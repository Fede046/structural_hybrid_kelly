"""Modulo 2 su finestre scorrevoli.

Gruppi (decisione di progetto, opzione (c) della nota 1.5 §9.4): alla data di decisione D, fra le
partite con Date strettamente anteriore a D della catena di stagioni di D, B = le ultime W
partite e A = le W precedenti. La catena è la serie cronologica che attraversa le stagioni
finché la precedente ha δ: si interrompe dove manca una stagione (per esempio fra 2000-01
e 2002-03, perché il 2001-02 non ha δ). Con meno di 2W partite anteriori lo stato è "non
attivo"; se uno dei due disegni ha rango non pieno lo stato è "rank_deficient".

Uscita: three-fold con π, two-fold per ogni riferimento, dettagliata con Yun (i flag sono
blocchi di dummy con il livello 0 omesso), numerosità e media di δ per finestra (ĝ della
finestra), indeterminatezza = (max − min delle spiegate delle two-fold) / |totale|.

Date di decisione: le Date distinte di ogni stagione (le date dell'ambiente). Intervalli a
fine matchday (blocchi di 10 partite del monitoraggio dei residui): per il matchday m la data di decisione è la
prima Date della stagione strettamente successiva a quella della partita 10m; per m = 38,
il giorno dopo l'ultima partita. Intervalli al 95% per stationary bootstrap dentro ciascuna
finestra (righe ricampionate insieme a δ), a L_PW stationary arrotondata del δ della
finestra, percentili per statistiche d'ordine sui ricampionamenti a rango pieno. Seed:
SeedSequence(SEED_S8).spawn(5)[2] (posizione 2), spawn(len(MODULE2_WINDOWS)) per W,
spawn(numero di stagioni) per stagione in ordine cronologico; ogni generatore si usa in
sequenza sui matchday, prima per A e poi per B.
"""

import math
from collections.abc import Mapping, Sequence
from typing import Final, NamedTuple

import numpy as np
import pandas as pd

from shk.model.covariate_inspection import FLAG_COVARIATES, MODULE2_WINDOWS
from shk.model.elo_fit import parse_season_start_year
from shk.model.task_seeds import task_sequence
from shk.stats.bootstrap import (
    optimal_block_length,
    round_block_length,
    stationary_bootstrap_indices,
)
from shk.stats.calibration import compute_order_statistic_index
from shk.stats.false_rejection import ALPHA
from shk.stats.oaxaca import (
    TWOFOLD_REFERENCES,
    OaxacaResult,
    oaxaca_blinder,
    three_fold_batch,
)
from shk.stats.oaxaca_synthetic import N_STORY_TASKS, SEED_S8

T47_STORY_POSITION: Final[int] = 2
STATE_ACTIVE: Final[str] = "active"
STATE_NOT_ACTIVE: Final[str] = "not_active"
STATE_RANK_DEFICIENT: Final[str] = "rank_deficient"
MATCHDAY_SIZE: Final[int] = 10
N_BOOT_CI: Final[int] = 999
COMPONENTS: Final[tuple[str, ...]] = ("total", "compositional", "structural", "interaction")


class Module2Output(NamedTuple):
    """Uscita del Modulo 2 a una data di decisione per una finestra W."""

    season: str
    decision_date: pd.Timestamp
    window: int
    state: str
    n_eligible: int
    n_a: int
    n_b: int
    mean_a: float
    mean_b: float
    result: OaxacaResult | None
    indeterminacy: float


def season_chain_ids(seasons: Sequence[str]) -> dict[str, int]:
    """Catene di stagioni consecutive: una nuova catena dove manca la stagione precedente."""
    ordered = sorted(set(seasons), key=parse_season_start_year)
    chains: dict[str, int] = {}
    chain = -1
    previous_year: int | None = None
    for s in ordered:
        year = parse_season_start_year(s)
        if previous_year is None or year != previous_year + 1:
            chain += 1
        chains[s] = chain
        previous_year = year
    return chains


def eligible_mask(dates: np.ndarray, decision_date: np.datetime64) -> np.ndarray:
    """Partite ammesse: Date strettamente anteriore alla data di decisione."""
    return dates < decision_date


def flag_dummy_blocks(covariates: Sequence[str]) -> dict[str, list[int]]:
    """Blocchi di Yun: ogni flag è una dummy con il livello 0 omesso."""
    return {f"{c}_0": [i] for i, c in enumerate(covariates) if c in FLAG_COVARIATES}


class Module2Data(NamedTuple):
    """Array del DataFrame per partita, ordinati per stagione e Date, per le chiamate online."""

    seasons: np.ndarray
    dates: np.ndarray
    chain: np.ndarray
    delta: np.ndarray
    x: np.ndarray
    covariates: tuple[str, ...]


def prepare_module2_data(frame: pd.DataFrame, covariates: Sequence[str]) -> Module2Data:
    """Ordina il DataFrame per stagione cronologica e Date stabile ed estrae gli array.

    Solleva
    -------
    ValueError
        Se mancano colonne.
    """
    needed = ["season", "Date", "delta", *covariates]
    missing = [c for c in needed if c not in frame.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    years = frame["season"].map(parse_season_start_year)
    ordered = frame.assign(_year=years).sort_values(["_year", "Date"], kind="stable")
    chains = season_chain_ids(list(ordered["season"].unique()))
    return Module2Data(
        seasons=ordered["season"].to_numpy(),
        dates=ordered["Date"].to_numpy(dtype="datetime64[ns]"),
        chain=ordered["season"].map(chains).to_numpy(dtype=np.int64),
        delta=ordered["delta"].to_numpy(dtype=np.float64),
        x=ordered[list(covariates)].to_numpy(dtype=np.float64),
        covariates=tuple(covariates),
    )


def _window_rows(data: Module2Data, season: str, decision_date: np.datetime64, window: int) -> np.ndarray:
    """Indici ammessi in ordine cronologico per la stagione e la data di decisione."""
    chain = data.chain[np.flatnonzero(data.seasons == season)[0]]
    mask = (data.chain == chain) & eligible_mask(data.dates, decision_date)
    return np.flatnonzero(mask)


def _full_rank(x: np.ndarray) -> bool:
    design = np.column_stack([np.ones(x.shape[0]), x])
    return bool(np.linalg.matrix_rank(design) == design.shape[1])


def module2_at_date(
    data: Module2Data,
    season: str,
    decision_date: pd.Timestamp | np.datetime64,
    window: int,
) -> Module2Output:
    """Uscita online del Modulo 2 alla data di decisione, solo con partite anteriori.

    Parametri
    ---------
    data : Module2Data
        Da prepare_module2_data.
    season : str
        Stagione della data di decisione (stabilisce la catena).
    decision_date : pd.Timestamp o np.datetime64
        Data di decisione D; si usano le partite con Date < D.
    window : int
        W, numero di partite per finestra (>= numero di covariate + 2).

    Solleva
    -------
    ValueError
        Se la stagione non è nei dati o W è troppo piccola.
    """
    if season not in set(data.seasons):
        raise ValueError(f"Season {season} not in data")
    if isinstance(window, bool) or not isinstance(window, (int, np.integer)) or window < len(data.covariates) + 2:
        raise ValueError(f"window must be an integer >= {len(data.covariates) + 2}, got {window}")
    d = np.datetime64(pd.Timestamp(decision_date), "ns")
    rows = _window_rows(data, season, d, int(window))
    n_eligible = int(rows.size)
    ts = pd.Timestamp(d)
    if n_eligible < 2 * window:
        return Module2Output(season, ts, int(window), STATE_NOT_ACTIVE, n_eligible, 0, 0,
                             math.nan, math.nan, None, math.nan)
    idx_a = rows[-2 * window:-window]
    idx_b = rows[-window:]
    xa, xb = data.x[idx_a], data.x[idx_b]
    ya, yb = data.delta[idx_a], data.delta[idx_b]
    mean_a, mean_b = float(ya.mean()), float(yb.mean())
    if not (_full_rank(xa) and _full_rank(xb)):
        return Module2Output(season, ts, int(window), STATE_RANK_DEFICIENT, n_eligible, int(window),
                             int(window), mean_a, mean_b, None, math.nan)
    res = oaxaca_blinder(xa, ya, xb, yb, names=data.covariates,
                         dummy_blocks=flag_dummy_blocks(data.covariates))
    explained = [res.twofold[r].explained for r in TWOFOLD_REFERENCES]
    indeterminacy = (max(explained) - min(explained)) / abs(res.total) if res.total != 0.0 else math.inf
    return Module2Output(season, ts, int(window), STATE_ACTIVE, n_eligible, int(window), int(window),
                         mean_a, mean_b, res, float(indeterminacy))


def season_decision_dates(data: Module2Data, season: str) -> list[pd.Timestamp]:
    """Date distinte della stagione, in ordine."""
    return [pd.Timestamp(d) for d in np.unique(data.dates[data.seasons == season])]


def matchday_decision_dates(data: Module2Data, season: str) -> list[pd.Timestamp]:
    """Data di decisione a fine matchday m = prima Date successiva alla partita 10m (vedi modulo)."""
    dates = data.dates[data.seasons == season]
    n_md = dates.size // MATCHDAY_SIZE
    unique = np.unique(dates)
    out: list[pd.Timestamp] = []
    for m in range(1, n_md + 1):
        last = dates[m * MATCHDAY_SIZE - 1]
        later = unique[unique > last]
        out.append(pd.Timestamp(later[0]) if later.size else pd.Timestamp(last) + pd.Timedelta(days=1))
    return out


def spawn_t47_generators(seasons: Sequence[str], seed: int | np.random.SeedSequence = SEED_S8) -> dict[tuple[int, str], np.random.Generator]:
    """Generatore per (W, stagione), schema nella docstring del modulo."""
    ordered = sorted(seasons, key=parse_season_start_year)
    task_seed = task_sequence(seed, T47_STORY_POSITION, N_STORY_TASKS)
    out: dict[tuple[int, str], np.random.Generator] = {}
    for w, w_seed in zip(MODULE2_WINDOWS, task_seed.spawn(len(MODULE2_WINDOWS))):
        for s, s_seed in zip(ordered, w_seed.spawn(len(ordered))):
            out[(w, s)] = np.random.default_rng(s_seed)
    return out


class Module2Interval(NamedTuple):
    """Intervallo al 95% delle componenti in una finestra a fine matchday."""

    lower: dict[str, float]
    upper: dict[str, float]
    n_valid: int
    block_length_a: int
    block_length_b: int


def module2_bootstrap_interval(
    data: Module2Data,
    season: str,
    decision_date: pd.Timestamp,
    window: int,
    rng: np.random.Generator,
    n_boot: int = N_BOOT_CI,
    alpha: float = ALPHA,
) -> Module2Interval | None:
    """Intervallo percentile delle componenti per stationary bootstrap dentro ciascuna finestra.

    Restituisce None se il Modulo 2 non è attivo alla data (nessuna estrazione da rng).
    """
    d = np.datetime64(pd.Timestamp(decision_date), "ns")
    rows = _window_rows(data, season, d, window)
    if rows.size < 2 * window:
        return None
    idx_a, idx_b = rows[-2 * window:-window], rows[-window:]
    xa, ya = data.x[idx_a], data.delta[idx_a]
    xb, yb = data.x[idx_b], data.delta[idx_b]
    l_a = round_block_length(optimal_block_length(ya).stationary)
    l_b = round_block_length(optimal_block_length(yb).stationary)
    boot_a = stationary_bootstrap_indices(window, l_a, n_boot, rng)
    boot_b = stationary_bootstrap_indices(window, l_b, n_boot, rng)
    batch = three_fold_batch(xa[boot_a], ya[boot_a], xb[boot_b], yb[boot_b])
    n_valid = int(batch.valid.sum())
    lower: dict[str, float] = {}
    upper: dict[str, float] = {}
    if n_valid >= 1:
        k_hi = compute_order_statistic_index(n_valid, alpha / 2.0)
        k_lo = compute_order_statistic_index(n_valid, 1.0 - alpha / 2.0)
    for comp in COMPONENTS:
        values = np.sort(getattr(batch, comp)[batch.valid])
        lower[comp] = float(values[k_lo - 1]) if n_valid >= 1 else math.nan
        upper[comp] = float(values[k_hi - 1]) if n_valid >= 1 else math.nan
    return Module2Interval(lower, upper, n_valid, l_a, l_b)


def module2_record_columns(covariates: Sequence[str]) -> tuple[str, ...]:
    """Colonne del CSV a una riga per data e W."""
    detail_names = ("intercept", *covariates, *flag_dummy_blocks(covariates).keys())
    return (
        "season", "role", "decision_date", "window", "state", "n_eligible", "n_a", "n_b",
        "mean_a", "mean_b", *COMPONENTS, "structural_share", "indeterminacy",
        *[f"explained_{r}" for r in TWOFOLD_REFERENCES],
        *[f"unexplained_{r}" for r in TWOFOLD_REFERENCES],
        *[f"detail_{c}_{n}" for c in ("compositional", "structural", "interaction") for n in detail_names],
    )


def module2_record(out: Module2Output, role: str, covariates: Sequence[str]) -> dict[str, object]:
    """Riga del CSV per un'uscita del Modulo 2 (campi vuoti se non attivo)."""
    rec: dict[str, object] = {c: "" for c in module2_record_columns(covariates)}
    rec.update(
        season=out.season, role=role, decision_date=out.decision_date.strftime("%Y-%m-%d"),
        window=out.window, state=out.state, n_eligible=out.n_eligible, n_a=out.n_a, n_b=out.n_b,
    )
    if out.state != STATE_NOT_ACTIVE:
        rec.update(mean_a=out.mean_a, mean_b=out.mean_b)
    if out.result is not None:
        res = out.result
        rec.update(total=res.total, compositional=res.compositional, structural=res.structural,
                   interaction=res.interaction, structural_share=res.structural_share,
                   indeterminacy=out.indeterminacy)
        for r in TWOFOLD_REFERENCES:
            rec[f"explained_{r}"] = res.twofold[r].explained
            rec[f"unexplained_{r}"] = res.twofold[r].unexplained
        for comp in ("compositional", "structural", "interaction"):
            for name, value in zip(res.detailed.names, getattr(res.detailed, comp)):
                rec[f"detail_{comp}_{name}"] = float(value)
    return rec


MODULE2_CI_COLUMNS: Final[tuple[str, ...]] = (
    "season", "role", "matchday", "decision_date", "window", "component", "estimate",
    "lower", "upper", "n_boot", "n_valid", "block_length_a", "block_length_b",
)


def evaluate_module2(
    frame: pd.DataFrame,
    covariates: Sequence[str],
    seed: int | np.random.SeedSequence = SEED_S8,
    n_boot: int = N_BOOT_CI,
    windows: Sequence[int] = MODULE2_WINDOWS,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Calcola l'uscita per ogni data e W e gli intervalli a fine matchday.

    Restituisce
    -----------
    tuple
        (record a una riga per stagione x data x W, record degli intervalli).
    """
    data = prepare_module2_data(frame, covariates)
    roles = dict(zip(frame["season"], frame["role"]))
    seasons = sorted(set(frame["season"]), key=parse_season_start_year)
    rngs = spawn_t47_generators(seasons, seed)
    records: list[dict[str, object]] = []
    ci_records: list[dict[str, object]] = []
    for season in seasons:
        for w in windows:
            for d in season_decision_dates(data, season):
                records.append(module2_record(module2_at_date(data, season, d, w), roles[season], covariates))
            rng = rngs[(w, season)]
            for m, d in enumerate(matchday_decision_dates(data, season), start=1):
                out = module2_at_date(data, season, d, w)
                if out.state != STATE_ACTIVE:
                    continue
                interval = module2_bootstrap_interval(data, season, d, w, rng, n_boot)
                for comp in COMPONENTS:
                    ci_records.append({
                        "season": season, "role": roles[season], "matchday": m,
                        "decision_date": d.strftime("%Y-%m-%d"), "window": w, "component": comp,
                        "estimate": float(getattr(out.result, comp)),
                        "lower": interval.lower[comp], "upper": interval.upper[comp],
                        "n_boot": n_boot, "n_valid": interval.n_valid,
                        "block_length_a": interval.block_length_a, "block_length_b": interval.block_length_b,
                    })
    return records, ci_records
