"""Script: scelta della candidata del Modulo 3 su verità sintetica.

Scrive results/us_c8_1a_module3_synthetic.csv e thesis/figures/us_c8_1a_module3_synthetic.png
(shk.model.module3_synthetic).
"""

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from shk.model.module3 import CANDIDATES
from shk.model.module3_synthetic import MODULE3_SYNTHETIC_CSV_COLUMNS, REGIMES, evaluate_module3_synthetic

REGIME_LABELS = {"i_stationary": "(i) stazionario", "ii_compositional": "(ii) compositivo",
                 "iii_structural": "(iii) strutturale", "iv_both": "(iv) entrambi"}


def run_experiment() -> None:
    """Valuta le candidate sui quattro regimi e sulla trappola; scrive CSV e figura a tre pannelli."""
    repo_root = Path(__file__).resolve().parents[1]
    csv_path = repo_root / "results" / "us_c8_1a_module3_synthetic.csv"
    png_path = repo_root / "thesis" / "figures" / "us_c8_1a_module3_synthetic.png"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    png_path.parent.mkdir(parents=True, exist_ok=True)

    chosen, _, _, records = evaluate_module3_synthetic()

    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(MODULE3_SYNTHETIC_CSV_COLUMNS))
        writer.writeheader()
        writer.writerows(records)

    df = pd.DataFrame(records)
    fig, (ax_a, ax_b, ax_c) = plt.subplots(1, 3, figsize=(21, 6.5))
    x = np.arange(len(REGIMES))
    colors = {"C0": "tab:gray", "C1": "tab:olive", "P1": "tab:red", "P2": "tab:blue", "P3": "tab:green"}

    # Pannello A: MSE fra λ̂ e λ* per candidata e regime
    crit = df[df["row_type"] == "criterion"]
    width = 0.26
    for j, c in enumerate(CANDIDATES):
        vals = [float(crit[(crit["regime"] == r) & (crit["candidate"] == c)]["mse"].iloc[0]) for r in REGIMES]
        label = f"{c} (scelta)" if c == chosen else c
        ax_a.bar(x + (j - 1) * width, vals, width, color=colors[c], label=label)
    ax_a.set_xticks(x)
    ax_a.set_xticklabels([REGIME_LABELS[r] for r in REGIMES], fontsize=9)
    ax_a.set_ylabel("MSE fra λ̂ e λ* oracolo")
    ax_a.set_title("A) Criterio di scelta per regime", loc="left", fontsize=11, fontweight="bold")
    ax_a.legend(fontsize=9)
    ax_a.grid(True, axis="y", linestyle=":", alpha=0.6)

    # Pannello B: crescita mediana contro drawdown medio dei bracci per regime
    arms = df[df["row_type"] == "arm"]
    markers = dict(zip(REGIMES, ("o", "s", "^", "D")))
    for r in REGIMES:
        for a in ("C0", "C1", *CANDIDATES):
            row = arms[(arms["regime"] == r) & (arms["arm"] == a)].iloc[0]
            ax_b.scatter(float(row["mean_max_drawdown"]), float(row["median_final_wealth"]), color=colors[a],
                         marker=markers[r], s=45)
    for a in ("C0", "C1", *CANDIDATES):
        ax_b.scatter([], [], color=colors[a], marker="o", label=a)
    for r in REGIMES:
        ax_b.scatter([], [], color="black", marker=markers[r], label=REGIME_LABELS[r])
    ax_b.axhline(1.0, color="black", linewidth=0.8)
    ax_b.set_xlabel("Drawdown massimo medio")
    ax_b.set_ylabel("Ricchezza finale mediana")
    ax_b.set_title("B) Bracci nei quattro regimi (C1 con κ = 0.4)", loc="left", fontsize=11, fontweight="bold")
    ax_b.legend(fontsize=8, ncol=2)
    ax_b.grid(True, linestyle=":", alpha=0.6)

    # Pannello C: trappola della nota 3.2 §7.5
    trap = df[df["row_type"] == "trap"]
    for _, row in trap.iterrows():
        ax_c.scatter(float(row["mean_max_drawdown"]), float(row["median_final_wealth"]), color=colors[row["arm"]],
                     s=70, label=row["arm"])
    ax_c.axhline(1.0, color="black", linewidth=0.8)
    ax_c.set_xlabel("Drawdown massimo medio")
    ax_c.set_ylabel("Ricchezza finale mediana")
    ax_c.set_title("C) Trappola (abl32b): P2 contro P1", loc="left", fontsize=11, fontweight="bold")
    ax_c.legend(fontsize=9)
    ax_c.grid(True, linestyle=":", alpha=0.6)

    fig.tight_layout()
    fig.savefig(png_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    run_experiment()
