"""Test: agente dello schema del relatore (C3, C3_stop), statistiche e soglie dell'allarme ANOVA."""

import math
from types import SimpleNamespace

import numpy as np
import pytest
import scipy.stats

from shk.kelly.agents import DateResults, DateView
from shk.model.agent_c import (
    DIAGNOSIS_COMPOSITIONAL,
    DIAGNOSIS_NONE,
    DIAGNOSIS_STRUCTURAL,
    SCHEME_STOP_CLEAR,
    SCHEME_STOP_SEASON,
    Module2Supervisor,
    SchemeAgent,
    SupervisorState,
    calibrate_scheme_thresholds,
    scheme_statistics,
)
from shk.model.module2 import STATE_ACTIVE, Module2Output
from shk.stats.calibration import compute_order_statistic_index, moving_block_indices

QUIET = (np.array([0.0, 0.1, -0.1, 0.05]), np.array([0.02, 0.08, -0.05, 0.03]))


class _ScriptedSupervisor(Module2Supervisor):
    """Supervisore con finestre di δ e S prefissate per data (None: meno di 2W partite / non attivo)."""

    def __init__(self, dates: np.ndarray, windows: list, structural: list[float | None]) -> None:
        super().__init__("s", dates, np.zeros((dates.shape[0], 1)), ["c"], 3)
        days = np.unique(dates)
        self._windows = dict(zip(days, windows))
        self._structural = dict(zip(days, structural))

    def delta_windows(self, decision_date: np.datetime64):
        return self._windows[np.datetime64(decision_date, "ns")]

    def state_at(self, decision_date: np.datetime64) -> SupervisorState:
        s = self._structural[np.datetime64(decision_date, "ns")]
        state = STATE_ACTIVE if s is not None else "not_active"
        result = SimpleNamespace(structural=s) if s is not None else None
        out = Module2Output("s", None, 3, state, 0, 0, 0, math.nan, math.nan, result, math.nan)
        return SupervisorState(out, None, None, None)


def test_scheme_statistics_match_scipy_with_sign():
    """F della media = f_oneway se B peggiora, F di dispersione = levene(median) se B è più dispersa."""
    rng = np.random.default_rng(0)
    a = rng.normal(0.0, 0.2, 40)
    b = rng.normal(0.0, 0.5, 40) - 0.5
    f_mean, f_disp = scheme_statistics(a, b)
    assert f_mean == pytest.approx(scipy.stats.f_oneway(a, b).statistic, rel=1e-10)
    assert f_disp == pytest.approx(scipy.stats.levene(a, b, center="median").statistic, rel=1e-10)
    # Ruoli scambiati: B migliora ed è meno dispersa, nessuna delle due conta
    assert scheme_statistics(b, a) == (0.0, 0.0)
    # Lotto = riga per riga
    batch_a, batch_b = rng.normal(size=(5, 30)), rng.normal(size=(5, 30))
    fm, fd = scheme_statistics(batch_a, batch_b)
    for i in range(5):
        assert (fm[i], fd[i]) == pytest.approx(scheme_statistics(batch_a[i], batch_b[i]), rel=1e-12)


def test_scheme_thresholds_are_order_statistics_at_half_alpha():
    """Soglie = statistica d'ordine ceil((1 − α/2)(B + 1)) delle F con segno sui ricampionamenti."""
    delta = np.random.default_rng(1).normal(0.0, 0.3, 150)
    w, length = 30, 6
    mean_thr, disp_thr = calibrate_scheme_thresholds(delta, w, length, np.random.default_rng(2))
    idx = moving_block_indices(150, length, 999, np.random.default_rng(2))[:, :2 * w]
    fm, fd = scheme_statistics(delta[idx[:, :w]], delta[idx[:, w:]])
    k = compute_order_statistic_index(999, 0.025)
    assert mean_thr == np.sort(fm)[k - 1]
    assert disp_thr == np.sort(fd)[k - 1]
    with pytest.raises(ValueError):
        calibrate_scheme_thresholds(delta[:50], w, length, np.random.default_rng(2))


def _days(n: int) -> np.ndarray:
    return (np.datetime64("2010-08-14") + np.arange(n) * np.timedelta64(7, "D")).astype("datetime64[ns]")


def test_scheme_agent_diagnosis_and_lambda():
    """Composizione: λ = 0.25·κ finché dura l'allarme; strutturale: λ = 0 finché dura (C3) o fino a fine stagione (C3_stop)."""
    days = _days(7)
    worse = (np.array([0.0, 0.1, 0.2, 0.1]), np.array([-1.0, -1.2, -0.9, -1.1]))
    windows = [None, worse, worse, QUIET, worse, QUIET, worse]
    # S: None = Modulo 2 non attivo; −0.2 strutturale (T = 0.2 > 0.1); −0.05 sotto soglia
    structural = [None, -0.05, -0.2, -0.2, None, None, 0.3]
    probs = np.array([[0.6, 0.25, 0.15]])
    odds = np.array([[2.0, 3.6, 7.0]])
    expected_diag = [DIAGNOSIS_NONE, DIAGNOSIS_COMPOSITIONAL, DIAGNOSIS_STRUCTURAL, DIAGNOSIS_NONE,
                     DIAGNOSIS_COMPOSITIONAL, DIAGNOSIS_NONE, DIAGNOSIS_COMPOSITIONAL]
    expected = {
        SCHEME_STOP_CLEAR: [0.25, 0.125, 0.0, 0.25, 0.125, 0.25, 0.125],
        SCHEME_STOP_SEASON: [0.25, 0.125, 0.0, 0.0, 0.0, 0.0, 0.0],
    }
    for stop, lam in expected.items():
        agent = SchemeAgent("C3", _ScriptedSupervisor(days, windows, structural), 0.5, 1.0, 1.0, 0.1, stop)
        decisions = [agent.decide(DateView(d, probs, odds)) for d in days]
        assert [agent.diagnosis_by_date[d] for d in days] == expected_diag
        assert [agent.lambda_by_date[d] for d in days] == lam
        assert agent.n_onsets == 3
        b = odds[0, 0] - 1.0
        full = (b * probs[0, 0] - (1.0 - probs[0, 0])) / b
        for dec, l in zip(decisions, lam):
            assert dec.fractions[0] == pytest.approx(l * full)


def test_scheme_agent_validates_arguments():
    sup = _ScriptedSupervisor(_days(1), [None], [None])
    with pytest.raises(ValueError):
        SchemeAgent("C3", sup, 0.5, 1.0, 1.0, 0.1, "never")
    with pytest.raises(ValueError):
        SchemeAgent("C3", sup, 1.5, 1.0, 1.0, 0.1, SCHEME_STOP_CLEAR)
    with pytest.raises(ValueError):
        SchemeAgent("C3", sup, 0.5, math.nan, 1.0, 0.1, SCHEME_STOP_CLEAR)
    with pytest.raises(TypeError):
        SchemeAgent("C3", object(), 0.5, 1.0, 1.0, 0.1, SCHEME_STOP_CLEAR)


def test_delta_windows_use_only_earlier_dates():
    """Finestre di δ dalle sole partite osservate con Date < d, le ultime 2W in ordine."""
    days = _days(8)
    sup = Module2Supervisor("s", days, np.random.default_rng(3).normal(size=(8, 1)), ["c"], 3)
    probs = np.array([[0.5, 0.3, 0.2]])
    odds = np.array([[1.9, 3.4, 4.5]])
    assert sup.delta_windows(days[5]) is None
    for i, d in enumerate(days):
        sup.observe(DateResults(d, probs, odds, np.array([[i % 3]])))
    deltas = [sup.delta_windows(days[7])[0], sup.delta_windows(days[7])[1]]
    full = np.array([sup._delta[i] for i in range(7)])
    np.testing.assert_array_equal(deltas[0], full[1:4])
    np.testing.assert_array_equal(deltas[1], full[4:7])
    assert sup.delta_windows(days[5]) is None
