"""Script T54: calibrazione sul training e file di congelamento (US-C8.2).

Scrive results/us_c8_2_calibration_log.csv (tutte le combinazioni delle griglie, comprese
le scartate) e config/frozen_params.toml, che si scrive una sola volta: se esiste già lo
script si ferma con FileExistsError, prima di calcolare.

Con l'opzione --from-log non ricalcola: rilegge il log esistente, riapplica la scelta
(training_calibration.finalize_log, con la regola di parità di secondo livello del
2026-10-11), riscrive il log e scrive il file di congelamento. I valori di obiettivo e
puntata media del log restano quelli del calcolo.
"""

import csv
import datetime
import hashlib
import sys
from pathlib import Path

import pandas as pd

from shk.kelly.environment import FALLBACK_MODEL_EV
from shk.kelly.staking import BASE_LAMBDA
from shk.model.agent_c import C0_LAMBDA, C1_N_BOOT
from shk.model.covariate_inspection import derive_specification
from shk.model.elo_fit import ELO_FITS
from shk.model.frozen_params import FROZEN_PARAMS_PATH, render_frozen_params, write_frozen_params
from shk.model.module2_data import build_module2_frame
from shk.model.module3 import CHOSEN_CANDIDATE, INACTIVE_LAMBDA
from shk.model.paired_backtest import CONFIGURATIONS
from shk.model.residuals import load_model_residuals
from shk.model.training_agents import season_input_from_frame, threshold_records, training_seasons
from shk.model.training_calibration import (
    CALIBRATION_CONFIG,
    CALIBRATION_LOG_COLUMNS,
    N_CALIBRATION_SEEDS,
    evaluate_calibration,
    finalize_log,
)
from shk.stats.drift import detector_params
from shk.stats.false_rejection import ALPHA
from shk.stats.nopo import MIN_CELL_COUNT

FROZEN_ON = datetime.date(2026, 10, 11)
SOURCE_CSVS = {
    "us_c7_2_covariates": "results/us_c7_2_covariates.csv",
    "us_c7_3_module2": "results/us_c7_3_module2.csv",
    "us_c7_3_module2_ci": "results/us_c7_3_module2_ci.csv",
    "us_c8_3b_power": "results/us_c8_3b_power.csv",
}
HEADER = """Parametri congelati di S9 (T54, US-C8.2), scritti una sola volta dallo script
scripts/us_c8_2_calibration.py e da non modificare. I parametri liberi sono calibrati
sulle sole stagioni di training (2000-01, 2010-11, 2020-21) con l'obiettivo unico della
decisione S9; gli altri sono fissati per costruzione. S10 li legge solo con
shk.model.frozen_params.load_frozen_params."""
COMMENTS = {
    "sources.us_c7_2_covariates": "SHA256 dei CSV da cui dipendono i parametri (T46, T47, T53)",
    "calibrated.c1_window": "Massimo dell'obiettivo sulle griglie del task T54 (log in [calibration])",
    "calibrated.d_adwin_delta": (
        "D_ADWIN: il training non identifica né δ né κ (nessun allarme di ADWIN con δ <= 0.5;\n"
        "41 combinazioni su 45 in parità esatta anche sulla puntata media). I valori vengono dalla\n"
        "regola di parità di secondo livello del 2026-10-11: δ = 0.002 congelato dalla decisione S5\n"
        "(ADWIN_DELTA), κ = 0.75 dal braccio D_PH, in cui κ è identificato."
    ),
    "calibration.objective": "Decisione S9",
    "fixed.c1_alpha": "Soglia di C1 (T52): moving block bootstrap della serie di δ del fit, B = 999, L_PW",
    "fixed.c1_alarm": "Decisioni del programmatore del 2026-10-11 (T52)",
    "fixed.lambda_min": "Decisione S9: λ in [0, 1], 0 se ĝ della finestra <= 0",
    "fixed.c0_lambda": "C0 = B_0.25; λ dei bracci con Modulo 2 non attivo (T51, decisione S9)",
    "fixed.module3_candidate": "Candidata del Modulo 3 scelta in T51",
    "fixed.covariates": "Specificazione del Modulo 2 (T46)",
    "fixed.out_of_support_min_count": "Regola fuori supporto di T49",
    "fixed.devig_method": "Decisione S7",
    "fixed.module1": "Modulo 1 raw con ELO_FITS (US-C4.1)",
    "fixed.n_seeds": "N_SEEDS dall'analisi di potenza di T53",
    "fixed.main_configuration_b0_over_f": "Configurazione principale (decisione S9)",
    "fixed.fallback_policy": "Ripiego forzato: default (a), politica attuale (T50)",
    "fixed.d_series": "D alimentata con δ (decisione S9); altri parametri del detector da drift.py",
    "c1_thresholds.2000-01": "Soglia di T = -S per fit alla W di C1, a L_PW (T52)",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_experiment(from_log: bool = False) -> None:
    """Calibra sul training (o rilegge il log con from_log), scrive il log e il file di congelamento."""
    repo_root = Path(__file__).resolve().parents[1]
    if FROZEN_PARAMS_PATH.exists():
        raise FileExistsError(f"{FROZEN_PARAMS_PATH} already exists: frozen parameters are written only once")
    log_path = repo_root / "results" / "us_c8_2_calibration_log.csv"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    frame = build_module2_frame(load_model_residuals())
    train = frame[frame["role"] == "training"]
    covariates = derive_specification(train).covariates
    if from_log:
        with open(log_path, newline="", encoding="utf-8") as f:
            records = finalize_log(list(csv.DictReader(f)))
    else:
        records = evaluate_calibration(train, covariates)
    with open(log_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(CALIBRATION_LOG_COLUMNS))
        writer.writeheader()
        writer.writerows(records)

    sections = build_sections(records, train, covariates, log_path, repo_root)
    write_frozen_params(FROZEN_PARAMS_PATH, render_frozen_params(FROZEN_ON, sections, COMMENTS, HEADER))


def build_sections(records: list[dict], train: pd.DataFrame, covariates: tuple[str, ...], log_path: Path,
                   repo_root: Path) -> dict[str, dict]:
    """Sezioni del file di congelamento dal log della calibrazione e dalle costanti del codice."""
    chosen = {r["family"]: r for r in records if r["chosen"]}
    inputs = [season_input_from_frame(train, s, covariates) for s in training_seasons(train)]
    _, thresholds = threshold_records(inputs)
    power = pd.read_csv(repo_root / SOURCE_CSVS["us_c8_3b_power"]).query("row_type == 'pooled'").iloc[0]
    adwin, ph = detector_params("adwin"), detector_params("page_hinkley")
    min_stake = dict(CONFIGURATIONS)[CALIBRATION_CONFIG]
    sections = {
        "sources": {k: _sha256(repo_root / v) for k, v in SOURCE_CSVS.items()},
        "calibrated": {
            "c1_window": int(chosen["C1"]["window"]),
            "c1_kappa": float(chosen["C1"]["kappa"]),
            "c2_global_window": int(chosen["C2_global"]["window"]),
            "c2_window": int(chosen["C2"]["window"]),
            "d_adwin_delta": float(chosen["D_ADWIN"]["detector_delta"]),
            "d_adwin_kappa": float(chosen["D_ADWIN"]["kappa"]),
            "d_page_hinkley_delta": float(chosen["D_PH"]["detector_delta"]),
            "d_page_hinkley_threshold": float(chosen["D_PH"]["detector_threshold"]),
            "d_page_hinkley_kappa": float(chosen["D_PH"]["kappa"]),
        },
        "calibration": {
            "objective": "mean final log-wealth over seeds and training seasons",
            "configuration": CALIBRATION_CONFIG,
            "n_seeds": N_CALIBRATION_SEEDS,
            "seed_scheme": "SeedSequence(SEED_S9).spawn(5)[4].spawn(3)[season].spawn(n_seeds)",
            "tie_rule": (
                "objective within 1e-12, then lower mean stake; on exact ties: values frozen by earlier "
                "decisions, then kappa of the most similar binary arm with identified kappa "
                "(other D detector, then C1, else 1), then grid order (2026-10-11)"
            ),
            "log_csv": "results/us_c8_2_calibration_log.csv",
            "log_sha256": _sha256(log_path),
        },
        "fixed": {
            "c1_alpha": ALPHA,
            "c1_n_boot": C1_N_BOOT,
            "c1_block_length": "politis_white_circular_of_fit_delta",
            "c1_threshold_seed_scheme": "SeedSequence(SEED_S9).spawn(5)[2]",
            "c1_alarm": "active and -S > threshold",
            "c1_alarm_count": "onsets",
            "lambda_min": 0.0,
            "lambda_max": 1.0,
            "stop_rule": "lambda = 0 if window g_hat <= 0",
            "c0_lambda": C0_LAMBDA,
            "inactive_lambda": INACTIVE_LAMBDA,
            "module3_candidate": CHOSEN_CANDIDATE,
            "covariates": list(covariates),
            "out_of_support_min_count": MIN_CELL_COUNT,
            "devig_method": "shin",
            "module1": "raw",
            "elo_fits": list(ELO_FITS),
            "n_seeds": int(power["n_seeds"]),
            "main_configuration_b0_over_f": int(round(1.0 / min_stake)),
            "fallback_policy": FALLBACK_MODEL_EV,
            "d_series": "delta",
            "d_base_lambda": BASE_LAMBDA,
            "d_adwin_clock": adwin["clock"],
            "d_adwin_max_buckets": adwin["max_buckets"],
            "d_adwin_min_window_length": adwin["min_window_length"],
            "d_adwin_grace_period": adwin["grace_period"],
            "d_page_hinkley_min_instances": ph["min_instances"],
            "d_page_hinkley_alpha": ph["alpha"],
            "d_page_hinkley_mode": ph["mode"],
        },
        "c1_thresholds": {s: thresholds[(s, int(chosen["C1"]["window"]))] for s in training_seasons(train)},
        "not_calibrated_on_training": {},
    }
    return sections


if __name__ == "__main__":
    run_experiment(from_log="--from-log" in sys.argv[1:])
