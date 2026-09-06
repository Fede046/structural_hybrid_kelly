"""Test unitari per le funzioni analitiche di base del criterio di Kelly."""

import numpy as np
import pytest

from shk.kelly.core import kelly_fraction, log_growth_rate


def test_kelly_fraction_positive_edge():
    """Verifica la frazione ottimale di Kelly per un vantaggio positivo (p=0.60, b=1.0)."""
    expected = 0.20
    actual = kelly_fraction(0.60, 1.0)
    assert abs(actual - expected) < 1e-12


def test_kelly_fraction_non_positive_edge():
    """Verifica che la frazione di Kelly restituisca 0.0 quando il vantaggio non è positivo."""
    # Vantaggio negativo: p=0.40, b=1.0 -> (1*0.4 - 0.6)/1 = -0.2 <= 0 -> 0.0
    assert kelly_fraction(0.40, 1.0) == 0.0
    # Vantaggio nullo: p=0.50, b=1.0 -> (1*0.5 - 0.5)/1 = 0.0 -> 0.0
    assert kelly_fraction(0.50, 1.0) == 0.0


def test_log_growth_rate_zero_fraction():
    """Verifica che il tasso di crescita logaritmico sia 0.0 quando non viene scommessa alcuna frazione (f=0.0)."""
    assert log_growth_rate(0.0, 0.60, 1.0) == 0.0


def test_log_growth_rate_optimal_fraction():
    """Verifica che il tasso di crescita logaritmico alla frazione ottimale f=0.20 sia circa 0.020136."""
    actual = log_growth_rate(0.20, 0.60, 1.0)
    assert actual == pytest.approx(0.020136, abs=1e-6)


def test_log_growth_rate_overbetting_negative():
    """Verifica che il sovrainvestimento (overbetting) a f=0.40 produca un tasso di crescita logaritmico negativo (-0.002447)."""
    actual = log_growth_rate(0.40, 0.60, 1.0)
    assert actual < 0.0
    assert actual == pytest.approx(-0.002447, abs=1e-6)


def test_log_growth_rate_maximum_on_fine_grid():
    """Verifica che il massimo di log_growth_rate su [0, 0.99] ricada in f=0.20 entro il passo della griglia."""
    grid, step = np.linspace(0.0, 0.99, num=9901, retstep=True)
    rates = [log_growth_rate(float(f_val), 0.60, 1.0) for f_val in grid]
    f_argmax = grid[int(np.argmax(rates))]
    assert abs(f_argmax - 0.20) <= step


def test_kelly_fraction_error_conditions():
    """Verifica che venga sollevato ValueError per input non validi in kelly_fraction."""
    # Probabilità non valide con p non in [0, 1]
    with pytest.raises(ValueError):
        kelly_fraction(-0.1, 1.0)
    with pytest.raises(ValueError):
        kelly_fraction(1.1, 1.0)

    # Quote non valide con b <= 0
    with pytest.raises(ValueError):
        kelly_fraction(0.60, 0.0)
    with pytest.raises(ValueError):
        kelly_fraction(0.60, -1.0)


def test_log_growth_rate_error_conditions():
    """Verifica che venga sollevato ValueError per input non validi in log_growth_rate."""
    # Frazione f non valida non in [0, 1)
    with pytest.raises(ValueError):
        log_growth_rate(-0.01, 0.60, 1.0)
    with pytest.raises(ValueError):
        log_growth_rate(1.0, 0.60, 1.0)
    with pytest.raises(ValueError):
        log_growth_rate(1.5, 0.60, 1.0)

    # Probabilità non valide con p non in [0, 1]
    with pytest.raises(ValueError):
        log_growth_rate(0.20, -0.05, 1.0)
    with pytest.raises(ValueError):
        log_growth_rate(0.20, 1.05, 1.0)

    # Quote non valide con b <= 0
    with pytest.raises(ValueError):
        log_growth_rate(0.20, 0.60, 0.0)
    with pytest.raises(ValueError):
        log_growth_rate(0.20, 0.60, -2.0)

