"""Decomposizione di Oaxaca-Blinder a mano, su array.

Convenzione della nota 1.5 §9.5: A è il gruppo di riferimento (la finestra vecchia), B il
gruppo recente; in ciascun gruppo si stima un OLS separato y = x'beta con intercetta. Con
x̄ che comprende l'1 dell'intercetta, il totale è Δ = ȳ_B − ȳ_A e la three-fold è

    Δ = beta_A'(x̄_B − x̄_A)              COMPOSITIVA
      + x̄_A'(beta_B − beta_A)            STRUTTURALE
      + (x̄_B − x̄_A)'(beta_B − beta_A)    INTERAZIONE.

La two-fold con un vettore di riferimento beta* (nota 1.5 §3.2) è

    Δ = beta*'(x̄_B − x̄_A)                                spiegata (compositiva)
      + x̄_B'(beta_B − beta*) + x̄_A'(beta* − beta_A)      non spiegata (strutturale),

con i riferimenti di TWOFOLD_REFERENCES: beta_A e beta_B (Oaxaca 1973), media semplice
(Reimers 1983), media pesata per numerosità (Cotton 1988), OLS pooled senza indicatore di
gruppo (Neumark 1988) e OLS pooled con indicatore di gruppo, di cui beta* sono intercetta e
pendenze (Fortin 2008, Jann 2008). La forma generale di Oaxaca-Ransom (1994) con
Omega = (X'X)^-1 X_A'X_A coincide con Neumark e non si ripete.

Decomposizione dettagliata: contributi per covariata (intercetta compresa) delle tre
componenti; con la normalizzazione di Yun (2005) i coefficienti delle dummy di una stessa
variabile categoriale si riportano a somma zero su tutti i livelli, compreso quello omesso,
così i contributi per livello non dipendono dalla categoria di riferimento.

Quota strutturale (scelta dichiarata, nota 1.5 §9.5): pi = |S| / (|C| + |S| + |I|), in
[0, 1]; NaN se le tre componenti sono nulle. I valori assoluti al denominatore evitano che
componenti di segno opposto rendano la quota instabile; non è l'unica definizione possibile.

Gli OLS si risolvono con la fattorizzazione QR, mai invertendo X'X.
"""

import math
from collections.abc import Mapping, Sequence
from typing import Final, NamedTuple

import numpy as np
import scipy.linalg

TWOFOLD_REFERENCES: Final[tuple[str, ...]] = (
    "beta_a",
    "beta_b",
    "reimers",
    "cotton",
    "neumark",
    "pooled_group",
)
INTERCEPT_NAME: Final[str] = "intercept"
RANK_TOLERANCE: Final[float] = 1e-10


class OlsFit(NamedTuple):
    """OLS con intercetta: coefficienti, varianza dei residui e fattore R di QR."""

    beta: np.ndarray
    sigma2: float
    r_factor: np.ndarray
    n_obs: int


class TwoFold(NamedTuple):
    """Two-fold per un riferimento: spiegata (compositiva) e non spiegata (strutturale)."""

    reference: np.ndarray
    explained: float
    unexplained: float


class DetailedDecomposition(NamedTuple):
    """Contributi per covariata, allineati a names (intercetta, covariate, livelli omessi)."""

    names: tuple[str, ...]
    compositional: np.ndarray
    structural: np.ndarray
    interaction: np.ndarray


class OaxacaResult(NamedTuple):
    """Esito della decomposizione per due gruppi A (riferimento) e B (recente)."""

    mean_a: float
    mean_b: float
    total: float
    compositional: float
    structural: float
    interaction: float
    structural_share: float
    xbar_a: np.ndarray
    xbar_b: np.ndarray
    fit_a: OlsFit
    fit_b: OlsFit
    twofold: dict[str, TwoFold]
    detailed: DetailedDecomposition


class OaxacaStandardErrors(NamedTuple):
    """Errori standard iid (metodo delta) di totale e componenti della three-fold."""

    total: float
    compositional: float
    structural: float
    interaction: float


def _validate_group(x: np.ndarray, y: np.ndarray, name: str) -> tuple[np.ndarray, np.ndarray]:
    """Valida covariate (n, k) e risposta (n,) di un gruppo e le converte in float64."""
    for arr, label in ((x, f"x_{name}"), (y, f"y_{name}")):
        if not isinstance(arr, np.ndarray):
            raise TypeError(f"{label} must be an instance of np.ndarray, got {type(arr)}")
        if (
            not np.issubdtype(arr.dtype, np.number)
            or np.issubdtype(arr.dtype, np.complexfloating)
            or np.issubdtype(arr.dtype, np.bool_)
        ):
            raise TypeError(f"{label} must have real numeric dtype, got {arr.dtype}")
        if not np.all(np.isfinite(arr)):
            raise ValueError(f"All elements of {label} must be finite")
    if x.ndim != 2:
        raise ValueError(f"x_{name} must be 2D (n, k), got {x.ndim}D")
    if y.ndim != 1 or y.shape[0] != x.shape[0]:
        raise ValueError(f"y_{name} must be 1D with length {x.shape[0]}, got shape {y.shape}")
    return x.astype(np.float64), y.astype(np.float64)


def _with_intercept(x: np.ndarray) -> np.ndarray:
    """Aggiunge la colonna dell'intercetta in prima posizione."""
    return np.column_stack([np.ones(x.shape[0]), x])


def ols_qr(design: np.ndarray, y: np.ndarray) -> OlsFit:
    """OLS di y su design (colonne già comprensive dell'intercetta) via QR.

    Solleva
    -------
    ValueError
        Se design ha rango non pieno (|R_ii| <= RANK_TOLERANCE * max |R_ii|) o se
        n <= numero di colonne.
    """
    n, p = design.shape
    if n <= p:
        raise ValueError(f"OLS needs more observations than regressors, got n={n}, p={p}")
    q_mat, r_mat = np.linalg.qr(design)
    diag = np.abs(np.diag(r_mat))
    if diag.min() <= RANK_TOLERANCE * diag.max():
        raise ValueError("Design matrix is rank deficient")
    beta = scipy.linalg.solve_triangular(r_mat, q_mat.T @ y)
    resid = y - design @ beta
    sigma2 = float(resid @ resid / (n - p))
    return OlsFit(beta=beta, sigma2=sigma2, r_factor=r_mat, n_obs=n)


def _yun_normalize(
    beta: np.ndarray, xbar: np.ndarray, dummy_blocks: Sequence[Sequence[int]]
) -> tuple[np.ndarray, np.ndarray]:
    """Coefficienti e medie normalizzati di Yun, con un livello omesso in coda per blocco.

    beta e xbar hanno l'intercetta in posizione 0; gli indici dei blocchi si riferiscono
    alle covariate (0-based, senza intercetta).
    """
    beta_n = list(beta)
    xbar_n = list(xbar)
    extra_beta: list[float] = []
    extra_xbar: list[float] = []
    for block in dummy_blocks:
        cols = [j + 1 for j in block]
        shift = float(sum(beta[c] for c in cols)) / (len(cols) + 1)
        beta_n[0] += shift
        for c in cols:
            beta_n[c] = beta[c] - shift
        extra_beta.append(-shift)
        extra_xbar.append(1.0 - float(sum(xbar[c] for c in cols)))
    return np.array(beta_n + extra_beta), np.array(xbar_n + extra_xbar)


def _check_blocks(
    dummy_blocks: Mapping[str, Sequence[int]] | None, k: int
) -> tuple[list[str], list[list[int]]]:
    """Valida i blocchi di dummy: indici interi distinti in [0, k)."""
    if dummy_blocks is None:
        return [], []
    names: list[str] = []
    blocks: list[list[int]] = []
    seen: set[int] = set()
    for ref_name, idx in dummy_blocks.items():
        if not isinstance(ref_name, str):
            raise TypeError("dummy block names must be str")
        block = [int(i) for i in idx]
        if not block:
            raise ValueError(f"dummy block '{ref_name}' is empty")
        if any(i < 0 or i >= k for i in block) or seen.intersection(block) or len(set(block)) != len(block):
            raise ValueError(f"dummy block '{ref_name}' has invalid or repeated indices")
        seen.update(block)
        names.append(ref_name)
        blocks.append(block)
    return names, blocks


def oaxaca_blinder(
    x_a: np.ndarray,
    y_a: np.ndarray,
    x_b: np.ndarray,
    y_b: np.ndarray,
    names: Sequence[str] | None = None,
    dummy_blocks: Mapping[str, Sequence[int]] | None = None,
) -> OaxacaResult:
    """Decomposizione three-fold, two-fold per ogni riferimento e dettagliata con Yun.

    Parametri
    ---------
    x_a, x_b : np.ndarray
        Covariate (n_A, k) e (n_B, k), senza colonna dell'intercetta.
    y_a, y_b : np.ndarray
        Risposte (n_A,) e (n_B,).
    names : Sequence[str] o None
        Nomi delle k covariate (default x0, x1, ...).
    dummy_blocks : Mapping[str, Sequence[int]] o None
        Per ogni variabile categoriale: nome del livello omesso -> indici (0-based) delle
        sue colonne di dummy. Nella dettagliata i coefficienti si normalizzano con Yun e
        il livello omesso compare come voce in coda.

    Restituisce
    -----------
    OaxacaResult

    Solleva
    -------
    TypeError
        Se gli array non sono reali o i nomi non sono stringhe.
    ValueError
        Per forme incoerenti, valori non finiti, rango non pieno o blocchi non validi.
    """
    xa, ya = _validate_group(x_a, y_a, "a")
    xb, yb = _validate_group(x_b, y_b, "b")
    if xa.shape[1] != xb.shape[1]:
        raise ValueError(f"x_a and x_b must have the same columns, got {xa.shape[1]} and {xb.shape[1]}")
    k = xa.shape[1]
    if names is None:
        cov_names = [f"x{j}" for j in range(k)]
    else:
        cov_names = list(names)
        if len(cov_names) != k or not all(isinstance(nm, str) for nm in cov_names):
            raise ValueError(f"names must be {k} strings")
    ref_names, blocks = _check_blocks(dummy_blocks, k)

    design_a = _with_intercept(xa)
    design_b = _with_intercept(xb)
    fit_a = ols_qr(design_a, ya)
    fit_b = ols_qr(design_b, yb)
    beta_a, beta_b = fit_a.beta, fit_b.beta
    xbar_a = design_a.mean(axis=0)
    xbar_b = design_b.mean(axis=0)
    dx = xbar_b - xbar_a
    dbeta = beta_b - beta_a

    mean_a = float(ya.mean())
    mean_b = float(yb.mean())
    total = mean_b - mean_a
    compositional = float(beta_a @ dx)
    structural = float(xbar_a @ dbeta)
    interaction = float(dx @ dbeta)
    denom = abs(compositional) + abs(structural) + abs(interaction)
    share = abs(structural) / denom if denom > 0.0 else math.nan

    # Two-fold per riferimento
    n_a, n_b = xa.shape[0], xb.shape[0]
    pooled_design = np.vstack([design_a, design_b])
    pooled_y = np.concatenate([ya, yb])
    group = np.concatenate([np.zeros(n_a), np.ones(n_b)])
    references = {
        "beta_a": beta_a,
        "beta_b": beta_b,
        "reimers": 0.5 * (beta_a + beta_b),
        "cotton": (n_a * beta_a + n_b * beta_b) / (n_a + n_b),
        "neumark": ols_qr(pooled_design, pooled_y).beta,
        "pooled_group": ols_qr(np.column_stack([pooled_design, group]), pooled_y).beta[:-1],
    }
    twofold = {
        name: TwoFold(
            reference=ref,
            explained=float(ref @ dx),
            unexplained=float(xbar_b @ (beta_b - ref) + xbar_a @ (ref - beta_a)),
        )
        for name, ref in references.items()
    }

    # Dettagliata con normalizzazione di Yun
    beta_a_n, xbar_a_n = _yun_normalize(beta_a, xbar_a, blocks)
    beta_b_n, xbar_b_n = _yun_normalize(beta_b, xbar_b, blocks)
    dx_n = xbar_b_n - xbar_a_n
    dbeta_n = beta_b_n - beta_a_n
    detailed = DetailedDecomposition(
        names=(INTERCEPT_NAME, *cov_names, *ref_names),
        compositional=beta_a_n * dx_n,
        structural=xbar_a_n * dbeta_n,
        interaction=dx_n * dbeta_n,
    )

    return OaxacaResult(
        mean_a=mean_a,
        mean_b=mean_b,
        total=total,
        compositional=compositional,
        structural=structural,
        interaction=interaction,
        structural_share=share,
        xbar_a=xbar_a,
        xbar_b=xbar_b,
        fit_a=fit_a,
        fit_b=fit_b,
        twofold=twofold,
        detailed=detailed,
    )


class ThreeFoldBatch(NamedTuple):
    """Three-fold per un lotto di coppie di gruppi; NaN dove un disegno ha rango non pieno."""

    total: np.ndarray
    compositional: np.ndarray
    structural: np.ndarray
    interaction: np.ndarray
    valid: np.ndarray


def ols_qr_batch(design: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """OLS in lotto via QR: coefficienti (B, p) e maschera dei disegni a rango pieno."""
    q_mat, r_mat = np.linalg.qr(design)
    diag = np.abs(np.diagonal(r_mat, axis1=1, axis2=2))
    valid = diag.min(axis=1) > RANK_TOLERANCE * diag.max(axis=1)
    safe_r = np.where(valid[:, None, None], r_mat, np.eye(r_mat.shape[1])[None, :, :])
    qty = np.einsum("bij,bi->bj", q_mat, y)
    beta = np.linalg.solve(safe_r, qty[:, :, None])[:, :, 0]
    return beta, valid


def three_fold_batch(
    x_a: np.ndarray, y_a: np.ndarray, x_b: np.ndarray, y_b: np.ndarray
) -> ThreeFoldBatch:
    """Three-fold di oaxaca_blinder per B coppie di gruppi in un colpo solo.

    Parametri
    ---------
    x_a, x_b : np.ndarray
        Covariate (B, n_A, k) e (B, n_B, k), senza intercetta.
    y_a, y_b : np.ndarray
        Risposte (B, n_A) e (B, n_B).

    Restituisce
    -----------
    ThreeFoldBatch
        Componenti (B,), NaN e valid = False dove uno dei due disegni ha rango non pieno.
    """
    for arr, label in ((x_a, "x_a"), (x_b, "x_b")):
        if not isinstance(arr, np.ndarray) or arr.ndim != 3:
            raise ValueError(f"{label} must be a 3D np.ndarray (B, n, k)")
    if y_a.shape != x_a.shape[:2] or y_b.shape != x_b.shape[:2]:
        raise ValueError("y_a and y_b must have shape (B, n) matching x_a and x_b")
    ones_a = np.ones(x_a.shape[:2] + (1,))
    ones_b = np.ones(x_b.shape[:2] + (1,))
    design_a = np.concatenate([ones_a, x_a.astype(np.float64)], axis=2)
    design_b = np.concatenate([ones_b, x_b.astype(np.float64)], axis=2)
    beta_a, valid_a = ols_qr_batch(design_a, y_a.astype(np.float64))
    beta_b, valid_b = ols_qr_batch(design_b, y_b.astype(np.float64))
    xbar_a = design_a.mean(axis=1)
    xbar_b = design_b.mean(axis=1)
    dx = xbar_b - xbar_a
    dbeta = beta_b - beta_a
    valid = valid_a & valid_b
    nan = np.where(valid, 1.0, np.nan)
    return ThreeFoldBatch(
        total=(y_b.mean(axis=1) - y_a.mean(axis=1)) * nan,
        compositional=np.einsum("bj,bj->b", beta_a, dx) * nan,
        structural=np.einsum("bj,bj->b", xbar_a, dbeta) * nan,
        interaction=np.einsum("bj,bj->b", dx, dbeta) * nan,
        valid=valid,
    )


def _beta_covariance(fit: OlsFit) -> np.ndarray:
    """sigma^2 (X'X)^-1 come sigma^2 R^-1 R^-T, con R di QR (mai l'inversa di X'X)."""
    r_inv = scipy.linalg.solve_triangular(fit.r_factor, np.eye(fit.r_factor.shape[0]))
    return fit.sigma2 * (r_inv @ r_inv.T)


def oaxaca_iid_standard_errors(
    result: OaxacaResult, x_a: np.ndarray, x_b: np.ndarray
) -> OaxacaStandardErrors:
    """Errori standard iid delle componenti con il metodo delta (Jann 2008).

    V(beta) = sigma^2 (X'X)^-1 e V(x̄) = S_x / n (covarianza campionaria delle covariate,
    nulla per l'intercetta), con i gruppi indipendenti e i termini di ordine superiore
    trascurati:
    - V(C) = dx' V(beta_A) dx + beta_A' (V(x̄_A) + V(x̄_B)) beta_A;
    - V(S) = x̄_A' (V(beta_A) + V(beta_B)) x̄_A + dbeta' V(x̄_A) dbeta;
    - V(I) = dx' (V(beta_A) + V(beta_B)) dx + dbeta' (V(x̄_A) + V(x̄_B)) dbeta;
    - V(totale) = V(ȳ_A) + V(ȳ_B), con V(ȳ_g) = x̄_g' V(beta_g) x̄_g + beta_g' V(x̄_g) beta_g,
      cioè (sigma_g^2 + beta_g' S_x beta_g) / n_g.
    Assumono osservazioni indipendenti: con errori autocorrelati sono nominali.
    """
    xa = np.asarray(x_a, dtype=np.float64)
    xb = np.asarray(x_b, dtype=np.float64)

    def xbar_cov(x: np.ndarray) -> np.ndarray:
        k = x.shape[1]
        cov = np.zeros((k + 1, k + 1))
        cov[1:, 1:] = np.atleast_2d(np.cov(x, rowvar=False, ddof=1)) / x.shape[0]
        return cov

    v_beta_a = _beta_covariance(result.fit_a)
    v_beta_b = _beta_covariance(result.fit_b)
    v_xbar_a = xbar_cov(xa)
    v_xbar_b = xbar_cov(xb)
    beta_a, beta_b = result.fit_a.beta, result.fit_b.beta
    dx = result.xbar_b - result.xbar_a
    dbeta = beta_b - beta_a

    var_c = dx @ v_beta_a @ dx + beta_a @ (v_xbar_a + v_xbar_b) @ beta_a
    var_s = result.xbar_a @ (v_beta_a + v_beta_b) @ result.xbar_a + dbeta @ v_xbar_a @ dbeta
    var_i = dx @ (v_beta_a + v_beta_b) @ dx + dbeta @ (v_xbar_a + v_xbar_b) @ dbeta
    var_mean_a = result.xbar_a @ v_beta_a @ result.xbar_a + beta_a @ v_xbar_a @ beta_a
    var_mean_b = result.xbar_b @ v_beta_b @ result.xbar_b + beta_b @ v_xbar_b @ beta_b
    return OaxacaStandardErrors(
        total=float(math.sqrt(var_mean_a + var_mean_b)),
        compositional=float(math.sqrt(var_c)),
        structural=float(math.sqrt(var_s)),
        interaction=float(math.sqrt(var_i)),
    )
