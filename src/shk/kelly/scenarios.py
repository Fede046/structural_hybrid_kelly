"""Modulo per la definizione degli scenari di simulazione e composizione del workflow."""

from dataclasses import dataclass
import numpy as np

from shk.kelly.simulate import draw_outcomes, simulate_growth
from shk.kelly.staking import kelly_staking

SEED: int = 20260927


@dataclass(frozen=True)
class Scenario:
    """Parametri immutabili di configurazione per uno scenario di scommessa e simulazione.

    Attributi
    ---------
    name : str
        Nome identificativo dello scenario.
    p : float
        Probabilità reale di vincita, in [0, 1].
    b : float
        Quota decimale netta (b a 1), strettamente positiva (b > 0).
    T : int
        Numero di scommesse per ogni traiettoria (T > 0).
    M : int
        Numero di traiettorie indipendenti (M > 0).
    """

    name: str
    p: float
    b: float
    T: int
    M: int


BASE_SCENARIO = Scenario(name="base", p=0.60, b=1.0, T=1000, M=10000)
SUBTLE_SCENARIO = Scenario(name="subtle", p=0.52, b=1.0, T=380, M=10000)


def spawn_generators(
    seed: int = SEED,
) -> tuple[np.random.Generator, np.random.Generator]:
    """Genera due generatori casuali indipendenti a partire da un unico seed master.

    Utilizza np.random.SeedSequence.spawn(2) per garantire l'indipendenza statistica.
    Il primo generatore è destinato all'estrazione degli esiti (draw_outcomes);
    il secondo è destinato alla generazione del rumore di stima (noisy_estimates).

    Parametri
    ---------
    seed : int, opzionale
        Seed master per la generazione della sequenza (default: SEED = 20260927).

    Restituisce
    -----------
    tuple[np.random.Generator, np.random.Generator]
        Tupla contenente (rng_outcomes, rng_noise).
    """
    ss = np.random.SeedSequence(seed)
    child_seeds = ss.spawn(2)
    return np.random.default_rng(child_seeds[0]), np.random.default_rng(child_seeds[1])


def draw_scenario_outcomes(
    scenario: Scenario, rng: np.random.Generator
) -> np.ndarray:
    """Estrae la matrice degli esiti bernoulliani per i parametri dello scenario specificato.

    Parametri
    ---------
    scenario : Scenario
        Scenario di configurazione contenente p, T e M.
    rng : np.random.Generator
        Generatore di numeri casuali di NumPy.

    Restituisce
    -----------
    np.ndarray
        Matrice booleana di shape (M, T) dove True rappresenta una vincita.
    """
    return draw_outcomes(scenario.p, scenario.T, scenario.M, rng)


def simulate_scenario(
    scenario: Scenario,
    outcomes: np.ndarray,
    p_hat: float | np.ndarray,
    lam: float = 1.0,
) -> np.ndarray:
    """Esegue la simulazione del log-wealth calcolando le frazioni da p_hat e delegando al motore.

    Calcola le frazioni di puntata tramite kelly_staking(p_hat, scenario.b, lam)
    e simula le traiettorie temporali con simulate_growth(outcomes, fractions, scenario.b).
    Non riceve generatori e non modifica in alcun modo la matrice outcomes ricevuta in ingresso.

    Parametri
    ---------
    scenario : Scenario
        Scenario di configurazione contenente b.
    outcomes : np.ndarray
        Matrice booleana di shape (M, T) contenente gli esiti (True = vincita).
    p_hat : float | np.ndarray
        Stima di probabilità (scalare o array broadcastabile a (M, T)).
    lam : float, opzionale
        Moltiplicatore di Kelly (default: 1.0).

    Restituisce
    -----------
    np.ndarray
        Array float64 di shape (M, T + 1) con il log-wealth per ciascuna traiettoria.
    """
    fractions = kelly_staking(p_hat, scenario.b, lam=lam)
    return simulate_growth(outcomes, fractions, scenario.b)
