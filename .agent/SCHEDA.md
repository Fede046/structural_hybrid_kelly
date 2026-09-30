# Scheda del progetto
Origine: mappa completa del 2026-09-29 a 27cf7a4 (serie 2026-09-29c), report fino a R1@2026-09-29c. Riferimenti: la numerazione R_n riparte da R1 a ogni mappa. @2026-09-29c: R1 = mappa a 27cf7a4. @2026-09-29b: R1 = mappa a 90a77a1, R2–R6 = risposte di Cline alla chat di scheda, R7–R33 = report dei task T20–T25. @2026-09-29 senza suffisso: R1 = mappa a 115e600, R2–R46 = report dei task T14–T19. @2026-09-28 e @2026-09-27 indicano le serie più vecchie. I fatti non rimappati conservano il riferimento originale.

## Stato repo
Radice: c:\Users\malse\Documents\GitHub\structural_hybrid_kelly [V, R1@2026-09-29c]
Alla mappa: branch main a 27cf7a4 "C4 (#18)"; working tree pulito, nessun file staged, modificato o non tracciato [V, R1@2026-09-29c]
main è allineato a origin/main rispetto all'ultimo fetch locale (0 avanti, 0 indietro). Nessun git fetch eseguito, quindi lo stato reale del remote non è verificato [V, R1@2026-09-29c]
Branch locali: solo main. Branch remoti: origin/HEAD → origin/main, origin/main [V, R1@2026-09-29c]. Nessun branch di lavoro aperto: il branch della prossima story lo crea il programmatore da main [D, convenzione dei branch]
Remote origin: https://github.com/Fede046/structural_hybrid_kelly.git, fetch e push [V, R1@2026-09-29c]
Ultimi cinque commit su main: 27cf7a4 "C4 (#18)", 90a77a1 "C3 (#17)", 115e600 "C2 (#16)", 1e7813d "C1 (#14)", 640b906 "C1 (#13)" [V, R1@2026-09-29c]
Commit di story su main: 115e600 = S2/C2, 90a77a1 = S3/C3, 27cf7a4 = S4/C4 [V, R1@2026-09-29, R1@2026-09-29b e R1@2026-09-29c]
Il branch C4 è entrato in main come il solo 27cf7a4 e non esiste più localmente [V, R1@2026-09-29c]. Partiva da 90a77a1 e aveva i commit 4b9e6c1 e 475f65f (solo .agent/), 7f8e928 (T20), 4710045 (T21), 15b2204 (T22), d329766 (T23), dc9d8f2 (T24), più le modifiche di T25 [V, R7, R11, R15, R22, R24, R27 e R31@2026-09-29b]. Lo stesso vale per C3 (→ 90a77a1) e C2 (→ 115e600) [V, R1, R4 e R5@2026-09-29b]. Il meccanismo è lo squash merge del PR su GitHub [D]
Le modifiche di T25 sono in 27cf7a4: .agent/report/ contiene T1.md … T25.md e il working tree è pulito [V, R1@2026-09-29c]. Che il contenuto di 27cf7a4 coincida con la punta del branch C4 non è verificato [D]
File ignorati presenti: .pytest_cache/, .venv/, data/raw/E0/, e __pycache__/ in scripts, src/shk, kelly, stats, data, market, model e tests [V, R1@2026-09-29c]
Albero tracciato a 27cf7a4 [V, R1@2026-09-29c]:
- src/shk/ con i sottopacchetti kelly/, stats/, data/, market/, model/
- tests/ con 24 moduli di test; scripts/ con 8 script
- results/ con 8 CSV e .gitkeep; thesis/figures/ con 8 PNG e .gitkeep
- config/ con .gitkeep e split.toml; data/raw/ con .gitkeep
- .github/workflows/test.yml
- .agent/ con PROTOCOLLO.md, BACKLOG.md, MAPPA.md, SCHEDA.md, report/T1.md … report/T25.md
- alla radice pyproject.toml, uv.lock, .gitignore, LICENSE
config/split.toml: fino a 90a77a1 lo toccava su main solo quel commit (2026-09-29T12:54:03+02:00) [V, R2@2026-09-29b]; che 27cf7a4 non lo tocchi non è verificato [D]. Il contenuto è identico a quello di 2cea0944b651b424fb704e03747340cfc26eda0e (2026-09-29T11:47:18+02:00), raggiungibile solo dalla reflog locale [V, R3–R6@2026-09-29b]. Il testo coincide con quello approvato, con test_unlocked = false [V, R28 e R38@2026-09-29]
data/raw/E0/ contiene 31 CSV, da 1993-94.csv a 2023-24.csv [V, R1@2026-09-29c]. Li ha scaricati il programmatore il 2026-09-29, per sua decisione solo nella finestra di KellyBench [V, R6 e R7@2026-09-29]. .gitignore esclude data/raw/* tranne .gitkeep, quindi i CSV non sono versionati [V, R1@2026-09-29c]
Nessun .env presente [V, R1@2026-09-29c, git status --ignored]

## Stack e comandi
Pacchetto structural-hybrid-kelly 0.1.0 (in pyproject.toml e src/shk/__init__.py), importabile come shk, sorgenti in src/shk/ [V, R1@2026-09-29c]
requires-python >=3.11; la CI usa Python 3.12 [V, R1@2026-09-29c]
Build backend hatchling [V, R1@2026-09-29c]; build con hatch build o python -m build [D]
Dipendenze runtime: numpy, scipy, matplotlib, pandas. Dipendenze dev: pytest. Nessun vincolo di versione. river non è fra le dipendenze [V, R1@2026-09-29c]. Se river sia installato nel venv non è verificato [D]
uv.lock è presente alla radice [V, R1@2026-09-29c]; che non contenga pandas non è verificato da una ricerca [D]; uv sync come alternativa locale [D]
CI (.github/workflows/test.yml): pip install -e ".[dev]" senza uv.lock, poi pytest -v [V, R1@2026-09-29c]; trigger su push verso main e su pull_request [D]
Esecuzioni della CI note [V, log CI forniti dal programmatore il 2026-09-28 e il 2026-09-29]:
- 2026-09-28: Linux, Python 3.12.14, pytest 9.1.1, dipendenze senza vincoli; prima di T13 falliva sul confronto dei float come stringhe.
- 2026-09-29, branch C4 dopo T24: 263 raccolti, 15 deselezionati, 237 passati, 9 saltati, 2 falliti, 4.05 s. I due falliti erano i test di ricalcolo di C4.2 e C4.3, corretti in T25.
Esito della CI dopo T25 e su 27cf7a4 non verificato [D]
Test veloci: pytest -v; addopts = "-m 'not slow'" in pyproject.toml esclude i test slow [V, R1@2026-09-29c]
Solo test slow: pytest -m slow; tutti i test: pytest -o addopts="" [D]
Interprete: Cline esegue ogni comando Python con il venv, cioè .\.venv\Scripts\python.exe -m pytest -v e .\.venv\Scripts\python.exe <script> [V, R7@2026-09-28; decisione del programmatore 2026-09-28]. Nel venv shk è installato in modalità editable [V, R7@2026-09-28]. Il Python di default del terminale di Cline è C:\Users\malse\anaconda3\python.exe, dove shk non è installato [V, R6@2026-09-28]
Venv .venv: Python 3.12.7, pytest 9.1.1 [V, R7 e R15@2026-09-28]; NumPy 2.5.2, SciPy 1.18.1, pandas 3.0.6 [V, R10@2026-09-29]
Suite veloce locale, con i dati locali presenti: dopo T25 248 verdi, 15 deselezionati, 50.28 s [V, R33@2026-09-29b]. I 248 sono i 181 di 90a77a1 più 67 di S4 [V, R11, R21, R23, R26 e R29@2026-09-29b; somma ricontata dal supervisore]. I 67 di S4 sono:
- test_elo.py 31, test_elo_predictor.py 8, test_us_c4_1_acceptance.py 6 veloci;
- test_scoring.py e test_us_c4_2_acceptance.py 11;
- test_recalibration.py e test_us_c4_3_acceptance.py 11.
Test slow: 15, cioè 9 di C1, 5 di C2 e 1 di C4 [V, R23@2026-09-29b]:
- i 14 di C1 e C2: all'ultimo esito 13 verdi e 1 rosso per il risultato noto (vedi Zone fragili), circa 117 s [V, R14@2026-09-28; non rieseguiti dopo];
- test_elo_fits_matches_data_recalibration: verde in 119.09 s [V, R23@2026-09-29b].
Esperimenti, tutti con .\.venv\Scripts\python.exe scripts/<nome>.py dalla radice. Quelli su dati reali richiedono data/raw/E0/ presente. Comandi dei singoli script [D, R1@2026-09-29c]:
- C1.1 us_c1_1_growth_vs_lambda.py;
- C1.2 us_c1_2_estimation_error.py: circa 70 s; CSV identici fra due esecuzioni [D, era V R16@2026-09-27];
- C2 us_c2_anova_autocorrelation.py: circa 90 s; SHA256 6711B906A5D0170124BE816BAB04C336854CF7FF62DF135FDC18F22B84AB3831 sul CSV di allora [V, R14@2026-09-28]; non ricalcolato sul CSV versionato [D];
- C3.1 us_c3_1_data_coverage.py: SHA256 F9EEA7264F5457A1728EA609CD6660BCEE9779D450099D446CC30A919D73E15C, stabile su due esecuzioni [V, R14@2026-09-29];
- C3.2 us_c3_2_devig_divergence.py: SHA256 5e9743252db28de1c2c6e28b5584725f4c2f78f47d4d830e318922d88e77ce92, stabile su quattro esecuzioni [V, R43 e R44@2026-09-29];
- C4.1 us_c4_1_elo_walkforward.py: circa 49 s; SHA256 92716bc7e6aa6a7b798370a09d1b31b33b0c0a49311bf35cd810f7975489f282, stabile su due esecuzioni [V, R23@2026-09-29b];
- C4.2 us_c4_2_g_hat.py: SHA256 e076f16f6a39606a4fcba04be5679a1fa0d7ce9f1c44893df47df79e39dee3a9, stabile su due esecuzioni [V, R26@2026-09-29b]; durata non misurata [D];
- C4.3 us_c4_3_calibration.py: SHA256 cc0d3577168ea47cc7f89b9d44f59c29be67062a2ad41634285d11e417ac2073, stabile su due esecuzioni [V, R29@2026-09-29b]; durata non misurata [D].
File di configurazione: pyproject.toml e config/split.toml [V, R1@2026-09-29c]
Nessuna variabile d'ambiente letta dal codice [D; nessuna ricerca nell'elenco comandi di R1@2026-09-29c]

## Moduli e responsabilità
src/shk/ contiene 21 moduli applicativi (6 in kelly, 4 in stats, 4 in data, 2 in market, 5 in model) più 6 __init__.py [V, R1@2026-09-29c; conteggio ricontato dal supervisore]. Nessun modulo di drift detection [D, dall'elenco dei moduli di R1@2026-09-29c]
src/shk/__init__.py — espone __version__ [V, R1@2026-09-28]
src/shk/kelly/__init__.py — re-esporta kelly_fraction e log_growth_rate tramite __all__; expected_final_wealth non è re-esportata [V, R1@2026-09-29c]
src/shk/kelly/core.py — formule chiuse per scommessa binaria: kelly_fraction(p, b), log_growth_rate(f, p, b), expected_final_wealth(f, p, b, T, b0=1.0) (righe 97-144). Nessun import interno [V, R1@2026-09-29c]
src/shk/kelly/core.py — kelly_fraction calcola (b·p − q)/b, dà 0.0 se il valore è ≤ 0, accetta solo scalari [D, era V R7@2026-09-27]
src/shk/kelly/simulate.py — nessun import interno [V, R1@2026-09-29c]:
- draw_outcomes(p, T, M, rng) → (M, T) bool, True = vincita;
- simulate_growth(outcomes, fractions, b) → log-wealth (M, T+1) float64 con colonna 0 nulla; frazioni broadcastabili da (), (T,), (1, T), (M, 1), (M, T); rifiuta frazioni fuori da [0, 1) [V, R1@2026-09-28 per il broadcasting];
- log_wealth_paths(outcomes, f, b) delega a simulate_growth.
src/shk/kelly/simulate.py — fattori logaritmici np.log(1 + b*f) e np.log(1 - f), senza log1p [D, era V R5@2026-09-27]
src/shk/kelly/estimation.py — relative_perturbation(p, delta) e noisy_estimates(p, sigma_p, T, M, rng); le stime sono saturate in [0, 1] con np.clip [V, R1@2026-09-29c]
src/shk/kelly/staking.py — kelly_staking(p_hat, b, lam=1.0); StakingMoments (NamedTuple: mean_c, mean_c2, var_c, fraction_zero); staking_moments(f_hat, f_star); plugin_staking(p_hat, b, sigma_p); nessun import interno [V, R1@2026-09-29c]
src/shk/kelly/staking.py — formule [D, era V R8 e R14@2026-09-27]:
- kelly_staking = lam·max(0, (b·p_hat − (1 − p_hat))/b), senza limite superiore su lam né sulla frazione;
- plugin_staking = λ_t·kelly_staking(p_hat, b), con λ_t = 1/(1 + (o·sigma_p/EV̂)²), o = b + 1, EV̂ = p_hat·o − 1, e 0.0 dove EV̂ ≤ 0.
src/shk/kelly/scenarios.py — contenuto; importa simulate.py e staking.py [V, R1@2026-09-29c]:
- dataclass frozen Scenario(name, p, b, T, M); BASE_SCENARIO (0.60, 1.0, 1000, 10000); SUBTLE_SCENARIO (0.52, 1.0, 380, 10000); SEED = 20260927;
- spawn_generators(seed=SEED);
- draw_scenario_outcomes(scenario, rng), che delega a draw_outcomes;
- simulate_scenario(scenario, outcomes, p_hat, lam=1.0), con puntate da kelly_staking e crescita da simulate_growth.
spawn_generators restituisce due generatori da SeedSequence.spawn(2): il primo per gli esiti, il secondo per il rumore [D, era V R10@2026-09-27]
src/shk/kelly/metrics.py — funzioni su paths: final_log_wealth, median_growth_rate, median_final_wealth, mean_final_wealth, max_drawdown ((M,) in [0, 1)), fraction_below_start. Nessun import interno [V, R1@2026-09-28; nomi confermati R1@2026-09-29c]
src/shk/kelly/metrics.py — dettagli [D, era V R9 e R13@2026-09-27]:
- median_growth_rate = mediana di ln(B_T/B_0)/T, con T = paths.shape[1] − 1;
- drawdown mediano = np.median(max_drawdown(paths));
- fraction_below_start = quota di traiettorie con B_T < B_0.
src/shk/stats/__init__.py — sola docstring in italiano: nessun import, nessuna re-esportazione, nessun __all__ [V, R5@2026-09-28]
src/shk/stats/anova.py — funzioni pure [V, R4@2026-09-28; firme R1@2026-09-29c]:
- OneWayAnovaResult (NamedTuple: ss_between, ss_within, ss_total, df_between, df_within, ms_between, ms_within, f_statistic, p_value);
- oneway_anova(groups), con p-value da scipy.stats.f.sf;
- oneway_anova_vectorized(values, labels) → float se values è 1D, altrimenti ndarray di forma values.shape[:-1]. values e labels devono essere np.ndarray (altrimenti TypeError); etichette int 0..k−1, tutte presenti.
src/shk/stats/timeseries.py — generate_ar1_series(phi, n, m, rng) → ndarray float64 (m, n), righe = serie [V, R7@2026-09-28]:
- estrazioni: prima x_0 ~ N(0, 1/(1 − φ²)) con size=m, poi innovazioni N(0, 1) in blocco (m, n − 1); ciclo solo sul tempo;
- ValueError per φ non finito o |φ| ≥ 1, n < 2, m < 1;
- TypeError per n o m bool o non interi, e per rng non Generator.
src/shk/stats/false_rejection.py — costanti e tipi [V, R13 e R14@2026-09-28; righe R1@2026-09-29c]:
- costanti: PHI_VALUES = (0.0, 0.3, 0.5, 0.7), N_OBS = 380, N_SERIES = 1000, ALPHA = 0.05, SEED_C2 = 20260928;
- disegni: DESIGN_CONTIGUOUS_2, DESIGN_CONTIGUOUS_38, DESIGN_RANDOM_2, e DESIGNS in quest'ordine;
- CSV_COLUMNS (10), FLOAT_CSV_COLUMNS, BLOCK_LENGTHS = (7, 20, 40), N_BOOT = 999;
- METHOD_NOMINAL (riga 22), METHOD_BLOCK_BOOTSTRAP;
- RejectionResult: dataclass frozen con to_row(); block_length str ("" per nominal, str(L) per block_bootstrap);
- PhiStreams (righe 48-65): NamedTuple con series_rng, perm_rng, boot_seed (SeedSequence).
src/shk/stats/false_rejection.py — funzioni [V, R13 e R14@2026-09-28; righe R1@2026-09-29c]:
- spawn_c2_generators(seed=SEED_C2) (righe 248-297) → tupla ordinata come PHI_VALUES;
- make_design_labels(design, n_obs=N_OBS), critical_value_nominal, monte_carlo_interval_99;
- compute_nominal_rejection_rates(seed=SEED_C2) → 12 RejectionResult, in ordine DESIGNS × PHI_VALUES;
- compute_calibrated_rejection_rates(seed=SEED_C2) → 12 RejectionResult per contiguous_2, in ordine BLOCK_LENGTHS × PHI_VALUES.
compute_calibrated_rejection_rates in dettaglio [V, R13 e R14@2026-09-28]:
- riusa le serie del nominale;
- per ogni φ esegue boot_seed.spawn(len(BLOCK_LENGTHS)) una volta e usa un generatore per L, in sequenza sulle serie;
- chiama calibrate_threshold sulla serie grezza (H₀ non imposta);
- rigetto se la F osservata supera la soglia.
src/shk/stats/calibration.py — funzioni; nessun import da anova.py, timeseries.py o false_rejection.py [V, R12@2026-09-28; firme R1@2026-09-29c]:
- moving_block_indices(n, block_length, n_boot, rng) → int64 (n_boot, n), con inizi da rng.integers(0, n − L + 1, size=(n_boot, ⌈n/L⌉));
- compute_order_statistic_index(b, alpha) → ⌈(1 − α)(b + 1)⌉, arrotondato se entro 1e-9; ValueError se supera b;
- calibrate_threshold(data, statistic, block_length, n_boot, alpha, rng, vectorized=False) → float. Indici estratti una volta; statistica attesa float64 (n_boot,), finita, altrimenti ValueError; soglia = elemento k − 1 delle statistiche ordinate.
src/shk/stats/calibration.py — la docstring del modulo ha due parti in contraddizione [V, R12@2026-09-28 e R1@2026-09-29c]:
- lo schema (a), che per l'ANOVA F indica come dato "la serie della risposta";
- il principio (c), "imporre H₀ spetta al chiamante".
Lo schema l'ha dettato il supervisore ed è da correggere [V, R12@2026-09-28]
src/shk/data/__init__.py — sola docstring in italiano [D]
src/shk/data/loading.py — DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "raw" / "E0". load_all_seasons(data_dir=DEFAULT_DATA_DIR, seasons: Collection[str] | None = None) → un DataFrame con [V, R10 e R26@2026-09-29]:
- colonna season (YYYY-YY, dal nome file);
- Date in datetime64[us] senza nulli;
- ordinamento stabile per season e Date.
src/shk/data/loading.py — validazioni [V, R10 e R26@2026-09-29; D per i dettagli di seasons]:
- TypeError per data_dir non str né Path, e per seasons str o con elementi non str;
- FileNotFoundError per directory inesistente;
- ValueError per: directory senza CSV, nome file non conforme, date miste, non conformi o fra 1° luglio e 31 agosto, campo in eccesso non vuoto, colonna senza nome non vuota, seasons vuota o con stagione senza file.
Con seasons valorizzato si validano i nomi di tutti i file ma si leggono solo quelli richiesti [D]
src/shk/data/loading.py — decodifica [D, piano approvato di T14]:
- per file: BOM → utf-8-sig, UTF-8 valido → utf-8, altrimenti cp1252, senza try;
- righe vuote scartate, campi mancanti in coda completati;
- Date con %d/%m/%y o %d/%m/%Y.
src/shk/data/coverage.py — costanti e classificazione [V, R14–R17 e R45@2026-09-29; righe R1@2026-09-29c]:
- NON_ODDS_COLUMNS;
- ColumnClassification (NamedTuple: group_type, group_name, source, market, timing, kind);
- classify_column(name), pubblica: group_type ∈ {1x2_prematch, 1x2_closing, aggregators, other_markets}, timing ∈ {prematch, closing}, kind ∈ {odds, line, count}. Bb*, Max* e Avg* sono aggregators. ValueError per colonne non di quota o sconosciute;
- GROUP_TYPE_ORDER (righe 68-74);
- COVERAGE_CSV_COLUMNS (12 colonne); compute_coverage(df) → una riga per stagione × gruppo presente.
coverage.py — regole di conteggio [D, piano approvato di T15]:
- presenza = almeno un valore non nullo del gruppo nella stagione;
- non validità solo per kind = odds (non numerico, non finito o ≤ 1);
- NaN conta come mancante;
- il gruppo results controlla gol, FTR e la loro coerenza.
src/shk/data/split.py — tipi e funzioni; delega a loading.py [V, R1@2026-09-29c; R26 e R39@2026-09-29 per il comportamento]:
- DEFAULT_SPLIT_CONFIG_PATH = radice / config / split.toml;
- TestSetLockedError(RuntimeError) con __test__ = False;
- SplitConfig (NamedTuple: frozen_on, test_unlocked, test_unlocked_on, training, validation, test);
- read_split_config(config_path) controlla chiavi esatte, ruoli disgiunti, test non vuoto, training e validation < min(test);
- load_by_role(role, config_path, data_dir): con il test bloccato, "test" → TestSetLockedError prima di leggere. Le stagioni ≥ min(test) non sono mai lette dagli altri ruoli. history = stagioni < min(test) né di training né di validation. Una stagione elencata ma assente dà ValueError.
src/shk/data/walkforward.py — importa coverage.py; non chiama load_all_seasons [V, R45 e R46@2026-09-29; righe e firme R1@2026-09-29c]:
- PREMATCH_IDENTIFIERS (righe 13-15), LeakageError(RuntimeError);
- get_prematch_whitelist(columns) → tupla per inclusione: Div, Date, HomeTeam, AwayTeam, season, Time, più le colonne con kind = odds e timing = prematch; lru_cache;
- walkforward_split(df, seasons_to_predict) → coppie (storia = df.iloc[:searchsorted(Date, side="left")], partita ridotta alla whitelist). ValueError se df non è ordinato per Date o mancano Date o season; TypeError se seasons_to_predict è str o ha elementi non str;
- check_leakage(history, match, whitelist=None) → lista di violazioni (data non anteriore, partita nella storia, campi fuori whitelist); assert_no_leakage solleva LeakageError.
walkforward_split e assert_no_leakage sono usati da tests/test_leakage.py e da predict_elo_walkforward, che chiama assert_no_leakage su ogni coppia [V, R21@2026-09-29b e R1@2026-09-29c]
src/shk/market/__init__.py — sola docstring in italiano [V, R32@2026-09-29]
src/shk/market/devig.py — funzioni; nessun import da shk.data [V, R30–R36 e R39@2026-09-29; R1@2026-09-29c]:
- implied_probabilities(odds) → (N, n); overround(odds) → (N,) = S − 1;
- devig_proportional(odds) → (N, n);
- devig_additive(odds) → (N, n), con riga di NaN dove un q ≤ 0;
- devig_power(odds) → (q (N, n), k (N,)).
Validazione comune: ndarray (N, n) con n ≥ 2; TypeError per argomento non ndarray o dtype non reale; ValueError per forma sbagliata o quote non finite o ≤ 1; conversione interna in float64.
src/shk/market/devig.py — power: Newton vettorizzato da k = 1, con salvaguardia k_new ≥ k/2; MAX_NEWTON_ITERATIONS = 50 (riga 7); RuntimeError se dopo il ciclo |Σq − 1| > 1e-12 su qualche mercato [V, R32@2026-09-29 e R1@2026-09-29c]
src/shk/market/divergence.py — costanti [V, R41 e R44@2026-09-29; riga R1@2026-09-29c]:
- ODDS_BINS (1, 1.5, 2, 3, 5, 10, inf), ODDS_BIN_LABELS, REFERENCE_EDGE = 0.02, B365_ODDS_COLUMNS (riga 33);
- DIVERGENCE_CSV_COLUMNS (19): level, category, n_outcomes, matches_used, matches_excluded, additive_nan_matches, mean_overround, mean_q_* per metodo, mean_spread_pts, p99_spread_pts, max_spread_pts, mean_relative_spread, max_spread_ratio_to_edge, p99_spread_ratio_to_edge, max_abs_sum_error_* per metodo.
divergence.py — funzioni [V, R41 e R44@2026-09-29; D per i dettagli]:
- assign_odds_bin: fasce chiuse a sinistra;
- compute_divergence_table: partite usate = B365 valida e additivo applicabile; p99 con np.percentile method="linear".
src/shk/model/__init__.py — sola docstring in italiano [V, R11@2026-09-29b]
src/shk/model/elo.py — funzioni pure, senza RNG né accesso ai dati; importate da elo_predictor.py [V, R16 e R17@2026-09-29b; R1@2026-09-29c]:
- elo_delta(r_home, r_away, h=0.0), solo scalari;
- expected_score(delta, s=400.0), E = 1/(1 + 10^(−delta/s));
- elo_update(r_home, r_away, outcome, k, h=0.0, s=400.0) → (R_casa', R_trasferta'), con S = 1, 0.5, 0 per H, D, A, a somma zero;
- davidson_probabilities(delta, nu, s=400.0) e constant_draw_probabilities(delta, c, s=400.0) → (p_home, p_draw, p_away).
Uno scalare reale dà float; un ndarray, anche 0-d, dà ndarray float64 della stessa forma.
src/shk/model/elo.py — validazioni [V, R11@2026-09-29b, test verdi]:
- TypeError per bool, np.bool_, non numerici, liste, stringhe, ndarray bool o complessi;
- ValueError per valori non finiti, ν ≤ 0, c fuori da (0, 1), s ≤ 0, k < 0, outcome fuori da H, D, A; k = 0 ammesso.
src/shk/model/elo.py — i rami di E e Davidson divergono solo per |delta/s| > 308, fuori da ogni valore realistico [V, R12@2026-09-29b; D per l'irrilevanza]:
- ramo ndarray: np.power senza guardie (righe 164-166 e 282-288);
- ramo scalare: math.pow con guardie (righe 169-174 e 291-299).
src/shk/model/elo_predictor.py — pubblico; importa walkforward.py ed elo.py [V, R1@2026-09-29c]:
- SEASON_REGEX; compute_season_standings(matches) → classifica con almeno team, points, goal_diff, goals_for [colonne V, R19@2026-09-29b];
- predict_elo_walkforward e predict_elo_fast con firma (df, seasons_to_predict, k, h, nu, s=400.0, initial_rating=1500.0) → DataFrame con season, Date, HomeTeam, AwayTeam, rating_home, rating_away, delta, p_home, p_draw, p_away, home_promotion, away_promotion;
- diagnose_season_transitions(df) → una riga per stagione dalla seconda (n_teams, promosse nuove e tornanti, retrocesse effettive e calcolate, relegation_agreement) [colonne V, R19–R22@2026-09-29b].
src/shk/model/elo_predictor.py — interno: _EloTracker (consume_match, predict_match, _ensure_season) condiviso dai due percorsi; _parse_season_start_year (riga 91, duplica parse_season_start_year di elo_fit.py:96); _CALC_COLS = Date, season, HomeTeam, AwayTeam, FTR, FTHG, FTAG (righe 14-22) [V, R21 e R22@2026-09-29b; righe 91 e 96 R1@2026-09-29c]
src/shk/model/elo_predictor.py — neopromosse: alla prima partita di una stagione si congela la classifica della precedente. Le squadre nuove prendono la media dei rating finali delle ultime tre; le tornanti riprendono l'ultimo rating attivo. Nella prima stagione del DataFrame tutti partono da initial_rating [V, R1@2026-09-29c per la regola; D per i dettagli, piano approvato]
src/shk/model/elo_predictor.py — validazioni: ValueError per FTR fuori da H, D, A, colonne mancanti, stagioni non consecutive o decrescenti lungo Date, df non ordinato, parametri non validi; TypeError per tipi sbagliati e per seasons_to_predict str [V, R19@2026-09-29b]
src/shk/model/elo_predictor.py — percorsi [V, R21 e R22@2026-09-29b]:
- via fornitore: assert_no_leakage su ogni coppia;
- veloce: itertools.groupby per Date su df[_CALC_COLS].itertuples; prima si prevede tutta la data, poi si aggiorna (righe 477-484).
Sui dati reali i due percorsi danno CSV identici byte per byte, SHA256 0b3048a7a170e7e149f6cb96c2790e36d3f05010a4d5ce35e1ea0febc1fcbce1 con K = 20, h = 60, ν = 1.
src/shk/model/elo_fit.py — funzioni [V, R1@2026-09-29c; R23 e R24@2026-09-29b per i dettagli]:
- derive_fit_schedule(training, validation=None), training anche SplitConfig → dict dal fit a {"training": […], "validation": […]}; fit 2000-01, 2010-11, 2020-21 con le stagioni di training ≤ j;
- compute_training_log_loss → (loss, preds); calibrate_single_fit, Nelder-Mead su K, h, ν;
- calibrate_all_fits(df, schedule) (righe 308-317);
- parse_season_start_year (riga 96).
elo_fit.py — tipi e costanti [V, R1@2026-09-29c]:
- EloFitParams (NamedTuple: k, h, nu, c);
- EloCalibrationResult (NamedTuple: fit_through, k, h, nu, c, log_loss_train, log_loss_train_baseline, n_train_matches, success, message, nit, nfev, duration_seconds, is_on_boundary);
- ELO_FITS, BOUNDS_K, BOUNDS_H, BOUNDS_NU, WALKFORWARD_CSV_COLUMNS (15 colonne).
src/shk/model/elo_fit.py — ELO_FITS, congelato il 2026-09-29, coincide con la ricalibrazione entro rel_tol 1e-9 [V, R23@2026-09-29b]:
- "2000-01": K = 10.318224689650037, h = 125.54022316884253, ν = 0.8062246331085681, c = 0.2657894736842105;
- "2010-11": K = 9.934776455088759, h = 127.87791672140764, ν = 0.8775613268630023, c = 0.2789473684210526;
- "2020-21": K = 7.928543266007228, h = 78.033626101627, ν = 0.7603760315281511, c = 0.25877192982456143.
src/shk/model/scoring.py — pubblico; importa devig.py, elo_fit.py, elo_predictor.py [V, R1@2026-09-29c]:
- costanti PINNACLE_CLOSING_START_SEASON, PINNACLE_START_YEAR, DEVIG_METHODS, SERIES_NAMES, MATCH_KEYS, CSV_COLUMNS;
- metriche: compute_log_loss (puntuale), compute_mean_log_loss, compute_g_hat_terms, compute_g_hat, compute_cumulative_g_hat;
- generate_validation_predictions(df, fits, schedule) (riga 218), che chiama predict_elo_fast con i parametri di ciascun fit;
- align_predictions_with_odds(df_preds, df_raw) su season, Date, HomeTeam, AwayTeam (riga 290), con ValueError per chiavi mancanti o duplicate [R26 e R27@2026-09-29b];
- prepare_series_evaluation(df_aligned, series, schedule) (riga 355) → SeriesEvaluationData.
Serie: "b365_prematch" (B365H/D/A) e "pinnacle_closing" (PSCH/D/A, stagioni con anno iniziale ≥ 2012).
src/shk/model/scoring.py — SeriesEvaluationData (NamedTuple, righe 336-352): series, seasons, matches_total, matches_used, missing_odds, invalid_odds, additive_inapplicable, matches_excluded, df_used, p_model, q_proportional, q_additive, q_power (N×3), outcomes (H/D/A). Righe in ordine cronologico stabile [V, R27@2026-09-29b e R1@2026-09-29c]
src/shk/model/scoring.py — metriche senza eps: una probabilità ≤ 0 per l'esito realizzato dà ValueError; matrici (N, 3) con righe a somma 1 entro 1e-9 [D, piano approvato; test verdi R26@2026-09-29b]
src/shk/model/recalibration.py — tipi e costanti [V, R1@2026-09-29c]:
- IsotonicModel (NamedTuple: p_support, q_support); PlattModel (NamedTuple: a, b, success, nit, nfev); FitCalibrationMaps (NamedTuple: fit_through, isotonic, platt), mappe per esito;
- PROB_LOWER_CLIP, PROB_UPPER_CLIP, OUTCOMES, CALIBRATION_CSV_COLUMNS (16 colonne).
recalibration.py — funzioni [V, R1@2026-09-29c]:
- fit_isotonic_single, predict_isotonic_single, fit_platt_single, predict_platt_single;
- generate_fit_training_predictions (righe 322-337);
- fit_all_calibration_maps, sulle sole partite di training di ciascun fit;
- recalibrate_series_predictions: one-vs-rest, limite a [1e-6, 1 − 1e-6], rinormalizzazione;
- compute_reliability_table (10 fasce), brier_score (multiclasse), compute_brier_scores.
recalibration.py — algoritmi [V, R29 e R30@2026-09-29b per l'uso; D per i dettagli]:
- isotonica con valori uguali aggregati, scipy.optimize.isotonic_regression e np.interp a estrapolazione costante;
- Platt con L-BFGS-B, gradiente analitico, punto iniziale (1, 0).
scripts/ — otto script, ognuno con run_experiment() senza parametri [V, R1@2026-09-29c]:
- us_c1_1_growth_vs_lambda.py, us_c1_2_estimation_error.py, us_c2_anova_autocorrelation.py;
- us_c3_1_data_coverage.py, us_c3_2_devig_divergence.py;
- us_c4_1_elo_walkforward.py, us_c4_2_g_hat.py, us_c4_3_calibration.py.
Nessun test chiama un run_experiment() [D, affermazione negativa senza ricerca in R1@2026-09-29c]
scripts/us_c2_anova_autocorrelation.py — PNG con plt.subplots(1, 2) [V, R13 e R14@2026-09-28]:
- pannello A: nominale, tre disegni;
- pannello B: contiguous_2 nominale e una curva per L;
- in entrambi linea ad ALPHA e banda al 99%.
scripts/us_c3_1_data_coverage.py — usa load_all_seasons (ammesso) e compute_coverage. PNG con imshow di complete_rows/total_rows, colormap viridis, gruppi assenti in grigio #dcdcdc [V, R14 e R17@2026-09-29]
scripts/us_c3_2_devig_divergence.py — read_split_config, poi load_by_role("training") e load_by_role("validation") concatenati, poi compute_divergence_table. PNG a due pannelli [V, R43@2026-09-29]
scripts C4 (us_c4_1, us_c4_2, us_c4_3) — leggono lo split con read_split_config e i dati con load_by_role (history, training, validation) [V, R1@2026-09-29c]
- C4.1: PNG con i profili della log-loss di training in K e in h, calcolati da ELO_FITS [V, R23@2026-09-29b];
- C4.2: PNG a due pannelli, una serie ciascuno e tre metodi [V, R26@2026-09-29b];
- C4.3: PNG a due pannelli (aggregato con tre versioni; per esito con la versione raw), 2025×825 px [V, R29 e R30@2026-09-29b].
tests/ — 24 moduli [V, R1@2026-09-29c]:
- unitari: test_kelly_core, test_simulate, test_estimation, test_staking, test_metrics, test_anova, test_timeseries, test_calibration, test_data_loading, test_coverage, test_split, test_devig, test_leakage, test_elo, test_elo_predictor, test_scoring, test_recalibration;
- accettazione: test_us_c1_1_acceptance, test_us_c1_2_acceptance, test_us_c2_acceptance, test_us_c3_2_acceptance, test_us_c4_1_acceptance, test_us_c4_2_acceptance, test_us_c4_3_acceptance.
Contenuto dei moduli di test (1/2):
- test_anova.py: 23 test veloci. Toy; concordanza con scipy.stats.f_oneway (F entro 1e-12, p-value entro 1e-10); partizione della devianza; versione vettorizzata [V, R4@2026-09-28; tolleranze R1@2026-09-29c].
- test_timeseries.py: 13 test veloci. Forma e dtype, riproducibilità, varianza e autocorrelazione pooled su φ ∈ {0.0, 0.3, 0.7} con seed 20260928, validazioni [V, R7@2026-09-28].
- test_calibration.py: 15 funzioni, 18 test. Indici, statistica d'ordine, vectorized contro non vectorized, seed, docstring, validazioni [V, R12@2026-09-28].
- test_us_c2_acceptance.py: 11 veloci e 5 slow, fixture scope="module". Le colonne di FLOAT_CSV_COLUMNS usano math.isclose (rel_tol 1e-12, abs_tol 0); le altre si confrontano come stringhe [V, R15@2026-09-28].
- test_data_loading.py: 18 test veloci su CSV sintetici in tmp_path, più uno sui dati reali saltato senza CSV [V, R10@2026-09-29].
- test_coverage.py: 12 test veloci su DataFrame sintetici [V, R15, R16 e R18@2026-09-29].
- test_split.py: 14 test veloci. Validazioni, blocco e sblocco del test, test di guardia AST su sorgenti sintetici e sul repository, file reale split.toml, dati reali per ruolo (saltato senza CSV) [V, R26@2026-09-29].
Contenuto dei moduli di test (2/2):
- test_leakage.py: 9 test veloci. Fornitore su dati sintetici, tre mutanti, campi vietati; nessun leakage sulle 8 360 partite reali (8.05 s, saltato senza CSV) [V, R46@2026-09-29].
- test_devig.py: 8 test veloci. Valori di riferimento (5e-6 sulle probabilità, 5e-5 su k); 10 000 mercati con default_rng(20260929); caso S = 1; NaN dell'additivo su (1.05, 10.0, 50.0); mercati estremi [V, R32 e R35@2026-09-29].
- test_us_c3_2_acceptance.py: 11 test veloci. Fasce, tabella sintetica, schema e 29 righe del CSV, somma a 1 entro 1e-12, overround medio in [0.01, 0.15], ricalcolo dai dati reali entro 1e-12 (saltato senza CSV) [V, R44@2026-09-29 e R1@2026-09-29c].
- test_elo.py: 31 test veloci. Somma zero; somme a 1; tabella delle note 2.8 §3.3 con s = 200 forzato (24 valori, tolleranza 5e-4); simmetria e monotonia; limite ν = 1e-12; p_draw == c; validazioni [V, R11@2026-09-29b e R1@2026-09-29c].
- test_elo_predictor.py: 8 test veloci. verify_future_invariance (righe 92-147) sui due percorsi e su un mutante; invarianza alle quote; neopromosse a mano; equivalenza fra percorsi (reali saltati senza CSV); transizioni; determinismo. Costanti K = 20, h = 60, ν = 1, s = 400, rating 1500 [V, R20@2026-09-29b e R1@2026-09-29c].
- test_us_c4_1_acceptance.py: 7 test. Veloci: test_calibration_training_only_synthetic, test_calibration_objective_matches_count_real_data, test_csv_validation_leakage_and_uniqueness, test_versioned_csv_schema_and_probabilities, test_recomputed_predictions_match_csv, test_elo_fit_validations. Slow: test_elo_fits_matches_data_recalibration [V, R23@2026-09-29b e log CI 2026-09-29].
- test_scoring.py: 7 test veloci sintetici [V, R26@2026-09-29b].
- test_us_c4_2_acceptance.py: 4 test. Schema e riepilogo del CSV, coerenza delle cumulative, figura, ricalcolo dai dati reali saltato con _has_real_data [V, R26 e R33@2026-09-29b].
- test_recalibration.py: 6 test sintetici. test_platt_fit_predict_properties accetta 0 e 1 inclusi (righe 132-133), per la saturazione di Platt in float64 [V, R29 e R30@2026-09-29b].
- test_us_c4_3_acceptance.py: 5 test. Schema e conteggi, test_reliability_z_scores_and_bounds, ĝ raw uguale a T23, figura, ricalcolo dai dati reali saltato con _has_real_data [V, R29, R30 e R33@2026-09-29b].
Classi del pacchetto [V, R1@2026-09-29c]: Scenario, StakingMoments, OneWayAnovaResult, PhiStreams, RejectionResult, ColumnClassification, SplitConfig, TestSetLockedError, LeakageError, EloFitParams, EloCalibrationResult, SeriesEvaluationData, IsotonicModel, PlattModel, FitCalibrationMaps, più l'interna _EloTracker
Persistenza [V, R1@2026-09-29c]:
- CSV versionati in results/ (colonne, righe): us_c1_1_growth_vs_lambda (10, –), us_c1_2_estimation_error (12, 46), us_c2_anova_autocorrelation (10, 24), us_c3_1_data_coverage (12, 477), us_c3_2_devig_divergence (19, 29), us_c4_1_elo_walkforward (15, 9 500), us_c4_2_g_hat (11, 33 066), us_c4_3_calibration (16, 144);
- PNG omonimi in thesis/figures/;
- config/split.toml; dati grezzi in data/raw/E0/, non versionati.
Nessun database [D]

## Flussi principali
Esperimento C1.1 (scripts/us_c1_1_growth_vs_lambda.py) [V, R1@2026-09-29c]:
- parametri cablati alle righe 30-36: p = 0.60, b = 1.0, T = 1000, M = 10000, seed 20260905, 51 valori di λ in [0, 2.5];
- sequenza: f* con kelly_fraction; una matrice di esiti; per ogni λ, log_wealth_paths, metriche, del paths, e benchmark con log_growth_rate ed expected_final_wealth [V, R1@2026-09-28].
C1.1, output: CSV a 10 colonne (lambda, f, median_growth_rate, analytic_growth_rate, median_final_wealth, mean_final_wealth_mc, mean_final_wealth_analytic, drawdown_median, drawdown_p95, fraction_below_start) e PNG a tre pannelli [V, R1@2026-09-28 per file e conteggio; D per i nomi]
Accettazione C1.1 (tests/test_us_c1_1_acceptance.py): tutti i test slow, parametri ripetuti a mano, seed 20260905 [V, R1@2026-09-29c]. Asserzioni:
- picco della mediana a λ = 1.0;
- drawdown mediano non decrescente, con tolleranza −0.01;
- |g mediano| < 0.002 a λ = 1.946;
- crescita negativa a λ = 2.5.
Valori analitici con p = 0.6, b = 1 [D, ricalcolo del supervisore]:
- f* = 0.2; g(0.2) = 0.020136; g(0.4) = −0.002447; zero di g a f = 0.38939, cioè λ = 1.94695;
- le costanti di test_kelly_core.py:32 e :39 e il λ = 1.946 dell'accettazione C1.1 sono valori analitici, non empirici.
Esperimento C1.2 [V, R1@2026-09-29c]:
- scenari e SEED da scenarios.py; per ogni scenario spawn_generators(SEED) ed esiti con draw_scenario_outcomes;
- errore deterministico ±10% con relative_perturbation;
- per σ_p ∈ {0.015, 0.0283, 0.045}: p̂ da noisy_estimates, f̂ da kelly_staking, momenti da staking_moments;
- regole: lambda_star, ratio_moments, lambda_linear, quarter_kelly, half_kelly, full_kelly, plugin;
- CSV di 46 righe = 2 × (2 + 3 × 7) [conteggio ricalcolato dal supervisore]; PNG a due pannelli.
C1.2, colonne del CSV: scenario, sigma_p, rule, lambda, mean_c, mean_c2, var_c_empirical, var_c_linear, fraction_f_hat_zero, median_growth_rate, median_drawdown, fraction_below_start; stringa vuota dove non applicabile [V, R8@2026-09-28]
Accettazione C1.2 [V, R1@2026-09-29c]:
- test veloci: esiti indipendenti da p̂, matrice esiti non modificata;
- test slow: asimmetria ±10% nello scenario sottile; Var(c) a σ_p = 0.0283 entro 0.005 dal riferimento nello scenario base; λ* contro quarto-Kelly.
Var(c) attesa a σ_p = 0.0283: circa 0.080 nello scenario base, circa 1.28 in quello sottile [D, ricalcolo del supervisore]
Esperimento C2 nominale: rigetti su 1000 serie per φ = 0.0, 0.3, 0.5, 0.7 [V, R9@2026-09-28 e ricalcolo del supervisore]:
- contiguous_2: 37, 149, 253, 399;
- contiguous_38: 44, 843, 999, 1000;
- random_2: 58, 35, 48, 45.
Intervallo al 99%: [0.0322461452073078, 0.0677538547926922]. Valori critici: 3.866176954321902 (k = 2), 1.445838076487165 (k = 38).
Esperimento C2 calibrato (contiguous_2, B = 999, serie grezza): rigetti per L = 7, 20, 40 [V, R14@2026-09-28 e ricalcolo del supervisore]:
- φ = 0.0: 35, 29, 32;
- φ = 0.3: 61, 57, 49;
- φ = 0.5: 73, 52, 42;
- φ = 0.7: 108, 65, 56.
C2 calibrato, soglie: media fra 3.46 e 18.64, contro 3.866 nominale. Una chiamata di calibrate_threshold con n = 380, L = 20, B = 999 e vectorized costa circa 6.8 ms [V, R11 e R14@2026-09-28]
Uso come libreria: from shk.kelly import kelly_fraction, log_growth_rate; expected_final_wealth solo da shk.kelly.core [V, R1@2026-09-29c]
Dati E0 caricati [V, R10@2026-09-29; totale ricalcolato dal supervisore]:
- 31 stagioni, 11 944 partite: 462 nel 1993-94 e nel 1994-95, 380 nelle altre;
- 161 colonne originali più season.
Colonne dei dati E0 (presenza, non completezza) [V, R8@2026-09-29]:
- comuni a tutte le stagioni: Div, Date, HomeTeam, AwayTeam, FTHG, FTAG, FTR; Time solo dal 2019-20;
- B365 pre-partita dal 2002-03; IW e WH dal 2000-01; PS e PSC* dal 2012-13;
- B365C* e le altre terne di chiusura dal 2019-20; Bb* dal 2005-06 al 2018-19; Max* e Avg* dal 2019-20.
Codifiche: 2004-05 in cp1252, 2021-22 con BOM UTF-8 [V, R9@2026-09-29]
Esperimento C3.1: CSV di 477 righe [V, R14@2026-09-29 e R1@2026-09-29c]:
- prima terna 1X2 pre-partita completa nel 2000-01 (GB, IW, SB, WH);
- B365 pre-partita completa in tutte le 22 stagioni dal 2002-03 al 2023-24, assente fino al 2001-02, quindi anche nel 2000-01, che è di training.
Split congelato (config/split.toml) [V, R26@2026-09-29; conteggi ricalcolati dal supervisore]:
- training: 2000-01, 2010-11, 2020-21 (1 140 partite);
- validation: 19 stagioni dal 2002-03 al 2022-23 tranne le due di training (7 220);
- history: dal 1993-94 al 1999-00 più il 2001-02, 8 stagioni (3 204);
- test: 2023-24, bloccato (380, non lette).
Esperimento C3.2, B365 pre-partita su training e validazione [V, R43@2026-09-29]:
- 7 980 partite usate su 8 360; 380 escluse, tutte del 2000-01 senza B365; overround medio 5.437%;
- spread medio in punti massimo nella fascia [1, 1.5) (2.33); spread relativo medio massimo in [10, ∞) (0.222);
- spread massimo 6.29 punti, cioè 3.14 volte l'edge di 2 punti.
Walk-forward anti-leakage: 8 360 partite previste, zero violazioni. La whitelist reale ha 87 campi: 6 identificativi e 81 quote pre-partita [V, R46@2026-09-29]
Flusso C4, catena di esperimenti [V, R1@2026-09-29c]:
- read_split_config e load_by_role;
- derive_fit_schedule;
- generate_validation_predictions (predict_elo_fast con ELO_FITS);
- align_predictions_with_odds;
- prepare_series_evaluation (tre metodi di de-vigging);
- per C4.2: ĝ = LL(q) − LL(p), riepilogo e cumulativo;
- per C4.3: mappe isotonica e Platt sul training, ricalibrazione, reliability e Brier.
Modulo 1 Elo (T20): la tabella Davidson delle note 2.8 §3.3 si riproduce con s = 200 (scarto massimo 4.418e-4); con s = 400 lo scarto sarebbe 0.20. Il modello usa s = 400 [V, R13@2026-09-29b e R1@2026-09-29c]
Transizioni reali dal 1993-94 al 2022-23 [V, R20 e R21@2026-09-29b]:
- 86 entrate (28 nuove, 58 tornanti);
- le ultime tre calcolate coincidono con le retrocesse in ogni transizione tranne il 1997-98, per penalizzazioni non presenti nei dati.
Tempi del previsore sulle 8 360 partite: percorso veloce 0.35 s, via fornitore 10.58 s [V, R21@2026-09-29b]
Esperimento C4.1, calibrazione [V, R23@2026-09-29b]:
- tutti i fit con success = True, nessun parametro su un limite;
- partite di training 380, 760, 1 140; durata totale 116.93 s.
C4.1, log-loss Davidson / baseline a pareggio costante:
- fit 2000-01: training 1.008189 / 1.014931; validazione (3 040 partite) 0.973761 / 0.976755;
- fit 2010-11: training 1.008987 / 1.015189; validazione (3 420) 0.983832 / 0.990144;
- fit 2020-21: training 1.020937 / 1.024782; validazione (760) 0.983300 / 0.987629.
Esperimento C4.2 [V, R24 e R26@2026-09-29b; righe ricalcolate dal supervisore, 6 + 3 × (7 220 + 3 800) = 33 066]:
- PSC completa dal 2012-13 al 2022-23 e devig_power converge su tutti i 3 800 mercati;
- partite usate: b365_prematch 7 220 (19 stagioni), pinnacle_closing 3 800 (10 stagioni); nessuna esclusione;
- log-loss del modello: 0.979536 (B365), 0.981229 (Pinnacle).
ĝ (proporzionale / additivo / power), negativo in tutti i casi e a ogni fine stagione del cumulativo [V, R26@2026-09-29b]:
- b365_prematch: −0.021429 / −0.022401 / −0.022402;
- pinnacle_closing: −0.031474 / −0.031572 / −0.031672.
Esperimento C4.3 [V, R29@2026-09-29b]:
- Platt converge sempre; valori limitati dall'isotonica: 265 (B365) e 77 (Pinnacle); da Platt: 0;
- fasce raw peggio calibrate: A [0.4, 0.5) z = +6.06, A [0.5, 0.6) +5.30, H [0.7, 0.8) +4.34.
C4.3, log-loss / Brier:
- b365: raw 0.979536 / 0.583437, isotonic 1.013931 / 0.586291, platt 0.982340 / 0.584171, mercato circa 0.957–0.958 / 0.568;
- pinnacle: raw 0.981229 / 0.583208, isotonic 0.991359 / 0.584444, platt 0.980927 / 0.583522, mercato circa 0.9496 / 0.5613.
C4.3, ĝ (proporzionale / additivo / power):
- isotonic: b365 −0.055824 / −0.056797 / −0.056797; pinnacle −0.041604 / −0.041703 / −0.041803;
- platt: b365 −0.024233 / −0.025205 / −0.025206; pinnacle −0.031173 / −0.031271 / −0.031371.

## Convenzioni da rispettare
Naming: snake_case per moduli, funzioni e variabili; PascalCase per le classi; UPPER_CASE per le costanti; simboli matematici della letteratura; test con prefisso test_ [V, R1@2026-09-29c]
Lingua: identificatori, nomi dei test e messaggi di eccezione in inglese; commenti e docstring in italiano [V, R1@2026-09-29c]
Type hints completi; docstring in stile NumPy con sezioni Parametri / Restituisce / Solleva [V, R1@2026-09-29c]
Validazione in apertura di funzione: ValueError per i valori, TypeError per i tipi; rng controllato con isinstance(rng, np.random.Generator) [V, R1@2026-09-29c e R5@2026-09-28]
Il codice nuovo controlla anche il tipo degli interi (bool e float → TypeError, interi NumPy accettati) e rifiuta una str dove attende una collezione di str. Eccezione storica: draw_outcomes e noisy_estimates di C1 accettano True come 1 [V, R1@2026-09-29c]
Eccezioni specializzate per i vincoli strutturali: TestSetLockedError, LeakageError [V, R1@2026-09-29c]
Nessun try:, print( o logging in src/ e scripts/ [V per i file controllati nei report: S1 R4@2026-09-28; S2 R5, R8, R10 e R12@2026-09-28; S3 R14, R26, R32, R43 e R46@2026-09-29; S4 in src R11, R19, R23 e R29@2026-09-29b]. Per gli script di S4 e per elo_predictor.py dopo il secondo correttivo di T21 non verificato [D]. R1@2026-09-29c lo afferma senza una ricerca [D]
L'RNG entra come argomento e non si crea dentro le funzioni di libreria; flussi indipendenti con np.random.SeedSequence.spawn [V, R1@2026-09-29c]
Vettorizzazione NumPy senza cicli su M e T nel motore; del paths nei loop Monte Carlo [V, R1@2026-09-29c e R1@2026-09-28]
Script di esperimento [V, R1@2026-09-29c e R8@2026-09-28]:
- matplotlib.use("Agg") prima di pyplot; run_experiment() senza parametri, chiamata dal blocco __main__; nessun argomento da riga di comando;
- CSV con csv.DictWriter, open(mode="w", newline="", encoding="utf-8"), float nativi, stringa vuota dove non applicabile;
- PNG con plt.tight_layout() e savefig(dpi=150); etichette in italiano.
Parametri condivisi fra script e test in un modulo di libreria importato da entrambi: scenarios.py (C1.2), false_rejection.py (C2), coverage.py, divergence.py e split.toml (C3), elo_fit.py (C4.1), scoring.py (C4.2), recalibration.py (C4.3). C1.1 è l'eccezione storica [V, R1@2026-09-29c]
Nomi: scripts/us_<story>_<nome>.py, con lo stesso nome base per results/<nome>.csv e thesis/figures/<nome>.png, entrambi versionati [V, R1@2026-09-29c]
Test [V, R1@2026-09-29c; decisioni delle story S3 e S4]:
- i Monte Carlo su larga scala e i test sui dati reali oltre 60 s si marcano @pytest.mark.slow;
- i test anti-leakage non si marcano slow;
- i test sui dati reali si saltano con motivo esplicito tramite _has_real_data o una condizione equivalente su DEFAULT_DATA_DIR;
- un test che controlla solo il CSV versionato in results/ non basta: in CI fallirebbe [V, R31 e R33@2026-09-29b].
Dati reali nel codice nuovo solo tramite load_by_role; load_all_seasons è ammessa solo in loading.py, split.py, coverage.py e scripts/us_c3_1_data_coverage.py [V, R26@2026-09-29 e R1@2026-09-29c]
Probabilità 1X2 del Modulo 1: matrici (N, 3) in ordine H, D, A, con righe a somma 1; previsioni sempre walk-forward, prima dell'aggiornamento della stessa data [V, R1@2026-09-29c e R22@2026-09-29b]
Commit fatti solo dal programmatore, a mano [V, .agent/PROTOCOLLO.md fornito dal programmatore 2026-09-28]
Ogni story ha un branch di lavoro (C2, C3, C4) che entra in main come un solo commit; il branch locale viene poi cancellato [V, R4 e R5@2026-09-29b e R1@2026-09-29c]
Cline scrive in .agent/ solo MAPPA.md in mappatura e report/T<n>.md in esecuzione [V, PROTOCOLLO.md 2026-09-28]
.agent/PROTOCOLLO.md non ha convenzioni aggiuntive per il progetto [V, PROTOCOLLO.md 2026-09-28]
Documenti di processo in .agent/, versionati: PROTOCOLLO.md, BACKLOG.md, MAPPA.md, SCHEDA.md, report/T1.md … T25.md [V, R1@2026-09-29c]

## Zone fragili da non toccare senza avviso
test_acceptance_calibrated_phi_zero_within_mc_interval (tests/test_us_c2_acceptance.py:350-363) fallisce per un risultato noto [V, R1@2026-09-29c e R14@2026-09-28; decisione del programmatore 2026-09-28]:
- 29 rigetti su 1000 a φ = 0 con L = 20, sotto l'estremo 32.25 dell'intervallo al 99%;
- è il T12 da rivedere, non una regressione: non si sistema allentando tolleranze o parametri.
noisy_estimates può restituire p̂ = 1 per saturazione; con lam ≥ 1 kelly_staking dà una frazione ≥ 1, che simulate_growth rifiuta con ValueError [V, R1@2026-09-29c]. Con p ≤ 0.6 e σ_p ≤ 0.045 l'evento dista almeno 8.9 deviazioni standard [D, ricalcolo del supervisore]
expected_final_wealth (core.py:97-144) è usata dallo script C1.1 e non ha test [V l'uso, R1@2026-09-29c; D l'assenza di test, nessuna ricerca]
Parametri di C1.1 duplicati fra scripts/us_c1_1_growth_vs_lambda.py:30-36 e tests/test_us_c1_1_acceptance.py [V, R1@2026-09-29c]
test_metrics.py:test_metrics_error_conditions non verifica il ValueError di median_final_wealth e mean_final_wealth [V, R1@2026-09-29c]
parse_season_start_year è duplicata: pubblica in elo_fit.py:96, privata in elo_predictor.py:91. Una modifica a una sola delle due le fa divergere [V, R1@2026-09-29c]
I test slow non girano in CI; dopo modifiche a src/shk/kelly/, src/shk/stats/ o al calcolo dell'Elo vanno lanciati a mano [V l'esclusione, R1@2026-09-29c; D la regola]
I test sui dati reali in CI si saltano, perché data/raw/* non è versionato: vanno eseguiti in locale [V, R1@2026-09-29c e log CI 2026-09-29]. Il test sui dati reali di test_leakage.py dura circa 8 s ed è nella suite veloce [V, R46@2026-09-29]
Rieseguire uno script sovrascrive CSV e PNG versionati: ogni task che rigenera un esperimento dice se vanno committati [V, R1@2026-09-28]. C4.1 dura circa 49 s [V, R23@2026-09-29b]
CSV versionati legati ai test:
- confrontati con il codice: C2 (test_us_c2_acceptance.py); C3.2, C4.1, C4.2 e C4.3, con ricalcolo dai dati reali solo in locale, entro 1e-12 [V, R1@2026-09-29c];
- C3.1 non ha un test di confronto [D].
Ogni modifica che cambia i risultati di false_rejection.py, divergence.py, devig.py o del modello Elo richiede di rieseguire lo script prima dei test.
Dipendenze senza vincoli di versione; la CI installa con pip ignorando uv.lock [V, R1@2026-09-29c]. NumPy non garantisce la stabilità del flusso di Generator fra versioni e i test con tolleranze empiriche possono rompersi [D]. Il valore critico C2 per k = 2 differisce all'ultima cifra fra venv e CI [V, R9 e R15@2026-09-28]
pandas 3: Date esce in datetime64[us] [V, R10@2026-09-29]; le colonne di testo hanno di default il dtype stringa [D]
classify_column solleva ValueError su ogni colonna non catalogata: nuovi file E0 con colonne nuove fermano audit e fornitore walk-forward [V, R1@2026-09-29c]. La whitelist anti-leakage dipende da kind e timing di classify_column: estendere coverage.py cambia i campi esposti dal fornitore [V, R45 e R46@2026-09-29]
devig_power solleva RuntimeError se anche un solo mercato non converge: ferma l'intero calcolo [V, R1@2026-09-29c]
devig_additive restituisce righe di NaN, da escludere per tutti i metodi. test_devig.py:test_extreme_markets salta quei mercati e non rileverebbe un NaN spurio [V, R32 e R35@2026-09-29 e R1@2026-09-29c]
config/split.toml è congelato e non si modifica. Lo sblocco del test lo fa solo il programmatore, a mano e con commit, dopo il congelamento dei parametri (US-C8.2) [V, decisione della story S3]
Test di guardia di tests/test_split.py: fallisce se load_all_seasons compare, come import o riferimento, in file di src/ o scripts/ diversi dai quattro ammessi. I test in tests/ la usano liberamente [V, R26@2026-09-29; R1@2026-09-29c dice "intero repository", in contrasto con l'uso in test_data_loading.py e test_split.py riportato dalla stessa mappa]
elo_predictor.py itera solo sulle colonne di _CALC_COLS: un calcolo che usa un'altra colonna deve aggiungerla lì [D]. Dopo ogni modifica al file, confrontare lo SHA256 delle previsioni con 0b3048a7…cbce1 (K = 20, h = 60, ν = 1) [V, R21@2026-09-29b]
ELO_FITS è congelato e non si modifica [V, R1@2026-09-29c]. Una modifica a elo.py, elo_predictor.py, elo_fit.py, scoring.py o recalibration.py che cambia previsioni o metriche rende incoerenti ELO_FITS e i CSV di C4.1, C4.2 e C4.3: vanno ricalibrati e rigenerati. Lo segnalano solo in locale i test di ricalcolo e il test slow di ricalibrazione [D]
La prova del congelamento dello split (US-C3.3) dipende dalla data di commit di config/split.toml. Il commit delle 11:47:18 (2cea094) è raggiungibile solo dalla reflog locale e una garbage collection può eliminarlo alla scadenza della voce (per default circa 30 giorni) [V, R2–R6@2026-09-29b; D la scadenza]

## Punti ancora incerti
Versione del Modulo 1 da usare dopo C4: raw, Platt o isotonica.
- Blocca: la serie di residui/log-loss su cui C5.1 fa girare i detector, e il Modulo 1 di C6 e C8.
- Alternative: (a) raw, migliore su B365 per log-loss, Brier e ĝ; (b) Platt, marginalmente migliore su Pinnacle (0.980927 contro 0.981229); (c) isotonica, peggiore ovunque.
- Si procede: i task che non consumano probabilità del Modulo 1 non dipendono dalla scelta.
Dipendenze e river.
- Blocca: il task di C5.1 che aggiunge river, cioè se basta pyproject.toml o va rigenerato anche uv.lock, e se mettere vincoli di versione.
- Si procede: pyproject.toml è la fonte di verità, l'unica usata dalla CI. Lo stato di uv.lock e la presenza di river nel venv si verificano nel primo passo del task.
Imposizione di H₀ prima del block bootstrap (per l'ANOVA: serie centrata per gruppo).
- Blocca: la chiusura di T12; la correzione della docstring di calibration.py; la calibrazione Monte Carlo della soglia dello Z-test in C5.2 (che riusa il codice di US-C2.3); la scelta di L per C5.2, C6.4 e C8.
- Si procede lasciando il test slow com'è e senza toccare calibration.py né false_rejection.py.
- Proposta: un task che aggiunge righe method = block_bootstrap_centered accanto alle attuali, con criteri scritti e datati prima dell'esecuzione.
Prova del congelamento dello split.
- Blocca: la data da dichiarare in US-C3.3 e in tesi, e la conservazione di 2cea094.
- Alternative: (a) dichiarare 90a77a1, con contenuto identico a 2cea094; (b) un tag su 2cea094 pubblicato su origin dal programmatore prima che la reflog scada; (c) affidarsi al ref del PR #17 su GitHub, non verificato.
- Si procede: nessun task di codice dipende dalla scelta.
Stagione di training 2000-01 senza B365.
- Blocca: gli esperimenti di C8 alimentati da quote B365 su quello scenario (in C3.2 è escluso per intero; in C4 non ha bloccato).
- Alternative: (a) dichiararlo in tesi e procedere con 2010-11 e 2020-21; (b) usare per il solo 2000-01 un'altra terna completa (GB, IW, SB o WH); (c) rivedere lo scenario in una chat di backlog.
- Si procede: C5 non usa le quote di training.
Versionamento dei CSV E0.
- Blocca: se la CI potrà mai verificare le pipeline su dati reali; decisione del programmatore dopo il controllo della licenza (note 2.9).
- Si procede: i test sui dati reali girano in locale.

## Ultimo aggiornamento
R1@2026-09-29c — task di scrittura chiusi dopo la mappa del 2026-09-29c: nessuno

---
Stato repo →
"Branch locali: solo main. Branch remoti: origin/HEAD → origin/main, origin/main [V, R1@2026-09-29c]. Nessun branch di lavoro aperto: il branch della prossima story lo crea il programmatore da main [D, convenzione dei branch]"
→ "Branch locali: main e C5, il branch di lavoro di S5, creato dal programmatore da main [V, R2@2026-09-29c]. Branch remoti: origin/HEAD → origin/main, origin/main [D, era V R1@2026-09-29c]"

Stato repo → (nuova riga, dopo "Alla mappa: …")
"Dopo T26: su C5 risultano modificati .agent/BACKLOG.md, .agent/MAPPA.md e .agent/SCHEDA.md, e non tracciati .agent/report/T26.md, src/shk/model/residuals.py e tests/test_residuals.py; stato dei commit successivi non noto [D, era V R4@2026-09-29c]"

Stack e comandi →
"Suite veloce locale, con i dati locali presenti: dopo T25 248 verdi, 15 deselezionati, 50.28 s [V, R33@2026-09-29b]. I 248 sono …"
→ "Suite veloce locale, con i dati locali presenti: dopo T26 257 verdi, 15 deselezionati, 45.36 s [V, R3@2026-09-29c]; sono i 248 di dopo T25 [V, R33@2026-09-29b] più i 9 di test_residuals.py. I 248 sono …" (il resto della riga e i tre punti che seguono restano invariati)

Moduli e responsabilità →
"src/shk/ contiene 21 moduli applicativi (6 in kelly, 4 in stats, 4 in data, 2 in market, 5 in model) più 6 __init__.py [V, R1@2026-09-29c; conteggio ricontato dal supervisore]. Nessun modulo di drift detection [D, …]"
→ "src/shk/ contiene 22 moduli applicativi (6 in kelly, 4 in stats, 4 in data, 2 in market, 6 in model) più 6 __init__.py [V, R1@2026-09-29c più residuals.py, R4@2026-09-29c]. Nessun modulo di drift detection [D, dall'elenco dei moduli di R1@2026-09-29c]"

Moduli e responsabilità →
"src/shk/data/loading.py — DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "raw" / "E0". load_all_seasons(…) → un DataFrame con [V, R10 e R26@2026-09-29]:"
→ stessa riga con "[V, R10 e R26@2026-09-29; DEFAULT_DATA_DIR alle righe 14-16, R3@2026-09-29c]:"

Moduli e responsabilità →
"src/shk/model/elo_fit.py — funzioni [V, R1@2026-09-29c; R23 e R24@2026-09-29b per i dettagli]:"
→ invariata; al primo punto ("- derive_fit_schedule(training, validation=None), …") aggiungi in coda: "; con lo split congelato il fit 2000-01 prevede le stagioni di validazione dal 2002-03 al 2009-10 (3 040 partite), il 2010-11 dal 2011-12 al 2019-20 (3 420), il 2020-21 il 2021-22 e il 2022-23 (760) [V, R2@2026-09-29c]"

Moduli e responsabilità →
"src/shk/model/scoring.py — metriche senza eps: una probabilità ≤ 0 per l'esito realizzato dà ValueError; matrici (N, 3) con righe a somma 1 entro 1e-9 [D, piano approvato; test verdi R26@2026-09-29b]"
→ "src/shk/model/scoring.py — compute_log_loss(probs, outcomes) → ndarray (N,) = −ln della probabilità realizzata; probs (N, 3) in ordine H, D, A con righe a somma 1 entro 1e-9, outcomes in H, D, A; nessun eps; ValueError se una probabilità realizzata è ≤ 0 (righe 79-118) [V, R2@2026-09-29c]"

Moduli e responsabilità → (nuova riga, dopo le righe di recalibration.py)
"src/shk/model/residuals.py — RESIDUALS_COLUMNS; compute_model_residuals(df, schedule, fits=None) → DataFrame con fit_through, role, season, Date, HomeTeam, AwayTeam, p_home, p_draw, p_away, FTR, log_loss; fits=None → ELO_FITS. Righe di training dalle preds di compute_training_log_loss, una per ogni fit che include la partita; righe di validazione da generate_validation_predictions; FTR con align_predictions_with_odds; log_loss con compute_log_loss. Ordine: fit, poi training prima di validation, poi Date stabile. Non modifica i moduli di C4 [V, R3 e R4@2026-09-29c]"

Moduli e responsabilità → tests/
"tests/ — 24 moduli [V, R1@2026-09-29c]:" → "tests/ — 25 moduli; nessun conftest.py [V, R3 e R4@2026-09-29c]:"
e nel punto "- unitari: …" aggiungi test_residuals in coda all'elenco.

Moduli e responsabilità → Contenuto dei moduli di test (2/2), nuova voce in coda:
"- test_residuals.py: 9 test veloci. 5 sintetici (schema e dtype, ordinamento, log_loss contro −ln p a mano, partite di training ripetute per fit, validazioni); 4 sui dati reali tramite la fixture real_data_computation (scope="module"), che senza CSV chiama pytest.skip: conteggi, medie contro i riferimenti di C4 entro 5e-7 e contro compute_training_log_loss entro 1e-12, log_loss finita e positiva, assenza del 2023-24. _has_real_data è definita nel modulo [V, R3 e R4@2026-09-29c]."

Flussi principali → (nuova riga, dopo "Esperimento C4.3 …" e relative righe)
"Serie di log-loss per partita del Modulo 1 raw (T26), con compute_model_residuals sui dati reali: 9 500 righe; training 380 / 760 / 1 140, validazione 3 040 / 3 420 / 760; log-loss media di training 1.00818933 / 1.00898737 / 1.02093662, di validazione 0.97376082 / 0.98383215 / 0.98330012, aggregata 0.97953559; 1.70 s [V, R3@2026-09-29c; aggregata ricontrollata dal supervisore dalle medie pesate]"

Convenzioni da rispettare → Test, aggiungi un punto:
"- _has_real_data non è condivisa: ogni modulo di test la definisce localmente con DEFAULT_DATA_DIR.exists() and len(list(DEFAULT_DATA_DIR.glob("*.csv"))) > 0; non esiste tests/conftest.py [V, R3@2026-09-29c]"

Ultimo aggiornamento →
"R1@2026-09-29c — task di scrittura chiusi dopo la mappa del 2026-09-29c: nessuno"
→ "R4@2026-09-29c — task di scrittura chiusi dopo la mappa del 2026-09-29c: T26"



---

Stato repo → (sostituisce la riga "Dopo T26: …")
"Su C5: 1ba1bb2 "Add model residual log-loss series" sopra 27cf7a4, con working tree pulito prima di T27 [V, R5@2026-09-29c]. Dopo T27 risultano modificato pyproject.toml e non tracciati src/shk/stats/drift.py, tests/test_drift.py e .agent/report/T27.md; stato dei commit successivi non noto [D, era V R6@2026-09-29c]"

Stack e comandi →
"Dipendenze runtime: numpy, scipy, matplotlib, pandas. Dipendenze dev: pytest. Nessun vincolo di versione. river non è fra le dipendenze [V, R1@2026-09-29c]. Se river sia installato nel venv non è verificato [D]"
→ "Dipendenze runtime: numpy, scipy, matplotlib, pandas, river. Dipendenze dev: pytest. Nessun vincolo di versione [V, R1@2026-09-29c e R6@2026-09-29c per river]. Nel venv: river 0.26.1 e narwhals 2.26.0, installati con pip il 2026-09-30 senza modifiche alle altre dipendenze [V, R6@2026-09-29c]. uv.lock non aggiornato per river [D]"

Stack e comandi →
"Suite veloce locale, con i dati locali presenti: dopo T26 257 verdi, 15 deselezionati, 45.36 s [V, R3@2026-09-29c]; sono i 248 …"
→ "Suite veloce locale, con i dati locali presenti: dopo T27 264 verdi, 15 deselezionati, 49.73 s [V, R6@2026-09-29c]; sono i 248 di dopo T25 [V, R33@2026-09-29b] più i 9 di test_residuals.py e i 7 di test_drift.py. I 248 sono …" (resto invariato)

Moduli e responsabilità →
"src/shk/ contiene 22 moduli applicativi (6 in kelly, 4 in stats, 4 in data, 2 in market, 6 in model) più 6 __init__.py […]. Nessun modulo di drift detection […]"
→ "src/shk/ contiene 23 moduli applicativi (6 in kelly, 5 in stats, 4 in data, 2 in market, 6 in model) più 6 __init__.py [V, R1@2026-09-29c più residuals.py, R4, e drift.py, R6@2026-09-29c]"

Moduli e responsabilità → (nuova riga, dopo le righe di calibration.py)
"src/shk/stats/drift.py — importa ADWIN e PageHinkley da river.drift [V, R6@2026-09-29c]:
- run_drift_detector(series, detector, params) → ndarray int64 degli indici base 0 con drift_detected; detector "adwin" o "page_hinkley"; istanza nuova a ogni chiamata; params=None → default di river;
- calibrate_drift_detectors(serie_a, serie_b) → (parametri ADWIN, parametri Page-Hinkley, tabella della griglia); regola: min |10·(a + b) − 38|, poi meno allarmi totali, poi ordine della griglia;
- costanti: TARGET_ALARMS_PER_SEASON = 1.9, griglie ADWIN (9 delta) e Page-Hinkley (3 delta × 6 threshold), ADWIN_DELTA = 0.002, PAGE_HINKLEY_DELTA = 0.05, PAGE_HINKLEY_THRESHOLD = 5.0.
Che gli altri parametri (clock, max_buckets, min_window_length, grace_period; min_instances, alpha, mode) siano congelati come costanti e passati in modo esplicito non è verificato [D]"

Moduli e responsabilità → tests/
"tests/ — 25 moduli; nessun conftest.py […]" → "tests/ — 26 moduli; nessun conftest.py [V, R3, R4 e R6@2026-09-29c]"; nel punto "- unitari: …" aggiungi test_drift.

Moduli e responsabilità → Contenuto dei moduli di test (2/2), nuova voce in coda:
"- test_drift.py: 7 test veloci, 4.69 s. 5 sintetici (salto di media con i default di river e seed 20260930, intervallo degli indici, ripetibilità, validazioni, regola di scelta); 2 sui dati reali, saltati senza dati (i parametri ricalcolati coincidono con quelli congelati; conteggi riprodotti) [V, R6@2026-09-29c]"

Flussi principali → (nuova riga, dopo la serie di log-loss di T26)
"Taratura dei detector (T27), river 0.26.1, sulle serie di training 2000-01 (fit 2000-01) e 2010-11 (fit 2010-11), 380 partite ciascuna [V, R6@2026-09-29c]:
- ADWIN: 0 allarmi su entrambe le stagioni per tutti i 9 delta; scelto delta 0.002 per l'ordine della griglia;
- Page-Hinkley: scelto delta 0.05, threshold 5.0, con 1 e 1 allarmi (media 1.0); le combinazioni con threshold 1 o 2 danno da 7 a 12 allarmi per stagione, quelle con threshold ≥ 20 nessuno;
- salto sintetico con i default: ADWIN all'indice 223, Page-Hinkley al 210, nessuno prima del salto."

Zone fragili → (nuova riga)
"river è senza vincolo di versione e la CI installa l'ultima: i conteggi di allarmi di T27 e dei task che li usano dipendono dall'implementazione di river 0.26.1 [V la versione, R6@2026-09-29c; D l'effetto di altre versioni]"

Punti ancora incerti → sostituisci la voce "Dipendenze e river." e i suoi punti con:
"Dipendenze e river.
- river è in pyproject.toml senza vincolo e installato nel venv (0.26.1) [V, R6@2026-09-29c].
- Resta aperto: aggiornare uv.lock, e se mettere un vincolo di versione a river; verificare che la CI installi river e resti verde."

Ultimo aggiornamento →
"R6@2026-09-29c — task di scrittura chiusi dopo la mappa del 2026-09-29c: T26, T27"

---
Stato repo → (sostituisce la riga "Su C5: 1ba1bb2 …")
"Su C5: 350ec52 "Add drift detection with ADWIN and Page-Hinkley" sopra 1ba1bb2 e 27cf7a4, con working tree pulito prima di T28 [V, R7@2026-09-29c]. Dopo T28 risultano modificato src/shk/stats/drift.py e non tracciati src/shk/model/monitoring.py, scripts/us_c5_1_drift_detectors.py, tests/test_us_c5_1_acceptance.py, results/us_c5_1_drift_detectors.csv, thesis/figures/us_c5_1_drift_detectors.png e .agent/report/T28.md; stato dei commit successivi non noto [D, era V R9@2026-09-29c]"

Stack e comandi →
"Suite veloce locale, con i dati locali presenti: dopo T27 264 verdi, 15 deselezionati, 49.73 s [V, R6@2026-09-29c]; sono i 248 di dopo T25 […] più i 9 di test_residuals.py e i 7 di test_drift.py. …"
→ "Suite veloce locale, con i dati locali presenti: dopo T28 272 verdi, 15 deselezionati, 48.31 s [V, R8@2026-09-29c]; sono i 248 di dopo T25 [V, R33@2026-09-29b] più i 9 di test_residuals.py, i 7 di test_drift.py e gli 8 di test_us_c5_1_acceptance.py. …" (resto invariato)

Stack e comandi → Esperimenti, nuovo punto in coda:
"- C5.1 us_c5_1_drift_detectors.py: SHA256 3D132F6FFC8A20365208A2041DC4270AEEBA289FBF5407630E6CAA92F8B20A96, stabile su due esecuzioni [V, R8@2026-09-29c]; durata non misurata [D]."

Moduli e responsabilità →
"src/shk/ contiene 23 moduli applicativi (6 in kelly, 5 in stats, 4 in data, 2 in market, 6 in model) più 6 __init__.py […]"
→ "src/shk/ contiene 24 moduli applicativi (6 in kelly, 5 in stats, 4 in data, 2 in market, 7 in model) più 6 __init__.py [V, R1@2026-09-29c più residuals.py R4, drift.py R6 e monitoring.py R9@2026-09-29c]"

Moduli e responsabilità → nella riga di drift.py, sostituisci l'ultima frase ("Che gli altri parametri … non è verificato [D]") con:
"Anche i parametri non tarati sono costanti: ADWIN_DEFAULT_DELTA, ADWIN_DEFAULT_CLOCK = 32, ADWIN_DEFAULT_MAX_BUCKETS = 5, ADWIN_DEFAULT_MIN_WINDOW_LENGTH = 5, ADWIN_DEFAULT_GRACE_PERIOD = 10; PAGE_HINKLEY_DEFAULT_MIN_INSTANCES = 30, PAGE_HINKLEY_DEFAULT_DELTA, PAGE_HINKLEY_DEFAULT_THRESHOLD, PAGE_HINKLEY_DEFAULT_ALPHA = 1 − 0.0001, PAGE_HINKLEY_DEFAULT_MODE = "both". Con params fornito, le chiavi mancanti si prendono da queste costanti e tutto si passa in modo esplicito; con params=None si istanzia ADWIN() o PageHinkley() coi default di river [V, R7@2026-09-29c]. detector_params(detector) restituisce a ogni chiamata un dict nuovo con i parametri congelati; ValueError per un nome sconosciuto [V, R8@2026-09-29c]"

Moduli e responsabilità → (nuova riga, dopo residuals.py)
"src/shk/model/monitoring.py — DRIFT_DETECTOR_CSV_COLUMNS (12 colonne: row_type, season, role, fit_through, detector, alarm_number, match_index, matchday, date, home_team, away_team, n_alarms); ScenarioSeries (NamedTuple: season, role, fit_through, log_loss, date, home_team, away_team); extract_scenario_series (22 serie di 380 partite in ordine cronologico di stagione: le tre di training dal fit omonimo, le 19 di validazione dal loro fit; ValueError se una serie non ha 380 partite); build_drift_records; generate_drift_detector_records, con i parametri da detector_params [V, R8@2026-09-29c; D per i dettagli interni]"

Moduli e responsabilità →
"scripts/ — otto script, ognuno con run_experiment() senza parametri [V, R1@2026-09-29c]:" → "scripts/ — nove script, ognuno con run_experiment() senza parametri [V, R1@2026-09-29c e R8@2026-09-29c]:"; aggiungi in coda all'elenco "us_c5_1_drift_detectors.py".

Moduli e responsabilità → tests/
"tests/ — 26 moduli; …" → "tests/ — 27 moduli; nessun conftest.py [V, R3, R4, R6 e R8@2026-09-29c]:"; nel punto "- accettazione: …" aggiungi test_us_c5_1_acceptance.

Moduli e responsabilità → Contenuto dei moduli di test (2/2), nuova voce in coda:
"- test_us_c5_1_acceptance.py: 8 test veloci. 4 sintetici (schema, matchday, stringhe vuote, parametri presi da detector_params con monkeypatch); 3 sul CSV versionato che girano anche senza dati (schema, 44 righe summary, coerenza alarm/summary e matchday, nessuna riga 2023-24); 1 di ricalcolo dai dati reali con confronto esatto, saltato senza dati, 3.66 s [V, R8 e R9@2026-09-29c]"

Moduli e responsabilità → Persistenza, primo punto: aggiungi "us_c5_1_drift_detectors (12, 66)" all'elenco dei CSV versionati.

Flussi principali → (nuova riga, dopo la taratura dei detector)
"Esperimento C5.1 (T28), 22 stagioni di 380 partite (3 di training, 19 di validazione) [V, R9@2026-09-29c]:
- ADWIN: 0 allarmi su tutte le 22 stagioni, compreso il 2020-21;
- Page-Hinkley: 22 allarmi, 2 in training (2000-01 alla matchday 8, 2010-11 alla 25, nessuno nel 2020-21) e 20 in validazione su 12 stagioni; da 0 a 3 allarmi per stagione; nessun allarme nel 2002-03, 2007-08, 2012-13, 2013-14, 2017-18, 2019-20, 2022-23."

Convenzioni da rispettare → (nuova riga, dopo "Nomi: scripts/us_<story>_<nome>.py …")
"Colonne dei CSV in snake_case e in inglese (date, home_team, away_team, come in C4.1); il blocco di 10 partite si chiama matchday [V, R9@2026-09-29c; decisione del programmatore 2026-09-30]"

Zone fragili → nella riga "CSV versionati legati ai test:", primo punto, aggiungi C5.1 all'elenco dei CSV confrontati con il codice (ricalcolo esatto dai dati reali solo in locale). Aggiungi poi un punto:
"- una modifica a residuals.py, drift.py o monitoring.py che cambia serie, parametri o record richiede di rieseguire scripts/us_c5_1_drift_detectors.py [D]."

Ultimo aggiornamento →
"R9@2026-09-29c — task di scrittura chiusi dopo la mappa del 2026-09-29c: T26, T27, T28"


---

Stato repo → (sostituisce la riga "Su C5: 350ec52 …")
"Su C5: e0d2396 "Add C5.1 drift detector monitoring" sopra 350ec52, 1ba1bb2 e 27cf7a4, con working tree pulito prima di T29 [V, R10@2026-09-29c]. Dopo T29 risultano modificati src/shk/stats/drift.py, src/shk/model/monitoring.py e tests/test_drift.py, e non tracciati scripts/us_c5_2_daily_z_test.py, results/us_c5_2_daily_z_test.csv, thesis/figures/us_c5_2_daily_z_test.png, tests/test_us_c5_2_acceptance.py e .agent/report/T29.md; stato dei commit successivi non noto [D, era V R11@2026-09-29c]"

Stack e comandi →
"Suite veloce locale, con i dati locali presenti: dopo T28 272 verdi, 15 deselezionati, 48.31 s [V, R8@2026-09-29c]; sono i 248 … e gli 8 di test_us_c5_1_acceptance.py. …"
→ "Suite veloce locale, con i dati locali presenti: dopo T29 284 verdi, 15 deselezionati, 52.41 s [V, R11@2026-09-29c]; sono i 248 di dopo T25 [V, R33@2026-09-29b] più i 9 di test_residuals.py, i 10 di test_drift.py, gli 8 di test_us_c5_1_acceptance.py e i 9 di test_us_c5_2_acceptance.py. …" (resto invariato)

Stack e comandi → Esperimenti, nuovo punto in coda:
"- C5.2 us_c5_2_daily_z_test.py: SHA256 015645CF5029EE57A32C036657B3C69259D629722B600E5A71078BD26760A6F5, stabile su due esecuzioni [V, R11@2026-09-29c]; durata non misurata [D]."

Moduli e responsabilità → riga di drift.py, aggiungi un punto:
"- MATCHDAY_SIZE = 10; compute_matchday_z_scores(series, mu, sigma, matchday_size=MATCHDAY_SIZE) → Z per blocco contiguo, (media − mu)/(sigma/√matchday_size); ValueError per lunghezza non multipla positiva di matchday_size, sigma ≤ 0 o valori non finiti [V, R11@2026-09-29c; D per i dettagli delle validazioni]"

Moduli e responsabilità → riga di monitoring.py, aggiungi in coda:
"; per C5.2: DAILY_Z_TEST_CSV_COLUMNS (14 colonne: row_type, season, fit_through, method, block_length, threshold, matchday, z, alarm, n_alarms, expected_alarms, mean_alarms, n_resamples, exceedance_rate), TrainingBaselineStats (fit_through, n_matches, mu, sigma), compute_training_baseline_stats(df_residuals, schedule=None) (μ_f e σ_f con ddof = 1 su tutte le righe di training del fit; ValueError sotto 2 righe), build_daily_z_test_records(validation_series, baseline_stats, alpha=ALPHA, matchday_size=MATCHDAY_SIZE), generate_daily_z_test_records [V, R11@2026-09-29c; D per i dettagli interni]"

Moduli e responsabilità →
"scripts/ — nove script …" → "scripts/ — dieci script, ognuno con run_experiment() senza parametri [V, R1@2026-09-29c, R8 e R11@2026-09-29c]:"; aggiungi in coda all'elenco "us_c5_2_daily_z_test.py".

Moduli e responsabilità → tests/
"tests/ — 27 moduli; …" → "tests/ — 28 moduli; nessun conftest.py [V, R3, R4, R6, R8 e R11@2026-09-29c]:"; nel punto "- accettazione: …" aggiungi test_us_c5_2_acceptance.

Moduli e responsabilità → Contenuto dei moduli di test (2/2):
nella voce di test_drift.py sostituisci "7 test veloci, 4.69 s. 5 sintetici" con "10 test veloci, 4.43 s. 8 sintetici (compresi Z contro il calcolo a mano entro 1e-12, Z nullo per blocchi con media μ e validazioni di compute_matchday_z_scores)" [V, R11@2026-09-29c]; poi aggiungi la voce:
"- test_us_c5_2_acceptance.py: 9 test veloci, 4.70 s. 3 sintetici (baseline, struttura dei record, coerenza fra matchday, summary e overall); 5 sul CSV versionato e sulla figura che girano anche senza dati (schema, conteggi per row_type, nessuna riga 2023-24, conteggi dei detector uguali al CSV di C5.1, esistenza del PNG); 1 di ricalcolo dai dati reali, saltato senza dati [V, R11@2026-09-29c]"

Moduli e responsabilità → Persistenza, primo punto: aggiungi "us_c5_2_daily_z_test (14, 782)".

Flussi principali → (nuova riga, dopo l'esperimento C5.1)
"Esperimento C5.2 (T29), Z-test per matchday sulle 19 stagioni di validazione [V, R11@2026-09-29c]:
- baseline (n, μ_f, σ_f): 2000-01 380, 1.00818933, 0.41019487; 2010-11 760, 1.00898737, 0.42054310; 2020-21 1 140, 1.02093662, 0.38389378;
- soglia nominale 1.959963984540054;
- allarmi z_nominal: 53 in totale (media 2.789 per stagione; 20 con Z > 0, 33 con Z < 0), da 0 (2012-13) a 5 (2008-09, 2022-23) per stagione;
- sulle stesse stagioni: ADWIN 0 allarmi, Page-Hinkley 20 (media 1.053)."

Zone fragili → riga "CSV versionati legati ai test:", primo punto: aggiungi C5.2 all'elenco dei CSV confrontati con il codice. Aggiungi poi un punto:
"- test_us_c5_2_acceptance.py confronta i conteggi dei detector nel CSV di C5.2 con il CSV di C5.1: rigenerarne uno solo li fa divergere [V, R11@2026-09-29c]."

Ultimo aggiornamento →
"R11@2026-09-29c — task di scrittura chiusi dopo la mappa del 2026-09-29c: T26, T27, T28, T29"