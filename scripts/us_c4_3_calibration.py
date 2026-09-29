"""Script per la ricalibrazione, analisi di affidabilità e Brier score (US-C4.3).

Genera il file CSV dei risultati (results/us_c4_3_calibration.csv) e la figura
dei diagrammi di calibrazione (thesis/figures/us_c4_3_calibration.png).
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
from shk.model.recalibration import (
    CALIBRATION_CSV_COLUMNS,
    brier_score,
    compute_reliability_table,
    fit_all_calibration_maps,
    recalibrate_series_predictions,
)
from shk.model.scoring import (
    DEVIG_METHODS,
    SERIES_NAMES,
    align_predictions_with_odds,
    compute_g_hat,
    compute_mean_log_loss,
    generate_validation_predictions,
    prepare_series_evaluation,
)


def run_experiment() -> None:
    """Esegue la stima delle mappe di calibrazione, calcola le metriche e scrive CSV e figura."""
    repo_root = Path(__file__).resolve().parents[1]
    csv_path = repo_root / "results" / "us_c4_3_calibration.csv"
    png_path = repo_root / "thesis" / "figures" / "us_c4_3_calibration.png"

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    png_path.parent.mkdir(parents=True, exist_ok=True)

    cfg = read_split_config()
    schedule = derive_fit_schedule(cfg)

    df_hist = load_by_role("history")
    df_train = load_by_role("training")
    df_val = load_by_role("validation")

    df_full = pd.concat([df_hist, df_train, df_val], ignore_index=True)
    df_full = df_full.sort_values("Date", kind="stable").reset_index(drop=True)

    # 1. Stima delle mappe di ricalibrazione one-vs-rest sui dati di training per ciascun fit
    fit_maps = fit_all_calibration_maps(df_full, ELO_FITS, schedule)

    # 2. Ottenimento di SeriesEvaluationData per le due serie come in T23
    df_preds = generate_validation_predictions(df_full, ELO_FITS, schedule)
    df_aligned = align_predictions_with_odds(df_preds, df_full)

    eval_b365 = prepare_series_evaluation(df_aligned, "b365_prematch", schedule)
    eval_psc = prepare_series_evaluation(df_aligned, "pinnacle_closing", schedule)

    eval_map = {
        "b365_prematch": eval_b365,
        "pinnacle_closing": eval_psc,
    }

    # 3. Ricalibrazione per ciascuna serie
    recalibrated_probs: dict[str, dict[str, np.ndarray]] = {
        "b365_prematch": {"raw": eval_b365.p_model},
        "pinnacle_closing": {"raw": eval_psc.p_model},
    }

    for s_name, ev_data in eval_map.items():
        p_iso, _, _ = recalibrate_series_predictions(ev_data, fit_maps, "isotonic", schedule)
        p_platt, _, _ = recalibrate_series_predictions(ev_data, fit_maps, "platt", schedule)
        recalibrated_probs[s_name]["isotonic"] = p_iso
        recalibrated_probs[s_name]["platt"] = p_platt

    csv_rows: list[dict[str, Any]] = []

    # 4. Righe di reliability sulla serie b365_prematch
    # Ordine prescritto: version (raw, isotonic, platt) -> outcome (all, H, D, A) -> bin crescente
    rel_versions = ("raw", "isotonic", "platt")
    rel_outcomes = ("all", "H", "D", "A")

    reliability_tables: dict[tuple[str, str], list[dict[str, Any]]] = {}

    for ver in rel_versions:
        p_eval = recalibrated_probs["b365_prematch"][ver]
        for out in rel_outcomes:
            table = compute_reliability_table(p_eval, eval_b365.outcomes, outcome_filter=out, n_bins=10)
            reliability_tables[(ver, out)] = table

            for b_dict in table:
                csv_rows.append({
                    "level": "reliability",
                    "version": ver,
                    "series": "b365_prematch",
                    "method": "",
                    "outcome": out,
                    "bin_lower": b_dict["bin_lower"],
                    "bin_upper": b_dict["bin_upper"],
                    "count": b_dict["count"],
                    "mean_predicted": "" if b_dict["mean_predicted"] is None else b_dict["mean_predicted"],
                    "observed_frequency": "" if b_dict["observed_frequency"] is None else b_dict["observed_frequency"],
                    "gap": "" if b_dict["gap"] is None else b_dict["gap"],
                    "z": "" if b_dict["z"] is None else b_dict["z"],
                    "matches_used": eval_b365.matches_used,
                    "log_loss": "",
                    "brier": "",
                    "g_hat": "",
                })

    # 5. Righe score del modello
    # Ordine: version (raw, isotonic, platt) -> series (b365_prematch, pinnacle_closing) -> method (proportional, additive, power)
    for ver in rel_versions:
        for s_name in SERIES_NAMES:
            ev_data = eval_map[s_name]
            p_curr = recalibrated_probs[s_name][ver]
            ll_mod = compute_mean_log_loss(p_curr, ev_data.outcomes)
            bs_mod = brier_score(p_curr, ev_data.outcomes)

            methods_q = {
                "proportional": ev_data.q_proportional,
                "additive": ev_data.q_additive,
                "power": ev_data.q_power,
            }

            for m in DEVIG_METHODS:
                q_mkt = methods_q[m]
                g_hat_val = compute_g_hat(p_curr, q_mkt, ev_data.outcomes)

                csv_rows.append({
                    "level": "score",
                    "version": ver,
                    "series": s_name,
                    "method": m,
                    "outcome": "",
                    "bin_lower": "",
                    "bin_upper": "",
                    "count": "",
                    "mean_predicted": "",
                    "observed_frequency": "",
                    "gap": "",
                    "z": "",
                    "matches_used": ev_data.matches_used,
                    "log_loss": ll_mod,
                    "brier": bs_mod,
                    "g_hat": g_hat_val,
                })

    # 6. Righe score del mercato
    # Ordine: series -> method
    for s_name in SERIES_NAMES:
        ev_data = eval_map[s_name]
        methods_q = {
            "proportional": ev_data.q_proportional,
            "additive": ev_data.q_additive,
            "power": ev_data.q_power,
        }

        for m in DEVIG_METHODS:
            q_mkt = methods_q[m]
            ll_mkt = compute_mean_log_loss(q_mkt, ev_data.outcomes)
            bs_mkt = brier_score(q_mkt, ev_data.outcomes)

            csv_rows.append({
                "level": "score",
                "version": "market",
                "series": s_name,
                "method": m,
                "outcome": "",
                "bin_lower": "",
                "bin_upper": "",
                "count": "",
                "mean_predicted": "",
                "observed_frequency": "",
                "gap": "",
                "z": "",
                "matches_used": ev_data.matches_used,
                "log_loss": ll_mkt,
                "brier": bs_mkt,
                "g_hat": "",
            })

    # Scrittura del file CSV
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CALIBRATION_CSV_COLUMNS)
        writer.writeheader()
        for r in csv_rows:
            writer.writerow(r)

    # 7. Generazione della figura a due pannelli
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.5))

    # Pannello 1: Aggregato con le tre versioni e diagonale ideale
    ax1.plot([0.0, 1.0], [0.0, 1.0], color="gray", linestyle="--", linewidth=1.2, label="Calibrazione ideale")

    ver_labels = {
        "raw": "Modello raw",
        "isotonic": "Ricalibrato isotonica",
        "platt": "Ricalibrato Platt",
    }
    ver_colors = {
        "raw": "#d62728",
        "isotonic": "#1f77b4",
        "platt": "#2ca02c",
    }
    ver_markers = {
        "raw": "o",
        "isotonic": "s",
        "platt": "^",
    }

    for ver in rel_versions:
        tbl = reliability_tables[(ver, "all")]
        pts_x = [b["mean_predicted"] for b in tbl if b["count"] > 0 and b["mean_predicted"] is not None]
        pts_y = [b["observed_frequency"] for b in tbl if b["count"] > 0 and b["observed_frequency"] is not None]
        ax1.plot(
            pts_x,
            pts_y,
            label=ver_labels[ver],
            color=ver_colors[ver],
            marker=ver_markers[ver],
            linewidth=1.6,
            markersize=5.5,
        )

    ax1.set_title("Diagramma di affidabilità aggregato (Bet365)", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Probabilità prevista media p̄", fontsize=10)
    ax1.set_ylabel("Frequenza osservata ȳ", fontsize=10)
    ax1.set_xlim(-0.02, 1.02)
    ax1.set_ylim(-0.02, 1.02)
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="upper left", fontsize=9)

    # Pannello 2: Per esito con la versione grezza (raw)
    ax2.plot([0.0, 1.0], [0.0, 1.0], color="gray", linestyle="--", linewidth=1.2, label="Calibrazione ideale")

    out_labels = {
        "H": "Casa (H)",
        "D": "Pareggio (D)",
        "A": "Trasferta (A)",
    }
    out_colors = {
        "H": "#1f77b4",
        "D": "#ff7f0e",
        "A": "#9467bd",
    }
    out_markers = {
        "H": "o",
        "D": "s",
        "A": "D",
    }

    for out in ("H", "D", "A"):
        tbl = reliability_tables[("raw", out)]
        pts_x = [b["mean_predicted"] for b in tbl if b["count"] > 0 and b["mean_predicted"] is not None]
        pts_y = [b["observed_frequency"] for b in tbl if b["count"] > 0 and b["observed_frequency"] is not None]
        ax2.plot(
            pts_x,
            pts_y,
            label=out_labels[out],
            color=out_colors[out],
            marker=out_markers[out],
            linewidth=1.6,
            markersize=5.5,
        )

    ax2.set_title("Diagramma di affidabilità per esito — Modello raw", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Probabilità prevista media p̄", fontsize=10)
    ax2.set_ylabel("Frequenza osservata ȳ", fontsize=10)
    ax2.set_xlim(-0.02, 1.02)
    ax2.set_ylim(-0.02, 1.02)
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="upper left", fontsize=9)

    fig.tight_layout()
    fig.savefig(png_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    run_experiment()
