"""Script: le due figure della tesi sulle analisi di robustezza (stesso stile di relatore_figures.py).

- thesis/figures/tesi_capitale_principale.png: capitale rimasto a fine stagione, nelle 19 stagioni
  vere, per il quarto di Kelly senza supervisore e per la versione principale dello schema
  (C3_ref_stop_season_dx: confronto con la stagione di calibrazione, soglie dell'allarme per
  stagione, diagnosi a due termini, fermo fino a fine stagione), con la puntata minima di £0,01
  (results/us_c27_two_fold_seasons.csv);
- thesis/figures/tesi_eta_calendario.png: per stagione, dispersione di δ e distanza dal mercato
  prima della partita (−E_q[δ]) del modello congelato e del modello ricalibrato ogni anno, sulle
  stesse partite (results/us_c28_model_age_seasons.csv).
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = REPO_ROOT / "thesis" / "figures"
RESULTS = REPO_ROOT / "results"
CAPITAL_PNG = FIG_DIR / "tesi_capitale_principale.png"
AGE_PNG = FIG_DIR / "tesi_eta_calendario.png"
MAIN = "C3_ref_stop_season_dx"

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
SERIES_KELLY = "#2a78d6"
SERIES_SCHEME = "#eb6834"


def _style(ax: plt.Axes) -> None:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=INK_2, labelsize=9)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def _fit_bands(ax: plt.Axes, fits: pd.Series, y: float) -> None:
    n = len(fits)
    starts = [i for i in range(n) if i == 0 or fits.iloc[i] != fits.iloc[i - 1]]
    for i in starts[1:]:
        ax.axvline(i - 0.5, color=GRID, linewidth=1.2)
    for k, i in enumerate(starts):
        end = starts[k + 1] - 1 if k + 1 < len(starts) else n - 1
        ax.text((i + end) / 2, y, f"calibrato sul {fits.iloc[i]}", color=INK_2, fontsize=8, ha="center",
                bbox={"facecolor": SURFACE, "edgecolor": "none", "pad": 1.5})


def plot_capital() -> None:
    d = pd.read_csv(RESULTS / "us_c27_two_fold_seasons.csv")
    d = d[d["config"] == "gbp_0.01"]
    wide = d.pivot(index="season", columns="agent", values="log_wealth").sort_index()
    fits = d.groupby("season")["fit_through"].first().reindex(wide.index)
    kelly, scheme = 100 * np.exp(wide["B_0.25"]), 100 * np.exp(wide[MAIN])
    n, w = len(wide), 0.38
    xs = np.arange(n)
    fig, ax = plt.subplots(figsize=(10, 4.8), facecolor=SURFACE)
    _style(ax)
    ax.bar(xs - w / 2 - 0.01, kelly, w, color=SERIES_KELLY, label="Quarto di Kelly, senza supervisore")
    ax.bar(xs + w / 2 + 0.01, scheme, w, color=SERIES_SCHEME,
           label="Schema, versione principale: soglie per stagione, diagnosi a due termini, fermo fino a fine stagione")
    ax.axhline(100, color=INK_2, linewidth=1)
    ax.text(n - 0.5, 102, "capitale iniziale", color=INK_2, fontsize=8, ha="right", va="bottom")
    ax.set_xticks(xs)
    ax.set_xticklabels(wide.index, rotation=60, fontsize=8)
    ax.set_ylabel("Capitale rimasto a fine stagione (%)", color=INK_2, fontsize=9)
    top = 10 * np.ceil(max(kelly.max(), scheme.max()) / 10) + 15
    ax.set_ylim(0, top)
    _fit_bands(ax, fits, top - 6)
    better, worse = int((scheme > kelly + 1e-9).sum()), int((scheme < kelly - 1e-9).sum())
    ax.legend(loc="upper left", bbox_to_anchor=(0, -0.22), frameon=False, fontsize=9, ncol=1)
    fig.suptitle(f"Capitale rimasto in ogni stagione: lo schema fa meglio in {better} stagioni su {n}, peggio in "
                 f"{worse}, uguale nelle altre", color=INK, fontsize=12, x=0.02, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(CAPITAL_PNG, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def plot_age() -> None:
    d = pd.read_csv(RESULTS / "us_c28_model_age_seasons.csv")
    xs = np.arange(len(d))
    fig, axes = plt.subplots(2, 1, figsize=(10, 6.6), sharex=True, facecolor=SURFACE)
    panels = (("dispersion", 1.0, "Dispersione degli errori\n(più alto = peggio)"),
              ("expected", -1.0, "Distanza dal mercato\nprima della partita\n(più alto = peggio)"))
    for ax, (name, sign, label) in zip(axes, panels):
        _style(ax)
        frozen, refit = sign * d[f"frozen_{name}"], sign * d[f"refit_{name}"]
        ax.plot(xs, frozen, color=SERIES_KELLY, linewidth=2, marker="o", markersize=5, markeredgecolor=SURFACE,
                label="Modello congelato (da 1 a 9 anni dalla calibrazione)")
        ax.plot(xs, refit, color=SERIES_SCHEME, linewidth=2, marker="o", markersize=5, markeredgecolor=SURFACE,
                label="Modello ricalibrato ogni anno sulla stagione precedente")
        ax.set_ylabel(label, color=INK_2, fontsize=9)
        low, high = min(frozen.min(), refit.min()), max(frozen.max(), refit.max())
        ax.set_ylim(low - 0.08 * (high - low), high + 0.22 * (high - low))
        _fit_bands(ax, d["frozen_fit"], high + 0.14 * (high - low))
    axes[1].set_xticks(xs)
    axes[1].set_xticklabels(d["season"], rotation=60, fontsize=8)
    axes[1].legend(loc="upper left", bbox_to_anchor=(0, -0.32), frameon=False, fontsize=9, ncol=1)
    fig.suptitle("Anche il modello ricalibrato ogni anno si allontana dal mercato con il passare delle stagioni",
                 color=INK, fontsize=12, x=0.02, ha="left")
    fig.text(0.02, 0.925, "Stesse partite e stesse quote per i due modelli. Le etichette in alto indicano la "
             "calibrazione del modello congelato.", color=INK_2, fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(AGE_PNG, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    plot_capital()
    plot_age()


if __name__ == "__main__":
    main()
