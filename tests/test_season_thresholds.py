"""Test: soglie dell'allarme calibrate sull'intera stagione (shk.model.season_thresholds), su dati costruiti."""

import numpy as np
import pytest

from shk.model.agent_c import calibrate_reference_thresholds, reference_statistics
from shk.model.scheme_reference_run import ReferenceSetup
from shk.model.season_thresholds import calibrate_season_alarm_thresholds, decision_ends, season_level_setup

WINDOW = 40


def _dates(n_days: int = 38, per_day: int = 10) -> np.ndarray:
    days = np.arange("2020-01-01", n_days, dtype="datetime64[D]").astype("datetime64[ns]")
    return np.repeat(days, per_day)


def test_decision_ends_count_the_earlier_matches():
    dates = _dates(6, 10)
    assert list(decision_ends(dates, 20)) == [20, 30, 40, 50]
    assert decision_ends(dates, 60).shape == (0,)
    uneven = np.array(["2020-01-01"] * 3 + ["2020-01-02"] * 2 + ["2020-01-05"] * 4, dtype="datetime64[ns]")
    assert list(decision_ends(uneven, 3)) == [3, 5]
    with pytest.raises(ValueError):
        decision_ends(dates[::-1], 20)


def test_season_level_setup_changes_only_the_alarm_thresholds():
    rng = np.random.default_rng(0)
    x, delta = rng.normal(size=(380, 3)), rng.normal(size=380)
    setup = ReferenceSetup(3.0, 3.0, 0.1, x, delta)
    out = season_level_setup(setup, _dates(), WINDOW, 5, np.random.default_rng(1))
    assert out.mean_threshold > setup.mean_threshold and out.dispersion_threshold > setup.dispersion_threshold
    assert out.structural_threshold == setup.structural_threshold
    assert out.x is setup.x and out.delta is setup.delta
    with pytest.raises(ValueError):
        calibrate_season_alarm_thresholds(delta[:30], _dates()[:30], WINDOW, 5, np.random.default_rng(1))


def test_season_level_thresholds_control_the_alarm_over_a_whole_season():
    """Stagioni i.i.d. senza cambiamenti: con le soglie per giornata almeno un allarme in molte stagioni,
    con le soglie per stagione in poche."""
    rng = np.random.default_rng(2)
    dates = _dates()
    ends = decision_ends(dates, WINDOW)
    windows = ends[:, None] - WINDOW + np.arange(WINDOW)[None, :]
    rates = {"per_date": [], "per_season": []}
    for k in range(8):  # più riferimenti: la garanzia vale in media sul riferimento
        reference = rng.normal(size=380)
        per_date = calibrate_reference_thresholds(rng.normal(size=(380, 3)), reference, WINDOW, 5,
                                                  np.random.default_rng(10 + k))[:2]
        per_season = calibrate_season_alarm_thresholds(reference, dates, WINDOW, 5, np.random.default_rng(20 + k))
        fresh = rng.normal(size=(250, 380))
        f_mean, f_disp = reference_statistics(reference, fresh[:, windows].reshape(-1, WINDOW))
        f_mean, f_disp = f_mean.reshape(250, -1), f_disp.reshape(250, -1)
        for name, (mean_thr, disp_thr) in (("per_date", per_date), ("per_season", per_season)):
            rates[name].append(float(((f_mean > mean_thr) | (f_disp > disp_thr)).any(axis=1).mean()))
    assert np.mean(rates["per_date"]) > 0.3
    assert np.mean(rates["per_season"]) < 0.12
