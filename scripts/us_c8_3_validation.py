"""Script T55: esecuzione appaiata congelata sulle 19 stagioni di validazione (US-C8.3).

Parametri solo da config/frozen_params.toml. Scrive:
- results/raw/us_c8_3_validation_raw.npz, uscite per seed e realizzazione osservata (non versionato);
- results/us_c8_3_validation_summary.csv, sintesi per agente × configurazione × stagione e
  partite con Modulo 2 non attivo per stagione e braccio;
- thesis/figures/us_c8_3_validation_summary.png.
Le stagioni girano su WORKERS processi; i risultati non dipendono dal numero di processi.
Con --figure-only rigenera solo la figura dal file npz già scritto.
"""

import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from shk.model.frozen_agents import AGENT_ORDER
from shk.model.frozen_params import load_frozen_params
from shk.model.module2_data import build_module2_frame
from shk.model.residuals import load_model_residuals
from shk.model.validation_run import (
    CONFIG_NAMES,
    METRICS,
    SUMMARY_COLUMNS,
    evaluate_validation,
    inactive_records,
    load_raw,
    save_raw,
    summary_records,
    validation_inputs,
)

WORKERS = 5


def run_experiment() -> None:
    """Esegue S10 sulla validazione, scrive le uscite per seed, la sintesi e la figura."""
    repo_root = Path(__file__).resolve().parents[1]
    raw_path = repo_root / "results" / "raw" / "us_c8_3_validation_raw.npz"
    csv_path = repo_root / "results" / "us_c8_3_validation_summary.csv"
    png_path = repo_root / "thesis" / "figures" / "us_c8_3_validation_summary.png"
    for p in (raw_path, csv_path, png_path):
        p.parent.mkdir(parents=True, exist_ok=True)

    frame = build_module2_frame(load_model_residuals())
    result = evaluate_validation(frame, workers=WORKERS)
    save_raw(raw_path, result)
    params = load_frozen_params()
    records = summary_records(result) + inactive_records(params, validation_inputs(frame, list(params.fixed["covariates"])))
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(SUMMARY_COLUMNS))
        writer.writeheader()
        writer.writerows(records)

    make_figure(result, png_path)


def make_figure(result, png_path: Path) -> None:
    """Figura a tre pannelli dalle uscite per seed e dalla realizzazione osservata."""
    lw = METRICS.index("final_log_wealth")
    ruined = METRICS.index("ruined")
    agents = [a for a in AGENT_ORDER if a != "E"]
    fig, (ax_a, ax_b, ax_c) = plt.subplots(1, 3, figsize=(22, 6.5))
    main = CONFIG_NAMES.index("gbp_0.01")

    # Pannello A: mediana sui seed della log-ricchezza finale, distribuzione sulle 19 stagioni
    data = [np.median(result.seeds[:, main, AGENT_ORDER.index(a), lw], axis=-1) for a in agents]
    ax_a.boxplot(data, tick_labels=agents)
    ax_a.axhline(0.0, color="black", linewidth=0.8)
    ax_a.set_ylabel("Mediana sui seed di ln W_T, per stagione")
    ax_a.set_title("A) Seed, configurazione principale £0.01", loc="left", fontsize=11, fontweight="bold")
    ax_a.tick_params(axis="x", rotation=45)
    ax_a.grid(True, axis="y", linestyle=":", alpha=0.6)

    # Pannello B: realizzazione osservata, somma su 19 stagioni per configurazione
    x = np.arange(len(agents))
    width = 0.27
    for ci, config in enumerate(CONFIG_NAMES):
        vals = [result.observed[:, ci, AGENT_ORDER.index(a), lw].sum() for a in agents]
        ax_b.bar(x + (ci - 1) * width, vals, width, label=config)
    ax_b.set_xticks(x)
    ax_b.set_xticklabels(agents, rotation=45)
    ax_b.axhline(0.0, color="black", linewidth=0.8)
    ax_b.set_ylabel("Somma su 19 stagioni di ln W_T")
    ax_b.set_title("B) Realizzazione osservata", loc="left", fontsize=11, fontweight="bold")
    ax_b.legend(fontsize=9)
    ax_b.grid(True, axis="y", linestyle=":", alpha=0.6)

    # Pannello C: tasso di rovina medio sulle stagioni, per configurazione
    for ci, config in enumerate(CONFIG_NAMES):
        vals = [np.nanmean(result.seeds[:, ci, AGENT_ORDER.index(a), ruined]) for a in agents]
        ax_c.bar(x + (ci - 1) * width, vals, width, label=config)
    ax_c.set_xticks(x)
    ax_c.set_xticklabels(agents, rotation=45)
    ax_c.set_ylabel("Tasso di rovina sui seed (media delle stagioni)")
    ax_c.set_title("C) Rovina", loc="left", fontsize=11, fontweight="bold")
    ax_c.legend(fontsize=9)
    ax_c.grid(True, axis="y", linestyle=":", alpha=0.6)

    fig.tight_layout()
    fig.savefig(png_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    if "--figure-only" in sys.argv[1:]:
        root = Path(__file__).resolve().parents[1]
        make_figure(load_raw(root / "results" / "raw" / "us_c8_3_validation_raw.npz"),
                    root / "thesis" / "figures" / "us_c8_3_validation_summary.png")
    else:
        run_experiment()
