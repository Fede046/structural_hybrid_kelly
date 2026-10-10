"""Test di accettazione e unita' per i test di eteroschedasticita' (US-C6.4 / Task 38).

Copre i criteri di accettazione:
1. Validazioni di tipi, forme, valori non finiti e rango;
2. Casi limite costruiti a mano (resid^2 lineare in z/x -> R^2=1, LM=n; resid^2 costante -> LM=0);
3. Equivalenza con statsmodels su 50 dataset casuali (rel_tol 1e-9);
4. Equivalenza della versione a lotti con il ciclo sui singoli campioni (rel_tol 1e-12 per B >= 20);
5. Taglia nominale al 5% in [0.0322, 0.0678] su 1000 dataset gaussiani omoschedastici e potenza > 90%;
7. Controllo AST: statsmodels compare solo nell'extra dev e solo in tests/, mai in src/ ne' in scripts/.
"""

import ast
import math
from pathlib import Path

import numpy as np
import pytest
import scipy.stats
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan, het_white

from shk.stats.heteroskedasticity import (
    HeteroskedasticityBatchResult,
    HeteroskedasticityTestResult,
    bp_statistic,
    bp_statistic_batch,
    breusch_pagan_lm,
    nominal_threshold,
    ols_residuals,
    white_lm,
    white_statistic,
    white_statistic_batch,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


# ==============================================================================
# Criterio 1: Validazioni di tipi, forme, valori non finiti e rango
# ==============================================================================


def test_validations_and_rank() -> None:
    """Verifica le eccezioni su tipi non validi, forme errate, NaN/Inf e rango deficitario."""
    n = 20
    y_valid = np.ones(n)
    x_valid = np.ones((n, 2))
    x_valid[:, 1] = np.arange(n)

    # 1. TypeError su tipi non numerici o non ndarray
    with pytest.raises(TypeError):
        ols_residuals([1, 2, 3], x_valid)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ols_residuals(y_valid, "invalid")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ols_residuals(y_valid.astype(bool), x_valid)
    with pytest.raises(TypeError):
        breusch_pagan_lm(y_valid, x_valid.astype(complex))
    with pytest.raises(TypeError):
        white_lm(y_valid.astype(object), x_valid)

    # 2. ValueError su forme incompatibili o non 1D/2D
    with pytest.raises(ValueError):
        ols_residuals(y_valid, x_valid[:10])  # mismatch righe
    with pytest.raises(ValueError):
        ols_residuals(np.ones((n, 2)), x_valid)  # y 2D
    with pytest.raises(ValueError):
        breusch_pagan_lm(y_valid, np.ones((n, 2, 2)))  # z 3D
    with pytest.raises(ValueError):
        white_lm(np.empty(0), x_valid)  # resid vuoto

    # 3. ValueError su valori non finiti
    y_nan = y_valid.copy()
    y_nan[0] = np.nan
    with pytest.raises(ValueError):
        ols_residuals(y_nan, x_valid)
    x_inf = x_valid.copy()
    x_inf[0, 0] = np.inf
    with pytest.raises(ValueError):
        breusch_pagan_lm(y_valid, x_inf)
    with pytest.raises(ValueError):
        white_lm(y_valid, x_inf)

    # 4. ValueError su rango deficitario del disegno primario
    # Matrice x con colonne identiche o collineari con la costante
    x_collinear = np.ones((n, 2))  # Entrambe le colonne uguali a 1 (collineari con costante)
    with pytest.raises(ValueError, match="full column rank"):
        ols_residuals(y_valid, x_collinear)

    # Campione con n <= k + 1
    with pytest.raises(ValueError, match="must exceed"):
        ols_residuals(np.ones(3), np.ones((3, 3)))

    # 5. ValueError su rango deficitario del disegno ausiliario
    z_collinear = np.ones((n, 2))
    with pytest.raises(ValueError, match="full column rank"):
        breusch_pagan_lm(y_valid, z_collinear)

    # 6. Validazione di nominal_threshold
    with pytest.raises(TypeError):
        nominal_threshold("df", 0.05)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        nominal_threshold(2, "alpha")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        nominal_threshold(0, 0.05)
    with pytest.raises(ValueError):
        nominal_threshold(2, 0.0)
    with pytest.raises(ValueError):
        nominal_threshold(2, 1.0)


# ==============================================================================
# Criterio 2: Casi limite costruiti a mano (R^2 = 1 -> LM = n; costante -> LM = 0)
# ==============================================================================


def test_exact_handcrafted_cases() -> None:
    """Verifica che resid^2 lineare in z dia R^2=1 e LM=n, e che resid^2 costante dia LM=0."""
    n = 100
    rng = np.random.default_rng(12345)

    # --- Breusch-Pagan ---
    # Caso 1: resid^2 esattamente lineare in z -> R^2 = 1.0, LM = n
    z = rng.uniform(1.0, 5.0, size=(n, 1))
    g_linear = 2.0 + 3.0 * z[:, 0]
    resid_linear = np.sqrt(g_linear)
    res_bp_lin = breusch_pagan_lm(resid_linear, z)
    assert res_bp_lin.df == 1
    assert math.isclose(res_bp_lin.lm_stat, float(n), rel_tol=1e-12)

    # Caso 2: resid^2 costante -> R^2 = 0.0, LM = 0.0
    resid_const = np.full(n, 2.5)  # resid^2 = 6.25 costante
    res_bp_const = breusch_pagan_lm(resid_const, z)
    assert res_bp_const.df == 1
    assert math.isclose(res_bp_const.lm_stat, 0.0, abs_tol=1e-15)
    assert math.isclose(res_bp_const.p_value, 1.0, rel_tol=1e-12)

    # --- White ---
    # Caso 1: resid^2 esattamente lineare nelle colonne di x -> R^2 = 1.0, LM = n
    x = rng.uniform(1.0, 5.0, size=(n, 2))
    g_white = 10.0 + 2.0 * x[:, 0] + 3.0 * x[:, 1]
    resid_white = np.sqrt(g_white)
    res_wh_lin = white_lm(resid_white, x)
    assert res_wh_lin.df == 5  # 2 lineari + 3 (x1^2, x1*x2, x2^2)
    assert math.isclose(res_wh_lin.lm_stat, float(n), rel_tol=1e-12)

    # Caso 2: resid^2 costante per White -> LM = 0.0
    res_wh_const = white_lm(resid_const, x)
    assert res_wh_const.df == 5
    assert math.isclose(res_wh_const.lm_stat, 0.0, abs_tol=1e-15)
    assert math.isclose(res_wh_const.p_value, 1.0, rel_tol=1e-12)


# ==============================================================================
# Criterio 3: Equivalenza con statsmodels su 50 dataset casuali (rel_tol 1e-9)
# ==============================================================================


def test_statsmodels_equivalence_50_datasets() -> None:
    """Verifica l'equivalenza numerica con statsmodels su 50 dataset casuali (25 homo, 25 hetero)."""
    rng = np.random.default_rng(20261009)
    n = 380
    n_datasets = 50

    for idx in range(n_datasets):
        # Due regressori continui
        x = rng.standard_normal((n, 2))
        X_with_const = sm.add_constant(x)
        beta = np.array([2.0, -1.2, 0.8])

        is_hetero = idx >= (n_datasets // 2)
        if is_hetero:
            sigma = 0.5 + np.abs(x[:, 0]) * 1.5
            eps = rng.standard_normal(n) * sigma
        else:
            eps = rng.standard_normal(n) * 1.0

        y = X_with_const @ beta + eps

        # 1. Residui manuali vs statsmodels
        resid_manual = ols_residuals(y, x)
        sm_ols_model = sm.OLS(y, X_with_const).fit()
        resid_sm = sm_ols_model.resid
        np.testing.assert_allclose(resid_manual, resid_sm, rtol=1e-12, atol=1e-12)

        # 2. Breusch-Pagan (Koenker)
        bp_res = breusch_pagan_lm(resid_manual, x)
        bp_sm = het_breuschpagan(resid_sm, X_with_const, robust=True)
        lm_sm = float(bp_sm[0])
        pval_sm = float(bp_sm[1])
        df_sm = X_with_const.shape[1] - 1

        assert bp_res.df == df_sm
        assert math.isclose(bp_res.lm_stat, lm_sm, rel_tol=1e-9, abs_tol=1e-12), (
            f"Dataset {idx}: BP LM manual {bp_res.lm_stat} != sm {lm_sm}"
        )
        assert math.isclose(bp_res.p_value, pval_sm, rel_tol=1e-9, abs_tol=1e-12)

        # 3. White
        wh_res = white_lm(resid_manual, x)
        wh_sm = het_white(resid_sm, X_with_const)
        lm_wh_sm = float(wh_sm[0])
        pval_wh_sm = float(wh_sm[1])
        df_wh_sm = 5

        assert wh_res.df == df_wh_sm
        assert math.isclose(wh_res.lm_stat, lm_wh_sm, rel_tol=1e-9, abs_tol=1e-12), (
            f"Dataset {idx}: White LM manual {wh_res.lm_stat} != sm {lm_wh_sm}"
        )
        assert math.isclose(wh_res.p_value, pval_wh_sm, rel_tol=1e-9, abs_tol=1e-12)


# ==============================================================================
# Criterio 4: Equivalenza a lotti con il ciclo sui singoli campioni (rel_tol 1e-12)
# ==============================================================================


def test_batch_equivalence_with_loop() -> None:
    """Verifica che le versioni a lotti (bp/white_statistic_batch) coincidano con il loop (rel 1e-12)."""
    rng = np.random.default_rng(42)
    b_count = 25  # B >= 20
    n = 380
    k = 2

    # Caso A: x condiviso (2D)
    x_shared = rng.standard_normal((n, k))
    y_batch = rng.standard_normal((b_count, n))

    # Breusch-Pagan batch vs loop
    batch_bp = bp_statistic_batch(y_batch, x_shared)
    loop_bp_stats = np.empty(b_count, dtype=np.float64)
    loop_bp_pvals = np.empty(b_count, dtype=np.float64)
    for b in range(b_count):
        res = bp_statistic(y_batch[b], x_shared)
        loop_bp_stats[b] = res.lm_stat
        loop_bp_pvals[b] = res.p_value

    assert batch_bp.df == k
    np.testing.assert_allclose(batch_bp.lm_stats, loop_bp_stats, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(batch_bp.p_values, loop_bp_pvals, rtol=1e-12, atol=1e-12)

    # White batch vs loop
    batch_wh = white_statistic_batch(y_batch, x_shared)
    loop_wh_stats = np.empty(b_count, dtype=np.float64)
    loop_wh_pvals = np.empty(b_count, dtype=np.float64)
    for b in range(b_count):
        res = white_statistic(y_batch[b], x_shared)
        loop_wh_stats[b] = res.lm_stat
        loop_wh_pvals[b] = res.p_value

    assert batch_wh.df == 5
    np.testing.assert_allclose(batch_wh.lm_stats, loop_wh_stats, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(batch_wh.p_values, loop_wh_pvals, rtol=1e-12, atol=1e-12)

    # Caso B: x non condiviso (3D)
    x_3d = rng.standard_normal((b_count, n, k))
    batch_bp_3d = bp_statistic_batch(y_batch, x_3d)
    loop_bp_stats_3d = np.empty(b_count, dtype=np.float64)
    for b in range(b_count):
        res = bp_statistic(y_batch[b], x_3d[b])
        loop_bp_stats_3d[b] = res.lm_stat
    np.testing.assert_allclose(batch_bp_3d.lm_stats, loop_bp_stats_3d, rtol=1e-12, atol=1e-12)

    batch_wh_3d = white_statistic_batch(y_batch, x_3d)
    loop_wh_stats_3d = np.empty(b_count, dtype=np.float64)
    for b in range(b_count):
        res = white_statistic(y_batch[b], x_3d[b])
        loop_wh_stats_3d[b] = res.lm_stat
    np.testing.assert_allclose(batch_wh_3d.lm_stats, loop_wh_stats_3d, rtol=1e-12, atol=1e-12)


# ==============================================================================
# Criterio 5: Taglia nominale al 5% e potenza su 1000 dataset gaussiani
# ==============================================================================


def test_nominal_size_and_power() -> None:
    """Verifica taglia nominale in [0.0322, 0.0678] al 5% e potenza > 90% su 1000 dataset."""
    rng = np.random.default_rng(20261009)
    n = 380
    b_count = 1_000

    # Regressori H (vantaggio/forza casa continua) e t (tempo normalizzato)
    H = rng.standard_normal(n)
    t = np.linspace(0.0, 1.0, n, dtype=np.float64)
    x = np.column_stack([H, t])

    # 1. Dataset omoschedastici: y = 1.0 + 0.5 * H - 0.2 * t + eps, eps ~ N(0, 1)
    eps_homo = rng.standard_normal((b_count, n))
    y_homo = 1.0 + 0.5 * H - 0.2 * t + eps_homo

    crit_bp = nominal_threshold(df=2, alpha=0.05)
    crit_wh = nominal_threshold(df=5, alpha=0.05)

    res_bp_homo = bp_statistic_batch(y_homo, x)
    res_wh_homo = white_statistic_batch(y_homo, x)

    rej_rate_bp_homo = float(np.mean(res_bp_homo.lm_stats > crit_bp))
    rej_rate_wh_homo = float(np.mean(res_wh_homo.lm_stats > crit_wh))

    # Intervallo asintotico al 99%: [0.0322, 0.0678]
    assert 0.0322 <= rej_rate_bp_homo <= 0.0678, (
        f"BP homo rejection rate {rej_rate_bp_homo} outside [0.0322, 0.0678]"
    )
    assert 0.0322 <= rej_rate_wh_homo <= 0.0678, (
        f"White homo rejection rate {rej_rate_wh_homo} outside [0.0322, 0.0678]"
    )

    # 2. Dataset eteroschedastici: sigma_i = 1.0 + 3.0 * t_i
    sigma = 1.0 + 3.0 * t
    eps_het = rng.standard_normal((b_count, n)) * sigma
    y_het = 1.0 + 0.5 * H - 0.2 * t + eps_het

    res_bp_het = bp_statistic_batch(y_het, x)
    res_wh_het = white_statistic_batch(y_het, x)

    rej_rate_bp_het = float(np.mean(res_bp_het.lm_stats > crit_bp))
    rej_rate_wh_het = float(np.mean(res_wh_het.lm_stats > crit_wh))

    assert rej_rate_bp_het > 0.90, f"BP power {rej_rate_bp_het} <= 0.90"
    assert rej_rate_wh_het > 0.90, f"White power {rej_rate_wh_het} <= 0.90"


# ==============================================================================
# Criterio 7: statsmodels compare solo nell'extra dev e solo in tests/
# ==============================================================================


def test_statsmodels_dependency_scope_ast() -> None:
    """Verifica via AST che statsmodels non sia mai importato in src/ ne' in scripts/."""
    # 1. Ispezione di pyproject.toml
    pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "statsmodels" in pyproject_text
    # Non deve comparire in dependencies primarie
    dep_section = pyproject_text.split("[project]")[1].split("[project.optional-dependencies]")[0]
    assert "statsmodels" not in dep_section, "statsmodels trovato nelle dipendenze primarie di pyproject.toml"

    # 2. Ispezione AST di src/ e scripts/
    for folder in ("src", "scripts"):
        dir_path = REPO_ROOT / folder
        if not dir_path.exists():
            continue
        for py_file in dir_path.rglob("*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == "statsmodels" or alias.name.startswith("statsmodels."):
                            pytest.fail(f"Import vietato di statsmodels in {py_file}:{node.lineno}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module and (node.module == "statsmodels" or node.module.startswith("statsmodels.")):
                        pytest.fail(f"ImportFrom vietato di statsmodels in {py_file}:{node.lineno}")
