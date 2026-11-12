"""Inferenza appaiata sulle 19 stagioni vere: lo schema contro il suo riferimento, stagione per stagione.

us_c19 riporta in quante stagioni un agente conserva più capitale del riferimento appaiato; qui si
aggiunge quanto quel conteggio e la differenza media sono distinguibili dal caso. L'unità è la
stagione (ogni stagione riparte dallo stesso capitale), d = ln W_T dell'agente − ln W_T del
riferimento sulla stagione vera, dalle sintesi già versionate (shk.model.real_seasons.REAL_SOURCES,
nessuna nuova esecuzione):
- test dei segni esatto a due code sulle stagioni con d ≠ 0 (scipy.stats.binomtest);
- test dei ranghi con segno di Wilcoxon a due code (scipy.stats.wilcoxon);
- rapporto dei capitali tipici exp(media di d) con intervallo percentile al 95% da un bootstrap
  delle stagioni (N_BOOT ricampionamenti con reinserimento).
Le stagioni sono trattate come indipendenti e scambiabili: con 19 stagioni e tre calibrazioni del
modello è un'approssimazione. Il test non dice perché l'agente fa meglio: con un vantaggio negativo
basta puntare meno (vedi shk.model.timing_placebo).
"""

import math
from collections.abc import Sequence
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from scipy.stats import binomtest, wilcoxon

from shk.model.real_seasons import REAL_SOURCES, TIE_TOL, RealSource

SEED_S24: Final[int] = 20261111
N_BOOT: Final[int] = 9999
PAIRED_COLUMNS: Final[tuple[str, ...]] = (
    "source", "config", "agent", "reference", "n_seasons", "seasons_better", "seasons_worse",
    "sign_test_p", "wilcoxon_p", "mean_log_difference", "capital_ratio", "capital_ratio_low", "capital_ratio_high",
    "n_boot",
)


def paired_statistics(log_wealth: np.ndarray, reference: np.ndarray, rng: np.random.Generator,
                      n_boot: int = N_BOOT) -> dict[str, float | int]:
    """Statistiche appaiate di un agente contro il riferimento (vedi modulo).

    Con una stagione in rovina (ln W_T = −inf) restano conteggi e test dei segni; il resto è NaN.
    """
    x, y = np.asarray(log_wealth, dtype=np.float64), np.asarray(reference, dtype=np.float64)
    if x.shape != y.shape or x.ndim != 1 or x.shape[0] < 2:
        raise ValueError(f"log_wealth and reference must be (n,) with n >= 2, got {x.shape}, {y.shape}")
    with np.errstate(invalid="ignore"):
        d = x - y
    better, worse = int((d > TIE_TOL).sum()), int((d < -TIE_TOL).sum())
    out: dict[str, float | int] = {
        "n_seasons": int(x.shape[0]), "seasons_better": better, "seasons_worse": worse,
        "sign_test_p": float(binomtest(better, better + worse, 0.5).pvalue) if better + worse else math.nan,
        "wilcoxon_p": math.nan, "mean_log_difference": math.nan, "capital_ratio": math.nan,
        "capital_ratio_low": math.nan, "capital_ratio_high": math.nan, "n_boot": n_boot,
    }
    if not np.all(np.isfinite(d)):
        return out
    if better + worse:
        out["wilcoxon_p"] = float(wilcoxon(d[np.abs(d) > TIE_TOL]).pvalue)
    means = d[rng.integers(0, d.shape[0], size=(n_boot, d.shape[0]))].mean(axis=1)
    low, high = np.quantile(means, [0.025, 0.975])
    out.update({"mean_log_difference": float(d.mean()), "capital_ratio": math.exp(d.mean()),
                "capital_ratio_low": math.exp(low), "capital_ratio_high": math.exp(high)})
    return out


def all_paired_records(results_dir: Path, sources: Sequence[RealSource] = REAL_SOURCES,
                       seed: int = SEED_S24, n_boot: int = N_BOOT) -> list[dict]:
    """Una riga per sintesi × configurazione × agente diverso dal suo riferimento."""
    out: list[dict] = []
    root = np.random.SeedSequence(seed)
    for source, source_seq in zip(sources, root.spawn(len(sources))):
        summary = pd.read_csv(results_dir / f"{source.csv}.csv")
        summary = summary[summary["row_type"] == "summary"]
        pairs = [(c, a, r) for c in summary["config"].unique() for a, r in source.references.items() if a != r]
        for (config, agent, ref), seq in zip(pairs, source_seq.spawn(len(pairs))):
            rows = summary[summary["config"] == config]
            g = rows[rows["agent"] == agent].set_index("season").sort_index()
            r = rows[rows["agent"] == ref].set_index("season").sort_index()
            if list(g.index) != list(r.index):
                raise ValueError(f"{source.name}: {agent} and {ref} cover different seasons")
            stats = paired_statistics(g["observed_log_wealth"].to_numpy(float), r["observed_log_wealth"].to_numpy(float),
                                      np.random.default_rng(seq), n_boot)
            out.append({"source": source.name, "config": config, "agent": agent, "reference": ref, **stats})
    return out
