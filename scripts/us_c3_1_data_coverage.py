"""Script di esperimento per l'audit di copertura dati (US-C3.1)."""

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

from shk.data.coverage import (
    COVERAGE_CSV_COLUMNS,
    GROUP_TYPE_ORDER,
    compute_coverage,
)
from shk.data.loading import load_all_seasons


def run_experiment() -> None:
    """Esegue l'audit di copertura su tutte le stagioni e genera CSV e figura."""
    repo_root = Path(__file__).resolve().parents[1]
    csv_path = repo_root / "results" / "us_c3_1_data_coverage.csv"
    png_path = repo_root / "thesis" / "figures" / "us_c3_1_data_coverage.png"

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    png_path.parent.mkdir(parents=True, exist_ok=True)

    df = load_all_seasons()
    cov_df = compute_coverage(df)

    # Scrittura del CSV in formato lungo
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COVERAGE_CSV_COLUMNS)
        writer.writeheader()
        for row in cov_df.to_dict(orient="records"):
            writer.writerow(row)

    # Generazione della mappa di copertura
    seasons = sorted(df["season"].unique())
    group_tuples = sorted(
        cov_df[["group_type", "group_name"]].drop_duplicates().itertuples(index=False),
        key=lambda x: (GROUP_TYPE_ORDER.get(x.group_type, 99), x.group_name),
    )

    season_idx = {s: i for i, s in enumerate(seasons)}
    group_idx = {g: i for i, g in enumerate(group_tuples)}

    matrix = np.full((len(group_tuples), len(seasons)), np.nan)

    for row in cov_df.itertuples():
        g_key = (row.group_type, row.group_name)
        r = group_idx[g_key]
        c = season_idx[row.season]
        ratio = row.complete_rows / row.total_rows if row.total_rows > 0 else 0.0
        matrix[r, c] = ratio

    cmap = plt.cm.viridis.copy()
    cmap.set_bad(color="#dcdcdc")

    fig, ax = plt.subplots(figsize=(18, 14))
    im = ax.imshow(matrix, cmap=cmap, aspect="auto", vmin=0.0, vmax=1.0)

    ax.set_xticks(range(len(seasons)))
    ax.set_xticklabels(seasons, rotation=90, fontsize=8)

    ax.set_yticks(range(len(group_tuples)))
    row_labels = [f"[{g.group_type}] {g.group_name}" for g in group_tuples]
    ax.set_yticklabels(row_labels, fontsize=7)

    ax.set_title(
        "Audit di copertura per stagione e gruppo di colonne (Premier League 1993-94 – 2023-24)",
        fontsize=12,
        pad=15,
    )
    ax.set_xlabel("Stagione", fontsize=10)
    ax.set_ylabel("Gruppo di colonne", fontsize=10)

    cbar = fig.colorbar(im, ax=ax, fraction=0.02, pad=0.02)
    cbar.set_label("Quota di righe complete (complete_rows / total_rows)", fontsize=9)

    absent_patch = mpatches.Patch(
        facecolor="#dcdcdc", edgecolor="gray", label="Gruppo assente nella stagione"
    )
    ax.legend(
        handles=[absent_patch],
        loc="upper left",
        bbox_to_anchor=(0.0, -0.06),
        ncol=1,
        frameon=True,
        fontsize=8,
    )

    fig.tight_layout()
    fig.savefig(png_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    run_experiment()
