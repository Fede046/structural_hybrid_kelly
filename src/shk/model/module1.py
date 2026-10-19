"""Identificatori del Modulo 1 e suffissi dei risultati.

Il Flusso 1 (dati, schema dei fit, previsioni, residui) accetta il Modulo 1 come parametro:
"elo" (ELO_FITS) oppure "dixon_coles" (DC_FITS). I risultati con
Dixon-Coles si scrivono con il suffisso "_dc" prima dell'estensione, senza sovrascrivere
quelli Elo, che restano con i nomi di sempre.
"""

from collections.abc import Sequence
from pathlib import Path
from typing import Final

MODULE1_ELO: Final[str] = "elo"
MODULE1_DIXON_COLES: Final[str] = "dixon_coles"
MODULE1_IDS: Final[tuple[str, ...]] = (MODULE1_ELO, MODULE1_DIXON_COLES)
MODULE1_SUFFIXES: Final[dict[str, str]] = {MODULE1_ELO: "", MODULE1_DIXON_COLES: "_dc"}
MODULE1_OPTION: Final[str] = "--module1"


def check_module1(module1: str) -> str:
    """Restituisce l'identificatore se valido, altrimenti solleva ValueError."""
    if module1 not in MODULE1_IDS:
        raise ValueError(f"Unknown Module 1 '{module1}', expected one of {MODULE1_IDS}")
    return module1


def module1_suffix(module1: str) -> str:
    """Suffisso dei risultati: vuoto per l'Elo, "_dc" per Dixon-Coles."""
    return MODULE1_SUFFIXES[check_module1(module1)]


def with_module1_suffix(path: Path | str, module1: str) -> Path:
    """Percorso con il suffisso del Modulo 1 prima dell'estensione (invariato per l'Elo)."""
    p = Path(path)
    return p.with_name(p.stem + module1_suffix(module1) + p.suffix)


def module1_from_argv(argv: Sequence[str]) -> str:
    """Modulo 1 dagli argomenti di uno script ("--module1 <id>"); "elo" se l'opzione manca."""
    args = list(argv)
    if MODULE1_OPTION not in args:
        return MODULE1_ELO
    i = args.index(MODULE1_OPTION)
    if i + 1 >= len(args):
        raise ValueError(f"{MODULE1_OPTION} requires a value, one of {MODULE1_IDS}")
    return check_module1(args[i + 1])
