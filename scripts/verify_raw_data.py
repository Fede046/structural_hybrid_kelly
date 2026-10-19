"""Verifica dei CSV grezzi E0 con il manifesto data/raw/E0/MANIFEST.sha256.

Senza argomenti confronta ogni CSV di data/raw/E0/ con il manifesto: l'esito, file per file,
va in build/reproduce/verify_raw_data.txt; se un file manca, è diverso o non è nel manifesto lo
script termina con un messaggio e codice di uscita 1.
Con --write scrive il manifesto dai CSV presenti (solo per crearlo; il manifesto è versionato).
"""

import sys
from pathlib import Path

from shk.data.manifest import build_entries, check_entries, read_manifest, write_manifest

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = REPO_ROOT / "data" / "raw" / "E0"
MANIFEST = RAW_DIR / "MANIFEST.sha256"
REPORT = REPO_ROOT / "build" / "reproduce" / "verify_raw_data.txt"
HEADER = (
    "SHA256 dei CSV E0 di football-data.co.uk usati dal progetto.",
    "Un file per stagione, data/raw/E0/<YYYY-YY>.csv, dal 1993-94 al 2023-24.",
    "Verifica: .venv/Scripts/python.exe scripts/verify_raw_data.py",
)


def raw_paths() -> list[str]:
    """CSV grezzi presenti, come percorsi relativi alla radice."""
    return [p.relative_to(REPO_ROOT).as_posix() for p in sorted(RAW_DIR.glob("*.csv"))]


def run_verification() -> None:
    """Confronta i CSV con il manifesto e scrive l'esito; esce con codice 1 se qualcosa non torna."""
    entries = read_manifest(MANIFEST)
    results = check_entries(REPO_ROOT, entries)
    extra = sorted(set(raw_paths()) - {e.path for e in entries})
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{r.status}  {r.entry.path}" for r in results] + [f"not_in_manifest  {p}" for p in extra]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    bad = [r for r in results if r.status != "ok"]
    if bad or extra:
        sys.exit(f"Raw data check failed: {len(bad)} missing or different, {len(extra)} not in manifest (see {REPORT})")


if __name__ == "__main__":
    if "--write" in sys.argv[1:]:
        write_manifest(MANIFEST, build_entries(REPO_ROOT, raw_paths()), HEADER)
    else:
        run_verification()
