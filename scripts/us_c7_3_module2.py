"""Script T47 (US-C7.3, parte 1): Modulo 2 su finestre scorrevoli.

Per ogni data di decisione delle 3 stagioni di training e delle 19 di validazione e per ogni
W in (40, 80, 120, 190): decomposizione di Oaxaca-Blinder fra le due finestre adiacenti di
partite anteriori (shk.model.module2), con intervalli al 95% a fine matchday. Scrive
results/us_c7_3_module2.csv (una riga per data x W), results/us_c7_3_module2_ci.csv e
thesis/figures/us_c7_3_module2.png. La specificazione è quella di T46, ricavata dalle
regole sul training (derive_specification).
Con --module1 dixon_coles usa il Modulo 1 Dixon-Coles e scrive le uscite con il suffisso _dc,
senza toccare quelle Elo (T60), con i seed di T61 (module1_seeds.procedure_seeds).
"""

import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from shk.model.covariate_inspection import MODULE2_WINDOWS, derive_specification
from shk.model.module1 import MODULE1_ELO, module1_from_argv, with_module1_suffix
from shk.model.module1_seeds import procedure_seeds
from shk.model.module2 import MODULE2_CI_COLUMNS, evaluate_module2, module2_record_columns
from shk.model.module2_data import build_module2_frame
from shk.model.residuals import load_model_residuals


def run_experiment(module1: str = MODULE1_ELO) -> None:
    """Calcola il Modulo 2, scrive i due CSV e la figura."""
    repo_root = Path(__file__).resolve().parents[1]
    csv_path = with_module1_suffix(repo_root / "results" / "us_c7_3_module2.csv", module1)
    ci_path = with_module1_suffix(repo_root / "results" / "us_c7_3_module2_ci.csv", module1)
    png_path = with_module1_suffix(repo_root / "thesis" / "figures" / "us_c7_3_module2.png", module1)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    png_path.parent.mkdir(parents=True, exist_ok=True)

    data = load_model_residuals(module1=module1)
    frame = build_module2_frame(data)
    spec = derive_specification(frame[frame["role"] == "training"])
    records, ci_records = evaluate_module2(frame, spec.covariates, seed=procedure_seeds(module1)["t47"])

    for path, columns, rows in (
        (csv_path, module2_record_columns(spec.covariates), records),
        (ci_path, MODULE2_CI_COLUMNS, ci_records),
    ):
        with open(path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(columns))
            writer.writeheader()
            writer.writerows(rows)

    df = pd.DataFrame(records)
    active = df[df["state"] == "active"].copy()
    active["structural_share"] = active["structural_share"].astype(float)
    ci = pd.DataFrame(ci_records)

    fig, (ax_a, ax_b, ax_c) = plt.subplots(1, 3, figsize=(21, 6), gridspec_kw={"width_ratios": [3, 1, 2]})

    # Pannello A: π nel tempo per ogni W
    for w in MODULE2_WINDOWS:
        sub = active[active["window"] == w]
        ax_a.plot(pd.to_datetime(sub["decision_date"]), sub["structural_share"], ".", markersize=2,
                  label=f"W = {w}", alpha=0.6)
    ax_a.set_ylabel("Quota strutturale π")
    ax_a.set_title("A) π alla data di decisione (training e validazione)", loc="left", fontsize=11,
                   fontweight="bold")
    ax_a.legend(fontsize=8, markerscale=4)
    ax_a.grid(True, linestyle=":", alpha=0.6)

    # Pannello B: distribuzione di π per W
    ax_b.boxplot([active.loc[active["window"] == w, "structural_share"] for w in MODULE2_WINDOWS],
                 tick_labels=[str(w) for w in MODULE2_WINDOWS])
    ax_b.set_xlabel("W")
    ax_b.set_title("B) π per W", loc="left", fontsize=11, fontweight="bold")
    ax_b.grid(True, axis="y", linestyle=":", alpha=0.6)

    # Pannello C: componente strutturale con intervallo, W = 80, stagione 2019-20
    sel = ci[(ci["window"] == 80) & (ci["component"] == "structural") & (ci["season"] == "2019-20")]
    ax_c.errorbar(sel["matchday"], sel["estimate"],
                  yerr=[sel["estimate"] - sel["lower"], sel["upper"] - sel["estimate"]],
                  fmt="o", color="tab:purple", capsize=2, markersize=3)
    ax_c.axhline(0.0, color="black", linewidth=0.8)
    ax_c.set_xlabel("Matchday")
    ax_c.set_ylabel("Componente strutturale")
    ax_c.set_title("C) Strutturale con intervallo al 95%, 2019-20, W = 80", loc="left", fontsize=11,
                   fontweight="bold")
    ax_c.grid(True, linestyle=":", alpha=0.6)

    fig.tight_layout()
    fig.savefig(png_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    run_experiment(module1_from_argv(sys.argv[1:]))
