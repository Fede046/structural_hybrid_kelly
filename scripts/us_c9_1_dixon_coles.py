"""Script T59: Dixon-Coles walk-forward, calibrazione di ξ e σ e confronto di validazione con l'Elo (US-C9.1).

Esecuzione completa: ricalcola la calibrazione sul training e verifica che la scelta coincida
con DC_FITS (altrimenti si ferma), poi previsioni di validazione con DC_FITS, log-loss e ĝ
(cinque metodi, b365_prematch) accanto all'Elo, neopromosse mai viste e controllo
anti-leakage sul campione del fornitore. Scrive results/us_c9_1_dixon_coles.csv e
thesis/figures/us_c9_1_dixon_coles.png. Il test set non si legge.

Opzioni:
- --calibration-only PATH: solo la calibrazione, scritta in PATH (serve a congelare DC_FITS);
- --figure-only: rigenera la figura dal CSV già scritto.
Le combinazioni e i fit girano su WORKERS processi; i risultati non dipendono dal numero di processi.
I tempi si misurano dall'esterno.
"""

import csv
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from shk.model.dixon_coles import DC_FITS, SIGMA_GRID, XI_GRID, t59_sequences
from shk.model.dixon_coles_calibration import (
    DC_CSV_COLUMNS,
    calibration_records,
    comparison_records,
    elo_validation_predictions,
    leakage_record,
    load_frame,
    new_team_records,
    validation_predictions,
)

WORKERS = 5


def write_csv(path: Path, records: list[dict]) -> None:
    """Scrive i record con le colonne di DC_CSV_COLUMNS; stringa vuota per i valori non applicabili (NaN)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(DC_CSV_COLUMNS))
        writer.writeheader()
        writer.writerows([{k: "" if isinstance(v, float) and math.isnan(v) else v for k, v in r.items()}
                          for r in records])


def output_paths() -> tuple[Path, Path]:
    repo_root = Path(__file__).resolve().parents[1]
    return repo_root / "results" / "us_c9_1_dixon_coles.csv", repo_root / "thesis" / "figures" / "us_c9_1_dixon_coles.png"


def run_experiment(calibration_path: Path | None = None) -> None:
    """Calibrazione; se calibration_path è None anche validazione, controlli, CSV e figura."""
    df, schedule = load_frame()
    cal, chosen = calibration_records(df, schedule, workers=WORKERS)
    if calibration_path is not None:
        write_csv(calibration_path, cal)
        return
    frozen = {f: (p.xi, p.sigma) for f, p in DC_FITS.items()}
    if chosen != frozen:
        raise RuntimeError(f"Calibration choice {chosen} differs from DC_FITS {frozen}")
    dc_preds, diag = validation_predictions(df, schedule, workers=WORKERS)
    elo_preds = elo_validation_predictions(df, schedule)
    check, _ = leakage_record(df, schedule, np.random.default_rng(t59_sequences()[1]))
    records = (cal + diag + comparison_records(df, schedule, dc_preds, elo_preds)
               + new_team_records(df, schedule, dc_preds, elo_preds) + [check])
    csv_path, png_path = output_paths()
    write_csv(csv_path, records)
    make_figure(pd.read_csv(csv_path), png_path)


def make_figure(df: pd.DataFrame, png_path: Path) -> None:
    """A) obiettivo di calibrazione ξ × σ per fit; B) log-loss di validazione; C) ĝ proporzionale."""
    png_path.parent.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(15, 10))
    grid = fig.add_gridspec(2, 3)
    cal = df[df["row_type"] == "calibration"]
    fits = sorted(cal["fit"].astype(str).unique())
    sigma_labels = ["∞" if not np.isfinite(s) else f"{s:g}" for s in SIGMA_GRID]
    for j, fit in enumerate(fits):
        ax = fig.add_subplot(grid[0, j])
        c = cal[cal["fit"].astype(str) == fit]
        z = np.array([[float(c[(c["xi"] == xi) & (c["sigma"] == s)]["log_loss"].iloc[0]) for s in SIGMA_GRID]
                      for xi in XI_GRID])
        im = ax.imshow(z, cmap="viridis_r", aspect="auto")
        for a in range(z.shape[0]):
            for b in range(z.shape[1]):
                light = (z[a, b] - z.min()) < 0.5 * (z.max() - z.min())
                ax.text(b, a, f"{z[a, b]:.4f}", ha="center", va="center", fontsize=7,
                        color="black" if light else "white")
        win = c[c["chosen"].astype(str) == "True"].iloc[0]
        a, b = XI_GRID.index(float(win["xi"])), [str(s) for s in SIGMA_GRID].index(str(float(win["sigma"])))
        ax.add_patch(plt.Rectangle((b - 0.5, a - 0.5), 1, 1, fill=False, edgecolor="red", linewidth=2))
        ax.set_xticks(range(len(SIGMA_GRID)))
        ax.set_xticklabels(sigma_labels)
        ax.set_yticks(range(len(XI_GRID)))
        ax.set_yticklabels([f"{x:g}" for x in XI_GRID])
        ax.set_xlabel("σ del prior delle neopromosse")
        ax.set_ylabel("ξ al giorno")
        elo = df[(df["row_type"] == "calibration_elo") & (df["fit"].astype(str) == fit)]["log_loss"].astype(float)
        ax.set_title(f"A) Calibrazione, fit {fit} (Elo {elo.iloc[0]:.4f})", loc="left", fontsize=10,
                     fontweight="bold")
        fig.colorbar(im, ax=ax, fraction=0.046)
    val = df[(df["row_type"] == "validation") & (df["season"] != "pooled")]
    seasons = sorted(val["season"].unique())
    x = np.arange(len(seasons))
    ax_b = fig.add_subplot(grid[1, :2])
    for model, colour in (("elo", "tab:blue"), ("dixon_coles", "tab:orange")):
        v = val[(val["model"] == model) & val["method"].isna()].set_index("season").loc[seasons]
        pooled = df[(df["row_type"] == "validation") & (df["season"] == "pooled") & (df["model"] == model)
                    & df["method"].isna()]["log_loss"].iloc[0]
        ax_b.plot(x, v["log_loss"].astype(float), "o-", color=colour, label=f"{model} (pooled {pooled:.4f})")
    ax_b.set_xticks(x)
    ax_b.set_xticklabels(seasons, rotation=60, fontsize=8)
    ax_b.set_ylabel("Log-loss media")
    ax_b.set_title("B) Log-loss di validazione per stagione", loc="left", fontsize=11, fontweight="bold")
    ax_b.legend(fontsize=8)
    ax_b.grid(True, linestyle=":", alpha=0.6)
    ax_c = fig.add_subplot(grid[1, 2])
    for model, colour in (("elo", "tab:blue"), ("dixon_coles", "tab:orange")):
        g = val[(val["model"] == model) & (val["method"] == "proportional")].set_index("season").loc[seasons]
        ax_c.plot(x, g["g_hat"].astype(float), "o-", color=colour, label=model, markersize=4)
    ax_c.axhline(0.0, color="black", linewidth=0.8)
    ax_c.set_xticks(x)
    ax_c.set_xticklabels(seasons, rotation=60, fontsize=7)
    ax_c.set_ylabel("ĝ (proporzionale, b365_prematch)")
    ax_c.set_title("C) ĝ di validazione per stagione", loc="left", fontsize=11, fontweight="bold")
    ax_c.legend(fontsize=8)
    ax_c.grid(True, linestyle=":", alpha=0.6)
    fig.tight_layout()
    fig.savefig(png_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--figure-only" in args:
        csv_, png_ = output_paths()
        make_figure(pd.read_csv(csv_), png_)
    elif "--calibration-only" in args:
        run_experiment(Path(args[args.index("--calibration-only") + 1]))
    else:
        run_experiment()
