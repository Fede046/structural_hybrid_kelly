"""Verità sintetica per il Modulo 3 e scelta della candidata (T51).

Generatore (fissato nel piano prima di eseguire), nel formato del Modulo 2. Una replica è
una stagione di N_MATCHES = 380 partite, MATCHES_PER_DATE = 10 per data (38 date), mercato
binario per partita: l'esito 0 è il candidato alla puntata con quota o scelta fra
ODDS_CATEGORIES, l'esito 1 ha quota con overround OVERROUND = 1.05 (1/o_0 + 1/o_1 = 1.05),
q proporzionale. EV vero μ e σ_p dipendono dal regime e dalla metà della stagione (rottura
alla partita 190):
- (i) stazionario: μ = 0.02, σ_p = 0.015, mix delle quote MIX_PRE;
- (ii) compositivo puro: σ_p = 0.015 se o < 3 e 0.030 se o >= 3, μ = 0.02, mix da MIX_PRE a
  MIX_POST (cambia la composizione, non la relazione);
- (iii) strutturale puro (come abl32b): σ_p da 0.015 a 0.045 e μ da +0.02 a −0.05, mix fisso;
- (iv) entrambi: relazione di (ii) prima, σ_p raddoppiata (0.030 / 0.060) e μ = 0.005 dopo,
  mix da MIX_PRE a MIX_POST.
p = (1 + μ)/o; p̂ = clip(p + ε, 0.01, 0.99) con ε ~ N(0, σ_p²) sull'esito 0 (e −ε
sull'esito 1); esito Bernoulli(p); δ = ln p̂(x) − ln q(x). Covariate del Modulo 2: ln o e il
flag o >= 3. λ* oracolo per partita da μ, σ_p e o veri (module3.lambda_star).

Modulo 2 sulla replica: alla data d, A e B = le W e W partite che precedono d
(W = GENERATOR_WINDOW = 80, parametro del generatore), three-fold di Oaxaca-Blinder sulle
covariate non costanti nelle due finestre (known_scenarios.decomposition_batch, stesse
formule di oaxaca_blinder); non attivo con meno di 2W partite anteriori.

Bracci per crescita e drawdown, sulle stesse stime e sugli stessi esiti (confronto
appaiato): C0 λ = 0.25; C1 λ = 0.25·κ con κ = 0.4 quando il Modulo 2 dà un allarme binario,
definito qui come S < 0 e π >= 0.5 (strutturale peggiorativa e dominante), 0.25 altrimenti;
C2 = ciascuna candidata. Puntata solo se EV̂ > 0, frazione λ·EV̂/(o − 1).

Criterio (fissato nel task): errore quadratico medio fra λ̂ e λ* su tutte le partite,
mediato sui quattro regimi e su R = 500 repliche; vince la candidata con errore minimo
diversa da P1, a parità entro 1e-12 quella con meno quantità stimate.

Scenario di trappola (nota 3.2 §7.5, abl32b): 150 partite a quota 2.10, una per data,
σ_p da 0.015 a 0.045 e μ da +0.02 a −0.05 alla partita 75, W = 20, R = TRAP_REPLICAS;
P1 e P2 con le stesse stime e gli stessi esiti.

Seed: SeedSequence(SEED_S9).spawn(5)[1] (T51 in posizione 1 della story S9), spawn(5):
figli 0–3 per i regimi (i)–(iv), figlio 4 per la trappola; ogni generatore in sequenza
sulle repliche.
"""

import math
from typing import Final, NamedTuple

import numpy as np

from shk.model.known_scenarios import decomposition_batch
from shk.model.module3 import CANDIDATES, ESTIMATED_QUANTITIES, WindowData, candidate_lambda, lambda_star

# Seed della story S9 (decisione S7)
SEED_S9: Final[int] = 20261013
N_STORY_TASKS: Final[int] = 5
T51_STORY_POSITION: Final[int] = 1

N_MATCHES: Final[int] = 380
MATCHES_PER_DATE: Final[int] = 10
BREAK_AT: Final[int] = 190
OVERROUND: Final[float] = 1.05
ODDS_CATEGORIES: Final[tuple[float, ...]] = (1.8, 2.1, 2.6, 3.4)
MIX_PRE: Final[tuple[float, ...]] = (0.4, 0.3, 0.2, 0.1)
MIX_POST: Final[tuple[float, ...]] = (0.1, 0.2, 0.3, 0.4)
HIGH_ODDS: Final[float] = 3.0
GENERATOR_WINDOW: Final[int] = 80
N_REPLICAS: Final[int] = 500
BASE_LAMBDA: Final[float] = 0.25
C1_KAPPA: Final[float] = 0.4
REGIMES: Final[tuple[str, ...]] = ("i_stationary", "ii_compositional", "iii_structural", "iv_both")
TRAP_MATCHES: Final[int] = 150
TRAP_BREAK: Final[int] = 75
TRAP_ODDS: Final[float] = 2.10
TRAP_WINDOW: Final[int] = 20
TRAP_REPLICAS: Final[int] = 2000

MODULE3_SYNTHETIC_CSV_COLUMNS: Final[tuple[str, ...]] = (
    "row_type", "regime", "arm", "candidate", "mse", "mse_active", "n_replicas", "n_matches",
    "median_final_wealth", "mean_max_drawdown", "chosen", "share_detect", "share_grade", "metric",
)


class SyntheticSeason(NamedTuple):
    """Una replica: partite in ordine, con verità e grandezze osservabili."""

    odds: np.ndarray        # (n,) quota dell'esito candidato
    odds_other: np.ndarray  # (n,) quota dell'altro esito
    p_true: np.ndarray      # (n,)
    p_hat: np.ndarray       # (n,)
    sigma_p: np.ndarray     # (n,)
    ev_true: np.ndarray     # (n,)
    win: np.ndarray         # (n,) bool, esito 0 realizzato
    date_index: np.ndarray  # (n,)
    lambda_oracle: np.ndarray  # (n,) λ* da μ, σ_p e o veri


def regime_parameters(regime: str, odds: np.ndarray, post: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(μ, σ_p) per partita dato il regime e la metà della stagione."""
    high = odds >= HIGH_ODDS
    if regime == "i_stationary":
        return np.full(odds.shape, 0.02), np.full(odds.shape, 0.015)
    if regime == "ii_compositional":
        return np.full(odds.shape, 0.02), np.where(high, 0.030, 0.015)
    if regime == "iii_structural":
        return np.where(post, -0.05, 0.02), np.where(post, 0.045, 0.015)
    if regime == "iv_both":
        sigma = np.where(high, 0.030, 0.015) * np.where(post, 2.0, 1.0)
        return np.where(post, 0.005, 0.02), sigma
    raise ValueError(f"Unknown regime {regime!r}")


def generate_season(regime: str, rng: np.random.Generator, n: int = N_MATCHES, break_at: int = BREAK_AT,
                    per_date: int = MATCHES_PER_DATE, fixed_odds: float | None = None) -> SyntheticSeason:
    """Una replica del regime. Estrazioni: quote (se non fisse), ε, esiti."""
    post = np.arange(n) >= break_at
    if fixed_odds is None:
        mix_post = MIX_POST if regime in ("ii_compositional", "iv_both") else MIX_PRE
        cat = np.where(post, rng.choice(len(ODDS_CATEGORIES), size=n, p=mix_post),
                       rng.choice(len(ODDS_CATEGORIES), size=n, p=MIX_PRE))
        odds = np.array(ODDS_CATEGORIES)[cat]
    else:
        odds = np.full(n, fixed_odds)
    if regime == "trap":
        ev, sigma = np.where(post, -0.05, 0.02), np.where(post, 0.045, 0.015)
    else:
        ev, sigma = regime_parameters(regime, odds, post)
    p = (1.0 + ev) / odds
    p_hat = np.clip(p + rng.normal(0.0, 1.0, n) * sigma, 0.01, 0.99)
    win = rng.random(n) < p
    odds_other = 1.0 / (OVERROUND - 1.0 / odds)
    return SyntheticSeason(odds, odds_other, p, p_hat, sigma, ev, win, np.arange(n) // per_date,
                           lambda_star(ev, odds * sigma))


def _window(season: SyntheticSeason, idx: np.ndarray) -> WindowData:
    p_hat = np.column_stack([season.p_hat[idx], 1.0 - season.p_hat[idx]])
    q0 = (1.0 / season.odds[idx]) / OVERROUND
    q = np.column_stack([q0, 1.0 - q0])
    outcome = np.where(season.win[idx], 0, 1)
    return WindowData(p_hat, q, outcome, season.p_hat[idx] * season.odds[idx] - 1.0)


def _delta(season: SyntheticSeason) -> np.ndarray:
    q0 = (1.0 / season.odds) / OVERROUND
    return np.where(season.win, np.log(season.p_hat) - np.log(q0), np.log(1.0 - season.p_hat) - np.log(1.0 - q0))


def season_lambdas(season: SyntheticSeason, window: int) -> dict[str, np.ndarray]:
    """λ per partita delle candidate e dei bracci C0, C1 su una replica."""
    n = season.odds.shape[0]
    delta = _delta(season)
    x = np.column_stack([np.log(season.odds), (season.odds >= HIGH_ODDS).astype(float)])
    ev_hat = season.p_hat * season.odds - 1.0
    out = {c: np.empty(n) for c in CANDIDATES}
    out["C0"] = np.full(n, BASE_LAMBDA)
    out["C1"] = np.empty(n)
    for d in np.unique(season.date_index):
        today = np.flatnonzero(season.date_index == d)
        before = np.flatnonzero(season.date_index < d)
        active = before.size >= 2 * window
        wa = wb = None
        structural, share = 0.0, 0.0
        if active:
            ia, ib = before[-2 * window:-window], before[-window:]
            xa, xb = x[ia], x[ib]
            keep = [j for j in range(x.shape[1]) if np.ptp(xa[:, j]) > 0 and np.ptp(xb[:, j]) > 0]
            q, _ = decomposition_batch(xa[None][:, :, keep], delta[ia][None], xb[None][:, :, keep], delta[ib][None])
            structural, share = float(q["structural"][0]), float(q["structural_share"][0])
            wa, wb = _window(season, ia), _window(season, ib)
        for c in CANDIDATES:
            out[c][today] = candidate_lambda(c, active, wa, wb, structural, season.odds[today], ev_hat[today])
        alarm = active and structural < 0.0 and share >= 0.5
        out["C1"][today] = BASE_LAMBDA * C1_KAPPA if alarm else BASE_LAMBDA
    return out


def wealth_path(season: SyntheticSeason, lam: np.ndarray) -> tuple[float, float]:
    """Ricchezza finale e drawdown massimo con frazioni λ·max(0, EV̂)/(o − 1)."""
    ev_hat = season.p_hat * season.odds - 1.0
    f = np.minimum(lam * np.maximum(ev_hat, 0.0) / (season.odds - 1.0), 0.99)
    factors = np.where(season.win, 1.0 + f * (season.odds - 1.0), 1.0 - f)
    wealth = np.cumprod(np.r_[1.0, factors])
    peak = np.maximum.accumulate(wealth)
    return float(wealth[-1]), float(np.max(1.0 - wealth / peak))


def spawn_t51_generators(seed: int = SEED_S9) -> tuple[np.random.Generator, ...]:
    """Cinque generatori: regimi (i)–(iv) e trappola."""
    if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)):
        raise TypeError(f"seed must be an integer, got {type(seed).__name__}")
    task = np.random.SeedSequence(seed).spawn(N_STORY_TASKS)[T51_STORY_POSITION]
    return tuple(np.random.default_rng(s) for s in task.spawn(5))


class RegimeResult(NamedTuple):
    """Errori e metriche per regime."""

    regime: str
    mse: dict[str, float]
    mse_active: dict[str, float]
    median_wealth: dict[str, float]
    mean_drawdown: dict[str, float]


def evaluate_regime(regime: str, rng: np.random.Generator, n_replicas: int = N_REPLICAS,
                    window: int = GENERATOR_WINDOW) -> RegimeResult:
    """MSE fra λ̂ e λ* e metriche dei bracci su n_replicas repliche."""
    sq = {c: [] for c in CANDIDATES}
    sq_act = {c: [] for c in CANDIDATES}
    wealth = {a: [] for a in ("C0", "C1", *CANDIDATES)}
    dd = {a: [] for a in wealth}
    for _ in range(n_replicas):
        season = generate_season(regime, rng)
        lam = season_lambdas(season, window)
        oracle = season.lambda_oracle
        active = season.date_index >= 2 * window // MATCHES_PER_DATE
        for c in CANDIDATES:
            sq[c].append((lam[c] - oracle) ** 2)
            sq_act[c].append(((lam[c] - oracle) ** 2)[active])
        for a in wealth:
            w, m = wealth_path(season, lam[a])
            wealth[a].append(w)
            dd[a].append(m)
    return RegimeResult(
        regime,
        {c: float(np.mean(np.concatenate(sq[c]))) for c in CANDIDATES},
        {c: float(np.mean(np.concatenate(sq_act[c]))) for c in CANDIDATES},
        {a: float(np.median(wealth[a])) for a in wealth},
        {a: float(np.mean(dd[a])) for a in dd},
    )


def choose_candidate(mse_by_regime: list[dict[str, float]]) -> str:
    """Regola del passo 4: minimo dell'MSE medio sui regimi fra le candidate diverse da P1."""
    means = {c: float(np.mean([m[c] for m in mse_by_regime])) for c in CANDIDATES if c != "P1"}
    best = min(means.values())
    tied = [c for c in means if means[c] - best <= 1e-12]
    return min(tied, key=lambda c: (ESTIMATED_QUANTITIES[c], c))


def trap_comparison(rng: np.random.Generator, n_replicas: int = TRAP_REPLICAS) -> dict[str, tuple[float, float]]:
    """Scenario abl32b: (crescita mediana, drawdown medio) di P1, P2 e C0, stesse stime ed esiti."""
    wealth = {a: [] for a in ("C0", "P1", "P2")}
    dd = {a: [] for a in wealth}
    for _ in range(n_replicas):
        season = generate_season("trap", rng, n=TRAP_MATCHES, break_at=TRAP_BREAK, per_date=1, fixed_odds=TRAP_ODDS)
        lam = season_lambdas(season, TRAP_WINDOW)
        for a in wealth:
            w, m = wealth_path(season, lam[a])
            wealth[a].append(w)
            dd[a].append(m)
    return {a: (float(np.median(wealth[a])), float(np.mean(dd[a]))) for a in wealth}


def evaluate_module3_synthetic(seed: int = SEED_S9, n_replicas: int = N_REPLICAS,
                               trap_replicas: int = TRAP_REPLICAS) -> tuple[str, list[RegimeResult], dict, list[dict]]:
    """Esegue regimi e trappola; restituisce (candidata scelta, risultati, trappola, record)."""
    rngs = spawn_t51_generators(seed)
    results = [evaluate_regime(r, g, n_replicas) for r, g in zip(REGIMES, rngs[:4])]
    chosen = choose_candidate([r.mse for r in results])
    trap = trap_comparison(rngs[4], trap_replicas)
    empty = {c: "" for c in MODULE3_SYNTHETIC_CSV_COLUMNS}
    records: list[dict] = []
    for r in results:
        for c in CANDIDATES:
            records.append({**empty, "row_type": "criterion", "regime": r.regime, "candidate": c, "mse": r.mse[c],
                            "mse_active": r.mse_active[c], "n_replicas": n_replicas, "n_matches": N_MATCHES,
                            "chosen": c == chosen})
        for a in ("C0", "C1", *CANDIDATES):
            records.append({**empty, "row_type": "arm", "regime": r.regime, "arm": a,
                            "median_final_wealth": r.median_wealth[a], "mean_max_drawdown": r.mean_drawdown[a],
                            "n_replicas": n_replicas})
        for metric, key in (("growth", r.median_wealth), ("drawdown", r.mean_drawdown)):
            total = key[chosen] - key["C0"]
            share_detect = (key["C1"] - key["C0"]) / total if total != 0.0 else math.nan
            share_grade = (key[chosen] - key["C1"]) / total if total != 0.0 else math.nan
            records.append({**empty, "row_type": "detect_grade", "regime": r.regime, "arm": chosen, "metric": metric,
                            "share_detect": share_detect, "share_grade": share_grade})
    for c in CANDIDATES:
        mean_mse = float(np.mean([r.mse[c] for r in results]))
        records.append({**empty, "row_type": "criterion", "regime": "mean", "candidate": c, "mse": mean_mse,
                        "n_replicas": n_replicas, "chosen": c == chosen})
    for a, (g, m) in trap.items():
        records.append({**empty, "row_type": "trap", "regime": "abl32b", "arm": a, "median_final_wealth": g,
                        "mean_max_drawdown": m, "n_replicas": trap_replicas, "n_matches": TRAP_MATCHES})
    return chosen, results, trap, records
