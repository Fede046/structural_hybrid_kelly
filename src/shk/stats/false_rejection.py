"""Modulo per l'analisi del tasso di falso rigetto dell'ANOVA su serie temporali autoregressive.

Tre metodi per la soglia della F sul disegno contiguous_2:
- nominal: quantile 1 - alpha della F(k - 1, N - k);
- block_bootstrap: moving block bootstrap della serie grezza, senza imporre H0;
- block_bootstrap_centered: moving block bootstrap della serie centrata per gruppo,
  cioè con H0 di medie uguali imposta prima del ricampionamento.
"""

from dataclasses import dataclass
import math
from typing import NamedTuple
import numpy as np
import scipy.stats

from shk.stats.anova import oneway_anova_vectorized
from shk.stats.calibration import calibrate_threshold
from shk.stats.timeseries import generate_ar1_series

PHI_VALUES: tuple[float, ...] = (0.0, 0.3, 0.5, 0.7)
N_OBS: int = 380
N_SERIES: int = 1000
ALPHA: float = 0.05
SEED_C2: int = 20260928

BLOCK_LENGTHS: tuple[int, ...] = (7, 20, 40)
N_BOOT: int = 999

METHOD_NOMINAL: str = "nominal"
METHOD_BLOCK_BOOTSTRAP: str = "block_bootstrap"
METHOD_BLOCK_BOOTSTRAP_CENTERED: str = "block_bootstrap_centered"

# Seed radice delle infrastrutture statistiche (decisione di progetto): la procedura in posizione i
# usa SeedSequence(SEED_S7).spawn(N_STORY_TASKS)[i]; la calibrazione centrata è in posizione 0.
SEED_S7: int = 20261011
N_STORY_TASKS: int = 5
T40_STORY_POSITION: int = 0

DESIGN_CONTIGUOUS_2: str = "contiguous_2"
DESIGN_CONTIGUOUS_38: str = "contiguous_38"
DESIGN_RANDOM_2: str = "random_2"
DESIGNS: tuple[str, ...] = (
    DESIGN_CONTIGUOUS_2,
    DESIGN_CONTIGUOUS_38,
    DESIGN_RANDOM_2,
)

CSV_COLUMNS: tuple[str, ...] = (
    "design",
    "phi",
    "method",
    "block_length",
    "n_series",
    "rejections",
    "rejection_rate",
    "critical_value_mean",
    "mc_lower_99",
    "mc_upper_99",
)


class PhiStreams(NamedTuple):
    """Flussi di numeri casuali indipendenti per un valore di phi.

    Attributi
    ---------
    series_rng : np.random.Generator
        Generatore per le serie stocastiche AR(1).
    perm_rng : np.random.Generator
        Generatore per le permutazioni casuali del disegno random_2.
    boot_seed : np.random.SeedSequence
        Sequenza di semi per il bootstrap, divisa con spawn(len(BLOCK_LENGTHS))
        da compute_calibrated_rejection_rates, con un generatore per ciascun L.
    """

    series_rng: np.random.Generator
    perm_rng: np.random.Generator
    boot_seed: np.random.SeedSequence


@dataclass(frozen=True)
class RejectionResult:
    """Risultato immutabile della simulazione del falso rigetto per una coppia (disegno, phi).

    Attributi
    ---------
    design : str
        Nome del disegno sperimentale ("contiguous_2", "contiguous_38", "random_2").
    phi : float
        Coefficiente autoregressivo della serie.
    method : str
        Metodo di calcolo della soglia ("nominal", "block_bootstrap" oppure
        "block_bootstrap_centered").
    block_length : str
        Lunghezza del blocco di bootstrap ("" per il metodo nominale, lunghezza dei blocchi
        come stringa per i due metodi bootstrap).
    n_series : int
        Numero totale di serie simulate.
    rejections : int
        Numero di serie per cui la statistica supera il valore critico.
    rejection_rate : float
        Quota empirica di rigetti (rejections / n_series).
    critical_value_mean : float
        Valore critico nominale per "nominal" e media delle soglie calibrate serie
        per serie per i due metodi bootstrap.
    mc_lower_99 : float
        Estremo inferiore dell'intervallo Monte Carlo al 99% attorno ad ALPHA.
    mc_upper_99 : float
        Estremo superiore dell'intervallo Monte Carlo al 99% attorno ad ALPHA.
    """

    design: str
    phi: float
    method: str
    block_length: str
    n_series: int
    rejections: int
    rejection_rate: float
    critical_value_mean: float
    mc_lower_99: float
    mc_upper_99: float

    def to_row(self) -> dict[str, str | int | float]:
        """Converte il record nel formato dizionario per la scrittura CSV."""
        return {
            "design": self.design,
            "phi": self.phi,
            "method": self.method,
            "block_length": self.block_length,
            "n_series": self.n_series,
            "rejections": self.rejections,
            "rejection_rate": self.rejection_rate,
            "critical_value_mean": self.critical_value_mean,
            "mc_lower_99": self.mc_lower_99,
            "mc_upper_99": self.mc_upper_99,
        }


def critical_value_nominal(k: int, n_obs: int = N_OBS, alpha: float = ALPHA) -> float:
    """Calcola il valore critico nominale per la distribuzione F(k - 1, n_obs - k).

    Parametri
    ---------
    k : int
        Numero di gruppi (k >= 2).
    n_obs : int, opzionale
        Numero di osservazioni totali (default: N_OBS = 380).
    alpha : float, opzionale
        Livello di significatività nominale (default: ALPHA = 0.05).

    Restituisce
    -----------
    float
        Quantile 1 - alpha della distribuzione F(k - 1, n_obs - k).

    Solleva
    -------
    TypeError
        Se k o n_obs non sono interi, o se alpha non è un float.
    ValueError
        Se k < 2, se n_obs <= k, o se non è soddisfatto 0 < alpha < 1.
    """
    if isinstance(k, bool) or not isinstance(k, (int, np.integer)):
        raise TypeError(f"k must be an integer, got {type(k).__name__}")
    if isinstance(n_obs, bool) or not isinstance(n_obs, (int, np.integer)):
        raise TypeError(f"n_obs must be an integer, got {type(n_obs).__name__}")
    if isinstance(alpha, bool) or not isinstance(alpha, (float, np.floating)):
        raise TypeError(f"alpha must be a float, got {type(alpha).__name__}")
    if k < 2:
        raise ValueError(f"k must be at least 2, got {k}")
    if n_obs <= k:
        raise ValueError(f"n_obs must be strictly greater than k ({k}), got {n_obs}")
    if not (0.0 < alpha < 1.0):
        raise ValueError(f"alpha must be strictly between 0 and 1, got {alpha}")

    return float(scipy.stats.f.ppf(1.0 - alpha, dfn=k - 1, dfd=n_obs - k))


def monte_carlo_interval_99(
    alpha: float = ALPHA, n_series: int = N_SERIES
) -> tuple[float, float]:
    """Calcola l'intervallo di confidenza Monte Carlo al 99% attorno al livello nominale alpha.

    L'intervallo simmetrico al 99% (z = 2.576) per una proporzione binomiale è:
        alpha +- 2.576 * sqrt(alpha * (1 - alpha) / n_series)

    Parametri
    ---------
    alpha : float, opzionale
        Livello di significatività nominale (default: ALPHA = 0.05).
    n_series : int, opzionale
        Numero di serie simulate (default: N_SERIES = 1000).

    Restituisce
    -----------
    tuple[float, float]
        Tupla (limite_inferiore, limite_superiore).

    Solleva
    -------
    TypeError
        Se alpha non è float o n_series non è intero.
    ValueError
        Se alpha non è in (0, 1) o n_series < 1.
    """
    if isinstance(alpha, bool) or not isinstance(alpha, (float, np.floating)):
        raise TypeError(f"alpha must be a float, got {type(alpha).__name__}")
    if isinstance(n_series, bool) or not isinstance(n_series, (int, np.integer)):
        raise TypeError(f"n_series must be an integer, got {type(n_series).__name__}")
    if not (0.0 < alpha < 1.0):
        raise ValueError(f"alpha must be strictly between 0 and 1, got {alpha}")
    if n_series < 1:
        raise ValueError(f"n_series must be strictly positive, got {n_series}")

    half_width = 2.576 * math.sqrt(alpha * (1.0 - alpha) / float(n_series))
    return float(alpha - half_width), float(alpha + half_width)


def make_design_labels(design: str, n_obs: int = N_OBS) -> np.ndarray:
    """Costruisce il vettore 1D di etichette per il disegno sperimentale specificato.

    Per contiguous_2 (k = 2): assegna l'osservazione t al gruppo floor(t * 2 / n_obs).
    Per contiguous_38 (k = 38): assegna l'osservazione t al gruppo floor(t * 38 / n_obs).
    Per random_2: restituisce le stesse etichette di contiguous_2, destinate ad essere
    applicate alla serie permutata casualmente.

    Parametri
    ---------
    design : str
        Nome del disegno ("contiguous_2", "contiguous_38", "random_2").
    n_obs : int, opzionale
        Numero di osservazioni totali (default: N_OBS = 380).

    Restituisce
    -----------
    np.ndarray
        Array 1D di int64 di lunghezza n_obs con etichette 0..k-1.

    Solleva
    -------
    TypeError
        Se design non è una stringa o n_obs non è un intero.
    ValueError
        Se design non appartiene a DESIGNS o se n_obs < 2.
    """
    if not isinstance(design, str):
        raise TypeError(f"design must be a string, got {type(design).__name__}")
    if isinstance(n_obs, bool) or not isinstance(n_obs, (int, np.integer)):
        raise TypeError(f"n_obs must be an integer, got {type(n_obs).__name__}")
    if n_obs < 2:
        raise ValueError(f"n_obs must be at least 2, got {n_obs}")

    if design == DESIGN_CONTIGUOUS_2:
        return (np.arange(n_obs, dtype=np.int64) * 2) // n_obs
    elif design == DESIGN_CONTIGUOUS_38:
        return (np.arange(n_obs, dtype=np.int64) * 38) // n_obs
    elif design == DESIGN_RANDOM_2:
        return (np.arange(n_obs, dtype=np.int64) * 2) // n_obs
    else:
        raise ValueError(f"Unknown design '{design}', must be one of {DESIGNS}")


def spawn_c2_generators(
    seed: int = SEED_C2,
) -> tuple[PhiStreams, ...]:
    """Costruisce i flussi di numeri casuali indipendenti per ciascun phi in PHI_VALUES.

    Utilizza SeedSequence(seed).spawn(len(PHI_VALUES)) per ottenere un seme figlio
    per ciascun phi nell'ordine di PHI_VALUES; ciascun seme figlio viene a sua volta
    suddiviso con spawn(3) in tre flussi ordinati:
    1. series_rng: generatore per la matrice di serie AR(1);
    2. perm_rng: generatore per le permutazioni delle serie in random_2;
    3. boot_seed: SeedSequence per il bootstrap, divisa con spawn(len(BLOCK_LENGTHS))
       da compute_calibrated_rejection_rates, con un generatore per ciascun L.

    Parametri
    ---------
    seed : int, opzionale
        Seed master per la simulazione (default: SEED_C2 = 20260928).

    Restituisce
    -----------
    tuple[PhiStreams, ...]
        Tupla ordinata come PHI_VALUES, dove l'elemento i corrisponde a PHI_VALUES[i].

    Solleva
    -------
    TypeError
        Se seed non è un intero valido.
    """
    if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)):
        raise TypeError(f"seed must be an integer, got {type(seed).__name__}")

    ss = np.random.SeedSequence(seed)
    phi_seeds = ss.spawn(len(PHI_VALUES))

    streams_list: list[PhiStreams] = []
    for phi_ss in phi_seeds:
        child_seeds = phi_ss.spawn(3)
        rng_series = np.random.default_rng(child_seeds[0])
        rng_perm = np.random.default_rng(child_seeds[1])
        boot_seed = child_seeds[2]
        streams_list.append(
            PhiStreams(
                series_rng=rng_series,
                perm_rng=rng_perm,
                boot_seed=boot_seed,
            )
        )

    return tuple(streams_list)


def compute_nominal_rejection_rates(
    seed: int = SEED_C2,
) -> list[RejectionResult]:
    """Calcola il tasso di falso rigetto nominale dell'ANOVA sui tre disegni e quattro phi.

    Per ciascun phi in PHI_VALUES:
    1. Genera una sola matrice di serie AR(1) di forma (N_SERIES, N_OBS) dal flusso series_rng;
    2. Valuta il disegno contiguous_2 con le etichette di due blocchi contigui;
    3. Valuta il disegno contiguous_38 con le etichette di 38 blocchi contigui;
    4. Valuta il disegno random_2 permutando ciascuna serie con una permutazione casuale
       estratta in sequenza da perm_rng (i = 0 ... N_SERIES - 1), applicando poi le etichette
       di contiguous_2.

    Restituisce i record ordinati prima per disegno (nell'ordine di DESIGNS)
    e poi per phi crescente.

    Parametri
    ---------
    seed : int, opzionale
        Seed master della sequenza (default: SEED_C2 = 20260928).

    Restituisce
    -----------
    list[RejectionResult]
        Lista di 12 record RejectionResult.
    """
    mc_lower, mc_upper = monte_carlo_interval_99(ALPHA, N_SERIES)
    cv_k2 = critical_value_nominal(k=2, n_obs=N_OBS, alpha=ALPHA)
    cv_k38 = critical_value_nominal(k=38, n_obs=N_OBS, alpha=ALPHA)

    labels_cont2 = make_design_labels(DESIGN_CONTIGUOUS_2, N_OBS)
    labels_cont38 = make_design_labels(DESIGN_CONTIGUOUS_38, N_OBS)

    streams = spawn_c2_generators(seed=seed)

    results_map: dict[tuple[str, float], RejectionResult] = {}

    for phi, phi_stream in zip(PHI_VALUES, streams):
        # 1. Generazione di UNA SOLA matrice di serie per questo phi
        series = generate_ar1_series(
            phi=phi, n=N_OBS, m=N_SERIES, rng=phi_stream.series_rng
        )

        # 2. contiguous_2 (k = 2)
        f_cont2 = oneway_anova_vectorized(series, labels_cont2)
        rejections_cont2 = int(np.sum(f_cont2 > cv_k2))
        results_map[(DESIGN_CONTIGUOUS_2, phi)] = RejectionResult(
            design=DESIGN_CONTIGUOUS_2,
            phi=phi,
            method="nominal",
            block_length="",
            n_series=N_SERIES,
            rejections=rejections_cont2,
            rejection_rate=float(rejections_cont2 / N_SERIES),
            critical_value_mean=cv_k2,
            mc_lower_99=mc_lower,
            mc_upper_99=mc_upper,
        )

        # 3. contiguous_38 (k = 38)
        f_cont38 = oneway_anova_vectorized(series, labels_cont38)
        rejections_cont38 = int(np.sum(f_cont38 > cv_k38))
        results_map[(DESIGN_CONTIGUOUS_38, phi)] = RejectionResult(
            design=DESIGN_CONTIGUOUS_38,
            phi=phi,
            method="nominal",
            block_length="",
            n_series=N_SERIES,
            rejections=rejections_cont38,
            rejection_rate=float(rejections_cont38 / N_SERIES),
            critical_value_mean=cv_k38,
            mc_lower_99=mc_lower,
            mc_upper_99=mc_upper,
        )

        # 4. random_2: permutazione sequenziale per ciascuna serie da perm_rng
        perm_matrix = np.empty((N_SERIES, N_OBS), dtype=np.int64)
        for i in range(N_SERIES):
            perm_matrix[i] = phi_stream.perm_rng.permutation(N_OBS)
        series_perm = np.take_along_axis(series, perm_matrix, axis=1)

        f_rand2 = oneway_anova_vectorized(series_perm, labels_cont2)
        rejections_rand2 = int(np.sum(f_rand2 > cv_k2))
        results_map[(DESIGN_RANDOM_2, phi)] = RejectionResult(
            design=DESIGN_RANDOM_2,
            phi=phi,
            method="nominal",
            block_length="",
            n_series=N_SERIES,
            rejections=rejections_rand2,
            rejection_rate=float(rejections_rand2 / N_SERIES),
            critical_value_mean=cv_k2,
            mc_lower_99=mc_lower,
            mc_upper_99=mc_upper,
        )

    ordered_results: list[RejectionResult] = []
    for d in DESIGNS:
        for phi in PHI_VALUES:
            ordered_results.append(results_map[(d, phi)])

    return ordered_results


def compute_calibrated_rejection_rates(
    seed: int = SEED_C2,
) -> list[RejectionResult]:
    """Calcola il tasso di falso rigetto calibrato per moving block bootstrap su contiguous_2.

    Per ciascun phi in PHI_VALUES:
    1. Genera una sola matrice di serie AR(1) di forma (N_SERIES, N_OBS) dal flusso series_rng;
       le serie generate sono le stesse di compute_nominal_rejection_rates, perché derivano
       dallo stesso series_rng generato dallo stesso seed.
    2. Valuta la statistica F osservata per ciascuna serie con il disegno contiguous_2.
    3. Suddivide il flusso boot_seed con spawn(len(BLOCK_LENGTHS)), ottenendo un generatore
       indipendente per ciascuna lunghezza di blocco L in BLOCK_LENGTHS.
    4. Per ciascun L, calcola la soglia calibrata serie per serie tramite calibrate_threshold,
       utilizzando il generatore in sequenza sulle N_SERIES serie con vectorized=True.
    5. Rigetta l'ipotesi nulla per le serie in cui la F osservata supera la soglia calibrata
       della rispettiva serie.

    Restituisce i record RejectionResult ordinati per L nell'ordine di BLOCK_LENGTHS e,
    all'interno di ciascun L, per phi nell'ordine di PHI_VALUES.

    Parametri
    ---------
    seed : int, opzionale
        Seed master per la simulazione (default: SEED_C2 = 20260928).

    Restituisce
    -----------
    list[RejectionResult]
        Lista di 12 record RejectionResult per le combinazioni di BLOCK_LENGTHS e PHI_VALUES.

    Solleva
    -------
    TypeError
        Se seed non è un intero valido.
    """
    if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)):
        raise TypeError(f"seed must be an integer, got {type(seed).__name__}")

    mc_lower, mc_upper = monte_carlo_interval_99(ALPHA, N_SERIES)
    labels_cont2 = make_design_labels(DESIGN_CONTIGUOUS_2, N_OBS)

    def stat_contiguous_2(b_data: np.ndarray) -> np.ndarray:
        return oneway_anova_vectorized(b_data, labels_cont2)

    streams = spawn_c2_generators(seed=seed)

    results_map: dict[tuple[int, float], RejectionResult] = {}

    for phi, phi_stream in zip(PHI_VALUES, streams):
        # 1. Generazione di UNA SOLA matrice di serie per questo phi
        series = generate_ar1_series(
            phi=phi, n=N_OBS, m=N_SERIES, rng=phi_stream.series_rng
        )
        f_obs = oneway_anova_vectorized(series, labels_cont2)

        # 2. Divisione del flusso bootstrap per le lunghezze di blocco
        boot_seeds = phi_stream.boot_seed.spawn(len(BLOCK_LENGTHS))

        for l_val, b_seed in zip(BLOCK_LENGTHS, boot_seeds):
            rng_l = np.random.default_rng(b_seed)
            thresholds = np.empty(N_SERIES, dtype=np.float64)

            for s in range(N_SERIES):
                thresholds[s] = calibrate_threshold(
                    data=series[s],
                    statistic=stat_contiguous_2,
                    block_length=l_val,
                    n_boot=N_BOOT,
                    alpha=ALPHA,
                    rng=rng_l,
                    vectorized=True,
                )

            rejections = int(np.sum(f_obs > thresholds))
            rejection_rate = float(rejections / N_SERIES)
            critical_value_mean = float(np.mean(thresholds))

            results_map[(l_val, phi)] = RejectionResult(
                design=DESIGN_CONTIGUOUS_2,
                phi=phi,
                method=METHOD_BLOCK_BOOTSTRAP,
                block_length=str(l_val),
                n_series=N_SERIES,
                rejections=rejections,
                rejection_rate=rejection_rate,
                critical_value_mean=critical_value_mean,
                mc_lower_99=mc_lower,
                mc_upper_99=mc_upper,
            )

    ordered_results: list[RejectionResult] = []
    for l_val in BLOCK_LENGTHS:
        for phi in PHI_VALUES:
            ordered_results.append(results_map[(l_val, phi)])

    return ordered_results


class CenteredCalibrationDetail(NamedTuple):
    """F osservate e soglie calibrate del metodo centrato per una coppia (phi, L).

    Attributi
    ---------
    phi : float
        Coefficiente autoregressivo delle serie.
    block_length : int
        Lunghezza dei blocchi del moving block bootstrap.
    f_observed : np.ndarray
        F osservata sulla serie originale, forma (N_SERIES,).
    thresholds : np.ndarray
        Soglia calibrata sulla serie centrata per gruppo, forma (N_SERIES,).
    """

    phi: float
    block_length: int
    f_observed: np.ndarray
    thresholds: np.ndarray


def center_by_group(series: np.ndarray, labels: np.ndarray) -> np.ndarray:
    """Sottrae a ciascuna osservazione la media del suo gruppo, imponendo H0 di medie uguali.

    Dopo il centramento ogni gruppo ha media nulla, a meno dell'arrotondamento, e la
    statistica F della serie centrata vale zero. Il tempo sta sull'ultimo asse, così la
    funzione accetta sia una serie (n,) sia una matrice di serie (m, n).

    Parametri
    ---------
    series : np.ndarray
        Serie con dtype reale e valori finiti, forma (..., n) con almeno 1 dimensione.
    labels : np.ndarray
        Etichette intere di gruppo di forma (n,), con valori 0..k-1 tutti presenti.

    Restituisce
    -----------
    np.ndarray
        Serie centrata float64 della stessa forma di series.

    Solleva
    -------
    TypeError
        Se series non è np.ndarray con dtype reale, o se labels non è np.ndarray intero.
    ValueError
        Se series ha 0 dimensioni o valori non finiti, se labels non è 1D di lunghezza n,
        se contiene valori negativi o se un gruppo fra 0 e k-1 è vuoto.
    """
    if not isinstance(series, np.ndarray):
        raise TypeError(f"series must be an instance of np.ndarray, got {type(series)}")
    if (
        not np.issubdtype(series.dtype, np.number)
        or np.issubdtype(series.dtype, np.complexfloating)
        or np.issubdtype(series.dtype, np.bool_)
    ):
        raise TypeError(f"series must have real numeric dtype, got {series.dtype}")
    if not isinstance(labels, np.ndarray):
        raise TypeError(f"labels must be an instance of np.ndarray, got {type(labels)}")
    if not np.issubdtype(labels.dtype, np.integer) or np.issubdtype(labels.dtype, np.bool_):
        raise TypeError(f"labels must have integer dtype, got {labels.dtype}")
    if series.ndim < 1:
        raise ValueError(f"series must have at least 1 dimension, got {series.ndim}D")
    if not np.all(np.isfinite(series)):
        raise ValueError("All elements of series must be finite (no NaN or Inf allowed)")
    n_obs = series.shape[-1]
    if labels.ndim != 1 or labels.shape[0] != n_obs:
        raise ValueError(
            f"labels must be 1D with length {n_obs}, got shape {labels.shape}"
        )
    if n_obs == 0:
        raise ValueError("series must have at least one observation")
    if np.any(labels < 0):
        raise ValueError("labels must be non-negative")

    counts = np.bincount(labels)
    if np.any(counts == 0):
        raise ValueError("Every group label between 0 and k-1 must be present")

    values = series.astype(np.float64)
    # Indicatrici di gruppo (n, k): le somme di gruppo sono un prodotto matriciale
    indicators = np.zeros((n_obs, counts.shape[0]), dtype=np.float64)
    indicators[np.arange(n_obs), labels] = 1.0
    group_means = (values @ indicators) / counts
    return values - group_means[..., labels]


def calibrate_centered_threshold(
    series: np.ndarray,
    labels: np.ndarray,
    block_length: int,
    n_boot: int,
    alpha: float,
    rng: np.random.Generator,
) -> float:
    """Soglia della F calibrata per moving block bootstrap con H0 imposta per centramento.

    La serie si centra per gruppo con center_by_group, poi calibrate_threshold ricampiona
    a blocchi la serie centrata e calcola la F con le etichette fisse. La F osservata da
    confrontare con la soglia si calcola invece sulla serie originale.

    Parametri
    ---------
    series : np.ndarray
        Serie 1D originale, forma (n,).
    labels : np.ndarray
        Etichette intere di gruppo, forma (n,), valori 0..k-1 tutti presenti.
    block_length : int
        Lunghezza dei blocchi (1 <= block_length <= n).
    n_boot : int
        Numero di ricampionamenti bootstrap (n_boot >= 1).
    alpha : float
        Livello nominale (0 < alpha < 1).
    rng : np.random.Generator
        Generatore degli indici del bootstrap.

    Restituisce
    -----------
    float
        Statistica d'ordine ceil((1 - alpha)(n_boot + 1)) delle F ricampionate.

    Solleva
    -------
    TypeError
        Per i tipi non validi, come center_by_group e calibrate_threshold.
    ValueError
        Se series non è 1D, oppure per i valori non validi di center_by_group e
        calibrate_threshold.
    """
    if not isinstance(series, np.ndarray):
        raise TypeError(f"series must be an instance of np.ndarray, got {type(series)}")
    if series.ndim != 1:
        raise ValueError(f"series must be 1D, got {series.ndim}D")

    centered = center_by_group(series, labels)

    def stat_fixed_labels(b_data: np.ndarray) -> np.ndarray:
        return oneway_anova_vectorized(b_data, labels)

    return calibrate_threshold(
        data=centered,
        statistic=stat_fixed_labels,
        block_length=block_length,
        n_boot=n_boot,
        alpha=alpha,
        rng=rng,
        vectorized=True,
    )


def spawn_t40_bootstrap_generators(
    seed: int = SEED_S7,
) -> tuple[tuple[np.random.Generator, ...], ...]:
    """Generatori del bootstrap del metodo centrato, separati dai flussi di SEED_C2.

    Schema: SeedSequence(seed).spawn(N_STORY_TASKS)[T40_STORY_POSITION], poi
    spawn(len(PHI_VALUES)) con un figlio per phi nell'ordine di PHI_VALUES, poi
    spawn(len(BLOCK_LENGTHS)) con un generatore per L nell'ordine di BLOCK_LENGTHS.
    Ogni generatore si usa in sequenza sulle N_SERIES serie.

    Parametri
    ---------
    seed : int, opzionale
        Seed radice (default: SEED_S7 = 20261011).

    Restituisce
    -----------
    tuple[tuple[np.random.Generator, ...], ...]
        Elemento [i][j] = generatore per PHI_VALUES[i] e BLOCK_LENGTHS[j].

    Solleva
    -------
    TypeError
        Se seed non è un intero valido.
    """
    if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)):
        raise TypeError(f"seed must be an integer, got {type(seed).__name__}")

    task_seed = np.random.SeedSequence(seed).spawn(N_STORY_TASKS)[T40_STORY_POSITION]
    phi_seeds = task_seed.spawn(len(PHI_VALUES))
    return tuple(
        tuple(np.random.default_rng(s) for s in phi_ss.spawn(len(BLOCK_LENGTHS)))
        for phi_ss in phi_seeds
    )


def compute_centered_calibration_details(
    seed: int = SEED_C2,
    bootstrap_seed: int = SEED_S7,
) -> list[CenteredCalibrationDetail]:
    """F osservate e soglie del metodo centrato per ogni phi e L, sul disegno contiguous_2.

    Le serie sono le stesse di compute_nominal_rejection_rates e
    compute_calibrated_rejection_rates: per ogni phi, generate_ar1_series col flusso
    series_rng di spawn_c2_generators(seed). Gli indici del bootstrap vengono da
    spawn_t40_bootstrap_generators(bootstrap_seed), quindi i flussi della calibrazione non centrata dell'ANOVA non si spostano.

    Parametri
    ---------
    seed : int, opzionale
        Seed delle serie (default: SEED_C2 = 20260928).
    bootstrap_seed : int, opzionale
        Seed del bootstrap centrato (default: SEED_S7 = 20261011).

    Restituisce
    -----------
    list[CenteredCalibrationDetail]
        12 elementi, ordinati per phi (PHI_VALUES) e, dentro ogni phi, per L (BLOCK_LENGTHS).

    Solleva
    -------
    TypeError
        Se seed o bootstrap_seed non sono interi validi.
    """
    if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)):
        raise TypeError(f"seed must be an integer, got {type(seed).__name__}")
    if isinstance(bootstrap_seed, bool) or not isinstance(bootstrap_seed, (int, np.integer)):
        raise TypeError(
            f"bootstrap_seed must be an integer, got {type(bootstrap_seed).__name__}"
        )

    labels_cont2 = make_design_labels(DESIGN_CONTIGUOUS_2, N_OBS)
    streams = spawn_c2_generators(seed=seed)
    boot_rngs = spawn_t40_bootstrap_generators(seed=bootstrap_seed)

    details: list[CenteredCalibrationDetail] = []
    for phi, phi_stream, phi_rngs in zip(PHI_VALUES, streams, boot_rngs):
        series = generate_ar1_series(
            phi=phi, n=N_OBS, m=N_SERIES, rng=phi_stream.series_rng
        )
        f_obs = oneway_anova_vectorized(series, labels_cont2)

        for l_val, rng_l in zip(BLOCK_LENGTHS, phi_rngs):
            thresholds = np.empty(N_SERIES, dtype=np.float64)
            for s in range(N_SERIES):
                thresholds[s] = calibrate_centered_threshold(
                    series=series[s],
                    labels=labels_cont2,
                    block_length=l_val,
                    n_boot=N_BOOT,
                    alpha=ALPHA,
                    rng=rng_l,
                )
            details.append(
                CenteredCalibrationDetail(
                    phi=phi,
                    block_length=l_val,
                    f_observed=f_obs,
                    thresholds=thresholds,
                )
            )

    return details


def compute_centered_calibrated_rejection_rates(
    seed: int = SEED_C2,
    bootstrap_seed: int = SEED_S7,
) -> list[RejectionResult]:
    """Tasso di falso rigetto con soglia calibrata sulla serie centrata per gruppo.

    Rigetto stretto: F osservata sulla serie originale > soglia calibrata sulla serie
    centrata, serie per serie. Restituisce i record ordinati per L (BLOCK_LENGTHS) e,
    dentro ogni L, per phi (PHI_VALUES), come compute_calibrated_rejection_rates.

    Parametri
    ---------
    seed : int, opzionale
        Seed delle serie (default: SEED_C2 = 20260928).
    bootstrap_seed : int, opzionale
        Seed del bootstrap centrato (default: SEED_S7 = 20261011).

    Restituisce
    -----------
    list[RejectionResult]
        12 record con method = "block_bootstrap_centered".

    Solleva
    -------
    TypeError
        Se seed o bootstrap_seed non sono interi validi.
    """
    details = compute_centered_calibration_details(
        seed=seed, bootstrap_seed=bootstrap_seed
    )
    mc_lower, mc_upper = monte_carlo_interval_99(ALPHA, N_SERIES)

    results_map: dict[tuple[int, float], RejectionResult] = {}
    for d in details:
        rejections = int(np.sum(d.f_observed > d.thresholds))
        results_map[(d.block_length, d.phi)] = RejectionResult(
            design=DESIGN_CONTIGUOUS_2,
            phi=d.phi,
            method=METHOD_BLOCK_BOOTSTRAP_CENTERED,
            block_length=str(d.block_length),
            n_series=N_SERIES,
            rejections=rejections,
            rejection_rate=float(rejections / N_SERIES),
            critical_value_mean=float(np.mean(d.thresholds)),
            mc_lower_99=mc_lower,
            mc_upper_99=mc_upper,
        )

    return [results_map[(l_val, phi)] for l_val in BLOCK_LENGTHS for phi in PHI_VALUES]
