"""Figure finali della tesi in PDF vettoriale, dai soli CSV versionati.

Una figura per tema, con lo stesso stile (STYLE): carattere con grazie DejaVu Serif, corpo 9,
tavolozza Okabe-Ito, griglia leggera, virgola decimale sugli assi ed etichette in italiano.
Le figure si costruiscono con matplotlib.figure.Figure, senza pyplot, e contengono solo
elementi vettoriali (nessuna immagine raster). Il PDF non registra la data di creazione,
così due esecuzioni sugli stessi CSV danno lo stesso file.

Come per le tabelle, i valori si leggono e si disegnano: nessun calcolo nuovo.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Final

import matplotlib
from matplotlib.figure import Figure
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator, ScalarFormatter

from shk.market.divergence import REFERENCE_EDGE
from shk.thesis.labels import AGENTS, CONFIGS, METHODS, METRICS, SERIES, comparison
from shk.thesis.sources import REPO_ROOT, read_versioned_csv
from shk.thesis.tables import CONFIG_ORDER, PREMATCH_SOURCES, one, select

GENERATED_BY: Final[str] = "scripts/build_thesis_figures.py"
WIDTH: Final[float] = 6.3
PALETTE: Final[tuple[str, ...]] = (
    "#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#000000", "#F0E442",
)
STYLE: Final[dict[str, object]] = {
    "font.family": "serif",
    "font.serif": ["DejaVu Serif"],
    "mathtext.fontset": "dejavuserif",
    "font.size": 9,
    "axes.titlesize": 9,
    "axes.labelsize": 9,
    "legend.fontsize": 7.5,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linewidth": 0.5,
    "axes.prop_cycle": matplotlib.cycler(color=PALETTE),
    "lines.linewidth": 1.2,
    "lines.markersize": 4,
    "legend.frameon": False,
    "pdf.fonttype": 42,
    "axes.unicode_minus": True,
}


class CommaFormatter(ScalarFormatter):
    """Etichette degli assi con la virgola decimale."""

    def __init__(self) -> None:
        super().__init__(useOffset=False)

    def __call__(self, x: float, pos: int | None = None) -> str:
        return super().__call__(x, pos).replace(".", ",")


def _comma_axes(*axes: object, x: bool = False, y: bool = True) -> None:
    for ax in axes:
        if y:
            ax.yaxis.set_major_formatter(CommaFormatter())
        if x:
            ax.xaxis.set_major_formatter(CommaFormatter())


def _season_short(season: str) -> str:
    return season[2:]


def figure_false_rejection(root: Path | str = REPO_ROOT) -> Figure:
    """Falso rigetto per φ, soglia nominale e calibrata centrata."""
    df = read_versioned_csv("us_c2_anova_autocorrelation", root)
    ref = one(df, 'design == "contiguous_2" and method == "nominal" and phi == 0.0')
    fig = Figure(figsize=(WIDTH, 2.6), layout="constrained")
    ax_a, ax_b = fig.subplots(1, 2, sharey=False)
    for ax in (ax_a, ax_b):
        ax.axhspan(ref.mc_lower_99, ref.mc_upper_99, color="0.85", lw=0, label="intervallo MC al 99%")
    names = {"contiguous_2": "due metà contigue", "contiguous_38": "38 blocchi contigui", "random_2": "due gruppi casuali"}
    for design, name in names.items():
        part = select(df, f'design == "{design}" and method == "nominal"')
        ax_a.plot(part.phi, part.rejection_rate, marker="o", label=name)
    ax_a.set(title="(a) soglia nominale", xlabel=r"$\varphi$", ylabel="tasso di falso rigetto")
    nom = select(df, 'design == "contiguous_2" and method == "nominal"')
    ax_b.plot(nom.phi, nom.rejection_rate, marker="o", color=PALETTE[6], label="nominale")
    for i, length in enumerate((7.0, 20.0, 40.0)):
        part = select(df, f'design == "contiguous_2" and method == "block_bootstrap_centered" and block_length == {length}')
        ax_b.plot(part.phi, part.rejection_rate, marker="s", color=PALETTE[i + 1], label=f"calibrata centrata, L = {int(length)}")
    ax_b.set(title="(b) due metà contigue", xlabel=r"$\varphi$")
    for ax in (ax_a, ax_b):
        ax.legend(loc="upper left")
    _comma_axes(ax_a, ax_b, x=True)
    return fig


def figure_data_window(root: Path | str = REPO_ROOT) -> Figure:
    """Copertura per stagione di risultati e terne 1X2 (piena, parziale, assente)."""
    cov = read_versioned_csv("us_c3_1_data_coverage", root)
    groups = [("results", "risultati")] + [(f"{s}_1x2_prematch", s.upper()) for s in PREMATCH_SOURCES] + [
        ("ps_1x2_closing", "PS chiusura")]
    seasons = list(dict.fromkeys(cov.season.tolist()))
    fig = Figure(figsize=(WIDTH, 3.6), layout="constrained")
    ax = fig.subplots()
    for i, (group, _) in enumerate(groups):
        part = select(cov, f'group_name == "{group}"')
        for _, r in part.iterrows():
            j = seasons.index(r.season)
            color = PALETTE[0] if bool(r.is_complete) else "#A6C8E0"
            ax.broken_barh([(j - 0.45, 0.9)], (i - 0.4, 0.8), facecolors=color, linewidth=0)
    ax.set_yticks(range(len(groups)), [name for _, name in groups])
    ax.set_xticks(range(len(seasons)), [_season_short(s) for s in seasons], rotation=90)
    ax.set_xlim(-0.6, len(seasons) - 0.4)
    ax.set_ylim(len(groups) - 0.5, -0.5)
    ax.grid(False)
    ax.set_xlabel("stagione")
    handles = [Patch(color=PALETTE[0], label="completa"), Patch(color="#A6C8E0", label="parziale")]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncols=2)
    return fig


def figure_devig_divergence(root: Path | str = REPO_ROOT) -> Figure:
    """Spread fra metodi di de-vigging per fascia di quota, con l'edge di riferimento."""
    df = read_versioned_csv("us_c3_2_devig_divergence", root)
    bins = select(df, 'level == "bin"')
    labels = [c.replace(", ", "; ").replace(".", ",").replace("inf", "∞") for c in bins.category]
    x = range(len(labels))
    fig = Figure(figsize=(WIDTH, 2.6), layout="constrained")
    ax_a, ax_b = fig.subplots(1, 2)
    ax_a.bar(x, bins.mean_spread_pts, color=PALETTE[0], label="media")
    ax_a.plot(x, bins.p99_spread_pts, "o", color=PALETTE[1], label="99° percentile")
    ax_a.plot(x, bins.max_spread_pts, "^", color=PALETTE[6], label="massimo")
    ax_a.axhline(100 * REFERENCE_EDGE, color=PALETTE[2], ls="--", lw=1, label="edge di riferimento")
    ax_a.set(title="(a) spread fra i metodi", xlabel="fascia di quota", ylabel="punti percentuali")
    ax_b.bar(x, bins.mean_relative_spread, color=PALETTE[0])
    ax_b.set(title="(b) spread relativo medio", xlabel="fascia di quota", ylabel="rapporto")
    for ax in (ax_a, ax_b):
        ax.set_xticks(list(x), labels, rotation=30)
    ax_a.legend(loc="upper right")
    _comma_axes(ax_a, ax_b)
    return fig


def figure_g_hat(root: Path | str = REPO_ROOT) -> Figure:
    """Ĝ Shin per stagione con gli intervalli, e il valore pooled."""
    df = read_versioned_csv("us_c4_2b_g_hat_inference", root)
    fig = Figure(figsize=(WIDTH, 2.8), layout="constrained")
    ax = fig.subplots()
    seasons = list(dict.fromkeys(select(df, 'row_type == "interval" and series == "b365_prematch" '
                                            'and season != "pooled"').season.tolist()))
    for k, (series, offset) in enumerate((("b365_prematch", -0.15), ("pinnacle_closing", 0.15))):
        part = select(df, f'row_type == "interval" and series == "{series}" and method == "shin" and season != "pooled"')
        x = [seasons.index(s) + offset for s in part.season]
        color = PALETTE[k]
        ax.vlines(x, part.ci_block_low, part.ci_block_high, color=color, lw=1)
        ax.plot(x, part.g_hat, "o", color=color, label=f"{SERIES[series].figure}, per stagione")
        pooled = one(df, f'row_type == "interval" and series == "{series}" and method == "shin" and season == "pooled"')
        ax.axhspan(pooled.ci_block_low, pooled.ci_block_high, color=color, alpha=0.12, lw=0)
        ax.axhline(pooled.g_hat, color=color, ls="--", lw=1, label=f"{SERIES[series].figure}, pooled")
    ax.axhline(0.0, color="0.3", lw=0.8)
    ax.set_xticks(range(len(seasons)), [_season_short(s) for s in seasons], rotation=90)
    ax.set(xlabel="stagione di validazione", ylabel=r"$\hat g$ (nat per partita), Shin")
    ax.legend(loc="lower left", ncols=2)
    _comma_axes(ax)
    return fig


def figure_alarms(root: Path | str = REPO_ROOT) -> Figure:
    """Allarmi per stagione di validazione di Z-test, ADWIN e Page-Hinkley."""
    df = read_versioned_csv("us_c5_2_daily_z_test", root)
    summary = select(df, 'row_type == "summary"')
    seasons = list(dict.fromkeys(summary.season.tolist()))
    methods = (('method == "z_nominal"', "Z nominale"),
               ('method == "z_block_bootstrap" and block_length == 20.0', "Z calibrato, L = 20"),
               ('method == "page_hinkley"', "Page-Hinkley"),
               ('method == "adwin"', "ADWIN"))
    fig = Figure(figsize=(WIDTH, 2.6), layout="constrained")
    ax = fig.subplots()
    width = 0.2
    for k, (query, name) in enumerate(methods):
        part = select(summary, query)
        x = [seasons.index(s) + (k - 1.5) * width for s in part.season]
        ax.bar(x, part.n_alarms, width=width, color=PALETTE[k], label=name)
    expected = one(df, 'row_type == "overall" and method == "z_nominal"').expected_alarms
    ax.axhline(expected, color="0.3", ls="--", lw=1, label="attesi sotto $H_0$")
    ax.set_xticks(range(len(seasons)), [_season_short(s) for s in seasons], rotation=90)
    ax.set(xlabel="stagione di validazione", ylabel="allarmi per stagione")
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncols=5)
    _comma_axes(ax)
    return fig


def figure_floor(root: Path | str = REPO_ROOT) -> Figure:
    """Rovina col floor sul calendario sintetico (sweep di B0/F) e nella configurazione reale."""
    syn = read_versioned_csv("us_c6_3_floor_synthetic", root)
    real = select(read_versioned_csv("us_c6_3_floor_real_config", root), 'row_type == "aggregate"')
    fig = Figure(figsize=(WIDTH, 2.7), layout="constrained")
    ax_a, ax_b = fig.subplots(1, 2)
    sweep = select(syn, 'experiment == "B"').sort_values("initial_ratio", kind="stable")
    for k, horizon in enumerate(dict.fromkeys(sweep.horizon.tolist())):
        part = select(sweep, f"horizon == {horizon}")
        ax_a.plot(part.initial_ratio, part.ruin_rate, marker="o", color=PALETTE[k], label=f"{int(horizon)} date")
    for ratio, name in ((220.0, "£1"), (22000.0, "£0,01")):
        ax_a.axvline(ratio, color="0.5", ls=":", lw=1)
        ax_a.text(ratio, 0.95, f" {name}", transform=ax_a.get_xaxis_transform(), fontsize=7, va="top")
    ax_a.set_xscale("log")
    ax_a.set(title="(a) calendario sintetico", xlabel=r"$B_0/F$", ylabel="tasso di rovina")
    ax_a.legend(loc="center right")
    agents = list(dict.fromkeys(real.agent.tolist()))
    for k, config in enumerate(("gbp_0.01", "gbp_1")):
        part = select(real, f'config == "{config}"')
        x = [agents.index(a) + (k - 0.5) * 0.25 for a in part.agent]
        ax_b.vlines(x, part.ruin_rate_ci_lower, part.ruin_rate_ci_upper, color=PALETTE[k], lw=1.5)
        ax_b.plot(x, part.ruin_rate, "o", color=PALETTE[k], label=CONFIGS[config].figure)
    ax_b.set_xticks(range(len(agents)), [AGENTS[a].figure for a in agents])
    ax_b.set(title="(b) configurazione reale, 19 stagioni", xlabel="agente")
    ax_b.legend(loc="upper right", title="floor")
    _comma_axes(ax_a, ax_b)
    return fig


def figure_heteroskedasticity(root: Path | str = REPO_ROOT) -> Figure:
    """Rigetti sulle 19 stagioni di validazione per statistica e soglia."""
    a = select(read_versioned_csv("us_c6_4_heteroskedasticity", root), 'row_type == "summary"')
    b = read_versioned_csv("us_c6_4b_variance_change", root)
    bs = select(b, 'row_type == "summary"')
    stats = (("bp_joint", "BP congiunto", a, "n_validation_rejections", "bootstrap_"),
             ("bp_time", "BP temporale", a, "n_validation_rejections", "bootstrap_"),
             ("white", "White", a, "n_validation_rejections", "bootstrap_"),
             ("goldfeld_quandt", "Goldfeld-Quandt", bs, "rejections", "mbb_"),
             ("arch_lm", "ARCH-LM", bs, "rejections", "mbb_"),
             ("rolling_log_variance", "log-varianza mobile", bs, "rejections", "mbb_"))
    methods = (("nominal", "nominale"), ("L7", "L = 7"), ("L20", "L = 20"), ("L40", "L = 40"), ("LPW", r"$L_{\mathrm{PW}}$"))
    fig = Figure(figsize=(WIDTH, 2.6), layout="constrained")
    ax = fig.subplots()
    width = 0.16
    for k, (suffix, name) in enumerate(methods):
        xs, ys = [], []
        for i, (stat, _, frame, column, prefix) in enumerate(stats):
            method = suffix if suffix == "nominal" else prefix + suffix
            hit = select(frame, f'statistic == "{stat}" and method == "{method}"')
            if len(hit) == 1:
                xs.append(i + (k - 2) * width)
                ys.append(hit.iloc[0][column])
        ax.bar(xs, ys, width=width, color=PALETTE[k], label=name)
    n_val = one(bs, 'statistic == "arch_lm" and method == "nominal"').n_validation
    ax.axhline(n_val, color="0.3", ls=":", lw=1)
    ax.set_xticks(range(len(stats)), [s[1] for s in stats])
    ax.set(ylabel="rigetti su 19 stagioni")
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncols=5)
    _comma_axes(ax)
    return fig


def figure_module2(root: Path | str = REPO_ROOT) -> Figure:
    """Decomposizione di δ nella sospensione del 2019-20 e quote alle transizioni (W = 80)."""
    df = read_versioned_csv("us_c7_3b_known_scenarios", root)
    covid = select(df, 'scenario == "2_covid" and version == "threefold"')
    trans = select(df, 'scenario == "1_transition" and version == "threefold" and window == 80')
    fig = Figure(figsize=(WIDTH, 2.8), layout="constrained")
    ax_a, ax_b = fig.subplots(1, 2, width_ratios=(1, 2.2))
    comps = (("total", "totale"), ("compositional", "compositiva"), ("structural", "strutturale"),
             ("interaction", "interazione"))
    for i, (quantity, _) in enumerate(comps):
        r = one(covid, f'quantity == "{quantity}"')
        ax_a.vlines(i, r.lower, r.upper, color=PALETTE[0], lw=1.5)
        ax_a.plot(i, r.estimate, "o", color=PALETTE[0])
    ax_a.axhline(0.0, color="0.3", lw=0.8)
    ax_a.set_xticks(range(len(comps)), [c[1] for c in comps], rotation=30)
    ax_a.set(title="(a) sospensione 2019-20", ylabel=r"componente di $\delta$ (nat per partita)")
    pairs = trans[["season_a", "season_b"]].drop_duplicates()
    labels = [f"{_season_short(a)}→{_season_short(b)}" for a, b in zip(pairs.season_a, pairs.season_b)]
    for k, (quantity, name) in enumerate((("compositional_share", "quota compositiva"),
                                          ("structural_share", r"quota strutturale $\pi$"))):
        part = select(trans, f'quantity == "{quantity}"')
        ax_b.plot(range(len(part)), part.estimate, "o-" if k else "s-", color=PALETTE[k + 1], label=name, lw=0.8)
    ax_b.set_xticks(range(len(labels)), labels, rotation=90)
    ax_b.set(title="(b) transizioni fra stagioni, W = 80", ylabel="quota")
    ax_b.legend(loc="upper right")
    _comma_axes(ax_a, ax_b)
    return fig


def _forest(ax: object, rows: list[tuple[str, float, float, float]], offset: float, color: str, label: str) -> None:
    y = [i + offset for i in range(len(rows))]
    ax.hlines(y, [r[2] for r in rows], [r[3] for r in rows], color=color, lw=1.5)
    ax.plot([r[1] for r in rows], y, "o", color=color, label=label)


def figure_comparisons(root: Path | str = REPO_ROOT) -> Figure:
    """Confronti sulla log-ricchezza finale, validazione e test 2023-24, per configurazione."""
    val = select(read_versioned_csv("us_c8_4_comparisons", root), 'row_type == "comparison" and metric == "final_log_wealth"')
    test = select(read_versioned_csv("us_c8_5_test_run", root), 'row_type == "comparison" and metric == "final_log_wealth"')
    fig = Figure(figsize=(WIDTH, 3.0), layout="constrained")
    axes = fig.subplots(1, 2, sharey=True)
    for ax, config in zip(axes, CONFIG_ORDER[:2]):
        v = select(val, f'config == "{config}"')
        codes = v.comparison.tolist()
        rows_v = [(c, r.estimate, r.ci_block_low, r.ci_block_high) for c, (_, r) in zip(codes, v.iterrows())]
        rows_t = []
        for c in codes:
            t = one(test, f'config == "{config}" and comparison == "{c}"')
            rows_t.append((c, t.estimate, t.ci_low, t.ci_high))
        _forest(ax, rows_v, -0.15, PALETTE[0], "validazione")
        _forest(ax, rows_t, 0.15, PALETTE[1], "test 2023-24")
        ax.axvline(0.0, color="0.3", lw=0.8)
        ax.set_yticks(range(len(codes)), [comparison(c).figure for c in codes])
        ax.set(title=f"floor {CONFIGS[config].figure}", xlabel="differenza di log-ricchezza finale")
    axes[0].invert_yaxis()
    axes[0].legend(loc="lower right")
    _comma_axes(*axes, x=True, y=False)
    return fig


def figure_robustness(root: Path | str = REPO_ROOT) -> Figure:
    """Τ_b fra Elo e Dixon-Coles, confronti coi due Moduli 1, ĝ per metodo di de-vigging."""
    rob = read_versioned_csv("us_c9_2_robustness", root)
    dev = read_versioned_csv("us_c9_3_devig_sensitivity", root)
    fig = Figure(figsize=(WIDTH, 7.6), layout="constrained")
    ax_a, ax_b, ax_c = fig.subplots(3, 1, height_ratios=(1, 1.1, 0.9))
    tau = select(rob, 'row_type == "tau" and config == "gbp_0.01"')
    metrics = list(dict.fromkeys(tau.metric.tolist()))
    for k, (dataset, name, offset) in enumerate((("validation", "validazione", -0.12), ("test", "test 2023-24", 0.12))):
        part = select(tau, f'dataset == "{dataset}"')
        x = [metrics.index(m) + offset for m in part.metric]
        ax_a.vlines(x, part.ci_low, part.ci_high, color=PALETTE[k], lw=1.2)
        ax_a.plot(x, part.tau, "o", color=PALETTE[k], label=name)
    ax_a.set_xticks(range(len(metrics)), [METRICS[m].figure for m in metrics], rotation=20, ha="right")
    ax_a.set(title=r"(a) $\tau_b$ fra i ranking con Elo e con Dixon-Coles, floor £0,01", ylabel=r"$\tau_b$")
    ax_a.legend(loc="lower left")
    cmp_ = select(rob, 'row_type == "comparison" and dataset == "validation" and config == "gbp_0.01" '
                       'and metric == "final_log_wealth"')
    codes = cmp_.comparison.tolist()
    _forest(ax_b, [(c, r.estimate_elo, r.ci_low_elo, r.ci_high_elo) for c, (_, r) in zip(codes, cmp_.iterrows())],
            -0.15, PALETTE[0], "Elo")
    _forest(ax_b, [(c, r.estimate_dc, r.ci_low_dc, r.ci_high_dc) for c, (_, r) in zip(codes, cmp_.iterrows())],
            0.15, PALETTE[2], "Dixon-Coles")
    ax_b.axvline(0.0, color="0.3", lw=0.8)
    ax_b.set_yticks(range(len(codes)), [comparison(c).figure for c in codes])
    ax_b.invert_yaxis()
    ax_b.set(title="(b) confronti in validazione, floor £0,01", xlabel="differenza di log-ricchezza finale")
    ax_b.legend(loc="lower right")
    g = select(dev, 'row_type == "g_hat" and (season == "pooled" or season == "2023-24")')
    methods = list(dict.fromkeys(g.method.tolist()))
    series_sets = (("validation", "b365_prematch"), ("validation", "pinnacle_closing"),
                   ("test", "b365_prematch"), ("test", "pinnacle_closing"))
    for k, (dataset, series) in enumerate(series_sets):
        part = select(g, f'dataset == "{dataset}" and series == "{series}"')
        x = [methods.index(m) + (k - 1.5) * 0.15 for m in part.method]
        ax_c.vlines(x, part.ci_low, part.ci_high, color=PALETTE[k], lw=1.2)
        name = f"{SERIES[series].figure}, {'validazione' if dataset == 'validation' else 'test 2023-24'}"
        ax_c.plot(x, part.estimate, "o", color=PALETTE[k], label=name)
    ax_c.axhline(0.0, color="0.3", lw=0.8)
    ax_c.set_xticks(range(len(methods)), [METHODS[m].figure for m in methods])
    ax_c.set(title=r"(c) $\hat g$ per metodo di de-vigging", ylabel=r"$\hat g$ (nat per partita)")
    ax_c.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncols=2)
    _comma_axes(ax_a, ax_c)
    _comma_axes(ax_b, x=True, y=False)
    return fig


FIGURES: Final[dict[str, Callable[..., Figure]]] = {
    "tesi_falso_rigetto": figure_false_rejection,
    "tesi_finestra_dati": figure_data_window,
    "tesi_divergenza_devig": figure_devig_divergence,
    "tesi_g_hat": figure_g_hat,
    "tesi_allarmi": figure_alarms,
    "tesi_floor": figure_floor,
    "tesi_eteroschedasticita": figure_heteroskedasticity,
    "tesi_modulo2": figure_module2,
    "tesi_confronti": figure_comparisons,
    "tesi_robustezza": figure_robustness,
}


def save_figure(name: str, out_dir: Path | str, root: Path | str = REPO_ROOT) -> Path:
    """Costruisce la figura del registro e la salva in out_dir/<name>.pdf, nello stile comune.

    Solleva
    -------
    ValueError
        Se il nome non è nel registro.
    """
    if name not in FIGURES:
        raise ValueError(f"Unknown figure {name!r}, expected one of {sorted(FIGURES)}")
    path = Path(out_dir) / f"{name}.pdf"
    with matplotlib.rc_context(STYLE):
        fig = FIGURES[name](root)
        fig.savefig(path, format="pdf", metadata={"CreationDate": None, "Creator": GENERATED_BY})
    return path
