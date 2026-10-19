"""Test: griglie, regola di scelta, agente D con q condivise, loader dei parametri congelati."""

import csv
import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shk.kelly.environment import run_paired_backtest
from shk.kelly.staking import KAPPA_GRID
from shk.model.covariate_inspection import MODULE2_WINDOWS
from shk.model.frozen_params import (
    FROZEN_PARAMS_PATH,
    SECTION_KEYS,
    check_keys,
    load_frozen_params,
    render_frozen_params,
    write_frozen_params,
)
from shk.model.module3_synthetic import SEED_S9
from shk.model.stateful_agents import SERIES_DELTA, BaselineDAgent
from shk.model.training_calibration import (
    CALIBRATION_LOG_COLUMNS,
    TIE_RULE_NOTE,
    Combination,
    SharedShin,
    SharedShinBaselineDAgent,
    calibration_grid,
    finalize_log,
    select_combinations,
    spawn_t54_generators,
)
from shk.stats.drift import (
    ADWIN_DELTA,
    ADWIN_GRID_DELTA,
    PAGE_HINKLEY_DELTA,
    PAGE_HINKLEY_GRID_DELTA,
    PAGE_HINKLEY_GRID_THRESHOLD,
    PAGE_HINKLEY_THRESHOLD,
    detector_params,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = REPO_ROOT / "results" / "us_c8_2_calibration_log.csv"
GRID_SIZES = {
    "C1": len(MODULE2_WINDOWS) * len(KAPPA_GRID),
    "C2_global": len(MODULE2_WINDOWS),
    "C2": len(MODULE2_WINDOWS),
    "D_ADWIN": len(ADWIN_GRID_DELTA) * len(KAPPA_GRID),
    "D_PH": len(PAGE_HINKLEY_GRID_DELTA) * len(PAGE_HINKLEY_GRID_THRESHOLD) * len(KAPPA_GRID),
}


def test_grid_is_complete_and_unique():
    grid = calibration_grid()
    assert {f: sum(1 for c in grid if c.family == f) for f in GRID_SIZES} == GRID_SIZES
    assert len({c.agent_name for c in grid}) == len(grid)


def _select_one(objectives, stakes, combos):
    return select_combinations({"C2": objectives}, {"C2": stakes}, {"C2": combos})["C2"]


def test_first_level_rule():
    """Massimo; parità entro 1e-12 → puntata media più bassa; poi ordine della griglia (senza κ né valori congelati)."""
    combos = [Combination("C2", i, w, None, None, None) for i, w in enumerate((40, 80, 120))]
    assert _select_one([0.1, 0.3, 0.2], [0.0, 0.5, 0.0], combos) == (1, "objective", [(0, 0)] * 3)
    assert _select_one([0.3, 0.3 - 5e-13, 0.1], [0.2, 0.1, 0.0], combos).index == 1
    assert _select_one([0.3, 0.3 - 5e-13, 0.1], [0.2, 0.1, 0.0], combos).chosen_by == "mean_stake"
    assert _select_one([0.3, 0.3, 0.3], [0.1, 0.1, 0.1], combos)[:2] == (0, "second_level_tie_rule")
    assert _select_one([0.3, 0.3 - 1e-9, 0.0], [0.2, 0.1, 0.0], combos).index == 0


def test_second_level_tie_rule():
    """Parità esatta: valore congelato (δ di ADWIN), poi κ dell'altro detector, poi di C1, altrimenti 1."""
    grid = calibration_grid()
    combos = {f: [c for c in grid if c.family == f] for f in ("C1", "D_ADWIN", "D_PH")}
    flat = {f: [0.0] * len(cs) for f, cs in combos.items()}
    stakes = {f: [0.1] * len(cs) for f, cs in combos.items()}
    # D_PH con un massimo unico a κ = 0.75, C1 con massimo unico a κ = 0.25
    objectives = dict(flat)
    objectives["D_PH"] = [1.0 if (c.kappa == 0.75 and c.detector_threshold == 1.0 and c.detector_delta == 0.005)
                          else 0.0 for c in combos["D_PH"]]
    objectives["C1"] = [1.0 if (c.kappa == 0.25 and c.window == 80) else 0.0 for c in combos["C1"]]
    sel = select_combinations(objectives, stakes, combos)
    c = combos["D_ADWIN"][sel["D_ADWIN"].index]
    assert (c.detector_delta, c.kappa, sel["D_ADWIN"].chosen_by) == (ADWIN_DELTA, 0.75, "second_level_tie_rule")
    # D_PH non identifica κ: si usa C1
    objectives["D_PH"] = list(flat["D_PH"])
    sel = select_combinations(objectives, stakes, combos)
    assert combos["D_ADWIN"][sel["D_ADWIN"].index].kappa == 0.25
    # Valori congelati di Page-Hinkley e κ di riserva da C1 (D_ADWIN non identifica κ)
    c = combos["D_PH"][sel["D_PH"].index]
    assert (c.detector_delta, c.detector_threshold, c.kappa) == (PAGE_HINKLEY_DELTA, PAGE_HINKLEY_THRESHOLD, 0.25)
    # Nessun riferimento identificato: κ = 1
    sel = select_combinations(flat, stakes, combos)
    assert combos["D_ADWIN"][sel["D_ADWIN"].index].kappa == 1.0
    # Senza parità esatta sulla puntata media la regola di secondo livello non interviene
    stakes_d = dict(stakes)
    stakes_d["D_ADWIN"] = [0.1 + 0.01 * i for i in range(len(combos["D_ADWIN"]))]
    sel = select_combinations(flat, stakes_d, combos)
    assert (sel["D_ADWIN"].index, sel["D_ADWIN"].chosen_by) == (0, "mean_stake")


def test_spawn_t54_generators_scheme():
    gens = spawn_t54_generators(["2000-01", "2010-11", "2020-21"], 3, SEED_S9)
    child = np.random.SeedSequence(SEED_S9).spawn(5)[4].spawn(3)[0].spawn(3)[2]
    assert gens["2000-01"][2].integers(0, 2**62) == np.random.default_rng(child).integers(0, 2**62)


def test_shared_shin_d_agent_matches_baseline_d():
    """Le q condivise non cambiano nulla: stesse ricchezze e stessi allarmi di BaselineDAgent."""
    rng = np.random.default_rng(4)
    n_dates, per_date = 60, 4
    n = n_dates * per_date
    dates = (np.datetime64("2010-08-14") + np.repeat(np.arange(n_dates), per_date) * np.timedelta64(7, "D")).astype("datetime64[ns]")
    probs = rng.dirichlet([4, 3, 3], size=n)
    odds = np.maximum(1.0 / (rng.dirichlet([4, 3, 3], size=n) * 1.06), 1.01)
    outcomes = np.array([rng.choice(3, p=p) for p in probs])[None, :]
    params = detector_params("page_hinkley")
    params["threshold"] = 1.0
    shin = SharedShin()
    agents = [BaselineDAgent("D", "page_hinkley", params, 0.5, series=SERIES_DELTA),
              SharedShinBaselineDAgent("D_shared", "page_hinkley", params, 0.5, shin),
              SharedShinBaselineDAgent("D_shared_2", "page_hinkley", dict(params), 0.25, shin)]
    runs = run_paired_backtest(agents, dates, probs, odds, outcomes, 0.0)
    np.testing.assert_array_equal(runs[1].wealth, runs[0].wealth)
    assert agents[0].n_alarms == agents[1].n_alarms == agents[2].n_alarms > 0


def _sections():
    return {
        s: {k: 1 for k in keys} for s, keys in SECTION_KEYS.items()
    }


def test_render_check_and_write_once(tmp_path):
    """Chiavi esatte; il file si scrive una volta sola e il loader lo rilegge."""
    text = render_frozen_params(datetime.date(2026, 10, 11), _sections(), {}, "intestazione")
    target = tmp_path / "frozen.toml"
    write_frozen_params(target, text)
    with pytest.raises(FileExistsError):
        write_frozen_params(target, text)
    params = load_frozen_params(target)
    assert params.frozen_on == datetime.date(2026, 10, 11)
    bad = _sections()
    bad["fixed"]["extra_key"] = 1
    with pytest.raises(ValueError):
        render_frozen_params(datetime.date(2026, 10, 11), bad, {}, "x")
    missing = _sections()
    del missing["calibrated"]["c1_window"]
    with pytest.raises(ValueError):
        check_keys({"frozen_on": datetime.date(2026, 10, 11), **missing})


def test_frozen_params_file_has_exactly_required_keys():
    """config/frozen_params.toml supera il test delle chiavi e il loader lo legge."""
    params = load_frozen_params(FROZEN_PARAMS_PATH)
    assert set(params.calibrated) == SECTION_KEYS["calibrated"]
    assert set(params.fixed) == SECTION_KEYS["fixed"]
    assert dict(params.not_calibrated_on_training) == {}
    assert params.adwin_params()["delta"] in ADWIN_GRID_DELTA
    assert params.page_hinkley_params()["threshold"] in PAGE_HINKLEY_GRID_THRESHOLD


def test_log_contains_every_combination_and_the_tie_rule():
    """Il log contiene tutte le combinazioni della griglia per ogni agente, comprese le scartate, e la regola."""
    log = pd.read_csv(LOG_PATH)
    assert tuple(log.columns) == CALIBRATION_LOG_COLUMNS
    combos = log[log["row_type"] == "combination"]
    grid = calibration_grid()
    assert sorted(combos["agent"]) == sorted(c.agent_name for c in grid)
    assert combos.groupby("family").size().to_dict() == GRID_SIZES
    rule = log[log["row_type"] == "rule"]
    assert len(rule) == 1 and rule["note"].iloc[0] == TIE_RULE_NOTE
    assert rule["note"].iloc[0].startswith("2026-10-11")


def test_d_adwin_exact_tie_and_second_level_choice():
    """(0.002, 0.75) è in parità esatta con il massimo (obiettivo e puntata media) ed è la scelta di D_ADWIN."""
    log = pd.read_csv(LOG_PATH)
    d = log[(log["row_type"] == "combination") & (log["family"] == "D_ADWIN")]
    best = d["objective"].max()
    target = d[(d["detector_delta"] == ADWIN_DELTA) & (d["kappa"] == 0.75)].iloc[0]
    exact = d[(best - d["objective"] <= 1e-12) & (d["mean_stake"] == d.loc[best - d["objective"] <= 1e-12, "mean_stake"].min())]
    assert len(exact) == 41
    assert target["objective"] == best and target["mean_stake"] == exact["mean_stake"].iloc[0]
    assert round(float(target["objective"]), 4) == -0.0082
    assert bool(target["chosen"]) and target["chosen_by"] == "second_level_tie_rule"
    text = FROZEN_PARAMS_PATH.read_text(encoding="utf-8")
    assert "il training non identifica né δ né κ" in text


def test_choice_follows_objective_on_log():
    """La scelta per agente segue meccanicamente l'obiettivo con la regola di parità e quella di secondo livello."""
    with open(LOG_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    recomputed = finalize_log(rows)
    for old, new in zip(rows, recomputed):
        for col in ("rank", "chosen", "on_grid_edge", "chosen_by"):
            assert old[col] == str(new[col]), (old["agent"], col)
    log = pd.read_csv(LOG_PATH)
    params = load_frozen_params(FROZEN_PARAMS_PATH)
    chosen = log[log["chosen"].astype(str) == "True"].set_index("family")
    assert params.calibrated["c1_window"] == chosen.loc["C1", "window"]
    assert params.calibrated["c1_kappa"] == chosen.loc["C1", "kappa"]
    assert params.calibrated["c2_global_window"] == chosen.loc["C2_global", "window"]
    assert params.calibrated["c2_window"] == chosen.loc["C2", "window"]
    assert params.calibrated["d_adwin_delta"] == chosen.loc["D_ADWIN", "detector_delta"]
    assert params.calibrated["d_adwin_kappa"] == chosen.loc["D_ADWIN", "kappa"]
    assert params.calibrated["d_page_hinkley_delta"] == chosen.loc["D_PH", "detector_delta"]
    assert params.calibrated["d_page_hinkley_threshold"] == chosen.loc["D_PH", "detector_threshold"]
    assert params.calibrated["d_page_hinkley_kappa"] == chosen.loc["D_PH", "kappa"]
