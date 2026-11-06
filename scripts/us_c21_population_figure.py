"""Script: figura della popolazione di strategie con le generazioni (us_c21).

Legge results/us_c21_population_shares.csv (o la cartella data con --dir) e scrive
thesis/figures/us_c21_population_shares.png: quote di capitale a inizio stagione, stagione per
stagione, senza e con la cassa. Le 11 strategie sono raggruppate in 5 famiglie.
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
PNG_PATH = REPO_ROOT / "thesis" / "figures" / "us_c21_population_shares.png"
SURFACE, INK, INK_2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
FAMILIES = (
    ("Kelly pieno", ("A",), "#2a78d6"),
    ("Quarto di Kelly", ("B_0.25", "R2_brake", "R3_brake"), "#eb6834"),
    ("Schema, 40 partite precedenti", ("C3", "R3_C3", "C3_stop"), "#1baf7a"),
    ("Schema, stagione di calibrazione, riprende", ("C3_ref", "R3_C3_ref"), "#eda100"),
    ("Schema, stagione di calibrazione, fermo", ("C3_ref_stop", "R3_C3_ref_stop"), "#e87ba4"),
    ("Cassa (non punta)", ("cash",), "#008300"),
)


def family_shares(sh: pd.DataFrame, version: str) -> tuple[list[str], list[tuple[str, np.ndarray, str]]]:
    """Quote a inizio stagione per famiglia, più la quota finale dell'ultima stagione."""
    p = sh[sh["version"] == version].pivot(index="season", columns="agent", values="start_share").sort_index()
    end = sh[(sh["version"] == version) & (sh["season"] == p.index[-1])].set_index("agent")["end_share"]
    seasons = list(p.index) + ["fine"]
    out = []
    for label, members, color in FAMILIES:
        cols = [m for m in members if m in p.columns]
        if cols:
            out.append((label, np.append(p[cols].sum(axis=1).to_numpy(), end[cols].sum()), color))
    return seasons, out


def plot(shares_csv: Path, png: Path) -> None:
    sh = pd.read_csv(shares_csv)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2), sharey=True, facecolor=SURFACE)
    titles = {"generations": "Senza la cassa", "generations_cash": "Con la cassa"}
    for ax, version in zip(axes, ("generations", "generations_cash")):
        seasons, fams = family_shares(sh, version)
        x = np.arange(len(seasons))
        ax.set_facecolor(SURFACE)
        ax.stackplot(x, *[100 * v for _, v, _ in fams], colors=[c for _, _, c in fams],
                     edgecolor=SURFACE, linewidth=1.2)
        bottom = 0.0
        for label, v, _ in fams:
            share = 100 * v[-1]
            if share >= 6:
                ax.text(x[-1] + 0.3, bottom + share / 2, f"{share:.0f}%", va="center", fontsize=8, color=INK)
            bottom += share
        ax.set_xlim(0, x[-1] + 1.6)
        ax.set_ylim(0, 100)
        ax.set_xticks(x)
        ax.set_xticklabels(seasons, rotation=60, fontsize=8, color=INK_2)
        ax.tick_params(axis="y", colors=INK_2, labelsize=9)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(GRID)
        ax.set_title(titles[version], color=INK, fontsize=11, loc="left")
    axes[0].set_ylabel("Quota del capitale a inizio stagione (%)", color=INK_2, fontsize=9)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for _, _, c in FAMILIES]
    fig.legend(handles, [lab for lab, _, _ in FAMILIES], loc="lower center", ncol=3, frameon=False, fontsize=9)
    fig.suptitle("Come la popolazione sposta il capitale da una stagione all'altra", color=INK, fontsize=12,
                 x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0.1, 1, 0.95))
    png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png, dpi=150, facecolor=SURFACE)
    plt.close(fig)


if __name__ == "__main__":
    argv = sys.argv[1:]
    base = Path(argv[argv.index("--dir") + 1]) if "--dir" in argv else REPO_ROOT / "results"
    out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else PNG_PATH
    plot(base / "us_c21_population_shares.csv", out)
