"""Modulo dell'ambiente di simulazione passo-passo del criterio di Kelly (Task 34).

L'ambiente esegue più agenti sulla stessa sequenza cronologica di date, previsioni,
quote ed esiti, gestendo la ricchezza come stato, il floor sulle puntate, la puntata
obbligatoria di ripiego e la rovina del capitale. Gli agenti forniscono unicamente
le frazioni desiderate di capitale tramite il metodo decide.

Codifica degli esiti: 0 = H, 1 = D, 2 = A; NO_BET (-1) indica nessuna puntata.
"""

from dataclasses import dataclass
import math
from typing import Final, Sequence

import numpy as np

from shk.kelly.agents import (
    NO_BET,
    Agent,
    AgentDecision,
    DateView,
    estimated_expected_values,
)

_N_OUTCOMES: Final[int] = 3


def _is_real_numeric_dtype(dtype: np.dtype) -> bool:
    """Indica se il dtype è numerico reale (intero o floating), escludendo bool e complessi.

    Parametri
    ---------
    dtype : np.dtype
        Dtype da controllare.

    Restituisce
    -----------
    bool
        True se il dtype è intero non booleano o floating.
    """
    if dtype == np.bool_:
        return False
    return bool(np.issubdtype(dtype, np.integer) or np.issubdtype(dtype, np.floating))


def _read_only_view(array: np.ndarray, dtype: type) -> np.ndarray:
    """Restituisce una vista non scrivibile di una copia privata e non scrivibile dell'array.

    Parametri
    ---------
    array : np.ndarray
        Array da copiare.
    dtype : type
        Dtype della copia (es. np.float64, np.int64, np.bool_).

    Restituisce
    -----------
    np.ndarray
        Vista non scrivibile della copia, senza memoria condivisa con l'input.
    """
    private_copy = np.array(array, dtype=dtype, copy=True)
    private_copy.setflags(write=False)
    view = private_copy.view()
    view.setflags(write=False)
    return view


def floor_thresholds(
    min_stake: float,
    f_star: float,
    lam: float,
) -> tuple[float, float, float]:
    """Calcola le soglie di ricchezza (B1, B2, B3) della Nota 2.9 §4.

    Formule:
        B1 = F / (lambda * f_star)
        B2 = F / (2 * f_star)
        B3 = F

    Parametri
    ---------
    min_stake : float
        Puntata minima fissa F > 0.
    f_star : float
        Frazione ottima di Kelly piena f* in (0, 1).
    lam : float
        Moltiplicatore di Kelly lambda in (0, 1].

    Restituisce
    -----------
    tuple[float, float, float]
        Terna delle soglie analitiche (B1, B2, B3).

    Solleva
    -------
    TypeError
        Se min_stake, f_star o lam non sono float o np.floating (compresi bool e int).
    ValueError
        Se i valori non sono finiti, se min_stake <= 0, se f_star non appartiene
        a (0, 1), oppure se lam non appartiene a (0, 1].
    """
    for param_name, param_val in (
        ("min_stake", min_stake),
        ("f_star", f_star),
        ("lam", lam),
    ):
        if isinstance(param_val, bool) or not isinstance(param_val, (float, np.floating)):
            raise TypeError(f"{param_name} must be a float, got {type(param_val).__name__}")
        if not math.isfinite(param_val):
            raise ValueError(f"{param_name} must be finite, got {param_val}")

    f_stake = float(min_stake)
    f_star_val = float(f_star)
    lam_val = float(lam)

    if f_stake <= 0.0:
        raise ValueError(f"min_stake must be strictly positive, got {min_stake}")
    if not (0.0 < f_star_val < 1.0):
        raise ValueError(f"f_star must be in (0, 1), got {f_star}")
    if not (0.0 < lam_val <= 1.0):
        raise ValueError(f"lam must be in (0, 1], got {lam}")

    b1 = f_stake / (lam_val * f_star_val)
    b2 = f_stake / (2.0 * f_star_val)
    b3 = f_stake
    return (b1, b2, b3)


@dataclass(frozen=True, eq=False)
class PlacedBets:
    """Puntate piazzate sulla data, esito per partita e contatori per replica.

    Attributi
    ---------
    stakes : np.ndarray
        Array float64 (M, n) delle puntate effettivamente piazzate per replica e partita.
    outcomes : np.ndarray
        Array int64 (n,) con l'esito puntato se la partita riceve una puntata (volontaria
        o forzata) in almeno una replica, oppure -1 (NO_BET) altrimenti.
    n_forced : np.ndarray
        Array int64 (M,) con il numero di puntate forzate piazzate sulla data per replica.
    n_floored : np.ndarray
        Array int64 (M,) con il numero di puntate volontarie alzate al floor e piazzate
        sulla data per replica.
    n_dropped : np.ndarray
        Array int64 (M,) con il numero di puntate volontarie scartate sulla data per replica.

    Solleva
    -------
    TypeError
        Se uno degli array non è un np.ndarray con il dtype prescritto.
    ValueError
        Se le dimensioni o le forme degli array non sono compatibili.
    """

    stakes: np.ndarray
    outcomes: np.ndarray
    n_forced: np.ndarray
    n_floored: np.ndarray
    n_dropped: np.ndarray

    def __post_init__(self) -> None:
        """Valida i campi e li converte in viste non scrivibili di copie private."""
        if not isinstance(self.stakes, np.ndarray):
            raise TypeError(f"stakes must be a numpy.ndarray, got {type(self.stakes).__name__}")
        if self.stakes.dtype != np.float64:
            raise TypeError(f"stakes must have float64 dtype, got {self.stakes.dtype}")

        if not isinstance(self.outcomes, np.ndarray):
            raise TypeError(f"outcomes must be a numpy.ndarray, got {type(self.outcomes).__name__}")
        if self.outcomes.dtype == np.bool_ or not np.issubdtype(self.outcomes.dtype, np.integer):
            raise TypeError(f"outcomes must have an integer dtype, got {self.outcomes.dtype}")

        for name, arr in (
            ("n_forced", self.n_forced),
            ("n_floored", self.n_floored),
            ("n_dropped", self.n_dropped),
        ):
            if not isinstance(arr, np.ndarray):
                raise TypeError(f"{name} must be a numpy.ndarray, got {type(arr).__name__}")
            if arr.dtype == np.bool_ or not np.issubdtype(arr.dtype, np.integer):
                raise TypeError(f"{name} must have an integer dtype, got {arr.dtype}")

        if self.stakes.ndim != 2:
            raise ValueError(f"stakes must be 2-dimensional, got shape {self.stakes.shape}")
        m_count, n_count = self.stakes.shape
        if self.outcomes.shape != (n_count,):
            raise ValueError(
                f"outcomes must have shape ({n_count},), got {self.outcomes.shape}"
            )
        for name, arr in (
            ("n_forced", self.n_forced),
            ("n_floored", self.n_floored),
            ("n_dropped", self.n_dropped),
        ):
            if arr.shape != (m_count,):
                raise ValueError(
                    f"{name} must have shape ({m_count},), got {arr.shape}"
                )

        object.__setattr__(self, "stakes", _read_only_view(self.stakes, np.float64))
        object.__setattr__(self, "outcomes", _read_only_view(self.outcomes, np.int64))
        object.__setattr__(self, "n_forced", _read_only_view(self.n_forced, np.int64))
        object.__setattr__(self, "n_floored", _read_only_view(self.n_floored, np.int64))
        object.__setattr__(self, "n_dropped", _read_only_view(self.n_dropped, np.int64))


def place_date_stakes(
    wealth: np.ndarray,
    view: DateView,
    decision: AgentDecision,
    min_stake: float,
) -> PlacedBets:
    """Calcola le puntate di una data per le sole repliche attive (non rovinate).

    Regole applicate in sequenza:
    a. Puntate volontarie: partite con frazione > 0, puntata desiderata f_i * W.
    b. Se F > 0, ogni puntata volontaria candidata vale max(f_i * W, F).
    c. Ordine di piazzamento: EV stimato decrescente dell'esito puntato, a parità
       l'indice di partita crescente. Si tiene il prefisso più lungo con somma <= W;
       le altre partite si scartano e si contano. Con W >= F la prima puntata entra sempre.
    d. Se F > 0 e non ci sono puntate volontarie: una puntata da F sul ripiego
       (fallback_match, fallback_outcome), contata come forzata.
    e. Se F = 0: niente floor, niente puntata forzata; resta solo la regola c.

    Parametri
    ---------
    wealth : np.ndarray
        Array float64 (M,) della ricchezza corrente delle repliche attive (M >= 1).
        Ogni elemento deve essere >= min_stake se min_stake > 0, oppure > 0 se min_stake == 0.
    view : DateView
        Vista in sola lettura delle partite della data.
    decision : AgentDecision
        Decisione dell'agente per le partite della data.
    min_stake : float
        Puntata minima fissa F >= 0.

    Restituisce
    -----------
    PlacedBets
        Dataclass con le puntate (M, n), l'esito puntato per partita (n,) e i contatori
        per replica (forzate, alzate al floor, scartate).

    Solleva
    -------
    TypeError
        Se gli argomenti non rispettano i tipi attesi.
    ValueError
        Se wealth ha forma o valori non validi, se contiene repliche rovinate (W < F o W <= 0),
        o se le dimensioni di view e decision non coincidono.
    """
    if not isinstance(wealth, np.ndarray):
        raise TypeError(f"wealth must be a numpy.ndarray, got {type(wealth).__name__}")
    if wealth.dtype != np.float64:
        raise TypeError(f"wealth must have float64 dtype, got {wealth.dtype}")
    if wealth.ndim != 1:
        raise ValueError(f"wealth must be 1-dimensional, got shape {wealth.shape}")
    m_count = wealth.shape[0]
    if m_count < 1:
        raise ValueError(f"wealth must contain at least one replica (M >= 1), got {m_count}")
    if not np.all(np.isfinite(wealth)):
        raise ValueError("wealth must contain only finite values")

    if not isinstance(view, DateView):
        raise TypeError(f"view must be a DateView, got {type(view).__name__}")
    if not isinstance(decision, AgentDecision):
        raise TypeError(f"decision must be an AgentDecision, got {type(decision).__name__}")

    n_matches = view.probs.shape[0]
    if decision.outcomes.shape[0] != n_matches:
        raise ValueError(
            f"decision matches ({decision.outcomes.shape[0]}) do not match view matches ({n_matches})"
        )

    if isinstance(min_stake, bool) or not isinstance(min_stake, (float, np.floating)):
        raise TypeError(f"min_stake must be a float, got {type(min_stake).__name__}")
    if not math.isfinite(min_stake) or min_stake < 0.0:
        raise ValueError(f"min_stake must be finite and >= 0, got {min_stake}")

    f_stake = float(min_stake)
    if f_stake > 0.0:
        if np.any(wealth < f_stake):
            raise ValueError(
                f"wealth must be >= min_stake ({f_stake}) for all active replicas"
            )
    else:
        if np.any(wealth <= 0.0):
            raise ValueError("wealth must be strictly positive for active replicas when min_stake is 0")

    voluntary_indices = np.flatnonzero(decision.fractions > 0.0)
    k_voluntary = voluntary_indices.shape[0]

    if k_voluntary == 0:
        # Nessuna puntata volontaria
        stakes = np.zeros((m_count, n_matches), dtype=np.float64)
        outcomes = np.full(n_matches, NO_BET, dtype=np.int64)
        if f_stake > 0.0:
            stakes[:, decision.fallback_match] = f_stake
            outcomes[decision.fallback_match] = decision.fallback_outcome
            n_forced = np.ones(m_count, dtype=np.int64)
        else:
            n_forced = np.zeros(m_count, dtype=np.int64)
        n_floored = np.zeros(m_count, dtype=np.int64)
        n_dropped = np.zeros(m_count, dtype=np.int64)
        return PlacedBets(
            stakes=stakes,
            outcomes=outcomes,
            n_forced=n_forced,
            n_floored=n_floored,
            n_dropped=n_dropped,
        )

    # Puntate volontarie presenti
    ev = estimated_expected_values(view.probs, view.odds)
    ev_voluntary = ev[voluntary_indices, decision.outcomes[voluntary_indices]]

    # Ordinamento: EV stimato decrescente, parità spezzata dall'indice di partita crescente
    sort_keys = [
        (-float(ev_voluntary[i]), int(voluntary_indices[i]))
        for i in range(k_voluntary)
    ]
    sort_order = sorted(range(k_voluntary), key=lambda idx: sort_keys[idx])
    ordered_matches = voluntary_indices[sort_order]
    ordered_fractions = decision.fractions[ordered_matches]

    # Matrice puntate candidate (M, k)
    wealth_col = wealth[:, None]
    desired_stakes = wealth_col * ordered_fractions[None, :]
    if f_stake > 0.0:
        candidate_stakes = np.maximum(desired_stakes, f_stake)
    else:
        candidate_stakes = desired_stakes.copy()

    # Prefisso cumulativo con somma <= W
    cum_stakes = np.cumsum(candidate_stakes, axis=1)
    keep_mask = cum_stakes <= wealth_col

    final_k_stakes = np.where(keep_mask, candidate_stakes, 0.0)

    n_dropped = np.sum(~keep_mask, axis=1, dtype=np.int64)
    if f_stake > 0.0:
        floored_mask = keep_mask & (desired_stakes < f_stake)
        n_floored = np.sum(floored_mask, axis=1, dtype=np.int64)
    else:
        n_floored = np.zeros(m_count, dtype=np.int64)
    n_forced = np.zeros(m_count, dtype=np.int64)

    stakes = np.zeros((m_count, n_matches), dtype=np.float64)
    stakes[:, ordered_matches] = final_k_stakes

    has_placed_stake = np.any(stakes > 0.0, axis=0)
    outcomes = np.where(has_placed_stake, decision.outcomes, NO_BET)

    return PlacedBets(
        stakes=stakes,
        outcomes=outcomes,
        n_forced=n_forced,
        n_floored=n_floored,
        n_dropped=n_dropped,
    )


@dataclass(frozen=True, eq=False)
class AgentRun:
    """Risultato del backtest appaiato per un agente.

    Tutti gli array sono esposti come viste non scrivibili di copie private.

    Attributi
    ---------
    name : str
        Nome dell'agente.
    dates : np.ndarray
        Array datetime64 (D,) delle date distinte simulate.
    wealth : np.ndarray
        Array float64 (M, D+1) con la ricchezza cumulativa; colonna 0 pari a 1.0.
    ruined : np.ndarray
        Array bool (M,) indicante se ciascuna replica è andata in rovina.
    ruin_date_index : np.ndarray
        Array int64 (M,) con l'indice della data di rovina (-1 se mai rovinata).
    n_bets : np.ndarray
        Array int64 (M,) con il numero totale di puntate piazzate.
    n_forced : np.ndarray
        Array int64 (M,) con il numero totale di puntate forzate sul ripiego.
    n_floored : np.ndarray
        Array int64 (M,) con il numero totale di puntate alzate al floor.
    n_dropped : np.ndarray
        Array int64 (M,) con il numero totale di puntate scartate.
    staked : np.ndarray | None
        Array float64 (M, D) con la somma delle puntate piazzate per data se
        record_stakes=True, altrimenti None.
    desired : np.ndarray | None
        Array float64 (M, D) con la somma delle puntate desiderate per data se
        record_stakes=True, altrimenti None.
    """

    name: str
    dates: np.ndarray
    wealth: np.ndarray
    ruined: np.ndarray
    ruin_date_index: np.ndarray
    n_bets: np.ndarray
    n_forced: np.ndarray
    n_floored: np.ndarray
    n_dropped: np.ndarray
    staked: np.ndarray | None = None
    desired: np.ndarray | None = None

    def __post_init__(self) -> None:
        """Valida i campi e li converte in viste non scrivibili di copie private."""
        if not isinstance(self.name, str) or len(self.name) == 0:
            raise TypeError("name must be a non-empty string")

        if not isinstance(self.dates, np.ndarray) or not np.issubdtype(self.dates.dtype, np.datetime64):
            raise TypeError("dates must be a numpy.ndarray with datetime64 dtype")
        d_count = self.dates.shape[0]

        if not isinstance(self.wealth, np.ndarray) or self.wealth.dtype != np.float64:
            raise TypeError("wealth must be a numpy.ndarray with float64 dtype")
        if self.wealth.ndim != 2 or self.wealth.shape[1] != d_count + 1:
            raise ValueError(
                f"wealth must have shape (M, {d_count + 1}), got {self.wealth.shape}"
            )
        m_count = self.wealth.shape[0]

        if not isinstance(self.ruined, np.ndarray) or self.ruined.dtype != np.bool_:
            raise TypeError("ruined must be a numpy.ndarray with bool dtype")
        if self.ruined.shape != (m_count,):
            raise ValueError(f"ruined must have shape ({m_count},), got {self.ruined.shape}")

        for arr_name, arr in (
            ("ruin_date_index", self.ruin_date_index),
            ("n_bets", self.n_bets),
            ("n_forced", self.n_forced),
            ("n_floored", self.n_floored),
            ("n_dropped", self.n_dropped),
        ):
            if not isinstance(arr, np.ndarray) or arr.dtype != np.int64:
                raise TypeError(f"{arr_name} must be a numpy.ndarray with int64 dtype")
            if arr.shape != (m_count,):
                raise ValueError(f"{arr_name} must have shape ({m_count},), got {arr.shape}")

        if self.staked is not None:
            if not isinstance(self.staked, np.ndarray) or self.staked.dtype != np.float64:
                raise TypeError("staked must be a numpy.ndarray with float64 dtype")
            if self.staked.shape != (m_count, d_count):
                raise ValueError(
                    f"staked must have shape ({m_count}, {d_count}), got {self.staked.shape}"
                )
            object.__setattr__(self, "staked", _read_only_view(self.staked, np.float64))

        if self.desired is not None:
            if not isinstance(self.desired, np.ndarray) or self.desired.dtype != np.float64:
                raise TypeError("desired must be a numpy.ndarray with float64 dtype")
            if self.desired.shape != (m_count, d_count):
                raise ValueError(
                    f"desired must have shape ({m_count}, {d_count}), got {self.desired.shape}"
                )
            object.__setattr__(self, "desired", _read_only_view(self.desired, np.float64))

        object.__setattr__(self, "dates", _read_only_view(self.dates, self.dates.dtype.type))
        object.__setattr__(self, "wealth", _read_only_view(self.wealth, np.float64))
        object.__setattr__(self, "ruined", _read_only_view(self.ruined, np.bool_))
        object.__setattr__(self, "ruin_date_index", _read_only_view(self.ruin_date_index, np.int64))
        object.__setattr__(self, "n_bets", _read_only_view(self.n_bets, np.int64))
        object.__setattr__(self, "n_forced", _read_only_view(self.n_forced, np.int64))
        object.__setattr__(self, "n_floored", _read_only_view(self.n_floored, np.int64))
        object.__setattr__(self, "n_dropped", _read_only_view(self.n_dropped, np.int64))


def run_paired_backtest(
    agents: Sequence[Agent],
    dates: np.ndarray,
    probs: np.ndarray,
    odds: np.ndarray,
    outcomes: np.ndarray,
    min_stake: float,
    record_stakes: bool = False,
) -> tuple[AgentRun, ...]:
    """Esegue il backtest appaiato su più agenti sulla stessa sequenza temporale.

    Parametri
    ---------
    agents : Sequence[Agent]
        Sequenza di istanze di Agent, almeno una, con nomi distinti.
    dates : np.ndarray
        Array datetime64 (N,) non decrescente senza NaT.
    probs : np.ndarray
        Matrice float64 (N, 3) delle probabilità stimate in ordine H, D, A.
    odds : np.ndarray
        Matrice float64 (N, 3) delle quote decimali lorde in ordine H, D, A.
    outcomes : np.ndarray
        Matrice intera (M, N) degli esiti realizzati in {0, 1, 2}, con M >= 1.
    min_stake : float
        Puntata minima fissa F >= 0.
    record_stakes : bool, default=False
        Se True, popola i campi staked e desired in AgentRun.

    Restituisce
    -----------
    tuple[AgentRun, ...]
        Tupla dei risultati, nell'ordine originale degli agenti.

    Solleva
    -------
    TypeError
        Se gli argomenti non rispettano i tipi attesi.
    ValueError
        Se le dimensioni o i valori degli array non sono validi o conformi.
    """
    if not isinstance(agents, (tuple, list)):
        raise TypeError(f"agents must be a tuple or list of Agent, got {type(agents).__name__}")
    if len(agents) < 1:
        raise ValueError("agents must contain at least one Agent")
    for a in agents:
        if not isinstance(a, Agent):
            raise TypeError(f"Each agent must be an instance of Agent, got {type(a).__name__}")
    agent_names = [a.name for a in agents]
    if len(set(agent_names)) != len(agent_names):
        raise ValueError("All agent names must be distinct")

    if not isinstance(dates, np.ndarray):
        raise TypeError(f"dates must be a numpy.ndarray, got {type(dates).__name__}")
    if not np.issubdtype(dates.dtype, np.datetime64):
        raise TypeError(f"dates must have datetime64 dtype, got {dates.dtype}")
    if dates.ndim != 1:
        raise ValueError(f"dates must be 1-dimensional, got shape {dates.shape}")
    if np.any(np.isnat(dates)):
        raise ValueError("dates must not contain NaT")
    if dates.shape[0] > 1 and np.any(dates[1:] < dates[:-1]):
        raise ValueError("dates must be in non-decreasing order")

    n_matches = dates.shape[0]

    for name_arg, arr_arg in (("probs", probs), ("odds", odds)):
        if not isinstance(arr_arg, np.ndarray):
            raise TypeError(f"{name_arg} must be a numpy.ndarray, got {type(arr_arg).__name__}")
        if not _is_real_numeric_dtype(arr_arg.dtype):
            raise TypeError(f"{name_arg} must have a real numeric dtype, got {arr_arg.dtype}")
        if arr_arg.ndim != 2 or arr_arg.shape != (n_matches, _N_OUTCOMES):
            raise ValueError(
                f"{name_arg} must have shape ({n_matches}, {_N_OUTCOMES}), got {arr_arg.shape}"
            )
        if not np.all(np.isfinite(arr_arg)):
            raise ValueError(f"{name_arg} must contain only finite values")

    probs_arr = np.asarray(probs, dtype=np.float64)
    odds_arr = np.asarray(odds, dtype=np.float64)

    if np.any(probs_arr < 0.0) or np.any(probs_arr > 1.0):
        raise ValueError("probs must have values in [0, 1]")
    if np.any(np.abs(probs_arr.sum(axis=1) - 1.0) > 1e-9):
        raise ValueError("Each row of probs must sum to 1 within 1e-9")
    if np.any(odds_arr <= 1.0):
        raise ValueError("odds must be strictly greater than 1.0")

    if not isinstance(outcomes, np.ndarray):
        raise TypeError(f"outcomes must be a numpy.ndarray, got {type(outcomes).__name__}")
    if outcomes.dtype == np.bool_ or not np.issubdtype(outcomes.dtype, np.integer):
        raise TypeError(f"outcomes must have an integer dtype, got {outcomes.dtype}")
    if outcomes.ndim != 2:
        raise ValueError(f"outcomes must be 2-dimensional, got shape {outcomes.shape}")
    m_replicas = outcomes.shape[0]
    if m_replicas < 1:
        raise ValueError(f"outcomes must contain at least one replica (M >= 1), got {m_replicas}")
    if outcomes.shape[1] != n_matches:
        raise ValueError(
            f"outcomes must have shape (M, {n_matches}), got {outcomes.shape}"
        )
    if np.any(~np.isin(outcomes, (0, 1, 2))):
        raise ValueError("outcomes must contain only values in {0, 1, 2}")

    if isinstance(min_stake, bool) or not isinstance(min_stake, (float, np.floating)):
        raise TypeError(f"min_stake must be a float, got {type(min_stake).__name__}")
    if not math.isfinite(min_stake) or min_stake < 0.0:
        raise ValueError(f"min_stake must be finite and >= 0, got {min_stake}")

    if not isinstance(record_stakes, bool):
        raise TypeError(f"record_stakes must be a bool, got {type(record_stakes).__name__}")

    f_stake = float(min_stake)

    if n_matches == 0:
        unique_dates = np.empty((0,), dtype=dates.dtype)
        runs_empty: list[AgentRun] = []
        for a in agents:
            runs_empty.append(
                AgentRun(
                    name=a.name,
                    dates=unique_dates,
                    wealth=np.ones((m_replicas, 1), dtype=np.float64),
                    ruined=np.zeros(m_replicas, dtype=np.bool_),
                    ruin_date_index=np.full(m_replicas, -1, dtype=np.int64),
                    n_bets=np.zeros(m_replicas, dtype=np.int64),
                    n_forced=np.zeros(m_replicas, dtype=np.int64),
                    n_floored=np.zeros(m_replicas, dtype=np.int64),
                    n_dropped=np.zeros(m_replicas, dtype=np.int64),
                    staked=np.zeros((m_replicas, 0), dtype=np.float64) if record_stakes else None,
                    desired=np.zeros((m_replicas, 0), dtype=np.float64) if record_stakes else None,
                )
            )
        return tuple(runs_empty)

    unique_dates, split_indices = np.unique(dates, return_index=True)
    sort_order = np.argsort(split_indices)
    unique_dates = unique_dates[sort_order]
    d_distinct = unique_dates.shape[0]

    n_agents = len(agents)
    wealth_all = [np.zeros((m_replicas, d_distinct + 1), dtype=np.float64) for _ in range(n_agents)]
    for w in wealth_all:
        w[:, 0] = 1.0

    ruined_all = [np.zeros(m_replicas, dtype=np.bool_) for _ in range(n_agents)]
    ruin_date_idx_all = [np.full(m_replicas, -1, dtype=np.int64) for _ in range(n_agents)]
    n_bets_all = [np.zeros(m_replicas, dtype=np.int64) for _ in range(n_agents)]
    n_forced_all = [np.zeros(m_replicas, dtype=np.int64) for _ in range(n_agents)]
    n_floored_all = [np.zeros(m_replicas, dtype=np.int64) for _ in range(n_agents)]
    n_dropped_all = [np.zeros(m_replicas, dtype=np.int64) for _ in range(n_agents)]

    staked_all = (
        [np.zeros((m_replicas, d_distinct), dtype=np.float64) for _ in range(n_agents)]
        if record_stakes
        else None
    )
    desired_all = (
        [np.zeros((m_replicas, d_distinct), dtype=np.float64) for _ in range(n_agents)]
        if record_stakes
        else None
    )

    for d_idx, d_date in enumerate(unique_dates):
        mask = (dates == d_date)
        d_probs = probs_arr[mask]
        d_odds = odds_arr[mask]
        view = DateView(date=d_date, probs=d_probs, odds=d_odds)
        d_outcomes_all_m = outcomes[:, mask]
        n_date_matches = d_probs.shape[0]

        for a_idx, agent in enumerate(agents):
            decision = agent.decide(view)

            w_current = wealth_all[a_idx][:, d_idx]

            # 3. Rovina all'inizio della data
            if f_stake > 0.0:
                is_ruin = (w_current < f_stake) | (w_current == 0.0)
            else:
                is_ruin = w_current <= 0.0

            newly_ruined = (~ruined_all[a_idx]) & is_ruin
            ruined_all[a_idx][newly_ruined] = True
            ruin_date_idx_all[a_idx][newly_ruined] = d_idx

            active_mask = ~ruined_all[a_idx]
            n_active = int(np.sum(active_mask))

            if n_active >= 1:
                active_wealth = w_current[active_mask]
                placed = place_date_stakes(active_wealth, view, decision, f_stake)

                n_forced_all[a_idx][active_mask] += placed.n_forced
                n_floored_all[a_idx][active_mask] += placed.n_floored
                n_dropped_all[a_idx][active_mask] += placed.n_dropped
                n_bets_all[a_idx][active_mask] += np.sum(placed.stakes > 0.0, axis=1, dtype=np.int64)

                if record_stakes and staked_all is not None and desired_all is not None:
                    staked_all[a_idx][active_mask, d_idx] = np.sum(placed.stakes, axis=1)
                    desired_all[a_idx][active_mask, d_idx] = np.sum(
                        decision.fractions[None, :] * active_wealth[:, None], axis=1
                    )

                # 4. Regolamento
                active_realized = d_outcomes_all_m[active_mask, :]
                placed_outcomes = placed.outcomes

                has_bet = placed_outcomes != NO_BET
                if np.any(has_bet):
                    valid_matches = np.flatnonzero(has_bet)
                    valid_outcomes = placed_outcomes[valid_matches]
                    valid_odds = view.odds[valid_matches, valid_outcomes]

                    won = active_realized[:, valid_matches] == valid_outcomes[None, :]
                    r_matrix = np.where(won, valid_odds[None, :] - 1.0, -1.0)
                    net_return = np.sum(placed.stakes[:, valid_matches] * r_matrix, axis=1)
                else:
                    net_return = np.zeros(n_active, dtype=np.float64)

                wealth_all[a_idx][active_mask, d_idx + 1] = active_wealth + net_return
                wealth_all[a_idx][~active_mask, d_idx + 1] = w_current[~active_mask]
            else:
                wealth_all[a_idx][:, d_idx + 1] = w_current

    runs: list[AgentRun] = []
    for a_idx, agent in enumerate(agents):
        runs.append(
            AgentRun(
                name=agent.name,
                dates=unique_dates,
                wealth=wealth_all[a_idx],
                ruined=ruined_all[a_idx],
                ruin_date_index=ruin_date_idx_all[a_idx],
                n_bets=n_bets_all[a_idx],
                n_forced=n_forced_all[a_idx],
                n_floored=n_floored_all[a_idx],
                n_dropped=n_dropped_all[a_idx],
                staked=staked_all[a_idx] if record_stakes else None,
                desired=desired_all[a_idx] if record_stakes else None,
            )
        )

    return tuple(runs)
