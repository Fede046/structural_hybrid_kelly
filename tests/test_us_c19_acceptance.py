"""Test: risultati sulle stagioni reali di validazione, dalle sintesi versionate."""

import math
from pathlib import Path

import pandas as pd

from shk.model.real_seasons import REAL_COLUMNS, REAL_SOURCES, all_real_records

RESULTS = Path(__file__).resolve().parents[1] / "results"
CSV_PATH = RESULTS / "us_c19_real_seasons.csv"


def test_csv_matches_versioned_summaries():
    df = pd.read_csv(CSV_PATH, dtype=str, keep_default_na=False)
    assert tuple(df.columns) == REAL_COLUMNS
    assert len(df) == 3 * sum(len(s.references) for s in REAL_SOURCES)
    fresh = pd.DataFrame(all_real_records(RESULTS)).astype(str).replace("nan", "")
    for col in ("source", "config", "agent", "reference", "seasons_better_real", "seasons_worse_real"):
        assert list(df[col]) == list(fresh[col]), col
    for col in ("typical_capital_real", "typical_capital_seeds"):
        assert all(math.isclose(float(a), float(b), rel_tol=1e-12) for a, b in zip(df[col], fresh[col])), col


def test_real_seasons_findings():
    df = pd.read_csv(CSV_PATH)
    main = df[df["config"] == "gbp_0.01"].set_index(["source", "agent"])
    # La stagione vera di B_0.25 è la stessa in tutte le esecuzioni sul modello congelato
    b = {main.loc[(s, "B_0.25"), "typical_capital_real"] for s in ("frozen", "scheme", "reference")}
    assert len({round(v, 12) for v in b}) == 1
    # Il Kelly pieno perde in tutte le stagioni reali
    assert main.loc[("frozen", "A"), "seasons_worse_real"] == 19
    # Il confronto con la stagione di calibrazione batte il quarto di Kelly in 14 stagioni reali su 19
    for agent in ("C3_ref", "C3_ref_stop"):
        assert main.loc[("reference", agent), "seasons_better_real"] == 14
        assert main.loc[("reference", agent), "typical_capital_real"] > main.loc[("reference", "B_0.25"), "typical_capital_real"]
    # Ricalibrare ogni anno peggiora anche sulle stagioni reali
    assert main.loc[("elo_refit", "B_0.25"), "typical_capital_real"] < main.loc[("reference", "B_0.25"), "typical_capital_real"]
