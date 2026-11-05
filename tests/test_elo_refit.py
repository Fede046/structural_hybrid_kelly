"""Test: schema dei fit della ri-parametrizzazione annuale dell'Elo."""

import pytest

from shk.model.elo_refit import refit_schedule


def test_refit_schedule_uses_previous_season_with_b365():
    available = ["1999-00", "2000-01", "2001-02", "2002-03", "2003-04", "2004-05"]
    schedule = refit_schedule(["2004-05", "2002-03", "2003-04"], available)
    # il 2001-02 non ha B365: il 2002-03 si prevede col 2000-01
    assert schedule == {
        "2000-01": {"training": ["2000-01"], "validation": ["2002-03"]},
        "2002-03": {"training": ["2002-03"], "validation": ["2003-04"]},
        "2003-04": {"training": ["2003-04"], "validation": ["2004-05"]},
    }


def test_refit_schedule_needs_an_earlier_season():
    with pytest.raises(ValueError):
        refit_schedule(["2000-01"], ["2000-01", "2001-02"])
