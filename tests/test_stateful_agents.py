"""Test: canale degli esiti, Baseline D come agente e politica del ripiego."""

import inspect
import math
import time

import numpy as np
import pandas as pd
import pytest

import shk.kelly.environment as environment
from shk.data.loading import DEFAULT_DATA_DIR
from shk.kelly.agents import Agent, DateResults, DateView, FractionalKellyAgent, MinimumStakeAgent
from shk.kelly.environment import FALLBACK_MARKET_EV, FALLBACK_MODEL_EV, run_paired_backtest
from shk.kelly.staking import KAPPA_GRID
from shk.market.devig import devig_shin
from shk.model.monitoring import (
    BaselineDValidationSeasonData,
    assemble_baseline_d_season_input,
    evaluate_baseline_d_agents,
)
from shk.model.residuals import load_model_residuals
from shk.model.stateful_agents import SERIES_DELTA, BaselineDAgent, adaptive_multiplier
from shk.stats.drift import detector_params, run_drift_detector

_FTR = {"H": 0, "D": 1, "A": 2}


class _ProbeAgent(Agent):
    """Registra le date osservate e controlla a ogni decisione che siano tutte anteriori."""

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.observed: list[np.datetime64] = []
        self.violations = 0

    def stake_fractions(self, view: DateView, p_hat: np.ndarray, b: np.ndarray) -> np.ndarray:
        if any(d >= view.date for d in self.observed):
            self.violations += 1
        return np.zeros(p_hat.shape[0], dtype=np.float64)

    def observe_results(self, results: DateResults) -> None:
        self.observed.append(results.date)


def _synthetic_season(n_dates: int = 30, per_date: int = 3, seed: int = 0):
    rng = np.random.default_rng(seed)
    n = n_dates * per_date
    dates = (np.datetime64("2010-08-14") + np.repeat(np.arange(n_dates), per_date) * np.timedelta64(7, "D")).astype("datetime64[ns]")
    raw = rng.dirichlet([4, 3, 3], size=n)
    probs = raw / raw.sum(axis=1, keepdims=True)
    odds = 1.0 / (rng.dirichlet([4, 3, 3], size=n) * 1.06)
    odds = np.maximum(odds, 1.01)
    outcomes = np.array([rng.choice(3, p=p) for p in probs])[None, :]
    return dates, probs, odds, outcomes


def _mutant_run_paired_backtest():
    """Mutante dell'ambiente: osservazione chiamata prima delle decisioni della data."""
    src = inspect.getsource(environment.run_paired_backtest)
    notify = "        _notify_results(agents, DateResults(date=d_date, probs=d_probs, odds=d_odds, outcomes=d_outcomes_all_m))\n"
    anchor = "        for a_idx, agent in enumerate(agents):\n            decision = agent.decide(view)\n"
    assert src.count(notify) == 1 and src.count(anchor) == 1
    mutated = src.replace(notify, "").replace(anchor, notify + anchor)
    namespace = dict(vars(environment))
    exec(compile(mutated, environment.__file__, "exec"), namespace)
    return namespace["run_paired_backtest"]


def test_results_channel_only_after_settlement():
    """Alla data d nessun agente ha ricevuto esiti di date >= d; il mutante viene scoperto."""
    dates, probs, odds, outcomes = _synthetic_season()
    probe = _ProbeAgent("probe")
    run_paired_backtest([probe, FractionalKellyAgent("B", 0.25)], dates, probs, odds, outcomes, 0.0)
    assert probe.violations == 0
    assert len(probe.observed) == 30
    assert probe.observed == sorted(set(probe.observed))

    mutant = _mutant_run_paired_backtest()
    probe_m = _ProbeAgent("probe")
    mutant([probe_m], dates, probs, odds, outcomes, 0.0)
    assert probe_m.violations > 0


def test_default_policy_unchanged_and_validation():
    """Il default coincide col comportamento precedente; market_probs solo con market_ev."""
    dates, probs, odds, outcomes = _synthetic_season()
    agents = lambda: [FractionalKellyAgent("A", 1.0), MinimumStakeAgent("E")]
    base = run_paired_backtest(agents(), dates, probs, odds, outcomes, 0.01)
    explicit = run_paired_backtest(agents(), dates, probs, odds, outcomes, 0.01, fallback_policy=FALLBACK_MODEL_EV)
    for r1, r2 in zip(base, explicit):
        np.testing.assert_array_equal(r1.wealth, r2.wealth)
    with pytest.raises(ValueError, match="only used with fallback_policy='market_ev'"):
        run_paired_backtest(agents(), dates, probs, odds, outcomes, 0.01, market_probs=probs)
    with pytest.raises(ValueError, match="market_probs must be a numpy.ndarray"):
        run_paired_backtest(agents(), dates, probs, odds, outcomes, 0.01, fallback_policy=FALLBACK_MARKET_EV)
    with pytest.raises(ValueError, match="fallback_policy must be one of"):
        run_paired_backtest(agents(), dates, probs, odds, outcomes, 0.01, fallback_policy="other")


def test_market_fallback_picks_least_negative_market_ev():
    """Con il ripiego di mercato la puntata obbligatoria va su q·o − 1 massimo della data."""
    dates = np.array(["2010-08-14", "2010-08-14"], dtype="datetime64[ns]")
    odds = np.array([[5.0, 3.5, 1.9], [2.0, 3.4, 4.2]])
    implied = 1.0 / odds[1]
    probs = np.array([[0.198, 0.285, 0.517], implied / implied.sum()])
    # EV del modello tutti <= 0: nessuna puntata volontaria; massimo su (0, D) = −0.0025
    model_ev = probs * odds - 1.0
    assert np.all(model_ev <= 0.0)
    assert np.unravel_index(np.argmax(model_ev), (2, 3)) == (0, 1)
    q, _ = devig_shin(odds)
    market_ev = q * odds - 1.0
    flat = int(np.argmax(market_ev.reshape(-1)))
    best = (flat // 3, flat % 3)
    assert best != (0, 1)
    outcomes = np.array([[best[1] if best[0] == 0 else 0, best[1] if best[0] == 1 else 0]])
    won_model = outcomes[0, 0] == 1
    f = 0.1
    model_run = run_paired_backtest([MinimumStakeAgent("E")], dates, probs, odds, outcomes, f)
    market_run = run_paired_backtest([MinimumStakeAgent("E")], dates, probs, odds, outcomes, f,
                                     fallback_policy=FALLBACK_MARKET_EV, market_probs=q)
    assert math.isclose(market_run[0].wealth[0, -1], 1.0 + f * (odds[best] - 1.0))
    assert math.isclose(model_run[0].wealth[0, -1], 1.0 + (f * (odds[0, 1] - 1.0) if won_model else -f))


def test_baseline_d_requires_single_replica_and_delta_series():
    """M > 1 dà ValueError; la serie δ usa q di Shin dalle quote della data."""
    dates, probs, odds, outcomes = _synthetic_season()
    agent = BaselineDAgent("D", "adwin", detector_params("adwin"), 0.5)
    with pytest.raises(ValueError, match="single replica"):
        run_paired_backtest([agent], dates, probs, odds, np.vstack([outcomes, outcomes]), 0.0)

    agent_delta = BaselineDAgent("Dd", "page_hinkley", detector_params("page_hinkley"), 0.5, series=SERIES_DELTA)
    seen: list[float] = []
    agent_delta._detector.update = lambda x: seen.append(x)  # type: ignore[method-assign]
    res = DateResults(date=dates[0], probs=probs[:3], odds=odds[:3], outcomes=outcomes[:, :3])
    agent_delta.observe_results(res)
    q, _ = devig_shin(odds[:3])
    idx = outcomes[0, :3]
    expected = np.log(probs[np.arange(3), idx]) - np.log(q[np.arange(3), idx])
    np.testing.assert_allclose(seen, expected, rtol=0, atol=1e-15)
    assert adaptive_multiplier(0.0, 0) == 1.0 and adaptive_multiplier(0.0, 2) == 0.0
    assert adaptive_multiplier(0.5, 3) == 0.125


@pytest.fixture(scope="module")
def real_data():
    if not (DEFAULT_DATA_DIR.is_dir() and any(DEFAULT_DATA_DIR.glob("*.csv"))):
        pytest.skip(f"Real data missing: no CSV in {DEFAULT_DATA_DIR}")
    return load_model_residuals()


def _season_inputs(data):
    seasons = []
    for fit, entry in data.schedule.items():
        if fit != "2000-01":
            seasons.append((fit, fit, "training"))
        seasons += [(s, fit, "validation") for s in entry["validation"]]
    return seasons


def test_baseline_d_reproduces_c5_3(real_data):
    """Con la log-loss e F = 0 l'agente D riproduce la Baseline D entro 1e-12, per detector e κ."""
    seasons = _season_inputs(real_data)
    assert len(seasons) == 21
    worst = 0.0
    for season, fit, role in seasons:
        inp = assemble_baseline_d_season_input(real_data.residuals, real_data.df, season, fit, role=role)
        sd = BaselineDValidationSeasonData(
            season=season, fit_through=fit, season_input=inp,
            adwin_alarm_dates=inp.dates[run_drift_detector(inp.log_loss, "adwin", detector_params("adwin"))],
            page_hinkley_alarm_dates=inp.dates[run_drift_detector(inp.log_loss, "page_hinkley", detector_params("page_hinkley"))],
        )
        outcomes = np.array([_FTR[x.strip()] for x in inp.ftr], dtype=np.int64)[None, :]
        for kappa in KAPPA_GRID:
            ref = evaluate_baseline_d_agents(sd, kappa_adwin=kappa, kappa_page_hinkley=kappa)
            agents = [BaselineDAgent("d_adwin", "adwin", detector_params("adwin"), kappa),
                      BaselineDAgent("d_page_hinkley", "page_hinkley", detector_params("page_hinkley"), kappa)]
            runs = run_paired_backtest(agents, inp.dates, inp.probs, inp.odds, outcomes, 0.0)
            for run, ref_res in zip(runs, ref[1:]):
                diff = abs(math.log(run.wealth[0, -1]) - ref_res.final_log_wealth)
                worst = max(worst, diff)
                assert diff <= 1e-12, (season, kappa, run.name, diff)
    assert worst <= 1e-12
