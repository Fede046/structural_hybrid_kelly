"""Script T45 (US-C7.1): Oaxaca-Blinder su verità nota sintetica.

Per cinque casi (misto, solo composizione, solo struttura, covariata omessa con drift
virtuale puro, errori AR(1)) e R = 1 000 repliche: stime medie, verità, errore standard
Monte Carlo, copertura degli intervalli iid al 95%, residui d'identità e two-fold per
riferimento. Scrive results/us_c7_1_ob_synthetic.csv e thesis/figures/us_c7_1_ob_synthetic.png.
"""

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from shk.stats.oaxaca_synthetic import (
    CASES,
    COMPONENTS,
    OB_SYNTHETIC_CSV_COLUMNS,
    SEED_S8,
    evaluate_synthetic_cases,
)

COMPONENT_LABELS = {
    "total": "Totale",
    "compositional": "Compositiva",
    "structural": "Strutturale",
    "interaction": "Interazione",
}
CASE_LABELS = {
    "a_mixed": "(a) misto",
    "b_composition": "(b) solo composizione",
    "c_structure": "(c) solo struttura",
    "d_omitted_virtual": "(d) covariata omessa",
    "e_ar1": "(e) errori AR(1)",
}


def run_experiment() -> None:
    """Esegue i casi, scrive il CSV e la figura."""
    repo_root = Path(__file__).resolve().parents[1]
    csv_path = repo_root / "results" / "us_c7_1_ob_synthetic.csv"
    png_path = repo_root / "thesis" / "figures" / "us_c7_1_ob_synthetic.png"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    png_path.parent.mkdir(parents=True, exist_ok=True)

    _, records = evaluate_synthetic_cases(seed=SEED_S8)
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(OB_SYNTHETIC_CSV_COLUMNS))
        writer.writeheader()
        writer.writerows(records)

    comp_rows = [r for r in records if r["row_type"] == "component"]
    fig, axes = plt.subplots(1, len(CASES), figsize=(22, 5), sharey=True)
    for ax, case in zip(axes, CASES):
        rows = [r for r in comp_rows if r["case"] == case.name]
        x_pos = np.arange(len(COMPONENTS))
        means = [float(r["mean"]) for r in rows]
        errs = [3.0 * float(r["mc_se"]) for r in rows]
        truths = [float(r["truth"]) for r in rows]
        ax.bar(x_pos, means, color="tab:blue", alpha=0.7, yerr=errs, capsize=4,
               label="Media delle stime ± 3 e.s. MC")
        ax.scatter(x_pos, truths, color="tab:red", marker="D", zorder=3, label="Valore vero")
        ax.axhline(0.0, color="black", linewidth=0.8)
        ax.set_xticks(x_pos)
        ax.set_xticklabels([COMPONENT_LABELS[c] for c in COMPONENTS], rotation=30, fontsize=9)
        ax.set_title(CASE_LABELS[case.name], fontsize=11, fontweight="bold")
        ax.grid(True, axis="y", linestyle=":", alpha=0.6)
    axes[0].set_ylabel("Componente (scala di y)")
    axes[0].legend(loc="upper left", fontsize=8)
    fig.suptitle("Oaxaca-Blinder three-fold su verità nota (R = 1 000, n = 190 per gruppo)", fontsize=12)
    fig.tight_layout()
    fig.savefig(png_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    run_experiment()
