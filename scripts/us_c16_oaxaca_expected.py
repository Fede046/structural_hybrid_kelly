"""Script: Oaxaca-Blinder dello schema sull'errore atteso E_q[δ] invece che su δ realizzato.

R² delle due risposte sulle covariate, rumore delle componenti, soglie strutturali, diagnosi sulle
stagioni osservate e capitale su 100 seed appaiati (shk.model.oaxaca_expected). Scrive
results/us_c16_oaxaca_expected.csv.
"""

import csv
from pathlib import Path

import pandas as pd

from shk.model.frozen_params import frozen_params_path
from shk.model.module1_seeds import s10_seed
from shk.model.module2_data import build_module2_frame
from shk.model.oaxaca_expected import EXPECTED_COLUMNS, expected_records
from shk.model.residuals import load_model_residuals

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "results" / "us_c16_oaxaca_expected.csv"
WORKERS = 5


def run_experiment() -> None:
    """Calcola tutte le righe della verifica e scrive il CSV."""
    frame = build_module2_frame(load_model_residuals())
    records = expected_records(frame, str(frozen_params_path()), s10_seed(), workers=WORKERS)
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CSV_PATH, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(EXPECTED_COLUMNS))
        writer.writeheader()
        writer.writerows(records)
    df = pd.DataFrame(records)
    r2 = df[df["row_type"] == "r2"].groupby("response")["value"].median()
    print("R² mediano:", r2.round(3).to_dict())
    print(df[df["row_type"].isin(["component_sd", "diagnosis", "wealth"])].dropna(axis=1, how="all").to_string(index=False))


if __name__ == "__main__":
    run_experiment()
