"""Script: le figure dei risultati della nuova tesi (thesis/TESI_kellybench.md).

Tre agenti, tutti con la puntata del Kelly pieno: Kelly pieno senza ricalibrazione, ricalibrazione con la
ristima a pesi uguali, ricalibrazione con la ristima recente (us_c46).

- tesi_kb_2018_19.png, tesi_kb_2016_17.png, tesi_kb_2020_21.png: una stagione giorno per giorno (statistica
  dell'allarme divisa per la soglia del modello in uso, i parametri K, h e ν del modello in uso, giorni
  delle ristime, capitale dei tre agenti);
- tesi_kb_stagioni.png: capitale finale delle 21 stagioni per i tre agenti;
- tesi_kb_popolazione.png: le quote della popolazione a inizio stagione (us_c43).

Legge results/us_c46_strong_refit_seasons.csv, us_c46_strong_refit_refits.csv, us_c42_rolling_seasons.csv
(K, h e ν del modello iniziale), results/raw/us_c46/*.npz e us_c43_population_shares.csv.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

REPO = Path(__file__).resolve().parents[1]
RES = REPO / "results"
RAW = RES / "raw" / "us_c46"
FIG = REPO / "thesis" / "figures"
SURFACE, INK, INK_2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
KELLY, EQUAL, RECENT = "#2a78d6", "#7a4fb5", "#eb6834"
STRUCTURAL, DATA_ERROR = "#c8443b", "#e0b330"  # diagnosi del ricalibratore: errore strutturale, errore nei dati
MONTHS = ("gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic")
AGENTS = (("kelly", "Kelly pieno senza ricalibrazione", KELLY),
          ("uguale", "ricalibrazione, rivalutazione a pesi uguali", EQUAL),
          ("recente", "ricalibrazione, rivalutazione recente", RECENT))


def _style(ax, grid="y"):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=INK_2, labelsize=9)
    if grid:
        ax.grid(axis=grid, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def _alarm_days(ax, days, end, mask, color, alpha) -> None:
    """Una fascia per ogni giornata di allarme, dal giorno della decisione al successivo (anche se isolata)."""
    for i in np.flatnonzero(mask):
        ax.axvspan(days[i], days[i + 1] if i + 1 < len(days) else end, color=color, alpha=alpha, lw=0, zorder=0.5)


def season_detail(season: str, png: Path) -> None:
    u = np.load(RAW / f"uguale_{season}.npz")
    r = np.load(RAW / f"recente_{season}.npz")
    days = pd.to_datetime(np.unique(u["dates"]))
    refits = pd.read_csv(RES / "us_c46_strong_refit_refits.csv")
    refits = refits[refits["season"] == season]
    initial = pd.read_csv(RES / "us_c42_rolling_seasons.csv").set_index("season").loc[season]
    start = days[0] - pd.Timedelta(days=1)
    end = days[-1] + pd.Timedelta(days=3)
    fig, axes = plt.subplots(5, 1, figsize=(9, 12), sharex=True, facecolor=SURFACE,
                             gridspec_kw={"height_ratios": [1.1, 0.55, 0.55, 0.55, 1.3]})
    alarm, bottom = axes[0], axes[-1]
    params = dict(zip(("k", "h", "nu"), axes[1:4]))
    for ax in axes:
        _style(ax)
    # Allarme: la più alta delle due statistiche (media, dispersione) divisa per la sua soglia, per il modello in
    # uso da ciascun agente; sopra 1 scatta l'allarme. Il Kelly pieno tiene sempre il modello di inizio stagione.
    alarm.axhline(1.0, color=INK, lw=1.0)
    alarm.text(end, 1.0, " soglia", color=INK, fontsize=8.5, va="center", ha="left")
    peak = 0.0
    for key, _, color in AGENTS:
        ratios = u["ratios0"] if key == "kelly" else (u["ratios"] if key == "uguale" else r["ratios"])
        a = np.asarray(ratios, dtype=float)
        m = np.fmax(a[:, 0], a[:, 1])  # NaN prima della 40ª partita
        peak = max(peak, float(np.nanmax(m)))
        alarm.plot(days, m, color=color, lw=2.0 if key == "recente" else 1.4,
                   ls=(0, (4, 2)) if key == "kelly" else "-", drawstyle="steps-post")
        if key != "kelly":  # giornate di allarme colorate secondo la diagnosi del ricalibratore
            d = np.asarray((u if key == "uguale" else r)["diag"]).astype(str)
            for kind, shade in (("structural", STRUCTURAL), ("compositional", DATA_ERROR)):
                _alarm_days(alarm, days, end, d == kind, shade, 0.22)
    alarm.set_ylim(0, max(1.6, peak * 1.08))
    alarm.set_ylabel("Statistica / soglia\n(la più alta delle due)", color=INK_2, fontsize=9)
    alarm.set_title(season, color=INK, fontsize=10, loc="left")
    # I tre parametri del modello in uso: il Kelly pieno tiene quelli di inizio stagione (tratteggio)
    labels = {"k": "K\n(velocità)", "h": "h\n(campo, punti Elo)", "nu": "ν\n(pareggi)"}
    for name, ax in params.items():
        ax.hlines(float(initial[name]), start, end, color=KELLY, lw=1.2, ls=(0, (4, 2)))
        ax.set_ylabel(labels[name], color=INK_2, fontsize=9)
    for version, color in (("uguale", EQUAL), ("recente", RECENT)):
        g = refits[refits["version"] == version].sort_values("day")
        for name, ax in params.items():
            xs, ys = [start], [float(initial[name])]
            for _, row in g.iterrows():
                d = days[int(row["day"]) - 1]
                xs += [d, d]
                ys += [ys[-1], float(row[name])]
            xs.append(end)
            ys.append(ys[-1])
            ax.plot(xs, ys, color=color, lw=2.0 if version == "recente" else 1.4)
        for _, row in g.iterrows():
            for ax in axes:
                ax.axvline(days[int(row["day"]) - 1], color=color, lw=0.8, ls=":")
    for key, label, color in AGENTS:
        w = u["wealth_full"] if key == "kelly" else (u["wealth"] if key == "uguale" else r["wealth"])
        bottom.plot([start] + list(days), 100 * np.asarray(w), color=color, label=label,
                    lw=2.2 if key == "recente" else 1.4, ls=(0, (4, 2)) if key == "kelly" else "-")
    bottom.set_yscale("log")
    lo, hi = bottom.get_ylim()  # tacche in percentuale, ogni fattore 3 circa, come nella figura delle stagioni
    bottom.yaxis.set_major_locator(matplotlib.ticker.FixedLocator(
        [v for v in (m * 10.0 ** e for e in range(-6, 3) for m in (1, 3)) if lo <= v <= hi]))
    bottom.yaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    bottom.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",") + "%"))
    bottom.set_ylabel("Capitale (% dell'iniziale)", color=INK_2, fontsize=9)
    bottom.set_xlim(start, end)
    bottom.xaxis.set_major_locator(mdates.MonthLocator())
    bottom.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: MONTHS[mdates.num2date(v).month - 1]))
    bottom.set_xlabel("Data delle partite (le linee punteggiate sono le rivalutazioni)", color=INK_2, fontsize=9)
    h, l = bottom.get_legend_handles_labels()
    h += [Patch(color=STRUCTURAL, alpha=0.3, lw=0), Patch(color=DATA_ERROR, alpha=0.3, lw=0),
          Line2D([], [], color=INK_2, lw=0.9, ls=":")]
    l += ["allarme con errore strutturale", "allarme con errore nei dati", "rivalutazione del modello"]
    fig.legend(h, l, loc="lower center", ncol=3, frameon=False, fontsize=8.5)
    fig.tight_layout(rect=(0, 0.075, 1, 1))
    fig.savefig(png, dpi=200, facecolor=SURFACE)
    plt.close(fig)


def seasons_overview(png: Path) -> None:
    d = pd.read_csv(RES / "us_c46_strong_refit_seasons.csv")
    u = d[d["version"] == "uguale"].set_index("season")
    r = d[d["version"] == "recente"].set_index("season")
    x = np.arange(len(u))
    fig, ax = plt.subplots(figsize=(10, 5.2), facecolor=SURFACE)
    _style(ax)
    off = 0.22
    ax.scatter(x - off, 100 * u["full_kelly"], color=KELLY, s=26, zorder=3, label=AGENTS[0][1])
    ax.scatter(x, 100 * u["final_capital"], color=EQUAL, marker="s", s=22, zorder=3, label=AGENTS[1][1])
    ax.scatter(x + off, 100 * r["final_capital"], color=RECENT, marker="D", s=24, zorder=4, label=AGENTS[2][1])
    for xi in x[::2]:  # colonne alternate, una stagione sì e una no, solo per la lettura
        ax.axvspan(xi - 0.5, xi + 0.5, color="#efeee9", lw=0, zorder=0)
    ax.set_xlim(x[0] - 0.5, x[-1] + 0.5)
    ax.set_yscale("log")
    ax.set_ylim(2e-4, 250)
    # Tacche ogni fattore 3 circa (1, 3, 10, 30…), invece che ogni fattore 10
    ticks = [m * 10.0 ** e for e in range(-4, 3) for m in (1, 3)] + [100]
    ticks = [v for v in ticks if 2e-4 <= v <= 250]
    ax.yaxis.set_major_locator(matplotlib.ticker.FixedLocator(ticks))
    ax.yaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",") + "%"))
    # Capitale iniziale e soglia della rovina: sotto la puntata minima di £0,01 su £220 non si può più puntare
    ruin = 100 * 0.01 / 220
    ax.axhline(100, color=INK_2, lw=0.8)
    ax.text(x[-1] + 0.4, 100 * 1.15, "capitale iniziale", ha="right", va="bottom", fontsize=8, color=INK_2)
    ax.axhline(ruin, color="#b8322a", lw=1.1, ls=(0, (5, 3)))
    ax.text(x[0] - 0.4, ruin * 1.15, "rovina: sotto la puntata minima di £0,01", ha="left", va="bottom",
            fontsize=8, color="#b8322a")
    for xs, vals, color in ((x - off, u["full_kelly"], KELLY), (x, u["final_capital"], EQUAL),
                            (x + off, r["final_capital"], RECENT)):
        for xi, v in zip(xs, 100 * vals):
            if v < 1.2e-4:
                ax.annotate("", xy=(xi, 1.05e-4), xytext=(xi, 3e-4),
                            arrowprops={"arrowstyle": "-|>", "color": color, "lw": 1.4})
    ax.set_xticks(x)
    ax.set_xticklabels(u.index, rotation=60, fontsize=8)
    ax.set_ylabel("Capitale finale (% del capitale iniziale)", color=INK_2, fontsize=9)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.02), frameon=False, fontsize=8.5, ncol=3)
    fig.tight_layout()
    fig.savefig(png, dpi=200, facecolor=SURFACE)
    plt.close(fig)


RUIN = 100 * 0.01 / 220  # rovina: capitale sotto la puntata minima di £0,01 su £220, in % dell'iniziale
COLUMN = "#efeee9"
PCT = plt.FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",") + "%")


def _month_columns(ax, start, end) -> None:
    """Colonne alternate, un mese sì e uno no, solo per la lettura."""
    m, i = pd.Timestamp(start).to_period("M").to_timestamp(), 0
    while m < end:
        nxt = m + pd.offsets.MonthBegin(1)
        if i % 2 == 0:
            ax.axvspan(max(m, start), min(nxt, end), color=COLUMN, lw=0, zorder=0)
        m, i = nxt, i + 1


def _pct_log_axis(ax, lo: float, hi: float) -> None:
    """Scala logaritmica in percentuale, con tacche ogni fattore 3 circa (…, 1%, 3%, 10%, 30%, 100%)."""
    ax.set_yscale("log")
    ax.set_ylim(lo, hi)
    ax.yaxis.set_major_locator(matplotlib.ticker.FixedLocator(
        [v for v in (m * 10.0 ** e for e in range(-6, 3) for m in (1, 3)) if lo <= v <= hi]))
    ax.yaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.yaxis.set_major_formatter(PCT)


def _month_axis(ax, start, end) -> None:
    ax.set_xlim(start, end)
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonthday=15))
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: MONTHS[mdates.num2date(v).month - 1]))
    ax.tick_params(axis="x", length=0)


def _agents(season: str) -> tuple[pd.DatetimeIndex, list[dict]]:
    """Per ciascun agente: statistiche dell'allarme, diagnosi, parametri, capitale e giorni delle ristime."""
    u = np.load(RAW / f"uguale_{season}.npz")
    r = np.load(RAW / f"recente_{season}.npz")
    days = pd.to_datetime(np.unique(u["dates"]))
    refits = pd.read_csv(RES / "us_c46_strong_refit_refits.csv")
    refits = refits[refits["season"] == season]
    init = pd.read_csv(RES / "us_c42_rolling_seasons.csv").set_index("season").loc[season]
    out = []
    for key, label, color in AGENTS:
        z = u if key in ("kelly", "uguale") else r
        g = refits[refits["version"] == key].sort_values("day") if key != "kelly" else refits.iloc[0:0]
        out.append({"key": key, "label": label, "color": color,
                    "ratios": np.asarray(z["ratios0"] if key == "kelly" else z["ratios"], dtype=float),
                    "diag": np.asarray(z["diag0"] if key == "kelly" else z["diag"]).astype(str),
                    "wealth": 100 * np.asarray(z["wealth_full"] if key == "kelly" else z["wealth"]),
                    "refit_days": [days[int(d) - 1] for d in g["day"]],
                    "params": {n: [float(init[n])] + [float(v) for v in g[n]] for n in ("k", "h", "nu")}})
    return days, out


def agent_detail(season: str, agent: dict, days: pd.DatetimeIndex, png: Path) -> None:
    """Una stagione vista da un solo agente: allarme, K, h, ν e capitale."""
    start, end = days[0] - pd.Timedelta(days=1), days[-1] + pd.Timedelta(days=3)
    color = agent["color"]
    fig, axes = plt.subplots(5, 1, figsize=(9, 11), sharex=True, facecolor=SURFACE,
                             gridspec_kw={"height_ratios": [1.2, 0.5, 0.5, 0.5, 1.3]})
    for ax in axes:
        _style(ax)
        _month_columns(ax, start, end)
    alarm, cap = axes[0], axes[-1]
    # Allarme: le due statistiche divise per la loro soglia; le fasce sono i giorni di allarme, per diagnosi
    a = agent["ratios"]
    alarm.plot(days, a[:, 0], color=color, lw=1.6, drawstyle="steps-post")
    alarm.plot(days, a[:, 1], color=color, lw=1.1, ls=(0, (3, 2)), alpha=0.8, drawstyle="steps-post")
    alarm.axhline(1.0, color=INK, lw=1.0)
    alarm.text(end, 1.0, " soglia", color=INK, fontsize=8.5, va="center", ha="left")
    for kind, shade in (("structural", STRUCTURAL), ("compositional", DATA_ERROR)):
        _alarm_days(alarm, days, end, agent["diag"] == kind, shade, 0.3)
    alarm.set_ylim(0, max(1.6, float(np.nanmax(a)) * 1.08))
    alarm.set_ylabel("Statistica / soglia", color=INK_2, fontsize=9)
    alarm.set_title(f"{season}: {agent['label']}", color=INK, fontsize=10, loc="left")
    # Parametri del modello in uso
    labels = {"k": "K\n(velocità)", "h": "h\n(campo,\npunti Elo)", "nu": "ν\n(pareggi)"}
    for ax, name in zip(axes[1:4], ("k", "h", "nu")):
        vals = agent["params"][name]
        xs, ys = [start], [vals[0]]
        for d, v in zip(agent["refit_days"], vals[1:]):
            xs += [d, d]
            ys += [ys[-1], v]
        xs.append(end)
        ys.append(ys[-1])
        ax.plot(xs, ys, color=color, lw=1.8, ls=(0, (4, 2)) if agent["key"] == "kelly" else "-")
        ax.set_ylabel(labels[name], color=INK_2, fontsize=8.5)
        ax.margins(y=0.25)
    # Capitale, con la soglia della rovina
    w = agent["wealth"]
    cap.plot([start] + list(days), w, color=color, lw=1.8)
    cap.axhline(RUIN, color=STRUCTURAL, lw=1.0, ls=(0, (5, 3)))
    cap.text(start, RUIN * 1.2, " rovina: sotto la puntata minima di £0,01", color=STRUCTURAL, fontsize=8,
             va="bottom", ha="left")
    _pct_log_axis(cap, min(float(np.min(w)), RUIN) / 3, max(float(np.max(w)), 100) * 2)
    cap.set_ylabel("Capitale\n(% dell'iniziale)", color=INK_2, fontsize=9)
    for d in agent["refit_days"]:
        for ax in axes:
            ax.axvline(d, color=INK, lw=0.9, ls=":")
    _month_axis(cap, start, end)
    handles = [Line2D([], [], color=color, lw=1.6), Line2D([], [], color=color, lw=1.1, ls=(0, (3, 2))),
               Patch(color=STRUCTURAL, alpha=0.35, lw=0), Patch(color=DATA_ERROR, alpha=0.35, lw=0),
               Line2D([], [], color=INK, lw=0.9, ls=":"), Line2D([], [], color=STRUCTURAL, lw=1.0, ls=(0, (5, 3)))]
    names = ["statistica della media / soglia", "statistica della dispersione / soglia",
             "allarme con errore strutturale", "allarme con errore nei dati", "rivalutazione del modello",
             "soglia della rovina"]
    fig.legend(handles, names, loc="lower center", ncol=3, frameon=False, fontsize=8.5)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(png, dpi=200, facecolor=SURFACE)
    plt.close(fig)


def agents_compared(season: str, days: pd.DatetimeIndex, agents: list[dict], png: Path) -> None:
    """I tre agenti a confronto: linea del tempo degli allarmi di ciascuno, con le ristime, e capitale."""
    start, end = days[0] - pd.Timedelta(days=1), days[-1] + pd.Timedelta(days=3)
    # stesse proporzioni delle figure di un solo agente, così occupa tutta la pagina
    fig, (line, cap) = plt.subplots(2, 1, figsize=(9, 11), sharex=True, facecolor=SURFACE,
                                    gridspec_kw={"height_ratios": [1, 2.6]})
    _style(line, grid="")
    _style(cap)
    for ax in (line, cap):
        _month_columns(ax, start, end)
    # Una riga per agente: una barra per ogni giornata di allarme, un triangolo per ogni ristima
    nxt = list(days[1:]) + [end]
    for row, ag in zip((2, 1, 0), agents):
        spans = [(mdates.date2num(days[i]), mdates.date2num(nxt[i]) - mdates.date2num(days[i]))
                 for i in np.flatnonzero(ag["diag"] != "none")]
        line.broken_barh(spans, (row - 0.3, 0.6), facecolors=ag["color"],
                         alpha=0.45 if ag["key"] == "kelly" else 1.0, zorder=2)
        line.axhline(row, color=GRID, lw=0.8, zorder=1)
        for d in ag["refit_days"]:
            line.plot(d, row + 0.42, marker="v", color=INK, ms=6, zorder=3)
        n_alarm, n_refit = len(spans), len(ag["refit_days"])
        line.text(end, row, f"  {n_alarm} giornate" + (f", {n_refit} rivalutazioni" if ag["key"] != "kelly" else ""),
                  va="center", ha="left", fontsize=8, color=INK_2)
    line.set_yticks([2, 1, 0])
    line.set_yticklabels(["Kelly pieno", "pesi uguali", "rivalutazione recente"], fontsize=8.5)
    line.set_ylim(-0.7, 2.8)
    line.tick_params(axis="y", length=0)
    line.set_title(f"{season}: i tre agenti a confronto. Giornate di allarme (barre) e rivalutazioni (▼)",
                   color=INK, fontsize=10, loc="left")
    lo = min(min(float(np.min(ag["wealth"])) for ag in agents), RUIN) / 3
    hi = max(max(float(np.max(ag["wealth"])) for ag in agents), 100) * 2
    for ag in agents:
        cap.plot([start] + list(days), ag["wealth"], color=ag["color"], label=ag["label"],
                 lw=2.0 if ag["key"] == "recente" else 1.4, ls=(0, (4, 2)) if ag["key"] == "kelly" else "-")
        for d in ag["refit_days"]:
            cap.axvline(d, color=ag["color"], lw=0.9, ls=":")
    cap.axhline(RUIN, color=STRUCTURAL, lw=1.0, ls=(0, (5, 3)))
    cap.text(start, RUIN * 1.2, " rovina: sotto la puntata minima di £0,01", color=STRUCTURAL, fontsize=8,
             va="bottom", ha="left")
    _pct_log_axis(cap, lo, hi)
    cap.set_ylabel("Capitale (% dell'iniziale)", color=INK_2, fontsize=9)
    _month_axis(cap, start, end)
    h, l = cap.get_legend_handles_labels()
    h.append(Line2D([], [], color=INK_2, lw=0.9, ls=":"))
    l.append("rivalutazione (nel colore dell'agente)")
    fig.legend(h, l, loc="lower center", ncol=2, frameon=False, fontsize=8.5)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(png, dpi=200, facecolor=SURFACE)
    plt.close(fig)


def season_agents(season: str) -> None:
    days, agents = _agents(season)
    tag = season.replace("-", "_")
    for ag in agents:
        agent_detail(season, ag, days, FIG / f"tesi_kb_{tag}_{ag['key']}.png")
    agents_compared(season, days, agents, FIG / f"tesi_kb_{tag}_confronto.png")


def population(png: Path) -> None:
    sh = pd.read_csv(RES / "us_c43_population_shares.csv")
    labels = {"kelly_pieno": ("Kelly pieno", KELLY), "ristima_uguale": ("Rivalutazione a pesi uguali", EQUAL),
              "ristima_recente": ("Rivalutazione recente", RECENT), "cassa": ("Cassa", "#008300")}
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2), sharey=True, facecolor=SURFACE)
    titles = {"generazioni_solo_kelly": "I tre agenti che puntano il Kelly pieno",
              "generazioni_cassa": "Con la cassa"}
    for ax, version in zip(axes, titles):
        p = sh[sh["version"] == version].pivot(index="season", columns="agent", values="start_share").sort_index()
        last = sh[(sh["version"] == version) & (sh["season"] == p.index[-1])].set_index("agent")["end_share"]
        cols = [c for c in labels if c in p.columns]
        seasons = list(p.index) + ["fine"]
        x = np.arange(len(seasons))
        vals = [100 * np.append(p[c].to_numpy(), last[c]) for c in cols]
        _style(ax, grid="")
        ax.stackplot(x, *vals, colors=[labels[c][1] for c in cols], edgecolor=SURFACE, linewidth=1.0)
        ax.set_xlim(0, x[-1])
        ax.set_ylim(0, 100)
        ax.set_xticks(x)
        ax.set_xticklabels(seasons, rotation=70, fontsize=7.5)
        ax.set_title(titles[version], color=INK, fontsize=10, loc="left")
    axes[0].set_ylabel("Quota del capitale a inizio stagione (%)", color=INK_2, fontsize=9)
    handles = [Patch(color=labels[c][1], label=labels[c][0]) for c in labels]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=9)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(png, dpi=200, facecolor=SURFACE)
    plt.close(fig)


if __name__ == "__main__":
    for s in ("2018-19", "2016-17", "2020-21"):
        season_detail(s, FIG / f"tesi_kb_{s.replace('-', '_')}.png")
    for s in ("2020-21", "2016-17"):  # i due casi del §5.3, agente per agente, più il confronto
        season_agents(s)
    seasons_overview(FIG / "tesi_kb_stagioni.png")
    population(FIG / "tesi_kb_popolazione.png")
    print("ok")
