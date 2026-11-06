"""Popolazione di strategie con dinamica del replicatore e mutazione (thesis/disegno_popolazione.md).

Le strategie si dividono il capitale; s_i(d) è la quota della strategia i alla giornata d e R_i(d) il
suo rendimento lordo nella giornata (W_i(d+1) / W_i(d)). Senza puntata minima ogni puntata è una
frazione del capitale corrente e lo schema decide su δ, quindi R_i(d) non dipende dal capitale
affidato alla strategia: la popolazione si calcola esattamente dai percorsi delle singole strategie.

- Capitale: W_pop(d+1) = W_pop(d) · Σ_i s_i(d) R_i(d), con W_pop(0) = 1.
- Quote: s_i(d+1) = (1 − μ) · s_i(d) R_i(d) / Σ_j s_j(d) R_j(d) + μ / N.
  Con μ = 0 è la selezione pura, uguale a dividere il capitale all'inizio senza mai ribilanciare;
  con μ > 0 ogni quota resta almeno μ / N.
- Generazioni: le quote iniziali di una stagione sono quelle finali della precedente.

Tutte le funzioni lavorano su array con assi iniziali qualsiasi (per esempio i seed): rendimenti
(..., N, D), quote (..., N).
"""

from collections.abc import Sequence

import numpy as np


def gross_returns(wealth: np.ndarray) -> np.ndarray:
    """Rendimenti lordi per giornata da percorsi del capitale (..., D+1) → (..., D).

    Solleva ValueError se il capitale non è finito e positivo.
    """
    w = np.asarray(wealth, dtype=np.float64)
    if w.shape[-1] < 2:
        raise ValueError(f"wealth must have at least 2 points on the last axis, got {w.shape}")
    if not np.all(np.isfinite(w)) or np.any(w <= 0.0):
        raise ValueError("wealth must be finite and strictly positive")
    return w[..., 1:] / w[..., :-1]


def _check_inputs(returns: np.ndarray, mu: float, initial: np.ndarray | None) -> tuple[np.ndarray, np.ndarray]:
    r = np.asarray(returns, dtype=np.float64)
    if r.ndim < 2:
        raise ValueError(f"returns must have shape (..., N, D), got {r.shape}")
    if not np.all(np.isfinite(r)) or np.any(r < 0.0):
        raise ValueError("returns must be finite and non-negative")
    if not 0.0 <= mu <= 1.0:
        raise ValueError(f"mu must be in [0, 1], got {mu}")
    n = r.shape[-2]
    if initial is None:
        s0 = np.full(r.shape[:-1], 1.0 / n)
    else:
        s0 = np.broadcast_to(np.asarray(initial, dtype=np.float64), r.shape[:-1]).copy()
        if np.any(s0 < 0.0) or not np.allclose(s0.sum(axis=-1), 1.0):
            raise ValueError("initial shares must be non-negative and sum to 1")
    return r, s0


def replicator_step(shares: np.ndarray, returns: np.ndarray, mu: float) -> np.ndarray:
    """Un passo del replicatore con mutazione: quote (..., N) e rendimenti (..., N) → quote (..., N).

    Se tutte le strategie perdono tutto (Σ s R = 0) le quote restano quelle di prima, poi la mutazione.
    """
    weighted = shares * returns
    total = weighted.sum(axis=-1, keepdims=True)
    selected = np.where(total > 0.0, weighted / np.where(total > 0.0, total, 1.0), shares)
    n = shares.shape[-1]
    return (1.0 - mu) * selected + mu / n


def evolve(returns: np.ndarray, mu: float, initial: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Quote e capitale della popolazione lungo una stagione.

    Parametri
    ---------
    returns : np.ndarray
        Rendimenti lordi (..., N, D) delle N strategie nelle D giornate.
    mu : float
        Tasso di mutazione in [0, 1].
    initial : np.ndarray o None
        Quote iniziali (..., N) o (N,); se None quote uguali 1/N.

    Restituisce
    -----------
    (shares, wealth)
        shares (..., N, D+1), quote prima di ogni giornata e dopo l'ultima;
        wealth (..., D+1), capitale della popolazione con W(0) = 1.
    """
    r, s = _check_inputs(returns, mu, initial)
    d_count = r.shape[-1]
    shares = np.empty(r.shape[:-1] + (d_count + 1,))
    wealth = np.empty(r.shape[:-2] + (d_count + 1,))
    shares[..., 0] = s
    wealth[..., 0] = 1.0
    for d in range(d_count):
        rd = r[..., d]
        wealth[..., d + 1] = wealth[..., d] * (s * rd).sum(axis=-1)
        s = replicator_step(s, rd, mu)
        shares[..., d + 1] = s
    return shares, wealth


def evolve_generations(season_returns: Sequence[np.ndarray], mu: float,
                       initial: np.ndarray | None = None) -> list[tuple[np.ndarray, np.ndarray]]:
    """Stagioni in sequenza, ognuna con capitale iniziale 1 e quote iniziali uguali alle finali della precedente.

    season_returns è una sequenza di rendimenti (..., N, D_k), con gli stessi assi iniziali e lo stesso N
    (il numero di giornate D_k può cambiare). Restituisce (shares, wealth) di evolve per ogni stagione.
    """
    out: list[tuple[np.ndarray, np.ndarray]] = []
    start = initial
    for r in season_returns:
        shares, wealth = evolve(r, mu, start)
        out.append((shares, wealth))
        start = shares[..., -1]
    return out


def with_cash(returns: np.ndarray) -> np.ndarray:
    """Aggiunge in coda la strategia «cassa», che non punta mai (rendimento 1 in ogni giornata)."""
    r = np.asarray(returns, dtype=np.float64)
    cash = np.ones(r.shape[:-2] + (1, r.shape[-1]))
    return np.concatenate([r, cash], axis=-2)
