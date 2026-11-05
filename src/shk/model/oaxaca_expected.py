"""Oaxaca-Blinder dello schema sull'errore atteso E_q[δ] invece che su δ realizzato.

δ = ln p̂(x) − ln q(x) dipende quasi tutto dall'esito x uscito, che le covariate non possono
spiegare. L'errore atteso E_q[δ] = Σ_j q_j ln(p̂_j / q_j) = −KL(q ‖ p̂) (agent_c.expected_delta) è la
distanza fra modello e mercato prima della partita, senza il caso dell'esito; la sua media è
quella di δ se il mercato è calibrato. Verifica (decisione del 2026-11-05), con l'allarme ANOVA
invariato su δ realizzato e la diagnosi di Oaxaca-Blinder sull'errore atteso:
- righe "r2": R² di δ e di E_q[δ] sulle covariate congelate, per stagione;
- righe "component_sd": deviazione standard delle componenti three-fold di E_q[δ] sulle finestre
  adiacenti di validazione, con e senza "position";
- righe "threshold": soglie strutturali per E_q[δ], calibrate sul training come quelle di δ
  (finestre adiacenti senza "position"; riferimento fisso con le covariate congelate), seed
  SeedSequence(SEED_S16).spawn(2 · numero di fit);
- righe "diagnosis": sulle stagioni di validazione osservate, giornate con allarme e quota di
  diagnosi strutturali (C3_ed, C3_ref_ed);
- righe "wealth": B_0.25, C3_ed, C3_stop_ed, C3_ref_ed, C3_ref_stop_ed su N_CHECK_SEEDS seed (i
  primi dell'esecuzione congelata, appaiati con oaxaca_position).
È una variante scelta dopo aver visto i dati.
"""

import math
from collections.abc import Mapping, Sequence
from typing import Final, NamedTuple

import numpy as np
import pandas as pd

from shk.kelly.agents import AGENT_B_LAMBDA, FractionalKellyAgent
from shk.kelly.environment import run_paired_backtest
from shk.model.agent_c import (
    OAXACA_EXPECTED,
    SCHEME_STOP_CLEAR,
    SCHEME_STOP_SEASON,
    Module2Supervisor,
    ReferenceData,
    SchemeAgent,
    calibrate_reference_thresholds,
    expected_delta,
)
from shk.model.elo_fit import parse_season_start_year
from shk.model.frozen_agents import scheme_window
from shk.model.frozen_params import FrozenParams, load_frozen_params
from shk.model.oaxaca_position import N_CHECK_SEEDS, POSITION, adjacent_structural_threshold
from shk.model.paired_backtest import CONFIGURATIONS
from shk.model.scheme_reference_run import reference_setups
from shk.model.scheme_run import evaluate_scheme, fit_block_length, scheme_thresholds
from shk.model.season_input import SeasonInput, season_input_from_frame, training_seasons
from shk.model.validation_run import CONFIG_NAMES, METRICS, run_metrics
from shk.stats.oaxaca import three_fold_batch

SEED_S16: Final[int] = 20261108
EXPECTED_ARMS: Final[tuple[str, ...]] = ("B_0.25", "C3_ed", "C3_stop_ed", "C3_ref_ed", "C3_ref_stop_ed")
EXPECTED_COLUMNS: Final[tuple[str, ...]] = (
    "row_type", "season", "fit_through", "response", "covariates", "design", "arm", "component", "value",
    "n_alarm_dates", "n_structural", "share_structural", "sum_median_log_wealth", "typical_capital",
    "seasons_better_than_b025", "n_seeds",
)


class ExpectedSetup(NamedTuple):
    """Soglie e stagione di calibrazione di un fit per la diagnosi sull'errore atteso."""

    mean_threshold: float
    dispersion_threshold: float
    structural_threshold: float        # finestre adiacenti, senza "position"
    ref_mean_threshold: float
    ref_dispersion_threshold: float
    ref_structural_threshold: float    # riferimento fisso, covariate congelate
    keep: tuple[int, ...]
    covariates: tuple[str, ...]
    reference: ReferenceData


def _row(**fields: object) -> dict[str, object]:
    rec = {c: "" for c in EXPECTED_COLUMNS}
    rec.update(fields)
    return rec


def with_expected(frame: pd.DataFrame) -> pd.DataFrame:
    """Il DataFrame con la colonna exp_delta = E_q[δ] dalle p̂ e dalle q di Shin."""
    return frame.assign(exp_delta=expected_delta(frame[["p_home", "p_draw", "p_away"]].to_numpy(dtype=np.float64),
                                                 frame[["q_home", "q_draw", "q_away"]].to_numpy(dtype=np.float64)))


def expected_setups(train: pd.DataFrame, params: FrozenParams,
                    seed: int | np.random.SeedSequence = SEED_S16) -> dict[str, ExpectedSetup]:
    """Soglie per fit (vedi modulo): media e dispersione dello schema, strutturali ricalibrate su E_q[δ]."""
    covs = tuple(params.fixed["covariates"])
    keep = tuple(i for i, c in enumerate(covs) if c != POSITION)
    w = scheme_window(params)
    thr, ref = scheme_thresholds(train, params), reference_setups(train, params)
    fits = training_seasons(train)
    gens = iter(np.random.SeedSequence(seed).spawn(2 * len(fits)))
    train = with_expected(train)
    out = {}
    for fit in fits:
        inp = season_input_from_frame(train, fit, covs)
        ed = train[train["season"] == fit].sort_values("Date", kind="stable")["exp_delta"].to_numpy(dtype=np.float64)
        length = fit_block_length(inp)
        s_adj = adjacent_structural_threshold(inp.x[:, list(keep)], ed, w, length, np.random.default_rng(next(gens)))
        s_ref = calibrate_reference_thresholds(inp.x, ed, w, length, np.random.default_rng(next(gens)))[2]
        out[fit] = ExpectedSetup(thr[fit][0], thr[fit][1], s_adj, ref[fit].mean_threshold,
                                 ref[fit].dispersion_threshold, s_ref, keep, covs, ReferenceData(inp.x, inp.delta, ed))
    return out


def _supervisors(params: FrozenParams, st: ExpectedSetup, inp: SeasonInput) -> dict[str, Module2Supervisor]:
    w = scheme_window(params)
    names = tuple(st.covariates[i] for i in st.keep)
    return {
        "adj": Module2Supervisor(inp.season, inp.dates, inp.x[:, list(st.keep)], names, w,
                                 oaxaca_response=OAXACA_EXPECTED),
        "ref": Module2Supervisor(inp.season, inp.dates, inp.x, st.covariates, w, reference=st.reference,
                                 oaxaca_response=OAXACA_EXPECTED),
    }


def _agents(params: FrozenParams, st: ExpectedSetup, sups: Mapping[str, Module2Supervisor]) -> list:
    kappa, base = float(params.calibrated["c1_kappa"]), float(params.fixed["c0_lambda"])

    def scheme(name: str, sup: str, stop: str) -> SchemeAgent:
        if sup == "ref":
            return SchemeAgent(name, sups[sup], kappa, st.ref_mean_threshold, st.ref_dispersion_threshold,
                               st.ref_structural_threshold, stop, base_lambda=base, reference=True)
        return SchemeAgent(name, sups[sup], kappa, st.mean_threshold, st.dispersion_threshold,
                           st.structural_threshold, stop, base_lambda=base)

    return [FractionalKellyAgent("B_0.25", lam=AGENT_B_LAMBDA),
            scheme("C3_ed", "adj", SCHEME_STOP_CLEAR), scheme("C3_stop_ed", "adj", SCHEME_STOP_SEASON),
            scheme("C3_ref_ed", "ref", SCHEME_STOP_CLEAR), scheme("C3_ref_stop_ed", "ref", SCHEME_STOP_SEASON)]


def run_expected_instance(params: FrozenParams, setups: Mapping[str, ExpectedSetup], inp: SeasonInput, fit: str,
                          arms: Sequence[str] = EXPECTED_ARMS) -> np.ndarray:
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
    """R² di δ e di E_q[δ] sulle covariate, per stagione."""
    frame = with_expected(frame)
    out = []
    for season in sorted(set(frame["season"]), key=parse_season_start_year):
        rows = frame[frame["season"] == season]
        x = np.column_stack([np.ones(len(rows)), rows[list(covariates)].to_numpy(dtype=np.float64)])
        for response, col in (("realized", "delta"), ("expected", "exp_delta")):
            y = rows[col].to_numpy(dtype=np.float64)
            beta, *_ = np.linalg.lstsq(x, y, rcond=None)
            out.append(_row(row_type="r2", season=season, response=response, covariates="frozen",
                            value=float(1.0 - (y - x @ beta).var() / y.var())))
    return out


def component_records(frame: pd.DataFrame, params: FrozenParams) -> list[dict[str, object]]:
    """Deviazione standard delle componenti di E_q[δ] sulle finestre adiacenti di validazione."""
    covs = list(params.fixed["covariates"])
    w = scheme_window(params)
    val = with_expected(frame[frame["role"] == "validation"])
    out = []
    for variant, cols in (("with_position", covs), ("without_position", [c for c in covs if c != POSITION])):
        xa, ya, xb, yb = [], [], [], []
        for season, _ in _validation_seasons(frame):
            rows = val[val["season"] == season].sort_values("Date", kind="stable")
            x, y, dates = rows[cols].to_numpy(dtype=np.float64), rows["exp_delta"].to_numpy(), rows["Date"].to_numpy()
            for d in np.unique(dates):
                idx = np.flatnonzero(dates < d)
                if idx.shape[0] < 2 * w:
                    continue
                a, b = idx[-2 * w:-w], idx[-w:]
                xa.append(x[a]); ya.append(y[a]); xb.append(x[b]); yb.append(y[b])
        tf = three_fold_batch(np.array(xa), np.array(ya), np.array(xb), np.array(yb))
        v = tf.valid
        for comp in ("total", "compositional", "structural", "interaction"):
            out.append(_row(row_type="component_sd", response="expected", covariates=variant, design="adjacent",
                            component=comp, value=float(getattr(tf, comp)[v].std())))
    return out


def threshold_records(setups: Mapping[str, ExpectedSetup]) -> list[dict[str, object]]:
    """Soglie strutturali per E_q[δ], per fit e disegno."""
    out = []
    for fit, st in setups.items():
        out.append(_row(row_type="threshold", fit_through=fit, response="expected", covariates="without_position",
                        design="adjacent", value=st.structural_threshold))
        out.append(_row(row_type="threshold", fit_through=fit, response="expected", covariates="frozen",
                        design="fixed_reference", value=st.ref_structural_threshold))
    return out


def diagnosis_records(frame: pd.DataFrame, params: FrozenParams,
                      setups: Mapping[str, ExpectedSetup]) -> list[dict[str, object]]:
    """Giornate con allarme e quota di diagnosi strutturali sulle stagioni di validazione osservate."""
    covs = list(params.fixed["covariates"])
    val = frame[frame["role"] == "validation"]
    counts = {"C3_ed": [0, 0], "C3_ref_ed": [0, 0]}
    for season, fit in _validation_seasons(frame):
        inp = season_input_from_frame(val, season, covs)
        agents = {a.name: a for a in _agents(params, setups[fit], _supervisors(params, setups[fit], inp))}
        run_paired_backtest([agents[k] for k in counts], inp.dates, inp.probs, inp.odds, inp.outcomes, 0.0)
        for name in counts:
            diag = list(agents[name].diagnosis_by_date.values())
            counts[name][0] += sum(d != "none" for d in diag)
            counts[name][1] += sum(d == "structural" for d in diag)
    return [_row(row_type="diagnosis", response="expected", arm=name,
                 design="fixed_reference" if "_ref" in name else "adjacent",
                 covariates="frozen" if "_ref" in name else "without_position",
                 n_alarm_dates=a, n_structural=s, share_structural=s / a if a else "")
            for name, (a, s) in counts.items()]


def wealth_records(frame: pd.DataFrame, params_path: str, setups: Mapping[str, ExpectedSetup], seed,
                   n_seeds: int = N_CHECK_SEEDS, workers: int = 1) -> list[dict[str, object]]:
    """Somma delle mediane di ln W_T e stagioni migliori di B_0.25, sugli stessi seed (vedi modulo)."""
    result = evaluate_scheme(frame, params_path, setups, n_seeds=n_seeds, workers=workers, seed=seed,
                             instance=run_expected_instance)
    m, lw = CONFIG_NAMES.index("gbp_0.01"), METRICS.index("final_log_wealth")
    seeds = result.seeds[:, m, :, lw]
    out = []
    for ai, arm in enumerate(EXPECTED_ARMS):
        total = float(np.median(seeds[:, ai], axis=1).sum())
        better = int((np.median(seeds[:, ai] - seeds[:, 0], axis=1) > 0).sum()) if ai else ""
        out.append(_row(row_type="wealth", response="expected" if ai else "", arm=arm,
                        design="fixed_reference" if "_ref" in arm else ("none" if not ai else "adjacent"),
                        sum_median_log_wealth=total, typical_capital=math.exp(total / len(result.seasons)),
                        seasons_better_than_b025=better, n_seeds=int(seeds.shape[-1])))
    return out


def expected_records(frame: pd.DataFrame, params_path: str, seed, n_seeds: int = N_CHECK_SEEDS,
                     workers: int = 1) -> list[dict[str, object]]:
    """Tutte le righe del CSV della verifica (vedi modulo)."""
    params = load_frozen_params(params_path)
    setups = expected_setups(frame[frame["role"] == "training"], params)
    return (r2_records(frame, list(params.fixed["covariates"])) + component_records(frame, params)
            + threshold_records(setups) + diagnosis_records(frame, params, setups)
            + wealth_records(frame, params_path, setups, seed, n_seeds, workers))
