"""Script: serie δ, covariate candidate e ispezione prima della specificazione.

Costruisce il DataFrame per partita del Modulo 2 (shk.model.module2_data), applica sul
training le regole di specificazione fissate prima (shk.model.covariate_inspection) e
scrive results/us_c7_2_covariates.csv e thesis/figures/us_c7_2_covariates.png.
Con --module1 dixon_coles usa il Modulo 1 Dixon-Coles e scrive le uscite con il suffisso _dc,
senza toccare quelle Elo; il differenziale di forza è lambda_diff e i seed sono quelli
della calibrazione con Dixon-Coles (module1_seeds.procedure_seeds).
"""

import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from shk.model.covariate_inspection import (
    ANOVA_COVARIATES,
    COVARIATES_CSV_COLUMNS,
    evaluate_covariates,
)
from shk.model.module1 import MODULE1_ELO, module1_from_argv, with_module1_suffix
from shk.model.module1_seeds import procedure_seeds
from shk.model.module2_data import build_module2_frame, select_triple_2000_01, strength_covariate, with_strength
from shk.model.residuals import load_model_residuals


def run_experiment(module1: str = MODULE1_ELO) -> None:
    """Calcola i record, scrive il CSV e la figura a tre pannelli."""
    repo_root = Path(__file__).resolve().parents[1]
    csv_path = with_module1_suffix(repo_root / "results" / "us_c7_2_covariates.csv", module1)
    png_path = with_module1_suffix(repo_root / "thesis" / "figures" / "us_c7_2_covariates.png", module1)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    png_path.parent.mkdir(parents=True, exist_ok=True)

    data = load_model_residuals(module1=module1)
    choice = select_triple_2000_01(data.df)
    frame = build_module2_frame(data, triple_2000_01=choice.source)
    spec, records = evaluate_covariates(frame, seed=procedure_seeds(module1)["t46"])

    triple_records = [
        {**{c: "" for c in COVARIATES_CSV_COLUMNS}, "row_type": "triple_2000_01", "dataset": "training",
         "season": "2000-01", "covariate": source, "value": overround,
         "included": source == choice.source,
         "reason": f"b365_2002_03_overround={choice.b365_reference_overround!r}"}
        for source, overround in choice.candidate_overrounds.items()
    ]
    val = frame[frame["role"] == "validation"]
    delta_records = [
        {**{c: "" for c in COVARIATES_CSV_COLUMNS}, "row_type": "delta_season", "dataset": role,
         "season": season, "covariate": "delta", "n": int(len(grp)), "mean": float(grp["delta"].mean()),
         "sd": float(grp["delta"].std(ddof=1))}
        for (role, season), grp in frame.groupby(["role", "season"], sort=False)
    ]
    all_records = triple_records + delta_records + records

    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(COVARIATES_CSV_COLUMNS))
        writer.writeheader()
        writer.writerows(all_records)

    fig, (ax_a, ax_b, ax_c) = plt.subplots(1, 3, figsize=(20, 6))

    # Pannello A: δ medio per stagione
    seasons = [r["season"] for r in delta_records]
    means = [r["mean"] for r in delta_records]
    colors = ["tab:green" if r["dataset"] == "training" else "tab:blue" for r in delta_records]
    ax_a.bar(np.arange(len(seasons)), means, color=colors)
    ax_a.axhline(0.0, color="black", linewidth=0.8)
    ax_a.axhline(float(val["delta"].mean()), color="tab:blue", linestyle="--", linewidth=1.0,
                 label="Media della validazione (ĝ Shin)")
    ax_a.set_xticks(np.arange(len(seasons)))
    ax_a.set_xticklabels(seasons, rotation=75, fontsize=8)
    ax_a.set_ylabel("δ medio per stagione")
    ax_a.set_title("A) δ = ln p̂(x) − ln q(x), q di Shin (verde: training)", loc="left", fontsize=11,
                   fontweight="bold")
    ax_a.legend(fontsize=8)

    # Pannello B: VIF passo per passo sul training
    vif_rows = [r for r in records if r["row_type"] == "vif"]
    steps = sorted({int(r["step"]) for r in vif_rows})
    covs = list(dict.fromkeys(r["covariate"] for r in vif_rows))
    for cov in covs:
        xs = [int(r["step"]) for r in vif_rows if r["covariate"] == cov]
        ys = [float(r["value"]) for r in vif_rows if r["covariate"] == cov]
        ax_b.plot(xs, ys, "o-", label=cov)
    ax_b.axhline(5.0, color="black", linestyle="--", linewidth=1.0, label="VIF = 5")
    ax_b.set_yscale("log")
    ax_b.set_xticks(steps)
    ax_b.set_xlabel("Passo della regola (ii)")
    ax_b.set_ylabel("VIF (scala log)")
    ax_b.set_title("B) Regola (ii) sul training. Specificazione finale:\n" + ", ".join(spec.covariates),
                   loc="left", fontsize=10, fontweight="bold")
    ax_b.legend(fontsize=7)

    # Pannello C: η² dell'ANOVA di δ per covariata
    anova = [r for r in records if r["row_type"] == "anova"]
    anova_names = with_strength(ANOVA_COVARIATES, strength_covariate(frame))
    width = 0.4
    for j, dataset in enumerate(("training", "validation")):
        values = [next(float(r["eta2"]) for r in anova if r["dataset"] == dataset and r["covariate"] == c)
                  for c in anova_names]
        ax_c.bar(np.arange(len(anova_names)) + (j - 0.5) * width, values, width=width, label=dataset)
    ax_c.set_xticks(np.arange(len(anova_names)))
    ax_c.set_xticklabels(anova_names, rotation=45, fontsize=8)
    ax_c.set_ylabel("η² di δ")
    ax_c.set_title("C) ANOVA di δ per covariata (quintili o flag)", loc="left", fontsize=11, fontweight="bold")
    ax_c.legend(fontsize=8)

    fig.tight_layout()
    fig.savefig(png_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    run_experiment(module1_from_argv(sys.argv[1:]))
