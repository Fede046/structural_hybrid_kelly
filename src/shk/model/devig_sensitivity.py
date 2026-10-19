"""Tabelle di T63 (US-C9.3): sensibilità al metodo di de-vigging, dalle uscite di devig_runs.

Righe di results/us_c9_3_devig_sensitivity.csv:
- "agent": metodo × dataset (validation, test) × configurazione × agente × metrica primaria, con
  la "mediana pooled" decisa per T62 (robustness.agent_statistics) e l'intervallo come in T56:
  bootstrap a due livelli con correzione t sulla validazione, percentile dai soli seed sul test;
- "comparison": confronti di T56 (validazione, solo intervallo block) e di T58 (test) per metodo;
- "g_hat": ĝ per metodo, serie e stagione da T57 (validazione) e T58 (2023-24), con il segno
  dell'intervallo principale e quello della stima puntuale;
- "conclusion": per ogni conclusione di T56 e T58 "l'intervallo esclude 0 con segno …", il segno
  con ciascun metodo e se vale per tutti e cinque.
Gli indici di ricampionamento sono quelli di T56 (t56_sequences(SEED_S10)[0]) e di T58
(t58_sequences(SEED_S10)[2]) per tutti i metodi: con Shin le righe ridanno T56 e T58.
"""

import csv
import math
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from shk.market.devig import DEVIG_METHOD_NAMES
from shk.model.comparisons import (
    COMPARISONS,
    N_BOOT,
    PRIMARY_METRICS,
    BootstrapIndices,
    comparison_available,
    percentile_interval,
    pooled_bootstrap,
    season_differences,
    t_cluster_interval,
    two_level_indices,
)
from shk.model.comparisons_run import t56_sequences
from shk.model.devig_runs import REPO_ROOT, test_raw_path, validation_raw_path
from shk.model.frozen_agents import AGENT_ORDER
from shk.model.robustness import agent_statistics
from shk.model.test_run import TestResult, comparison_records_single, t58_sequences
from shk.model.validation_run import CONFIG_NAMES, SEED_S10, ValidationResult, load_raw

CSV_PATH: Final[Path] = REPO_ROOT / "results" / "us_c9_3_devig_sensitivity.csv"
PNG_PATH: Final[Path] = REPO_ROOT / "thesis" / "figures" / "us_c9_3_devig_sensitivity.png"
T56_CSV: Final[Path] = REPO_ROOT / "results" / "us_c8_4_comparisons.csv"
T57_CSV: Final[Path] = REPO_ROOT / "results" / "us_c4_2b_g_hat_inference.csv"
T58_CSV: Final[Path] = REPO_ROOT / "results" / "us_c8_5_test_run.csv"

SENSITIVITY_COLUMNS: Final[tuple[str, ...]] = (
    "row_type", "method", "dataset", "series", "season", "config", "agent", "metric", "comparison",
    "estimate", "ci_low", "ci_high", "se_boot", "interval", "excludes_zero", "sign", "sign_estimate",
    "source", "signs_by_method", "stable",
)


def _sign(lo: float, hi: float) -> str:
    """"+" o "-" se l'intervallo esclude 0, altrimenti stringa vuota."""
    if not (math.isfinite(lo) and math.isfinite(hi)):
        return ""
    return "+" if lo > 0.0 else ("-" if hi < 0.0 else "")


def load_method(method: str) -> tuple[ValidationResult, TestResult]:
    """Uscite per seed di un metodo: validazione e 2023-24 (block e iid)."""
    return (load_raw(validation_raw_path(method)),
            TestResult(load_raw(test_raw_path(method)), load_raw(test_raw_path(method, iid=True))))


def validation_indices(result: ValidationResult) -> BootstrapIndices:
    """Indici a due livelli di T56."""
    return two_level_indices(result.seeds.shape[0], result.seeds.shape[-1],
                             np.random.default_rng(t56_sequences(SEED_S10)[0]))


def test_indices(result: ValidationResult) -> BootstrapIndices:
    """Indici dei soli seed di T58, con la stagione unica."""
    n = result.seeds.shape[-1]
    rng = np.random.default_rng(t58_sequences(SEED_S10)[2])
    return BootstrapIndices(np.zeros((N_BOOT, 1), dtype=np.int64), rng.integers(0, n, size=(N_BOOT, 1, n), dtype=np.int32))


def agent_records(method: str, dataset: str, result: ValidationResult, idx: BootstrapIndices) -> list[dict]:
    """Righe "agent" di un metodo e di un dataset."""
    s_count = result.seeds.shape[0]
    records = []
    for ci, config in enumerate(CONFIG_NAMES):
        for metric in PRIMARY_METRICS:
            est = agent_statistics(result, ci, metric)
            boot = np.stack([agent_statistics(result, ci, metric, idx.seasons[b], idx.seeds[b])
                             for b in range(idx.seasons.shape[0])])
            for a, agent in enumerate(AGENT_ORDER):
                if not math.isfinite(est[a]):
                    continue
                finite = boot[:, a][np.isfinite(boot[:, a])]
                if s_count > 1:
                    lo, hi, se = t_cluster_interval(float(est[a]), boot[:, a], s_count)
                    interval = "t_cluster"
                else:
                    lo, hi = percentile_interval(finite) if finite.size >= 40 else (math.nan, math.nan)
                    se = float(np.std(finite, ddof=1)) if finite.size > 1 else math.nan
                    interval = "percentile_seeds"
                records.append({"row_type": "agent", "method": method, "dataset": dataset, "config": config,
                                "agent": agent, "metric": metric, "estimate": float(est[a]), "ci_low": lo,
                                "ci_high": hi, "se_boot": se, "interval": interval})
    return records


def validation_comparison_records(method: str, result: ValidationResult, idx: BootstrapIndices) -> list[dict]:
    """Confronti di T56 per un metodo: stima e intervallo block con correzione t, con gli indici di T56."""
    s_count = result.seeds.shape[0]
    records = []
    for ci, config in enumerate(CONFIG_NAMES):
        for a, b in COMPARISONS:
            if not comparison_available(result, ci, a, b):
                continue
            for metric in PRIMARY_METRICS:
                est = float(np.mean(season_differences(result, ci, a, b, metric)))
                lo, hi, se = t_cluster_interval(est, pooled_bootstrap(result, ci, a, b, metric, idx), s_count)
                sign = _sign(lo, hi)
                records.append({"row_type": "comparison", "method": method, "dataset": "validation", "config": config,
                                "comparison": f"{a}-{b}", "metric": metric, "estimate": est, "ci_low": lo,
                                "ci_high": hi, "se_boot": se, "interval": "t_cluster", "excludes_zero": sign != "",
                                "sign": sign})
    return records


def test_comparison_records(method: str, result: TestResult) -> list[dict]:
    """Confronti di T58 per un metodo (comparison_records_single con i seed di T58)."""
    return [{"row_type": "comparison", "method": method, "dataset": "test", "config": r["config"],
             "comparison": r["comparison"], "metric": r["metric"], "estimate": r["estimate"], "ci_low": r["ci_low"],
             "ci_high": r["ci_high"], "interval": "percentile_seeds", "excludes_zero": r["excludes_zero"],
             "sign": r["sign"]}
            for r in comparison_records_single(result, seed=SEED_S10)]


def g_hat_records() -> list[dict]:
    """ĝ per metodo, serie e stagione: T57 per la validazione (intervallo t corretto per il pooled), T58 per il test."""
    records = []
    t57 = pd.read_csv(T57_CSV)
    for r in t57[t57["row_type"] == "interval"].itertuples():
        lo, hi = float(r.ci_block_low), float(r.ci_block_high)
        records.append({"row_type": "g_hat", "method": r.method, "dataset": "validation", "series": r.series,
                        "season": r.season, "estimate": float(r.g_hat), "ci_low": lo, "ci_high": hi,
                        "interval": "t_cluster" if r.season == "pooled" else "stationary", "sign": _sign(lo, hi),
                        "sign_estimate": "+" if r.g_hat > 0 else "-", "source": "us_c4_2b_g_hat_inference.csv"})
    t58 = pd.read_csv(T58_CSV)
    for r in t58[t58["row_type"] == "g_hat"].itertuples():
        lo, hi = float(r.ci_low), float(r.ci_high)
        records.append({"row_type": "g_hat", "method": r.method, "dataset": "test", "series": r.series,
                        "season": r.season, "estimate": float(r.estimate), "ci_low": lo, "ci_high": hi,
                        "interval": "stationary", "sign": _sign(lo, hi),
                        "sign_estimate": "+" if r.estimate > 0 else "-", "source": "us_c8_5_test_run.csv"})
    return records


def conclusion_records(comparisons: list[dict]) -> list[dict]:
    """Conclusioni di T56 e T58 che escludono 0: segno con ciascun metodo e stabilità."""
    by_key = {(r["dataset"], r["config"], r["comparison"], r["metric"], r["method"]): r["sign"] for r in comparisons}
    t56 = pd.read_csv(T56_CSV, dtype=str, keep_default_na=False)
    t58 = pd.read_csv(T58_CSV, dtype=str, keep_default_na=False)
    originals = ([("validation", r) for r in t56[t56["row_type"] == "comparison"].to_dict(orient="records")
                  if r["block_excludes_zero"] == "True"]
                 + [("test", r) for r in t58[t58["row_type"] == "comparison"].to_dict(orient="records")
                    if r["excludes_zero"] == "True"])
    records = []
    for dataset, r in originals:
        signs = [by_key.get((dataset, r["config"], r["comparison"], r["metric"], m), "") for m in DEVIG_METHOD_NAMES]
        records.append({"row_type": "conclusion", "dataset": dataset, "config": r["config"],
                        "comparison": r["comparison"], "metric": r["metric"], "sign": r["sign"],
                        "source": "us_c8_4_comparisons.csv" if dataset == "validation" else "us_c8_5_test_run.csv",
                        "signs_by_method": ";".join(f"{m}:{s or '0'}" for m, s in zip(DEVIG_METHOD_NAMES, signs)),
                        "stable": all(s == r["sign"] for s in signs)})
    return records


def all_records() -> list[dict]:
    """Tutte le righe della tabella, dai cinque metodi."""
    records, comparisons = [], []
    for method in DEVIG_METHOD_NAMES:
        validation, test = load_method(method)
        records += agent_records(method, "validation", validation, validation_indices(validation))
        records += agent_records(method, "test", test.block, test_indices(test.block))
        comparisons += validation_comparison_records(method, validation, validation_indices(validation))
        comparisons += test_comparison_records(method, test)
    return records + comparisons + g_hat_records() + conclusion_records(comparisons)


def write_outputs() -> None:
    """Scrive il CSV (stringa vuota per i valori non applicabili) e la figura."""
    records = all_records()
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CSV_PATH, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(SENSITIVITY_COLUMNS))
        writer.writeheader()
        writer.writerows([{k: "" if isinstance(v, float) and math.isnan(v) else v for k, v in r.items()}
                          for r in records])
    make_figure(pd.read_csv(CSV_PATH), PNG_PATH)


def make_figure(df: pd.DataFrame, png_path: Path) -> None:
    """A) ĝ pooled e 2023-24 per metodo; B) confronti di T56 per metodo, £0.01; C) conclusioni stabili e fragili."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    png_path.parent.mkdir(parents=True, exist_ok=True)
    fig, (ax_a, ax_b, ax_c) = plt.subplots(1, 3, figsize=(22, 6.5))
    colors = dict(zip(DEVIG_METHOD_NAMES, ("tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple")))
    g = df[(df["row_type"] == "g_hat") & (((df["dataset"] == "validation") & (df["season"] == "pooled"))
                                          | (df["dataset"] == "test"))]
    groups = [("validation", "b365_prematch"), ("validation", "pinnacle_closing"), ("test", "b365_prematch"),
              ("test", "pinnacle_closing")]
    for k, method in enumerate(DEVIG_METHOD_NAMES):
        for j, (dataset, series) in enumerate(groups):
            r = g[(g["method"] == method) & (g["dataset"] == dataset) & (g["series"] == series)]
            if r.empty:
                continue
            est, lo, hi = (float(r[c].iloc[0]) for c in ("estimate", "ci_low", "ci_high"))
            ax_a.errorbar(j + (k - 2) * 0.12, est, yerr=[[est - lo], [hi - est]], fmt="o", color=colors[method],
                          capsize=3, label=method if j == 0 else None)
    ax_a.axhline(0.0, color="black", linewidth=0.8)
    ax_a.set_xticks(range(len(groups)))
    ax_a.set_xticklabels(["valid. B365", "valid. Pinnacle", "2023-24 B365", "2023-24 Pinnacle"], fontsize=9)
    ax_a.set_ylabel("ĝ con intervallo al 95%")
    ax_a.set_title("A) ĝ per metodo di de-vigging", loc="left", fontsize=11, fontweight="bold")
    ax_a.legend(fontsize=8)
    ax_a.grid(True, axis="y", linestyle=":", alpha=0.6)

    comp = df[(df["row_type"] == "comparison") & (df["dataset"] == "validation") & (df["config"] == "gbp_0.01")
              & (df["metric"] == "final_log_wealth")]
    names = list(dict.fromkeys(comp["comparison"]))
    for k, method in enumerate(DEVIG_METHOD_NAMES):
        c = comp[comp["method"] == method].set_index("comparison").reindex(names)
        est = c["estimate"].astype(float).to_numpy()
        lo, hi = c["ci_low"].astype(float).to_numpy(), c["ci_high"].astype(float).to_numpy()
        y = np.arange(len(names)) + (k - 2) * 0.14
        ax_b.errorbar(est, y, xerr=[np.maximum(est - lo, 0), np.maximum(hi - est, 0)], fmt="o", color=colors[method],
                      capsize=2, markersize=4, label=method)
    ax_b.axvline(0.0, color="black", linewidth=0.8)
    ax_b.set_yticks(np.arange(len(names)))
    ax_b.set_yticklabels(names)
    ax_b.set_xlabel("Differenza pooled di ln W_T (19 stagioni), intervallo t corretto")
    ax_b.set_title("B) Confronti di T56 per metodo, £0.01", loc="left", fontsize=11, fontweight="bold")
    ax_b.legend(fontsize=8)
    ax_b.grid(True, axis="x", linestyle=":", alpha=0.6)

    concl = df[df["row_type"] == "conclusion"]
    labels, stable, fragile = [], [], []
    for dataset in ("validation", "test"):
        for comparison in sorted(concl.loc[concl["dataset"] == dataset, "comparison"].unique()):
            sub = concl[(concl["dataset"] == dataset) & (concl["comparison"] == comparison)]
            labels.append(f"{'valid.' if dataset == 'validation' else '2023-24'} {comparison}")
            stable.append(int(sub["stable"].astype(str).eq("True").sum()))
            fragile.append(int((~sub["stable"].astype(str).eq("True")).sum()))
    y = np.arange(len(labels))
    ax_c.barh(y, stable, color="tab:green", label="stabile con i cinque metodi")
    ax_c.barh(y, fragile, left=stable, color="tab:red", label="cambia con almeno un metodo")
    ax_c.set_yticks(y)
    ax_c.set_yticklabels(labels, fontsize=8)
    ax_c.set_xlim(0, 1.35 * max(s + f for s, f in zip(stable, fragile)))
    ax_c.set_xlabel("Conclusioni di T56 e T58 che escludono 0 (metriche × configurazioni)")
    ax_c.set_title("C) Conclusioni stabili e fragili", loc="left", fontsize=11, fontweight="bold")
    ax_c.legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(png_path, dpi=150)
    plt.close(fig)
