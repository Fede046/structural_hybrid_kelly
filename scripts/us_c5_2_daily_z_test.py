"""Script per il monitoraggio dello Z-test per giornata e confronto con i detector (US-C5.2 / Task 29 e Task 30).

Calcola lo Z-test per giornata (blocchi di 10 partite) sulle 19 stagioni di validazione
utilizzando le baseline di training dei rispettivi fit, calcola le soglie calibrate
per moving block bootstrap (L in {7, 20, 40}) e confronta gli allarmi nominali e calibrati
con quelli di ADWIN e Page-Hinkley.

Genera:
- results/us_c5_2_daily_z_test.csv: file CSV con 860 righe (matchday, summary, overall, verification);
- thesis/figures/us_c5_2_daily_z_test.png: figura a due pannelli (A e B) con gli allarmi per stagione.
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
    DAILY_Z_TEST_CSV_COLUMNS,
    generate_daily_z_test_records,
)
from shk.model.residuals import compute_model_residuals
from shk.stats.false_rejection import BLOCK_LENGTHS


def run_experiment() -> None:
    """Esegue la generazione del CSV dello Z-test e della figura a due pannelli per la tesi."""
    repo_root = Path(__file__).resolve().parents[1]
    csv_path = repo_root / "results" / "us_c5_2_daily_z_test.csv"
    png_path = repo_root / "thesis" / "figures" / "us_c5_2_daily_z_test.png"

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    png_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Caricamento dati e calcolo residui del Modulo 1
    cfg = read_split_config()
    df_hist = load_by_role("history")
    df_train = load_by_role("training")
    df_val = load_by_role("validation")

    df = pd.concat([df_hist, df_train, df_val], ignore_index=True)
    df = df.sort_values("Date", kind="stable").reset_index(drop=True)

    schedule = derive_fit_schedule(cfg)
    df_residuals = compute_model_residuals(df, schedule, ELO_FITS)

    # 2. Generazione record e scrittura CSV
    records = generate_daily_z_test_records(df_residuals, schedule)

    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(DAILY_Z_TEST_CSV_COLUMNS))
        writer.writeheader()
        writer.writerows(records)

    # 3. Preparazione dati per la figura
    summary_rows = [r for r in records if r["row_type"] == "summary"]
    val_seasons = sorted(
        list(dict.fromkeys(r["season"] for r in summary_rows)),
        key=lambda s: int(s.split("-")[0]),
    )

    z_alarms: list[int] = []
    adwin_alarms: list[int] = []
    ph_alarms: list[int] = []
    calib_alarms: dict[int, list[int]] = {l_val: [] for l_val in BLOCK_LENGTHS}

    for s in val_seasons:
        z_row = next(r for r in summary_rows if r["season"] == s and r["method"] == "z_nominal")
        adwin_row = next(r for r in summary_rows if r["season"] == s and r["method"] == "adwin")
        ph_row = next(r for r in summary_rows if r["season"] == s and r["method"] == "page_hinkley")

        z_alarms.append(int(z_row["n_alarms"]))
        adwin_alarms.append(int(adwin_row["n_alarms"]))
        ph_alarms.append(int(ph_row["n_alarms"]))

        for l_val in BLOCK_LENGTHS:
            c_row = next(
                r for r in summary_rows
                if r["season"] == s
                and r["method"] == "z_block_bootstrap"
                and int(r["block_length"]) == l_val
            )
            calib_alarms[l_val].append(int(c_row["n_alarms"]))

    # 4. Generazione figura a due pannelli (2x1) con etichette in italiano
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

    x = np.arange(len(val_seasons))

    # --- Pannello A: Z nominale vs ADWIN vs Page-Hinkley ---
    width_a = 0.26
    ax1.bar(x - width_a, z_alarms, width_a, label="Z-test nominale (α = 0.05)", color="#1f77b4", alpha=0.88)
    ax1.bar(x, adwin_alarms, width_a, label="ADWIN (tarato)", color="#2ca02c", alpha=0.88)
    ax1.bar(x + width_a, ph_alarms, width_a, label="Page-Hinkley (tarato)", color="#ff7f0e", alpha=0.88)

    ax1.axhline(
        1.9,
        color="#d62728",
        linestyle="--",
        linewidth=1.5,
        label="Allarmi attesi per stagione (1.9)",
    )
    ax1.set_ylabel("Numero di allarmi", fontsize=11)
    ax1.set_title(
        "A: Allarmi per stagione di validazione: Z-test nominale vs ADWIN e Page-Hinkley",
        fontsize=12,
        fontweight="bold",
    )
    ax1.set_xticks(x)
    ax1.set_xticklabels(val_seasons, rotation=45, ha="right", fontsize=9)
    ax1.set_ylim(bottom=0)
    ax1.legend(frameon=True, fontsize=9, loc="upper right")
    ax1.grid(axis="y", linestyle=":", alpha=0.5)

    # --- Pannello B: Z nominale vs Z calibrato per ciascuna L ---
    width_b = 0.20
    colors_b = {7: "#2ca02c", 20: "#9467bd", 40: "#8c564b"}
    ax2.bar(x - 1.5 * width_b, z_alarms, width_b, label="Z-test nominale (α = 0.05)", color="#1f77b4", alpha=0.88)
    for idx_l, l_val in enumerate(BLOCK_LENGTHS):
        offset = (-0.5 + idx_l) * width_b
        ax2.bar(
            x + offset,
            calib_alarms[l_val],
            width_b,
            label=f"Z-test calibrato (L = {l_val})",
            color=colors_b[l_val],
            alpha=0.88,
        )

    ax2.axhline(
        1.9,
        color="#d62728",
        linestyle="--",
        linewidth=1.5,
        label="Allarmi attesi per stagione (1.9)",
    )
    ax2.set_xlabel("Stagione di validazione", fontsize=11)
    ax2.set_ylabel("Numero di allarmi", fontsize=11)
    ax2.set_title(
        "B: Allarmi per stagione di validazione: Z-test nominale vs Z-test calibrato per ciascuna L",
        fontsize=12,
        fontweight="bold",
    )
    ax2.set_xticks(x)
    ax2.set_xticklabels(val_seasons, rotation=45, ha="right", fontsize=9)
    ax2.set_ylim(bottom=0)
    ax2.legend(frameon=True, fontsize=9, loc="upper right")
    ax2.grid(axis="y", linestyle=":", alpha=0.5)

    plt.tight_layout()
    plt.savefig(png_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    run_experiment()
