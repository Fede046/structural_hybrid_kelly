"""Test del Modulo 3 (T51): λ*, stime di σ_p, candidate e regole comuni."""

import math

import numpy as np
import pytest

from shk.model.module3 import (
    CANDIDATES,
    INACTIVE_LAMBDA,
    WindowData,
    candidate_lambda,
    delta_dispersion_sigma2,
    lambda_star,
    selected_sd,
    structural_inflation,
)
from shk.model.module3_synthetic import (
    REGIMES,
    _window,
    choose_candidate,
    generate_season,
    season_lambdas,
    trap_comparison,
)


def test_lambda_star_matches_monte_carlo_and_limits():
    """λ* = E[c]/E[c²] col troncamento coincide con la media Monte Carlo; limiti e casi degeneri."""
    rng = np.random.default_rng(1)
    for mu, s in ((0.05, 0.0375), (0.02, 0.03), (0.04, 0.01)):
        x = rng.normal(mu, s, 2_000_000)
        c = np.maximum(x, 0.0) / mu
        assert math.isclose(float(lambda_star(mu, s)), float(c.mean() / (c**2).mean()), rel_tol=5e-3)
    # Senza troncamento rilevante coincide con 1/(1 + Var(c))
    assert math.isclose(float(lambda_star(0.05, 0.005)), 1.0 / (1.0 + 0.01), rel_tol=1e-6)
    assert lambda_star(-0.01, 0.02) == 0.0 and lambda_star(0.0, 0.02) == 0.0
    assert lambda_star(0.03, 0.0) == 1.0
    values = lambda_star(np.linspace(-0.1, 0.2, 50), np.linspace(0.0, 0.2, 50))
    assert np.all((values >= 0.0) & (values <= 1.0))


def test_delta_dispersion_recovers_sigma_p():
    """La dispersione di δ ricostruisce σ_p con p̂ = p + ε, a 2 esiti (anche con c medio < 0) e a 3."""
    rng = np.random.default_rng(2)
    n = 400_000
    # Il caso a quota 3.4 ha c medio negativo: il primo ordine dava 0
    for sigma_p, cats in ((0.04, [1.8, 2.1, 2.6, 3.4]), (0.03, [3.4])):
        odds = rng.choice(cats, size=n)
        p = 1.02 / odds
        p_hat = p + rng.normal(0.0, sigma_p, n)
        q0 = (1.0 / odds) / 1.05
        win = rng.random(n) < p
        w = WindowData(np.column_stack([p_hat, 1 - p_hat]), np.column_stack([q0, 1 - q0]),
                       np.where(win, 0, 1), p_hat * odds - 1)
        est = selected_sd(delta_dispersion_sigma2(w), 2)
        assert abs(est - sigma_p) < 0.1 * sigma_p
    # Tre esiti con ε = P z a somma nulla (σ_p piccola: p̂ resta in (0, 1))
    sigma_p = 0.02
    base = np.array([[0.45, 0.28, 0.27], [0.25, 0.27, 0.48], [0.60, 0.22, 0.18]])
    p = base[rng.integers(3, size=n)]
    z = rng.normal(0.0, sigma_p / math.sqrt(2.0 / 3.0), (n, 3))
    p_hat = p + z - z.mean(axis=1, keepdims=True)
    q = p * np.array([1.0, 0.95, 1.05])
    q = q / q.sum(axis=1, keepdims=True)
    y = (rng.random(n)[:, None] > np.cumsum(p, axis=1)).sum(axis=1)
    est = selected_sd(delta_dispersion_sigma2(WindowData(p_hat, q, y, np.zeros(n))), 3)
    assert abs(est - sigma_p) < 0.1 * sigma_p


def test_structural_inflation_sign_and_scale():
    """Nessun gonfiamento con S >= 0; con S < 0 vale −S/h."""
    p = np.array([[0.5, 0.5], [0.4, 0.6]])
    assert structural_inflation(0.01, p) == 0.0
    h = float(np.mean(0.25 * (1 / p).sum(axis=1)))
    assert math.isclose(structural_inflation(-0.02, p), 0.02 / h)


def _windows(g_hat_positive: bool):
    rng = np.random.default_rng(3)
    season = generate_season("i_stationary" if g_hat_positive else "iii_structural", rng)
    idx_a, idx_b = np.arange(100, 180), np.arange(300, 380)
    return season, _window(season, idx_a), _window(season, idx_b)


def test_common_rules():
    """λ in [0, 1]; 0 se ĝ della finestra B <= 0; 0.25 se non attivo."""
    odds = np.array([2.1, 3.4])
    ev = np.array([0.03, 0.05])
    for c in CANDIDATES:
        assert np.all(candidate_lambda(c, False, None, None, 0.0, odds, ev) == INACTIVE_LAMBDA)
    rng = np.random.default_rng(4)
    for _ in range(30):
        season = generate_season(REGIMES[rng.integers(4)], rng)
        wa, wb = _window(season, np.arange(100, 180)), _window(season, np.arange(300, 380))
        g_b = float(np.mean(np.log(wb.p_hat[np.arange(80), wb.outcome]) - np.log(wb.q[np.arange(80), wb.outcome])))
        for c in CANDIDATES:
            lam = candidate_lambda(c, True, wa, wb, -0.01, odds, ev)
            assert np.all((lam >= 0.0) & (lam <= 1.0))
            if g_b <= 0.0:
                assert np.all(lam == 0.0)
    # Una finestra B con ĝ <= 0 per costruzione: q = p̂ dà δ = 0
    wb0 = WindowData(wb.p_hat, wb.p_hat, wb.outcome, wb.ev_candidate)
    for c in CANDIDATES:
        assert np.all(candidate_lambda(c, True, wa, wb0, 0.0, odds, ev) == 0.0)


def test_choice_rule_minimum_excluding_p1_and_ties():
    """Vince il minimo dell'MSE medio fra P2 e P3; a parità quella con meno quantità stimate."""
    assert choose_candidate([{"P1": 0.0, "P2": 0.2, "P3": 0.1}, {"P1": 0.0, "P2": 0.2, "P3": 0.1}]) == "P3"
    assert choose_candidate([{"P1": 0.0, "P2": 0.1, "P3": 0.1 + 1e-13}]) == "P2"
    assert choose_candidate([{"P1": 0.0, "P2": 0.3, "P3": 0.1}]) == "P3"


def test_season_lambdas_shapes():
    rng = np.random.default_rng(5)
    season = generate_season("iv_both", rng)
    lam = season_lambdas(season, 80)
    for key in ("C0", "C1", *CANDIDATES):
        assert lam[key].shape == (380,)
        assert np.all((lam[key] >= 0.0) & (lam[key] <= 1.0))
    assert np.all(lam["P2"][:160] == INACTIVE_LAMBDA)


def test_trap_p2_dominates_p1():
    """Trappola della nota 3.2 §7.5 (vincolante): P2 domina P1 in crescita mediana e drawdown medio."""
    res = trap_comparison(np.random.default_rng(20261013), n_replicas=400)
    assert res["P2"][0] > res["P1"][0]
    assert res["P2"][1] < res["P1"][1]
