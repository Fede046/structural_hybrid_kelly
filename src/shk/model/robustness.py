"""Robustezza del ranking degli agenti fra Modulo 1 Elo e Dixon-Coles.

Statistica di ranking per agente, metrica primaria e configurazione ("mediana pooled",
decisione del programmatore del 2026-10-17):
- metriche per seed (log-ricchezza finale, drawdown massimo, tempo di recupero): mediana sui
  seed in ogni stagione, poi media sulle stagioni;
- metriche per stagione (g_CE(γ), tasso di rovina, SD di ln W_T, calcolate sui seed come nei confronti fra agenti): media sulle stagioni.
Gli agenti con statistica non finita in una delle due esecuzioni (E con F = 0) non entrano.

Confronto dei due ordinamenti: τ-b di Kendall, che tratta le parità (C0 = B_0.25 per
costruzione): τ_b = (n_c − n_d) / √((n_0 − n_1)(n_0 − n_2)), con n_0 = n(n − 1)/2, n_1 e n_2 le
coppie in parità nel primo e nel secondo ordinamento. Coppie invertite: segno opposto delle
differenze nelle due esecuzioni.

Intervallo: bootstrap a due livelli (stagioni con reinserimento e, dentro ciascuna, seed con
reinserimento), con gli stessi indici per le due esecuzioni. Sulla validazione l'intervallo
principale è τ̂ ± t_{0.975, S−1}·√(S/(S − 1))·se_boot (correzione per i cluster decisa il
2026-10-12 per l'inferenza su ĝ, per la robustezza del ranking e per la sensibilità al de-vigging), il percentile è secondario; sul test, con una stagione sola,
si ricampionano i soli seed e si usa il percentile, come nell'esecuzione sul test 2023-24.
"""

import math
from itertools import combinations
from collections.abc import Sequence
from typing import Final

import numpy as np

from shk.model.comparisons import (
    N_BOOT,
    PRIMARY_METRICS,
    SEED_METRICS,
    percentile_interval,
    season_statistic_batch,
    t_cluster_interval,
    two_level_indices,
)
from shk.model.frozen_agents import AGENT_ORDER
from shk.model.validation_run import CONFIG_NAMES, METRICS, ValidationResult

ROBUSTNESS_COLUMNS: Final[tuple[str, ...]] = (
    "row_type", "dataset", "config", "metric", "agent", "other", "comparison",
    "value_elo", "value_dc", "rank_elo", "rank_dc", "n_agents", "tau", "se_boot", "ci_low", "ci_high",
    "ci_pct_low", "ci_pct_high", "interval", "n_boot_finite", "n_inverted", "n_tied_pairs", "share_inverted",
    "estimate_elo", "ci_low_elo", "ci_high_elo", "sign_elo", "estimate_dc", "ci_low_dc", "ci_high_dc", "sign_dc",
    "same_conclusion",
)


def kendall_tau_b(x: Sequence[float], y: Sequence[float]) -> float:
    """τ-b di Kendall fra due vettori della stessa lunghezza (NaN se un ordinamento è tutto in parità)."""
    a, b = np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64)
    if a.shape != b.shape or a.ndim != 1:
        raise ValueError("x and y must be 1-D arrays of the same length")
    n = a.size
    nc = nd = tied_x = tied_y = 0
    for i, j in combinations(range(n), 2):
        dx, dy = np.sign(a[i] - a[j]), np.sign(b[i] - b[j])
        tied_x += int(dx == 0)
        tied_y += int(dy == 0)
        if dx != 0 and dy != 0:
            nc += int(dx == dy)
            nd += int(dx != dy)
    n0 = n * (n - 1) / 2
    denom = math.sqrt((n0 - tied_x) * (n0 - tied_y))
    return (nc - nd) / denom if denom > 0 else math.nan


def inverted_pairs(x: Sequence[float], y: Sequence[float]) -> list[tuple[int, int]]:
    """Coppie (i, j), i < j, con differenze di segno opposto nei due vettori."""
    a, b = np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64)
    return [(i, j) for i, j in combinations(range(a.size), 2) if (a[i] - a[j]) * (b[i] - b[j]) < 0]


def ranks(values: Sequence[float]) -> np.ndarray:
    """Rango decrescente (1 = valore più alto), parità con il rango minimo."""
    v = np.asarray(values, dtype=np.float64)
    return np.array([1 + int(np.sum(v > x)) for x in v])


def agent_statistics(result: ValidationResult, config: int, metric: str,
                     season_idx: np.ndarray | None = None, seed_idx: np.ndarray | None = None) -> np.ndarray:
    """Statistica di ranking (A,) per tutti gli agenti, con eventuali indici ricampionati.

    season_idx ha forma (S,) e seed_idx forma (S, N): le stagioni e, dentro ciascuna, i seed.
    """
    s_count, n = result.seeds.shape[0], result.seeds.shape[-1]
    s_idx = np.arange(s_count) if season_idx is None else np.asarray(season_idx)
    k_idx = np.broadcast_to(np.arange(n), (s_idx.size, n)) if seed_idx is None else np.asarray(seed_idx)
    rows, agents = s_idx[:, None, None], np.arange(len(AGENT_ORDER))[None, :, None]
    cols = k_idx[:, None, :]
    if metric in SEED_METRICS:
        values = result.seeds[:, config, :, METRICS.index(metric), :][rows, agents, cols]
        return np.median(values, axis=2).mean(axis=0)
    lw = result.seeds[:, config, :, METRICS.index("final_log_wealth"), :][rows, agents, cols]
    ru = result.seeds[:, config, :, METRICS.index("ruined"), :][rows, agents, cols]
    n_dates = np.broadcast_to(result.n_dates[s_idx].astype(np.float64)[:, None], lw.shape[:2])
    return season_statistic_batch(metric, lw, ru, n_dates).mean(axis=0)


def _usable(elo: np.ndarray, dc: np.ndarray) -> np.ndarray:
    return np.flatnonzero(np.isfinite(elo) & np.isfinite(dc))


def ranking_records(elo: ValidationResult, dc: ValidationResult, dataset: str, rng: np.random.Generator,
                    n_boot: int = N_BOOT) -> list[dict[str, object]]:
    """Righe "statistic", "tau" e "inversion" per configurazione e metrica primaria.

    Sulla validazione (più stagioni) bootstrap a due livelli; con una stagione sola, i soli seed.
    Gli indici sono gli stessi per le due esecuzioni e per tutte le metriche e configurazioni.
    """
    if elo.seeds.shape != dc.seeds.shape or tuple(elo.seasons) != tuple(dc.seasons):
        raise ValueError("Elo and Dixon-Coles results must have the same seasons and shape")
    s_count, n = elo.seeds.shape[0], elo.seeds.shape[-1]
    if s_count > 1:
        idx = two_level_indices(s_count, n, rng, n_boot)
        seasons_b, seeds_b = idx.seasons, idx.seeds
    else:
        seasons_b = np.zeros((n_boot, 1), dtype=np.int64)
        seeds_b = rng.integers(0, n, size=(n_boot, 1, n), dtype=np.int32)
    records: list[dict[str, object]] = []
    for ci, config in enumerate(CONFIG_NAMES):
        for metric in PRIMARY_METRICS:
            e_hat, d_hat = agent_statistics(elo, ci, metric), agent_statistics(dc, ci, metric)
            use = _usable(e_hat, d_hat)
            names = [AGENT_ORDER[i] for i in use]
            tau_hat = kendall_tau_b(e_hat[use], d_hat[use])
            pairs = list(combinations(range(use.size), 2))
            boot = np.empty(n_boot)
            inverted_count = np.zeros(len(pairs))
            for b in range(n_boot):
                eb = agent_statistics(elo, ci, metric, seasons_b[b], seeds_b[b])[use]
                db = agent_statistics(dc, ci, metric, seasons_b[b], seeds_b[b])[use]
                boot[b] = kendall_tau_b(eb, db)
                inverted_count += np.array([(eb[i] - eb[j]) * (db[i] - db[j]) < 0 for i, j in pairs])
            finite = boot[np.isfinite(boot)]
            # τ non definito se un ordinamento è tutto in parità (per esempio nessuna rovina)
            pct_lo, pct_hi = percentile_interval(finite) if finite.size >= 40 else (math.nan, math.nan)
            if s_count > 1:
                lo, hi, se = t_cluster_interval(tau_hat, boot, s_count)
                interval = "t_cluster"
            else:
                se = float(np.std(finite, ddof=1)) if finite.size > 1 else math.nan
                lo, hi = pct_lo, pct_hi
                interval = "percentile_seeds"
            inv = inverted_pairs(e_hat[use], d_hat[use])
            tied = sum(1 for i, j in pairs if e_hat[use][i] == e_hat[use][j] and d_hat[use][i] == d_hat[use][j])
            base = {"dataset": dataset, "config": config, "metric": metric}
            records.append({**base, "row_type": "tau", "n_agents": len(names), "tau": tau_hat, "se_boot": se,
                            "n_boot_finite": int(finite.size),
                            "ci_low": lo, "ci_high": hi, "ci_pct_low": pct_lo, "ci_pct_high": pct_hi,
                            "interval": interval, "n_inverted": len(inv), "n_tied_pairs": tied})
            r_e, r_d = ranks(e_hat[use]), ranks(d_hat[use])
            for k, name in enumerate(names):
                records.append({**base, "row_type": "statistic", "agent": name, "value_elo": float(e_hat[use][k]),
                                "value_dc": float(d_hat[use][k]), "rank_elo": int(r_e[k]), "rank_dc": int(r_d[k])})
            for p, (i, j) in enumerate(pairs):
                if (i, j) in inv:
                    records.append({**base, "row_type": "inversion", "agent": names[i], "other": names[j],
                                    "value_elo": float(e_hat[use][i] - e_hat[use][j]),
                                    "value_dc": float(d_hat[use][i] - d_hat[use][j]),
                                    "share_inverted": float(inverted_count[p] / n_boot)})
    return records


def comparison_pairs(elo_rows: list[dict], dc_rows: list[dict], dataset: str, low: str, high: str,
                     sign: str) -> list[dict[str, object]]:
    """Righe "comparison": differenze appaiate dei confronti fra agenti (validazione o test) con Elo e con Dixon-Coles affiancate."""
    key = lambda r: (r["config"], r["comparison"], r["metric"])
    dc_by_key = {key(r): r for r in dc_rows}
    records = []
    for r in elo_rows:
        d = dc_by_key.get(key(r))
        if d is None:
            continue
        records.append({"row_type": "comparison", "dataset": dataset, "config": r["config"], "metric": r["metric"],
                        "comparison": r["comparison"], "estimate_elo": r["estimate"], "ci_low_elo": r[low],
                        "ci_high_elo": r[high], "sign_elo": r[sign], "estimate_dc": d["estimate"],
                        "ci_low_dc": d[low], "ci_high_dc": d[high], "sign_dc": d[sign],
                        "same_conclusion": str(r[sign]) == str(d[sign])})
    return records
