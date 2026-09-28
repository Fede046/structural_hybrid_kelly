"""Calibrazione generica della soglia per moving block bootstrap.

Questo modulo fornisce funzioni generiche e indipendenti dal modello per calibrare
la soglia critica di una statistica test mediante moving block bootstrap (Künsch, 1989),
preservando la dipendenza seriale presente nei dati di serie storiche.

Il moving block bootstrap ricampiona blocchi consecutivi di lunghezza L da una serie
temporale di lunghezza n (avente il tempo sull'asse 0). Ciascun ricampionamento concatena
ceil(n / L) blocchi con inizio estratto uniformemente fra 0 e n - L, e viene troncato
a n osservazioni. La soglia calibrata al livello alpha è definita come la statistica d'ordine
ceil((1 - alpha) * (B + 1)) calcolata sulle B replicazioni bootstrap.

(a) Rimedio unico all'autocorrelazione:
La calibrazione della soglia mediante moving block bootstrap costituisce il rimedio
unificato per correggere la distorsione indotta dall'autocorrelazione sulle decisioni
inferenziali. L'applicazione copre quattro strumenti metodologici principali del progetto
(schema indicativo, da confermare nelle story C5.2, C6.4 e C8):
1. ANOVA F:
   - Dato: la serie della risposta, con il tempo sull'asse 0;
   - Statistica: statistica F con etichette di gruppo fisse, allineate al tempo originale.
2. FWER dello Z-test per giornata (C5.2):
   - Dato: la serie dei residui in ordine temporale;
   - Statistica: il massimo su tutte le giornate di |Z|, con l'assegnazione alle giornate fissa.
3. Difference-in-Differences (DiD):
   - Dato: la serie della differenza fra trattati e controlli;
   - Statistica: la differenza fra la media post e la media pre, con la data di separazione fissa.
4. Test di Breusch-Pagan (C6.4):
   - Dato: la serie dei residui OLS;
   - Statistica: moltiplicatore di Lagrange LM = n * R^2 della regressione ausiliaria
     dei residui al quadrato sui regressori, tenuti fissi e non ricampionati.

(b) Dipendenza dalla lunghezza dei blocchi L:
La soglia calibrata, e quindi il tasso di falso rigetto che ne risulta, dipende dalla lunghezza dei blocchi L. La dipendenza misurata sulle serie AR(1) dell'esperimento C2 è riportata nelle righe con method = block_bootstrap di results/us_c2_anova_autocorrelation.csv.

(c) Imposizione dell'ipotesi nulla H0:
La funzione di calibrazione opera come algoritmo generale di ricampionamento e non altera
né trasforma i dati in ingresso: imporre l'ipotesi nulla H0 nei dati passati (per esempio
centrando la serie attorno alla media teorica, sottraendo l'effetto stimato o calcolando
i residui vincolati sotto H0) spetta esclusivamente al chiamante prima dell'invocazione.
"""

from collections.abc import Callable
import math
from typing import Any
import numpy as np


def moving_block_indices(
    n: int,
    block_length: int,
    n_boot: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Genera la matrice di indici temporali ricampionati per moving block bootstrap.

    Ricampiona blocchi consecutivi di lunghezza block_length da una sequenza di lunghezza n.
    Ciascun ricampionamento concatena ceil(n / block_length) blocchi estratti con inizio
    uniforme in [0, n - block_length], e viene troncato a n osservazioni.
    L'estrazione avviene in modo interamente vettorizzato senza cicli Python su n_boot.

    Parametri
    ---------
    n : int
        Lunghezza temporale della serie originale (n >= 1).
    block_length : int
        Lunghezza del blocco consecutivo (1 <= block_length <= n).
    n_boot : int
        Numero di replicazioni bootstrap da generare (n_boot >= 1).
    rng : np.random.Generator
        Generatore di numeri casuali NumPy.

    Restituisce
    -----------
    np.ndarray
        Array NumPy int64 di forma (n_boot, n) contenente gli indici ricampionati.

    Solleva
    -------
    TypeError
        Se n, block_length o n_boot sono di tipo booleano o non sono interi (int o np.integer),
        oppure se rng non è un'istanza di np.random.Generator.
    ValueError
        Se n < 1, se non è soddisfatto 1 <= block_length <= n, o se n_boot < 1.
    """
    if isinstance(n, bool) or not isinstance(n, (int, np.integer)):
        raise TypeError(f"n must be an integer, got {type(n).__name__}")
    if isinstance(block_length, bool) or not isinstance(block_length, (int, np.integer)):
        raise TypeError(f"block_length must be an integer, got {type(block_length).__name__}")
    if isinstance(n_boot, bool) or not isinstance(n_boot, (int, np.integer)):
        raise TypeError(f"n_boot must be an integer, got {type(n_boot).__name__}")
    if not isinstance(rng, np.random.Generator):
        raise TypeError(f"rng must be an instance of np.random.Generator, got {type(rng)}")

    n_val = int(n)
    l_val = int(block_length)
    b_val = int(n_boot)

    if n_val < 1:
        raise ValueError(f"n must be at least 1, got {n_val}")
    if not (1 <= l_val <= n_val):
        raise ValueError(f"block_length must satisfy 1 <= block_length <= n ({n_val}), got {l_val}")
    if b_val < 1:
        raise ValueError(f"n_boot must be strictly positive (n_boot >= 1), got {b_val}")

    k_blocks = math.ceil(n_val / l_val)

    # Estrazione vettorizzata delle posizioni di inizio dei blocchi
    # Intervallo consentito: [0, n - block_length], estremo high esclusivo in rng.integers
    start_indices = rng.integers(
        low=0, high=n_val - l_val + 1, size=(b_val, k_blocks), dtype=np.int64
    )

    # Offset consecutivi entro ciascun blocco: forma (L,)
    offsets = np.arange(l_val, dtype=np.int64)

    # Broadcasting: (B, K, 1) + (1, 1, L) -> (B, K, L)
    block_indices = start_indices[:, :, None] + offsets[None, None, :]

    # Linearizzazione lungo le dimensioni dei blocchi e troncamento a n elementi
    indices = block_indices.reshape(b_val, k_blocks * l_val)[:, :n_val]

    return indices


def compute_order_statistic_index(
    b: int,
    alpha: float,
) -> int:
    """Calcola l'indice 1-based della statistica d'ordine ceil((1 - alpha) * (b + 1)).

    Include un assorbimento delle imprecisioni di arrotondamento floating-point attorno
    agli interi (tolleranza 1e-9).

    Parametri
    ---------
    b : int
        Numero di replicazioni bootstrap (b >= 1).
    alpha : float
        Livello di significatività nominale (0 < alpha < 1).

    Restituisce
    -----------
    int
        Indice 1-based della statistica d'ordine desiderata.

    Solleva
    -------
    TypeError
        Se b non è un intero o se alpha non è un float.
    ValueError
        Se b < 1, se not (0 < alpha < 1), o se l'indice calcolato k supera b.
    """
    if isinstance(b, bool) or not isinstance(b, (int, np.integer)):
        raise TypeError(f"b must be an integer, got {type(b).__name__}")
    if isinstance(alpha, bool) or not isinstance(alpha, (float, np.floating)):
        raise TypeError(f"alpha must be a float, got {type(alpha).__name__}")

    b_val = int(b)
    alpha_val = float(alpha)

    if b_val < 1:
        raise ValueError(f"b must be at least 1, got {b_val}")
    if not (0.0 < alpha_val < 1.0):
        raise ValueError(f"alpha must be strictly between 0 and 1, got {alpha_val}")

    val = (1.0 - alpha_val) * (b_val + 1)
    nearest_int = round(val)
    if abs(val - nearest_int) < 1e-9:
        k = nearest_int
    else:
        k = math.ceil(val)

    if k > b_val:
        raise ValueError(
            f"Order statistic index ({k}) exceeds number of bootstrap resamples B ({b_val}) for alpha={alpha_val}"
        )

    return int(k)


def calibrate_threshold(
    data: np.ndarray,
    statistic: Callable[..., Any],
    block_length: int,
    n_boot: int,
    alpha: float,
    rng: np.random.Generator,
    vectorized: bool = False,
) -> float:
    """Calcola la soglia calibrata al livello alpha per moving block bootstrap.

    Parametri
    ---------
    data : np.ndarray
        Array NumPy di forma (n, ...) avente la dimensione temporale sull'asse 0.
        Deve avere valori numerici reali finiti e almeno 1 dimensione.
    statistic : Callable
        Funzione statistica da valutare sui ricampionamenti.
        Se vectorized è False, riceve un singolo ricampionamento di forma identica a data
        e restituisce un valore scalare float.
        Se vectorized è True, riceve l'array completo dei ricampionamenti di forma
        (n_boot, *data.shape) e restituisce un array 1D di forma (n_boot,).
    block_length : int
        Lunghezza del blocco temporale (1 <= block_length <= n).
    n_boot : int
        Numero di replicazioni bootstrap (n_boot >= 1).
    alpha : float
        Livello di significatività nominale (0 < alpha < 1).
    rng : np.random.Generator
        Generatore di numeri casuali NumPy.
    vectorized : bool, opzionale
        Flag che indica se la funzione statistica supporta l'input multidimensionale
        (default: False).

    Restituisce
    -----------
    float
        Soglia critica calibrata (statistica d'ordine ceil((1 - alpha) * (n_boot + 1))).

    Solleva
    -------
    TypeError
        Se data non è np.ndarray con dtype numerico reale, se block_length o n_boot non sono
        interi, se alpha non è float, se statistic non è callable, se rng non è
        np.random.Generator, o se vectorized non è un bool.
    ValueError
        Se data ha 0 dimensioni, se data contiene valori non finiti, se block_length
        non è compreso tra 1 e n, se n_boot < 1, se alpha non è in (0, 1),
        se l'indice della statistica d'ordine supera n_boot, se la statistica produce un output
        di forma diversa da (n_boot,), o se le statistiche calcolate non sono finite.
    """
    if not isinstance(data, np.ndarray):
        raise TypeError(f"data must be an instance of np.ndarray, got {type(data)}")
    if not np.issubdtype(data.dtype, np.number) or np.issubdtype(data.dtype, np.complexfloating):
        raise TypeError(f"data must have real numeric dtype, got {data.dtype}")
    if data.ndim < 1:
        raise ValueError(f"data must have at least 1 dimension, got {data.ndim}D")
    if not np.all(np.isfinite(data)):
        raise ValueError("All elements of data must be finite (no NaN or Inf allowed)")

    if isinstance(block_length, bool) or not isinstance(block_length, (int, np.integer)):
        raise TypeError(f"block_length must be an integer, got {type(block_length).__name__}")
    if isinstance(n_boot, bool) or not isinstance(n_boot, (int, np.integer)):
        raise TypeError(f"n_boot must be an integer, got {type(n_boot).__name__}")
    if isinstance(alpha, bool) or not isinstance(alpha, (float, np.floating)):
        raise TypeError(f"alpha must be a float, got {type(alpha).__name__}")
    if not callable(statistic):
        raise TypeError(f"statistic must be callable, got {type(statistic).__name__}")
    if not isinstance(rng, np.random.Generator):
        raise TypeError(f"rng must be an instance of np.random.Generator, got {type(rng)}")
    if not isinstance(vectorized, bool):
        raise TypeError(f"vectorized must be a bool, got {type(vectorized).__name__}")

    n_obs = data.shape[0]
    l_val = int(block_length)
    b_val = int(n_boot)
    alpha_val = float(alpha)

    if not (1 <= l_val <= n_obs):
        raise ValueError(f"block_length must satisfy 1 <= block_length <= n ({n_obs}), got {l_val}")
    if b_val < 1:
        raise ValueError(f"n_boot must be at least 1, got {b_val}")
    if not (0.0 < alpha_val < 1.0):
        raise ValueError(f"alpha must be strictly between 0 and 1, got {alpha_val}")

    # Calcolo dell'indice della statistica d'ordine (solleva ValueError se k > B)
    k_order = compute_order_statistic_index(b_val, alpha_val)

    # Estrazione degli indici di ricampionamento (B, n)
    indices = moving_block_indices(n_obs, l_val, b_val, rng)

    # Valutazione della statistica
    if vectorized:
        # data ha il tempo sull'asse 0: data[indices] ha forma (B, *data.shape)
        boot_data = data[indices]
        raw_stats = statistic(boot_data)
    else:
        raw_stats = [statistic(data[indices[b]]) for b in range(b_val)]

    # Conversione e validazione rigorosa della forma (b_val,) in entrambi i casi
    boot_arr = np.asarray(raw_stats)
    if not np.issubdtype(boot_arr.dtype, np.number) or np.issubdtype(boot_arr.dtype, np.complexfloating):
        raise ValueError(f"statistic output must have real numeric values, got {boot_arr.dtype}")

    if boot_arr.shape != (b_val,):
        raise ValueError(
            f"statistic output must have 1D shape ({b_val},), got shape {boot_arr.shape}"
        )

    boot_stats = boot_arr.astype(np.float64)
    if not np.all(np.isfinite(boot_stats)):
        raise ValueError("statistic output contains non-finite values (NaN or Inf)")

    sorted_stats = np.sort(boot_stats)
    threshold = float(sorted_stats[k_order - 1])

    return threshold
