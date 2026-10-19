"""Test di src/shk/model/season_objectives.py: flag "senza obiettivi"."""

import numpy as np
import pandas as pd
import pytest

import shk.model.season_objectives as season_objectives
from shk.data.loading import DEFAULT_DATA_DIR
from shk.model.season_objectives import no_objective_flags


def _round_robin_season(seed: int, n_teams: int = 20, season: str = "2005-06") -> pd.DataFrame:
    """Doppio girone all'italiana (metodo del cerchio), una data per giornata, forze diverse."""
    rng = np.random.default_rng(seed)
    teams = [f"T{i:02d}" for i in range(n_teams)]
    strength = np.linspace(1.5, -1.5, n_teams)
    rounds = []
    order = list(range(n_teams))
    for _ in range(n_teams - 1):
        pairs = [(order[i], order[n_teams - 1 - i]) for i in range(n_teams // 2)]
        rounds.append(pairs)
        order = [order[0]] + [order[-1]] + order[1:-1]
    rounds = rounds + [[(b, a) for a, b in r] for r in rounds]
    rows = []
    start = pd.Timestamp(f"{season[:4]}-08-15")
    for r, pairs in enumerate(rounds):
        for h, a in pairs:
            diff = strength[h] - strength[a] + 0.3
            p_h = 1 / (1 + np.exp(-diff)) * 0.75
            p_a = (1 - 1 / (1 + np.exp(-diff))) * 0.75
            u = rng.random()
            ftr = "H" if u < p_h else ("A" if u < p_h + p_a else "D")
            rows.append((season, start + pd.Timedelta(days=7 * r), teams[h], teams[a], ftr))
    return pd.DataFrame(rows, columns=["season", "Date", "HomeTeam", "AwayTeam", "FTR"])


def _brute_force(matches: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Definizione diretta, partita per partita, con cicli espliciti."""
    pts = {"H": (3, 0), "D": (1, 1), "A": (0, 3)}
    fh, fa = [], []
    for _, m in matches.iterrows():
        season = matches[matches["season"] == m["season"]]
        teams = sorted(set(season["HomeTeam"]) | set(season["AwayTeam"]))
        prior = season[season["Date"] < m["Date"]]
        points = {t: 0 for t in teams}
        played = {t: 0 for t in teams}
        for _, p in prior.iterrows():
            points[p["HomeTeam"]] += pts[p["FTR"]][0]
            points[p["AwayTeam"]] += pts[p["FTR"]][1]
            played[p["HomeTeam"]] += 1
            played[p["AwayTeam"]] += 1
        max_pts = {t: points[t] + 3 * (2 * (len(teams) - 1) - played[t]) for t in teams}

        def no_obj(t):
            safe = sum(max_pts[o] < points[t] for o in teams if o != t) >= 3
            out_of_top = sum(points[o] > max_pts[t] for o in teams if o != t) >= 4
            return int(safe and out_of_top)

        fh.append(no_obj(m["HomeTeam"]))
        fa.append(no_obj(m["AwayTeam"]))
    return np.array(fh), np.array(fa)


def test_flags_match_brute_force():
    """La versione vettorizzata coincide con la definizione diretta su una stagione sintetica."""
    season = _round_robin_season(1)
    fh, fa = no_objective_flags(season)
    bh, ba = _brute_force(season)
    np.testing.assert_array_equal(fh, bh)
    np.testing.assert_array_equal(fa, ba)
    assert fh.sum() + fa.sum() > 0
    early = season["Date"] < season["Date"].unique()[25]
    assert fh[early.to_numpy()].sum() + fa[early.to_numpy()].sum() == 0


def _swap_results_from(matches: pd.DataFrame, d: pd.Timestamp) -> pd.DataFrame:
    mut = matches.copy()
    later = mut["Date"] >= d
    mut.loc[later, "FTR"] = mut.loc[later, "FTR"].map({"H": "A", "A": "H", "D": "H"})
    return mut


def test_flags_use_only_strictly_earlier_results(monkeypatch):
    """Mutante: cambiare i risultati dalla data D in poi non cambia i flag delle partite fino a D.

    Con l'anteriorità non stretta (Date <= D) lo stesso controllo rileva differenze.
    """
    season = _round_robin_season(2)
    dates = season["Date"].unique()
    base_h, base_a = no_objective_flags(season)
    for d in dates[28:]:
        mut_h, mut_a = no_objective_flags(_swap_results_from(season, d))
        upto = (season["Date"] <= d).to_numpy()
        np.testing.assert_array_equal(mut_h[upto], base_h[upto])
        np.testing.assert_array_equal(mut_a[upto], base_a[upto])

    monkeypatch.setattr(season_objectives, "prior_results_mask", lambda ds, dd: ds <= dd)
    leak_h, leak_a = no_objective_flags(season)
    detected = 0
    for d in dates[28:]:
        mut_h, mut_a = no_objective_flags(_swap_results_from(season, d))
        today = (season["Date"] == d).to_numpy()
        if not (np.array_equal(mut_h[today], leak_h[today]) and np.array_equal(mut_a[today], leak_a[today])):
            detected += 1
    assert detected >= 1


def test_validation_errors():
    with pytest.raises(ValueError, match="Column 'FTR' not found"):
        no_objective_flags(pd.DataFrame({"season": [], "Date": [], "HomeTeam": [], "AwayTeam": []}))
    bad = _round_robin_season(3).iloc[:5].assign(FTR="X")
    with pytest.raises(ValueError, match="H, D, A"):
        no_objective_flags(bad)


@pytest.mark.skipif(not (DEFAULT_DATA_DIR.is_dir() and any(DEFAULT_DATA_DIR.glob("*.csv"))),
                    reason="Real data missing in data/raw/E0/")
def test_real_data_mutant_last_weeks():
    """Dati reali, 2015-16: mutando i risultati da D in poi i flag fino a D non cambiano."""
    from shk.data.split import load_by_role

    season = load_by_role("validation")
    season = season[season["season"] == "2015-16"].reset_index(drop=True)
    base_h, base_a = no_objective_flags(season)
    assert base_h.sum() + base_a.sum() > 0
    for d in season["Date"].unique()[-15::3]:
        mut_h, mut_a = no_objective_flags(_swap_results_from(season, d))
        upto = (season["Date"] <= d).to_numpy()
        np.testing.assert_array_equal(mut_h[upto], base_h[upto])
        np.testing.assert_array_equal(mut_a[upto], base_a[upto])
