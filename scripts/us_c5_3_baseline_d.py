"""Script per l'esecuzione appaiata della Baseline D sulle stagioni di validazione (US-C5.3 / Task 32).

Esegue i tre agenti (reference con quarto-Kelly fisso, d_adwin con KAPPA_ADWIN,
d_page_hinkley con KAPPA_PAGE_HINKLEY) sulle 19 stagioni di validazione,
scrive il file results/us_c5_3_baseline_d.csv e genera la figura thesis/figures/us_c5_3_baseline_d.png.
"""

import csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from shk.data.split import load_by_role, read_split_config
from shk.model.elo_fit import ELO_FITS, derive_fit_schedule
from shk.model.monitoring import (
    BASELINE_D_CSV_COLUMNS,
    generate_baseline_d_records,
)
from shk.model.residuals import compute_model_residuals


def run_experiment() -> None:
    """Esegue l'esperimento di backtest appaiato della Baseline D e salva CSV e figura."""
    repo_root = Path(__file__).resolve().parents[1]
    results_dir = repo_root / "results"
    figures_dir = repo_root / "thesis" / "figures"
    results_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    csv_path = results_dir / "us_c5_3_baseline_d.csv"
    png_path = figures_dir / "us_c5_3_baseline_d.png"

    # Caricamento dei dati tramite split config (history, training, validation; no test)
    cfg = read_split_config()
    df_hist = load_by_role("history")
    df_train = load_by_role("training")
    df_val = load_by_role("validation")

    df = pd.concat([df_hist, df_train, df_val], ignore_index=True)
    df = df.sort_values("Date", kind="stable").reset_index(drop=True)

    schedule = derive_fit_schedule(cfg)
    df_residuals = compute_model_residuals(df, schedule, ELO_FITS)

    records = generate_baseline_d_records(df_residuals, df, schedule)

    # Scrittura del file CSV con le 9 colonne prescritte
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(BASELINE_D_CSV_COLUMNS))
        writer.writeheader()
        writer.writerows(records)

    # Preparazione dei dati per il grafico delle differenze appaiate
    season_rows = [r for r in records if r["row_type"] == "season"]
    seasons = sorted({r["season"] for r in season_rows})

    diff_adwin = []
    diff_ph = []
    for s in seasons:
        s_records = {r["agent"]: r for r in season_rows if r["season"] == s}
        ref_lw = float(s_records["reference"]["final_log_wealth"])
        adw_lw = float(s_records["d_adwin"]["final_log_wealth"])
        ph_lw = float(s_records["d_page_hinkley"]["final_log_wealth"])
        diff_adwin.append(adw_lw - ref_lw)
        diff_ph.append(ph_lw - ref_lw)

    # Generazione figura
    fig, ax = plt.subplots(figsize=(12, 6))
    x_indices = np.arange(len(seasons))
    width = 0.35

    ax.bar(x_indices - width / 2, diff_adwin, width=width, label="D-ADWIN − Riferimento (κ = 1.0)", color="#2b5c8f", alpha=0.85)
    ax.bar(x_indices + width / 2, diff_ph, width=width, label="D-Page-Hinkley − Riferimento (κ = 1.0)", color="#d95f02", alpha=0.85)
    ax.axhline(0.0, color="black", linestyle="--", linewidth=1.0, alpha=0.7)

    ax.set_xticks(x_indices)
    ax.set_xticklabels(seasons, rotation=45, ha="right", fontsize=9)
    ax.set_xlabel("Stagione di validazione", fontsize=11)
    ax.set_ylabel("Differenza di log-ricchezza finale (D − Riferimento)", fontsize=11)
    ax.set_title("Differenze appaiate di log-ricchezza finale per stagione di validazione (US-C5.3)", fontsize=12)
    ax.set_ylim(-0.05, 0.05)
    ax.grid(axis="y", linestyle=":", alpha=0.6)
    ax.legend(loc="upper right", frameon=True)

    plt.tight_layout()
    fig.savefig(png_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    run_experiment()
