"""Agente C e bracci dell'ablazione dentro l'architettura di C6 (T52, decisione S9).

Supervisore del Modulo 2 (Module2Supervisor). Un'istanza per esecuzione dell'ambiente,
condivisa dai bracci che lo usano (C1, C2_global, C2), così il Modulo 2 si calcola una volta
per data. Riceve all'inizio solo le covariate pre-partita della stagione, nell'ordine delle
partite dell'ambiente. Gli esiti gli arrivano solo da Agent.observe_results, che l'ambiente
chiama dopo il regolamento di ogni data: per ogni partita regolata registra p̂, q di Shin
dalle quote della data, esito e δ = ln p̂(x) − ln q(x) (decisione S8). L'aggiornamento è
idempotente per data, perché i bracci inoltrano le stesse DateResults.

Alla data di decisione d (state_at, con cache per data) il supervisore costruisce i dati
del Modulo 2 dalle sole partite osservate e chiama module2.module2_at_date con anteriorità
stretta (Date < d), sulla catena della sola stagione: in T52 le stagioni di training non si
collegano alle stagioni di validazione precedenti. Restituisce anche:
- le finestre A e B nel formato del Modulo 3 (WindowData, con EV̂ dell'esito candidato,
  cioè quello a EV stimato massimo, di ogni partita della finestra);
- la maschera "fuori supporto" di T49 per le partite della data (out_of_support_mask sulla
  finestra A), quando ci sono almeno 2W partite anteriori, come out_of_support_at_date.

Bracci (decisione S9; il supervisore cambia solo le frazioni, mai previsioni, selezione o
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
  (candidata P3 di T51), con le finestre A e B e S del supervisore; Modulo 2 non attivo
  o con rango non pieno → λ = 0.25;
- C2 (GradedAgent, abstain=True): come C2_global, con frazione 0 sulle partite fuori
  supporto.
Frazione sull'esito selezionato: kelly_staking(p̂, o − 1, λ), elemento per elemento.

Soglia di C1 (calibrate_c1_threshold): moving block bootstrap della serie di training del
fit, con le righe (covariate, δ) ricampionate insieme; dei ricampionamenti di lunghezza n si
tengono le prime 2W posizioni come finestre A e B; T = −S della three-fold. I
ricampionamenti con un disegno a rango non pieno (stato "rank_deficient" del Modulo 2) si
scartano; soglia = statistica d'ordine ceil((1 − α)(B_validi + 1)) di T sui validi, con
α = 0.05 e B = 999.
"""

import math
from collections.abc import Sequence
from typing import Final, NamedTuple

import numpy as np
import pandas as pd

from shk.kelly.agents import Agent, DateResults, DateView, FractionalKellyAgent, estimated_expected_values
from shk.kelly.staking import BASE_LAMBDA, kelly_staking
from shk.market.devig import devig_shin
from shk.model.module2 import STATE_ACTIVE, STATE_NOT_ACTIVE, Module2Data, Module2Output, module2_at_date
from shk.model.module3 import WindowData, module3_lambda
from shk.model.stateful_agents import adaptive_multiplier
from shk.stats.calibration import compute_order_statistic_index, moving_block_indices
from shk.stats.false_rejection import ALPHA
from shk.stats.nopo import out_of_support_mask
from shk.stats.oaxaca import three_fold_batch

C0_LAMBDA: Final[float] = BASE_LAMBDA
C1_N_BOOT: Final[int] = 999


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
    ) -> None:
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
        self._dummy_columns = [i for i, c in enumerate(names) if c.startswith("flag_")]
        self._observed = np.zeros(n, dtype=bool)
        self._delta = np.full(n, np.nan)
        self._p_hat = np.full((n, 3), np.nan)
        self._q = np.full((n, 3), np.nan)
        self._outcome = np.full(n, -1, dtype=np.int64)
        self._ev_candidate = np.full(n, np.nan)
        self._observed_dates: set[np.datetime64] = set()
        self._cache: dict[np.datetime64, SupervisorState] = {}

    @property
    def window(self) -> int:
        """W del Modulo 2."""
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
        odds = np.asarray(results.odds, dtype=np.float64)
        realized = np.asarray(results.outcomes[0], dtype=np.int64)
        idx = np.arange(rows.shape[0])
        q, _ = devig_shin(odds)
        self._delta[rows] = np.log(probs[idx, realized]) - np.log(q[idx, realized])
        self._p_hat[rows] = probs
        self._q[rows] = q
        self._outcome[rows] = realized
        self._ev_candidate[rows] = estimated_expected_values(probs, odds).max(axis=1)
        self._observed[rows] = True
        self._observed_dates.add(day)

    def cutoff(self, decision_date: np.datetime64) -> np.datetime64:
        """Data di taglio passata a module2_at_date: si usano le partite con Date < taglio."""
        return decision_date

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


def _selected_rows(view: DateView) -> np.ndarray:
    """Partite selezionate da Agent.decide (EV stimato massimo > 0), nell'ordine della data."""
    ev = estimated_expected_values(view.probs, view.odds)
    return np.flatnonzero(ev.max(axis=1) > 0.0)


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
        odds_bet = np.asarray(b, dtype=np.float64) + 1.0
        lam = module3_lambda(active, state.window_a, state.window_b, structural, odds_bet,
                             np.asarray(p_hat, dtype=np.float64) * odds_bet - 1.0)
        if day not in self._lambda_zero_by_date:
            ev = estimated_expected_values(view.probs, view.odds)
            best = ev.argmax(axis=1)
            rows = np.arange(ev.shape[0])
            lam_all = module3_lambda(active, state.window_a, state.window_b, structural,
                                     np.asarray(view.odds)[rows, best], ev[rows, best])
            self._lambda_zero_by_date[day] = bool(np.all(lam_all == 0.0))
        fractions = _kelly_fractions(p_hat, b, lam)
        if self._abstain and state.out_of_support is not None:
            outside = state.out_of_support[_selected_rows(view)]
            self._n_abstained += int(outside.sum())
            fractions[outside] = 0.0
        return fractions

    def observe_results(self, results: DateResults) -> None:
        """Inoltra gli esiti della data regolata al supervisore."""
        self._supervisor.observe(results)


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
