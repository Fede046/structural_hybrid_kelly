"""Unit tests for the core Kelly criterion analytical functions."""

import numpy as np
import pytest

from shk.kelly.core import kelly_fraction, log_growth_rate


def test_kelly_fraction_positive_edge():
    """Verify optimal Kelly fraction for positive edge (p=0.60, b=1.0)."""
    expected = 0.20
    actual = kelly_fraction(0.60, 1.0)
    assert abs(actual - expected) < 1e-12


def test_kelly_fraction_non_positive_edge():
    """Verify Kelly fraction returns 0.0 when edge is non-positive."""
    # Negative edge: p=0.40, b=1.0 -> (1*0.4 - 0.6)/1 = -0.2 <= 0 -> 0.0
    assert kelly_fraction(0.40, 1.0) == 0.0
    # Zero edge: p=0.50, b=1.0 -> (1*0.5 - 0.5)/1 = 0.0 -> 0.0
    assert kelly_fraction(0.50, 1.0) == 0.0


def test_log_growth_rate_zero_fraction():
    """Verify log growth rate is 0.0 when no fraction is wagered (f=0.0)."""
    assert log_growth_rate(0.0, 0.60, 1.0) == 0.0


def test_log_growth_rate_optimal_fraction():
    """Verify log growth rate at optimal fraction f=0.20 is approx 0.020136."""
    actual = log_growth_rate(0.20, 0.60, 1.0)
    assert actual == pytest.approx(0.020136, abs=1e-6)


def test_log_growth_rate_overbetting_negative():
    """Verify overbetting at f=0.40 yields a negative log growth rate (-0.002447)."""
    actual = log_growth_rate(0.40, 0.60, 1.0)
    assert actual < 0.0
    assert actual == pytest.approx(-0.002447, abs=1e-6)


def test_log_growth_rate_maximum_on_fine_grid():
    """Verify the maximum of log_growth_rate on [0, 0.99] falls at f=0.20 within grid step."""
    grid, step = np.linspace(0.0, 0.99, num=9901, retstep=True)
    rates = [log_growth_rate(float(f_val), 0.60, 1.0) for f_val in grid]
    f_argmax = grid[int(np.argmax(rates))]
    assert abs(f_argmax - 0.20) <= step


def test_kelly_fraction_error_conditions():
    """Verify ValueError is raised for invalid inputs in kelly_fraction."""
    # Invalid probabilities p not in [0, 1]
    with pytest.raises(ValueError):
        kelly_fraction(-0.1, 1.0)
    with pytest.raises(ValueError):
        kelly_fraction(1.1, 1.0)

    # Invalid odds b <= 0
    with pytest.raises(ValueError):
        kelly_fraction(0.60, 0.0)
    with pytest.raises(ValueError):
        kelly_fraction(0.60, -1.0)


def test_log_growth_rate_error_conditions():
    """Verify ValueError is raised for invalid inputs in log_growth_rate."""
    # Invalid fraction f not in [0, 1)
    with pytest.raises(ValueError):
        log_growth_rate(-0.01, 0.60, 1.0)
    with pytest.raises(ValueError):
        log_growth_rate(1.0, 0.60, 1.0)
    with pytest.raises(ValueError):
        log_growth_rate(1.5, 0.60, 1.0)

    # Invalid probabilities p not in [0, 1]
    with pytest.raises(ValueError):
        log_growth_rate(0.20, -0.05, 1.0)
    with pytest.raises(ValueError):
        log_growth_rate(0.20, 1.05, 1.0)

    # Invalid odds b <= 0
    with pytest.raises(ValueError):
        log_growth_rate(0.20, 0.60, 0.0)
    with pytest.raises(ValueError):
        log_growth_rate(0.20, 0.60, -2.0)

