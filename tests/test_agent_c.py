"""Test: supervisore del Modulo 2, bracci C1, C2_global e C2, soglia di C1."""

import inspect
import math
from types import SimpleNamespace

import numpy as np
import pytest

import shk.kelly.environment as environment
from shk.data.loading import DEFAULT_DATA_DIR
from shk.kelly.agents import DateResults, DateView, FractionalKellyAgent
from shk.kelly.environment import run_paired_backtest
from shk.model.agent_c import (
    C1Agent,
    GradedAgent,
    Module2Supervisor,
    SupervisorState,
    build_c0_agent,
    c1_null_statistics,
    calibrate_c1_threshold,
)
from shk.model.covariate_inspection import derive_specification
from shk.model.did_support import out_of_support_at_date
from shk.model.module2 import STATE_ACTIVE, Module2Output, module2_at_date, prepare_module2_data
from shk.model.module2_data import build_module2_frame
from shk.model.residuals import load_model_residuals
from shk.model.training_agents import PROVISIONAL_WINDOW, season_input_from_frame, training_seasons
from shk.stats.calibration import compute_order_statistic_index


def _has_real_data() -> bool:
    return DEFAULT_DATA_DIR.is_dir() and any(DEFAULT_DATA_DIR.glob("*.csv"))


@pytest.fixture(scope="module")
def training():
    if not _has_real_data():
        pytest.skip(f"Real data missing: no CSV in {DEFAULT_DATA_DIR}")
    frame = build_module2_frame(load_model_residuals())
    train = frame[frame["role"] == "training"]
    covs = derive_specification(train).covariates
    inputs = {s: season_input_from_frame(train, s, covs) for s in training_seasons(train)}
    return train, covs, inputs


class _ScriptedSupervisor(Module2Supervisor):
    """Supervisore con uscite prefissate per data: attivo con la S indicata, oppure non attivo."""

    def __init__(self, dates: np.ndarray, structural: list[float | None]) -> None:
        super().__init__("s", dates, np.zeros((dates.shape[0], 1)), ["c"], 3)
        self._script = dict(zip(np.unique(dates), structural))

    def state_at(self, decision_date: np.datetime64) -> SupervisorState:
        s = self._script[np.datetime64(decision_date, "ns")]
        state = STATE_ACTIVE if s is not None else "not_active"
        result = SimpleNamespace(structural=s) if s is not None else None
        out = Module2Output("s", None, 3, state, 0, 0, 0, math.nan, math.nan, result, math.nan)
        return SupervisorState(out, None, None, None)


def test_c1_counts_alarm_onsets():
    """λ = 0.25·κ^(accensioni): un allarme acceso per più date conta una volta; T = −S."""
    days = (np.datetime64("2010-08-14") + np.arange(7) * np.timedelta64(7, "D")).astype("datetime64[ns]")
    # T = −S: allarme con S = −0.2 (T = 0.2 > 0.1); S = +0.2 non dà allarme
    script = [None, -0.2, -0.2, 0.2, -0.2, -0.05, -0.3]
    sup = _ScriptedSupervisor(days, script)
    agent = C1Agent("C1", sup, 0.5, 0.1)
    probs = np.array([[0.6, 0.25, 0.15]])
    odds = np.array([[2.0, 3.6, 7.0]])
    for d in days:
        agent.decide(DateView(d, probs, odds))
    lam = [agent.lambda_by_date[d] for d in days]
    assert agent.alarm_by_date == dict(zip(days, [False, True, True, False, True, False, True]))
    assert lam == [0.25, 0.125, 0.125, 0.125, 0.0625, 0.0625, 0.03125]
    assert agent.n_onsets == 3
    # κ = 0: dopo la prima accensione λ = 0
    agent0 = C1Agent("C1", _ScriptedSupervisor(days, script), 0.0, 0.1)
    for d in days:
        agent0.decide(DateView(d, probs, odds))
    assert [agent0.lambda_by_date[d] for d in days] == [0.25, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]


def test_c1_threshold_order_statistic_and_rank_deficient_resamples():
    """Soglia = statistica d'ordine sui ricampionamenti a rango pieno; i ricampionamenti degeneri si scartano."""
    rng = np.random.default_rng(0)
    n, w = 120, 20
    flag = np.zeros(n)
    flag[[5, 60]] = 1.0
    x = np.column_stack([rng.normal(size=n), flag])
    delta = rng.normal(0.0, 0.3, n)
    stats, n_valid = c1_null_statistics(x, delta, w, 5, 999, np.random.default_rng(1))
    assert 0 < n_valid < 999
    thr, n_valid2 = calibrate_c1_threshold(x, delta, w, 5, np.random.default_rng(1))
    assert n_valid2 == n_valid
    assert thr == np.sort(stats)[compute_order_statistic_index(n_valid, 0.05) - 1]


def test_supervisor_matches_module2_and_support_rule_on_frame(training):
    """Con gli esiti solo dall'ambiente il supervisore riproduce module2_at_date e la regola dell'analisi del supporto comune."""
    train, covs, inputs = training
    dummies = [i for i, c in enumerate(covs) if c.startswith("flag_")]
    for season, inp in inputs.items():
        sup = Module2Supervisor(season, inp.dates, inp.x, covs, PROVISIONAL_WINDOW)
        ref = prepare_module2_data(train[train["season"] == season], covs)
        n_active = 0
        for d in np.unique(inp.dates):
            st = sup.state_at(d)
            r = module2_at_date(ref, season, d, PROVISIONAL_WINDOW)
            assert st.output.state == r.state
            if r.state == STATE_ACTIVE:
                n_active += 1
                for c in ("total", "compositional", "structural", "interaction"):
                    assert abs(getattr(st.output.result, c) - getattr(r.result, c)) <= 1e-12
            rows = np.flatnonzero(inp.dates == d)
            mask = out_of_support_at_date(ref, season, d, PROVISIONAL_WINDOW, inp.x[rows], dummies)
            if mask is None:
                assert st.out_of_support is None
            else:
                np.testing.assert_array_equal(st.out_of_support, mask)
            sup.observe(DateResults(date=d, probs=inp.probs[rows], odds=inp.odds[rows], outcomes=inp.outcomes[:, rows]))
        assert n_active > 0


class _RecB(FractionalKellyAgent):
    def __init__(self, name, lam):
        super().__init__(name, lam)
        self.log = {}

    def stake_fractions(self, view, p_hat, b):
        f = super().stake_fractions(view, p_hat, b)
        self.log[view.date] = (view.probs.copy(), view.odds.copy(), p_hat.copy(), b.copy(), f.copy())
        return f


class _RecC1(C1Agent):
    def __init__(self, *args):
        super().__init__(*args)
        self.log = {}

    def stake_fractions(self, view, p_hat, b):
        f = super().stake_fractions(view, p_hat, b)
        self.log[view.date] = (view.probs.copy(), view.odds.copy(), p_hat.copy(), b.copy(), f.copy())
        return f


class _RecGraded(GradedAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log = {}

    def stake_fractions(self, view, p_hat, b):
        f = super().stake_fractions(view, p_hat, b)
        self.log[view.date] = (view.probs.copy(), view.odds.copy(), p_hat.copy(), b.copy(), f.copy())
        return f


def _recorded_run(inp, covs, min_stake=0.0):
    sup = Module2Supervisor(inp.season, inp.dates, inp.x, covs, PROVISIONAL_WINDOW)
    agents = [_RecB("B_0.25", 0.25), _RecC1("C1", sup, 0.5, 0.05),
              _RecGraded("C2_global", sup, abstain=False), _RecGraded("C2", sup, abstain=True)]
    runs = run_paired_backtest(agents, inp.dates, inp.probs, inp.odds, inp.outcomes, min_stake)
    return sup, agents, runs


def test_separation_of_responsibilities(training):
    """Stesse previsioni e quote viste, stessa selezione di B_0.25; i bracci cambiano solo le frazioni."""
    _, covs, inputs = training
    for inp in inputs.values():
        _, agents, _ = _recorded_run(inp, covs)
        b_log = agents[0].log
        for agent in agents[1:]:
            assert agent.log.keys() == b_log.keys()
            for d, (probs, odds, p_hat, b, f) in agent.log.items():
                ref = b_log[d]
                np.testing.assert_array_equal(probs, ref[0])
                np.testing.assert_array_equal(odds, ref[1])
                # Stessi esiti selezionati: stessi p̂ e b dei soli esiti scelti da B_0.25
                np.testing.assert_array_equal(p_hat, ref[2])
                np.testing.assert_array_equal(b, ref[3])
                assert np.all((f >= 0.0) & (f < 1.0))


def test_c2_abstains_only_out_of_support(training):
    """C2 = C2_global dove la regola dà "nel supporto" (o non si applica), 0 dove dà "fuori"."""
    _, covs, inputs = training
    n_out = 0
    for inp in inputs.values():
        sup, agents, _ = _recorded_run(inp, covs)
        g_log, c2_log = agents[2].log, agents[3].log
        for d, entry in c2_log.items():
            f_c2, f_g = entry[4], g_log[d][4]
            mask = sup.state_at(d).out_of_support
            if mask is None:
                np.testing.assert_array_equal(f_c2, f_g)
                continue
            view_probs, view_odds = entry[0], entry[1]
            ev = view_probs * view_odds - 1.0
            selected = np.flatnonzero(ev.max(axis=1) > 0.0)
            outside = mask[selected]
            n_out += int(outside.sum())
            assert np.all(f_c2[outside] == 0.0)
            np.testing.assert_array_equal(f_c2[~outside], f_g[~outside])
        assert agents[3].n_abstained == sum(
            int(sup.state_at(d).out_of_support[np.flatnonzero((e[0] * e[1] - 1.0).max(axis=1) > 0.0)].sum())
            for d, e in c2_log.items() if sup.state_at(d).out_of_support is not None)
    assert n_out > 0


def test_c0_equals_b025(training):
    _, covs, inputs = training
    for inp in inputs.values():
        for min_stake in (0.0, 0.01 / 220, 1.0 / 220):
            runs = run_paired_backtest([FractionalKellyAgent("B_0.25", 0.25), build_c0_agent("C0")],
                                       inp.dates, inp.probs, inp.odds, inp.outcomes, min_stake)
            np.testing.assert_allclose(runs[1].wealth, runs[0].wealth, rtol=0.0, atol=1e-12)


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


class _LeakySupervisor(Module2Supervisor):
    """Mutante del supervisore: anteriorità non stretta (Date <= d)."""

    def cutoff(self, decision_date):
        return np.datetime64(decision_date, "ns") + np.timedelta64(1, "D")


def _module2_outputs(runner, supervisor_cls, inp, covs, outcomes):
    sup = supervisor_cls(inp.season, inp.dates, inp.x, covs, PROVISIONAL_WINDOW)
    runner([GradedAgent("C2_global", sup, abstain=False)], inp.dates, inp.probs, inp.odds, outcomes, 0.0)
    out = {}
    for d in np.unique(inp.dates):
        res = sup.state_at(d).output.result
        out[d] = None if res is None else (res.total, res.structural)
    return out


def test_module2_anti_leakage_with_mutant(training):
    """Alterare gli esiti di date >= d non cambia l'uscita del Modulo 2 usata a d; il mutante sì."""
    _, covs, inputs = training
    inp = inputs["2010-11"]
    days = np.unique(inp.dates)
    d0 = days[len(days) // 2]
    altered = inp.outcomes.copy()
    late = inp.dates >= d0
    altered[0, late] = (altered[0, late] + 1) % 3

    for runner in (run_paired_backtest, _mutant_run_paired_backtest()):
        base = _module2_outputs(runner, Module2Supervisor, inp, covs, inp.outcomes)
        alt = _module2_outputs(runner, Module2Supervisor, inp, covs, altered)
        for d in days[days <= d0]:
            assert base[d] == alt[d]

    # Mutante: ambiente che notifica prima delle decisioni e supervisore con Date <= d
    mutant = _mutant_run_paired_backtest()
    base = _module2_outputs(mutant, _LeakySupervisor, inp, covs, inp.outcomes)
    alt = _module2_outputs(mutant, _LeakySupervisor, inp, covs, altered)
    assert base[d0] is not None and base[d0] != alt[d0]
