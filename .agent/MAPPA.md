Mappa completa — 2026-10-07 — R1

Legenda: `[V]` verificato in questa sessione (file aperto o ricerca eseguita); `[D]` dedotto (nome, convenzione, struttura, documenti di `.agent/`), non riletto nel codice. Percorsi sempre dalla radice del repository.

### 0. Stato del repository

* Radice: `C:\Users\malse\Documents\GitHub\structural_hybrid_kelly` `[V]`.
* Branch corrente: `main` `[V]`.
* Working tree: pulito (`nothing to commit, working tree clean`) `[V]`.
* File modificati, staged o non tracciati: nessuno `[V]`.
* File ignorati presenti su disco: `.pytest_cache/`, `.venv/`, `data/raw/E0/`, `scripts/__pycache__/`, `src/shk/__pycache__/`, `src/shk/data/__pycache__/`, `src/shk/kelly/__pycache__/`, `src/shk/market/__pycache__/`, `src/shk/model/__pycache__/`, `src/shk/stats/__pycache__/`, `tests/__pycache__/` `[V]`.
* `.git/info/exclude` contiene solo commenti `[V]`.
* `.agent/` è tracciato su `main`: `git log -- .agent/MAPPA.md` restituisce 736f5cd, 27cf7a4, 90a77a1 `[V]`.
* Ultimi cinque commit di `main` `[V]`:
  * `736f5cd` `C5 (#20)` — 2026-10-02 14:18:43 +0200
  * `27cf7a4` `C4 (#18)`
  * `90a77a1` `C3 (#17)`
  * `115e600` `C2 (#16)`
  * `1e7813d` `C1 (#14)`
* Remote: `origin` → `https://github.com/Fede046/structural_hybrid_kelly.git` (fetch e push) `[V]`.
* Allineamento: `main...origin/main` senza avanti né indietro, rispetto all'ultimo fetch locale `[V]`. Nessun `git fetch` eseguito: lo stato reale del remote non è verificato `[V]`.
* Branch locali: `main` e `pre-c4` (a `5249f9b` "fix", traccia `origin/pre-c4`) `[V]`.
* Branch remoti: `origin/HEAD -> origin/main`, `origin/main`, `origin/pre-c4` `[V]`.
* `pre-c4` contiene due commit assenti da `main`: `5249f9b` "fix" (2026-10-02 00:22:56 +0200) e `043b9a5` "Rimuove .agent dal tracciamento" `[V]`. Nella sua storia lineare `043b9a5` segue `90a77a1` `[V]`.
* Il branch di lavoro `C5` non esiste più né localmente né sul remote noto `[V]`.
* Fra 27cf7a4 (mappa precedente) e 736f5cd sono cambiati 32 file, tutti di S5 o di `.agent/` più `pyproject.toml` `[V]` (`git diff --stat 27cf7a4 736f5cd`). `uv.lock` non è fra questi `[V]`.

### 1. Identikit

* Nome: `structural-hybrid-kelly`, versione `0.1.0` (`pyproject.toml` e `src/shk/__init__.py`) `[V]`; pacchetto importabile `shk` da `src/shk/` `[V]`.
* Descrizione in `pyproject.toml`: "Analytical Kelly criterion and structural hybrid models" `[V]`.
* Cosa fa: libreria e script di esperimento per una tesi, che simulano il criterio di Kelly sotto errore di stima e studiano l'ANOVA su serie autocorrelate con calibrazione per block bootstrap `[V]`. Su dati Premier League (E0, football-data) carica e partiziona le stagioni, de-vigga le quote, prevede gli esiti con un Elo walk-forward, misura ĝ contro il mercato, ricalibra, monitora il drift (ADWIN, Page-Hinkley, Z per matchday) ed esegue un backtest della "Baseline D" `[V]`.
* Linguaggio: Python `[V]`. `requires-python = ">=3.11"` `[V]`. La CI usa Python 3.12 `[V]`.
* Dipendenze runtime dichiarate, senza vincoli di versione: numpy, scipy, matplotlib, pandas, river `[V]`. Extra `dev`: pytest `[V]`.
* Ambiente locale `.venv`: Python 3.12.7, creato con `python -m venv` dall'interprete Anaconda (`.venv/pyvenv.cfg`) `[V]`. Pacchetti installati (da `dist-info`): numpy 2.5.2, scipy 1.18.1, pandas 3.0.6, matplotlib 3.11.1, river 0.26.1, narwhals 2.26.0, pytest 9.1.1 `[V]`. `shk` installato in modalità editable (`_editable_impl_structural_hybrid_kelly.pth`) `[V]`.
* Gestore di pacchetti: la CI usa pip `[V]`. `uv.lock` (version 1, revision 3) è presente alla radice `[V]`, ma non contiene né pandas né river e il suo `requires-dist` elenca solo matplotlib, numpy, scipy, pytest `[V]`. Quale dei due sia il gestore canonico non è dichiarato in alcun file `[D]`.
* Build system: hatchling, wheel con `packages = ["src/shk"]` `[V]`.
* README: assente `[V]`. Licenza: `LICENSE` alla radice `[V]`.

### 2. Come si esegue

* Installazione, attestata in `.github/workflows/test.yml`: `python -m pip install --upgrade pip` e `pip install -e ".[dev]"` `[V]`.
* Installazione locale con l'interprete del venv, `.\.venv\Scripts\python.exe -m pip install -e ".[dev]"`: `[D]` (non scritta in file di configurazione; la regola "usa il venv" sta in `.agent/BACKLOG.md`).
* `uv sync`: `[D]`; con `uv.lock` attuale non installerebbe pandas né river `[D]`.
* Avvio in sviluppo: nessun server, nessun entry point `[project.scripts]` in `pyproject.toml` `[V]`. L'esecuzione passa dagli script in `scripts/` `[V]`.
* Build del pacchetto: `hatch build` o `python -m build` `[D]`.
* Test:
  * `pytest -v` è il comando della CI `[V]`.
  * `pyproject.toml` imposta `addopts = "-m 'not slow'"` e registra il marker `slow` `[V]`.
  * Solo i test slow: `pytest -m slow` `[D]`. Tutti i test: `pytest -o addopts=""` `[D]`.
  * Locale: `.\.venv\Scripts\python.exe -m pytest -v` `[D]` (stessa fonte di sopra).
* Esperimenti: `python scripts/<nome>.py`, uno per esperimento `[D]` (nessun file lo scrive; ogni script ha `run_experiment()` chiamata dal blocco `__main__` `[V]`).
  * `scripts/us_c1_1_growth_vs_lambda.py`, `scripts/us_c1_2_estimation_error.py`, `scripts/us_c2_anova_autocorrelation.py` scrivono in `results/` e `thesis/figures/` relativi alla directory corrente `[V]`: vanno lanciati dalla radice `[D]`.
  * Gli altri otto script calcolano i percorsi da `Path(__file__).resolve().parents[1]` `[V]`.
  * Gli script C3.2, C4.x e C5.x leggono i dati con `load_by_role` e richiedono `data/raw/E0/*.csv` `[V]`. C3.1 usa `load_all_seasons()` su tutta la directory `[V]`.
* Variabili d'ambiente lette dal codice: nessuna (ricerca di `os.environ`, `getenv`, `dotenv` in `src/`, `scripts/`, `tests/` senza risultati) `[V]`.
* File di configurazione richiesti:
  * `pyproject.toml` `[V]`.
  * `config/split.toml`, con chiavi `frozen_on`, `test_unlocked`, `test_unlocked_on`, `training`, `validation`, `test` `[V]`.
  * Dati grezzi `data/raw/E0/<YYYY-YY>.csv`, 31 file dal 1993-94 al 2023-24, presenti in locale e ignorati da `.gitignore` (`data/raw/*`, eccetto `.gitkeep`) `[V]`.
  * Nessun `.env` presente `[V]`.

### 3. Albero delle directory

* `.agent/` — file di stato del processo: `PROTOCOLLO.md`, `SCHEDA.md`, `BACKLOG.md`, `MAPPA.md`, `report/T1.md` … `report/T32.md` `[V]`.
* `.github/workflows/` — CI, solo `test.yml` `[V]`.
* `config/` — `split.toml` congelato e `.gitkeep` `[V]`.
* `data/raw/` — `.gitkeep` versionato e `E0/` con i CSV grezzi non versionati `[V]`.
* `results/` — undici CSV di esperimento versionati e `.gitkeep` `[V]`.
* `scripts/` — undici script `us_c<story>_<n>_<nome>.py`, uno per esperimento `[V]`.
* `src/shk/kelly/` — formule di Kelly, simulazione Monte Carlo, stima rumorosa, regole di puntata, metriche, scenari, motore su quote reali `[V]`.
* `src/shk/stats/` — ANOVA, AR(1), block bootstrap, falso rigetto C2, drift detector e Z per matchday `[V]`.
* `src/shk/data/` — caricamento CSV E0, audit di copertura, split per ruolo, fornitore walk-forward anti-leakage `[V]`.
* `src/shk/market/` — de-vigging e tabella di divergenza fra metodi `[V]`.
* `src/shk/model/` — Elo, previsore walk-forward, calibrazione Elo, ĝ, ricalibrazione, residui, monitoraggio e Baseline D `[V]`.
* `tests/` — 30 moduli di test pytest, nessun `conftest.py` `[V]`.
* `thesis/figures/` — undici PNG omonimi dei CSV e `.gitkeep` `[V]`.

### 4. Moduli principali

`src/shk/` contiene 25 moduli applicativi più 6 `__init__.py` `[V]`. Scelti dieci; gli esclusi sono elencati in fondo alla sezione.

1. `src/shk/kelly/staking.py`
   * Responsabilità: regole di puntata Kelly su probabilità stimata, e regola della Baseline D `[V]`.
   * Espone `[V]`:
     * `kelly_staking(p_hat, b, lam=1.0)`: `lam·max(0, (b·p̂ − (1 − p̂))/b)`, senza limite superiore; float per input 0-d, ndarray altrimenti.
     * `StakingMoments` (mean_c, mean_c2, var_c, fraction_zero), `staking_moments(f_hat, f_star)`.
     * `plugin_staking(p_hat, b, sigma_p)`.
     * Costanti alle righe 224-229: `BASE_LAMBDA = 0.25`, `KAPPA_GRID = (0.0, 0.25, 0.5, 0.75, 1.0)`, `KAPPA_ADWIN = 1.0`, `KAPPA_PAGE_HINKLEY = 1.0`, `OUTCOME_LABELS = ("H", "D", "A")`.
     * `BaselineDBets` (outcomes, odds, fractions).
     * `compute_adaptive_lambda(match_dates, alarm_dates, kappa, base_lambda=BASE_LAMBDA)`: `λ_j = base·κ^(allarmi con data < D_j)`; `kappa` deve essere float, un `int` dà TypeError (righe 297-298).
     * `select_baseline_d_bets(probs, odds, lambdas)`: esito con `p̂·o − 1` massimo (`np.argmax`, parità nell'ordine H, D, A), frazione `kelly_staking` solo se il massimo è > 0; ciclo Python per partita.
   * Dipendenze interne: nessuna `[V]`.

2. `src/shk/kelly/backtest.py`
   * Responsabilità: traiettoria di log-ricchezza di una stagione su quote reali, con regolamento simultaneo delle puntate della stessa data `[V]`.
   * Espone `[V]`: `BacktestResult` (dates, log_wealth); `backtest_log_wealth(dates, fractions, odds, won)`, con dtype obbligati datetime64, float64, float64, bool. Somma delle frazioni di una data ≥ 1, frazioni fuori da [0, 1), quote ≤ 1 o non finite, date non ordinate danno ValueError.
   * Dipendenze interne: nessuna `[V]`.

3. `src/shk/stats/calibration.py`
   * Responsabilità: calibrazione generica di una soglia per moving block bootstrap `[V]`.
   * Espone `[V]`: `moving_block_indices(n, block_length, n_boot, rng)` → int64 (n_boot, n); `compute_order_statistic_index(b, alpha)` → ⌈(1 − α)(b + 1)⌉ con tolleranza 1e-9; `calibrate_threshold(data, statistic, block_length, n_boot, alpha, rng, vectorized=False)` → float.
   * Dipendenze interne: nessuna `[V]`.

4. `src/shk/stats/drift.py`
   * Responsabilità: esecuzione e taratura di ADWIN e Page-Hinkley (da river), Z-test per matchday nominale e calibrato `[V]`.
   * Espone `[V]`:
     * costanti: `TARGET_ALARMS_PER_SEASON = 1.9`, `MATCHDAY_SIZE = 10`, `SEED_C5 = 20260929`, `N_VERIFICATION_RESAMPLES = 1000`, le griglie `ADWIN_GRID_DELTA` (9 valori) e `PAGE_HINKLEY_GRID_DELTA` × `PAGE_HINKLEY_GRID_THRESHOLD` (3 × 6), i default di river 0.26.1 (`ADWIN_DEFAULT_*`, `PAGE_HINKLEY_DEFAULT_*`), i valori scelti `ADWIN_DELTA = 0.002`, `PAGE_HINKLEY_DELTA = 0.05`, `PAGE_HINKLEY_THRESHOLD = 5.0`;
     * `detector_params(detector)`, `run_drift_detector(series, detector, params=None)` (istanza nuova per chiamata; con `params=None` usa i default di river);
     * `select_best_candidate`, `calibrate_adwin`, `calibrate_page_hinkley`, `calibrate_drift_detectors` (restituiscono `pd.DataFrame` per la griglia);
     * `compute_matchday_z_scores`, `compute_resampled_matchday_abs_z`, `calibrate_matchday_z_threshold`, `verify_matchday_z_thresholds`, `spawn_c5_generators(seed=SEED_C5, n_fits=3)`.
   * Dipendenze interne: `src/shk/stats/calibration.py` (`calibrate_threshold`, `moving_block_indices`), `src/shk/stats/false_rejection.py` (`ALPHA`, `BLOCK_LENGTHS`, `N_BOOT`) `[V]`. Esterne: `river.drift`, `pandas` `[V]`.

5. `src/shk/data/split.py`
   * Responsabilità: lettura e validazione dello split congelato, e barriera di accesso ai dati per ruolo `[V]`.
   * Espone `[V]`: `DEFAULT_SPLIT_CONFIG_PATH` (radice/config/split.toml); `TestSetLockedError(RuntimeError)` con `__test__ = False`; `SplitConfig` (frozen_on, test_unlocked, test_unlocked_on, training, validation, test); `read_split_config(config_path)`; `load_by_role(role, config_path, data_dir)` con ruoli `training`, `validation`, `test`, `history`.
   * `load_by_role` solleva `TestSetLockedError` prima di toccare i dati `[V]`. Controlla poi che tutte le stagioni configurate, test compreso, abbiano un file nella directory, solo per nome (righe 272-277) `[V]`. `history` = stagioni presenti, anteriori al primo anno di test, né training né validation `[V]`.
   * Dipendenze interne: `src/shk/data/loading.py` (`DEFAULT_DATA_DIR`, `load_all_seasons`) `[V]`.

6. `src/shk/market/devig.py`
   * Responsabilità: probabilità implicite e tre metodi di de-vigging `[V]`.
   * Espone `[V]`: `MAX_NEWTON_ITERATIONS = 50`; `implied_probabilities`, `overround`, `devig_proportional`, `devig_additive` (riga di NaN se un q ≤ 0), `devig_power` → (q, k), con Newton vettorizzato da k = 1, salvaguardia `max(k − step, k/2)` e RuntimeError se un mercato ha |Σq − 1| > 1e-12.
   * Dipendenze interne: nessuna `[V]`.

7. `src/shk/model/elo_predictor.py`
   * Responsabilità: previsioni Elo walk-forward 1X2 con la regola per neopromosse e tornanti `[V]`.
   * Espone `[V]`: `SEASON_REGEX`; `compute_season_standings(matches)`; `predict_elo_walkforward(...)` (via fornitore, con `assert_no_leakage` su ogni coppia); `predict_elo_fast(df, seasons_to_predict, k, h, nu, s=400.0, initial_rating=1500.0)` (passata unica, `groupby` per data: prima previsione, poi aggiornamento); `diagnose_season_transitions(df)`. Output: DataFrame con 12 colonne (season, Date, HomeTeam, AwayTeam, rating_home, rating_away, delta, p_home, p_draw, p_away, home_promotion, away_promotion).
   * Interni: `_CALC_COLS` (righe 14-22), `_parse_season_start_year` (riga 91), `_validate_inputs`, `_EloTracker` `[V]`.
   * Dipendenze interne: `src/shk/data/walkforward.py`, `src/shk/model/elo.py` `[V]`.

8. `src/shk/model/elo_fit.py`
   * Responsabilità: schema espansivo dei fit, log-loss di training, calibrazione Nelder-Mead di K, h, ν, e parametri congelati `[V]`.
   * Espone `[V]`: `SEASON_REGEX`; `BOUNDS_K` (5, 80), `BOUNDS_H` (0, 200), `BOUNDS_NU` (0.05, 3), `INITIAL_PARAMS` (30, 60, 1), `OPTIMIZER_*`, `GRID_K`, `GRID_H` (41 punti), `WALKFORWARD_CSV_COLUMNS` (15); `EloFitParams` (k, h, nu, c); `EloCalibrationResult`; `parse_season_start_year` (riga 96); `derive_fit_schedule(training, validation=None)`; `compute_training_log_loss(...)` → (loss, preds); `calibrate_single_fit`; `calibrate_all_fits`; `ELO_FITS` per "2000-01", "2010-11", "2020-21" (righe 321-340).
   * Dipendenze interne: `src/shk/data/split.py` (`SplitConfig`), `src/shk/model/elo.py` (`expected_score`), `src/shk/model/elo_predictor.py` (`predict_elo_fast`) `[V]`.

9. `src/shk/model/scoring.py`
   * Responsabilità: log-loss, ĝ, previsioni di validazione, allineamento alle quote, campioni di valutazione per serie di mercato `[V]`.
   * Espone `[V]`: costanti `PINNACLE_CLOSING_START_SEASON`, `PINNACLE_START_YEAR = 2012`, `DEVIG_METHODS`, `SERIES_NAMES` ("b365_prematch", "pinnacle_closing"), `MATCH_KEYS`, `CSV_COLUMNS` (11); `compute_log_loss` (ValueError se la probabilità realizzata è ≤ 0, nessun eps), `compute_mean_log_loss`, `compute_g_hat_terms`, `compute_g_hat`, `compute_cumulative_g_hat`; `generate_validation_predictions(df, fits, schedule)`; `align_predictions_with_odds(df_preds, df_raw)` (merge inner su MATCH_KEYS, aggiunge da df_raw solo colonne mancanti); `SeriesEvaluationData`; `prepare_series_evaluation(df_aligned, series, schedule)`.
   * Dipendenze interne: `src/shk/market/devig.py`, `src/shk/model/elo_fit.py` (`EloFitParams`, `parse_season_start_year`), `src/shk/model/elo_predictor.py` `[V]`.

10. `src/shk/model/monitoring.py` (1351 righe)
    * Responsabilità: serie per scenario dai residui, record dei CSV di C5.1, C5.2, C5.3, calibrazione di κ ed esecuzione appaiata della Baseline D `[V]`.
    * Espone `[V]`:
      * C5.1: `DRIFT_DETECTOR_CSV_COLUMNS` (12), `EXPECTED_MATCHES_PER_SEASON = 380`, `ScenarioSeries`, `extract_scenario_series`, `build_drift_records`, `generate_drift_detector_records`;
      * C5.2: `DAILY_Z_TEST_CSV_COLUMNS` (14), `TrainingBaselineStats`, `compute_training_baseline_stats`, `build_daily_z_test_records`, `generate_daily_z_test_records`;
      * C5.3: `BaselineDSeasonInput`, `KappaCalibrationRow`, `KappaCalibrationResult`, `assemble_baseline_d_season_input`, `calibrate_baseline_d_kappa` (default `calibration_seasons=("2010-11", "2020-21")`), `BASELINE_D_CSV_COLUMNS` (9), `BaselineDValidationSeasonData`, `BaselineDAgentResult`, `build_baseline_d_season_data`, `evaluate_baseline_d_agents`, `generate_baseline_d_records`.
    * Dipendenze interne: `src/shk/kelly/backtest.py`, `src/shk/kelly/metrics.py` (`max_drawdown`), `src/shk/kelly/staking.py`, `src/shk/model/elo_fit.py` (`parse_season_start_year`), `src/shk/model/scoring.py` (`align_predictions_with_odds`), `src/shk/stats/drift.py`, `src/shk/stats/false_rejection.py` `[V]`. Esterna: `scipy.stats.norm` `[V]`.

Moduli esclusi dai dieci, con una riga ciascuno:
* `src/shk/kelly/core.py` — `kelly_fraction`, `log_growth_rate`, `expected_final_wealth`; nessun import interno `[V]`.
* `src/shk/kelly/simulate.py` — `draw_outcomes`, `simulate_growth` (frazioni broadcastabili, log-ricchezza (M, T+1)), `log_wealth_paths` `[V]`.
* `src/shk/kelly/estimation.py` — `relative_perturbation`, `noisy_estimates` (clip in [0, 1]) `[V]`.
* `src/shk/kelly/scenarios.py` — `Scenario`, `BASE_SCENARIO`, `SUBTLE_SCENARIO`, `SEED = 20260927`, `spawn_generators`, `draw_scenario_outcomes`, `simulate_scenario`; importa `simulate.py` e `staking.py` `[V]`.
* `src/shk/kelly/metrics.py` — `final_log_wealth`, `median_growth_rate`, `median_final_wealth`, `mean_final_wealth`, `max_drawdown`, `fraction_below_start` `[V]`.
* `src/shk/stats/anova.py` — `OneWayAnovaResult`, `oneway_anova`, `oneway_anova_vectorized` `[V]`.
* `src/shk/stats/timeseries.py` — `generate_ar1_series` `[V]`.
* `src/shk/stats/false_rejection.py` — costanti C2 (`PHI_VALUES`, `N_OBS`, `N_SERIES`, `ALPHA = 0.05`, `SEED_C2`, `BLOCK_LENGTHS = (7, 20, 40)`, `N_BOOT = 999`, disegni, `CSV_COLUMNS`), `PhiStreams`, `RejectionResult`, `critical_value_nominal`, `monte_carlo_interval_99`, `make_design_labels`, `spawn_c2_generators`, `compute_nominal_rejection_rates`, `compute_calibrated_rejection_rates`; importa `anova.py`, `calibration.py`, `timeseries.py` `[V]`.
* `src/shk/data/loading.py` — `DEFAULT_DATA_DIR`, `load_all_seasons(data_dir, seasons=None)` `[V]`.
* `src/shk/data/coverage.py` — `COVERAGE_CSV_COLUMNS`, `NON_ODDS_COLUMNS`, `GROUP_TYPE_ORDER`, `ColumnClassification`, `classify_column`, `compute_coverage` `[V]`.
* `src/shk/data/walkforward.py` — `PREMATCH_IDENTIFIERS`, `LeakageError`, `get_prematch_whitelist`, `check_leakage`, `assert_no_leakage`, `walkforward_split`; importa `coverage.py` `[V]`.
* `src/shk/market/divergence.py` — `ODDS_BINS`, `ODDS_BIN_LABELS`, `REFERENCE_EDGE = 0.02`, `B365_ODDS_COLUMNS`, `DIVERGENCE_CSV_COLUMNS` (19), `assign_odds_bin`, `compute_divergence_table`; importa `devig.py` e, senza usarli, nomi di `data/split.py` `[V]`.
* `src/shk/model/elo.py` — `elo_delta`, `expected_score`, `elo_update`, `davidson_probabilities`, `constant_draw_probabilities` `[V]`.
* `src/shk/model/recalibration.py` — `PROB_LOWER_CLIP`, `PROB_UPPER_CLIP`, `OUTCOMES`, `CALIBRATION_CSV_COLUMNS` (16), `IsotonicModel`, `PlattModel`, `FitCalibrationMaps`, `compute_brier_scores`, `brier_score`, `compute_reliability_table`, `fit_isotonic_single`, `predict_isotonic_single`, `fit_platt_single`, `predict_platt_single`, `generate_fit_training_predictions`, `fit_all_calibration_maps`, `recalibrate_series_predictions`; importa `elo_fit.py`, `elo_predictor.py`, `scoring.py` `[V]`.
* `src/shk/model/residuals.py` — `REQUIRED_INPUT_COLUMNS`, `RESIDUALS_COLUMNS` (11), `compute_model_residuals(df, schedule, fits=None)`; importa `elo_fit.py` e `scoring.py` `[V]`.
* `__init__.py`: `src/shk/__init__.py` espone `__version__` `[V]`; `src/shk/kelly/__init__.py` re-esporta solo `kelly_fraction` e `log_growth_rate` con `__all__` `[V]`; gli altri quattro contengono solo una docstring `[V]`.

### 5. Punti di ingresso e flussi

Punti di ingresso:
* Undici script in `scripts/`, ognuno con `run_experiment()` senza parametri e `if __name__ == "__main__": run_experiment()` `[V]`.
* La suite pytest in `tests/` `[V]`.
* Uso come libreria (`import shk...`) `[V]`.
* La CI GitHub Actions, su push verso `main` e su `pull_request` `[V]`.
* Nessuno script chiama `calibrate_single_fit`, `calibrate_all_fits`, `calibrate_drift_detectors`, `calibrate_baseline_d_kappa`, `predict_elo_walkforward` o `diagnose_season_transitions` (ricerca in `src/` e `scripts/`) `[V]`. Le tarature che hanno prodotto `ELO_FITS`, i parametri dei detector e i κ si rieseguono solo dai test `[V]`.

Flusso 1 — Previsioni walk-forward e ĝ contro il mercato (`scripts/us_c4_2_g_hat.py`):
1. `run_experiment` → `data/split.read_split_config()` → `model/elo_fit.derive_fit_schedule(cfg)` `[V]`.
2. `data/split.load_by_role("history" | "training" | "validation")` → `data/loading.load_all_seasons(seasons=...)`; concatenazione e ordinamento stabile per `Date` nello script `[V]`.
3. `model/scoring.generate_validation_predictions(df, ELO_FITS, schedule)` → per ogni fit `model/elo_predictor.predict_elo_fast` → `_EloTracker.predict_match` / `consume_match` → `model/elo.elo_delta`, `davidson_probabilities`, `elo_update` `[V]`.
4. `model/scoring.align_predictions_with_odds(df_preds, df_full)` `[V]`.
5. `model/scoring.prepare_series_evaluation(..., "b365_prematch" | "pinnacle_closing", schedule)` → `market/devig.devig_additive` per le esclusioni, poi `devig_proportional`, `devig_additive`, `devig_power` sulle partite usate `[V]`.
6. `compute_mean_log_loss`, `compute_g_hat_terms`, `compute_cumulative_g_hat`; righe summary e cumulative assemblate nello script; CSV e PNG `[V]`.

Replica: `tests/test_us_c4_2_acceptance.py::test_recalculation_from_real_data_matches_csv` (righe 109-166) rifà i passi 1-5 con le stesse funzioni di libreria `[V]`. Diverge così:
* confronta solo le 6 righe summary, non le cumulative `[V]`;
* ricava ĝ con `compute_g_hat`, mentre lo script usa `np.mean(compute_g_hat_terms(...))` `[V]`;
* asserisce in più esclusioni nulle e `matches_used` 7220 e 3800 `[V]`.

`scripts/us_c4_3_calibration.py` ripete i passi 1-5 per conto suo `[V]`. `scripts/us_c4_1_elo_walkforward.py` costruisce le righe del CSV nello script (righe 52-105), e `tests/test_us_c4_1_acceptance.py::test_recomputed_predictions_match_csv` (righe 188-220) duplica quella logica `[V]`. Divergenze fra i due:
* lo script fa `str(gt_row["FTR"]).strip()`, il test usa `g["FTR"]` senza strip `[V]`;
* lo script controlla conteggi e chiavi riga per riga, il test no `[V]`;
* il test confronta i float con differenza assoluta ≤ 1e-12 `[V]`.

Flusso 2 — Residui del Modulo 1 e monitoraggio del drift (`scripts/us_c5_1_drift_detectors.py`, `scripts/us_c5_2_daily_z_test.py`):
1. Caricamento e schema come nel flusso 1, passi 1-2 `[V]`.
2. `model/residuals.compute_model_residuals(df, schedule, ELO_FITS)` `[V]`:
   * per la validazione: `scoring.generate_validation_predictions` + `align_predictions_with_odds`;
   * per il training: `elo_fit.compute_training_log_loss` su `df` ristretto alle stagioni ≤ fit, poi `align_predictions_with_odds`;
   * per tutte le righe: `scoring.compute_log_loss`.
3. C5.1: `model/monitoring.generate_drift_detector_records` → `extract_scenario_series` (22 serie da 380) → `build_drift_records` → `stats/drift.detector_params` + `run_drift_detector` `[V]`. Lo script riesegue `run_drift_detector` per la figura (righe 90-93) `[V]`.
4. C5.2: `model/monitoring.generate_daily_z_test_records` → `extract_scenario_series`, `compute_training_baseline_stats`, serie di training per fit → `build_daily_z_test_records` `[V]`. Quest'ultima chiama `stats/drift.spawn_c5_generators`, `calibrate_matchday_z_threshold` (→ `stats/calibration.calibrate_threshold`), `verify_matchday_z_thresholds` (→ `moving_block_indices`), `compute_matchday_z_scores`, `run_drift_detector` `[V]`.
5. CSV e PNG `[V]`.

Replica: i ricalcoli in `tests/test_us_c5_1_acceptance.py` (riga 274) e `tests/test_us_c5_2_acceptance.py` (riga 496) chiamano le stesse `generate_*_records`, senza logica duplicata `[V]`. `tests/test_us_c5_2_acceptance.py::test_versioned_csv_calibrated_alarms_match_thresholds` (righe 424-436) reimplementa la regola `|z| > soglia` sui valori del CSV `[V]`.

Flusso 3 — Baseline D sulle stagioni di validazione (`scripts/us_c5_3_baseline_d.py`):
1. Caricamento e residui come nel flusso 2, passi 1-2 `[V]`.
2. `model/monitoring.generate_baseline_d_records(df_residuals, df, schedule)` → per ogni stagione di validazione `build_baseline_d_season_data` `[V]`:
   * `assemble_baseline_d_season_input` → `scoring.align_predictions_with_odds`, quote `B365H/D/A`;
   * `stats/drift.run_drift_detector` per i due detector.
3. `evaluate_baseline_d_agents` (reference, d_adwin, d_page_hinkley) → `kelly/staking.compute_adaptive_lambda` → `select_baseline_d_bets` (→ `kelly_staking`) → `kelly/backtest.backtest_log_wealth` → `kelly/metrics.max_drawdown` `[V]`.
4. CSV (57 righe season + 3 total) e PNG delle differenze appaiate `[V]`.

Replica:
* `tests/test_us_c5_3_acceptance.py::test_real_data_recomputation_matches_versioned_csv` richiama `generate_baseline_d_records` `[V]`.
* `test_kappa_tie_breaking_synthetic` (righe 130-142) riscrive la regola di parità `max(KAPPA_GRID, key=lambda k: (total[k], k))` invece di chiamare `calibrate_baseline_d_kappa` (`src/shk/model/monitoring.py:988`) `[V]`.
* La calibrazione di κ si esegue solo in `test_frozen_kappas_match_real_data_calibration`, saltato senza dati `[V]`.

Altre repliche fuori dai tre flussi:
* C1.1: p, b, T, M, seed 20260905 e λ = 1.946 sono cablati sia in `scripts/us_c1_1_growth_vs_lambda.py` (righe 30-36, 124) sia in `tests/test_us_c1_1_acceptance.py` (righe 19-23 e seguenti, 78) `[V]`.
* C1.2: il test usa `1.1 * p` e `0.9 * p` (righe 62, 67), lo script `relative_perturbation(p, ±0.10)` `[V]`.

### 6. Modello dei dati

* Nessuna classe di dominio con comportamento, a parte `_EloTracker` (`src/shk/model/elo_predictor.py:212`) `[V]`. Il resto sono NamedTuple o dataclass frozen `[V]`.
* Strutture in circolo:
  * DataFrame E0 grezzo da `load_all_seasons`: colonne originali dei CSV più `season` (str `YYYY-YY`); `Date` datetime64 senza nulli, ordinato stabile per `season`, `Date` `[V]`. Le colonne di quota sono classificate da `classify_column` `[V]`.
  * `SplitConfig` (`src/shk/data/split.py`) `[V]`.
  * `schedule`: `dict[str, {"training": list[str], "validation": list[str]}]`, chiave = ultima stagione di training del fit, da `derive_fit_schedule` `[V]`.
  * `ELO_FITS: dict[str, EloFitParams]` `[V]`.
  * Previsioni Elo: DataFrame a 12 colonne (sezione 4, modulo 7) `[V]`.
  * Residui: DataFrame a 11 colonne `RESIDUALS_COLUMNS` (fit_through, role, season, Date, HomeTeam, AwayTeam, p_home, p_draw, p_away, FTR, log_loss) `[V]`.
  * `SeriesEvaluationData`: conteggi di esclusione, `df_used`, `p_model` e tre `q_*` (N×3), `outcomes` `[V]`.
  * Probabilità 1X2 come ndarray (N, 3) in ordine H, D, A `[V]`.
  * Monte Carlo C1: esiti bool (M, T), log-ricchezza float64 (M, T+1) con colonna 0 nulla `[V]`.
  * C5: `ScenarioSeries`, `TrainingBaselineStats`, `BaselineDSeasonInput`, `BaselineDBets`, `BacktestResult`, `BaselineDAgentResult`, `KappaCalibrationRow`/`Result` `[V]`.
  * I record CSV sono `list[dict]` con stringa vuota per i campi non applicabili, scritti con `csv.DictWriter` `[V]`.
* Collegamenti: `split.toml` → `SplitConfig` → `schedule` → previsioni per fit con `ELO_FITS` → residui → serie per scenario → record CSV `[V]`.
* Persistenza:
  * Nessun database: nessun driver fra le dipendenze di `pyproject.toml` `[V]`.
  * File: `config/split.toml` `[V]`; undici CSV in `results/` `[V]` (righe di dati: C1.1 51, C1.2 46, C2 24, C3.1 477, C3.2 29, C4.1 9 500, C4.2 33 066, C4.3 144, C5.1 66, C5.2 860, C5.3 60, da `wc -l` meno l'intestazione); undici PNG in `thesis/figures/` `[V]`.
  * Nessuna migrazione: gli schemi dei CSV sono costanti Python (`*_CSV_COLUMNS`) `[V]`.

### 7. Convenzioni in vigore

* Naming: snake_case per moduli, funzioni e variabili; PascalCase per le classi; UPPER_CASE per le costanti; prefisso `_` per gli helper interni `[V]`.
* Script e output: `scripts/us_c<story>_<n>_<nome>.py` → `results/<stesso nome>.csv` e `thesis/figures/<stesso nome>.png` `[V]`. `matplotlib.use("Agg")` prima di pyplot, `savefig(dpi=150)`, etichette delle figure in italiano `[V]`.
* Organizzazione: `kelly/` e `stats/` funzioni su array; `data/` I/O e split; `market/` quote; `model/` funzioni sui DataFrame e costruzione dei CSV di C4 e C5 `[V]`. `src/shk/kelly/` non importa da `shk.model` né da `shk.data` (ricerca degli import) `[V]`.
* Stile: type hints sulle funzioni pubbliche e docstring in stile NumPy con sezioni `Parametri`, `Restituisce`, `Solleva` nei file letti `[V]`.
* Errori: validazione in apertura, TypeError per i tipi e ValueError per i valori `[V]`. Eccezioni dedicate `TestSetLockedError` e `LeakageError` `[V]`. `RuntimeError` in `devig_power`, `prepare_series_evaluation`, `fit_platt_single` `[V]`. Nessun `try:`/`except` in `src/` e `scripts/` `[V]`.
* `assert` usati in codice di libreria: `src/shk/model/elo.py` righe 163, 168, 230, 281, 290, 345, 347, 354, 356 e `src/shk/model/elo_predictor.py:282` `[V]`.
* Logging e output: nessun `print(`, `logging` o `warnings.warn` in `src/`, `scripts/` e `tests/` `[V]`.
* Lingua: commenti e docstring in italiano nei file letti; identificatori, nomi dei test e messaggi delle `raise` in inglese (nessun messaggio di `raise` con parole italiane nella ricerca) `[V]`.
* RNG passato come argomento; flussi indipendenti con `SeedSequence.spawn` (`spawn_generators`, `spawn_c2_generators`, `spawn_c5_generators`) `[V]`.
* Test sui dati reali saltati se `data/raw/E0/` non ha CSV; `_has_real_data` è definita localmente in otto moduli di test `[V]`.

Incoerenze rilevate:
1. Messaggi di asserzione e motivi di skip in italiano: `tests/test_leakage.py` (360, 374, 384, 394-396, 407), `tests/test_us_c3_2_acceptance.py` (129-132, 161-163, 172, 184-187, 219, 243-256), `tests/test_us_c4_1_acceptance.py` (81, 108, 123, 128, 134, 172, 174, 243), `tests/test_us_c5_2_acceptance.py` (456-457, 464-465, 476, 479, 509-529), `tests/test_us_c5_3_acceptance.py` (265, 319, 323, 349, 353), `tests/test_split.py:480` `[V]`. Altrove sono in inglese (`tests/test_drift.py:63-64`, `tests/test_us_c2_acceptance.py`) `[V]`. Che un messaggio di asserzione conti come "messaggio di eccezione" ai fini della convenzione è un'interpretazione `[D]`.
2. Percorsi di output: C1.1, C1.2 e C2 (script) e `tests/test_us_c2_acceptance.py` (righe 179, 257, 315) usano percorsi relativi alla directory corrente; gli altri script e test usano `Path(__file__).resolve().parents[1]` `[V]`.
3. Validazione dei tipi interi: `draw_outcomes`, `noisy_estimates`, `expected_final_wealth`, `kelly_fraction` non controllano il tipo (`True` passa come 1); il codice da C2 in poi sì `[V]`.
4. Parsing della stagione ripetuto in più punti `[V]`:
   * `parse_season_start_year` pubblica (`src/shk/model/elo_fit.py:96`) e `_parse_season_start_year` privata (`src/shk/model/elo_predictor.py:91`), con `SEASON_REGEX` definita in entrambi i file;
   * regex inline in `src/shk/data/loading.py:101` e `src/shk/data/split.py:125` e `:258`;
   * `int(s.split("-")[0])` in `src/shk/data/split.py:162`, `:279`, `:292` e `scripts/us_c5_2_daily_z_test.py:65`.
5. Due calcoli di log-loss: `compute_training_log_loss` taglia p a 1e-15 (`src/shk/model/elo_fit.py:200`), `compute_log_loss` solleva ValueError per p ≤ 0 (`src/shk/model/scoring.py:114`) `[V]`. Lo stesso clip c'è nella baseline (`src/shk/model/elo_fit.py:277`) `[V]`.
6. Import non usati, ciascuno presente una sola volta nel file `[V]`:
   * `src/shk/market/divergence.py`: `Path` (riga 4), `DEFAULT_SPLIT_CONFIG_PATH`, `SplitConfig`, `read_split_config` (riga 10); creano una dipendenza `market` → `data` non necessaria;
   * `src/shk/model/recalibration.py`: `ELO_FITS`, `derive_fit_schedule`, `parse_season_start_year`, `MATCH_KEYS`;
   * `src/shk/model/residuals.py`: `MATCH_KEYS`;
   * `Any` in `src/shk/model/elo.py:4` e `src/shk/model/scoring.py:3`.
   In più, `generate_fit_training_predictions` riceve `fit_through` senza usarlo (`src/shk/model/recalibration.py:322-336`) `[V]`.
7. La dimensione del matchday è cablata invece di usare `MATCHDAY_SIZE` `[V]`:
   * `src/shk/model/monitoring.py:258` (`idx_int // 10 + 1`) e `:429` (`38.0 * alpha`);
   * `scripts/us_c5_1_drift_detectors.py:68-69, 97, 114, 134`;
   * `scripts/us_c5_2_daily_z_test.py:103, 137` (1.9).
8. `src/shk/stats/drift.py` importa pandas e restituisce DataFrame (`calibrate_*`), mentre il resto di `stats/` lavora su array `[V]`.
9. Docstring non aggiornate in `src/shk/model/monitoring.py` `[V]`:
   * quella di modulo (righe 1-6) cita solo Task 28 / US-C5.1, ma il modulo copre anche C5.2 e C5.3;
   * il commento alla riga 57 attribuisce `DAILY_Z_TEST_CSV_COLUMNS` a "C5.2 e C5.3", ma C5.3 usa `BASELINE_D_CSV_COLUMNS`.
   Anche la docstring di `scripts/us_c4_1_elo_walkforward.py` dice "Script di calibrazione", ma lo script usa `ELO_FITS` senza calibrare `[V]`.
10. `verify_matchday_z_thresholds` converte `int(n_resamples)` (riga 665) prima del controllo di tipo (riga 666) `[V]`.
11. Docstring di `src/shk/stats/calibration.py`: lo schema (a) indica come dato dell'ANOVA F "la serie della risposta" (righe 18-20), il principio (c) dice che imporre H₀ spetta al chiamante (righe 35-39) `[V]`.
12. Politica sul CSV versionato mancante: `tests/test_us_c4_1_acceptance.py` salta (righe 107-108, 133-134, 173-174), mentre i test di C4.2, C4.3, C5.2 e C5.3 asseriscono che esiste `[V]`.
13. Test con logica d'eccezione: `tests/test_us_c3_2_acceptance.py:245-256` usa `try`/`except ValueError` dentro il test `[V]`.

### 8. Test

* Dove: `tests/`, 30 moduli, nessun `conftest.py` `[V]`. Nella ricerca risultano 312 definizioni di funzione `test_*`, prima della parametrizzazione `[V]`.
* Tipi `[V]`:
  * unitari su dati sintetici: `test_kelly_core`, `test_simulate`, `test_estimation`, `test_staking`, `test_metrics`, `test_backtest`, `test_anova`, `test_timeseries`, `test_calibration`, `test_data_loading`, `test_coverage`, `test_split`, `test_devig`, `test_leakage`, `test_elo`, `test_elo_predictor`, `test_scoring`, `test_recalibration`, `test_residuals`, `test_drift`;
  * accettazione `test_us_c*_acceptance.py` (dieci file): sintetici, controlli sui CSV e PNG versionati (girano anche senza dati) e ricalcoli dai dati reali (saltati senza `data/raw/E0/`).
* Marker `slow` `[V]`: tutti i 4 test di `tests/test_us_c1_1_acceptance.py`, 5 di `tests/test_us_c1_2_acceptance.py`, 3 funzioni di `tests/test_us_c2_acceptance.py` (righe 310, 349, 365, l'ultima parametrizzata su tre φ), 1 di `tests/test_us_c4_1_acceptance.py` (riga 239).
* Come si lanciano: sezione 2 `[V]`/`[D]` come indicato lì. Esiti, tempi e coperture numeriche non riportati: servirebbe eseguire la suite.
* Test noto in rosso: `tests/test_us_c2_acceptance.py::test_acceptance_calibrated_phi_zero_within_mc_interval` (righe 349-362, slow) `[D]` sull'esito (da `.agent/BACKLOG.md`, non eseguito); il codice del test è quello descritto nel backlog `[V]`.

Copertura desunta dai file di test (ricerca dei nomi in `tests/*.py`):
* Funzioni pubbliche che non compaiono in nessun test `[V]`: `expected_final_wealth`, `spawn_c2_generators`, `calibrate_adwin`, `calibrate_page_hinkley`, `calibrate_all_fits`, `generate_fit_training_predictions`, `assemble_baseline_d_season_input`. Le ultime quattro e `spawn_c2_generators` sono raggiunte solo indirettamente, tramite altre funzioni `[V]`.
* Solo importate, mai chiamate direttamente `[V]`:
  * `build_baseline_d_season_data` (`tests/test_us_c5_3_acceptance.py:41`);
  * `extract_scenario_series`, `build_drift_records` (`tests/test_us_c5_1_acceptance.py:26-27`);
  * `build_daily_z_test_records` (`tests/test_us_c5_2_acceptance.py:29`);
  * `recalibrate_series_predictions` in `tests/test_recalibration.py:19`.
* Chiamate solo in test saltati senza dati reali, quindi mai in CI `[V]`:
  * `calibrate_drift_detectors` (`tests/test_drift.py:289`);
  * `recalibrate_series_predictions` (`tests/test_us_c4_3_acceptance.py:168-169`);
  * `calibrate_baseline_d_kappa` (`tests/test_us_c5_3_acceptance.py:158`);
  * `generate_baseline_d_records` (riga 336; altrove solo `inspect.signature`, riga 256);
  * `load_by_role` sui ruoli reali;
  * `diagnose_season_transitions` sui dati reali (`tests/test_elo_predictor.py:351`).
  `diagnose_season_transitions` ha anche un uso sintetico, ma non verificato in questa sessione `[D]`.
* Tutte le altre funzioni pubbliche elencate in sezione 4 compaiono in almeno un test con chiamata diretta `[V]`.
* CSV versionati senza test che li legga: `results/us_c1_1_growth_vs_lambda.csv`, `results/us_c1_2_estimation_error.csv`, `results/us_c3_1_data_coverage.csv` `[V]`.
* PNG senza test di esistenza `[V]`: `us_c1_1`, `us_c1_2`, `us_c3_1`, `us_c4_1` (`PNG_PATH` definito ma mai usato in `tests/test_us_c4_1_acceptance.py:25`), `us_c5_1`, `us_c5_3`.

Asserzioni che dipendono da seed fisso, tolleranze numeriche o costanti empiriche (file:riga) `[V]`:
* `tests/test_us_c1_1_acceptance.py`: seed 20260905 (23, 47, 73, 92); argmax a λ = 1 (37); drawdown con tolleranza −0.01 (63); |g| < 0.002 a λ = 1.946 (82).
* `tests/test_us_c1_2_acceptance.py`: `SEED` via `spawn_generators`; `g_under == 0.0` esatto (73); |Var(c) − rif| < 0.005 (96); Var(c) > 1 (117); λ* > quarto-Kelly (140, 163).
* `tests/test_kelly_core.py`: 0.020136 e −0.002447 con abs 1e-6 (32, 39).
* `tests/test_simulate.py`: seed 999, |media − p| < 0.01 (32-38).
* `tests/test_estimation.py`: seed 20260927, tolleranza 0.001 su media e std (44-53).
* `tests/test_timeseries.py`: seed 20260928, varianza entro il 15% e autocorrelazione entro 0.02 (52-88).
* `tests/test_anova.py`: seed da 20260928 a 20260933 e 98765; tolleranze relative 1e-12 e 1e-10 (57-220).
* `tests/test_calibration.py`: seed vari; `th1 != th3` dipende dai seed 12345 e 54321 (283-293).
* `tests/test_us_c2_acceptance.py`: `SEED_C2`; intervallo MC al 99% (56, 74, 359); monotonia (92); `math.isclose` rel_tol 1e-12 sui float del CSV (200-205, 333-338).
* `tests/test_devig.py`: valori di riferimento entro 5e-6 e k entro 5e-5 (19-63); seed 20260929 (76, 162); soglia S > 1.02 (165).
* `tests/test_elo.py`: tabella di riferimento con s = 200 e tolleranza 5e-4 (251-260).
* `tests/test_drift.py`: seed 20260930 per il salto sintetico (51); seed 20261002, 42, 101, 102 (359, 437, 442, 461); conteggi esatti di allarmi sui dati reali, 0 ADWIN e 1 + 1 Page-Hinkley (324-335), legati all'implementazione di river.
* `tests/test_residuals.py`: medie di log-loss di riferimento entro 5e-7 (311-326); confronto con `compute_training_log_loss` entro 1e-12 (345).
* `tests/test_us_c5_2_acceptance.py`: tassi di verifica nell'intervallo MC al 99% sul CSV versionato (451-457); conteggi 722/114/6/18/860 (310-318); atteso 1.9 (380, 395).
* `tests/test_us_c3_2_acceptance.py`: overround medio in [0.01, 0.15] (172); spread relativo massimo in [10, ∞) (180-187); ricalcolo rel_tol e abs_tol 1e-12 (248).
* `tests/test_us_c4_1_acceptance.py`: conteggi per fit e ruolo (144-153); ricalibrazione slow con rel_tol 1e-9 (258-261); ricalcolo entro 1e-12 (236).
* Conteggi reali cablati: `tests/test_split.py:483-491` (1140, 7220, 3204), `tests/test_leakage.py:434-436`, `tests/test_us_c4_2_acceptance.py:137-139` (7220, 3800), `tests/test_elo_predictor.py:366-386` (29 transizioni, 22 o 20 squadre).

### 9. Zone fragili

* Tarature congelate non riproducibili dagli script: nessuno script chiama `calibrate_single_fit`, `calibrate_drift_detectors` o `calibrate_baseline_d_kappa` `[V]`. `ELO_FITS`, i parametri dei detector e i κ si riverificano solo da test locali (uno slow, gli altri saltati senza dati) `[V]`.
* Test che replicano la logica invece di chiamarla `[V]`:
  * `tests/test_us_c5_3_acceptance.py:130-142` (regola di parità di κ);
  * `tests/test_us_c4_1_acceptance.py:188-220` (righe del CSV C4.1);
  * parametri di C1.1 cablati sia nello script che nel test.
* Accoppiamento fra CSV versionati `[V]`:
  * `tests/test_us_c4_3_acceptance.py::test_raw_g_hat_matches_t23` confronta il CSV di C4.3 con quello di C4.2;
  * `tests/test_us_c5_2_acceptance.py::test_versioned_csv_alarms_match_c5_1` confronta C5.2 con C5.1.
  Rigenerarne uno solo li fa divergere `[D]`.
* Rieseguire uno script sovrascrive CSV e PNG versionati (`open(..., mode="w")`, `savefig`) `[V]`.
* Dipendenze senza vincoli e CI senza lockfile `[V]`: la CI installa le ultime versioni di numpy, scipy, pandas e river. I conteggi esatti di allarmi (`tests/test_drift.py:324-335`, CSV di C5.x) dipendono da river 0.26.1 `[D]`. `uv.lock` è disallineato da `pyproject.toml` (mancano pandas e river) `[V]`.
* Test slow e test sui dati reali non girano in CI: `addopts`, e `data/raw/*` ignorato `[V]`.
* Il blocco del test set è aggirato da due percorsi ammessi `[V]`:
  * `tests/test_data_loading.py:312` chiama `load_all_seasons` su tutta la directory, 2023-24 compreso;
  * `scripts/us_c3_1_data_coverage.py:29` fa lo stesso, e `results/us_c3_1_data_coverage.csv` contiene 35 righe del 2023-24.
  Il test di guardia AST (`tests/test_split.py:428-454`) scandisce solo `src/` e `scripts/` `[V]`.
* `load_by_role` richiede che esista il file di ogni stagione configurata, test compreso, anche per caricare `training` (`src/shk/data/split.py:272-277`) `[V]`.
* `walkforward_split` è una funzione generatore (contiene `yield`, `src/shk/data/walkforward.py:229`): le validazioni scattano alla prima iterazione, non alla chiamata `[V]`.
* `classify_column` solleva ValueError su colonne non catalogate (`src/shk/data/coverage.py:292`) `[V]`; `compute_coverage` e la whitelist del fornitore walk-forward dipendono da essa `[V]`. File E0 con colonne nuove fermerebbero audit e fornitore `[D]`.
* `devig_power` solleva RuntimeError se anche un solo mercato non converge (`src/shk/market/devig.py:189-193`) `[V]`. `fit_platt_single` solleva RuntimeError se L-BFGS-B non converge (`src/shk/model/recalibration.py:300-303`) `[V]`.
* `noisy_estimates` può restituire p̂ = 1 per saturazione `[V]`; con `lam ≥ 1` `kelly_staking` dà frazioni ≥ 1, che `simulate_growth` rifiuta `[V]`.
* `elo_predictor.py` itera solo sulle colonne di `_CALC_COLS` nel percorso veloce (`df[_CALC_COLS]`, riga 475) `[V]`: un calcolo che usa un'altra colonna deve aggiungerla lì `[D]`.
* Valori cablati legati a costanti di libreria `[V]`:
  * `scripts/us_c5_3_baseline_d.py:75-76, 84`: etichetta "κ = 1.0" e asse fissato a ±0.05;
  * `scripts/us_c5_2_daily_z_test.py`: 1.9 cablato;
  * matchday 10/38 cablato in `monitoring.py` e negli script C5 (incoerenza 7).
  Cambiare `KAPPA_*` o `MATCHDAY_SIZE` non aggiornerebbe le figure `[D]`.
* Duplicazione del parsing della stagione (incoerenza 4) e delle due log-loss (incoerenza 5) `[V]`.
* `_has_real_data` duplicata in otto moduli di test con la stessa espressione `[V]`.
* Test di docstring: `tests/test_calibration.py:322-338`, `tests/test_staking.py:405-410` e `tests/test_us_c5_3_acceptance.py:122-127` cercano frasi esatte; la correzione della docstring di `calibration.py` deve preservarle `[V]`.
* CI (`.github/workflows/test.yml`): referenzia solo `pyproject.toml` (extra `dev`) e `pytest`, entrambi presenti; nessun file o comando mancante `[V]`. Nessuna cache e nessun uso di `uv.lock` `[V]`.
* Branch `pre-c4` con il commit "Rimuove .agent dal tracciamento" (043b9a5), non in `main` `[V]`. Un merge di quel branch toglierebbe `.agent/` dal tracciamento, contro `.agent/PROTOCOLLO.md` ("Aggiungi .agent/ al repository") `[D]`; il contenuto del commit non è stato ispezionato.
* TODO, FIXME, XXX, HACK: nessuno in `src/`, `scripts/`, `tests/`, `config/`, `.github/` `[V]`.

### 10. Limiti di questa mappa

* Non eseguito nulla del progetto: né test, né script, né import di `shk` `[V]`. Esiti della suite, tempi, hash dei CSV e conformità dei CSV versionati al codice attuale non sono verificati.
* Non ispezionati: contenuto dei CSV in `data/raw/E0/`, dei PNG, dei report `.agent/report/T*.md`, del commit `043b9a5` e del branch `pre-c4`, delle pagine di `uv.lock` oltre il blocco del pacchetto, di `.venv/` oltre `pyvenv.cfg` e dei nomi dei `dist-info` `[V]`.
* Letti per intero: tutti i moduli di `src/shk/`, tutti gli script, e i test `test_kelly_core`, `test_metrics`, `test_simulate`, `test_estimation`, `test_staking`, `test_anova`, `test_timeseries`, `test_calibration`, `test_us_c1_1`, `test_us_c1_2`, `test_us_c2`, `test_split`, `test_devig`, `test_us_c3_2`, `test_us_c4_1`, `test_us_c4_2`, `test_recalibration` `[V]`.
* Letti in parte o solo tramite ricerca: `test_data_loading`, `test_leakage`, `test_coverage`, `test_elo`, `test_elo_predictor`, `test_scoring`, `test_backtest`, `test_residuals`, `test_drift`, `test_us_c4_3`, `test_us_c5_1`, `test_us_c5_2`, `test_us_c5_3` `[V]`. Le affermazioni su questi file valgono per le righe citate.
* Sezioni in prevalenza `[D]`: la 2 per i comandi locali; il resto è in prevalenza `[V]`.
* Discrepanze notate rispetto a `.agent/SCHEDA.md`:
  * `FLOAT_CSV_COLUMNS` è definito in `tests/test_us_c2_acceptance.py:33`, non in `src/shk/stats/false_rejection.py` `[V]`;
  * il test sintetico di divergenza include il mercato 1.25 / 6.00 / 11.0 (`tests/test_us_c3_2_acceptance.py:65-67`) `[V]`;
  * `KappaCalibrationRow` esiste in `src/shk/model/monitoring.py:744` e manca dall'elenco delle classi della scheda `[V]`;
  * la scheda parla di un branch locale `C5`, che non esiste più `[V]`.
* Discrepanza rispetto alla mappa precedente: il test di guardia AST non ispeziona "l'intero repository" ma solo `src/` e `scripts/` (`tests/test_split.py:443`) `[V]`.
* Un import non usato è stato rilevato solo per i nomi controllati (conteggio = 1); non è stata fatta un'analisi completa degli import `[V]`.

Domande che farei:
1. Il gestore di dipendenze canonico è pip o uv? `uv.lock` va tenuto?
2. Le tarature (`ELO_FITS`, parametri dei detector, κ) devono essere riproducibili da uno script versionato, o bastano i test?
3. Il branch `pre-c4` con "Rimuove .agent dal tracciamento" è ancora attivo, o è un residuo?
4. I messaggi di asserzione e i motivi di skip rientrano nella regola "messaggi delle eccezioni in inglese"?
5. La lettura del 2023-24 in `scripts/us_c3_1_data_coverage.py` e in `tests/test_data_loading.py:312` è un'eccezione voluta al blocco del test set?
6. Gli script C1.1, C1.2 e C2 vanno lanciati sempre dalla radice, o ci sono altri modi d'uso?
7. Qual è lo stato della CI su `736f5cd` e sui PR di C5?
8. La convenzione "funzioni pure su array" vale anche per `src/shk/stats/drift.py`, che restituisce DataFrame?

### 11. Comandi eseguiti

Comandi shell (Bash, tutti preceduti da `cd /c/Users/malse/Documents/GitHub/structural_hybrid_kelly &&`):
1. `pwd && git --no-optional-locks status && git --no-optional-locks status -sb`
2. `git log --oneline -n 5 && git branch -vv && git remote -v`
3. `ls -la && find . -path ./.venv -prune -o -path ./.git -prune -o -type f -print | sort`
4. `wc -l src/shk/*.py src/shk/*/*.py scripts/*.py tests/*.py`
5. `for f in src/shk/__init__.py src/shk/*/__init__.py; do echo "=== $f"; cat "$f"; done`
6. ciclo `for n in <113 nomi di funzioni pubbliche>; do grep -lw "$n" tests/*.py ...; done`
7. ciclo `for n in <13 nomi>; do grep -nw "$n" tests/*.py | grep -v "^\s*#"; done`
8. `grep -n "^import\|^from" scripts/*.py | grep -v ... | awk ... | sort | uniq -c | sort -rn | head -40; grep -ln "os.path.join(\"results\"\|os.makedirs(\"results\"" scripts/*.py`
9. funzione `chk()` con `grep -cw <nome> <file>` su divergence.py, recalibration.py, elo.py, residuals.py, scoring.py, elo_fit.py, monitoring.py
10. `ls .venv/Lib/site-packages | grep -iE "^(numpy|scipy|pandas|matplotlib|river|pytest|narwhals|structural|_?editable|__editable__).*(dist-info|\.pth)$"`
11. `git branch -a -vv && git log --oneline -n 8 pre-c4 && git log --oneline main..pre-c4 | head -20 && git log -1 --format='%H %ci %s' main && git log -1 --format='%H %ci %s' pre-c4`
12. `git log --oneline -n 3 -- .agent/MAPPA.md && git log --oneline -n 3 -- .agent/report/T32.md && git --no-optional-locks status --ignored --short && git diff --stat 27cf7a4 736f5cd`
13. `grep -nw "build_baseline_d_season_data\|calibrate_baseline_d_kappa\|...|compute_training_baseline_stats" tests/*.py | grep -v ...`
14. `wc -l results/*.csv && grep -c "^2023-24," results/us_c3_1_data_coverage.csv; grep -c "2023-24" results/us_c4_1_elo_walkforward.csv results/us_c5_1_drift_detectors.csv results/us_c5_2_daily_z_test.csv results/us_c5_3_baseline_d.csv`
15. `grep -cw PNG_PATH tests/test_us_c4_1_acceptance.py; grep -n "png" tests/test_us_c5_1_acceptance.py tests/test_us_c5_3_acceptance.py | head; grep -n "^name\|runs-on\|python-version\|run:" .github/workflows/test.yml`

Strumenti di lettura e ricerca (nessuno scrive):
* Glob `**/*` sulla radice (una volta).
* Read:
  * `.agent/PROTOCOLLO.md`, `.agent/SCHEDA.md` (due pagine), `.agent/BACKLOG.md`;
  * `.agent/MAPPA.md` precedente, in due pagine (righe 1-397, poi 398-674);
  * `pyproject.toml`, `.gitignore`, `.github/workflows/test.yml`, `config/split.toml`, `.git/info/exclude`, `.venv/pyvenv.cfg`;
  * tutti i moduli di `src/shk/` diversi dagli `__init__.py` e tutti gli undici script;
  * i test elencati in sezione 10, con letture parziali (offset) di `test_data_loading.py`, `test_leakage.py`, `test_drift.py`, `test_elo.py`, `test_us_c4_3_acceptance.py`, `test_us_c5_2_acceptance.py`, `test_us_c5_3_acceptance.py`.
* Grep: marker e skip pytest; conteggio delle funzioni `test_`; tolleranze; seed; `_has_real_data` e percorsi; asserzioni numeriche nei test di C4 e C5; definizioni pubbliche in `src/shk`; import `shk` in `src/`; `print`/`logging`/`warnings.warn`; `os.environ`/`getenv`/`dotenv`; `TODO|FIXME|XXX|HACK`; `try|except|assert` in `src/` e `scripts/`; messaggi di `raise` in italiano; commenti in inglese; nomi di test in italiano; messaggi di asserzione in italiano; `pytest.skip`/`reason=`; voci di `uv.lock` (due ricerche); riferimenti a CSV e PNG nei test; chiamate alle funzioni di taratura in `src/` e `scripts/`; definizioni di funzione nei test C4 e C5.

Scrittura: unicamente `.agent/MAPPA.md` (questo file, sovrascritto). Il primo tentativo di scrittura è stato rifiutato dallo strumento perché il file precedente non era stato letto per intero; ho letto le righe 398-674 e riscritto.

Dichiarazioni:
* Nessun comando git fuori da status, log, branch, remote -v, diff. A `git status` ho aggiunto `--no-optional-locks` per non aggiornare l'indice; ho usato anche le varianti `-sb`, `--ignored --short` e `branch -a -vv`.
* Ho usato comandi shell di sola lettura non git (`ls`, `find`, `wc`, `cat`, `grep`, `awk`, `sort`, `uniq`, `head`, `xargs`, `basename`, `tr`) `[V]`.
* Nessun codice del progetto eseguito, nessun test, nessun `uv`, nessun import di `shk` `[V]`.
* Nessun comando shell fallito né ripetuto; l'unico tentativo fallito è la scrittura descritta sopra `[V]`.
* `.pytest_cache/` e i `__pycache__/` esistevano già prima di questa sessione (date di settembre in `ls -la` per `.pytest_cache`) `[V]`.
