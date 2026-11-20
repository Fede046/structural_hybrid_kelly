"""Script: figura dell'evoluzione con la versione principale fra i geni (us_c32), thesis/figures/us_c32_main_evolution.png.

Tre pannelli, mediana sulle evoluzioni indipendenti, stagione per stagione:
1. variante libera: frazione di Kelly media della generazione (scala logaritmica);
2. variante con il quarto di Kelly fisso: quota della generazione con ciascuna scelta dei geni;
3. variante con il quarto di Kelly fisso: capitale della popolazione, accanto al quarto di Kelly senza
   supervisore e alla migliore strategia della popolazione (results/us_c31_main_population_summary.csv).
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SEASONS_CSV = ROOT / "results" / "us_c32_main_evolution_seasons.csv"
POPULATION_CSV = ROOT / "results" / "us_c31_main_population_summary.csv"
PNG = ROOT / "thesis" / "figures" / "us_c32_main_evolution.png"
SURFACE, INK, INK_2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"


def _style(ax: plt.Axes, title: str) -> None:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=INK_2, labelsize=8)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_title(title, color=INK, fontsize=10, loc="left")


def main() -> None:
    d = pd.read_csv(SEASONS_CSV)
    seasons = list(dict.fromkeys(d["season"]))
    x = np.arange(len(seasons))
    med = d.groupby(["variant", "season"], sort=False).median(numeric_only=True)

    fig = plt.figure(figsize=(11, 10), facecolor=SURFACE)
    grid = fig.add_gridspec(2, 2, height_ratios=(1, 1.05), hspace=0.75, wspace=0.25)
    axes = [fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1]), fig.add_subplot(grid[1, :])]
    ax = axes[0]
    _style(ax, "1. Frazione di Kelly libera di evolvere")
    ax.plot(x, med.loc["free"].loc[seasons, "mean_lam"], color=BLUE, linewidth=2, marker="o", markersize=4)
    ax.set_yscale("log")
    ax.set_ylabel("Frazione di Kelly media (scala log)", color=INK_2, fontsize=9)
    ax.axhline(0.25, color=INK_2, linewidth=1, linestyle=(0, (4, 3)))
    ax.text(len(x) - 1, 0.27, "quarto di Kelly", color=INK_2, fontsize=8, ha="right")

    ax = axes[1]
    _style(ax, "2. Quarto di Kelly fisso: quali geni vincono")
    fixed = med.loc["fixed_lam_0.25"].loc[seasons]
    series = (("con supervisore", "share_supervised", BLUE),
              ("supervisore: stagione di calibrazione", "share_calibration", ORANGE),
              ("riduzione fino a fine stagione", "share_stop_season", AQUA),
              ("regola: esito più probabile", "share_r3", YELLOW),
              ("scelte della versione definitiva", "share_main", INK))
    for label, col, color in series:
        ax.plot(x, 100 * fixed[col], color=color, linewidth=2, label=label)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Quota della generazione (%)", color=INK_2, fontsize=9)
    ax.legend(frameon=False, fontsize=8, loc="upper left", bbox_to_anchor=(-0.15, -0.3), ncol=1)

    ax = axes[2]
    _style(ax, "3. Quarto di Kelly fisso: capitale per stagione")
    pop = d[d["variant"] == "fixed_lam_0.25"].pivot(index="season", columns="run", values="population_log_wealth")
    pop = 100 * np.exp(pop.loc[seasons])
    ax.fill_between(x, pop.quantile(0.05, axis=1), pop.quantile(0.95, axis=1), color=BLUE, alpha=0.18, linewidth=0)
    ax.plot(x, pop.median(axis=1), color=BLUE, linewidth=2, label="popolazione che evolve (mediana, 5-95%)")
    ref = pd.read_csv(POPULATION_CSV)
    for version, label, color in (("member:B_0.25", "quarto di Kelly, senza supervisore", ORANGE),
                                  ("member:R3_F_season", "migliore strategia, scelta dopo", AQUA)):
        v = ref[ref["version"] == version].set_index("season").loc[seasons, "observed_log_wealth"]
        ax.plot(x, 100 * np.exp(v), color=color, linewidth=1.5, marker="o", markersize=3, label=label)
    ax.axhline(100, color=INK_2, linewidth=1)
    ax.set_ylabel("Capitale rimasto a fine stagione (%)", color=INK_2, fontsize=9)
    ax.legend(frameon=False, fontsize=8, loc="upper left", bbox_to_anchor=(0, -0.22), ncol=3)

    for ax in axes:
        ax.set_xticks(x)
        ax.set_xticklabels(seasons, rotation=70, fontsize=7)
    fig.suptitle("Evoluzione delle strategie: variazione, selezione ed ereditarietà, una generazione per stagione",
                 color=INK, fontsize=12, x=0.01, ha="left")
    fig.subplots_adjust(left=0.08, right=0.98, top=0.92, bottom=0.1)
    PNG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(PNG, dpi=150, facecolor=SURFACE)
    plt.close(fig)


if __name__ == "__main__":
    main()
