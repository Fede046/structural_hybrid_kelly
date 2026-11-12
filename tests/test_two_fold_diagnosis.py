"""Test: diagnosi di Blinder-Oaxaca a due termini (shk.model.two_fold_diagnosis), su dati costruiti."""

import numpy as np
import pytest

from shk.model.two_fold_diagnosis import (
    calibrate_reference_diagnosis,
    diagnosis_table,
    explained_parts,
    reference_coefficients,
    unexplained_parts,
)

WINDOW = 40


def _world(rng: np.random.Generator, n: int, x_shift: float = 0.0, scale: float = 1.0, drop: float = 0.0):
    """δ con dispersione che cresce con la prima covariata: sd = scale · (0.5 + x1), media −drop."""
    x = np.column_stack([rng.uniform(0.2, 1.0, size=n) + x_shift, rng.normal(size=n)])
    delta = rng.normal(size=n) * scale * (0.5 + x[:, 0]) - drop
    return x, delta


def test_two_fold_identity():
    """Spiegato + non spiegato = scarto fra la finestra e il riferimento, per media e dispersione."""
    rng = np.random.default_rng(0)
    x_ref, d_ref = _world(rng, 380)
    x_win, d_win = _world(rng, WINDOW, x_shift=0.3, drop=0.2)
    median, beta_mean, beta_disp = reference_coefficients(x_ref, d_ref)
    u_mean, u_disp = unexplained_parts(x_win, d_win, median, beta_mean, beta_disp)
    c_mean, c_disp = explained_parts(x_win, x_ref, beta_mean, beta_disp)
    assert c_mean + u_mean == pytest.approx(-(d_win.mean() - d_ref.mean()))
    z_ref, z_win = np.abs(d_ref - median), np.abs(d_win - median)
    assert c_disp + u_disp == pytest.approx(z_win.mean() - z_ref.mean())
    # Sul riferimento stesso non resta nulla da spiegare
    assert unexplained_parts(x_ref, d_ref, median, beta_mean, beta_disp) == pytest.approx((0.0, 0.0), abs=1e-12)


def test_unexplained_parts_accept_batches():
    rng = np.random.default_rng(1)
    x_ref, d_ref = _world(rng, 380)
    coef = reference_coefficients(x_ref, d_ref)
    xb, db = rng.normal(size=(7, WINDOW, 2)), rng.normal(size=(7, WINDOW))
    u_mean, u_disp = unexplained_parts(xb, db, *coef)
    assert u_mean.shape == u_disp.shape == (7,)
    single = unexplained_parts(xb[3], db[3], *coef)
    assert single == pytest.approx((u_mean[3], u_disp[3]))


def test_reference_coefficients_reject_bad_designs():
    rng = np.random.default_rng(2)
    with pytest.raises(ValueError):
        reference_coefficients(rng.normal(size=(3, 2)), rng.normal(size=3))
    constant = np.column_stack([np.ones(50), rng.normal(size=50)])  # collineare con l'intercetta
    with pytest.raises(ValueError):
        reference_coefficients(constant, rng.normal(size=50))


def test_diagnosis_separates_composition_from_structure():
    """Più dispersione perché cambiano le partite: spiegata. Più dispersione sulle stesse partite: non spiegata."""
    rng = np.random.default_rng(3)
    x_ref, d_ref = _world(rng, 380)
    diag = calibrate_reference_diagnosis(x_ref, d_ref, WINDOW, 5, np.random.default_rng(4))
    coef = (diag.median, diag.beta_mean, diag.beta_dispersion)
    rates = {}
    for name, kwargs in (("same", {}), ("composition", {"x_shift": 0.5}), ("structure", {"scale": 1.6}),
                         ("mean_drop", {"drop": 0.6})):
        u_mean, u_disp, c_disp = [], [], []
        for _ in range(400):
            x, d = _world(rng, WINDOW, **kwargs)
            um, ud = unexplained_parts(x, d, *coef)
            u_mean.append(um > diag.mean_threshold)
            u_disp.append(ud > diag.dispersion_threshold)
            c_disp.append(explained_parts(x, x_ref, diag.beta_mean, diag.beta_dispersion)[1])
        rates[name] = (float(np.mean(u_mean)), float(np.mean(u_disp)), float(np.mean(c_disp)))
    # Senza cambiamenti ciascuna parte non spiegata supera la soglia in circa il 2,5% delle finestre
    assert rates["same"][0] < 0.08 and rates["same"][1] < 0.08
    # Cambio di composizione: la dispersione cresce, ma è spiegata dalle covariate
    assert rates["composition"][2] > 0.15
    assert rates["composition"][1] < 0.15
    # Cambio di struttura: la dispersione cresce a parità di covariate, e resta non spiegata
    assert abs(rates["structure"][2]) < 0.03
    assert rates["structure"][1] > 0.6
    # Peggioramento della media a parità di covariate: non spiegato
    assert rates["mean_drop"][0] > 0.8


def test_diagnosis_table_uses_the_part_that_triggered_the_alarm():
    records = [
        {"by_mean": False, "by_dispersion": False, "three_fold": True, "two_fold_mean": False, "two_fold_dispersion": False},
        {"by_mean": True, "by_dispersion": False, "three_fold": False, "two_fold_mean": True, "two_fold_dispersion": False},
        {"by_mean": True, "by_dispersion": False, "three_fold": True, "two_fold_mean": False, "two_fold_dispersion": True},
        {"by_mean": False, "by_dispersion": True, "three_fold": False, "two_fold_mean": True, "two_fold_dispersion": False},
        {"by_mean": True, "by_dispersion": True, "three_fold": True, "two_fold_mean": False, "two_fold_dispersion": True},
    ]
    table = {r["alarm"]: r for r in diagnosis_table(records)}
    assert [table[k]["n_days"] for k in ("none", "mean_only", "dispersion_only", "both")] == [1, 2, 1, 1]
    assert table["mean_only"]["share_structural_two_fold"] == 0.5      # conta solo la parte della media
    assert table["dispersion_only"]["share_structural_two_fold"] == 0.0  # conta solo la parte della dispersione
    assert table["both"]["share_structural_two_fold"] == 1.0
    assert table["none"]["share_structural_three_fold"] == 1.0
