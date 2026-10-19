"""Tabelle e numeri citabili della tesi, dai soli CSV versionati (T65).

Per ogni tabella di shk.thesis.tables.TABLES scrive thesis/tables/<nome>.tex (booktabs, etichette
in italiano, fonte in nota) e thesis/tables/<nome>.csv (la stessa tabella, valori a piena
precisione); poi thesis/numeri.md dalle voci di shk.thesis.numbers.NUMBERS. Legge solo i CSV
elencati in results/MANIFEST.sha256 e non calcola nulla di nuovo.

Uso, dalla radice del repository:
- senza argomenti rigenera tutte le tabelle e thesis/numeri.md;
- con --only NOME (ripetibile) rigenera solo le tabelle indicate;
- con --list scrive l'elenco delle tabelle in build/thesis/tables.txt.
"""

import sys
from pathlib import Path

from shk.thesis.latex import render_csv, render_latex
from shk.thesis.numbers import render_numbers
from shk.thesis.tables import TABLES, build_table

REPO_ROOT = Path(__file__).resolve().parents[1]
TABLES_DIR = REPO_ROOT / "thesis" / "tables"
NUMBERS_PATH = REPO_ROOT / "thesis" / "numeri.md"
LIST_PATH = REPO_ROOT / "build" / "thesis" / "tables.txt"


def write_table(name: str) -> None:
    """Scrive il .tex e il .csv di una tabella del registro."""
    table = build_table(name, REPO_ROOT)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    (TABLES_DIR / f"{name}.tex").write_text(render_latex(table), encoding="utf-8", newline="\n")
    (TABLES_DIR / f"{name}.csv").write_text(render_csv(table), encoding="utf-8", newline="")


def run(argv: list[str]) -> None:
    """Esegue lo script con gli argomenti dati."""
    if "--list" in argv:
        LIST_PATH.parent.mkdir(parents=True, exist_ok=True)
        LIST_PATH.write_text("\n".join(TABLES) + "\n", encoding="utf-8")
        return
    only = [argv[i + 1] for i, a in enumerate(argv) if a == "--only" and i + 1 < len(argv)]
    unknown = sorted(set(only) - set(TABLES))
    if unknown:
        sys.exit(f"Unknown table(s) {unknown}, expected one of {sorted(TABLES)}")
    for name in only or TABLES:
        write_table(name)
    if not only:
        NUMBERS_PATH.write_text(render_numbers(REPO_ROOT), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    run(sys.argv[1:])
