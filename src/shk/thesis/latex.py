"""Tabelle LaTeX con booktabs e loro gemelle CSV.

Una tabella è un elenco di colonne e di righe di celle. Ogni cella ha:
- la resa LaTeX, con la virgola decimale (DECIMAL_MARK) e le etichette in italiano;
- uno o più valori per il CSV gemello, a piena precisione e col punto decimale. Un intervallo
  occupa due colonne del CSV, il limite inferiore e quello superiore.
Le colonne marcate group mostrano il valore in LaTeX solo quando cambia, preceduto da un
\\midrule; nel CSV il valore si ripete su ogni riga.

La resa non calcola nulla: formatta i valori letti dai CSV versionati.
"""

import csv
import io
import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from shk.thesis.sources import VersionedCsv

DECIMAL_MARK: Final[str] = ","
GENERATED_BY: Final[str] = "scripts/build_thesis_tables.py"
SHORT_SHA: Final[int] = 12

_LATEX_SPECIAL: Final[dict[str, str]] = {
    "\\": r"\textbackslash{}", "_": r"\_", "%": r"\%", "&": r"\&", "#": r"\#",
    "$": r"\$", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
}


def latex_escape(text: str) -> str:
    """Testo con i caratteri speciali di LaTeX protetti."""
    return "".join(_LATEX_SPECIAL.get(ch, ch) for ch in text)


def is_missing(value: object) -> bool:
    """Vero per None, NaN e stringa vuota."""
    if value is None:
        return True
    if isinstance(value, float):
        return math.isnan(value)
    return isinstance(value, str) and value == ""


def format_number(value: float, decimals: int, signed: bool = False) -> str:
    """Numero in LaTeX con la virgola decimale; "---" se manca.

    Il segno meno è $-$; con signed=True i positivi hanno $+$. Gli interi da 10 000 in su hanno
    il separatore delle migliaia \\, (spazio fine).
    """
    if is_missing(value):
        return "---"
    x = float(value)
    text = f"{abs(x):,.{decimals}f}".replace(",", " ").replace(".", DECIMAL_MARK)
    integer, _, fraction = text.partition(DECIMAL_MARK)
    if len(integer.replace(" ", "")) < 5:
        integer = integer.replace(" ", "")
    text = integer.replace(" ", r"\,") + (DECIMAL_MARK + fraction if fraction else "")
    rounded_zero = float(f"{abs(x):.{decimals}f}") == 0.0
    if x < 0 and not rounded_zero:
        return "$-$" + text
    if signed and x > 0 and not rounded_zero:
        return "$+$" + text
    return text


def csv_value(value: object) -> str:
    """Valore per il CSV gemello: float a piena precisione (repr), stringa vuota se manca."""
    if is_missing(value):
        return ""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        x = float(value)
        return str(int(x)) if x.is_integer() and abs(x) < 1e15 else repr(x)
    return str(value)


@dataclass(frozen=True)
class Cell:
    """Cella: resa LaTeX e valori del CSV gemello."""

    latex: str
    csv: tuple[str, ...]


def num(value: object, decimals: int, signed: bool = False) -> Cell:
    """Cella numerica."""
    return Cell(format_number(value, decimals, signed), (csv_value(value),))


def integer(value: object) -> Cell:
    """Cella intera (conteggi)."""
    return num(value, 0)


def text(latex: str, plain: str | None = None) -> Cell:
    """Cella di testo: plain è il testo del CSV (di default quello LaTeX)."""
    return Cell(latex, (latex if plain is None else plain,))


def interval(low: object, high: object, decimals: int) -> Cell:
    """Intervallo "[a; b]" in LaTeX, due valori nel CSV."""
    if is_missing(low) and is_missing(high):
        latex = "---"
    else:
        latex = f"[{format_number(low, decimals)}; {format_number(high, decimals)}]"
    return Cell(latex, (csv_value(low), csv_value(high)))


@dataclass(frozen=True)
class Column:
    """Colonna: intestazione LaTeX, intestazioni del CSV, allineamento e raggruppamento."""

    header: str
    csv_headers: tuple[str, ...]
    align: str = "r"
    group: bool = False


@dataclass(frozen=True)
class ThesisTable:
    """Tabella della tesi, con le fonti e le note."""

    name: str
    caption: str
    columns: tuple[Column, ...]
    rows: tuple[tuple[Cell, ...], ...]
    sources: tuple[VersionedCsv, ...]
    notes: tuple[str, ...] = ()
    header_groups: tuple[tuple[str, int], ...] = ()
    font_size: str = r"\small"
    tabcolsep: str = ""

    def __post_init__(self) -> None:
        for row in self.rows:
            if len(row) != len(self.columns):
                raise ValueError(f"Table {self.name}: row with {len(row)} cells, expected {len(self.columns)}")
            for cell, col in zip(row, self.columns):
                if len(cell.csv) != len(col.csv_headers):
                    raise ValueError(f"Table {self.name}: cell {cell.latex!r} does not fit column {col.header!r}")
        if self.header_groups and sum(span for _, span in self.header_groups) != len(self.columns):
            raise ValueError(f"Table {self.name}: header groups do not cover the columns")

    @property
    def label(self) -> str:
        """Etichetta LaTeX della tabella."""
        return "tab:" + self.name.removeprefix("tab_")


def _source_note(sources: Sequence[VersionedCsv]) -> str:
    parts = [rf"\texttt{{{latex_escape(s.path)}}} (SHA256 \texttt{{{s.sha256[:SHORT_SHA]}}})" for s in sources]
    return ("Fonte: " if len(parts) == 1 else "Fonti: ") + "; ".join(parts) + "."


def render_latex(table: ThesisTable) -> str:
    """Sorgente LaTeX della tabella (ambiente table, tabular con booktabs, note e fonte)."""
    lines = [
        f"% Generato da {GENERATED_BY} dai CSV versionati: non modificare a mano.",
        r"% Richiede \usepackage{booktabs}.",
        r"\begin{table}[htbp]",
        r"\centering",
    ]
    if table.font_size:
        lines.append(table.font_size)
    if table.tabcolsep:
        lines.append(rf"\setlength{{\tabcolsep}}{{{table.tabcolsep}}}")
    lines += [
        rf"\caption{{{table.caption}}}",
        rf"\label{{{table.label}}}",
        r"\begin{tabular}{" + "".join(c.align for c in table.columns) + "}",
        r"\toprule",
    ]
    if table.header_groups:
        cells, rules, start = [], [], 1
        for label, span in table.header_groups:
            if not label:
                cells.extend([""] * span)
            else:
                cells.append(rf"\multicolumn{{{span}}}{{c}}{{{label}}}" if span > 1 else label)
                rules.append(rf"\cmidrule(lr){{{start}-{start + span - 1}}}")
            start += span
        lines.append(" & ".join(cells) + r" \\")
        lines.append(" ".join(rules))
    lines.append(" & ".join(c.header for c in table.columns) + r" \\")
    lines.append(r"\midrule")
    previous: tuple[str, ...] | None = None
    for row in table.rows:
        key = tuple(cell.latex for cell, col in zip(row, table.columns) if col.group)
        if previous is not None and key and key != previous:
            lines.append(r"\midrule")
        shown = []
        for cell, col in zip(row, table.columns):
            shown.append("" if col.group and key == previous else cell.latex)
        lines.append(" & ".join(shown) + r" \\")
        previous = key
    lines += [r"\bottomrule", r"\end{tabular}", "", r"\smallskip", r"\begin{minipage}{\linewidth}", r"\footnotesize"]
    lines += [note + r"\par" for note in table.notes]
    lines += [_source_note(table.sources), r"\end{minipage}", r"\end{table}"]
    return "\n".join(lines) + "\n"


def render_csv(table: ThesisTable) -> str:
    """CSV gemello: le stesse righe e colonne, valori a piena precisione (csv.writer, "\\r\\n")."""
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\r\n")
    writer.writerow([h for c in table.columns for h in c.csv_headers])
    for row in table.rows:
        writer.writerow([v for cell in row for v in cell.csv])
    return out.getvalue()
