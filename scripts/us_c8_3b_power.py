"""Script T53: analisi di potenza sulle stagioni di training e numero di seed per S10.

Scrive results/us_c8_3b_power.csv (shk.model.power). Parametri provvisori di T52.
Con --module1 dixon_coles usa il Modulo 1 Dixon-Coles e scrive le uscite con il suffisso _dc,
senza toccare quelle Elo (T60).
"""

import csv
import sys
from pathlib import Path

from shk.model.covariate_inspection import derive_specification
from shk.model.module1 import MODULE1_ELO, module1_from_argv, with_module1_suffix
from shk.model.module2_data import build_module2_frame
from shk.model.power import POWER_CSV_COLUMNS, evaluate_power
from shk.model.residuals import load_model_residuals


def run_experiment(module1: str = MODULE1_ELO) -> None:
    """Seed ricostruiti, differenze appaiate C1 − C0 e C2 − C1, N_SEEDS e tempo di S10; scrive il CSV."""
    repo_root = Path(__file__).resolve().parents[1]
    csv_path = with_module1_suffix(repo_root / "results" / "us_c8_3b_power.csv", module1)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    frame = build_module2_frame(load_model_residuals(module1=module1))
    train = frame[frame["role"] == "training"]
    records = evaluate_power(train, derive_specification(train).covariates)

    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(POWER_CSV_COLUMNS))
        writer.writeheader()
        writer.writerows(records)


if __name__ == "__main__":
    run_experiment(module1_from_argv(sys.argv[1:]))
