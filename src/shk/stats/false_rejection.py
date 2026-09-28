"""Modulo per l'analisi del tasso di falso rigetto dell'ANOVA su serie temporali autoregressive."""

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
        Metodo di calcolo della soglia ("nominal" oppure "block_bootstrap").
    block_length : str
        Lunghezza del blocco di bootstrap ("" per il metodo nominale, lunghezza dei blocchi
        come stringa per "block_bootstrap").
    n_series : int
        Numero totale di serie simulate.
    rejections : int
        Numero di serie per cui la statistica supera il valore critico.
    rejection_rate : float
        Quota empirica di rigetti (rejections / n_series).
    critical_value_mean : float
        Valore critico nominale per "nominal" e media delle soglie calibrate serie
        per serie per "block_bootstrap".
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
