"""Test: Flusso 1 con il Modulo 1 come parametro (identificatori, suffissi, catena comune)."""

import datetime
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.data.split import load_by_role, read_split_config
from shk.model.dixon_coles import DixonColesFitParams
from shk.model.elo_fit import ELO_FITS, EloFitParams, derive_fit_schedule
from shk.model.frozen_params import FROZEN_PARAMS_DC_PATH, FROZEN_PARAMS_PATH, frozen_params_path
from shk.model.module1 import (
    MODULE1_DIXON_COLES,
    MODULE1_ELO,
    check_module1,
    module1_from_argv,
    module1_suffix,
    with_module1_suffix,
)
from shk.model.residuals import (
    RESIDUALS_COLUMNS,
    compute_model_residuals,
    load_match_frame,
    load_model_residuals,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
T59_CSV = REPO_ROOT / "results" / "us_c9_1_dixon_coles.csv"


def _has_real_data() -> bool:
    return DEFAULT_DATA_DIR.is_dir() and any(DEFAULT_DATA_DIR.glob("*.csv"))


def test_module1_identifiers_and_suffixes():
    """Identificatori validi, suffisso vuoto per l'Elo e "_dc" per Dixon-Coles."""
    assert check_module1("elo") == MODULE1_ELO
    assert check_module1("dixon_coles") == MODULE1_DIXON_COLES
    with pytest.raises(ValueError, match="Unknown Module 1"):
        check_module1("poisson")
    assert module1_suffix(MODULE1_ELO) == ""
    assert module1_suffix(MODULE1_DIXON_COLES) == "_dc"
    path = Path("results") / "us_c8_3_validation_summary.csv"
    assert with_module1_suffix(path, MODULE1_ELO) == path
    assert with_module1_suffix(path, MODULE1_DIXON_COLES) == Path("results") / "us_c8_3_validation_summary_dc.csv"
    assert with_module1_suffix("raw/x.npz", MODULE1_DIXON_COLES) == Path("raw/x_dc.npz")


def test_module1_from_argv():
    """Opzione --module1 degli script: assente → Elo; valore controllato."""
    assert module1_from_argv([]) == MODULE1_ELO
    assert module1_from_argv(["--from-raw"]) == MODULE1_ELO
    assert module1_from_argv(["--from-raw", "--module1", "dixon_coles"]) == MODULE1_DIXON_COLES
    with pytest.raises(ValueError, match="requires a value"):
        module1_from_argv(["--module1"])
    with pytest.raises(ValueError, match="Unknown Module 1"):
        module1_from_argv(["--module1", "dc"])


def test_frozen_params_path_by_module1():
    """File di congelamento: frozen_params.toml per l'Elo, frozen_params_dc.toml per Dixon-Coles."""
    assert frozen_params_path() == FROZEN_PARAMS_PATH
    assert frozen_params_path(MODULE1_ELO) == FROZEN_PARAMS_PATH
    assert frozen_params_path(MODULE1_DIXON_COLES) == FROZEN_PARAMS_DC_PATH
    assert FROZEN_PARAMS_DC_PATH.name == "frozen_params_dc.toml"


def _synthetic_league(n_seasons: int = 3, n_teams: int = 6, seed: int = 7) -> pd.DataFrame:
    """Campionati a girone doppio con le stesse squadre, gol Poisson, una giornata a settimana."""
    rng = np.random.default_rng(seed)
    teams = [f"T{i}" for i in range(n_teams)]
    rows = []
    for k in range(n_seasons):
        year = 2001 + k
        day = datetime.date(year, 8, 1)
        order = list(teams)
        rounds = []
        for _ in range(n_teams - 1):
            rounds.append([(order[i], order[n_teams - 1 - i]) for i in range(n_teams // 2)])
            order = [order[0]] + [order[-1]] + order[1:-1]
        rounds += [[(b, a) for a, b in r] for r in rounds]
        for r in rounds:
            for h, a in r:
                hg, ag = int(rng.poisson(1.5)), int(rng.poisson(1.1))
                rows.append({"Date": pd.Timestamp(day), "season": f"{year}-{(year + 1) % 100:02d}", "HomeTeam": h,
                             "AwayTeam": a, "FTHG": hg, "FTAG": ag,
                             "FTR": "H" if hg > ag else ("D" if hg == ag else "A")})
            day += datetime.timedelta(days=7)
    return pd.DataFrame(rows)


def test_dixon_coles_residuals_have_elo_schema():
    """Su dati sintetici: con "dixon_coles" stesse colonne, tipi e partite della versione "elo"."""
    df = _synthetic_league()
    schedule = {"2002-03": {"training": ["2002-03"], "validation": ["2003-04"]}}
    elo = compute_model_residuals(df, schedule, {"2002-03": EloFitParams(k=20.0, h=60.0, nu=0.8, c=0.27)})
    dc = compute_model_residuals(df, schedule, {"2002-03": DixonColesFitParams(xi=0.003, sigma=0.4)},
                                 module1=MODULE1_DIXON_COLES)
    assert list(elo.columns) == list(dc.columns) == list(RESIDUALS_COLUMNS)
    assert (elo.dtypes == dc.dtypes).all()
    keys = ["fit_through", "role", "season", "Date", "HomeTeam", "AwayTeam", "FTR"]
    assert elo[keys].equals(dc[keys])
    assert np.isfinite(dc["log_loss"]).all()
    assert np.allclose(dc[["p_home", "p_draw", "p_away"]].sum(axis=1), 1.0, atol=1e-12)
    with pytest.raises(ValueError, match="Unknown Module 1"):
        compute_model_residuals(df, schedule, module1="poisson")


def test_load_match_frame_and_elo_chain_match_copied_sequence():
    """Dati reali: la catena comune con l'Elo coincide con la sequenza che gli script copiavano."""
    if not _has_real_data():
        pytest.skip(f"Real data missing: no CSV in {DEFAULT_DATA_DIR}")
    cfg = read_split_config()
    df = pd.concat([load_by_role("history"), load_by_role("training"), load_by_role("validation")],
                   ignore_index=True)
    df = df.sort_values("Date", kind="stable").reset_index(drop=True)
    schedule = derive_fit_schedule(cfg)
    expected = compute_model_residuals(df, schedule, ELO_FITS)

    frame, frame_schedule = load_match_frame()
    pd.testing.assert_frame_equal(frame, df)
    assert frame_schedule == schedule
    data = load_model_residuals()
    assert data.module1 == MODULE1_ELO
    pd.testing.assert_frame_equal(data.df, df)
    pd.testing.assert_frame_equal(data.residuals, expected)


@pytest.mark.slow
def test_dixon_coles_chain_on_real_data_matches_t59():
    """Dati reali (slow, circa 80 s): schema dell'Elo e log-loss di validazione uguale al CSV del Dixon-Coles walk-forward."""
    if not _has_real_data():
        pytest.skip(f"Real data missing: no CSV in {DEFAULT_DATA_DIR}")
    if not T59_CSV.exists():
        pytest.skip(f"Missing {T59_CSV}")
    elo = load_model_residuals()
    dc = load_model_residuals(module1=MODULE1_DIXON_COLES)
    assert dc.module1 == MODULE1_DIXON_COLES
    assert list(dc.residuals.columns) == list(elo.residuals.columns)
    assert (dc.residuals.dtypes == elo.residuals.dtypes).all()
    keys = ["fit_through", "role", "season", "Date", "HomeTeam", "AwayTeam", "FTR"]
    assert dc.residuals[keys].equals(elo.residuals[keys])
    t59 = pd.read_csv(T59_CSV)
    pooled = t59[(t59["row_type"] == "validation") & (t59["season"] == "pooled") & (t59["model"] == "dixon_coles")
                 & t59["method"].isna()]["log_loss"].iloc[0]
    val = dc.residuals[dc.residuals["role"] == "validation"]["log_loss"].mean()
    assert math.isclose(float(val), float(pooled), rel_tol=0.0, abs_tol=1e-12)
