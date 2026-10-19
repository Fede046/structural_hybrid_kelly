"""Verità nota per la decomposizione di Oaxaca-Blinder.

Generatore: in ogni gruppo g, n = 190 osservazioni con covariate x1 ~ N(m1_g, 1),
x2 ~ N(m2_g, 1) indipendenti e una dummy d ~ Bernoulli(p_g); risposta
y = b0_g + b1_g x1 + b2_g x2 + b3_g d (+ gamma w) + e, con e iid N(0, sigma^2) oppure AR(1)
con phi = 0.5 e varianza marginale sigma^2. Nel caso (d) w ~ N(mw_g, 1) è una covariata
rilevante che la decomposizione omette.

Con mu_g = (1, m1_g, m2_g, p_g), le componenti vere a valori attesi sono
C = beta_A'(mu_B - mu_A), S = mu_A'(beta_B - beta_A), I = (mu_B - mu_A)'(beta_B - beta_A),
totale = C + S + I; le stime OLS sono corrette per esse anche con errori AR(1), perché
beta_A stimato è indipendente da x̄_B e beta_g' x̄_g = ȳ_g.

Parametri fissati prima di eseguire (piano della validazione sintetica di Oaxaca-Blinder):
- gruppo A: m = (0, 0), p = 0.30, beta_A = (0.00, 0.10, 0.05, 0.20), sigma = 0.5;
- (a) misto: B con m = (0.5, -0.3), p = 0.50, beta_B = (0.10, 0.20, 0.05, 0.10);
- (b) solo composizione: medie di B come (a), beta_B = beta_A;
- (c) solo struttura: medie di B uguali ad A, beta_B come (a);
- (d) covariata omessa con drift virtuale puro: covariate incluse e coefficienti uguali
  nei due gruppi, gamma = 0.3 in entrambi, mw_A = 0 e mw_B = 1 (totale vero 0.3, tutto
  nella covariata omessa);
- (e) come (a), con errori AR(1) phi = 0.5.
R = 1 000 repliche per caso. Seed: SeedSequence(SEED_S8).spawn(5)[0] (posizione 0),
diviso con spawn(5), un generatore per caso nell'ordine (a)-(e), usato in
sequenza sulle repliche (prima il gruppo A, poi il B; in ogni gruppo x1 e x2, d, w se c'è,
poi gli errori).
"""

import math
from typing import Final, NamedTuple

import numpy as np

from shk.stats.oaxaca import TWOFOLD_REFERENCES, oaxaca_blinder, oaxaca_iid_standard_errors
from shk.stats.timeseries import generate_ar1_series

# Seed radice del Modulo 2 (decisione di progetto): la procedura in posizione i usa spawn(5)[i]
SEED_S8: Final[int] = 20261012
N_STORY_TASKS: Final[int] = 5
T45_STORY_POSITION: Final[int] = 0

N_PER_GROUP: Final[int] = 190
N_REPLICAS: Final[int] = 1_000
SIGMA: Final[float] = 0.5
AR_PHI: Final[float] = 0.5
Z_95: Final[float] = 1.959963984540054
COVARIATE_NAMES: Final[tuple[str, ...]] = ("x1", "x2", "d")
COMPONENTS: Final[tuple[str, ...]] = ("total", "compositional", "structural", "interaction")


class SyntheticCase(NamedTuple):
    """Parametri di un caso: medie (m1, m2, p) e coefficienti (b0, b1, b2, b3) per gruppo."""

    name: str
    means_a: tuple[float, float, float]
    beta_a: tuple[float, float, float, float]
    means_b: tuple[float, float, float]
    beta_b: tuple[float, float, float, float]
    ar_errors: bool
    omitted_gamma: float
    omitted_mean_a: float
    omitted_mean_b: float


_MEANS_A: Final[tuple[float, float, float]] = (0.0, 0.0, 0.30)
_BETA_A: Final[tuple[float, float, float, float]] = (0.00, 0.10, 0.05, 0.20)
_MEANS_B: Final[tuple[float, float, float]] = (0.5, -0.3, 0.50)
_BETA_B: Final[tuple[float, float, float, float]] = (0.10, 0.20, 0.05, 0.10)

CASES: Final[tuple[SyntheticCase, ...]] = (
    SyntheticCase("a_mixed", _MEANS_A, _BETA_A, _MEANS_B, _BETA_B, False, 0.0, 0.0, 0.0),
    SyntheticCase("b_composition", _MEANS_A, _BETA_A, _MEANS_B, _BETA_A, False, 0.0, 0.0, 0.0),
    SyntheticCase("c_structure", _MEANS_A, _BETA_A, _MEANS_A, _BETA_B, False, 0.0, 0.0, 0.0),
    SyntheticCase("d_omitted_virtual", _MEANS_A, _BETA_A, _MEANS_A, _BETA_A, False, 0.3, 0.0, 1.0),
    SyntheticCase("e_ar1", _MEANS_A, _BETA_A, _MEANS_B, _BETA_B, True, 0.0, 0.0, 0.0),
)

OB_SYNTHETIC_CSV_COLUMNS: Final[tuple[str, ...]] = (
    "row_type",
    "case",
    "component",
    "reference",
    "truth",
    "mean",
    "sd",
    "mc_se",
    "z_score",
    "coverage_iid95",
    "max_abs_residual",
    "mean_explained",
    "mean_unexplained",
    "mean_structural_share",
    "ratio_structural_to_total_of_means",
    "mean_ratio_structural_to_total",
)


def true_components(case: SyntheticCase) -> dict[str, float]:
    """Componenti vere a valori attesi (la covariata omessa entra solo nel totale).

    Nel caso (d) la covariata omessa sposta la media di y di gamma (mw_B - mw_A) senza
    cambiare coefficienti né medie delle covariate incluse: il totale vero è
    gamma (mw_B - mw_A) e C, S, I calcolate sulle covariate incluse valgono 0. La
    decomposizione che omette w attribuisce lo spostamento all'intercetta, cioè alla
    componente strutturale (nota 2.7 §9.2): per (d) si misura quella quota, non si
    confronta con questi valori.
    """
    mu_a = np.array((1.0, *case.means_a))
    mu_b = np.array((1.0, *case.means_b))
    beta_a = np.array(case.beta_a)
    beta_b = np.array(case.beta_b)
    comp = float(beta_a @ (mu_b - mu_a))
    struct = float(mu_a @ (beta_b - beta_a))
    inter = float((mu_b - mu_a) @ (beta_b - beta_a))
    omitted = case.omitted_gamma * (case.omitted_mean_b - case.omitted_mean_a)
    return {
        "total": comp + struct + inter + omitted,
        "compositional": comp,
        "structural": struct,
        "interaction": inter,
    }


def generate_group(
    n: int,
    means: tuple[float, float, float],
    beta: tuple[float, float, float, float],
    rng: np.random.Generator,
    ar_errors: bool = False,
    omitted_gamma: float = 0.0,
    omitted_mean: float = 0.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Un gruppo sintetico: covariate (n, 3) = (x1, x2, d) e risposta (n,).

    Estrazioni nell'ordine: x1 e x2 come rng.normal((n, 2)), d come rng.random(n) < p,
    w come rng.normal(n) solo se omitted_gamma != 0, poi gli errori (rng.normal(0, sigma, n)
    oppure generate_ar1_series con phi = AR_PHI, riscalata a varianza marginale sigma^2).
    """
    if isinstance(n, bool) or not isinstance(n, (int, np.integer)) or n < 2:
        raise ValueError(f"n must be an integer >= 2, got {n}")
    if not isinstance(rng, np.random.Generator):
        raise TypeError(f"rng must be an instance of np.random.Generator, got {type(rng)}")
    cont = rng.normal(size=(n, 2)) + np.array(means[:2])
    dummy = (rng.random(n) < means[2]).astype(np.float64)
    x = np.column_stack([cont, dummy])
    y = beta[0] + x @ np.array(beta[1:])
    if omitted_gamma != 0.0:
        y = y + omitted_gamma * (rng.normal(size=n) + omitted_mean)
    if ar_errors:
        errors = generate_ar1_series(AR_PHI, n, 1, rng)[0] * SIGMA * math.sqrt(1.0 - AR_PHI**2)
    else:
        errors = rng.normal(0.0, SIGMA, n)
    return x, y + errors


def spawn_t45_generators(seed: int = SEED_S8) -> tuple[np.random.Generator, ...]:
    """Un generatore per caso, da SeedSequence(seed).spawn(5)[0].spawn(len(CASES))."""
    if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)):
        raise TypeError(f"seed must be an integer, got {type(seed).__name__}")
    task_seed = np.random.SeedSequence(seed).spawn(N_STORY_TASKS)[T45_STORY_POSITION]
    return tuple(np.random.default_rng(s) for s in task_seed.spawn(len(CASES)))


class CaseReplicas(NamedTuple):
    """Stime per replica di un caso."""

    case: SyntheticCase
    components: dict[str, np.ndarray]
    standard_errors: dict[str, np.ndarray]
    twofold_explained: dict[str, np.ndarray]
    twofold_unexplained: dict[str, np.ndarray]
    structural_share: np.ndarray
    max_threefold_residual: float
    max_twofold_residual: float


def run_case(case: SyntheticCase, rng: np.random.Generator, n_replicas: int = N_REPLICAS) -> CaseReplicas:
    """Esegue le repliche di un caso e raccoglie stime, errori standard e residui d'identità."""
    comps = {c: np.empty(n_replicas) for c in COMPONENTS}
    ses = {c: np.empty(n_replicas) for c in COMPONENTS}
    expl = {r: np.empty(n_replicas) for r in TWOFOLD_REFERENCES}
    unexpl = {r: np.empty(n_replicas) for r in TWOFOLD_REFERENCES}
    share = np.empty(n_replicas)
    max_three = 0.0
    max_two = 0.0
    for i in range(n_replicas):
        xa, ya = generate_group(
            N_PER_GROUP, case.means_a, case.beta_a, rng, case.ar_errors,
            case.omitted_gamma, case.omitted_mean_a,
        )
        xb, yb = generate_group(
            N_PER_GROUP, case.means_b, case.beta_b, rng, case.ar_errors,
            case.omitted_gamma, case.omitted_mean_b,
        )
        res = oaxaca_blinder(xa, ya, xb, yb, names=COVARIATE_NAMES)
        se = oaxaca_iid_standard_errors(res, xa, xb)
        for c in COMPONENTS:
            comps[c][i] = getattr(res, c)
            ses[c][i] = getattr(se, c)
        for r in TWOFOLD_REFERENCES:
            expl[r][i] = res.twofold[r].explained
            unexpl[r][i] = res.twofold[r].unexplained
            max_two = max(max_two, abs(res.twofold[r].explained + res.twofold[r].unexplained - res.total))
        share[i] = res.structural_share
        max_three = max(max_three, abs(res.compositional + res.structural + res.interaction - res.total))
    return CaseReplicas(case, comps, ses, expl, unexpl, share, max_three, max_two)


def _empty() -> dict[str, object]:
    return {col: "" for col in OB_SYNTHETIC_CSV_COLUMNS}


def build_case_records(rep: CaseReplicas) -> list[dict[str, object]]:
    """Record del CSV per un caso: componenti, identità, two-fold, quote."""
    truth = true_components(rep.case)
    n = rep.structural_share.shape[0]
    records: list[dict[str, object]] = []
    for c in COMPONENTS:
        est = rep.components[c]
        mean = float(est.mean())
        sd = float(est.std(ddof=1))
        mc_se = sd / math.sqrt(n)
        covered = np.abs(est - truth[c]) <= Z_95 * rep.standard_errors[c]
        rec = _empty()
        rec.update(
            row_type="component", case=rep.case.name, component=c, truth=truth[c], mean=mean,
            sd=sd, mc_se=mc_se, z_score=(mean - truth[c]) / mc_se,
            coverage_iid95=float(np.mean(covered)),
        )
        records.append(rec)
    rec = _empty()
    rec.update(row_type="identity", case=rep.case.name, component="threefold",
               max_abs_residual=rep.max_threefold_residual)
    records.append(rec)
    rec = _empty()
    rec.update(row_type="identity", case=rep.case.name, component="twofold",
               max_abs_residual=rep.max_twofold_residual)
    records.append(rec)
    for r in TWOFOLD_REFERENCES:
        rec = _empty()
        rec.update(row_type="twofold", case=rep.case.name, reference=r,
                   mean_explained=float(rep.twofold_explained[r].mean()),
                   mean_unexplained=float(rep.twofold_unexplained[r].mean()))
        records.append(rec)
    total = rep.components["total"]
    struct = rep.components["structural"]
    rec = _empty()
    rec.update(
        row_type="share", case=rep.case.name,
        mean_structural_share=float(np.nanmean(rep.structural_share)),
        ratio_structural_to_total_of_means=float(struct.mean() / total.mean()),
        mean_ratio_structural_to_total=float(np.mean(struct / total)),
    )
    records.append(rec)
    return records


def evaluate_synthetic_cases(
    seed: int = SEED_S8, n_replicas: int = N_REPLICAS
) -> tuple[list[CaseReplicas], list[dict[str, object]]]:
    """Esegue i cinque casi e restituisce repliche e record del CSV."""
    reps = [run_case(case, rng, n_replicas) for case, rng in zip(CASES, spawn_t45_generators(seed))]
    records = [rec for rep in reps for rec in build_case_records(rep)]
    return reps, records
