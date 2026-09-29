"""Modulo per la gestione dello split dei dati e il blocco del test set."""

import datetime
from pathlib import Path
import re
import tomllib
from typing import Final, NamedTuple

import pandas as pd

from shk.data.loading import DEFAULT_DATA_DIR, load_all_seasons

# Percorso predefinito del file di configurazione split.toml
DEFAULT_SPLIT_CONFIG_PATH: Final[Path] = (
    Path(__file__).resolve().parents[3] / "config" / "split.toml"
)


class TestSetLockedError(RuntimeError):
    """Eccezione sollevata quando si tenta di accedere al test set bloccato."""

    # Disabilita la raccolta automatica da parte di pytest, che altrimenti
    # considererebbe la classe una test suite a causa del prefisso 'Test'.
    __test__ = False


class SplitConfig(NamedTuple):
    """Configurazione congelata dello split delle stagioni per ruolo."""

    frozen_on: datetime.date
    test_unlocked: bool
    test_unlocked_on: datetime.date | str
    training: tuple[str, ...]
    validation: tuple[str, ...]
    test: tuple[str, ...]


def read_split_config(
    config_path: Path | str = DEFAULT_SPLIT_CONFIG_PATH,
) -> SplitConfig:
    """Legge e valida il file di configurazione dello split temporale.

    Parametri
    ----------
    config_path : Path o str, opzionale
        Percorso del file split.toml da leggere.
        Predefinito a DEFAULT_SPLIT_CONFIG_PATH.

    Restituisce
    -----------
    SplitConfig
        Struttura dati tipizzata contenente i metadati di congelamento e le liste
        delle stagioni assegnate ai ruoli training, validation e test.

    Solleva
    -------
    TypeError
        Se config_path non e' str o Path, se frozen_on non e' una data TOML (datetime.date),
        se test_unlocked non e' bool, se test_unlocked_on (quando test_unlocked e' true)
        non e' una data TOML, o se uno dei ruoli non e' una lista di stringhe.
    FileNotFoundError
        Se il file di configurazione specificato non esiste.
    ValueError
        Se le chiavi del TOML differiscono da quelle attese, se test_unlocked_on non e'
        stringa vuota quando test_unlocked e' false, se test_unlocked_on precede frozen_on,
        se il ruolo test e' vuoto, se vi sono duplicati dentro un ruolo o fra ruoli,
        se una stagione ha formato non valido (YYYY-YY con anni non consecutivi), o se
        le stagioni di training o validation non sono strettamente anteriori alla prima
        stagione di test.
    """
    if not isinstance(config_path, (str, Path)):
        raise TypeError(
            f"config_path must be str or Path, got {type(config_path).__name__}"
        )

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    raw_bytes = path.read_bytes()
    text = raw_bytes.decode("utf-8")
    data = tomllib.loads(text)

    expected_keys = {
        "frozen_on",
        "test_unlocked",
        "test_unlocked_on",
        "training",
        "validation",
        "test",
    }
    if set(data.keys()) != expected_keys:
        raise ValueError(
            f"Config keys mismatch: expected {sorted(expected_keys)}, got {sorted(data.keys())}"
        )

    frozen_on = data["frozen_on"]
    if type(frozen_on) is not datetime.date:
        raise TypeError(
            f"frozen_on must be a TOML date (datetime.date), got {type(frozen_on).__name__}"
        )

    test_unlocked = data["test_unlocked"]
    if type(test_unlocked) is not bool:
        raise TypeError(
            f"test_unlocked must be bool, got {type(test_unlocked).__name__}"
        )

    test_unlocked_on = data["test_unlocked_on"]
    if not test_unlocked:
        if test_unlocked_on != "":
            raise ValueError(
                "test_unlocked_on must be empty string when test_unlocked is false"
            )
    else:
        if type(test_unlocked_on) is not datetime.date:
            raise TypeError(
                f"test_unlocked_on must be a TOML date when test_unlocked is true, got {type(test_unlocked_on).__name__}"
            )
        if test_unlocked_on < frozen_on:
            raise ValueError(
                f"test_unlocked_on ({test_unlocked_on}) cannot be earlier than frozen_on ({frozen_on})"
            )

    season_pattern = re.compile(r"^(\d{4})-(\d{2})$")
    role_names = ("training", "validation", "test")
    role_tuples: dict[str, tuple[str, ...]] = {}

    for r in role_names:
        val = data[r]
        if type(val) is not list:
            raise TypeError(f"Role '{r}' must be a list, got {type(val).__name__}")
        for item in val:
            if type(item) is not str:
                raise TypeError(
                    f"Elements of role '{r}' must be str, got {type(item).__name__}"
                )
        if len(val) != len(set(val)):
            raise ValueError(f"Duplicate seasons found within role '{r}'")
        for s in val:
            m = season_pattern.match(s)
            if not m:
                raise ValueError(
                    f"Invalid season format '{s}' in role '{r}', expected YYYY-YY"
                )
            sy = int(m.group(1))
            ey = int(m.group(2))
            if (sy + 1) % 100 != ey:
                raise ValueError(f"Season year continuity mismatch '{s}' in role '{r}'")
        role_tuples[r] = tuple(val)

    if len(role_tuples["test"]) == 0:
        raise ValueError("test role cannot be empty")

    train_set = set(role_tuples["training"])
    val_set = set(role_tuples["validation"])
    test_set = set(role_tuples["test"])

    if (train_set & val_set) or (train_set & test_set) or (val_set & test_set):
        raise ValueError("Roles training, validation, and test must be mutually disjoint")

    min_test_year = min(int(s.split("-")[0]) for s in role_tuples["test"])
    for s in role_tuples["training"]:
        if int(s.split("-")[0]) >= min_test_year:
            raise ValueError(
                f"Training season '{s}' is not strictly earlier than first test season ({min_test_year})"
            )
    for s in role_tuples["validation"]:
        if int(s.split("-")[0]) >= min_test_year:
            raise ValueError(
                f"Validation season '{s}' is not strictly earlier than first test season ({min_test_year})"
            )

    return SplitConfig(
        frozen_on=frozen_on,
        test_unlocked=test_unlocked,
        test_unlocked_on=test_unlocked_on,
        training=role_tuples["training"],
        validation=role_tuples["validation"],
        test=role_tuples["test"],
    )


def load_by_role(
    role: str,
    config_path: Path | str = DEFAULT_SPLIT_CONFIG_PATH,
    data_dir: Path | str = DEFAULT_DATA_DIR,
) -> pd.DataFrame:
    """Carica le partite della Premier League per lo specifico ruolo richiesto.

    Verifica la presenza delle stagioni richieste sul disco e garantisce che nessuna
    riga appartenente al test set bloccato o a stagioni successive all'inizio del test set
    venga restituita per ruoli non-test.

    Parametri
    ----------
    role : str
        Ruolo da caricare. Valori ammessi: 'training', 'validation', 'test', 'history'.
    config_path : Path o str, opzionale
        Percorso del file di configurazione split.toml.
        Predefinito a DEFAULT_SPLIT_CONFIG_PATH.
    data_dir : Path o str, opzionale
        Directory contenente i file CSV delle stagioni.
        Predefinito a DEFAULT_DATA_DIR.

    Restituisce
    -----------
    pd.DataFrame
        DataFrame consolidato contenente le sole partite delle stagioni associate
        al ruolo indicato.

    Solleva
    -------
    TypeError
        Se role non e' str, oppure se config_path o data_dir non sono str o Path.
    ValueError
        Se role non appartiene all'insieme {'training', 'validation', 'test', 'history'},
        oppure se una stagione configurata per il ruolo e' assente nella directory.
    FileNotFoundError
        Se config_path o data_dir non esistono sul file system.
    TestSetLockedError
        Se viene richiesto il ruolo 'test' mentre test_unlocked e' false.
    """
    if not isinstance(role, str):
        raise TypeError(f"role must be str, got {type(role).__name__}")

    valid_roles = {"training", "validation", "test", "history"}
    if role not in valid_roles:
        raise ValueError(
            f"Invalid role '{role}', must be one of {sorted(valid_roles)}"
        )

    if not isinstance(config_path, (str, Path)):
        raise TypeError(
            f"config_path must be str or Path, got {type(config_path).__name__}"
        )

    if not isinstance(data_dir, (str, Path)):
        raise TypeError(
            f"data_dir must be str or Path, got {type(data_dir).__name__}"
        )

    cfg = read_split_config(config_path)

    if role == "test" and not cfg.test_unlocked:
        raise TestSetLockedError(
            "Test set is locked. Access to test data requires test_unlocked = true."
        )

    dir_path = Path(data_dir)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")

    csv_files = sorted(dir_path.glob("*.csv"))
    if not csv_files:
        raise ValueError(f"No CSV files found in directory: {dir_path}")

    filename_pattern = re.compile(r"^(\d{4})-(\d{2})\.csv$")
    available_seasons: set[str] = set()
    for f in csv_files:
        m = filename_pattern.match(f.name)
        if not m:
            raise ValueError(
                f"Invalid season filename format: {f.name}, expected YYYY-YY.csv"
            )
        sy = int(m.group(1))
        ey = int(m.group(2))
        if (sy + 1) % 100 != ey:
            raise ValueError(f"Season year continuity mismatch: {f.name}")
        available_seasons.add(f"{sy:04d}-{ey:02d}")

    all_configured = cfg.training + cfg.validation + cfg.test
    for s in all_configured:
        if s not in available_seasons:
            raise ValueError(
                f"Configured season '{s}' not found in data directory: {dir_path}"
            )

    min_test_year = min(int(s.split("-")[0]) for s in cfg.test)

    if role == "training":
        target_seasons = list(cfg.training)
    elif role == "validation":
        target_seasons = list(cfg.validation)
    elif role == "test":
        target_seasons = list(cfg.test)
    else:  # role == "history"
        assigned = set(cfg.training) | set(cfg.validation)
        target_seasons = sorted(
            s
            for s in available_seasons
            if int(s.split("-")[0]) < min_test_year and s not in assigned
        )

    return load_all_seasons(data_dir=dir_path, seasons=target_seasons)
