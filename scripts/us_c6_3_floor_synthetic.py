"""Script per la simulazione del floor su calendario sintetico (US-C6.3, Task 36).

Questo script esegue gli esperimenti sintetici A (confronto con/senza floor), B (sweep
del rapporto B0/F) e C (tempi di rovina e limite analitico), salva i risultati nel file
results/us_c6_3_floor_synthetic.csv e genera la figura a tre pannelli
thesis/figures/us_c6_3_floor_synthetic.png.
"""

import csv
from pathlib import Path
from typing import Sequence

import matplotlib.pyplot as plt
import numpy as np

from shk.kelly.floor import (
    EXP_A_HORIZONS_50F,
    EXP_A_HORIZONS_1000F,
    EXP_B_HORIZONS,
    FLOOR_SYNTHETIC_CSV_COLUMNS,
    NOTE_EXP_A_RUIN_RATES_50F,
    NOTE_EXP_A_RUIN_RATES_1000F,
    ExperimentARunResult,
    ExperimentBResult,
    ExperimentCConfigResult,
    evaluate_all_synthetic_experiments,
)


def save_csv(
    records: Sequence[dict[str, str | float | int | bool]],
    csv_path: Path,
) -> None:
    """Salva i record generati nel file CSV con le colonne prescritte.

    Parametri
    ---------
    records : Sequence[dict]
        Lista dei record dizionario conformi allo schema.
    csv_path : Path
        Percorso del file CSV di output.
    """
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(FLOOR_SYNTHETIC_CSV_COLUMNS))
        writer.writeheader()
        writer.writerows(records)


def generate_figure(
    exp_a_res: tuple[ExperimentARunResult, ExperimentARunResult],
    exp_b_res: ExperimentBResult,
    exp_c_res: Sequence[ExperimentCConfigResult],
    output_path: Path,
) -> None:
    """Genera la figura a tre pannelli in lingua italiana per la tesi.

    Pannelli:
    (A) Rovina per orizzonte temporale, con e senza floor, per partenze 50F e 1000F.
    (B) Rovina in funzione di B0/F (scala logaritmica) a T = 150 e T = 1000.
    (C) Tempo medio di rovina simulato contro limite analitico, col fattore di accelerazione.

    Parametri
    ---------
    exp_a_res : tuple[ExperimentARunResult, ExperimentARunResult]
        Risultati dell'Esperimento A (1000F, 50F).
    exp_b_res : ExperimentBResult
        Risultati dello sweep dell'Esperimento B.
    exp_c_res : Sequence[ExperimentCConfigResult]
        Risultati delle tre configurazioni dell'Esperimento C.
    output_path : Path
        Percorso in cui salvare l'immagine PNG.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))

    # --------------------------------------------------------------------------
    # Pannello A: Rovina per orizzonte (Esperimento A)
    # --------------------------------------------------------------------------
    ax_a = axes[0]
    res_1000f, res_50f = exp_a_res

    # Partenza 50F
    h_50f = sorted(list(res_50f.horizons))
    r_50f_floor = [float(np.mean((res_50f.run_floor.wealth[:, h] < res_50f.min_stake) | (res_50f.run_floor.wealth[:, h] == 0.0))) for h in h_50f]
    r_50f_nofloor = [float(np.mean(res_50f.run_nofloor.wealth[:, h] == 0.0)) for h in h_50f]
    note_50f = [NOTE_EXP_A_RUIN_RATES_50F[h] for h in h_50f]

    # Partenza 1000F
    h_1000f = sorted(list(res_1000f.horizons))
    r_1000f_floor = [float(np.mean((res_1000f.run_floor.wealth[:, h] < res_1000f.min_stake) | (res_1000f.run_floor.wealth[:, h] == 0.0))) for h in h_1000f]
    r_1000f_nofloor = [float(np.mean(res_1000f.run_nofloor.wealth[:, h] == 0.0)) for h in h_1000f]

    ax_a.plot(h_50f, [r * 100 for r in r_50f_floor], "o-", color="#d62728", lw=2, label="Partenza 50F (con floor)")
    ax_a.plot(h_50f, [r * 100 for r in r_50f_nofloor], "s--", color="#1f77b4", lw=1.5, label="Partenza 50F (senza floor)")
    ax_a.plot(h_50f, [r * 100 for r in note_50f], "^:", color="#ff7f0e", lw=1.5, ms=8, label="Partenza 50F (Nota 2.9)")

    ax_a.plot(h_1000f, [r * 100 for r in r_1000f_floor], "D-", color="#2ca02c", lw=2, label="Partenza 1000F (con floor)")
    ax_a.plot(h_1000f, [r * 100 for r in r_1000f_nofloor], "x--", color="#9467bd", lw=1.5, label="Partenza 1000F (senza floor)")

    ax_a.set_title("(A) Tasso di rovina per orizzonte temporale", fontsize=12, fontweight="bold")
    ax_a.set_xlabel("Orizzonte temporale T (date)", fontsize=11)
    ax_a.set_ylabel("Tasso di rovina (%)", fontsize=11)
    ax_a.grid(True, linestyle=":", alpha=0.6)
    ax_a.legend(loc="upper left", fontsize=8.5)

    # --------------------------------------------------------------------------
    # Pannello B: Rovina in funzione di B0/F (Esperimento B)
    # --------------------------------------------------------------------------
    ax_b = axes[1]
    sorted_ratios = sorted(exp_b_res.ratios)
    r_150 = [exp_b_res.ruin_rates_150[r] * 100 for r in sorted_ratios]
    r_1000 = [exp_b_res.ruin_rates_1000[r] * 100 for r in sorted_ratios]

    ax_b.plot(sorted_ratios, r_150, "o-", color="#1f77b4", lw=2, label="T = 150 date")
    ax_b.plot(sorted_ratios, r_1000, "s-", color="#d62728", lw=2, label="T = 1000 date")

    # Linee verticali per £1 e £0.01 su bankroll £220
    ax_b.axvline(220.0, color="#7f7f7f", linestyle="--", lw=1.5, label="B0/F = 220 (£1)")
    ax_b.axvline(22000.0, color="#bcbd22", linestyle="--", lw=1.5, label="B0/F = 22 000 (£0.01)")

    ax_b.set_xscale("log")
    ax_b.set_title("(B) Rovina al variare del rapporto B0 / F", fontsize=12, fontweight="bold")
    ax_b.set_xlabel("Rapporto iniziale B0 / F (scala logaritmica)", fontsize=11)
    ax_b.set_ylabel("Tasso di rovina (%)", fontsize=11)
    ax_b.grid(True, which="both", linestyle=":", alpha=0.6)
    ax_b.legend(loc="upper right", fontsize=9)

    # --------------------------------------------------------------------------
    # Pannello C: Tempo medio di rovina e limite teorico (Esperimento C)
    # --------------------------------------------------------------------------
    ax_c = axes[2]
    cfg_labels = [
        f"Conf. {c.config.config_id.upper()}\n(EV={c.config.ev_true:+.2f}, λ={c.config.lam:.2f})"
        for c in exp_c_res
    ]
    x_indices = np.arange(len(cfg_labels))
    bar_width = 0.35

    bounds = [c.bound for c in exp_c_res]
    means = [c.mean_ruin_time for c in exp_c_res]

    rects1 = ax_c.bar(x_indices - bar_width / 2, bounds, bar_width, label="Limite teorico (ln(r)/|μ|)", color="#aec7e8")
    rects2 = ax_c.bar(x_indices + bar_width / 2, means, bar_width, label="Tempo medio simulato", color="#1f77b4")

    ax_c.set_yscale("log")
    ax_c.set_title("(C) Tempi di rovina e fattore di accelerazione", fontsize=12, fontweight="bold")
    ax_c.set_xticks(x_indices)
    ax_c.set_xticklabels(cfg_labels, fontsize=10)
    ax_c.set_ylabel("Numero di date (scala logaritmica)", fontsize=11)
    ax_c.grid(True, which="both", axis="y", linestyle=":", alpha=0.6)
    ax_c.legend(loc="upper right", fontsize=9)

    # Annotazione del fattore di accelerazione sopra le barre
    for idx, c in enumerate(exp_c_res):
        accel_text = f"Acc: {c.acceleration_factor:.1f}×\n(nota: {c.config.note_acceleration:.1f}×)"
        y_pos = max(c.bound, c.mean_ruin_time) * 1.3
        ax_c.text(idx, y_pos, accel_text, ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#333333")

    # Spazio extra in alto per le etichette
    y_min, y_max = ax_c.get_ylim()
    ax_c.set_ylim(y_min, y_max * 3.5)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def run_experiment() -> None:
    """Esegue tutti gli esperimenti e genera CSV e figura PNG."""
    project_root = Path(__file__).resolve().parents[1]
    csv_path = project_root / "results" / "us_c6_3_floor_synthetic.csv"
    png_path = project_root / "thesis" / "figures" / "us_c6_3_floor_synthetic.png"

    records, exp_a_res, exp_b_res, exp_c_res = evaluate_all_synthetic_experiments()
    save_csv(records, csv_path)
    generate_figure(exp_a_res, exp_b_res, exp_c_res, png_path)


if __name__ == "__main__":
    run_experiment()
