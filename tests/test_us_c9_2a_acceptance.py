"""Test di T61 (US-C9.2): seed per Modulo 1, schema del file di Dixon-Coles, DataFrame del Modulo 2,
file di congelamento e log della calibrazione con Dixon-Coles."""

import csv
import datetime
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.kelly.staking import KAPPA_GRID
from shk.model.covariate_inspection import MODULE2_WINDOWS
from shk.model.frozen_params import (
    FROZEN_PARAMS_DC_PATH,
    MODULE1_KEY,
    SECTION_KEYS,
    check_keys,
    load_frozen_params,
    render_frozen_params,
    write_frozen_params,
)
from shk.model.module1 import MODULE1_DIXON_COLES, MODULE1_ELO
from shk.model.module1_seeds import procedure_seeds, t61_sequences
from shk.model.module2_data import (
    MODULE2_FRAME_COLUMNS,
    build_module2_frame,
    module2_frame_columns,
    strength_covariate,
    with_strength,
)
from shk.model.module3_synthetic import SEED_S9
from shk.model.residuals import RATE_COLUMNS, load_model_residuals
from shk.model.task_seeds import task_sequence
from shk.model.training_calibration import CALIBRATION_LOG_COLUMNS, TIE_RULE_NOTE, calibration_grid, finalize_log
from shk.stats.drift import ADWIN_GRID_DELTA, PAGE_HINKLEY_GRID_THRESHOLD
from shk.stats.oaxaca_synthetic import SEED_S8

REPO_ROOT = Path(__file__).resolve().parents[1]
DC_LOG_PATH = REPO_ROOT / "results" / "us_c9_2a_calibration_log_dc.csv"
GRID_SIZES = {
    "C1": len(MODULE2_WINDOWS) * len(KAPPA_GRID),
    "C2_global": len(MODULE2_WINDOWS),
    "C2": len(MODULE2_WINDOWS),
}


def _has_real_data() -> bool:
    return DEFAULT_DATA_DIR.is_dir() and any(DEFAULT_DATA_DIR.glob("*.csv"))


def test_task_sequence_int_and_seed_sequence():
    """Con un intero la sequenza del task di sempre; con una SeedSequence una copia nuova, ripetibile."""
    a = task_sequence(SEED_S9, 3).generate_state(4)
    assert np.array_equal(a, np.random.SeedSequence(SEED_S9).spawn(5)[3].generate_state(4))
    given = np.random.SeedSequence(20261015).spawn(5)[2].spawn(5)[3]
    first = task_sequence(given, 3).spawn(2)[1].generate_state(4)
    second = task_sequence(given, 3).spawn(2)[1].generate_state(4)
    assert np.array_equal(first, second)
    assert np.array_equal(first, given.spawn(2)[1].generate_state(4))
    with pytest.raises(TypeError, match="seed must be an integer or a SeedSequence"):
        task_sequence(True, 0)
    with pytest.raises(TypeError, match="seed must be an integer or a SeedSequence"):
        task_sequence("1", 0)


def test_procedure_seeds_by_module1():
    """Elo: i seed interi di S8 e S9; Dixon-Coles: i figli di SeedSequence(SEED_S11).spawn(5)[2]."""
    assert procedure_seeds(MODULE1_ELO) == {"t46": SEED_S8, "t47": SEED_S8, "t52": SEED_S9, "t53": SEED_S9,
                                            "t54": SEED_S9}
    dc = procedure_seeds(MODULE1_DIXON_COLES)
    assert [s.spawn_key for s in dc.values()] == [(2, k) for k in range(5)]
    assert all(s.entropy == 20261015 for s in dc.values())
    assert list(dc) == list(t61_sequences())


def test_strength_covariate_names():
    """Elo: elo_diff; Dixon-Coles: lambda_diff al suo posto, stesse altre colonne."""
    assert module2_frame_columns(MODULE1_ELO) == MODULE2_FRAME_COLUMNS
    dc = module2_frame_columns(MODULE1_DIXON_COLES)
    assert "lambda_diff" in dc and "elo_diff" not in dc
    assert dc.index("lambda_diff") == MODULE2_FRAME_COLUMNS.index("elo_diff")
    assert with_strength(("a", "elo_diff", "b"), "lambda_diff") == ("a", "lambda_diff", "b")
    assert strength_covariate(pd.DataFrame(columns=["elo_diff"])) == "elo_diff"
    assert strength_covariate(pd.DataFrame(columns=["lambda_diff"])) == "lambda_diff"


def _sections():
    return {s: {k: 1 for k in keys} for s, keys in SECTION_KEYS.items()}


def test_render_and_load_with_module1_key(tmp_path):
    """Stesse chiavi più module1 = "dixon_coles"; module1 = "elo" o sconosciuto rifiutati."""
    text = render_frozen_params(datetime.date(2026, 10, 17), _sections(), {}, "intestazione",
                                module1=MODULE1_DIXON_COLES)
    assert 'module1 = "dixon_coles"' in text
    target = tmp_path / "frozen_dc.toml"
    write_frozen_params(target, text)
    assert load_frozen_params(target).module1 == MODULE1_DIXON_COLES
    for bad in (MODULE1_ELO, "poisson"):
        with pytest.raises(ValueError, match="module1"):
            check_keys({"frozen_on": datetime.date(2026, 10, 17), MODULE1_KEY: bad, **_sections()})
    # La chiave di primo livello manca nel file dell'Elo (fixed.module1 è un'altra chiave)
    elo_text = render_frozen_params(datetime.date(2026, 10, 17), _sections(), {}, "intestazione")
    assert MODULE1_KEY not in elo_text.split("[sources]")[0]
    assert MODULE1_KEY in text.split("[sources]")[0]


@pytest.mark.slow
def test_dixon_coles_module2_frame_uses_expected_goals():
    """Dati reali (slow): con Dixon-Coles lambda_diff = λ − μ delle stesse previsioni, nessuna colonna Elo."""
    if not _has_real_data():
        pytest.skip(f"Real data missing: no CSV in {DEFAULT_DATA_DIR}")
    data = load_model_residuals(module1=MODULE1_DIXON_COLES)
    assert list(data.rates.columns) == list(RATE_COLUMNS)
    assert data.rates.index.equals(data.residuals.index)
    frame = build_module2_frame(data)
    assert tuple(frame.columns) == module2_frame_columns(MODULE1_DIXON_COLES)
    res = data.residuals.join(data.rates)
    keys = ["season", "Date", "HomeTeam", "AwayTeam", "fit_through", "role"]
    merged = frame[keys + ["lambda_diff"]].merge(res[keys + list(RATE_COLUMNS)], on=keys, how="left")
    assert np.allclose(merged["lambda_diff"], merged["lambda_home"] - merged["lambda_away"], rtol=0.0, atol=1e-15)
    assert (merged[list(RATE_COLUMNS)] > 0.0).all().all()


def test_frozen_params_dc_file_has_exactly_required_keys():
    """config/frozen_params_dc.toml supera il test delle chiavi, con module1 = "dixon_coles"."""
    if not FROZEN_PARAMS_DC_PATH.exists():
        pytest.skip(f"Missing {FROZEN_PARAMS_DC_PATH}: run scripts/us_c8_2_calibration.py --module1 dixon_coles")
    params = load_frozen_params(FROZEN_PARAMS_DC_PATH)
    assert params.module1 == MODULE1_DIXON_COLES
    assert set(params.calibrated) == SECTION_KEYS["calibrated"]
    assert set(params.fixed) == SECTION_KEYS["fixed"]
    assert dict(params.not_calibrated_on_training) == {}
    assert params.adwin_params()["delta"] in ADWIN_GRID_DELTA
    assert params.page_hinkley_params()["threshold"] in PAGE_HINKLEY_GRID_THRESHOLD
    assert params.calibration["log_csv"] == "results/us_c9_2a_calibration_log_dc.csv"
    assert params.calibration["log_sha256"] == hashlib.sha256(DC_LOG_PATH.read_bytes()).hexdigest()


def test_dc_log_contains_every_combination_and_choices_follow_the_rule():
    """Log di Dixon-Coles: tutte le combinazioni, la regola, e scelte che la regola riproduce."""
    if not DC_LOG_PATH.exists():
        pytest.skip(f"Missing {DC_LOG_PATH}: run scripts/us_c8_2_calibration.py --module1 dixon_coles")
    log = pd.read_csv(DC_LOG_PATH)
    assert tuple(log.columns) == CALIBRATION_LOG_COLUMNS
    combos = log[log["row_type"] == "combination"]
    assert sorted(combos["agent"]) == sorted(c.agent_name for c in calibration_grid())
    sizes = combos.groupby("family").size().to_dict()
    assert all(sizes[f] == n for f, n in GRID_SIZES.items())
    rule = log[log["row_type"] == "rule"]
    assert len(rule) == 1 and rule["note"].iloc[0] == TIE_RULE_NOTE
    assert combos.groupby("family")["chosen"].sum().eq(1).all()
    with open(DC_LOG_PATH, newline="", encoding="utf-8") as f:
        again = finalize_log(list(csv.DictReader(f)))
    chosen_again = sorted(r["agent"] for r in again if r["chosen"] is True)
    assert chosen_again == sorted(combos.loc[combos["chosen"], "agent"])
    if FROZEN_PARAMS_DC_PATH.exists():
        params = load_frozen_params(FROZEN_PARAMS_DC_PATH)
        chosen = combos[combos["chosen"]].set_index("family")
        assert params.calibrated["c1_window"] == int(chosen.loc["C1", "window"])
        assert params.calibrated["c2_window"] == int(chosen.loc["C2", "window"])
        assert params.calibrated["c2_global_window"] == int(chosen.loc["C2_global", "window"])
        assert params.calibrated["d_adwin_delta"] == float(chosen.loc["D_ADWIN", "detector_delta"])
