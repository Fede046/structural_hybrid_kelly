"""Test di accettazione per l'esperimento US-C2.2 (falso rigetto dell'ANOVA su serie AR(1))."""

import os
import csv
import math
import numpy as np
import pytest

import shk.stats.false_rejection
from shk.stats.anova import oneway_anova_vectorized
from shk.stats.calibration import calibrate_threshold
from shk.stats.timeseries import generate_ar1_series
from shk.stats.false_rejection import (
    ALPHA,
    BLOCK_LENGTHS,
    CSV_COLUMNS,
    DESIGNS,
    DESIGN_CONTIGUOUS_2,
    DESIGN_CONTIGUOUS_38,
    DESIGN_RANDOM_2,
    METHOD_BLOCK_BOOTSTRAP,
    METHOD_BLOCK_BOOTSTRAP_CENTERED,
    N_OBS,
    N_SERIES,
    PHI_VALUES,
    SEED_C2,
    SEED_S7,
    RejectionResult,
    calibrate_centered_threshold,
    center_by_group,
    compute_calibrated_rejection_rates,
    compute_centered_calibrated_rejection_rates,
    compute_centered_calibration_details,
    compute_nominal_rejection_rates,
    critical_value_nominal,
    make_design_labels,
    monte_carlo_interval_99,
    spawn_t40_bootstrap_generators,
)

N_CSV_ROWS: int = 36

FLOAT_CSV_COLUMNS: tuple[str, ...] = (
    "phi",
    "rejection_rate",
    "critical_value_mean",
    "mc_lower_99",
    "mc_upper_99",
)


# ---------------------------------------------------------------------------
# Criterio 1: contiguous_2, phi = 0.0 dentro l'intervallo Monte Carlo al 99%
# ---------------------------------------------------------------------------


def test_acceptance_contiguous_2_phi_zero_within_mc_interval():
    """Verifica che con phi = 0.0 il tasso di falso rigetto stia nell'intervallo MC al 99%."""
    results = compute_nominal_rejection_rates(seed=SEED_C2)
    cont2_phi0 = [
        r
        for r in results
        if r.design == DESIGN_CONTIGUOUS_2 and abs(r.phi - 0.0) < 1e-9
    ][0]

    assert cont2_phi0.mc_lower_99 <= cont2_phi0.rejection_rate <= cont2_phi0.mc_upper_99


# ---------------------------------------------------------------------------
# Criterio 2: contiguous_2, phi in {0.3, 0.5, 0.7} strettamente sopra l'intervallo
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("phi_val", [0.3, 0.5, 0.7])
def test_acceptance_contiguous_2_autocorrelation_inflates_rejection(phi_val: float):
    """Verifica che l'autocorrelazione positiva gonfi il tasso di falso rigetto sopra il 99% MC."""
    results = compute_nominal_rejection_rates(seed=SEED_C2)
    record = [
        r
        for r in results
        if r.design == DESIGN_CONTIGUOUS_2 and abs(r.phi - phi_val) < 1e-9
    ][0]

    assert record.rejection_rate > record.mc_upper_99


# ---------------------------------------------------------------------------
# Criterio 3: contiguous_2, tasso strettamente crescente lungo phi
# ---------------------------------------------------------------------------


def test_acceptance_contiguous_2_rejection_strictly_increasing():
    """Verifica che il tasso di falso rigetto per contiguous_2 sia strettamente crescente in phi."""
    results = compute_nominal_rejection_rates(seed=SEED_C2)
    cont2_records = [r for r in results if r.design == DESIGN_CONTIGUOUS_2]
    # Ordinati per phi crescente
    cont2_records.sort(key=lambda r: r.phi)

    rates = [r.rejection_rate for r in cont2_records]
    assert len(rates) == 4
    for i in range(len(rates) - 1):
        assert rates[i] < rates[i + 1]


# ---------------------------------------------------------------------------
# Criterio 4: Conteggio matrici e stesse serie per tutti i disegni
# ---------------------------------------------------------------------------


def test_acceptance_matrix_generation_count(monkeypatch):
    """Verifica che generate_ar1_series sia chiamata esattamente una volta per ciascun phi."""
    calls: list[tuple[float, int, int]] = []
    original_generate = shk.stats.false_rejection.generate_ar1_series

    def recording_wrapper(phi: float, n: int, m: int, rng: np.random.Generator):
        calls.append((phi, n, m))
        return original_generate(phi, n, m, rng)

    monkeypatch.setattr(
        shk.stats.false_rejection, "generate_ar1_series", recording_wrapper
    )

    _ = compute_nominal_rejection_rates(seed=SEED_C2)

    assert len(calls) == len(PHI_VALUES)
    for (phi, n, m), expected_phi in zip(calls, PHI_VALUES):
        assert abs(phi - expected_phi) < 1e-9
        assert n == N_OBS
        assert m == N_SERIES


def test_acceptance_same_series_across_designs():
    """Verifica che tutti i disegni usino la stessa matrice derivata direttamente da SeedSequence."""
    results = compute_nominal_rejection_rates(seed=SEED_C2)
    results_dict = {(r.design, r.phi): r for r in results}

    labels_cont2 = make_design_labels(DESIGN_CONTIGUOUS_2, N_OBS)
    labels_cont38 = make_design_labels(DESIGN_CONTIGUOUS_38, N_OBS)
    cv_k2 = critical_value_nominal(k=2, n_obs=N_OBS, alpha=ALPHA)
    cv_k38 = critical_value_nominal(k=38, n_obs=N_OBS, alpha=ALPHA)

    # Ricostruzione indipendente direttamente dalla SeedSequence
    ss = np.random.SeedSequence(SEED_C2)
    phi_seeds = ss.spawn(len(PHI_VALUES))

    for i, phi in enumerate(PHI_VALUES):
        stream_seeds = phi_seeds[i].spawn(3)
        ref_rng_series = np.random.default_rng(stream_seeds[0])
        ref_rng_perm = np.random.default_rng(stream_seeds[1])

        ref_series = generate_ar1_series(phi, N_OBS, N_SERIES, ref_rng_series)

        # 1. contiguous_2
        f_cont2 = oneway_anova_vectorized(ref_series, labels_cont2)
        ref_rejections_cont2 = int(np.sum(f_cont2 > cv_k2))
        assert (
            results_dict[(DESIGN_CONTIGUOUS_2, phi)].rejections
            == ref_rejections_cont2
        )

        # 2. contiguous_38
        f_cont38 = oneway_anova_vectorized(ref_series, labels_cont38)
        ref_rejections_cont38 = int(np.sum(f_cont38 > cv_k38))
        assert (
            results_dict[(DESIGN_CONTIGUOUS_38, phi)].rejections
            == ref_rejections_cont38
        )

        # 3. random_2
        perm_matrix = np.empty((N_SERIES, N_OBS), dtype=np.int64)
        for s_idx in range(N_SERIES):
            perm_matrix[s_idx] = ref_rng_perm.permutation(N_OBS)
        ref_series_perm = np.take_along_axis(ref_series, perm_matrix, axis=1)

        f_rand2 = oneway_anova_vectorized(ref_series_perm, labels_cont2)
        ref_rejections_rand2 = int(np.sum(f_rand2 > cv_k2))
        assert (
            results_dict[(DESIGN_RANDOM_2, phi)].rejections == ref_rejections_rand2
        )


# ---------------------------------------------------------------------------
# Criterio 5: Struttura del CSV e coincidenza campo per campo
# ---------------------------------------------------------------------------


def test_acceptance_csv_structure_and_values():
    """Verifica che il CSV abbia 36 righe e che la struttura e i valori nominali coincidano."""
    csv_path = os.path.join("results", "us_c2_anova_autocorrelation.csv")
    assert os.path.isfile(csv_path), f"CSV file not found at {csv_path}"

    expected_nominal = compute_nominal_rejection_rates(seed=SEED_C2)

    with open(csv_path, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert tuple(header) == CSV_COLUMNS

        rows = list(reader)
        assert len(rows) == N_CSV_ROWS

    # 1. Verifica campo per campo delle prime 12 righe (nominali)
    for row_idx, (csv_row, exp_res) in enumerate(zip(rows[:12], expected_nominal)):
        exp_dict = exp_res.to_row()
        assert len(csv_row) == len(CSV_COLUMNS)
        for col_idx, col_name in enumerate(CSV_COLUMNS):
            expected_val_str = str(exp_dict[col_name])
            actual_val_str = csv_row[col_idx]
            if col_name in FLOAT_CSV_COLUMNS:
                assert math.isclose(
                    float(actual_val_str),
                    float(expected_val_str),
                    rel_tol=1e-12,
                    abs_tol=0.0,
                ), (
                    f"Mismatch at nominal row {row_idx}, column '{col_name}': "
                    f"expected '{expected_val_str}', got '{actual_val_str}'"
                )
            else:
                assert actual_val_str == expected_val_str, (
                    f"Mismatch at nominal row {row_idx}, column '{col_name}': "
                    f"expected '{expected_val_str}', got '{actual_val_str}'"
                )

    # 2. Verifica rapida della struttura e sequenza delle righe 12..23 (calibrate)
    expected_pairs = [
        (str(l_val), phi) for l_val in BLOCK_LENGTHS for phi in PHI_VALUES
    ]
    ref_nominal_dict = expected_nominal[0].to_row()
    exp_mc_lower = str(ref_nominal_dict["mc_lower_99"])
    exp_mc_upper = str(ref_nominal_dict["mc_upper_99"])
    exp_n_series = str(N_SERIES)

    # 3. Stessa verifica per le righe 24..35 (calibrate sulla serie centrata, T40)
    calibrated_rows = rows[12:24]
    centered_rows = rows[24:36]
    assert len(calibrated_rows) == len(expected_pairs)
    assert len(centered_rows) == len(expected_pairs)

    checks = [
        (csv_row, METHOD_BLOCK_BOOTSTRAP, pair)
        for csv_row, pair in zip(calibrated_rows, expected_pairs)
    ] + [
        (csv_row, METHOD_BLOCK_BOOTSTRAP_CENTERED, pair)
        for csv_row, pair in zip(centered_rows, expected_pairs)
    ]
    for csv_row, exp_method, (exp_l_str, exp_phi) in checks:
        assert len(csv_row) == len(CSV_COLUMNS)
        row_dict = dict(zip(CSV_COLUMNS, csv_row))

        assert row_dict["design"] == DESIGN_CONTIGUOUS_2
        assert abs(float(row_dict["phi"]) - exp_phi) < 1e-9
        assert row_dict["method"] == exp_method
        assert row_dict["block_length"] == exp_l_str
        assert row_dict["n_series"] == exp_n_series
        assert row_dict["mc_lower_99"] == exp_mc_lower
        assert row_dict["mc_upper_99"] == exp_mc_upper

        # Coerenza interna di rejections e rejection_rate
        rejections = int(row_dict["rejections"])
        assert 0 <= rejections <= N_SERIES
        rate = float(row_dict["rejection_rate"])
        assert abs(rate - (rejections / N_SERIES)) < 1e-9
        cv_mean = float(row_dict["critical_value_mean"])
        assert cv_mean > 0.0


# ---------------------------------------------------------------------------
# Criterio 6: Esistenza e dimensione della figura PNG
# ---------------------------------------------------------------------------


def test_acceptance_figure_exists():
    """Verifica che la figura generata esista e abbia dimensione non nulla."""
    fig_path = os.path.join("thesis", "figures", "us_c2_anova_autocorrelation.png")
    assert os.path.isfile(fig_path), f"Figure not found at {fig_path}"
    assert os.path.getsize(fig_path) > 0, "Figure file is empty"


# ---------------------------------------------------------------------------
# Validazione della funzione make_design_labels
# ---------------------------------------------------------------------------


def test_make_design_labels_validation():
    """Verifica la corretta validazione dei parametri in make_design_labels."""
    with pytest.raises(ValueError, match="Unknown design 'invalid_design'"):
        make_design_labels("invalid_design")

    with pytest.raises(TypeError, match="design must be a string"):
        make_design_labels(123)  # type: ignore

    with pytest.raises(TypeError, match="n_obs must be an integer"):
        make_design_labels(DESIGN_CONTIGUOUS_2, n_obs=10.5)  # type: ignore

    with pytest.raises(ValueError, match="n_obs must be at least 2"):
        make_design_labels(DESIGN_CONTIGUOUS_2, n_obs=1)


# ---------------------------------------------------------------------------
# Validazione della funzione compute_calibrated_rejection_rates
# ---------------------------------------------------------------------------


def test_compute_calibrated_rejection_rates_validation():
    """Verifica la validazione dell'argomento seed in compute_calibrated_rejection_rates."""
    with pytest.raises(TypeError, match="seed must be an integer"):
        compute_calibrated_rejection_rates(seed=True)  # type: ignore

    with pytest.raises(TypeError, match="seed must be an integer"):
        compute_calibrated_rejection_rates(seed="invalid")  # type: ignore

    with pytest.raises(TypeError, match="seed must be an integer"):
        compute_calibrated_rejection_rates(seed=2.5)  # type: ignore


# ---------------------------------------------------------------------------
# T40: centramento per gruppo e soglia calibrata con H0 imposta
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("design", [DESIGN_CONTIGUOUS_2, DESIGN_CONTIGUOUS_38])
@pytest.mark.parametrize("phi", [0.0, 0.7])
def test_center_by_group_zero_group_means(design: str, phi: float):
    """Dopo il centramento la media di ciascun gruppo è nulla entro 1e-12 (criterio T40)."""
    rng = np.random.default_rng(20261011)
    series = generate_ar1_series(phi, N_OBS, 50, rng) + 3.0
    labels = make_design_labels(design, N_OBS)

    centered = center_by_group(series, labels)
    assert centered.shape == series.shape
    assert centered.dtype == np.float64
    for g in np.unique(labels):
        group_means = centered[:, labels == g].mean(axis=1)
        assert np.max(np.abs(group_means)) <= 1e-12

    # Versione 1D coerente con la versione 2D (l'ordine delle somme può cambiare l'ultima cifra)
    centered_1d = center_by_group(series[7], labels)
    np.testing.assert_allclose(centered_1d, centered[7], rtol=0.0, atol=1e-13)


def test_center_by_group_preserves_within_group_deviations():
    """Il centramento sottrae una costante per gruppo: le differenze interne restano uguali."""
    rng = np.random.default_rng(1)
    series = rng.normal(size=N_OBS)
    labels = make_design_labels(DESIGN_CONTIGUOUS_2, N_OBS)
    centered = center_by_group(series, labels)

    for g in (0, 1):
        mask = labels == g
        np.testing.assert_allclose(
            centered[mask] - centered[mask][0],
            series[mask] - series[mask][0],
            rtol=0.0,
            atol=1e-12,
        )
    # La F della serie centrata è nulla
    assert abs(oneway_anova_vectorized(centered, labels)) < 1e-20


def test_center_by_group_validation():
    """Verifica tipi e valori non validi di center_by_group."""
    labels = make_design_labels(DESIGN_CONTIGUOUS_2, 10)
    with pytest.raises(TypeError, match="series must be an instance of np.ndarray"):
        center_by_group([1.0] * 10, labels)  # type: ignore
    with pytest.raises(TypeError, match="series must have real numeric dtype"):
        center_by_group(np.ones(10, dtype=bool), labels)
    with pytest.raises(TypeError, match="labels must be an instance of np.ndarray"):
        center_by_group(np.ones(10), [0] * 10)  # type: ignore
    with pytest.raises(TypeError, match="labels must have integer dtype"):
        center_by_group(np.ones(10), labels.astype(np.float64))
    with pytest.raises(ValueError, match="at least 1 dimension"):
        center_by_group(np.array(1.0), labels)
    with pytest.raises(ValueError, match="must be finite"):
        center_by_group(np.array([np.nan] + [1.0] * 9), labels)
    with pytest.raises(ValueError, match="labels must be 1D with length 10"):
        center_by_group(np.ones(10), labels[:9])
    with pytest.raises(ValueError, match="labels must be non-negative"):
        center_by_group(np.ones(10), labels - 1)
    with pytest.raises(ValueError, match="Every group label"):
        center_by_group(np.ones(10), labels * 2)


def test_calibrate_centered_threshold_equals_threshold_on_centered_series():
    """La soglia centrata coincide con calibrate_threshold sulla serie centrata a parità di rng."""
    rng_series = np.random.default_rng(7)
    series = generate_ar1_series(0.5, N_OBS, 1, rng_series)[0] + 1.5
    labels = make_design_labels(DESIGN_CONTIGUOUS_2, N_OBS)

    threshold = calibrate_centered_threshold(
        series, labels, block_length=20, n_boot=199, alpha=ALPHA,
        rng=np.random.default_rng(11),
    )
    expected = calibrate_threshold(
        data=center_by_group(series, labels),
        statistic=lambda b: oneway_anova_vectorized(b, labels),
        block_length=20,
        n_boot=199,
        alpha=ALPHA,
        rng=np.random.default_rng(11),
        vectorized=True,
    )
    assert threshold == expected

    # Con una differenza fra le metà enorme la soglia centrata non cambia: dipende solo
    # dagli scarti interni ai gruppi
    shifted = series + 100.0 * labels
    threshold_shifted = calibrate_centered_threshold(
        shifted, labels, block_length=20, n_boot=199, alpha=ALPHA,
        rng=np.random.default_rng(11),
    )
    assert math.isclose(threshold_shifted, threshold, rel_tol=1e-9)


def test_calibrate_centered_threshold_requires_1d_series():
    """Una matrice di serie dà ValueError: la soglia si calibra una serie alla volta."""
    labels = make_design_labels(DESIGN_CONTIGUOUS_2, N_OBS)
    with pytest.raises(ValueError, match="series must be 1D"):
        calibrate_centered_threshold(
            np.ones((2, N_OBS)), labels, 7, 99, ALPHA, np.random.default_rng(0)
        )


def test_spawn_t40_bootstrap_generators_scheme():
    """I generatori del metodo centrato derivano da SeedSequence(SEED_S7).spawn(5)[0]."""
    rngs = spawn_t40_bootstrap_generators(seed=SEED_S7)
    assert len(rngs) == len(PHI_VALUES)
    task_seed = np.random.SeedSequence(SEED_S7).spawn(5)[0]
    for i, phi_ss in enumerate(task_seed.spawn(len(PHI_VALUES))):
        assert len(rngs[i]) == len(BLOCK_LENGTHS)
        for j, l_ss in enumerate(phi_ss.spawn(len(BLOCK_LENGTHS))):
            expected = np.random.default_rng(l_ss).integers(0, 2**62, size=4)
            assert np.array_equal(rngs[i][j].integers(0, 2**62, size=4), expected)

    with pytest.raises(TypeError, match="seed must be an integer"):
        spawn_t40_bootstrap_generators(seed=True)  # type: ignore


def test_centered_functions_seed_validation():
    """I seed non interi danno TypeError prima di qualunque calcolo."""
    with pytest.raises(TypeError, match="seed must be an integer"):
        compute_centered_calibrated_rejection_rates(seed=1.5)  # type: ignore
    with pytest.raises(TypeError, match="bootstrap_seed must be an integer"):
        compute_centered_calibrated_rejection_rates(bootstrap_seed="x")  # type: ignore
    with pytest.raises(TypeError, match="bootstrap_seed must be an integer"):
        compute_centered_calibration_details(bootstrap_seed=False)  # type: ignore


# ---------------------------------------------------------------------------
# Fixture e test di accettazione per US-C2.3 (marcati slow)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def calibrated_simulation_results() -> list[RejectionResult]:
    """Esegue una sola volta la simulazione calibrata per i test slow del modulo."""
    return compute_calibrated_rejection_rates(seed=SEED_C2)


@pytest.mark.slow
def test_acceptance_csv_calibrated_values(
    calibrated_simulation_results: list[RejectionResult],
):
    """Verifica che le 12 righe calibrate del CSV coincidano campo per campo con la simulazione."""
    csv_path = os.path.join("results", "us_c2_anova_autocorrelation.csv")
    with open(csv_path, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        _ = next(reader)
        rows = list(reader)

    calibrated_rows = rows[12:24]
    assert len(calibrated_rows) == len(calibrated_simulation_results)

    for row_idx, (csv_row, exp_res) in enumerate(
        zip(calibrated_rows, calibrated_simulation_results)
    ):
        exp_dict = exp_res.to_row()
        assert len(csv_row) == len(CSV_COLUMNS)
        for col_idx, col_name in enumerate(CSV_COLUMNS):
            expected_val_str = str(exp_dict[col_name])
            actual_val_str = csv_row[col_idx]
            if col_name in FLOAT_CSV_COLUMNS:
                assert math.isclose(
                    float(actual_val_str),
                    float(expected_val_str),
                    rel_tol=1e-12,
                    abs_tol=0.0,
                ), (
                    f"Mismatch at calibrated row {row_idx} (CSV row {row_idx + 12}), "
                    f"column '{col_name}': expected '{expected_val_str}', got '{actual_val_str}'"
                )
            else:
                assert actual_val_str == expected_val_str, (
                    f"Mismatch at calibrated row {row_idx} (CSV row {row_idx + 12}), "
                    f"column '{col_name}': expected '{expected_val_str}', got '{actual_val_str}'"
                )


@pytest.mark.slow
@pytest.mark.xfail(
    strict=True,
    reason=(
        "Known result of T12: the threshold calibrated on the raw series, without imposing "
        "H0, gives 29 (L = 20) and 32 (L = 40) rejections out of 1000 at phi = 0, below "
        "the 99% MC interval; the centered method of T40 is the remedy"
    ),
)
def test_acceptance_calibrated_phi_zero_within_mc_interval(
    calibrated_simulation_results: list[RejectionResult],
):
    """Verifica che per contiguous_2 e phi = 0.0 ogni L abbia tasso nell'intervallo MC al 99%."""
    phi0_results = [
        r for r in calibrated_simulation_results if abs(r.phi - 0.0) < 1e-9
    ]
    assert len(phi0_results) == len(BLOCK_LENGTHS)
    for r in phi0_results:
        assert r.mc_lower_99 <= r.rejection_rate <= r.mc_upper_99, (
            f"Rate {r.rejection_rate} for L={r.block_length} outside 99% MC interval "
            f"[{r.mc_lower_99}, {r.mc_upper_99}]"
        )


@pytest.mark.slow
@pytest.mark.parametrize("phi_val", [0.3, 0.5, 0.7])
def test_acceptance_calibrated_strictly_below_nominal(
    calibrated_simulation_results: list[RejectionResult],
    phi_val: float,
):
    """Verifica che per phi in {0.3, 0.5, 0.7} il tasso calibrato sia strettamente minore del nominale."""
    nominal_results = compute_nominal_rejection_rates(seed=SEED_C2)
    nom_cont2 = [
        r
        for r in nominal_results
        if r.design == DESIGN_CONTIGUOUS_2 and abs(r.phi - phi_val) < 1e-9
    ][0]

    cal_phi = [
        r for r in calibrated_simulation_results if abs(r.phi - phi_val) < 1e-9
    ]
    assert len(cal_phi) == len(BLOCK_LENGTHS)
    for r in cal_phi:
        assert r.rejection_rate < nom_cont2.rejection_rate, (
            f"Calibrated rate {r.rejection_rate} for L={r.block_length} not strictly below "
            f"nominal rate {nom_cont2.rejection_rate} at phi={phi_val}"
        )


# ---------------------------------------------------------------------------
# T40: test slow sul metodo centrato (H0 imposta)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def centered_simulation_results() -> list[RejectionResult]:
    """Esegue una sola volta la simulazione calibrata centrata per i test slow del modulo."""
    return compute_centered_calibrated_rejection_rates(seed=SEED_C2, bootstrap_seed=SEED_S7)


@pytest.mark.slow
def test_acceptance_centered_calibrated_phi_zero_within_mc_interval(
    centered_simulation_results: list[RejectionResult],
):
    """A phi = 0, per ogni L, il tasso del metodo centrato sta nell'intervallo MC al 99%."""
    phi0_results = [
        r for r in centered_simulation_results if abs(r.phi - 0.0) < 1e-9
    ]
    assert len(phi0_results) == len(BLOCK_LENGTHS)
    for r in phi0_results:
        assert r.method == METHOD_BLOCK_BOOTSTRAP_CENTERED
        assert r.mc_lower_99 <= r.rejection_rate <= r.mc_upper_99, (
            f"Centered rate {r.rejection_rate} for L={r.block_length} outside 99% MC "
            f"interval [{r.mc_lower_99}, {r.mc_upper_99}]"
        )


@pytest.mark.slow
def test_acceptance_csv_centered_values(
    centered_simulation_results: list[RejectionResult],
):
    """Le 12 righe centrate del CSV coincidono campo per campo con la simulazione."""
    csv_path = os.path.join("results", "us_c2_anova_autocorrelation.csv")
    with open(csv_path, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        _ = next(reader)
        rows = list(reader)

    centered_rows = rows[24:36]
    assert len(centered_rows) == len(centered_simulation_results)

    for row_idx, (csv_row, exp_res) in enumerate(
        zip(centered_rows, centered_simulation_results)
    ):
        exp_dict = exp_res.to_row()
        assert len(csv_row) == len(CSV_COLUMNS)
        for col_idx, col_name in enumerate(CSV_COLUMNS):
            expected_val_str = str(exp_dict[col_name])
            actual_val_str = csv_row[col_idx]
            if col_name in FLOAT_CSV_COLUMNS:
                assert math.isclose(
                    float(actual_val_str),
                    float(expected_val_str),
                    rel_tol=1e-12,
                    abs_tol=0.0,
                ), (
                    f"Mismatch at centered row {row_idx} (CSV row {row_idx + 24}), "
                    f"column '{col_name}': expected '{expected_val_str}', got '{actual_val_str}'"
                )
            else:
                assert actual_val_str == expected_val_str, (
                    f"Mismatch at centered row {row_idx} (CSV row {row_idx + 24}), "
                    f"column '{col_name}': expected '{expected_val_str}', got '{actual_val_str}'"
                )

