"""Test: numeri citabili, tabelle e figure della tesi.

- Ogni voce di thesis/numeri.md si rilegge qui in modo indipendente: riga della tabella,
  CSV letto con la regola del manifesto, selezione con DataFrame.query, cella, valore e SHA256.
- Le tabelle di thesis/tables/ coincidono con quelle rigenerate dai CSV versionati.
- Le figure di thesis/figures/tesi_*.pdf sono PDF senza immagini raster e coincidono con
  quelle rigenerate.
Girano senza i dati grezzi: leggono solo CSV versionati.
"""

import io
import math
import shutil
from pathlib import Path

import pandas as pd
import pytest

from shk.data.manifest import normalized_bytes, read_manifest, sha256_bytes
from shk.thesis.figures import FIGURES, save_figure
from shk.thesis.latex import Cell, Column, ThesisTable, format_number, interval, render_csv, render_latex
from shk.thesis.numbers import NUMBERS, THEMES, NumberEntry, check_entry, parse_numbers, render_numbers
from shk.thesis.sources import read_versioned_csv, versioned_csv
from shk.thesis.tables import TABLES, build_table

REPO_ROOT = Path(__file__).resolve().parents[1]
NUMBERS_FILE = REPO_ROOT / "thesis" / "numeri.md"
TABLES_DIR = REPO_ROOT / "thesis" / "tables"
FIGURES_DIR = REPO_ROOT / "thesis" / "figures"


def _numbers_lines() -> list[list[str]]:
    """Righe di dati delle tabelle di numeri.md, divise nei loro otto campi."""
    rows = []
    for line in NUMBERS_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("| ") and not line.startswith("| id |"):
            rows.append([f.strip() for f in line.strip().strip("|").split("|")])
    return rows


def _manifest() -> dict[str, tuple[str, str]]:
    return {e.path: (e.sha256, e.rule) for e in read_manifest(REPO_ROOT / "results" / "MANIFEST.sha256")}


def test_numbers_file_entries_match_csv():
    rows = _numbers_lines()
    assert len(rows) == len(NUMBERS)
    manifest = _manifest()
    frames: dict[str, pd.DataFrame] = {}
    for fields in rows:
        assert len(fields) == 8, fields
        number_id, _, value, _, csv_path, query, column, sha = fields
        assert csv_path in manifest, f"{number_id}: {csv_path} not in results/MANIFEST.sha256"
        expected_sha, rule = manifest[csv_path]
        data = normalized_bytes(REPO_ROOT / csv_path, rule)
        assert sha == expected_sha == sha256_bytes(data), number_id
        if csv_path not in frames:
            frames[csv_path] = pd.read_csv(io.BytesIO(data))
        assert query.startswith("`") and query.endswith("`"), number_id
        selected = frames[csv_path].query(query[1:-1], engine="python")
        assert len(selected) == 1, f"{number_id}: {len(selected)} rows"
        cell = float(selected.iloc[0][column])
        decimals = len(value.partition(".")[2])
        assert math.isfinite(cell), number_id
        assert abs(cell - float(value)) <= 0.5 * 10.0 ** (-decimals) + 1e-12, f"{number_id}: {value} vs {cell!r}"


def test_numbers_file_is_up_to_date_and_covers_every_theme():
    text = NUMBERS_FILE.read_text(encoding="utf-8")
    assert text == render_numbers(REPO_ROOT)
    for title in THEMES.values():
        assert f"## {title}" in text
    assert {s.theme for s in NUMBERS} == set(THEMES)
    entries = parse_numbers(text)
    assert [e.id for e in entries] == [s.id for s in NUMBERS]
    assert all(check_entry(e, REPO_ROOT) == [] for e in entries)


def test_check_entry_reports_wrong_value_and_sha():
    entry = parse_numbers(NUMBERS_FILE.read_text(encoding="utf-8"))[0]
    wrong_value = entry._replace(value=f"{float(entry.value) + 0.01:.3f}")
    wrong_sha = entry._replace(sha256="0" * 64)
    assert any("value" in p for p in check_entry(wrong_value, REPO_ROOT))
    assert any("SHA256" in p for p in check_entry(wrong_sha, REPO_ROOT))
    ambiguous = NumberEntry(entry.id, "", "0", "", entry.csv, 'design == "contiguous_2"', "rejection_rate", entry.sha256)
    assert any("selects" in p for p in check_entry(ambiguous, REPO_ROOT))


def test_read_versioned_csv_rejects_unlisted_and_modified_files(tmp_path):
    with pytest.raises(ValueError, match="not listed"):
        versioned_csv("us_does_not_exist")
    (tmp_path / "results").mkdir()
    shutil.copy(REPO_ROOT / "results" / "MANIFEST.sha256", tmp_path / "results" / "MANIFEST.sha256")
    source = REPO_ROOT / "results" / "us_c2_anova_autocorrelation.csv"
    (tmp_path / "results" / source.name).write_bytes(source.read_bytes().replace(b"0.037", b"0.038", 1))
    with pytest.raises(ValueError, match="does not match"):
        read_versioned_csv("us_c2_anova_autocorrelation", tmp_path)


@pytest.mark.parametrize("name", list(TABLES))
def test_tables_regenerate_identically(name):
    table = build_table(name, REPO_ROOT)
    assert (TABLES_DIR / f"{name}.tex").read_text(encoding="utf-8") == render_latex(table)
    assert (TABLES_DIR / f"{name}.csv").read_bytes().decode("utf-8") == render_csv(table)


@pytest.mark.parametrize("name", list(TABLES))
def test_table_rows_have_one_cell_per_column(name):
    table = build_table(name, REPO_ROOT)
    tex = render_latex(table)
    body = tex.split(r"\midrule", 1)[1].split(r"\bottomrule", 1)[0]
    for line in body.splitlines():
        if line.strip() and line.strip() != r"\midrule":
            assert line.replace(r"\&", "").count("&") == len(table.columns) - 1, line
    if table.header_groups:
        header = tex.split(r"\toprule", 1)[1].splitlines()[1]
        cells = header.replace(r" \\", "").split(" & ")
        spans = sum(int(c.split("{")[1].split("}")[0]) if c.startswith(r"\multicolumn") else 1 for c in cells)
        assert spans == len(table.columns), header
    for source in table.sources:
        assert source.path.replace("_", r"\_") in tex


def test_format_number_and_interval():
    assert format_number(-0.02224, 4) == "$-$0,0222"
    assert format_number(0.3214, 3, signed=True) == "$+$0,321"
    assert format_number(-0.00001, 3) == "0,000"
    assert format_number(22000, 0) == r"22\,000"
    assert format_number(1427.04, 1) == "1427,0"
    assert format_number(float("nan"), 2) == "---"
    cell = interval(-0.0298, -0.0147, 4)
    assert cell.latex == "[$-$0,0298; $-$0,0147]" and cell.csv == ("-0.0298", "-0.0147")


def test_group_column_is_shown_once_per_group():
    table = ThesisTable(
        name="tab_prova",
        caption="Prova",
        columns=(Column("Gruppo", ("gruppo",), "l", group=True), Column("Valore", ("valore",))),
        rows=((Cell("a", ("a",)), Cell("1", ("1",))), (Cell("a", ("a",)), Cell("2", ("2",))),
              (Cell("b", ("b",)), Cell("3", ("3",)))),
        sources=(versioned_csv("us_c2_anova_autocorrelation", REPO_ROOT),),
        header_groups=(("", 1), ("Misure", 1)),
    )
    tex = render_latex(table)
    assert "a & 1 \\\\\n & 2 \\\\\n\\midrule\nb & 3 \\\\" in tex
    assert render_csv(table) == "gruppo,valore\r\na,1\r\na,2\r\nb,3\r\n"
    with pytest.raises(ValueError):
        ThesisTable("tab_x", "x", table.columns, ((Cell("a", ("a",)),),), table.sources)


@pytest.mark.parametrize("name", list(FIGURES))
def test_figures_are_vector_pdfs_and_regenerate_identically(name, tmp_path):
    path = save_figure(name, tmp_path, REPO_ROOT)
    data = path.read_bytes()
    assert data.startswith(b"%PDF")
    assert b"/Subtype /Image" not in data
    assert b"CreationDate" not in data
    assert (FIGURES_DIR / f"{name}.pdf").read_bytes() == data
