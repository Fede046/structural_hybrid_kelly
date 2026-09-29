"""Script per il calcolo di g_hat del Modulo 1 contro il mercato de-viggato (US-C4.2).

Genera il file CSV dei risultati (results/us_c4_2_g_hat.csv) e la figura
dell'edge cumulativo g_hat (thesis/figures/us_c4_2_g_hat.png).
"""

import csv
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from shk.data.split import load_by_role, read_split_config
from shk.model.elo_fit import ELO_FITS, derive_fit_schedule
from shk.model.scoring import (
    CSV_COLUMNS,
    DEVIG_METHODS,
    SERIES_NAMES,
    align_predictions_with_odds,
    compute_cumulative_g_hat,
    compute_g_hat_terms,
    compute_mean_log_loss,
    generate_validation_predictions,
    prepare_series_evaluation,
)


def run_experiment() -> None:
    """Esegue la stima di g_hat, la generazione del CSV e la figura."""
    repo_root = Path(__file__).resolve().parents[1]
    csv_path = repo_root / "results" / "us_c4_2_g_hat.csv"
    png_path = repo_root / "thesis" / "figures" / "us_c4_2_g_hat.png"

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    png_path.parent.mkdir(parents=True, exist_ok=True)

    cfg = read_split_config()
    schedule = derive_fit_schedule(cfg)

    df_hist = load_by_role("history")
    df_train = load_by_role("training")
    df_val = load_by_role("validation")

    df_full = pd.concat([df_hist, df_train, df_val], ignore_index=True)
    df_full = df_full.sort_values("Date", kind="stable").reset_index(drop=True)

    # 1. Previsioni del modello e allineamento semantico
    df_preds = generate_validation_predictions(df_full, ELO_FITS, schedule)
    df_aligned = align_predictions_with_odds(df_preds, df_full)

    # 2. Preparazione delle due serie di valutazione
    eval_b365 = prepare_series_evaluation(df_aligned, "b365_prematch", schedule)
    eval_psc = prepare_series_evaluation(df_aligned, "pinnacle_closing", schedule)

    eval_map = {
        "b365_prematch": eval_b365,
        "pinnacle_closing": eval_psc,
    }

    csv_rows: list[dict[str, Any]] = []
    plot_data: dict[str, dict[str, np.ndarray]] = {
        "b365_prematch": {},
        "pinnacle_closing": {},
    }

    # 3. Calcolo metriche e assemblaggio righe CSV nell'ordine specificato
    for series_name in SERIES_NAMES:
        eval_data = eval_map[series_name]
        ll_model = compute_mean_log_loss(eval_data.p_model, eval_data.outcomes)

        methods_q = {
            "proportional": eval_data.q_proportional,
            "additive": eval_data.q_additive,
            "power": eval_data.q_power,
        }

        for method in DEVIG_METHODS:
            q_market = methods_q[method]
            ll_market = compute_mean_log_loss(q_market, eval_data.outcomes)
            terms = compute_g_hat_terms(eval_data.p_model, q_market, eval_data.outcomes)
            g_hat_val = float(np.mean(terms))
            g_hat_cum = compute_cumulative_g_hat(terms)

            plot_data[series_name][method] = g_hat_cum

            # Riga di summary per la coppia (series, method)
            csv_rows.append({
                "level": "summary",
                "series": series_name,
                "method": method,
                "t": "",
                "season": "",
                "date": "",
                "matches_used": eval_data.matches_used,
                "matches_excluded": eval_data.matches_excluded,
                "log_loss_model": ll_model,
                "log_loss_market": ll_market,
                "g_hat": g_hat_val,
            })

            # Righe cumulative per partita
            for t_idx in range(len(terms)):
                row_match = eval_data.df_used.iloc[t_idx]
                date_str = pd.Timestamp(row_match["Date"]).strftime("%Y-%m-%d")
                csv_rows.append({
                    "level": "cumulative",
                    "series": series_name,
                    "method": method,
                    "t": t_idx + 1,
                    "season": str(row_match["season"]),
                    "date": date_str,
                    "matches_used": "",
                    "matches_excluded": "",
                    "log_loss_model": "",
                    "log_loss_market": "",
                    "g_hat": float(g_hat_cum[t_idx]),
                })

    # Scrittura del file CSV
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for r in csv_rows:
            writer.writerow(r)

    # 4. Generazione della figura a due pannelli
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.2), sharey=False)

    method_labels = {
        "proportional": "Proporzionale",
        "additive": "Additivo",
        "power": "Power",
    }
    method_colors = {
        "proportional": "#1f77b4",
        "additive": "#2ca02c",
        "power": "#d62728",
    }

    # Pannello 1: Bet365 pre-partita
    ax1.axhline(0.0, color="black", linestyle="--", linewidth=1.0, alpha=0.7, label="ĝ = 0")
    for method in DEVIG_METHODS:
        cum_series = plot_data["b365_prematch"][method]
        t_steps = np.arange(1, len(cum_series) + 1)
        ax1.plot(
            t_steps,
            cum_series,
            label=method_labels[method],
            color=method_colors[method],
            linewidth=1.6,
        )
    ax1.set_title("Serie Bet365 pre-partita (19 stagioni di validazione)", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Numero di partite t (ordine cronologico)", fontsize=10)
    ax1.set_ylabel("Edge empirico cumulativo ĝ_t", fontsize=10)
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="best", fontsize=9)

    # Pannello 2: Pinnacle chiusura
    ax2.axhline(0.0, color="black", linestyle="--", linewidth=1.0, alpha=0.7, label="ĝ = 0")
    for method in DEVIG_METHODS:
        cum_series = plot_data["pinnacle_closing"][method]
        t_steps = np.arange(1, len(cum_series) + 1)
        ax2.plot(
            t_steps,
            cum_series,
            label=method_labels[method],
            color=method_colors[method],
            linewidth=1.6,
        )
    ax2.set_title("Serie Pinnacle chiusura (10 stagioni di validazione)", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Numero di partite t (ordine cronologico)", fontsize=10)
    ax2.set_ylabel("Edge empirico cumulativo ĝ_t", fontsize=10)
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="best", fontsize=9)

    fig.tight_layout()
    fig.savefig(png_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    run_experiment()
