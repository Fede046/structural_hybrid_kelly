"""Confronti appaiati fra agenti con intervalli block e iid ed effect size.

Ingressi: le uscite per seed dell'esecuzione congelata sulla validazione (seed a L_PW, "block") e di un run iid aggiuntivo degli
stessi agenti (seed con L = 1), nella forma ValidationResult (S stagioni, C configurazioni,
A agenti, M metriche, N seed).

Metriche primarie (PRIMARY_METRICS):
- per seed: log-ricchezza finale, drawdown massimo, tempo di recupero (con la censura dell'esecuzione congelata sulla validazione: senza recupero vale la durata osservata D − t*);
- per stagione, calcolate sui seed: g_CE(γ) per γ ∈ {1, 2, 5} (decisione di progetto), tasso di
  rovina, SD di ln B_T sulle traiettorie non rovinate.

Differenza pooled di A − B: media sulle stagioni della differenza per stagione; per le
metriche per seed la differenza per stagione è la media sui seed delle differenze appaiate
(stessi seed per i due agenti), per le metriche per stagione è la differenza delle due
statistiche. C2 − E non esiste con F = 0 (E non c'è).

Intervallo al 95%, bootstrap a due livelli (stagioni come cluster indipendenti, decisione
di progetto): a ogni ricampionamento si estraggono 19 stagioni con reinserimento e, dentro ciascuna,
N seed con reinserimento fra quelli esistenti, gli stessi per i due agenti; si ricalcola la
differenza pooled. Intervallo principale (decisione del programmatore del 2026-10-12, per la
sottocopertura nota con pochi cluster): D̂ ± t_{0.975, S−1}·√(S/(S − 1))·se_boot, con se_boot
la deviazione standard dei ricampionamenti e S il numero di stagioni; la correzione è fissata
dalla teoria e può solo allargare. L'intervallo percentile (statistiche d'ordine, B = 999: la
25-esima e la 975-esima) resta come secondario. Lo stesso calcolo sulle uscite iid dà
l'intervallo iid; il rapporto fra le ampiezze è block/iid. Gli stessi indici di
ricampionamento valgono per tutti i confronti, le metriche e le configurazioni.

Effect size (nota 1.3): d = Δ/σ con σ la deviazione standard entro gruppo, a parità di
agente: per le metriche per seed, radice della media sulle stagioni e sui due agenti della
varianza fra seed; per le metriche per stagione, radice della media delle varianze fra
stagioni dei due agenti. OVL = 2Φ(−|d|/2); R² = d² (limite superiore) e R² = d²/(d² + 4)
(formula canonica, gruppi bilanciati).
"""

import math
from collections.abc import Sequence
from typing import Final, NamedTuple

import numpy as np
import scipy.special
import scipy.stats

from shk.model.frozen_agents import AGENT_ORDER
from shk.model.validation_run import CONFIG_NAMES, METRICS, ValidationResult, certainty_equivalent
from shk.stats.calibration import compute_order_statistic_index

COMPARISONS: Final[tuple[tuple[str, str], ...]] = (
    ("C2", "D_ADWIN"), ("C2", "D_PH"), ("C2", "E"),
    ("C1", "C0"), ("C2", "C1"), ("C2", "C2_global"), ("C1", "D_PH"),
)
SEED_METRICS: Final[tuple[str, ...]] = ("final_log_wealth", "max_drawdown", "recovery_time")
SEASON_METRICS: Final[tuple[str, ...]] = ("g_ce_1", "g_ce_2", "g_ce_5", "ruin_rate", "sd_log_wealth")
PRIMARY_METRICS: Final[tuple[str, ...]] = SEED_METRICS + SEASON_METRICS
N_BOOT: Final[int] = 999
INTERVAL_ALPHA: Final[float] = 0.05
_GAMMA: Final[dict[str, float]] = {"g_ce_1": 1.0, "g_ce_2": 2.0, "g_ce_5": 5.0}


def season_statistic(metric: str, log_wealth: np.ndarray, ruined: np.ndarray, n_dates: int) -> float:
    """Statistica per stagione dai seed: g_CE(γ), tasso di rovina o SD di ln B_T sui non rovinati."""
    if metric in _GAMMA:
        return certainty_equivalent(log_wealth, n_dates, _GAMMA[metric])
    if metric == "ruin_rate":
        return float(np.mean(ruined))
    if metric == "sd_log_wealth":
        alive = log_wealth[(ruined < 0.5) & np.isfinite(log_wealth)]
        return float(np.std(alive, ddof=1)) if alive.size > 1 else math.nan
    raise ValueError(f"Unknown season metric {metric!r}")


def _seed_values(result: ValidationResult, config: int, agent: str, metric: str) -> np.ndarray:
    return result.seeds[:, config, AGENT_ORDER.index(agent), METRICS.index(metric)]


def season_differences(result: ValidationResult, config: int, a: str, b: str, metric: str,
                       seed_idx: np.ndarray | None = None) -> np.ndarray:
    """Differenza A − B per stagione (S,), con eventuali indici di seed (S, N) ricampionati."""
    s_count, n = result.seeds.shape[0], result.seeds.shape[-1]
    idx = np.broadcast_to(np.arange(n), (s_count, n)) if seed_idx is None else seed_idx
    rows = np.arange(s_count)[:, None]
    if metric in SEED_METRICS:
        va = _seed_values(result, config, a, metric)[rows, idx]
        vb = _seed_values(result, config, b, metric)[rows, idx]
        return (va - vb).mean(axis=1)
    lw_m, ru_m = METRICS.index("final_log_wealth"), METRICS.index("ruined")
    out = np.empty(s_count)
    for s in range(s_count):
        stats = []
        for agent in (a, b):
            ai = AGENT_ORDER.index(agent)
            lw = result.seeds[s, config, ai, lw_m][idx[s]]
            ru = result.seeds[s, config, ai, ru_m][idx[s]]
            stats.append(season_statistic(metric, lw, ru, int(result.n_dates[s])))
        out[s] = stats[0] - stats[1]
    return out


def effect_size_sigma(result: ValidationResult, config: int, a: str, b: str, metric: str) -> float:
    """σ entro gruppo per d (vedi modulo)."""
    if metric in SEED_METRICS:
        var = [np.var(_seed_values(result, config, agent, metric), axis=1, ddof=1).mean() for agent in (a, b)]
        return float(math.sqrt(np.mean(var)))
    lw_m, ru_m = METRICS.index("final_log_wealth"), METRICS.index("ruined")
    per_agent = []
    for agent in (a, b):
        ai = AGENT_ORDER.index(agent)
        vals = [season_statistic(metric, result.seeds[s, config, ai, lw_m], result.seeds[s, config, ai, ru_m],
                                 int(result.n_dates[s])) for s in range(result.seeds.shape[0])]
        per_agent.append(np.var(vals, ddof=1))
    return float(math.sqrt(np.mean(per_agent)))


def effect_sizes(delta: float, sigma: float) -> dict[str, float]:
    """d, OVL = 2Φ(−|d|/2), R² = d² e R² = d²/(d² + 4)."""
    if not (math.isfinite(delta) and math.isfinite(sigma)) or sigma <= 0.0:
        return {"d": math.nan, "ovl": math.nan, "r2_upper": math.nan, "r2_canonical": math.nan}
    d = delta / sigma
    return {"d": d, "ovl": float(2.0 * scipy.stats.norm.cdf(-abs(d) / 2.0)), "r2_upper": d * d,
            "r2_canonical": d * d / (d * d + 4.0)}


class BootstrapIndices(NamedTuple):
    """Indici del bootstrap a due livelli: stagioni (B, S) e seed (B, S, N)."""

    seasons: np.ndarray
    seeds: np.ndarray


def two_level_indices(n_seasons: int, n_seeds: int, rng: np.random.Generator, n_boot: int = N_BOOT) -> BootstrapIndices:
    """Stagioni con reinserimento e, dentro ciascuna, N seed con reinserimento."""
    seasons = rng.integers(0, n_seasons, size=(n_boot, n_seasons))
    seeds = rng.integers(0, n_seeds, size=(n_boot, n_seasons, n_seeds), dtype=np.int32)
    return BootstrapIndices(seasons, seeds)


def percentile_interval(values: np.ndarray, alpha: float = INTERVAL_ALPHA) -> tuple[float, float]:
    """Estremi per statistiche d'ordine ceil((α/2)(B + 1)) e ceil((1 − α/2)(B + 1))."""
    v = np.sort(np.asarray(values, dtype=np.float64))
    lo = compute_order_statistic_index(v.size, 1.0 - alpha / 2.0)
    hi = compute_order_statistic_index(v.size, alpha / 2.0)
    return float(v[lo - 1]), float(v[hi - 1])


def season_statistic_batch(metric: str, log_wealth: np.ndarray, ruined: np.ndarray,
                           n_dates: np.ndarray) -> np.ndarray:
    """season_statistic sull'ultimo asse (seed) di array (..., N); n_dates con la forma (...)."""
    if metric in _GAMMA:
        gamma = _GAMMA[metric]
        if gamma == 1.0:
            return log_wealth.mean(axis=-1) / n_dates
        with np.errstate(invalid="ignore", over="ignore"):
            lse = scipy.special.logsumexp((1.0 - gamma) * log_wealth, axis=-1)
        return (lse - math.log(log_wealth.shape[-1])) / ((1.0 - gamma) * n_dates)
    if metric == "ruin_rate":
        return ruined.mean(axis=-1)
    if metric == "sd_log_wealth":
        mask = (ruined < 0.5) & np.isfinite(log_wealth)
        count = mask.sum(axis=-1)
        x = np.where(mask, log_wealth, 0.0)
        mean = x.sum(axis=-1) / np.maximum(count, 1)
        ss = (np.where(mask, log_wealth - mean[..., None], 0.0) ** 2).sum(axis=-1)
        with np.errstate(invalid="ignore", divide="ignore"):
            return np.where(count > 1, np.sqrt(ss / (count - 1)), np.nan)
    raise ValueError(f"Unknown season metric {metric!r}")


def t_cluster_interval(estimate: float, boot: np.ndarray, n_clusters: int,
                       alpha: float = INTERVAL_ALPHA) -> tuple[float, float, float]:
    """(basso, alto, se_boot) di D̂ ± t_{1−α/2, S−1}·√(S/(S − 1))·se_boot (vedi modulo)."""
    values = np.asarray(boot, dtype=np.float64)
    finite = values[np.isfinite(values)]
    if finite.size < 2 or not math.isfinite(estimate):
        return math.nan, math.nan, math.nan
    se = float(np.std(finite, ddof=1))
    half = float(scipy.stats.t.ppf(1.0 - alpha / 2.0, n_clusters - 1)) * math.sqrt(n_clusters / (n_clusters - 1)) * se
    return estimate - half, estimate + half, se


def pooled_bootstrap(result: ValidationResult, config: int, a: str, b: str, metric: str,
                     idx: BootstrapIndices, chunk: int = 100) -> np.ndarray:
    """Differenze pooled sui ricampionamenti a due livelli (B,), a blocchi di chunk ricampionamenti."""
    ai, bi = AGENT_ORDER.index(a), AGENT_ORDER.index(b)
    lw_m, ru_m = METRICS.index("final_log_wealth"), METRICS.index("ruined")
    out = np.empty(idx.seasons.shape[0])
    for start in range(0, idx.seasons.shape[0], chunk):
        s_idx = idx.seasons[start:start + chunk][:, :, None]
        k_idx = idx.seeds[start:start + chunk]
        if metric in SEED_METRICS:
            m = METRICS.index(metric)
            diff = result.seeds[:, config, ai, m] - result.seeds[:, config, bi, m]
            out[start:start + chunk] = diff[s_idx, k_idx].mean(axis=(1, 2))
            continue
        n_dates = result.n_dates[idx.seasons[start:start + chunk]].astype(np.float64)
        stats = []
        for x in (ai, bi):
            lw = result.seeds[:, config, x, lw_m][s_idx, k_idx]
            ru = result.seeds[:, config, x, ru_m][s_idx, k_idx]
            stats.append(season_statistic_batch(metric, lw, ru, n_dates))
        out[start:start + chunk] = (stats[0] - stats[1]).mean(axis=1)
    return out


def comparison_available(result: ValidationResult, config: int, a: str, b: str) -> bool:
    """False se uno dei due agenti non c'è nella configurazione (E con F = 0)."""
    lw = METRICS.index("final_log_wealth")
    return all(not np.all(np.isnan(result.seeds[:, config, AGENT_ORDER.index(x), lw])) for x in (a, b))


def coverage_simulation(rng: np.random.Generator, n_replicas: int = 1000, n_seasons: int = 19, n_seeds: int = 500,
                        delta: float = 0.05, tau: float = 0.1, sigma: float = 0.3,
                        n_boot: int = N_BOOT, one_seed_per_season: bool = False) -> tuple[float, float]:
    """Copertura del bootstrap a due livelli su dati sintetici con differenza nota: (percentile, t corretto).

    Ogni replica: effetti veri per stagione μ_s ~ N(delta, tau²), differenze per seed
    μ_s + N(0, sigma²); la stima è la media delle medie per stagione e la verità è delta
    (media della popolazione delle stagioni). Sugli stessi ricampionamenti si valutano
    l'intervallo percentile e quello t con la correzione per il numero di cluster. Con
    one_seed_per_season ogni stagione estratta contribuisce un solo seed estratto (lettura
    alternativa del passo 2, solo per confronto).
    """
    hits_pct = hits_t = 0
    for _ in range(n_replicas):
        mu = rng.normal(delta, tau, n_seasons)
        diff = mu[:, None] + rng.normal(0.0, sigma, (n_seasons, n_seeds))
        seasons = rng.integers(0, n_seasons, size=(n_boot, n_seasons))
        if one_seed_per_season:
            boot = diff[seasons, rng.integers(0, n_seeds, size=(n_boot, n_seasons))].mean(axis=1)
        else:
            boot = np.empty(n_boot)
            for start in range(0, n_boot, 100):
                seeds = rng.integers(0, n_seeds, size=(min(100, n_boot - start), n_seasons, n_seeds), dtype=np.int32)
                boot[start:start + seeds.shape[0]] = diff[seasons[start:start + seeds.shape[0], :, None], seeds].mean(axis=(1, 2))
        lo, hi = percentile_interval(boot)
        hits_pct += int(lo <= delta <= hi)
        lo, hi, _ = t_cluster_interval(float(diff.mean()), boot, n_seasons)
        hits_t += int(lo <= delta <= hi)
    return hits_pct / n_replicas, hits_t / n_replicas
