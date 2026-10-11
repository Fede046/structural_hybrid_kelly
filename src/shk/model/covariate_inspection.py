"""Ispezione delle covariate del Modulo 2 e regole di specificazione (T46, US-C7.2).

Le regole si applicano sul solo training pooled (le tre stagioni di training, 1 140
partite) e sono fissate prima di vedere i numeri:
- (i) flag neopromossa: "mai vista" (flag_new) e "tornante" (flag_returning) restano
  distinti se ciascuno ha in media almeno MIN_FLAG_MATCHES_PER_SEASON = 30 partite per
  stagione di training; altrimenti si usa il solo flag_promoted;
- (ii) si toglie una alla volta la covariata con VIF massimo finché tutti i VIF sono
  <= VIF_MAX = 5 (a parità esatta, la prima nell'ordine delle candidate);
- (iii) model_entropy H(p̂) resta solo se sopravvive a (ii): è una conseguenza di (ii),
  verificata in coda.
La validazione riceve le stesse tabelle descrittive, che non decidono nulla (protocollo
esteso, decisione S9).

ANOVA a una via di δ per covariata: quintili per le continue (bordi = quantili 0.2, 0.4,
0.6, 0.8 dell'insieme analizzato; un valore uguale a un bordo va nel gruppo superiore),
livelli 0/1 per i flag. F nominale con soglia F(k − 1, N − k) al 95%; soglia calibrata col
metodo centrato di T40 (calibrate_centered_threshold) a L = L_PW circolare arrotondata
della serie di δ centrata per gruppo, B = N_BOOT; η² = SS_between / SS_total; per i flag
d di Cohen (gruppo con flag meno gruppo senza, deviazione standard pooled) e
OVL = 2 Φ(−|d| / 2). Seed: SeedSequence(SEED_S8).spawn(5)[1] (T46 in posizione 1),
spawn(2) per insieme (training, validazione), poi spawn(len(ANOVA_COVARIATES)), un
generatore per covariata.
"""

import math
from typing import Final, NamedTuple

import numpy as np
import pandas as pd
import scipy.stats

from shk.model.module2_data import COVARIATE_COLUMNS
from shk.stats.anova import oneway_anova
from shk.stats.bootstrap import optimal_block_length, round_block_length
from shk.stats.false_rejection import (
    ALPHA,
    N_BOOT,
    calibrate_centered_threshold,
    center_by_group,
    critical_value_nominal,
)
from shk.stats.oaxaca import ols_qr
from shk.stats.oaxaca_synthetic import N_STORY_TASKS, SEED_S8

T46_STORY_POSITION: Final[int] = 1
MODULE2_WINDOWS: Final[tuple[int, ...]] = (40, 80, 120, 190)
MIN_FLAG_MATCHES_PER_SEASON: Final[float] = 30.0
VIF_MAX: Final[float] = 5.0
N_QUINTILES: Final[int] = 5
CONTINUOUS_COVARIATES: Final[tuple[str, ...]] = (
    "log_odds_ratio",
    "market_entropy",
    "elo_diff",
    "position",
    "model_entropy",
)
FLAG_COVARIATES: Final[tuple[str, ...]] = ("flag_new", "flag_returning", "flag_promoted")
ANOVA_COVARIATES: Final[tuple[str, ...]] = CONTINUOUS_COVARIATES + FLAG_COVARIATES
MODEL_ENTROPY: Final[str] = "model_entropy"

COVARIATES_CSV_COLUMNS: Final[tuple[str, ...]] = (
    "row_type",
    "dataset",
    "season",
    "covariate",
    "other",
    "window",
    "step",
    "n",
    "mean",
    "sd",
    "min",
    "q25",
    "median",
    "q75",
    "max",
    "count_min",
    "count_mean",
    "count_max",
    "value",
    "f_stat",
    "threshold_nominal",
    "threshold_calibrated",
    "block_length",
    "reject_nominal",
    "reject_calibrated",
    "eta2",
    "cohen_d",
    "ovl",
    "included",
    "reason",
)


class FlagRuleResult(NamedTuple):
    """Esito della regola (i): flag da usare e medie per stagione."""

    flags: tuple[str, ...]
    mean_new_per_season: float
    mean_returning_per_season: float


class VifStep(NamedTuple):
    """Un passo della regola (ii): VIF di tutte le covariate rimaste e quella tolta."""

    step: int
    vifs: dict[str, float]
    removed: str | None


def apply_flag_rule(train: pd.DataFrame) -> FlagRuleResult:
    """Regola (i) sul training pooled."""
    per_season = train.groupby("season")[["flag_new", "flag_returning"]].sum()
    mean_new = float(per_season["flag_new"].mean())
    mean_ret = float(per_season["flag_returning"].mean())
    if mean_new >= MIN_FLAG_MATCHES_PER_SEASON and mean_ret >= MIN_FLAG_MATCHES_PER_SEASON:
        flags: tuple[str, ...] = ("flag_new", "flag_returning")
    else:
        flags = ("flag_promoted",)
    return FlagRuleResult(flags, mean_new, mean_ret)


def variance_inflation_factors(matrix: np.ndarray) -> np.ndarray:
    """VIF_j = 1 / (1 − R²_j), con R²_j dell'OLS (via QR) della colonna j sulle altre e costante.

    Solleva
    -------
    ValueError
        Se ci sono meno di due colonne o una colonna è costante.
    """
    x = np.asarray(matrix, dtype=np.float64)
    if x.ndim != 2 or x.shape[1] < 2:
        raise ValueError("matrix must be 2D with at least two columns")
    vifs = np.empty(x.shape[1])
    for j in range(x.shape[1]):
        y = x[:, j]
        sst = float(((y - y.mean()) ** 2).sum())
        if sst <= 0.0:
            raise ValueError(f"Column {j} is constant")
        others = np.column_stack([np.ones(x.shape[0]), np.delete(x, j, axis=1)])
        fit = ols_qr(others, y)
        ssr = float(((y - others @ fit.beta) ** 2).sum())
        r2 = 1.0 - ssr / sst
        vifs[j] = math.inf if r2 >= 1.0 else 1.0 / (1.0 - r2)
    return vifs


def vif_elimination(train: pd.DataFrame, candidates: tuple[str, ...]) -> list[VifStep]:
    """Regola (ii): toglie la covariata col VIF massimo finché tutti i VIF sono <= VIF_MAX."""
    remaining = list(candidates)
    steps: list[VifStep] = []
    step = 0
    while True:
        if len(remaining) == 1:
            # Con una sola covariata il VIF vale 1 per definizione
            steps.append(VifStep(step, {remaining[0]: 1.0}, None))
            return steps
        vifs = variance_inflation_factors(train[remaining].to_numpy(dtype=np.float64))
        vif_map = dict(zip(remaining, (float(v) for v in vifs)))
        worst = int(np.argmax(vifs))
        if vifs[worst] <= VIF_MAX:
            steps.append(VifStep(step, vif_map, None))
            return steps
        removed = remaining.pop(worst)
        steps.append(VifStep(step, vif_map, removed))
        step += 1


class Specification(NamedTuple):
    """Specificazione finale del Modulo 2."""

    covariates: tuple[str, ...]
    flag_rule: FlagRuleResult
    vif_steps: list[VifStep]
    excluded: dict[str, str]


def derive_specification(train: pd.DataFrame) -> Specification:
    """Applica le regole (i), (ii), (iii) al training pooled."""
    flag_rule = apply_flag_rule(train)
    candidates = (
        "log_odds_ratio", "market_entropy", "elo_diff", *flag_rule.flags, "position", MODEL_ENTROPY,
    )
    steps = vif_elimination(train, candidates)
    removed = [s.removed for s in steps if s.removed is not None]
    final = tuple(c for c in candidates if c not in removed)
    excluded: dict[str, str] = {}
    for flag in FLAG_COVARIATES:
        if flag not in flag_rule.flags:
            excluded[flag] = "rule (i): flag variant not used"
    for s in steps:
        if s.removed is not None:
            excluded[s.removed] = f"rule (ii): max VIF {s.vifs[s.removed]:.6g} > {VIF_MAX} at step {s.step}"
    if MODEL_ENTROPY not in final:
        excluded[MODEL_ENTROPY] = excluded.get(MODEL_ENTROPY, "") + "; rule (iii): removed by (ii)"
    return Specification(final, flag_rule, steps, excluded)


def quintile_labels(values: np.ndarray) -> np.ndarray:
    """Gruppi 0..k−1 per quintili; i gruppi vuoti per valori ripetuti si comprimono."""
    edges = np.quantile(values, [0.2, 0.4, 0.6, 0.8])
    raw = np.searchsorted(edges, values, side="right")
    _, labels = np.unique(raw, return_inverse=True)
    return labels.astype(np.int64)


def covariate_labels(frame: pd.DataFrame, covariate: str) -> np.ndarray:
    """Etichette di gruppo per l'ANOVA: quintili per le continue, 0/1 per i flag."""
    values = frame[covariate].to_numpy(dtype=np.float64)
    if covariate in FLAG_COVARIATES:
        return values.astype(np.int64)
    return quintile_labels(values)


def cohen_d_and_ovl(y: np.ndarray, flag: np.ndarray) -> tuple[float, float]:
    """d di Cohen (con flag meno senza, s pooled ddof = 1) e OVL = 2 Φ(−|d|/2)."""
    y1, y0 = y[flag == 1], y[flag == 0]
    n1, n0 = y1.size, y0.size
    pooled = math.sqrt(((n1 - 1) * y1.var(ddof=1) + (n0 - 1) * y0.var(ddof=1)) / (n1 + n0 - 2))
    d = float((y1.mean() - y0.mean()) / pooled)
    return d, float(2.0 * scipy.stats.norm.cdf(-abs(d) / 2.0))


def spawn_t46_generators(seed: int = SEED_S8) -> tuple[tuple[np.random.Generator, ...], ...]:
    """(training, validazione) x covariate di ANOVA_COVARIATES."""
    if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)):
        raise TypeError(f"seed must be an integer, got {type(seed).__name__}")
    task_seed = np.random.SeedSequence(seed).spawn(N_STORY_TASKS)[T46_STORY_POSITION]
    return tuple(
        tuple(np.random.default_rng(s) for s in ds.spawn(len(ANOVA_COVARIATES)))
        for ds in task_seed.spawn(2)
    )


def _record(**fields: object) -> dict[str, object]:
    rec: dict[str, object] = {c: "" for c in COVARIATES_CSV_COLUMNS}
    for k, v in fields.items():
        if k not in rec:
            raise KeyError(k)
        rec[k] = v
    return rec


def anova_records(frame: pd.DataFrame, dataset: str, rngs: tuple[np.random.Generator, ...]) -> list[dict[str, object]]:
    """ANOVA di δ per covariata con soglia nominale e calibrata (metodo centrato di T40)."""
    delta = frame["delta"].to_numpy(dtype=np.float64)
    records = []
    for covariate, rng in zip(ANOVA_COVARIATES, rngs):
        labels = covariate_labels(frame, covariate)
        k = int(labels.max()) + 1
        res = oneway_anova([delta[labels == g] for g in range(k)])
        nominal = critical_value_nominal(k=k, n_obs=int(delta.size), alpha=ALPHA)
        centered = center_by_group(delta, labels)
        l_val = round_block_length(optimal_block_length(centered).circular)
        calibrated = calibrate_centered_threshold(delta, labels, l_val, N_BOOT, ALPHA, rng)
        d, ovl = ("", "")
        if covariate in FLAG_COVARIATES:
            d, ovl = cohen_d_and_ovl(delta, labels)
        records.append(
            _record(
                row_type="anova", dataset=dataset, covariate=covariate, n=int(delta.size),
                value=k, f_stat=float(res.f_statistic), threshold_nominal=nominal,
                threshold_calibrated=calibrated, block_length=l_val,
                reject_nominal=bool(res.f_statistic > nominal),
                reject_calibrated=bool(res.f_statistic > calibrated),
                eta2=float(res.ss_between / res.ss_total), cohen_d=d, ovl=ovl,
            )
        )
    return records


def descriptive_records(frame: pd.DataFrame, dataset: str) -> list[dict[str, object]]:
    """Distribuzioni, conteggi per cella, finestre, deviazione Elo nelle finestre, correlazioni, VIF."""
    records: list[dict[str, object]] = []
    for col in ("delta", *COVARIATE_COLUMNS):
        v = frame[col].to_numpy(dtype=np.float64)
        q = np.quantile(v, [0.25, 0.5, 0.75])
        records.append(_record(
            row_type="distribution", dataset=dataset, covariate=col, n=int(v.size),
            mean=float(v.mean()), sd=float(v.std(ddof=1)), min=float(v.min()), q25=float(q[0]),
            median=float(q[1]), q75=float(q[2]), max=float(v.max()),
        ))
    for season, grp in frame.groupby("season", sort=False):
        for flag in FLAG_COVARIATES:
            records.append(_record(row_type="cell_count", dataset=dataset, season=season,
                                   covariate=flag, n=int(len(grp)), value=int(grp[flag].sum())))
    sd_all = float(frame["elo_diff"].std(ddof=1))
    for w in MODULE2_WINDOWS:
        sds: list[float] = []
        counts: dict[str, list[int]] = {f: [] for f in FLAG_COVARIATES}
        for _, grp in frame.groupby("season", sort=False):
            for start in range(0, len(grp) - w + 1, w):
                win = grp.iloc[start:start + w]
                sds.append(float(win["elo_diff"].std(ddof=1)))
                for f in FLAG_COVARIATES:
                    counts[f].append(int(win[f].sum()))
        for f in FLAG_COVARIATES:
            c = np.array(counts[f])
            records.append(_record(row_type="window_count", dataset=dataset, covariate=f, window=w,
                                   n=int(c.size), count_min=int(c.min()), count_mean=float(c.mean()),
                                   count_max=int(c.max())))
        records.append(_record(row_type="elo_window_sd", dataset=dataset, covariate="elo_diff",
                               window=w, n=len(sds), value=float(np.mean(sds)) / sd_all))
    continuous = list(CONTINUOUS_COVARIATES) + list(FLAG_COVARIATES)
    corr = frame[continuous].corr().to_numpy()
    for i, a in enumerate(continuous):
        for j, b in enumerate(continuous):
            if j > i:
                records.append(_record(row_type="correlation", dataset=dataset, covariate=a, other=b,
                                       value=float(corr[i, j])))
    return records


def evaluate_covariates(frame: pd.DataFrame, seed: int = SEED_S8) -> tuple[Specification, list[dict[str, object]]]:
    """Specificazione sul training e record del CSV results/us_c7_2_covariates.csv."""
    train = frame[frame["role"] == "training"]
    valid = frame[frame["role"] == "validation"]
    spec = derive_specification(train)
    rngs_train, rngs_valid = spawn_t46_generators(seed)

    records: list[dict[str, object]] = []
    records.append(_record(row_type="flag_rule", dataset="training", covariate="flag_new",
                           value=spec.flag_rule.mean_new_per_season))
    records.append(_record(row_type="flag_rule", dataset="training", covariate="flag_returning",
                           value=spec.flag_rule.mean_returning_per_season))
    for step in spec.vif_steps:
        for cov, vif in step.vifs.items():
            records.append(_record(row_type="vif", dataset="training", covariate=cov, step=step.step,
                                   value=vif, reason="removed" if cov == step.removed else ""))
    candidates_all = ("log_odds_ratio", "market_entropy", "elo_diff", "flag_new", "flag_returning",
                      "flag_promoted", "position", MODEL_ENTROPY)
    for cov in candidates_all:
        records.append(_record(row_type="specification", dataset="training", covariate=cov,
                               included=cov in spec.covariates, reason=spec.excluded.get(cov, "kept")))
    for dataset, sub in (("training", train), ("validation", valid)):
        records.extend(descriptive_records(sub, dataset))
        flags_used = list(spec.flag_rule.flags)
        cols = ["log_odds_ratio", "market_entropy", "elo_diff", *flags_used, "position", MODEL_ENTROPY]
        vifs = variance_inflation_factors(sub[cols].to_numpy(dtype=np.float64))
        for cov, vif in zip(cols, vifs):
            records.append(_record(row_type="vif_full", dataset=dataset, covariate=cov, value=float(vif)))
        final_cols = list(spec.covariates)
        if len(final_cols) >= 2:
            vifs = variance_inflation_factors(sub[final_cols].to_numpy(dtype=np.float64))
            for cov, vif in zip(final_cols, vifs):
                records.append(_record(row_type="vif_final", dataset=dataset, covariate=cov, value=float(vif)))
    records.extend(anova_records(train, "training", rngs_train))
    records.extend(anova_records(valid, "validation", rngs_valid))
    return spec, records
