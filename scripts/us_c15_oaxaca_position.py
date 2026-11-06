"""Script: verifica di robustezza di Oaxaca-Blinder nello schema, con e senza la covariata "position".

Perché la decomposizione separa poco errore nei dati ed errore strutturale (shk.model.oaxaca_position):
R² di δ sulle covariate, rumore delle componenti nelle finestre adiacenti, soglie strutturali
ricalibrate senza "position", diagnosi sulle stagioni osservate e capitale su 100 seed appaiati.
Scrive results/us_c15_oaxaca_position.csv.
"""

import csv
from pathlib import Path

import pandas as pd

from shk.model.frozen_params import frozen_params_path
from shk.model.module1_seeds import s10_seed
from shk.model.module2_data import build_module2_frame
from shk.model.oaxaca_position import POSITION_COLUMNS, position_records
from shk.model.residuals import load_model_residuals

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "results" / "us_c15_oaxaca_position.csv"
WORKERS = 5


def run_experiment() -> None:
    """Calcola tutte le righe della verifica e scrive il CSV."""
    frame = build_module2_frame(load_model_residuals())
    records = position_records(frame, str(frozen_params_path()), s10_seed(), workers=WORKERS)
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CSV_PATH, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(POSITION_COLUMNS))
        writer.writeheader()
        writer.writerows(records)
    df = pd.DataFrame(records)
    print(df[df["row_type"].isin(["component_sd", "diagnosis", "wealth"])].dropna(axis=1, how="all").to_string(index=False))


if __name__ == "__main__":
    run_experiment()
