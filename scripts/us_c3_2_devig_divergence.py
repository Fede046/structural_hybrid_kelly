"""Script di esperimento per l'analisi di divergenza fra metodi di de-vigging (US-C3.2)."""

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from shk.data.split import load_by_role, read_split_config
from shk.market.divergence import (
    DIVERGENCE_CSV_COLUMNS,
    ODDS_BIN_LABELS,
    compute_divergence_table,
)


def run_experiment() -> None:
    """Esegue il confronto fra metodi di de-vigging sulle stagioni non di test."""
    repo_root = Path(__file__).resolve().parents[1]
    csv_path = repo_root / "results" / "us_c3_2_devig_divergence.csv"
    png_path = repo_root / "thesis" / "figures" / "us_c3_2_devig_divergence.png"

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    png_path.parent.mkdir(parents=True, exist_ok=True)

    cfg = read_split_config()
    seasons_order = sorted(list(cfg.training) + list(cfg.validation))

    df_train = load_by_role("training")
    df_val = load_by_role("validation")
    df = pd.concat([df_train, df_val], ignore_index=True)

    div_df = compute_divergence_table(df, seasons_order=seasons_order)

    # Scrittura del CSV dei risultati
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=DIVERGENCE_CSV_COLUMNS)
        writer.writeheader()
        for row in div_df.to_dict(orient="records"):
            writer.writerow(row)

    # Estrazione dati per i pannelli della figura
    bin_data = div_df[div_df["level"] == "bin"].copy()
    categories = bin_data["category"].tolist()
    mean_spread_pts = [float(v) for v in bin_data["mean_spread_pts"]]
    mean_rel_spread = [float(v) for v in bin_data["mean_relative_spread"]]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    # Pannello A: Spread medio in punti percentuali
    bars1 = ax1.bar(
        categories,
        mean_spread_pts,
        color="#2b5c8f",
        edgecolor="#1a365d",
        alpha=0.85,
    )
    ax1.set_title(
        "Pannello A: Spread medio fra i metodi di de-vigging",
        fontsize=11,
        pad=10,
    )
    ax1.set_xlabel("Fascia di quota dell'esito", fontsize=10)
    ax1.set_ylabel("Spread medio (punti percentuali)", fontsize=10)
    ax1.grid(axis="y", linestyle="--", alpha=0.5)
    for bar in bars1:
        height = bar.get_height()
        ax1.annotate(
            f"{height:.3f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    # Pannello B: Spread relativo medio
    bars2 = ax2.bar(
        categories,
        mean_rel_spread,
        color="#c05621",
        edgecolor="#7b341e",
        alpha=0.85,
    )
    ax2.set_title(
        "Pannello B: Spread relativo medio ((max q - min q) / q medio)",
        fontsize=11,
        pad=10,
    )
    ax2.set_xlabel("Fascia di quota dell'esito", fontsize=10)
    ax2.set_ylabel("Spread relativo medio", fontsize=10)
    ax2.grid(axis="y", linestyle="--", alpha=0.5)
    for bar in bars2:
        height = bar.get_height()
        ax2.annotate(
            f"{height:.3f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    fig.suptitle(
        "Divergenza fra metodi di de-vigging per fascia di quota (Premier League, non-test)",
        fontsize=12,
        y=1.02,
    )
    fig.tight_layout()
    fig.savefig(png_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    run_experiment()
