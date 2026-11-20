"""Script: le due figure della tesi sugli allarmi della versione principale (stesso stile di tesi_robustezza_figures.py).

- thesis/figures/tesi_allarmi_stagioni.png: le 19 stagioni vere giornata per giornata, con la
  puntata della versione definitiva (quarto di Kelly senza allarme, 0.25·κ dopo un errore nei dati,
  0.10 dopo un errore strutturale, finché dura l'allarme) e il capitale finale dei due agenti;
- thesis/figures/tesi_allarmi_2018_19.png: la stagione 2018-19, con le statistiche dell'ANOVA sulla media e sulla dispersione divise per la loro soglia e il capitale della
  versione principale e del quarto di Kelly.

Legge results/us_c33_main_alarm_trace.csv e results/us_c33_main_alarm_seasons.csv.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

REPO_ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = REPO_ROOT / "thesis" / "figures"
RESULTS = REPO_ROOT / "results"
SEASONS_PNG = FIG_DIR / "tesi_allarmi_stagioni.png"
DETAIL_PNG = FIG_DIR / "tesi_allarmi_2018_19.png"
DETAIL_SEASONS = ("2018-19",)

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
SERIES_KELLY = "#2a78d6"
SERIES_SCHEME = "#eb6834"
ACTIVE = "#d9e6f5"
REDUCED = "#f2c14e"
STOPPED = "#eb6834"
ALARM = "#0b0b0b"
MEAN_LINE = "#7a4fb5"
DISP_LINE = "#1f9e89"


def _style(ax: plt.Axes, grid_axis: str = "y") -> None:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=INK_2, labelsize=9)
    if grid_axis:
        ax.grid(axis=grid_axis, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def plot_seasons() -> None:
    trace = pd.read_csv(RESULTS / "us_c33_main_alarm_trace.csv")
    seasons = pd.read_csv(RESULTS / "us_c33_main_alarm_seasons.csv")
    order = list(seasons["season"])
    fits = seasons["fit_through"]
    group = np.cumsum([i > 0 and fits.iloc[i] != fits.iloc[i - 1] for i in range(len(order))])
    ys = [-(i + 1.2 * group[i]) for i in range(len(order))]
    fig, ax = plt.subplots(figsize=(10, 7.2), facecolor=SURFACE)
    _style(ax, grid_axis="")
    for i, season in enumerate(order):
        d = trace[trace["season"] == season]
        y = ys[i]
        x0 = d["matches_before"].to_numpy(float)
        x1 = np.append(x0[1:], 380.0)
        colors = np.where(d["diagnosis"] == "structural", STOPPED,
                          np.where(d["diagnosis"] == "compositional", REDUCED, ACTIVE))
        ax.barh(np.full(len(d), y), x1 - x0, left=x0, height=0.62, color=colors, linewidth=0)
        alarm = d[d["diagnosis"] != "none"]
        ax.scatter(alarm["matches_before"], np.full(len(alarm), y), marker="|", s=90, color=ALARM, linewidths=1.2,
                   zorder=3)
        row = seasons[seasons["season"] == season].iloc[0]
        m, b = 100 * row["capital_main"], 100 * row["capital_quarter"]
        mark = "+" if m > b + 0.5 else ("−" if m < b - 0.5 else "=")
        ax.text(392, y, f"{m:.0f}%", color=SERIES_SCHEME, fontsize=8.5, va="center", ha="left")
        ax.text(432, y, f"{b:.0f}%", color=SERIES_KELLY, fontsize=8.5, va="center", ha="left")
        ax.text(470, y, mark, color=INK, fontsize=9, va="center", ha="left")
    starts = [i for i in range(len(order)) if i == 0 or fits.iloc[i] != fits.iloc[i - 1]]
    for i in starts:
        ax.text(0, ys[i] + 0.55, f"modello calibrato sul {fits.iloc[i]}", color=INK_2, fontsize=8.5,
                ha="left", va="bottom", style="italic")
    ax.set_yticks(ys)
    ax.set_yticklabels(order, fontsize=8.5)
    ax.set_xlim(0, 485)
    ax.set_xticks([0, 40, 100, 190, 280, 380])
    ax.set_xlabel("Partite giocate nella stagione", color=INK_2, fontsize=9)
    ax.text(392, ys[0] + 0.55, "schema", color=SERIES_SCHEME, fontsize=8, ha="left", va="bottom")
    ax.text(432, ys[0] + 0.55, "¼ Kelly", color=SERIES_KELLY, fontsize=8, ha="left", va="bottom")
    ax.axvline(40, color=GRID, linewidth=1, linestyle="--")
    ax.set_ylim(ys[-1] - 0.6, ys[0] + 1.3)
    handles = [Patch(color=ACTIVE, label="nessun allarme: quarto di Kelly (0,25)"),
               Patch(color=REDUCED, label="errore nei dati: puntata 0,19"),
               Patch(color=STOPPED, label="errore strutturale: puntata 0,10"),
               Line2D([], [], color=ALARM, marker="|", linestyle="none", markersize=9,
                      label="giornata con l'allarme acceso")]
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(0, -0.08), frameon=False, fontsize=9, ncol=2)
    fig.tight_layout()
    fig.savefig(SEASONS_PNG, dpi=200, facecolor=SURFACE)
    plt.close(fig)


def plot_detail() -> None:
    trace = pd.read_csv(RESULTS / "us_c33_main_alarm_trace.csv")
    fig, axes = plt.subplots(2, len(DETAIL_SEASONS), figsize=(3 + 5 * len(DETAIL_SEASONS), 6.4),
                             facecolor=SURFACE, sharex=True, squeeze=False, gridspec_kw={"height_ratios": [1, 1]})
    for col, season in enumerate(DETAIL_SEASONS):
        d = trace[(trace["season"] == season) & trace["f_mean"].notna()]
        full = trace[trace["season"] == season]
        x = d["matches_before"]
        top, bottom = axes[0, col], axes[1, col]
        _style(top)
        _style(bottom)
        top.plot(x, d["f_mean"] / d["f_mean_threshold"], color=MEAN_LINE, linewidth=1.3,
                 label="ANOVA sulla media del residuo, divisa per la soglia")
        top.plot(x, d["f_dispersion"] / d["f_dispersion_threshold"], color=DISP_LINE, linewidth=1.3,
                 label="ANOVA sulla dispersione del residuo, divisa per la soglia")
        top.axhline(1.0, color=INK, linewidth=1, linestyle="--")
        top.text(380, 1.03, "soglia", color=INK, fontsize=8, ha="right", va="bottom")
        starts = full["matches_before"].to_numpy(float)
        ends = np.append(starts[1:], 380.0)
        for s0, s1, diag in zip(starts, ends, full["diagnosis"]):
            if diag == "structural":
                for ax in (top, bottom):
                    ax.axvspan(s0, s1, color=STOPPED, alpha=0.18, linewidth=0)
        top.set_title(season, color=INK, fontsize=10, loc="left")
        after = np.append(0, (full["matches_before"] + full["n_matches"]).to_numpy())
        bottom.plot(after, np.append(100, 100 * full["wealth_quarter"]), color=SERIES_KELLY, linewidth=1.4,
                    label="quarto di Kelly, senza supervisore")
        bottom.plot(after, np.append(100, 100 * full["wealth_main"]), color=SERIES_SCHEME, linewidth=1.4,
                    label="schema, versione definitiva")
        bottom.axhline(100, color=INK_2, linewidth=0.8)
        bottom.set_xlim(0, 380)
        bottom.set_xlabel("Partite giocate nella stagione", color=INK_2, fontsize=9)
        if col == 0:
            top.set_ylabel("Statistica / soglia", color=INK_2, fontsize=9)
            bottom.set_ylabel("Capitale (%)", color=INK_2, fontsize=9)
    h1, l1 = axes[0, 0].get_legend_handles_labels()
    h2, l2 = axes[1, 0].get_legend_handles_labels()
    span = Patch(color=STOPPED, alpha=0.18, label="giornate con errore strutturale: puntata 0,10")
    fig.legend(h1 + h2 + [span], l1 + l2 + [span.get_label()], loc="lower center", ncol=1, frameon=False,
               fontsize=9)
    fig.tight_layout(rect=(0, 0.17, 1, 1))
    fig.savefig(DETAIL_PNG, dpi=200, facecolor=SURFACE)
    plt.close(fig)


if __name__ == "__main__":
    plot_seasons()
    plot_detail()
