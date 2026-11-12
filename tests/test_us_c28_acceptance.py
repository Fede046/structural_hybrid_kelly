"""Test: età del modello, tempo di calendario e sensibilità al riferimento (us_c28), appaiato con us_c18."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shk.model.two_fold_diagnosis import RUN_ARMS

RESULTS = Path(__file__).resolve().parents[1] / "results"
N_SEASONS, N_EVALUATED, N_CONFIGS = 19, 16, 3


def _csv(name: str) -> pd.DataFrame:
    return pd.read_csv(RESULTS / f"us_c28_{name}.csv")


pytestmark = pytest.mark.skipif(not (RESULTS / "us_c28_model_age_tests.csv").exists(), reason="us_c28 non ancora eseguito")


def test_structure():
    assert len(_csv("model_age_seasons")) == N_SEASONS
    assert len(_csv("model_age_tests")) == 4 * 3
    assert len(_csv("reference_setups")) == 2 * 3
    assert len(_csv("reference_summary")) == 2 * N_CONFIGS * len(RUN_ARMS)
    assert len(_csv("reference_seasons")) == 2 * N_EVALUATED * N_CONFIGS * len(RUN_ARMS)


def test_matches_the_annual_refit_of_us_c18():
    """Stessi modelli di us_c18: stessi errori attesi e stessa media di δ, congelato e ricalibrato."""
    mine = _csv("model_age_seasons").set_index("season")
    c18 = pd.read_csv(RESULTS / "us_c18_elo_refit_aging.csv").set_index("season").loc[mine.index]
    for ours, theirs in (("frozen_expected", "frozen_expected"), ("refit_expected", "refit_expected"),
                         ("frozen_mean", "frozen_g_hat"), ("refit_mean", "refit_g_hat")):
        assert np.allclose(mine[ours], c18[theirs], rtol=0, atol=1e-12), ours
    assert (mine["refit_fit"] == c18["refit_fit"]).all()
    # Nel 2002-03 il modello ricalibrato è il congelato: nessuna differenza
    first = mine.loc["2002-03"]
    assert first["frozen_fit"] == first["refit_fit"] and first["dispersion_difference"] == 0.0


def test_findings_age_and_calendar():
    tests = _csv("model_age_tests").set_index(["test", "measure"])
    # Dentro una calibrazione la dispersione del modello congelato cresce con l'età...
    assert tests.loc[("frozen_vs_age", "dispersion"), "p_value"] < 0.01
    # ...ma cresce con gli anni anche quella del modello ricalibrato ogni anno, che ha sempre la stessa età
    assert tests.loc[("refit_vs_year", "dispersion"), "p_value"] < 0.05
    assert tests.loc[("refit_vs_year", "expected"), "p_value"] < 0.05
    # Sulle stesse partite il modello congelato è più lontano dal mercato prima della partita in quasi tutte
    # le stagioni: l'effetto dell'età c'è sull'errore atteso
    row = tests.loc[("paired_difference", "expected")]
    assert row["n_positive"] >= 13 and row["n_positive"] + row["n_negative"] == 16 and row["p_value"] < 0.01
    # ...ma non è distinguibile sulla dispersione degli errori realizzati, e non cresce in modo
    # distinguibile con l'età
    assert tests.loc[("paired_difference", "dispersion"), "p_value"] > 0.1
    for measure in ("dispersion", "expected"):
        assert tests.loc[("difference_vs_age", measure), "p_value"] > 0.1


def test_findings_reference_sensitivity():
    setups = _csv("reference_setups").set_index(["reference", "fit"])
    # La stagione di calibrazione 2010-11 è molto meno dispersa della stagione successiva con lo stesso modello
    assert setups.loc[("first_after", "2010-11"), "dispersion"] > setups.loc[("calibration", "2010-11"), "dispersion"] + 0.03
    summary = _csv("reference_summary")
    main = summary[summary["config"] == "gbp_0.01"].set_index(["reference", "agent"])
    assert (main["n_seasons"] == N_EVALUATED).all()
    # Il quarto di Kelly non dipende dal riferimento
    assert main.loc[("calibration", "B_0.25"), "typical_capital"] == pytest.approx(main.loc[("first_after", "B_0.25"), "typical_capital"])
    # Con il riferimento fuori campione lo schema si ferma in molte meno stagioni
    for agent in ("C3_ref_stop", "C3_ref_stop_season", "C3_ref_stop_season_dx"):
        assert main.loc[("first_after", agent), "seasons_with_stop"] < main.loc[("calibration", agent), "seasons_with_stop"]
    assert main.loc[("calibration", "C3_ref_stop_season"), "seasons_with_stop"] >= 10
    assert main.loc[("first_after", "C3_ref_stop_season"), "seasons_with_stop"] <= 4
    # ...e conserva meno capitale, perché punta di più
    assert main.loc[("first_after", "C3_ref_stop"), "typical_capital"] < main.loc[("calibration", "C3_ref_stop"), "typical_capital"]
