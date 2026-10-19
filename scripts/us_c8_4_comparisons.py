"""Script: confronti che decidono, con intervalli block e iid, effect size e falsi allarmi.

Legge le uscite per seed dell'esecuzione congelata sulla validazione (results/raw/us_c8_3_validation_raw.npz), esegue il run iid
aggiuntivo degli stessi agenti (results/raw/us_c8_4_validation_iid_raw.npz, non versionato)
e π e λ di C2 sui seed dell'esecuzione congelata sulla validazione, e scrive results/us_c8_4_comparisons.csv e
thesis/figures/us_c8_4_comparisons.png. Nessun confronto è una soglia da superare.
Con --from-raw rilegge anche il run iid già scritto invece di rieseguirlo.
Con --module1 dixon_coles usa il Modulo 1 Dixon-Coles e config/frozen_params_dc.toml, e legge e
scrive i file con il suffisso _dc, senza toccare quelli Elo.
"""

import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from shk.model.comparisons_run import (
    COMPARISON_COLUMNS,
    alarm_records,
    comparison_records,
    coverage_records,
    evaluate_iid,
    pi_lambda_records,
)
from shk.model.frozen_params import frozen_params_path
from shk.model.module1 import MODULE1_ELO, module1_from_argv, with_module1_suffix
from shk.model.module1_seeds import s10_seed
from shk.model.module2_data import build_module2_frame
from shk.model.residuals import load_model_residuals
from shk.model.validation_run import load_raw, save_raw

WORKERS = 5


def run_experiment(from_raw: bool = False, module1: str = MODULE1_ELO) -> None:
    """Run iid (o rilettura con from_raw), confronti, falsi allarmi, π e λ, copertura; scrive CSV e figura."""
    repo_root = Path(__file__).resolve().parents[1]
    block = load_raw(with_module1_suffix(repo_root / "results" / "raw" / "us_c8_3_validation_raw.npz", module1))
    iid_path = with_module1_suffix(repo_root / "results" / "raw" / "us_c8_4_validation_iid_raw.npz", module1)
    csv_path = with_module1_suffix(repo_root / "results" / "us_c8_4_comparisons.csv", module1)
    png_path = with_module1_suffix(repo_root / "thesis" / "figures" / "us_c8_4_comparisons.png", module1)
    png_path.parent.mkdir(parents=True, exist_ok=True)

    params_path = frozen_params_path(module1)
    seed = s10_seed(module1)
    frame = build_module2_frame(load_model_residuals(module1=module1))
    if from_raw:
        iid = load_raw(iid_path)
    else:
        iid = evaluate_iid(frame, block, params_path=params_path, workers=WORKERS, seed=seed)
        save_raw(iid_path, iid)
    records = (comparison_records(block, iid, seed=seed) + alarm_records(block)
               + pi_lambda_records(frame, params_path=params_path, workers=WORKERS, seed=seed)
               + coverage_records(block, seed=seed))
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(COMPARISON_COLUMNS))
        writer.writeheader()
        writer.writerows(records)

    df = pd.DataFrame(records)
    comp = df[(df["row_type"] == "comparison") & (df["config"] == "gbp_0.01")]
    fig, (ax_a, ax_b, ax_c) = plt.subplots(1, 3, figsize=(22, 6.5))

    # Pannello A: differenze della log-ricchezza finale con intervallo block e iid
    lw = comp[comp["metric"] == "final_log_wealth"]
    y = np.arange(len(lw))
    est = lw["estimate"].astype(float).to_numpy()
    for off, lo_col, hi_col, color, label in ((-0.15, "ci_block_low", "ci_block_high", "tab:blue", "block (L_PW), t corretto"),
                                              (0.15, "ci_iid_low", "ci_iid_high", "tab:orange", "iid (L = 1), t corretto")):
        lo, hi = lw[lo_col].astype(float).to_numpy(), lw[hi_col].astype(float).to_numpy()
        ax_a.errorbar(est, y + off, xerr=[np.maximum(est - lo, 0), np.maximum(hi - est, 0)], fmt="o",
                      color=color, capsize=3, label=label)
    ax_a.axvline(0.0, color="black", linewidth=0.8)
    ax_a.set_yticks(y)
    ax_a.set_yticklabels(lw["comparison"])
    ax_a.set_xlabel("Differenza pooled di ln W_T (19 stagioni)")
    ax_a.set_title("A) Confronti, configurazione £0.01", loc="left", fontsize=11, fontweight="bold")
    ax_a.legend(fontsize=9)
    ax_a.grid(True, axis="x", linestyle=":", alpha=0.6)

    # Pannello B: rapporto fra le ampiezze block e iid per metrica
    ratios = comp.pivot_table(index="metric", columns="comparison", values="width_ratio_block_iid")
    ax_b.boxplot([ratios.loc[m].dropna().to_numpy() for m in ratios.index], tick_labels=list(ratios.index))
    ax_b.axhline(1.0, color="black", linewidth=0.8)
    ax_b.set_ylabel("Ampiezza block / ampiezza iid")
    ax_b.set_title("B) Costo dell'autocorrelazione", loc="left", fontsize=11, fontweight="bold")
    ax_b.tick_params(axis="x", rotation=45)
    ax_b.grid(True, axis="y", linestyle=":", alpha=0.6)

    # Pannello C: falsi allarmi, quota di seed con almeno un allarme sotto H₀ e allarmi osservati
    al = df[df["row_type"] == "alarms"]
    x = np.arange(al["season"].nunique())
    seasons = list(dict.fromkeys(al["season"]))
    for k, (agent, color) in enumerate((("C1", "tab:olive"), ("D_ADWIN", "tab:purple"), ("D_PH", "tab:red"))):
        sub = al[al["agent"] == agent].set_index("season").loc[seasons]
        ax_c.bar(x + (k - 1) * 0.27, sub["h0_share_seeds_with_alarm"].astype(float), 0.27, color=color, alpha=0.6,
                 label=f"{agent}: H₀, quota di seed con allarme")
        ax_c.scatter(x + (k - 1) * 0.27, (sub["observed_alarms"].astype(float) > 0).astype(float), color=color,
                     marker="x", s=40)
    ax_c.set_xticks(x)
    ax_c.set_xticklabels(seasons, rotation=75, fontsize=8)
    ax_c.set_ylabel("Quota (barre); allarme sui dati sì/no (croci)")
    ax_c.set_title("C) Falsi allarmi sotto H₀ e allarmi sui dati", loc="left", fontsize=11, fontweight="bold")
    ax_c.legend(fontsize=8)
    ax_c.grid(True, axis="y", linestyle=":", alpha=0.6)

    fig.tight_layout()
    fig.savefig(png_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    run_experiment(from_raw="--from-raw" in sys.argv[1:], module1=module1_from_argv(sys.argv[1:]))
