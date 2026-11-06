"""Test: ri-parametrizzazione annuale dell'Elo e schema a riferimento fisso sul modello ricalibrato."""

from pathlib import Path

import pandas as pd

from shk.model.elo_refit import REFIT_AGING_COLUMNS, REFIT_PARAM_COLUMNS
from shk.model.frozen_params import load_frozen_params
from shk.model.scheme_reference_run import REFERENCE_ARMS
from shk.model.validation_run import CONFIG_NAMES, SUMMARY_COLUMNS

RESULTS = Path(__file__).resolve().parents[1] / "results"
FROZEN_CSV = RESULTS / "us_c13_scheme_reference_summary.csv"
N_SEASONS = 19


def _sum_median(df: pd.DataFrame, agent: str) -> float:
    rows = df[(df["agent"] == agent) & (df["config"] == "gbp_0.01")]
    assert len(rows) == N_SEASONS
    return float(rows["median_log_wealth"].sum())


def test_params_and_aging_structure():
    params = pd.read_csv(RESULTS / "us_c18_elo_refit_params.csv")
    assert tuple(params.columns) == REFIT_PARAM_COLUMNS and len(params) == N_SEASONS
    assert "2001-02" not in set(params["fit"])
    aging = pd.read_csv(RESULTS / "us_c18_elo_refit_aging.csv")
    assert tuple(aging.columns) == REFIT_AGING_COLUMNS and len(aging) == N_SEASONS
    assert (aging["n_matches"] == 380).all()
    # 2002-03: stesso fit (2000-01) per il modello congelato e per quello ricalibrato
    first = aging.iloc[0]
    assert first["season"] == "2002-03" and first["frozen_fit"] == first["refit_fit"] == "2000-01"
    assert abs(first["frozen_expected"] - first["refit_expected"]) < 1e-12


def test_summary_structure_and_findings():
    df = pd.read_csv(RESULTS / "us_c18_elo_refit_summary.csv")
    assert tuple(df.columns) == SUMMARY_COLUMNS
    assert len(df) == N_SEASONS * len(CONFIG_NAMES) * len(REFERENCE_ARMS)
    assert (df["n_seeds"] == int(load_frozen_params().fixed["n_seeds"])).all()
    frozen = pd.read_csv(FROZEN_CSV)
    # Ricalibrare ogni anno non aiuta: tutti gli agenti perdono più che col modello congelato
    for arm in REFERENCE_ARMS:
        assert _sum_median(df, arm) < _sum_median(frozen, arm)
    # Lo schema resta utile anche sul modello ricalibrato
    assert _sum_median(df, "C3_ref_stop") > _sum_median(df, "C3_ref") > _sum_median(df, "B_0.25")
