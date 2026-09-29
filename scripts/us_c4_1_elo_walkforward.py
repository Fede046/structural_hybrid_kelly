"""Script di calibrazione e previsione walk-forward Elo (US-C4.1).

Genera il file CSV delle previsioni (results/us_c4_1_elo_walkforward.csv) e la figura
dei profili di log-loss rispetto a K e h (thesis/figures/us_c4_1_elo_walkforward.png).
"""

import csv
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from shk.data.split import load_by_role, read_split_config
from shk.model.elo_fit import (
    ELO_FITS,
    GRID_H,
    GRID_K,
    WALKFORWARD_CSV_COLUMNS,
    compute_training_log_loss,
    derive_fit_schedule,
    parse_season_start_year,
)
from shk.model.elo_predictor import predict_elo_fast


def run_experiment() -> None:
    """Esegue la generazione del CSV delle previsioni e della figura dei profili."""
    repo_root = Path(__file__).resolve().parents[1]
    csv_path = repo_root / "results" / "us_c4_1_elo_walkforward.csv"
    png_path = repo_root / "thesis" / "figures" / "us_c4_1_elo_walkforward.png"

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    png_path.parent.mkdir(parents=True, exist_ok=True)

    cfg = read_split_config()
    df_hist = load_by_role("history")
    df_train = load_by_role("training")
    df_val = load_by_role("validation")

    df = pd.concat([df_hist, df_train, df_val], ignore_index=True)
    df = df.sort_values("Date", kind="stable").reset_index(drop=True)

    schedule = derive_fit_schedule(cfg)
    ordered_fits = sorted(schedule.keys(), key=parse_season_start_year)

    csv_rows: list[dict[str, Any]] = []

    # 1. Generazione righe del CSV per ciascun fit in ordine cronologico
    for fit_through in ordered_fits:
        params = ELO_FITS[fit_through]
        train_seasons = schedule[fit_through]["training"]
        val_seasons = schedule[fit_through]["validation"]
        target_seasons = train_seasons + val_seasons

        preds = predict_elo_fast(
            df,
            target_seasons,
            k=params.k,
            h=params.h,
            nu=params.nu,
        )

        # Due gruppi ordinati: prima training, poi validation
        for role, role_seasons in (("training", train_seasons), ("validation", val_seasons)):
            sub_preds = preds[preds["season"].isin(role_seasons)].copy().reset_index(drop=True)
            sub_gt = df[df["season"].isin(role_seasons)].copy().reset_index(drop=True)

            if len(sub_preds) != len(sub_gt):
                raise ValueError(
                    f"Row count mismatch for fit {fit_through} ({role}): "
                    f"{len(sub_preds)} vs {len(sub_gt)}"
                )

            # Verifica di allineamento chiave per chiave
            for col in ("season", "Date", "HomeTeam", "AwayTeam"):
                if not sub_preds[col].equals(sub_gt[col]):
                    raise ValueError(
                        f"Key mismatch in column '{col}' for fit {fit_through} ({role})"
                    )

            for i in range(len(sub_preds)):
                pred_row = sub_preds.iloc[i]
                gt_row = sub_gt.iloc[i]

                date_str = pd.Timestamp(pred_row["Date"]).strftime("%Y-%m-%d")
                csv_rows.append({
                    "fit_through": fit_through,
                    "role": role,
                    "season": str(pred_row["season"]),
                    "date": date_str,
                    "home_team": str(pred_row["HomeTeam"]),
                    "away_team": str(pred_row["AwayTeam"]),
                    "ftr": str(gt_row["FTR"]).strip(),
                    "home_promotion": str(pred_row["home_promotion"]),
                    "away_promotion": str(pred_row["away_promotion"]),
                    "rating_home": float(pred_row["rating_home"]),
                    "rating_away": float(pred_row["rating_away"]),
                    "delta": float(pred_row["delta"]),
                    "p_home": float(pred_row["p_home"]),
                    "p_draw": float(pred_row["p_draw"]),
                    "p_away": float(pred_row["p_away"]),
                })

    # Scrittura del CSV
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=WALKFORWARD_CSV_COLUMNS)
        writer.writeheader()
        for r in csv_rows:
            writer.writerow(r)

    # 2. Generazione della figura dei profili di log-loss rispetto a K e h
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    colors = {"2000-01": "#1f77b4", "2010-11": "#2ca02c", "2020-21": "#d62728"}

    for fit_through in ordered_fits:
        params = ELO_FITS[fit_through]
        train_seasons = schedule[fit_through]["training"]
        j_year = parse_season_start_year(fit_through)

        season_years = df["season"].map(parse_season_start_year)
        df_sub = df[season_years <= j_year].copy().reset_index(drop=True)
        df_gt = df_sub[df_sub["season"].isin(train_seasons)].copy().reset_index(drop=True)

        color = colors.get(fit_through, "black")
        label_fit = f"Fit fino al {fit_through}"

        # Profilo vs K (con h e nu ottimi)
        losses_k = []
        for k_val in GRID_K:
            loss_k, _ = compute_training_log_loss(
                df_sub, train_seasons, float(k_val), params.h, params.nu, df_gt
            )
            losses_k.append(loss_k)

        ax1.plot(GRID_K, losses_k, label=label_fit, color=color, linewidth=1.8)
        # Punto di ottimo
        opt_loss, _ = compute_training_log_loss(
            df_sub, train_seasons, params.k, params.h, params.nu, df_gt
        )
        ax1.scatter([params.k], [opt_loss], color=color, s=50, zorder=5)

        # Profilo vs h (con K e nu ottimi)
        losses_h = []
        for h_val in GRID_H:
            loss_h, _ = compute_training_log_loss(
                df_sub, train_seasons, params.k, float(h_val), params.nu, df_gt
            )
            losses_h.append(loss_h)

        ax2.plot(GRID_H, losses_h, label=label_fit, color=color, linewidth=1.8)
        ax2.scatter([params.h], [opt_loss], color=color, s=50, zorder=5)

    ax1.set_title("Profilo della log-loss rispetto a K", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Fattore di aggiornamento K", fontsize=10)
    ax1.set_ylabel("Log-loss media di training", fontsize=10)
    ax1.grid(True, linestyle="--", alpha=0.6)
    ax1.legend(loc="best", fontsize=9)

    ax2.set_title("Profilo della log-loss rispetto a h", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Vantaggio campo h (punti Elo)", fontsize=10)
    ax2.set_ylabel("Log-loss media di training", fontsize=10)
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend(loc="best", fontsize=9)

    fig.suptitle(
        "Profili di verosimiglianza di training per i tre fit Elo (US-C4.1)",
        fontsize=12,
        fontweight="bold",
        y=1.02,
    )
    plt.tight_layout()
    fig.savefig(png_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    run_experiment()
