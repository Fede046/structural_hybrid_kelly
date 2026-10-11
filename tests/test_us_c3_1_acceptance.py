"""Test di accettazione di US-C3.1 sul blocco del test set (T41).

Lo script dell'audit di copertura non apre nessun file di stagione dal primo anno di test
in poi finché config/split.toml ha test_unlocked = false.
"""

import builtins
import csv
import importlib.util
import io
import os
import re
from pathlib import Path
from types import ModuleType

import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.data.split import DEFAULT_SPLIT_CONFIG_PATH, read_split_config

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "us_c3_1_data_coverage.py"
CSV_PATH = REPO_ROOT / "results" / "us_c3_1_data_coverage.csv"
SEASON_FILE_PATTERN = re.compile(r"^(\d{4})-(\d{2})\.csv$")


def _has_real_data() -> bool:
    """Vero se data/raw/E0/ contiene almeno un CSV."""
    return DEFAULT_DATA_DIR.is_dir() and any(DEFAULT_DATA_DIR.glob("*.csv"))


def _first_test_year() -> int:
    """Primo anno delle stagioni di test di config/split.toml."""
    cfg = read_split_config(DEFAULT_SPLIT_CONFIG_PATH)
    return min(int(s.split("-")[0]) for s in cfg.test)


def _load_script_module() -> ModuleType:
    """Importa lo script C3.1 come modulo, senza eseguirne il blocco __main__."""
    spec = importlib.util.spec_from_file_location("us_c3_1_data_coverage_under_test", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_versioned_csv_has_no_locked_season():
    """Con il test bloccato il CSV versionato non ha righe di stagioni dal primo anno di test."""
    cfg = read_split_config(DEFAULT_SPLIT_CONFIG_PATH)
    if cfg.test_unlocked:
        pytest.skip("Test set unlocked: the check applies only while test_unlocked = false")
    first_test_year = _first_test_year()

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        seasons = {row["season"] for row in csv.DictReader(f)}

    assert seasons, "Empty coverage CSV"
    assert all(int(s.split("-")[0]) < first_test_year for s in seasons)


def test_script_opens_no_locked_season_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Esegue run_experiment registrando i file aperti: nessuno è di una stagione bloccata."""
    if not _has_real_data():
        pytest.skip(f"Real data missing: no CSV in {DEFAULT_DATA_DIR}")
    cfg = read_split_config(DEFAULT_SPLIT_CONFIG_PATH)
    if cfg.test_unlocked:
        pytest.skip("Test set unlocked: the check applies only while test_unlocked = false")
    first_test_year = _first_test_year()

    module = _load_script_module()
    # Radice temporanea per le uscite: CSV e PNG versionati non vengono riscritti
    monkeypatch.setattr(module, "__file__", str(tmp_path / "scripts" / SCRIPT_PATH.name))

    opened: list[Path] = []
    original_open = io.open

    def recording_open(file, *args, **kwargs):
        if isinstance(file, (str, os.PathLike)):
            opened.append(Path(os.fspath(file)))
        return original_open(file, *args, **kwargs)

    # pathlib.Path.open, e quindi read_bytes, passa da io.open
    monkeypatch.setattr(io, "open", recording_open)
    monkeypatch.setattr(builtins, "open", recording_open)

    module.run_experiment()

    monkeypatch.undo()

    data_dir = DEFAULT_DATA_DIR.resolve()
    opened_seasons = {
        p.stem
        for p in opened
        if p.resolve().parent == data_dir and SEASON_FILE_PATTERN.match(p.name)
    }
    # Il registratore deve aver visto le letture: altrimenti il test non proverebbe nulla
    assert opened_seasons, "No season file recorded: reads were not intercepted"

    locked = sorted(s for s in opened_seasons if int(s.split("-")[0]) >= first_test_year)
    assert locked == [], f"Locked season files opened: {locked}"

    expected = {
        p.stem
        for p in DEFAULT_DATA_DIR.glob("*.csv")
        if int(p.stem.split("-")[0]) < first_test_year
    }
    assert opened_seasons == expected

    # Uscite scritte nella radice temporanea, senza stagioni bloccate
    out_csv = tmp_path / "results" / CSV_PATH.name
    with open(out_csv, newline="", encoding="utf-8") as f:
        out_seasons = {row["season"] for row in csv.DictReader(f)}
    assert out_seasons == expected
    assert (tmp_path / "thesis" / "figures" / "us_c3_1_data_coverage.png").is_file()
