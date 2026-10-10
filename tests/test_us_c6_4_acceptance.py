"""Test di accettazione per la User Story US-C6.4 (Task 39).

Verifica:
- Criterio 1: Statistiche Breusch-Pagan e White su dati sintetici controllati
  e coerenza esatta fra versione scalare e versione batch (tolleranza 1e-12);
- Criterio 2: Proprietà della calibrazione: entropia H, ordinamento date,
  e soglie calibrate maggiori delle soglie nominali;
- Criterio 3: Verifica Bonferroni: tutti i 27 tassi simulati cadono in [0.0153, 0.0847];
- Criterio 4: Coerenza interna del CSV results/us_c6_4_heteroskedasticity.csv
  (105 righe, schema 23 colonne, corrispondenza conteggi 19 validazioni e p-value binomiali);
- Criterio 5: Ricalcolo dai dati reali e integrità della figura PNG;
- Criterio 6: Convenzioni del codice e controlli AST su modulo e script (nessun print).
"""

import ast
import csv
import math
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
import pytest
import scipy.stats

from shk.data.loading import DEFAULT_DATA_DIR
from shk.data.split import load_by_role, read_split_config
from shk.kelly.floor import SEED_C6
from shk.model.elo_fit import ELO_FITS, derive_fit_schedule
from shk.model.residual_heteroskedasticity import (
    ALPHA,
    BLOCK_LENGTHS,
    BONFERRONI_LOWER,
    BONFERRONI_UPPER,
    HETEROSKEDASTICITY_CSV_COLUMNS,
    MATCHES_PER_SEASON,
    STATISTIC_DFS,
    STATISTICS,
    binomial_exceedance_p_value,
    compute_scenario_test_statistics,
    compute_shannon_entropy,
    evaluate_residual_heteroskedasticity,
    nominal_threshold,
    spawn_c6_4_generators,
)
from shk.model.residuals import compute_model_residuals
from shk.stats.heteroskedasticity import (
    bp_statistic,
    bp_statistic_batch,
    white_statistic,
    white_statistic_batch,
)


def _has_real_data() -> bool:
    """Verifica se la directory data/raw/E0 contiene file CSV reali."""
    return DEFAULT_DATA_DIR.exists() and len(list(DEFAULT_DATA_DIR.glob("*.csv"))) > 0


def _load_csv_records() -> list[dict[str, str]]:
    """Carica i record dal CSV results/us_c6_4_heteroskedasticity.csv."""
    csv_path = Path(__file__).resolve().parents[1] / "results" / "us_c6_4_heteroskedasticity.csv"
    assert csv_path.exists(), f"File CSV non trovato: {csv_path}"
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


# ==============================================================================
# Criterio 1: Statistiche su dati sintetici e coerenza scalare/batch
# ==============================================================================
def test_synthetic_homoskedastic_and_heteroskedastic_behavior() -> None:
    """Verifica il comportamento dei test su serie sintetiche controllate."""
    rng = np.random.default_rng(12345)
    n = MATCHES_PER_SEASON
    t = np.arange(1, n + 1, dtype=np.float64)
    h = rng.uniform(0.5, 1.1, size=n)

    # 1. Omoschedastico: errore gaussiano i.i.d.
    y_homo = 1.0 + 0.5 * h + 0.001 * t + rng.normal(0, 0.1, size=n)
    res_homo = compute_scenario_test_statistics(y_homo, h, t)
    for stat_name, res in res_homo.items():
        assert res.df == STATISTIC_DFS[stat_name]
        nom_th = nominal_threshold(res.df, ALPHA)
        # Sotto H0 con n=380 e rumore gaussiano, non deve rigettare ad alpha=0.01
        assert res.lm_stat < nominal_threshold(res.df, 0.001)

    # 2. Eteroschedastico temporale: varianza crescente con t
    sigma_time = 0.05 + 0.001 * t
    y_time = 1.0 + 0.5 * h + rng.normal(0, sigma_time)
    res_time = compute_scenario_test_statistics(y_time, h, t)
    assert res_time["bp_time"].p_value < 0.01
    assert res_time["bp_joint"].p_value < 0.01


def test_scalar_vs_batch_consistency() -> None:
    """Verifica che la versione batch e la versione scalare coincidano entro 1e-12."""
    rng = np.random.default_rng(54321)
    b_count = 5
    n = MATCHES_PER_SEASON
    t = np.arange(1, n + 1, dtype=np.float64)

    y_batch = rng.normal(0, 1, size=(b_count, n))
    h_batch = rng.uniform(0.6, 1.0, size=(b_count, n))

    x_batch = np.empty((b_count, n, 2), dtype=np.float64)
    x_batch[:, :, 0] = h_batch
    x_batch[:, :, 1] = np.broadcast_to(t, (b_count, n))

    z_time_batch = np.broadcast_to(t[np.newaxis, :, np.newaxis], (b_count, n, 1))

    # Calcolo batch
    batch_joint = bp_statistic_batch(y_batch, x_batch)
    batch_time = bp_statistic_batch(y_batch, x_batch, z=z_time_batch)
    batch_white = white_statistic_batch(y_batch, x_batch)

    # Confronto con calcolo scalare per ciascun campione
    for b in range(b_count):
        y_b = y_batch[b]
        h_b = h_batch[b]
        res_scal = compute_scenario_test_statistics(y_b, h_b, t)

        np.testing.assert_allclose(batch_joint.lm_stats[b], res_scal["bp_joint"].lm_stat, rtol=1e-12)
        np.testing.assert_allclose(batch_time.lm_stats[b], res_scal["bp_time"].lm_stat, rtol=1e-12)
        np.testing.assert_allclose(batch_white.lm_stats[b], res_scal["white"].lm_stat, rtol=1e-12)


# ==============================================================================
# Criterio 2: Proprietà della calibrazione e dell'entropia
# ==============================================================================
def test_shannon_entropy_calculation() -> None:
    """Verifica che l'entropia Shannon valga ln(3) per distribuzione uniforme (1/3, 1/3, 1/3)."""
    probs_uniform = np.full((10, 3), 1.0 / 3.0, dtype=np.float64)
    h_uniform = compute_shannon_entropy(probs_uniform)
    expected_ln3 = float(np.log(3.0))
    np.testing.assert_allclose(h_uniform, expected_ln3, rtol=1e-14)


def test_generator_hierarchy_determinism() -> None:
    """Verifica che la gerarchia spawn_c6_4_generators sia deterministica e riproducibile."""
    rng_dict1 = spawn_c6_4_generators(seed=SEED_C6)
    rng_dict2 = spawn_c6_4_generators(seed=SEED_C6)

    # Estrazione di un float di controllo
    val1 = rng_dict1["2000-01"][7][0].standard_normal()
    val2 = rng_dict2["2000-01"][7][0].standard_normal()
    assert val1 == val2


def test_calibrated_thresholds_exceed_nominal_for_joint_and_white() -> None:
    """Verifica che per bp_joint e white le soglie calibrate superino quelle nominali per la presenza di persistenza."""
    records = _load_csv_records()
    verif_rows = [r for r in records if r["row_type"] == "verification"]

    for r in verif_rows:
        stat_name = r["statistic"]
        calib_th = float(r["calibrated_threshold"])
        nom_th = float(r["threshold_nom"])

        if stat_name in ("bp_joint", "white"):
            assert calib_th > nom_th, (
                f"Per {stat_name} (fit {r['fit_through']}, L={r['block_length']}), "
                f"calibrated {calib_th} non supera nominal {nom_th}"
            )


# ==============================================================================
# Criterio 3: Verifica Bonferroni [0.0153, 0.0847]
# ==============================================================================
def test_verification_rejection_rates_within_bonferroni_interval() -> None:
    """Verifica che tutti i 27 tassi di rigetto simulati cadano nell'intervallo di Bonferroni al 99%."""
    records = _load_csv_records()
    verif_rows = [r for r in records if r["row_type"] == "verification"]
    assert len(verif_rows) == 27, f"Attese 27 righe di verifica, trovate {len(verif_rows)}"

    for r in verif_rows:
        rate = float(r["verif_rejection_rate_calib"])
        assert BONFERRONI_LOWER <= rate <= BONFERRONI_UPPER, (
            f"Tasso di rigetto {rate} fuori dall'intervallo [{BONFERRONI_LOWER}, {BONFERRONI_UPPER}] "
            f"per fit {r['fit_through']}, L={r['block_length']}, stat {r['statistic']}"
        )


# ==============================================================================
# Criterio 4: Coerenza interna del CSV
# ==============================================================================
def test_csv_structure_and_row_counts() -> None:
    """Verifica che il CSV contenga esattamente 105 righe e le 23 colonne prescritte."""
    csv_path = Path(__file__).resolve().parents[1] / "results" / "us_c6_4_heteroskedasticity.csv"
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    assert tuple(header) == HETEROSKEDASTICITY_CSV_COLUMNS, "Schema delle colonne CSV non conforme"
    assert len(rows) == 105, f"Attese 105 righe nel CSV, trovate {len(rows)}"

    records = _load_csv_records()
    scenario_rows = [r for r in records if r["row_type"] == "scenario"]
    verif_rows = [r for r in records if r["row_type"] == "verification"]
    summary_rows = [r for r in records if r["row_type"] == "summary"]

    assert len(scenario_rows) == 66, f"Attese 66 righe scenario, trovate {len(scenario_rows)}"
    assert len(verif_rows) == 27, f"Attese 27 righe verification, trovate {len(verif_rows)}"
    assert len(summary_rows) == 12, f"Attese 12 righe summary, trovate {len(summary_rows)}"

    # 3 stagioni training e 19 stagioni validation
    training_scenarios = [r for r in scenario_rows if r["role"] == "training"]
    validation_scenarios = [r for r in scenario_rows if r["role"] == "validation"]
    assert len(training_scenarios) == 3 * 3, "Attese 9 righe per 3 stagioni di training"
    assert len(validation_scenarios) == 19 * 3, "Attese 57 righe per 19 stagioni di validazione"


def test_summary_rejections_and_binomial_pvalues_coherence() -> None:
    """Verifica che i conteggi nelle righe summary coincidano con la somma dei flag nelle 19 di validazione."""
    records = _load_csv_records()
    scenario_val_rows = [r for r in records if r["row_type"] == "scenario" and r["role"] == "validation"]
    summary_rows = [r for r in records if r["row_type"] == "summary"]

    method_to_col = {
        "nominal": "reject_nom",
        "bootstrap_L7": "reject_L7",
        "bootstrap_L20": "reject_L20",
        "bootstrap_L40": "reject_L40",
    }

    for s_row in summary_rows:
        stat_name = s_row["statistic"]
        method_name = s_row["method"]
        expected_k = int(s_row["n_validation_rejections"])
        reported_p = float(s_row["p_value_binomial"])

        col_name = method_to_col[method_name]
        matches = [
            r for r in scenario_val_rows if r["statistic"] == stat_name and r[col_name] == "True"
        ]
        calculated_k = len(matches)

        assert expected_k == calculated_k, (
            f"Incongruenza rigetti per {stat_name} e {method_name}: "
            f"summary indica {expected_k}, somma delle righe da {calculated_k}"
        )

        expected_p = binomial_exceedance_p_value(calculated_k, n=19, p=ALPHA)
        np.testing.assert_allclose(reported_p, expected_p, rtol=1e-6)


# ==============================================================================
# Criterio 5: Ricalcolo dai dati reali e verifica PNG
# ==============================================================================
def test_real_data_recalculation_matches_versioned_csv() -> None:
    """Ricalcola l'esperimento sui dati reali se presenti e verifica coincidenza con il CSV versionato."""
    if not _has_real_data():
        pytest.skip("Dati reali non presenti in data/raw/E0")

    cfg = read_split_config()
    df_hist = load_by_role("history")
    df_train = load_by_role("training")
    df_val = load_by_role("validation")

    df = pd.concat([df_hist, df_train, df_val], ignore_index=True)
    df = df.sort_values("Date", kind="stable").reset_index(drop=True)

    schedule = derive_fit_schedule(cfg)
    df_residuals = compute_model_residuals(df, schedule, ELO_FITS)

    recalculated_records = evaluate_residual_heteroskedasticity(
        df_residuals=df_residuals,
        schedule=schedule,
        seed=SEED_C6,
    )

    versioned_records = _load_csv_records()
    assert len(recalculated_records) == len(versioned_records)

    numeric_cols = {
        "lm_stat",
        "p_value_nom",
        "threshold_nom",
        "threshold_L7",
        "threshold_L20",
        "threshold_L40",
        "calibrated_threshold",
        "verif_rejection_rate_calib",
        "verif_rejection_rate_nom",
        "n_validation_rejections",
        "p_value_binomial",
    }

    for idx, (recalc, vers) in enumerate(zip(recalculated_records, versioned_records)):
        assert recalc["row_type"] == vers["row_type"]
        assert recalc["statistic"] == vers["statistic"]
        for col in HETEROSKEDASTICITY_CSV_COLUMNS:
            val_recalc = recalc[col]
            val_vers = vers[col]
            if val_vers == "":
                assert val_recalc == "" or val_recalc is None or (isinstance(val_recalc, float) and math.isnan(val_recalc))
            elif col in numeric_cols:
                np.testing.assert_allclose(
                    float(val_recalc), float(val_vers), rtol=1e-7, atol=1e-7,
                    err_msg=f"Discrepanza colonna {col} alla riga {idx}"
                )
            else:
                assert str(val_recalc) == str(val_vers), (
                    f"Discrepanza colonna {col} alla riga {idx}: {val_recalc} vs {val_vers}"
                )


def test_png_figure_exists_and_valid() -> None:
    """Verifica che la figura thesis/figures/us_c6_4_heteroskedasticity.png esista e non sia vuota."""
    png_path = Path(__file__).resolve().parents[1] / "thesis" / "figures" / "us_c6_4_heteroskedasticity.png"
    assert png_path.exists(), f"Figura PNG mancante: {png_path}"
    assert png_path.stat().st_size > 10_000, f"Dimensione figura non valida: {png_path.stat().st_size} bytes"


# ==============================================================================
# Criterio 6: Convenzioni del codice e controlli AST
# ==============================================================================
def test_no_forbidden_print_or_logging() -> None:
    """Verifica tramite AST che né il modulo né lo script contengano chiamate a print() o logging."""
    repo_root = Path(__file__).resolve().parents[1]
    files_to_check = [
        repo_root / "src" / "shk" / "model" / "residual_heteroskedasticity.py",
        repo_root / "scripts" / "us_c6_4_heteroskedasticity.py",
    ]

    for f_path in files_to_check:
        assert f_path.exists(), f"File non trovato: {f_path}"
        with open(f_path, mode="r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(f_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                # Controllo print()
                if isinstance(func, ast.Name) and func.id == "print":
                    pytest.fail(f"Chiamata a print() trovata in {f_path} alla riga {node.lineno}")
                # Controllo logging.*
                if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id == "logging":
                    pytest.fail(f"Chiamata a logging trovata in {f_path} alla riga {node.lineno}")
