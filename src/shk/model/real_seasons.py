"""Risultati sulle stagioni reali di validazione, accanto alla mediana sulle stagioni ricostruite.

Decisione del 2026-11-05: il risultato principale è la realizzazione osservata di ogni stagione
(la stagione vera, giocata una volta), non la mediana sulle 500 stagioni ricostruite per
stationary bootstrap delle date. Le stagioni ricostruite usano partite, quote e risultati veri, ma
ripetono alcune giornate e ne saltano altre, quindi alterano proprio la sequenza nel tempo che il
supervisore osserva; restano come misura dell'incertezza.

Il modulo legge le sintesi già versionate (nessuna nuova esecuzione) e, per ogni agente e
configurazione, confronta la stagione vera con un riferimento appaiato: capitale tipico
exp(media sulle stagioni di ln W_T), stagioni meglio e peggio del riferimento, allarmi e quota di date
con λ = 0. Per le stagioni ricostruite riporta solo il capitale tipico della mediana: i confronti appaiati per seed restano
nei documenti delle singole esecuzioni (mediana delle differenze appaiate, non differenza delle mediane).
"""

import math
from collections.abc import Sequence
from pathlib import Path
from typing import Final, NamedTuple

import numpy as np
import pandas as pd


class RealSource(NamedTuple):
    """Una sintesi versionata e il riferimento appaiato di ogni suo agente."""

    name: str
    csv: str
    references: dict[str, str]  # agente -> riferimento nello stesso file


REAL_SOURCES: Final[tuple[RealSource, ...]] = (
    RealSource("frozen", "us_c8_3_validation_summary", {"A": "B_0.25", "B_0.25": "B_0.25"}),
    RealSource("scheme", "us_c10_scheme_validation_summary",
               {a: "B_0.25" for a in ("B_0.25", "C3", "C3_stop", "C3_and")}),
    RealSource("reference", "us_c13_scheme_reference_summary",
               {a: "B_0.25" for a in ("B_0.25", "C3_ref", "C3_ref_stop")}),
    RealSource("worker_rules", "us_c11_worker_rules_summary",
               {f"{r}_{v}": f"{r}_brake" for r in ("R1", "R2", "R3") for v in ("alone", "brake", "C3")}),
    RealSource("r3_reference", "us_c17_r3_reference_summary",
               {a: "R3_brake" for a in ("R3_brake", "R3_C3_ref", "R3_C3_ref_stop")}),
    RealSource("elo_refit", "us_c18_elo_refit_summary",
               {a: "B_0.25" for a in ("B_0.25", "C3_ref", "C3_ref_stop")}),
    RealSource("extra_fit", "us_c20_training_fits_summary",
               {a: "B_0.25" for a in ("B_0.25", "C3_ref", "C3_ref_stop")}),
)

REAL_COLUMNS: Final[tuple[str, ...]] = (
    "source", "config", "agent", "reference", "n_seasons",
    "typical_capital_real", "typical_capital_seeds",
    "seasons_better_real", "seasons_worse_real",
    "mean_alarms_real", "mean_alarms_seeds", "share_lambda_zero_real", "share_lambda_zero_seeds",
)

TIE_TOL: Final[float] = 1e-12


def _typical(log_wealth: np.ndarray) -> float:
    """exp della media sulle stagioni di ln W_T (0 se una stagione va in rovina)."""
    m = float(np.mean(log_wealth))
    return 0.0 if m == -math.inf else math.exp(m)


def _better_worse(x: np.ndarray, y: np.ndarray) -> tuple[int, int]:
    d = x - y
    return int((d > TIE_TOL).sum()), int((d < -TIE_TOL).sum())


def _nan_mean(s: pd.Series) -> float:
    v = pd.to_numeric(s, errors="coerce").astype(float)
    return float(v.mean()) if v.notna().any() else math.nan


def real_records(summary: pd.DataFrame, source: RealSource) -> list[dict]:
    """Una riga per configurazione × agente della sintesi (vedi modulo)."""
    out: list[dict] = []
    for config in summary["config"].unique():
        rows = summary[summary["config"] == config]
        by_agent = {a: g.set_index("season").sort_index() for a, g in rows.groupby("agent", sort=False)}
        for agent, ref in source.references.items():
            g, r = by_agent[agent], by_agent[ref]
            if list(g.index) != list(r.index):
                raise ValueError(f"{source.name}: {agent} and {ref} cover different seasons")
            obs, obs_ref = g["observed_log_wealth"].to_numpy(float), r["observed_log_wealth"].to_numpy(float)
            med = g["median_log_wealth"].to_numpy(float)
            better, worse = _better_worse(obs, obs_ref)
            same = agent == ref
            out.append({
                "source": source.name, "config": config, "agent": agent, "reference": ref, "n_seasons": len(g),
                "typical_capital_real": _typical(obs), "typical_capital_seeds": _typical(med),
                "seasons_better_real": "" if same else better, "seasons_worse_real": "" if same else worse,
                "mean_alarms_real": _nan_mean(g["observed_n_alarms"]), "mean_alarms_seeds": _nan_mean(g["mean_n_alarms"]),
                "share_lambda_zero_real": _nan_mean(g["observed_share_lambda_zero"]),
                "share_lambda_zero_seeds": _nan_mean(g["mean_share_lambda_zero"]),
            })
    return out


def all_real_records(results_dir: Path, sources: Sequence[RealSource] = REAL_SOURCES) -> list[dict]:
    """Righe di tutte le sintesi di REAL_SOURCES."""
    out: list[dict] = []
    for source in sources:
        summary = pd.read_csv(results_dir / f"{source.csv}.csv")
        out.extend(real_records(summary[summary["row_type"] == "summary"], source))
    return out
