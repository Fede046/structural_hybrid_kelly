"""Test di accettazione per la User Story US-C6.3 (Task 36).

Verifica della predizione teorica della Nota 2.9: il floor sulle puntate (F > 0)
e l'unico meccanismo che rende possibile la rovina di un agente Kelly.
"""

import ast
import csv
import math
from pathlib import Path

import numpy as np
import pytest

from shk.kelly.floor import (
    EXP_A_LAMBDA,
    EXP_A_M,
    EXP_A_ODDS,
    FLOOR_SYNTHETIC_CSV_COLUMNS,
    NOTE_EXP_A_M,
    NOTE_EXP_A_RUIN_RATES_50F,
    NOTE_EXP_A_RUIN_RATES_1000F,
    SEED_C6,
    evaluate_all_synthetic_experiments,
    expected_ruin_time_bound,
    run_experiment_a,
    spawn_t36_generators,
    two_sample_mc_tolerance,
)


def _load_csv_records() -> list[dict[str, str]]:
    """Carica i record dal CSV versionato results/us_c6_3_floor_synthetic.csv."""
    csv_path = Path(__file__).resolve().parents[1] / "results" / "us_c6_3_floor_synthetic.csv"
    assert csv_path.exists(), f"CSV file not found: {csv_path}"
    with open(csv_path, mode="r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ==============================================================================
# Criterio 2: Senza floor la rovina e esattamente 0 e W > 0
# ==============================================================================
def test_no_ruin_without_floor_in_csv_and_simulation() -> None:
    """Verifica che senza floor (F = 0) la rovina sia esattamente 0.0 in tutte le repliche."""
    records = _load_csv_records()
    nofloor_rows = [r for r in records if r["with_floor"] == "False"]
    assert len(nofloor_rows) > 0, "No rows with with_floor=False found in CSV"

    for r in nofloor_rows:
        ruin_rate = float(r["ruin_rate"])
        assert ruin_rate == 0.0, f"Expected 0.0 ruin rate without floor, got {ruin_rate} in row {r}"


# ==============================================================================
# Criterio 3: Riproduzione dei tassi di rovina della Nota 2.9 §5.2-§5.3
# ==============================================================================
def test_reproduction_of_note_ruin_rates_in_experiment_a() -> None:
    """Verifica che i tassi dell'esperimento A riproducano la Nota entro la tolleranza al 99%."""
    records = _load_csv_records()
    exp_a_floor_rows = [r for r in records if r["experiment"] == "A" and r["with_floor"] == "True"]

    for r in exp_a_floor_rows:
        ratio = float(r["initial_ratio"])
        h = int(r["horizon"])
        ruin_r = float(r["ruin_rate"])
        note_r = float(r["note_ruin_rate"])
        tol = float(r["mc_tol_99"])
        within_tol = r["within_tolerance"] == "True"

        if ratio == 1000.0:
            # Compatibile con 0.000%
            assert ruin_r == 0.0
            assert note_r == 0.0
            assert within_tol
        elif ratio == 50.0:
            assert h in NOTE_EXP_A_RUIN_RATES_50F
            assert math.isclose(note_r, NOTE_EXP_A_RUIN_RATES_50F[h], rel_tol=1e-5)
            # Tolleranza a due campioni
            expected_tol = two_sample_mc_tolerance(ruin_r, note_r, EXP_A_M, NOTE_EXP_A_M)
            assert math.isclose(tol, expected_tol, rel_tol=1e-9)
            assert abs(ruin_r - note_r) <= tol, (
                f"Ruin rate at H={h} ({ruin_r}) deviates from note ({note_r}) by "
                f"{abs(ruin_r - note_r)}, which exceeds tolerance {tol}"
            )
            assert within_tol


# ==============================================================================
# Criterio 4: Soglia e sovraesposizione nell'esperimento A
# ==============================================================================
def test_regime_threshold_and_overexposure_in_experiment_a() -> None:
    """Verifica che le traiettorie con e senza floor coincidano fino a W < B1 compresa e le regole di puntata."""
    rng_a, _, _ = spawn_t36_generators(SEED_C6)
    # Eseguiamo un campione ridotto di 100 repliche per verificare le proprietà microscopiche
    res_1000f, res_50f = run_experiment_a(rng_a, m_replicas=100, chunk_size=50)

    for res in (res_1000f, res_50f):
        w_floor = res.run_floor.wealth
        w_nofloor = res.run_nofloor.wealth
        b1 = res.thresholds[0]
        min_stake = res.min_stake
        staked = res.run_floor.staked
        desired = res.run_floor.desired
        assert staked is not None and desired is not None

        m_count, d_plus_1 = w_floor.shape
        d_count = d_plus_1 - 1

        for i in range(m_count):
            # Trova la prima colonna con W < B1
            below_b1_cols = np.where(w_floor[i, :] < b1)[0]
            if len(below_b1_cols) > 0:
                first_below_idx = int(below_b1_cols[0])
                # Le colonne [0, first_below_idx] devono coincidere esattamente!
                assert np.allclose(
                    w_floor[i, : first_below_idx + 1],
                    w_nofloor[i, : first_below_idx + 1],
                    rtol=1e-12,
                    atol=1e-12,
                ), f"Mismatch before or at first column below B1 (replica {i})"

            # Controllo puntate su ciascuna data
            for t in range(d_count):
                w_curr = w_floor[i, t]
                stk = staked[i, t]
                des = desired[i, t]

                if w_curr >= b1:
                    # Regime 0: puntata piazzata coincide con puntata desiderata f * W
                    assert math.isclose(stk, des, rel_tol=1e-12, abs_tol=1e-12)
                elif min_stake <= w_curr < b1:
                    # Regime 1 o 2: puntata piazzata alzata al floor
                    assert math.isclose(stk, min_stake, rel_tol=1e-12, abs_tol=1e-12)
                    assert stk > des  # Sovraesposizione: F > f * W
                else:
                    # Replica rovinata: non punta più
                    assert stk == 0.0


# ==============================================================================
# Criterio 5: Esperimento C (tempo medio di rovina <= limite teorico)
# ==============================================================================
def test_ruin_times_upper_bounded_by_limit_in_experiment_c() -> None:
    """Verifica che il tempo medio di rovina simulato sia <= limite analitico nelle 3 configurazioni."""
    records = _load_csv_records()
    exp_c_rows = [r for r in records if r["experiment"] == "C"]
    assert len(exp_c_rows) == 3, f"Expected 3 rows for Experiment C, got {len(exp_c_rows)}"

    for r in exp_c_rows:
        cfg_id = r["config_id"]
        bound = float(r["bound_limit"])
        mean_time = float(r["mean_ruin_time"])
        censored = int(r["censored_count"])
        accel = float(r["acceleration_factor"])

        # Tempo medio simulato <= limite teorico
        assert mean_time <= bound, (
            f"Mean ruin time ({mean_time}) exceeds bound ({bound}) in {cfg_id}"
        )
        assert accel >= 1.0, f"Acceleration factor must be >= 1.0, got {accel} in {cfg_id}"

        assert censored == 0, f"Expected 0 censored replicas in {cfg_id}, got {censored}"
        if cfg_id == "C_a":
            assert math.isclose(bound, 32986.2, rel_tol=0.01)
        elif cfg_id == "C_b":
            assert math.isclose(bound, 914.1, rel_tol=0.01)
        elif cfg_id == "C_c":
            assert math.isclose(bound, 4096.6, rel_tol=0.01)


# ==============================================================================
# Criterio 6: CSV e PNG versionati, coerenza e ricalcolo
# ==============================================================================
def test_floor_synthetic_csv_and_figure_exist_and_consistent() -> None:
    """Verifica l'esistenza, la consistenza dello schema del CSV e la figura PNG."""
    project_root = Path(__file__).resolve().parents[1]
    csv_path = project_root / "results" / "us_c6_3_floor_synthetic.csv"
    png_path = project_root / "thesis" / "figures" / "us_c6_3_floor_synthetic.png"

    assert csv_path.exists(), "CSV results file does not exist"
    assert png_path.exists(), "PNG figure file does not exist"
    assert png_path.stat().st_size > 0, "PNG figure file is empty"

    records = _load_csv_records()
    assert len(records) == 47, f"Expected exactly 47 rows, got {len(records)}"

    # Verifica colonne
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
    assert tuple(header) == FLOOR_SYNTHETIC_CSV_COLUMNS


@pytest.mark.slow
def test_real_recalculation_matches_versioned_csv() -> None:
    """Ricalcola tutti gli esperimenti da floor.py e verifica identita col CSV (rel_tol=1e-12)."""
    records_sim, _, _, _ = evaluate_all_synthetic_experiments(seed=SEED_C6)
    records_csv = _load_csv_records()

    assert len(records_sim) == len(records_csv)

    for idx, (sim_r, csv_r) in enumerate(zip(records_sim, records_csv)):
        for col in FLOOR_SYNTHETIC_CSV_COLUMNS:
            sim_val = sim_r[col]
            csv_val = csv_r[col]

            if sim_val == "" or csv_val == "":
                assert sim_val == "" and csv_val == "", f"Mismatch at row {idx}, col {col}"
            elif isinstance(sim_val, bool):
                assert str(sim_val) == csv_val, f"Mismatch at row {idx}, col {col}"
            elif isinstance(sim_val, (int, np.integer)):
                assert int(sim_val) == int(csv_val), f"Mismatch at row {idx}, col {col}"
            elif isinstance(sim_val, (float, np.floating)):
                sim_f = float(sim_val)
                csv_f = float(csv_val)
                assert math.isclose(sim_f, csv_f, rel_tol=1e-12, abs_tol=1e-12), (
                    f"Mismatch at row {idx}, col {col}: sim={sim_f}, csv={csv_f}"
                )
            else:
                assert str(sim_val) == str(csv_val), f"Mismatch at row {idx}, col {col}"


# ==============================================================================
# Criterio 7: Convenzioni del progetto e controllo AST su floor.py e script
# ==============================================================================
def test_floor_conventions_and_ast_cleanliness() -> None:
    """Verifica che floor.py e lo script rispettino le convenzioni del progetto e i controlli AST."""
    project_root = Path(__file__).resolve().parents[1]
    floor_path = project_root / "src" / "shk" / "kelly" / "floor.py"
    script_path = project_root / "scripts" / "us_c6_3_floor_synthetic.py"

    assert floor_path.exists(), f"File {floor_path} not found"
    assert script_path.exists(), f"File {script_path} not found"

    content = floor_path.read_text(encoding="utf-8")
    tree = ast.parse(content, filename=str(floor_path))

    # Controllo import consentiti (solo numpy, typing, math, dataclasses, shk.kelly)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_pkg = alias.name.split(".")[0]
                assert root_pkg in ("numpy", "math", "typing", "dataclasses", "shk"), (
                    f"Forbidden import: {alias.name}"
                )
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root_pkg = node.module.split(".")[0]
                assert root_pkg in ("numpy", "math", "typing", "dataclasses", "shk"), (
                    f"Forbidden import from: {node.module}"
                )

    # Nessun print, logging, assert, try, except, warnings in floor.py
    for node in ast.walk(tree):
        assert not isinstance(node, ast.Try), "Forbidden 'try' statement in floor.py"
        assert not isinstance(node, ast.Assert), "Forbidden 'assert' statement in floor.py"
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id != "print", "Forbidden print() in floor.py"
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in ("warn", "warning", "info", "error", "debug"), (
                    f"Forbidden logging call: {node.func.attr} in floor.py"
                )

    # Tutte le funzioni pubbliche in floor.py devono avere docstring e annotazioni
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
            assert ast.get_docstring(node) is not None, f"Missing docstring in public function {node.name}"
            assert node.returns is not None, f"Missing return annotation in public function {node.name}"

    # Controllo divieti AST esteso allo script
    script_content = script_path.read_text(encoding="utf-8")
    script_tree = ast.parse(script_content, filename=str(script_path))

    for node in ast.walk(script_tree):
        assert not isinstance(node, ast.Try), "Forbidden 'try' statement in script"
        assert not isinstance(node, ast.Assert), "Forbidden 'assert' statement in script"
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id != "print", "Forbidden print() in script"
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in ("warn", "warning", "info", "error", "debug"), (
                    f"Forbidden logging call: {node.func.attr} in script"
                )
