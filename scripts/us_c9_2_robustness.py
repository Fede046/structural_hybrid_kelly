"""Script: robustezza del ranking degli agenti fra Elo e Dixon-Coles.

Legge le uscite per seed delle esecuzioni Elo e Dixon-Coles (suffisso _dc):
- results/raw/us_c8_3_validation_raw.npz e us_c8_3_validation_raw_dc.npz (19 stagioni);
- results/raw/us_c8_5_test_raw.npz e us_c8_5_test_raw_dc.npz (2023-24);
e i confronti fra agenti in validazione e sul test 2023-24 (results/us_c8_4_comparisons*.csv, results/us_c8_5_test_run*.csv).
Scrive results/us_c9_2_robustness.csv (statistiche di ranking, τ di Kendall con intervalli,
coppie invertite, differenze appaiate affiancate) e thesis/figures/us_c9_2_robustness.png.
Seed del bootstrap: SeedSequence(SEED_S11).spawn(5)[3].spawn(5)[4], spawn(2): validazione, test.
"""

import csv
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from shk.model.comparisons import PRIMARY_METRICS
from shk.model.module1 import MODULE1_DIXON_COLES
from shk.model.module1_seeds import T62_RANKING_POSITION, s10_seed
from shk.model.robustness import ROBUSTNESS_COLUMNS, comparison_pairs, ranking_records
from shk.model.task_seeds import story_task_sequence
from shk.model.validation_run import CONFIG_NAMES, load_raw

MAIN_CONFIG = "gbp_0.01"


def _rows(path: Path) -> list[dict]:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    return df[df["row_type"] == "comparison"].to_dict(orient="records")


def run_experiment() -> None:
    """Ranking, τ di Kendall, inversioni e confronti affiancati; scrive CSV e figura."""
    repo_root = Path(__file__).resolve().parents[1]
    raw = repo_root / "results" / "raw"
    csv_path = repo_root / "results" / "us_c9_2_robustness.csv"
    png_path = repo_root / "thesis" / "figures" / "us_c9_2_robustness.png"
    png_path.parent.mkdir(parents=True, exist_ok=True)

    seqs = story_task_sequence(s10_seed(MODULE1_DIXON_COLES), T62_RANKING_POSITION).spawn(2)
    records = ranking_records(load_raw(raw / "us_c8_3_validation_raw.npz"),
                              load_raw(raw / "us_c8_3_validation_raw_dc.npz"), "validation",
                              np.random.default_rng(seqs[0]))
    records += ranking_records(load_raw(raw / "us_c8_5_test_raw.npz"), load_raw(raw / "us_c8_5_test_raw_dc.npz"),
                               "test", np.random.default_rng(seqs[1]))
    results = repo_root / "results"
    records += comparison_pairs(_rows(results / "us_c8_4_comparisons.csv"), _rows(results / "us_c8_4_comparisons_dc.csv"),
                                "validation", "ci_block_low", "ci_block_high", "sign")
    records += comparison_pairs(_rows(results / "us_c8_5_test_run.csv"), _rows(results / "us_c8_5_test_run_dc.csv"),
                                "test", "ci_low", "ci_high", "sign")
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(ROBUSTNESS_COLUMNS))
        writer.writeheader()
        writer.writerows([{k: "" if isinstance(v, float) and math.isnan(v) else v for k, v in r.items()}
                          for r in records])
    make_figure(pd.read_csv(csv_path), png_path)


def make_figure(df: pd.DataFrame, png_path: Path) -> None:
    """A) τ sulla validazione; B) τ sul test; C) differenze appaiate Elo e Dixon-Coles, £0.01, validazione."""
    fig, (ax_a, ax_b, ax_c) = plt.subplots(1, 3, figsize=(22, 6.5))
    x = np.arange(len(PRIMARY_METRICS))
    colors = {"none": "tab:gray", "gbp_0.01": "tab:blue", "gbp_1": "tab:orange"}
    for ax, dataset, title in ((ax_a, "validation", "A) τ di Kendall Elo/Dixon-Coles, validazione (t corretto)"),
                               (ax_b, "test", "B) τ di Kendall Elo/Dixon-Coles, 2023-24 (percentile, soli seed)")):
        tau = df[(df["row_type"] == "tau") & (df["dataset"] == dataset)]
        for k, config in enumerate(CONFIG_NAMES):
            t = tau[tau["config"] == config].set_index("metric").reindex(list(PRIMARY_METRICS))
            est = t["tau"].astype(float).to_numpy()
            lo, hi = t["ci_low"].astype(float).to_numpy(), t["ci_high"].astype(float).to_numpy()
            off = (k - 1) * 0.25
            ok = np.isfinite(est)
            ax.errorbar(x[ok] + off, est[ok], yerr=[np.maximum(est - lo, 0)[ok], np.maximum(hi - est, 0)[ok]],
                        fmt="o", color=colors[config], capsize=3, label=f"F: {config}")
        ax.axhline(0.0, color="black", linewidth=0.8)
        ax.axhline(1.0, color="black", linewidth=0.5, linestyle=":")
        ax.set_xticks(x)
        ax.set_xticklabels(PRIMARY_METRICS, rotation=45, fontsize=8)
        ax.set_ylabel("τ-b di Kendall")
        ax.set_title(title, loc="left", fontsize=10, fontweight="bold")
        ax.legend(fontsize=8)
        ax.grid(True, axis="y", linestyle=":", alpha=0.6)
    comp = df[(df["row_type"] == "comparison") & (df["dataset"] == "validation") & (df["config"] == MAIN_CONFIG)
              & (df["metric"] == "final_log_wealth")]
    y = np.arange(len(comp))
    for off, suffix, color, label in ((-0.15, "elo", "tab:blue", "Elo"), (0.15, "dc", "tab:orange", "Dixon-Coles")):
        est = comp[f"estimate_{suffix}"].astype(float).to_numpy()
        lo, hi = comp[f"ci_low_{suffix}"].astype(float).to_numpy(), comp[f"ci_high_{suffix}"].astype(float).to_numpy()
        ax_c.errorbar(est, y + off, xerr=[np.maximum(est - lo, 0), np.maximum(hi - est, 0)], fmt="o", color=color,
                      capsize=3, label=label)
    ax_c.axvline(0.0, color="black", linewidth=0.8)
    ax_c.set_yticks(y)
    ax_c.set_yticklabels(comp["comparison"])
    ax_c.set_xlabel("Differenza pooled di ln W_T (19 stagioni), intervallo t corretto")
    ax_c.set_title("C) Confronti fra agenti con Elo e Dixon-Coles, £0.01", loc="left", fontsize=10, fontweight="bold")
    ax_c.legend(fontsize=8)
    ax_c.grid(True, axis="x", linestyle=":", alpha=0.6)
    fig.tight_layout()
    fig.savefig(png_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    run_experiment()
