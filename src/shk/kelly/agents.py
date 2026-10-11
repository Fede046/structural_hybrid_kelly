"""Modulo degli agenti di scommessa come classi con una base comune (Task 33 / US-C6.1).

La classe base Agent esegue ciò che gli agenti condividono: selezione dell'esito per
partita, ripiego sulla data, validazioni e sola lettura degli input. Ogni sottoclasse
ridefinisce soltanto la regola di staking, cioè la frazione di capitale per gli esiti
selezionati. Il bankroll non entra in questo modulo: floor, puntata obbligatoria e
rovina sono responsabilità dell'ambiente.

Codifica degli esiti: 0 = H, 1 = D, 2 = A; NO_BET (-1) indica nessuna puntata volontaria.
"""

import abc
import inspect
import math
from dataclasses import dataclass
from types import FunctionType
from typing import Any, Final

import numpy as np

from shk.kelly.staking import kelly_staking

# Codice dell'esito per le partite senza puntata volontaria
NO_BET: Final[int] = -1

# Moltiplicatori di Kelly degli agenti A (Kelly pieno) e B (Kelly frazionario)
AGENT_A_LAMBDA: Final[float] = 1.0
AGENT_B_LAMBDAS: Final[tuple[float, ...]] = (0.25, 0.10)

# Numero di esiti del mercato 1X2 e tolleranza sulla somma delle probabilità di riga
_N_OUTCOMES: Final[int] = 3
_ROW_SUM_TOLERANCE: Final[float] = 1e-9

# Membri di Agent che una sottoclasse può ridefinire
_OVERRIDABLE_MEMBERS: Final[frozenset[str]] = frozenset({"__init__", "stake_fractions"})


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

    La copia è resa non scrivibile prima di crearne la vista: in questo modo anche
    setflags(write=True) sulla vista solleva ValueError, perché la sua base non è
    scrivibile. Il vincolo resta aggirabile solo passando dall'attributo base.

    Parametri
    ---------
    array : np.ndarray
        Array da copiare.
    dtype : type
        Dtype della copia (np.float64 o np.int64).

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


def _validate_outcome_matrices(probs: np.ndarray, odds: np.ndarray) -> None:
    """Valida tipo, dtype, forma e finitezza di due matrici (n, 3) di probabilità e quote.

    Parametri
    ---------
    probs : np.ndarray
        Matrice candidata delle probabilità stimate.
    odds : np.ndarray
        Matrice candidata delle quote decimali lorde.

    Solleva
    -------
    TypeError
        Se probs o odds non sono np.ndarray, o se hanno un dtype non numerico reale.
    ValueError
        Se probs non ha forma (n, 3) con n >= 1, se odds ha forma diversa da probs,
        o se uno dei due contiene valori non finiti.
    """
    for arg_name, arg in (("probs", probs), ("odds", odds)):
        if not isinstance(arg, np.ndarray):
            raise TypeError(f"{arg_name} must be a numpy.ndarray, got {type(arg).__name__}")
        if not _is_real_numeric_dtype(arg.dtype):
            raise TypeError(f"{arg_name} must have a real integer or floating dtype, got {arg.dtype}")

    if probs.ndim != 2 or probs.shape[1] != _N_OUTCOMES:
        raise ValueError(f"probs must have shape (n, 3), got {probs.shape}")
    if probs.shape[0] < 1:
        raise ValueError("probs must contain at least one match (n >= 1)")
    if odds.shape != probs.shape:
        raise ValueError(f"odds must have the same shape as probs {probs.shape}, got {odds.shape}")
    if not np.all(np.isfinite(probs)):
        raise ValueError("probs must contain only finite values")
    if not np.all(np.isfinite(odds)):
        raise ValueError("odds must contain only finite values")


@dataclass(frozen=True, eq=False)
class DateView:
    """Vista in sola lettura delle partite di una data, con probabilità stimate e quote.

    Il costruttore copia probs e odds in float64 e salva nei campi viste non scrivibili
    di copie non scrivibili: le scritture e setflags(write=True) sui campi sollevano
    ValueError, e i campi non condividono memoria con gli array ricevuti.

    Attributi
    ---------
    date : np.datetime64
        Data delle partite.
    probs : np.ndarray
        Matrice float64 (n, 3) delle probabilità stimate in ordine H, D, A, n >= 1,
        valori in [0, 1] e righe a somma 1 entro 1e-9.
    odds : np.ndarray
        Matrice float64 (n, 3) delle quote decimali lorde in ordine H, D, A, finite e > 1.

    Solleva
    -------
    TypeError
        Se date non è np.datetime64, se probs o odds non sono np.ndarray o hanno un dtype
        non numerico reale (bool, complessi, stringhe, object).
    ValueError
        Se date è NaT, se le forme non sono (n, 3) uguali con n >= 1, se compaiono valori
        non finiti, probabilità fuori da [0, 1], righe che non sommano a 1 entro 1e-9,
        oppure quote <= 1.
    """

    date: np.datetime64
    probs: np.ndarray
    odds: np.ndarray

    def __post_init__(self) -> None:
        """Valida i campi e li sostituisce con viste float64 non scrivibili di copie private."""
        if not isinstance(self.date, np.datetime64):
            raise TypeError(f"date must be a numpy.datetime64, got {type(self.date).__name__}")
        if np.isnat(self.date):
            raise ValueError("date must not be NaT")

        _validate_outcome_matrices(self.probs, self.odds)

        probs = _read_only_view(self.probs, np.float64)
        odds = _read_only_view(self.odds, np.float64)

        if np.any(probs < 0.0) or np.any(probs > 1.0):
            raise ValueError("probs must have values in [0, 1]")
        if np.any(np.abs(probs.sum(axis=1) - 1.0) > _ROW_SUM_TOLERANCE):
            raise ValueError(f"Each row of probs must sum to 1 within {_ROW_SUM_TOLERANCE}")
        if np.any(odds <= 1.0):
            raise ValueError("odds must be strictly greater than 1.0")

        object.__setattr__(self, "probs", probs)
        object.__setattr__(self, "odds", odds)


def estimated_expected_values(probs: np.ndarray, odds: np.ndarray) -> np.ndarray:
    """Calcola il valore atteso stimato di una puntata unitaria per ogni partita ed esito.

    Unica formula dell'EV stimato del pacchetto agenti, usata per la selezione e per il
    ripiego:
        EV = p_hat * o - 1

    Parametri
    ---------
    probs : np.ndarray
        Matrice (n, 3) delle probabilità stimate in ordine H, D, A, con n >= 1.
    odds : np.ndarray
        Matrice (n, 3) delle quote decimali lorde in ordine H, D, A.

    Restituisce
    -----------
    np.ndarray
        Matrice float64 (n, 3) di p_hat * o - 1.

    Solleva
    -------
    TypeError
        Se probs o odds non sono np.ndarray o hanno un dtype non numerico reale.
    ValueError
        Se le forme non sono (n, 3) uguali con n >= 1 o se compaiono valori non finiti.
    """
    _validate_outcome_matrices(probs, odds)
    p = np.asarray(probs, dtype=np.float64)
    o = np.asarray(odds, dtype=np.float64)
    return p * o - 1.0


@dataclass(frozen=True, eq=False)
class AgentDecision:
    """Decisione di un agente per le partite di una data.

    Gli array salvati nei campi sono viste non scrivibili di copie private non scrivibili,
    come in DateView.

    Attributi
    ---------
    outcomes : np.ndarray
        Array int64 (n,) con l'esito della puntata volontaria per partita: 0 = H, 1 = D,
        2 = A, NO_BET (-1) se l'agente non punta.
    fractions : np.ndarray
        Array float64 (n,) delle frazioni di capitale, finite, in [0, 1), nulle dove
        outcomes vale NO_BET.
    fallback_match : int
        Indice in [0, n) della partita del ripiego (EV stimato massimo sulla data).
    fallback_outcome : int
        Esito del ripiego, in {0, 1, 2}.

    Solleva
    -------
    TypeError
        Se outcomes non è un np.ndarray di dtype intero non booleano, se fractions non è un
        np.ndarray di dtype floating, o se fallback_match o fallback_outcome non sono interi
        (bool esclusi).
    ValueError
        Se outcomes non è 1D con almeno un elemento, se fractions ha forma diversa, se
        outcomes contiene valori fuori da {-1, 0, 1, 2}, se fractions contiene valori non
        finiti, negativi o >= 1, o non nulli dove outcomes vale NO_BET, oppure se il ripiego
        è fuori intervallo.
    """

    outcomes: np.ndarray
    fractions: np.ndarray
    fallback_match: int
    fallback_outcome: int

    def __post_init__(self) -> None:
        """Valida i campi e sostituisce gli array con viste non scrivibili di copie private."""
        if not isinstance(self.outcomes, np.ndarray):
            raise TypeError(f"outcomes must be a numpy.ndarray, got {type(self.outcomes).__name__}")
        if self.outcomes.dtype == np.bool_ or not np.issubdtype(self.outcomes.dtype, np.integer):
            raise TypeError(f"outcomes must have an integer dtype, got {self.outcomes.dtype}")
        if not isinstance(self.fractions, np.ndarray):
            raise TypeError(f"fractions must be a numpy.ndarray, got {type(self.fractions).__name__}")
        if not np.issubdtype(self.fractions.dtype, np.floating):
            raise TypeError(f"fractions must have a floating dtype, got {self.fractions.dtype}")
        for field_name, value in (
            ("fallback_match", self.fallback_match),
            ("fallback_outcome", self.fallback_outcome),
        ):
            if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
                raise TypeError(f"{field_name} must be an int, got {type(value).__name__}")

        if self.outcomes.ndim != 1:
            raise ValueError(f"outcomes must be 1-dimensional, got shape {self.outcomes.shape}")
        n_matches = self.outcomes.shape[0]
        if n_matches < 1:
            raise ValueError("outcomes must contain at least one match")
        if self.fractions.shape != (n_matches,):
            raise ValueError(
                f"fractions must have shape ({n_matches},), got {self.fractions.shape}"
            )
        if np.any(~np.isin(self.outcomes, (NO_BET, 0, 1, 2))):
            raise ValueError("outcomes must contain only -1, 0, 1, 2")
        if not np.all(np.isfinite(self.fractions)):
            raise ValueError("fractions must contain only finite values")
        if np.any(self.fractions < 0.0) or np.any(self.fractions >= 1.0):
            raise ValueError("fractions must be in [0, 1)")
        if np.any(self.fractions[self.outcomes == NO_BET] != 0.0):
            raise ValueError("fractions must be zero where outcomes is -1")
        if not 0 <= int(self.fallback_match) < n_matches:
            raise ValueError(
                f"fallback_match must be in [0, {n_matches}), got {self.fallback_match}"
            )
        if int(self.fallback_outcome) not in (0, 1, 2):
            raise ValueError(f"fallback_outcome must be 0, 1 or 2, got {self.fallback_outcome}")

        object.__setattr__(self, "outcomes", _read_only_view(self.outcomes, np.int64))
        object.__setattr__(self, "fractions", _read_only_view(self.fractions, np.float64))
        object.__setattr__(self, "fallback_match", int(self.fallback_match))
        object.__setattr__(self, "fallback_outcome", int(self.fallback_outcome))


def _validate_stake_output(result: object, n_selected: int) -> np.ndarray:
    """Valida l'uscita di stake_fractions e la restituisce come array float64.

    Parametri
    ---------
    result : object
        Valore restituito da stake_fractions.
    n_selected : int
        Numero k di esiti selezionati, cioè la lunghezza attesa dell'uscita.

    Restituisce
    -----------
    np.ndarray
        Array float64 (k,) delle frazioni validate.

    Solleva
    -------
    TypeError
        Se result non è un np.ndarray o non ha dtype floating.
    ValueError
        Se result non ha forma (k,) o contiene valori non finiti, negativi o >= 1.
    """
    if not isinstance(result, np.ndarray):
        raise TypeError(f"stake_fractions must return a numpy.ndarray, got {type(result).__name__}")
    if not np.issubdtype(result.dtype, np.floating):
        raise TypeError(f"stake_fractions must return a floating array, got dtype {result.dtype}")
    if result.shape != (n_selected,):
        raise ValueError(
            f"stake_fractions must return shape ({n_selected},), got {result.shape}"
        )
    if not np.all(np.isfinite(result)):
        raise ValueError("stake_fractions must return finite values")
    if np.any(result < 0.0) or np.any(result >= 1.0):
        raise ValueError("stake_fractions must return values in [0, 1)")
    return np.asarray(result, dtype=np.float64)


class Agent(abc.ABC):
    """Classe base astratta degli agenti di scommessa.

    La base esegue in decide la selezione dell'esito, le validazioni e il ripiego;
    una sottoclasse può ridefinire soltanto __init__ e stake_fractions. Ogni altra
    ridefinizione di un metodo o di una proprietà di Agent, anche tramite un mixin,
    solleva TypeError alla definizione della sottoclasse.

    Parametri
    ---------
    name : str
        Nome non vuoto dell'agente, esposto come proprietà in sola lettura.

    Solleva
    -------
    TypeError
        Se name non è una stringa.
    ValueError
        Se name è la stringa vuota.
    """

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Impedisce alle sottoclassi di ridefinire metodi e proprietà di Agent non ammessi.

        Parametri
        ---------
        **kwargs : Any
            Argomenti di parola chiave inoltrati a object.__init_subclass__.

        Solleva
        -------
        TypeError
            Se la sottoclasse, direttamente o tramite un'altra base, ridefinisce un metodo o
            una proprietà di Agent diversi da __init__ e stake_fractions.
        """
        super().__init_subclass__(**kwargs)
        protected_kinds = (FunctionType, property, classmethod, staticmethod)
        for member_name, member in vars(Agent).items():
            if member_name in _OVERRIDABLE_MEMBERS or not isinstance(member, protected_kinds):
                continue
            if inspect.getattr_static(cls, member_name) is not member:
                raise TypeError(
                    f"{cls.__name__} must not override Agent.{member_name}; "
                    "only __init__ and stake_fractions may be overridden"
                )

    def __init__(self, name: str) -> None:
        """Inizializza l'agente con un nome non vuoto.

        Parametri
        ---------
        name : str
            Nome non vuoto dell'agente.

        Solleva
        -------
        TypeError
            Se name non è una stringa.
        ValueError
            Se name è la stringa vuota.
        """
        if not isinstance(name, str):
            raise TypeError(f"name must be a str, got {type(name).__name__}")
        if len(name) == 0:
            raise ValueError("name must be a non-empty string")
        self._name = name

    @property
    def name(self) -> str:
        """Nome dell'agente, in sola lettura."""
        return self._name

    def decide(self, view: DateView) -> AgentDecision:
        """Calcola la decisione dell'agente per le partite di una data.

        Passi, nell'ordine:
        1. per ogni partita, l'esito con EV stimato massimo (np.argmax, parità nell'ordine
           H, D, A), selezionato solo se il suo EV è > 0;
        2. stake_fractions(view, p_hat, b) sui soli esiti selezionati, con p_hat e
           b = o - 1 di forma (k,) non scrivibili, anche con k = 0;
        3. validazione dell'uscita; frazione nulla sulle partite non selezionate;
        4. ripiego: la coppia (partita, esito) con EV stimato massimo su tutta la data,
           np.argmax sulla matrice (n, 3) appiattita per righe, anche con EV <= 0.

        Parametri
        ---------
        view : DateView
            Vista in sola lettura delle partite della data.

        Restituisce
        -----------
        AgentDecision
            Esiti, frazioni e ripiego della data.

        Solleva
        -------
        TypeError
            Se view non è un DateView, o se stake_fractions restituisce un oggetto che non
            è un np.ndarray di dtype floating.
        ValueError
            Se stake_fractions restituisce una forma diversa da (k,) o valori non finiti,
            negativi o >= 1, oppure se scrive su un array non scrivibile.
        """
        if not isinstance(view, DateView):
            raise TypeError(f"view must be a DateView, got {type(view).__name__}")

        ev = estimated_expected_values(view.probs, view.odds)
        n_matches = ev.shape[0]

        # 1. Esito con EV stimato massimo per partita, selezionato solo se EV > 0
        best_outcomes = np.argmax(ev, axis=1)
        best_ev = ev[np.arange(n_matches), best_outcomes]
        selected_rows = np.flatnonzero(best_ev > 0.0)
        selected_outcomes = best_outcomes[selected_rows]

        # 2. Regola di staking sui soli esiti selezionati, con input non scrivibili
        p_hat = _read_only_view(view.probs[selected_rows, selected_outcomes], np.float64)
        b = _read_only_view(view.odds[selected_rows, selected_outcomes] - 1.0, np.float64)
        raw_fractions = self.stake_fractions(view, p_hat, b)

        # 3. Validazione dell'uscita e frazione nulla sulle partite non selezionate
        selected_fractions = _validate_stake_output(raw_fractions, selected_rows.shape[0])
        outcomes = np.full(n_matches, NO_BET, dtype=np.int64)
        outcomes[selected_rows] = selected_outcomes
        fractions = np.zeros(n_matches, dtype=np.float64)
        fractions[selected_rows] = selected_fractions

        # 4. Ripiego: EV stimato massimo sulla matrice appiattita per righe
        flat_index = int(np.argmax(ev.reshape(-1)))

        return AgentDecision(
            outcomes=outcomes,
            fractions=fractions,
            fallback_match=flat_index // _N_OUTCOMES,
            fallback_outcome=flat_index % _N_OUTCOMES,
        )

    @abc.abstractmethod
    def stake_fractions(
        self, view: DateView, p_hat: np.ndarray, b: np.ndarray
    ) -> np.ndarray:
        """Regola di staking: frazioni di capitale per gli esiti selezionati.

        Parametri
        ---------
        view : DateView
            Vista in sola lettura delle partite della data.
        p_hat : np.ndarray
            Array float64 (k,) non scrivibile delle probabilità stimate degli esiti selezionati.
        b : np.ndarray
            Array float64 (k,) non scrivibile delle quote nette o - 1 degli esiti selezionati.

        Restituisce
        -----------
        np.ndarray
            Array floating (k,) di frazioni finite in [0, 1).
        """


class FractionalKellyAgent(Agent):
    """Agente a Kelly frazionario: frazione = kelly_staking(p_hat, b, lam).

    L'agente A usa lam = AGENT_A_LAMBDA (1.0), gli agenti B i valori di AGENT_B_LAMBDAS
    (0.25 e 0.10). Con lam = 1 e p_hat = 1 la frazione vale 1 e decide solleva ValueError.

    Parametri
    ---------
    name : str
        Nome non vuoto dell'agente.
    lam : float
        Moltiplicatore di Kelly, float o np.floating finito in (0, 1].

    Solleva
    -------
    TypeError
        Se name non è una stringa, o se lam non è float o np.floating (bool e int compresi).
    ValueError
        Se name è vuota, o se lam non è finito o non appartiene a (0, 1].
    """

    def __init__(self, name: str, lam: float) -> None:
        """Inizializza l'agente con nome e moltiplicatore di Kelly.

        Parametri
        ---------
        name : str
            Nome non vuoto dell'agente.
        lam : float
            Moltiplicatore di Kelly in (0, 1].

        Solleva
        -------
        TypeError
            Se name non è una stringa, o se lam non è float o np.floating.
        ValueError
            Se name è vuota, o se lam non è finito o non appartiene a (0, 1].
        """
        super().__init__(name)
        if isinstance(lam, bool) or not isinstance(lam, (float, np.floating)):
            raise TypeError(f"lam must be a float, got {type(lam).__name__}")
        if not math.isfinite(lam) or not 0.0 < lam <= 1.0:
            raise ValueError(f"lam must be finite and in (0, 1], got {lam}")
        self._lam = float(lam)

    @property
    def lam(self) -> float:
        """Moltiplicatore di Kelly dell'agente, in sola lettura."""
        return self._lam

    def stake_fractions(
        self, view: DateView, p_hat: np.ndarray, b: np.ndarray
    ) -> np.ndarray:
        """Calcola le frazioni con kelly_staking, un esito selezionato alla volta.

        kelly_staking accetta b solo scalare (math.isfinite(b)), quindi la chiamata avviene
        elemento per elemento, come in select_baseline_d_bets.

        Parametri
        ---------
        view : DateView
            Vista in sola lettura delle partite della data (non usata dalla regola).
        p_hat : np.ndarray
            Array float64 (k,) delle probabilità stimate degli esiti selezionati.
        b : np.ndarray
            Array float64 (k,) delle quote nette degli esiti selezionati.

        Restituisce
        -----------
        np.ndarray
            Array float64 (k,) delle frazioni lam * max(0, (b * p_hat - (1 - p_hat)) / b).
        """
        n_selected = p_hat.shape[0]
        fractions = np.empty(n_selected, dtype=np.float64)
        for i in range(n_selected):
            fractions[i] = kelly_staking(float(p_hat[i]), float(b[i]), lam=self._lam)
        return fractions


class MinimumStakeAgent(Agent):
    """Agente E: nessuna puntata volontaria, frazioni tutte nulle.

    La puntata minima dell'agente verrà dal ripiego obbligatorio dell'ambiente.

    Parametri
    ---------
    name : str
        Nome non vuoto dell'agente.

    Solleva
    -------
    TypeError
        Se name non è una stringa.
    ValueError
        Se name è la stringa vuota.
    """

    def stake_fractions(
        self, view: DateView, p_hat: np.ndarray, b: np.ndarray
    ) -> np.ndarray:
        """Restituisce frazioni nulle per tutti gli esiti selezionati.

        Parametri
        ---------
        view : DateView
            Vista in sola lettura delle partite della data (non usata dalla regola).
        p_hat : np.ndarray
            Array float64 (k,) delle probabilità stimate degli esiti selezionati.
        b : np.ndarray
            Array float64 (k,) delle quote nette degli esiti selezionati (non usate).

        Restituisce
        -----------
        np.ndarray
            Array float64 (k,) di zeri.
        """
        return np.zeros(p_hat.shape[0], dtype=np.float64)
