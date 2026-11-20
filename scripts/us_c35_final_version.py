"""Script: la versione definitiva dello schema sulle 19 stagioni vere (shk.model.main_version, "F").

Versione definitiva: allarme e diagnosi della versione principale (riferimento = stagione di
calibrazione, soglie per stagione, diagnosi a due termini); la puntata dipende solo dalla diagnosi
del giorno: 0.25 senza allarme, 0.25·κ dopo un errore nei dati, STRUCTURAL_LAMBDA = 0.10 dopo un
errore strutturale, ogni riduzione finché dura l'allarme.

1. Capitale: nelle tre configurazioni di puntata minima giocano il quarto di Kelly senza supervisore
   e le versioni F, F_season (0.10 fino a fine stagione), M (0 fino a fine stagione, la versione
   principale precedente) e M_clear (0 finché dura l'allarme), con il confronto appaiato con il
   quarto di Kelly (shk.model.paired_inference). La griglia STRUCTURAL_GRID dà il capitale della
   regola di F con altri livelli dopo l'errore strutturale (puntata minima di £0,01).
2. Controllo a pari esposizione per F, senza puntata minima (shk.model.timing_placebo con il livello
   più basso a 0.10): calendari permutati, ruotati e di altre stagioni, frazione fissa di pari
   esposizione, e la distanza dal mercato prima della partita nelle giornate con la puntata ridotta.

Scrive results/us_c35_final_version_seasons.csv (stagione × configurazione × agente),
results/us_c35_final_version_summary.csv (configurazione × agente) e
results/us_c35_final_version_placebo.csv (righe di shk.model.timing_placebo.COLUMNS).
Con --draws N usa N estrazioni placebo e scrive in build/final_version/ (prova rapida).
"""

import csv
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from shk.kelly.environment import run_paired_backtest
from shk.model.frozen_agents import n_alarms, share_lambda_zero
from shk.model.frozen_params import frozen_params_path, load_frozen_params
from shk.model.main_version import MainSetup, build_agents, main_agent, main_setups, reference_supervisor
from shk.model.main_version import STRUCTURAL_LAMBDA
from shk.model.module2_data import build_module2_frame
from shk.model.paired_backtest import CONFIGURATIONS
from shk.model.paired_inference import paired_statistics
from shk.model.residuals import load_model_residuals
from shk.model.timing_placebo import COLUMNS, N_DRAWS, extract_schedules, mean_lambda, placebo_tables
from shk.model.timing_placebo import run_constant_season
from shk.model.agent_c import SCHEME_STOP_CLEAR
from shk.model.validation_run import ValidationSeason, validation_inputs

SEED_S35: Final[int] = 20261120
WORKERS = 5
ARMS: Final[tuple[str, ...]] = ("B_0.25", "F", "F_season", "M", "M_clear")
STRUCTURAL_GRID: Final[tuple[float, ...]] = (0.0, 0.05, 0.15, 0.1875)
PLACEBO_ARMS: Final[dict[str, str]] = {"F": "R1"}
SEASON_COLUMNS: Final[tuple[str, ...]] = ("season", "fit_through", "config", "agent", "log_wealth", "n_bets",
                                          "n_alarms", "share_days_zero", "share_days_reduced")
SUMMARY_COLUMNS: Final[tuple[str, ...]] = (
    "config", "agent", "n_seasons", "typical_capital", "mean_n_bets", "seasons_better", "seasons_worse",
    "seasons_with_structural", "share_days_zero", "share_days_reduced", "sign_test_p", "wilcoxon_p",
    "capital_ratio", "capital_ratio_low", "capital_ratio_high",
)
PAIRED: Final[tuple[str, ...]] = ("seasons_better", "seasons_worse", "sign_test_p", "wilcoxon_p", "capital_ratio",
                                  "capital_ratio_low", "capital_ratio_high")


def output_paths(quick: bool) -> dict[str, Path]:
    root = Path(__file__).resolve().parents[1]
    folder = root / "build" / "final_version" if quick else root / "results"
    return {k: folder / f"us_c35_final_version_{k}.csv" for k in ("seasons", "summary", "placebo")}


def grid_name(level: float) -> str:
    return f"F_{level:g}"


def _share_reduced(agent) -> float:
    lam = np.array(list(agent.lambda_by_date.values()))
    return float(np.mean(lam < 0.25 - 1e-12)) if lam.size else float("nan")


def run_season(params_path: str, setups: dict[str, MainSetup], season: ValidationSeason) -> list[dict]:
    """La stagione vera nelle tre configurazioni: una riga per configurazione × agente (più la griglia)."""
    params = load_frozen_params(params_path)
    inp, setup = season.inp, setups[season.fit]
    rows = []
    for config, min_stake in CONFIGURATIONS:
        supervisor = reference_supervisor(params, inp, setup)
        agents = build_agents(params, setup, supervisor, ARMS)
        if config == "gbp_0.01":
            agents += [main_agent(grid_name(lv), params, setup, supervisor, stop=SCHEME_STOP_CLEAR,
                                  structural_lambda=lv) for lv in STRUCTURAL_GRID]
        runs = run_paired_backtest(agents, inp.dates, inp.probs, inp.odds, inp.outcomes, min_stake,
                                   fallback_policy=params.fixed["fallback_policy"])
        for run, agent in zip(runs, agents):
            final = float(run.wealth[0, -1])
            scheme = run.name != "B_0.25"
            rows.append({"season": inp.season, "fit_through": season.fit, "config": config, "agent": run.name,
                         "log_wealth": float(np.log(final)) if final > 0.0 else -np.inf,
                         "n_bets": int(run.n_bets[0]), "n_alarms": n_alarms(agent),
                         "share_days_zero": share_lambda_zero(agent),
                         "share_days_reduced": _share_reduced(agent) if scheme else float("nan")})
    return rows


def run_schedule(params_path: str, setups: dict[str, MainSetup], season: ValidationSeason):
    """Calendario di F senza puntata minima, con il livello più basso a STRUCTURAL_LAMBDA."""
    params = load_frozen_params(params_path)
    setup = setups[season.fit]
    agents = build_agents(params, setup, reference_supervisor(params, season.inp, setup), ("B_0.25", "F"))
    return extract_schedules(params, season, agents, PLACEBO_ARMS, floor=STRUCTURAL_LAMBDA)


def summary_rows(season_rows: list[dict], seed: int = SEED_S35) -> list[dict]:
    """Per configurazione × agente: capitale tipico e confronto appaiato con il quarto di Kelly."""
    df = pd.DataFrame(season_rows)
    out = []
    pairs = [(c, a) for c in df["config"].unique() for a in df.loc[df["config"] == c, "agent"].unique()]
    for (config, agent), seq in zip(pairs, np.random.SeedSequence(seed).spawn(len(pairs))):
        rows = df[df["config"] == config]
        g = rows[rows["agent"] == agent].set_index("season").sort_index()
        row = {c: "" for c in SUMMARY_COLUMNS}
        row.update(config=config, agent=agent, n_seasons=len(g), typical_capital=float(np.exp(g["log_wealth"].mean())),
                   mean_n_bets=float(g["n_bets"].mean()))
        if agent != "B_0.25":
            ref = rows[rows["agent"] == "B_0.25"].set_index("season").sort_index().loc[g.index]
            stats = paired_statistics(g["log_wealth"].to_numpy(float), ref["log_wealth"].to_numpy(float),
                                      np.random.default_rng(seq))
            row.update(seasons_with_structural=int((g["n_alarms"] > 0).sum()),
                       share_days_zero=float(g["share_days_zero"].mean()),
                       share_days_reduced=float(g["share_days_reduced"].mean()), **{k: stats[k] for k in PAIRED})
        out.append(row)
    return out


def _write(path: Path, columns: tuple[str, ...], rows: list[dict]) -> None:
    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(columns), restval="")
        writer.writeheader()
        writer.writerows(rows)


def run_experiment(n_draws: int | None = None) -> None:
    paths = output_paths(quick=n_draws is not None)
    paths["seasons"].parent.mkdir(parents=True, exist_ok=True)
    draws = N_DRAWS if n_draws is None else n_draws
    params_path = frozen_params_path()
    params = load_frozen_params(params_path)
    frame = build_module2_frame(load_model_residuals())
    setups = main_setups(frame[frame["role"] == "training"], params)
    val = validation_inputs(frame, list(params.fixed["covariates"]))
    n, p = len(val), str(params_path)
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        season_rows = [r for rows in pool.map(run_season, [p] * n, [setups] * n, val) for r in rows]
        schedules = list(pool.map(run_schedule, [p] * n, [setups] * n, val))
        lams = {arm: mean_lambda(schedules, arm) for arm in PLACEBO_ARMS}
        constant = list(pool.map(run_constant_season, [p] * n, val, [lams] * n, [PLACEBO_ARMS] * n))
    summary = summary_rows(season_rows)
    placebo_rows, _ = placebo_tables(schedules, constant, lams, draws, np.random.SeedSequence([SEED_S35, 1]),
                                     PLACEBO_ARMS)
    _write(paths["seasons"], SEASON_COLUMNS, season_rows)
    _write(paths["summary"], SUMMARY_COLUMNS, summary)
    _write(paths["placebo"], COLUMNS, placebo_rows)
    for r in summary:
        if r["config"] != "gbp_0.01":
            continue
        tail = "" if r["agent"] == "B_0.25" else (
            f"  vs B_0.25 {r['seasons_better']}/{r['seasons_worse']}  reduced days {r['share_days_reduced']:.3f}"
            f"  wilcoxon p {r['wilcoxon_p']:.3f}")
        print(f"{r['agent']:<10} typical {r['typical_capital']:.4f}  bets {r['mean_n_bets']:.0f}{tail}")
    for r in placebo_rows:
        if r["row_type"] in ("capital", "expected_delta", "constant"):
            print(f"{r['row_type']:<15} {r['placebo']:<18} observed {float(r['observed']):.4f}"
                  f"  placebo median {r.get('placebo_median', r.get('placebo_mean', ''))}"
                  f"  p {r.get('p_value', '')}")


if __name__ == "__main__":
    args = sys.argv[1:]
    run_experiment(int(args[args.index("--draws") + 1]) if "--draws" in args else None)
