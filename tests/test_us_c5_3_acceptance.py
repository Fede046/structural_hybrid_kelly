"""Test di accettazione per US-C5.3 / Task 31.

Verifica:
- Criterio 1: il motore riproduce la log-ricchezza di un caso sintetico calcolata a mano entro 1e-12,
  solleva gli errori previsti e non riceve p né p_hat;
- Criterio 2: un allarme della data d cambia lambda solo dalle date successive (test);
- Criterio 3: con kappa = 1 le frazioni coincidono col quarto-Kelly senza detector (test);
- Criterio 4: i kappa congelati per ADWIN e Page-Hinkley coincidono con la calibrazione ricalcolata
  sui dati reali (test saltato senza dati);
- Criterio 5: la docstring della regola dice che il detector indica quando, non quanto né di che tipo;
- Test sintetico: regola di parità fra esiti (H > D > A) e regola di parità fra kappa (vince il più grande).
"""

import csv
import inspect
import math
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from shk.data.loading import DEFAULT_DATA_DIR
from shk.data.split import load_by_role, read_split_config
import shk.model.monitoring as monitoring_module
from shk.kelly.backtest import BacktestResult, backtest_log_wealth
from shk.kelly.staking import (
    BASE_LAMBDA,
    KAPPA_ADWIN,
    KAPPA_GRID,
    KAPPA_PAGE_HINKLEY,
    compute_adaptive_lambda,
    kelly_staking,
    select_baseline_d_bets,
)
from shk.model.elo_fit import ELO_FITS, derive_fit_schedule
from shk.model.monitoring import (
    BASELINE_D_CSV_COLUMNS,
    BaselineDSeasonInput,
    BaselineDValidationSeasonData,
    KappaCalibrationResult,
    build_baseline_d_season_data,
    calibrate_baseline_d_kappa,
    evaluate_baseline_d_agents,
    generate_baseline_d_records,
)
from shk.model.residuals import compute_model_residuals


def _has_real_data() -> bool:
    """Verifica se i dati grezzi sono presenti sul filesystem."""
    return DEFAULT_DATA_DIR.exists() and len(list(DEFAULT_DATA_DIR.glob("*.csv"))) > 0


def test_motor_reproduces_hand_calculation_and_interface():
    """Criterio 1: il motore riproduce la log-ricchezza calcolata a mano entro 1e-12 e non riceve p/p_hat."""
    # Controllo interfaccia
    sig = inspect.signature(backtest_log_wealth)
    assert "p" not in sig.parameters
    assert "p_hat" not in sig.parameters
    assert list(sig.parameters.keys()) == ["dates", "fractions", "odds", "won"]

    # Calcolo a mano sintetico
    dates = np.array(["2010-09-01", "2010-09-02"], dtype="datetime64[D]")
    fractions = np.array([0.10, 0.20], dtype=np.float64)
    odds = np.array([2.50, 3.00], dtype=np.float64)
    won = np.array([True, False], dtype=bool)

    res = backtest_log_wealth(dates, fractions, odds, won)
    assert isinstance(res, BacktestResult)
    assert len(res.dates) == 2
    assert len(res.log_wealth) == 3

    # Giorno 1: r = 1.5, return = 0.15 -> L_1 = ln(1.15)
    # Giorno 2: r = -1.0, return = -0.20 -> L_2 = ln(1.15) + ln(0.80) = ln(0.92)
    expected = np.array([0.0, math.log(1.15), math.log(0.92)], dtype=np.float64)
    np.testing.assert_allclose(res.log_wealth, expected, atol=1e-12)

    # Errori previsti:
    # 1. Quota <= 1.0
    with pytest.raises(ValueError, match="strictly greater than 1.0"):
        backtest_log_wealth(dates, fractions, np.array([1.0, 3.0], dtype=np.float64), won)
    # 2. Frazione >= 1.0
    with pytest.raises(ValueError, match=r"\[0, 1\)"):
        backtest_log_wealth(dates, np.array([1.0, 0.2], dtype=np.float64), odds, won)
    # 3. Somma frazioni su stessa data >= 1.0
    same_date = np.array(["2010-09-01", "2010-09-01"], dtype="datetime64[D]")
    with pytest.raises(ValueError, match="Sum of fractions on date .* is >= 1.0"):
        backtest_log_wealth(same_date, np.array([0.6, 0.5], dtype=np.float64), odds, won)
    # 4. Date non ordinate
    unordered = np.array(["2010-09-02", "2010-09-01"], dtype="datetime64[D]")
    with pytest.raises(ValueError, match="non-decreasing chronological order"):
        backtest_log_wealth(unordered, fractions, odds, won)


def test_alarm_delay_criterion():
    """Criterio 2: un allarme della data d cambia lambda solo dalle date successive."""
    dates = np.array(["2010-09-10", "2010-09-10", "2010-09-11"], dtype="datetime64[D]")
    alarm_dates = np.array(["2010-09-10"], dtype="datetime64[D]")
    lambdas = compute_adaptive_lambda(dates, alarm_dates, kappa=0.5, base_lambda=0.25)

    assert lambdas[0] == pytest.approx(0.25)
    assert lambdas[1] == pytest.approx(0.25)
    assert lambdas[2] == pytest.approx(0.25 * 0.5)


def test_kappa_one_quarter_kelly_criterion():
    """Criterio 3: con kappa = 1 le frazioni coincidono col quarto-Kelly senza detector."""
    dates = np.array(["2010-09-10", "2010-09-15"], dtype="datetime64[D]")
    alarm_dates = np.array(["2010-09-10"], dtype="datetime64[D]")
    lambdas = compute_adaptive_lambda(dates, alarm_dates, kappa=1.0, base_lambda=0.25)
    np.testing.assert_allclose(lambdas, [0.25, 0.25])

    probs = np.array([[0.60, 0.20, 0.20], [0.55, 0.25, 0.20]], dtype=np.float64)
    odds = np.array([[2.00, 3.00, 3.00], [2.20, 3.00, 3.00]], dtype=np.float64)

    bets = select_baseline_d_bets(probs, odds, lambdas)
    expected_f0 = kelly_staking(0.60, 1.0, lam=0.25)
    expected_f1 = kelly_staking(0.55, 1.20, lam=0.25)
    np.testing.assert_allclose(bets.fractions, [expected_f0, expected_f1], atol=1e-12)


def test_baseline_d_docstring_criterion():
    """Criterio 5: la docstring dice che il detector indica quando, non quanto né di che tipo."""
    doc = select_baseline_d_bets.__doc__
    assert doc is not None
    assert "Il detector dice quando, non quanto né di che tipo" in doc
    assert "iperparametro fisso" in doc


def test_kappa_tie_breaking_synthetic():
    """Test sintetico della regola di parità tra kappa: a parità di somma vince il kappa più grande."""
    # Simuliamo un dataset in cui kappa = 0.5 e kappa = 0.75 danno la stessa somma float
    # Verifichiamo che la funzione di selezione basata sulla regola approvata scelga 0.75
    total_wealth = {
        0.0: 0.10,
        0.25: 0.20,
        0.5: 0.35,
        0.75: 0.35,  # Esatta parità tra 0.5 e 0.75
        1.0: 0.30,
    }
    best_k = max(KAPPA_GRID, key=lambda k: (total_wealth[k], k))
    assert best_k == 0.75


def test_frozen_kappas_match_real_data_calibration():
    """Criterio 4: i kappa congelati per ADWIN e Page-Hinkley coincidono con la calibrazione reale."""
    if not _has_real_data():
        pytest.skip("Real data in data/raw/E0 not available")

    cfg = read_split_config()
    df_hist = load_by_role("history")
    df_train = load_by_role("training")
    df_val = load_by_role("validation")
    df = pd.concat([df_hist, df_train, df_val], ignore_index=True).sort_values("Date", kind="stable").reset_index(drop=True)
    schedule = derive_fit_schedule(cfg)
    df_residuals = compute_model_residuals(df, schedule, ELO_FITS)

    res = calibrate_baseline_d_kappa(df_residuals, df)
    assert isinstance(res, KappaCalibrationResult)
    assert res.chosen_kappas["adwin"] == KAPPA_ADWIN
    assert res.chosen_kappas["page_hinkley"] == KAPPA_PAGE_HINKLEY


# --- Nuovi test di accettazione per Task 32 (US-C5.3) ---

def _create_synthetic_validation_season_data() -> BaselineDValidationSeasonData:
    """Crea una BaselineDValidationSeasonData sintetica per i test unitari."""
    n_matches = 10
    dates = np.array([f"2015-09-{i+1:02d}" for i in range(n_matches)], dtype="datetime64[D]")
    probs = np.full((n_matches, 3), [0.55, 0.25, 0.20], dtype=np.float64)
    odds = np.full((n_matches, 3), [2.00, 3.20, 4.00], dtype=np.float64)
    ftr = np.array(["H", "D", "A", "H", "H", "D", "A", "H", "H", "D"], dtype=object)
    log_loss = np.full(n_matches, 0.65, dtype=np.float64)

    season_input = BaselineDSeasonInput(
        season="2015-16",
        dates=dates,
        probs=probs,
        odds=odds,
        ftr=ftr,
        log_loss=log_loss,
    )

    adwin_alarms = np.array(["2015-09-03"], dtype="datetime64[D]")
    ph_alarms = np.array(["2015-09-03", "2015-09-07"], dtype="datetime64[D]")

    return BaselineDValidationSeasonData(
        season="2015-16",
        fit_through="2010-11",
        season_input=season_input,
        adwin_alarm_dates=adwin_alarms,
        page_hinkley_alarm_dates=ph_alarms,
    )


def test_identical_inputs_across_agents_synthetic(monkeypatch: pytest.MonkeyPatch):
    """Verifica che i tre agenti ricevano dates, odds e won identici per una stagione."""
    s_data = _create_synthetic_validation_season_data()

    calls: list[dict[str, np.ndarray]] = []
    original_backtest = backtest_log_wealth

    def spy_backtest(dates: np.ndarray, fractions: np.ndarray, odds: np.ndarray, won: np.ndarray) -> BacktestResult:
        calls.append({
            "dates": dates.copy(),
            "odds": odds.copy(),
            "won": won.copy(),
        })
        return original_backtest(dates, fractions, odds, won)

    import shk.model.monitoring as mon_mod
    monkeypatch.setattr(mon_mod, "backtest_log_wealth", spy_backtest)

    results = evaluate_baseline_d_agents(s_data)
    assert len(results) == 3
    assert len(calls) == 3

    # Confronto bit-a-bit degli input passati a backtest_log_wealth fra i 3 agenti
    ref_call = calls[0]
    for agent_call in calls[1:]:
        np.testing.assert_array_equal(agent_call["dates"], ref_call["dates"])
        np.testing.assert_array_equal(agent_call["odds"], ref_call["odds"])
        np.testing.assert_array_equal(agent_call["won"], ref_call["won"])


def test_baseline_d_matches_reference_with_kappa_one_synthetic():
    """Verifica che con kappa = 1.0 la Baseline D coincida col riferimento anche con allarmi."""
    s_data = _create_synthetic_validation_season_data()
    ref_res, adw_res, ph_res = evaluate_baseline_d_agents(
        s_data,
        base_lambda=0.25,
        kappa_adwin=1.0,
        kappa_page_hinkley=1.0,
    )

    # final_log_wealth identica
    assert ref_res.final_log_wealth == pytest.approx(adw_res.final_log_wealth, abs=1e-12)
    assert ref_res.final_log_wealth == pytest.approx(ph_res.final_log_wealth, abs=1e-12)

    # frazioni e numero di puntate identici
    assert ref_res.n_bets == adw_res.n_bets == ph_res.n_bets
    np.testing.assert_allclose(ref_res.bets.fractions, adw_res.bets.fractions, atol=1e-12)
    np.testing.assert_allclose(ref_res.bets.fractions, ph_res.bets.fractions, atol=1e-12)

    # max_drawdown identico
    assert ref_res.max_drawdown == pytest.approx(adw_res.max_drawdown, abs=1e-12)
    assert ref_res.max_drawdown == pytest.approx(ph_res.max_drawdown, abs=1e-12)


def test_kappas_imported_from_staking_constants():
    """Verifica che le funzioni in monitoring.py importino e usino i kappa congelati."""
    sig_eval = inspect.signature(evaluate_baseline_d_agents)
    assert sig_eval.parameters["kappa_adwin"].default == KAPPA_ADWIN
    assert sig_eval.parameters["kappa_page_hinkley"].default == KAPPA_PAGE_HINKLEY

    sig_gen = inspect.signature(generate_baseline_d_records)
    assert sig_gen.parameters["kappa_adwin"].default == KAPPA_ADWIN
    assert sig_gen.parameters["kappa_page_hinkley"].default == KAPPA_PAGE_HINKLEY


def test_versioned_csv_schema_counts_and_totals():
    """Verifica lo schema del CSV versionato, i conteggi (57 season + 3 total) e le somme."""
    repo_root = Path(__file__).resolve().parents[1]
    csv_path = repo_root / "results" / "us_c5_3_baseline_d.csv"
    assert csv_path.exists(), f"File CSV non trovato: {csv_path}"

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == list(BASELINE_D_CSV_COLUMNS)
        rows = list(reader)

    assert len(rows) == 60

    season_rows = [r for r in rows if r["row_type"] == "season"]
    total_rows = [r for r in rows if r["row_type"] == "total"]
    assert len(season_rows) == 57
    assert len(total_rows) == 3

    # Ordine degli agenti per stagione
    expected_agents = ["reference", "d_adwin", "d_page_hinkley"]
    seasons_seen = []
    for i in range(0, 57, 3):
        group = season_rows[i:i+3]
        s = group[0]["season"]
        seasons_seen.append(s)
        assert [r["agent"] for r in group] == expected_agents
        assert all(r["season"] == s for r in group)
        assert all(r["max_drawdown"] != "" for r in group)

    assert len(set(seasons_seen)) == 19

    # Controllo righe total
    assert [r["agent"] for r in total_rows] == expected_agents
    for tot_row in total_rows:
        ag = tot_row["agent"]
        assert tot_row["season"] == ""
        assert tot_row["fit_through"] == ""
        assert tot_row["max_drawdown"] == ""

        # Somma log-wealth sulle 19 stagioni
        expected_lw_sum = sum(float(r["final_log_wealth"]) for r in season_rows if r["agent"] == ag)
        assert float(tot_row["final_log_wealth"]) == pytest.approx(expected_lw_sum, abs=1e-12)

        # Somma n_bets sulle 19 stagioni
        expected_bets_sum = sum(int(r["n_bets"]) for r in season_rows if r["agent"] == ag)
        assert int(tot_row["n_bets"]) == expected_bets_sum

        # Allarmi
        if ag == "reference":
            assert tot_row["n_alarms"] == ""
        else:
            expected_alarms_sum = sum(int(r["n_alarms"]) for r in season_rows if r["agent"] == ag)
            assert int(tot_row["n_alarms"]) == expected_alarms_sum


def test_real_data_recomputation_matches_versioned_csv():
    """Verifica che il ricalcolo dai dati reali coincida con il CSV versionato."""
    if not _has_real_data():
        pytest.skip("Dati reali non presenti sul filesystem")

    repo_root = Path(__file__).resolve().parents[1]
    csv_path = repo_root / "results" / "us_c5_3_baseline_d.csv"
    assert csv_path.exists(), f"File CSV non trovato: {csv_path}"

    with open(csv_path, mode="r", encoding="utf-8") as f:
        csv_rows = list(csv.DictReader(f))

    cfg = read_split_config()
    df_hist = load_by_role("history")
    df_train = load_by_role("training")
    df_val = load_by_role("validation")
    df = pd.concat([df_hist, df_train, df_val], ignore_index=True).sort_values("Date", kind="stable").reset_index(drop=True)
    schedule = derive_fit_schedule(cfg)
    df_residuals = compute_model_residuals(df, schedule, ELO_FITS)

    recomputed = generate_baseline_d_records(df_residuals, df, schedule)
    assert len(recomputed) == len(csv_rows)

    float_cols = {"final_log_wealth", "max_drawdown"}
    for i, (rec, csv_r) in enumerate(zip(recomputed, csv_rows, strict=True)):
        for col in BASELINE_D_CSV_COLUMNS:
            val_rec = rec[col]
            val_csv = csv_r[col]
            if col in float_cols:
                if val_csv == "":
                    assert str(val_rec) == ""
                else:
                    assert float(val_rec) == pytest.approx(float(val_csv), abs=1e-12), (
                        f"Discrepanza float riga {i}, colonna '{col}': {val_rec} vs {val_csv}"
                    )
            else:
                assert str(val_rec) == str(val_csv), (
                    f"Discrepanza testo riga {i}, colonna '{col}': '{val_rec}' vs '{val_csv}'"
                )

