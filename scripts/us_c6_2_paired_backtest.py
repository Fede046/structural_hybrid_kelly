"""Script per l'esecuzione appaiata degli agenti A, B ed E sulle 19 stagioni di validazione (US-C6.2 / Task 35).

Scrive results/us_c6_2_paired_backtest.csv e genera la figura a tre pannelli
thesis/figures/us_c6_2_paired_backtest.png.
"""

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from shk.data.split import load_by_role, read_split_config
from shk.model.elo_fit import ELO_FITS, derive_fit_schedule, parse_season_start_year
from shk.model.paired_backtest import (
    PAIRED_BACKTEST_CSV_COLUMNS,
    evaluate_validation_seasons,
)
from shk.model.residuals import compute_model_residuals


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
    cfg = read_split_config()
    df_hist = load_by_role("history")
    df_train = load_by_role("training")
    df_val = load_by_role("validation")

    df = pd.concat([df_hist, df_train, df_val], ignore_index=True)
    df = df.sort_values("Date", kind="stable").reset_index(drop=True)

    schedule = derive_fit_schedule(cfg)
    df_residuals = compute_model_residuals(df, schedule, ELO_FITS)

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

    fig, axes = plt.subplots(3, 1, figsize=(13, 14), sharex=True)

    # --------------------------------------------------------------------------
    # Pannello A: ln B_T per stagione dei quattro agenti con F = £0.01
    # Poiché l'agente A (Kelly pieno) presenta escursioni di scala molto maggiori
    # rispetto agli agenti B ed E, A viene tracciato su un asse Y secondario dedicato.
    # --------------------------------------------------------------------------
    ax_a = axes[0]
    ax_a_right = ax_a.twinx()

    b025_vals = [float(lookup[(s, "gbp_0.01", "B_0.25")]["final_log_wealth"]) for s in seasons]
    b010_vals = [float(lookup[(s, "gbp_0.01", "B_0.10")]["final_log_wealth"]) for s in seasons]
    e_vals = [float(lookup[(s, "gbp_0.01", "E")]["final_log_wealth"]) for s in seasons]
    a_vals = [float(lookup[(s, "gbp_0.01", "A")]["final_log_wealth"]) for s in seasons]

    line_b025 = ax_a.plot(x_indices, b025_vals, marker="o", color="tab:blue", label="B 0.25")[0]
    line_b010 = ax_a.plot(x_indices, b010_vals, marker="s", color="tab:green", label="B 0.10")[0]
    line_e = ax_a.plot(x_indices, e_vals, marker="^", color="tab:orange", label="E (Puntata minima)")[0]
    line_a = ax_a_right.plot(x_indices, a_vals, marker="D", color="tab:red", linestyle="--", label="A (Kelly pieno, asse dx)")[0]

    ax_a.axhline(0.0, color="gray", linestyle=":", alpha=0.6)
    ax_a.set_ylabel("ln B_T per B ed E (F = £0.01)")
    ax_a_right.set_ylabel("ln B_T per A (asse destro)", color="tab:red")
    ax_a_right.tick_params(axis="y", labelcolor="tab:red")
    ax_a.set_title("(A) Log-ricchezza finale per stagione con floor F = £0.01")

    lines_a_all = [line_b025, line_b010, line_e, line_a]
    labels_a_all = [line.get_label() for line in lines_a_all]
    ax_a.legend(lines_a_all, labels_a_all, loc="upper right")
    ax_a.grid(True, linestyle=":", alpha=0.5)

    # --------------------------------------------------------------------------
    # Pannello B: Differenza appaiata ln B_T(F = £1) - ln B_T(F = 0) per A, B_0.25, B_0.10
    # --------------------------------------------------------------------------
    ax_b = axes[1]
    for agent_name, color, marker, label in (
        ("A", "tab:red", "D", "A (Kelly pieno)"),
        ("B_0.25", "tab:blue", "o", "B 0.25"),
        ("B_0.10", "tab:green", "s", "B 0.10"),
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
    ax_b.legend(loc="upper right")
    ax_b.grid(True, linestyle=":", alpha=0.5)

    # --------------------------------------------------------------------------
    # Pannello C: ROI di E per stagione con F = £0.01 e F = £1
    # Linee orizzontali a -0.041 (GPT-5.4) e -0.051 (nota 3.4 §9)
    # --------------------------------------------------------------------------
    ax_c = axes[2]
    roi_e_001 = [float(lookup[(s, "gbp_0.01", "E")]["roi"]) for s in seasons]
    roi_e_1 = [float(lookup[(s, "gbp_1", "E")]["roi"]) for s in seasons]

    ax_c.plot(x_indices, roi_e_001, marker="^", color="tab:orange", label="E (F = £0.01)")
    ax_c.plot(x_indices, roi_e_1, marker="v", color="tab:purple", linestyle="--", label="E (F = £1.00)")

    # Linee orizzontali di riferimento
    ax_c.axhline(-0.041, color="tab:green", linestyle="--", label="Miglior seed paper GPT-5.4 (-4.1%)")
    ax_c.axhline(-0.051, color="tab:red", linestyle=":", label="Seed dedotto nota 3.4 §9 (-5.1%)")

    # Verifica e marcatura di eventuali stagioni rovinate per E
    for s_idx, s in enumerate(seasons):
        for cfg_name, marker_sym, color_sym in (
            ("gbp_0.01", "^", "tab:orange"),
            ("gbp_1", "v", "tab:purple"),
        ):
            rec_e = lookup[(s, cfg_name, "E")]
            if bool(rec_e["ruined"]):
                roi_val = float(rec_e["roi"])
                ax_c.scatter(
                    [s_idx],
                    [roi_val],
                    color="red",
                    s=120,
                    marker="X",
                    zorder=5,
                    label="Rovina (W < F)" if s_idx == 0 else None,
                )

    ax_c.set_ylabel("ROI (final_wealth - 1)")
    ax_c.set_title("(C) Ritorno sull'investimento (ROI) di MinimumStakeAgent (E)")
    ax_c.set_xticks(x_indices)
    ax_c.set_xticklabels(seasons, rotation=45, ha="right")
    ax_c.set_xlabel("Stagione di validazione")
    ax_c.legend(loc="upper right")
    ax_c.grid(True, linestyle=":", alpha=0.5)

    fig.tight_layout()
    fig.savefig(png_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    run_experiment()
