"""Test di accettazione per l'esperimento US-C2.2 (falso rigetto dell'ANOVA su serie AR(1))."""

import os
import csv
import numpy as np
import pytest

import shk.stats.false_rejection
from shk.stats.anova import oneway_anova_vectorized
from shk.stats.timeseries import generate_ar1_series
from shk.stats.false_rejection import (
    ALPHA,
    CSV_COLUMNS,
    DESIGNS,
    DESIGN_CONTIGUOUS_2,
    DESIGN_CONTIGUOUS_38,
    DESIGN_RANDOM_2,
    N_OBS,
    N_SERIES,
    PHI_VALUES,
    SEED_C2,
    RejectionResult,
    compute_nominal_rejection_rates,
    critical_value_nominal,
    make_design_labels,
    monte_carlo_interval_99,
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
    """Verifica che il CSV abbia 12 righe e che ciascun campo coincida con i risultati calcolati."""
    csv_path = os.path.join("results", "us_c2_anova_autocorrelation.csv")
    assert os.path.isfile(csv_path), f"CSV file not found at {csv_path}"

    expected_results = compute_nominal_rejection_rates(seed=SEED_C2)

    with open(csv_path, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert tuple(header) == CSV_COLUMNS

        rows = list(reader)
        assert len(rows) == 12

    for row_idx, (csv_row, exp_res) in enumerate(zip(rows, expected_results)):
        exp_dict = exp_res.to_row()
        assert len(csv_row) == len(CSV_COLUMNS)
        for col_idx, col_name in enumerate(CSV_COLUMNS):
            expected_val_str = str(exp_dict[col_name])
            actual_val_str = csv_row[col_idx]
            assert actual_val_str == expected_val_str, (
                f"Mismatch at row {row_idx}, column '{col_name}': "
                f"expected '{expected_val_str}', got '{actual_val_str}'"
            )


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
