"""Test unitari e di conformità per il modulo ANOVA a una via."""

import numpy as np
import pytest
import scipy.stats

from shk.stats.anova import OneWayAnovaResult, oneway_anova, oneway_anova_vectorized


# ---------------------------------------------------------------------------
# Criterio 1: Toy dataset e valori teorici esatti
# ---------------------------------------------------------------------------


def test_oneway_anova_toy_dataset():
    """Verifica il calcolo dell'ANOVA sul toy dataset con tolleranza relativa 1e-12."""
    group_a = np.array([4.0, 7.0])
    group_b = np.array([2.0, 9.0, 3.0])

    res = oneway_anova([group_a, group_b])

    assert isinstance(res, OneWayAnovaResult)

    expected_ss_between = 5.0 / 6.0
    expected_ss_within = 199.0 / 6.0
    expected_ss_total = 34.0
    expected_df_between = 1
    expected_df_within = 3
    expected_f = 15.0 / 199.0
    expected_p = float(scipy.stats.f.sf(expected_f, expected_df_between, expected_df_within))

    assert abs(res.ss_between - expected_ss_between) / expected_ss_between < 1e-12
    assert abs(res.ss_within - expected_ss_within) / expected_ss_within < 1e-12
    assert abs(res.ss_total - expected_ss_total) / expected_ss_total < 1e-12
    assert res.df_between == expected_df_between
    assert res.df_within == expected_df_within
    assert abs(res.f_statistic - expected_f) / expected_f < 1e-12
    assert abs(res.p_value - expected_p) / expected_p < 1e-10


# ---------------------------------------------------------------------------
# Criterio 2: Confronto con scipy.stats.f_oneway
# ---------------------------------------------------------------------------


def test_oneway_anova_agreement_with_scipy():
    """Verifica concordanza di F (tolleranza 1e-12) e p-value (tolleranza 1e-10) con scipy."""
    # 1. Toy dataset
    toy_a = np.array([4.0, 7.0])
    toy_b = np.array([2.0, 9.0, 3.0])
    res_toy = oneway_anova([toy_a, toy_b])
    scipy_toy = scipy.stats.f_oneway(toy_a, toy_b)
    assert abs(res_toy.f_statistic - scipy_toy.statistic) / scipy_toy.statistic < 1e-12
    assert abs(res_toy.p_value - scipy_toy.pvalue) / scipy_toy.pvalue < 1e-10

    # 2. Dataset casuale 1: seed 20260928, k=3, sizes=[15, 25, 10]
    rng1 = np.random.default_rng(20260928)
    ds1 = [
        rng1.normal(loc=0.0, scale=1.0, size=15),
        rng1.normal(loc=1.5, scale=1.0, size=25),
        rng1.normal(loc=-0.5, scale=1.0, size=10),
    ]
    res1 = oneway_anova(ds1)
    scipy1 = scipy.stats.f_oneway(*ds1)
    assert abs(res1.f_statistic - scipy1.statistic) / scipy1.statistic < 1e-12
    assert abs(res1.p_value - scipy1.pvalue) / scipy1.pvalue < 1e-10

    # 3. Dataset casuale 2: seed 20260929, k=4, sizes=[8, 12, 20, 15]
    rng2 = np.random.default_rng(20260929)
    ds2 = [
        rng2.normal(loc=-1.0, scale=1.2, size=8),
        rng2.normal(loc=0.0, scale=1.2, size=12),
        rng2.normal(loc=0.5, scale=1.2, size=20),
        rng2.normal(loc=2.0, scale=1.2, size=15),
    ]
    res2 = oneway_anova(ds2)
    scipy2 = scipy.stats.f_oneway(*ds2)
    assert abs(res2.f_statistic - scipy2.statistic) / scipy2.statistic < 1e-12
    assert abs(res2.p_value - scipy2.pvalue) / scipy2.pvalue < 1e-10

    # 4. Dataset casuale 3: seed 20260930, k=5, sizes=[30, 10, 18, 22, 40]
    rng3 = np.random.default_rng(20260930)
    ds3 = [
        rng3.normal(loc=1.0, scale=0.8, size=30),
        rng3.normal(loc=2.0, scale=0.8, size=10),
        rng3.normal(loc=1.5, scale=0.8, size=18),
        rng3.normal(loc=0.5, scale=0.8, size=22),
        rng3.normal(loc=-1.0, scale=0.8, size=40),
    ]
    res3 = oneway_anova(ds3)
    scipy3 = scipy.stats.f_oneway(*ds3)
    assert abs(res3.f_statistic - scipy3.statistic) / scipy3.statistic < 1e-12
    assert abs(res3.p_value - scipy3.pvalue) / scipy3.pvalue < 1e-10


# ---------------------------------------------------------------------------
# Criterio 3: Partizione della devianza SS_total = SS_between + SS_within
# ---------------------------------------------------------------------------


def test_oneway_anova_ss_partitioning():
    """Verifica che SS_total = SS_between + SS_within entro 1e-12 su toy e dataset casuali."""
    rng1 = np.random.default_rng(20260928)
    ds1 = [
        rng1.normal(loc=0.0, scale=1.0, size=15),
        rng1.normal(loc=1.5, scale=1.0, size=25),
        rng1.normal(loc=-0.5, scale=1.0, size=10),
    ]

    rng2 = np.random.default_rng(20260929)
    ds2 = [
        rng2.normal(loc=-1.0, scale=1.2, size=8),
        rng2.normal(loc=0.0, scale=1.2, size=12),
        rng2.normal(loc=0.5, scale=1.2, size=20),
        rng2.normal(loc=2.0, scale=1.2, size=15),
    ]

    rng3 = np.random.default_rng(20260930)
    ds3 = [
        rng3.normal(loc=1.0, scale=0.8, size=30),
        rng3.normal(loc=2.0, scale=0.8, size=10),
        rng3.normal(loc=1.5, scale=0.8, size=18),
        rng3.normal(loc=0.5, scale=0.8, size=22),
        rng3.normal(loc=-1.0, scale=0.8, size=40),
    ]

    datasets = [
        [np.array([4.0, 7.0]), np.array([2.0, 9.0, 3.0])],
        ds1,
        ds2,
        ds3,
    ]

    for groups in datasets:
        res = oneway_anova(groups)
        all_obs = np.concatenate([np.asarray(g, dtype=np.float64) for g in groups])
        independent_ss_total = float(np.sum((all_obs - np.mean(all_obs)) ** 2))

        # Verifica concordanza del calcolo interno di ss_total
        assert abs(res.ss_total - independent_ss_total) / independent_ss_total < 1e-12

        # Verifica partizione esatta della devianza
        sum_between_within = res.ss_between + res.ss_within
        assert abs(res.ss_total - sum_between_within) / res.ss_total < 1e-12


# ---------------------------------------------------------------------------
# Criterio 4: Funzione vettorizzata (due casi con shape (3, 4, 380) e test 1D)
# ---------------------------------------------------------------------------


def test_oneway_anova_vectorized_multidimensional_case1():
    """Caso 1: values (3, 4, 380), contiguous_2 (2 blocchi da 190), tolleranza 1e-12."""
    rng = np.random.default_rng(20260931)
    values = rng.normal(loc=0.0, scale=1.0, size=(3, 4, 380))

    # Etichette contiguous_2: 0 per t < 190, 1 per t >= 190
    labels = np.zeros(380, dtype=np.int64)
    labels[190:] = 1

    f_vec = oneway_anova_vectorized(values, labels)

    assert isinstance(f_vec, np.ndarray)
    assert f_vec.shape == (3, 4)

    # Confronto serie per serie con oneway_anova
    for i in range(3):
        for j in range(4):
            series = values[i, j]
            g0 = series[labels == 0]
            g1 = series[labels == 1]
            res_single = oneway_anova([g0, g1])
            expected_f = res_single.f_statistic
            actual_f = f_vec[i, j]
            assert abs(actual_f - expected_f) / expected_f < 1e-12


def test_oneway_anova_vectorized_multidimensional_case2():
    """Caso 2: values (3, 4, 380), k=5 gruppi disuguali permutati, tolleranza 1e-12."""
    rng = np.random.default_rng(20260932)
    values = rng.normal(loc=0.0, scale=1.0, size=(3, 4, 380))

    # 5 gruppi di dimensioni diverse: 50, 70, 80, 80, 100 (totale 380)
    raw_labels = np.concatenate([
        np.full(50, 0, dtype=np.int64),
        np.full(70, 1, dtype=np.int64),
        np.full(80, 2, dtype=np.int64),
        np.full(80, 3, dtype=np.int64),
        np.full(100, 4, dtype=np.int64),
    ])
    perm_rng = np.random.default_rng(98765)
    labels = perm_rng.permutation(raw_labels)

    f_vec = oneway_anova_vectorized(values, labels)

    assert isinstance(f_vec, np.ndarray)
    assert f_vec.shape == (3, 4)

    for i in range(3):
        for j in range(4):
            series = values[i, j]
            groups = [series[labels == g_idx] for g_idx in range(5)]
            res_single = oneway_anova(groups)
            expected_f = res_single.f_statistic
            actual_f = f_vec[i, j]
            assert abs(actual_f - expected_f) / expected_f < 1e-12


def test_oneway_anova_vectorized_1d_input():
    """Verifica che con input 1D (380,) restituisca un float uguale a oneway_anova."""
    rng = np.random.default_rng(20260933)
    values_1d = rng.normal(loc=0.0, scale=1.0, size=380)
    labels = np.zeros(380, dtype=np.int64)
    labels[190:] = 1

    f_val = oneway_anova_vectorized(values_1d, labels)

    assert isinstance(f_val, float)
    res_single = oneway_anova([values_1d[labels == 0], values_1d[labels == 1]])
    assert abs(f_val - res_single.f_statistic) / res_single.f_statistic < 1e-12


# ---------------------------------------------------------------------------
# Test delle condizioni di validazione (oneway_anova)
# ---------------------------------------------------------------------------


def test_oneway_anova_validation_insufficient_groups():
    """Meno di 2 gruppi solleva ValueError."""
    with pytest.raises(ValueError, match="At least 2 groups must be provided"):
        oneway_anova([[1.0, 2.0, 3.0]])


def test_oneway_anova_validation_empty_group():
    """Gruppo vuoto solleva ValueError."""
    with pytest.raises(ValueError, match="each group must contain at least one observation"):
        oneway_anova([[1.0, 2.0], []])


def test_oneway_anova_validation_non_finite_values():
    """Valori non finiti (NaN o Inf) sollevano ValueError."""
    with pytest.raises(ValueError, match="contains non-finite values"):
        oneway_anova([[1.0, np.nan], [2.0, 3.0]])
    with pytest.raises(ValueError, match="contains non-finite values"):
        oneway_anova([[1.0, np.inf], [2.0, 3.0]])


def test_oneway_anova_validation_df_within_zero():
    """N <= k (df_within <= 0) solleva ValueError."""
    with pytest.raises(ValueError, match="strictly greater than number of groups"):
        oneway_anova([[1.0], [2.0]])


def test_oneway_anova_validation_group_not_1d():
    """Gruppo multidimensionale non 1D solleva ValueError (correzione 3a)."""
    with pytest.raises(ValueError, match="must be a 1D sequence"):
        oneway_anova([np.ones((2, 2)), np.array([1.0, 2.0])])


def test_oneway_anova_validation_invalid_types():
    """Tipi non conformi sollevano TypeError."""
    with pytest.raises(TypeError, match="must be a sequence of groups"):
        oneway_anova("not_a_sequence")  # type: ignore
    with pytest.raises(TypeError, match="must be a numerical sequence or 1D array"):
        oneway_anova([123, [1.0, 2.0]])  # type: ignore
    with pytest.raises(TypeError, match="must have real numeric dtype"):
        oneway_anova([["a", "b"], [1.0, 2.0]])


# ---------------------------------------------------------------------------
# Test delle condizioni di validazione (oneway_anova_vectorized)
# ---------------------------------------------------------------------------


def test_oneway_anova_vectorized_validation_values_not_ndarray():
    """values non np.ndarray solleva TypeError (correzione 3c)."""
    labels = np.array([0, 1, 0, 1], dtype=np.int64)
    with pytest.raises(TypeError, match="values must be an instance of np.ndarray"):
        oneway_anova_vectorized([[1.0, 2.0, 3.0, 4.0]], labels)  # type: ignore


def test_oneway_anova_vectorized_validation_values_not_real_numeric():
    """values con dtype non numerico reale solleva TypeError (correzione 3c)."""
    labels = np.array([0, 1, 0, 1], dtype=np.int64)
    values_str = np.array(["a", "b", "c", "d"])
    with pytest.raises(TypeError, match="values must have real numeric dtype"):
        oneway_anova_vectorized(values_str, labels)


def test_oneway_anova_vectorized_validation_labels_not_ndarray():
    """labels non np.ndarray solleva TypeError (correzione 3c)."""
    values = np.array([1.0, 2.0, 3.0, 4.0])
    with pytest.raises(TypeError, match="labels must be an instance of np.ndarray"):
        oneway_anova_vectorized(values, [0, 1, 0, 1])  # type: ignore


def test_oneway_anova_vectorized_validation_labels_dtype_not_integer():
    """labels con dtype float solleva TypeError."""
    values = np.array([1.0, 2.0, 3.0, 4.0])
    labels_float = np.array([0.0, 1.0, 0.0, 1.0])
    with pytest.raises(TypeError, match="labels must have integer dtype"):
        oneway_anova_vectorized(values, labels_float)


def test_oneway_anova_vectorized_validation_labels_negative():
    """labels con interi negativi solleva ValueError prima di bincount (correzione 3b)."""
    values = np.array([1.0, 2.0, 3.0, 4.0])
    labels_neg = np.array([-1, 0, 1, 0], dtype=np.int64)
    with pytest.raises(ValueError, match="cannot contain negative integers"):
        oneway_anova_vectorized(values, labels_neg)


def test_oneway_anova_vectorized_validation_labels_not_1d():
    """labels non 1D solleva ValueError."""
    values = np.array([[1.0, 2.0], [3.0, 4.0]])
    labels_2d = np.array([[0, 1], [0, 1]], dtype=np.int64)
    with pytest.raises(ValueError, match="labels must be a 1D array"):
        oneway_anova_vectorized(values, labels_2d)


def test_oneway_anova_vectorized_validation_length_mismatch():
    """Lunghezza labels diversa dall'ultimo asse di values solleva ValueError."""
    values = np.array([1.0, 2.0, 3.0, 4.0])
    labels_short = np.array([0, 1, 0], dtype=np.int64)
    with pytest.raises(ValueError, match="Length of labels .* must match"):
        oneway_anova_vectorized(values, labels_short)


def test_oneway_anova_vectorized_validation_missing_labels():
    """Valori di etichetta mancanti tra 0 e k-1 sollevano ValueError."""
    values = np.array([1.0, 2.0, 3.0, 4.0])
    labels_gap = np.array([0, 2, 0, 2], dtype=np.int64)  # Manca 1
    with pytest.raises(ValueError, match="All group labels from 0 to k-1 must be present"):
        oneway_anova_vectorized(values, labels_gap)


def test_oneway_anova_vectorized_validation_fewer_than_two_groups():
    """Meno di 2 gruppi distinti (k=1) solleva ValueError."""
    values = np.array([1.0, 2.0, 3.0, 4.0])
    labels_single = np.array([0, 0, 0, 0], dtype=np.int64)
    with pytest.raises(ValueError, match="At least 2 distinct group labels required"):
        oneway_anova_vectorized(values, labels_single)


def test_oneway_anova_vectorized_validation_df_within_zero():
    """N <= k solleva ValueError."""
    values = np.array([1.0, 2.0])
    labels = np.array([0, 1], dtype=np.int64)
    with pytest.raises(ValueError, match="strictly greater than number of groups"):
        oneway_anova_vectorized(values, labels)


def test_oneway_anova_vectorized_validation_non_finite_values():
    """values con valori non finiti solleva ValueError."""
    labels = np.array([0, 1, 0, 1], dtype=np.int64)
    values_nan = np.array([1.0, np.nan, 2.0, 3.0])
    with pytest.raises(ValueError, match="All elements of values must be finite"):
        oneway_anova_vectorized(values_nan, labels)
