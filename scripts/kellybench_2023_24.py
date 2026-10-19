"""Script: stagione 2023-24 giocata come in KellyBench, partendo da £100 000.

Gli agenti con i parametri congelati e il Modulo 1 Elo giocano gli esiti veri del 2023-24, data per
data, senza floor e con floor di £0.01 e £1 (shk.model.kellybench_run). Scrive
results/kellybench_2023_24.csv e thesis/figures/kellybench_2023_24.png.
Con `--figure-only` rigenera solo la figura dal CSV già scritto.
"""

import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from shk.model.frozen_agents import AGENT_ORDER
from shk.model.kellybench_run import KELLYBENCH_BANKROLL_GBP, KELLYBENCH_COLUMNS, evaluate_kellybench

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "results" / "kellybench_2023_24.csv"
PNG_PATH = REPO_ROOT / "thesis" / "figures" / "kellybench_2023_24.png"
CONFIG_LABELS = {"none": "senza floor", "gbp_0.01": "floor £0.01", "gbp_1": "floor £1"}


def write_csv(records: list[dict[str, object]], path: Path = CSV_PATH) -> None:
    """Scrive le righe nell'ordine di KELLYBENCH_COLUMNS."""
    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(KELLYBENCH_COLUMNS))
        writer.writeheader()
        for r in records:
            writer.writerow({c: r.get(c, "") for c in KELLYBENCH_COLUMNS})


def make_figure(df: pd.DataFrame, path: Path = PNG_PATH) -> None:
    """(a) bankroll in £ data per data con il floor da £0.01; (b) bankroll finale per agente e floor."""
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(14, 5.5), gridspec_kw={"width_ratios": (1.6, 1)})
    path_rows = df[(df["row_type"] == "path") & (df["config"] == "gbp_0.01")].copy()
    path_rows["date"] = pd.to_datetime(path_rows["date"])
    for agent in AGENT_ORDER:
        part = path_rows[path_rows["agent"] == agent]
        if len(part):
            ax_a.plot(part["date"], part["bankroll_gbp"], label=agent, lw=1.2)
    ax_a.axhline(KELLYBENCH_BANKROLL_GBP, color="0.4", ls="--", lw=0.8)
    ax_a.set_yscale("log")
    ax_a.set_title("A) Bankroll durante il 2023-24, floor £0.01", loc="left")
    ax_a.set_xlabel("data")
    ax_a.set_ylabel("bankroll (£, scala logaritmica)")
    ax_a.legend(ncols=2, fontsize=8)
    ax_a.grid(alpha=0.3)
    summary = df[df["row_type"] == "summary"]
    agents = [a for a in AGENT_ORDER if a in set(summary["agent"])]
    width = 0.27
    for k, config in enumerate(CONFIG_LABELS):
        part = summary[summary["config"] == config].set_index("agent")
        xs = [i + (k - 1) * width for i, a in enumerate(agents) if a in part.index]
        ys = [part.loc[a, "bankroll_gbp"] for a in agents if a in part.index]
        ax_b.bar(xs, ys, width=width, label=CONFIG_LABELS[config])
    ax_b.axhline(KELLYBENCH_BANKROLL_GBP, color="0.4", ls="--", lw=0.8, label="£100 000 iniziali")
    ax_b.set_xticks(range(len(agents)), agents, rotation=45, ha="right")
    ax_b.set_title("B) Bankroll finale per agente", loc="left")
    ax_b.set_ylabel("bankroll finale (£)")
    ax_b.legend(fontsize=8)
    ax_b.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def run_experiment(argv: list[str]) -> None:
    """Esegue la stagione (o solo la figura) e scrive CSV e figura."""
    if "--figure-only" not in argv:
        write_csv(evaluate_kellybench())
    make_figure(pd.read_csv(CSV_PATH))


if __name__ == "__main__":
    run_experiment(sys.argv[1:])
