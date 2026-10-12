"""Modulo 1 Dixon-Coles walk-forward (T59, US-C9.1; nota 2.8 §5).

Modello (Dixon e Coles, 1997): gol della squadra di casa X ~ Poisson(λ), della squadra in
trasferta Y ~ Poisson(μ), con ln λ = α_casa + β_trasferta + γ e ln μ = α_trasferta + β_casa
(α attacco, β difesa nella scala logaritmica del tasso di gol, γ vantaggio casalingo), e
P(X = x, Y = y) = τ(x, y)·Pois(x; λ)·Pois(y; μ) con la correzione
τ(0,0) = 1 − λμρ, τ(0,1) = 1 + λρ, τ(1,0) = 1 + μρ, τ(1,1) = 1 − ρ, τ = 1 altrove.
Vincolo di identificabilità: somma nulla degli attacchi delle squadre del fit, imposto
dentro l'ottimizzazione (α = a − mean(a)).

Stima: massima verosimiglianza pesata, ℓ = Σ_k φ_k ln P_k con φ_k = exp(−ξ·t_k), t_k giorni
fra la partita e la data di valutazione; partite con peso < WEIGHT_TRUNCATION escluse.
ρ limitato a RHO_BOUNDS. Nella verosimiglianza ln τ è sostituito, sotto TAU_FLOOR, dalla sua
prosecuzione lineare (ln ε + (τ − ε)/ε, valore e derivata continui): l'ammissibilità τ > 0
non può bloccare la stima per partite con peso minimo e parametri poco identificati, che
non contano per le previsioni. L-BFGS-B con gradiente analitico, avvio dalla soluzione della
data precedente.

Neopromosse (decisioni S4/S11 e del programmatore del 2026-10-12): ogni squadra alla prima
stagione dopo l'ingresso, mai vista o tornante, ha un valore d'ingresso (α₀, β₀):
- mai vista: media dei parametri delle ultime tre della classifica della stagione precedente,
  stimati a inizio stagione;
- tornante: ultimi parametri stimati, cioè quelli del fit di inizio stagione se la squadra ha
  ancora partite con peso sufficiente, altrimenti quelli di un fit alla fine della sua ultima
  stagione.
Per tutta quella stagione la verosimiglianza ha un prior gaussiano su α e β della squadra,
centrato su (α₀, β₀) con deviazione standard σ (uguale per attacco e difesa); γ e ρ senza
prior. σ = ∞ è la massima verosimiglianza pura: il previsore la accetta, ma è esclusa dalla
griglia (decisione del programmatore del 2026-10-12), perché per una squadra senza storia lo
stimatore non esiste se nelle prime partite fa 0 gol (l'attacco diverge) o ne subisce 0 (la
difesa diverge). Prima della prima partita di una mai vista la previsione usa il valore
d'ingresso (con σ finito è automatico, con σ = ∞ è imposto).

Probabilità 1X2 dalla griglia dei punteggi 0..MAX_GOALS per squadra, rinormalizzata.
ξ e σ si calibrano sul training con lo schema espansivo dell'Elo (obiettivo: log-loss media
sulle partite di training del fit, previsioni walk-forward); i valori scelti stanno in DC_FITS.
"""

import math
from collections.abc import Collection, Sequence
from typing import Final, NamedTuple

import numpy as np
import pandas as pd
import scipy.optimize
import scipy.special

from shk.data.walkforward import LeakageError, assert_no_leakage, walkforward_split
from shk.model.elo_fit import parse_season_start_year
from shk.model.elo_predictor import compute_season_standings
from shk.model.module2_data import STATUS_NEW, STATUS_RETURNING, entry_status_by_team_season

SEED_S11: Final[int] = 20261015
T59_STORY_POSITION: Final[int] = 0
MAX_GOALS: Final[int] = 10
WEIGHT_TRUNCATION: Final[float] = 1e-4
XI_GRID: Final[tuple[float, ...]] = (0.0, 0.0005, 0.001, 0.0019, 0.003, 0.005)
SIGMA_GRID: Final[tuple[float, ...]] = (0.1, 0.2, 0.4)
RHO_BOUNDS: Final[tuple[float, float]] = (-0.25, 0.25)
TAU_FLOOR: Final[float] = 1e-3
MAX_ITER: Final[int] = 2000
LOG_RATE_LIMIT: Final[float] = 10.0


def t59_sequences(seed: int = SEED_S11) -> list[np.random.SeedSequence]:
    """Figli di SeedSequence(SEED_S11).spawn(5)[0] (T59 in posizione 0 di S11): 0 recupero dei
    parametri su dati simulati, 1 campione del controllo anti-leakage."""
    return np.random.SeedSequence(seed).spawn(5)[T59_STORY_POSITION].spawn(2)


def tau(x: np.ndarray, y: np.ndarray, lam: np.ndarray, mu: np.ndarray, rho: float) -> np.ndarray:
    """Correzione τ di Dixon-Coles per i punteggi (x, y)."""
    x, y = np.asarray(x), np.asarray(y)
    out = np.ones(np.broadcast(x, y, lam, mu).shape)
    out = np.where((x == 0) & (y == 0), 1.0 - lam * mu * rho, out)
    out = np.where((x == 0) & (y == 1), 1.0 + lam * rho, out)
    out = np.where((x == 1) & (y == 0), 1.0 + mu * rho, out)
    out = np.where((x == 1) & (y == 1), 1.0 - rho, out)
    return out


def score_matrix(lam: np.ndarray, mu: np.ndarray, rho: float, max_goals: int = MAX_GOALS) -> np.ndarray:
    """Probabilità dei punteggi (n, max_goals + 1, max_goals + 1), troncate e rinormalizzate."""
    lam = np.atleast_1d(np.asarray(lam, dtype=np.float64))
    mu = np.atleast_1d(np.asarray(mu, dtype=np.float64))
    g = np.arange(max_goals + 1)
    px = np.exp(g[None, :] * np.log(lam[:, None]) - lam[:, None] - scipy.special.gammaln(g + 1)[None, :])
    py = np.exp(g[None, :] * np.log(mu[:, None]) - mu[:, None] - scipy.special.gammaln(g + 1)[None, :])
    p = px[:, :, None] * py[:, None, :]
    xx, yy = np.meshgrid(g, g, indexing="ij")
    p = p * np.maximum(tau(xx[None], yy[None], lam[:, None, None], mu[:, None, None], rho), 0.0)
    return p / p.sum(axis=(1, 2), keepdims=True)


def outcome_probs(lam: np.ndarray, mu: np.ndarray, rho: float, max_goals: int = MAX_GOALS) -> np.ndarray:
    """Probabilità 1X2 (n, 3): casa, pareggio, trasferta."""
    p = score_matrix(lam, mu, rho, max_goals)
    g = np.arange(max_goals + 1)
    xx, yy = np.meshgrid(g, g, indexing="ij")
    return np.stack([p[:, xx > yy].sum(axis=1), p[:, xx == yy].sum(axis=1), p[:, xx < yy].sum(axis=1)], axis=1)


class DixonColesFitParams(NamedTuple):
    """Parametri calibrati di un fit: decadimento ξ al giorno e σ del prior delle neopromosse."""

    xi: float
    sigma: float


# Parametri congelati della calibrazione US-C9.1 (calibrati il 2026-10-12, T59). Aggiornati lo
# stesso giorno con la griglia σ senza ∞ (decisione del programmatore): cambia solo il fit 2000-01,
# prima (ξ 0.001, σ ∞)
DC_FITS: Final[dict[str, DixonColesFitParams]] = {
    "2000-01": DixonColesFitParams(xi=0.001, sigma=0.4),
    "2010-11": DixonColesFitParams(xi=0.001, sigma=0.4),
    "2020-21": DixonColesFitParams(xi=0.0019, sigma=0.4),
}


class FitData(NamedTuple):
    """Partite di un fit con indici locali delle squadre."""

    home: np.ndarray
    away: np.ndarray
    hg: np.ndarray
    ag: np.ndarray
    weight: np.ndarray
    n_teams: int


class Prior(NamedTuple):
    """Prior gaussiano su α e β di alcune squadre (indici locali)."""

    teams: np.ndarray
    alpha0: np.ndarray
    beta0: np.ndarray
    sigma: float


def negative_log_likelihood(theta: np.ndarray, data: FitData, prior: Prior | None = None) -> tuple[float, np.ndarray]:
    """−ℓ pesata (senza le costanti ln x! e ln y!) più il prior, e il suo gradiente.

    theta = (a [n], β [n], γ, ρ), con α = a − mean(a).
    """
    n = data.n_teams
    a, beta, gamma, rho = theta[:n], theta[n:2 * n], theta[2 * n], theta[2 * n + 1]
    alpha = a - a.mean()
    # Esponenti limitati a ±LOG_RATE_LIMIT: solo i passi estremi della ricerca di linea li toccano
    log_lam = np.clip(alpha[data.home] + beta[data.away] + gamma, -LOG_RATE_LIMIT, LOG_RATE_LIMIT)
    log_mu = np.clip(alpha[data.away] + beta[data.home], -LOG_RATE_LIMIT, LOG_RATE_LIMIT)
    lam, mu = np.exp(log_lam), np.exp(log_mu)
    x, y, w = data.hg, data.ag, data.weight
    t = tau(x, y, lam, mu, rho)
    low = t < TAU_FLOOR
    t_safe = np.where(low, TAU_FLOOR, t)
    log_t = np.where(low, math.log(TAU_FLOOR) + (t - TAU_FLOOR) / TAU_FLOOR, np.log(t_safe))
    ll = w * (x * log_lam - lam + y * log_mu - mu + log_t)
    # Derivate di ln τ rispetto a λ, μ e ρ
    c00, c01, c10, c11 = (x == 0) & (y == 0), (x == 0) & (y == 1), (x == 1) & (y == 0), (x == 1) & (y == 1)
    dt_lam = np.where(c00, -mu * rho, 0.0) + np.where(c01, rho, 0.0)
    dt_mu = np.where(c00, -lam * rho, 0.0) + np.where(c10, rho, 0.0)
    dt_rho = np.where(c00, -lam * mu, 0.0) + np.where(c01, lam, 0.0) + np.where(c10, mu, 0.0) + np.where(c11, -1.0, 0.0)
    g_loglam = w * (x - lam + lam * dt_lam / t_safe)
    g_logmu = w * (y - mu + mu * dt_mu / t_safe)
    g_rho = float((w * dt_rho / t_safe).sum())
    g_alpha = np.bincount(data.home, g_loglam, n) + np.bincount(data.away, g_logmu, n)
    g_beta = np.bincount(data.away, g_loglam, n) + np.bincount(data.home, g_logmu, n)
    g_gamma = float(g_loglam.sum())
    value = -float(ll.sum())
    grad_alpha, grad_beta = -g_alpha, -g_beta
    if prior is not None and math.isfinite(prior.sigma) and prior.teams.size:
        s2 = prior.sigma ** 2
        da = alpha[prior.teams] - prior.alpha0
        db = beta[prior.teams] - prior.beta0
        value += float((da ** 2).sum() + (db ** 2).sum()) / (2.0 * s2)
        grad_alpha = grad_alpha.copy()
        grad_beta = grad_beta.copy()
        np.add.at(grad_alpha, prior.teams, da / s2)
        np.add.at(grad_beta, prior.teams, db / s2)
    grad_a = grad_alpha - grad_alpha.mean()
    grad = np.concatenate([grad_a, grad_beta, [-g_gamma, -g_rho]])
    return value, grad


class FitResult(NamedTuple):
    """Esito di un fit: parametri (α centrato), convergenza e iterazioni."""

    alpha: np.ndarray
    beta: np.ndarray
    gamma: float
    rho: float
    converged: bool
    n_iter: int


def fit_dixon_coles(data: FitData, start: np.ndarray | None = None, prior: Prior | None = None) -> FitResult:
    """Massima verosimiglianza pesata (penalizzata dal prior) con L-BFGS-B."""
    n = data.n_teams
    x0 = np.zeros(2 * n + 2) if start is None else np.asarray(start, dtype=np.float64).copy()
    bounds = [(None, None)] * (2 * n + 1) + [RHO_BOUNDS]
    res = scipy.optimize.minimize(negative_log_likelihood, x0, args=(data, prior), jac=True, method="L-BFGS-B",
                                  bounds=bounds, options={"maxiter": MAX_ITER})
    a = res.x[:n]
    return FitResult(a - a.mean(), res.x[n:2 * n].copy(), float(res.x[2 * n]), float(res.x[2 * n + 1]),
                     bool(res.success), int(res.nit))


def _theta(alpha: np.ndarray, beta: np.ndarray, gamma: float, rho: float) -> np.ndarray:
    return np.concatenate([alpha, beta, [gamma, rho]])


class MatchArrays(NamedTuple):
    """Partite del DataFrame ordinate per Date, con indici globali delle squadre."""

    teams: tuple[str, ...]
    day: np.ndarray
    home: np.ndarray
    away: np.ndarray
    hg: np.ndarray
    ag: np.ndarray
    season: np.ndarray


def match_arrays(df: pd.DataFrame) -> MatchArrays:
    """Array del DataFrame (che deve essere ordinato per Date)."""
    teams = tuple(sorted(set(df["HomeTeam"]) | set(df["AwayTeam"])))
    index = {t: i for i, t in enumerate(teams)}
    day = (pd.to_datetime(df["Date"]).to_numpy(dtype="datetime64[D]").astype(np.int64))
    return MatchArrays(teams, day, df["HomeTeam"].map(index).to_numpy(np.int64),
                       df["AwayTeam"].map(index).to_numpy(np.int64), df["FTHG"].to_numpy(np.int64),
                       df["FTAG"].to_numpy(np.int64), df["season"].astype(str).to_numpy())


class State(NamedTuple):
    """Parametri correnti per squadra globale (NaN se assente) più γ e ρ."""

    alpha: np.ndarray
    beta: np.ndarray
    gamma: float
    rho: float


class WalkForwardStats(NamedTuple):
    """Diagnostica del previsore."""

    n_fits: int
    n_not_converged: int
    max_iter: int


class DixonColesForecaster:
    """Previsore walk-forward Dixon-Coles con ξ e σ dati (vedi modulo).

    Parametri
    ---------
    df : pd.DataFrame
        Partite con Date, season, HomeTeam, AwayTeam, FTHG, FTAG, ordinate per Date; solo
        stagioni di storia, training e validazione (il test solo dopo lo sblocco).
    xi : float
        Tasso di decadimento dei pesi al giorno.
    sigma : float
        Deviazione standard del prior delle neopromosse (math.inf: nessun prior).
    """

    def __init__(self, df: pd.DataFrame, xi: float, sigma: float) -> None:
        if not pd.to_datetime(df["Date"]).is_monotonic_increasing:
            raise ValueError("df must be sorted by Date")
        self._df = df.reset_index(drop=True)
        self._m = match_arrays(self._df)
        self._xi = float(xi)
        self._sigma = float(sigma)
        self._status = entry_status_by_team_season(self._df)
        self._seasons = sorted(set(self._m.season.tolist()), key=parse_season_start_year)
        self._n_fits = self._n_bad = self._max_iter = 0
        self._last_params: dict[int, tuple[float, float]] = {}

    @property
    def frame(self) -> pd.DataFrame:
        """Il DataFrame delle partite (indice posizionale)."""
        return self._df

    @property
    def stats(self) -> WalkForwardStats:
        """Fit eseguiti, mancate convergenze, iterazioni massime."""
        return WalkForwardStats(self._n_fits, self._n_bad, self._max_iter)

    def history_rows(self, decision_day: int) -> np.ndarray:
        """Indici delle partite usate a una data: Date strettamente anteriore e peso >= soglia."""
        end = int(np.searchsorted(self._m.day, decision_day, side="left"))
        if self._xi > 0.0:
            horizon = math.log(1.0 / WEIGHT_TRUNCATION) / self._xi
            start = int(np.searchsorted(self._m.day, decision_day - horizon, side="left"))
        else:
            start = 0
        return np.arange(start, end)

    def _fit(self, decision_day: int, extra_teams: Collection[int] = (), prior_values: dict[int, tuple[float, float]]
             | None = None, warm: State | None = None) -> tuple[State, np.ndarray]:
        rows = self.history_rows(decision_day)
        m = self._m
        present = set(m.home[rows].tolist()) | set(m.away[rows].tolist())
        teams = np.array(sorted(present | set(extra_teams)), dtype=np.int64)
        local = {int(t): i for i, t in enumerate(teams)}
        weight = np.exp(-self._xi * (decision_day - m.day[rows]))
        data = FitData(np.searchsorted(teams, m.home[rows]), np.searchsorted(teams, m.away[rows]),
                       m.hg[rows].astype(np.float64), m.ag[rows].astype(np.float64), weight, teams.size)
        prior = None
        if prior_values and math.isfinite(self._sigma):
            ids = [t for t in prior_values if t in local]
            prior = Prior(np.array([local[t] for t in ids], dtype=np.int64),
                          np.array([prior_values[t][0] for t in ids]), np.array([prior_values[t][1] for t in ids]),
                          self._sigma)
        start = None
        if warm is not None:
            a0 = np.nan_to_num(warm.alpha[teams], nan=0.0)
            b0 = np.nan_to_num(warm.beta[teams], nan=0.0)
            if prior_values:
                for t, (pa, pb) in prior_values.items():
                    if t in local and math.isnan(warm.alpha[t]):
                        a0[local[t]], b0[local[t]] = pa, pb
            start = _theta(a0, b0, warm.gamma, warm.rho)
        res = fit_dixon_coles(data, start, prior)
        self._n_fits += 1
        self._n_bad += int(not res.converged)
        self._max_iter = max(self._max_iter, res.n_iter)
        alpha = np.full(len(m.teams), np.nan)
        beta = np.full(len(m.teams), np.nan)
        alpha[teams], beta[teams] = res.alpha, res.beta
        return State(alpha, beta, res.gamma, res.rho), teams

    def _entry_values(self, season: str, start_state: State) -> dict[int, tuple[float, float]]:
        """Valori d'ingresso delle neopromosse della stagione (vedi modulo)."""
        m = self._m
        index = {t: i for i, t in enumerate(m.teams)}
        rows_s = np.flatnonzero(m.season == season)
        teams_s = set(m.home[rows_s].tolist()) | set(m.away[rows_s].tolist())
        promoted = {t for t in teams_s if self._status.get((season, m.teams[t])) in (STATUS_NEW, STATUS_RETURNING)}
        if not promoted:
            return {}
        k = self._seasons.index(season)
        prev = self._seasons[k - 1]
        prev_df = self._df[self._df["season"] == prev]
        bottom = [index[t] for t in compute_season_standings(prev_df)["team"].tolist()[-3:]]
        new_value = (float(np.nanmean(start_state.alpha[bottom])), float(np.nanmean(start_state.beta[bottom])))
        out = {}
        for t in promoted:
            if self._status[(season, m.teams[t])] == STATUS_NEW:
                out[t] = new_value
            elif not math.isnan(start_state.alpha[t]):
                out[t] = (float(start_state.alpha[t]), float(start_state.beta[t]))
            else:
                out[t] = self._last_known(t)
        return out

    def _last_known(self, team: int) -> tuple[float, float]:
        """Parametri della squadra alla fine della sua ultima stagione giocata (fit dedicato)."""
        if team in self._last_params:
            return self._last_params[team]
        m = self._m
        rows = np.flatnonzero((m.home == team) | (m.away == team))
        last_day = int(m.day[rows].max()) + 1
        state, _ = self._fit(last_day)
        value = (float(state.alpha[team]), float(state.beta[team]))
        self._last_params[team] = value
        return value

    def predict_season(self, season: str) -> pd.DataFrame:
        """Previsioni walk-forward delle partite della stagione (stesso ordine del DataFrame)."""
        m = self._m
        rows_s = np.flatnonzero(m.season == season)
        if rows_s.size == 0:
            raise ValueError(f"Season {season} not in data")
        days = np.unique(m.day[rows_s])
        start_state, _ = self._fit(int(days[0]))
        entry = self._entry_values(season, start_state)
        warm = start_state
        probs = np.empty((rows_s.size, 3))
        pos = {int(r): i for i, r in enumerate(rows_s)}
        # Con σ = ∞ le neopromosse senza partite restano fuori dal fit e usano il valore d'ingresso
        extra = entry.keys() if math.isfinite(self._sigma) else ()
        for d in days:
            state, _ = self._fit(int(d), extra_teams=extra, prior_values=entry, warm=warm)
            today = rows_s[m.day[rows_s] == d]
            alpha, beta = state.alpha.copy(), state.beta.copy()
            for t, (pa, pb) in entry.items():
                if math.isnan(alpha[t]):
                    alpha[t], beta[t] = pa, pb
            lam = np.exp(alpha[m.home[today]] + beta[m.away[today]] + state.gamma)
            mu = np.exp(alpha[m.away[today]] + beta[m.home[today]])
            p = outcome_probs(lam, mu, state.rho)
            for r, row_p in zip(today, p):
                probs[pos[int(r)]] = row_p
            warm = state
        out = self._df.iloc[rows_s][["season", "Date", "HomeTeam", "AwayTeam", "FTR"]].copy()
        out[["p_home", "p_draw", "p_away"]] = probs
        return out.reset_index(drop=True)


def log_loss(pred: pd.DataFrame) -> np.ndarray:
    """Log-loss per partita delle previsioni (colonne p_home, p_draw, p_away, FTR)."""
    y = pred["FTR"].map({"H": 0, "D": 1, "A": 2}).to_numpy()
    p = pred[["p_home", "p_draw", "p_away"]].to_numpy()
    return -np.log(p[np.arange(y.size), y])


class LeakageCheck(NamedTuple):
    """Esito del controllo anti-leakage sul campione di partite del fornitore."""

    n_checked: int
    n_violations: int
    n_outside_provider: int


def provider_leakage_check(forecaster: DixonColesForecaster, seasons: Sequence[str], sample_size: int,
                           rng: np.random.Generator) -> LeakageCheck:
    """Controlla la storia usata dal previsore su un campione di partite passate dal fornitore.

    Per ogni partita campionata fra quelle che walkforward_split restituisce per le stagioni date,
    la storia del previsore alla sua data deve superare assert_no_leakage ed essere contenuta
    nella storia del fornitore (Date strettamente anteriore).
    """
    df = forecaster.frame
    candidates = np.flatnonzero(df["season"].isin(list(seasons)).to_numpy())
    if sample_size > candidates.size:
        raise ValueError(f"sample_size {sample_size} exceeds the {candidates.size} candidate matches")
    chosen = set(rng.choice(candidates, size=sample_size, replace=False).tolist())
    day = forecaster._m.day
    n_checked = n_violations = n_outside = 0
    for history, match in walkforward_split(df, list(seasons)):
        i = int(match.name)
        if i not in chosen:
            continue
        rows = forecaster.history_rows(int(day[i]))
        n_checked += 1
        try:
            assert_no_leakage(df.iloc[rows], match)
        except LeakageError:
            n_violations += 1
        n_outside += int(rows.size > 0 and int(rows.max()) >= len(history))
    return LeakageCheck(n_checked, n_violations, n_outside)
