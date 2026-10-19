"""Script, sensibilità: C1, C2_global e C2 con la catena del Modulo 2 che attraversa le stagioni.

Solo sulla realizzazione osservata, parametri di config/frozen_params.toml invariati, tre
configurazioni. Si esegue dopo il run principale, di cui rilegge i valori a catena tagliata
da results/raw/us_c8_3_validation_raw.npz. Scrive results/us_c8_3_validation_with_history.csv.
Non entra nei confronti principali fra agenti.
Con --module1 dixon_coles usa il Modulo 1 Dixon-Coles e config/frozen_params_dc.toml, e scrive
le uscite con il suffisso _dc, senza toccare quelle Elo.
"""

import csv
import sys
from pathlib import Path

from shk.model.frozen_params import frozen_params_path
from shk.model.module1 import MODULE1_ELO, module1_from_argv, with_module1_suffix
from shk.model.module2_data import build_module2_frame
from shk.model.residuals import load_model_residuals
from shk.model.validation_run import WITH_HISTORY_COLUMNS, load_raw, with_history_records


def run_experiment(module1: str = MODULE1_ELO) -> None:
    """Sensibilità con storia e confronto con la catena tagliata; scrive il CSV."""
    repo_root = Path(__file__).resolve().parents[1]
    result = load_raw(with_module1_suffix(repo_root / "results" / "raw" / "us_c8_3_validation_raw.npz", module1))
    frame = build_module2_frame(load_model_residuals(module1=module1))
    records = with_history_records(frame, result, params_path=frozen_params_path(module1))
    csv_path = with_module1_suffix(repo_root / "results" / "us_c8_3_validation_with_history.csv", module1)
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(WITH_HISTORY_COLUMNS))
        writer.writeheader()
        writer.writerows(records)


if __name__ == "__main__":
    run_experiment(module1_from_argv(sys.argv[1:]))
