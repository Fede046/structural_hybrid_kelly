# Scheda del progetto
Origine: mappa completa del 2026-09-29 a 90a77a1 (serie 2026-09-29b), report fino a R6@2026-09-29b. Riferimenti: la numerazione R_n riparte da R1 a ogni mappa. La serie di questa mappa si cita @2026-09-29b: R1 = mappa, R2–R6 = risposte di Cline alla chat di scheda, i report dei prossimi task proseguono da R7@2026-09-29b. @2026-09-29 senza suffisso indica la serie precedente: R1 = mappa a 115e600, R2–R46 = report dei task T14–T19. @2026-09-28 e @2026-09-27 indicano le serie più vecchie. I fatti non rimappati conservano il riferimento originale.

## Stato repo
Radice: c:\Users\malse\Documents\GitHub\structural_hybrid_kelly [V, R1@2026-09-29b]
Alla mappa: branch main a 90a77a1 "C3 (#17)"; working tree pulito, nessun file staged, modificato o non tracciato [V, R1@2026-09-29b]
main è allineato a origin/main rispetto all'ultimo fetch locale (0 avanti, 0 indietro). La mappa non ha eseguito git fetch, quindi lo stato reale del remote non è verificato [V, R1@2026-09-29b]. L'ultimo aggiornamento da origin è un pull fast-forward a 90a77a1, il 2026-09-29 alle 12:54:31 +0200 [V, R5@2026-09-29b]
Branch locali: solo main. Branch remoti: origin/HEAD → origin/main, origin/main [V, R1@2026-09-29b]
Remote origin: https://github.com/Fede046/structural_hybrid_kelly.git, fetch e push [V, R1@2026-09-29b]
Ultimi cinque commit su main: 90a77a1 "C3 (#17)", 115e600 "C2 (#16)", 1e7813d "C1 (#14)", 640b906 "C1 (#13)", a7420cb "create c1 (#5)" [V, R1@2026-09-29b]. Data autore e data commit di 90a77a1: 2026-09-29T12:54:03+02:00 [V, R2@2026-09-29b]
Commit di story su main: 115e600 = S2/C2, 90a77a1 = S3/C3 [V, R1@2026-09-29 e R1@2026-09-29b]
I commit dei branch di lavoro non sono nella storia di main. Il branch C3 (5065407, 7bd013b, 2cea094, 4bb6327, a650494, 0406ef1, dalle 11:13 alle 12:52 del 2026-09-29) è entrato in main come il solo 90a77a1. Il branch C2 (da 5f7d414 a 2e623bd, 2026-09-28) è entrato come il solo 115e600. I branch locali C2 e C3 non esistono più [V, R1, R4 e R5@2026-09-29b]. Il meccanismo è lo squash merge del PR su GitHub [D]
File ignorati presenti: .pytest_cache/, .venv/, data/raw/E0/, e __pycache__/ in src/shk, kelly, stats, data, market e tests [V, R1@2026-09-29b]
Albero tracciato in HEAD (90a77a1):
- src/shk/ con i sottopacchetti kelly/, stats/, data/, market/
- tests/ con 17 moduli di test
- scripts/ con 5 script
- results/ con 5 CSV e .gitkeep; thesis/figures/ con 5 PNG e .gitkeep
- config/ con .gitkeep e split.toml; data/raw/ con .gitkeep
- .github/workflows/test.yml
- .agent/ con PROTOCOLLO.md, BACKLOG.md, MAPPA.md, SCHEDA.md, report/T1.md … report/T19.md
- alla radice pyproject.toml, uv.lock, .gitignore, LICENSE
[V, R1@2026-09-29b]
config/split.toml: su main lo tocca un solo commit, 90a77a1 (2026-09-29T12:54:03+02:00) [V, R2@2026-09-29b]. Il contenuto è identico a quello di 2cea0944b651b424fb704e03747340cfc26eda0e (2026-09-29T11:47:18+02:00, "Add frozen split config and role-based loading"). Quel commit non è contenuto in alcun branch locale o remoto ed è raggiungibile solo dalla reflog locale [V, R3–R6@2026-09-29b]. Il testo coincide con quello approvato, con test_unlocked = false [V, R28 e R38@2026-09-29]
data/raw/E0/ contiene 31 CSV, da 1993-94.csv a 2023-24.csv, scaricati dal programmatore il 2026-09-29 (solo la finestra di KellyBench, per sua decisione). .gitignore esclude data/raw/* tranne .gitkeep, quindi i CSV non sono versionati [V, R6 e R7@2026-09-29; presenza confermata da R1@2026-09-29b]
Nessun .env presente [V, R1@2026-09-29b, git status --ignored e albero]

## Stack e comandi
Pacchetto structural-hybrid-kelly 0.1.0 (in pyproject.toml e src/shk/__init__.py), importabile come shk, sorgenti in src/shk/ [V, R1@2026-09-29b]
requires-python >=3.11; la CI usa Python 3.12 [V, R1@2026-09-29b]
Build backend hatchling [V, R1@2026-09-29b]; build con hatch build o python -m build [D]
Dipendenze runtime: numpy, scipy, matplotlib, pandas (pandas aggiunta in T14). Dipendenze dev: solo pytest. Nessun vincolo di versione [V, R1@2026-09-29b]
uv.lock è presente alla radice ma non è aggiornato con pandas [V, R1@2026-09-29b]; uv sync come alternativa locale [D]
CI (.github/workflows/test.yml): pip install -e ".[dev]" senza uv.lock, poi pytest -v [V, R1@2026-09-29b]; trigger su push verso main e su pull_request [D]
CI (GitHub Actions) al 2026-09-28: Linux, Python 3.12.14, pytest 9.1.1, dipendenze senza vincoli. Prima di T13 falliva test_acceptance_csv_structure_and_values sul confronto dei float come stringhe [V, log CI fornito dal programmatore 2026-09-28]. Esito della CI dopo T13, dopo 115e600 e dopo 90a77a1 non verificato [D]
Test veloci: pytest -v; addopts = "-m 'not slow'" in pyproject.toml esclude i test slow [V, R1@2026-09-29b]
Interprete: Cline esegue ogni comando Python esplicitamente con il venv, cioè .\.venv\Scripts\python.exe -m pytest -v e .\.venv\Scripts\python.exe <script> [V, R7@2026-09-28; decisione del programmatore 2026-09-28]. Nel venv shk è installato in modalità editable [V, R7@2026-09-28]. Il terminale di Cline usa di default C:\Users\malse\anaconda3\python.exe (Python 3.12.7, pytest 7.4.4), dove shk non è installato [V, R6@2026-09-28]
Venv .venv: Python 3.12.7, pytest 9.1.1 [V, R7 e R15@2026-09-28]; NumPy 2.5.2, SciPy 1.18.1, pandas 3.0.6 [V, R10@2026-09-29]
Solo test slow: pytest -m slow; tutti i test: pytest -o addopts="" [D]
Suite veloce dopo T19: 181 verdi, 14 deselezionati, circa 14 s con i dati locali presenti [V, R46@2026-09-29]. I 181 sono i 109 di 115e600 più 18 di test_data_loading.py, 12 di test_coverage.py, 14 di test_split.py, 8 di test_devig.py, 11 di test_us_c3_2_acceptance.py e 9 di test_leakage.py. Non rieseguita su 90a77a1 [D]
Test slow: 14 (9 di C1, 5 di C2). Ultimo esito: 13 verdi e 1 rosso per il risultato noto test_acceptance_calibrated_phi_zero_within_mc_interval; pytest -m slow dura circa 117 s [V, R14@2026-09-28; non rieseguiti dopo]
Esperimento C1.1: .\.venv\Scripts\python.exe scripts/us_c1_1_growth_vs_lambda.py dalla radice [D]
Esperimento C1.2: .\.venv\Scripts\python.exe scripts/us_c1_2_estimation_error.py dalla radice, circa 70 s; due esecuzioni danno CSV identici byte per byte [D, era V R16@2026-09-27]
Esperimento C2: .\.venv\Scripts\python.exe scripts\us_c2_anova_autocorrelation.py dalla radice, circa 90 s. Due esecuzioni danno CSV identici, SHA256 6711B906A5D0170124BE816BAB04C336854CF7FF62DF135FDC18F22B84AB3831 [V, R14@2026-09-28, sul CSV di allora]; hash non ricalcolato sul CSV versionato [D]
Esperimento C3.1: .\.venv\Scripts\python.exe scripts/us_c3_1_data_coverage.py dalla radice, con data/raw/E0/ presente. Due esecuzioni danno CSV identici, SHA256 F9EEA7264F5457A1728EA609CD6660BCEE9779D450099D446CC30A919D73E15C [V, R14@2026-09-29]
Esperimento C3.2: .\.venv\Scripts\python.exe scripts/us_c3_2_devig_divergence.py dalla radice, con data/raw/E0/ presente. CSV identico su quattro esecuzioni, SHA256 5e9743252db28de1c2c6e28b5584725f4c2f78f47d4d830e318922d88e77ce92 [V, R43 e R44@2026-09-29]
File di configurazione: pyproject.toml e config/split.toml [V, R1@2026-09-29b]
Nessuna variabile d'ambiente richiesta o letta dal codice [D]

## Moduli e responsabilità
src/shk/ contiene 16 moduli applicativi (6 in kelly, 4 in stats, 4 in data, 2 in market) più 5 __init__.py [V, R1@2026-09-29b; conteggio ricalcolato dal supervisore]
src/shk/__init__.py — espone __version__ [V, R1@2026-09-28]
src/shk/kelly/__init__.py — re-esporta kelly_fraction e log_growth_rate tramite __all__; expected_final_wealth non è re-esportata [V, R1@2026-09-29b]
src/shk/kelly/core.py — formule chiuse per scommessa binaria: kelly_fraction(p, b), log_growth_rate(f, p, b), expected_final_wealth(f, p, b, T, b0=1.0) alle righe 97-144 [V, R1@2026-09-29b]; nessun import interno [V, R1@2026-09-28]
src/shk/kelly/core.py — kelly_fraction calcola (b·p − q)/b, restituisce 0.0 se il valore è ≤ 0, accetta solo scalari [D, era V R7@2026-09-27]
src/shk/kelly/simulate.py — draw_outcomes(p, T, M, rng) → (M, T) bool, True = vincita. simulate_growth(outcomes, fractions, b) → log-wealth (M, T+1) float64 con colonna 0 nulla; accetta frazioni broadcastabili da (), (T,), (1, T), (M, 1), (M, T) e rifiuta frazioni fuori da [0, 1). log_wealth_paths(outcomes, f, b) delega a simulate_growth. Nessun import interno [V, R1@2026-09-28; firme confermate R1@2026-09-29b]
src/shk/kelly/simulate.py — fattori logaritmici np.log(1 + b*f) e np.log(1 - f), senza log1p (righe 142-143) [D, era V R5@2026-09-27]
src/shk/kelly/estimation.py — relative_perturbation(p, delta) e noisy_estimates(p, sigma_p, T, M, rng); le stime sono saturate in [0, 1] con np.clip [V, R1@2026-09-29b]; nessun import interno [V, R1@2026-09-28]
src/shk/kelly/staking.py — kelly_staking(p_hat, b, lam=1.0); StakingMoments (NamedTuple: mean_c, mean_c2, var_c, fraction_zero); staking_moments(f_hat, f_star); plugin_staking(p_hat, b, sigma_p) [V, R1@2026-09-29b]; non importa core.py [V, R1@2026-09-28]
src/shk/kelly/staking.py — kelly_staking = lam·max(0, (b·p_hat − (1 − p_hat))/b), senza limite superiore su lam né sulla frazione. plugin_staking = λ_t·kelly_staking(p_hat, b), con λ_t = 1/(1 + (o·sigma_p/EV̂)²), o = b + 1, EV̂ = p_hat·o − 1, e 0.0 dove EV̂ ≤ 0 [D, era V R8 e R14@2026-09-27]
src/shk/kelly/scenarios.py — dataclass frozen Scenario(name, p, b, T, M); BASE_SCENARIO (0.60, 1.0, 1000, 10000); SUBTLE_SCENARIO (0.52, 1.0, 380, 10000); SEED = 20260927; spawn_generators(seed=SEED); draw_scenario_outcomes(scenario, rng); simulate_scenario(scenario, outcomes, p_hat, lam=1.0). Importa simulate.py e staking.py [V, R1@2026-09-29b]
src/shk/kelly/scenarios.py — spawn_generators restituisce due generatori da SeedSequence.spawn(2): il primo per gli esiti, il secondo per il rumore di stima [D, era V R10@2026-09-27]
src/shk/kelly/metrics.py — funzioni su paths: final_log_wealth, median_growth_rate, median_final_wealth, mean_final_wealth, max_drawdown ((M,) in [0, 1)), fraction_below_start; nessun import interno [V, R1@2026-09-28]
src/shk/kelly/metrics.py — median_growth_rate = mediana di ln(B_T/B_0)/T con T = paths.shape[1] − 1; il drawdown mediano si calcola con np.median(max_drawdown(paths)); fraction_below_start = quota di traiettorie con B_T < B_0 [D, era V R9 e R13@2026-09-27]
src/shk/stats/__init__.py — solo docstring di modulo in italiano: nessun import, nessuna re-esportazione, nessun __all__ [V, R5@2026-09-28]
src/shk/stats/anova.py — OneWayAnovaResult (NamedTuple: ss_between, ss_within, ss_total, df_between, df_within, ms_between, ms_within, f_statistic, p_value). oneway_anova(groups) → OneWayAnovaResult, con p-value da scipy.stats.f.sf. oneway_anova_vectorized(values, labels) → float se values è 1D, altrimenti ndarray di forma values.shape[:-1]. values e labels devono essere np.ndarray (altrimenti TypeError); le etichette sono interi 0..k−1, tutti presenti [V, R4@2026-09-28; firme confermate R1@2026-09-29b]. Medie di gruppo via matrice di incidenza, senza ciclo sulle serie [D]
src/shk/stats/timeseries.py — generate_ar1_series(phi, n, m, rng) → ndarray float64 (m, n), con righe = serie e colonne = tempo.
- Ordine delle estrazioni: prima x_0 ~ N(0, 1/(1 − φ²)) con size=m, poi le innovazioni N(0, 1) in un blocco (m, n − 1); ciclo solo sul tempo.
- ValueError per φ non finito o |φ| ≥ 1, n < 2, m < 1.
- TypeError per n o m bool o non interi, e per rng non Generator; interi NumPy accettati.
[V, R7@2026-09-28; ordine delle estrazioni confermato dal ricalcolo del supervisore]
src/shk/stats/false_rejection.py — costanti e tipi:
- Costanti: PHI_VALUES = (0.0, 0.3, 0.5, 0.7), N_OBS = 380, N_SERIES = 1000, ALPHA = 0.05, SEED_C2 = 20260928; DESIGN_CONTIGUOUS_2, DESIGN_CONTIGUOUS_38, DESIGN_RANDOM_2 e DESIGNS in quest'ordine; CSV_COLUMNS (10 colonne); FLOAT_CSV_COLUMNS; BLOCK_LENGTHS = (7, 20, 40); N_BOOT = 999; METHOD_NOMINAL; METHOD_BLOCK_BOOTSTRAP.
- RejectionResult: dataclass frozen con to_row(). block_length è str: "" per nominal, str(L) per block_bootstrap. critical_value_mean è il valore critico nominale oppure la media delle soglie calibrate.
- PhiStreams: NamedTuple con series_rng, perm_rng e boot_seed (SeedSequence).
[V, R13 e R14@2026-09-28; tipi confermati R1@2026-09-29b]
src/shk/stats/false_rejection.py — funzioni:
- spawn_c2_generators(seed=SEED_C2) → tupla ordinata come PHI_VALUES; make_design_labels(design, n_obs=N_OBS); critical_value_nominal; monte_carlo_interval_99.
- compute_nominal_rejection_rates(seed=SEED_C2) → 12 RejectionResult in ordine DESIGNS × PHI_VALUES.
- compute_calibrated_rejection_rates(seed=SEED_C2) → 12 RejectionResult per contiguous_2, in ordine BLOCK_LENGTHS × PHI_VALUES. Valida il seed in apertura e crea flussi nuovi con spawn_c2_generators. Usa le stesse serie del nominale (da series_rng). Per ogni φ esegue boot_seed.spawn(len(BLOCK_LENGTHS)) una sola volta e usa un generatore per L, in sequenza sulle serie. Chiama calibrate_threshold sulla serie grezza (H₀ non imposta) con la F vettorizzata di contiguous_2. Rigetto se la F osservata supera la soglia.
[V, R13 e R14@2026-09-28; 12 conteggi calibrati riprodotti dal supervisore]
src/shk/stats/calibration.py — funzioni:
- moving_block_indices(n, block_length, n_boot, rng) → int64 (n_boot, n): inizi con rng.integers(0, n − L + 1, size=(n_boot, ⌈n/L⌉)), blocchi costruiti per broadcasting, troncamento a n.
- compute_order_statistic_index(b, alpha) → int ⌈(1 − α)(b + 1)⌉, arrotondato all'intero più vicino se entro 1e-9; ValueError se il risultato supera b.
- calibrate_threshold(data, statistic, block_length, n_boot, alpha, rng, vectorized=False) → float. Gli indici si estraggono una sola volta. Con vectorized: statistic(data[indices]) su forma (B, *data.shape); altrimenti ciclo sulle B righe. L'output deve essere float64 di forma (n_boot,), altrimenti ValueError; un valore non finito dà ValueError. La soglia è l'elemento k − 1 delle statistiche ordinate.
- Nessun import da anova.py, timeseries.py o false_rejection.py.
[V, R12@2026-09-28; firme confermate R1@2026-09-29b]
src/shk/stats/calibration.py — la docstring del modulo contiene (a) uno schema indicativo dei quattro strumenti, (b) il rimando alle righe block_bootstrap del CSV C2, (c) "imporre H₀ spetta al chiamante". Nello schema (a), per l'ANOVA F il dato indicato è "la serie della risposta", in contraddizione con (c). Lo schema è stato dettato dal supervisore ed è da correggere [V, R12@2026-09-28 e R1@2026-09-29b]
scripts/us_c2_anova_autocorrelation.py — run_experiment() senza parametri. Scrive 24 righe (12 nominali, poi 12 calibrate) con csv.DictWriter e CSV_COLUMNS. PNG con plt.subplots(1, 2): pannello A nominale (tre disegni); pannello B con contiguous_2 nominale e una curva per L; linea ad ALPHA e banda al 99% in entrambi; etichette in italiano; savefig(dpi=150) [V, R13 e R14@2026-09-28]
src/shk/data/__init__.py — sola docstring di modulo in italiano [D]
src/shk/data/loading.py — DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "raw" / "E0". load_all_seasons(data_dir=DEFAULT_DATA_DIR, seasons: Collection[str] | None = None) → un unico DataFrame con colonna season (YYYY-YY, dal nome del file), Date in datetime64[us] senza nulli, ordinamento stabile per season e Date [V, R10 e R26@2026-09-29]
src/shk/data/loading.py — con seasons valorizzato si validano i nomi di tutti i file ma si leggono solo quelli richiesti. Una str o elementi non str danno TypeError; una collezione vuota o una stagione senza file danno ValueError [V, R26@2026-09-29 per i test verdi; D per i dettagli]
src/shk/data/loading.py — validazioni:
- TypeError per data_dir né str né Path.
- FileNotFoundError per directory inesistente.
- ValueError per: directory senza CSV; nome di file non conforme; date miste, non conformi o nella finestra esclusa (1° luglio – 31 agosto); campo in eccesso non vuoto; colonna senza nome non vuota.
[V, R10@2026-09-29]
src/shk/data/loading.py — decodifica per file: BOM → utf-8-sig, UTF-8 valido → utf-8, altrimenti cp1252, senza try. Righe di soli campi vuoti scartate; campi mancanti in coda completati; colonne senza nome vuote scartate; tipi inferiti da pd.read_csv; Date con formato esplicito %d/%m/%y o %d/%m/%Y [D, piano approvato di T14]
src/shk/data/coverage.py — costanti e classificazione:
- NON_ODDS_COLUMNS: identificativi (Div, Date, Time, HomeTeam, AwayTeam, season), risultati, primo tempo, arbitro e statistiche, comprese Attendance, HHW, AHW, HO, AO, HBP, ABP.
- ColumnClassification (NamedTuple: group_type, group_name, source, market, timing, kind).
- classify_column(name), pubblica: group_type ∈ {1x2_prematch, 1x2_closing, aggregators, other_markets}; timing ∈ {prematch, closing}; kind ∈ {odds, line, count}. Tutte le colonne Bb*, Max* e Avg* sono aggregators, con timing valorizzato. ValueError per colonne non di quota o sconosciute.
- GROUP_TYPE_ORDER.
[V, R14–R17 e R45@2026-09-29; costanti confermate R1@2026-09-29b]
src/shk/data/coverage.py — audit:
- COVERAGE_CSV_COLUMNS (12 colonne: season, group_type, group_name, source, market, timing, columns, total_rows, missing_rows, invalid_rows, complete_rows, is_complete).
- compute_coverage(df) → DataFrame lungo, una riga per stagione × gruppo presente.
[V, R14–R17 e R45@2026-09-29]
src/shk/data/coverage.py — regole di conteggio: presenza = almeno un valore non nullo del gruppo nella stagione; non validità solo per kind = odds (pd.to_numeric con coerce: non numerico, non finito o ≤ 1); NaN conta come mancante; il gruppo results controlla la validità di gol e FTR e la coerenza fra gol ed esito [D, piano approvato di T15]
src/shk/data/split.py — tipi e costanti:
- DEFAULT_SPLIT_CONFIG_PATH = radice del repo / config / split.toml.
- TestSetLockedError(RuntimeError) con __test__ = False.
- SplitConfig (NamedTuple: frozen_on, test_unlocked, test_unlocked_on, training, validation, test).
[V, R1@2026-09-29b]
src/shk/data/split.py — read_split_config(config_path): chiavi esatte, date TOML, ruoli disgiunti, test non vuoto, training e validation < min(test) [V, R26@2026-09-29 per i test verdi; D per i dettagli]
src/shk/data/split.py — load_by_role(role, config_path, data_dir):
- Con il test bloccato, "test" → TestSetLockedError prima di leggere i dati.
- Le stagioni ≥ min(test), ricavate dai nomi dei file, non sono mai restituite né lette dai ruoli non test.
- history = stagioni presenti < min(test) che non sono né di training né di validation.
- Una stagione elencata ma assente dà ValueError.
- Delega a load_all_seasons di loading.py.
[V, R26 e R39@2026-09-29 e R1@2026-09-29b; D per i dettagli del piano]
src/shk/data/walkforward.py — PREMATCH_IDENTIFIERS (righe 13-15); LeakageError(RuntimeError); get_prematch_whitelist(columns) → tuple costruita per inclusione: identificativi Div, Date, HomeTeam, AwayTeam, season, Time, più le colonne con classify_column kind = odds e timing = prematch, con cache lru_cache. Importa coverage.py [V, R45 e R46@2026-09-29 e R1@2026-09-29b]
src/shk/data/walkforward.py — walkforward_split(df, seasons_to_predict) → generatore di coppie (storia DataFrame, partita Series):
- storia = df.iloc[:searchsorted(Date, side="left")], una slice da non modificare;
- partita = riga ridotta alla whitelist;
- ValueError se df non è ordinato per Date o mancano Date e season;
- TypeError se seasons_to_predict è str o ha elementi non str.
[V, R46@2026-09-29; D per i dettagli interni]
src/shk/data/walkforward.py — check_leakage(history, match, whitelist=None) → lista di violazioni: date non anteriori, partita presente nella storia, campi fuori whitelist; la whitelist predefinita si ricava da history.columns. assert_no_leakage solleva LeakageError. Il modulo non chiama load_all_seasons [V, R46@2026-09-29]
walkforward_split e assert_no_leakage oggi sono usati solo da tests/test_leakage.py: nessuno script li chiama [D]
src/shk/market/__init__.py — sola docstring di modulo in italiano [V, R32@2026-09-29]
src/shk/market/devig.py — funzioni: implied_probabilities(odds) → (N, n); overround(odds) → (N,) con S − 1; devig_proportional(odds) → (N, n); devig_additive(odds) → (N, n), con riga di NaN dove un q ≤ 0; devig_power(odds) → (q (N, n), k (N,)). Non importa da shk.data [V, R30–R36 e R39@2026-09-29; valori ricalcolati dal supervisore]
src/shk/market/devig.py — validazione comune: argomento ndarray (N, n) con n ≥ 2. TypeError per argomento non ndarray o dtype non intero né floating reale (bool, complessi, object). ValueError per forma sbagliata e per quote non finite o ≤ 1. Conversione interna in float64 [V, R30–R36@2026-09-29]
src/shk/market/devig.py — power: Newton vettorizzato da k = 1, con salvaguardia k_new ≥ k/2; MAX_NEWTON_ITERATIONS = 50 (riga 7); RuntimeError se dopo il ciclo |Σq − 1| > 1e-12 su qualche mercato [V, R32@2026-09-29 e R1@2026-09-29b]
src/shk/market/divergence.py — costanti: ODDS_BINS (1, 1.5, 2, 3, 5, 10, inf); ODDS_BIN_LABELS; REFERENCE_EDGE = 0.02; B365_ODDS_COLUMNS (riga 33); DIVERGENCE_CSV_COLUMNS, 19 colonne:
- level, category, n_outcomes, matches_used, matches_excluded, additive_nan_matches, mean_overround;
- mean_q_* per metodo;
- mean_spread_pts, p99_spread_pts, max_spread_pts, mean_relative_spread, max_spread_ratio_to_edge, p99_spread_ratio_to_edge;
- max_abs_sum_error_* per metodo.
[V, R41 e R44@2026-09-29]
src/shk/market/divergence.py — assign_odds_bin: fasce chiuse a sinistra. compute_divergence_table:
- partite usate = B365 valida e additivo applicabile;
- overround calcolato sulle partite usate;
- 99° percentile con np.percentile method="linear";
- con zero partite usate le colonne statistiche restano vuote.
[V, R41 e R44@2026-09-29; D per i dettagli del piano]
scripts/us_c3_1_data_coverage.py — run_experiment(): load_all_seasons, compute_coverage, CSV con csv.DictWriter. PNG con imshow della quota complete_rows/total_rows, colormap viridis; gruppi assenti come NaN in grigio #dcdcdc, spiegati in legenda [V, R14 e R17@2026-09-29]
scripts/us_c3_2_devig_divergence.py — run_experiment(): read_split_config, load_by_role("training") e load_by_role("validation") concatenati, compute_divergence_table. CSV di 29 righe (6 fasce, 22 stagioni di training e validazione, 1 overall). PNG a due pannelli (spread medio in punti e spread relativo medio per fascia, etichette in italiano) [V, R43@2026-09-29 e R1@2026-09-29b]
tests/ — 17 moduli: test_kelly_core, test_simulate, test_estimation, test_staking, test_metrics, test_anova, test_timeseries, test_calibration, test_data_loading, test_coverage, test_split, test_devig, test_leakage, test_us_c1_1_acceptance, test_us_c1_2_acceptance, test_us_c2_acceptance, test_us_c3_2_acceptance [V, R1@2026-09-29b]
tests/test_anova.py — 23 test veloci: toy; concordanza con f_oneway su toy e su 3 dataset casuali; partizione della devianza; versione vettorizzata su (3, 4, 380) con contiguous_2 e con k = 5 permutato; validazioni [V, R4@2026-09-28]
tests/test_timeseries.py — 13 test veloci: forma e dtype; riproducibilità; varianze e autocorrelazione pooled parametrizzate su φ ∈ {0.0, 0.3, 0.7} con seed 20260928; validazioni [V, R7@2026-09-28]
tests/test_calibration.py — 15 funzioni di test (18 test): proprietà degli indici, L = n, integrità delle righe 2D, statistica d'ordine, vectorized contro non vectorized, due statistiche, seed, i quattro casi di compute_order_statistic_index, docstring, validazioni [V, R12@2026-09-28]
tests/test_us_c2_acceptance.py — 11 test veloci e 5 slow, con fixture scope="module". Nei confronti fra CSV e valori calcolati, le colonne di FLOAT_CSV_COLUMNS usano math.isclose (rel_tol 1e-12, abs_tol 0); le altre si confrontano esattamente come stringhe [V, R15@2026-09-28]
tests/test_data_loading.py — 18 test veloci su CSV sintetici in tmp_path, più un test sui dati reali saltato se data/raw/E0/ non contiene CSV [V, R10@2026-09-29]
tests/test_coverage.py — 12 test veloci su DataFrame sintetici:
- classificazione: MaxCH e AvgCA come aggregators closing; colonne non di quota e sconosciute → ValueError;
- validità: stringa non numerica, inf, NaN; line e count mai non validi; riga insieme mancante e non valida;
- altro: gruppo assente omesso, risultati, colonne e ordinamento del CSV, esclusione delle statistiche e del primo tempo.
[V, R15, R16 e R18@2026-09-29]
tests/test_split.py — 14 test veloci:
- validazioni di tipo e valore; parametro seasons; file bloccato non letto; blocco e sblocco del test; ruoli non test senza stagioni bloccate;
- test di guardia AST su sorgenti sintetici e sul repository;
- file reale config/split.toml; dati reali per ruolo (saltato senza CSV).
[V, R26@2026-09-29]
tests/test_leakage.py — 9 test veloci:
- validazioni;
- fornitore vero su dati sintetici: più partite nello stesso giorno, due stagioni, storia vuota;
- rilevamento delle violazioni; tre mutanti (side="right", partita nella storia, riga intera);
- campi vietati su dati sintetici e reali;
- nessun leakage sulle 8 360 partite reali di training e validazione (8.05 s, saltato senza CSV).
[V, R46@2026-09-29]
tests/test_devig.py — 8 test veloci:
- valori di riferimento (tolleranza 5e-6 sulle probabilità, 5e-5 su k);
- 10 000 mercati casuali con default_rng(20260929) e quote uniformi in [1.1, 10.0], S ≤ 1 incluso;
- caso S = 1; riga di NaN dell'additivo su (1.05, 10.0, 50.0);
- rapporto q_proporzionale / q_power decrescente in π per S > 1;
- mercati estremi, validazioni, overround.
[V, R32 e R35@2026-09-29; tolleranze R1@2026-09-29b]
tests/test_us_c3_2_acceptance.py — 11 test veloci:
- fasce ai bordi e input non validi; tabella su dati sintetici; additivo NaN escluso;
- esistenza di CSV e PNG, colonne e 29 righe;
- criteri letti dal CSV versionato: somma a 1 entro 1e-12, overround medio in [0.01, 0.15], spread relativo massimo nella fascia [10, inf), sole stagioni di training e validazione;
- ricalcolo dai dati reali con math.isclose (rel_tol e abs_tol 1e-12), saltato senza CSV.
[V, R44@2026-09-29 e R1@2026-09-29b]
Classi del pacchetto: Scenario, StakingMoments, OneWayAnovaResult, RejectionResult, PhiStreams, ColumnClassification, SplitConfig, TestSetLockedError, LeakageError [V, R1@2026-09-29b]; nessun'altra [D]
Persistenza: risultati solo come CSV versionati in results/ e PNG versionati in thesis/figures/; configurazione dello split in config/split.toml; dati grezzi in data/raw/E0/, non versionati [V, R1@2026-09-29b]; nessun database [D]

## Flussi principali
Esperimento C1.1 (scripts/us_c1_1_growth_vs_lambda.py, run_experiment() dal blocco __main__): parametri locali alle righe 30-36, cioè p=0.60, b=1.0, T=1000, M=10000, seed 20260905, 51 valori di λ in [0, 2.5] [V, R1@2026-09-29b]
Esperimento C1.1, sequenza: f* con kelly_fraction; una sola matrice di esiti con draw_outcomes; per ogni λ, log_wealth_paths, cinque metriche empiriche, del paths, e benchmark con log_growth_rate ed expected_final_wealth [V, R1@2026-09-28]. La frazione passata a log_wealth_paths è λ·f* [D]
Esperimento C1.1, output: results/us_c1_1_growth_vs_lambda.csv (10 colonne: lambda, f, median_growth_rate, analytic_growth_rate, median_final_wealth, mean_final_wealth_mc, mean_final_wealth_analytic, drawdown_median, drawdown_p95, fraction_below_start) e thesis/figures/us_c1_1_growth_vs_lambda.png (tre pannelli) [V, R1@2026-09-28 per file e conteggio; D per i nomi delle colonne]
Accettazione C1.1 (tests/test_us_c1_1_acceptance.py): tutti i test sono @pytest.mark.slow; parametri ripetuti a mano; esiti rigenerati in ogni test con seed 20260905. Asserzioni: picco della mediana a λ=1.0; drawdown mediano non decrescente con tolleranza −0.01; |g mediano| < 0.002 a λ=1.946; crescita negativa a λ=2.5 [V, R1@2026-09-29b]
Esperimento C1.2 (scripts/us_c1_2_estimation_error.py, run_experiment()): scenari e SEED da scenarios.py. Per ogni combinazione: spawn_generators(SEED); esiti con draw_scenario_outcomes; errore deterministico ±10% con relative_perturbation; per σ_p ∈ {0.015, 0.0283, 0.045}, p̂ da noisy_estimates, f̂ da kelly_staking con lam=1, momenti da staking_moments. Regole: lambda_star, ratio_moments, lambda_linear, quarter_kelly, half_kelly, full_kelly, plugin [V, R1@2026-09-29b]
Esperimento C1.2, output: results/us_c1_2_estimation_error.csv (12 colonne, 46 righe = 2 scenari × (2 + 3 × 7)) e thesis/figures/us_c1_2_estimation_error.png (due pannelli) [V, R1@2026-09-29b; conteggio ricalcolato dal supervisore]
Esperimento C1.2, colonne del CSV: scenario, sigma_p, rule, lambda, mean_c, mean_c2, var_c_empirical, var_c_linear, fraction_f_hat_zero, median_growth_rate, median_drawdown, fraction_below_start. Float nativi, stringa vuota per i valori non applicabili [V, R8@2026-09-28]. Regole deterministiche: overestimation_10pct e underestimation_10pct [D]
Accettazione C1.2 (tests/test_us_c1_2_acceptance.py): importa scenari e SEED da scenarios.py. I test veloci verificano esiti indipendenti da p̂ e matrice esiti non modificata. I test slow verificano l'asimmetria ±10% nello scenario sottile, Var(c) a σ_p = 0.0283 (nello scenario base entro 0.005 dal riferimento) e λ* contro λ = 0.25 [V, R1@2026-09-29b]
Esperimento C2 nominale (righe method = nominal del CSV, ordine DESIGNS × PHI_VALUES). Rigetti su 1000 serie per φ = 0.0, 0.3, 0.5, 0.7:
- contiguous_2: 37, 149, 253, 399
- contiguous_38: 44, 843, 999, 1000
- random_2: 58, 35, 48, 45
Intervallo al 99%: [0.0322461452073078, 0.0677538547926922]. Valori critici: 3.866176954321902 (k = 2) e 1.445838076487165 (k = 38) [V, R9@2026-09-28 e ricalcolo del supervisore]
Esperimento C2 calibrato (contiguous_2, B = 999, soglia sulla serie grezza). Rigetti su 1000 serie per L = 7, 20, 40:
- φ = 0.0: 35, 29, 32
- φ = 0.3: 61, 57, 49
- φ = 0.5: 73, 52, 42
- φ = 0.7: 108, 65, 56
Media delle soglie da 3.46 a 18.64, contro 3.866 nominale. A φ = 0, correlazione di rango fra F osservata e soglia: 0.057, 0.19, 0.276 [V, R14@2026-09-28 e ricalcolo del supervisore]
CSV C2: 24 righe (12 nominali e 12 calibrate), 10 colonne [V, R1@2026-09-29b]
Uso come libreria: from shk.kelly import kelly_fraction, log_growth_rate; expected_final_wealth solo da shk.kelly.core [V, R1@2026-09-29b]
Valori analitici con p=0.6, b=1:
- f* = 0.2; g(0.2) = 0.020136; g(0.4) = −0.002447; g(0.5) ≈ −0.0340;
- zero di g a f ≈ 0.3894, cioè λ ≈ 1.9470;
- vicino a f ≈ 0.3894, una vincita in più o in meno su T=1000 sposta la crescita mediana di circa 0.0008.
Le costanti di tests/test_kelly_core.py:32 e :39 e il λ=1.946 dell'accettazione C1.1 sono valori analitici, non empirici [D, ricalcolo del supervisore]
Var(c) attesa a σ_p = 0.0283: circa 0.080 nello scenario base, circa 1.28 in quello sottile (troncamento a zero incluso) [D, ricalcolo del supervisore]
Costo della calibrazione: una chiamata di calibrate_threshold con n = 380, F a due blocchi, L = 20, B = 999 e vectorized vero dura in media 6.8 ms nel venv [V, R11@2026-09-28]
Dati E0 caricati da load_all_seasons [V, R10@2026-09-29]:
- 31 stagioni, 11 944 partite: 462 nel 1993-94 e nel 1994-95, 380 nelle altre;
- 161 colonne originali più season; colonne con nome per stagione da 7 a 106.
Colonne dei dati E0 [V, R8@2026-09-29]:
- comuni a tutte le stagioni: Div, Date, HomeTeam, AwayTeam, FTHG, FTAG, FTR; Time solo dal 2019-20;
- presenza delle colonne, non completezza: B365 pre-partita dal 2002-03; IW e WH dal 2000-01; PS e PSC* dal 2012-13; B365C* e le altre terne di chiusura dal 2019-20; Bb* dal 2005-06 al 2018-19; Max*/Avg* dal 2019-20.
Codifiche dei file E0: il 2004-05 esce decodificato in cp1252 (9 byte 0xA0 davanti ai nomi degli arbitri, righe 316–324); il 2021-22 ha il BOM UTF-8 [V, R9@2026-09-29]
Esperimento C3.1 [V, R14@2026-09-29; scomposizione ricalcolata dal supervisore]:
- output: results/us_c3_1_data_coverage.csv con 477 righe (31 risultati + 183 terne pre-partita + 37 terne di chiusura + 158 aggregatori + 68 altri mercati) e thesis/figures/us_c3_1_data_coverage.png;
- risultati completi in tutte le stagioni dal 1993-94;
- prima terna 1X2 pre-partita completa nel 2000-01 (GB, IW, SB, WH; LB 325/380), due stagioni prima del 2002-03 del paper;
- B365 pre-partita completa in tutte le 22 stagioni dal 2002-03 al 2023-24 e assente dal 1993-94 al 2001-02, quindi anche nel 2000-01, che è di training.
Split congelato (config/split.toml) [V, R26@2026-09-29; conteggi ricalcolati dal supervisore]:
- training: 2000-01, 2010-11, 2020-21 (1 140 partite);
- validation: 19 stagioni, dal 2002-03 al 2022-23 tranne le due di training (7 220 partite);
- history: 1993-94 … 1999-00 e 2001-02, 8 stagioni (3 204 partite);
- test: 2023-24, bloccato (380 partite, non lette).
Esperimento C3.2 (B365 pre-partita, training e validazione) [V, R43@2026-09-29 e R1@2026-09-29b; overround medio e rapporti ricalcolati dal supervisore]:
- partite: 7 980 usate su 8 360; 380 escluse, tutte del 2000-01; 0 mercati esclusi per l'additivo;
- overround medio 5.437%; per stagione dal 7.86% all'11.60% nel 2002-03…2006-07, dal 2.62% al 5.99% dopo;
- spread medio in punti massimo nella fascia [1, 1.5) (2.33);
- spread relativo medio massimo in [10, ∞) (0.222), non monotono (minimo in [2, 3), 0.008);
- spread massimo 6.29 punti, cioè 3.14 volte l'edge di 2 punti; 99° percentile 3.45 punti, cioè 1.73 volte.
Walk-forward anti-leakage, verificato da tests/test_leakage.py sulle stagioni di training e validazione con la history come storia pregressa: 8 360 partite previste, zero violazioni. Sulle colonne reali la whitelist ha 87 campi: 6 identificativi e 81 quote pre-partita (1X2 dei bookmaker e aggregate, over/under 2.5, handicap asiatico); nessuna chiusura, linea o conteggio [V, R46@2026-09-29; composizione ricontata dal supervisore]

## Convenzioni da rispettare
Naming: snake_case per moduli, funzioni e variabili; PascalCase per le classi; UPPER_CASE per le costanti; lettere matematiche della letteratura (p, b, f, T, M, b0, λ, σ_p, c, δ, φ, L, B, α, q) [V, R1@2026-09-29b]
Lingua: identificatori, nomi dei test e messaggi di eccezione in inglese; commenti e docstring in italiano [V, R1@2026-09-29b]
Type hints completi su argomenti e ritorni; docstring in stile NumPy con sezioni Parametri / Restituisce / Solleva [V, R1@2026-09-29b]
Validazione in apertura di funzione: ValueError per i valori, TypeError per i tipi; rng controllato con isinstance(rng, np.random.Generator) → TypeError [V, R5@2026-09-28]
Eccezione nel codice esistente: draw_outcomes e noisy_estimates non controllano il tipo di T e M (True è accettato come 1) [V, R1@2026-09-29b]
Il codice nuovo controlla anche il tipo degli interi (bool e non interi → TypeError), come generate_ar1_series [V, R7@2026-09-28]; una str passata dove si attende una collezione di str dà TypeError (load_all_seasons, walkforward_split) [V, R26 e R46@2026-09-29]
Nessuna occorrenza di try:, print( o logging in src/ e scripts/. Fonti:
- file di S1: [V, R4@2026-09-28, git grep];
- file di S2: [V, R5, R8, R10 e R12@2026-09-28];
- file di S3: [V, R14, R26, R32, R43 e R46@2026-09-29].
Non ricontrollato con una ricerca sulla mappa di 90a77a1 [D]
L'RNG entra come argomento e non viene mai creato dentro le funzioni di libreria; i flussi indipendenti si derivano con np.random.SeedSequence.spawn [V, R1@2026-09-29b]
Vettorizzazione NumPy senza cicli su M e T nel motore; del paths nei loop Monte Carlo [V, R1@2026-09-28]
Script di esperimento: matplotlib.use("Agg") prima di importare pyplot; run_experiment() senza parametri, chiamata dal blocco __main__; nessun argomento da riga di comando; import diretti da shk.* [V, R8@2026-09-28 e R1@2026-09-29b]
Output degli script: CSV con csv.DictWriter, open(mode="w", newline="", encoding="utf-8"), lineterminator di default (\r\n), float nativi e stringa vuota per i valori non applicabili; PNG con plt.tight_layout() e savefig(dpi=150); etichette delle figure in italiano [V, R8 e R9@2026-09-28 e R1@2026-09-29b]
Parametri condivisi fra script e test in un modulo di libreria importato da entrambi: scenarios.py per C1.2, false_rejection.py per C2, coverage.py e divergence.py (con split.toml) per C3. C1.1 è l'eccezione storica [V, R1@2026-09-29b]
Nomi: scripts/us_<story>_<nome>.py, con lo stesso nome base per results/<nome>.csv e thesis/figures/<nome>.png, entrambi versionati [V, R1@2026-09-29b]
Test in tests/test_*.py. I Monte Carlo su larga scala si marcano @pytest.mark.slow; i test sui dati reali si saltano con motivo esplicito se data/raw/E0/ non contiene CSV; i test anti-leakage non si marcano slow [V, R1@2026-09-29b; decisioni della story S3]
Dati reali nel codice nuovo solo attraverso load_by_role; load_all_seasons è ammessa solo nei quattro file controllati dal test di guardia [V, R26@2026-09-29 e R1@2026-09-29b]
Commit fatti solo dal programmatore, a mano [V, testo di .agent/PROTOCOLLO.md fornito dal programmatore 2026-09-28]. Ogni story si sviluppa su un branch di lavoro (C2, C3) che entra in main come un solo commit; i commit intermedi non restano nella storia di main e il branch locale viene poi cancellato [V, R4 e R5@2026-09-29b]
Cline scrive in .agent/ solo MAPPA.md in mappatura e report/T<n>.md in esecuzione [V, testo di .agent/PROTOCOLLO.md fornito dal programmatore 2026-09-28]
.agent/PROTOCOLLO.md, sezione "Convenzioni del progetto": nessuna convenzione aggiuntiva per questo progetto; valgono le regole di base dei prompt e quelle di questa sezione [V, testo di .agent/PROTOCOLLO.md fornito dal programmatore 2026-09-28]
Documenti di processo in .agent/: PROTOCOLLO.md, BACKLOG.md, MAPPA.md, SCHEDA.md, report/T<n>.md (oggi da T1 a T19), tutti versionati [V, R1@2026-09-29b]

## Zone fragili da non toccare senza avviso
Il test slow test_acceptance_calibrated_phi_zero_within_mc_interval (tests/test_us_c2_acceptance.py:350-363 [V, R1@2026-09-29b]) fallisce per un risultato noto: 29 rigetti su 1000 a φ = 0 con L = 20, sotto l'estremo inferiore 32.25 dell'intervallo al 99% (T12 da rivedere). Non è una regressione e non va "sistemato" allentando la tolleranza o cambiando parametri [V, decisione del programmatore 2026-09-28; conteggio da R14@2026-09-28, non rieseguito]
noisy_estimates può restituire p̂ = 1 per saturazione. kelly_staking dà allora lam·1, e con lam ≥ 1 la frazione è ≥ 1, che simulate_growth rifiuta con ValueError [V, R1@2026-09-29b]. Con p ≤ 0.6 e σ_p ≤ 0.045 l'evento dista almeno 8.9 deviazioni standard [D, ricalcolo del supervisore]
expected_final_wealth (core.py:97-144) è usata dallo script C1.1 [V, R1@2026-09-29b] e non ha test [D]
Parametri di C1.1 duplicati fra scripts/us_c1_1_growth_vs_lambda.py:30-36 e tests/test_us_c1_1_acceptance.py: cambiarli da una parte sola disallinea esperimento e verifica [V, R1@2026-09-29b]
I test slow non girano in CI (addopts li esclude, la CI esegue solo pytest -v) [V, R1@2026-09-29b]. Dopo modifiche a simulate.py, staking.py, scenarios.py, metrics.py o src/shk/stats/ vanno lanciati a mano [D]
Rieseguire uno script di esperimento sovrascrive CSV e PNG versionati: ogni task che rigenera un esperimento deve dire se vanno committati [V, R1@2026-09-28]
Le dipendenze non hanno vincoli di versione e la CI installa con pip ignorando uv.lock [V, R1@2026-09-29b]. NumPy non garantisce la stabilità del flusso di Generator fra versioni, quindi i test con tolleranze empiriche possono rompersi [D]. Per default_rng(20260928).normal il flusso dà valori identici a 15 cifre con NumPy 2.4.4 e 2.5.2 [V, R7@2026-09-28 e ricalcolo del supervisore]
tests/test_metrics.py:test_metrics_error_conditions non verifica il ValueError di median_final_wealth e mean_final_wealth [V, R1@2026-09-29b]
Il test del drawdown non decrescente (tolleranza −0.01) è l'unica asserzione di accettazione C1.1 di cui non si è stimata la robustezza al seed e alla versione di NumPy [D]
tests/test_us_c2_acceptance.py confronta il CSV versionato con compute_nominal_rejection_rates (test veloce) e con compute_calibrated_rejection_rates (test slow). Ogni modifica a false_rejection.py che cambia i risultati richiede di rieseguire lo script (circa 90 s) prima dei test [V, R14@2026-09-28]
L'identità byte per byte del CSV C2 vale solo a parità di ambiente: il valore critico per k = 2 è 3.866176954321902 nel venv (scipy 1.18.1) e 3.866176954321901 in CI [V, R9 e R15@2026-09-28, log CI]. Dopo T13 i test confrontano i float con tolleranza; rigenerare il CSV in un altro ambiente può comunque cambiare il file [D]
Controlli dei CSV versionati:
- i run_experiment() dei cinque script non sono richiamati da alcun test [D];
- il CSV di C2 è confrontato con il codice da tests/test_us_c2_acceptance.py [V, R14@2026-09-28];
- il CSV di C3.2 da tests/test_us_c3_2_acceptance.py, con ricalcolo solo in locale [V, R44@2026-09-29];
- il CSV di C3.1 non ha un test di confronto [D].
pandas 3.0.6 è nel venv; la CI installa l'ultima versione senza vincoli. In pandas 3 Date esce in datetime64[us], non [ns] [V, R10@2026-09-29], e le colonne di testo hanno di default il dtype stringa, non object [D]: da tenere presente nei controlli sulle quote non numeriche
I test sui dati reali non girano in CI, perché data/raw/* è escluso da .gitignore: in CI si saltano e vanno eseguiti in locale [D]. Il test sui dati reali di tests/test_leakage.py dura circa 8 s ed è nella suite veloce [V, R46@2026-09-29]
classify_column solleva ValueError su ogni colonna che le regole non classificano: nuovi file E0 con colonne nuove (per esempio stagioni successive al 2023-24) fermano audit e fornitore walk-forward finché le regole non vengono estese [D]
La whitelist anti-leakage di walkforward.py si basa su kind e timing di classify_column: estendere le regole di coverage.py cambia anche i campi esposti dal fornitore, e va rivisto contro il test dei campi vietati [V, R45 e R46@2026-09-29]
config/split.toml è congelato e non si modifica. Lo sblocco del test lo fa solo il programmatore, a mano e con commit, dopo il congelamento dei parametri (US-C8.2) [V, decisione della story S3]
La prova del congelamento (US-C3.3) è la data di commit di config/split.toml. Su main quella data è 2026-09-29T12:54:03+02:00 (90a77a1), successiva al commit dell'analisi C3.2 sul branch (a650494, 12:31). Il commit delle 11:47:18 (2cea094), con contenuto identico, è raggiungibile solo dalla reflog locale [V, R2–R6@2026-09-29b]. Una garbage collection di git può eliminarlo quando la voce di reflog scade (per default circa 30 giorni per i commit non raggiungibili) [D]. Vedi Punti ancora incerti
Il test di guardia di tests/test_split.py fallisce se load_all_seasons compare, come import o riferimento, in file di src/ o scripts/ diversi dai quattro ammessi (loading.py, split.py, coverage.py, scripts/us_c3_1_data_coverage.py) [V, R26@2026-09-29 e R1@2026-09-29b]
devig_power solleva RuntimeError se anche un solo mercato non converge entro 1e-12 in 50 iterazioni: su quote estreme ferma l'intero calcolo, non solo il mercato [V, R32@2026-09-29 e R1@2026-09-29b per il comportamento; D per le quote reali]
devig_additive restituisce righe di NaN, che vanno escluse dal confronto per tutti i metodi (decisione della story S3) [V, R32@2026-09-29]. tests/test_devig.py:test_extreme_markets salta i mercati NaN dell'additivo e non rileverebbe un NaN spurio su quei mercati [V, R35@2026-09-29]
Una parte dei test di tests/test_us_c3_2_acceptance.py legge il CSV versionato: ogni modifica a divergence.py o devig.py che cambia i risultati richiede di rieseguire lo script (con i dati locali) prima dei test [V, R44@2026-09-29]

## Punti ancora incerti
Prova del congelamento dello split: la data su main è 12:54:03 (90a77a1); quella delle 11:47:18 (2cea094) sta solo nella reflog locale. Blocca: la data di congelamento da dichiarare in US-C3.3 e in tesi, e la conservazione di 2cea094. Alternative, da decidere col programmatore: (a) dichiarare 90a77a1 come prova, precisando che il contenuto è identico a quello di 2cea094; (b) conservare 2cea094 con un tag pubblicato su origin, messo a mano dal programmatore prima che la reflog scada; (c) affidarsi al ref del PR #17 su GitHub, non verificato [D]. Si procede: il contenuto non è cambiato e nessun task di codice dipende dalla scelta.
Gestore canonico delle dipendenze (pip + pyproject.toml oppure uv + uv.lock), non deciso dal programmatore; uv.lock non è aggiornato con pandas. Blocca: se la CI vada migrata a uv. Si procede con pyproject.toml come fonte di verità, l'unica usata dalla CI.
Se la calibrazione per block bootstrap debba imporre H₀ nei dati prima di ricampionare (per l'ANOVA: serie centrata per gruppo). Blocca: la chiusura di T12 (test slow rosso), la correzione dello schema della docstring di calibration.py e la scelta di L per C5.2, C6.4 e C8. Si procede lasciando il test slow com'è e senza toccare calibration.py né false_rejection.py. Proposta: un task nuovo che aggiunge al CSV righe method = block_bootstrap_centered accanto a quelle attuali, con criteri scritti e datati prima dell'esecuzione.
Esito della CI su main dopo 90a77a1 (pandas più recente, test S3 sintetici) e stato della suite veloce su 90a77a1: non verificati. Blocca: la baseline del prossimo task di scrittura, che deve partire da una suite verde. Si procede facendo cominciare il prossimo task con l'esecuzione della suite veloce.
Scenario di training 2000-01 senza B365: con q alimentato da B365, in C3.2 è escluso per intero (380 partite). Blocca: gli esperimenti di C4 e C8 che usano quello scenario. Alternative: (a) dichiararlo in tesi e procedere con 2010-11 e 2020-21; (b) usare per il solo 2000-01 un'altra terna completa (GB, IW, SB o WH); (c) rivedere lo scenario in una chat di backlog. Decisione del programmatore [V, R14 e R43@2026-09-29]
Versionamento dei CSV E0: oggi sono esclusi da .gitignore, quindi in CI i test sui dati reali si saltano. Blocca: se la CI possa mai verificare le pipeline su dati reali. Decisione del programmatore, dopo il controllo della licenza (note 2.9) [V, R6@2026-09-29]

## Ultimo aggiornamento
R6@2026-09-29b — task di scrittura chiusi dopo la mappa del 2026-09-29b: nessuno

----

Stato repo → (nuova riga, dopo "Branch locali: solo main. …") →
Dopo la mappa: branch C4 creato da 90a77a1 con due commit solo su .agent/ (4b9e6c1 "Refresh C3 project documentation", 475f65f "Update BACKLOG.md"; diff solo su BACKLOG.md, MAPPA.md, SCHEDA.md). A inizio T20 HEAD su C4 a 475f65f, working tree pulito [V, R7 e R11@2026-09-29b]. Dopo T20 il working tree contiene, non committati, src/shk/model/__init__.py, src/shk/model/elo.py, tests/test_elo.py, .agent/report/T20.md [D]

Stato repo → "Branch locali: solo main. Branch remoti: origin/HEAD → origin/main, origin/main [V, R1@2026-09-29b]" →
Branch locali: C4 (corrente) [V, R11@2026-09-29b]; main presumibilmente ancora presente [D]. Branch remoti: origin/HEAD → origin/main, origin/main [V, R1@2026-09-29b]; se C4 sia pubblicato su origin non è verificato [D]

Stack e comandi → "Suite veloce dopo T19: 181 verdi, 14 deselezionati, circa 14 s con i dati locali presenti [V, R46@2026-09-29]. I 181 sono … Non rieseguita su 90a77a1 [D]" →
Suite veloce: 181 verdi, 14 deselezionati, 14.41 s su C4 a 475f65f, codice identico a 90a77a1 [V, R11@2026-09-29b]. I 181 sono i 109 di 115e600 più 18 di test_data_loading.py, 12 di test_coverage.py, 14 di test_split.py, 8 di test_devig.py, 11 di test_us_c3_2_acceptance.py e 9 di test_leakage.py. Dopo T20: 212 verdi (più 31 di test_elo.py), 14 deselezionati, 13.92 s [V, R11@2026-09-29b]

Moduli e responsabilità → "src/shk/ contiene 16 moduli applicativi (6 in kelly, 4 in stats, 4 in data, 2 in market) più 5 __init__.py [V, R1@2026-09-29b; conteggio ricalcolato dal supervisore]" →
src/shk/ contiene 17 moduli applicativi (6 in kelly, 4 in stats, 4 in data, 2 in market, 1 in model) più 6 __init__.py [V, R1@2026-09-29b e R11@2026-09-29b; conteggio ricalcolato dal supervisore]

Moduli e responsabilità → (nuove righe, dopo quelle di src/shk/market/divergence.py) →
src/shk/model/__init__.py — sola docstring di modulo in italiano [V, R11@2026-09-29b]
src/shk/model/elo.py — funzioni pure, nessun RNG e nessun accesso ai dati:
- elo_delta(r_home, r_away, h=0.0) → float, solo scalari;
- expected_score(delta, s=400.0), E = 1/(1 + 10^(−delta/s));
- elo_update(r_home, r_away, outcome, k, h=0.0, s=400.0) → (R_casa', R_trasferta'), con S = 1, 0.5, 0 per H, D, A;
- davidson_probabilities(delta, nu, s=400.0) → (p_home, p_draw, p_away);
- constant_draw_probabilities(delta, c, s=400.0) → (p_home, p_draw, p_away).
Uno scalare reale in ingresso dà float; qualunque ndarray, anche 0-d, dà ndarray float64 della stessa forma [V, R11@2026-09-29b per i test verdi; D per le firme esatte e per l'uso di elo_delta ed expected_score dentro elo_update]
src/shk/model/elo.py — validazioni: TypeError per bool, np.bool_, non numerici, liste, stringhe, ndarray bool o complessi; ValueError per valori non finiti, ν ≤ 0, c fuori da (0, 1), s ≤ 0, k < 0, outcome fuori da H, D, A; k = 0 ammesso [V, R11@2026-09-29b, test verdi]
src/shk/model/elo.py — calcolo di E e di Davidson: il ramo ndarray usa np.power senza guardie (righe 164-166 e 282-288); il ramo scalare usa math.pow con guardie per |delta/s| > 308, che restituiscono 0 o 1 e p_draw = 0 (righe 169-174 e 291-299) [V, R12@2026-09-29b]. I due rami divergono solo per |delta/s| > 308, fuori da ogni valore realistico [D]

Moduli e responsabilità → "tests/ — 17 moduli: test_kelly_core, …, test_us_c3_2_acceptance [V, R1@2026-09-29b]" →
tests/ — 18 moduli: test_kelly_core, test_simulate, test_estimation, test_staking, test_metrics, test_anova, test_timeseries, test_calibration, test_data_loading, test_coverage, test_split, test_devig, test_leakage, test_elo, test_us_c1_1_acceptance, test_us_c1_2_acceptance, test_us_c2_acceptance, test_us_c3_2_acceptance [V, R1@2026-09-29b e R11@2026-09-29b]

Moduli e responsabilità → (nuova riga, dopo quella di tests/test_us_c3_2_acceptance.py) →
tests/test_elo.py — 31 test veloci:
- somma zero; somma a 1 e probabilità in (0, 1) su delta in [−800, 800] con ν in [0.05, 3] e c in [0.01, 0.99];
- tabella delle note 2.8 §3.3 con s = 200 (24 valori come costanti, tolleranza 5e-4); simmetria; p_draw monotono su entrambi i lati; limite ν = 1e-12; p_draw == c esatto;
- validazioni; k = 0.
[V, R11@2026-09-29b]

Flussi principali → (nuova riga, dopo "Walk-forward anti-leakage, …") →
Modulo 1 Elo (T20): la tabella Davidson delle note 2.8 §3.3 si riproduce con s = 200 (scarto massimo 4.418e-4, a delta = 100, ν = 1.1, p_away); con s = 400 lo scarto sarebbe 0.20. Con ν = 1e-12, max |p_home − E| = 3.2485e-13 su 1601 punti in [−800, 800], pari al valore teorico ν·max r^1.5/(r + 1)² ≈ 0.325·ν. Somme a 1 entro 2.2e-16 per entrambi i mapping [V, R13@2026-09-29b e ricalcolo del supervisore]

Convenzioni da rispettare → "- file di S3: [V, R14, R26, R32, R43 e R46@2026-09-29]." →
- file di S3: [V, R14, R26, R32, R43 e R46@2026-09-29];
- file di S4: src/shk/model/ [V, R11@2026-09-29b, Select-String].

Punti ancora incerti → "Esito della CI su main dopo 90a77a1 (pandas più recente, test S3 sintetici) e stato della suite veloce su 90a77a1: non verificati. Blocca: la baseline del prossimo task di scrittura, che deve partire da una suite verde. Si procede facendo cominciare il prossimo task con l'esecuzione della suite veloce." →
Esito della CI dopo 90a77a1 (pandas più recente, test S3 sintetici): non verificato. La suite veloce locale è verde su quel codice (181, R11@2026-09-29b). Non blocca i task; da controllare al primo push del branch C4.

Ultimo aggiornamento → "R6@2026-09-29b — task di scrittura chiusi dopo la mappa del 2026-09-29b: nessuno" →
R14@2026-09-29b — task di scrittura chiusi dopo la mappa del 2026-09-29b: T20

-------

Stato repo → "Dopo la mappa: branch C4 creato da 90a77a1 con due commit solo su .agent/ (…). A inizio T20 HEAD su C4 a 475f65f, working tree pulito [V, R7 e R11@2026-09-29b]. Dopo T20 il working tree contiene, non committati, src/shk/model/__init__.py, src/shk/model/elo.py, tests/test_elo.py, .agent/report/T20.md [D]" →
Dopo la mappa: branch C4 creato da 90a77a1 con due commit solo su .agent/ (4b9e6c1 "Refresh C3 project documentation", 475f65f "Update BACKLOG.md") [V, R7 e R11@2026-09-29b]. Commit del programmatore per T20: 7f8e928 "Add Elo rating model and 1X2 mappings". A inizio T21 HEAD su C4 a 7f8e928, working tree pulito [V, R15@2026-09-29b]. Dopo T21 il working tree contiene, non committati, src/shk/model/elo_predictor.py, tests/test_elo_predictor.py, .agent/report/T21.md [D]

Stack e comandi → "… Dopo T20: 212 verdi (più 31 di test_elo.py), 14 deselezionati, 13.92 s [V, R11@2026-09-29b]" →
… Dopo T20: 212 verdi (più 31 di test_elo.py), 14 deselezionati, 13.92 s [V, R11@2026-09-29b]. Dopo T21: 220 verdi (più 8 di test_elo_predictor.py), 14 deselezionati, 28.48 s; tests/test_elo_predictor.py da solo 13.52 s, con i dati locali presenti [V, R21@2026-09-29b]

Moduli e responsabilità → "src/shk/ contiene 17 moduli applicativi (6 in kelly, 4 in stats, 4 in data, 2 in market, 1 in model) più 6 __init__.py […]" →
src/shk/ contiene 18 moduli applicativi (6 in kelly, 4 in stats, 4 in data, 2 in market, 2 in model) più 6 __init__.py [V, R1@2026-09-29b, R11 e R19@2026-09-29b; conteggio ricalcolato dal supervisore]

Moduli e responsabilità → "src/shk/model/elo.py — funzioni pure, … [V, R11@2026-09-29b per i test verdi; D per le firme esatte e per l'uso di elo_delta ed expected_score dentro elo_update]" →
(stesso testo fino a "della stessa forma", poi) [V, R11@2026-09-29b per i test verdi; firme e tipi restituiti V, R16@2026-09-29b; elo_update calcola delta con elo_delta ed E con expected_score, righe 228-230, seguite da assert isinstance(e, float), V, R17@2026-09-29b]

Moduli e responsabilità → (nuove righe, dopo quelle di src/shk/model/elo.py) →
src/shk/model/elo_predictor.py — funzioni pubbliche:
- compute_season_standings(df) → DataFrame ordinato con almeno team, points, goal_diff, goals_for;
- predict_elo_walkforward(df, seasons_to_predict, k, h, nu, s=400.0, initial_rating=1500.0) e predict_elo_fast con la stessa firma → DataFrame con season, Date, HomeTeam, AwayTeam, rating_home, rating_away, delta, p_home, p_draw, p_away, home_promotion, away_promotion;
- diagnose_season_transitions(df) → DataFrame con una riga per stagione dalla seconda: season, n_teams, n_promoted_new, promoted_new, n_promoted_returning, promoted_returning, promoted_total, n_relegated_actual, relegated_actual, relegated_calculated, relegation_agreement.
[V, R19–R21@2026-09-29b per l'uso; D per le firme esatte, prese dal piano approvato]
src/shk/model/elo_predictor.py — parti interne: _EloTracker (consume_match, predict_match, _ensure_season), condiviso dai due percorsi; _get_field, _validate_inputs, _parse_season_start_year; _CALC_COLS = Date, season, HomeTeam, AwayTeam, FTR, FTHG, FTAG [V, R21@2026-09-29b]
src/shk/model/elo_predictor.py — regola di ingresso: alla prima riga di s si congelano la classifica di s − 1 e la media dei rating finali delle sue ultime tre. Ogni squadra riceve rating e stato alla sua prima comparsa in s, una sola volta. Nella prima stagione del DataFrame tutte le squadre partono da initial_rating con stato "" [D, piano approvato; coperta da test verdi, R19@2026-09-29b]
src/shk/model/elo_predictor.py — validazioni: ValueError per FTR fuori da H, D, A, colonne mancanti (Date, season, HomeTeam, AwayTeam, FTHG, FTAG), stagioni non consecutive, stagione decrescente lungo Date, df non ordinato, parametri non validi; TypeError per tipi sbagliati e per seasons_to_predict str [V, R19@2026-09-29b, test verdi]
src/shk/model/elo_predictor.py — percorsi:
- via fornitore: chiama assert_no_leakage su ogni coppia e consuma la storia nuova proiettata su _CALC_COLS;
- veloce: una passata con itertools.groupby per Date su df[_CALC_COLS].itertuples; le partite di una data si prevedono prima di aggiornare con quella data.
Sui dati reali i due percorsi danno CSV identici byte per byte: SHA256 0b3048a7a170e7e149f6cb96c2790e36d3f05010a4d5ce35e1ea0febc1fcbce1 con K = 20, h = 60, ν = 1 [V, R21@2026-09-29b]

Moduli e responsabilità → "tests/ — 18 moduli: … test_elo, … [V, R1@2026-09-29b e R11@2026-09-29b]" →
tests/ — 19 moduli: test_kelly_core, test_simulate, test_estimation, test_staking, test_metrics, test_anova, test_timeseries, test_calibration, test_data_loading, test_coverage, test_split, test_devig, test_leakage, test_elo, test_elo_predictor, test_us_c1_1_acceptance, test_us_c1_2_acceptance, test_us_c2_acceptance, test_us_c3_2_acceptance [V, R1, R11 e R19@2026-09-29b]

Moduli e responsabilità → (nuova riga, dopo quella di tests/test_elo.py) →
tests/test_elo_predictor.py — 8 test veloci:
- invarianza al futuro: una sola funzione di controllo, verify_future_invariance (righe 92-147), applicata al percorso via fornitore, al percorso veloce e al mutante predict_elo_mutant_update_before_predict; date di taglio 2001-08-18, 2001-08-25, 2002-08-17;
- invarianza alle quote; regola delle neopromosse calcolata a mano; equivalenza fra i due percorsi su dati sintetici e reali (i reali si saltano senza CSV); transizioni sui dati reali; validazioni; determinismo.
Costanti di test: K = 20, h = 60, ν = 1, s = 400, rating iniziale 1500.
[V, R20@2026-09-29b; costanti dal piano, D]

Moduli e responsabilità → "Classi del pacchetto: Scenario, StakingMoments, OneWayAnovaResult, RejectionResult, PhiStreams, ColumnClassification, SplitConfig, TestSetLockedError, LeakageError [V, R1@2026-09-29b]; nessun'altra [D]" →
Classi del pacchetto: Scenario, StakingMoments, OneWayAnovaResult, RejectionResult, PhiStreams, ColumnClassification, SplitConfig, TestSetLockedError, LeakageError [V, R1@2026-09-29b], più la classe interna _EloTracker di src/shk/model/elo_predictor.py [V, R21@2026-09-29b]; nessun'altra [D]

Flussi principali → (nuove righe, dopo quella del Modulo 1 Elo di T20) →
Transizioni reali dal 1993-94 al 2022-23 (29) [V, R21@2026-09-29b; somme del supervisore dallo stdout]:
- 22 squadre nel 1993-94 e nel 1994-95, 20 dopo;
- entrate 86: 28 nuove, 58 tornanti. Ne entrano 2 al 1995-96 e 3 alle altre transizioni; ne escono 4 al 1995-96 e 3 alle altre;
- nomi squadra coerenti fra stagioni secondo questo criterio.
Accordo fra ultime tre calcolate e uscite effettive: 3 in ogni transizione tranne il 1997-98, dove vale 2. Classifica 1996-97 calcolata dai risultati: Everton 42, Southampton 41 (−6), Coventry 41 (−16), Sunderland 40 (−18), Nott'm Forest 34 (−28); il Middlesbrough non è fra le ultime tre. Le penalizzazioni non sono nei dati [V, R20@2026-09-29b]
Tempi del previsore Elo sui dati reali (8 360 partite previste): percorso veloce 0.35 s, via fornitore 10.58 s. Prima del secondo correttivo di T21 erano 31.71 s e 30.31 s; il profilo attribuiva 68.7 dei 72 s profilati a itertuples su tutte le colonne, 3 199 volte [V, R20 e R21@2026-09-29b]

Convenzioni da rispettare → "- file di S4: src/shk/model/ [V, R11@2026-09-29b, Select-String]." →
- file di S4: src/shk/model/elo.py [V, R11@2026-09-29b, Select-String]; src/shk/model/elo_predictor.py [V, R19@2026-09-29b, prima del secondo correttivo di T21; D dopo].

Zone fragili da non toccare senza avviso → (nuova riga, in fondo) →
I due percorsi di src/shk/model/elo_predictor.py iterano solo sulle colonne di _CALC_COLS: un calcolo che usa un'altra colonna deve aggiungerla a _CALC_COLS [D]. Dopo ogni modifica al file, il confronto dello SHA256 delle previsioni con 0b3048a7…cbce1 (K = 20, h = 60, ν = 1) mostra se l'output è cambiato [V, R21@2026-09-29b]

Ultimo aggiornamento → "R14@2026-09-29b — task di scrittura chiusi dopo la mappa del 2026-09-29b: T20" →
R21@2026-09-29b — task di scrittura chiusi dopo la mappa del 2026-09-29b: T20, T21


---

Stato repo → "… Commit del programmatore per T20: 7f8e928 "Add Elo rating model and 1X2 mappings". A inizio T21 HEAD su C4 a 7f8e928, working tree pulito [V, R15@2026-09-29b]. Dopo T21 il working tree contiene, non committati, src/shk/model/elo_predictor.py, tests/test_elo_predictor.py, .agent/report/T21.md [D]" →
… Commit del programmatore: 7f8e928 "Add Elo rating model and 1X2 mappings" (T20), 4710045 "Add Elo walk-forward predictor and tests" (T21). A inizio T22 HEAD su C4 a 4710045, working tree pulito [V, R22@2026-09-29b]. Dopo T22 il working tree contiene, non committati, src/shk/model/elo_fit.py, scripts/us_c4_1_elo_walkforward.py, tests/test_us_c4_1_acceptance.py, results/us_c4_1_elo_walkforward.csv, thesis/figures/us_c4_1_elo_walkforward.png, .agent/report/T22.md [D]

Stack e comandi → "… Dopo T21: 220 verdi (più 8 di test_elo_predictor.py), 14 deselezionati, 28.48 s; tests/test_elo_predictor.py da solo 13.52 s, con i dati locali presenti [V, R21@2026-09-29b]" →
… Dopo T21: 220 verdi (più 8 di test_elo_predictor.py), 14 deselezionati, 28.48 s; tests/test_elo_predictor.py da solo 13.52 s, con i dati locali presenti [V, R21@2026-09-29b]. Dopo T22: 226 verdi (più 6 di test_us_c4_1_acceptance.py), 15 deselezionati, 33.56 s [V, R23@2026-09-29b]

Stack e comandi → "Test slow: 14 (9 di C1, 5 di C2). Ultimo esito: 13 verdi e 1 rosso per il risultato noto test_acceptance_calibrated_phi_zero_within_mc_interval; pytest -m slow dura circa 117 s [V, R14@2026-09-28; non rieseguiti dopo]" →
Test slow: 15 (9 di C1, 5 di C2, 1 di C4). I 14 di C1 e C2 all'ultimo esito: 13 verdi e 1 rosso per il risultato noto test_acceptance_calibrated_phi_zero_within_mc_interval, circa 117 s [V, R14@2026-09-28; non rieseguiti dopo]. Quello di C4, test_elo_fits_matches_data_recalibration, è verde in 119.09 s [V, R23@2026-09-29b]

Stack e comandi → (nuova riga, dopo "Esperimento C3.2: …") →
Esperimento C4.1: .\.venv\Scripts\python.exe scripts/us_c4_1_elo_walkforward.py dalla radice, con data/raw/E0/ presente, circa 49 s. Due esecuzioni danno CSV identici, SHA256 92716bc7e6aa6a7b798370a09d1b31b33b0c0a49311bf35cd810f7975489f282 [V, R23@2026-09-29b]

Moduli e responsabilità → "src/shk/ contiene 18 moduli applicativi (6 in kelly, 4 in stats, 4 in data, 2 in market, 2 in model) più 6 __init__.py […]" →
src/shk/ contiene 19 moduli applicativi (6 in kelly, 4 in stats, 4 in data, 2 in market, 3 in model) più 6 __init__.py [V, R1@2026-09-29b, R11, R19 e R23@2026-09-29b; conteggio ricalcolato dal supervisore]

Moduli e responsabilità → (nuove righe, dopo quelle di src/shk/model/elo_predictor.py) →
src/shk/model/elo_fit.py — funzioni:
- derive_fit_schedule(cfg) → dict dalla stagione del fit a {"training": […], "validation": […]}, derivato da SplitConfig;
- calibrate_all_fits(df, schedule) → dict dalla stagione del fit a un risultato con success, message, nit, nfev, duration_seconds, k, h, nu, c, log_loss_train, log_loss_train_baseline, n_train_matches, is_on_boundary;
- parse_season_start_year, pubblica: duplica _parse_season_start_year di elo_predictor.py.
Tipi e costanti: EloFitParams (NamedTuple: k, h, nu, c); ELO_FITS; WALKFORWARD_CSV_COLUMNS (15 colonne); limiti, punto iniziale e opzioni di Nelder-Mead; griglie dei profili.
[V, R23@2026-09-29b per l'uso; D per le firme esatte e per i nomi delle costanti non citati nei comandi]
src/shk/model/elo_fit.py — ELO_FITS, congelato il 2026-09-29 [V, R23@2026-09-29b; coincide con la ricalibrazione entro rel_tol 1e-9]:
- "2000-01": K = 10.318224689650037, h = 125.54022316884253, ν = 0.8062246331085681, c = 0.2657894736842105;
- "2010-11": K = 9.934776455088759, h = 127.87791672140764, ν = 0.8775613268630023, c = 0.2789473684210526;
- "2020-21": K = 7.928543266007228, h = 78.033626101627, ν = 0.7603760315281511, c = 0.25877192982456143.
scripts/us_c4_1_elo_walkforward.py — run_experiment(): dati solo con load_by_role; CSV di 9 500 righe e 15 colonne (per fit: prima training, poi validation); PNG a due pannelli con i profili della log-loss di training in K e in h, calcolati da ELO_FITS [V, R23@2026-09-29b; D per i dettagli]

Moduli e responsabilità → "tests/ — 19 moduli: … test_elo_predictor, test_us_c1_1_acceptance, … [V, R1, R11 e R19@2026-09-29b]" →
tests/ — 20 moduli: test_kelly_core, test_simulate, test_estimation, test_staking, test_metrics, test_anova, test_timeseries, test_calibration, test_data_loading, test_coverage, test_split, test_devig, test_leakage, test_elo, test_elo_predictor, test_us_c1_1_acceptance, test_us_c1_2_acceptance, test_us_c2_acceptance, test_us_c3_2_acceptance, test_us_c4_1_acceptance [V, R1, R11, R19 e R23@2026-09-29b]

Moduli e responsabilità → (nuova riga, dopo quella di tests/test_elo_predictor.py) →
tests/test_us_c4_1_acceptance.py — 7 test:
- veloci: test_calibration_training_only_synthetic, test_calibration_objective_matches_count_real_data, test_csv_validation_leakage_and_uniqueness, test_versioned_csv_schema_and_probabilities, test_recomputed_predictions_match_csv;
- slow: test_elo_fits_matches_data_recalibration (119.09 s).
I test sui dati reali si saltano senza CSV; nessun test esegue lo script.
[V, R23@2026-09-29b]

Moduli e responsabilità → "Classi del pacchetto: … più la classe interna _EloTracker di src/shk/model/elo_predictor.py [V, R21@2026-09-29b]; nessun'altra [D]" →
Classi del pacchetto: Scenario, StakingMoments, OneWayAnovaResult, RejectionResult, PhiStreams, ColumnClassification, SplitConfig, TestSetLockedError, LeakageError [V, R1@2026-09-29b], EloFitParams [V, R23@2026-09-29b], più la classe interna _EloTracker di src/shk/model/elo_predictor.py [V, R21@2026-09-29b]; nessun'altra [D]

Flussi principali → (nuove righe, dopo quelle del previsore Elo di T21) →
Esperimento C4.1, calibrazione espansiva Nelder-Mead [V, R23@2026-09-29b; c e durate ricalcolati dal supervisore]:
- tutti i fit con success = True, nessun parametro su un limite;
- nit/nfev 103/185, 158/284, 107/194; durate 14.80, 49.59, 52.54 s, in tutto 116.93 s;
- partite di training 380, 760, 1 140; pareggi 101, 212, 295, cioè 111 nel 2010-11 e 83 nel 2020-21.
Esperimento C4.1, log-loss (Davidson / baseline a pareggio costante) [V, R23@2026-09-29b]:
- fit 2000-01: training 1.008189 / 1.014931; validazione (3 040 partite) 0.973761 / 0.976755;
- fit 2010-11: training 1.008987 / 1.015189; validazione (3 420) 0.983832 / 0.990144;
- fit 2020-21: training 1.020937 / 1.024782; validazione (760) 0.983300 / 0.987629.
Frequenza del pareggio in validazione: 0.255263, 0.241228, 0.230263.
Media dei rating a inizio stagione, con i parametri di ciascun fit: 1500 nel 1993-94 e nel 1994-95; dal 1995-96 fra 1502.3 e 1524.9, con il massimo nel 2022-23 [V, R23@2026-09-29b; tabella in .agent/report/T22.md]

Convenzioni da rispettare → "Parametri condivisi fra script e test in un modulo di libreria importato da entrambi: scenarios.py per C1.2, false_rejection.py per C2, coverage.py e divergence.py (con split.toml) per C3. C1.1 è l'eccezione storica [V, R1@2026-09-29b]" →
Parametri condivisi fra script e test in un modulo di libreria importato da entrambi: scenarios.py per C1.2, false_rejection.py per C2, coverage.py e divergence.py (con split.toml) per C3, elo_fit.py per C4.1. C1.1 è l'eccezione storica [V, R1@2026-09-29b e R23@2026-09-29b]

Convenzioni da rispettare → "- file di S4: src/shk/model/elo.py [V, R11@2026-09-29b, Select-String]; src/shk/model/elo_predictor.py [V, R19@2026-09-29b, prima del secondo correttivo di T21; D dopo]." →
- file di S4: src/shk/model/elo.py [V, R11@2026-09-29b, Select-String]; src/shk/model/elo_predictor.py [V, R19@2026-09-29b, prima del secondo correttivo di T21; D dopo]; src/shk/model/elo_fit.py [V, R23@2026-09-29b, Select-String].

Zone fragili da non toccare senza avviso → (nuove righe, in fondo) →
ELO_FITS in src/shk/model/elo_fit.py è congelato e non si modifica: T23 e T24 lo vietano esplicitamente. Una modifica a elo.py o elo_predictor.py che cambia le previsioni rende ELO_FITS e results/us_c4_1_elo_walkforward.csv incoerenti col codice: vanno ricalibrati e rigenerati, e lo segnalano test_recomputed_predictions_match_csv (in locale) e il test slow di ricalibrazione [D]
Rieseguire scripts/us_c4_1_elo_walkforward.py sovrascrive CSV e PNG versionati; dura circa 49 s [V, R23@2026-09-29b]

Ultimo aggiornamento → "R21@2026-09-29b — task di scrittura chiusi dopo la mappa del 2026-09-29b: T20, T21" →
R23@2026-09-29b — task di scrittura chiusi dopo la mappa del 2026-09-29b: T20, T21, T22