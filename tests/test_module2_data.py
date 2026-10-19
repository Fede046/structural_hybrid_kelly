"""Test di src/shk/model/module2_data.py: δ, covariate e anti-leakage."""

import numpy as np
import pandas as pd
import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.model.elo import davidson_probabilities
from shk.model.elo_fit import ELO_FITS
from shk.model.module2_data import (
    COVARIATE_COLUMNS,
    MODULE2_FRAME_COLUMNS,
    build_module2_frame,
    entry_status_by_team_season,
    reconstruct_elo_diff,
    select_triple_2000_01,
)
from shk.model.residuals import ModelResidualsData, compute_model_residuals, load_model_residuals
from shk.model.scoring import (
    align_predictions_with_odds,
    generate_validation_predictions,
    prepare_series_evaluation,
)


def _has_real_data() -> bool:
    return DEFAULT_DATA_DIR.is_dir() and any(DEFAULT_DATA_DIR.glob("*.csv"))


def test_reconstruct_elo_diff_inverts_davidson():
    """400·log10(p_home/p_away) restituisce il delta di Davidson."""
    deltas = np.array([-250.0, -10.0, 0.0, 77.7, 410.0])
    p_home, _, p_away = davidson_probabilities(deltas, nu=0.8)
    np.testing.assert_allclose(reconstruct_elo_diff(p_home, p_away), deltas, rtol=0, atol=1e-9)
    with pytest.raises(ValueError, match="strictly positive"):
        reconstruct_elo_diff(np.array([0.0]), np.array([0.5]))


def test_entry_status_rule():
    """Prima stagione tutte vuote; poi 'new' mai vista, 'returning' vista ma non in s − 1."""
    rows = [
        ("1999-00", "A", "B"), ("1999-00", "C", "D"),
        ("2000-01", "A", "E"), ("2000-01", "B", "F"),
        ("2001-02", "A", "C"), ("2001-02", "E", "G"),
    ]
    df = pd.DataFrame(rows, columns=["season", "HomeTeam", "AwayTeam"])
    status = entry_status_by_team_season(df)
    assert all(status[("1999-00", t)] == "" for t in "ABCD")
    assert status[("2000-01", "E")] == "new" and status[("2000-01", "F")] == "new"
    assert status[("2000-01", "A")] == "" and status[("2000-01", "B")] == ""
    assert status[("2001-02", "C")] == "returning"
    assert status[("2001-02", "G")] == "new"
    assert status[("2001-02", "E")] == "" and status[("2001-02", "A")] == ""


def _triple_frame() -> pd.DataFrame:
    base = {"season": ["2000-01"] * 2 + ["2002-03"] * 2}
    for src, odds in {"GB": (2.0, 3.0, 3.5), "IW": (1.8, 3.0, 3.4), "SB": (2.1, 3.3, 3.6),
                      "WH": (2.0, 3.1, 3.2), "B365": (2.05, 3.25, 3.55)}.items():
        for col, val in zip("HDA", odds):
            base[f"{src}{col}"] = [val] * 4
    return pd.DataFrame(base)


def test_select_triple_2000_01_closest_overround():
    """Vince la terna con overround medio più vicino a B365 nel 2002-03."""
    df = _triple_frame()
    choice = select_triple_2000_01(df)
    ref = 1 / 2.05 + 1 / 3.25 + 1 / 3.55 - 1
    diffs = {s: abs(choice.candidate_overrounds[s] - ref) for s in choice.candidate_overrounds}
    assert choice.source == min(diffs, key=diffs.get)
    assert abs(choice.b365_reference_overround - ref) < 1e-15
    df.loc[0, "SBH"] = np.nan
    assert "SB" not in select_triple_2000_01(df).candidate_overrounds


@pytest.fixture(scope="module")
def real_frame():
    if not _has_real_data():
        pytest.skip(f"Real data missing: no CSV in {DEFAULT_DATA_DIR}")
    data = load_model_residuals()
    return data, build_module2_frame(data)


def test_frame_structure(real_frame):
    """22 stagioni da 380 partite, colonne prescritte, posizioni 1..380."""
    _, frame = real_frame
    assert tuple(frame.columns) == MODULE2_FRAME_COLUMNS
    assert len(frame) == 22 * 380
    assert frame.groupby("season").size().eq(380).all()
    assert frame.groupby("season")["position"].apply(lambda s: list(s) == list(range(1, 381))).all()
    assert (frame.loc[frame["season"] == "2000-01", "odds_source"] == "SB").all()


def test_delta_season_means_match_shin_g_hat(real_frame):
    """δ medio per stagione di validazione = ĝ Shin per stagione della serie dell'aggiunta di Shin e odds ratio, entro 1e-12."""
    data, frame = real_frame
    preds = generate_validation_predictions(data.df, ELO_FITS, data.schedule)
    ev = prepare_series_evaluation(align_predictions_with_odds(preds, data.df), "b365_prematch", data.schedule)
    idx = np.array([{"H": 0, "D": 1, "A": 2}[o] for o in ev.outcomes])
    rows = np.arange(idx.size)
    terms = np.log(ev.p_model[rows, idx]) - np.log(ev.q_shin[rows, idx])
    g_hat = pd.Series(terms).groupby(ev.df_used["season"].to_numpy()).mean()
    delta = frame[frame["role"] == "validation"].groupby("season")["delta"].mean()
    assert len(delta) == 19
    np.testing.assert_allclose(delta.loc[g_hat.index].to_numpy(), g_hat.to_numpy(), rtol=0, atol=1e-12)


def test_elo_diff_and_flags_match_predictor(real_frame):
    """Differenziale Elo e flag coincidono con predict_elo_fast sulla validazione."""
    data, frame = real_frame
    preds = generate_validation_predictions(data.df, ELO_FITS, data.schedule)
    merged = frame.merge(preds, on=["season", "Date", "HomeTeam", "AwayTeam"], suffixes=("", "_pred"))
    assert len(merged) == 7220
    np.testing.assert_allclose(merged["elo_diff"], merged["delta_pred"], rtol=0, atol=1e-9)
    new = (merged["home_promotion"] == "new") | (merged["away_promotion"] == "new")
    ret = (merged["home_promotion"] == "returning") | (merged["away_promotion"] == "returning")
    assert (new.astype(int) == merged["flag_new"]).all()
    assert (ret.astype(int) == merged["flag_returning"]).all()


def test_covariates_do_not_depend_on_same_or_later_dates(real_frame):
    """Anti-leakage: esiti e dati dalla data della partita in poi non cambiano le sue covariate.

    Mutante: si invertono gli esiti di tutte le partite con Date >= D (bersaglio compreso) e
    si alzano del 10% le quote di tutte quelle con Date >= D tranne il bersaglio; le
    covariate del bersaglio e di tutte le partite anteriori restano identiche.
    """
    data, frame = real_frame
    target = frame[(frame["season"] == "2015-16") & (frame["position"] == 200)].iloc[0]
    d = target["Date"]
    raw = data.df.copy()
    later = raw["Date"] >= d
    swap = {"H": "A", "A": "H", "D": "H"}
    raw.loc[later, "FTR"] = raw.loc[later, "FTR"].map(swap)
    raw.loc[later, ["FTHG", "FTAG"]] = raw.loc[later, ["FTAG", "FTHG"]].to_numpy()
    raw.loc[later & (raw["FTR"] == "H") & (raw["FTHG"] <= raw["FTAG"]), "FTHG"] = raw["FTAG"] + 1
    is_target = (
        (raw["season"] == target["season"]) & (raw["Date"] == d)
        & (raw["HomeTeam"] == target["HomeTeam"]) & (raw["AwayTeam"] == target["AwayTeam"])
    )
    assert int(is_target.sum()) == 1
    odds_cols = [c for c in ("B365H", "B365D", "B365A", "SBH", "SBD", "SBA") if c in raw.columns]
    bump = later & ~is_target
    raw.loc[bump, odds_cols] = raw.loc[bump, odds_cols].apply(pd.to_numeric, errors="coerce") * 1.1

    mutated = build_module2_frame(
        ModelResidualsData(raw, data.schedule, compute_model_residuals(raw, data.schedule, ELO_FITS)),
        triple_2000_01="SB",
    )
    key = ["season", "Date", "HomeTeam", "AwayTeam"]
    both = frame.merge(mutated, on=key, suffixes=("", "_mut"))
    earlier_or_target = (both["Date"] < d) | (
        (both["Date"] == d) & (both["HomeTeam"] == target["HomeTeam"]) & (both["AwayTeam"] == target["AwayTeam"])
    )
    for col in COVARIATE_COLUMNS:
        sel = both[earlier_or_target]
        assert (sel[col] == sel[f"{col}_mut"]).all(), col
    # Il mutante ha effetto: dopo D cambiano rating e quote
    after = both[both["Date"] > d]
    assert (after["elo_diff"] != after["elo_diff_mut"]).any()
    assert (after["log_odds_ratio"] != after["log_odds_ratio_mut"]).any()
    tgt = both[earlier_or_target & (both["Date"] == d)]
    assert (tgt["delta"] != tgt["delta_mut"]).all()
