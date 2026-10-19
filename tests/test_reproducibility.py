"""Test: manifesti SHA256, normalizzazioni dichiarate, percorsi degli script, passi di reproduce_all."""

import csv
import hashlib
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.data.manifest import (
    ManifestEntry,
    build_entries,
    check_entries,
    file_sha256,
    normalized_bytes,
    read_manifest,
    write_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_MANIFEST = REPO_ROOT / "results" / "MANIFEST.sha256"
RAW_MANIFEST = REPO_ROOT / "data" / "raw" / "E0" / "MANIFEST.sha256"
PATH_SCRIPTS = ("us_c1_1_growth_vs_lambda", "us_c1_2_estimation_error", "us_c2_anova_autocorrelation")


def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(f"script_{name}", REPO_ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_csv(path: Path, rows: list[list[str]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)


def test_normalization_rules(tmp_path):
    """drop_seasons toglie le righe delle stagioni date; blank_columns svuota le colonne date."""
    a = tmp_path / "a.csv"
    _write_csv(a, [["season", "x", "seconds"], ["2022-23", "1", "0.5"], ["2023-24", "2", "0.7"]])
    kept = normalized_bytes(a, "drop_seasons:2023-24").decode("utf-8")
    assert kept == "season,x,seconds\r\n2022-23,1,0.5\r\n"
    b = tmp_path / "b.csv"
    _write_csv(b, [["season", "x", "seconds"], ["2022-23", "1", "9.9"], ["2023-24", "2", "1.1"]])
    assert file_sha256(a, "blank_columns:seconds") == file_sha256(b, "blank_columns:seconds")
    assert file_sha256(a) != file_sha256(b)
    _write_csv(b, [["season", "x", "seconds"], ["2022-23", "3", "9.9"], ["2023-24", "2", "1.1"]])
    assert file_sha256(a, "blank_columns:seconds") != file_sha256(b, "blank_columns:seconds")
    with pytest.raises(ValueError, match="Unknown normalization rule"):
        normalized_bytes(a, "sort_rows:x")


def test_manifest_roundtrip_and_check(tmp_path):
    """Scrittura e lettura del manifesto; esiti ok, mismatch e missing."""
    (tmp_path / "one.csv").write_bytes(b"a\r\n1\r\n")
    (tmp_path / "two.csv").write_bytes(b"season\r\n2023-24\r\n")
    entries = build_entries(tmp_path, ["one.csv", "two.csv"], {"two.csv": "drop_seasons:2023-24"})
    manifest = tmp_path / "MANIFEST.sha256"
    write_manifest(manifest, entries, ("intestazione",))
    assert read_manifest(manifest) == entries
    assert entries[1].sha256 == hashlib.sha256(b"season\r\n").hexdigest()
    (tmp_path / "one.csv").write_bytes(b"a\r\n2\r\n")
    statuses = [r.status for r in check_entries(tmp_path, entries + [ManifestEntry("0" * 64, "three.csv")])]
    assert statuses == ["mismatch", "ok", "missing"]
    manifest.write_text("abc  x.csv\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Malformed manifest line"):
        read_manifest(manifest)


def test_raw_data_manifest_verifies():
    """I CSV grezzi coincidono con data/raw/E0/MANIFEST.sha256 e sono tutti nel manifesto."""
    if not DEFAULT_DATA_DIR.is_dir() or not any(DEFAULT_DATA_DIR.glob("*.csv")):
        pytest.skip(f"Real data missing: no CSV in {DEFAULT_DATA_DIR}")
    entries = read_manifest(RAW_MANIFEST)
    assert all(r.status == "ok" for r in check_entries(REPO_ROOT, entries))
    assert {e.path for e in entries} == {p.relative_to(REPO_ROOT).as_posix() for p in DEFAULT_DATA_DIR.glob("*.csv")}


def test_results_manifest_matches_current_files():
    """Ogni riga di results/MANIFEST.sha256 coincide con il file attuale (normalizzato dove dichiarato)."""
    bad = [r for r in check_entries(REPO_ROOT, read_manifest(RESULTS_MANIFEST)) if r.status != "ok"]
    assert bad == []


def test_reproduce_steps_cover_every_manifest_csv():
    """Ogni CSV del manifesto è prodotto da un passo di reproduce_all; le regole sono quelle dichiarate."""
    reproduce = _load_script("reproduce_all")
    produced = {o for s in reproduce.STEPS for o in s.outputs}
    entries = read_manifest(RESULTS_MANIFEST)
    assert {e.path for e in entries if e.path.endswith(".csv")} == produced
    assert {e.path: e.rule for e in entries if e.rule} == reproduce.normalization_rules()


def test_c3_1_unlocked_regeneration_matches_normalized_manifest(tmp_path):
    """L'audit di copertura rigenerato con il test sbloccato coincide con il manifesto dopo drop_seasons."""
    if not DEFAULT_DATA_DIR.is_dir() or not any(DEFAULT_DATA_DIR.glob("*.csv")):
        pytest.skip(f"Real data missing: no CSV in {DEFAULT_DATA_DIR}")
    script = _load_script("us_c3_1_data_coverage")
    out = tmp_path / "us_c3_1_data_coverage.csv"
    with open(out, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=script.COVERAGE_CSV_COLUMNS)
        writer.writeheader()
        for row in script.compute_coverage(script.load_coverage_seasons()).to_dict(orient="records"):
            writer.writerow(row)
    entry = next(e for e in read_manifest(RESULTS_MANIFEST) if e.path == "results/us_c3_1_data_coverage.csv")
    assert file_sha256(out, entry.rule) == entry.sha256


@pytest.mark.parametrize("name", PATH_SCRIPTS)
def test_c1_c2_paths_do_not_depend_on_working_directory(name, tmp_path, monkeypatch):
    """Gli script di C1 e C2 calcolano i percorsi da __file__: da un'altra directory puntano alla radice."""
    monkeypatch.chdir(tmp_path)
    module = _load_script(name)
    assert module.CSV_PATH == REPO_ROOT / "results" / f"{name}.csv"
    assert module.PNG_PATH == REPO_ROOT / "thesis" / "figures" / f"{name}.png"
    source = (REPO_ROOT / "scripts" / f"{name}.py").read_text(encoding="utf-8")
    assert 'os.path.join("results"' not in source and 'os.path.join("thesis"' not in source


@pytest.mark.slow
def test_c1_1_script_writes_to_repository_from_other_directory(tmp_path):
    """Slow (circa 15 s): l'esperimento crescita-frazione lanciato da un'altra directory scrive in results/ della radice, con lo stesso SHA256."""
    target = REPO_ROOT / "results" / "us_c1_1_growth_vs_lambda.csv"
    before = target.stat().st_mtime_ns
    subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "us_c1_1_growth_vs_lambda.py")], cwd=tmp_path,
                   check=True)
    assert target.stat().st_mtime_ns > before
    assert not (tmp_path / "results").exists() and not (tmp_path / "thesis").exists()
    entry = next(e for e in read_manifest(RESULTS_MANIFEST) if e.path == "results/us_c1_1_growth_vs_lambda.csv")
    assert file_sha256(target) == entry.sha256
