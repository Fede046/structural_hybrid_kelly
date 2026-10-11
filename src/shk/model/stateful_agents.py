"""Agenti con stato dell'architettura di C6 (T50): la Baseline D come agente.

Gli agenti con stato ricevono gli esiti solo da Agent.observe_results, chiamato
dall'ambiente dopo il regolamento di ogni data, e cambiano solo le frazioni: selezione
dell'esito, ripiego e previsioni restano quelli della classe base (decisione S9).

Stato e repliche (scelta delegata di T50, opzione a): un agente con stato accetta un'unica
replica, M = 1, e lo verifica a ogni osservazione. I seed di S10 sono stagioni ricostruite,
cioè chiamate separate dell'ambiente, ciascuna con M = 1.

Baseline D (decisioni S5 e S9): λ_j = base · κ^k_j, con k_j il numero di allarmi del
detector su partite con Date strettamente anteriore a quella della partita j, e con
κ = 0 il moltiplicatore vale 1 senza allarmi e 0 con almeno un allarme, come
staking.compute_adaptive_lambda; frazione kelly_staking(p̂, o − 1, λ_j) sull'esito
selezionato. Il detector (river, istanza nuova per agente) si alimenta con la serie
scelta, una partita alla volta nell'ordine delle partite della data:
- "log_loss": −ln p̂(x), come la serie di C5;
- "delta": δ = ln p̂(x) − ln q(x), con q di Shin dalle quote della data (decisione S8).
"""

import math
from collections.abc import Mapping
from typing import Any, Final

import numpy as np

from shk.kelly.agents import Agent, DateResults, DateView
from shk.kelly.staking import BASE_LAMBDA, kelly_staking
from shk.market.devig import devig_shin
from shk.stats.drift import make_drift_detector

SERIES_LOG_LOSS: Final[str] = "log_loss"
SERIES_DELTA: Final[str] = "delta"
DETECTORS: Final[tuple[str, ...]] = ("adwin", "page_hinkley")


def adaptive_multiplier(kappa: float, n_alarms: int) -> float:
    """κ^k con la convenzione di compute_adaptive_lambda per κ = 0 (1 se k = 0, altrimenti 0)."""
    if kappa == 0.0:
        return 1.0 if n_alarms == 0 else 0.0
    return kappa**n_alarms


class BaselineDAgent(Agent):
    """Baseline D: quarto-Kelly ridotto di κ a ogni allarme del detector (vedi modulo).

    Parametri
    ---------
    name : str
        Nome dell'agente.
    detector : str
        "adwin" oppure "page_hinkley".
    detector_params : Mapping[str, Any]
        Parametri espliciti del detector (per esempio drift.detector_params(detector)).
    kappa : float
        Fattore di riduzione per allarme, in [0, 1].
    series : str, default "log_loss"
        Serie monitorata: "log_loss" oppure "delta".
    base_lambda : float, default BASE_LAMBDA
        λ senza allarmi.

    Solleva
    -------
    TypeError
        Se i tipi non sono validi.
    ValueError
        Se detector, series, kappa o base_lambda non sono ammessi.
    """

    def __init__(
        self,
        name: str,
        detector: str,
        detector_params: Mapping[str, Any],
        kappa: float,
        series: str = SERIES_LOG_LOSS,
        base_lambda: float = BASE_LAMBDA,
    ) -> None:
        super().__init__(name)
        if detector not in DETECTORS:
            raise ValueError(f"detector must be one of {DETECTORS}, got {detector!r}")
        if not isinstance(detector_params, Mapping):
            raise TypeError("detector_params must be a Mapping with explicit parameters")
        if series not in (SERIES_LOG_LOSS, SERIES_DELTA):
            raise ValueError(f"series must be 'log_loss' or 'delta', got {series!r}")
        for label, value in (("kappa", kappa), ("base_lambda", base_lambda)):
            if isinstance(value, bool) or not isinstance(value, (float, np.floating)):
                raise TypeError(f"{label} must be a float, got {type(value).__name__}")
            if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{label} must be in [0, 1], got {value}")
        self._detector = make_drift_detector(detector, dict(detector_params))
        self._kappa = float(kappa)
        self._base_lambda = float(base_lambda)
        self._series = series
        self._n_alarms = 0
        self._n_observed = 0

    @property
    def n_alarms(self) -> int:
        """Allarmi del detector sulle partite osservate finora."""
        return self._n_alarms

    @property
    def current_lambda(self) -> float:
        """λ in vigore per la prossima data."""
        return self._base_lambda * adaptive_multiplier(self._kappa, self._n_alarms)

    def stake_fractions(self, view: DateView, p_hat: np.ndarray, b: np.ndarray) -> np.ndarray:
        """kelly_staking(p̂, b, λ) elemento per elemento, con λ dagli allarmi già osservati."""
        lam = self.current_lambda
        fractions = np.empty(p_hat.shape[0], dtype=np.float64)
        for i in range(p_hat.shape[0]):
            fractions[i] = kelly_staking(float(p_hat[i]), float(b[i]), lam=lam)
        return fractions

    def _market_probs(self, results: DateResults) -> np.ndarray:
        """q di Shin dalle quote della data regolata, per la serie δ.

        Una sottoclasse può ridefinirlo per condividere il calcolo fra più agenti (T54).
        """
        q, _ = devig_shin(np.asarray(results.odds))
        return q

    def observe_results(self, results: DateResults) -> None:
        """Aggiorna il detector con la serie delle partite della data regolata (M = 1)."""
        if results.outcomes.shape[0] != 1:
            raise ValueError("BaselineDAgent requires a single replica (M = 1)")
        realized = results.outcomes[0]
        rows = np.arange(realized.shape[0])
        p_real = results.probs[rows, realized]
        if self._series == SERIES_LOG_LOSS:
            values = -np.log(p_real)
        else:
            q = self._market_probs(results)
            values = np.log(p_real) - np.log(q[rows, realized])
        for x in values:
            self._detector.update(float(x))
            self._n_observed += 1
            if self._detector.drift_detected:
                self._n_alarms += 1
