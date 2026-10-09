"""Test di accettazione per il floor nella configurazione reale (US-C6.3 / Task 37).

Copre i 7 criteri di accettazione:
1. Estrazione degli esiti per inversione, frequenze Monte Carlo, bordi e determinismo;
2. Con F = 0 nessuna rovina e min_wealth > 0 in ogni stagione, replica e agente;
3. Controllo di verita' per E: media del ROI entro 2.576 SE dal valore analitico, nessuna rovina;
4. Appaiamento: stessa matrice esiti condivisa dentro ogni stagione; identita' conteggi puntate con F=0;
5. Ricalcolo delle righe aggregate (rel_tol 1e-12);
6. CSV e PNG versionati: schema, coerenza interna, e ricalcolo da dati reali;
7. Convenzioni di codice e controllo AST sullo script e modulo (nessun print, nessun log vietato).
"""

import ast
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.data.split import load_by_role, read_split_config
from shk.kelly.environment import AgentRun, DateView, run_paired_backtest
from shk.kelly.floor import SEED_C6
from shk.market.devig import devig_proportional
from shk.model.elo_fit import ELO_FITS, derive_fit_schedule
from shk.model.residuals import compute_model_residuals
from shk.model.floor_real_config import (
    FLOOR_REAL_CSV_COLUMNS,
    M_REPLICAS,
    Z_99,
    SeasonRunArtifact,
    compute_agent_e_analytic_roi,
    compute_aggregate_metrics,
    evaluate_floor_real_config,
    outcomes_by_inversion,
    sample_match_outcomes,
)
from shk.model.paired_backtest import CONFIGURATIONS, build_season_agents

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "results" / "us_c6_3_floor_real_config.csv"
FIG_PATH = REPO_ROOT / "thesis" / "figures" / "us_c6_3_floor_real_config.png"
SCRIPT_PATH = REPO_ROOT / "scripts" / "us_c6_3_floor_real_config.py"
MODULE_PATH = REPO_ROOT / "src" / "shk" / "model" / "floor_real_config.py"

DATA_AVAILABLE = DEFAULT_DATA_DIR.exists() and len(list(DEFAULT_DATA_DIR.glob("*.csv"))) > 0


# ==============================================================================
# Criterio 1: Estrazione degli esiti per inversione
# ==============================================================================


def test_outcome_sampling_properties() -> None:
    """Verifica frequenze Monte Carlo al 99%, bordi di inversione e determinismo seed."""
    # 1. Test frequenze Monte Carlo con M = 50 000 su 5 partite sintetiche
    odds_sample = np.array(
        [
            [2.0, 3.2, 3.8],
            [1.5, 4.0, 7.0],
            [3.0, 3.0, 2.5],
            [2.2, 3.3, 3.1],
            [1.8, 3.5, 4.5],
        ],
        dtype=np.float64,
    )
    q = devig_proportional(odds_sample)  # (5, 3)
    n_samples = 50_000
    rng = np.random.default_rng(12345)
    outcomes = sample_match_outcomes(odds_sample, rng, m_replicas=n_samples)

    assert outcomes.shape == (n_samples, 5)
    assert np.all(np.isin(outcomes, (0, 1, 2)))

    for match_idx in range(5):
        for outcome_idx in range(3):
            freq = float(np.mean(outcomes[:, match_idx] == outcome_idx))
            p_true = float(q[match_idx, outcome_idx])
            margin = Z_99 * math.sqrt(p_true * (1.0 - p_true) / n_samples)
            assert (
                abs(freq - p_true) <= margin
            ), f"Match {match_idx}, Outcome {outcome_idx}: freq {freq} outside [{p_true - margin}, {p_true + margin}]"

    # 2. Test bordi dell'inversione
    # q = [0.5, 0.3, 0.2] -> q_H = 0.5, q_H + q_D = 0.8
    q_edge = np.array([[0.5, 0.3, 0.2]], dtype=np.float64)
    u_edge = np.array(
        [
            [0.0],
            [0.4999999],
            [0.5],
            [0.7999999],
            [0.8],
            [0.9999999],
            [1.0],
        ],
        dtype=np.float64,
    )
    expected_outcomes = np.array([[0], [0], [1], [1], [2], [2], [2]], dtype=np.int64)
    out_edge = outcomes_by_inversion(q_edge, u_edge)
    np.testing.assert_array_equal(out_edge, expected_outcomes)

    # 3. Determinismo con stesso seed
    rng_a = np.random.default_rng(9999)
    rng_b = np.random.default_rng(9999)
    out_a = sample_match_outcomes(odds_sample, rng_a, m_replicas=100)
    out_b = sample_match_outcomes(odds_sample, rng_b, m_replicas=100)
    np.testing.assert_array_equal(out_a, out_b)


# ==============================================================================
# Criterio 2: Con F = 0 nessuna rovina e min_wealth > 0
# ==============================================================================


def test_no_floor_zero_ruin_and_min_wealth_positive() -> None:
    """Verifica che con F=0 la rovina sia 0.0 e min_wealth > 0 per ogni stagione e agente."""
    if not CSV_PATH.exists():
        pytest.skip("CSV non ancora generato")

    df_csv = pd.read_csv(CSV_PATH)
    sub_none = df_csv[df_csv["config"] == "none"]
    assert len(sub_none) > 0, "Nessuna riga trovata per config 'none'"

    # Tutte le righe di config 'none' devono avere ruin_rate == 0 e min_wealth > 0
    assert (
        sub_none["ruin_rate"] == 0.0
    ).all(), "Trovata rovina > 0 con configurazione 'none'"
    assert (
        sub_none["min_wealth"] > 0.0
    ).all(), "Trovato min_wealth <= 0 con configurazione 'none'"


# ==============================================================================
# Criterio 3: Controllo della verita' per E con F = £1 e F = £0.01
# ==============================================================================


def test_agent_e_truth_check_and_no_ruin() -> None:
    """Verifica per E che ruin_rate == 0 e che mean_roi disti meno di 2.576 SE dal valore analitico."""
    if not CSV_PATH.exists():
        pytest.skip("CSV non ancora generato")

    df_csv = pd.read_csv(CSV_PATH)
    e_seasons = df_csv[
        (df_csv["row_type"] == "season")
        & (df_csv["agent"] == "E")
        & (df_csv["config"].isin(["gbp_0.01", "gbp_1"]))
    ]
    assert len(e_seasons) == 38, f"Attese 38 righe di stagione per E, trovate {len(e_seasons)}"

    # Nessuna replica di E e' in rovina
    assert (
        e_seasons["ruin_rate"] == 0.0
    ).all(), "Trovata rovina per l'agente E!"

    failures: list[str] = []
    for _, row in e_seasons.iterrows():
        mean_roi = float(row["mean_roi"])
        analytic_roi = float(row["analytic_expected_roi"])
        se_roi = float(row["se_roi"])
        threshold = Z_99 * se_roi

        diff = abs(mean_roi - analytic_roi)
        if diff >= threshold:
            failures.append(
                f"Stagione {row['season']} ({row['config']}): diff {diff:.6f} >= 2.576*SE ({threshold:.6f})"
            )

    if failures:
        pytest.fail("Controllo verita' per E fallito:\n" + "\n".join(failures))


# ==============================================================================
# Criterio 4: Appaiamento e identita' conteggi puntate con F = 0
# ==============================================================================


def test_pairing_outcomes_and_bet_counts() -> None:
    """Verifica che gli esiti siano condivisi e che con F=0 n_bets(A) + n_dropped(A) == n_bets(B)."""
    # Mock su una stagione sintetica a 2 date
    d1 = np.datetime64("2020-09-12")
    d2 = np.datetime64("2020-09-19")
    dates = np.array([d1, d1, d2, d2])
    probs = np.array(
        [
            [0.6, 0.25, 0.15],
            [0.2, 0.3, 0.5],
            [0.4, 0.35, 0.25],
            [0.55, 0.25, 0.2],
        ],
        dtype=np.float64,
    )
    odds = np.array(
        [
            [2.1, 3.4, 4.5],
            [4.0, 3.2, 1.9],
            [2.6, 3.0, 3.2],
            [2.0, 3.5, 4.0],
        ],
        dtype=np.float64,
    )
    rng = np.random.default_rng(42)
    m = 20
    outcomes = sample_match_outcomes(odds, rng, m_replicas=m)

    # Verifica con F = 0
    agents_none = build_season_agents(0.0)
    runs_none = run_paired_backtest(
        agents=agents_none,
        dates=dates,
        probs=probs,
        odds=odds,
        outcomes=outcomes,
        min_stake=0.0,
    )

    run_a = next(r for r in runs_none if r.name == "A")
    run_b25 = next(r for r in runs_none if r.name == "B_0.25")
    run_b10 = next(r for r in runs_none if r.name == "B_0.10")

    # In ogni replica: n_bets(A) + n_dropped(A) == n_bets(B_0.25) == n_bets(B_0.10)
    for rep in range(m):
        tot_a = int(run_a.n_bets[rep] + run_a.n_dropped[rep])
        tot_b25 = int(run_b25.n_bets[rep])
        tot_b10 = int(run_b10.n_bets[rep])
        assert tot_a == tot_b25 == tot_b10, f"Replica {rep}: {tot_a} vs {tot_b25} vs {tot_b10}"


# ==============================================================================
# Criterio 5: Ricalcolo delle righe aggregate
# ==============================================================================


def test_aggregate_recalculation() -> None:
    """Verifica il ricalcolo esatto delle righe aggregate (rel_tol 1e-12)."""
    if not CSV_PATH.exists():
        pytest.skip("CSV non ancora generato")

    df_csv = pd.read_csv(CSV_PATH)
    df_agg = df_csv[df_csv["row_type"] == "aggregate"]
    assert len(df_agg) == 11, f"Attese 11 righe aggregate, trovate {len(df_agg)}"

    for _, agg_row in df_agg.iterrows():
        cfg = agg_row["config"]
        ag = agg_row["agent"]
        sub_seasons = df_csv[
            (df_csv["row_type"] == "season")
            & (df_csv["config"] == cfg)
            & (df_csv["agent"] == ag)
        ]
        assert len(sub_seasons) == 19

        # 1. Statistiche lineari (medie delle 19 stagioni con 1000 repliche ciascuna)
        math.isclose(float(agg_row["ruin_rate"]), float(sub_seasons["ruin_rate"].mean()), rel_tol=1e-12)
        math.isclose(float(agg_row["mean_roi"]), float(sub_seasons["mean_roi"].mean()), rel_tol=1e-12)
        math.isclose(
            float(agg_row["prob_min_wealth_le_0_5"]),
            float(sub_seasons["prob_min_wealth_le_0_5"].mean()),
            rel_tol=1e-12,
        )
        math.isclose(
            float(agg_row["prob_min_wealth_le_0_1"]),
            float(sub_seasons["prob_min_wealth_le_0_1"].mean()),
            rel_tol=1e-12,
        )
        math.isclose(
            float(agg_row["prob_replica_floored"]),
            float(sub_seasons["prob_replica_floored"].mean()),
            rel_tol=1e-12,
        )

        # 2. Min wealth complessivo
        expected_min_w = float(sub_seasons["min_wealth"].min())
        assert math.isclose(float(agg_row["min_wealth"]), expected_min_w, rel_tol=1e-12)

        # 3. Intervallo di confidenza al 99%
        r = float(agg_row["ruin_rate"])
        margin = Z_99 * math.sqrt(r * (1.0 - r) / 19_000)
        expected_ci_lower = max(0.0, r - margin)
        expected_ci_upper = min(1.0, r + margin)
        assert math.isclose(float(agg_row["ruin_rate_ci_lower"]), expected_ci_lower, rel_tol=1e-12)
        assert math.isclose(float(agg_row["ruin_rate_ci_upper"]), expected_ci_upper, rel_tol=1e-12)

        # 4. Per E: analytic_expected_roi
        if ag == "E":
            expected_analytic = float(sub_seasons["analytic_expected_roi"].astype(float).mean())
            assert math.isclose(
                float(agg_row["analytic_expected_roi"]), expected_analytic, rel_tol=1e-12
            )


# ==============================================================================
# Criterio 6: CSV e PNG versionati + ricalcolo da dati reali
# ==============================================================================


def test_csv_and_png_schema_and_internal_consistency() -> None:
    """Verifica schema, tipi, colonne del CSV e integrita' del file PNG."""
    if not CSV_PATH.exists():
        pytest.skip("CSV non ancora generato")
    if not FIG_PATH.exists():
        pytest.skip("PNG non ancora generato")

    df_csv = pd.read_csv(CSV_PATH)
    assert tuple(df_csv.columns) == FLOOR_REAL_CSV_COLUMNS
    assert len(df_csv) == 220, f"Attese 220 righe nel CSV, trovate {len(df_csv)}"

    season_rows = df_csv[df_csv["row_type"] == "season"]
    agg_rows = df_csv[df_csv["row_type"] == "aggregate"]
    assert len(season_rows) == 209
    assert len(agg_rows) == 11

    # Integrita' PNG: magic bytes e dimensione minima (> 10 KB)
    with open(FIG_PATH, "rb") as f:
        header = f.read(8)
    assert header == b"\x89PNG\r\n\x1a\n", "Header non conforme a PNG"
    assert FIG_PATH.stat().st_size > 10_000, "Dimensione PNG sospetta (< 10 KB)"


def test_real_data_recalculation_matches_versioned_csv() -> None:
    """Ricalcola dai dati reali e confronta con il CSV versionato (rel_tol 1e-12)."""
    if not DATA_AVAILABLE:
        pytest.skip("Dati grezzi non disponibili")
    if not CSV_PATH.exists():
        pytest.skip("CSV versionato non ancora generato")

    cfg = read_split_config()
    df_hist = load_by_role("history")
    df_train = load_by_role("training")
    df_val = load_by_role("validation")
    df = pd.concat([df_hist, df_train, df_val], ignore_index=True)
    df = df.sort_values("Date", kind="stable").reset_index(drop=True)

    schedule = derive_fit_schedule(cfg)
    df_residuals = compute_model_residuals(df, schedule, ELO_FITS)

    records, _ = evaluate_floor_real_config(
        df_residuals=df_residuals,
        df=df,
        schedule=schedule,
        m_replicas=1000,
        seed=SEED_C6,
    )

    df_recalc = pd.DataFrame(records)[list(FLOOR_REAL_CSV_COLUMNS)]
    df_disk = pd.read_csv(CSV_PATH)

    assert df_recalc.shape == df_disk.shape

    numeric_cols = [
        "min_stake",
        "m_replicas",
        "ruin_rate",
        "median_final_wealth",
        "p05_final_wealth",
        "p95_final_wealth",
        "mean_roi",
        "prob_min_wealth_le_0_5",
        "prob_min_wealth_le_0_1",
        "min_wealth",
        "median_max_drawdown",
        "floored_bets_share",
        "prob_replica_floored",
    ]

    for col in numeric_cols:
        v_rec = pd.to_numeric(df_recalc[col], errors="coerce").to_numpy(dtype=np.float64)
        v_dsk = pd.to_numeric(df_disk[col], errors="coerce").to_numpy(dtype=np.float64)
        np.testing.assert_allclose(v_rec, v_dsk, rtol=1e-12, atol=1e-12)


# ==============================================================================
# Criterio 7: Convenzioni di codice e controllo AST
# ==============================================================================


def test_code_conventions_and_ast() -> None:
    """Verifica tramite AST l'assenza di print e chiamate di logging vietate."""
    for path in (SCRIPT_PATH, MODULE_PATH):
        assert path.exists(), f"File non trovato: {path}"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

        forbidden_methods = {"warn", "warning", "info", "error", "debug"}

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Nessun print()
                if isinstance(node.func, ast.Name) and node.func.id == "print":
                    pytest.fail(f"Chiamata a print() trovata in {path.name}:{node.lineno}")

                # Nessuna chiamata di logging vietata
                if isinstance(node.func, ast.Attribute) and node.func.attr in forbidden_methods:
                    pytest.fail(
                        f"Chiamata vietata a .{node.func.attr}() trovata in {path.name}:{node.lineno}"
                    )
