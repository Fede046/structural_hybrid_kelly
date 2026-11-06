"""Script per l'esecuzione appaiata degli agenti A e B_0.25 sulle 19 stagioni di validazione.

Scrive results/us_c6_2_paired_backtest.csv e genera la figura a due pannelli
thesis/figures/us_c6_2_paired_backtest.png.
"""

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from shk.model.elo_fit import parse_season_start_year
from shk.model.paired_backtest import (
    PAIRED_BACKTEST_CSV_COLUMNS,
    evaluate_validation_seasons,
)
from shk.model.residuals import load_model_residuals


def run_experiment() -> None:
    """Esegue il backtest appaiato sulle stagioni di validazione, salva CSV e figura."""
    repo_root = Path(__file__).resolve().parents[1]
    results_dir = repo_root / "results"
    figures_dir = repo_root / "thesis" / "figures"
    results_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    csv_path = results_dir / "us_c6_2_paired_backtest.csv"
    png_path = figures_dir / "us_c6_2_paired_backtest.png"

    # Caricamento dei dati tramite split config (history, training, validation)
    data = load_model_residuals()
    df, schedule, df_residuals = data.df, data.schedule, data.residuals

    records = evaluate_validation_seasons(df_residuals, df, schedule)

    # Scrittura del file CSV con le 31 colonne prescritte
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(PAIRED_BACKTEST_CSV_COLUMNS))
        writer.writeheader()
        writer.writerows(records)

    # Costruzione della figura direttamente dai record calcolati
    season_rows = [r for r in records if r["row_type"] == "season"]
    seasons = sorted({str(r["season"]) for r in season_rows}, key=parse_season_start_year)
    x_indices = np.arange(len(seasons))

    # Indicizzazione rapida dei record di stagione per (season, config, agent)
    lookup: dict[tuple[str, str, str], dict[str, str | int | float]] = {
        (str(r["season"]), str(r["config"]), str(r["agent"])): r for r in season_rows
    }

    fig, axes = plt.subplots(2, 1, figsize=(13, 10), sharex=True)

    # --------------------------------------------------------------------------
    # Pannello A: ln B_T per stagione dei due agenti con F = £0.01
    # Poiché l'agente A (Kelly pieno) presenta escursioni di scala molto maggiori
    # rispetto a B_0.25, A viene tracciato su un asse Y secondario dedicato.
    # --------------------------------------------------------------------------
    ax_a = axes[0]
    ax_a_right = ax_a.twinx()

    b025_vals = [float(lookup[(s, "gbp_0.01", "B_0.25")]["final_log_wealth"]) for s in seasons]
    a_vals = [float(lookup[(s, "gbp_0.01", "A")]["final_log_wealth"]) for s in seasons]

    line_b025 = ax_a.plot(x_indices, b025_vals, marker="o", color="tab:blue", label="B 0.25")[0]
    line_a = ax_a_right.plot(x_indices, a_vals, marker="D", color="tab:red", linestyle="--", label="A (Kelly pieno, asse dx)")[0]

    ax_a.axhline(0.0, color="gray", linestyle=":", alpha=0.6)
    ax_a.set_ylabel("ln B_T per B 0.25 (F = £0.01)")
    ax_a_right.set_ylabel("ln B_T per A (asse destro)", color="tab:red")
    ax_a_right.tick_params(axis="y", labelcolor="tab:red")
    ax_a.set_title("(A) Log-ricchezza finale per stagione con floor F = £0.01")

    lines_a_all = [line_b025, line_a]
    labels_a_all = [line.get_label() for line in lines_a_all]
    ax_a.legend(lines_a_all, labels_a_all, loc="upper right")
    ax_a.grid(True, linestyle=":", alpha=0.5)

    # --------------------------------------------------------------------------
    # Pannello B: Differenza appaiata ln B_T(F = £1) - ln B_T(F = 0) per A e B_0.25
    # --------------------------------------------------------------------------
    ax_b = axes[1]
    for agent_name, color, marker, label in (
        ("A", "tab:red", "D", "A (Kelly pieno)"),
        ("B_0.25", "tab:blue", "o", "B 0.25"),
    ):
        diffs = []
        for s in seasons:
            lw_f1 = float(lookup[(s, "gbp_1", agent_name)]["final_log_wealth"])
            lw_f0 = float(lookup[(s, "none", agent_name)]["final_log_wealth"])
            diffs.append(lw_f1 - lw_f0)
        ax_b.plot(x_indices, diffs, marker=marker, color=color, label=label)

    ax_b.axhline(0.0, color="gray", linestyle="--", alpha=0.7)
    ax_b.set_ylabel("ln B_T(F = £1) - ln B_T(F = £0)")
    ax_b.set_title("(B) Differenza appaiata di log-ricchezza finale tra F = £1 e F = £0")
    ax_b.set_xticks(x_indices)
    ax_b.set_xticklabels(seasons, rotation=45, ha="right")
    ax_b.set_xlabel("Stagione di validazione")
    ax_b.legend(loc="upper right")
    ax_b.grid(True, linestyle=":", alpha=0.5)


    fig.tight_layout()
    fig.savefig(png_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    run_experiment()
