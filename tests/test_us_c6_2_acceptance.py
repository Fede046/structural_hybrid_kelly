"""Test di accettazione per US-C6.2 / Task 35.

Verifica:
- Criterio 3: equivalenza tra B_0.25 (F = 0) e il reference di us_c5_3_baseline_d.csv entro 1e-12
  e stesso n_bets (6 234 totale); ricalcolo sui dati reali se presenti;
- Criterio 4: stessa selezione per tutti a F = 0 (n_bets(A) + n_dropped(A) == n_bets(B_0.25) == n_bets(B_0.10));
- Criterio 5: regole dell'ambiente nel CSV (con F = 0 nessuna rovina, E punta una volta per data, F > 0 n_bets >= n_dates);
- Criterio 6: le righe di riepilogo si ricalcolano dalle 209 righe di stagione (220 righe totali);
- Criterio 7: ricalcolo dai dati reali coincide col CSV versionato e la figura PNG esiste e non è vuota;
- Criterio 8: convenzioni di codice e controlli AST su paired_backtest.py e le aggiunte a metrics.py.
"""

import ast
import csv
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.data.split import load_by_role, read_split_config
from shk.model.elo_fit import ELO_FITS, derive_fit_schedule
from shk.model.paired_backtest import (
    PAIRED_BACKTEST_CSV_COLUMNS,
    evaluate_validation_seasons,
)
from shk.model.residuals import compute_model_residuals


def _has_real_data() -> bool:
    """Verifica se la directory data/raw/E0 contiene file CSV reali."""
    return DEFAULT_DATA_DIR.exists() and len(list(DEFAULT_DATA_DIR.glob("*.csv"))) > 0


def _load_versioned_c6_2_records() -> list[dict[str, str]]:
    """Carica i record dal CSV versionato results/us_c6_2_paired_backtest.csv."""
    csv_path = Path(__file__).resolve().parents[1] / "results" / "us_c6_2_paired_backtest.csv"
    assert csv_path.exists(), f"Versioned CSV missing: {csv_path}"
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _load_versioned_c5_3_records() -> list[dict[str, str]]:
    """Carica i record dal CSV versionato results/us_c5_3_baseline_d.csv."""
    csv_path = Path(__file__).resolve().parents[1] / "results" / "us_c5_3_baseline_d.csv"
    assert csv_path.exists(), f"Versioned CSV missing: {csv_path}"
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


# ==============================================================================
# Criterio 3: Allineamento con C5.3 (B_0.25 con F = 0 contro reference)
# ==============================================================================


def test_b_025_f0_matches_c5_3_csv() -> None:
    """Per ogni stagione B_0.25 (F = 0) ha final_log_wealth uguale a C5.3 entro 1e-12 e stesso n_bets (6234 totale)."""
    c6_records = _load_versioned_c6_2_records()
    c5_records = _load_versioned_c5_3_records()

    # Filtra B_0.25 con config "none" (F = 0)
    b025_rows = {
        r["season"]: r
        for r in c6_records
        if r["row_type"] == "season" and r["config"] == "none" and r["agent"] == "B_0.25"
    }

    # Filtra reference di C5.3
    ref_rows = {
        r["season"]: r
        for r in c5_records
        if r["row_type"] == "season" and r["agent"] == "reference"
    }

    assert len(b025_rows) == 19
    assert len(ref_rows) == 19

    total_bets_b025 = 0
    total_bets_ref = 0

    for season, ref_r in ref_rows.items():
        assert season in b025_rows, f"Missing season {season} in B_0.25 rows"
        b025_r = b025_rows[season]

        ref_lw = float(ref_r["final_log_wealth"])
        b025_lw = float(b025_r["final_log_wealth"])
        assert math.isclose(b025_lw, ref_lw, rel_tol=1e-12, abs_tol=1e-12), (
            f"Season {season} log_wealth mismatch: B_0.25={b025_lw}, ref={ref_lw}"
        )

        ref_bets = int(ref_r["n_bets"])
        b025_bets = int(b025_r["n_bets"])
        assert b025_bets == ref_bets, (
            f"Season {season} n_bets mismatch: B_0.25={b025_bets}, ref={ref_bets}"
        )

        total_bets_b025 += b025_bets
        total_bets_ref += ref_bets

    assert total_bets_b025 == 6234
    assert total_bets_ref == 6234


@pytest.mark.skipif(not _has_real_data(), reason="Requires real data in data/raw/E0")
def test_b_025_f0_recalculation_matches_c5_3() -> None:
    """Ricalcola le stagioni dai dati reali e verifica l'allineamento con C5.3 reference."""
    cfg = read_split_config()
    df_hist = load_by_role("history")
    df_train = load_by_role("training")
    df_val = load_by_role("validation")
    df = pd.concat([df_hist, df_train, df_val], ignore_index=True)
    df = df.sort_values("Date", kind="stable").reset_index(drop=True)

    schedule = derive_fit_schedule(cfg)
    df_residuals = compute_model_residuals(df, schedule, ELO_FITS)

    records = evaluate_validation_seasons(df_residuals, df, schedule)
    c5_records = _load_versioned_c5_3_records()

    ref_rows = {
        r["season"]: r
        for r in c5_records
        if r["row_type"] == "season" and r["agent"] == "reference"
    }

    b025_rows = {
        r["season"]: r
        for r in records
        if r["row_type"] == "season" and r["config"] == "none" and r["agent"] == "B_0.25"
    }

    for season, ref_r in ref_rows.items():
        ref_lw = float(ref_r["final_log_wealth"])
        b025_lw = float(b025_rows[season]["final_log_wealth"])
        assert math.isclose(b025_lw, ref_lw, rel_tol=1e-12, abs_tol=1e-12)
        assert int(b025_rows[season]["n_bets"]) == int(ref_r["n_bets"])


# ==============================================================================
# Criterio 4: Stessa selezione per tutti a F = 0
# ==============================================================================


def test_same_selection_across_agents_f_zero() -> None:
    """Con F = 0, in ogni stagione n_bets(A) + n_dropped(A) == n_bets(B_0.25) == n_bets(B_0.10)."""
    records = _load_versioned_c6_2_records()
    season_rows = [r for r in records if r["row_type"] == "season" and r["config"] == "none"]

    seasons = sorted({r["season"] for r in season_rows})
    assert len(seasons) == 19

    for s in seasons:
        s_recs = {r["agent"]: r for r in season_rows if r["season"] == s}
        a_bets = int(s_recs["A"]["n_bets"])
        a_dropped = int(s_recs["A"]["n_dropped"])
        b025_bets = int(s_recs["B_0.25"]["n_bets"])
        b010_bets = int(s_recs["B_0.10"]["n_bets"])

        assert a_bets + a_dropped == b025_bets, (
            f"Season {s}: n_bets(A) + n_dropped(A) ({a_bets + a_dropped}) != n_bets(B_0.25) ({b025_bets})"
        )
        assert b025_bets == b010_bets, (
            f"Season {s}: n_bets(B_0.25) ({b025_bets}) != n_bets(B_0.10) ({b010_bets})"
        )


# ==============================================================================
# Criterio 5: Regole dell'ambiente nel CSV
# ==============================================================================


def test_environment_rules_in_csv() -> None:
    """Verifica le regole di floor, ripiego e conteggio puntate nelle righe di stagione del CSV."""
    records = _load_versioned_c6_2_records()
    season_rows = [r for r in records if r["row_type"] == "season"]

    for r in season_rows:
        cfg = r["config"]
        agent = r["agent"]
        ruined = r["ruined"] == "True"
        n_bets = int(r["n_bets"])
        n_forced = int(r["n_forced"])
        n_floored = int(r["n_floored"])
        n_dates = int(r["n_dates"])

        # Con F = 0: nessuna rovina, nessuna puntata forzata né alzata al floor
        if cfg == "none":
            assert not ruined, f"Ruin detected with F = 0 for {agent} in season {r['season']}"
            assert n_forced == 0, f"Forced bets > 0 with F = 0 for {agent} in {r['season']}"
            assert n_floored == 0, f"Floored bets > 0 with F = 0 for {agent} in {r['season']}"

        # Per MinimumStakeAgent (E): nelle stagioni non rovinate n_bets == n_forced == n_dates
        if agent == "E" and not ruined:
            assert n_bets == n_dates, f"E: n_bets ({n_bets}) != n_dates ({n_dates}) in {r['season']}"
            assert n_forced == n_dates, f"E: n_forced ({n_forced}) != n_dates ({n_dates}) in {r['season']}"

        # Con F > 0: ogni data ha almeno una puntata nelle stagioni non rovinate
        if cfg in ("gbp_0.01", "gbp_1") and not ruined:
            assert n_bets >= n_dates, (
                f"{agent} ({cfg}) in {r['season']}: n_bets ({n_bets}) < n_dates ({n_dates})"
            )


# ==============================================================================
# Criterio 6: Ricalcolo righe di riepilogo da righe di stagione
# ==============================================================================


def test_summary_rows_recalculated_from_season_rows() -> None:
    """Le 11 righe di riepilogo si ricalcolano dalle 209 righe di stagione entro rel_tol 1e-12."""
    records = _load_versioned_c6_2_records()
    season_rows = [r for r in records if r["row_type"] == "season"]
    summary_rows = [r for r in records if r["row_type"] == "summary"]

    assert len(season_rows) == 209, f"Expected 209 season rows, got {len(season_rows)}"
    assert len(summary_rows) == 11, f"Expected 11 summary rows, got {len(summary_rows)}"
    assert len(records) == 220, f"Expected 220 total rows, got {len(records)}"

    summary_map = {(r["config"], r["agent"]): r for r in summary_rows}

    # Per ogni combinazione (config, agent), ricalcola i valori
    for (cfg_name, agent_name), s_row in summary_map.items():
        g_rows = [r for r in season_rows if r["config"] == cfg_name and r["agent"] == agent_name]
        assert len(g_rows) == 19

        w_list = [float(r["final_wealth"]) for r in g_rows]
        ruined_list = [r["ruined"] == "True" for r in g_rows]
        dd_list = [float(r["max_drawdown"]) for r in g_rows]
        rec_list = [r["recovered"] == "True" for r in g_rows]
        roi_list = [float(r["roi"]) for r in g_rows]

        # Mediana final_wealth
        exp_med_w = float(np.median(w_list))
        assert math.isclose(float(s_row["median_final_wealth"]), exp_med_w, rel_tol=1e-12, abs_tol=1e-12)

        # Stagioni non rovinate e sd_log_wealth
        unruined_w = [w_list[i] for i in range(19) if not ruined_list[i]]
        assert int(s_row["n_unruined"]) == len(unruined_w)

        if len(unruined_w) > 1:
            exp_sd_lw = float(np.std([np.log(uw) for uw in unruined_w], ddof=1))
            assert math.isclose(float(s_row["sd_log_wealth"]), exp_sd_lw, rel_tol=1e-12, abs_tol=1e-12)
        else:
            assert s_row["sd_log_wealth"] == ""

        # Tasso di rovina
        exp_ruin_r = float(np.mean(ruined_list))
        assert math.isclose(float(s_row["ruin_rate"]), exp_ruin_r, rel_tol=1e-12, abs_tol=1e-12)

        # Mediana e max max_drawdown
        exp_med_dd = float(np.median(dd_list))
        exp_max_dd = float(np.max(dd_list))
        assert math.isclose(float(s_row["median_max_drawdown"]), exp_med_dd, rel_tol=1e-12, abs_tol=1e-12)
        assert math.isclose(float(s_row["max_max_drawdown"]), exp_max_dd, rel_tol=1e-12, abs_tol=1e-12)

        # Quota di recupero
        exp_rec_r = float(np.mean(rec_list))
        assert math.isclose(float(s_row["recovery_rate"]), exp_rec_r, rel_tol=1e-12, abs_tol=1e-12)

        # Mediana recovery_dates sulle sole recuperate
        rec_dates_vals = [int(g_rows[i]["recovery_dates"]) for i in range(19) if rec_list[i]]
        if len(rec_dates_vals) > 0:
            exp_med_rec_d = float(np.median(rec_dates_vals))
            assert math.isclose(float(s_row["median_recovery_dates"]), exp_med_rec_d, rel_tol=1e-12, abs_tol=1e-12)
        else:
            assert s_row["median_recovery_dates"] == ""

        # Contatori totali
        exp_tot_bets = sum(int(r["n_bets"]) for r in g_rows)
        exp_tot_forced = sum(int(r["n_forced"]) for r in g_rows)
        exp_tot_floored = sum(int(r["n_floored"]) for r in g_rows)
        exp_tot_dropped = sum(int(r["n_dropped"]) for r in g_rows)
        assert int(s_row["n_bets"]) == exp_tot_bets
        assert int(s_row["n_forced"]) == exp_tot_forced
        assert int(s_row["n_floored"]) == exp_tot_floored
        assert int(s_row["n_dropped"]) == exp_tot_dropped

        # Somma final_log_wealth se nessuna rovinata, vuota altrimenti
        if any(ruined_list):
            assert s_row["sum_final_log_wealth"] == ""
        else:
            exp_sum_lw = sum(float(r["final_log_wealth"]) for r in g_rows)
            assert math.isclose(float(s_row["sum_final_log_wealth"]), exp_sum_lw, rel_tol=1e-12, abs_tol=1e-12)

        # Mediana, min e max ROI
        exp_med_roi = float(np.median(roi_list))
        exp_min_roi = float(np.min(roi_list))
        exp_max_roi = float(np.max(roi_list))
        assert math.isclose(float(s_row["median_roi"]), exp_med_roi, rel_tol=1e-12, abs_tol=1e-12)
        assert math.isclose(float(s_row["min_roi"]), exp_min_roi, rel_tol=1e-12, abs_tol=1e-12)
        assert math.isclose(float(s_row["max_roi"]), exp_max_roi, rel_tol=1e-12, abs_tol=1e-12)


# ==============================================================================
# Criterio 7: Ricalcolo dai dati reali e figura PNG
# ==============================================================================


def test_figure_png_exists_and_not_empty() -> None:
    """Verifica che la figura thesis/figures/us_c6_2_paired_backtest.png esista e abbia dimensione > 0."""
    png_path = Path(__file__).resolve().parents[1] / "thesis" / "figures" / "us_c6_2_paired_backtest.png"
    assert png_path.exists(), f"Figure file missing: {png_path}"
    assert png_path.stat().st_size > 0, "Figure file is empty"


@pytest.mark.skipif(not _has_real_data(), reason="Requires real data in data/raw/E0")
def test_real_data_recalculation_matches_versioned_csv() -> None:
    """Ricalcola tutti i record dai dati reali e verifica che coincidano col CSV versionato."""
    cfg = read_split_config()
    df_hist = load_by_role("history")
    df_train = load_by_role("training")
    df_val = load_by_role("validation")
    df = pd.concat([df_hist, df_train, df_val], ignore_index=True)
    df = df.sort_values("Date", kind="stable").reset_index(drop=True)

    schedule = derive_fit_schedule(cfg)
    df_residuals = compute_model_residuals(df, schedule, ELO_FITS)

    recomputed = evaluate_validation_seasons(df_residuals, df, schedule)
    versioned = _load_versioned_c6_2_records()

    assert len(recomputed) == len(versioned)

    for i in range(len(versioned)):
        rec_calc = recomputed[i]
        rec_ver = versioned[i]

        for col in PAIRED_BACKTEST_CSV_COLUMNS:
            val_c = rec_calc[col]
            val_v = rec_ver[col]

            if val_v == "":
                assert val_c == "", f"Row {i} col {col}: expected empty string, got {val_c}"
            elif isinstance(val_c, float):
                assert math.isclose(val_c, float(val_v), rel_tol=1e-12, abs_tol=1e-12), (
                    f"Row {i} col {col}: {val_c} != {val_v}"
                )
            else:
                assert str(val_c) == str(val_v), f"Row {i} col {col}: {val_c} != {val_v}"


# ==============================================================================
# Criterio 8: Convenzioni di codice e controlli AST
# ==============================================================================


def test_conventions_and_ast_cleanliness() -> None:
    """Verifica AST divieti di print/log/try/assert su paired_backtest.py e funzioni aggiunte a metrics.py."""
    repo_root = Path(__file__).resolve().parents[1]
    pb_path = repo_root / "src" / "shk" / "model" / "paired_backtest.py"
    metrics_path = repo_root / "src" / "shk" / "kelly" / "metrics.py"

    # Controllo su paired_backtest.py
    with open(pb_path, "r", encoding="utf-8") as f:
        pb_tree = ast.parse(f.read(), filename=str(pb_path))

    for node in ast.walk(pb_tree):
        assert not isinstance(node, ast.Try), "try statement forbidden in paired_backtest.py"
        assert not isinstance(node, ast.Assert), "assert statement forbidden in paired_backtest.py"
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id != "print", "print() forbidden in paired_backtest.py"
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {
                    "warn", "warning", "info", "error", "debug"
                }, f"logging forbidden: {node.func.attr}"

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                doc = ast.get_docstring(node)
                assert doc is not None and len(doc) > 0, f"Function {node.name} must have docstring"
                assert node.returns is not None, f"Function {node.name} must have return type annotation"

    # Controllo sulle funzioni aggiunte a metrics.py (wealth_max_drawdown, wealth_recovery_time)
    with open(metrics_path, "r", encoding="utf-8") as f:
        metrics_tree = ast.parse(f.read(), filename=str(metrics_path))

    target_funcs = {"wealth_max_drawdown", "wealth_recovery_time", "_validate_wealth_matrix"}
    for node in ast.walk(metrics_tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in target_funcs:
            for subnode in ast.walk(node):
                assert not isinstance(subnode, ast.Try), f"try statement forbidden in {node.name}"
                assert not isinstance(subnode, ast.Assert), f"assert statement forbidden in {node.name}"
                if isinstance(subnode, ast.Call):
                    if isinstance(subnode.func, ast.Name):
                        assert subnode.func.id != "print", f"print() forbidden in {node.name}"

            if not node.name.startswith("_"):
                doc = ast.get_docstring(node)
                assert doc is not None and len(doc) > 0, f"Function {node.name} must have docstring"
                assert node.returns is not None, f"Function {node.name} must have return type annotation"
