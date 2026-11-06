"""Test: verifiche sulle stagioni di training (Covid e fit aggiuntivo 2015-16)."""

from pathlib import Path

import pandas as pd

from shk.model.frozen_params import load_frozen_params
from shk.model.scheme_reference_run import REFERENCE_ARMS
from shk.model.training_fits import COVID_SEASONS, ERROR_COLUMNS, EXTRA_SEASONS
from shk.model.validation_run import CONFIG_NAMES, SUMMARY_COLUMNS

RESULTS = Path(__file__).resolve().parents[1] / "results"
FROZEN_CSV = RESULTS / "us_c13_scheme_reference_summary.csv"
N_SEASONS = 19


def _pooled(df: pd.DataFrame, check: str, model: str) -> pd.Series:
    return df[(df["check"] == check) & (df["model"] == model) & (df["season"] == "all")].iloc[0]


def test_errors_structure_and_findings():
    df = pd.read_csv(RESULTS / "us_c20_training_fits_errors.csv")
    assert tuple(df.columns) == ERROR_COLUMNS
    assert len(df) == 2 * (len(COVID_SEASONS) + 1) + 2 * (len(EXTRA_SEASONS) + 1)
    # Togliere il 2020-21 dal fit peggiora le previsioni del 2021-23
    with_covid, without = _pooled(df, "covid", "frozen"), _pooled(df, "covid", "without_2020_21")
    assert without["g_hat"] < with_covid["g_hat"] and without["log_loss"] > with_covid["log_loss"]
    # Il fit 2015-16 prevede meglio il 2016-20 e dà alle squadre di casa quasi quanto il mercato;
    # il fit 2010-11 dava loro di più, e in quelle stagioni le squadre di casa vincevano più del mercato
    old, new = _pooled(df, "extra_fit", "frozen"), _pooled(df, "extra_fit", "fit_2015_16")
    assert new["log_loss"] < old["log_loss"] and new["g_hat"] > old["g_hat"]
    assert abs(new["p_home"] - new["q_home"]) < abs(old["p_home"] - old["q_home"])
    assert old["q_home"] < old["home_rate"] < old["p_home"]


def test_summary_paired_with_frozen_run():
    df = pd.read_csv(RESULTS / "us_c20_training_fits_summary.csv", dtype=str, keep_default_na=False)
    assert tuple(df.columns) == SUMMARY_COLUMNS
    assert len(df) == N_SEASONS * len(CONFIG_NAMES) * len(REFERENCE_ARMS)
    assert set(df["n_seeds"]) == {str(load_frozen_params().fixed["n_seeds"])}
    ref = pd.read_csv(FROZEN_CSV, dtype=str, keep_default_na=False)
    keep = ~df["season"].isin(EXTRA_SEASONS)
    # Fuori da EXTRA_SEASONS il modello e i seed sono quelli congelati: stesse sintesi
    a = df[keep].reset_index(drop=True)
    b = ref[~ref["season"].isin(EXTRA_SEASONS)].reset_index(drop=True)
    pd.testing.assert_frame_equal(a, b)
    assert set(df[~keep]["fit_through"]) == {"2015-16"}


def test_scheme_beats_quarter_kelly_on_real_seasons():
    df = pd.read_csv(RESULTS / "us_c20_training_fits_summary.csv")
    main = df[df["config"] == "gbp_0.01"]
    b = main[main["agent"] == "B_0.25"].set_index("season")["observed_log_wealth"]
    stop = main[main["agent"] == "C3_ref_stop"].set_index("season")["observed_log_wealth"]
    assert ((stop - b) > 1e-12).sum() >= 17
