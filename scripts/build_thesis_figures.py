"""Figure finali della tesi in PDF vettoriale, dai soli CSV versionati.

Per ogni figura di shk.thesis.figures.FIGURES scrive thesis/figures/<nome>.pdf, nello stile
comune (shk.thesis.figures.STYLE) e con le etichette in italiano. I PNG degli script degli
esperimenti restano dove sono. Legge solo i CSV elencati in results/MANIFEST.sha256 e non
calcola nulla di nuovo.

Uso, dalla radice del repository:
- senza argomenti rigenera tutte le figure;
- con --only NOME (ripetibile) rigenera solo le figure indicate.
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

from shk.thesis.figures import FIGURES, save_figure

REPO_ROOT = Path(__file__).resolve().parents[1]
FIGURES_DIR = REPO_ROOT / "thesis" / "figures"


def run(argv: list[str]) -> None:
    """Esegue lo script con gli argomenti dati."""
    only = [argv[i + 1] for i, a in enumerate(argv) if a == "--only" and i + 1 < len(argv)]
    unknown = sorted(set(only) - set(FIGURES))
    if unknown:
        sys.exit(f"Unknown figure(s) {unknown}, expected one of {sorted(FIGURES)}")
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    for name in only or FIGURES:
        save_figure(name, FIGURES_DIR, REPO_ROOT)


if __name__ == "__main__":
    run(sys.argv[1:])
