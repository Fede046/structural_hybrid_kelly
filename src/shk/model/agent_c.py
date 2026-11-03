"""Agente C e bracci dell'ablazione dentro l'architettura del backtest appaiato (decisione di progetto).

Supervisore del Modulo 2 (Module2Supervisor). Un'istanza per esecuzione dell'ambiente,
condivisa dai bracci che lo usano (C1, C2_global, C2), così il Modulo 2 si calcola una volta
per data. Riceve all'inizio solo le covariate pre-partita della stagione, nell'ordine delle
partite dell'ambiente. Gli esiti gli arrivano solo da Agent.observe_results, che l'ambiente
chiama dopo il regolamento di ogni data: per ogni partita regolata registra p̂, q di Shin
dalle quote della data, esito e δ = ln p̂(x) − ln q(x) (decisione di progetto). L'aggiornamento è
idempotente per data, perché i bracci inoltrano le stesse DateResults.

Alla data di decisione d (state_at, con cache per data) il supervisore costruisce i dati
del Modulo 2 dalle sole partite osservate e chiama module2.module2_at_date con anteriorità
stretta (Date < d), sulla catena della sola stagione: nell'esecuzione di prova sul training le stagioni di training non si
collegano alle stagioni di validazione precedenti. Restituisce anche:
- le finestre A e B nel formato del Modulo 3 (WindowData, con EV̂ dell'esito candidato,
  cioè quello a EV stimato massimo, di ogni partita della finestra);
- la maschera "fuori supporto" dell'analisi del supporto comune per le partite della data (out_of_support_mask sulla
  finestra A), quando ci sono almeno 2W partite anteriori, come out_of_support_at_date.

Bracci (decisione di progetto; il supervisore cambia solo le frazioni, mai previsioni, selezione o
ripiego, che restano quelli di Agent.decide):
- C0: FractionalKellyAgent con λ = 0.25, identico a B_0.25 (build_c0_agent);
- C1 (C1Agent): λ = 0.25·κ^n, con n il numero di accensioni dell'allarme strutturale,
  cioè delle date di decisione in cui l'allarme è acceso e alla data di decisione
  precedente era spento (decisione del programmatore, 2026-10-11). L'allarme alla data d
  è acceso se il Modulo 2 è attivo e T = −S supera la soglia calibrata, con S la
  componente strutturale three-fold (degrado di δ a composizione fissa). L'allarme alla
  data d usa solo partite con Date < d, quindi l'accensione conta già alla data d, come
  un allarme di D su partite anteriori. Con κ = 0 vale la convenzione di
  compute_adaptive_lambda (adaptive_multiplier);
- C2_global (GradedAgent, abstain=False): λ per scommessa = module3.module3_lambda
  (candidata P3 della scelta del Modulo 3), con le finestre A e B e S del supervisore; Modulo 2 non attivo
  o con rango non pieno → λ = 0.25;
- C2 (GradedAgent, abstain=True): come C2_global, con frazione 0 sulle partite fuori
  supporto.
Frazione sull'esito selezionato: kelly_staking(p̂, o − 1, λ), elemento per elemento.
Con una regola del lavoratore (shk.kelly.outcome_rules.with_outcome_rule) l'esito è quello
della regola; C2 usa allora, per il Modulo 3, l'EV̂ dell'esito candidato della regola sulla
finestra B (Module2Supervisor.window_candidate_ev) e si astiene sulle partite selezionate
dalla regola. Con R1, il default, tutto coincide con i bracci di sopra.

Soglia di C1 (calibrate_c1_threshold): moving block bootstrap della serie di training del
fit, con le righe (covariate, δ) ricampionate insieme; dei ricampionamenti di lunghezza n si
tengono le prime 2W posizioni come finestre A e B; T = −S della three-fold. I
ricampionamenti con un disegno a rango non pieno (stato "rank_deficient" del Modulo 2) si
scartano; soglia = statistica d'ordine ceil((1 − α)(B_validi + 1)) di T sui validi, con
α = 0.05 e B = 999.

Schema del relatore (C3, SchemeAgent; mail del prof. Roccetti, 2026-11): il Modulo 2 monitora
con l'ANOVA i residui δ e dà l'allarme; il Modulo 3 usa Oaxaca-Blinder per decidere la puntata.
- Allarme alla data d, sulle finestre A e B di δ (partite con Date < d, le stesse del Modulo 2):
  F dell'ANOVA a una via sulla media, contata solo se la media di B è minore di quella di A
  (peggioramento), oppure F di Brown-Forsythe (ANOVA sulle deviazioni assolute dalla mediana,
  eteroschedasticità), contata solo se la dispersione di B è maggiore di quella di A.
  Allarme se una delle due supera la sua soglia (C3, C3_stop), oppure, alla lettera della mail
  («la media degli errori cresce e la varianza esplode»), se le superano entrambe (C3_and);
  con meno di 2W partite non c'è allarme.
- Diagnosi con allarme: errore strutturale se il Modulo 2 è attivo e T = −S supera la soglia di
  C1 alla stessa W (componente strutturale significativamente negativa); altrimenti errore di
  composizione (dati), anche con Modulo 2 a rango non pieno.
- λ: senza allarme 0.25 (come C0); composizione 0.25·κ; strutturale 0 finché dura l'allarme
  (C3) oppure fino a fine stagione (C3_stop: «finché il modello non viene ri-parametrizzato»,
  e nella stagione il Modulo 1 non si ri-parametrizza).
Soglie dell'allarme (calibrate_scheme_thresholds): come la soglia di C1, moving block bootstrap
della serie di δ del fit, prime 2W posizioni come finestre A e B, B = 999; ogni F con segno ha
livello α/2 (Bonferroni), così l'allarme ha livello α = 0.05 al più. Per C3_and
(calibrate_scheme_and_thresholds), sugli stessi ricampionamenti: le due soglie sono statistiche
d'ordine allo stesso indice k, il più basso per cui la quota di ricampionamenti con entrambe le
F oltre soglia è ancora <= α.
"""

import math
from collections.abc import Callable, Sequence
from typing import Final, NamedTuple

import numpy as np
import pandas as pd

from shk.kelly.agents import Agent, DateResults, DateView, FractionalKellyAgent, estimated_expected_values
from shk.kelly.staking import BASE_LAMBDA, kelly_staking
from shk.market.devig import devig_probabilities
from shk.model.module2 import STATE_ACTIVE, STATE_NOT_ACTIVE, Module2Data, Module2Output, module2_at_date
from shk.model.module3 import WindowData, module3_lambda
from shk.model.stateful_agents import adaptive_multiplier
from shk.stats.calibration import compute_order_statistic_index, moving_block_indices
from shk.stats.false_rejection import ALPHA
from shk.stats.nopo import out_of_support_mask
from shk.stats.anova import oneway_anova_vectorized
from shk.stats.oaxaca import three_fold_batch
from shk.stats.variance_change import brown_forsythe

C0_LAMBDA: Final[float] = BASE_LAMBDA
C1_N_BOOT: Final[int] = 999
SCHEME_STOP_CLEAR: Final[str] = "until_clear"
SCHEME_STOP_SEASON: Final[str] = "until_season_end"
SCHEME_STOPS: Final[tuple[str, ...]] = (SCHEME_STOP_CLEAR, SCHEME_STOP_SEASON)
SCHEME_ALARM_OR: Final[str] = "or"
SCHEME_ALARM_AND: Final[str] = "and"
SCHEME_ALARMS: Final[tuple[str, ...]] = (SCHEME_ALARM_OR, SCHEME_ALARM_AND)
DIAGNOSIS_NONE: Final[str] = "none"
DIAGNOSIS_COMPOSITIONAL: Final[str] = "compositional"
DIAGNOSIS_STRUCTURAL: Final[str] = "structural"


class SupervisorState(NamedTuple):
    """Uscita del supervisore a una data di decisione.

    Attributi
    ---------
    output : Module2Output
        Uscita del Modulo 2 (module2_at_date) sulle partite osservate con Date < d.
    window_a, window_b : WindowData o None
        Finestre A e B per il Modulo 3, None se il Modulo 2 non è attivo.
    out_of_support : np.ndarray o None
        Maschera bool (n_data,) delle partite della data fuori supporto; None con meno di
        2W partite anteriori.
    """

    output: Module2Output
    window_a: WindowData | None
    window_b: WindowData | None
    out_of_support: np.ndarray | None


class SupervisorHistory(NamedTuple):
    """Partite già regolate delle stagioni precedenti della catena (sensibilità dell'esecuzione congelata sulla validazione)."""

    dates: np.ndarray     # (H,) datetime64, ordinate e anteriori alla stagione
    x: np.ndarray         # (H, k) covariate pre-partita
    probs: np.ndarray     # (H, 3)
    odds: np.ndarray      # (H, 3)
    outcomes: np.ndarray  # (H,) esiti realizzati 0..2


class Module2Supervisor:
    """Modulo 2 online per un'esecuzione dell'ambiente (vedi modulo).

    Parametri
    ---------
    season : str
        Stagione dell'esecuzione.
    dates : np.ndarray
        Date (N,) delle partite, nell'ordine dell'ambiente (non decrescenti).
    covariates_x : np.ndarray
        Covariate pre-partita (N, k) nello stesso ordine.
    covariate_names : Sequence[str]
        Nomi delle k covariate; quelle che iniziano con "flag_" sono dummy.
    window : int
        W del Modulo 2.
    history : SupervisorHistory o None, default None
        Partite già regolate delle stagioni precedenti della catena, tutte anteriori alla
        stagione: con None la catena è tagliata alla stagione (calibrazione sul training ed esecuzioni congelate);
        altrimenti attraversa le stagioni come nella decisione di progetto (sensibilità dell'esecuzione congelata sulla validazione).
    devig_method : str, default "shin"
        Metodo di de-vigging di q per δ (decisione di progetto; gli altri per la sensibilità al de-vigging).

    Solleva
    -------
    ValueError
        Se le forme non sono coerenti, le date non sono ordinate o la storia non è anteriore.
    """

    def __init__(
        self,
        season: str,
        dates: np.ndarray,
        covariates_x: np.ndarray,
        covariate_names: Sequence[str],
        window: int,
        history: "SupervisorHistory | None" = None,
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
        n_hist = 0
        if history is not None:
            h_dates = np.asarray(history.dates).astype("datetime64[ns]")
            n_hist = h_dates.shape[0]
            if n_hist and (np.any(h_dates[1:] < h_dates[:-1]) or (d.shape[0] and h_dates[-1] >= d[0])):
                raise ValueError("history must be sorted and strictly earlier than the season")
            d = np.concatenate([h_dates, d])
            x = np.concatenate([np.asarray(history.x, dtype=np.float64).reshape(n_hist, len(names)), x])
        n = d.shape[0]
        self._season = season
        self._dates = d
        self._x = x.copy()
        self._names = names
        self._window = int(window)
        self._dummy_columns = [i for i, c in enumerate(names) if c.startswith("flag_")]
        self._observed = np.zeros(n, dtype=bool)
        self._delta = np.full(n, np.nan)
        self._p_hat = np.full((n, 3), np.nan)
        self._q = np.full((n, 3), np.nan)
        self._outcome = np.full(n, -1, dtype=np.int64)
        self._ev_candidate = np.full(n, np.nan)
        self._odds = np.full((n, 3), np.nan)
        self._observed_dates: set[np.datetime64] = set()
        self._cache: dict[np.datetime64, SupervisorState] = {}
        if n_hist:
            self._record(np.arange(n_hist), np.asarray(history.probs, dtype=np.float64),
                         np.asarray(history.odds, dtype=np.float64), np.asarray(history.outcomes, dtype=np.int64))

    @property
    def window(self) -> int:
        """W del Modulo 2."""
        return self._window

    def _record(self, rows: np.ndarray, probs: np.ndarray, odds: np.ndarray, realized: np.ndarray) -> None:
        idx = np.arange(rows.shape[0])
        q = devig_probabilities(odds, self._devig_method)
        self._delta[rows] = np.log(probs[idx, realized]) - np.log(q[idx, realized])
        self._p_hat[rows] = probs
        self._q[rows] = q
        self._outcome[rows] = realized
        self._ev_candidate[rows] = estimated_expected_values(probs, odds).max(axis=1)
        self._odds[rows] = odds
        self._observed[rows] = True

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
        self._record(rows, np.asarray(results.probs, dtype=np.float64), np.asarray(results.odds, dtype=np.float64),
                     np.asarray(results.outcomes[0], dtype=np.int64))
        self._observed_dates.add(day)

    def cutoff(self, decision_date: np.datetime64) -> np.datetime64:
        """Data di taglio passata a module2_at_date: si usano le partite con Date < taglio."""
        return decision_date

    def delta_windows(self, decision_date: np.datetime64) -> tuple[np.ndarray, np.ndarray] | None:
        """δ delle finestre A e B (partite osservate con Date < d); None con meno di 2W partite."""
        cut = np.datetime64(self.cutoff(np.datetime64(decision_date, "ns")), "ns")
        observed = np.flatnonzero(self._observed)
        eligible = observed[self._dates[observed] < cut]
        if eligible.shape[0] < 2 * self._window:
            return None
        return self._delta[eligible[-2 * self._window:-self._window]], self._delta[eligible[-self._window:]]

    def window_candidate_ev(self, decision_date: np.datetime64, rule: Callable[[np.ndarray, np.ndarray], np.ndarray]) -> np.ndarray | None:
        """EV̂ dell'esito candidato della regola (shk.kelly.outcome_rules) sulla finestra B; None con meno di 2W partite."""
        cut = np.datetime64(self.cutoff(np.datetime64(decision_date, "ns")), "ns")
        observed = np.flatnonzero(self._observed)
        eligible = observed[self._dates[observed] < cut]
        if eligible.shape[0] < 2 * self._window:
            return None
        rows = eligible[-self._window:]
        probs, odds = self._p_hat[rows], self._odds[rows]
        ev = estimated_expected_values(probs, odds)
        return ev[np.arange(rows.shape[0]), rule(probs, odds)]

    def _window_data(self, rows: np.ndarray) -> WindowData:
        return WindowData(self._p_hat[rows], self._q[rows], self._outcome[rows], self._ev_candidate[rows])

    def state_at(self, decision_date: np.datetime64) -> SupervisorState:
        """Uscita del Modulo 2, finestre e maschera fuori supporto alla data (in cache)."""
        day = np.datetime64(decision_date, "ns")
        if day in self._cache:
            return self._cache[day]
        cut = np.datetime64(self.cutoff(day), "ns")
        observed = np.flatnonzero(self._observed)
        eligible = observed[self._dates[observed] < cut]
        today = np.flatnonzero(self._dates == day)
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
        window_a = window_b = None
        out_of_support = None
        if eligible.shape[0] >= 2 * self._window:
            idx_a = eligible[-2 * self._window:-self._window]
            idx_b = eligible[-self._window:]
            out_of_support = out_of_support_mask(self._x[idx_a], self._x[today], self._dummy_columns)
            if output.state == STATE_ACTIVE:
                window_a, window_b = self._window_data(idx_a), self._window_data(idx_b)
        state = SupervisorState(output, window_a, window_b, out_of_support)
        self._cache[day] = state
        return state


def _selected_rows(view: DateView, candidates: np.ndarray) -> np.ndarray:
    """Partite selezionate da Agent.decide (EV stimato dell'esito candidato > 0), nell'ordine della data."""
    ev = estimated_expected_values(view.probs, view.odds)
    return np.flatnonzero(ev[np.arange(ev.shape[0]), candidates] > 0.0)


def _kelly_fractions(p_hat: np.ndarray, b: np.ndarray, lam: np.ndarray) -> np.ndarray:
    fractions = np.empty(p_hat.shape[0], dtype=np.float64)
    for i in range(p_hat.shape[0]):
        fractions[i] = kelly_staking(float(p_hat[i]), float(b[i]), lam=float(lam[i]))
    return fractions


def build_c0_agent(name: str = "C0") -> FractionalKellyAgent:
    """C0: supervisore spento, λ = 0.25 costante (identico a B_0.25)."""
    return FractionalKellyAgent(name, lam=C0_LAMBDA)


class C1Agent(Agent):
    """C1: allarme binario del Modulo 2 e riduzione fissa κ a ogni accensione (vedi modulo).

    Parametri
    ---------
    name : str
        Nome dell'agente.
    supervisor : Module2Supervisor
        Supervisore condiviso dell'esecuzione.
    kappa : float
        Fattore di riduzione per accensione, in [0, 1].
    threshold : float
        Soglia di T = −S.
    base_lambda : float, default 0.25
        λ senza allarmi.
    """

    def __init__(self, name: str, supervisor: Module2Supervisor, kappa: float, threshold: float,
                 base_lambda: float = BASE_LAMBDA) -> None:
        super().__init__(name)
        if not isinstance(supervisor, Module2Supervisor):
            raise TypeError("supervisor must be a Module2Supervisor")
        for label, value in (("kappa", kappa), ("base_lambda", base_lambda)):
            if isinstance(value, bool) or not isinstance(value, (float, np.floating)) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{label} must be a float in [0, 1], got {value!r}")
        if isinstance(threshold, bool) or not isinstance(threshold, (float, np.floating)) or not math.isfinite(threshold):
            raise ValueError(f"threshold must be a finite float, got {threshold!r}")
        self._supervisor = supervisor
        self._kappa = float(kappa)
        self._threshold = float(threshold)
        self._base_lambda = float(base_lambda)
        self._n_onsets = 0
        self._previous_alarm = False
        self._lambda_by_date: dict[np.datetime64, float] = {}
        self._alarm_by_date: dict[np.datetime64, bool] = {}

    @property
    def n_onsets(self) -> int:
        """Accensioni dell'allarme fino all'ultima data di decisione."""
        return self._n_onsets

    @property
    def lambda_by_date(self) -> dict[np.datetime64, float]:
        """λ applicato a ogni data di decisione."""
        return dict(self._lambda_by_date)

    @property
    def alarm_by_date(self) -> dict[np.datetime64, bool]:
        """Stato dell'allarme a ogni data di decisione."""
        return dict(self._alarm_by_date)

    def stake_fractions(self, view: DateView, p_hat: np.ndarray, b: np.ndarray) -> np.ndarray:
        """kelly_staking con λ = 0.25·κ^(accensioni), aggiornato una volta per data."""
        day = np.datetime64(view.date, "ns")
        if day not in self._lambda_by_date:
            out = self._supervisor.state_at(day).output
            alarm = out.state == STATE_ACTIVE and -out.result.structural > self._threshold
            if alarm and not self._previous_alarm:
                self._n_onsets += 1
            self._previous_alarm = alarm
            self._alarm_by_date[day] = alarm
            self._lambda_by_date[day] = self._base_lambda * adaptive_multiplier(self._kappa, self._n_onsets)
        lam = np.full(p_hat.shape[0], self._lambda_by_date[day])
        return _kelly_fractions(p_hat, b, lam)

    def observe_results(self, results: DateResults) -> None:
        """Inoltra gli esiti della data regolata al supervisore."""
        self._supervisor.observe(results)


class GradedAgent(Agent):
    """C2_global (abstain=False) e C2 (abstain=True): λ dal Modulo 3 (vedi modulo).

    Parametri
    ---------
    name : str
        Nome dell'agente.
    supervisor : Module2Supervisor
        Supervisore condiviso dell'esecuzione.
    abstain : bool
        Se True, frazione 0 sulle partite fuori supporto (C2).
    """

    def __init__(self, name: str, supervisor: Module2Supervisor, abstain: bool) -> None:
        super().__init__(name)
        if not isinstance(supervisor, Module2Supervisor):
            raise TypeError("supervisor must be a Module2Supervisor")
        if not isinstance(abstain, bool):
            raise TypeError("abstain must be a bool")
        self._supervisor = supervisor
        self._abstain = abstain
        self._lambda_zero_by_date: dict[np.datetime64, bool] = {}
        self._n_abstained = 0

    @property
    def lambda_zero_by_date(self) -> dict[np.datetime64, bool]:
        """Per ogni data di decisione, True se λ = 0 su tutti gli esiti candidati della data."""
        return dict(self._lambda_zero_by_date)

    @property
    def n_abstained(self) -> int:
        """Esiti selezionati con frazione azzerata perché fuori supporto (solo C2)."""
        return self._n_abstained

    def stake_fractions(self, view: DateView, p_hat: np.ndarray, b: np.ndarray) -> np.ndarray:
        """kelly_staking con λ = module3_lambda per scommessa; C2 azzera le partite fuori supporto."""
        day = np.datetime64(view.date, "ns")
        state = self._supervisor.state_at(day)
        out = state.output
        active = out.state == STATE_ACTIVE
        structural = float(out.result.structural) if active else 0.0
        window_b = state.window_b
        rule = getattr(type(self), "outcome_rule", None)
        if rule is not None and window_b is not None:
            window_b = window_b._replace(ev_candidate=self._supervisor.window_candidate_ev(day, rule))
        odds_bet = np.asarray(b, dtype=np.float64) + 1.0
        lam = module3_lambda(active, state.window_a, window_b, structural, odds_bet,
                             np.asarray(p_hat, dtype=np.float64) * odds_bet - 1.0)
        candidates = self.candidate_outcomes(view)
        if day not in self._lambda_zero_by_date:
            ev = estimated_expected_values(view.probs, view.odds)
            rows = np.arange(ev.shape[0])
            lam_all = module3_lambda(active, state.window_a, window_b, structural,
                                     np.asarray(view.odds)[rows, candidates], ev[rows, candidates])
            self._lambda_zero_by_date[day] = bool(np.all(lam_all == 0.0))
        fractions = _kelly_fractions(p_hat, b, lam)
        if self._abstain and state.out_of_support is not None:
            outside = state.out_of_support[_selected_rows(view, candidates)]
            self._n_abstained += int(outside.sum())
            fractions[outside] = 0.0
        return fractions

    def observe_results(self, results: DateResults) -> None:
        """Inoltra gli esiti della data regolata al supervisore."""
        self._supervisor.observe(results)


class SchemeAgent(Agent):
    """C3 e C3_stop: schema del relatore, allarme ANOVA sui residui δ e risposta dalla three-fold (vedi modulo).

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
        Soglia di T = −S oltre la quale l'errore è strutturale (la soglia di C1 alla stessa W).
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
        out = self._supervisor.state_at(day).output
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
    n_boot: int = C1_N_BOOT,
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
    n_boot: int = C1_N_BOOT,
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


def c1_null_statistics(
    x: np.ndarray,
    delta: np.ndarray,
    window: int,
    block_length: int,
    n_boot: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, int]:
    """T = −S sui ricampionamenti a rango pieno (moving block bootstrap delle righe).

    Restituisce
    -----------
    tuple[np.ndarray, int]
        Statistiche T dei ricampionamenti validi e loro numero.
    """
    x_arr = np.asarray(x, dtype=np.float64)
    y_arr = np.asarray(delta, dtype=np.float64)
    n = y_arr.shape[0]
    if x_arr.shape[0] != n or 2 * window > n:
        raise ValueError(f"need x and delta with the same length >= 2W, got {x_arr.shape[0]}, {n}, W = {window}")
    idx = moving_block_indices(n, block_length, n_boot, rng)[:, :2 * window]
    ia, ib = idx[:, :window], idx[:, window:]
    tf = three_fold_batch(x_arr[ia], y_arr[ia], x_arr[ib], y_arr[ib])
    return -tf.structural[tf.valid], int(tf.valid.sum())


def calibrate_c1_threshold(
    x: np.ndarray,
    delta: np.ndarray,
    window: int,
    block_length: int,
    rng: np.random.Generator,
    n_boot: int = C1_N_BOOT,
    alpha: float = ALPHA,
) -> tuple[float, int]:
    """Soglia di C1 al livello α sotto H₀ (vedi modulo): (soglia, ricampionamenti validi).

    Solleva
    -------
    ValueError
        Se nessun ricampionamento ha rango pieno.
    """
    stats, n_valid = c1_null_statistics(x, delta, window, block_length, n_boot, rng)
    if n_valid < 1:
        raise ValueError("no full-rank bootstrap resample")
    k = compute_order_statistic_index(n_valid, alpha)
    return float(np.sort(stats)[k - 1]), n_valid
