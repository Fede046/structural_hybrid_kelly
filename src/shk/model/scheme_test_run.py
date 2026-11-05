"""Schema del relatore sul 2023-24 su stagioni ricostruite, invece che sulla sola realizzazione osservata.

Su richiesta del 2026-11-05: la stagione di KellyBench giocata una volta dice poco, quindi gli agenti
la giocano anche su N_SEEDS stagioni ricostruite per stationary bootstrap delle date a L_PW, come
nelle esecuzioni sulla validazione. I seed sono quelli "block" dell'esecuzione unica
(test_run.t58_sequences, figlio 0), quindi A e B_0.25 coincidono con l'esecuzione unica e i confronti
con lo schema sono appaiati. Agenti: A e B_0.25, lo schema (C3, C3_stop, C3_and, soglie di
scheme_run.scheme_thresholds) e la variante con riferimento fisso (C3_ref, C3_ref_stop, soglie di
scheme_reference_run.reference_setups), con i parametri congelati e il fit 2020-21. Lo schema è
stato costruito dopo l'esecuzione unica sul test: il risultato è esplorativo.
"""

from collections.abc import Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor
from typing import Final

import numpy as np

from shk.model.frozen_agents import check_frozen_constants
from shk.model.frozen_params import load_frozen_params
from shk.model.module2_data import build_module2_frame
from shk.model.scheme_reference_run import ReferenceSetup, reference_setups, run_reference_instance
from shk.model.scheme_run import SchemeThresholds, run_scheme_instance, scheme_thresholds
from shk.model.season_bootstrap import reconstruct_season, season_block_length
from shk.model.season_input import SeasonInput
from shk.model.test_run import SeasonData, season_params_path, t58_sequences
from shk.model.validation_run import SEED_S10, ValidationResult, run_instance

TEST_SCHEME_ARMS: Final[tuple[str, ...]] = ("A", "B_0.25", "C3", "C3_stop", "C3_and", "C3_ref", "C3_ref_stop")
_SCHEME_PART: Final[tuple[str, ...]] = ("C3", "C3_stop", "C3_and")
_REFERENCE_PART: Final[tuple[str, ...]] = ("C3_ref", "C3_ref_stop")


def run_all_arms(params_path: str, thresholds: SchemeThresholds, setups: Mapping[str, ReferenceSetup],
                 inp: SeasonInput, fit: str) -> np.ndarray:
    """Una stagione (ricostruita o osservata) per tutti gli agenti di TEST_SCHEME_ARMS: (C, A, M)."""
    params = load_frozen_params(params_path)
    return np.concatenate([
        run_instance(params, inp, ("A", "B_0.25")),
        run_scheme_instance(params, thresholds, inp, fit, _SCHEME_PART),
        run_reference_instance(params, setups, inp, fit, _REFERENCE_PART),
    ], axis=1)


def _chunk(params_path: str, thresholds: SchemeThresholds, setups: Mapping[str, ReferenceSetup], inp: SeasonInput,
           fit: str, seed_seqs: Sequence[np.random.SeedSequence], block_length: float) -> np.ndarray:
    covariates = list(load_frozen_params(params_path).fixed["covariates"])
    outs = []
    for ss in seed_seqs:
        rec = reconstruct_season(inp, np.random.default_rng(ss), block_length, covariates=covariates)
        outs.append(run_all_arms(params_path, thresholds, setups, rec, fit))
    return np.stack(outs, axis=-1)


def evaluate_test_scheme(sd: SeasonData, workers: int = 1, seed: int | np.random.SeedSequence = SEED_S10,
                         n_seeds: int | None = None, chunk: int = 25) -> ValidationResult:
    """Soglie sul training, seed block dell'esecuzione unica e realizzazione osservata (vedi modulo)."""
    params_path = str(season_params_path(sd))
    params = load_frozen_params(params_path)
    check_frozen_constants(params)
    frame = build_module2_frame(sd.residuals, devig_method=sd.devig_method)
    train = frame[frame["role"] == "training"]
    thresholds = dict(scheme_thresholds(train, params))
    setups = reference_setups(train, params)
    n = int(params.fixed["n_seeds"]) if n_seeds is None else n_seeds
    seqs = t58_sequences(seed)[0].spawn(int(params.fixed["n_seeds"]))[:n]
    l_pw = season_block_length(sd.inp)
    parts = [seqs[i:i + chunk] for i in range(0, len(seqs), chunk)]
    args = [(params_path, thresholds, setups, sd.inp, sd.fit, p, l_pw) for p in parts]
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            outs = list(pool.map(_chunk, *zip(*args)))
    else:
        outs = [_chunk(*a) for a in args]
    seeds = np.concatenate(outs, axis=-1)
    observed = run_all_arms(params_path, thresholds, setups, sd.inp, sd.fit)
    n_dates = np.array([np.unique(sd.inp.dates).shape[0]])
    return ValidationResult((sd.season,), (sd.fit,), n_dates, np.array([l_pw]), seeds[None], observed[None])
