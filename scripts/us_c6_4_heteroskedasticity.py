"""Script per l'analisi dell'eteroschedasticità dei residui del Modulo 1 (US-C6.4 / Task 39).

Genera il file CSV dei risultati results/us_c6_4_heteroskedasticity.csv e la figura
a tre pannelli thesis/figures/us_c6_4_heteroskedasticity.png.
Nessun output su stdout o stderr conforme alla convenzione di progetto per gli script.
"""

import csv
from pathlib import Path
from typing import Sequence

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from shk.data.split import load_by_role, read_split_config
from shk.kelly.floor import SEED_C6
from shk.model.elo_fit import ELO_FITS, derive_fit_schedule
from shk.model.residual_heteroskedasticity import (
    HETEROSKEDASTICITY_CSV_COLUMNS,
    STATISTIC_DFS,
    STATISTICS,
    evaluate_residual_heteroskedasticity,
)
from shk.model.residuals import compute_model_residuals


def save_csv(
    records: Sequence[dict[str, str | float | int | bool]],
    csv_path: Path,
) -> None:
    """Salva i 105 record nel file CSV con le colonne prescritte."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(HETEROSKEDASTICITY_CSV_COLUMNS))
        writer.writeheader()
        writer.writerows(records)


def generate_figure(
    records: Sequence[dict[str, str | float | int | bool]],
    output_path: Path,
) -> None:
    """Genera la figura a tre pannelli in lingua italiana per la tesi."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    scenario_rows = [r for r in records if r["row_type"] == "scenario"]
    summary_rows = [r for r in records if r["row_type"] == "summary"]
    verif_rows = [r for r in records if r["row_type"] == "verification"]

    # Estrazione stagioni ordinate
    seasons = []
    roles = {}
    for r in scenario_rows:
        s = str(r["season"])
        if s not in seasons:
            seasons.append(s)
            roles[s] = str(r["role"])

    fig, axes = plt.subplots(1, 3, figsize=(19, 5.5))

    # --------------------------------------------------------------------------
    # Pannello A: Statistiche LM osservate per stagione
    # --------------------------------------------------------------------------
    ax_a = axes[0]
    x_indices = np.arange(len(seasons))

    stat_data: dict[str, list[float]] = {"white": [], "bp_joint": [], "bp_time": []}
    nom_thresh: dict[str, float] = {}

    for s in seasons:
        for stat_name in ("white", "bp_joint", "bp_time"):
            r_match = next(
                r for r in scenario_rows if r["season"] == s and r["statistic"] == stat_name
            )
            stat_data[stat_name].append(float(r_match["lm_stat"]))
            nom_thresh[stat_name] = float(r_match["threshold_nom"])

    ax_a.plot(
        x_indices,
        stat_data["white"],
        "^-",
        color="#2ca02c",
        lw=1.8,
        ms=6,
        label=f"White (df={STATISTIC_DFS['white']})",
    )
    ax_a.plot(
        x_indices,
        stat_data["bp_joint"],
        "o-",
        color="#1f77b4",
        lw=1.8,
        ms=6,
        label=f"BP joint (df={STATISTIC_DFS['bp_joint']})",
    )
    ax_a.plot(
        x_indices,
        stat_data["bp_time"],
        "s-",
        color="#ff7f0e",
        lw=1.8,
        ms=6,
        label=f"BP tempo (df={STATISTIC_DFS['bp_time']})",
    )

    # Linee orizzontali soglie nominali
    ax_a.axhline(
        nom_thresh["white"],
        color="#2ca02c",
        linestyle="--",
        lw=1.2,
        alpha=0.8,
        label=f"Soglia nom. White ({nom_thresh['white']:.2f})",
    )
    ax_a.axhline(
        nom_thresh["bp_joint"],
        color="#1f77b4",
        linestyle="--",
        lw=1.2,
        alpha=0.8,
        label=f"Soglia nom. BP joint ({nom_thresh['bp_joint']:.2f})",
    )
    ax_a.axhline(
        nom_thresh["bp_time"],
        color="#ff7f0e",
        linestyle="--",
        lw=1.2,
        alpha=0.8,
        label=f"Soglia nom. BP tempo ({nom_thresh['bp_time']:.2f})",
    )

    # Evidenziazione stagioni di training con sfondo ombreggiato
    for idx, s in enumerate(seasons):
        if roles[s] == "training":
            ax_a.axvspan(idx - 0.4, idx + 0.4, color="#d3d3d3", alpha=0.35, zorder=0)

    ax_a.set_xticks(x_indices)
    ax_a.set_xticklabels(seasons, rotation=60, ha="right", fontsize=8.5)
    ax_a.set_title("(A) Statistiche LM osservate per stagione (22 stagioni)", fontsize=11, fontweight="bold")
    ax_a.set_xlabel("Stagione (grigio = training congelato)", fontsize=10)
    ax_a.set_ylabel("Statistica LM (n · R²)", fontsize=10)
    ax_a.grid(True, linestyle=":", alpha=0.5)
    ax_a.legend(loc="upper left", fontsize=7.5, framealpha=0.9)

    # --------------------------------------------------------------------------
    # Pannello B: Soglie critiche nominali vs calibrate per fit e blocco L
    # --------------------------------------------------------------------------
    ax_b = axes[1]
    fits = sorted(list({str(r["fit_through"]) for r in verif_rows}))
    bar_width = 0.22
    group_indices = np.arange(len(fits))

    # Mostriamo White e BP joint a confronto
    # Calibrazione per White: L=7, L=20, L=40 vs nominale
    colors_l = {"7": "#aec7e8", "20": "#1f77b4", "40": "#08519c"}

    for l_idx, blk in enumerate((7, 20, 40)):
        vals_white = []
        for f in fits:
            r_v = next(
                r
                for r in verif_rows
                if r["fit_through"] == f and int(r["block_length"]) == blk and r["statistic"] == "white"
            )
            vals_white.append(float(r_v["calibrated_threshold"]))

        pos = group_indices + (l_idx - 1) * bar_width
        ax_b.bar(
            pos,
            vals_white,
            width=bar_width,
            color=colors_l[str(blk)],
            edgecolor="black",
            lw=0.8,
            label=f"White calibrata L={blk}",
        )

    ax_b.axhline(
        nom_thresh["white"],
        color="#d62728",
        linestyle="--",
        lw=1.5,
        label=f"Soglia nominale White ({nom_thresh['white']:.2f})",
    )

    ax_b.set_xticks(group_indices)
    ax_b.set_xticklabels([f"Fit {f}" for f in fits], fontsize=10)
    ax_b.set_title("(B) Soglie critiche White: asintotica vs bootstrap", fontsize=11, fontweight="bold")
    ax_b.set_xlabel("Fit congelato di riferimento", fontsize=10)
    ax_b.set_ylabel("Soglia critica al 95% (valore LM)", fontsize=10)
    ax_b.grid(True, axis="y", linestyle=":", alpha=0.5)
    ax_b.legend(loc="upper left", fontsize=8.5, framealpha=0.9)

    # --------------------------------------------------------------------------
    # Pannello C: Conteggio rigetti nelle 19 stagioni di validazione
    # --------------------------------------------------------------------------
    ax_c = axes[2]
    stat_labels = ["BP tempo (df=1)", "BP joint (df=2)", "White (df=5)"]
    stat_keys = ["bp_time", "bp_joint", "white"]
    methods = ["nominal", "bootstrap_L7", "bootstrap_L20", "bootstrap_L40"]
    method_labels = ["Nominale χ²", "Bootstrap L=7", "Bootstrap L=20", "Bootstrap L=40"]
    method_colors = ["#e377c2", "#aec7e8", "#1f77b4", "#08519c"]

    c_width = 0.18
    s_indices = np.arange(len(stat_keys))

    for m_idx, (m_key, m_lbl, m_col) in enumerate(zip(methods, method_labels, method_colors)):
        counts = []
        for st_key in stat_keys:
            r_s = next(
                r for r in summary_rows if r["statistic"] == st_key and r["method"] == m_key
            )
            counts.append(int(r_s["n_validation_rejections"]))

        pos = s_indices + (m_idx - 1.5) * c_width
        bars = ax_c.bar(
            pos,
            counts,
            width=c_width,
            color=m_col,
            edgecolor="black",
            lw=0.8,
            label=m_lbl,
        )
        # Valore sopra la barra
        for bar, count in zip(bars, counts):
            ax_c.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.2,
                str(count),
                ha="center",
                va="bottom",
                fontsize=8.5,
                fontweight="bold",
            )

    # Linee di riferimento: atteso 19 * 0.05 = 0.95 e soglia binomiale al 99% (k = 5)
    ax_c.axhline(
        0.95,
        color="#7f7f7f",
        linestyle="--",
        lw=1.3,
        label="Atteso sotto H₀ (19 · 0.05 = 0.95)",
    )
    ax_c.axhline(
        5.0,
        color="#d62728",
        linestyle=":",
        lw=1.5,
        label="Soglia binomiale 99% (k = 5, p < 0.01)",
    )

    ax_c.set_xticks(s_indices)
    ax_c.set_xticklabels(stat_labels, fontsize=10)
    ax_c.set_ylim(0, max(6, max(int(r["n_validation_rejections"]) for r in summary_rows) + 2))
    ax_c.set_title("(C) Rigetti nelle 19 stagioni di validazione", fontsize=11, fontweight="bold")
    ax_c.set_xlabel("Statistica di eteroschedasticità", fontsize=10)
    ax_c.set_ylabel("Stagioni con rigetto (su 19)", fontsize=10)
    ax_c.grid(True, axis="y", linestyle=":", alpha=0.5)
    ax_c.legend(loc="upper right", fontsize=8, framealpha=0.9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close(fig)


def main() -> None:
    """Funzione principale: carica dati, calcola eteroschedasticità, scrive CSV e PNG."""
    repo_root = Path(__file__).resolve().parents[1]
    results_dir = repo_root / "results"
    figures_dir = repo_root / "thesis" / "figures"
    results_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    csv_path = results_dir / "us_c6_4_heteroskedasticity.csv"
    png_path = figures_dir / "us_c6_4_heteroskedasticity.png"

    # Caricamento storico, training e validazione
    cfg = read_split_config()
    df_hist = load_by_role("history")
    df_train = load_by_role("training")
    df_val = load_by_role("validation")

    df = pd.concat([df_hist, df_train, df_val], ignore_index=True)
    df = df.sort_values("Date", kind="stable").reset_index(drop=True)

    schedule = derive_fit_schedule(cfg)
    df_residuals = compute_model_residuals(df, schedule, ELO_FITS)

    records = evaluate_residual_heteroskedasticity(
        df_residuals=df_residuals,
        schedule=schedule,
        seed=SEED_C6,
    )

    save_csv(records, csv_path)
    generate_figure(records, png_path)


if __name__ == "__main__":
    main()
