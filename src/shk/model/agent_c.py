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

Variante con riferimento fisso (C3_ref, C3_ref_stop; decisione del 2026-11-05): la finestra A non
è più quella delle W partite precedenti ma la stagione di calibrazione del Modulo 1 (la stagione di
training del fit, ReferenceData), fissa per tutta la stagione; B resta l'ultima finestra di W
partite con Date < d. Allarme con F della media e di Brown-Forsythe con segno fra gruppi di
dimensione diversa (reference_statistics); diagnosi con la three-fold fra il riferimento e B
(Module2Supervisor.reference_diagnostics). Soglie di media, dispersione e componente strutturale
calibrate insieme (calibrate_reference_thresholds): moving block bootstrap della stagione di
calibrazione, B = W righe (covariate e δ insieme) ricampionate contro la stagione intera; media e
dispersione al livello α/2, T = −S al livello α sui ricampionamenti a rango pieno. È una variante
scelta dopo aver visto le frequenze d'allarme sulla validazione (non i rendimenti).

Soglie dell'allarme (calibrate_scheme_thresholds): moving block bootstrap della serie di δ del
fit, dei ricampionamenti di lunghezza n si tengono le prime 2W posizioni come finestre A e B,
B = 999; ogni F con segno ha livello α/2 (Bonferroni), così l'allarme ha livello α = 0.05 al più.
Per C3_and (calibrate_scheme_and_thresholds), sugli stessi ricampionamenti: le due soglie sono
statistiche d'ordine allo stesso indice k, il più basso per cui la quota di ricampionamenti con
entrambe le F oltre soglia è ancora <= α.
"""

import math
from collections.abc import Sequence
from typing import Final, NamedTuple

import numpy as np
import pandas as pd

from shk.kelly.agents import Agent, DateResults, DateView
from shk.kelly.staking import BASE_LAMBDA, kelly_staking
from shk.market.devig import devig_probabilities
from shk.model.module2 import STATE_ACTIVE, STATE_NOT_ACTIVE, Module2Data, Module2Output, module2_at_date
from shk.stats.calibration import compute_order_statistic_index, moving_block_indices
from shk.stats.false_rejection import ALPHA
from shk.stats.anova import oneway_anova_vectorized
from shk.stats.oaxaca import three_fold_batch
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


OAXACA_REALIZED: Final[str] = "realized"
OAXACA_EXPECTED: Final[str] = "expected"
OAXACA_RESPONSES: Final[tuple[str, ...]] = (OAXACA_REALIZED, OAXACA_EXPECTED)


class ReferenceData(NamedTuple):
    """Partite della stagione di calibrazione del Modulo 1, riferimento fisso della variante C3_ref."""

    x: np.ndarray                         # (n, k) covariate pre-partita
    delta: np.ndarray                     # (n,) δ
    expected: np.ndarray | None = None    # (n,) E_q[δ], per la diagnosi con l'errore atteso


def expected_delta(probs: np.ndarray, q: np.ndarray) -> np.ndarray:
    """Errore atteso E_q[δ] = Σ_j q_j ln(p̂_j / q_j) per partita (= −KL(q ‖ p̂), non dipende dall'esito)."""
    p = np.asarray(probs, dtype=np.float64)
    qq = np.asarray(q, dtype=np.float64)
    return (qq * np.log(p / qq)).sum(axis=-1)


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
    reference : ReferenceData o None, default None
        Stagione di calibrazione per la variante con riferimento fisso (reference_diagnostics).
    oaxaca_response : str, default OAXACA_REALIZED
        Risposta della diagnosi di Oaxaca-Blinder: δ realizzato (OAXACA_REALIZED) oppure l'errore
        atteso E_q[δ] (OAXACA_EXPECTED, expected_delta). L'allarme ANOVA usa sempre δ realizzato.

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
        reference: ReferenceData | None = None,
        oaxaca_response: str = OAXACA_REALIZED,
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
        if oaxaca_response not in OAXACA_RESPONSES:
            raise ValueError(f"oaxaca_response must be one of {OAXACA_RESPONSES}, got {oaxaca_response!r}")
        self._oaxaca_response = oaxaca_response
        self._expected = np.full(n, np.nan)
        self._observed_dates: set[np.datetime64] = set()
        self._cache: dict[np.datetime64, Module2Output] = {}
        if reference is not None:
            rx = np.asarray(reference.x, dtype=np.float64)
            rd = np.asarray(reference.delta, dtype=np.float64)
            if rx.ndim != 2 or rx.shape != (rd.shape[0], len(names)) or rd.shape[0] < 2 * len(names) + 2:
                raise ValueError("reference must have x (n, k) and delta (n,) with the supervisor's covariates")
            re = None if reference.expected is None else np.asarray(reference.expected, dtype=np.float64)
            if oaxaca_response == OAXACA_EXPECTED and (re is None or re.shape != rd.shape):
                raise ValueError("an expected-error diagnosis needs reference.expected with the shape of delta")
            reference = ReferenceData(rx, rd, re)
        self._reference = reference
        self._reference_cache: dict[np.datetime64, tuple[float, float, float] | None] = {}

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
        self._expected[rows] = expected_delta(probs, q)
        self._observed[rows] = True
        self._observed_dates.add(day)

    def _oaxaca_y(self) -> np.ndarray:
        return self._expected if self._oaxaca_response == OAXACA_EXPECTED else self._delta

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

    def reference_diagnostics(self, decision_date: np.datetime64) -> tuple[float, float, float] | None:
        """(F della media, F di dispersione, T = −S) fra il riferimento fisso e le ultime W partite con Date < d.

        None con meno di W partite; T è NaN se un disegno ha rango non pieno (in cache per data).
        """
        if self._reference is None:
            raise ValueError("the supervisor has no reference")
        day = np.datetime64(decision_date, "ns")
        if day in self._reference_cache:
            return self._reference_cache[day]
        eligible = self._eligible(day)
        if eligible.shape[0] < self._window:
            out = None
        else:
            rows = eligible[-self._window:]
            f_mean, f_disp = reference_statistics(self._reference.delta, self._delta[rows])
            ref_y = self._reference.expected if self._oaxaca_response == OAXACA_EXPECTED else self._reference.delta
            tf = three_fold_batch(self._reference.x[None], ref_y[None], self._x[rows][None],
                                  self._oaxaca_y()[rows][None])
            out = (float(f_mean), float(f_disp), float(-tf.structural[0]) if bool(tf.valid[0]) else math.nan)
        self._reference_cache[day] = out
        return out

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
                delta=self._oaxaca_y()[observed],
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
    reference : bool, default False
        Se True, allarme e diagnosi contro il riferimento fisso del supervisore (C3_ref, vedi modulo).
    """

    def __init__(self, name: str, supervisor: Module2Supervisor, kappa: float, mean_threshold: float,
                 dispersion_threshold: float, structural_threshold: float, stop: str,
                 base_lambda: float = BASE_LAMBDA, alarm: str = SCHEME_ALARM_OR, reference: bool = False) -> None:
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
        if reference and supervisor._reference is None:
            raise ValueError("reference=True needs a supervisor with a reference")
        self._alarm = alarm
        self._reference = bool(reference)
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

    def _alarm_on(self, f_mean: float, f_dispersion: float) -> bool:
        exceed = (f_mean > self._mean_threshold, f_dispersion > self._dispersion_threshold)
        return all(exceed) if self._alarm == SCHEME_ALARM_AND else any(exceed)

    def _diagnose(self, day: np.datetime64) -> str:
        if self._reference:
            diag = self._supervisor.reference_diagnostics(day)
            if diag is None or not self._alarm_on(diag[0], diag[1]):
                return DIAGNOSIS_NONE
            return DIAGNOSIS_STRUCTURAL if diag[2] > self._structural_threshold else DIAGNOSIS_COMPOSITIONAL
        windows = self._supervisor.delta_windows(day)
        if windows is None:
            return DIAGNOSIS_NONE
        f_mean, f_dispersion = scheme_statistics(windows[0], windows[1])
        if not self._alarm_on(f_mean, f_dispersion):
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


def reference_statistics(reference: np.ndarray, window: np.ndarray) -> tuple[np.ndarray | float, np.ndarray | float]:
    """F della media e F di Brown-Forsythe con segno fra il riferimento (n_A,) e la finestra (W,) o (B, W).

    ANOVA a una via con due gruppi di dimensione diversa; la F della media conta solo se la media
    della finestra è minore di quella del riferimento, la F di dispersione solo se la deviazione
    assoluta media dalla mediana della finestra è maggiore.
    """
    a = np.asarray(reference, dtype=np.float64)
    b = np.asarray(window, dtype=np.float64)
    if a.ndim != 1 or b.ndim not in (1, 2) or a.shape[0] < 2 or b.shape[-1] < 2:
        raise ValueError(f"reference must be (n,) and window (W,) or (B, W), got {a.shape}, {b.shape}")

    def oneway(ga: np.ndarray, gb: np.ndarray) -> np.ndarray:
        na, nb = ga.shape[-1], gb.shape[-1]
        ma, mb = ga.mean(axis=-1), gb.mean(axis=-1)
        grand = (na * ma + nb * mb) / (na + nb)
        between = na * (ma - grand) ** 2 + nb * (mb - grand) ** 2
        within = ((ga - ma[..., None]) ** 2).sum(axis=-1) + ((gb - mb[..., None]) ** 2).sum(axis=-1)
        return between / (within / (na + nb - 2))

    za = np.abs(a - np.median(a))
    zb = np.abs(b - np.median(b, axis=-1, keepdims=True))
    f_mean = oneway(a, b)
    f_disp = oneway(za, zb)
    worse = b.mean(axis=-1) < a.mean()
    wider = zb.mean(axis=-1) > za.mean()
    if b.ndim == 1:
        return (float(f_mean) if worse else 0.0), (float(f_disp) if wider else 0.0)
    return np.where(worse, f_mean, 0.0), np.where(wider, f_disp, 0.0)


def calibrate_reference_thresholds(
    x: np.ndarray,
    delta: np.ndarray,
    window: int,
    block_length: int,
    rng: np.random.Generator,
    n_boot: int = N_BOOT,
    alpha: float = ALPHA,
) -> tuple[float, float, float]:
    """Soglie (media, dispersione, T = −S) della variante con riferimento fisso (vedi modulo)."""
    xa = np.asarray(x, dtype=np.float64)
    ya = np.asarray(delta, dtype=np.float64)
    n = ya.shape[0]
    if xa.shape[0] != n or window > n:
        raise ValueError(f"need x and delta with the same length >= W, got {xa.shape[0]}, {n}, W = {window}")
    idx = moving_block_indices(n, block_length, n_boot, rng)[:, :window]
    f_mean, f_disp = reference_statistics(ya, ya[idx])
    k = compute_order_statistic_index(n_boot, alpha / 2.0)
    tf = three_fold_batch(np.ascontiguousarray(np.broadcast_to(xa, (n_boot,) + xa.shape)),
                          np.ascontiguousarray(np.broadcast_to(ya, (n_boot, n))), xa[idx], ya[idx])
    t = -tf.structural[tf.valid]
    if t.shape[0] < 1:
        raise ValueError("no full-rank bootstrap resample")
    ks = compute_order_statistic_index(t.shape[0], alpha)
    return float(np.sort(f_mean)[k - 1]), float(np.sort(f_disp)[k - 1]), float(np.sort(t)[ks - 1])
