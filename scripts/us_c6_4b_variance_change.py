"""Script T44: diagnostiche della varianza nel tempo sui residui del Modulo 1 (seguito di C6.4).

Scrive results/us_c6_4b_variance_change.csv e thesis/figures/us_c6_4b_variance_change.png.
Con --module1 dixon_coles usa il Modulo 1 Dixon-Coles e scrive le uscite con il suffisso _dc,
senza toccare quelle Elo (T60).
"""

import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from shk.model.module1 import MODULE1_ELO, module1_from_argv, with_module1_suffix
from shk.model.residuals import load_model_residuals
from shk.model.variance_change import (
    CALIBRATED_METHODS,
    METHOD_NOMINAL,
    TIME_STATISTICS,
    VARIANCE_CHANGE_CSV_COLUMNS,
    evaluate_variance_change,
)
from shk.stats.false_rejection import SEED_S7

STAT_LABELS = {
    "goldfeld_quandt": "Goldfeld-Quandt (|ln F|)",
    "arch_lm": "ARCH-LM (q = 10)",
    "rolling_log_variance": "Max |ln var mobile|",
    "brown_forsythe": "Brown-Forsythe",
}


def run_experiment(module1: str = MODULE1_ELO) -> None:
    """Calcola i record, scrive il CSV e la figura a tre pannelli."""
    repo_root = Path(__file__).resolve().parents[1]
    csv_path = with_module1_suffix(repo_root / "results" / "us_c6_4b_variance_change.csv", module1)
    png_path = with_module1_suffix(repo_root / "thesis" / "figures" / "us_c6_4b_variance_change.png", module1)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    png_path.parent.mkdir(parents=True, exist_ok=True)

    data = load_model_residuals(module1=module1)
    records = evaluate_variance_change(data.residuals, data.schedule, seed=SEED_S7)

    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(VARIANCE_CHANGE_CSV_COLUMNS))
        writer.writeheader()
        writer.writerows(records)

    fig, (ax_a, ax_b, ax_c) = plt.subplots(1, 3, figsize=(20, 6))

    # Pannello A: media e varianza di z per stagione
    moments = [r for r in records if r["row_type"] == "z_moments"]
    x_pos = np.arange(len(moments))
    ax_a.plot(x_pos, [r["z_var"] for r in moments], "o-", color="tab:blue", label="Varianza di $z_t$")
    ax_a.plot(x_pos, [r["z_mean"] for r in moments], "s--", color="tab:orange", label="Media di $z_t$")
    ax_a.axhline(1.0, color="tab:blue", linestyle=":", linewidth=1.0)
    ax_a.axhline(0.0, color="tab:orange", linestyle=":", linewidth=1.0)
    for i, r in enumerate(moments):
        if r["role"] == "training":
            ax_a.axvspan(i - 0.4, i + 0.4, color="tab:green", alpha=0.12)
    ax_a.set_xticks(x_pos)
    ax_a.set_xticklabels([r["season"] for r in moments], rotation=75, fontsize=8)
    ax_a.set_title("A) Residui standardizzati per varentropia", loc="left", fontsize=11, fontweight="bold")
    ax_a.grid(True, linestyle=":", alpha=0.6)
    ax_a.legend(fontsize=9)

    # Pannello B: rigetti sulle 19 stagioni di validazione per statistica e metodo
    summary = {(r["statistic"], r["method"]): int(r["rejections"]) for r in records if r["row_type"] == "summary"}
    methods = (METHOD_NOMINAL,) + CALIBRATED_METHODS
    width = 0.15
    for j, method in enumerate(methods):
        values = [summary.get((stat, method), np.nan) for stat in TIME_STATISTICS]
        ax_b.bar(np.arange(len(TIME_STATISTICS)) + (j - 2) * width, values, width=width, label=method)
    ax_b.axhline(19 * 0.05, color="black", linestyle="--", linewidth=1.0, label="Atteso sotto H$_0$ (0.95)")
    ax_b.set_xticks(np.arange(len(TIME_STATISTICS)))
    ax_b.set_xticklabels([STAT_LABELS[s] for s in TIME_STATISTICS], fontsize=9)
    ax_b.set_ylabel("Stagioni di validazione con rigetto (su 19)")
    ax_b.set_title("B) Rigetti per statistica e soglia", loc="left", fontsize=11, fontweight="bold")
    ax_b.grid(True, axis="y", linestyle=":", alpha=0.6)
    ax_b.legend(fontsize=8)

    # Pannello C: verifica delle soglie calibrate
    verif = [r for r in records if r["row_type"] == "verification"]
    labels = [f"{r['fit_through']}\n{STAT_LABELS[r['statistic']]}\n{r['method']}" for r in verif]
    rates = [float(r["rejection_rate"]) for r in verif]
    colors = ["tab:green" if r["within_interval"] else "tab:red" for r in verif]
    ax_c.scatter(np.arange(len(verif)), rates, c=colors, s=18)
    ax_c.axhspan(float(verif[0]["mc_lower"]), float(verif[0]["mc_upper"]), color="gray", alpha=0.2,
                 label="Intervallo con Bonferroni (T39)")
    ax_c.axhline(0.05, color="black", linestyle="--", linewidth=1.0, label=r"$\alpha = 0.05$")
    ax_c.set_xticks(np.arange(len(verif))[::4])
    ax_c.set_xticklabels(labels[::4], rotation=90, fontsize=6)
    ax_c.set_ylabel("Tasso di rigetto su 1 000 ricampionamenti")
    ax_c.set_title("C) Verifica delle soglie calibrate", loc="left", fontsize=11, fontweight="bold")
    ax_c.grid(True, linestyle=":", alpha=0.6)
    ax_c.legend(fontsize=8)

    fig.tight_layout()
    fig.savefig(png_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    run_experiment(module1_from_argv(sys.argv[1:]))
