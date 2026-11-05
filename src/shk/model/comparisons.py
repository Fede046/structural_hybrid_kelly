"""Intervalli bootstrap usati dall'inferenza su ĝ e dall'esecuzione sul test.

- percentile_interval: estremi per statistiche d'ordine (B = 999: la 25-esima e la 975-esima).
- t_cluster_interval: D̂ ± t_{0.975, S−1}·√(S/(S − 1))·se_boot, con se_boot la deviazione
  standard dei ricampionamenti e S il numero di cluster (decisione del programmatore del
  2026-10-12, per la sottocopertura nota con pochi cluster); la correzione è fissata dalla
  teoria e può solo allargare.
"""

import math
from typing import Final

import numpy as np
import scipy.stats

from shk.stats.calibration import compute_order_statistic_index

INTERVAL_ALPHA: Final[float] = 0.05


def percentile_interval(values: np.ndarray, alpha: float = INTERVAL_ALPHA) -> tuple[float, float]:
    """Estremi per statistiche d'ordine ceil((α/2)(B + 1)) e ceil((1 − α/2)(B + 1))."""
    v = np.sort(np.asarray(values, dtype=np.float64))
    lo = compute_order_statistic_index(v.size, 1.0 - alpha / 2.0)
    hi = compute_order_statistic_index(v.size, alpha / 2.0)
    return float(v[lo - 1]), float(v[hi - 1])


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
