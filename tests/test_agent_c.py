"""Test: supervisore dello schema del relatore sui dati reali (Oaxaca-Blinder, separazione, anti-leakage)."""

import inspect

import numpy as np
import pytest

import shk.kelly.environment as environment
from shk.data.loading import DEFAULT_DATA_DIR
from shk.kelly.agents import DateResults, FractionalKellyAgent
from shk.kelly.environment import run_paired_backtest
from shk.model.agent_c import SCHEME_STOP_CLEAR, Module2Supervisor, SchemeAgent
from shk.model.covariate_inspection import derive_specification
from shk.model.module2 import STATE_ACTIVE, module2_at_date, prepare_module2_data
from shk.model.module2_data import build_module2_frame
from shk.model.residuals import load_model_residuals
from shk.model.season_input import season_input_from_frame, training_seasons

WINDOW = 40


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


def test_supervisor_matches_module2_on_frame(training):
    """Con gli esiti solo dall'ambiente il supervisore riproduce module2_at_date e le finestre di δ."""
    train, covs, inputs = training
    for season, inp in inputs.items():
        sup = Module2Supervisor(season, inp.dates, inp.x, covs, WINDOW)
        ref = prepare_module2_data(train[train["season"] == season], covs)
        n_active = 0
        for d in np.unique(inp.dates):
            out = sup.state_at(d)
            r = module2_at_date(ref, season, d, WINDOW)
            assert out.state == r.state
            if r.state == STATE_ACTIVE:
                n_active += 1
                for c in ("total", "compositional", "structural", "interaction"):
                    assert abs(getattr(out.result, c) - getattr(r.result, c)) <= 1e-12
            windows = sup.delta_windows(d)
            earlier = np.flatnonzero(inp.dates < d)
            if earlier.shape[0] < 2 * WINDOW:
                assert windows is None
            else:
                np.testing.assert_allclose(np.concatenate(windows), inp.delta[earlier[-2 * WINDOW:]], rtol=0, atol=1e-12)
            rows = np.flatnonzero(inp.dates == d)
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


class _RecScheme(SchemeAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log = {}

    def stake_fractions(self, view, p_hat, b):
        f = super().stake_fractions(view, p_hat, b)
        self.log[view.date] = (view.probs.copy(), view.odds.copy(), p_hat.copy(), b.copy(), f.copy())
        return f


def _scheme(sup: Module2Supervisor) -> SchemeAgent:
    """Schema con soglie basse, così l'allarme scatta spesso."""
    return _RecScheme("C3", sup, 0.75, 0.5, 0.5, 0.01, SCHEME_STOP_CLEAR)


def test_separation_of_responsibilities(training):
    """Stesse previsioni e quote viste, stessa selezione di B_0.25; lo schema cambia solo le frazioni."""
    _, covs, inputs = training
    for inp in inputs.values():
        sup = Module2Supervisor(inp.season, inp.dates, inp.x, covs, WINDOW)
        b_agent, scheme = _RecB("B_0.25", 0.25), _scheme(sup)
        run_paired_backtest([b_agent, scheme], inp.dates, inp.probs, inp.odds, inp.outcomes, 0.0)
        assert scheme.log.keys() == b_agent.log.keys()
        assert scheme.n_onsets > 0
        for d, (probs, odds, p_hat, b, f) in scheme.log.items():
            ref = b_agent.log[d]
            np.testing.assert_array_equal(probs, ref[0])
            np.testing.assert_array_equal(odds, ref[1])
            np.testing.assert_array_equal(p_hat, ref[2])
            np.testing.assert_array_equal(b, ref[3])
            assert np.all((f >= 0.0) & (f < 1.0))


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


def _supervisor_outputs(runner, supervisor_cls, inp, covs, outcomes):
    sup = supervisor_cls(inp.season, inp.dates, inp.x, covs, WINDOW)
    runner([_scheme(sup)], inp.dates, inp.probs, inp.odds, outcomes, 0.0)
    out = {}
    for d in np.unique(inp.dates):
        res = sup.state_at(d).result
        windows = sup.delta_windows(d)
        out[d] = (None if res is None else (res.total, res.structural),
                  None if windows is None else tuple(np.concatenate(windows)))
    return out


def test_supervisor_anti_leakage_with_mutant(training):
    """Alterare gli esiti di date >= d non cambia ciò che il supervisore usa a d; il mutante sì."""
    _, covs, inputs = training
    inp = inputs["2010-11"]
    days = np.unique(inp.dates)
    d0 = days[len(days) // 2]
    altered = inp.outcomes.copy()
    late = inp.dates >= d0
    altered[0, late] = (altered[0, late] + 1) % 3

    for runner in (run_paired_backtest, _mutant_run_paired_backtest()):
        base = _supervisor_outputs(runner, Module2Supervisor, inp, covs, inp.outcomes)
        alt = _supervisor_outputs(runner, Module2Supervisor, inp, covs, altered)
        for d in days[days <= d0]:
            assert base[d] == alt[d]

    # Mutante: ambiente che notifica prima delle decisioni e supervisore con Date <= d
    mutant = _mutant_run_paired_backtest()
    base = _supervisor_outputs(mutant, _LeakySupervisor, inp, covs, inp.outcomes)
    alt = _supervisor_outputs(mutant, _LeakySupervisor, inp, covs, altered)
    assert base[d0][0] is not None and base[d0] != alt[d0]
