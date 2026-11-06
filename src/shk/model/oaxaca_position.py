"""Verifica di robustezza: Oaxaca-Blinder dello schema con e senza la covariata "position".

Perché la decomposizione separa poco i due tipi di errore (decisione del 2026-11-05):
- righe "r2": R² della regressione di δ sulle covariate congelate, per stagione intera;
- righe "component_sd": deviazione standard delle componenti three-fold sulle finestre adiacenti
  delle stagioni di validazione (le 2W partite osservate più recenti alla data, A le più vecchie),
  con e senza "position", e correlazione fra componente compositiva e interazione. Nelle finestre
  adiacenti "position" non si sovrappone mai fra A e B, e la decomposizione estrapola;
- righe "threshold": soglia strutturale senza "position", ricalibrata sul training come quelle
  congelate (finestre adiacenti: prime 2W posizioni dei ricampionamenti; riferimento fisso:
  agent_c.calibrate_reference_thresholds), seed SeedSequence(SEED_S15).spawn(2 · numero di fit);
- righe "diagnosis": sulle stagioni di validazione osservate, giornate con allarme e quota di
  diagnosi strutturali, con e senza "position", per le finestre adiacenti (C3) e il riferimento
  fisso (C3_ref). L'allarme non dipende dalle covariate: cambia solo la diagnosi;
- righe "wealth": C3, C3_stop, C3_ref, C3_ref_stop con e senza "position" e B_0.25 su N_CHECK_SEEDS
  seed (i primi dell'esecuzione congelata, quindi appaiati): somma sulle stagioni della mediana di
  ln W_T nella configurazione principale e stagioni con mediana migliore di B_0.25.
Le soglie di media e dispersione restano quelle dello schema e della variante.
"""

import math
from collections.abc import Mapping, Sequence
from typing import Final, NamedTuple

import numpy as np
import pandas as pd

from shk.kelly.agents import AGENT_B_LAMBDA, FractionalKellyAgent
from shk.kelly.environment import run_paired_backtest
from shk.model.agent_c import (
    SCHEME_STOP_CLEAR,
    SCHEME_STOP_SEASON,
    Module2Supervisor,
    ReferenceData,
    SchemeAgent,
    calibrate_reference_thresholds,
)
from shk.model.elo_fit import parse_season_start_year
from shk.model.frozen_agents import scheme_window
from shk.model.frozen_params import FrozenParams, load_frozen_params
from shk.model.paired_backtest import CONFIGURATIONS
from shk.model.scheme_reference_run import reference_setups
from shk.model.scheme_run import evaluate_scheme, fit_block_length, scheme_thresholds
from shk.model.season_input import SeasonInput, season_input_from_frame, training_seasons
from shk.model.validation_run import CONFIG_NAMES, METRICS, run_metrics
from shk.stats.calibration import compute_order_statistic_index, moving_block_indices
from shk.stats.oaxaca import three_fold_batch

SEED_S15: Final[int] = 20261107
N_CHECK_SEEDS: Final[int] = 100
POSITION: Final[str] = "position"
VARIANTS: Final[tuple[str, ...]] = ("with_position", "without_position")
CHECK_ARMS: Final[tuple[str, ...]] = (
    "B_0.25", "C3", "C3_stop", "C3_ref", "C3_ref_stop",
    "C3_nopos", "C3_stop_nopos", "C3_ref_nopos", "C3_ref_stop_nopos",
)
POSITION_COLUMNS: Final[tuple[str, ...]] = (
    "row_type", "season", "fit_through", "covariates", "design", "arm", "component", "value", "corr_comp_inter",
    "n_alarm_dates", "n_structural", "share_structural", "sum_median_log_wealth", "typical_capital",
    "seasons_better_than_b025", "n_seeds",
)


class PositionSetup(NamedTuple):
    """Soglie e stagione di calibrazione di un fit, con e senza "position"."""

    mean_threshold: float
    dispersion_threshold: float
    structural_threshold: float          # finestre adiacenti, con "position" (congelata)
    structural_threshold_nopos: float    # finestre adiacenti, senza "position"
    ref_mean_threshold: float
    ref_dispersion_threshold: float
    ref_structural_threshold: float      # riferimento fisso, con "position"
    ref_structural_threshold_nopos: float
    keep: tuple[int, ...]                # colonne delle covariate senza "position"
    names_nopos: tuple[str, ...]
    ref_x: np.ndarray
    ref_delta: np.ndarray


def _row(**fields: object) -> dict[str, object]:
    rec = {c: "" for c in POSITION_COLUMNS}
    rec.update(fields)
    return rec


def adjacent_structural_threshold(x: np.ndarray, delta: np.ndarray, window: int, block_length: int,
                                  rng: np.random.Generator, n_boot: int = 999, alpha: float = 0.05) -> float:
    """Soglia di T = −S per le finestre adiacenti: prime 2W posizioni dei ricampionamenti, rango pieno."""
    idx = moving_block_indices(delta.shape[0], block_length, n_boot, rng)[:, :2 * window]
    ia, ib = idx[:, :window], idx[:, window:]
    tf = three_fold_batch(x[ia], delta[ia], x[ib], delta[ib])
    t = np.sort(-tf.structural[tf.valid])
    return float(t[compute_order_statistic_index(t.shape[0], alpha) - 1])


def position_setups(train: pd.DataFrame, params: FrozenParams,
                    seed: int | np.random.SeedSequence = SEED_S15) -> dict[str, PositionSetup]:
    """Soglie per fit con e senza "position" (vedi modulo)."""
    covs = list(params.fixed["covariates"])
    keep = tuple(i for i, c in enumerate(covs) if c != POSITION)
    w = scheme_window(params)
    thr = scheme_thresholds(train, params)
    ref = reference_setups(train, params)
    fits = training_seasons(train)
    gens = iter(np.random.SeedSequence(seed).spawn(2 * len(fits)))
    out = {}
    for fit in fits:
        inp = season_input_from_frame(train, fit, covs)
        x, length = inp.x[:, list(keep)], fit_block_length(inp)
        s_adj = adjacent_structural_threshold(x, inp.delta, w, length, np.random.default_rng(next(gens)))
        s_ref = calibrate_reference_thresholds(x, inp.delta, w, length, np.random.default_rng(next(gens)))[2]
        out[fit] = PositionSetup(thr[fit][0], thr[fit][1], float(params.c1_thresholds[fit]), s_adj,
                                 ref[fit].mean_threshold, ref[fit].dispersion_threshold, ref[fit].structural_threshold,
                                 s_ref, keep, tuple(covs[i] for i in keep), ref[fit].x, ref[fit].delta)
    return out


def _supervisors(params: FrozenParams, st: PositionSetup, inp: SeasonInput) -> dict[str, Module2Supervisor]:
    """I quattro supervisori della stagione: finestre adiacenti e riferimento fisso, con e senza "position"."""
    covs = list(params.fixed["covariates"])
    w = scheme_window(params)
    x_nopos = inp.x[:, list(st.keep)]
    return {
        "adj": Module2Supervisor(inp.season, inp.dates, inp.x, covs, w),
        "adj_nopos": Module2Supervisor(inp.season, inp.dates, x_nopos, st.names_nopos, w),
        "ref": Module2Supervisor(inp.season, inp.dates, inp.x, covs, w,
                                 reference=ReferenceData(st.ref_x, st.ref_delta)),
        "ref_nopos": Module2Supervisor(inp.season, inp.dates, x_nopos, st.names_nopos, w,
                                       reference=ReferenceData(st.ref_x[:, list(st.keep)], st.ref_delta)),
    }


def _agents(params: FrozenParams, st: PositionSetup, sups: Mapping[str, Module2Supervisor]) -> list:
    """B_0.25 e gli otto bracci dello schema, nell'ordine di CHECK_ARMS."""
    kappa, base = float(params.calibrated["c1_kappa"]), float(params.fixed["c0_lambda"])

    def scheme(name: str, sup: str, structural: float, stop: str) -> SchemeAgent:
        reference = sup.startswith("ref")
        mean_thr = st.ref_mean_threshold if reference else st.mean_threshold
        disp_thr = st.ref_dispersion_threshold if reference else st.dispersion_threshold
        return SchemeAgent(name, sups[sup], kappa, mean_thr, disp_thr, structural, stop, base_lambda=base,
                           reference=reference)

    return [
        FractionalKellyAgent("B_0.25", lam=AGENT_B_LAMBDA),
        scheme("C3", "adj", st.structural_threshold, SCHEME_STOP_CLEAR),
        scheme("C3_stop", "adj", st.structural_threshold, SCHEME_STOP_SEASON),
        scheme("C3_ref", "ref", st.ref_structural_threshold, SCHEME_STOP_CLEAR),
        scheme("C3_ref_stop", "ref", st.ref_structural_threshold, SCHEME_STOP_SEASON),
        scheme("C3_nopos", "adj_nopos", st.structural_threshold_nopos, SCHEME_STOP_CLEAR),
        scheme("C3_stop_nopos", "adj_nopos", st.structural_threshold_nopos, SCHEME_STOP_SEASON),
        scheme("C3_ref_nopos", "ref_nopos", st.ref_structural_threshold_nopos, SCHEME_STOP_CLEAR),
        scheme("C3_ref_stop_nopos", "ref_nopos", st.ref_structural_threshold_nopos, SCHEME_STOP_SEASON),
    ]


def run_position_instance(params: FrozenParams, setups: Mapping[str, PositionSetup], inp: SeasonInput, fit: str,
                          arms: Sequence[str] = CHECK_ARMS) -> np.ndarray:
    """Una stagione nelle tre configurazioni: (C, len(arms), M); supervisori condivisi fra le configurazioni."""
    st = setups[fit]
    sups = _supervisors(params, st, inp)
    out = np.full((len(CONFIGURATIONS), len(arms), len(METRICS)), np.nan)
    for ci, (_, min_stake) in enumerate(CONFIGURATIONS):
        agents = _agents(params, st, sups)
        runs = run_paired_backtest(agents, inp.dates, inp.probs, inp.odds, inp.outcomes, min_stake,
                                   fallback_policy=params.fixed["fallback_policy"])
        for run, agent in zip(runs, agents):
            out[ci, list(arms).index(run.name)] = run_metrics(run, agent)
    return out


def _validation_seasons(frame: pd.DataFrame) -> list[tuple[str, str]]:
    val = frame[frame["role"] == "validation"]
    return [(s, str(val.loc[val["season"] == s, "fit_through"].iloc[0]))
            for s in sorted(set(val["season"]), key=parse_season_start_year)]


def r2_records(frame: pd.DataFrame, covariates: Sequence[str]) -> list[dict[str, object]]:
    """R² di δ sulle covariate per stagione intera."""
    out = []
    for season in sorted(set(frame["season"]), key=parse_season_start_year):
        rows = frame[frame["season"] == season]
        x = np.column_stack([np.ones(len(rows)), rows[list(covariates)].to_numpy(dtype=np.float64)])
        y = rows["delta"].to_numpy(dtype=np.float64)
        beta, *_ = np.linalg.lstsq(x, y, rcond=None)
        out.append(_row(row_type="r2", season=season, covariates="frozen",
                        value=float(1.0 - (y - x @ beta).var() / y.var())))
    return out


def component_records(frame: pd.DataFrame, params: FrozenParams) -> list[dict[str, object]]:
    """Deviazione standard delle componenti sulle finestre adiacenti di validazione, con e senza "position"."""
    covs = list(params.fixed["covariates"])
    w = scheme_window(params)
    val = frame[frame["role"] == "validation"]
    out = []
    for variant, cols in (("with_position", covs), ("without_position", [c for c in covs if c != POSITION])):
        xa, ya, xb, yb = [], [], [], []
        for season, _ in _validation_seasons(frame):
            inp = season_input_from_frame(val, season, cols)
            for d in np.unique(inp.dates):
                idx = np.flatnonzero(inp.dates < d)
                if idx.shape[0] < 2 * w:
                    continue
                a, b = idx[-2 * w:-w], idx[-w:]
                xa.append(inp.x[a]); ya.append(inp.delta[a]); xb.append(inp.x[b]); yb.append(inp.delta[b])
        tf = three_fold_batch(np.array(xa), np.array(ya), np.array(xb), np.array(yb))
        v = tf.valid
        corr = float(np.corrcoef(tf.compositional[v], tf.interaction[v])[0, 1])
        for comp in ("total", "compositional", "structural", "interaction"):
            out.append(_row(row_type="component_sd", covariates=variant, design="adjacent", component=comp,
                            value=float(getattr(tf, comp)[v].std()), corr_comp_inter=corr))
    return out


def diagnosis_records(frame: pd.DataFrame, params: FrozenParams,
                      setups: Mapping[str, PositionSetup]) -> list[dict[str, object]]:
    """Giornate con allarme e quota di diagnosi strutturali sulle stagioni di validazione osservate."""
    covs = list(params.fixed["covariates"])
    val = frame[frame["role"] == "validation"]
    arms = {("adjacent", "with_position"): "C3", ("adjacent", "without_position"): "C3_nopos",
            ("fixed_reference", "with_position"): "C3_ref", ("fixed_reference", "without_position"): "C3_ref_nopos"}
    counts = {k: [0, 0] for k in arms}
    for season, fit in _validation_seasons(frame):
        inp = season_input_from_frame(val, season, covs)
        agents = {a.name: a for a in _agents(params, setups[fit], _supervisors(params, setups[fit], inp))}
        chosen = [agents[name] for name in arms.values()]
        run_paired_backtest(chosen, inp.dates, inp.probs, inp.odds, inp.outcomes, 0.0)
        for key, name in arms.items():
            diag = list(agents[name].diagnosis_by_date.values())
            counts[key][0] += sum(d != "none" for d in diag)
            counts[key][1] += sum(d == "structural" for d in diag)
    return [_row(row_type="diagnosis", design=k[0], covariates=k[1], arm=arms[k], n_alarm_dates=a, n_structural=s,
                 share_structural=s / a if a else "") for k, (a, s) in counts.items()]


def threshold_records(setups: Mapping[str, PositionSetup]) -> list[dict[str, object]]:
    """Soglie strutturali con e senza "position", per fit e disegno."""
    out = []
    for fit, st in setups.items():
        for design, with_pos, without_pos in (("adjacent", st.structural_threshold, st.structural_threshold_nopos),
                                              ("fixed_reference", st.ref_structural_threshold,
                                               st.ref_structural_threshold_nopos)):
            out.append(_row(row_type="threshold", fit_through=fit, design=design, covariates="with_position", value=with_pos))
            out.append(_row(row_type="threshold", fit_through=fit, design=design, covariates="without_position",
                            value=without_pos))
    return out


def wealth_records(frame: pd.DataFrame, params_path: str, setups: Mapping[str, PositionSetup], seed,
                   n_seeds: int = N_CHECK_SEEDS, workers: int = 1) -> list[dict[str, object]]:
    """Somma delle mediane di ln W_T e stagioni migliori di B_0.25, sugli stessi seed (vedi modulo)."""
    result = evaluate_scheme(frame, params_path, setups, n_seeds=n_seeds, workers=workers, seed=seed,
                             instance=run_position_instance)
    m, lw = CONFIG_NAMES.index("gbp_0.01"), METRICS.index("final_log_wealth")
    seeds = result.seeds[:, m, :, lw]
    base = seeds[:, 0]
    out = []
    for ai, arm in enumerate(CHECK_ARMS):
        total = float(np.median(seeds[:, ai], axis=1).sum())
        better = int((np.median(seeds[:, ai] - base, axis=1) > 0).sum()) if ai else ""
        out.append(_row(row_type="wealth", arm=arm, covariates="without_position" if arm.endswith("_nopos") else "with_position",
                        design="fixed_reference" if "_ref" in arm else ("none" if arm == "B_0.25" else "adjacent"),
                        sum_median_log_wealth=total, typical_capital=math.exp(total / len(result.seasons)),
                        seasons_better_than_b025=better, n_seeds=int(seeds.shape[-1])))
    return out


def position_records(frame: pd.DataFrame, params_path: str, seed, n_seeds: int = N_CHECK_SEEDS,
                     workers: int = 1) -> list[dict[str, object]]:
    """Tutte le righe del CSV della verifica (vedi modulo)."""
    params = load_frozen_params(params_path)
    train = frame[frame["role"] == "training"]
    setups = position_setups(train, params)
    return (r2_records(frame, list(params.fixed["covariates"])) + component_records(frame, params)
            + threshold_records(setups) + diagnosis_records(frame, params, setups)
            + wealth_records(frame, params_path, setups, seed, n_seeds, workers))
