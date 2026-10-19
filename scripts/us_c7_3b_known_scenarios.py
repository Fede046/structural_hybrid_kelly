"""Script: scenari con drift di tipo atteso.

Scenario 1 (transizioni di stagione), scenario 2 (sospensione e porte chiuse 2019-20/2020-21)
e scenario 3 (fine stagione senza e con il flag "senza obiettivi"), con intervalli al 95%
(shk.model.known_scenarios). Scrive results/us_c7_3b_known_scenarios.csv e
thesis/figures/us_c7_3b_known_scenarios.png.
Con --module1 dixon_coles usa il Modulo 1 Dixon-Coles e scrive le uscite con il suffisso _dc,
senza toccare quelle Elo.
"""

import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from shk.model.covariate_inspection import derive_specification
from shk.model.known_scenarios import (
    KNOWN_SCENARIOS_CSV_COLUMNS,
    MAIN_WINDOW,
    VERSION_WITH_FLAG_A,
    VERSION_WITHOUT_FLAG,
    add_no_objective_flag,
    evaluate_known_scenarios,
)
from shk.model.module1 import MODULE1_ELO, module1_from_argv, with_module1_suffix
from shk.model.module2_data import build_module2_frame
from shk.model.residuals import load_model_residuals
from shk.stats.oaxaca_synthetic import SEED_S8


def _error_bars(est: np.ndarray, sel: pd.DataFrame) -> list[np.ndarray]:
    """Barre d'errore dall'intervallo percentile; zero dove la stima puntuale cade fuori."""
    lower = sel["lower"].astype(float).to_numpy()
    upper = sel["upper"].astype(float).to_numpy()
    return [np.maximum(est - lower, 0.0), np.maximum(upper - est, 0.0)]


def run_experiment(module1: str = MODULE1_ELO) -> None:
    """Calcola gli scenari, scrive il CSV e la figura a tre pannelli."""
    repo_root = Path(__file__).resolve().parents[1]
    csv_path = with_module1_suffix(repo_root / "results" / "us_c7_3b_known_scenarios.csv", module1)
    png_path = with_module1_suffix(repo_root / "thesis" / "figures" / "us_c7_3b_known_scenarios.png", module1)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    png_path.parent.mkdir(parents=True, exist_ok=True)

    data = load_model_residuals(module1=module1)
    frame = add_no_objective_flag(build_module2_frame(data), data.df)
    spec = derive_specification(frame[frame["role"] == "training"])
    records = evaluate_known_scenarios(frame, spec.covariates, seed=SEED_S8)

    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(KNOWN_SCENARIOS_CSV_COLUMNS))
        writer.writeheader()
        writer.writerows(records)

    df = pd.DataFrame(records)
    fig, (ax_a, ax_b, ax_c) = plt.subplots(1, 3, figsize=(22, 6.5))

    # Pannello A: scenario 1, quote compositiva e strutturale per transizione (W = 80)
    s1 = df[(df["scenario"] == "1_transition") & (df["window"] == MAIN_WINDOW)]
    labels = [f"{a[2:4]}→{b[2:4]}" for a, b in s1.loc[s1["quantity"] == "structural_share", ["season_a", "season_b"]].to_numpy()]
    x = np.arange(len(labels))
    for offset, (q, color, name) in zip((-0.15, 0.15), (("compositional_share", "tab:blue", "Quota compositiva"),
                                                        ("structural_share", "tab:red", "Quota strutturale π"))):
        sel = s1[s1["quantity"] == q]
        est = sel["estimate"].astype(float).to_numpy()
        ax_a.errorbar(x + offset, est, yerr=_error_bars(est, sel),
                      fmt="o", color=color, capsize=2, markersize=4, label=name)
    ax_a.set_xticks(x)
    ax_a.set_xticklabels(labels, rotation=75, fontsize=8)
    ax_a.set_ylim(-0.05, 1.05)
    ax_a.set_title("A) Scenario 1: ultime 80 di s−1 contro prime 80 di s", loc="left", fontsize=11, fontweight="bold")
    ax_a.legend(fontsize=8)
    ax_a.grid(True, linestyle=":", alpha=0.6)

    # Pannello B: scenario 2, dettagliata per covariata
    s2 = df[df["scenario"] == "2_covid_detail"]
    names = list(dict.fromkeys(s2["covariate"]))
    width = 0.27
    for j, (comp, color) in enumerate((("compositional", "tab:blue"), ("structural", "tab:red"), ("interaction", "tab:gray"))):
        vals = [float(s2[(s2["covariate"] == n) & (s2["quantity"] == comp)]["estimate"].iloc[0]) for n in names]
        ax_b.bar(np.arange(len(names)) + (j - 1) * width, vals, width=width, color=color, label=comp)
    ax_b.axhline(0.0, color="black", linewidth=0.8)
    ax_b.set_xticks(np.arange(len(names)))
    ax_b.set_xticklabels(names, rotation=45, fontsize=8)
    ax_b.set_title("B) Scenario 2: 2019-20 prima della sospensione\ncontro porte chiuse, dettagliata (Yun)",
                   loc="left", fontsize=11, fontweight="bold")
    ax_b.legend(fontsize=8)
    ax_b.grid(True, axis="y", linestyle=":", alpha=0.6)

    # Pannello C: scenario 3, π_B senza e con il flag
    s3 = df[(df["scenario"] == "3_end_season") & (df["quantity"] == "structural_share_b")]
    seasons = list(dict.fromkeys(s3["season_a"]))
    x3 = np.arange(len(seasons))
    for offset, (version, color, name) in zip((-0.15, 0.15), ((VERSION_WITHOUT_FLAG, "tab:red", "Senza flag"),
                                                              (VERSION_WITH_FLAG_A, "tab:green", "Con flag"))):
        sel = s3[s3["version"] == version]
        est = sel["estimate"].astype(float).to_numpy()
        ax_c.errorbar(x3 + offset, est, yerr=_error_bars(est, sel),
                      fmt="o", color=color, capsize=2, markersize=4, label=name)
    ax_c.set_xticks(x3)
    ax_c.set_xticklabels(seasons, rotation=75, fontsize=8)
    ax_c.set_ylim(-0.05, 1.05)
    ax_c.set_ylabel("π_B = |S| / (|C+I| + |S|)")
    ax_c.set_title("C) Scenario 3: matchday 10–25 contro 30–38", loc="left", fontsize=11, fontweight="bold")
    ax_c.legend(fontsize=8)
    ax_c.grid(True, linestyle=":", alpha=0.6)

    fig.tight_layout()
    fig.savefig(png_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    run_experiment(module1_from_argv(sys.argv[1:]))
