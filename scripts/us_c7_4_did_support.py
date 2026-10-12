"""Script T49: DiD fra partite con neopromosse e fra squadre note, Ñopo e supporto comune.

Scrive results/us_c7_4_did_support.csv e thesis/figures/us_c7_4_did_support.png
(shk.model.did_support).
Con --module1 dixon_coles usa il Modulo 1 Dixon-Coles e scrive le uscite con il suffisso _dc,
senza toccare quelle Elo (T60).
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
from shk.model.did_support import DID_SUPPORT_CSV_COLUMNS, evaluate_did_support
from shk.model.known_scenarios import add_no_objective_flag
from shk.model.module1 import MODULE1_ELO, module1_from_argv, with_module1_suffix
from shk.model.module2_data import build_module2_frame
from shk.model.residuals import load_model_residuals
from shk.stats.oaxaca_synthetic import SEED_S8


def run_experiment(module1: str = MODULE1_ELO) -> None:
    """Calcola DiD, placebo, Ñopo e supporto; scrive CSV e figura a tre pannelli."""
    repo_root = Path(__file__).resolve().parents[1]
    csv_path = with_module1_suffix(repo_root / "results" / "us_c7_4_did_support.csv", module1)
    png_path = with_module1_suffix(repo_root / "thesis" / "figures" / "us_c7_4_did_support.png", module1)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    png_path.parent.mkdir(parents=True, exist_ok=True)

    data = load_model_residuals(module1=module1)
    frame = add_no_objective_flag(build_module2_frame(data), data.df)
    spec = derive_specification(frame[frame["role"] == "training"])
    records = evaluate_did_support(frame, spec.covariates, data.df, seed=SEED_S8)

    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(DID_SUPPORT_CSV_COLUMNS))
        writer.writeheader()
        writer.writerows(records)

    df = pd.DataFrame(records)
    fig, (ax_a, ax_b, ax_c) = plt.subplots(1, 3, figsize=(22, 6.5))

    # Pannello A: DiD per stagione con intervallo e banda placebo
    did = df[df["row_type"] == "did"]
    plc = df[df["row_type"] == "placebo"].set_index("season")
    x = np.arange(len(did))
    est = did["estimate"].astype(float).to_numpy()
    lo = did["lower"].astype(float).to_numpy()
    hi = did["upper"].astype(float).to_numpy()
    ax_a.errorbar(x, est, yerr=[np.maximum(est - lo, 0), np.maximum(hi - est, 0)], fmt="o", color="tab:blue",
                  capsize=2, markersize=4, label="DiD con intervallo al 95%")
    seasons = did["season"].tolist()
    ql = [float(plc.loc[s, "placebo_q025"]) if s in plc.index else np.nan for s in seasons]
    qh = [float(plc.loc[s, "placebo_q975"]) if s in plc.index else np.nan for s in seasons]
    ax_a.fill_between(x, ql, qh, color="gray", alpha=0.25, step="mid", label="Placebo 2.5–97.5%")
    ax_a.axhline(0.0, color="black", linewidth=0.8)
    ax_a.set_xticks(x)
    ax_a.set_xticklabels(seasons, rotation=75, fontsize=8)
    ax_a.set_ylabel("DiD di δ (neopromosse − note, tardi − presto)")
    ax_a.set_title("A) DiD sequenziale per stagione e pooled", loc="left", fontsize=11, fontweight="bold")
    ax_a.legend(fontsize=8)
    ax_a.grid(True, linestyle=":", alpha=0.6)

    # Pannello B: Ñopo, quota di partite fuori supporto per scenario
    nopo = df[df["row_type"] == "nopo"]
    groups = [("1_transition", 80, "covariates", "Transizioni, W = 80"),
              ("3_end_season", "", "without_flag", "Fine stagione, senza flag"),
              ("3_end_season", "", "with_flag", "Fine stagione, con flag")]
    data_b = []
    for scenario, w, version, label in groups:
        sel = nopo[(nopo["scenario"] == scenario) & (nopo["version"] == version)]
        if w != "":
            sel = sel[sel["window"] == w]
        data_b.append((label, sel["share_unmatched_a"].astype(float), sel["share_unmatched_b"].astype(float)))
    pos = np.arange(len(data_b))
    ax_b.boxplot([d[1] for d in data_b], positions=pos - 0.18, widths=0.3, patch_artist=True,
                 boxprops={"facecolor": "tab:blue", "alpha": 0.5})
    ax_b.boxplot([d[2] for d in data_b], positions=pos + 0.18, widths=0.3, patch_artist=True,
                 boxprops={"facecolor": "tab:orange", "alpha": 0.5})
    ax_b.set_xticks(pos)
    ax_b.set_xticklabels([d[0] for d in data_b], fontsize=8)
    ax_b.set_ylabel("Quota di partite fuori supporto (blu: A, arancio: B)")
    ax_b.set_title("B) Ñopo: quote fuori supporto", loc="left", fontsize=11, fontweight="bold")
    ax_b.grid(True, axis="y", linestyle=":", alpha=0.6)

    # Pannello C: quota fuori supporto nei matchday 1–10 per W e gruppo
    sup = df[df["row_type"] == "support"]
    width = 0.2
    for j, group in enumerate(("new", "returning", "none")):
        vals = [pd.to_numeric(sup[(sup["window"] == w) & (sup["group"] == group)]["share"], errors="coerce").mean()
                for w in (40, 80, 120, 190)]
        ax_c.bar(np.arange(4) + (j - 1) * width, vals, width=width,
                 label={"new": "Con neopromossa mai vista", "returning": "Con tornante", "none": "Senza neopromosse"}[group])
    ax_c.set_xticks(np.arange(4))
    ax_c.set_xticklabels(["W = 40", "W = 80", "W = 120", "W = 190"])
    ax_c.set_ylim(0, 1.05)
    ax_c.set_ylabel("Quota fuori supporto (media sulle stagioni)")
    ax_c.set_title("C) Regola fuori supporto, matchday 1–10", loc="left", fontsize=11, fontweight="bold")
    ax_c.legend(fontsize=8)
    ax_c.grid(True, axis="y", linestyle=":", alpha=0.6)

    fig.tight_layout()
    fig.savefig(png_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    run_experiment(module1_from_argv(sys.argv[1:]))
