"""Script T52: soglie di C1 ed esecuzione appaiata di prova degli agenti sulle stagioni di training.

Scrive results/us_c8_1b_agents_training.csv (shk.model.training_agents). Parametri
provvisori W = 80 e κ = 0.5: non sono una calibrazione.
"""

import csv
from pathlib import Path

from shk.model.covariate_inspection import derive_specification
from shk.model.module2_data import build_module2_frame
from shk.model.residuals import load_model_residuals
from shk.model.training_agents import TRAINING_AGENTS_CSV_COLUMNS, evaluate_training_agents


def run_experiment() -> None:
    """Calcola soglie e metriche per agente, stagione di training e configurazione; scrive il CSV."""
    repo_root = Path(__file__).resolve().parents[1]
    csv_path = repo_root / "results" / "us_c8_1b_agents_training.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    data = load_model_residuals()
    frame = build_module2_frame(data)
    train = frame[frame["role"] == "training"]
    spec = derive_specification(train)
    records = evaluate_training_agents(train, spec.covariates)

    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(TRAINING_AGENTS_CSV_COLUMNS))
        writer.writeheader()
        writer.writerows(records)


if __name__ == "__main__":
    run_experiment()
