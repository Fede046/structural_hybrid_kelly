"""Schema del relatore (C3) dentro l'architettura del backtest appaiato (decisione di progetto).

Supervisore (Module2Supervisor). Un'istanza per esecuzione dell'ambiente, condivisa dai bracci
che lo usano (C3, C3_stop, C3_and), così Oaxaca-Blinder si calcola una volta per data. Riceve
all'inizio solo le covariate pre-partita della stagione, nell'ordine delle partite
dell'ambiente. Gli esiti gli arrivano solo da Agent.observe_results, che l'ambiente chiama dopo
il regolamento di ogni data: per ogni partita regolata registra δ = ln p̂(x) − ln q(x), con q di
Shin dalle quote della data (decisione di progetto). L'aggiornamento è idempotente per data,
perché i bracci inoltrano le stesse DateResults.

Alla data di decisione d il supervisore restituisce:
- le finestre A e B di δ (delta_windows): le 2W partite osservate più recenti con Date < d;
- l'uscita di module2.module2_at_date (state_at, con cache per data) con anteriorità stretta
  (Date < d), sulla catena della sola stagione.

Schema del relatore (SchemeAgent; mail del prof. Roccetti, 2026-11): il supervisore monitora
con l'ANOVA i residui δ e dà l'allarme; il ricalibratore usa Oaxaca-Blinder per decidere la puntata.
Il supervisore cambia solo le frazioni, mai previsioni, selezione o ripiego, che restano quelli
di Agent.decide.
- Allarme alla data d, sulle finestre A e B di δ: F dell'ANOVA a una via sulla media, contata
  solo se la media di B è minore di quella di A (peggioramento), oppure F di Brown-Forsythe
  (ANOVA sulle deviazioni assolute dalla mediana, eteroschedasticità), contata solo se la
  dispersione di B è maggiore di quella di A. Allarme se una delle due supera la sua soglia
  (C3, C3_stop), oppure, alla lettera della mail («la media degli errori cresce e la varianza
  esplode»), se le superano entrambe (C3_and); con meno di 2W partite non c'è allarme.
- Diagnosi con allarme: errore strutturale se Oaxaca-Blinder è attivo e T = −S supera la soglia
  strutturale congelata alla stessa W, con S la componente strutturale three-fold (degrado di δ
  a composizione fissa); altrimenti errore di composizione (dati), anche a rango non pieno.
- λ: senza allarme 0.25; composizione 0.25·κ; strutturale 0 finché dura l'allarme (C3) oppure
  fino a fine stagione (C3_stop: «finché il modello non viene ri-parametrizzato», e nella
  stagione il Modulo 1 non si ri-parametrizza).
Frazione sull'esito selezionato: kelly_staking(p̂, o − 1, λ), elemento per elemento. Con una
regola del lavoratore (shk.kelly.outcome_rules.with_outcome_rule) l'esito è quello della regola.

W, κ e la soglia strutturale sono i valori congelati in config/frozen_params.toml (chiavi c1_*:
vengono dalla calibrazione del 2026-10, documentata sul branch confronti-controllo).

Soglie dell'allarme (calibrate_scheme_thresholds): moving block bootstrap della serie di δ del
fit, dei ricampionamenti di lunghezza n si tengono le prime 2W posizioni come finestre A e B,
B = 999; ogni F con segno ha livello α/2 (Bonferroni), così l'allarme ha livello α = 0.05 al più.
Per C3_and (calibrate_scheme_and_thresholds), sugli stessi ricampionamenti: le due soglie sono
statistiche d'ordine allo stesso indice k, il più basso per cui la quota di ricampionamenti con
entrambe le F oltre soglia è ancora <= α.
"""

import math
from collections.abc import Sequence
from typing import Final

import numpy as np
import pandas as pd

from shk.kelly.agents import Agent, DateResults, DateView
from shk.kelly.staking import BASE_LAMBDA, kelly_staking
from shk.market.devig import devig_probabilities
from shk.model.module2 import STATE_ACTIVE, STATE_NOT_ACTIVE, Module2Data, Module2Output, module2_at_date
from shk.stats.calibration import compute_order_statistic_index, moving_block_indices
from shk.stats.false_rejection import ALPHA
from shk.stats.anova import oneway_anova_vectorized
from shk.stats.variance_change import brown_forsythe

N_BOOT: Final[int] = 999
SCHEME_STOP_CLEAR: Final[str] = "until_clear"
SCHEME_STOP_SEASON: Final[str] = "until_season_end"
SCHEME_STOPS: Final[tuple[str, ...]] = (SCHEME_STOP_CLEAR, SCHEME_STOP_SEASON)
SCHEME_ALARM_OR: Final[str] = "or"
SCHEME_ALARM_AND: Final[str] = "and"
SCHEME_ALARMS: Final[tuple[str, ...]] = (SCHEME_ALARM_OR, SCHEME_ALARM_AND)
DIAGNOSIS_NONE: Final[str] = "none"
DIAGNOSIS_COMPOSITIONAL: Final[str] = "compositional"
DIAGNOSIS_STRUCTURAL: Final[str] = "structural"


class Module2Supervisor:
    """Supervisore online per un'esecuzione dell'ambiente (vedi modulo).

    Parametri
    ---------
    season : str
        Stagione dell'esecuzione.
    dates : np.ndarray
        Date (N,) delle partite, nell'ordine dell'ambiente (non decrescenti).
    covariates_x : np.ndarray
        Covariate pre-partita (N, k) nello stesso ordine.
    covariate_names : Sequence[str]
        Nomi delle k covariate.
    window : int
        W delle finestre A e B.
    devig_method : str, default "shin"
        Metodo di de-vigging di q per δ (decisione di progetto).

    Solleva
    -------
    ValueError
        Se le forme non sono coerenti o le date non sono ordinate.
    """

    def __init__(
        self,
        season: str,
        dates: np.ndarray,
        covariates_x: np.ndarray,
        covariate_names: Sequence[str],
        window: int,
        devig_method: str = "shin",
    ) -> None:
        self._devig_method = devig_method
        d = np.asarray(dates).astype("datetime64[ns]")
        x = np.asarray(covariates_x, dtype=np.float64)
        names = tuple(covariate_names)
        if d.ndim != 1 or x.ndim != 2 or x.shape != (d.shape[0], len(names)):
            raise ValueError("dates (N,), covariates_x (N, k) and k covariate names are required")
        if np.any(d[1:] < d[:-1]):
            raise ValueError("dates must be non-decreasing")
        if isinstance(window, bool) or not isinstance(window, (int, np.integer)) or window < len(names) + 2:
            raise ValueError(f"window must be an integer >= {len(names) + 2}, got {window}")
        n = d.shape[0]
        self._season = season
        self._dates = d
        self._x = x.copy()
        self._names = names
        self._window = int(window)
        self._observed = np.zeros(n, dtype=bool)
        self._delta = np.full(n, np.nan)
        self._observed_dates: set[np.datetime64] = set()
        self._cache: dict[np.datetime64, Module2Output] = {}

    @property
    def window(self) -> int:
        """W delle finestre A e B."""
        return self._window

    def observe(self, results: DateResults) -> None:
        """Registra gli esiti di una data regolata (una sola volta per data, M = 1)."""
        if results.outcomes.shape[0] != 1:
            raise ValueError("Module2Supervisor requires a single replica (M = 1)")
        day = np.datetime64(results.date, "ns")
        if day in self._observed_dates:
            return
        rows = np.flatnonzero(self._dates == day)
        if rows.shape[0] != results.probs.shape[0]:
            raise ValueError("results do not match the season calendar of the supervisor")
        probs = np.asarray(results.probs, dtype=np.float64)
        realized = np.asarray(results.outcomes[0], dtype=np.int64)
        q = devig_probabilities(np.asarray(results.odds, dtype=np.float64), self._devig_method)
        idx = np.arange(rows.shape[0])
        self._delta[rows] = np.log(probs[idx, realized]) - np.log(q[idx, realized])
        self._observed[rows] = True
        self._observed_dates.add(day)

    def cutoff(self, decision_date: np.datetime64) -> np.datetime64:
        """Data di taglio: si usano le partite con Date < taglio."""
        return decision_date

    def _eligible(self, decision_date: np.datetime64) -> np.ndarray:
        observed = np.flatnonzero(self._observed)
        cut = np.datetime64(self.cutoff(np.datetime64(decision_date, "ns")), "ns")
        return observed[self._dates[observed] < cut]

    def delta_windows(self, decision_date: np.datetime64) -> tuple[np.ndarray, np.ndarray] | None:
        """δ delle finestre A e B (partite osservate con Date < d); None con meno di 2W partite."""
        eligible = self._eligible(decision_date)
        if eligible.shape[0] < 2 * self._window:
            return None
        return self._delta[eligible[-2 * self._window:-self._window]], self._delta[eligible[-self._window:]]

    def state_at(self, decision_date: np.datetime64) -> Module2Output:
        """Uscita di Oaxaca-Blinder (module2_at_date) sulle partite osservate con Date < d (in cache)."""
        day = np.datetime64(decision_date, "ns")
        if day in self._cache:
            return self._cache[day]
        cut = np.datetime64(self.cutoff(day), "ns")
        observed = np.flatnonzero(self._observed)
        if observed.shape[0] == 0:
            output = Module2Output(self._season, pd.Timestamp(cut), self._window, STATE_NOT_ACTIVE, 0, 0, 0,
                                   math.nan, math.nan, None, math.nan)
        else:
            data = Module2Data(
                seasons=np.full(observed.shape[0], self._season, dtype=object),
                dates=self._dates[observed],
                chain=np.zeros(observed.shape[0], dtype=np.int64),
                delta=self._delta[observed],
                x=self._x[observed],
                covariates=self._names,
            )
            output = module2_at_date(data, self._season, cut, self._window)
        self._cache[day] = output
        return output


def _kelly_fractions(p_hat: np.ndarray, b: np.ndarray, lam: np.ndarray) -> np.ndarray:
    fractions = np.empty(p_hat.shape[0], dtype=np.float64)
    for i in range(p_hat.shape[0]):
        fractions[i] = kelly_staking(float(p_hat[i]), float(b[i]), lam=float(lam[i]))
    return fractions


class SchemeAgent(Agent):
    """C3, C3_stop e C3_and: schema del relatore, allarme ANOVA sui residui δ e risposta dalla three-fold (vedi modulo).

    Parametri
    ---------
    name : str
        Nome dell'agente.
    supervisor : Module2Supervisor
        Supervisore condiviso dell'esecuzione.
    kappa : float
        Riduzione di λ con errore di composizione, in [0, 1].
    mean_threshold, dispersion_threshold : float
        Soglie dell'F di media e dell'F di Brown-Forsythe con segno (calibrate_scheme_thresholds).
    structural_threshold : float
        Soglia di T = −S oltre la quale l'errore è strutturale (valore congelato alla stessa W).
    stop : str
        SCHEME_STOP_CLEAR (λ = 0 finché dura l'allarme) o SCHEME_STOP_SEASON (λ = 0 fino a
        fine stagione: nella stagione il Modulo 1 non si ri-parametrizza).
    base_lambda : float, default 0.25
        λ senza allarme.
    alarm : str, default SCHEME_ALARM_OR
        SCHEME_ALARM_OR (una delle due F oltre soglia) o SCHEME_ALARM_AND (entrambe).
    """

    def __init__(self, name: str, supervisor: Module2Supervisor, kappa: float, mean_threshold: float,
                 dispersion_threshold: float, structural_threshold: float, stop: str,
                 base_lambda: float = BASE_LAMBDA, alarm: str = SCHEME_ALARM_OR) -> None:
        super().__init__(name)
        if not isinstance(supervisor, Module2Supervisor):
            raise TypeError("supervisor must be a Module2Supervisor")
        for label, value in (("kappa", kappa), ("base_lambda", base_lambda)):
            if isinstance(value, bool) or not isinstance(value, (float, np.floating)) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{label} must be a float in [0, 1], got {value!r}")
        for label, value in (("mean_threshold", mean_threshold), ("dispersion_threshold", dispersion_threshold),
                             ("structural_threshold", structural_threshold)):
            if isinstance(value, bool) or not isinstance(value, (float, np.floating)) or not math.isfinite(value):
                raise ValueError(f"{label} must be a finite float, got {value!r}")
        if stop not in SCHEME_STOPS:
            raise ValueError(f"stop must be one of {SCHEME_STOPS}, got {stop!r}")
        if alarm not in SCHEME_ALARMS:
            raise ValueError(f"alarm must be one of {SCHEME_ALARMS}, got {alarm!r}")
        self._alarm = alarm
        self._supervisor = supervisor
        self._kappa = float(kappa)
        self._mean_threshold = float(mean_threshold)
        self._dispersion_threshold = float(dispersion_threshold)
        self._structural_threshold = float(structural_threshold)
        self._stop = stop
        self._base_lambda = float(base_lambda)
        self._stopped = False
        self._n_onsets = 0
        self._previous_alarm = False
        self._lambda_by_date: dict[np.datetime64, float] = {}
        self._diagnosis_by_date: dict[np.datetime64, str] = {}

    @property
    def n_onsets(self) -> int:
        """Accensioni dell'allarme ANOVA fino all'ultima data di decisione."""
        return self._n_onsets

    @property
    def lambda_by_date(self) -> dict[np.datetime64, float]:
        """λ applicato a ogni data di decisione."""
        return dict(self._lambda_by_date)

    @property
    def diagnosis_by_date(self) -> dict[np.datetime64, str]:
        """Diagnosi a ogni data di decisione: "none", "compositional" o "structural"."""
        return dict(self._diagnosis_by_date)

    def _diagnose(self, day: np.datetime64) -> str:
        windows = self._supervisor.delta_windows(day)
        if windows is None:
            return DIAGNOSIS_NONE
        f_mean, f_dispersion = scheme_statistics(windows[0], windows[1])
        exceed = (f_mean > self._mean_threshold, f_dispersion > self._dispersion_threshold)
        if not (all(exceed) if self._alarm == SCHEME_ALARM_AND else any(exceed)):
            return DIAGNOSIS_NONE
        out = self._supervisor.state_at(day)
        if out.state == STATE_ACTIVE and -out.result.structural > self._structural_threshold:
            return DIAGNOSIS_STRUCTURAL
        return DIAGNOSIS_COMPOSITIONAL

    def stake_fractions(self, view: DateView, p_hat: np.ndarray, b: np.ndarray) -> np.ndarray:
        """kelly_staking con λ dalla diagnosi della data, aggiornato una volta per data."""
        day = np.datetime64(view.date, "ns")
        if day not in self._lambda_by_date:
            diagnosis = self._diagnose(day)
            alarm = diagnosis != DIAGNOSIS_NONE
            if alarm and not self._previous_alarm:
                self._n_onsets += 1
            self._previous_alarm = alarm
            if diagnosis == DIAGNOSIS_STRUCTURAL and self._stop == SCHEME_STOP_SEASON:
                self._stopped = True
            if self._stopped or diagnosis == DIAGNOSIS_STRUCTURAL:
                lam = 0.0
            elif diagnosis == DIAGNOSIS_COMPOSITIONAL:
                lam = self._base_lambda * self._kappa
            else:
                lam = self._base_lambda
            self._diagnosis_by_date[day] = diagnosis
            self._lambda_by_date[day] = lam
        lam_arr = np.full(p_hat.shape[0], self._lambda_by_date[day])
        return _kelly_fractions(p_hat, b, lam_arr)

    def observe_results(self, results: DateResults) -> None:
        """Inoltra gli esiti della data regolata al supervisore."""
        self._supervisor.observe(results)


def scheme_statistics(delta_a: np.ndarray, delta_b: np.ndarray) -> tuple[np.ndarray | float, np.ndarray | float]:
    """F di media e F di Brown-Forsythe fra le finestre A e B, con segno (vedi modulo).

    Parametri
    ---------
    delta_a, delta_b : np.ndarray
        δ delle finestre, (W,) oppure lotto (B, W).

    Restituisce
    -----------
    tuple
        (F della media se la media di B è minore di quella di A, altrimenti 0;
        F di Brown-Forsythe se la dispersione di B è maggiore di quella di A, altrimenti 0),
        float per finestre 1D, altrimenti ndarray (B,).
    """
    a = np.asarray(delta_a, dtype=np.float64)
    b = np.asarray(delta_b, dtype=np.float64)
    if a.shape != b.shape or a.ndim not in (1, 2) or a.shape[-1] < 2:
        raise ValueError(f"delta_a and delta_b must have the same shape (W,) or (B, W), W >= 2, got {a.shape}, {b.shape}")
    w = a.shape[-1]
    labels = np.repeat(np.array([0, 1], dtype=np.int64), w)
    f_mean = oneway_anova_vectorized(np.concatenate([a, b], axis=-1), labels)
    worse = b.mean(axis=-1) < a.mean(axis=-1)
    f_disp = brown_forsythe(np.stack([a, b], axis=-2))
    spread_a = np.abs(a - np.median(a, axis=-1, keepdims=True)).mean(axis=-1)
    spread_b = np.abs(b - np.median(b, axis=-1, keepdims=True)).mean(axis=-1)
    wider = spread_b > spread_a
    if a.ndim == 1:
        return (float(f_mean) if worse else 0.0), (float(f_disp) if wider else 0.0)
    return np.where(worse, f_mean, 0.0), np.where(wider, f_disp, 0.0)


def calibrate_scheme_thresholds(
    delta: np.ndarray,
    window: int,
    block_length: int,
    rng: np.random.Generator,
    n_boot: int = N_BOOT,
    alpha: float = ALPHA,
) -> tuple[float, float]:
    """Soglie (media, dispersione) dell'allarme di C3 al livello α/2 ciascuna sotto H₀ (vedi modulo)."""
    y = np.asarray(delta, dtype=np.float64)
    n = y.shape[0]
    if 2 * window > n:
        raise ValueError(f"need delta with length >= 2W, got {n}, W = {window}")
    idx = moving_block_indices(n, block_length, n_boot, rng)[:, :2 * window]
    f_mean, f_disp = scheme_statistics(y[idx[:, :window]], y[idx[:, window:]])
    k = compute_order_statistic_index(n_boot, alpha / 2.0)
    return float(np.sort(f_mean)[k - 1]), float(np.sort(f_disp)[k - 1])


def calibrate_scheme_and_thresholds(
    delta: np.ndarray,
    window: int,
    block_length: int,
    rng: np.random.Generator,
    n_boot: int = N_BOOT,
    alpha: float = ALPHA,
) -> tuple[float, float]:
    """Soglie (media, dispersione) dell'allarme congiunto di C3_and: quota congiunta <= α sotto H₀ (vedi modulo)."""
    y = np.asarray(delta, dtype=np.float64)
    n = y.shape[0]
    if 2 * window > n:
        raise ValueError(f"need delta with length >= 2W, got {n}, W = {window}")
    idx = moving_block_indices(n, block_length, n_boot, rng)[:, :2 * window]
    f_mean, f_disp = scheme_statistics(y[idx[:, :window]], y[idx[:, window:]])
    sorted_mean, sorted_disp = np.sort(f_mean), np.sort(f_disp)
    best = (float(sorted_mean[-1]), float(sorted_disp[-1]))
    for k in range(n_boot - 1, 0, -1):
        mean_thr, disp_thr = float(sorted_mean[k - 1]), float(sorted_disp[k - 1])
        if np.mean((f_mean > mean_thr) & (f_disp > disp_thr)) > alpha:
            break
        best = (mean_thr, disp_thr)
    return best
