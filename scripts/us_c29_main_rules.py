"""Script: la versione principale dello schema con le tre regole di scelta dell'esito (shk.model.main_version).

Sulle 19 stagioni vere di validazione giocano, nelle tre configurazioni di puntata minima, il quarto
di Kelly senza supervisore e la versione principale, ciascuno con le regole R1, R2 e R3. Ogni versione
dello schema è confrontata con il quarto di Kelly della stessa regola (RULE_REFERENCES), con le
statistiche appaiate di shk.model.paired_inference. Con R1 la versione principale coincide con
C3_ref_stop_season_dx di us_c27.

Scrive results/us_c29_main_rules_seasons.csv (stagione × configurazione × agente) e
results/us_c29_main_rules_summary.csv (configurazione × agente).
"""

import csv
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from shk.model.frozen_params import frozen_params_path, load_frozen_params
from shk.model.main_version import RULE_ARMS, RULE_REFERENCES, main_setups, run_rules_season
from shk.model.module2_data import build_module2_frame
from shk.model.paired_inference import paired_statistics
from shk.model.residuals import load_model_residuals
from shk.model.validation_run import validation_inputs

SEED_S29: Final[int] = 20261116
WORKERS = 5
REPO_ROOT = Path(__file__).resolve().parents[1]
SEASONS_CSV = REPO_ROOT / "results" / "us_c29_main_rules_seasons.csv"
SUMMARY_CSV = REPO_ROOT / "results" / "us_c29_main_rules_summary.csv"
SEASON_COLUMNS: Final[tuple[str, ...]] = ("season", "fit_through", "config", "agent", "log_wealth", "n_bets",
                                          "n_alarms", "share_days_zero")
SUMMARY_COLUMNS: Final[tuple[str, ...]] = (
    "config", "agent", "reference", "n_seasons", "typical_capital", "mean_n_bets", "seasons_better",
    "seasons_worse", "seasons_with_stop", "share_days_zero", "sign_test_p", "wilcoxon_p", "capital_ratio",
    "capital_ratio_low", "capital_ratio_high",
)
PAIRED: Final[tuple[str, ...]] = ("seasons_better", "seasons_worse", "sign_test_p", "wilcoxon_p", "capital_ratio",
                                  "capital_ratio_low", "capital_ratio_high")


def summary_rows(season_rows: list[dict], seed: int = SEED_S29) -> list[dict]:
    """Per configurazione × agente: capitale tipico, puntate e, per lo schema, confronto con la sua regola."""
    df = pd.DataFrame(season_rows)
    out = []
    pairs = [(c, a) for c in df["config"].unique() for a in RULE_ARMS]
    for (config, agent), seq in zip(pairs, np.random.SeedSequence(seed).spawn(len(pairs))):
        rows = df[df["config"] == config]
        g = rows[rows["agent"] == agent].set_index("season").sort_index()
        row = {c: "" for c in SUMMARY_COLUMNS}
        row.update(config=config, agent=agent, n_seasons=len(g), typical_capital=float(np.exp(g["log_wealth"].mean())),
                   mean_n_bets=float(g["n_bets"].mean()))
        if agent in RULE_REFERENCES:
            ref = RULE_REFERENCES[agent]
            r = rows[rows["agent"] == ref].set_index("season").sort_index().loc[g.index]
            stats = paired_statistics(g["log_wealth"].to_numpy(float), r["log_wealth"].to_numpy(float),
                                      np.random.default_rng(seq))
            row.update(reference=ref, seasons_with_stop=int((g["share_days_zero"] > 0).sum()),
                       share_days_zero=float(g["share_days_zero"].mean()), **{k: stats[k] for k in PAIRED})
        out.append(row)
    return out


def _write(path: Path, columns: tuple[str, ...], rows: list[dict]) -> None:
    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(columns), restval="")
        writer.writeheader()
        writer.writerows(rows)


def run_experiment() -> None:
    params_path = frozen_params_path()
    params = load_frozen_params(params_path)
    frame = build_module2_frame(load_model_residuals())
    setups = main_setups(frame[frame["role"] == "training"], params)
    val = validation_inputs(frame, list(params.fixed["covariates"]))
    n = len(val)
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        season_rows = [r for rows in pool.map(run_rules_season, [str(params_path)] * n, [setups] * n, val)
                       for r in rows]
    summary = summary_rows(season_rows)
    _write(SEASONS_CSV, SEASON_COLUMNS, season_rows)
    _write(SUMMARY_CSV, SUMMARY_COLUMNS, summary)
    for r in summary:
        if r["config"] != "gbp_0.01":
            continue
        tail = "" if r["reference"] == "" else (
            f"  vs {r['reference']}: {r['seasons_better']}/{r['seasons_worse']}  zero days {r['share_days_zero']:.2f}"
            f"  wilcoxon p {r['wilcoxon_p']:.3f}")
        print(f"{r['agent']:<10} typical {r['typical_capital']:.3f}  bets {r['mean_n_bets']:.0f}{tail}")


if __name__ == "__main__":
    run_experiment()
