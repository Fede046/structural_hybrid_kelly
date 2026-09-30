"""Script per il monitoraggio dello Z-test per giornata e confronto con i detector (US-C5.2 / Task 29).

Calcola lo Z-test per giornata (blocchi di 10 partite) sulle 19 stagioni di validazione
utilizzando le baseline di training dei rispettivi fit, e confronta gli allarmi nominali
con quelli di ADWIN e Page-Hinkley.

Genera:
- results/us_c5_2_daily_z_test.csv: file CSV con 782 righe (matchday, summary, overall);
- thesis/figures/us_c5_2_daily_z_test.png: grafico a barre raggruppate con gli allarmi per stagione e metodo.
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


def run_experiment() -> None:
    """Esegue la generazione del CSV dello Z-test e della figura per la tesi."""
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

    for s in val_seasons:
        z_row = next(r for r in summary_rows if r["season"] == s and r["method"] == "z_nominal")
        adwin_row = next(r for r in summary_rows if r["season"] == s and r["method"] == "adwin")
        ph_row = next(r for r in summary_rows if r["season"] == s and r["method"] == "page_hinkley")

        z_alarms.append(int(z_row["n_alarms"]))
        adwin_alarms.append(int(adwin_row["n_alarms"]))
        ph_alarms.append(int(ph_row["n_alarms"]))

    # 4. Generazione figura a barre raggruppate
    fig, ax = plt.subplots(figsize=(14, 6))

    x = np.arange(len(val_seasons))
    width = 0.26

    ax.bar(x - width, z_alarms, width, label="Z-test nominale (α = 0.05)", color="#1f77b4", alpha=0.88)
    ax.bar(x, adwin_alarms, width, label="ADWIN (tarato)", color="#2ca02c", alpha=0.88)
    ax.bar(x + width, ph_alarms, width, label="Page-Hinkley (tarato)", color="#ff7f0e", alpha=0.88)

    # Linea orizzontale a quota 1.9 (allarmi attesi per stagione)
    ax.axhline(
        1.9,
        color="#d62728",
        linestyle="--",
        linewidth=1.5,
        label="Allarmi attesi per stagione (1.9)",
    )

    ax.set_xlabel("Stagione di validazione", fontsize=11)
    ax.set_ylabel("Numero di allarmi", fontsize=11)
    ax.set_title(
        "Allarmi per stagione di validazione: Z-test nominale vs ADWIN e Page-Hinkley",
        fontsize=12,
    )
    ax.set_xticks(x)
    ax.set_xticklabels(val_seasons, rotation=45, ha="right", fontsize=9)
    ax.set_ylim(bottom=0)
    ax.legend(frameon=True, fontsize=10, loc="upper right")
    ax.grid(axis="y", linestyle=":", alpha=0.5)

    plt.tight_layout()
    plt.savefig(png_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    run_experiment()
