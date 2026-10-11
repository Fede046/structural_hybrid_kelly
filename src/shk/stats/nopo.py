"""Supporto comune: celle di covariate, decomposizione di Ñopo e regola "fuori supporto" (T49).

Celle: le covariate continue si discretizzano in quintili con bordi = quantili 0.2, 0.4,
0.6, 0.8 di un insieme di riferimento (un valore uguale a un bordo va nel gruppo superiore,
un valore oltre i bordi nel primo o nell'ultimo gruppo); le dummy restano ai loro livelli.
Una cella è la combinazione dei livelli di tutte le covariate.

Decomposizione di Ñopo (2008) a quattro parti, per i gruppi A (riferimento) e B, con
Δ = ȳ_B − ȳ_A. Le celle comuni sono quelle presenti in entrambi i gruppi:
- fuori supporto in A: −p_A^u (ȳ_A^u − ȳ_A^m), con p_A^u la quota di A nelle celle che B non
  ha e ȳ_A^u, ȳ_A^m le medie di A fuori e dentro le celle comuni (0 se p_A^u = 0);
- fuori supporto in B: p_B^u (ȳ_B^u − ȳ_B^m) (0 se p_B^u = 0);
- composizione nel supporto: Σ_c (w_B,c − w_A,c) ȳ_A,c, con w i pesi delle celle comuni
  dentro ciascun gruppo;
- struttura nel supporto: Σ_c w_B,c (ȳ_B,c − ȳ_A,c).
Le quattro parti sommano a Δ.

Regola "fuori supporto" (decisione di T49, riusata da C2 in S9): una partita da prevedere è
fuori supporto se la sua cella, costruita con i bordi dei quintili della finestra A, ha meno
di MIN_CELL_COUNT = 5 partite della finestra A.
"""

from collections.abc import Sequence
from typing import Final, NamedTuple

import numpy as np

MIN_CELL_COUNT: Final[int] = 5
QUANTILE_LEVELS: Final[tuple[float, ...]] = (0.2, 0.4, 0.6, 0.8)


class NopoResult(NamedTuple):
    """Decomposizione di Ñopo a quattro parti."""

    total: float
    out_of_support_a: float
    out_of_support_b: float
    composition: float
    structure: float
    share_unmatched_a: float
    share_unmatched_b: float
    n_common_cells: int


def quintile_edges(reference: np.ndarray, dummy_columns: Sequence[int]) -> list[np.ndarray | None]:
    """Bordi dei quintili per colonna (None per le dummy), calcolati su reference (n, k)."""
    ref = np.asarray(reference, dtype=np.float64)
    if ref.ndim != 2 or ref.shape[0] < 1:
        raise ValueError("reference must be 2D with at least one row")
    dummies = set(dummy_columns)
    return [None if j in dummies else np.quantile(ref[:, j], QUANTILE_LEVELS) for j in range(ref.shape[1])]


def cell_ids(x: np.ndarray, edges: Sequence[np.ndarray | None]) -> np.ndarray:
    """Identificatore intero della cella per ogni riga di x (n, k), dati i bordi."""
    arr = np.asarray(x, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[1] != len(edges):
        raise ValueError(f"x must be 2D with {len(edges)} columns")
    levels = np.empty(arr.shape, dtype=np.int64)
    for j, e in enumerate(edges):
        if e is None:
            if not np.all(np.isin(arr[:, j], (0.0, 1.0))):
                raise ValueError(f"Dummy column {j} must contain only 0 and 1")
            levels[:, j] = arr[:, j].astype(np.int64)
        else:
            levels[:, j] = np.searchsorted(e, arr[:, j], side="right")
    # Codifica mista con base 6 (5 quintili, 2 livelli per le dummy, margine per sicurezza)
    weights = 6 ** np.arange(arr.shape[1], dtype=np.int64)
    return levels @ weights


def nopo_decomposition(cells_a: np.ndarray, y_a: np.ndarray, cells_b: np.ndarray, y_b: np.ndarray) -> NopoResult:
    """Decomposizione di Ñopo per celle già assegnate.

    Solleva
    -------
    ValueError
        Se i gruppi sono vuoti o le forme non coincidono.
    """
    ca, cb = np.asarray(cells_a), np.asarray(cells_b)
    ya, yb = np.asarray(y_a, dtype=np.float64), np.asarray(y_b, dtype=np.float64)
    if ca.shape != ya.shape or cb.shape != yb.shape or ya.ndim != 1 or ya.size == 0 or yb.size == 0:
        raise ValueError("cells and y must be non-empty 1D arrays of equal length per group")
    common = np.intersect1d(ca, cb)
    in_a = np.isin(ca, common)
    in_b = np.isin(cb, common)
    p_a_u = float(1.0 - in_a.mean())
    p_b_u = float(1.0 - in_b.mean())
    total = float(yb.mean() - ya.mean())
    if common.size == 0:
        # Nessuna cella comune: tutto il divario è fuori supporto
        return NopoResult(total, -float(ya.mean()), float(yb.mean()), 0.0, 0.0, 1.0, 1.0, 0)
    ya_m, yb_m = float(ya[in_a].mean()), float(yb[in_b].mean())
    out_a = -p_a_u * (float(ya[~in_a].mean()) - ya_m) if p_a_u > 0.0 else 0.0
    out_b = p_b_u * (float(yb[~in_b].mean()) - yb_m) if p_b_u > 0.0 else 0.0
    _, inv_a = np.unique(ca[in_a], return_inverse=True)
    _, inv_b = np.unique(cb[in_b], return_inverse=True)
    n_c = common.size
    w_a = np.bincount(inv_a, minlength=n_c) / in_a.sum()
    w_b = np.bincount(inv_b, minlength=n_c) / in_b.sum()
    mean_a = np.bincount(inv_a, weights=ya[in_a], minlength=n_c) / np.bincount(inv_a, minlength=n_c)
    mean_b = np.bincount(inv_b, weights=yb[in_b], minlength=n_c) / np.bincount(inv_b, minlength=n_c)
    composition = float(((w_b - w_a) * mean_a).sum())
    structure = float((w_b * (mean_b - mean_a)).sum())
    return NopoResult(total, out_a, out_b, composition, structure, p_a_u, p_b_u, int(n_c))


def nopo_from_covariates(x_a: np.ndarray, y_a: np.ndarray, x_b: np.ndarray, y_b: np.ndarray,
                         dummy_columns: Sequence[int]) -> NopoResult:
    """Ñopo con celle dai quintili calcolati sull'unione dei due gruppi."""
    edges = quintile_edges(np.vstack([x_a, x_b]), dummy_columns)
    return nopo_decomposition(cell_ids(x_a, edges), y_a, cell_ids(x_b, edges), y_b)


def out_of_support_mask(window_a_x: np.ndarray, match_x: np.ndarray, dummy_columns: Sequence[int],
                        min_count: int = MIN_CELL_COUNT) -> np.ndarray:
    """Vero per le partite la cui cella ha meno di min_count partite della finestra A.

    I bordi dei quintili si calcolano sulla sola finestra A, quindi la regola usa solo
    partite della finestra A.
    """
    if isinstance(min_count, bool) or not isinstance(min_count, (int, np.integer)) or min_count < 1:
        raise ValueError(f"min_count must be a positive integer, got {min_count}")
    edges = quintile_edges(window_a_x, dummy_columns)
    cells_a = cell_ids(window_a_x, edges)
    cells_m = cell_ids(match_x, edges)
    unique, counts = np.unique(cells_a, return_counts=True)
    lookup = dict(zip(unique.tolist(), counts.tolist()))
    return np.array([lookup.get(int(c), 0) < min_count for c in cells_m], dtype=bool)


def did_2x2(y: np.ndarray, treated: np.ndarray, late: np.ndarray) -> float:
    """DiD = (ȳ_E,tardi − ȳ_E,presto) − (ȳ_NE,tardi − ȳ_NE,presto).

    Solleva
    -------
    ValueError
        Se una delle quattro celle è vuota.
    """
    yv = np.asarray(y, dtype=np.float64)
    t = np.asarray(treated, dtype=bool)
    l = np.asarray(late, dtype=bool)
    means = {}
    for name, mask in (("e_late", t & l), ("e_early", t & ~l), ("n_late", ~t & l), ("n_early", ~t & ~l)):
        if not mask.any():
            raise ValueError(f"Empty DiD cell: {name}")
        means[name] = float(yv[mask].mean())
    return (means["e_late"] - means["e_early"]) - (means["n_late"] - means["n_early"])
