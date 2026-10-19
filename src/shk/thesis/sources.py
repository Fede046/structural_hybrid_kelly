"""Lettura dei CSV versionati per tabelle, figure e numeri della tesi (T65).

Un CSV è versionato se ha una riga in results/MANIFEST.sha256 (T64). Si legge come nel
confronto di T64: con la regola di normalizzazione della sua riga, se c'è (per esempio
us_c3_1_data_coverage senza le righe del 2023-24). Lo SHA256 citato è quello del manifesto,
e read_versioned_csv lo ricontrolla sul contenuto letto.
"""

import functools
import io
from pathlib import Path
from typing import Final, NamedTuple

import pandas as pd

from shk.data.manifest import normalized_bytes, read_manifest, sha256_bytes

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[3]
RESULTS_MANIFEST: Final[str] = "results/MANIFEST.sha256"


class VersionedCsv(NamedTuple):
    """Un CSV versionato: nome senza estensione, percorso relativo alla radice, SHA256 e regola."""

    name: str
    path: str
    sha256: str
    rule: str


def versioned_csv(name: str, root: Path | str = REPO_ROOT) -> VersionedCsv:
    """Riga del manifesto di results/<name>.csv.

    Solleva
    -------
    ValueError
        Se il CSV non è nel manifesto.
    """
    path = f"results/{name}.csv"
    for entry in read_manifest(Path(root) / RESULTS_MANIFEST):
        if entry.path == path:
            return VersionedCsv(name, path, entry.sha256, entry.rule)
    raise ValueError(f"{path} is not listed in {RESULTS_MANIFEST}")


@functools.lru_cache(maxsize=None)
def _read(name: str, root: str) -> pd.DataFrame:
    source = versioned_csv(name, root)
    data = normalized_bytes(Path(root) / source.path, source.rule)
    actual = sha256_bytes(data)
    if actual != source.sha256:
        raise ValueError(f"{source.path} does not match {RESULTS_MANIFEST}: {actual} != {source.sha256}")
    return pd.read_csv(io.BytesIO(data))


def read_versioned_csv(name: str, root: Path | str = REPO_ROOT) -> pd.DataFrame:
    """Copia del DataFrame di results/<name>.csv, letto con la regola del manifesto.

    Solleva
    -------
    ValueError
        Se il CSV non è nel manifesto o il suo SHA256 non coincide.
    """
    return _read(name, str(Path(root).resolve())).copy()
