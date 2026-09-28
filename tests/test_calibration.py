"""Test unitari e di conformità per la calibrazione con moving block bootstrap."""

import math
import numpy as np
import pytest

import shk.stats.calibration
from shk.stats.anova import oneway_anova_vectorized
from shk.stats.calibration import (
    calibrate_threshold,
    compute_order_statistic_index,
    moving_block_indices,
)


# ---------------------------------------------------------------------------
# Criterio 1: Proprietà strutturali degli indici del moving block bootstrap
# ---------------------------------------------------------------------------


def test_moving_block_indices_properties():
    """Verifica forma, intervallo [0, n), consecutività nei blocchi e inizio blocchi."""
    rng = np.random.default_rng(20260928)
    n = 100
    block_length = 7
    n_boot = 50

    indices = moving_block_indices(n=n, block_length=block_length, n_boot=n_boot, rng=rng)

    assert isinstance(indices, np.ndarray)
    assert indices.shape == (n_boot, n)
    assert indices.dtype == np.int64
    assert np.all((indices >= 0) & (indices < n))

    # Verifica consecutività entro ogni blocco (+1) e inizio dei blocchi in [0, n - L]
    k_blocks = math.ceil(n / block_length)
    for b in range(n_boot):
        row = indices[b]
        for k in range(k_blocks):
            start_pos = k * block_length
            end_pos = min((k + 1) * block_length, n)
            block = row[start_pos:end_pos]

            # Inizio del blocco originario in [0, n - block_length]
            block_start_val = block[0]
            assert 0 <= block_start_val <= n - block_length

            # Incremento consecutivo di 1 per gli elementi dello stesso blocco
            if len(block) > 1:
                assert np.all(np.diff(block) == 1)


# ---------------------------------------------------------------------------
# Criterio 2: Con L = n ogni ricampionamento coincide con la serie originale
# ---------------------------------------------------------------------------


def test_moving_block_indices_full_length_is_identity():
    """Verifica che con L = n ogni ricampionamento sia esattamente 0, 1, ..., n - 1."""
    rng = np.random.default_rng(42)
    n = 80
    n_boot = 30
    indices = moving_block_indices(n=n, block_length=n, n_boot=n_boot, rng=rng)

    expected_row = np.arange(n, dtype=np.int64)
    for b in range(n_boot):
        np.testing.assert_array_equal(indices[b], expected_row)


# ---------------------------------------------------------------------------
# Criterio 3: Integrità delle righe con dati 2D (forma (50, 3) e L = 7)
# ---------------------------------------------------------------------------


def test_calibrate_threshold_2d_row_integrity():
    """Verifica che con dati 2D ogni riga ricampionata coincida con una riga intera dell'originale."""
    rng_data = np.random.default_rng(12345)
    # data di forma (50, 3) con colonne diverse fra loro
    data = np.column_stack([
        rng_data.normal(loc=0.0, scale=1.0, size=50),
        rng_data.normal(loc=5.0, scale=2.0, size=50),
        rng_data.normal(loc=-3.0, scale=0.5, size=50),
    ])
    assert data.shape == (50, 3)

    n_obs = 50
    block_length = 7
    n_boot = 20
    alpha = 0.05
    seed = 99999

    recorded_arrays: list[np.ndarray] = []

    def recording_statistic(boot_array: np.ndarray) -> np.ndarray:
        recorded_arrays.append(boot_array)
        return np.zeros(boot_array.shape[0], dtype=np.float64)

    rng_test = np.random.default_rng(seed)
    _ = calibrate_threshold(
        data=data,
        statistic=recording_statistic,
        block_length=block_length,
        n_boot=n_boot,
        alpha=alpha,
        rng=rng_test,
        vectorized=True,
    )

    assert len(recorded_arrays) == 1
    boot_data = recorded_arrays[0]

    # Verifica forma (B, *data.shape) == (20, 50, 3)
    assert boot_data.shape == (n_boot, *data.shape)

    # Verifica coincidenza con data[moving_block_indices(...)] con stesso seed
    rng_ref = np.random.default_rng(seed)
    expected_indices = moving_block_indices(n_obs, block_length, n_boot, rng_ref)
    expected_boot_data = data[expected_indices]
    np.testing.assert_array_equal(boot_data, expected_boot_data)

    # Verifica che ogni riga ricampionata sia identica a una riga intera di data
    for b in range(n_boot):
        for t in range(n_obs):
            row_resampled = boot_data[b, t, :]
            orig_idx = expected_indices[b, t]
            np.testing.assert_array_equal(row_resampled, data[orig_idx, :])


# ---------------------------------------------------------------------------
# Criterio 4: Concordanza con la statistica d'ordine ricalcolata nel test
# ---------------------------------------------------------------------------


def test_calibrate_threshold_order_statistic_agreement():
    """Verifica che la soglia coincida con la statistica d'ordine ceil((1 - alpha)*(B + 1))."""
    rng_data = np.random.default_rng(42)
    data = rng_data.normal(size=120)
    block_length = 10
    n_boot = 99
    alpha = 0.05

    def dummy_stat(x: np.ndarray) -> float:
        return float(np.mean(x**2))

    rng1 = np.random.default_rng(20260928)
    threshold = calibrate_threshold(
        data=data,
        statistic=dummy_stat,
        block_length=block_length,
        n_boot=n_boot,
        alpha=alpha,
        rng=rng1,
        vectorized=False,
    )

    # Ricalcolo indipendente nel test con lo stesso seed
    rng2 = np.random.default_rng(20260928)
    indices = moving_block_indices(len(data), block_length, n_boot, rng2)
    stats = [dummy_stat(data[indices[b]]) for b in range(n_boot)]
    sorted_stats = np.sort(stats)

    k_order = compute_order_statistic_index(n_boot, alpha)
    expected_threshold = float(sorted_stats[k_order - 1])

    assert math.isclose(threshold, expected_threshold, rel_tol=1e-12)


# ---------------------------------------------------------------------------
# Criterio 5: Concordanza esatta tra modalità vectorized=True e vectorized=False
# ---------------------------------------------------------------------------


def test_calibrate_threshold_vectorized_vs_non_vectorized():
    """Verifica che a parità di seed la modalità vettorizzata e non diano la stessa soglia."""
    rng_data = np.random.default_rng(100)
    data = rng_data.normal(loc=1.0, scale=2.0, size=200)
    block_length = 15
    n_boot = 80
    alpha = 0.05
    seed = 777

    # Statistica che supporta sia 1D (un ricampionamento) sia 2D (B, n)
    def stat_dual(x: np.ndarray) -> float | np.ndarray:
        if x.ndim == 1:
            return float(np.var(x, ddof=1))
        return np.var(x, axis=1, ddof=1)

    rng_vec = np.random.default_rng(seed)
    th_vec = calibrate_threshold(
        data=data,
        statistic=stat_dual,
        block_length=block_length,
        n_boot=n_boot,
        alpha=alpha,
        rng=rng_vec,
        vectorized=True,
    )

    rng_loop = np.random.default_rng(seed)
    th_loop = calibrate_threshold(
        data=data,
        statistic=stat_dual,
        block_length=block_length,
        n_boot=n_boot,
        alpha=alpha,
        rng=rng_loop,
        vectorized=False,
    )

    assert isinstance(th_vec, float)
    assert isinstance(th_loop, float)
    assert math.isclose(th_vec, th_loop, rel_tol=1e-12)


# ---------------------------------------------------------------------------
# Criterio 6: Test con due statistiche distinte (ANOVA 1D e statistica 2D)
# ---------------------------------------------------------------------------


def test_calibrate_threshold_two_different_statistics():
    """Verifica il funzionamento con ANOVA vettorizzata (1D) e statistica multivariata (2D)."""
    # Statistica 1: ANOVA vettorizzata del Task 8 con etichette fisse su dati 1D
    rng_1d = np.random.default_rng(1)
    data_1d = rng_1d.normal(size=380)
    labels = np.array([0] * 190 + [1] * 190, dtype=np.int64)

    def anova_stat_vectorized(boot_batch: np.ndarray) -> np.ndarray:
        # boot_batch ha forma (B, 380)
        return oneway_anova_vectorized(boot_batch, labels)

    rng_boot1 = np.random.default_rng(20260928)
    th_anova = calibrate_threshold(
        data=data_1d,
        statistic=anova_stat_vectorized,
        block_length=20,
        n_boot=50,
        alpha=0.05,
        rng=rng_boot1,
        vectorized=True,
    )
    assert isinstance(th_anova, float)
    assert th_anova > 0.0

    # Statistica 2: Media della prima colonna divisa per l'errore standard ingenuo su dati 2D
    rng_2d = np.random.default_rng(2)
    data_2d = rng_2d.normal(size=(100, 4))

    def stat_2d_vectorized(boot_batch: np.ndarray) -> np.ndarray:
        # boot_batch ha forma (B, 100, 4)
        col0 = boot_batch[:, :, 0]  # forma (B, 100)
        means = np.mean(col0, axis=1)  # forma (B,)
        stds = np.std(col0, axis=1, ddof=1) / math.sqrt(col0.shape[1])
        return means / stds

    rng_boot2 = np.random.default_rng(20260928)
    th_2d = calibrate_threshold(
        data=data_2d,
        statistic=stat_2d_vectorized,
        block_length=10,
        n_boot=50,
        alpha=0.05,
        rng=rng_boot2,
        vectorized=True,
    )
    assert isinstance(th_2d, float)
    assert math.isfinite(th_2d)


# ---------------------------------------------------------------------------
# Criterio 7: Riproducibilità con stesso seed e dipendenza dal seed
# ---------------------------------------------------------------------------


def test_calibrate_threshold_reproducibility_and_seed_dependence():
    """Verifica che lo stesso seed dia la stessa soglia e seed diversi diano soglie diverse."""
    rng_data = np.random.default_rng(3)
    data = rng_data.normal(size=150)

    def simple_stat(x: np.ndarray) -> float:
        return float(np.mean(np.abs(x)))

    th1 = calibrate_threshold(
        data, simple_stat, 12, 60, 0.05, np.random.default_rng(12345)
    )
    th2 = calibrate_threshold(
        data, simple_stat, 12, 60, 0.05, np.random.default_rng(12345)
    )
    th3 = calibrate_threshold(
        data, simple_stat, 12, 60, 0.05, np.random.default_rng(54321)
    )

    assert th1 == th2
    assert th1 != th3


# ---------------------------------------------------------------------------
# Criterio 8: Robustezza al floating-point nel calcolo dell'indice d'ordine
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "b, alpha, expected_k",
    [
        (999, 0.05, 950),
        (99, 0.05, 95),
        (19, 0.05, 19),
        (99, 0.10, 90),
    ],
)
def test_order_statistic_index_robustness(b: int, alpha: float, expected_k: int):
    """Verifica che ceil((1 - alpha) * (b + 1)) sia calcolato esattamente sui casi critici."""
    k = compute_order_statistic_index(b, alpha)
    assert k == expected_k
    assert isinstance(k, int)


# ---------------------------------------------------------------------------
# Criterio 9: Contenuto documentale della docstring di modulo
# ---------------------------------------------------------------------------


def test_module_docstring_contents():
    """Verifica che la docstring contenga i quattro strumenti, il percorso del CSV e l'onere di H0."""
    doc = shk.stats.calibration.__doc__
    assert doc is not None

    # (a) I quattro strumenti menzionati
    assert "ANOVA F" in doc
    assert "FWER dello Z-test per giornata" in doc
    assert "Difference-in-Differences" in doc
    assert "Breusch-Pagan" in doc

    # (b) Dipendenza da L e menzione esplicita del percorso del CSV
    assert "results/us_c2_anova_autocorrelation.csv" in doc
    assert "method = block_bootstrap" in doc

    # (c) Imposizione di H0 a carico del chiamante
    assert "imporre l'ipotesi nulla H0" in doc or "imporre H0" in doc


# ---------------------------------------------------------------------------
# Condizioni di validazione ed eccezioni attese
# ---------------------------------------------------------------------------


def test_calibrate_threshold_validation_data_errors():
    """Verifica la validazione dell'array data (tipo, dtype reale, dimensione, valori finiti)."""
    rng = np.random.default_rng(42)
    stat = lambda x: float(np.mean(x))

    # data non np.ndarray -> TypeError
    with pytest.raises(TypeError, match="data must be an instance of np.ndarray"):
        calibrate_threshold([1.0, 2.0, 3.0], stat, 2, 10, 0.05, rng)  # type: ignore

    # data non numerico reale (es. stringhe o complessi) -> TypeError
    with pytest.raises(TypeError, match="data must have real numeric dtype"):
        calibrate_threshold(np.array(["a", "b"]), stat, 1, 10, 0.05, rng)

    with pytest.raises(TypeError, match="data must have real numeric dtype"):
        calibrate_threshold(np.array([1 + 2j, 2 + 3j]), stat, 1, 10, 0.05, rng)

    # data con 0 dimensioni -> ValueError
    with pytest.raises(ValueError, match="data must have at least 1 dimension"):
        calibrate_threshold(np.array(5.0), stat, 1, 10, 0.05, rng)

    # data con valori non finiti -> ValueError
    with pytest.raises(ValueError, match="All elements of data must be finite"):
        calibrate_threshold(np.array([1.0, np.nan, 3.0]), stat, 2, 10, 0.05, rng)

    with pytest.raises(ValueError, match="All elements of data must be finite"):
        calibrate_threshold(np.array([1.0, np.inf, 3.0]), stat, 2, 10, 0.05, rng)


def test_calibrate_threshold_validation_parameter_types_and_bounds():
    """Verifica le eccezioni su block_length, n_boot, alpha, statistic, rng e vectorized."""
    rng = np.random.default_rng(42)
    data = np.ones(50)
    stat = lambda x: float(np.mean(x))

    # block_length bool o float -> TypeError
    with pytest.raises(TypeError, match="block_length must be an integer"):
        calibrate_threshold(data, stat, True, 10, 0.05, rng)  # type: ignore
    with pytest.raises(TypeError, match="block_length must be an integer"):
        calibrate_threshold(data, stat, 5.5, 10, 0.05, rng)  # type: ignore

    # block_length < 1 o > n -> ValueError
    with pytest.raises(ValueError, match="block_length must satisfy 1 <= block_length <= n"):
        calibrate_threshold(data, stat, 0, 10, 0.05, rng)
    with pytest.raises(ValueError, match="block_length must satisfy 1 <= block_length <= n"):
        calibrate_threshold(data, stat, 51, 10, 0.05, rng)

    # n_boot bool o float -> TypeError
    with pytest.raises(TypeError, match="n_boot must be an integer"):
        calibrate_threshold(data, stat, 5, True, 0.05, rng)  # type: ignore
    with pytest.raises(TypeError, match="n_boot must be an integer"):
        calibrate_threshold(data, stat, 5, 10.5, 0.05, rng)  # type: ignore

    # n_boot < 1 -> ValueError
    with pytest.raises(ValueError, match="n_boot must be at least 1"):
        calibrate_threshold(data, stat, 5, 0, 0.05, rng)

    # alpha bool o non float -> TypeError
    with pytest.raises(TypeError, match="alpha must be a float"):
        calibrate_threshold(data, stat, 5, 10, True, rng)  # type: ignore
    with pytest.raises(TypeError, match="alpha must be a float"):
        calibrate_threshold(data, stat, 5, 10, 1, rng)  # type: ignore

    # alpha fuori da (0, 1) -> ValueError
    with pytest.raises(ValueError, match="alpha must be strictly between 0 and 1"):
        calibrate_threshold(data, stat, 5, 10, 0.0, rng)
    with pytest.raises(ValueError, match="alpha must be strictly between 0 and 1"):
        calibrate_threshold(data, stat, 5, 10, 1.0, rng)

    # statistic non callable -> TypeError
    with pytest.raises(TypeError, match="statistic must be callable"):
        calibrate_threshold(data, "not_callable", 5, 10, 0.05, rng)  # type: ignore

    # rng non np.random.Generator -> TypeError
    with pytest.raises(TypeError, match="rng must be an instance of np.random.Generator"):
        calibrate_threshold(data, stat, 5, 10, 0.05, "not_an_rng")  # type: ignore

    # vectorized non bool -> TypeError
    with pytest.raises(TypeError, match="vectorized must be a bool"):
        calibrate_threshold(data, stat, 5, 10, 0.05, rng, vectorized="yes")  # type: ignore


def test_calibrate_threshold_validation_order_statistic_exceeds_b():
    """Verifica che venga sollevato ValueError quando k > B, nominando B e alpha."""
    rng = np.random.default_rng(42)
    data = np.ones(30)
    stat = lambda x: float(np.mean(x))

    # Con B = 5 e alpha = 0.01: (1 - 0.01) * 6 = 5.94 -> k = 6 > 5
    with pytest.raises(ValueError, match=r"exceeds number of bootstrap resamples B \(5\) for alpha=0\.01"):
        calibrate_threshold(data, stat, 5, n_boot=5, alpha=0.01, rng=rng)

    with pytest.raises(ValueError, match=r"exceeds number of bootstrap resamples B \(5\) for alpha=0\.01"):
        compute_order_statistic_index(b=5, alpha=0.01)


def test_calibrate_threshold_validation_statistic_output_errors():
    """Verifica che output di forma errata o non finiti della statistica sollevino ValueError."""
    rng = np.random.default_rng(42)
    data = np.ones(40)

    # 1. vectorized=True: output con forma errata diversa da (n_boot,) -> ValueError
    def bad_shape_vectorized(x: np.ndarray) -> np.ndarray:
        return np.zeros((x.shape[0], 2))  # forma (B, 2) invece di (B,)

    with pytest.raises(ValueError, match="statistic output must have 1D shape"):
        calibrate_threshold(data, bad_shape_vectorized, 5, 20, 0.05, rng, vectorized=True)

    # 2. vectorized=False: statistica che restituisce un array di 2 elementi invece di uno scalare -> ValueError
    def return_array_non_vectorized(x: np.ndarray) -> np.ndarray:
        return np.array([1.0, 2.0])

    with pytest.raises(ValueError, match="statistic output must have 1D shape"):
        calibrate_threshold(data, return_array_non_vectorized, 5, 20, 0.05, rng, vectorized=False)

    # 3. Output contenente valori non finiti -> ValueError
    def non_finite_stat(x: np.ndarray) -> float:
        return float(np.nan)

    with pytest.raises(ValueError, match="contains non-finite values"):
        calibrate_threshold(data, non_finite_stat, 5, 20, 0.05, rng, vectorized=False)


def test_calibrate_threshold_numpy_integer_types_accepted():
    """Verifica che block_length e n_boot di tipo np.integer siano accettati."""
    rng = np.random.default_rng(42)
    data = np.ones(50)
    stat = lambda x: float(np.mean(x))

    th = calibrate_threshold(
        data=data,
        statistic=stat,
        block_length=np.int64(10),
        n_boot=np.int32(20),
        alpha=0.05,
        rng=rng,
        vectorized=False,
    )
    assert isinstance(th, float)


def test_moving_block_indices_validation():
    """Verifica i controlli di tipo e di validità su moving_block_indices."""
    rng = np.random.default_rng(42)

    with pytest.raises(TypeError, match="n must be an integer"):
        moving_block_indices("10", 2, 5, rng)  # type: ignore
    with pytest.raises(TypeError, match="n must be an integer"):
        moving_block_indices(True, 2, 5, rng)  # type: ignore
    with pytest.raises(ValueError, match="n must be at least 1"):
        moving_block_indices(0, 2, 5, rng)

    with pytest.raises(TypeError, match="block_length must be an integer"):
        moving_block_indices(10, 2.5, 5, rng)  # type: ignore
    with pytest.raises(ValueError, match="block_length must satisfy 1 <= block_length <= n"):
        moving_block_indices(10, 0, 5, rng)
    with pytest.raises(ValueError, match="block_length must satisfy 1 <= block_length <= n"):
        moving_block_indices(10, 11, 5, rng)

    with pytest.raises(TypeError, match="n_boot must be an integer"):
        moving_block_indices(10, 2, False, rng)  # type: ignore
    with pytest.raises(ValueError, match="n_boot must be strictly positive"):
        moving_block_indices(10, 2, 0, rng)

    with pytest.raises(TypeError, match="rng must be an instance of np.random.Generator"):
        moving_block_indices(10, 2, 5, "invalid")  # type: ignore
