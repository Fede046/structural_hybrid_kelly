"""Test: lo schema nel mondo simulato con vantaggio noto (us_c25)."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shk.model.edge_simulation import N_REPLICAS, SCENARIOS, SCHEME_ARMS
from shk.model.season_thresholds import PER_DATE_ARMS, SEASON_ARMS

CSV_PATH = Path(__file__).resolve().parents[1] / "results" / "us_c25_edge_simulation.csv"
N_SEASONS = 19
AGENTS = ("full_kelly", "quarter_kelly") + SCHEME_ARMS + tuple(f"constant:{a}" for a in SCHEME_ARMS) + ("oracle",)

pytestmark = pytest.mark.skipif(not CSV_PATH.exists(), reason="us_c25 non ancora eseguito")


def _rows(row_type: str) -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH)
    return df[df["row_type"] == row_type].set_index(["scenario", "agent"])


def test_structure():
    df = pd.read_csv(CSV_PATH)
    assert len(df) == len(SCENARIOS) * (len(AGENTS) + len(SCHEME_ARMS))
    assert (df["n_units"] == N_SEASONS * N_REPLICAS).all()
    capital = _rows("capital")
    assert set(capital.index) == {(s.name, a) for s in SCENARIOS for a in AGENTS}
    assert (capital["typical_capital"] >= 0).all()


def test_oracle_by_construction():
    capital = _rows("capital")
    # Con il vantaggio stabile l'oracolo non si ferma mai; senza vantaggio non punta mai
    assert capital.loc[("stable_edge", "oracle"), "typical_capital"] == pytest.approx(
        capital.loc[("stable_edge", "quarter_kelly"), "typical_capital"])
    assert capital.loc[("no_edge", "oracle"), "typical_capital"] == pytest.approx(1.0)
    # Negli scenari con il cambiamento l'oracolo è lo stesso: conta solo la prima metà, che coincide
    assert capital.loc[("edge_vanishes", "oracle"), "typical_capital"] == pytest.approx(
        capital.loc[("edge_reverses", "oracle"), "typical_capital"])


def test_scenarios_are_paired_until_the_break():
    """Stessi esiti e stesso riferimento prima del cambiamento: stessi stop e stesso costo fino a metà stagione."""
    det = _rows("detection")
    for arm in SCHEME_ARMS:
        for col in ("share_stopped_before", "share_days_zero_before", "mean_log_gain_before"):
            values = [det.loc[(s, arm), col] for s in ("stable_edge", "edge_vanishes", "edge_reverses")]
            assert np.allclose(values, values[0], rtol=0, atol=1e-12), (arm, col)
    # Le due versioni con le stesse soglie hanno lo stesso supervisore: stesso primo errore strutturale
    for s in SCENARIOS:
        for resume, stop in (PER_DATE_ARMS, tuple(SEASON_ARMS)):
            assert det.loc[(s.name, resume), "share_stopped"] == det.loc[(s.name, stop), "share_stopped"]


def test_findings():
    capital, det = _rows("capital"), _rows("detection")

    def typical(scenario: str, agent: str) -> float:
        return float(capital.loc[(scenario, agent), "typical_capital"])

    # Quando il modello ha ragione il Kelly pieno è il migliore; quando il vantaggio sparisce o si rovescia crolla
    assert typical("stable_edge", "full_kelly") > typical("stable_edge", "quarter_kelly")
    assert typical("edge_reverses", "full_kelly") < 0.1 < typical("edge_reverses", "quarter_kelly")
    # Vantaggio che si rovescia: lo schema batte il quarto di Kelly e la frazione costante di pari esposizione
    for arm in PER_DATE_ARMS:
        assert typical("edge_reverses", arm) > 1.2 * typical("edge_reverses", "quarter_kelly")
        assert typical("edge_reverses", arm) > 1.2 * typical("edge_reverses", f"constant:{arm}")
        assert capital.loc[("edge_reverses", arm), "share_better_than_quarter"] > 0.8
    # Vantaggio che svanisce: fa meglio della frazione costante di pari esposizione
    for arm in SCHEME_ARMS:
        assert typical("edge_vanishes", arm) > typical("edge_vanishes", f"constant:{arm}")
    # Dopo il cambiamento lo schema recupera capitale, e di più se il cambiamento è più grande
    for arm in SCHEME_ARMS:
        assert 0 < det.loc[("edge_vanishes", arm), "mean_log_gain_after"] < det.loc[("edge_reverses", arm), "mean_log_gain_after"]
    # Il costo: in un mondo stabile lo stop fino a fine stagione scatta per falso allarme in molte stagioni
    assert det.loc[("stable_edge", "C3_ref_stop"), "share_stopped"] > 0.3
    assert typical("stable_edge", "C3_ref_stop") < typical("stable_edge", "quarter_kelly")
    assert det.loc[("stable_edge", "C3_ref_stop"), "mean_log_gain_after"] < 0
    # Soglie per stagione: nel mondo stabile lo schema quasi non si ferma più e non costa quasi nulla...
    season_stop = "C3_ref_stop_season"
    for scenario in ("stable_edge", "no_edge"):
        assert det.loc[(scenario, season_stop), "share_stopped"] < 0.10
    assert typical("stable_edge", season_stop) > 0.95 * typical("stable_edge", "quarter_kelly")
    # ...riconosce ancora il cambiamento grande, e lì batte quarto di Kelly e frazione costante...
    assert det.loc[("edge_reverses", season_stop), "share_stopped"] > 0.5
    assert typical("edge_reverses", season_stop) > 1.2 * typical("edge_reverses", "quarter_kelly")
    assert typical("edge_reverses", season_stop) > 1.2 * typical("edge_reverses", f"constant:{season_stop}")
    # ...ma più di rado e più tardi delle soglie per giornata, e il cambiamento piccolo lo vede poco
    for scenario in ("edge_vanishes", "edge_reverses"):
        assert det.loc[(scenario, season_stop), "share_stopped"] < det.loc[(scenario, "C3_ref_stop"), "share_stopped"]
        assert det.loc[(scenario, season_stop), "median_delay_days"] > det.loc[(scenario, "C3_ref_stop"), "median_delay_days"]
    assert det.loc[("edge_vanishes", season_stop), "share_stopped"] < 0.5
    # Diagnosi: quella a tre termini dice «strutturale» in circa metà degli allarmi in ogni scenario,
    # anche quando cambia solo il tipo di partite; quella a due termini distingue i due casi
    structural = det["share_structural_after"]
    for scenario in ("edge_vanishes", "edge_reverses", "composition_shift"):
        assert 0.35 < structural[(scenario, "C3_ref")] < 0.65
    assert structural[("composition_shift", "C3_ref_dx")] < 0.25
    assert structural[("edge_vanishes", "C3_ref_dx")] > 0.75 and structural[("edge_reverses", "C3_ref_dx")] > 0.85
    # ...e con il solo cambio di composizione lo schema si ferma meno e perde meno, pur non azzerando l'errore
    assert det.loc[("composition_shift", "C3_ref_stop_dx"), "share_stopped"] \
        < det.loc[("composition_shift", "C3_ref_stop"), "share_stopped"] - 0.2
    assert typical("composition_shift", "C3_ref_stop_dx") > 1.3 * typical("composition_shift", "C3_ref_stop")
    assert typical("composition_shift", "C3_ref_stop_dx") < typical("composition_shift", "quarter_kelly")
    # Un falso allarme non è spiegato dal tipo di partite: la diagnosi a due termini lo chiama strutturale
    assert structural[("stable_edge", "C3_ref_dx")] > 0.6
    # Un cambiamento più grande è riconosciuto più spesso e prima
    assert det.loc[("edge_reverses", "C3_ref"), "share_stopped"] > det.loc[("stable_edge", "C3_ref"), "share_stopped"]
    assert det.loc[("edge_reverses", "C3_ref"), "median_delay_days"] <= det.loc[("edge_vanishes", "C3_ref"), "median_delay_days"]
