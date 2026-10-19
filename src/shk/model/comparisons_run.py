"""Esecuzioni e tabelle dei confronti fra agenti: run iid, confronti con intervalli, falsi allarmi, π e λ di C2.

Seed: SeedSequence(SEED_S10).spawn(5)[1] (posizione 1), spawn(3):
- figlio 0: indici del bootstrap a due livelli, gli stessi per l'intervallo block e per
  quello iid (numeri casuali comuni: il rapporto fra le ampiezze non dipende dagli indici);
- figlio 1: seed del run iid (L = 1), spawn(19) per stagione in ordine cronologico e
  spawn(N_SEEDS) per seed;
- figlio 2: simulazione di copertura.

Falsi allarmi (passo 4): sotto H₀ sono gli allarmi sui seed dell'esecuzione congelata sulla validazione, cioè su stagioni
ricostruite per stationary bootstrap delle date a L_PW della serie per data di δ, che
rompe la non stazionarietà; sui dati sono quelli della realizzazione osservata. Allarmi di
C1 (accensioni) e dei detector di D non dipendono dalla configurazione: si usa F = 0.
π e λ di C2: supervisore con la W di C2 sui seed dell'esecuzione congelata sulla validazione (gli stessi SeedSequence) e sulla
realizzazione osservata; a ogni data attiva π = quota strutturale e λ = module3_lambda
sull'esito candidato di ogni partita della data, mediato sulle partite.
"""

import math
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from shk.kelly.agents import DateResults, estimated_expected_values
from shk.model.agent_c import Module2Supervisor
from shk.model.comparisons import (
    COMPARISONS,
    PRIMARY_METRICS,
    comparison_available,
    coverage_simulation,
    effect_size_sigma,
    effect_sizes,
    percentile_interval,
    pooled_bootstrap,
    season_differences,
    t_cluster_interval,
    two_level_indices,
)
from shk.model.frozen_agents import AGENT_ORDER, arm_windows, check_frozen_constants
from shk.model.frozen_params import FROZEN_PARAMS_PATH, load_frozen_params
from shk.model.module2 import STATE_ACTIVE
from shk.model.module3 import module3_lambda
from shk.model.module3_synthetic import N_STORY_TASKS
from shk.model.season_bootstrap import reconstruct_season, season_block_length
from shk.model.task_seeds import story_task_sequence
from shk.model.validation_run import (
    CONFIG_NAMES,
    METRICS,
    SEED_S10,
    ValidationResult,
    ValidationSeason,
    run_instance,
    spawn_t55_sequences,
    validation_inputs,
)

T56_STORY_POSITION: Final[int] = 1
IID_BLOCK_LENGTH: Final[float] = 1.0
MAIN_CONFIG: Final[str] = "gbp_0.01"
ALARM_AGENTS: Final[tuple[str, ...]] = ("C1", "D_ADWIN", "D_PH")
QUANTILES: Final[tuple[float, ...]] = (0.05, 0.25, 0.5, 0.75, 0.95)

COMPARISON_COLUMNS: Final[tuple[str, ...]] = (
    "row_type", "config", "comparison", "metric", "estimate", "se_boot_block", "ci_block_low", "ci_block_high",
    "ci_block_pct_low", "ci_block_pct_high", "estimate_iid", "se_boot_iid", "ci_iid_low", "ci_iid_high",
    "ci_iid_pct_low", "ci_iid_pct_high", "width_ratio_block_iid", "sigma", "d", "ovl",
    "r2_upper", "r2_canonical", "block_excludes_zero", "sign", "block_pct_excludes_zero", "sign_pct",
    "conclusion_changed",
    "season", "agent", "h0_mean_alarms", "h0_share_seeds_with_alarm", "observed_alarms",
    "quantity", "source", "n_values", "q05", "q25", "q50", "q75", "q95", "share_active_dates",
    "design_tau", "design_sigma", "design_delta", "n_seasons", "n_seeds", "n_replicas", "coverage",
    "coverage_corrected",
)


def t56_sequences(seed: int | np.random.SeedSequence = SEED_S10) -> list[np.random.SeedSequence]:
    """Tre figli di SeedSequence(SEED_S10).spawn(5)[1] (vedi modulo); seed è la radice."""
    return story_task_sequence(seed, T56_STORY_POSITION, N_STORY_TASKS).spawn(3)


def run_iid_season(params_path: str, season: ValidationSeason,
                   seed_seqs: Sequence[np.random.SeedSequence]) -> np.ndarray:
    """Seed iid (L = 1) di una stagione, tutti gli agenti e configurazioni: (C, A, M, N)."""
    params = load_frozen_params(params_path)
    check_frozen_constants(params)
    covariates = list(params.fixed["covariates"])
    out = np.full((len(CONFIG_NAMES), len(AGENT_ORDER), len(METRICS), len(seed_seqs)), np.nan)
    for k, ss in enumerate(seed_seqs):
        rec = reconstruct_season(season.inp, np.random.default_rng(ss), IID_BLOCK_LENGTH, covariates=covariates)
        out[..., k] = run_instance(params, rec, season.fit)
    return out


def evaluate_iid(frame: pd.DataFrame, block: ValidationResult, params_path: Path | str = FROZEN_PARAMS_PATH,
                 workers: int = 1, seed: int | np.random.SeedSequence = SEED_S10) -> ValidationResult:
    """Run iid aggiuntivo degli stessi agenti, con N_SEEDS seed per stagione."""
    params = load_frozen_params(params_path)
    seasons = validation_inputs(frame, list(params.fixed["covariates"]))
    n = int(params.fixed["n_seeds"])
    seqs = [s.spawn(n) for s in t56_sequences(seed)[1].spawn(len(seasons))]
    args = [(str(params_path), s, q) for s, q in zip(seasons, seqs)]
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            outputs = list(pool.map(run_iid_season, *zip(*args)))
    else:
        outputs = [run_iid_season(*a) for a in args]
    return block._replace(seeds=np.stack(outputs), l_pw=np.ones_like(block.l_pw))


def _excludes(lo: float, hi: float) -> tuple[bool, str]:
    excludes = bool(lo > 0.0 or hi < 0.0)
    return excludes, (("+" if lo > 0.0 else "-") if excludes else "")


def comparison_records(block: ValidationResult, iid: ValidationResult, seed: int | np.random.SeedSequence = SEED_S10) -> list[dict[str, object]]:
    """Righe "comparison": stima, intervalli principali (t corretto) e percentile, block e iid, effect size."""
    n_seasons = block.seeds.shape[0]
    idx = two_level_indices(n_seasons, block.seeds.shape[-1], np.random.default_rng(t56_sequences(seed)[0]))
    records = []
    for ci, config in enumerate(CONFIG_NAMES):
        for a, b in COMPARISONS:
            if not comparison_available(block, ci, a, b):
                continue
            for metric in PRIMARY_METRICS:
                est = float(np.mean(season_differences(block, ci, a, b, metric)))
                est_iid = float(np.mean(season_differences(iid, ci, a, b, metric)))
                boot_b = pooled_bootstrap(block, ci, a, b, metric, idx)
                boot_i = pooled_bootstrap(iid, ci, a, b, metric, idx)
                lo, hi, se_b = t_cluster_interval(est, boot_b, n_seasons)
                lo_i, hi_i, se_i = t_cluster_interval(est_iid, boot_i, n_seasons)
                plo, phi = percentile_interval(boot_b)
                plo_i, phi_i = percentile_interval(boot_i)
                sigma = effect_size_sigma(block, ci, a, b, metric)
                excludes, sign = _excludes(lo, hi) if math.isfinite(lo) else (False, "")
                excludes_p, sign_p = _excludes(plo, phi)
                width_iid = hi_i - lo_i
                rec = {c: "" for c in COMPARISON_COLUMNS}
                rec.update(row_type="comparison", config=config, comparison=f"{a}-{b}", metric=metric,
                           estimate=est, se_boot_block=se_b, ci_block_low=lo, ci_block_high=hi,
                           ci_block_pct_low=plo, ci_block_pct_high=phi, estimate_iid=est_iid, se_boot_iid=se_i,
                           ci_iid_low=lo_i, ci_iid_high=hi_i, ci_iid_pct_low=plo_i, ci_iid_pct_high=phi_i,
                           width_ratio_block_iid=(hi - lo) / width_iid if width_iid > 0 else math.nan,
                           sigma=sigma, block_excludes_zero=excludes, sign=sign,
                           block_pct_excludes_zero=excludes_p, sign_pct=sign_p,
                           conclusion_changed=bool(sign != sign_p))
                rec.update(effect_sizes(est, sigma))
                records.append(rec)
    return records


def alarm_records(block: ValidationResult) -> list[dict[str, object]]:
    """Righe "alarms" per stagione e agente: sotto H₀ (seed) e sui dati (realizzazione osservata)."""
    m = METRICS.index("n_alarms")
    records = []
    for si, season in enumerate(block.seasons):
        for agent in ALARM_AGENTS:
            ai = AGENT_ORDER.index(agent)
            h0 = block.seeds[si, 0, ai, m]
            rec = {c: "" for c in COMPARISON_COLUMNS}
            rec.update(row_type="alarms", config=CONFIG_NAMES[0], season=season, agent=agent,
                       h0_mean_alarms=float(np.mean(h0)), h0_share_seeds_with_alarm=float(np.mean(h0 > 0)),
                       observed_alarms=float(block.observed[si, 0, ai, m]))
            records.append(rec)
    return records


def pi_lambda_trace(season: str, inp, covariates: Sequence[str], window: int) -> tuple[list[float], list[float], int]:
    """π e λ medio della data alle date attive di C2, e numero di date (supervisore da solo)."""
    sup = Module2Supervisor(season, inp.dates, inp.x, covariates, window)
    pis, lams = [], []
    days = np.unique(inp.dates)
    for d in days:
        st = sup.state_at(d)
        if st.output.state == STATE_ACTIVE:
            rows = np.flatnonzero(inp.dates == d)
            ev = estimated_expected_values(inp.probs[rows], inp.odds[rows])
            best = ev.argmax(axis=1)
            r = np.arange(rows.shape[0])
            lam = module3_lambda(True, st.window_a, st.window_b, float(st.output.result.structural),
                                 inp.odds[rows][r, best], ev[r, best])
            pis.append(float(st.output.result.structural_share))
            lams.append(float(np.mean(lam)))
        rows = np.flatnonzero(inp.dates == d)
        sup.observe(DateResults(date=d, probs=inp.probs[rows], odds=inp.odds[rows], outcomes=inp.outcomes[:, rows]))
    return pis, lams, int(days.shape[0])


def pi_lambda_season(params_path: str, season: ValidationSeason,
                     seed_seqs: Sequence[np.random.SeedSequence]) -> dict[str, object]:
    """π e λ di C2 sui seed dell'esecuzione congelata sulla validazione (H₀) e sulla realizzazione osservata, per una stagione."""
    params = load_frozen_params(params_path)
    covariates = list(params.fixed["covariates"])
    window = arm_windows(params)["C2"]
    l_pw = season_block_length(season.inp)
    h0_pi, h0_lam, h0_dates, h0_active = [], [], 0, 0
    for ss in seed_seqs:
        rec = reconstruct_season(season.inp, np.random.default_rng(ss), l_pw, covariates=covariates)
        p, lam, n = pi_lambda_trace(season.inp.season, rec, covariates, window)
        h0_pi += p
        h0_lam += lam
        h0_dates += n
        h0_active += len(p)
    o_pi, o_lam, o_dates = pi_lambda_trace(season.inp.season, season.inp, covariates, window)
    return {"season": season.inp.season, "h0_pi": h0_pi, "h0_lambda": h0_lam, "h0_share_active": h0_active / h0_dates,
            "obs_pi": o_pi, "obs_lambda": o_lam, "obs_share_active": len(o_pi) / o_dates}


def pi_lambda_records(frame: pd.DataFrame, params_path: Path | str = FROZEN_PARAMS_PATH, workers: int = 1,
                      seed: int | np.random.SeedSequence = SEED_S10) -> list[dict[str, object]]:
    """Righe "pi_lambda": quantili di π e λ di C2 per stagione e pooled, sotto H₀ e sui dati."""
    params = load_frozen_params(params_path)
    seasons = validation_inputs(frame, list(params.fixed["covariates"]))
    seqs = spawn_t55_sequences(len(seasons), int(params.fixed["n_seeds"]), seed)
    args = [(str(params_path), s, q) for s, q in zip(seasons, seqs)]
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            outputs = list(pool.map(pi_lambda_season, *zip(*args)))
    else:
        outputs = [pi_lambda_season(*a) for a in args]
    records = []
    pooled: dict[tuple[str, str], list[float]] = {}
    for out in outputs + [None]:
        if out is None:
            season, items = "pooled", [((q, s), v, math.nan) for (q, s), v in pooled.items()]
        else:
            season = out["season"]
            items = [(("pi", "h0"), out["h0_pi"], out["h0_share_active"]),
                     (("lambda", "h0"), out["h0_lambda"], out["h0_share_active"]),
                     (("pi", "observed"), out["obs_pi"], out["obs_share_active"]),
                     (("lambda", "observed"), out["obs_lambda"], out["obs_share_active"])]
            for key, values, _ in items:
                pooled.setdefault(key, []).extend(values)
        for (quantity, source), values, share in items:
            rec = {c: "" for c in COMPARISON_COLUMNS}
            rec.update(row_type="pi_lambda", season=season, agent="C2", quantity=quantity, source=source,
                       n_values=len(values), share_active_dates="" if math.isnan(share) else share)
            if values:
                for q, col in zip(QUANTILES, ("q05", "q25", "q50", "q75", "q95")):
                    rec[col] = float(np.quantile(values, q))
            records.append(rec)
    return records


def coverage_records(block: ValidationResult, seed: int | np.random.SeedSequence = SEED_S10, n_replicas: int = 1000) -> list[dict[str, object]]:
    """Copertura del bootstrap a due livelli su un disegno sintetico con le dimensioni e le varianze dei dati.

    Disegno fissato prima di calcolare la copertura: 19 stagioni, N_SEEDS seed, differenza
    C2 − C1 della log-ricchezza finale nella configurazione principale; σ = radice della
    media delle varianze fra seed, τ² = varianza fra stagioni delle medie meno σ²/N (almeno
    0), delta = stima puntuale. Si riporta anche la lettura con un solo seed per stagione.
    """
    ci = CONFIG_NAMES.index(MAIN_CONFIG)
    m = METRICS.index("final_log_wealth")
    diff = block.seeds[:, ci, AGENT_ORDER.index("C2"), m] - block.seeds[:, ci, AGENT_ORDER.index("C1"), m]
    n_seasons, n_seeds = diff.shape
    sigma = float(math.sqrt(np.mean(np.var(diff, axis=1, ddof=1))))
    tau = float(math.sqrt(max(0.0, np.var(diff.mean(axis=1), ddof=1) - sigma**2 / n_seeds)))
    delta = float(diff.mean())
    records = []
    rng = np.random.default_rng(t56_sequences(seed)[2])
    for variant, one in (("seeds_resampled", False), ("one_seed_per_season", True)):
        cov, cov_t = coverage_simulation(rng, n_replicas, n_seasons, n_seeds, delta, tau, sigma, one_seed_per_season=one)
        rec = {c: "" for c in COMPARISON_COLUMNS}
        rec.update(row_type="coverage", config=MAIN_CONFIG, comparison="C2-C1", metric="final_log_wealth",
                   source=variant, design_tau=tau, design_sigma=sigma, design_delta=delta, n_seasons=n_seasons,
                   n_seeds=n_seeds, n_replicas=n_replicas, coverage=cov, coverage_corrected=cov_t)
        records.append(rec)
    return records

