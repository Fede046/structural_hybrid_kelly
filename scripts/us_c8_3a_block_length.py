"""Script T42: lunghezza dei blocchi di Politis-White sulle serie di log-loss del Modulo 1.

Per la serie di training di ciascun fit e per ciascuna stagione di validazione riporta
L_PW stationary, L_PW circolare e la più vicina fra 7, 20 e 40; aggiunge la copertura
Monte Carlo dell'intervallo al 95% della media di AR(1) con stationary bootstrap a L_PW
contro il bootstrap iid. Scrive results/us_c8_3a_block_length.csv e
thesis/figures/us_c8_3a_block_length.png.
"""

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from shk.model.block_length import (
    BLOCK_LENGTH_CSV_COLUMNS,
    METHOD_IID,
    METHOD_STATIONARY_L_PW,
    ROW_TYPE_COVERAGE,
    ROW_TYPE_SERIES,
    SERIES_KIND_TRAINING,
    compute_mean_coverage_records,
    compute_series_block_length_records,
)
from shk.model.residuals import load_model_residuals
from shk.stats.false_rejection import BLOCK_LENGTHS, SEED_S7


def run_experiment() -> None:
    """Calcola i record, scrive il CSV e la figura a due pannelli."""
    repo_root = Path(__file__).resolve().parents[1]
    csv_path = repo_root / "results" / "us_c8_3a_block_length.csv"
    png_path = repo_root / "thesis" / "figures" / "us_c8_3a_block_length.png"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    png_path.parent.mkdir(parents=True, exist_ok=True)

    data = load_model_residuals()
    series_records = compute_series_block_length_records(data.residuals, data.schedule)
    coverage_records = compute_mean_coverage_records(seed=SEED_S7)
    records = series_records + coverage_records

    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(BLOCK_LENGTH_CSV_COLUMNS))
        writer.writeheader()
        writer.writerows(records)

    fig, (ax_a, ax_b) = plt.subplots(
        1, 2, figsize=(16, 6), gridspec_kw={"width_ratios": [3, 1]}
    )

    # Pannello A: L_PW per serie
    series_rows = [r for r in records if r["row_type"] == ROW_TYPE_SERIES]
    labels = [
        f"train ≤ {r['fit_through']}"
        if r["series_kind"] == SERIES_KIND_TRAINING
        else str(r["seasons"])
        for r in series_rows
    ]
    x_pos = np.arange(len(series_rows))
    ax_a.plot(
        x_pos,
        [float(r["l_pw_stationary"]) for r in series_rows],
        "o",
        color="tab:blue",
        label=r"$L_{PW}$ stationary",
    )
    ax_a.plot(
        x_pos,
        [float(r["l_pw_circular"]) for r in series_rows],
        "s",
        color="tab:orange",
        label=r"$L_{PW}$ circolare",
    )
    for l_val in BLOCK_LENGTHS:
        ax_a.axhline(l_val, color="gray", linestyle="--", linewidth=0.8)
        ax_a.annotate(
            f"L = {l_val}",
            xy=(len(series_rows) - 0.5, l_val),
            fontsize=8,
            color="gray",
            va="bottom",
            ha="right",
        )
    train_idx = [i for i, r in enumerate(series_rows) if r["series_kind"] == SERIES_KIND_TRAINING]
    for i in train_idx:
        ax_a.axvspan(i - 0.4, i + 0.4, color="tab:green", alpha=0.12)
    ax_a.set_xticks(x_pos)
    ax_a.set_xticklabels(labels, rotation=75, fontsize=8)
    ax_a.set_ylabel("Lunghezza ottima dei blocchi")
    ax_a.set_title(
        "A) Lunghezza di Politis-White (correzione 2009) sulla log-loss del Modulo 1",
        loc="left",
        fontsize=11,
        fontweight="bold",
    )
    ax_a.grid(True, linestyle=":", alpha=0.6)
    ax_a.legend(loc="upper left", fontsize=9)

    # Pannello B: copertura dell'intervallo al 95% della media di AR(1)
    coverage_rows = [r for r in records if r["row_type"] == ROW_TYPE_COVERAGE]
    names = {
        METHOD_STATIONARY_L_PW: r"Stationary, $L_{PW}$",
        METHOD_IID: "iid ($L = 1$)",
    }
    cov_values = [float(r["coverage"]) for r in coverage_rows]
    ax_b.bar(
        [names[str(r["method"])] for r in coverage_rows],
        cov_values,
        color=["tab:blue", "tab:red"],
        width=0.5,
    )
    mc_lower = float(coverage_rows[0]["mc_lower_99"])
    mc_upper = float(coverage_rows[0]["mc_upper_99"])
    ax_b.axhline(0.95, color="black", linestyle="--", linewidth=1.0, label="Livello nominale 0.95")
    ax_b.axhspan(mc_lower, mc_upper, color="gray", alpha=0.2, label="Intervallo 99% MC")
    for i, v in enumerate(cov_values):
        ax_b.annotate(f"{v:.3f}", xy=(i, v), ha="center", va="bottom", fontsize=9)
    ax_b.set_ylim(0.5, 1.0)
    ax_b.set_ylabel("Copertura empirica")
    ax_b.set_title(
        "B) Copertura al 95% della media\nAR(1), φ = 0.5, n = 380",
        loc="left",
        fontsize=11,
        fontweight="bold",
    )
    ax_b.legend(loc="lower right", fontsize=8)
    ax_b.grid(True, axis="y", linestyle=":", alpha=0.6)

    fig.tight_layout()
    fig.savefig(png_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    run_experiment()
