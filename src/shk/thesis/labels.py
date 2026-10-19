"""Etichette in italiano di agenti, configurazioni, confronti, metriche, metodi e serie (T65).

Ogni etichetta ha tre forme: LaTeX (tabelle), testo semplice (CSV gemelli) e mathtext
(figure di matplotlib). Gli identificativi sono quelli dei CSV di results/.
"""

from typing import Final, NamedTuple


class Label(NamedTuple):
    """Etichetta nelle tre forme."""

    latex: str
    plain: str
    figure: str


def _same(text: str) -> Label:
    return Label(text, text, text)


AGENTS: Final[dict[str, Label]] = {
    "A": _same("A"),
    "B_0.25": Label(r"B\textsubscript{0,25}", "B_0.25", r"B$_{0,25}$"),
    "B_0.10": Label(r"B\textsubscript{0,10}", "B_0.10", r"B$_{0,10}$"),
    "C0": _same("C0"),
    "C1": _same("C1"),
    "C2_global": Label(r"C2\textsubscript{global}", "C2_global", r"C2$_{\mathrm{global}}$"),
    "C2": _same("C2"),
    "D_ADWIN": Label(r"D\textsubscript{ADWIN}", "D_ADWIN", r"D$_{\mathrm{ADWIN}}$"),
    "D_PH": Label(r"D\textsubscript{PH}", "D_PH", r"D$_{\mathrm{PH}}$"),
    "E": _same("E"),
}

CONFIGS: Final[dict[str, Label]] = {
    "none": Label(r"senza floor ($F = 0$)", "F = 0", r"senza floor ($F = 0$)"),
    "gbp_0.01": Label(r"\pounds{}0,01", "£0.01", "£0,01"),
    "gbp_1": Label(r"\pounds{}1", "£1", "£1"),
}

METRICS: Final[dict[str, Label]] = {
    "final_log_wealth": Label("log-ricchezza finale", "log-ricchezza finale", "log-ricchezza finale"),
    "max_drawdown": Label("drawdown massimo", "drawdown massimo", "drawdown massimo"),
    "recovery_time": Label("tempo di recupero", "tempo di recupero", "tempo di recupero"),
    "g_ce_1": Label(r"$g_{\mathrm{CE}}$, $\gamma = 1$", "g_CE (gamma = 1)", r"$g_{\mathrm{CE}}$, $\gamma = 1$"),
    "g_ce_2": Label(r"$g_{\mathrm{CE}}$, $\gamma = 2$", "g_CE (gamma = 2)", r"$g_{\mathrm{CE}}$, $\gamma = 2$"),
    "g_ce_5": Label(r"$g_{\mathrm{CE}}$, $\gamma = 5$", "g_CE (gamma = 5)", r"$g_{\mathrm{CE}}$, $\gamma = 5$"),
    "ruin_rate": Label("tasso di rovina", "tasso di rovina", "tasso di rovina"),
    "sd_log_wealth": Label(r"SD di $\ln W_T$", "SD di ln W_T", r"SD di $\ln W_T$"),
}

METHODS: Final[dict[str, Label]] = {
    "proportional": _same("proporzionale"),
    "additive": _same("additivo"),
    "power": _same("power"),
    "shin": _same("Shin"),
    "odds_ratio": _same("odds ratio"),
}

SERIES: Final[dict[str, Label]] = {
    "b365_prematch": _same("B365 pre-partita"),
    "pinnacle_closing": _same("Pinnacle chiusura"),
}

MODELS: Final[dict[str, Label]] = {
    "elo": _same("Elo"),
    "dixon_coles": _same("Dixon-Coles"),
}


def comparison(code: str) -> Label:
    """Etichetta di un confronto "X-Y" (differenza X − Y)."""
    left, _, right = code.partition("-")
    a, b = AGENTS[left], AGENTS[right]
    return Label(f"{a.latex} $-$ {b.latex}", code, f"{a.figure} − {b.figure}")
