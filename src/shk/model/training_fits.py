"""Verifiche sulla scelta delle stagioni di training (decisione del 2026-11-05).

Le stagioni di training sono una ogni dieci anni (2000-01, 2010-11, 2020-21, config/split.toml); il
2020-21 è la stagione del Covid, giocata quasi tutta a porte chiuse, e il fit 2010-11 prevede fino a
nove stagioni. Lo split congelato non cambia; qui ci sono due verifiche:

- Covid: il 2021-22 e il 2022-23, previsti dal fit congelato 2020-21 (che include il 2020-21),
  previsti invece dal fit 2010-11, che non lo include;
- fit aggiuntivo: un fit 2015-16, calibrato come gli altri (schema espansivo: 2000-01, 2010-11,
  2015-16, con elo_fit.calibrate_single_fit), prevede le stagioni dal 2016-17 al 2019-20 al posto
  del fit 2010-11. Le altre 15 stagioni restano quelle del modello congelato, bit per bit.

Per entrambe: ĝ, errore atteso e log-loss per stagione, e quota media di vittorie in casa prevista
dal modello, dal mercato e reale. Per il fit aggiuntivo anche lo schema a riferimento fisso
(B_0.25, C3_ref, C3_ref_stop) con gli stessi seed dell'esecuzione congelata: soglie e stagione di
calibrazione congelate per i fit esistenti (scheme_reference_run.reference_setups) e, per il fit
2015-16, calibrate sulla stagione 2015-16 con un seed proprio. Il 2015-16 resta anche stagione di
validazione, prevista dal fit 2010-11: il fit 2015-16 prevede solo stagioni successive.
"""

import copy
from typing import Final

import numpy as np
import pandas as pd

from shk.model.elo_fit import ELO_FITS, EloFitParams, calibrate_single_fit
from shk.model.elo_refit import refit_module2_frame, season_model_stats
from shk.model.frozen_params import FrozenParams
from shk.model.module2_data import build_module2_frame
from shk.model.residuals import ModelResidualsData, model_residuals_data
from shk.model.scheme_reference_run import ReferenceSetup, reference_setups

COVID_FIT: Final[str] = "2010-11"
COVID_SEASONS: Final[tuple[str, ...]] = ("2021-22", "2022-23")
EXTRA_FIT: Final[str] = "2015-16"
EXTRA_TRAINING: Final[tuple[str, ...]] = ("2000-01", "2010-11", "2015-16")
EXTRA_SEASONS: Final[tuple[str, ...]] = ("2016-17", "2017-18", "2018-19", "2019-20")
SEED_S20: Final[int] = 20261109

ERROR_COLUMNS: Final[tuple[str, ...]] = (
    "check", "model", "season", "fit", "k", "h", "nu", "n_matches", "g_hat", "expected", "log_loss",
    "p_home", "q_home", "home_rate",
)


def extra_fit_params(df: pd.DataFrame) -> EloFitParams:
    """Parametri del fit 2015-16, calibrato come i fit congelati."""
    res = calibrate_single_fit(df, EXTRA_FIT, list(EXTRA_TRAINING))
    return EloFitParams(k=res.k, h=res.h, nu=res.nu, c=res.c)


def extra_fit_data(df: pd.DataFrame, frozen: ModelResidualsData, fit: EloFitParams) -> ModelResidualsData:
    """Residui con il fit 2015-16 per EXTRA_SEASONS e i fit congelati per le altre stagioni."""
    schedule = copy.deepcopy(frozen.schedule)
    schedule[COVID_FIT]["validation"] = [s for s in schedule[COVID_FIT]["validation"] if s not in EXTRA_SEASONS]
    schedule[EXTRA_FIT] = {"training": list(EXTRA_TRAINING), "validation": list(EXTRA_SEASONS)}
    return model_residuals_data(df, schedule, {**ELO_FITS, EXTRA_FIT: fit})


def covid_check_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Righe di validazione di COVID_SEASONS previste dal fit 2010-11."""
    sched = {COVID_FIT: {"training": ["2000-01", COVID_FIT], "validation": list(COVID_SEASONS)}}
    data = model_residuals_data(df, sched, {COVID_FIT: ELO_FITS[COVID_FIT]})
    res = data.residuals
    return build_module2_frame(data._replace(residuals=res[res["role"] == "validation"].reset_index(drop=True)))


def _rows(check: str, model: str, frame: pd.DataFrame, fits: dict[str, EloFitParams]) -> list[dict]:
    pooled = frame.assign(season="all")
    stats = pd.concat([season_model_stats(frame), season_model_stats(pooled)])
    out = []
    for season, st in stats.iterrows():
        part = frame if season == "all" else frame[frame["season"] == season]
        fit = str(st["fit"])
        p = fits[fit]
        out.append({"check": check, "model": model, "season": season, "fit": fit, "k": p.k, "h": p.h, "nu": p.nu,
                    "n_matches": int(st["n_matches"]), "g_hat": st["g_hat"], "expected": st["expected"],
                    "log_loss": st["log_loss"], "p_home": float(part["p_home"].mean()),
                    "q_home": float(part["q_home"].mean()), "home_rate": float((part["FTR"] == "H").mean())})
    return out


def error_records(frozen_frame: pd.DataFrame, covid_frame: pd.DataFrame, extra_frame: pd.DataFrame,
                  extra_fit: EloFitParams) -> list[dict]:
    """Errori del modello per stagione e sulle stagioni insieme ("all"), nelle due verifiche."""
    fits = {**ELO_FITS, EXTRA_FIT: extra_fit}
    val = frozen_frame[frozen_frame["role"] == "validation"]
    ext = extra_frame[extra_frame["role"] == "validation"]
    return (_rows("covid", "frozen", val[val["season"].isin(COVID_SEASONS)], fits)
            + _rows("covid", "without_2020_21", covid_frame, fits)
            + _rows("extra_fit", "frozen", val[val["season"].isin(EXTRA_SEASONS)], fits)
            + _rows("extra_fit", "fit_2015_16", ext[ext["season"].isin(EXTRA_SEASONS)], fits))


def extra_frame_unchanged(frozen_frame: pd.DataFrame, extra_frame: pd.DataFrame) -> bool:
    """Vero se le stagioni di validazione fuori da EXTRA_SEASONS hanno gli stessi δ del modello congelato."""
    def part(f: pd.DataFrame) -> pd.DataFrame:
        v = f[(f["role"] == "validation") & ~f["season"].isin(EXTRA_SEASONS)]
        return v.sort_values(["Date", "HomeTeam"], kind="stable").reset_index(drop=True)
    a, b = part(frozen_frame), part(extra_frame)
    return len(a) == len(b) and np.array_equal(a["delta"].to_numpy(), b["delta"].to_numpy())


def extra_setups(frozen_frame: pd.DataFrame, extra_frame: pd.DataFrame,
                 params: FrozenParams) -> dict[str, ReferenceSetup]:
    """Setup del riferimento fisso: congelati per i fit esistenti, nuovi (SEED_S20) per il fit 2015-16."""
    setups = reference_setups(frozen_frame[frozen_frame["role"] == "training"], params)
    train = extra_frame[(extra_frame["role"] == "training") & (extra_frame["season"] == EXTRA_FIT)]
    setups[EXTRA_FIT] = reference_setups(train, params, seed=SEED_S20)[EXTRA_FIT]
    return setups


def extra_module2_frame(data: ModelResidualsData) -> pd.DataFrame:
    """DataFrame del Modulo 2 con il fit aggiuntivo (il 2015-16 è sia training sia validazione)."""
    return refit_module2_frame(data)
