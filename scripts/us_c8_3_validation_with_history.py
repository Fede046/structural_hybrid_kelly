"""Script T55, sensibilità: C1, C2_global e C2 con la catena del Modulo 2 che attraversa le stagioni.

Solo sulla realizzazione osservata, parametri di config/frozen_params.toml invariati, tre
configurazioni. Si esegue dopo il run principale, di cui rilegge i valori a catena tagliata
da results/raw/us_c8_3_validation_raw.npz. Scrive results/us_c8_3_validation_with_history.csv.
Non entra nei confronti principali di T56.
"""

import csv
from pathlib import Path

from shk.model.module2_data import build_module2_frame
from shk.model.residuals import load_model_residuals
from shk.model.validation_run import WITH_HISTORY_COLUMNS, load_raw, with_history_records


def run_experiment() -> None:
    """Sensibilità con storia e confronto con la catena tagliata; scrive il CSV."""
    repo_root = Path(__file__).resolve().parents[1]
    result = load_raw(repo_root / "results" / "raw" / "us_c8_3_validation_raw.npz")
    frame = build_module2_frame(load_model_residuals())
    records = with_history_records(frame, result)
    with open(repo_root / "results" / "us_c8_3_validation_with_history.csv", mode="w", newline="",
              encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(WITH_HISTORY_COLUMNS))
        writer.writeheader()
        writer.writerows(records)


if __name__ == "__main__":
    run_experiment()
