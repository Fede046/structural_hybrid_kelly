"""Test di T55: agenti dal solo loader, supervisore con storia, uscite per seed e sintesi."""

import dataclasses
import math
from pathlib import Path
from types import MappingProxyType

import numpy as np
import pandas as pd
import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.kelly.agents import DateResults
from shk.model.agent_c import C1Agent, Module2Supervisor
from shk.model.training_agents import SeasonInput
from shk.model.frozen_agents import (
    AGENT_ORDER,
    RecordingDAgent,
    arm_windows,
    build_frozen_agents,
    build_supervisors,
    check_frozen_constants,
)
from shk.model.frozen_params import load_frozen_params
from shk.model.module2 import STATE_ACTIVE, module2_at_date, prepare_module2_data
from shk.model.module2_data import build_module2_frame
from shk.model.residuals import load_model_residuals
from shk.model.training_calibration import SharedShin
from shk.model.validation_run import (
    METRICS,
    SEED_S10,
    SUMMARY_COLUMNS,
    certainty_equivalent,
    chain_history,
    inactive_counts,
    load_raw,
    spawn_t55_sequences,
    validation_inputs,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = REPO_ROOT / "results" / "raw" / "us_c8_3_validation_raw.npz"
SUMMARY_PATH = REPO_ROOT / "results" / "us_c8_3_validation_summary.csv"
C62_PATH = REPO_ROOT / "results" / "us_c6_2_paired_backtest.csv"


def _has_real_data() -> bool:
    return DEFAULT_DATA_DIR.is_dir() and any(DEFAULT_DATA_DIR.glob("*.csv"))


@pytest.fixture(scope="module")
def frame():
    if not _has_real_data():
        pytest.skip(f"Real data missing: no CSV in {DEFAULT_DATA_DIR}")
    return build_module2_frame(load_model_residuals())


def test_agents_built_only_from_frozen_params(frame):
    """Cambiare un valore del file cambia l'agente; le costanti interne sono confrontate col file."""
    params = load_frozen_params()
    check_frozen_constants(params)
    val = validation_inputs(frame, list(params.fixed["covariates"]))[0]
    sups = build_supervisors(params, val.inp)
    assert sorted(sups) == sorted(set(arm_windows(params).values()))
    agents = build_frozen_agents(params, 0.0, sups, SharedShin(), val.fit)
    assert [a.name for a in agents] == [a for a in AGENT_ORDER if a != "E"]
    changed = dict(params.calibrated)
    changed["c1_kappa"] = 0.123
    other = dataclasses.replace(params, calibrated=MappingProxyType(changed))
    c1 = [a for a in build_frozen_agents(other, 0.0, sups, SharedShin(), val.fit) if a.name == "C1"][0]
    assert isinstance(c1, C1Agent) and c1._kappa == 0.123
    d = [a for a in agents if a.name == "D_ADWIN"][0]
    assert isinstance(d, RecordingDAgent) and d._kappa == params.calibrated["d_adwin_kappa"]
    bad = dict(params.fixed)
    bad["inactive_lambda"] = 0.3
    with pytest.raises(ValueError):
        check_frozen_constants(dataclasses.replace(params, fixed=MappingProxyType(bad)))


def test_supervisor_with_history_matches_chain_module2(frame):
    """Con la storia della catena il supervisore riproduce module2_at_date sulla catena (decisione S8)."""
    params = load_frozen_params()
    covs = list(params.fixed["covariates"])
    s = [v for v in validation_inputs(frame, covs) if v.inp.season == "2003-04"][0]
    history = chain_history(frame, "2003-04", covs)
    w = 80
    sup = Module2Supervisor("2003-04", s.inp.dates, s.inp.x, covs, w, history=history)
    chain = frame[frame["season"].isin(["2002-03", "2003-04"])]
    ref = prepare_module2_data(chain, covs)
    n_active = 0
    for d in np.unique(s.inp.dates):
        st = sup.state_at(d)
        r = module2_at_date(ref, "2003-04", d, w)
        assert st.output.state == r.state
        if r.state == STATE_ACTIVE:
            n_active += 1
            assert abs(st.output.result.structural - r.result.structural) <= 1e-12
        rows = np.flatnonzero(s.inp.dates == d)
        sup.observe(DateResults(date=d, probs=s.inp.probs[rows], odds=s.inp.odds[rows], outcomes=s.inp.outcomes[:, rows]))
    assert n_active == np.unique(s.inp.dates).shape[0]


def test_inactive_counts_and_certainty_equivalent():
    dates = np.repeat(np.arange(5), 3).astype("datetime64[D]").astype("datetime64[ns]")
    x = np.column_stack([np.zeros(15), np.r_[np.ones(4), np.zeros(11)]])
    inp = SeasonInput("s", dates, np.zeros((15, 3)), np.ones((15, 3)), np.zeros((1, 15), int), x, np.zeros(15))
    # 2W = 6: le date con meno di 6 partite anteriori sono le prime 2, cioè 6 partite
    assert inactive_counts(inp, 3, ["c", "flag_promoted"]) == (6, 4, 4)
    assert inactive_counts(inp, 3, ["c", "flag_promoted"], history_rows=6) == (0, 4, 0)
    lw = np.log(np.array([1.2, 0.8, 1.0]))
    assert math.isclose(certainty_equivalent(lw, 10, 1.0), lw.mean() / 10)
    assert math.isclose(certainty_equivalent(lw, 10, 2.0), -math.log(np.mean(1 / np.exp(lw))) / 10)
    assert certainty_equivalent(np.r_[lw, -np.inf], 10, 5.0) == -math.inf


def test_spawn_t55_sequences_scheme():
    seqs = spawn_t55_sequences(19, 3, SEED_S10)
    child = np.random.SeedSequence(SEED_S10).spawn(5)[0].spawn(19)[7].spawn(3)[2]
    assert np.random.default_rng(seqs[7][2]).integers(0, 2**62) == np.random.default_rng(child).integers(0, 2**62)


def test_raw_file_seeds_and_c0_equals_b025():
    """Ogni agente ha N_SEEDS seed per stagione e configurazione; C0 = B_0.25 entro 1e-12 ovunque."""
    params = load_frozen_params()
    res = load_raw(RAW_PATH)
    n_seeds = int(params.fixed["n_seeds"])
    assert res.seeds.shape == (19, 3, len(AGENT_ORDER), len(METRICS), n_seeds)
    lw = METRICS.index("final_log_wealth")
    for ai, agent in enumerate(AGENT_ORDER):
        block = res.seeds[:, :, ai, lw]
        if agent == "E":
            assert np.all(np.isnan(block[:, 0])) and not np.any(np.isnan(block[:, 1:]))
        else:
            assert not np.any(np.isnan(block))
    b, c0 = AGENT_ORDER.index("B_0.25"), AGENT_ORDER.index("C0")
    for arr in (res.seeds, res.observed):
        diff = np.abs(arr[:, :, c0] - arr[:, :, b])
        assert np.nanmax(np.where(np.isinf(arr[:, :, b]), 0.0, diff)) <= 1e-12


def test_observed_b025_reproduces_c6_2():
    """Con F = 0, B_0.25 sulla realizzazione osservata riproduce C6.2 (−10.580 su 6 234 puntate)."""
    res = load_raw(RAW_PATH)
    c62 = pd.read_csv(C62_PATH)
    ref = c62[(c62["row_type"] == "summary") & (c62["config"] == "none") & (c62["agent"] == "B_0.25")].iloc[0]
    b = AGENT_ORDER.index("B_0.25")
    total = float(res.observed[:, 0, b, METRICS.index("final_log_wealth")].sum())
    bets = int(res.observed[:, 0, b, METRICS.index("n_bets")].sum())
    assert math.isclose(total, float(ref["sum_final_log_wealth"]), rel_tol=1e-12)
    assert bets == int(ref["n_bets"]) == 6234
    assert round(total, 3) == -10.580


def test_summary_csv_structure():
    df = pd.read_csv(SUMMARY_PATH)
    assert tuple(df.columns) == SUMMARY_COLUMNS
    summ = df[df["row_type"] == "summary"]
    assert len(summ) == 19 * (9 + 10 + 10)
    assert (summ["n_seeds"] == int(load_frozen_params().fixed["n_seeds"])).all()
    inactive = df[df["row_type"] == "module2_inactive"]
    assert len(inactive) == 19 * 3
