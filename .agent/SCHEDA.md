# Scheda del progetto
Origine: mappa completa del 2026-10-07 a 736f5cd, report fino a R6@2026-10-07. Riferimenti: la numerazione R_n riparte da R1 a ogni mappa. Serie 2026-10-07: R1 = mappa a 736f5cd, R2–R6 = risposte di Cline alla chat di scheda; un riferimento senza data appartiene a questa serie. @2026-09-29c: R1 = mappa a 27cf7a4. @2026-09-29b: R1 = mappa a 90a77a1, R2–R6 = risposte di Cline, R7–R33 = report di T20–T25. @2026-09-29 senza suffisso: R1 = mappa a 115e600, R2–R46 = report di T14–T19. @2026-09-28 e @2026-09-27: serie più vecchie. Un fatto con riferimento anteriore al 2026-10-07 riguarda un file che C5 non ha toccato [V, R2]. I valori misurati in T26–T32 stanno in .agent/report/T26.md … T32.md e qui compaiono solo quelli riletti in R1–R6 [D]

## Stato repo
Radice: C:\Users\malse\Documents\GitHub\structural_hybrid_kelly [V, R1]
Alla mappa: branch main a 736f5cd "C5 (#20)", 2026-10-02 14:18:43 +0200; working tree pulito, nessun file staged, modificato o non tracciato [V, R1]
main allineato a origin/main rispetto all'ultimo fetch locale; nessun git fetch eseguito, stato reale del remote non verificato [V, R1]
Remote origin: https://github.com/Fede046/structural_hybrid_kelly.git, fetch e push [V, R1]
Ultimi cinque commit su main: 736f5cd "C5 (#20)", 27cf7a4 "C4 (#18)", 90a77a1 "C3 (#17)", 115e600 "C2 (#16)", 1e7813d "C1 (#14)" [V, R1]
Commit di story su main: 115e600 = S2/C2, 90a77a1 = S3/C3, 27cf7a4 = S4/C4 [V, R1@2026-09-29, R1@2026-09-29b, R1@2026-09-29c]; 736f5cd = S5/C5 [V, R1 e R2]. Ogni story entra in main come un solo commit e il branch di lavoro poi sparisce: C5 non esiste più né in locale né su origin [V, R1]. Il meccanismo è lo squash merge del PR [D]
736f5cd rispetto a 27cf7a4 cambia 32 file [V, R2]:
- modificati: .agent/BACKLOG.md, .agent/MAPPA.md, .agent/SCHEDA.md, pyproject.toml, src/shk/kelly/staking.py, tests/test_staking.py;
- aggiunti: .agent/report/T26.md … T32.md; src/shk/kelly/backtest.py, src/shk/model/residuals.py, src/shk/model/monitoring.py, src/shk/stats/drift.py; script, CSV e PNG us_c5_1_drift_detectors, us_c5_2_daily_z_test, us_c5_3_baseline_d; tests/test_backtest.py, test_drift.py, test_residuals.py, test_us_c5_1_acceptance.py, test_us_c5_2_acceptance.py, test_us_c5_3_acceptance.py.
Nessun altro file è cambiato in C5: moduli di C1–C4, config/split.toml, uv.lock, .gitignore, CI e .agent/PROTOCOLLO.md sono quelli di 27cf7a4 [V, R2]
Branch [V, R1 e R3]:
- locali: main e pre-c4 (traccia origin/pre-c4); remoti: origin/HEAD → origin/main, origin/main, origin/pre-c4;
- pre-c4 parte da 90a77a1 con due commit assenti da main: 043b9a5 (2026-10-02 00:16:55, "Rimuove .agent dal tracciamento") toglie dall'indice 23 file di .agent/ (BACKLOG, MAPPA, PROTOCOLLO, SCHEDA, report T1–T19); 5249f9b (00:22:56, "fix") aggiunge solo la riga .agent/ in coda a .gitignore;
- nessuna delle due modifiche è in main: il .gitignore di main non contiene "agent" e .agent/ è tracciato.
File ignorati presenti: .pytest_cache/, .venv/, data/raw/E0/, __pycache__/ in scripts, tests, src/shk e nei cinque sottopacchetti [V, R1]
Albero tracciato a 736f5cd [V, R1]:
- src/shk/ con kelly/, stats/, data/, market/, model/;
- tests/ con 30 moduli, nessun conftest.py; scripts/ con 11 script;
- results/ con 11 CSV e .gitkeep; thesis/figures/ con 11 PNG e .gitkeep;
- config/ con split.toml e .gitkeep; data/raw/ con .gitkeep; .github/workflows/test.yml;
- .agent/ con PROTOCOLLO.md, BACKLOG.md, MAPPA.md, SCHEDA.md, report/T1.md … T32.md;
- alla radice pyproject.toml, uv.lock, .gitignore, LICENSE; nessun README.
data/raw/E0/ contiene 31 CSV, da 1993-94.csv a 2023-24.csv, non versionati (.gitignore esclude data/raw/* tranne .gitkeep) [V, R1]. Li ha scaricati il programmatore il 2026-09-29, solo nella finestra di KellyBench [V, R6 e R7@2026-09-29]
config/split.toml: chiavi frozen_on, test_unlocked, test_unlocked_on, training, validation, test [V, R1]; test_unlocked = false [V, R28 e R38@2026-09-29]; non toccato in C5 [V, R2], fra 90a77a1 e 27cf7a4 non verificato [D]. Contenuto identico a quello di 2cea094 (2026-09-29 11:47:18), raggiungibile solo dalla reflog locale [V, R3–R6@2026-09-29b]
Nessun .env [V, R1]

## Stack e comandi
Pacchetto structural-hybrid-kelly 0.1.0 (pyproject.toml e src/shk/__init__.py), importabile come shk da src/shk/ [V, R1]
requires-python >= 3.11; la CI usa Python 3.12 [V, R1]
Build hatchling, wheel con packages = ["src/shk"]; nessun [project.scripts] [V, R1]. Build con hatch build o python -m build [D]
Dipendenze runtime: numpy, scipy, matplotlib, pandas, river, senza vincoli di versione; extra dev: pytest; statsmodels non c'è [V, R1]. river è entrato in C5 [V, confronto fra R1@2026-09-29c e R1]
uv.lock (version 1, revision 3): requires-dist con solo matplotlib, numpy, scipy, pytest; non contiene pandas né river; non toccato in C5 [V, R1 e R2]. Nessun file dichiara il gestore canonico [D]. Decisione S3: fonte di verità pyproject.toml, uv.lock aggiornato a mano dal programmatore [V, BACKLOG.md]
CI (.github/workflows/test.yml): trigger su push verso main e su pull_request; Python 3.12; python -m pip install --upgrade pip, pip install -e ".[dev]", pytest -v; nessuna cache, uv.lock non usato [V, R1]
Esecuzioni note della CI [V, log forniti dal programmatore il 2026-09-28 e il 2026-09-29]:
- 2026-09-28: Linux, Python 3.12.14, pytest 9.1.1; prima di T13 falliva sul confronto dei float come stringhe;
- 2026-09-29, branch C4 dopo T24: 263 raccolti, 15 deselezionati, 237 passati, 9 saltati, 2 falliti, corretti in T25.
Esito della CI dopo T25, sul PR di C5 e su 736f5cd, compresa l'installazione di river: non noto [D]
Venv .venv: Python 3.12.7 creato con python -m venv dall'interprete di Anaconda; numpy 2.5.2, scipy 1.18.1, pandas 3.0.6, matplotlib 3.11.1, river 0.26.1, narwhals 2.26.0, pytest 9.1.1; shk installato editable [V, R1]
Interprete: Cline esegue ogni comando Python con .\.venv\Scripts\python.exe dalla radice (es. .\.venv\Scripts\python.exe -m pytest -v). Il Python di default del suo terminale è C:\Users\malse\anaconda3\python.exe, senza shk [V, R6 e R7@2026-09-28; decisione del programmatore 2026-09-28]
Installazione: pip install -e ".[dev]" in CI [V, R1]; in locale con l'interprete del venv [D]. uv sync non installerebbe pandas né river [D]
Test: pytest -v; pyproject.toml ha addopts = "-m 'not slow'" e registra il marker slow [V, R1]. Solo slow: pytest -m slow; tutti: pytest -o addopts="" [D]
Suite: 30 moduli, 312 definizioni test_* prima della parametrizzazione [V, R1]. Conteggi ed esiti dopo T32: nei report, non qui [D]. Ultimo dato noto: dopo T25, 248 veloci verdi e 15 deselezionati in 50.28 s [V, R33@2026-09-29b]
Test slow: 15, cioè i 4 di test_us_c1_1_acceptance.py, 5 di test_us_c1_2_acceptance.py, 3 funzioni di test_us_c2_acceptance.py (5 test, l'ultima parametrizzata su tre φ) e 1 di test_us_c4_1_acceptance.py; C5 non ne ha aggiunti [V, R1; conteggio ricalcolato dal supervisore]. Ultimi esiti: dei 14 di C1 e C2, 13 verdi e 1 rosso per il risultato noto, circa 117 s [V, R14@2026-09-28]; quello di C4 verde in 119.09 s [V, R23@2026-09-29b]
Esperimenti: python scripts/<nome>.py, con run_experiment() chiamata dal blocco __main__ [V, R1]:
- C1.1, C1.2 e C2 scrivono in results/ e thesis/figures/ relativi alla directory corrente: vanno lanciati dalla radice [V i percorsi, R1; D la regola];
- gli altri otto calcolano i percorsi da Path(__file__).resolve().parents[1] [V, R1];
- C3.2, C4.x e C5.x leggono i dati con load_by_role e richiedono data/raw/E0/; C3.1 usa load_all_seasons su tutta la directory [V, R1].
Durate e SHA256 noti dei CSV:
- C1.2: circa 70 s; CSV identici fra due esecuzioni [D, era V R16@2026-09-27];
- C2: circa 90 s; SHA256 6711B906A5D0170124BE816BAB04C336854CF7FF62DF135FDC18F22B84AB3831 sul CSV di allora [V, R14@2026-09-28], non ricalcolato sul versionato [D];
- C3.1: F9EEA7264F5457A1728EA609CD6660BCEE9779D450099D446CC30A919D73E15C [V, R14@2026-09-29];
- C3.2: 5e9743252db28de1c2c6e28b5584725f4c2f78f47d4d830e318922d88e77ce92 [V, R43 e R44@2026-09-29];
- C4.1: circa 49 s; 92716bc7e6aa6a7b798370a09d1b31b33b0c0a49311bf35cd810f7975489f282 [V, R23@2026-09-29b];
- C4.2: e076f16f6a39606a4fcba04be5679a1fa0d7ce9f1c44893df47df79e39dee3a9 [V, R26@2026-09-29b];
- C4.3: cc0d3577168ea47cc7f89b9d44f59c29be67062a2ad41634285d11e417ac2073 [V, R29@2026-09-29b];
- C5.1, C5.2, C5.3: nei report T28–T32 [D].
File di configurazione: pyproject.toml e config/split.toml. Nessuna variabile d'ambiente letta dal codice: nessun os.environ, getenv o dotenv in src/, scripts/, tests/ [V, R1]
Uso come libreria: from shk.kelly import kelly_fraction, log_growth_rate; il resto si importa dal modulo (es. shk.kelly.core.expected_final_wealth) [V, R1]

## Moduli e responsabilità
src/shk/ ha 25 moduli applicativi (7 in kelly, 5 in stats, 4 in data, 2 in market, 7 in model) più 6 __init__.py [V, R1; conteggio ricalcolato dal supervisore]
__init__.py: src/shk espone __version__; kelly re-esporta kelly_fraction e log_growth_rate con __all__; stats, data, market e model hanno solo una docstring [V, R1]
Dipendenze fra sottopacchetti: kelly/ non importa da model/ né da data/; market/divergence.py importa nomi di data/split.py senza usarli; model/monitoring.py importa da kelly/ e stats/ [V, R1]
src/shk/kelly/core.py — kelly_fraction(p, b), log_growth_rate(f, p, b), expected_final_wealth(f, p, b, T, b0=1.0) (righe 97-144); nessun import interno [V, R1]. kelly_fraction = (b·p − q)/b, 0.0 se ≤ 0, solo scalari [D, era V R7@2026-09-27]
src/shk/kelly/simulate.py — nessun import interno [V, R1]:
- draw_outcomes(p, T, M, rng) → bool (M, T), True = vincita;
- simulate_growth(outcomes, fractions, b) → log-ricchezza float64 (M, T+1) con colonna 0 nulla; frazioni broadcastabili da (), (T,), (1, T), (M, 1), (M, T); ValueError per frazioni fuori da [0, 1) [V, R1@2026-09-28 per il broadcasting];
- log_wealth_paths(outcomes, f, b) delega a simulate_growth.
src/shk/kelly/estimation.py — relative_perturbation(p, delta); noisy_estimates(p, sigma_p, T, M, rng), con clip in [0, 1] [V, R1]
src/shk/kelly/scenarios.py — importa simulate.py e staking.py [V, R1]:
- Scenario (dataclass frozen: name, p, b, T, M); BASE_SCENARIO (0.60, 1.0, 1000, 10000); SUBTLE_SCENARIO (0.52, 1.0, 380, 10000); SEED = 20260927 [V, R1@2026-09-29c];
- spawn_generators(seed=SEED), due generatori: esiti, poi rumore [D, era V R10@2026-09-27];
- draw_scenario_outcomes(scenario, rng); simulate_scenario(scenario, outcomes, p_hat, lam=1.0) [V, R1].
src/shk/kelly/metrics.py — nessun import interno; funzioni su traiettorie (M, T+1) [V, R1]:
- final_log_wealth, median_growth_rate, median_final_wealth, mean_final_wealth, fraction_below_start;
- max_drawdown → (M,) in [0, 1); richiede almeno 2 colonne (righe 141-142) [V, R1 e R5].
src/shk/kelly/staking.py — modificato in C5 [V, R2]; nessun import interno [V, R1]:
- kelly_staking(p_hat, b, lam=1.0) = lam·max(0, (b·p̂ − (1 − p̂))/b), senza limite superiore; float per input 0-d, ndarray altrimenti [V, R1];
- StakingMoments (mean_c, mean_c2, var_c, fraction_zero), staking_moments(f_hat, f_star), plugin_staking(p_hat, b, sigma_p) [V, R1]. plugin = λ_t·kelly_staking con λ_t = 1/(1 + (o·σ_p/EV̂)²), 0 dove EV̂ ≤ 0 [D, era V R8@2026-09-27];
- costanti (righe 224-229): BASE_LAMBDA = 0.25, KAPPA_GRID = (0.0, 0.25, 0.5, 0.75, 1.0), KAPPA_ADWIN = 1.0, KAPPA_PAGE_HINKLEY = 1.0, OUTCOME_LABELS = ("H", "D", "A") [V, R1 e R5];
- BaselineDBets (outcomes, odds, fractions) [V, R1];
- compute_adaptive_lambda(match_dates, alarm_dates, kappa, base_lambda=BASE_LAMBDA): λ_j = base·κ^(allarmi con data < D_j); un kappa int dà TypeError (righe 297-298) [V, R1];
- select_baseline_d_bets(probs, odds, lambdas): esito con p̂·o − 1 massimo (np.argmax, parità nell'ordine H, D, A), frazione kelly_staking solo se il massimo è > 0; ciclo Python per partita [V, R1].
src/shk/kelly/backtest.py — motore su quote reali; nessun import interno né funzione privata [V, R1 e R4]:
- BacktestResult(dates, log_wealth); backtest_log_wealth(dates, fractions, odds, won), con dtype obbligati datetime64, float64, float64, bool [V, R1];
- ValueError per frazioni fuori da [0, 1), somma delle frazioni di una data ≥ 1, quote ≤ 1 o non finite, date non ordinate [V, R1];
- algoritmo [V, R4]:
  - date distinte da np.unique(return_index=True), in ordine di prima comparsa; parte da L_0 = 0;
  - ciclo Python sulle date (riga 125), con maschera dates == d sull'intero array (riga 126);
  - per data r_i = o_i − 1 se vinta, −1 se persa; L += ln(1 + Σ f_i·r_i) (righe 136-138);
- dates ha D elementi, uno per data distinta; log_wealth ne ha D + 1, con il punto iniziale 0; input vuoto → dates vuoto e log_wealth [0.0] [V, R4];
- tutte le frazioni entrano prima del calcolo, e il motore non conosce la ricchezza corrente [V, R4].
src/shk/stats/anova.py — OneWayAnovaResult (ss_between, ss_within, ss_total, df_between, df_within, ms_between, ms_within, f_statistic, p_value); oneway_anova(groups), con p-value da scipy.stats.f.sf [V, R4@2026-09-28; firme R1]
oneway_anova_vectorized(values, labels) → float per values 1D, altrimenti ndarray di forma values.shape[:-1]; values e labels np.ndarray (TypeError altrimenti); etichette int 0..k−1, tutte presenti [V, R4@2026-09-28; firme R1]
src/shk/stats/timeseries.py — generate_ar1_series(phi, n, m, rng) → float64 (m, n) [V, R7@2026-09-28]:
- estrazioni: x_0 ~ N(0, 1/(1 − φ²)) con size=m, poi innovazioni N(0, 1) in blocco;
- ValueError per φ non finito o |φ| ≥ 1, n < 2, m < 1;
- TypeError per n o m bool o non interi, e per rng non Generator.
src/shk/stats/calibration.py — nessun import interno [V, R1]:
- moving_block_indices(n, block_length, n_boot, rng) → int64 (n_boot, n), inizi da rng.integers(0, n − L + 1, size=(n_boot, ⌈n/L⌉)) [V, R12@2026-09-28];
- compute_order_statistic_index(b, alpha) → ⌈(1 − α)(b + 1)⌉ con tolleranza 1e-9; ValueError se supera b [V, R1 e R12@2026-09-28];
- calibrate_threshold(data, statistic, block_length, n_boot, alpha, rng, vectorized=False) → float [V, R12@2026-09-28]: indici estratti una volta; statistica float64 (n_boot,) finita; soglia = elemento k − 1 delle statistiche ordinate.
calibration.py — la docstring si contraddice [V, R1]: lo schema (a) indica come dato dell'ANOVA F "la serie della risposta" (righe 18-20); il principio (c) dice che imporre H₀ spetta al chiamante (righe 35-39). Lo schema l'ha dettato il supervisore ed è da correggere [V, R12@2026-09-28]
src/shk/stats/false_rejection.py — importa anova.py, calibration.py, timeseries.py [V, R1]:
- PHI_VALUES = (0.0, 0.3, 0.5, 0.7), N_OBS = 380, N_SERIES = 1000, ALPHA = 0.05, SEED_C2 = 20260928, BLOCK_LENGTHS = (7, 20, 40), N_BOOT = 999 [V, R1];
- DESIGN_CONTIGUOUS_2, DESIGN_CONTIGUOUS_38, DESIGN_RANDOM_2 e DESIGNS; CSV_COLUMNS (10); METHOD_NOMINAL, METHOD_BLOCK_BOOTSTRAP [V, R13 e R14@2026-09-28];
- PhiStreams (series_rng, perm_rng, boot_seed); RejectionResult (dataclass frozen con to_row()) [V, R1];
- critical_value_nominal, monte_carlo_interval_99, make_design_labels, spawn_c2_generators [V, R1];
- compute_nominal_rejection_rates → 12 risultati, DESIGNS × PHI_VALUES [V, R13@2026-09-28];
- compute_calibrated_rejection_rates → 12 per contiguous_2, BLOCK_LENGTHS × PHI_VALUES; calibrate_threshold sulla serie grezza, H₀ non imposta [V, R13 e R14@2026-09-28].
FLOAT_CSV_COLUMNS non sta in false_rejection.py ma in tests/test_us_c2_acceptance.py:33 [V, R1]
src/shk/stats/drift.py — ADWIN e PageHinkley da river.drift, e Z per giornata [V, R1]:
- importa calibration.py (calibrate_threshold, moving_block_indices), false_rejection.py (ALPHA, BLOCK_LENGTHS, N_BOOT) e pandas;
- costanti: TARGET_ALARMS_PER_SEASON = 1.9, MATCHDAY_SIZE = 10, SEED_C5 = 20260929, N_VERIFICATION_RESAMPLES = 1000;
- griglie: ADWIN_GRID_DELTA (9 valori); PAGE_HINKLEY_GRID_DELTA × PAGE_HINKLEY_GRID_THRESHOLD (3 × 6); default di river 0.26.1 in ADWIN_DEFAULT_* e PAGE_HINKLEY_DEFAULT_*;
- valori congelati: ADWIN_DELTA = 0.002, PAGE_HINKLEY_DELTA = 0.05, PAGE_HINKLEY_THRESHOLD = 5.0;
- detector_params(detector); run_drift_detector(series, detector, params=None), con un'istanza nuova per chiamata e i default di river se params=None;
- select_best_candidate, calibrate_adwin, calibrate_page_hinkley, calibrate_drift_detectors → pd.DataFrame per la griglia;
- compute_matchday_z_scores, compute_resampled_matchday_abs_z, calibrate_matchday_z_threshold, spawn_c5_generators(seed=SEED_C5, n_fits=3);
- verify_matchday_z_thresholds, che converte int(n_resamples) alla riga 665 prima del controllo di tipo alla riga 666.
src/shk/data/loading.py — DEFAULT_DATA_DIR = radice/data/raw/E0; load_all_seasons(data_dir=DEFAULT_DATA_DIR, seasons=None) [V, R1; R10 e R26@2026-09-29]:
- restituisce le colonne dei CSV più season (YYYY-YY, dal nome file);
- Date in datetime64[us] senza nulli; ordinamento stabile per season e Date.
loading.py — validazioni [V, R10 e R26@2026-09-29]:
- TypeError per data_dir non str né Path, e per seasons str o con elementi non str;
- FileNotFoundError per directory inesistente;
- ValueError per directory senza CSV, nome file non conforme, date miste, non conformi o fra 1° luglio e 31 agosto, campi in eccesso non vuoti, seasons vuota o con stagione senza file.
loading.py — decodifica per file: BOM → utf-8-sig, UTF-8 valido → utf-8, altrimenti cp1252; Date con %d/%m/%y o %d/%m/%Y [D, piano di T14]
src/shk/data/coverage.py — [V, R14–R17 e R45@2026-09-29; righe R1]:
- NON_ODDS_COLUMNS; ColumnClassification (group_type, group_name, source, market, timing, kind);
- classify_column(name): group_type ∈ {1x2_prematch, 1x2_closing, aggregators, other_markets}, timing ∈ {prematch, closing}, kind ∈ {odds, line, count}; ValueError per colonne non di quota o sconosciute (riga 292);
- GROUP_TYPE_ORDER; COVERAGE_CSV_COLUMNS (12); compute_coverage(df) → una riga per stagione × gruppo presente.
src/shk/data/split.py — delega a loading.py [V, R1]:
- DEFAULT_SPLIT_CONFIG_PATH; TestSetLockedError(RuntimeError) con __test__ = False; SplitConfig (frozen_on, test_unlocked, test_unlocked_on, training, validation, test) [V, R1];
- read_split_config(config_path): chiavi esatte, ruoli disgiunti, test non vuoto, training e validation < min(test) [V, R26 e R39@2026-09-29];
- load_by_role(role, config_path, data_dir), con i ruoli training, validation, test, history [V, R1]:
  - con il test bloccato, "test" dà TestSetLockedError prima di toccare i dati;
  - poi verifica, solo per nome, che ogni stagione configurata abbia un file, test compreso (righe 272-277);
  - history = stagioni presenti, anteriori al primo anno di test, né di training né di validation.
src/shk/data/walkforward.py — importa coverage.py [V, R1]:
- PREMATCH_IDENTIFIERS; LeakageError(RuntimeError) [V, R1];
- get_prematch_whitelist(columns), per inclusione e con lru_cache: Div, Date, HomeTeam, AwayTeam, season, Time e le colonne con kind = odds e timing = prematch [V, R45 e R46@2026-09-29];
- walkforward_split(df, seasons_to_predict), generatore (yield alla riga 229): coppie con storia a Date strettamente anteriore e partita ridotta alla whitelist [V, R1 e R45@2026-09-29];
- check_leakage(history, match, whitelist=None) → lista di violazioni; assert_no_leakage solleva LeakageError [V, R45@2026-09-29].
src/shk/market/devig.py — nessun import interno [V, R1]:
- implied_probabilities(odds) → (N, n); overround(odds) → (N,) = S − 1; devig_proportional;
- devig_additive: riga di NaN se un q ≤ 0;
- devig_power → (q, k): Newton vettorizzato da k = 1 con salvaguardia max(k − step, k/2), MAX_NEWTON_ITERATIONS = 50; RuntimeError se un mercato ha |Σq − 1| > 1e-12 (righe 189-193).
devig.py — validazione: ndarray (N, n) con n ≥ 2 e dtype reale, quote finite > 1, conversione in float64 [V, R30–R36@2026-09-29]
src/shk/market/divergence.py — importa devig.py [V, R1]:
- ODDS_BINS (1, 1.5, 2, 3, 5, 10, inf), ODDS_BIN_LABELS, REFERENCE_EDGE = 0.02, B365_ODDS_COLUMNS, DIVERGENCE_CSV_COLUMNS (19) [V, R1];
- assign_odds_bin, con fasce chiuse a sinistra [V, R41 e R44@2026-09-29];
- compute_divergence_table: partite usate = B365 valida e additivo applicabile; p99 con np.percentile lineare [V, R41 e R44@2026-09-29];
- import non usati: Path (riga 4); DEFAULT_SPLIT_CONFIG_PATH, SplitConfig, read_split_config (riga 10) [V, R1].
src/shk/model/elo.py — funzioni pure, senza RNG né accesso ai dati [V, R1]:
- elo_delta(r_home, r_away, h=0.0), solo scalari;
- expected_score(delta, s=400.0) = 1/(1 + 10^(−delta/s));
- elo_update(r_home, r_away, outcome, k, h=0.0, s=400.0): S = 1, 0.5, 0 per H, D, A, a somma zero;
- davidson_probabilities(delta, nu, s=400.0) e constant_draw_probabilities(delta, c, s=400.0) → (p_home, p_draw, p_away).
elo.py — tipi e validazioni:
- uno scalare reale dà float; un ndarray, anche 0-d, dà ndarray float64 [V, R16 e R17@2026-09-29b];
- TypeError per bool, non numerici, liste, stringhe, ndarray bool o complessi [V, R11@2026-09-29b];
- ValueError per valori non finiti, ν ≤ 0, c fuori da (0, 1), s ≤ 0, k < 0, outcome fuori da H, D, A [V, R11@2026-09-29b];
- assert nel codice alle righe 163, 168, 230, 281, 290, 345, 347, 354, 356; import Any non usato [V, R1].
src/shk/model/elo_predictor.py — importa walkforward.py ed elo.py [V, R1]:
- SEASON_REGEX; compute_season_standings(matches), con almeno team, points, goal_diff, goals_for [V, R1 e R19@2026-09-29b];
- predict_elo_walkforward(...): via fornitore, con assert_no_leakage su ogni coppia [V, R1];
- predict_elo_fast(df, seasons_to_predict, k, h, nu, s=400.0, initial_rating=1500.0): passata unica, groupby per data, prima la previsione e poi l'aggiornamento [V, R1];
- diagnose_season_transitions(df) [V, R1];
- output: DataFrame a 12 colonne (season, Date, HomeTeam, AwayTeam, rating_home, rating_away, delta, p_home, p_draw, p_away, home_promotion, away_promotion) [V, R1].
elo_predictor.py — interni [V, R1]:
- _CALC_COLS = Date, season, HomeTeam, AwayTeam, FTR, FTHG, FTAG (righe 14-22), l'unico sottoinsieme su cui itera il percorso veloce (riga 475);
- _parse_season_start_year (riga 91); _validate_inputs; assert alla riga 282;
- _EloTracker (riga 212), unica classe del pacchetto con comportamento.
elo_predictor.py — neopromosse:
- alla prima partita di una stagione si congela la classifica della precedente; le squadre mai viste prendono la media dei rating finali delle ultime tre, le tornanti riprendono l'ultimo rating attivo [V la regola, R1@2026-09-29c; D i dettagli];
- nella prima stagione del DataFrame tutte partono da initial_rating [V, R1@2026-09-29c].
elo_predictor.py — sui dati reali i due percorsi danno previsioni identiche byte per byte: SHA256 0b3048a7a170e7e149f6cb96c2790e36d3f05010a4d5ce35e1ea0febc1fcbce1 con K = 20, h = 60, ν = 1 [V, R21@2026-09-29b]
src/shk/model/elo_fit.py — importa split.py (SplitConfig), elo.py (expected_score), elo_predictor.py (predict_elo_fast) [V, R1]:
- costanti: SEASON_REGEX; BOUNDS_K (5, 80), BOUNDS_H (0, 200), BOUNDS_NU (0.05, 3); INITIAL_PARAMS (30, 60, 1); OPTIMIZER_*; GRID_K, GRID_H (41 punti); WALKFORWARD_CSV_COLUMNS (15);
- tipi: EloFitParams (k, h, nu, c); EloCalibrationResult;
- funzioni: parse_season_start_year (riga 96); derive_fit_schedule(training, validation=None); calibrate_single_fit (Nelder-Mead su K, h, ν); calibrate_all_fits;
- compute_training_log_loss → (loss, preds), con clip a 1e-15 (riga 200; lo stesso nella baseline, riga 277).
ELO_FITS (righe 321-340), congelato il 2026-09-29, coincide con la ricalibrazione entro rel_tol 1e-9 [V, R23@2026-09-29b; righe R1]:
- "2000-01": K = 10.318224689650037, h = 125.54022316884253, ν = 0.8062246331085681, c = 0.2657894736842105;
- "2010-11": K = 9.934776455088759, h = 127.87791672140764, ν = 0.8775613268630023, c = 0.2789473684210526;
- "2020-21": K = 7.928543266007228, h = 78.033626101627, ν = 0.7603760315281511, c = 0.25877192982456143.
src/shk/model/scoring.py — importa devig.py, elo_fit.py, elo_predictor.py [V, R1]:
- costanti: PINNACLE_CLOSING_START_SEASON, PINNACLE_START_YEAR = 2012, DEVIG_METHODS, SERIES_NAMES ("b365_prematch", "pinnacle_closing"), MATCH_KEYS (season, Date, HomeTeam, AwayTeam), CSV_COLUMNS (11);
- compute_log_loss puntuale, senza eps: ValueError se la probabilità realizzata è ≤ 0 (riga 114); compute_mean_log_loss; compute_g_hat_terms, compute_g_hat, compute_cumulative_g_hat;
- generate_validation_predictions(df, fits, schedule): predict_elo_fast con i parametri di ogni fit;
- import Any non usato.
scoring.py — allineamento e serie:
- align_predictions_with_odds(df_preds, df_raw): merge inner su MATCH_KEYS, prende da df_raw solo le colonne mancanti; ValueError per chiavi mancanti o duplicate [V, R1 e R26–R27@2026-09-29b];
- SeriesEvaluationData: conteggi di esclusione, df_used, p_model, q_proportional, q_additive, q_power (N×3), outcomes [V, R1 e R27@2026-09-29b];
- prepare_series_evaluation(df_aligned, series, schedule), che può sollevare RuntimeError [V, R1].
src/shk/model/recalibration.py — importa elo_fit.py, elo_predictor.py, scoring.py [V, R1]:
- costanti e tipi: PROB_LOWER_CLIP, PROB_UPPER_CLIP, OUTCOMES, CALIBRATION_CSV_COLUMNS (16); IsotonicModel, PlattModel, FitCalibrationMaps [V, R1];
- fit_isotonic_single, predict_isotonic_single, predict_platt_single; fit_platt_single, con RuntimeError se L-BFGS-B non converge (righe 300-303) [V, R1];
- compute_brier_scores, brier_score, compute_reliability_table (10 fasce) [V, R1];
- generate_fit_training_predictions: riceve fit_through senza usarlo (righe 322-336) [V, R1];
- fit_all_calibration_maps; recalibrate_series_predictions (one-vs-rest, limite [1e-6, 1 − 1e-6], rinormalizzazione) [V, R1 e R29–R30@2026-09-29b];
- import non usati: ELO_FITS, derive_fit_schedule, parse_season_start_year, MATCH_KEYS [V, R1].
src/shk/model/residuals.py — importa elo_fit.py e scoring.py [V, R1]:
- REQUIRED_INPUT_COLUMNS; RESIDUALS_COLUMNS (11): fit_through, role, season, Date, HomeTeam, AwayTeam, p_home, p_draw, p_away, FTR, log_loss;
- compute_model_residuals(df, schedule, fits=None):
  - validazione: generate_validation_predictions + align_predictions_with_odds;
  - training: compute_training_log_loss sulle stagioni ≤ fit, poi align_predictions_with_odds;
  - log_loss: compute_log_loss su tutte le righe;
- import MATCH_KEYS non usato.
src/shk/model/monitoring.py — 1351 righe: serie per scenario, record dei CSV di C5, Baseline D [V, R1]
monitoring.py — import [V, R1]: backtest.py, metrics.py (max_drawdown), staking.py, elo_fit.py (parse_season_start_year), scoring.py (align_predictions_with_odds), drift.py, false_rejection.py, scipy.stats.norm
monitoring.py — contenuto per story [V, R1]:
- C5.1: DRIFT_DETECTOR_CSV_COLUMNS (12), EXPECTED_MATCHES_PER_SEASON = 380, ScenarioSeries, extract_scenario_series, build_drift_records, generate_drift_detector_records;
- C5.2: DAILY_Z_TEST_CSV_COLUMNS (14), TrainingBaselineStats, compute_training_baseline_stats, build_daily_z_test_records, generate_daily_z_test_records;
- C5.3: BaselineDSeasonInput, KappaCalibrationRow (riga 744), KappaCalibrationResult, assemble_baseline_d_season_input, BASELINE_D_CSV_COLUMNS (9), BaselineDValidationSeasonData, BaselineDAgentResult, build_baseline_d_season_data, evaluate_baseline_d_agents, generate_baseline_d_records;
- calibrate_baseline_d_kappa (riga 988), con default calibration_seasons=("2010-11", "2020-21").
monitoring.py — campi delle classi di C5.3 [V, R5]:
- BaselineDSeasonInput (righe 736-741): season (str); dates, probs, odds, ftr, log_loss (ndarray);
- BaselineDValidationSeasonData (righe 1030-1034): season, fit_through, season_input, adwin_alarm_dates, page_hinkley_alarm_dates;
- BaselineDAgentResult (righe 1060-1067): agent, kappa, final_log_wealth, n_bets, n_alarms (int | None), max_drawdown, backtest_result (BacktestResult), bets (BaselineDBets).
monitoring.py — esecuzione degli agenti [V, R5]:
- evaluate_baseline_d_agents(season_data, base_lambda=BASE_LAMBDA, kappa_adwin=KAPPA_ADWIN, kappa_page_hinkley=KAPPA_PAGE_HINKLEY) → tupla di tre BaselineDAgentResult (righe 1141-1146); TypeError se season_data non è BaselineDValidationSeasonData;
- i tre agenti sono cablati nel corpo, senza lista né registro, e l'ordine di ritorno è fissato alla riga 1246:
  - reference (righe 1179-1200): allarmi vuoti, κ = 1.0 letterale alle righe 1184 e 1193;
  - d_adwin (righe 1202-1222) e d_page_hinkley (righe 1224-1244): κ dal parametro;
- generate_baseline_d_records ripete i tre nomi: nel dizionario agent_totals (righe 1295-1299, con "kappa": 1.0 cablato per reference) e nella tupla dei totali (riga 1334);
- catena per ciascun agente: compute_adaptive_lambda → select_baseline_d_bets → backtest_log_wealth → float(max_drawdown(log_wealth.reshape(1, -1))[0]) (righe 1190, 1212, 1234).
scripts/ — undici script con run_experiment() senza parametri [V, R1]: us_c1_1_growth_vs_lambda, us_c1_2_estimation_error, us_c2_anova_autocorrelation, us_c3_1_data_coverage, us_c3_2_devig_divergence, us_c4_1_elo_walkforward, us_c4_2_g_hat, us_c4_3_calibration, us_c5_1_drift_detectors, us_c5_2_daily_z_test, us_c5_3_baseline_d
Particolarità degli script [V, R1]:
- C1.1: p = 0.60, b = 1.0, T = 1000, M = 10000, seed 20260905 e 51 λ in [0, 2.5] cablati alle righe 30-36, λ = 1.946 alla riga 124; gli stessi valori sono ripetuti nel test;
- C3.1: load_all_seasons su tutta la directory (riga 29), 2023-24 compreso;
- C4.1: la docstring dice "script di calibrazione" ma usa ELO_FITS; costruisce le righe del CSV nello script (righe 52-105);
- C4.2: ĝ come np.mean(compute_g_hat_terms(...)); C4.3 rifà per conto suo la catena di C4.2;
- C5.1: riesegue run_drift_detector per la figura (righe 90-93); giornata 10/38 cablata alle righe 68-69, 97, 114, 134;
- C5.2: 1.9 cablato (righe 103, 137); int(s.split("-")[0]) alla riga 65;
- C5.3: etichetta "κ = 1.0" e asse fissato a ±0.05 (righe 75-76, 84).
Nessuno script chiama calibrate_single_fit, calibrate_all_fits, calibrate_drift_detectors, calibrate_baseline_d_kappa, predict_elo_walkforward o diagnose_season_transitions [V, R1]
tests/ — 30 moduli [V, R1]:
- unitari: test_kelly_core, test_simulate, test_estimation, test_staking, test_metrics, test_backtest, test_anova, test_timeseries, test_calibration, test_data_loading, test_coverage, test_split, test_devig, test_leakage, test_elo, test_elo_predictor, test_scoring, test_recalibration, test_residuals, test_drift;
- accettazione test_us_c1_1, c1_2, c2, c3_2, c4_1, c4_2, c4_3, c5_1, c5_2, c5_3 (_acceptance): controlli sintetici, controlli sui CSV e PNG versionati, ricalcoli dai dati reali.
Test sui dati reali saltati se data/raw/E0/ non ha CSV; _has_real_data è definita in otto moduli [V, R1]
Copertura desunta dai file di test [V, R1, salvo dove indicato]:
- mai nominate in un test: expected_final_wealth, spawn_c2_generators, calibrate_adwin, calibrate_page_hinkley, calibrate_all_fits, generate_fit_training_predictions, assemble_baseline_d_season_input; tutte tranne expected_final_wealth sono raggiunte solo tramite altre funzioni;
- solo importate, mai chiamate: build_baseline_d_season_data, extract_scenario_series, build_drift_records, build_daily_z_test_records;
- chiamate solo in test saltati senza dati, quindi mai in CI: calibrate_drift_detectors (test_drift.py:289), recalibrate_series_predictions (test_us_c4_3_acceptance.py:168-169), calibrate_baseline_d_kappa (test_us_c5_3_acceptance.py:158), generate_baseline_d_records (riga 336), load_by_role sui ruoli reali, diagnose_season_transitions sui dati reali (test_elo_predictor.py:351);
- le altre funzioni pubbliche sono nominate in almeno un test; la chiamata diretta è verificata solo per 13 nomi [D];
- CSV versionati senza un test che li legga: C1.1, C1.2, C3.1;
- PNG senza test di esistenza: C1.1, C1.2, C3.1, C5.1, C5.3, e C4.1 (PNG_PATH definito ma non usato, test_us_c4_1_acceptance.py:25);
- test_metrics.py:test_metrics_error_conditions non verifica il ValueError di median_final_wealth e mean_final_wealth [V, R1@2026-09-29c].
Classi del pacchetto [V, R1]: Scenario, StakingMoments, BaselineDBets, BacktestResult, OneWayAnovaResult, PhiStreams, RejectionResult, ColumnClassification, SplitConfig, TestSetLockedError, LeakageError, EloFitParams, EloCalibrationResult, SeriesEvaluationData, IsotonicModel, PlattModel, FitCalibrationMaps, ScenarioSeries, TrainingBaselineStats, BaselineDSeasonInput, KappaCalibrationRow, KappaCalibrationResult, BaselineDValidationSeasonData, BaselineDAgentResult, più l'interna _EloTracker. Escluse le eccezioni e _EloTracker, sono tutte NamedTuple o dataclass frozen
Persistenza: nessun database; config/split.toml; undici CSV in results/ e undici PNG omonimi in thesis/figures/, tutti versionati. Gli schemi dei CSV sono costanti *_CSV_COLUMNS; i record sono list[dict] con stringa vuota per i campi non applicabili, scritti con csv.DictWriter [V, R1]
CSV versionati, colonne e righe di dati [V, R1; colonne di C1–C4 R1@2026-09-29c; intestazione di C5.3 R6]: us_c1_1_growth_vs_lambda (10, 51), us_c1_2_estimation_error (12, 46), us_c2_anova_autocorrelation (10, 24), us_c3_1_data_coverage (12, 477), us_c3_2_devig_divergence (19, 29), us_c4_1_elo_walkforward (15, 9 500), us_c4_2_g_hat (11, 33 066), us_c4_3_calibration (16, 144), us_c5_1_drift_detectors (12, 66), us_c5_2_daily_z_test (14, 860), us_c5_3_baseline_d (9, 60)
results/us_c5_3_baseline_d.csv: intestazione row_type, season, fit_through, agent, kappa, final_log_wealth, n_bets, n_alarms, max_drawdown [V, R6]

## Flussi principali
Dati E0: 31 stagioni, 11 944 partite (462 nel 1993-94 e nel 1994-95, 380 nelle altre); 161 colonne originali più season [V, R10@2026-09-29; totale ricalcolato dal supervisore]
Colonne E0, per presenza e non completezza [V, R8@2026-09-29]:
- in tutte le stagioni: Div, Date, HomeTeam, AwayTeam, FTHG, FTAG, FTR; Time dal 2019-20;
- B365 pre-partita dal 2002-03; IW e WH dal 2000-01; PS e PSC* dal 2012-13;
- B365C* e le altre chiusure dal 2019-20; Bb* dal 2005-06 al 2018-19; Max* e Avg* dal 2019-20.
Codifiche: 2004-05 in cp1252, 2021-22 con BOM UTF-8 [V, R9@2026-09-29]
Split congelato [V, R26@2026-09-29; conteggi ricalcolati dal supervisore e asseriti in test_split.py:483-491, R1]:
- training: 2000-01, 2010-11, 2020-21 (1 140 partite);
- validation: 19 stagioni dal 2002-03 al 2022-23, tranne 2010-11 e 2020-21 (7 220);
- history: dal 1993-94 al 1999-00, più il 2001-02 (3 204);
- test: 2023-24, bloccato e non letto (380).
Schema espansivo: ogni fit j si stima sulle stagioni di training ≤ j e prevede le stagioni di validazione fino al fit successivo [V, R1]. Conteggi per fit [V, R23@2026-09-29b; stagioni D, ricalcolo del supervisore]:
- fit 2000-01: training 380, validazione dal 2002-03 al 2009-10 (3 040);
- fit 2010-11: training 760, validazione dal 2011-12 al 2019-20 (3 420);
- fit 2020-21: training 1 140, validazione 2021-22 e 2022-23 (760).
Catena comune sui dati reali, negli script C4 e C5 [V, R1]:
1. read_split_config → derive_fit_schedule(cfg);
2. load_by_role("history" | "training" | "validation"), poi concatenazione e ordinamento stabile per Date nello script;
3. generate_validation_predictions(df, ELO_FITS, schedule) → predict_elo_fast per fit → _EloTracker → elo_delta, davidson_probabilities, elo_update;
4. align_predictions_with_odds(df_preds, df_full).
C4.2 e C4.3, dopo la catena [V, R1]:
- prepare_series_evaluation per "b365_prematch" e "pinnacle_closing" (devig_additive per le esclusioni, poi i tre metodi);
- compute_mean_log_loss, compute_g_hat_terms, compute_cumulative_g_hat;
- per C4.3: mappe isotonica e Platt sul training, ricalibrazione, reliability e Brier.
C5.1 e C5.2 [V, R1]:
- compute_model_residuals(df, schedule, ELO_FITS) dà la log-loss per partita del Modulo 1 raw, sia sul training di ogni fit sia sulla validazione;
- C5.1: generate_drift_detector_records → extract_scenario_series (22 serie da 380: 3 di training e 19 di validazione) → build_drift_records → run_drift_detector, con un'istanza nuova per stagione;
- C5.2: generate_daily_z_test_records → compute_training_baseline_stats e serie di training per fit → build_daily_z_test_records;
- build_daily_z_test_records usa spawn_c5_generators, calibrate_matchday_z_threshold (→ calibrate_threshold), verify_matchday_z_thresholds, compute_matchday_z_scores e run_drift_detector.
C5.3 [V, R1 e R5]:
1. residui come sopra;
2. generate_baseline_d_records → per ogni stagione di validazione build_baseline_d_season_data (assemble_baseline_d_season_input con le quote B365H/D/A, run_drift_detector per i due detector);
3. evaluate_baseline_d_agents;
4. CSV con 57 righe di stagione (19 × 3 agenti) e 3 di totale; PNG delle differenze appaiate.
Definizioni di C5, dalle decisioni S5, scelte del supervisore su delega non ancora confermate [D, BACKLOG.md; implementazione non riletta salvo dove marcato]:
- giornata = blocco contiguo di 10 partite nell'ordine cronologico stabile;
- Z = (media della log-loss della giornata − μ_f)/(σ_f/√10), con μ_f e σ_f (ddof = 1) dal training del fit; allarme nominale se |Z| > z_0.975;
- parametri dei detector: la combinazione della griglia con la media di allarmi su 2000-01 e 2010-11 più vicina a 1.9;
- Baseline D: al più una puntata per partita (esito con p̂·o − 1 massimo se positivo) con quote B365 non de-viggate e p̂ raw; λ = 0.25·κ^allarmi, dove un allarme della data d conta dalle date successive [V la regola, R1]; bankroll 1 a inizio stagione;
- κ scelto per detector sulla somma della log-ricchezza finale di 2010-11 e 2020-21; a parità vince il più grande.
CSV di C5.2: 860 righe = 722 + 114 + 6 + 18, conteggi asseriti in test_us_c5_2_acceptance.py:310-318 [V, R1]. Interpretazione [D, ricalcolo del supervisore]: 722 = 19 stagioni × 38 giornate dello Z nominale; 114 = 19 × 6 metodi; 6 riepiloghi complessivi; 18 righe di verifica
Repliche di logica nei test [V, R1]:
- test_us_c5_3_acceptance.py:130-142 riscrive la regola di parità di κ invece di chiamare calibrate_baseline_d_kappa;
- test_us_c4_1_acceptance.py:188-220 duplica la costruzione delle righe di C4.1, senza strip di FTR e senza i controlli riga per riga dello script;
- test_us_c4_2_acceptance.py:109-166 confronta solo le 6 righe di riepilogo e usa compute_g_hat;
- test_us_c5_2_acceptance.py:424-436 reimplementa |z| > soglia sui valori del CSV;
- test_us_c1_2_acceptance.py usa 1.1·p e 0.9·p invece di relative_perturbation.
Risultati C1 [D, ricalcolo del supervisore]:
- con p = 0.6 e b = 1: f* = 0.2, g(0.2) = 0.020136, g(0.4) = −0.002447, g si annulla a λ = 1.94695;
- le costanti di test_kelly_core.py:32 e :39 e il λ = 1.946 di C1.1 sono valori analitici.
Risultati C2, rigetti su 1000 serie per φ = 0.0, 0.3, 0.5, 0.7 [V, R9 e R14@2026-09-28; ricalcolo del supervisore]:
- nominale contiguous_2: 37, 149, 253, 399; contiguous_38: 44, 843, 999, 1000; random_2: 58, 35, 48, 45;
- calibrato su contiguous_2 (serie grezza), per L = 7, 20, 40: φ = 0.0 → 35, 29, 32; 0.3 → 61, 57, 49; 0.5 → 73, 52, 42; 0.7 → 108, 65, 56;
- intervallo Monte Carlo al 99%: [0.0322, 0.0678].
Risultati C3 [V, R14, R43 e R46@2026-09-29]:
- B365 pre-partita completa dal 2002-03 al 2023-24, assente nel 2000-01;
- su training e validazione, 7 980 partite B365 su 8 360; overround medio 5.437%; spread massimo 6.29 punti, 3.14 volte l'edge di 2 punti;
- anti-leakage: 8 360 partite senza violazioni; whitelist di 87 campi.
Risultati C4 [V, R23, R26 e R29@2026-09-29b]:
- log-loss Davidson / pareggio costante sulla validazione: 0.973761 / 0.976755 (fit 2000-01), 0.983832 / 0.990144 (2010-11), 0.983300 / 0.987629 (2020-21); sul training 1.008189, 1.008987, 1.020937;
- ĝ (proporzionale / additivo / power), negativo in tutti i casi e a ogni fine stagione: b365_prematch (7 220 partite) −0.021429 / −0.022401 / −0.022402; pinnacle_closing (3 800, dal 2012-13) −0.031474 / −0.031572 / −0.031672;
- log-loss di validazione raw / Platt / isotonica: 0.979536 / 0.982340 / 1.013931 su B365, 0.981229 / 0.980927 / 0.991359 su Pinnacle.
Risultati C5.3, da results/us_c5_3_baseline_d.csv [V, R6]:
- sulle 19 stagioni, reference, d_adwin e d_page_hinkley hanno κ = 1.0, final_log_wealth totale −10.58001605492385 e 6 234 puntate ciascuno;
- allarmi: 0 per ADWIN e 20 per Page-Hinkley;
- final_log_wealth di d_adwin e di d_page_hinkley è identico, come stringa, a quello di reference in 19 stagioni su 19.
Con κ = 1 vale λ = 0.25 a ogni partita, qualunque sia il numero di allarmi: la Baseline D coincide col quarto-Kelly senza detector per costruzione [V la formula, R1; D la conseguenza, confermata da R6]
In media per stagione la log-ricchezza è −0.5568, cioè il bankroll finisce a circa 0.573 volte quello iniziale; si punta su 6 234 partite delle 7 220 (86.3%) [D, ricalcolo del supervisore]
Altri valori misurati in C5 (griglie dei detector, soglie calibrate, tabella di κ, allarmi per stagione): solo nei report T27–T32 [D]. test_drift.py:324-335 asserisce sui dati reali 0 allarmi ADWIN e 1 + 1 Page-Hinkley con i parametri congelati [V, R1]; su quali stagioni, non riportato [D]

## Convenzioni da rispettare
Naming: snake_case per moduli, funzioni e variabili; PascalCase per le classi; UPPER_CASE per le costanti; prefisso _ per gli helper interni; test con prefisso test_ [V, R1]
Lingua: commenti e docstring in italiano; identificatori, nomi dei test e messaggi delle raise in inglese [V, R1]
Messaggi di assert e motivi di skip: in italiano in test_leakage, test_us_c3_2, test_us_c4_1, test_us_c5_2, test_us_c5_3 e test_split.py:480, in inglese altrove [V, R1]. Se la regola sulla lingua li copra non è deciso [D]
Type hints sulle funzioni pubbliche; docstring in stile NumPy con sezioni Parametri / Restituisce / Solleva [V, R1]
Validazione in apertura di funzione: TypeError per i tipi, ValueError per i valori; rng controllato con isinstance(rng, np.random.Generator) [V, R1 e R5@2026-09-28]
Nel codice da C2 in poi: bool e float al posto di un intero danno TypeError, gli interi NumPy sono accettati, una str non vale come collezione di str [V, R1]. Eccezione storica di C1: draw_outcomes, noisy_estimates, expected_final_wealth e kelly_fraction non controllano il tipo [V, R1]
Eccezioni dedicate: TestSetLockedError, LeakageError. RuntimeError per mancata convergenza (devig_power, fit_platt_single) e in prepare_series_evaluation [V, R1]
Nessun try/except in src/ e scripts/; nessun print(, logging o warnings.warn in src/, scripts/ e tests/ [V, R1]. Unico try in un test: tests/test_us_c3_2_acceptance.py:245-256 [V, R1]
assert nel codice di libreria solo in elo.py ed elo_predictor.py, alle righe elencate in Moduli [V, R1]
RNG passato come argomento, mai creato nelle funzioni di libreria; flussi indipendenti con SeedSequence.spawn (spawn_generators, spawn_c2_generators, spawn_c5_generators) [V, R1]. Seed: SEED = 20260927 (C1.2), 20260905 (C1.1), SEED_C2 = 20260928, SEED_C5 = 20260929 [V, R1]
Organizzazione [V, R1]:
- kelly/ e stats/: funzioni su array; eccezione drift.py, che usa pandas e restituisce DataFrame dalle calibrate_*;
- data/: I/O e split; market/: quote;
- model/: funzioni su DataFrame e costruzione dei CSV di C4 e C5.
Vettorizzazione: nessun ciclo su M e T nel motore Monte Carlo; del paths nei loop Monte Carlo [V, R1@2026-09-29c e R1@2026-09-28]. backtest_log_wealth cicla sulle date, select_baseline_d_bets sulle partite [V, R1 e R4]
Script di esperimento [V, R1]:
- scripts/us_c<story>_<n>_<nome>.py → results/<stesso nome>.csv e thesis/figures/<stesso nome>.png, entrambi versionati;
- matplotlib.use("Agg") prima di pyplot; run_experiment() senza parametri, dal blocco __main__; nessun argomento da riga di comando;
- CSV con csv.DictWriter, float nativi e stringa vuota dove non applicabile; savefig(dpi=150); etichette in italiano.
Percorsi: script e test nuovi usano Path(__file__).resolve().parents[1]. Eccezioni storiche con percorsi relativi alla directory corrente: C1.1, C1.2, C2 e tests/test_us_c2_acceptance.py (righe 179, 257, 315) [V, R1]
Parametri condivisi fra script e test stanno in un modulo di libreria [V, R1; elenco C1–C4 R1@2026-09-29c]:
- C1.2 scenarios.py; C2 false_rejection.py; C3 coverage.py, divergence.py e split.toml;
- C4 elo_fit.py, scoring.py, recalibration.py; C5 drift.py, staking.py, monitoring.py;
- eccezione storica: C1.1, con i parametri cablati nello script e nel test.
Test [V, R1 e decisioni S3–S4]:
- Monte Carlo su larga scala e test sui dati reali oltre 60 s si marcano @pytest.mark.slow; i test anti-leakage no;
- i test sui dati reali si saltano con motivo esplicito, tramite _has_real_data o una condizione equivalente su DEFAULT_DATA_DIR;
- un test che controlla solo il CSV versionato non basta, perché in CI mancano i dati grezzi [V, R31 e R33@2026-09-29b];
- se il CSV versionato manca, C4.1 salta, mentre C4.2, C4.3, C5.2 e C5.3 asseriscono che esiste [V, R1].
Dati reali nel codice nuovo solo con read_split_config e load_by_role [V, R1 e R26@2026-09-29]:
- load_all_seasons è ammessa solo in loading.py, split.py, coverage.py e scripts/us_c3_1_data_coverage.py;
- un test di guardia AST in tests/test_split.py (righe 428-454) lo verifica, scandendo solo src/ e scripts/;
- i test in tests/ la usano liberamente.
Probabilità 1X2: ndarray (N, 3) in ordine H, D, A con righe a somma 1; previsioni walk-forward, prima dell'aggiornamento della stessa data [V, R1]
Processo [V, PROTOCOLLO.md fornito dal programmatore il 2026-09-28; non toccato in C5, R2]:
- i commit li fa solo il programmatore, a mano;
- ogni story ha un branch di lavoro che entra in main come un solo commit;
- Cline scrive in .agent/ solo MAPPA.md in mappatura e report/T<n>.md in esecuzione;
- .agent/ è versionato [V, R1].
La sezione "Convenzioni del progetto" di PROTOCOLLO.md non aveva convenzioni aggiuntive al 2026-09-28 [V, PROTOCOLLO.md 2026-09-28]; eventuali modifiche fino a 27cf7a4 non verificate [D]

## Zone fragili da non toccare senza avviso
test_acceptance_calibrated_phi_zero_within_mc_interval (tests/test_us_c2_acceptance.py, slow) fallisce per un risultato noto [V, R14@2026-09-28; decisione del programmatore 2026-09-28; non rieseguito dopo]:
- 29 rigetti su 1000 a φ = 0 con L = 20, sotto l'estremo 32.25 dell'intervallo al 99%;
- è il T12 da rivedere, non una regressione: non si sistema allentando tolleranze o parametri.
Tarature congelate: ELO_FITS, ADWIN_DELTA, PAGE_HINKLEY_DELTA, PAGE_HINKLEY_THRESHOLD, KAPPA_ADWIN e KAPPA_PAGE_HINKLEY non si modificano [D, decisioni S4 e S5]. Nessuno script le riesegue; si riverificano solo con test locali: uno slow per ELO_FITS, gli altri saltati senza dati [V, R1]
Una modifica a elo.py, elo_predictor.py, elo_fit.py, scoring.py, residuals.py o recalibration.py che cambia previsioni o metriche rende incoerenti ELO_FITS, le tarature di C5 e i CSV di C4 e C5: vanno ricalibrati e rigenerati. Lo segnalano solo in locale i test di ricalcolo e di taratura [D]
Baseline D degenerata [V, R1, R5 e R6; D la conseguenza sulla figura]:
- con KAPPA_ADWIN = KAPPA_PAGE_HINKLEY = 1.0 i due agenti D puntano come il riferimento (vedi Flussi);
- il κ del riferimento è 1.0 letterale in monitoring.py (righe 1184, 1193, 1295-1299);
- lo script C5.3 cabla l'etichetta "κ = 1.0" e l'asse ±0.05: cambiando le costanti la figura non si aggiorna.
Motore backtest_log_wealth [V, R1 e R4 per i fatti; D le conseguenze]:
- riceve le frazioni già calcolate, quindi non regge regole che dipendono dalla ricchezza corrente (puntata minima fissa, floor) senza un nuovo motore o un'interfaccia passo-passo;
- con λ = 1 (Kelly pieno) e più partite nella stessa data può scattare il ValueError per somma delle frazioni ≥ 1;
- con Σ f < 1 per data e r ≥ −1 la ricchezza resta > 0: un tasso di rovina va definito con una soglia [ricalcolo del supervisore];
- il costo cresce come date distinte × partite, per la maschera sull'intero array a ogni data.
max_drawdown richiede almeno 2 colonne: una stagione senza date darebbe ValueError in evaluate_baseline_d_agents [V il reshape, R5; D la conseguenza]
Agenti cablati in monitoring.py: evaluate_baseline_d_agents e generate_baseline_d_records ripetono i tre nomi, quindi un agente nuovo tocca entrambe le funzioni [V, R5]
CSV accoppiati [V i test, R1; D la conseguenza]:
- test_us_c4_3_acceptance.py::test_raw_g_hat_matches_t23 confronta C4.3 con C4.2;
- test_us_c5_2_acceptance.py::test_versioned_csv_alarms_match_c5_1 confronta C5.2 con C5.1;
- rigenerarne uno solo li fa divergere.
Rieseguire uno script sovrascrive CSV e PNG versionati: ogni task che rigenera un esperimento dice se vanno committati [V, R1]
Dipendenze senza vincoli e CI senza lockfile:
- la CI installa le ultime versioni [V, R1];
- i conteggi esatti degli allarmi (test_drift.py:324-335 e CSV di C5) dipendono da river 0.26.1 [D];
- NumPy non garantisce la stabilità dei flussi di Generator fra versioni [D];
- il valore critico C2 per k = 2 differisce all'ultima cifra fra venv e CI [V, R9 e R15@2026-09-28];
- uv.lock non ha pandas né river [V, R1].
Test slow e test sui dati reali non girano in CI, per addopts e per data/raw/* ignorato [V, R1]. Vanno lanciati a mano dopo modifiche a kelly/, stats/ o model/ [D]. Il test sui dati reali di test_leakage.py dura circa 8 s ed è nella suite veloce [V, R46@2026-09-29]
Blocco del test set aggirato da due percorsi ammessi [V, R1]:
- scripts/us_c3_1_data_coverage.py:29 e tests/test_data_loading.py:312 chiamano load_all_seasons su tutta la directory, 2023-24 compreso;
- results/us_c3_1_data_coverage.csv ha 35 righe del 2023-24;
- il test di guardia AST non scandisce tests/.
config/split.toml è congelato e non si modifica. Lo sblocco del test lo fa solo il programmatore, a mano e con commit, dopo il congelamento dei parametri (US-C8.2) [V, decisione S3]
La prova del congelamento dello split dipende da 2cea094, che sta solo nella reflog locale: una garbage collection può eliminarlo alla scadenza della voce, per default circa 30 giorni dopo il 2026-09-29 [V, R2–R6@2026-09-29b; D la scadenza]
load_by_role richiede il file di ogni stagione configurata, test compreso, anche per caricare training (split.py:272-277) [V, R1]
walkforward_split è un generatore: le validazioni scattano alla prima iterazione, non alla chiamata [V, R1]
classify_column solleva ValueError su colonne non catalogate, quindi file E0 con colonne nuove fermano audit e fornitore walk-forward; estendere coverage.py cambia i campi esposti dal fornitore [V, R1 e R45–R46@2026-09-29]
Errori che fermano un calcolo intero [V, R1]: devig_power solleva RuntimeError se anche un solo mercato non converge; fit_platt_single se L-BFGS-B non converge
devig_additive dà righe di NaN da escludere per tutti i metodi; test_devig.py:test_extreme_markets salta quei mercati [V, R35@2026-09-29]
noisy_estimates può dare p̂ = 1 per saturazione; con lam ≥ 1 kelly_staking dà frazioni ≥ 1, che simulate_growth rifiuta [V, R1]. Con p ≤ 0.6 e σ_p ≤ 0.045 l'evento dista almeno 8.9 deviazioni standard [D, ricalcolo del supervisore]
elo_predictor.py: il percorso veloce itera solo su _CALC_COLS, quindi un calcolo che usa un'altra colonna deve aggiungerla lì [V la riga 475, R1; D la regola]. Dopo ogni modifica al file, confrontare lo SHA256 delle previsioni con quello di riferimento (vedi Moduli) [V, R21@2026-09-29b]
Duplicazioni [V, R1]:
- parsing della stagione: parse_season_start_year (elo_fit.py:96) e _parse_season_start_year (elo_predictor.py:91), con SEASON_REGEX in entrambi; regex in loading.py:101 e split.py:125, :258; int(s.split("-")[0]) in split.py:162, :279, :292 e nello script C5.2;
- due log-loss: compute_training_log_loss con clip a 1e-15 (elo_fit.py:200 e :277) e compute_log_loss con ValueError per p ≤ 0 (scoring.py:114); test_residuals.py:345 le confronta entro 1e-12;
- giornata da 10 e 38 cablata invece di MATCHDAY_SIZE: monitoring.py:258 e :429, script C5.1 e C5.2;
- _has_real_data definita in otto moduli di test.
Test che cercano frasi esatte nelle docstring: test_calibration.py:322-338, test_staking.py:405-410, test_us_c5_3_acceptance.py:122-127. La correzione della docstring di calibration.py deve preservarle [V, R1]
Asserzioni legate a seed, tolleranze o costanti empiriche, che si rompono se cambiano RNG, versioni o dati [V, R1]:
- conteggi reali cablati: test_split.py:483-491, test_leakage.py:434-436, test_us_c4_2_acceptance.py:137-139, test_elo_predictor.py:366-386, test_us_c5_2_acceptance.py:310-318;
- allarmi esatti di river: test_drift.py:324-335;
- tassi Monte Carlo entro l'intervallo al 99%: test_us_c2_acceptance.py e test_us_c5_2_acceptance.py:451-457;
- seed e tolleranze empiriche in test_us_c1_1, test_us_c1_2, test_simulate, test_estimation, test_timeseries, test_devig, test_drift, e in test_calibration, dove th1 != th3 dipende dai seed 12345 e 54321.
pandas 3: Date esce in datetime64[us] [V, R10@2026-09-29]; le colonne di testo hanno di default il dtype stringa [D]
Branch pre-c4: toglie .agent/ dal tracciamento e lo aggiunge a .gitignore, contro il versionamento di .agent/ in vigore su main [V, R3]. Non va unito senza decisione del programmatore [D]

## Punti ancora incerti
Esito di US-C5.3: la Baseline D coincide col riferimento (κ = 1 per entrambi i detector).
- Blocca: la chiusura di S5 e il ruolo della Baseline D fra gli agenti di C6.
- Alternative: (a) dichiararlo in tesi come esito, la riduzione non paga sul training, e portare D in C6 così com'è; (b) una variante di D pre-registrata, con griglia o obiettivo fissati prima dei risultati, accanto all'attuale; (c) lasciare D fuori da C6.
- Si procede: gli agenti A, B ed E di C6 non dipendono dalla scelta; B con λ = 0.25 coincide già col riferimento di C5.3.
Esito della CI su 736f5cd e sul PR di C5.
- Blocca: se la prossima story deve partire con una correzione della CI (installazione di river, test nuovi).
- Si procede: il primo task della story lo mette fra le cose da verificare prima di iniziare.
Confronto della Baseline E col −4.1% del paper, criterio di US-C6.2.
- Blocca: il task di C6.2 che lo esegue, perché il paper usa il 2023-24, bloccato fino a US-C8.2.
- Alternative: (a) rimandarlo a dopo lo sblocco; (b) eseguire E sulla validazione e dichiarare che il confronto col paper è solo indicativo.
- Si procede: A, B ed E si costruiscono e girano sulla validazione.
Versione del Modulo 1: raw, adottata in C5 su delega, senza conferma.
- Blocca: le probabilità date agli agenti di C6 e il Modulo 1 di C8.
- Alternative: (a) raw, la migliore su B365; (b) Platt, marginalmente migliore su Pinnacle (0.980927 contro 0.981229); (c) isotonica, peggiore ovunque.
- Si procede con raw.
Imposizione di H₀ prima del block bootstrap, e scelta di L.
- Blocca: la chiusura di T12, la correzione della docstring di calibration.py e la L delle soglie calibrate di C6.4 e C8.
- Si procede lasciando il test rosso e senza toccare calibration.py né false_rejection.py. In C5.2 la soglia è calibrata sul training del fit, dove H₀ vale per costruzione [D, ragionamento del supervisore in S5].
Lettura del 2023-24 da parte dello script C3.1 e di tests/test_data_loading.py:312.
- Blocca: l'affermazione in tesi (US-C3.3) che il test set non è mai stato letto.
- Alternative: (a) dichiararla come eccezione ammessa, limitata a copertura e caricamento; (b) un task che esclude le stagioni bloccate da script e test e rigenera il CSV di C3.1; (c) in più, estendere il test di guardia a tests/.
- Si procede: nessun task di C6 legge il test.
Prova del congelamento dello split.
- Blocca: la data da dichiarare in US-C3.3 e la conservazione di 2cea094, che dalla reflog può sparire verso fine ottobre 2026.
- Alternative: (a) dichiarare 90a77a1, con contenuto identico; (b) un tag su 2cea094 pubblicato su origin dal programmatore; (c) affidarsi al ref del PR #17 su GitHub, non verificato.
- Si procede: nessun task di codice dipende dalla scelta.
Stagione di training 2000-01 senza B365.
- Blocca: gli esperimenti di C6 e C8 alimentati da quote B365 su quello scenario; in C3.2 e nella calibrazione di κ è escluso.
- Alternative: (a) dichiararlo e procedere con 2010-11 e 2020-21; (b) per il solo 2000-01 un'altra terna completa (GB, IW, SB o WH); (c) rivedere lo scenario in una chat di backlog.
- Si procede: le stagioni di validazione hanno tutte B365.
Versionamento dei CSV E0.
- Blocca: se la CI potrà mai verificare le pipeline su dati reali; decisione del programmatore dopo il controllo della licenza.
- Si procede: i test sui dati reali girano in locale.
Lingua dei messaggi di assert e dei motivi di skip.
- Blocca: la regola da scrivere nei task di C6 e un eventuale task di pulizia.
- Alternative: (a) inglese, come i messaggi delle eccezioni; (b) italiano ammesso; (c) libera, senza pulizia.
- Si procede scrivendo in inglese quelli nuovi, che vanno bene con ogni scelta.

## Ultimo aggiornamento
R6@2026-10-07 — task di scrittura chiusi dopo la mappa del 2026-10-07: nessuno