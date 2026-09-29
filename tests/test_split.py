"""Test per il modulo src/shk/data/split.py e il blocco del test set."""

import ast
import datetime
from pathlib import Path

import pandas as pd
import pytest

from shk.data.loading import DEFAULT_DATA_DIR, load_all_seasons
from shk.data.split import (
    DEFAULT_SPLIT_CONFIG_PATH,
    SplitConfig,
    TestSetLockedError,
    load_by_role,
    read_split_config,
)


def _write_csv(
    file_path: Path,
    date_str: str = "10/08/2000",
    valid_date: bool = True,
) -> None:
    """Crea un file CSV sintetico valido o volutamente malformato."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    header = "Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\n"
    row = f"E0,{date_str if valid_date else 'INVALID_DATE'},TeamA,TeamB,1,0,H\n"
    file_path.write_text(header + row, encoding="utf-8")


def _write_split_toml(
    file_path: Path,
    frozen_on: str = "2026-09-29",
    test_unlocked: bool = False,
    test_unlocked_on: str = '""',
    training: list[str] | None = None,
    validation: list[str] | None = None,
    test: list[str] | None = None,
) -> None:
    """Scrive un file TOML sintetico di configurazione split."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    tr = training if training is not None else ["2000-01"]
    val = validation if validation is not None else ["2001-02"]
    ts = test if test is not None else ["2023-24"]

    content = f"""frozen_on = {frozen_on}
test_unlocked = {str(test_unlocked).lower()}
test_unlocked_on = {test_unlocked_on}
training = {tr!r}
validation = {val!r}
test = {ts!r}
"""
    file_path.write_text(content, encoding="utf-8")


def find_load_all_seasons_references(source_code: str) -> list[int]:
    """Analizza l'AST del codice e restituisce i numeri di riga delle occorrenze di load_all_seasons."""
    tree = ast.parse(source_code)
    lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "load_all_seasons" or alias.asname == "load_all_seasons":
                    lines.add(node.lineno)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "load_all_seasons" or alias.asname == "load_all_seasons":
                    lines.add(node.lineno)
        elif isinstance(node, ast.Name):
            if node.id == "load_all_seasons":
                lines.add(node.lineno)
        elif isinstance(node, ast.Attribute):
            if node.attr == "load_all_seasons":
                lines.add(node.lineno)
    return sorted(lines)


# ---------------------------------------------------------------------------
# Test di read_split_config
# ---------------------------------------------------------------------------


def test_read_split_config_missing_file_raises(tmp_path: Path):
    """Verifica che un file di configurazione inesistente sollevi FileNotFoundError."""
    missing_path = tmp_path / "non_existent.toml"
    with pytest.raises(FileNotFoundError, match="Config file not found"):
        read_split_config(missing_path)


def test_read_split_config_type_validations(tmp_path: Path):
    """Verifica che tipi errati in read_split_config sollevino TypeError."""
    with pytest.raises(TypeError, match="config_path must be str or Path"):
        read_split_config(12345)  # type: ignore

    cfg_file = tmp_path / "split.toml"

    # frozen_on come stringa invece che data nativa
    _write_split_toml(cfg_file, frozen_on='"2026-09-29"')
    with pytest.raises(TypeError, match="frozen_on must be a TOML date"):
        read_split_config(cfg_file)

    # test_unlocked non booleano
    cfg_file.write_text(
        'frozen_on = 2026-09-29\ntest_unlocked = "false"\ntest_unlocked_on = ""\ntraining = ["2000-01"]\nvalidation = []\ntest = ["2023-24"]\n',
        encoding="utf-8",
    )
    with pytest.raises(TypeError, match="test_unlocked must be bool"):
        read_split_config(cfg_file)

    # test_unlocked true ma test_unlocked_on non data
    cfg_file.write_text(
        'frozen_on = 2026-09-29\ntest_unlocked = true\ntest_unlocked_on = "2026-10-01"\ntraining = ["2000-01"]\nvalidation = []\ntest = ["2023-24"]\n',
        encoding="utf-8",
    )
    with pytest.raises(TypeError, match="test_unlocked_on must be a TOML date"):
        read_split_config(cfg_file)

    # training non lista
    cfg_file.write_text(
        'frozen_on = 2026-09-29\ntest_unlocked = false\ntest_unlocked_on = ""\ntraining = "2000-01"\nvalidation = []\ntest = ["2023-24"]\n',
        encoding="utf-8",
    )
    with pytest.raises(TypeError, match="Role 'training' must be a list"):
        read_split_config(cfg_file)

    # elementi non stringhe
    cfg_file.write_text(
        'frozen_on = 2026-09-29\ntest_unlocked = false\ntest_unlocked_on = ""\ntraining = [2000]\nvalidation = []\ntest = ["2023-24"]\n',
        encoding="utf-8",
    )
    with pytest.raises(TypeError, match="Elements of role 'training' must be str"):
        read_split_config(cfg_file)


def test_read_split_config_value_validations(tmp_path: Path):
    """Verifica che valori errati o chiavi non conformi sollevino ValueError."""
    cfg_file = tmp_path / "split.toml"

    # Chiave in piu'
    cfg_file.write_text(
        'extra_key = 1\nfrozen_on = 2026-09-29\ntest_unlocked = false\ntest_unlocked_on = ""\ntraining = ["2000-01"]\nvalidation = []\ntest = ["2023-24"]\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Config keys mismatch"):
        read_split_config(cfg_file)

    # test_unlocked false ma test_unlocked_on non vuoto
    _write_split_toml(cfg_file, test_unlocked=False, test_unlocked_on='"some_value"')
    with pytest.raises(ValueError, match="test_unlocked_on must be empty string"):
        read_split_config(cfg_file)

    # test_unlocked true ma test_unlocked_on anteriore a frozen_on
    _write_split_toml(
        cfg_file,
        frozen_on="2026-09-29",
        test_unlocked=True,
        test_unlocked_on="2026-09-20",
    )
    with pytest.raises(ValueError, match="cannot be earlier than frozen_on"):
        read_split_config(cfg_file)

    # formato stagione non valido (non YYYY-YY)
    _write_split_toml(cfg_file, training=["2000/01"])
    with pytest.raises(ValueError, match="Invalid season format"):
        read_split_config(cfg_file)

    # anni non consecutivi
    _write_split_toml(cfg_file, training=["2000-02"])
    with pytest.raises(ValueError, match="Season year continuity mismatch"):
        read_split_config(cfg_file)

    # duplicati all'interno di un ruolo
    _write_split_toml(cfg_file, training=["2000-01", "2000-01"])
    with pytest.raises(ValueError, match="Duplicate seasons found within role 'training'"):
        read_split_config(cfg_file)

    # sovrapposizione fra ruoli
    _write_split_toml(
        cfg_file,
        training=["2000-01"],
        validation=["2000-01"],
        test=["2023-24"],
    )
    with pytest.raises(ValueError, match="Roles training, validation, and test must be mutually disjoint"):
        read_split_config(cfg_file)

    # test vuoto
    _write_split_toml(cfg_file, test=[])
    with pytest.raises(ValueError, match="test role cannot be empty"):
        read_split_config(cfg_file)

    # training non strettamente anteriore a min(test)
    _write_split_toml(cfg_file, training=["2023-24"], test=["2023-24"])
    # Nota: intercettato prima dalla disgiunzione se identico, quindi testiamo stagione successiva
    _write_split_toml(cfg_file, training=["2024-25"], test=["2023-24"])
    with pytest.raises(ValueError, match="is not strictly earlier than first test season"):
        read_split_config(cfg_file)


def test_read_split_config_success(tmp_path: Path):
    """Verifica la corretta lettura di configurazioni bloccate e sbloccate."""
    cfg_file = tmp_path / "split.toml"
    _write_split_toml(
        cfg_file,
        frozen_on="2026-09-29",
        test_unlocked=False,
        test_unlocked_on='""',
        training=["2000-01"],
        validation=["2010-11"],
        test=["2023-24"],
    )
    cfg = read_split_config(cfg_file)
    assert isinstance(cfg, SplitConfig)
    assert cfg.frozen_on == datetime.date(2026, 9, 29)
    assert cfg.test_unlocked is False
    assert cfg.test_unlocked_on == ""
    assert cfg.training == ("2000-01",)
    assert cfg.validation == ("2010-11",)
    assert cfg.test == ("2023-24",)

    # Caso con sblocco
    _write_split_toml(
        cfg_file,
        frozen_on="2026-09-29",
        test_unlocked=True,
        test_unlocked_on="2026-10-15",
        training=["2000-01"],
        validation=["2010-11"],
        test=["2023-24"],
    )
    cfg_unlocked = read_split_config(cfg_file)
    assert cfg_unlocked.test_unlocked is True
    assert cfg_unlocked.test_unlocked_on == datetime.date(2026, 10, 15)


# ---------------------------------------------------------------------------
# Test del parametro seasons in load_all_seasons (Variante ii)
# ---------------------------------------------------------------------------


def test_load_all_seasons_seasons_param_validations(tmp_path: Path):
    """Verifica le validazioni e il funzionamento del parametro seasons in load_all_seasons."""
    _write_csv(tmp_path / "2000-01.csv", date_str="15/08/2000")
    _write_csv(tmp_path / "2001-02.csv", date_str="15/08/2001")

    # seasons come str solleva TypeError
    with pytest.raises(TypeError, match="seasons cannot be a str"):
        load_all_seasons(tmp_path, seasons="2000-01")  # type: ignore

    # seasons con elementi non str solleva TypeError
    with pytest.raises(TypeError, match="All items in seasons must be str"):
        load_all_seasons(tmp_path, seasons=[2000])  # type: ignore

    # seasons vuoto solleva ValueError
    with pytest.raises(ValueError, match="seasons collection cannot be empty"):
        load_all_seasons(tmp_path, seasons=[])

    # stagione priva di file solleva ValueError
    with pytest.raises(ValueError, match="Seasons without corresponding file"):
        load_all_seasons(tmp_path, seasons=["1999-00"])

    # Caricamento parziale con seasons
    df_subset = load_all_seasons(tmp_path, seasons=["2000-01"])
    assert list(df_subset["season"].unique()) == ["2000-01"]
    assert len(df_subset) == 1


# ---------------------------------------------------------------------------
# Test della barriera I/O (Variante ii)
# ---------------------------------------------------------------------------


def test_variant_ii_locked_file_not_read(tmp_path: Path):
    """Verifica che il file del test set malformato non venga letto quando si carica training."""
    data_dir = tmp_path / "data"
    _write_csv(data_dir / "2000-01.csv", date_str="15/08/2000", valid_date=True)
    _write_csv(data_dir / "2023-24.csv", date_str="15/08/2023", valid_date=False)  # Malformato

    cfg_file = tmp_path / "split.toml"
    _write_split_toml(
        cfg_file,
        training=["2000-01"],
        validation=[],
        test=["2023-24"],
        test_unlocked=False,
    )

    # 1. Caricare 'training' passa: il file 2023-24.csv malformato non viene aperto ne' letto
    df_train = load_by_role("training", config_path=cfg_file, data_dir=data_dir)
    assert len(df_train) == 1
    assert list(df_train["season"].unique()) == ["2000-01"]

    # 2. Caricare senza filtro seasons tramite load_all_seasons solleva ValueError:
    # prova che 2023-24.csv e' effettivamente malformato
    with pytest.raises(ValueError, match="Mixed, invalid, or non-conforming date formats"):
        load_all_seasons(data_dir=data_dir)


# ---------------------------------------------------------------------------
# Test di load_by_role e del blocco del test set
# ---------------------------------------------------------------------------


def test_load_by_role_locked_raises_test_set_locked_error(tmp_path: Path):
    """Verifica che richiedere il ruolo test con test_unlocked=false sollevi TestSetLockedError prima dei dati."""
    cfg_file = tmp_path / "split.toml"
    _write_split_toml(cfg_file, test_unlocked=False)

    # Solleva eccezione anche se data_dir non esiste, poiché il controllo avviene prima
    with pytest.raises(TestSetLockedError, match="Test set is locked"):
        load_by_role("test", config_path=cfg_file, data_dir=tmp_path / "non_existent_dir")


def test_load_by_role_unlocked_loads_test_set(tmp_path: Path):
    """Verifica che con test_unlocked=true il ruolo test restituisca solo le stagioni di test."""
    data_dir = tmp_path / "data"
    _write_csv(data_dir / "2000-01.csv", date_str="15/08/2000")
    _write_csv(data_dir / "2023-24.csv", date_str="15/08/2023")

    cfg_file = tmp_path / "split.toml"
    _write_split_toml(
        cfg_file,
        test_unlocked=True,
        test_unlocked_on="2026-10-01",
        training=["2000-01"],
        validation=[],
        test=["2023-24"],
    )

    df_test = load_by_role("test", config_path=cfg_file, data_dir=data_dir)
    assert list(df_test["season"].unique()) == ["2023-24"]


def test_load_by_role_non_test_roles_never_return_blocked_seasons(tmp_path: Path):
    """Verifica che nessun ruolo diverso da test restituisca stagioni >= min(test), anche non censite."""
    data_dir = tmp_path / "data"
    _write_csv(data_dir / "1998-99.csv", date_str="15/08/1998")  # history
    _write_csv(data_dir / "2000-01.csv", date_str="15/08/2000")  # training
    _write_csv(data_dir / "2005-06.csv", date_str="15/08/2005")  # validation
    _write_csv(data_dir / "2023-24.csv", date_str="15/08/2023")  # test
    _write_csv(data_dir / "2024-25.csv", date_str="15/08/2024")  # stagione >= 2023 non censita (bloccata)

    cfg_file = tmp_path / "split.toml"
    _write_split_toml(
        cfg_file,
        training=["2000-01"],
        validation=["2005-06"],
        test=["2023-24"],
        test_unlocked=False,
    )

    # training
    df_train = load_by_role("training", config_path=cfg_file, data_dir=data_dir)
    assert list(df_train["season"].unique()) == ["2000-01"]

    # validation
    df_val = load_by_role("validation", config_path=cfg_file, data_dir=data_dir)
    assert list(df_val["season"].unique()) == ["2005-06"]

    # history: deve contenere 1998-99, ma NON 2024-25 (che e' >= 2023-24 e bloccata)
    df_hist = load_by_role("history", config_path=cfg_file, data_dir=data_dir)
    assert list(df_hist["season"].unique()) == ["1998-99"]


def test_load_by_role_validations(tmp_path: Path):
    """Verifica le validazioni degli argomenti in load_by_role."""
    cfg_file = tmp_path / "split.toml"
    _write_split_toml(cfg_file)

    # role non str
    with pytest.raises(TypeError, match="role must be str"):
        load_by_role(123)  # type: ignore

    # role non riconosciuto
    with pytest.raises(ValueError, match="Invalid role 'unknown'"):
        load_by_role("unknown", config_path=cfg_file)

    # config_path non valido
    with pytest.raises(TypeError, match="config_path must be str or Path"):
        load_by_role("training", config_path=123)  # type: ignore

    # data_dir non valido
    with pytest.raises(TypeError, match="data_dir must be str or Path"):
        load_by_role("training", config_path=cfg_file, data_dir=123)  # type: ignore

    # stagione configurata assente dalla directory
    data_dir = tmp_path / "data"
    _write_csv(data_dir / "2000-01.csv")
    with pytest.raises(ValueError, match="Configured season '2001-02' not found"):
        load_by_role("training", config_path=cfg_file, data_dir=data_dir)


# ---------------------------------------------------------------------------
# Test di guardia AST su load_all_seasons
# ---------------------------------------------------------------------------


def test_guard_ast_analysis_synthetic():
    """Verifica che l'analisi AST rilevi import e chiamate ed escluda commenti e docstring."""
    code_direct_call = """
def run():
    df = load_all_seasons()
"""
    assert find_load_all_seasons_references(code_direct_call) == [3]

    code_from_import = """
from shk.data.loading import load_all_seasons
"""
    assert find_load_all_seasons_references(code_from_import) == [2]

    code_module_alias = """
import shk.data.loading as l
l.load_all_seasons()
"""
    assert find_load_all_seasons_references(code_module_alias) == [3]

    code_docstring_and_comments = '''
"""Questo modulo menziona load_all_seasons nella docstring."""
# Un commento che dice load_all_seasons() non deve essere contato
def some_func():
    """Altra docstring con load_all_seasons."""
    pass
'''
    assert find_load_all_seasons_references(code_docstring_and_comments) == []


def test_guard_repository_load_all_seasons_occurrences():
    """Verifica che nel repository load_all_seasons compaia solo nei quattro file ammessi."""
    import warnings

    repo_root = Path(__file__).resolve().parents[1]
    allowed_files = {
        "src/shk/data/loading.py",
        "src/shk/data/split.py",
        "src/shk/data/coverage.py",
        "scripts/us_c3_1_data_coverage.py",
    }

    files_with_occurrences: dict[str, list[int]] = {}
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=SyntaxWarning)
        for target_dir in ("src", "scripts"):
            for py_path in (repo_root / target_dir).rglob("*.py"):
                rel_path = py_path.relative_to(repo_root).as_posix()
                source = py_path.read_text(encoding="utf-8")
                refs = find_load_all_seasons_references(source)
                if refs:
                    files_with_occurrences[rel_path] = refs

    # Solo i quattro file ammessi possono avere occorrenze
    assert set(files_with_occurrences.keys()).issubset(allowed_files)
    assert "src/shk/data/split.py" in files_with_occurrences
    assert "scripts/us_c3_1_data_coverage.py" in files_with_occurrences


# ---------------------------------------------------------------------------
# Test su file reale config/split.toml e dati reali
# ---------------------------------------------------------------------------


def test_real_config_split_file():
    """Verifica che config/split.toml esista, sia valido e blocchi il test set."""
    cfg = read_split_config(DEFAULT_SPLIT_CONFIG_PATH)
    assert cfg.frozen_on == datetime.date(2026, 9, 29)
    assert cfg.test_unlocked is False
    assert cfg.test_unlocked_on == ""
    assert cfg.training == ("2000-01", "2010-11", "2020-21")
    assert len(cfg.validation) == 19
    assert cfg.test == ("2023-24",)

    # Con test_unlocked=false, richiedere 'test' solleva TestSetLockedError
    with pytest.raises(TestSetLockedError, match="Test set is locked"):
        load_by_role("test", config_path=DEFAULT_SPLIT_CONFIG_PATH)


def test_real_data_load_by_role():
    """Verifica il caricamento dei ruoli sui dati reali (saltato se mancano i CSV)."""
    if not DEFAULT_DATA_DIR.exists() or not list(DEFAULT_DATA_DIR.glob("*.csv")):
        pytest.skip(f"Dati reali assenti in {DEFAULT_DATA_DIR}")

    df_train = load_by_role("training")
    assert len(df_train) == 1140
    assert set(df_train["season"].unique()) == {"2000-01", "2010-11", "2020-21"}

    df_val = load_by_role("validation")
    assert len(df_val) == 7220
    assert len(df_val["season"].unique()) == 19

    df_hist = load_by_role("history")
    assert len(df_hist) == 3204
    assert len(df_hist["season"].unique()) == 8

    # Nessuna stagione >= 2023-24 deve comparire in nessuno dei ruoli non-test
    for df_role in (df_train, df_val, df_hist):
        years = [int(s.split("-")[0]) for s in df_role["season"].unique()]
        assert all(y < 2023 for y in years)
