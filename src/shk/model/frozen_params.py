"""File di congelamento dei parametri di S9 e loader unico per S10 (T54, US-C8.2).

config/frozen_params.toml si scrive una sola volta, in T54 (write_frozen_params rifiuta di
sovrascrivere un file esistente), e poi non si tocca più. Il programmatore lo committa
prima di T55. S10 legge i parametri solo da qui, con load_frozen_params, che verifica che
il file contenga esattamente le chiavi richieste.

Sezioni:
- frozen_on: data del congelamento;
- [sources]: SHA256 dei CSV di T46, T47 e T53 da cui dipendono i parametri;
- [calibrated]: parametri liberi scelti sul training (T54);
- [calibration]: obiettivo, configurazione, seed e log della calibrazione;
- [fixed]: parametri fissati per costruzione, con la loro origine nei commenti del file;
- [c1_thresholds]: soglia di C1 per fit alla W scelta per C1, a L_PW;
- [not_calibrated_on_training]: parametri non calibrati sul training, con il motivo (vuota).

Con Dixon-Coles come Modulo 1 (T60, T61) il file è config/frozen_params_dc.toml;
frozen_params_path restituisce il file del Modulo 1 dato.
"""

import datetime
import math
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final

from shk.model.module1 import MODULE1_ELO, check_module1

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

    def adwin_params(self) -> dict[str, Any]:
        """Parametri completi di ADWIN per D_ADWIN."""
        return {
            "delta": self.calibrated["d_adwin_delta"],
            "clock": self.fixed["d_adwin_clock"],
            "max_buckets": self.fixed["d_adwin_max_buckets"],
            "min_window_length": self.fixed["d_adwin_min_window_length"],
            "grace_period": self.fixed["d_adwin_grace_period"],
        }

    def page_hinkley_params(self) -> dict[str, Any]:
        """Parametri completi di Page-Hinkley per D_PH."""
        return {
            "min_instances": self.fixed["d_page_hinkley_min_instances"],
            "delta": self.calibrated["d_page_hinkley_delta"],
            "threshold": self.calibrated["d_page_hinkley_threshold"],
            "alpha": self.fixed["d_page_hinkley_alpha"],
            "mode": self.fixed["d_page_hinkley_mode"],
        }


def check_keys(data: Mapping[str, Any]) -> None:
    """Verifica che il contenuto abbia esattamente le chiavi richieste.

    Solleva
    -------
    ValueError
        Con l'elenco delle chiavi mancanti o in più.
    """
    problems = []
    top = set(data)
    if top != TOP_LEVEL_KEYS:
        problems.append(f"top level: missing {sorted(TOP_LEVEL_KEYS - top)}, extra {sorted(top - TOP_LEVEL_KEYS)}")
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
    """Loader unico dei parametri congelati per S10.

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
    )


def _toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"non-finite float {value} cannot be frozen")
        return repr(value)
    if isinstance(value, str):
        if '"' in value or "\\" in value or "\n" in value:
            raise ValueError(f"unsupported string {value!r}")
        return f'"{value}"'
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_toml_value(v) for v in value) + "]"
    raise TypeError(f"unsupported TOML value {type(value).__name__}")


def render_frozen_params(frozen_on: datetime.date, sections: Mapping[str, Mapping[str, Any]],
                         comments: Mapping[str, str], header: str) -> str:
    """Testo TOML del file di congelamento; comments: commento per "sezione.chiave"."""
    data_check = {"frozen_on": frozen_on, **sections}
    check_keys(data_check)
    lines = [f"# {line}" if line else "#" for line in header.splitlines()]
    lines += ["", f"frozen_on = {frozen_on.isoformat()}"]
    for section in SECTION_KEYS:
        lines += ["", f"[{section}]"]
        for key, value in sections[section].items():
            note = comments.get(f"{section}.{key}")
            if note:
                lines += [f"# {line}" for line in note.splitlines()]
            name = f'"{key}"' if not key.replace("_", "").isalnum() else key
            lines.append(f"{name} = {_toml_value(value)}")
    text = "\n".join(lines) + "\n"
    tomllib.loads(text)
    return text


def write_frozen_params(path: Path | str, text: str) -> None:
    """Scrive il file di congelamento; rifiuta di sovrascrivere un file esistente.

    Solleva
    -------
    FileExistsError
        Se il file esiste già.
    """
    target = Path(path)
    if target.exists():
        raise FileExistsError(f"{target} already exists: frozen parameters are written only once")
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, mode="x", encoding="utf-8", newline="\n") as f:
        f.write(text)
