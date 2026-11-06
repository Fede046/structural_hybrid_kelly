"""Script: i due grafici del documento per il relatore (thesis/schema_relatore.md).

- thesis/figures/relatore_invecchiamento.png: per ogni stagione, media e dispersione di δ
  (scarto medio assoluto dalla mediana, la misura del test di Brown-Forsythe) con il modello
  Elo, colorate per stagione di calibrazione; la linea tratteggiata è il valore della stagione
  di calibrazione.
- thesis/figures/relatore_capitale.png: capitale rimasto a fine stagione, nelle 19 stagioni
  vere, per il quarto di Kelly senza supervisore e per lo schema con confronto con la stagione
  di calibrazione, fermo fino a fine stagione (results/us_c13_scheme_reference_summary.csv,
  senza puntata minima).
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from shk.model.module2_data import build_module2_frame
from shk.model.residuals import load_model_residuals

REPO_ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = REPO_ROOT / "thesis" / "figures"
AGING_PNG = FIG_DIR / "relatore_invecchiamento.png"
CAPITAL_PNG = FIG_DIR / "relatore_capitale.png"
SUMMARY_CSV = REPO_ROOT / "results" / "us_c13_scheme_reference_summary.csv"

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
FIT_COLORS = {"2000-01": "#2a78d6", "2010-11": "#eb6834", "2020-21": "#1baf7a"}
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


def _season_stats() -> pd.DataFrame:
    frame = build_module2_frame(load_model_residuals(module1="elo"))
    rows = []
    for (season, fit, role), g in frame.groupby(["season", "fit_through", "role"]):
        d = g["delta"].to_numpy()
        rows.append({"season": season, "fit": fit, "role": role, "mean": d.mean(),
                     "dispersion": np.abs(d - np.median(d)).mean()})
    return pd.DataFrame(rows).sort_values("season").reset_index(drop=True)


def plot_aging(stats: pd.DataFrame) -> None:
    x = {s: i for i, s in enumerate(stats["season"])}
    fig, axes = plt.subplots(2, 1, figsize=(10, 6.4), sharex=True, facecolor=SURFACE,
                             gridspec_kw={"height_ratios": [1.4, 1]})
    panels = (("dispersion", "Dispersione degli errori\n(più alto = peggio)"),
              ("mean", "Errore medio\n(più basso = peggio)"))
    for ax, (col, label) in zip(axes, panels):
        _style(ax)
        for fit, color in FIT_COLORS.items():
            g = stats[stats["fit"] == fit]
            xs = [x[s] for s in g["season"]]
            ref = g.loc[g["role"] == "training", col].iloc[0]
            ax.hlines(ref, min(xs) - 0.3, max(xs) + 0.3, colors=color, linestyles=(0, (4, 3)), linewidth=1.2)
            ax.plot(xs, g[col], color=color, linewidth=2)
            train = g["role"] == "training"
            ax.scatter([x[s] for s in g.loc[train, "season"]], g.loc[train, col], s=70, facecolor=SURFACE,
                       edgecolor=color, linewidth=2, zorder=3)
            ax.scatter([x[s] for s in g.loc[~train, "season"]], g.loc[~train, col], s=40, color=color,
                       edgecolor=SURFACE, linewidth=1.5, zorder=3)
        ax.set_ylabel(label, color=INK_2, fontsize=9)
    axes[1].axhline(0.0, color=INK_2, linewidth=0.8)
    for fit, color in FIT_COLORS.items():
        g = stats[stats["fit"] == fit]
        xs = [x[s] for s in g["season"]]
        axes[0].text(np.mean(xs), 0.212, f"modello calibrato sul {fit}", color=INK, fontsize=9, ha="center")
        axes[0].hlines(0.207, min(xs) - 0.3, max(xs) + 0.3, colors=color, linewidth=3)
    axes[0].set_ylim(0.09, 0.222)
    axes[1].set_xticks(range(len(x)))
    axes[1].set_xticklabels(list(x), rotation=60, fontsize=8)
    fig.suptitle("Gli errori del modello rispetto al mercato crescono man mano che il modello invecchia",
                 color=INK, fontsize=12, x=0.02, ha="left")
    fig.text(0.02, 0.915, "Cerchio vuoto: stagione di calibrazione. Linea tratteggiata: il suo valore, "
             "che è il riferimento del confronto con la stagione di calibrazione.", color=INK_2, fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    fig.savefig(AGING_PNG, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def plot_capital() -> None:
    d = pd.read_csv(SUMMARY_CSV)
    d = d[(d["row_type"] == "summary") & (d["config"] == "none")]
    wide = d.pivot(index="season", columns="agent", values="observed_log_wealth").sort_index()
    fits = d.groupby("season")["fit_through"].first().reindex(wide.index)
    kelly = 100 * np.exp(wide["B_0.25"])
    scheme = 100 * np.exp(wide["C3_ref_stop"])
    n = len(wide)
    xs = np.arange(n)
    w = 0.38
    fig, ax = plt.subplots(figsize=(10, 4.8), facecolor=SURFACE)
    _style(ax)
    ax.bar(xs - w / 2 - 0.01, kelly, w, color=SERIES_KELLY, label="Quarto di Kelly, senza supervisore")
    ax.bar(xs + w / 2 + 0.01, scheme, w, color=SERIES_SCHEME,
           label="Schema: confronto con la stagione di calibrazione, fermo fino a fine stagione")
    ax.axhline(100, color=INK_2, linewidth=1)
    ax.text(n - 0.5, 102, "capitale iniziale", color=INK_2, fontsize=8, ha="right", va="bottom")
    ax.set_xticks(xs)
    ax.set_xticklabels(wide.index, rotation=60, fontsize=8)
    ax.set_ylabel("Capitale rimasto a fine stagione (%)", color=INK_2, fontsize=9)
    top = 10 * np.ceil(max(kelly.max(), scheme.max()) / 10) + 15
    ax.set_ylim(0, top)
    starts = [i for i in range(n) if i == 0 or fits.iloc[i] != fits.iloc[i - 1]]
    for i in starts[1:]:
        ax.axvline(i - 0.5, color=GRID, linewidth=1.2)
    for k, i in enumerate(starts):
        end = starts[k + 1] - 1 if k + 1 < len(starts) else n - 1
        ax.text((i + end) / 2, top - 6, f"calibrato sul {fits.iloc[i]}", color=INK_2, fontsize=8, ha="center",
                bbox={"facecolor": SURFACE, "edgecolor": "none", "pad": 1.5})
    better = int((scheme > kelly + 1e-9).sum())
    worse = int((scheme < kelly - 1e-9).sum())
    ax.legend(loc="upper left", bbox_to_anchor=(0, -0.22), frameon=False, fontsize=9, ncol=1)
    fig.suptitle(f"Capitale rimasto in ogni stagione: lo schema fa meglio in {better} stagioni su {n}, "
                 f"peggio in {worse}", color=INK, fontsize=12, x=0.02, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(CAPITAL_PNG, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    stats = _season_stats()
    print(stats.to_string(index=False))
    plot_aging(stats)
    plot_capital()


if __name__ == "__main__":
    main()
