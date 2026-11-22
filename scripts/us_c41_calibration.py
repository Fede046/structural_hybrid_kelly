"""Script: calibrazione della nuova tesi (thesis/TESI_kellybench.md, capitolo 4), senza il 2023-24.

Stima il modello Elo-Davidson sulle stagioni dal 2000-01 al 2022-23, costruisce il riferimento
(stagioni dal 2002-03 al 2022-23), calibra le soglie dell'allarme per stagione e la diagnosi a due
termini. Non carica il 2023-24: le regole sono fissate prima del test.

Scrive results/us_c41_calibration.csv (una riga) e results/us_c41_reference_seasons.csv (media e
dispersione di δ per stagione del riferimento, e le giornate in cui, dentro il riferimento stesso,
l'allarme supererebbe le soglie: è solo un'informazione, non cambia le regole).
"""

import os

os.environ["SHK_ELO_ENTRY"] = "plain"  # nuova tesi: nessuna regola per le neopromosse, prima di importare shk

import csv
from pathlib import Path

import numpy as np

from shk.model.frozen_agents import scheme_window
from shk.model.frozen_params import frozen_params_path, load_frozen_params
from shk.model.full_kelly_test import (
    CALENDAR_SEASON, DATA_LAMBDA, FREE_LAMBDA, REFERENCE, SEED_S41, STRUCTURAL_LAMBDA, fit_full_model, full_frame,
    full_residuals, pooled_alarm_thresholds, pooled_block_length, pooled_reference,
)
from shk.model.agent_c import reference_statistics
from shk.model.model_age import dispersion
from shk.model.season_thresholds import decision_ends
from shk.model.residuals import load_match_frame
from shk.model.two_fold_diagnosis import calibrate_reference_diagnosis

REPO_ROOT = Path(__file__).resolve().parents[1]
CALIBRATION_CSV = REPO_ROOT / "results" / "us_c41_calibration.csv"
SEASONS_CSV = REPO_ROOT / "results" / "us_c41_reference_seasons.csv"


def run_experiment() -> None:
    params = load_frozen_params(frozen_params_path())
    covariates = list(params.fixed["covariates"])
    w = scheme_window(params)
    df, _ = load_match_frame(roles=("history", "training", "validation"))
    fit = fit_full_model(df)
    print(f"fit: K={fit.k:.3f} h={fit.h:.2f} nu={fit.nu:.4f} c={fit.c:.4f}")
    frame = full_frame(full_residuals(df, fit, include_test=False))
    ref = pooled_reference(frame, covariates)
    length = pooled_block_length(ref)
    thr_seq, diag_seq = np.random.SeedSequence(SEED_S41).spawn(4)[:2]
    calendar = frame[frame["season"] == CALENDAR_SEASON]["Date"].to_numpy("datetime64[ns]")
    mean_thr, disp_thr = pooled_alarm_thresholds(ref, calendar, w, length, np.random.default_rng(thr_seq))
    diag = calibrate_reference_diagnosis(ref.x, ref.delta, w, length, np.random.default_rng(diag_seq))
    row = {"k": fit.k, "h": fit.h, "nu": fit.nu, "c": fit.c, "n_reference": int(ref.delta.shape[0]),
           "reference_first": REFERENCE[0], "reference_last": REFERENCE[-1], "window": w, "block_length": length,
           "mean_threshold": mean_thr, "dispersion_threshold": disp_thr,
           "unexplained_mean_threshold": diag.mean_threshold,
           "unexplained_dispersion_threshold": diag.dispersion_threshold, "reference_median": diag.median,
           "reference_mean": float(ref.delta.mean()), "reference_dispersion": dispersion(ref.delta),
           "lambda_free": FREE_LAMBDA, "lambda_data": DATA_LAMBDA, "lambda_structural": STRUCTURAL_LAMBDA,
           "seed": SEED_S41}
    season_rows = []
    for s in REFERENCE:
        m = ref.seasons == s
        y = ref.delta[m]
        ends = decision_ends(ref.dates[m], w)
        f_mean, f_disp = reference_statistics(ref.delta, y[ends[:, None] - w + np.arange(w)[None, :]])
        alarm = (f_mean > mean_thr) | (f_disp > disp_thr)
        season_rows.append({"season": s, "n": int(m.sum()), "mean_delta": float(y.mean()), "dispersion": dispersion(y),
                            "n_decisions": int(ends.shape[0]), "alarm_days": int(alarm.sum()),
                            "max_mean_ratio": float(f_mean.max() / mean_thr),
                            "max_dispersion_ratio": float(f_disp.max() / disp_thr)})
    row["reference_seasons_with_alarm"] = int(sum(r["alarm_days"] > 0 for r in season_rows))
    for path, rows in ((CALIBRATION_CSV, [row]), (SEASONS_CSV, season_rows)):
        with open(path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    for k, v in row.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    run_experiment()
