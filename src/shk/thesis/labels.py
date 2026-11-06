"""Etichette in italiano di agenti, configurazioni, metriche, metodi e serie.

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
}

CONFIGS: Final[dict[str, Label]] = {
    "none": Label(r"senza floor ($F = 0$)", "F = 0", r"senza floor ($F = 0$)"),
    "gbp_0.01": Label(r"\pounds{}0,01", "£0.01", "£0,01"),
    "gbp_1": Label(r"\pounds{}1", "£1", "£1"),
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
