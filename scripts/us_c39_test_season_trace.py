"""Script: la versione definitiva giornata per giornata sulla stagione 2023-24 di KellyBench (esplorativo).

Come us_c33, ma sulla stagione di test, con i parametri congelati e il fit 2020-21: a ogni giornata le
due statistiche dell'allarme e le soglie per stagione, le parti non spiegate e le loro soglie, la
diagnosi, λ, il capitale della versione definitiva e del quarto di Kelly (puntata minima £0,01 sul
capitale di £220), la media e lo scarto tipico dei residui nelle ultime 40 partite e nella stagione
di calibrazione. È la stessa esecuzione deterministica di us_c30 sulla stagione vera, ripetuta per
registrarne il percorso; non si sceglie nulla sui dati del 2023-24.

Scrive results/us_c39_test_season_trace.csv (una riga per giornata, colonne di us_c33).
"""

import csv
import importlib.util
from pathlib import Path

from shk.model.frozen_agents import check_frozen_constants
from shk.model.frozen_params import load_frozen_params
from shk.model.main_version import main_setups
from shk.model.module2_data import build_module2_frame
from shk.model.test_run import TEST_FIT, TEST_SEASON, load_season_data, season_params_path
from shk.model.validation_run import ValidationSeason

REPO_ROOT = Path(__file__).resolve().parents[1]
TRACE_CSV = REPO_ROOT / "results" / "us_c39_test_season_trace.csv"

_spec = importlib.util.spec_from_file_location("us_c33", REPO_ROOT / "scripts" / "us_c33_main_alarm_trace.py")
us_c33 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(us_c33)


def run_experiment() -> None:
    sd = load_season_data(TEST_SEASON, TEST_FIT)
    params_path = str(season_params_path(sd))
    params = load_frozen_params(params_path)
    check_frozen_constants(params)
    frame = build_module2_frame(sd.residuals, devig_method=sd.devig_method)
    setups = main_setups(frame[frame["role"] == "training"], params)
    rows = us_c33.trace_season(params_path, setups, ValidationSeason(sd.inp, sd.fit))
    with open(TRACE_CSV, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(us_c33.TRACE_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)
    s = us_c33.season_rows(rows)[0]
    valid = [r for r in rows if r["f_mean"] == r["f_mean"]]
    print(f"{TEST_SEASON}: allarmi {s['n_alarm_days']}, capitale schema {100 * s['capital_main']:.1f}% "
          f"quarto {100 * s['capital_quarter']:.1f}%")
    print("max media/soglia %.3f  max dispersione/soglia %.3f" % (
        max(r["f_mean"] / r["f_mean_threshold"] for r in valid),
        max(r["f_dispersion"] / r["f_dispersion_threshold"] for r in valid)))
    last = valid[-1]
    print("riferimento: media %.4f scarto %.4f | ultime 40 a fine stagione: media %.4f scarto %.4f" % (
        last["mean_reference"], last["spread_reference"], last["mean_window"], last["spread_window"]))


if __name__ == "__main__":
    run_experiment()
