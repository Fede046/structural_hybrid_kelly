"""Script di rilevazione del drift su tutti gli scenari (US-C5.1 / Task 28).

Esegue ADWIN e Page-Hinkley con parametri congelati sulle 22 serie temporali di log-loss
(3 di training e 19 di validazione). Genera:
- results/us_c5_1_drift_detectors.csv: registro dettagliato degli allarmi e riepilogo;
- thesis/figures/us_c5_1_drift_detectors.png: figura a 3 pannelli con i profili dei tre
  scenari di training e la collocazione temporale degli allarmi rilevati.
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
    DRIFT_DETECTOR_CSV_COLUMNS,
    extract_scenario_series,
    generate_drift_detector_records,
)
from shk.model.residuals import compute_model_residuals
from shk.stats.drift import detector_params, run_drift_detector


def run_experiment() -> None:
    """Esegue la generazione del CSV degli allarmi e della figura per la tesi."""
    repo_root = Path(__file__).resolve().parents[1]
    csv_path = repo_root / "results" / "us_c5_1_drift_detectors.csv"
    png_path = repo_root / "thesis" / "figures" / "us_c5_1_drift_detectors.png"

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    png_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Caricamento dati e calcolo residui
    cfg = read_split_config()
    df_hist = load_by_role("history")
    df_train = load_by_role("training")
    df_val = load_by_role("validation")

    df = pd.concat([df_hist, df_train, df_val], ignore_index=True)
    df = df.sort_values("Date", kind="stable").reset_index(drop=True)

    schedule = derive_fit_schedule(cfg)
    df_residuals = compute_model_residuals(df, schedule, ELO_FITS)

    # 2. Generazione record e scrittura CSV
    records = generate_drift_detector_records(df_residuals, schedule)

    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(DRIFT_DETECTOR_CSV_COLUMNS))
        writer.writeheader()
        writer.writerows(records)

    # 3. Generazione figura per i 3 scenari di training
    series_list = extract_scenario_series(df_residuals, schedule)
    training_series = [s for s in series_list if s.role == "training"]

    fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(11, 9), sharex=True)

    for ax, s in zip(axes, training_series, strict=True):
        losses = s.log_loss
        # Calcolo medie di giornata (38 blocchi contigui da 10 partite)
        matchdays = np.arange(1, 39)
        daily_means = [float(np.mean(losses[(g - 1) * 10 : g * 10])) for g in matchdays]
        overall_mean = float(np.mean(losses))

        ax.plot(
            matchdays,
            daily_means,
            color="#1f77b4",
            linewidth=1.6,
            marker="o",
            markersize=3.5,
            label="Log-loss media di giornata",
        )
        ax.axhline(
            overall_mean,
            color="#7f7f7f",
            linestyle="--",
            linewidth=1.2,
            label=f"Media stagione ({overall_mean:.4f})",
        )

        # Rilevazione allarmi
        adwin_params = detector_params("adwin")
        ph_params = detector_params("page_hinkley")
        adwin_alarms = run_drift_detector(losses, "adwin", adwin_params)
        ph_alarms = run_drift_detector(losses, "page_hinkley", ph_params)

        # Marcatura allarmi ADWIN
        if len(adwin_alarms) > 0:
            adwin_days = [int(idx // 10 + 1) for idx in adwin_alarms]
            adwin_vals = [daily_means[d - 1] for d in adwin_days]
            ax.scatter(
                adwin_days,
                adwin_vals,
                color="#2ca02c",
                marker="D",
                s=80,
                zorder=6,
                label=f"Allarme ADWIN (n={len(adwin_alarms)})",
            )
        else:
            # Entry invisibile in legenda per chiarire l'assenza di allarmi
            ax.scatter([], [], color="#2ca02c", marker="D", s=80, label="Allarme ADWIN (n=0)")

        # Marcatura allarmi Page-Hinkley
        if len(ph_alarms) > 0:
            ph_days = [int(idx // 10 + 1) for idx in ph_alarms]
            ph_vals = [daily_means[d - 1] for d in ph_days]
            ax.scatter(
                ph_days,
                ph_vals,
                color="#d62728",
                marker="^",
                s=90,
                zorder=7,
                label=f"Allarme Page-Hinkley (n={len(ph_alarms)})",
            )
        else:
            ax.scatter([], [], color="#d62728", marker="^", s=90, label="Allarme Page-Hinkley (n=0)")

        ax.set_title(
            f"Scenario di training {s.season} (Fit {s.fit_through})",
            fontsize=11,
            fontweight="bold",
        )
        ax.set_ylabel("Log-loss media", fontsize=10)
        ax.set_xticks(np.arange(1, 39, 2))
        ax.grid(True, linestyle=":", alpha=0.6)
        ax.legend(loc="upper right", fontsize=8.5)

    axes[-1].set_xlabel("Giornata (blocco contiguo di 10 partite)", fontsize=10)
    plt.tight_layout()
    fig.savefig(png_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    run_experiment()
