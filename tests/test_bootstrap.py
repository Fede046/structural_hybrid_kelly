"""Test di src/shk/stats/bootstrap.py: lunghezza di Politis-White e stationary bootstrap."""

import ast
import math
import warnings
from pathlib import Path

import numpy as np
import pytest
import scipy.stats
from arch.bootstrap import optimal_block_length as arch_optimal_block_length

from shk.stats.bootstrap import (
    OptimalBlockLength,
    _stationary_block_layout,
    optimal_block_length,
    round_block_length,
    stationary_bootstrap_indices,
    stationary_bootstrap_mean_interval,
)
from shk.stats.calibration import moving_block_indices
from shk.stats.timeseries import generate_ar1_series

REPO_ROOT = Path(__file__).resolve().parents[1]
ARCH_PHI_VALUES = (0.0, 0.3, 0.5, 0.7)
ARCH_N_VALUES = (100, 380, 1000)
ARCH_SERIES_PER_CASE = 2
MIN_BLOCKS = 100_000


# ---------------------------------------------------------------------------
# Lunghezza ottima dei blocchi
# ---------------------------------------------------------------------------


def _arch_comparison_series() -> list[tuple[float, int, np.ndarray]]:
    """24 serie AR(1): 2 per ogni phi in {0, 0.3, 0.5, 0.7} e n in {100, 380, 1000}."""
    rng = np.random.default_rng(20261011)
    cases = []
    for phi in ARCH_PHI_VALUES:
        for n in ARCH_N_VALUES:
            for x in generate_ar1_series(phi, n, ARCH_SERIES_PER_CASE, rng):
                cases.append((phi, n, x))
    return cases


def test_optimal_block_length_matches_arch():
    """La lunghezza ottima coincide con arch entro 1e-6 relativo su 24 serie."""
    cases = _arch_comparison_series()
    assert len(cases) >= 20
    for phi, n, x in cases:
        ours = optimal_block_length(x)
        ref = arch_optimal_block_length(x)
        for ours_val, ref_val in (
            (ours.stationary, float(ref["stationary"].iloc[0])),
            (ours.circular, float(ref["circular"].iloc[0])),
        ):
            assert math.isclose(ours_val, ref_val, rel_tol=1e-6, abs_tol=0.0), (
                f"phi={phi}, n={n}: {ours_val} != {ref_val}"
            )


def test_optimal_block_length_structure():
    """Restituisce float, circolare = stationary * (2 / (4/3))^(1/3) sotto il tetto."""
    x = generate_ar1_series(0.5, 380, 1, np.random.default_rng(3))[0]
    result = optimal_block_length(x)
    assert isinstance(result, OptimalBlockLength)
    assert isinstance(result.stationary, float) and isinstance(result.circular, float)
    assert math.isclose(result.circular / result.stationary, 1.5 ** (1 / 3), rel_tol=1e-12)


def test_optimal_block_length_increases_with_dependence():
    """Su serie lunghe la lunghezza media cresce con phi."""
    rng = np.random.default_rng(5)
    means = []
    for phi in (0.0, 0.5, 0.8):
        series = generate_ar1_series(phi, 2000, 20, rng)
        means.append(np.mean([optimal_block_length(x).stationary for x in series]))
    assert means[0] < means[1] < means[2]


def test_optimal_block_length_validation():
    """Tipi e valori non validi."""
    with pytest.raises(TypeError, match="x must be an instance of np.ndarray"):
        optimal_block_length([1.0] * 50)  # type: ignore
    with pytest.raises(TypeError, match="x must have real numeric dtype"):
        optimal_block_length(np.ones(50, dtype=bool))
    with pytest.raises(ValueError, match="x must be 1D"):
        optimal_block_length(np.ones((5, 50)))
    with pytest.raises(ValueError, match="must be finite"):
        optimal_block_length(np.array([np.nan] + [1.0] * 49))
    with pytest.raises(ValueError, match="x must have more than"):
        optimal_block_length(np.arange(10, dtype=float))
    with pytest.raises(ValueError, match="x must not be constant"):
        optimal_block_length(np.ones(50))


# ---------------------------------------------------------------------------
# Arrotondamento
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "length, expected",
    [(0.0, 1), (0.2, 1), (1.49, 1), (1.5, 2), (2.5, 3), (7.4999, 7), (12.0, 12), (np.float64(19.6), 20), (3, 3)],
)
def test_round_block_length(length, expected):
    """Intero più vicino, metà per eccesso, almeno 1."""
    assert round_block_length(length) == expected
    assert isinstance(round_block_length(length), int)


def test_round_block_length_validation():
    """Tipi e valori non validi."""
    with pytest.raises(TypeError, match="length must be a real number"):
        round_block_length(True)  # type: ignore
    with pytest.raises(TypeError, match="length must be a real number"):
        round_block_length("3")  # type: ignore
    with pytest.raises(ValueError, match="length must be non-negative"):
        round_block_length(-0.5)
    with pytest.raises(ValueError, match="length must be finite"):
        round_block_length(float("inf"))


# ---------------------------------------------------------------------------
# Indici dello stationary bootstrap
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mean_length", [1, 2.5, 7, 40.0])
def test_stationary_indices_contract(mean_length):
    """Stesso contratto di moving_block_indices: int64 (n_boot, n), valori in [0, n)."""
    n, n_boot = 380, 199
    idx = stationary_bootstrap_indices(n, mean_length, n_boot, np.random.default_rng(1))
    ref = moving_block_indices(n, 7, n_boot, np.random.default_rng(1))
    assert idx.shape == ref.shape == (n_boot, n)
    assert idx.dtype == ref.dtype == np.int64
    assert idx.min() >= 0 and idx.max() < n


def test_stationary_indices_match_layout_and_wrap():
    """Gli indici avanzano di 1 modulo n dentro un blocco, con avvolgimento circolare."""
    n, n_boot = 50, 400
    idx, new_block, starts = _stationary_block_layout(n, 10.0, n_boot, np.random.default_rng(2))
    public = stationary_bootstrap_indices(n, 10.0, n_boot, np.random.default_rng(2))
    np.testing.assert_array_equal(idx, public)

    assert np.all(new_block[:, 0])
    np.testing.assert_array_equal(idx[new_block], starts[new_block])
    continuing = ~new_block[:, 1:]
    np.testing.assert_array_equal(idx[:, 1:][continuing], ((idx[:, :-1] + 1) % n)[continuing])
    # Almeno un avvolgimento da n - 1 a 0 dentro un blocco
    assert np.any((idx[:, :-1] == n - 1) & continuing)


def test_stationary_indices_iid_when_length_one():
    """Con lunghezza media 1 ogni posizione apre un blocco: bootstrap iid."""
    _, new_block, _ = _stationary_block_layout(100, 1.0, 50, np.random.default_rng(4))
    assert np.all(new_block)


@pytest.mark.parametrize("mean_length", [2.5, 10.0, 20.0])
def test_stationary_mean_block_length_within_three_se(mean_length):
    """Su almeno 100 000 blocchi la lunghezza media dista da L meno di 3 errori standard."""
    n = 20_000
    n_boot = int(math.ceil(MIN_BLOCKS * mean_length / n)) + 20
    _, new_block, _ = _stationary_block_layout(n, mean_length, n_boot, np.random.default_rng(7))

    lengths: list[np.ndarray] = []
    for row in new_block:
        block_starts = np.flatnonzero(row)
        # L'ultimo blocco è troncato alla fine del ricampionamento: si esclude
        lengths.append(np.diff(block_starts))
    all_lengths = np.concatenate(lengths)
    assert all_lengths.size >= MIN_BLOCKS

    p = 1.0 / mean_length
    se = math.sqrt(1.0 - p) / p / math.sqrt(all_lengths.size)
    assert abs(all_lengths.mean() - mean_length) < 3.0 * se


def test_stationary_block_starts_uniform():
    """La prima osservazione di ogni blocco è uniforme su [0, n): chi quadro con p > 0.01."""
    n = 50
    idx, new_block, _ = _stationary_block_layout(n, 5.0, 4000, np.random.default_rng(11))
    first_values = idx[new_block]
    assert first_values.size > 30_000
    counts = np.bincount(first_values, minlength=n)
    result = scipy.stats.chisquare(counts)
    assert result.pvalue > 0.01


def test_stationary_indices_validation():
    """Tipi e valori non validi."""
    rng = np.random.default_rng(0)
    with pytest.raises(TypeError, match="n must be an integer"):
        stationary_bootstrap_indices(10.0, 2, 5, rng)  # type: ignore
    with pytest.raises(TypeError, match="n_boot must be an integer"):
        stationary_bootstrap_indices(10, 2, True, rng)  # type: ignore
    with pytest.raises(TypeError, match="mean_block_length must be a real number"):
        stationary_bootstrap_indices(10, "2", 5, rng)  # type: ignore
    with pytest.raises(TypeError, match="rng must be an instance"):
        stationary_bootstrap_indices(10, 2, 5, 42)  # type: ignore
    with pytest.raises(ValueError, match="n must be at least 1"):
        stationary_bootstrap_indices(0, 1, 5, rng)
    with pytest.raises(ValueError, match="n_boot must be at least 1"):
        stationary_bootstrap_indices(10, 2, 0, rng)
    with pytest.raises(ValueError, match="mean_block_length must satisfy"):
        stationary_bootstrap_indices(10, 0.5, 5, rng)
    with pytest.raises(ValueError, match="mean_block_length must satisfy"):
        stationary_bootstrap_indices(10, 11, 5, rng)


# ---------------------------------------------------------------------------
# Intervallo della media
# ---------------------------------------------------------------------------


def test_stationary_mean_interval_order_statistics():
    """Gli estremi sono la 25-esima e la 975-esima media ricampionata per B = 999."""
    x = generate_ar1_series(0.3, 200, 1, np.random.default_rng(8))[0]
    lo, hi = stationary_bootstrap_mean_interval(x, 4, 999, 0.05, np.random.default_rng(9))
    idx = stationary_bootstrap_indices(200, 4, 999, np.random.default_rng(9))
    means = np.sort(x[idx].mean(axis=1))
    assert lo == means[24] and hi == means[974]
    assert lo < x.mean() < hi


def test_stationary_mean_interval_validation():
    """Tipi e valori non validi."""
    rng = np.random.default_rng(0)
    with pytest.raises(TypeError, match="x must be an instance of np.ndarray"):
        stationary_bootstrap_mean_interval([1.0, 2.0], 1, 9, 0.1, rng)  # type: ignore
    with pytest.raises(ValueError, match="x must be 1D"):
        stationary_bootstrap_mean_interval(np.ones((2, 3)), 1, 9, 0.1, rng)
    with pytest.raises(ValueError, match="alpha must be strictly between 0 and 1"):
        stationary_bootstrap_mean_interval(np.arange(10.0), 1, 9, 1.5, rng)


# ---------------------------------------------------------------------------
# arch solo nei test
# ---------------------------------------------------------------------------


def test_arch_only_imported_in_tests():
    """arch è nell'extra dev di pyproject.toml e nessun modulo di src/ o scripts/ lo importa."""
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    dev_block = pyproject.split("[project.optional-dependencies]")[1].split("[tool")[0]
    runtime_block = pyproject.split("dependencies = [")[1].split("]")[0]
    assert '"arch"' in dev_block
    assert '"arch"' not in runtime_block

    offenders: list[str] = []
    for target in ("src", "scripts"):
        for py_path in (REPO_ROOT / target).rglob("*.py"):
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=SyntaxWarning)
                tree = ast.parse(py_path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names: list[str] = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module]
                if any(name == "arch" or name.startswith("arch.") for name in names):
                    offenders.append(py_path.relative_to(REPO_ROOT).as_posix())
    assert offenders == []
