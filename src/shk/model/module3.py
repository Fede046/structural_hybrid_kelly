"""Modulo 3: dall'uscita del Modulo 2 a Var(c), E[c] e λ (T51).

Notazione. Per una scommessa su un esito con quota o, EV vero μ = p·o − 1 e stima
EV̂ = p̂·o − 1 = μ + o·ε, con ε l'errore della probabilità stimata sull'esito. Con
ε ~ N(0, σ_p²) l'EV stimato è X ~ N(μ, s²), s = o·σ_p, e la frazione stimata troncata è
f̂ = max(0, X)/b, con c = f̂/f* = max(0, X)/μ. Il moltiplicatore ottimo (nota 2.3 §4) è
λ* = E[c]/E[c²] = μ·E[X⁺]/E[(X⁺)²], con E[X⁺] = μΦ(μ/s) + sφ(μ/s) e
E[(X⁺)²] = (μ² + s²)Φ(μ/s) + μsφ(μ/s); λ* = 0 se μ <= 0, λ* = 1 se s = 0; limitato a
[0, 1]. Senza troncamento E[c] = 1 e λ* = 1/(1 + Var(c)), Var(c) = (o·σ_p/μ)² (nota 2.7 §7.1).

Errore sulle probabilità a K esiti: ε = P z, z ~ N(0, σ² I_K), P = I − 11'/K (somma nulla),
quindi l'errore sull'esito scommesso ha deviazione standard σ_p = σ·sqrt((K − 1)/K).

Stima di σ² dalla dispersione di δ (delta_dispersion_sigma2). Con L_i = ln p̂_i − ln q_i,
δ = L_X, e = δ − m̂ (scarto di δ dal valore atteso secondo il modello, m̂ = Σ_i p̂_i L_i) e
V = Σ_i p̂_i L_i² − m̂² la varianza di δ secondo il modello, vale esattamente
E[e² − V | p, p̂] = 2 m̂ (ε·L) − Σ_i ε_i L_i²: il termine (ε·L)² si cancella. Sviluppando
L_i = L⁰_i + ε_i/p_i − ε_i²/(2p_i²) + … con Σ_i ε_i = 0 e Var(ε_i) = σ²(1 − 1/K), al secondo
ordine E[e² − V] = σ²·E[c], c = 2 Σ_i (L_i − L̄)² + 2(1 − 1/K)(m̂ Σ_i 1/p̂_i − Σ_i L_i/p̂_i),
con c valutato in p̂. Quindi σ̂² = max(σ²_min, (mean(e²) − mean(V)) / mean(c)); mean(c) può
essere negativo (a quote alte domina il termine in 1/p̂), e se è nullo σ̂² = σ²_min.

Gonfiamento strutturale (P3, dalla catena OB → σ_p → Var(c) → λ* della nota 2.7 §7.1).
Al secondo ordine E[δ] = D(p, q) − ½ Σ_i E[ε_i²]/p_i = D(p, q) − ½ σ² (1 − 1/K) Σ_i 1/p_i:
un aumento Δ di σ² abbassa la media di δ di Δ·h, h = mean((1 − 1/K)/2 · Σ_i 1/p̂_i). Una
componente strutturale S < 0 del Modulo 2 (δ peggiorato a composizione fissa) si traduce in
Δ = −S/h; con S >= 0, Δ = 0.

Candidate (scritte prima della valutazione, piano di T51):
- P1, plug-in per scommessa (controllo negativo, nota 3.2 §7.5): μ̂ = EV̂ della singola
  scommessa, σ̂ dalla dispersione di δ sulla finestra B; λ = λ*(μ̂, o·σ̂_p);
- P2: μ̂ = media degli EV̂ della finestra B (tutte le candidate, non solo le selezionate,
  nota 2.3 §7.2), σ̂ dalla dispersione di δ sulla finestra B; λ = λ*(μ̂, o·σ̂_p);
- P3: μ̂ come P2; σ̂² = σ̂²_A (dispersione di δ sulla finestra A) + Δ dal gonfiamento
  strutturale; λ = λ*(μ̂, o·σ̂_p).
Regole comuni: λ in [0, 1]; λ = 0 se ĝ della finestra B (media di δ) è <= 0; "non
attivo" dà λ = INACTIVE_LAMBDA = 0.25, come C0.

Scelta (T51, criterio del passo 4 su verità sintetica): CHOSEN_CANDIDATE = "P3", usata da
module3_lambda, la funzione del Modulo 3.
"""

import math
from typing import Final, NamedTuple

import numpy as np
import scipy.stats

INACTIVE_LAMBDA: Final[float] = 0.25
SIGMA2_MIN: Final[float] = 1e-6
CANDIDATES: Final[tuple[str, ...]] = ("P1", "P2", "P3")
# Quantità stimate per candidata, per la regola di parità del criterio di T51
ESTIMATED_QUANTITIES: Final[dict[str, int]] = {"P1": 2, "P2": 2, "P3": 3}


class WindowData(NamedTuple):
    """Partite di una finestra del Modulo 2 per il Modulo 3.

    Attributi
    ---------
    p_hat : np.ndarray
        Probabilità del modello (n, K).
    q : np.ndarray
        Probabilità di mercato (n, K).
    outcome : np.ndarray
        Esito realizzato (n,), interi 0..K−1.
    ev_candidate : np.ndarray
        EV̂ = p̂·o − 1 dell'esito candidato alla puntata di ogni partita (n,).
    """

    p_hat: np.ndarray
    q: np.ndarray
    outcome: np.ndarray
    ev_candidate: np.ndarray


def lambda_star(mu: np.ndarray | float, s: np.ndarray | float) -> np.ndarray:
    """λ* = E[c]/E[c²] con troncamento a zero, limitato a [0, 1] (vedi modulo)."""
    mu_arr = np.asarray(mu, dtype=np.float64)
    s_arr = np.broadcast_to(np.asarray(s, dtype=np.float64), mu_arr.shape)
    out = np.zeros(np.broadcast(mu_arr, s_arr).shape)
    pos = mu_arr > 0.0
    zero_s = pos & (s_arr <= 0.0)
    out[zero_s] = 1.0
    reg = pos & (s_arr > 0.0)
    m, sd = mu_arr[reg], s_arr[reg]
    z = m / sd
    cdf, pdf = scipy.stats.norm.cdf(z), scipy.stats.norm.pdf(z)
    e1 = m * cdf + sd * pdf
    e2 = (m**2 + sd**2) * cdf + m * sd * pdf
    out[reg] = m * e1 / e2
    return np.clip(out, 0.0, 1.0)


def delta_dispersion_sigma2(w: WindowData) -> float:
    """σ̂² dalla dispersione di δ sulla finestra (vedi modulo), almeno SIGMA2_MIN."""
    p = np.asarray(w.p_hat, dtype=np.float64)
    q = np.asarray(w.q, dtype=np.float64)
    idx = np.asarray(w.outcome, dtype=np.int64)
    rows = np.arange(p.shape[0])
    log_ratio = np.log(p) - np.log(q)
    expected = (p * log_ratio).sum(axis=1)
    model_var = (p * log_ratio**2).sum(axis=1) - expected**2
    e = log_ratio[rows, idx] - expected
    k = p.shape[1]
    spread = ((log_ratio - log_ratio.mean(axis=1, keepdims=True)) ** 2).sum(axis=1)
    curvature = expected * (1.0 / p).sum(axis=1) - (log_ratio / p).sum(axis=1)
    denom = float((2.0 * spread + 2.0 * (1.0 - 1.0 / k) * curvature).mean())
    # c può essere negativo (quote alte): conta solo che non sia nullo
    if denom == 0.0 or not math.isfinite(denom):
        return SIGMA2_MIN
    return max(SIGMA2_MIN, float((e**2).mean() - model_var.mean()) / denom)


def structural_inflation(structural: float, p_hat_a: np.ndarray) -> float:
    """Δσ² = −S/h se S < 0, altrimenti 0, con h = mean((1 − 1/K)/2 · Σ 1/p̂) sulla finestra A."""
    if not structural < 0.0:
        return 0.0
    p = np.asarray(p_hat_a, dtype=np.float64)
    k = p.shape[1]
    h = float(((1.0 - 1.0 / k) / 2.0 * (1.0 / p).sum(axis=1)).mean())
    return float(-structural / h)


def selected_sd(sigma2: float, k: int) -> float:
    """Deviazione standard dell'errore sull'esito scommesso: σ·sqrt((K − 1)/K)."""
    return math.sqrt(sigma2 * (k - 1) / k)


def candidate_lambda(
    candidate: str,
    active: bool,
    window_a: WindowData | None,
    window_b: WindowData | None,
    structural: float,
    odds_bet: np.ndarray,
    ev_hat_bet: np.ndarray,
) -> np.ndarray:
    """λ di una candidata per le scommesse della data (vettore della lunghezza di odds_bet).

    Parametri
    ---------
    candidate : str
        "P1", "P2" o "P3".
    active : bool
        Stato del Modulo 2; se False λ = INACTIVE_LAMBDA.
    window_a, window_b : WindowData o None
        Finestre A e B del Modulo 2 (None se non attivo).
    structural : float
        Componente strutturale S del Modulo 2 (usata da P3).
    odds_bet, ev_hat_bet : np.ndarray
        Quota ed EV̂ delle scommesse della data.
    """
    n = np.asarray(odds_bet).shape[0]
    if candidate not in CANDIDATES:
        raise ValueError(f"candidate must be one of {CANDIDATES}, got {candidate!r}")
    if not active:
        return np.full(n, INACTIVE_LAMBDA)
    g_hat_b = float(np.mean(np.log(window_b.p_hat[np.arange(window_b.outcome.size), window_b.outcome])
                            - np.log(window_b.q[np.arange(window_b.outcome.size), window_b.outcome])))
    if g_hat_b <= 0.0:
        return np.zeros(n)
    k = window_b.p_hat.shape[1]
    if candidate == "P3":
        sigma2 = delta_dispersion_sigma2(window_a) + structural_inflation(structural, window_a.p_hat)
    else:
        sigma2 = delta_dispersion_sigma2(window_b)
    s = np.asarray(odds_bet, dtype=np.float64) * selected_sd(sigma2, k)
    if candidate == "P1":
        mu = np.asarray(ev_hat_bet, dtype=np.float64)
    else:
        mu = np.full(n, float(np.mean(window_b.ev_candidate)))
    return lambda_star(mu, s)


# Candidata scelta in T51 con il criterio del passo 4 (results/us_c8_1a_module3_synthetic.csv)
CHOSEN_CANDIDATE: Final[str] = "P3"


def module3_lambda(
    active: bool,
    window_a: WindowData | None,
    window_b: WindowData | None,
    structural: float,
    odds_bet: np.ndarray,
    ev_hat_bet: np.ndarray,
) -> np.ndarray:
    """Funzione del Modulo 3: λ delle scommesse della data con la candidata CHOSEN_CANDIDATE.

    Parametri come candidate_lambda.
    """
    return candidate_lambda(CHOSEN_CANDIDATE, active, window_a, window_b, structural, odds_bet, ev_hat_bet)
