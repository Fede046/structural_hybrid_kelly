"""Test di src/shk/stats/oaxaca.py (T45)."""

import math

import numpy as np
import pytest

from shk.stats.oaxaca import (
    INTERCEPT_NAME,
    TWOFOLD_REFERENCES,
    oaxaca_blinder,
    oaxaca_iid_standard_errors,
    ols_qr,
)

TOL = 1e-12


def test_hand_example():
    """Esempio minimo calcolato a mano: A x = (0, 1, 2), y = (1, 2, 4); B x = (1, 2, 3), y = (2, 4, 7).

    beta_A = (5/6, 3/2), beta_B = (-2/3, 5/2), x̄_A = (1, 1), x̄_B = (1, 2):
    totale 2, C = 3/2, S = -1/2, I = 1, pi = 1/6; Neumark e pooled con indicatore hanno
    pendenza 2, quindi spiegata 2 e non spiegata 0.
    """
    res = oaxaca_blinder(
        np.array([[0.0], [1.0], [2.0]]), np.array([1.0, 2.0, 4.0]),
        np.array([[1.0], [2.0], [3.0]]), np.array([2.0, 4.0, 7.0]),
    )
    np.testing.assert_allclose(res.fit_a.beta, [5 / 6, 3 / 2], rtol=0, atol=TOL)
    np.testing.assert_allclose(res.fit_b.beta, [-2 / 3, 5 / 2], rtol=0, atol=TOL)
    assert math.isclose(res.total, 2.0, abs_tol=TOL)
    assert math.isclose(res.compositional, 1.5, abs_tol=TOL)
    assert math.isclose(res.structural, -0.5, abs_tol=TOL)
    assert math.isclose(res.interaction, 1.0, abs_tol=TOL)
    assert math.isclose(res.structural_share, 1 / 6, abs_tol=TOL)
    expected_twofold = {
        "beta_a": (1.5, 0.5),
        "beta_b": (2.5, -0.5),
        "reimers": (2.0, 0.0),
        "cotton": (2.0, 0.0),
        "neumark": (2.0, 0.0),
        "pooled_group": (2.0, 0.0),
    }
    for ref, (expl, unexpl) in expected_twofold.items():
        assert math.isclose(res.twofold[ref].explained, expl, abs_tol=TOL), ref
        assert math.isclose(res.twofold[ref].unexplained, unexpl, abs_tol=TOL), ref
    np.testing.assert_allclose(res.twofold["pooled_group"].reference, [1 / 3, 2.0], atol=TOL)
    assert res.detailed.names == (INTERCEPT_NAME, "x0")
    np.testing.assert_allclose(res.detailed.compositional, [0.0, 1.5], atol=TOL)
    np.testing.assert_allclose(res.detailed.structural, [-1.5, 1.0], atol=TOL)
    np.testing.assert_allclose(res.detailed.interaction, [0.0, 1.0], atol=TOL)


def _random_groups(rng: np.random.Generator, n: int = 150):
    xa = np.column_stack([rng.normal(size=n), rng.normal(1, 2, size=n), rng.random(n) < 0.4])
    xb = np.column_stack([rng.normal(0.5, 1, size=n), rng.normal(0, 1, size=n), rng.random(n) < 0.6])
    ya = 0.3 + xa @ [0.2, -0.1, 0.5] + rng.normal(size=n)
    yb = -0.1 + xb @ [0.4, -0.1, 0.1] + rng.normal(size=n)
    return xa.astype(float), ya, xb.astype(float), yb


def test_components_sum_to_total():
    """Three-fold, ogni two-fold e la dettagliata sommano al totale entro 1e-12."""
    rng = np.random.default_rng(10)
    for _ in range(20):
        res = oaxaca_blinder(*_random_groups(rng), dummy_blocks={"d_is_0": [2]})
        assert abs(res.compositional + res.structural + res.interaction - res.total) <= TOL
        assert set(res.twofold) == set(TWOFOLD_REFERENCES)
        for tf in res.twofold.values():
            assert abs(tf.explained + tf.unexplained - res.total) <= TOL
        d = res.detailed
        assert abs(d.compositional.sum() - res.compositional) <= TOL
        assert abs(d.structural.sum() - res.structural) <= TOL
        assert abs(d.interaction.sum() - res.interaction) <= TOL


def test_twofold_extreme_references_match_threefold():
    """Con beta* = beta_A la spiegata è C; con beta* = beta_B la non spiegata è S."""
    res = oaxaca_blinder(*_random_groups(np.random.default_rng(11)))
    assert math.isclose(res.twofold["beta_a"].explained, res.compositional, abs_tol=TOL)
    assert math.isclose(res.twofold["beta_a"].unexplained, res.structural + res.interaction, abs_tol=TOL)
    assert math.isclose(res.twofold["beta_b"].unexplained, res.structural, abs_tol=TOL)
    assert math.isclose(res.twofold["beta_b"].explained, res.compositional + res.interaction, abs_tol=TOL)
    assert 0.0 <= res.structural_share <= 1.0


def _categorical_data(rng: np.random.Generator, n: int, probs, betas, intercept):
    levels = rng.choice(3, size=n, p=probs)
    x_cont = rng.normal(size=n)
    y = intercept + 0.3 * x_cont + np.array(betas)[levels] + rng.normal(scale=0.5, size=n)
    return levels, x_cont, y


def _design(levels: np.ndarray, x_cont: np.ndarray, reference: int) -> np.ndarray:
    dummies = [(levels == lv).astype(float) for lv in range(3) if lv != reference]
    return np.column_stack([x_cont, *dummies])


def test_yun_detailed_invariant_to_reference_category():
    """La dettagliata con Yun non dipende dalla categoria omessa, entro 1e-12 (criterio T45)."""
    rng = np.random.default_rng(12)
    lev_a, xc_a, y_a = _categorical_data(rng, 300, [0.5, 0.3, 0.2], [0.0, 0.4, -0.2], 0.1)
    lev_b, xc_b, y_b = _categorical_data(rng, 300, [0.2, 0.3, 0.5], [0.0, 0.1, 0.3], -0.2)

    by_level: list[dict[str, tuple[float, float, float]]] = []
    for reference in range(3):
        others = [lv for lv in range(3) if lv != reference]
        names = ["x_cont", *[f"level_{lv}" for lv in others]]
        res = oaxaca_blinder(
            _design(lev_a, xc_a, reference), y_a, _design(lev_b, xc_b, reference), y_b,
            names=names, dummy_blocks={f"level_{reference}": [1, 2]},
        )
        d = res.detailed
        by_level.append({
            nm: (d.compositional[i], d.structural[i], d.interaction[i]) for i, nm in enumerate(d.names)
        })
    for other in by_level[1:]:
        assert set(other) == set(by_level[0])
        for name, values in by_level[0].items():
            np.testing.assert_allclose(other[name], values, rtol=0, atol=TOL, err_msg=name)


def test_yun_binary_dummy_invariant_to_coding():
    """Dummy binaria codificata come d oppure 1 - d: stessi contributi per livello."""
    xa, ya, xb, yb = _random_groups(np.random.default_rng(13))
    res_1 = oaxaca_blinder(xa, ya, xb, yb, names=["x1", "x2", "d_is_1"], dummy_blocks={"d_is_0": [2]})
    flip_a, flip_b = xa.copy(), xb.copy()
    flip_a[:, 2] = 1.0 - flip_a[:, 2]
    flip_b[:, 2] = 1.0 - flip_b[:, 2]
    res_0 = oaxaca_blinder(flip_a, ya, flip_b, yb, names=["x1", "x2", "d_is_0"], dummy_blocks={"d_is_1": [2]})
    d1 = dict(zip(res_1.detailed.names, zip(res_1.detailed.compositional, res_1.detailed.structural)))
    d0 = dict(zip(res_0.detailed.names, zip(res_0.detailed.compositional, res_0.detailed.structural)))
    for name in d1:
        np.testing.assert_allclose(d0[name], d1[name], rtol=0, atol=TOL, err_msg=name)


def test_iid_standard_errors_positive_and_finite():
    """Errori standard iid finiti e positivi."""
    xa, ya, xb, yb = _random_groups(np.random.default_rng(14))
    se = oaxaca_iid_standard_errors(oaxaca_blinder(xa, ya, xb, yb), xa, xb)
    for value in se:
        assert math.isfinite(value) and value > 0.0


def test_validation_errors():
    """Tipi, forme, rango e blocchi non validi."""
    xa, ya, xb, yb = _random_groups(np.random.default_rng(15))
    with pytest.raises(TypeError, match="x_a must be an instance of np.ndarray"):
        oaxaca_blinder(xa.tolist(), ya, xb, yb)  # type: ignore
    with pytest.raises(ValueError, match="x_a must be 2D"):
        oaxaca_blinder(xa[:, 0], ya, xb, yb)
    with pytest.raises(ValueError, match="same columns"):
        oaxaca_blinder(xa, ya, xb[:, :2], yb)
    with pytest.raises(ValueError, match="y_b must be 1D"):
        oaxaca_blinder(xa, ya, xb, yb[:-1])
    with pytest.raises(ValueError, match="names must be 3 strings"):
        oaxaca_blinder(xa, ya, xb, yb, names=["a", "b"])
    with pytest.raises(ValueError, match="invalid or repeated"):
        oaxaca_blinder(xa, ya, xb, yb, dummy_blocks={"ref": [5]})
    collinear = xa.copy()
    collinear[:, 1] = 2.0 * collinear[:, 0]
    with pytest.raises(ValueError, match="rank deficient"):
        oaxaca_blinder(collinear, ya, xb, yb)
    with pytest.raises(ValueError, match="more observations than regressors"):
        ols_qr(np.ones((2, 2)), np.ones(2))
