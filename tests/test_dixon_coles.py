"""Test di T59: Dixon-Coles (τ, probabilità, verosimiglianza, recupero dei parametri, walk-forward)."""

import datetime
import math

import numpy as np
import pandas as pd
import pytest

from shk.model.dixon_coles import (
    LOG_RATE_LIMIT,
    MAX_GOALS,
    SIGMA_GRID,
    DixonColesForecaster,
    FitData,
    Prior,
    fit_dixon_coles,
    negative_log_likelihood,
    outcome_probs,
    score_matrix,
    t59_sequences,
    tau,
)
from shk.model.dixon_coles_calibration import choose, new_team_early_mask
from shk.model.elo_predictor import compute_season_standings


def test_tau_matches_dixon_coles_formula():
    """τ nei quattro casi di Dixon e Coles (1997) e 1 altrove."""
    lam, mu, rho = 1.4, 1.1, -0.13
    assert tau(0, 0, lam, mu, rho) == pytest.approx(1.0 - lam * mu * rho, abs=1e-15)
    assert tau(0, 1, lam, mu, rho) == pytest.approx(1.0 + lam * rho, abs=1e-15)
    assert tau(1, 0, lam, mu, rho) == pytest.approx(1.0 + mu * rho, abs=1e-15)
    assert tau(1, 1, lam, mu, rho) == pytest.approx(1.0 - rho, abs=1e-15)
    for x, y in ((2, 0), (0, 2), (1, 2), (2, 1), (3, 3), (5, 0)):
        assert tau(x, y, lam, mu, rho) == 1.0


def test_outcome_probs_sum_to_one():
    """Griglia 0..10 rinormalizzata: punteggi e 1X2 sommano a 1 entro 1e-12."""
    rng = np.random.default_rng(0)
    lam, mu = rng.uniform(0.3, 3.5, 200), rng.uniform(0.3, 3.5, 200)
    for rho in (-0.2, 0.0, 0.15):
        p = score_matrix(lam, mu, rho)
        assert p.shape == (200, MAX_GOALS + 1, MAX_GOALS + 1)
        assert np.all(p >= 0.0)
        assert np.max(np.abs(p.sum(axis=(1, 2)) - 1.0)) <= 1e-12
        q = outcome_probs(lam, mu, rho)
        assert np.max(np.abs(q.sum(axis=1) - 1.0)) <= 1e-12


def test_outcome_probs_without_correction_is_independent_poisson():
    """Con ρ = 0 la griglia è il prodotto di due Poisson troncate e rinormalizzate."""
    lam, mu = np.array([1.3]), np.array([0.9])
    p = score_matrix(lam, mu, 0.0)[0]
    g = np.arange(MAX_GOALS + 1)
    px = np.array([math.exp(-1.3) * 1.3 ** k / math.factorial(k) for k in g])
    py = np.array([math.exp(-0.9) * 0.9 ** k / math.factorial(k) for k in g])
    expected = np.outer(px, py) / np.outer(px, py).sum()
    assert np.max(np.abs(p - expected)) <= 1e-14


def _random_data(rng: np.random.Generator, n_teams: int = 6, n_matches: int = 120) -> FitData:
    home = rng.integers(0, n_teams, n_matches)
    away = (home + rng.integers(1, n_teams, n_matches)) % n_teams
    return FitData(home, away, rng.poisson(1.4, n_matches).astype(float), rng.poisson(1.1, n_matches).astype(float),
                   rng.uniform(0.2, 1.0, n_matches), n_teams)


def test_gradient_matches_finite_differences():
    """Il gradiente analitico (con prior) coincide con le differenze finite centrali."""
    rng = np.random.default_rng(1)
    data = _random_data(rng)
    prior = Prior(np.array([1, 4]), np.array([0.1, -0.2]), np.array([0.05, 0.0]), 0.2)
    theta = np.concatenate([rng.normal(0, 0.2, 12), [0.25, -0.08]])
    value, grad = negative_log_likelihood(theta, data, prior)
    eps = 1e-6
    numeric = np.array([(negative_log_likelihood(theta + eps * e, data, prior)[0]
                         - negative_log_likelihood(theta - eps * e, data, prior)[0]) / (2 * eps)
                        for e in np.eye(theta.size)])
    # Il gradiente di a è proiettato a media nulla (vincolo di somma nulla degli attacchi)
    numeric[:6] -= numeric[:6].mean()
    assert np.max(np.abs(grad - numeric)) < 1e-5
    assert math.isfinite(value)


def _simulate_league(rng: np.random.Generator, n_teams: int = 20, n_seasons: int = 5):
    alpha = rng.normal(0.0, 0.25, n_teams)
    alpha -= alpha.mean()
    beta = rng.normal(0.0, 0.2, n_teams)
    gamma, rho = 0.25, -0.1
    pairs = [(i, j) for i in range(n_teams) for j in range(n_teams) if i != j]
    home = np.array([i for _ in range(n_seasons) for i, _j in pairs])
    away = np.array([j for _ in range(n_seasons) for _i, j in pairs])
    lam = np.exp(alpha[home] + beta[away] + gamma)
    mu = np.exp(alpha[away] + beta[home])
    p = score_matrix(lam, mu, rho).reshape(home.size, -1)
    cells = np.array([rng.choice(p.shape[1], p=row) for row in p])
    data = FitData(home, away, (cells // (MAX_GOALS + 1)).astype(float), (cells % (MAX_GOALS + 1)).astype(float),
                   np.ones(home.size), n_teams)
    return data, np.concatenate([alpha, beta, [gamma, rho]])


def _standard_errors(fit_theta: np.ndarray, data: FitData) -> np.ndarray:
    """Errori standard dall'Hessiana numerica nella parametrizzazione ridotta (α_n = −Σ α_i)."""
    n = data.n_teams

    def full(z):
        return np.concatenate([z[:n - 1], [-z[:n - 1].sum()], z[n - 1:]])

    def grad_reduced(z):
        g = negative_log_likelihood(full(z), data)[1]
        return np.concatenate([g[:n - 1] - g[n - 1], g[n:]])

    z0 = np.concatenate([fit_theta[:n - 1], fit_theta[n:]])
    eps = 1e-5
    hess = np.array([(grad_reduced(z0 + eps * e) - grad_reduced(z0 - eps * e)) / (2 * eps) for e in np.eye(z0.size)])
    cov = np.linalg.inv((hess + hess.T) / 2.0)
    jac = np.zeros((2 * n + 2, z0.size))
    jac[:n - 1, :n - 1] = np.eye(n - 1)
    jac[n - 1, :n - 1] = -1.0
    jac[n:, n - 1:] = np.eye(n + 2)
    return np.sqrt(np.diag(jac @ cov @ jac.T))


def test_parameter_recovery_within_three_standard_errors():
    """20 squadre, 5 stagioni simulate dal modello (seme di S11, figlio 0): stime entro 3 SE."""
    rng = np.random.default_rng(t59_sequences()[0])
    data, true = _simulate_league(rng)
    res = fit_dixon_coles(data)
    assert res.converged
    est = np.concatenate([res.alpha, res.beta, [res.gamma, res.rho]])
    z = (est - true) / _standard_errors(est, data)
    assert abs(res.alpha.sum()) < 1e-10
    assert np.max(np.abs(z)) <= 3.0


def test_fit_is_invariant_to_warm_start():
    """Avvio dalla soluzione precedente o da zero: stessa soluzione (problema convesso in α, β, γ)."""
    rng = np.random.default_rng(2)
    data = _random_data(rng, n_matches=300)
    cold = fit_dixon_coles(data)
    warm = fit_dixon_coles(data, start=np.concatenate([cold.alpha + 0.05, cold.beta - 0.05, [0.1, 0.0]]))
    assert np.max(np.abs(cold.alpha - warm.alpha)) < 1e-4
    assert abs(cold.rho - warm.rho) < 1e-4


def _synthetic_frame(rng: np.random.Generator, seasons: list[list[str]], start_year: int = 2001) -> pd.DataFrame:
    """Campionati a girone doppio, una giornata a settimana, gol Poisson."""
    rows = []
    day = datetime.date(start_year, 8, 1)
    for k, teams in enumerate(seasons):
        label = f"{start_year + k}-{(start_year + k + 1) % 100:02d}"
        n = len(teams)
        order = list(teams)
        rounds = []
        for _ in range(n - 1):
            rounds.append([(order[i], order[n - 1 - i]) for i in range(n // 2)])
            order = [order[0]] + [order[-1]] + order[1:-1]
        rounds += [[(b, a) for a, b in r] for r in rounds]
        for r in rounds:
            for h, a in r:
                hg, ag = int(rng.poisson(1.5)), int(rng.poisson(1.1))
                rows.append({"Date": pd.Timestamp(day), "season": label, "HomeTeam": h, "AwayTeam": a,
                             "FTHG": hg, "FTAG": ag, "FTR": "H" if hg > ag else ("D" if hg == ag else "A")})
            day += datetime.timedelta(days=7)
        day = datetime.date(start_year + k + 1, 8, 1)
    return pd.DataFrame(rows)


class _NonStrictForecaster(DixonColesForecaster):
    """Mutante: storia con Date <= data di previsione (anteriorità non stretta)."""

    def history_rows(self, decision_day: int) -> np.ndarray:
        return super().history_rows(decision_day + 1)


@pytest.mark.parametrize("sigma", [0.2, math.inf])
def test_future_outcomes_do_not_change_predictions(sigma):
    """Alterare gli esiti delle partite con Date >= d non cambia le previsioni a d; il mutante sì."""
    rng = np.random.default_rng(3)
    teams = [f"T{i}" for i in range(6)]
    df = _synthetic_frame(rng, [teams, teams, teams])
    season = df["season"].iloc[-1]
    days = sorted(df.loc[df["season"] == season, "Date"].unique())
    cut = days[4]
    altered = df.copy()
    future = altered["Date"] >= cut
    altered.loc[future, "FTHG"] = 0
    altered.loc[future, "FTAG"] = 5
    altered.loc[future, "FTR"] = "A"
    probs = ["p_home", "p_draw", "p_away"]
    for cls, should_match in ((DixonColesForecaster, True), (_NonStrictForecaster, False)):
        base = cls(df, 0.003, sigma).predict_season(season)
        alt = cls(altered, 0.003, sigma).predict_season(season)
        upto = (base["Date"] <= cut).to_numpy()
        same = np.array_equal(base.loc[upto, probs].to_numpy(), alt.loc[upto, probs].to_numpy())
        assert same is should_match


def test_entry_values_of_promoted_teams():
    """Mai vista: media delle ultime tre della stagione precedente; tornante: ultimi parametri."""
    rng = np.random.default_rng(4)
    s1 = [f"T{i}" for i in range(6)]
    s2 = s1[:5] + ["N1"]
    s3 = ["T0", "T1", "T2", "T3", "N1", "T5"]
    df = _synthetic_frame(rng, [s1, s2, s3])
    fc = DixonColesForecaster(df, 0.003, 0.2)
    teams = list(fc._m.teams)
    second = df["season"].unique()[1]
    first_day = int(fc._m.day[np.flatnonzero(fc._m.season == second)].min())
    start_state, _ = fc._fit(first_day)
    entry = fc._entry_values(second, start_state)
    bottom = compute_season_standings(df[df["season"] == df["season"].unique()[0]])["team"].tolist()[-3:]
    idx = [teams.index(t) for t in bottom]
    assert set(entry) == {teams.index("N1")}
    a0, b0 = entry[teams.index("N1")]
    assert a0 == pytest.approx(float(np.mean(start_state.alpha[idx])), abs=1e-15)
    assert b0 == pytest.approx(float(np.mean(start_state.beta[idx])), abs=1e-15)
    # T5 torna nella terza stagione: con peso ancora sufficiente usa i parametri d'inizio stagione
    third = df["season"].unique()[2]
    third_day = int(fc._m.day[np.flatnonzero(fc._m.season == third)].min())
    state3, _ = fc._fit(third_day)
    entry3 = fc._entry_values(third, state3)
    t5 = teams.index("T5")
    assert set(entry3) == {t5}
    assert entry3[t5] == (float(state3.alpha[t5]), float(state3.beta[t5]))


def test_new_team_first_match_uses_entry_value_with_infinite_sigma():
    """Con σ = ∞ la prima partita di una mai vista usa il valore d'ingresso (imposto)."""
    rng = np.random.default_rng(5)
    s1 = [f"T{i}" for i in range(6)]
    s2 = s1[:5] + ["N1"]
    df = _synthetic_frame(rng, [s1, s1, s2])
    fc = DixonColesForecaster(df, 0.003, math.inf)
    season = df["season"].unique()[2]
    pred = fc.predict_season(season)
    assert np.isfinite(pred[["p_home", "p_draw", "p_away"]].to_numpy()).all()
    assert np.allclose(pred[["p_home", "p_draw", "p_away"]].sum(axis=1), 1.0, atol=1e-12)


def test_choose_prefers_larger_sigma_then_smaller_xi_on_ties():
    """Parità entro 1e-12: σ maggiore, poi ξ minore; altrimenti il minimo."""
    combos = [(0.0, 0.1), (0.0, math.inf), (0.001, math.inf), (0.001, 0.2)]
    assert choose([1.0, 1.0, 1.0, 1.1], combos) == 1
    assert choose([1.0, 1.0 + 5e-13, 0.9, 1.1], combos) == 2
    assert choose([0.8, 1.0, 1.0, 1.1], combos) == 0


def test_new_team_early_mask_uses_first_matchdays():
    """Partite di una mai vista nei primi matchday (blocchi di 10 partite nell'ordine della stagione)."""
    n = 30
    home = ["N" if i in (3, 15, 25) else f"H{i}" for i in range(n)]
    away = ["N" if i == 9 else f"A{i}" for i in range(n)]
    preds = pd.DataFrame({"season": ["2001-02"] * n, "HomeTeam": home, "AwayTeam": away})
    status = {("2001-02", "N"): "new"}
    assert np.flatnonzero(new_team_early_mask(preds, status, n_matchdays=1)).tolist() == [3, 9]
    assert np.flatnonzero(new_team_early_mask(preds, status, n_matchdays=2)).tolist() == [3, 9, 15]
    assert np.flatnonzero(new_team_early_mask(preds, status, n_matchdays=10)).tolist() == [3, 9, 15, 25]


def _never_seen_parameters(sigma: float, case: str, n_played: int) -> tuple[float, float]:
    """α e β di una mai vista al fit successivo alle sue prime n_played partite.

    Nelle prime n_played partite della mai vista N1 i suoi gol fatti (case "zero_scored") o i
    suoi gol subiti (case "zero_conceded") sono 0. Il fit è quello che predict_season usa alla
    prima data successiva: inizio stagione, valori d'ingresso, prior con σ.
    """
    rng = np.random.default_rng(6)
    s1 = [f"T{i}" for i in range(6)]
    df = _synthetic_frame(rng, [s1, s1, s1[:5] + ["N1"]])
    season = df["season"].unique()[2]
    played = df.index[(df["season"] == season) & ((df["HomeTeam"] == "N1") | (df["AwayTeam"] == "N1"))][:n_played]
    for i in played:
        n1_home = df.at[i, "HomeTeam"] == "N1"
        scored, conceded = ("FTHG", "FTAG") if n1_home else ("FTAG", "FTHG")
        df.at[i, scored if case == "zero_scored" else conceded] = 0
        hg, ag = df.at[i, "FTHG"], df.at[i, "FTAG"]
        df.at[i, "FTR"] = "H" if hg > ag else ("D" if hg == ag else "A")
    fc = DixonColesForecaster(df, 0.003, sigma)
    m = fc._m
    days = np.unique(m.day[m.season == season])
    start, _ = fc._fit(int(days[0]))
    entry = fc._entry_values(season, start)
    decision = int(days[days > m.day[played[-1]]][0])
    extra = entry.keys() if math.isfinite(sigma) else ()
    state, _ = fc._fit(decision, extra_teams=extra, prior_values=entry, warm=start)
    team = m.teams.index("N1")
    return float(state.alpha[team]), float(state.beta[team])


@pytest.mark.parametrize("n_played", [1, 3])
@pytest.mark.parametrize("case", ["zero_scored", "zero_conceded"])
@pytest.mark.parametrize("sigma", SIGMA_GRID)
def test_never_seen_team_parameters_exist_for_every_grid_sigma(sigma, case, n_played):
    """Stimatore definito per una mai vista con 0 gol fatti o subiti: α e β finiti e lontani dai limiti.

    Margine: |α| e |β| sotto metà di LOG_RATE_LIMIT, il limite dei log-tassi nell'ottimizzazione.
    Con σ = ∞ (massima verosimiglianza pura) la stima diverge e il test fallisce: per questo σ = ∞
    è escluso dalla griglia (decisione del programmatore del 2026-10-12).
    """
    alpha, beta = _never_seen_parameters(sigma, case, n_played)
    assert math.isfinite(alpha) and math.isfinite(beta)
    assert abs(alpha) < LOG_RATE_LIMIT / 2
    assert abs(beta) < LOG_RATE_LIMIT / 2
