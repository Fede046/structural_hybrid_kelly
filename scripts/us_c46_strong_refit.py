"""Script: la ricalibrazione senza riduzione della puntata, con una ristima che pesa di più il presente.

Variante esplorativa del 2026-11-21, decisa dopo aver visto us_c45: si toglie del tutto la riduzione della
puntata (λ = 1 sempre) e il framework agisce solo ristimando il modello. Le regole sono quelle di us_c45:
per ogni stagione S dal 2003-04 al 2023-24 il modello iniziale è stimato sulle stagioni precedenti con
pesi uguali; il giorno in cui comincia un errore strutturale (dopo almeno una giornata senza allarme
dall'ultima ristima), prima delle partite, K, h, ν si ristimano; dal giorno dopo il supervisore giudica il
modello nuovo (riferimento, soglie e diagnosi ricalcolati con gli stessi seed). Dal 2026-11-22 la soglia
della parte non spiegata ha la stessa severità di quella del supervisore (pooled_unexplained_thresholds:
massimo sulla stagione, quantile α/2) invece di essere calcolata su una finestra singola. Due ristime:
- "uguale": log-loss con lo stesso peso per tutte le stagioni passate più la stagione in corso (us_c45);
- "recente": log-loss pesata, il peso di una partita si dimezza a ogni stagione di età (HALF_LIFE = 1).

Scrive results/us_c46_strong_refit_seasons.csv, results/us_c46_strong_refit_refits.csv e
results/raw/us_c46/<versione>_<stagione>.npz (con ratios: statistiche dell'allarme divise per la soglia, del
modello in uso giorno per giorno; ratios0: le stesse del modello di inizio stagione; diag e diag0: la diagnosi
del giorno, none, structural o compositional, del modello in uso e di quello di inizio stagione).
"""

import os

os.environ["SHK_ELO_ENTRY"] = "plain"  # nuova tesi: nessuna regola per le neopromosse, prima di importare shk

import csv
import importlib.util
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from shk.kelly.environment import run_paired_backtest
from shk.kelly.outcome_rules import with_outcome_rule
from shk.model.agent_c import SCHEME_STOP_CLEAR, Module2Supervisor, ReferenceData
from shk.model.frozen_agents import scheme_window
from shk.model.frozen_params import frozen_params_path, load_frozen_params
from shk.model.full_kelly_test import (FREE_LAMBDA, KAPPA, SEED_S41, STRUCTURAL_LAMBDA, ScheduledKellyAgent,
                                       fit_full_model, full_frame, full_residuals, past_reference,
                                       pooled_alarm_thresholds, pooled_block_length, pooled_reference,
                                       pooled_unexplained_thresholds, previous_season, test_input, weighted_refit)
from shk.model.paired_backtest import CONFIGURATIONS
from shk.model.residuals import load_match_frame
from shk.model.two_fold_diagnosis import TwoFoldSchemeAgent, calibrate_reference_diagnosis

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS = REPO_ROOT / "results"
RAW = RESULTS / "raw" / "us_c46"
MIN_STAKE: Final[float] = dict(CONFIGURATIONS)["gbp_0.01"]
HALF_LIFE: Final[float] = 1.0
SEASONS: Final[tuple[str, ...]] = tuple(f"{y}-{str(y + 1)[-2:]}" for y in range(2003, 2024))

_spec = importlib.util.spec_from_file_location("us_c45", REPO_ROOT / "scripts" / "us_c45_reparam.py")
us_c45 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(us_c45)


def model_setup(df: pd.DataFrame, season: str, fit, cov: list[str], w: int, fallback: str):
    """Ingressi della stagione e diagnosi giorno per giorno con i parametri `fit` (come us_c45.model_setup,
    ma con le soglie stagionali della parte non spiegata, dal terzo generatore di SEED_S41)."""
    frame = full_frame(full_residuals(df, fit, True, season), season)
    ref = pooled_reference(frame, cov, past_reference(season))
    length = pooled_block_length(ref)
    thr_seq, diag_seq, unexplained_seq = np.random.SeedSequence(SEED_S41).spawn(4)[:3]
    calendar = frame[frame["season"] == previous_season(season)]["Date"].to_numpy("datetime64[ns]")
    mt, dt = pooled_alarm_thresholds(ref, calendar, w, length, np.random.default_rng(thr_seq))
    diag = calibrate_reference_diagnosis(ref.x, ref.delta, w, length, np.random.default_rng(diag_seq))
    um, ud = pooled_unexplained_thresholds(ref, diag, calendar, w, length, np.random.default_rng(unexplained_seq))
    diag = diag._replace(mean_threshold=um, dispersion_threshold=ud)
    inp = test_input(frame, cov, season)
    sup = Module2Supervisor(inp.season, inp.dates, inp.x, cov, w, devig_method="shin",
                            reference=ReferenceData(ref.x, ref.delta))
    agent = with_outcome_rule(TwoFoldSchemeAgent, "R1")("supervisore", sup, KAPPA, mt, dt, diag, SCHEME_STOP_CLEAR,
                                                       base_lambda=FREE_LAMBDA, structural_lambda=STRUCTURAL_LAMBDA)
    run_paired_backtest([agent], inp.dates, inp.probs, inp.odds, inp.outcomes, MIN_STAKE, fallback_policy=fallback)
    days = np.unique(inp.dates)
    d = agent.diagnosis_by_date
    stats = [sup.reference_diagnostics(np.datetime64(x, "ns")) for x in days]
    ratios = np.array([[s[0] / mt, s[1] / dt] if s else [np.nan, np.nan] for s in stats])
    return inp, np.array([d.get(np.datetime64(x, "ns"), "none") for x in days], dtype=object), ratios


def run_season(args: tuple[str, str]) -> tuple[dict, list[dict]]:
    season, version = args
    params = load_frozen_params(frozen_params_path())
    cov = list(params.fixed["covariates"])
    w = scheme_window(params)
    fallback = params.fixed["fallback_policy"]
    df, _ = load_match_frame(roles=("history", "training", "validation", "test"))
    fit = fit_full_model(df, season)
    inp0, diag0, ratios0 = model_setup(df, season, fit, cov, w, fallback)
    days = np.unique(inp0.dates)
    probs = inp0.probs.copy()
    ratios = ratios0.copy()  # statistiche dell'allarme / soglia (media, dispersione) del modello in uso, per giornata
    diag = diag0.copy()  # diagnosi del giorno del modello in uso: none, structural, compositional
    current_diag, start, refits = diag0, 0, []
    while True:
        seen_clear = start == 0
        onset = None
        for j in range(start + (0 if start == 0 else 1), len(days)):
            if current_diag[j] == "none":
                seen_clear = True
            elif current_diag[j] == "structural" and seen_clear:
                onset = j
                break
        if onset is None:
            break
        before = np.datetime64(days[onset], "ns")
        fit = (us_c45.refit(df, season, before) if version == "uguale"
               else weighted_refit(df, season, before, HALF_LIFE))
        inp, new_diag, new_ratios = model_setup(df, season, fit, cov, w, fallback)
        rows = inp.dates >= days[onset]
        probs[rows] = inp.probs[rows]
        ratios[onset + 1:] = new_ratios[onset + 1:]  # dal giorno dopo il supervisore giudica il modello nuovo
        diag[onset + 1:] = new_diag[onset + 1:]
        refits.append({"version": version, "season": season, "refit": len(refits) + 1, "day": onset + 1,
                       "date": str(pd.Timestamp(days[onset]).date()), "k": fit.k, "h": fit.h, "nu": fit.nu})
        current_diag, start = new_diag, onset
    ones = {np.datetime64(d, "ns"): 1.0 for d in days}
    full, run = (run_paired_backtest([ScheduledKellyAgent(n, ones)], inp0.dates, p, inp0.odds, inp0.outcomes,
                                     MIN_STAKE, fallback_policy=fallback)[0] for n, p in (("pieno", inp0.probs),
                                                                                          ("ristima", probs)))
    k = np.arange(probs.shape[0])
    y = inp0.outcomes[0]
    RAW.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(RAW / f"{version}_{season}.npz", dates=inp0.dates, probs0=inp0.probs, probs=probs,
                        odds=inp0.odds, outcomes=inp0.outcomes, wealth=run.wealth[0], wealth_full=full.wealth[0],
                        ratios=ratios, ratios0=ratios0, diag=diag.astype(str), diag0=diag0.astype(str), refit_days=np.array([r["day"] - 1 for r in refits], dtype=np.int64))
    row = {"version": version, "season": season, "n_refits": len(refits),
           "structural_days": int((diag == "structural").sum()), "data_error_days": int((diag == "compositional").sum()), "full_kelly": float(full.wealth[0, -1]),
           "final_capital": float(run.wealth[0, -1]), "full_ruined": bool(full.ruined[0]), "ruined": bool(run.ruined[0]),
           "log_loss_used": float(-np.log(probs[k, y]).mean()), "log_loss_original": float(-np.log(inp0.probs[k, y]).mean())}
    return row, refits


def _write(path: Path, rows: list[dict]) -> None:
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, restval="")
        writer.writeheader()
        writer.writerows(rows)


def run_experiment(seasons=SEASONS) -> None:
    jobs = [(s, v) for v in ("recente", "uguale") for s in seasons]
    with ProcessPoolExecutor(max_workers=5) as pool:
        out = list(pool.map(run_season, jobs))
    rows = [r for r, _ in out]
    refits = [x for _, rr in out for x in rr]
    _write(RESULTS / "us_c46_strong_refit_seasons.csv", rows)
    if refits:
        _write(RESULTS / "us_c46_strong_refit_refits.csv", refits)
    d = pd.DataFrame(rows)
    pd.set_option("display.width", 250)
    for v, g in d.groupby("version"):
        g = g.set_index("season")
        print(f"== {v}")
        print(g[["n_refits", "full_kelly", "final_capital", "ruined", "log_loss_original", "log_loss_used"]].round(5).to_string())
        print("typical full", float(np.exp(np.log(g.full_kelly).mean())), "refit", float(np.exp(np.log(g.final_capital).mean())))
        a = g[g.n_refits > 0]
        diff = np.log(a.final_capital) - np.log(a.full_kelly)
        nz = diff[diff.abs() > 1e-12]
        print("better", int((diff > 1e-12).sum()), "worse", int((diff < -1e-12).sum()),
              "wilcoxon", float(wilcoxon(nz).pvalue) if len(nz) else "", "mean log-loss change",
              float((a.log_loss_used - a.log_loss_original).mean()) if len(a) else "")
    if refits:
        print(pd.DataFrame(refits).round(3).to_string())


if __name__ == "__main__":
    run_experiment(tuple(sys.argv[1:]) or SEASONS)
