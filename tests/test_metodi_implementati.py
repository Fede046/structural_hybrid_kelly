"""Test: riferimenti al codice e parametri di thesis/metodi_implementati.md.

- Ogni riferimento `shk.modulo:nome` si risolve con un import (nome anche puntato, Classe.metodo).
- Ogni riga "Formula:" ha almeno un riferimento, e almeno uno è a una funzione o classe.
- Ogni parametro `shk.modulo:NOME = valore` coincide con la costante del codice (percorso con
  attributi e chiavi ['…']), oppure, nella forma `shk.modulo:funzione(argomento) = valore`, col
  default dell'argomento; ogni parametro `config/<file>.toml:sezione.chiave = valore` coincide
  con la chiave del file.
- Il documento ha le dodici sezioni del task e l'indice, e i file dell'indice esistono.
Non servono i dati grezzi.
"""

import ast
import importlib
import inspect
import math
import re
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DOC = REPO_ROOT / "thesis" / "metodi_implementati.md"

REF = re.compile(r"`(shk(?:\.\w+)+):([A-Za-z_][\w.]*)`")
CODE_PARAM = re.compile(r"`(shk(?:\.\w+)+):([^`=]+?) = ([^`]+)`")
TOML_PARAM = re.compile(r"`(config/[\w.]+\.toml):([^`=]+?) = ([^`]+)`")
PATH_TOKEN = re.compile(r"\['([^']*)'\]|\.?(\w+)")
DEFAULT_ARG = re.compile(r"^(\w+)\((\w+)\)$")
INDEX_FILE = re.compile(r"\b((?:src|scripts|tests|config|thesis)/[\w./-]+\.\w+|README\.md)\b")

SECTIONS = (
    "## 1. Dati e split",
    "## 2. De-vigging",
    "## 3. Modulo 1 Elo e Dixon-Coles",
    "## 4. ĝ",
    "## 5. Detector e Baseline D",
    "## 6. Ambiente e floor",
    "## 7. Agenti",
    "## 8. Modulo 2",
    "## 9. Modulo 3",
    "## 10. Seed e bootstrap",
    "## 11. Calibrazione e congelamento",
    "## 12. Intervalli",
    "## Indice: aree del progetto e file",
)


def _text() -> str:
    return DOC.read_text(encoding="utf-8")


def resolve(module: str, path: str) -> object:
    """Oggetto indicato da modulo e percorso (attributi puntati e chiavi ['…'])."""
    obj: object = importlib.import_module(module)
    pos = 0
    while pos < len(path):
        m = PATH_TOKEN.match(path, pos)
        if m is None or m.end() == pos:
            raise ValueError(f"Bad path {path!r} at {pos}")
        obj = obj[m.group(1)] if m.group(1) is not None else getattr(obj, m.group(2))
        pos = m.end()
    return obj


def same(a: object, b: object) -> bool:
    """Uguaglianza fra il valore del codice o del file (a) e il letterale del documento (b)."""
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return float(a) == float(b) or (math.isnan(float(a)) and math.isnan(float(b)))
    if isinstance(a, (tuple, list)) and isinstance(b, (tuple, list)):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if isinstance(a, (set, frozenset)) and isinstance(b, (set, frozenset)):
        return set(a) == set(b)
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    return a == b


def test_document_has_sections_and_conventions():
    text = _text()
    for heading in SECTIONS:
        assert heading in text.splitlines(), heading
    assert len(REF.findall(text)) > 100


def test_every_code_reference_resolves():
    refs = sorted(set(REF.findall(_text())))
    unresolved = []
    for module, path in refs:
        try:
            resolve(module, path)
        except (ImportError, AttributeError, KeyError, ValueError) as exc:
            unresolved.append(f"{module}:{path} ({exc})")
    assert unresolved == []


def test_every_formula_line_references_a_function_or_class():
    lines = [ln for ln in _text().splitlines() if ln.lstrip().startswith("- Formula:")]
    assert len(lines) >= 60
    for line in lines:
        refs = REF.findall(line)
        assert refs, line
        assert any(callable(resolve(m, p)) for m, p in refs), line


def test_code_parameters_match_the_code():
    params = CODE_PARAM.findall(_text())
    assert len(params) >= 100
    wrong = []
    for module, path, literal in params:
        expected = ast.literal_eval(literal)
        default = DEFAULT_ARG.match(path)
        if default:
            func = resolve(module, default.group(1))
            actual = inspect.signature(func).parameters[default.group(2)].default
        else:
            actual = resolve(module, path)
        if not same(actual, expected):
            wrong.append(f"{module}:{path} = {literal} (code {actual!r})")
    assert wrong == []


def test_frozen_file_parameters_match_the_files():
    params = TOML_PARAM.findall(_text())
    assert len(params) >= 30
    wrong = []
    for file, path, literal in params:
        data = tomllib.loads((REPO_ROOT / file).read_text(encoding="utf-8"))
        section, _, key = path.partition(".")
        actual = data[section][key] if key else data[section]
        expected = ast.literal_eval(literal)
        if not same(actual, expected):
            wrong.append(f"{file}:{path} = {literal} (file {actual!r})")
    assert wrong == []


def test_index_lists_existing_files_for_every_area():
    text = _text()
    index = text.split("## Indice: aree del progetto e file", 1)[1]
    rows = [ln for ln in index.splitlines() if ln.startswith("| ") and not ln.startswith("| Area")]
    assert len(rows) == 12
    files = INDEX_FILE.findall(index)
    assert len(files) >= 60
    missing = [f for f in files if not (REPO_ROOT / f).is_file()]
    assert missing == []


@pytest.mark.parametrize("bad", ["`shk.market.devig:REFERENCE_EDGE = 0.02`", "`shk.nope:x = 1`"])
def test_unresolvable_parameters_raise(bad):
    module, path, _ = CODE_PARAM.findall(bad)[0]
    with pytest.raises((AttributeError, ImportError)):
        resolve(module, path)


def test_same_detects_different_values():
    assert not same(0.02, ast.literal_eval("0.03"))
    assert not same((7, 20, 40), ast.literal_eval("(7, 20)"))
    assert not same(True, ast.literal_eval("1"))
    assert same(frozenset({"a", "b"}), ast.literal_eval('{"b", "a"}'))
    assert same(resolve("shk.model.elo_fit", "ELO_FITS['2000-01'].k"), 10.318224689650037)
