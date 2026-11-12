"""Test: inferenza appaiata sulle 19 stagioni vere (us_c24), dalle sintesi versionate."""

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shk.model.paired_inference import N_BOOT, PAIRED_COLUMNS, all_paired_records, paired_statistics
from shk.model.real_seasons import REAL_SOURCES

RESULTS = Path(__file__).resolve().parents[1] / "results"
CSV_PATH = RESULTS / "us_c24_paired_inference.csv"
REAL_CSV = RESULTS / "us_c19_real_seasons.csv"


def test_paired_statistics_on_a_known_example():
    rng = np.random.default_rng(0)
    x = np.log([1.2, 1.1, 0.9, 1.3, 1.0])
    y = np.zeros(5)
    out = paired_statistics(x, y, rng, n_boot=999)
    assert (out["seasons_better"], out["seasons_worse"]) == (3, 1)
    assert out["sign_test_p"] == pytest.approx(0.625)  # 2 · P(X >= 3), X ~ Bin(4, 1/2)
    assert out["capital_ratio"] == pytest.approx(math.exp(x.mean()))
    assert out["capital_ratio_low"] <= out["capital_ratio"] <= out["capital_ratio_high"]


def test_paired_statistics_with_a_ruined_season():
    out = paired_statistics(np.array([-math.inf, -0.5, -0.2]), np.array([-0.1, -0.4, -0.3]),
                            np.random.default_rng(0), n_boot=99)
    assert (out["seasons_better"], out["seasons_worse"]) == (1, 2)
    assert math.isnan(out["capital_ratio"]) and math.isnan(out["wilcoxon_p"])
    with pytest.raises(ValueError):
        paired_statistics(np.zeros(3), np.zeros(4), np.random.default_rng(0))


def test_csv_matches_versioned_summaries():
    df = pd.read_csv(CSV_PATH)
    assert tuple(df.columns) == PAIRED_COLUMNS
    assert len(df) == 3 * sum(sum(a != r for a, r in s.references.items()) for s in REAL_SOURCES)
    assert (df["n_boot"] == N_BOOT).all()
    fresh = pd.DataFrame(all_paired_records(RESULTS))
    for col in ("source", "config", "agent", "reference", "seasons_better", "seasons_worse"):
        assert list(df[col]) == list(fresh[col]), col
    for col in ("sign_test_p", "wilcoxon_p", "capital_ratio", "capital_ratio_low", "capital_ratio_high"):
        assert np.allclose(df[col], fresh[col], rtol=1e-12, atol=0, equal_nan=True), col


def test_counts_match_real_seasons():
    mine = pd.read_csv(CSV_PATH).set_index(["source", "config", "agent"])
    real = pd.read_csv(REAL_CSV).set_index(["source", "config", "agent"]).loc[mine.index]
    assert (mine["seasons_better"] == real["seasons_better_real"]).all()
    assert (mine["seasons_worse"] == real["seasons_worse_real"]).all()


def test_findings():
    main = pd.read_csv(CSV_PATH)
    main = main[main["config"] == "gbp_0.01"].set_index(["source", "agent"])
    row = main.loc[("reference", "C3_ref_stop")]
    # 14 stagioni su 19: al limite per il test dei segni, significativo per Wilcoxon e per l'intervallo
    assert (row["seasons_better"], row["seasons_worse"]) == (14, 5)
    assert 0.05 < row["sign_test_p"] < 0.10
    assert row["wilcoxon_p"] < 0.05
    assert 1.0 < row["capital_ratio_low"] < row["capital_ratio"] < row["capital_ratio_high"]
    # Il confronto con le 40 partite precedenti, senza stop, non si distingue dal quarto di Kelly
    assert main.loc[("scheme", "C3"), "sign_test_p"] > 0.10
    # Il Kelly pieno perde contro il quarto di Kelly in ogni stagione
    assert main.loc[("frozen", "A"), "seasons_worse"] == 19
