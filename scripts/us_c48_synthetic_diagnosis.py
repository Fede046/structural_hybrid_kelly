"""Script: la diagnosi del ricalibratore su scenari sintetici in cui la risposta giusta è nota.

Riferimento della stagione 2023-24 (stagioni 2002-03..2022-23 con le quote, modello di inizio stagione), soglie
dell'allarme e coefficienti della scomposizione come in us_c46. Finestre di 40 partite, N_WINDOWS per scenario:
- tipo di partite: 40 partite del riferimento estratte a caso fra la quota q (20%, 10%, 5%) di quelle su cui il
  riferimento si aspetta più errore (dispersione attesa più alta, o residuo atteso più basso), ciascuna con il
  suo δ vero: il modello si comporta come al solito, cambia solo il tipo di partite -> risposta giusta "dati";
- nessun cambiamento: 40 partite consecutive del riferimento (blocchi mobili);
- modello che cambia: gli stessi blocchi con δ più disperso, δ' = mediana + s (δ − mediana), s = 1,3 e 1,5,
  o spostato, δ' = δ − c, c = 0,05 e 0,08 -> risposta giusta "strutturale".
Per ogni scenario: quota di finestre con allarme e, fra queste, quota diagnosticata come errore nei dati con la
soglia della parte non spiegata su una finestra singola (regola fino al 2026-11-21) e con quella stagionale.

Scrive results/us_c48_synthetic_diagnosis.csv.
"""

import os

os.environ["SHK_ELO_ENTRY"] = "plain"  # nuova tesi: nessuna regola per le neopromosse, prima di importare shk

from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from shk.model.agent_c import reference_statistics
from shk.model.frozen_agents import scheme_window
from shk.model.frozen_params import frozen_params_path, load_frozen_params
from shk.model.full_kelly_test import (SEED_S41, TEST_SEASON, fit_full_model, full_frame, full_residuals,
                                       past_reference, pooled_alarm_thresholds, pooled_block_length,
                                       pooled_reference, pooled_unexplained_thresholds, previous_season)
from shk.model.residuals import load_match_frame
from shk.model.two_fold_diagnosis import calibrate_reference_diagnosis, unexplained_parts
from shk.stats.calibration import moving_block_indices

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT = REPO_ROOT / "results" / "us_c48_synthetic_diagnosis.csv"
SEED_S48: Final[int] = 20261126
N_WINDOWS: Final[int] = 4000
SHARES: Final[tuple[float, ...]] = (0.20, 0.10, 0.05)
SCALES: Final[tuple[float, ...]] = (1.3, 1.5)
SHIFTS: Final[tuple[float, ...]] = (0.05, 0.08)


def main() -> None:
    params = load_frozen_params(frozen_params_path())
    cov = list(params.fixed["covariates"])
    w = scheme_window(params)
    df, _ = load_match_frame(roles=("history", "training", "validation", "test"))
    season = TEST_SEASON
    fit = fit_full_model(df, season)
    frame = full_frame(full_residuals(df, fit, True, season), season)
    ref = pooled_reference(frame, cov, past_reference(season))
    length = pooled_block_length(ref)
    thr_seq, diag_seq, unexplained_seq = np.random.SeedSequence(SEED_S41).spawn(4)[:3]
    calendar = frame[frame["season"] == previous_season(season)]["Date"].to_numpy("datetime64[ns]")
    mt, dt = pooled_alarm_thresholds(ref, calendar, w, length, np.random.default_rng(thr_seq))
    d = calibrate_reference_diagnosis(ref.x, ref.delta, w, length, np.random.default_rng(diag_seq))
    sm, sd = pooled_unexplained_thresholds(ref, d, calendar, w, length, np.random.default_rng(unexplained_seq))
    design = np.concatenate([np.ones((ref.x.shape[0], 1)), ref.x], axis=1)
    rng = np.random.default_rng(SEED_S48)

    def evaluate(kind: str, scenario: str, idx: np.ndarray, y: np.ndarray) -> dict:
        f_mean, f_disp = reference_statistics(ref.delta, y)
        by_m, by_d = f_mean > mt, f_disp > dt
        alarm = by_m | by_d
        um, ud = unexplained_parts(ref.x[idx], y, d.median, d.beta_mean, d.beta_dispersion)
        old = (by_m & (um > d.mean_threshold)) | (by_d & (ud > d.dispersion_threshold))
        new = (by_m & (um > sm)) | (by_d & (ud > sd))
        n = int(alarm.sum())
        return {"kind": kind, "scenario": scenario, "windows": N_WINDOWS, "alarm_rate": float(alarm.mean()),
                "alarms": n, "data_share_window_rule": float((alarm & ~old).sum() / n) if n else np.nan,
                "data_share_season_rule": float((alarm & ~new).sum() / n) if n else np.nan,
                "unexplained_mean_window": d.mean_threshold, "unexplained_dispersion_window": d.dispersion_threshold,
                "unexplained_mean_season": sm, "unexplained_dispersion_season": sd}

    rows = []
    for name, score in (("dispersione attesa", design @ d.beta_dispersion), ("residuo atteso", -(design @ d.beta_mean))):
        for q in SHARES:
            pool = np.flatnonzero(score >= np.quantile(score, 1 - q))
            idx = np.array([rng.choice(pool, size=w, replace=False) for _ in range(N_WINDOWS)])
            rows.append(evaluate("dati", f"{name}, {round(q * 100)}% delle partite", idx, ref.delta[idx]))
    blocks = moving_block_indices(ref.delta.shape[0], length, N_WINDOWS, rng)[:, :w]
    rows.append(evaluate("nessuno", "nessun cambiamento", blocks, ref.delta[blocks]))
    for s in SCALES:
        rows.append(evaluate("strutturale", f"dispersione x{s}", blocks, d.median + s * (ref.delta[blocks] - d.median)))
    for c in SHIFTS:
        rows.append(evaluate("strutturale", f"media -{c}", blocks, ref.delta[blocks] - c))
    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    pd.set_option("display.width", 220)
    print(f"soglie allarme media {mt:.3f} dispersione {dt:.3f}")
    print(out.drop(columns=[c for c in out.columns if c.startswith("unexplained")]).round(3).to_string())


if __name__ == "__main__":
    main()
