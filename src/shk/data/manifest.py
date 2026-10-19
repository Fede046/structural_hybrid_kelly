"""Manifesti SHA256 dei dati grezzi e dei risultati (T64, riproducibilità).

Formato di una riga: "<sha256>  <percorso relativo alla radice>", con eventualmente
"  normalized=<regola>". Le righe che iniziano con "#" sono commenti.

Regole di normalizzazione, per i file che non si riproducono byte per byte per ragioni note
(decisione del programmatore del 2026-10-18), dichiarate nella riga stessa:
- "drop_seasons:S1,S2,…": si tolgono le righe la cui colonna season vale una delle stagioni
  date (per esempio le stagioni di test aggiunte dopo lo sblocco); intestazione e altre righe
  restano byte per byte;
- "blank_columns:C1,C2,…": le colonne date si svuotano (per esempio i tempi misurati) e il CSV
  si riscrive con csv.writer e terminatore di riga "\\r\\n", come gli script;
- "drop_lines:P1,P2,…": si tolgono le righe che iniziano con uno dei prefissi dati (per esempio
  la riga del file congelato con lo SHA256 grezzo del CSV di potenza, che dipende dai tempi).
Lo SHA256 normalizzato si calcola allo stesso modo sul file versionato e su quello rigenerato.
"""

import csv
import hashlib
import io
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import NamedTuple

DROP_SEASONS = "drop_seasons"
BLANK_COLUMNS = "blank_columns"
DROP_LINES = "drop_lines"


class ManifestEntry(NamedTuple):
    """Una riga del manifesto: SHA256 (eventualmente normalizzato), percorso e regola."""

    sha256: str
    path: str
    rule: str = ""


class CheckResult(NamedTuple):
    """Esito del confronto di un file con la sua riga del manifesto."""

    entry: ManifestEntry
    status: str            # "ok", "mismatch" o "missing"
    actual_sha256: str
    checked_path: str


def sha256_bytes(data: bytes) -> str:
    """SHA256 esadecimale di una sequenza di byte."""
    return hashlib.sha256(data).hexdigest()


def _parse_rule(rule: str) -> tuple[str, list[str]]:
    name, _, args = rule.partition(":")
    if name not in (DROP_SEASONS, BLANK_COLUMNS, DROP_LINES) or not args:
        raise ValueError(f"Unknown normalization rule {rule!r}")
    return name, args.split(",")


def normalized_bytes(path: Path | str, rule: str = "") -> bytes:
    """Contenuto del file dopo la regola di normalizzazione (il file stesso se la regola è vuota)."""
    data = Path(path).read_bytes()
    if not rule:
        return data
    name, args = _parse_rule(rule)
    lines = data.decode("utf-8").splitlines(keepends=True)
    if name == DROP_LINES:
        return "".join(ln for ln in lines if not ln.startswith(tuple(args))).encode("utf-8")
    header = next(csv.reader([lines[0]]))
    if name == DROP_SEASONS:
        col = header.index("season")
        drop = set(args)
        kept = [lines[0]]
        for ln in lines[1:]:
            row = next(csv.reader([ln]), [])
            if len(row) <= col or row[col] not in drop:
                kept.append(ln)
        return "".join(kept).encode("utf-8")
    cols = [header.index(c) for c in args]
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\r\n")
    for row in csv.reader(lines):
        if row != header:
            for c in cols:
                row[c] = ""
        writer.writerow(row)
    return out.getvalue().encode("utf-8")


def file_sha256(path: Path | str, rule: str = "") -> str:
    """SHA256 del file, eventualmente normalizzato."""
    return sha256_bytes(normalized_bytes(path, rule))


def format_entry(entry: ManifestEntry) -> str:
    """Riga del manifesto."""
    return f"{entry.sha256}  {entry.path}" + (f"  normalized={entry.rule}" if entry.rule else "")


def read_manifest(path: Path | str) -> list[ManifestEntry]:
    """Righe del manifesto, nell'ordine del file.

    Solleva
    -------
    ValueError
        Se una riga non ha la forma attesa.
    """
    entries = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("  ")
        if len(parts) not in (2, 3) or len(parts[0]) != 64:
            raise ValueError(f"Malformed manifest line: {line!r}")
        rule = ""
        if len(parts) == 3:
            if not parts[2].startswith("normalized="):
                raise ValueError(f"Malformed manifest line: {line!r}")
            rule = parts[2][len("normalized="):]
            _parse_rule(rule)
        entries.append(ManifestEntry(parts[0], parts[1], rule))
    return entries


def write_manifest(path: Path | str, entries: Iterable[ManifestEntry], header: Iterable[str] = ()) -> None:
    """Scrive il manifesto con le righe di commento dell'intestazione (terminatore "\\n")."""
    lines = [f"# {h}" if h else "#" for h in header] + [format_entry(e) for e in entries]
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def build_entries(root: Path | str, paths: Iterable[str], rules: Mapping[str, str] | None = None) -> list[ManifestEntry]:
    """Righe del manifesto per i percorsi dati, relativi a root, con le regole indicate."""
    rules = rules or {}
    return [ManifestEntry(file_sha256(Path(root) / p, rules.get(p, "")), p, rules.get(p, "")) for p in paths]


def check_entries(root: Path | str, entries: Iterable[ManifestEntry],
                  replacements: Mapping[str, Path | str] | None = None) -> list[CheckResult]:
    """Confronta ogni riga con il file corrispondente (o con quello indicato in replacements)."""
    replacements = replacements or {}
    results = []
    for e in entries:
        target = Path(replacements.get(e.path, Path(root) / e.path))
        if not target.exists():
            results.append(CheckResult(e, "missing", "", str(target)))
            continue
        actual = file_sha256(target, e.rule)
        results.append(CheckResult(e, "ok" if actual == e.sha256 else "mismatch", actual, str(target)))
    return results
