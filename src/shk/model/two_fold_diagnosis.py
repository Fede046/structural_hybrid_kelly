"""Diagnosi di Blinder-Oaxaca a due termini, sulla grandezza che ha fatto scattare l'allarme.

La diagnosi di agent_c.SchemeAgent applica la scomposizione a tre termini alla media di δ fra la
stagione di calibrazione e le ultime W partite, e chiama strutturale l'errore se la sola componente
strutturale supera una soglia. Sui dati veri ha tre difetti (thesis: «separa poco»):
1. scompone la media di δ, che le covariate spiegano per il 2,5%, mentre l'allarme scatta quasi
   sempre sulla dispersione, che le covariate spiegano per circa un quarto; la proposta del relatore
   era capire quanto c'è di strutturale nel cambiamento della varianza;
2. stima una regressione su W = 40 partite consecutive, in cui «position» copre un intervallo
   stretto: struttura e interazione diventano due numeri grandi e opposti, e la decisione guarda
   solo il primo;
3. la soglia strutturale è calibrata su finestre ricampionate da tutta la stagione, non su partite
   consecutive, quindi è superata per caso molto più spesso del livello nominale.

Qui la scomposizione è quella a due termini con i coefficienti del riferimento (Oaxaca 1973): la
stagione di calibrazione è il gruppo di riferimento per costruzione, quindi la scelta del gruppo non
è arbitraria. Per una risposta y con regressione di riferimento β_A:

    ȳ_B − ȳ_A = (x̄_B − x̄_A)ᵀ β_A  +  media_B(y − xᵀ β_A)
                 spiegato (composizione)   non spiegato (struttura e interazione)

Nella finestra non si stima nessuna regressione: il termine non spiegato è la media, sulle W partite,
dei residui del modello di riferimento. Le risposte sono due, una per ciascuna statistica dell'allarme:
- media: y = δ; la parte non spiegata del peggioramento è u_mean = −media_B(δ − xᵀ β_A);
- dispersione: y = |δ − mediana del riferimento|, la risposta di Brown-Forsythe;
  u_dispersion = media_B(y − xᵀ β_A).
Diagnosi con allarme: errore strutturale se la parte non spiegata della grandezza che ha fatto
scattare l'allarme supera la sua soglia (con le due statistiche oltre soglia, basta una delle due);
altrimenti errore nei dati. La risposta sulla puntata è quella di SchemeAgent.

Soglie (calibrate_reference_diagnosis): moving block bootstrap della stagione di calibrazione, W righe
ricampionate (covariate e δ insieme) contro la regressione della stagione intera, come in
agent_c.calibrate_reference_thresholds; ciascuna parte non spiegata al livello α/2.

La diagnosi dice se il cambiamento è spiegato dal tipo di partite, non se l'allarme è vero: un falso
allarme senza cambio di composizione risulta «strutturale». Il controllo dei falsi allarmi è compito
delle soglie dell'allarme (shk.model.season_thresholds).

Versioni: C3_ref_dx, C3_ref_stop_dx (soglie dell'allarme per giornata) e C3_ref_season_dx,
C3_ref_stop_season_dx (per stagione). È una variante successiva a tutte le altre.

Seed: SeedSequence(SEED_S27).spawn(2) = (soglie per fit, in ordine cronologico; bootstrap della
scomposizione per stagione).
"""

from collections.abc import Mapping, Sequence
from typing import Final, NamedTuple

import numpy as np
import pandas as pd

from shk.kelly.agents import Agent
from shk.kelly.environment import run_paired_backtest
from shk.kelly.staking import BASE_LAMBDA
from shk.model.agent_c import (
    DIAGNOSIS_COMPOSITIONAL,
    DIAGNOSIS_NONE,
    DIAGNOSIS_STRUCTURAL,
    N_BOOT,
    SCHEME_STOP_CLEAR,
    SCHEME_STOP_SEASON,
    Module2Supervisor,
    ReferenceData,
    SchemeAgent,
    reference_statistics,
)
from shk.model.frozen_agents import n_alarms, scheme_window, share_lambda_zero
from shk.model.frozen_params import FrozenParams, load_frozen_params
from shk.model.paired_backtest import CONFIGURATIONS
from shk.model.scheme_reference_run import ReferenceSetup, build_reference_agents
from shk.model.scheme_run import fit_block_length
from shk.model.season_input import SeasonInput, season_input_from_frame, training_seasons
from shk.model.season_thresholds import PER_DATE_ARMS, SEASON_ARMS, decision_ends, season_agents
from shk.model.timing_placebo import SeasonSchedules, extract_schedules
from shk.model.validation_run import ValidationSeason
from shk.stats.calibration import compute_order_statistic_index, moving_block_indices
from shk.stats.false_rejection import ALPHA
from shk.stats.oaxaca import three_fold_batch

SEED_S27: Final[int] = 20261114
DX_ARMS: Final[dict[str, str]] = {
    "C3_ref_dx": "R1", "C3_ref_stop_dx": "R1", "C3_ref_season_dx": "R1", "C3_ref_stop_season_dx": "R1",
}
OLD_ARMS: Final[tuple[str, ...]] = PER_DATE_ARMS + tuple(SEASON_ARMS)
RUN_ARMS: Final[tuple[str, ...]] = ("B_0.25",) + OLD_ARMS + tuple(DX_ARMS)
RESPONSES: Final[tuple[str, ...]] = ("mean", "dispersion")
DIAGNOSIS_COLUMNS: Final[tuple[str, ...]] = (
    "fit", "window", "block_length", "n_reference", "r2_mean", "r2_dispersion",
    "unexplained_mean_threshold", "unexplained_dispersion_threshold",
)


class ReferenceDiagnosis(NamedTuple):
    """Regressioni di riferimento e soglie della diagnosi a due termini di un fit."""

    median: float
    beta_mean: np.ndarray           # (k + 1,) regressione di δ sulle covariate, con intercetta
    beta_dispersion: np.ndarray     # (k + 1,) regressione di |δ − mediana| sulle covariate
    mean_threshold: float           # soglia della parte non spiegata del peggioramento della media
    dispersion_threshold: float     # soglia della parte non spiegata dell'aumento di dispersione


def _design(x: np.ndarray) -> np.ndarray:
    xx = np.asarray(x, dtype=np.float64)
    return np.concatenate([np.ones(xx.shape[:-1] + (1,)), xx], axis=-1)


def reference_coefficients(x: np.ndarray, delta: np.ndarray) -> tuple[float, np.ndarray, np.ndarray]:
    """Mediana di δ e coefficienti OLS (con intercetta) di δ e di |δ − mediana| sulle covariate del riferimento."""
    xx, y = np.asarray(x, dtype=np.float64), np.asarray(delta, dtype=np.float64)
    if xx.ndim != 2 or y.shape != (xx.shape[0],) or xx.shape[0] <= xx.shape[1] + 1:
        raise ValueError(f"need x (n, k) and delta (n,) with n > k + 1, got {xx.shape}, {y.shape}")
    design = _design(xx)
    if np.linalg.matrix_rank(design) < design.shape[1]:
        raise ValueError("the reference design is rank deficient")
    median = float(np.median(y))
    beta_mean, *_ = np.linalg.lstsq(design, y, rcond=None)
    beta_disp, *_ = np.linalg.lstsq(design, np.abs(y - median), rcond=None)
    return median, beta_mean, beta_disp


def unexplained_parts(x: np.ndarray, delta: np.ndarray, median: float, beta_mean: np.ndarray,
                      beta_dispersion: np.ndarray) -> tuple[np.ndarray | float, np.ndarray | float]:
    """Parti non spiegate (u_mean, u_dispersion) di finestre (..., W, k), (..., W); positive = peggio del riferimento."""
    design = _design(x)
    y = np.asarray(delta, dtype=np.float64)
    u_mean = -(y - design @ beta_mean).mean(axis=-1)
    u_disp = (np.abs(y - median) - design @ beta_dispersion).mean(axis=-1)
    return (float(u_mean), float(u_disp)) if y.ndim == 1 else (u_mean, u_disp)


def explained_parts(x: np.ndarray, reference_x: np.ndarray, beta_mean: np.ndarray,
                    beta_dispersion: np.ndarray) -> tuple[float, float]:
    """Parti spiegate dalla composizione: (peggioramento della media, aumento della dispersione)."""
    dx = np.asarray(x, dtype=np.float64).mean(axis=0) - np.asarray(reference_x, dtype=np.float64).mean(axis=0)
    return float(-dx @ beta_mean[1:]), float(dx @ beta_dispersion[1:])


def calibrate_reference_diagnosis(x: np.ndarray, delta: np.ndarray, window: int, block_length: int,
                                  rng: np.random.Generator, n_boot: int = N_BOOT,
                                  alpha: float = ALPHA) -> ReferenceDiagnosis:
    """Regressioni del riferimento e soglie delle due parti non spiegate al livello α/2 ciascuna (vedi modulo)."""
    xx, y = np.asarray(x, dtype=np.float64), np.asarray(delta, dtype=np.float64)
    median, beta_mean, beta_disp = reference_coefficients(xx, y)
    if window > y.shape[0]:
        raise ValueError(f"need at least W = {window} reference matches, got {y.shape[0]}")
    idx = moving_block_indices(y.shape[0], block_length, n_boot, rng)[:, :window]
    u_mean, u_disp = unexplained_parts(xx[idx], y[idx], median, beta_mean, beta_disp)
    k = compute_order_statistic_index(n_boot, alpha / 2.0)
    return ReferenceDiagnosis(median, beta_mean, beta_disp, float(np.sort(u_mean)[k - 1]),
                              float(np.sort(u_disp)[k - 1]))


def _r2(design: np.ndarray, y: np.ndarray, beta: np.ndarray) -> float:
    return float(1.0 - (y - design @ beta).var() / y.var())


def diagnosis_setups(train: pd.DataFrame, params: FrozenParams,
                     seed: int = SEED_S27) -> tuple[dict[str, ReferenceDiagnosis], list[dict]]:
    """Per fit: diagnosi a due termini calibrata sulla stagione di training, e righe delle soglie."""
    covariates = list(params.fixed["covariates"])
    fits = training_seasons(train)
    w = scheme_window(params)
    out, records = {}, []
    for fit, seq in zip(fits, np.random.SeedSequence(seed).spawn(2)[0].spawn(len(fits))):
        inp = season_input_from_frame(train, fit, covariates)
        length = fit_block_length(inp)
        diag = calibrate_reference_diagnosis(inp.x, inp.delta, w, length, np.random.default_rng(seq))
        design = _design(inp.x)
        out[fit] = diag
        records.append({"fit": fit, "window": w, "block_length": length, "n_reference": int(inp.delta.shape[0]),
                        "r2_mean": _r2(design, inp.delta, diag.beta_mean),
                        "r2_dispersion": _r2(design, np.abs(inp.delta - diag.median), diag.beta_dispersion),
                        "unexplained_mean_threshold": diag.mean_threshold,
                        "unexplained_dispersion_threshold": diag.dispersion_threshold})
    return out, records


class TwoFoldSchemeAgent(SchemeAgent):
    """Schema con riferimento fisso e diagnosi a due termini sulla grandezza che ha fatto scattare l'allarme.

    Allarme e risposta sulla puntata sono quelli di SchemeAgent (reference=True); cambia solo la
    diagnosi (vedi modulo). mean_threshold e dispersion_threshold sono le soglie dell'allarme.
    """

    def __init__(self, name: str, supervisor: Module2Supervisor, kappa: float, mean_threshold: float,
                 dispersion_threshold: float, diagnosis: ReferenceDiagnosis, stop: str,
                 base_lambda: float = BASE_LAMBDA) -> None:
        super().__init__(name, supervisor, kappa, mean_threshold, dispersion_threshold, 0.0, stop,
                         base_lambda=base_lambda, reference=True)
        self._diagnosis = diagnosis

    def _diagnose(self, day: np.datetime64) -> str:
        stats = self._supervisor.reference_diagnostics(day)
        if stats is None:
            return DIAGNOSIS_NONE
        by_mean, by_dispersion = stats[0] > self._mean_threshold, stats[1] > self._dispersion_threshold
        if not (by_mean or by_dispersion):
            return DIAGNOSIS_NONE
        window = self._supervisor.reference_window(day)
        assert window is not None
        d = self._diagnosis
        u_mean, u_disp = unexplained_parts(window[0], window[1], d.median, d.beta_mean, d.beta_dispersion)
        structural = (by_mean and u_mean > d.mean_threshold) or (by_dispersion and u_disp > d.dispersion_threshold)
        return DIAGNOSIS_STRUCTURAL if structural else DIAGNOSIS_COMPOSITIONAL


def dx_agents(params: FrozenParams, per_date: ReferenceSetup, per_season: ReferenceSetup,
              diagnosis: ReferenceDiagnosis, supervisor: Module2Supervisor) -> list[Agent]:
    """Le quattro versioni di DX_ARMS: soglie dell'allarme per giornata o per stagione, riprende o resta fermo."""
    kappa, base = float(params.calibrated["c1_kappa"]), float(params.fixed["c0_lambda"])
    plan = zip(DX_ARMS, (per_date, per_date, per_season, per_season),
               (SCHEME_STOP_CLEAR, SCHEME_STOP_SEASON, SCHEME_STOP_CLEAR, SCHEME_STOP_SEASON))
    return [TwoFoldSchemeAgent(name, supervisor, kappa, setup.mean_threshold, setup.dispersion_threshold,
                               diagnosis, stop, base_lambda=base) for name, setup, stop in plan]


def _agents(params: FrozenParams, per_date: ReferenceSetup, per_season: ReferenceSetup,
            diagnosis: ReferenceDiagnosis, season: ValidationSeason) -> list[Agent]:
    inp = season.inp
    supervisor = Module2Supervisor(inp.season, inp.dates, inp.x, list(params.fixed["covariates"]),
                                   scheme_window(params), reference=ReferenceData(per_date.x, per_date.delta))
    return (build_reference_agents(params, per_date, supervisor, ("B_0.25",) + PER_DATE_ARMS)
            + season_agents(params, per_season, supervisor)
            + dx_agents(params, per_date, per_season, diagnosis, supervisor))


def run_real_season(params_path: str, per_date: Mapping[str, ReferenceSetup],
                    per_season: Mapping[str, ReferenceSetup], diagnoses: Mapping[str, ReferenceDiagnosis],
                    season: ValidationSeason) -> list[dict]:
    """La stagione vera nelle tre configurazioni di puntata minima: una riga per configurazione × agente."""
    params = load_frozen_params(params_path)
    inp, fit = season.inp, season.fit
    rows = []
    for config, min_stake in CONFIGURATIONS:
        agents = _agents(params, per_date[fit], per_season[fit], diagnoses[fit], season)
        runs = run_paired_backtest(agents, inp.dates, inp.probs, inp.odds, inp.outcomes, min_stake,
                                   fallback_policy=params.fixed["fallback_policy"])
        for run, agent in zip(runs, agents):
            final = float(run.wealth[0, -1])
            rows.append({"season": inp.season, "fit_through": fit, "config": config, "agent": run.name,
                         "log_wealth": float(np.log(final)) if final > 0.0 else -np.inf,
                         "n_alarms": n_alarms(agent), "share_days_zero": share_lambda_zero(agent)})
    return rows


def run_schedule_season(params_path: str, per_date: Mapping[str, ReferenceSetup],
                        per_season: Mapping[str, ReferenceSetup], diagnoses: Mapping[str, ReferenceDiagnosis],
                        season: ValidationSeason) -> SeasonSchedules:
    """Calendari senza puntata minima delle versioni di DX_ARMS (per il controllo placebo)."""
    params = load_frozen_params(params_path)
    fit = season.fit
    agents = [a for a in _agents(params, per_date[fit], per_season[fit], diagnoses[fit], season)
              if a.name == "B_0.25" or a.name in DX_ARMS]
    return extract_schedules(params, season, agents, DX_ARMS)


def decision_records(season: ValidationSeason, per_date: ReferenceSetup, diagnosis: ReferenceDiagnosis,
                     window: int) -> list[dict]:
    """A ogni giornata di decisione della stagione vera: allarme (soglie per giornata) e le due diagnosi.

    three_fold: T = −S della scomposizione a tre termini oltre la soglia strutturale di per_date;
    two_fold: le parti non spiegate oltre le loro soglie.
    """
    inp = season.inp
    rows = []
    for end in decision_ends(inp.dates, window):
        x, delta = inp.x[end - window:end], inp.delta[end - window:end]
        f_mean, f_disp = reference_statistics(per_date.delta, delta)
        tf = three_fold_batch(per_date.x[None], per_date.delta[None], x[None], delta[None])
        u_mean, u_disp = unexplained_parts(x, delta, diagnosis.median, diagnosis.beta_mean, diagnosis.beta_dispersion)
        rows.append({"season": inp.season, "fit_through": season.fit,
                     "by_mean": bool(f_mean > per_date.mean_threshold),
                     "by_dispersion": bool(f_disp > per_date.dispersion_threshold),
                     "three_fold": bool(tf.valid[0] and -tf.structural[0] > per_date.structural_threshold),
                     "total": float(tf.total[0]), "composition": float(tf.compositional[0]),
                     "structure": float(tf.structural[0]), "interaction": float(tf.interaction[0]),
                     "two_fold_mean": bool(u_mean > diagnosis.mean_threshold),
                     "two_fold_dispersion": bool(u_disp > diagnosis.dispersion_threshold)})
    return rows


def component_summary(records: Sequence[Mapping]) -> list[dict]:
    """Quanto variano, fra le giornate di decisione, le componenti a tre termini della media di δ.

    Deviazione standard di scarto totale, composizione, struttura e interazione, e correlazioni della
    struttura con lo scarto totale e con l'interazione: mostrano se la componente strutturale, su cui
    decide la diagnosi a tre termini, segue lo scarto che deve spiegare.
    """
    df = pd.DataFrame(list(records)).dropna(subset=["structure"])
    rows = [{"statistic": f"sd_{name}", "value": float(df[name].std(ddof=0))}
            for name in ("total", "composition", "structure", "interaction")]
    rows += [
        {"statistic": "corr_structure_total", "value": float(np.corrcoef(df["structure"], df["total"])[0, 1])},
        {"statistic": "corr_structure_interaction",
         "value": float(np.corrcoef(df["structure"], df["interaction"])[0, 1])},
        {"statistic": "corr_structure_plus_interaction_total",
         "value": float(np.corrcoef(df["structure"] + df["interaction"], df["total"])[0, 1])},
        {"statistic": "n_decisions", "value": float(len(df))},
    ]
    return rows


def diagnosis_table(records: Sequence[Mapping]) -> list[dict]:
    """Per tipo di allarme: giornate e quota di diagnosi strutturali con le due scomposizioni.

    Senza allarme la diagnosi non si applica: la quota è quella che si avrebbe applicandola comunque
    (per la diagnosi a due termini, una delle due parti non spiegate oltre soglia).
    """
    df = pd.DataFrame(list(records))
    two = np.where(df["by_mean"] & df["by_dispersion"], df["two_fold_mean"] | df["two_fold_dispersion"],
                   np.where(df["by_mean"], df["two_fold_mean"],
                            np.where(df["by_dispersion"], df["two_fold_dispersion"],
                                     df["two_fold_mean"] | df["two_fold_dispersion"])))
    groups = {"none": ~df["by_mean"] & ~df["by_dispersion"], "mean_only": df["by_mean"] & ~df["by_dispersion"],
              "dispersion_only": ~df["by_mean"] & df["by_dispersion"], "both": df["by_mean"] & df["by_dispersion"]}
    return [{"alarm": name, "n_days": int(mask.sum()),
             "share_structural_three_fold": float(df.loc[mask, "three_fold"].mean()),
             "share_structural_two_fold": float(two[mask.to_numpy()].mean())} for name, mask in groups.items()]


def season_decomposition(reference: ReferenceSetup, inp: SeasonInput, reference_block: int,
                         rng: np.random.Generator, n_boot: int = N_BOOT) -> list[dict]:
    """Scomposizione a tre termini della stagione intera contro la stagione di calibrazione, per media e dispersione.

    Intervalli percentili al 95% da un moving block bootstrap dei due gruppi (blocchi di lunghezza
    reference_block per il riferimento e fit_block_length per la stagione); la mediana della risposta
    di dispersione è ricalcolata su ogni ricampionamento del riferimento.
    """
    def components(xa: np.ndarray, ya: np.ndarray, xb: np.ndarray, yb: np.ndarray) -> dict[str, np.ndarray]:
        med = np.median(ya, axis=1, keepdims=True)
        out = {}
        for response, a, b in (("mean", ya, yb), ("dispersion", np.abs(ya - med), np.abs(yb - med))):
            tf = three_fold_batch(xa, a, xb, b)
            out[response] = np.stack([tf.total, tf.compositional, tf.structural, tf.interaction])
        return out

    observed = components(reference.x[None], reference.delta[None], inp.x[None], inp.delta[None])
    ia = moving_block_indices(reference.delta.shape[0], reference_block, n_boot, rng)
    ib = moving_block_indices(inp.delta.shape[0], fit_block_length(inp), n_boot, rng)
    boot = components(reference.x[ia], reference.delta[ia], inp.x[ib], inp.delta[ib])
    rows = []
    for response in RESPONSES:
        for j, part in enumerate(("total", "composition", "structure", "interaction")):
            draws = boot[response][j]
            draws = draws[np.isfinite(draws)]
            low, high = np.quantile(draws, [0.025, 0.975])
            rows.append({"season": inp.season, "response": response, "component": part,
                         "value": float(observed[response][j, 0]), "low": float(low), "high": float(high)})
    return rows
