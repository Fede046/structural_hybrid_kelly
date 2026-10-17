"""Script T52: soglie di C1 ed esecuzione appaiata di prova degli agenti sulle stagioni di training.

Scrive results/us_c8_1b_agents_training.csv (shk.model.training_agents). Parametri
provvisori W = 80 e κ = 0.5: non sono una calibrazione.
Con --module1 dixon_coles usa il Modulo 1 Dixon-Coles e scrive le uscite con il suffisso _dc,
senza toccare quelle Elo (T60), con i seed di T61 (module1_seeds.procedure_seeds).
"""

import csv
import sys
from pathlib import Path

from shk.model.covariate_inspection import derive_specification
from shk.model.module1 import MODULE1_ELO, module1_from_argv, with_module1_suffix
from shk.model.module1_seeds import procedure_seeds
from shk.model.module2_data import build_module2_frame
from shk.model.residuals import load_model_residuals
from shk.model.training_agents import TRAINING_AGENTS_CSV_COLUMNS, evaluate_training_agents


def run_experiment(module1: str = MODULE1_ELO) -> None:
    """Calcola soglie e metriche per agente, stagione di training e configurazione; scrive il CSV."""
    repo_root = Path(__file__).resolve().parents[1]
    csv_path = with_module1_suffix(repo_root / "results" / "us_c8_1b_agents_training.csv", module1)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    data = load_model_residuals(module1=module1)
    frame = build_module2_frame(data)
    train = frame[frame["role"] == "training"]
    spec = derive_specification(train)
    records = evaluate_training_agents(train, spec.covariates, seed=procedure_seeds(module1)["t52"])

    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(TRAINING_AGENTS_CSV_COLUMNS))
        writer.writeheader()
        writer.writerows(records)


if __name__ == "__main__":
    run_experiment(module1_from_argv(sys.argv[1:]))
