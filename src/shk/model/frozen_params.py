"""Loader unico dei parametri congelati per le esecuzioni congelate.

config/frozen_params.toml è stato scritto una sola volta, dalla calibrazione sul training del
2026-10, e poi non si è più toccato. La calibrazione sceglieva anche i parametri degli agenti di
confronto (C1, C2, D), che non fanno più parte del progetto: script e codice sono sul branch
confronti-controllo. Il file resta invariato come dato d'ingresso; lo schema del relatore ne usa
W (c1_window), κ (c1_kappa) e la soglia strutturale per fit ([c1_thresholds]).
load_frozen_params verifica che il file contenga esattamente le chiavi richieste.

Sezioni:
- frozen_on: data del congelamento;
- [sources]: SHA256 dei CSV da cui dipendevano i parametri;
- [calibrated]: parametri liberi scelti sul training;
- [calibration]: obiettivo, configurazione, seed e log della calibrazione;
- [fixed]: parametri fissati per costruzione, con la loro origine nei commenti del file;
- [c1_thresholds]: soglia strutturale per fit alla W congelata, a L_PW;
- [not_calibrated_on_training]: parametri non calibrati sul training, con il motivo (vuota).

Con Dixon-Coles come Modulo 1 il file è config/frozen_params_dc.toml;
frozen_params_path restituisce il file del Modulo 1 dato. Il file di Dixon-Coles ha le stesse
chiavi più la chiave di primo livello module1 = "dixon_coles"; quello dell'Elo non la ha,
e vale "elo".
"""

import datetime
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final

from shk.model.module1 import MODULE1_ELO, MODULE1_IDS, check_module1

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[3]
FROZEN_PARAMS_PATH: Final[Path] = REPO_ROOT / "config" / "frozen_params.toml"
FROZEN_PARAMS_DC_PATH: Final[Path] = REPO_ROOT / "config" / "frozen_params_dc.toml"


def frozen_params_path(module1: str = MODULE1_ELO) -> Path:
    """File di congelamento del Modulo 1: frozen_params.toml (Elo) o frozen_params_dc.toml."""
    return FROZEN_PARAMS_PATH if check_module1(module1) == MODULE1_ELO else FROZEN_PARAMS_DC_PATH


SECTION_KEYS: Final[dict[str, frozenset[str]]] = {
    "sources": frozenset({"us_c7_2_covariates", "us_c7_3_module2", "us_c7_3_module2_ci", "us_c8_3b_power"}),
    "calibrated": frozenset({
        "c1_window", "c1_kappa", "c2_global_window", "c2_window", "d_adwin_delta", "d_adwin_kappa",
        "d_page_hinkley_delta", "d_page_hinkley_threshold", "d_page_hinkley_kappa",
    }),
    "calibration": frozenset({
        "objective", "configuration", "n_seeds", "seed_scheme", "tie_rule", "log_csv", "log_sha256",
    }),
    "fixed": frozenset({
        "c1_alpha", "c1_n_boot", "c1_block_length", "c1_threshold_seed_scheme", "c1_alarm", "c1_alarm_count",
        "lambda_min", "lambda_max", "stop_rule", "c0_lambda", "inactive_lambda", "module3_candidate",
        "covariates", "out_of_support_min_count", "devig_method", "module1", "elo_fits", "n_seeds",
        "main_configuration_b0_over_f", "fallback_policy", "d_series", "d_base_lambda",
        "d_adwin_clock", "d_adwin_max_buckets", "d_adwin_min_window_length", "d_adwin_grace_period",
        "d_page_hinkley_min_instances", "d_page_hinkley_alpha", "d_page_hinkley_mode",
    }),
    "c1_thresholds": frozenset({"2000-01", "2010-11", "2020-21"}),
    "not_calibrated_on_training": frozenset(),
}
TOP_LEVEL_KEYS: Final[frozenset[str]] = frozenset({"frozen_on", *SECTION_KEYS})
MODULE1_KEY: Final[str] = "module1"


@dataclass(frozen=True)
class FrozenParams:
    """Parametri congelati, in sola lettura."""

    frozen_on: datetime.date
    sources: Mapping[str, str]
    calibrated: Mapping[str, Any]
    calibration: Mapping[str, Any]
    fixed: Mapping[str, Any]
    c1_thresholds: Mapping[str, float]
    not_calibrated_on_training: Mapping[str, str]
    module1: str = MODULE1_ELO


def check_keys(data: Mapping[str, Any]) -> None:
    """Verifica che il contenuto abbia esattamente le chiavi richieste.

    Solleva
    -------
    ValueError
        Con l'elenco delle chiavi mancanti o in più.
    """
    problems = []
    top = set(data)
    expected = TOP_LEVEL_KEYS | ({MODULE1_KEY} if MODULE1_KEY in data else set())
    if top != expected:
        problems.append(f"top level: missing {sorted(expected - top)}, extra {sorted(top - expected)}")
    # Identificatore del Modulo 1: solo per Modulo 1 diversi dall'Elo, che è il default senza chiave
    if MODULE1_KEY in data and (data[MODULE1_KEY] not in MODULE1_IDS or data[MODULE1_KEY] == MODULE1_ELO):
        problems.append(f"{MODULE1_KEY}: must be one of {[m for m in MODULE1_IDS if m != MODULE1_ELO]}, "
                        f"got {data[MODULE1_KEY]!r}")
    for section, keys in SECTION_KEYS.items():
        if section in data:
            if not isinstance(data[section], Mapping):
                problems.append(f"{section}: must be a table")
                continue
            got = set(data[section])
            if got != keys:
                problems.append(f"{section}: missing {sorted(keys - got)}, extra {sorted(got - keys)}")
    if problems:
        raise ValueError("frozen params keys mismatch: " + "; ".join(problems))


def load_frozen_params(path: Path | str = FROZEN_PARAMS_PATH) -> FrozenParams:
    """Loader unico dei parametri congelati per le esecuzioni congelate.

    Solleva
    -------
    FileNotFoundError
        Se il file non esiste.
    ValueError
        Se le chiavi non sono esattamente quelle richieste o frozen_on non è una data.
    """
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    check_keys(data)
    if not isinstance(data["frozen_on"], datetime.date):
        raise ValueError("frozen_on must be a TOML date")
    return FrozenParams(
        frozen_on=data["frozen_on"],
        **{s: MappingProxyType(dict(data[s])) for s in SECTION_KEYS},
        module1=data.get(MODULE1_KEY, MODULE1_ELO),
    )
