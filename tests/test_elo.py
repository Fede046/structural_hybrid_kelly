"""Test unitari e criteri di accettazione per il modulo elo (Task 20)."""

import math
from typing import Final
import numpy as np
import pytest

from shk.model.elo import (
    constant_draw_probabilities,
    davidson_probabilities,
    elo_delta,
    elo_update,
    expected_score,
)

# 24 valori di riferimento delle note 2.8 §3.3 da riprodurre con s = 200 entro 5e-4
# Formato: delta -> {nu -> (p_home, p_draw, p_away)}
REFERENCE_TABLE_NOTE_2_8: Final[dict[float, dict[float, tuple[float, float, float]]]] = {
    0.0: {
        0.8: (0.357, 0.286, 0.357),
        1.1: (0.323, 0.355, 0.323),
    },
    100.0: {
        0.8: (0.566, 0.255, 0.179),
        1.1: (0.517, 0.320, 0.163),
    },
    200.0: {
        0.8: (0.739, 0.187, 0.074),
        1.1: (0.691, 0.240, 0.069),
    },
    400.0: {
        0.8: (0.917, 0.073, 0.009),
        1.1: (0.893, 0.098, 0.009),
    },
}

NU_TEST_LIST: Final[list[float]] = [0.05, 0.5, 0.8, 1.0, 1.1, 2.0, 3.0]


# ==============================================================================
# 1. elo_delta tests
# ==============================================================================


def test_elo_delta_scalar_calculation():
    """Verifica il calcolo di elo_delta su scalari Python e NumPy."""
    assert elo_delta(1500, 1500) == 0.0
    assert elo_delta(1600.0, 1400.0) == 200.0
    assert elo_delta(1600.0, 1400.0, h=50.0) == 250.0
    assert elo_delta(np.int64(1500), np.float64(1450.0), h=np.float32(25.0)) == 75.0
    assert isinstance(elo_delta(1500, 1500), float)


def test_elo_delta_validations():
    """Verifica validazioni di tipo e valore per elo_delta."""
    with pytest.raises(TypeError):
        elo_delta(True, 1500.0)  # bool
    with pytest.raises(TypeError):
        elo_delta(1500.0, np.bool_(False))  # np.bool_
    with pytest.raises(TypeError):
        elo_delta("1500", 1400.0)  # stringa numerica
    with pytest.raises(TypeError):
        elo_delta(1500.0, 1400.0, h="50")  # stringa numerica
    with pytest.raises(TypeError):
        elo_delta([1500.0], 1400.0)  # lista
    with pytest.raises(ValueError):
        elo_delta(float("nan"), 1500.0)
    with pytest.raises(ValueError):
        elo_delta(1500.0, float("inf"))
    with pytest.raises(ValueError):
        elo_delta(1500.0, 1400.0, h=float("-inf"))


# ==============================================================================
# 2. expected_score tests
# ==============================================================================


def test_expected_score_scalar_and_array_types():
    """Verifica il tipo restituito da expected_score per scalari e ndarray."""
    # Scalare Python int -> float nativo
    e_int = expected_score(0, s=400)
    assert type(e_int) is float
    assert e_int == 0.5

    # Scalare Python float -> float nativo
    e_flt = expected_score(100.0, s=400.0)
    assert type(e_flt) is float

    # Scalare NumPy -> float nativo
    e_np = expected_score(np.float64(200.0), s=np.int32(400))
    assert type(e_np) is float

    # Array a 0 dimensioni -> np.ndarray float64 di forma ()
    arr_0d = np.array(100.0)
    e_0d = expected_score(arr_0d, s=400.0)
    assert isinstance(e_0d, np.ndarray)
    assert e_0d.shape == ()
    assert e_0d.dtype == np.float64

    # Array 1D -> np.ndarray float64 di forma (N,)
    arr_1d = np.array([-100.0, 0.0, 100.0])
    e_1d = expected_score(arr_1d, s=400.0)
    assert isinstance(e_1d, np.ndarray)
    assert e_1d.shape == (3,)
    assert e_1d.dtype == np.float64
    assert np.allclose(e_1d, [1.0 / (1.0 + 10**0.25), 0.5, 1.0 / (1.0 + 10**-0.25)])

    # Array 2D intero -> np.ndarray float64 di forma (M, N)
    arr_2d = np.array([[-200, 0], [200, 400]], dtype=np.int32)
    e_2d = expected_score(arr_2d, s=400.0)
    assert isinstance(e_2d, np.ndarray)
    assert e_2d.shape == (2, 2)
    assert e_2d.dtype == np.float64


def test_expected_score_validations():
    """Verifica eccezioni sollevate da expected_score."""
    with pytest.raises(TypeError):
        expected_score(True)
    with pytest.raises(TypeError):
        expected_score(np.bool_(False))
    with pytest.raises(TypeError):
        expected_score("200")
    with pytest.raises(TypeError):
        expected_score([0.0, 100.0])  # lista Python al posto di ndarray
    with pytest.raises(TypeError):
        expected_score(np.array([True, False]))  # ndarray bool
    with pytest.raises(TypeError):
        expected_score(np.array([1.0 + 2.0j]))  # ndarray complesso
    with pytest.raises(TypeError):
        expected_score(100.0, s=True)  # s bool
    with pytest.raises(TypeError):
        expected_score(100.0, s="400")  # s stringa numerica
    with pytest.raises(ValueError):
        expected_score(100.0, s=0.0)  # s <= 0
    with pytest.raises(ValueError):
        expected_score(100.0, s=-400.0)
    with pytest.raises(ValueError):
        expected_score(100.0, s=float("nan"))
    with pytest.raises(ValueError):
        expected_score(float("nan"), s=400.0)
    with pytest.raises(ValueError):
        expected_score(float("inf"), s=400.0)
    with pytest.raises(ValueError):
        expected_score(np.array([0.0, float("nan")]), s=400.0)


# ==============================================================================
# 3. elo_update tests
# ==============================================================================


@pytest.mark.parametrize("outcome", ["H", "D", "A"])
@pytest.mark.parametrize(
    ("r_h", "r_a", "k", "h"),
    [
        (1500.0, 1500.0, 20.0, 0.0),
        (1600.0, 1400.0, 32.0, 50.0),
        (1350.0, 1750.0, 40.0, 100.0),
        (1800.0, 1200.0, 10.0, 0.0),
    ],
)
def test_elo_update_zero_sum(outcome: str, r_h: float, r_a: float, k: float, h: float):
    """Criterio Somma zero: la somma dei due rating resta invariata entro 1e-12."""
    r_h_new, r_a_new = elo_update(r_h, r_a, outcome, k=k, h=h, s=400.0)
    initial_sum = r_h + r_a
    final_sum = r_h_new + r_a_new
    assert abs(final_sum - initial_sum) <= 1e-12


def test_elo_update_direction():
    """Verifica la coerenza del verso di aggiornamento."""
    # Con vittoria casa (H), rating casa cresce e rating trasferta scende
    r_h_new, r_a_new = elo_update(1500.0, 1500.0, "H", k=20.0)
    assert r_h_new > 1500.0
    assert r_a_new < 1500.0

    # Con vittoria trasferta (A), rating casa scende e rating trasferta cresce
    r_h_new, r_a_new = elo_update(1500.0, 1500.0, "A", k=20.0)
    assert r_h_new < 1500.0
    assert r_a_new > 1500.0

    # Con pareggio (D) e quote alla pari (delta = 0 -> E = 0.5), rating invariati
    r_h_new, r_a_new = elo_update(1500.0, 1500.0, "D", k=20.0, h=0.0)
    assert abs(r_h_new - 1500.0) <= 1e-12
    assert abs(r_a_new - 1500.0) <= 1e-12


def test_elo_update_zero_k():
    """Verifica che k = 0 lasci i rating invariati per tutti gli esiti."""
    for out in ("H", "D", "A"):
        r_h_new, r_a_new = elo_update(1600.0, 1400.0, out, k=0.0, h=50.0)
        assert r_h_new == 1600.0
        assert r_a_new == 1400.0


def test_elo_update_validations():
    """Verifica validazioni di elo_update."""
    with pytest.raises(TypeError):
        elo_update(True, 1500.0, "H", k=20.0)
    with pytest.raises(TypeError):
        elo_update(1500.0, np.bool_(False), "H", k=20.0)
    with pytest.raises(TypeError):
        elo_update(1500.0, 1500.0, "H", k=True)
    with pytest.raises(TypeError):
        elo_update(1500.0, 1500.0, "H", k="20")
    with pytest.raises(TypeError):
        elo_update(1500.0, 1500.0, 1, k=20.0)  # outcome non str
    with pytest.raises(ValueError):
        elo_update(1500.0, 1500.0, "h", k=20.0)  # outcome minuscolo
    with pytest.raises(ValueError):
        elo_update(1500.0, 1500.0, "", k=20.0)  # outcome stringa vuota
    with pytest.raises(ValueError):
        elo_update(1500.0, 1500.0, "X", k=20.0)  # outcome non valido
    with pytest.raises(ValueError):
        elo_update(1500.0, 1500.0, "H", k=-5.0)  # k < 0
    with pytest.raises(ValueError):
        elo_update(1500.0, 1500.0, "H", k=float("inf"))
    with pytest.raises(ValueError):
        elo_update(1500.0, 1500.0, "H", k=20.0, s=0.0)


# ==============================================================================
# 4. davidson_probabilities tests
# ==============================================================================


def test_davidson_sum_to_one_and_bounds():
    """Criterio Somma a 1 e probabilità in (0, 1) per Davidson su griglia [-800, 800] x [0.05, 3]."""
    delta_grid = np.linspace(-800.0, 800.0, 161)
    nu_grid = np.linspace(0.05, 3.0, 60)

    for nu in nu_grid:
        p_home, p_draw, p_away = davidson_probabilities(delta_grid, nu=nu, s=400.0)

        assert isinstance(p_home, np.ndarray)
        assert isinstance(p_draw, np.ndarray)
        assert isinstance(p_away, np.ndarray)

        # Somma a 1 entro 1e-12
        p_sum = p_home + p_draw + p_away
        assert np.all(np.abs(p_sum - 1.0) <= 1e-12)

        # Tutte le probabilità strettamente in (0, 1)
        assert np.all(p_home > 0.0) and np.all(p_home < 1.0)
        assert np.all(p_draw > 0.0) and np.all(p_draw < 1.0)
        assert np.all(p_away > 0.0) and np.all(p_away < 1.0)


def test_davidson_reference_table_notes_2_8():
    """Criterio Tabella Note 2.8 §3.3: 24 valori riprodotti con s = 200 entro 5e-4."""
    for delta, nu_dict in REFERENCE_TABLE_NOTE_2_8.items():
        for nu, (ref_home, ref_draw, ref_away) in nu_dict.items():
            p_home, p_draw, p_away = davidson_probabilities(delta, nu=nu, s=200.0)

            # Verifica accuratezza entro 5e-4 (0.0005)
            assert abs(p_home - ref_home) <= 5e-4, f"Mismatch on p_home for delta={delta}, nu={nu}"
            assert abs(p_draw - ref_draw) <= 5e-4, f"Mismatch on p_draw for delta={delta}, nu={nu}"
            assert abs(p_away - ref_away) <= 5e-4, f"Mismatch on p_away for delta={delta}, nu={nu}"


def test_davidson_symmetry():
    """Criterio Simmetria: delta -> -delta scambia p_home e p_away, lascia p_draw invariato."""
    delta_pos = np.linspace(0.0, 800.0, 81)
    delta_neg = -delta_pos

    for nu in NU_TEST_LIST:
        p_h_pos, p_d_pos, p_a_pos = davidson_probabilities(delta_pos, nu=nu, s=400.0)
        p_h_neg, p_d_neg, p_a_neg = davidson_probabilities(delta_neg, nu=nu, s=400.0)

        # delta -> -delta scambia p_home e p_away
        assert np.all(np.abs(p_h_pos - p_a_neg) <= 1e-12)
        assert np.all(np.abs(p_a_pos - p_h_neg) <= 1e-12)

        # p_draw è identico per delta e -delta
        assert np.all(np.abs(p_d_pos - p_d_neg) <= 1e-12)


def test_davidson_draw_monotonicity():
    """Criterio Monotonia: p_draw strettamente decrescente su [0, 800] e crescente su [-800, 0]."""
    delta_pos = np.linspace(0.0, 800.0, 161)
    delta_neg = np.linspace(-800.0, 0.0, 161)

    for nu in NU_TEST_LIST:
        # Su [0, 800]: strettamente decrescente
        _, p_draw_pos, _ = davidson_probabilities(delta_pos, nu=nu, s=400.0)
        diff_pos = np.diff(p_draw_pos)
        assert np.all(diff_pos < 0.0), f"p_draw is not strictly decreasing on [0, 800] for nu={nu}"

        # Su [-800, 0]: strettamente crescente
        _, p_draw_neg, _ = davidson_probabilities(delta_neg, nu=nu, s=400.0)
        diff_neg = np.diff(p_draw_neg)
        assert np.all(diff_neg > 0.0), f"p_draw is not strictly increasing on [-800, 0] for nu={nu}"


def test_davidson_limit_nu_zero():
    """Criterio Limite nu -> 0: con nu = 1e-12, p_home coincide con E entro 1e-9."""
    delta_grid = np.linspace(-800.0, 800.0, 161)
    e = expected_score(delta_grid, s=400.0)
    p_home, _, _ = davidson_probabilities(delta_grid, nu=1e-12, s=400.0)

    assert np.all(np.abs(p_home - e) <= 1e-9)


def test_davidson_return_types():
    """Verifica tipi restituiti da davidson_probabilities per scalari e array."""
    # Scalare Python
    p_h, p_d, p_a = davidson_probabilities(100.0, nu=0.8, s=400.0)
    assert type(p_h) is float
    assert type(p_d) is float
    assert type(p_a) is float

    # Scalare NumPy
    p_h, p_d, p_a = davidson_probabilities(np.float64(100.0), nu=np.float32(0.8))
    assert type(p_h) is float
    assert type(p_d) is float
    assert type(p_a) is float

    # 0-d array
    p_h, p_d, p_a = davidson_probabilities(np.array(100.0), nu=0.8)
    assert isinstance(p_h, np.ndarray) and p_h.shape == () and p_h.dtype == np.float64
    assert isinstance(p_d, np.ndarray) and p_d.shape == () and p_d.dtype == np.float64
    assert isinstance(p_a, np.ndarray) and p_a.shape == () and p_a.dtype == np.float64

    # 1D array
    p_h, p_d, p_a = davidson_probabilities(np.array([-50.0, 50.0]), nu=0.8)
    assert isinstance(p_h, np.ndarray) and p_h.shape == (2,) and p_h.dtype == np.float64
    assert isinstance(p_d, np.ndarray) and p_d.shape == (2,) and p_d.dtype == np.float64
    assert isinstance(p_a, np.ndarray) and p_a.shape == (2,) and p_a.dtype == np.float64


def test_davidson_validations():
    """Verifica eccezioni sollevate da davidson_probabilities."""
    with pytest.raises(TypeError):
        davidson_probabilities(True, nu=0.8)
    with pytest.raises(TypeError):
        davidson_probabilities(np.bool_(False), nu=0.8)
    with pytest.raises(TypeError):
        davidson_probabilities(100.0, nu=True)
    with pytest.raises(TypeError):
        davidson_probabilities(100.0, nu=np.bool_(True))
    with pytest.raises(TypeError):
        davidson_probabilities([100.0], nu=0.8)  # lista
    with pytest.raises(TypeError):
        davidson_probabilities("100", nu=0.8)  # stringa numerica
    with pytest.raises(TypeError):
        davidson_probabilities(100.0, nu="0.8")  # stringa numerica
    with pytest.raises(TypeError):
        davidson_probabilities(np.array([True]), nu=0.8)  # ndarray bool
    with pytest.raises(TypeError):
        davidson_probabilities(np.array([1.0 + 1.0j]), nu=0.8)  # ndarray complesso
    with pytest.raises(ValueError):
        davidson_probabilities(100.0, nu=0.0)  # nu <= 0
    with pytest.raises(ValueError):
        davidson_probabilities(100.0, nu=-0.5)
    with pytest.raises(ValueError):
        davidson_probabilities(100.0, nu=float("nan"))
    with pytest.raises(ValueError):
        davidson_probabilities(float("nan"), nu=0.8)
    with pytest.raises(ValueError):
        davidson_probabilities(100.0, nu=0.8, s=0.0)
    with pytest.raises(ValueError):
        davidson_probabilities(np.array([0.0, float("inf")]), nu=0.8)


# ==============================================================================
# 5. constant_draw_probabilities tests
# ==============================================================================


def test_constant_draw_sum_to_one_and_bounds():
    """Criterio Somma a 1 e probabilità in (0, 1) per pareggio costante su griglia [-800, 800] x [0.01, 0.99]."""
    delta_grid = np.linspace(-800.0, 800.0, 161)
    c_grid = np.linspace(0.01, 0.99, 99)

    for c in c_grid:
        p_home, p_draw, p_away = constant_draw_probabilities(delta_grid, c=c, s=400.0)

        assert isinstance(p_home, np.ndarray)
        assert isinstance(p_draw, np.ndarray)
        assert isinstance(p_away, np.ndarray)

        # Somma a 1 entro 1e-12
        p_sum = p_home + p_draw + p_away
        assert np.all(np.abs(p_sum - 1.0) <= 1e-12)

        # Tutte le probabilità strettamente in (0, 1)
        assert np.all(p_home > 0.0) and np.all(p_home < 1.0)
        assert np.all(p_draw > 0.0) and np.all(p_draw < 1.0)
        assert np.all(p_away > 0.0) and np.all(p_away < 1.0)


def test_constant_draw_exact_c():
    """Criterio p_draw = c esatto (==) senza tolleranza, su scalari e array float e int."""
    c_val = 0.28

    # 1. Delta scalare Python
    _, p_draw_scalar, _ = constant_draw_probabilities(150.0, c=c_val)
    assert p_draw_scalar == c_val
    assert type(p_draw_scalar) is float

    # 2. Delta ndarray float
    delta_float = np.array([-200.0, 0.0, 200.0], dtype=np.float64)
    _, p_draw_float, _ = constant_draw_probabilities(delta_float, c=c_val)
    assert np.all(p_draw_float == c_val)
    assert p_draw_float.dtype == np.float64
    assert p_draw_float.shape == (3,)

    # 3. Delta ndarray intero (verifica che p_draw non erediti il dtype intero)
    delta_int = np.array([-150, 0, 150], dtype=np.int32)
    _, p_draw_int, _ = constant_draw_probabilities(delta_int, c=c_val)
    assert np.all(p_draw_int == c_val)
    assert p_draw_int.dtype == np.float64
    assert p_draw_int.shape == (3,)


def test_constant_draw_e_ratio():
    """Criterio p_home / (p_home + p_away) = E entro 1e-12."""
    delta_grid = np.linspace(-800.0, 800.0, 161)
    e = expected_score(delta_grid, s=400.0)

    for c in [0.05, 0.25, 0.50, 0.75, 0.95]:
        p_home, _, p_away = constant_draw_probabilities(delta_grid, c=c, s=400.0)
        ratio = p_home / (p_home + p_away)
        assert np.all(np.abs(ratio - e) <= 1e-12)


def test_constant_draw_return_types():
    """Verifica tipi restituiti da constant_draw_probabilities."""
    # Scalare Python
    p_h, p_d, p_a = constant_draw_probabilities(100.0, c=0.25)
    assert type(p_h) is float
    assert type(p_d) is float
    assert type(p_a) is float

    # 0-d array
    p_h, p_d, p_a = constant_draw_probabilities(np.array(100.0), c=0.25)
    assert isinstance(p_h, np.ndarray) and p_h.shape == () and p_h.dtype == np.float64
    assert isinstance(p_d, np.ndarray) and p_d.shape == () and p_d.dtype == np.float64
    assert isinstance(p_a, np.ndarray) and p_a.shape == () and p_a.dtype == np.float64

    # 1D array
    p_h, p_d, p_a = constant_draw_probabilities(np.array([-50.0, 50.0]), c=0.25)
    assert isinstance(p_h, np.ndarray) and p_h.shape == (2,) and p_h.dtype == np.float64
    assert isinstance(p_d, np.ndarray) and p_d.shape == (2,) and p_d.dtype == np.float64
    assert isinstance(p_a, np.ndarray) and p_a.shape == (2,) and p_a.dtype == np.float64


def test_constant_draw_validations():
    """Verifica eccezioni sollevate da constant_draw_probabilities."""
    with pytest.raises(TypeError):
        constant_draw_probabilities(True, c=0.25)
    with pytest.raises(TypeError):
        constant_draw_probabilities(np.bool_(False), c=0.25)
    with pytest.raises(TypeError):
        constant_draw_probabilities(100.0, c=True)
    with pytest.raises(TypeError):
        constant_draw_probabilities([100.0], c=0.25)  # lista
    with pytest.raises(TypeError):
        constant_draw_probabilities("100", c=0.25)  # stringa numerica
    with pytest.raises(TypeError):
        constant_draw_probabilities(100.0, c="0.25")  # stringa numerica
    with pytest.raises(TypeError):
        constant_draw_probabilities(np.array([True]), c=0.25)  # ndarray bool
    with pytest.raises(TypeError):
        constant_draw_probabilities(np.array([1.0 + 2.0j]), c=0.25)  # ndarray complesso
    with pytest.raises(ValueError):
        constant_draw_probabilities(100.0, c=0.0)  # c <= 0
    with pytest.raises(ValueError):
        constant_draw_probabilities(100.0, c=1.0)  # c >= 1
    with pytest.raises(ValueError):
        constant_draw_probabilities(100.0, c=-0.1)
    with pytest.raises(ValueError):
        constant_draw_probabilities(100.0, c=1.1)
    with pytest.raises(ValueError):
        constant_draw_probabilities(100.0, c=float("nan"))
    with pytest.raises(ValueError):
        constant_draw_probabilities(float("inf"), c=0.25)
    with pytest.raises(ValueError):
        constant_draw_probabilities(100.0, c=0.25, s=0.0)
