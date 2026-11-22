"""Script: le verifiche promesse dal capitolo 2 di thesis/TESI_kellybench.md.

1. Per ogni stagione di prova dal 2003-04 al 2023-24, con il modello di inizio stagione stimato sulle
   stagioni precedenti (come us_c42/us_c46), lo scarto medio ĝ dal mercato con cinque metodi per
   togliere il margine (Shin, proporzionale, additivo, potenza, odds ratio) e l'intervallo di
   confidenza al 95% di ĝ (Shin) con un bootstrap a blocchi mobili, lunghezza dei blocchi di
   Politis e White (§2.3, §2.6).
2. I falsi allarmi dell'ANOVA con la soglia nominale (§2.7): sui residui del riferimento del 2023-24
   (2002-03 → 2022-23), ogni gruppo di 40 partite consecutive confrontato con le altre partite del
   riferimento; quota di confronti oltre la soglia F al 5%, nell'ordine vero e con l'ordine mescolato.

Scrive in results/: us_c51_devig_seasons.csv e us_c51_nominal_false_alarms.csv.
"""

import os

os.environ["SHK_ELO_ENTRY"] = "plain"  # nuova tesi: nessuna regola per le neopromosse, prima di importare shk

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from scipy.stats import f as f_dist

from shk.market.devig import devig_probabilities
from shk.model.elo_fit import parse_season_start_year
from shk.model.frozen_agents import scheme_window
from shk.model.frozen_params import frozen_params_path, load_frozen_params
from shk.model.full_kelly_test import (
    FIRST_ROLLING_TEST, TEST_SEASON, fit_full_model, full_frame, full_residuals, past_reference, pooled_block_length,
    pooled_reference, season_label,
)
from shk.model.residuals import load_match_frame
from shk.stats.calibration import moving_block_indices

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS = REPO_ROOT / "results"
SEED_S51: Final[int] = 20261123
N_BOOT: Final[int] = 9999
WORKERS: Final[int] = 5
METHODS: Final[tuple[str, ...]] = ("shin", "proportional", "additive", "power", "odds_ratio")
OUTCOME: Final[dict[str, int]] = {"H": 0, "D": 1, "A": 2}
TEST_SEASONS: Final[tuple[str, ...]] = tuple(
    season_label(y) for y in range(parse_season_start_year(FIRST_ROLLING_TEST), parse_season_start_year(TEST_SEASON) + 1))


def season_frame(test_season: str) -> pd.DataFrame:
    df, _ = load_match_frame(roles=("history", "training", "validation", "test"))
    fit = fit_full_model(df, test_season)
    return full_frame(full_residuals(df, fit, True, test_season), test_season)


def run_season(args: tuple[int, str]) -> dict:
    i, season = args
    params = load_frozen_params(frozen_params_path())
    cov = list(params.fixed["covariates"])
    frame = season_frame(season)
    rows = frame[frame["season"] == season].sort_values("Date", kind="stable")
    y = rows["FTR"].map(OUTCOME).to_numpy()
    p = rows[["p_home", "p_draw", "p_away"]].to_numpy(np.float64)[np.arange(len(y)), y]
    odds = rows[["odds_home", "odds_draw", "odds_away"]].to_numpy(np.float64)
    out: dict = {"season": season, "n_matches": len(y)}
    for m in METHODS:
        q = devig_probabilities(odds, m)[np.arange(len(y)), y]
        out[f"g_hat_{m}"] = float(np.mean(np.log(p) - np.log(q)))
    delta = rows["delta"].to_numpy(np.float64)
    if not np.isclose(delta.mean(), out["g_hat_shin"], atol=1e-9):
        raise RuntimeError(f"{season}: δ del frame diverso da ĝ di Shin")
    test_ref = pooled_reference(rows, cov, [season])
    length = pooled_block_length(test_ref)
    rng = np.random.default_rng(np.random.SeedSequence(SEED_S51).spawn(len(TEST_SEASONS))[i])
    boot = delta[moving_block_indices(len(delta), length, N_BOOT, rng)].mean(axis=1)
    out.update(block_length=length, ci_low=float(np.quantile(boot, 0.025)), ci_high=float(np.quantile(boot, 0.975)))
    out["methods_all_negative"] = all(out[f"g_hat_{m}"] < 0 for m in METHODS)
    return out


def f_two_groups(a: np.ndarray, b: np.ndarray) -> float:
    """F dell'ANOVA a una via con due gruppi."""
    n_a, n_b = len(a), len(b)
    grand = (a.sum() + b.sum()) / (n_a + n_b)
    between = n_a * (a.mean() - grand) ** 2 + n_b * (b.mean() - grand) ** 2
    within = ((a - a.mean()) ** 2).sum() + ((b - b.mean()) ** 2).sum()
    return float(between / (within / (n_a + n_b - 2)))


def nominal_false_alarms(delta: np.ndarray, window: int) -> dict:
    """Quota di gruppi di `window` partite consecutive oltre la soglia F nominale al 5%, contro il resto."""
    n = len(delta)
    crit = float(f_dist.ppf(0.95, 1, n - 2))
    mean_hits = disp_hits = 0
    starts = range(0, n - window + 1)
    for s in starts:
        win = delta[s:s + window]
        rest = np.concatenate([delta[:s], delta[s + window:]])
        mean_hits += f_two_groups(win, rest) > crit
        disp_hits += f_two_groups(np.abs(win - np.median(win)), np.abs(rest - np.median(rest))) > crit
    return {"n_windows": len(starts), "critical_f": crit,
            "mean_rate": mean_hits / len(starts), "dispersion_rate": disp_hits / len(starts)}


def main() -> None:
    with ProcessPoolExecutor(WORKERS) as pool:
        seasons = list(pool.map(run_season, enumerate(TEST_SEASONS)))
    pd.DataFrame(seasons).to_csv(RESULTS / "us_c51_devig_seasons.csv", index=False)

    params = load_frozen_params(frozen_params_path())
    cov = list(params.fixed["covariates"])
    window = scheme_window(params)
    ref = pooled_reference(season_frame(TEST_SEASON), cov, past_reference(TEST_SEASON))
    rows = [{"order": "vero", **nominal_false_alarms(ref.delta, window)}]
    shuffled = np.random.default_rng(SEED_S51).permutation(ref.delta)
    rows.append({"order": "mescolato", **nominal_false_alarms(shuffled, window)})
    lag1 = float(np.corrcoef(ref.delta[:-1], ref.delta[1:])[0, 1])
    absdev = np.abs(ref.delta - np.median(ref.delta))
    lag1_abs = float(np.corrcoef(absdev[:-1], absdev[1:])[0, 1])
    for r in rows:
        r.update(window=window, n_reference=len(ref.delta), lag1_delta=lag1, lag1_absdev=lag1_abs)
    pd.DataFrame(rows).to_csv(RESULTS / "us_c51_nominal_false_alarms.csv", index=False)

    s = pd.DataFrame(seasons)
    print(s.round(4).to_string())
    print(pd.DataFrame(rows).round(4).to_string())


if __name__ == "__main__":
    main()
