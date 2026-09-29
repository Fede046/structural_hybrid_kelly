Mappa completa — 2026-09-29 — R1

### 0. Stato del repository

* Percorso assoluto della radice: `c:\Users\malse\Documents\GitHub\structural_hybrid_kelly` `[V]`.
* Branch corrente: `main` `[V]`.
* Stato del working tree: sporco `[V]`.
* File modificati non staged:
  * `.agent/BACKLOG.md` (modificato con l'inserimento della pianificazione della Story S3 / C3: 341 inserimenti, 2 cancellazioni) `[V]`.
* File modificati staged: nessuno `[V]`.
* File non tracciati: nessuno `[V]`.
* File ignorati rilevati nel filesystem locale: `.pytest_cache/`, `.venv/`, `src/shk/__pycache__/`, `src/shk/kelly/__pycache__/`, `src/shk/stats/__pycache__/`, `tests/__pycache__/` `[V]`.
* Ultimi cinque commit in forma breve (dalla storia di Git su branch `main`):
  * `115e600` `C2 (#16)` `[V]`
  * `1e7813d` `C1 (#14)` `[V]`
  * `640b906` `C1 (#13)` `[V]`
  * `a7420cb` `create c1 (#5)` `[V]`
  * `6187309` `Feature/us c1.1 trade off crescita/varianza (#4)` `[V]`
* Remote configurati:
  * `origin`: `https://github.com/Fede046/structural_hybrid_kelly.git` (fetch) `[V]`
  * `origin`: `https://github.com/Fede046/structural_hybrid_kelly.git` (push) `[V]`
* Allineamento rispetto al remote: `main` è allineato a `origin/main` (up to date, 0 commit avanti, 0 commit indietro rispetto all'ultimo fetch locale) `[V]`.
* Altri branch locali: nessuno (è presente solo `main`) `[V]`.
* Branch remoti: `origin/HEAD -> origin/main`, `origin/main` `[V]`.

### 1. Identikit

* Nome del progetto: `structural-hybrid-kelly` `[V]`.
* Descrizione: Libreria scientifica e ambiente di simulazione per l'analisi analitica e stocastica del criterio di Kelly e dei modelli ibridi strutturali `[V]`. Modella strategie di scommessa e investimento, valutando il trade-off crescita/varianza, l'errore di stima e la robustezza dell'inferenza statistica (ANOVA, autocorrelazione, block bootstrap) `[V]`.
* Stack: Python `[V]`.
* Linguaggi: Python 3 `[V]`.
* Versioni:
  * Versione Python minima supportata: `>=3.11` (specificata in `pyproject.toml`) `[V]`.
  * Versione Python impiegata nella CI: `3.12` (specificata in `.github/workflows/test.yml`) `[V]`.
  * Versione del pacchetto: `0.1.0` (dichiarata in `pyproject.toml` e in `src/shk/__init__.py`) `[V]`.
* Gestore di pacchetti: `uv` (attestato dalla presenza del lockfile `uv.lock` alla radice) `[V]`, con `pip` impiegato nel workflow di CI `[V]`.
* Build system: Hatchling (`hatchling.build` specificato in `pyproject.toml`) `[V]`.

### 2. Come si esegue

* Installazione delle dipendenze:
  * Tramite pip (attestato nel workflow CI `.github/workflows/test.yml`): `pip install -e ".[dev]"` `[V]`.
  * Tramite pip in ambiente locale: `pip install -e ".[dev]"` `[D]`.
  * Tramite uv: `uv sync` `[D]`.
* Avvio in sviluppo:
  * Nessun server interattivo né processo daemon presente `[V]`.
  * Installazione del pacchetto in modalità editabile: `pip install -e .` `[D]`.
* Build del pacchetto:
  * Tramite Hatch: `hatch build` `[D]`.
  * Tramite modulo build di Python: `python -m build` `[D]`.
* Lancio dei test:
  * Test veloci (suite predefinita, esclude i test slow tramite `addopts = "-m 'not slow'"` in `pyproject.toml`): `pytest -v` `[V]`.
  * Test veloci tramite interprete del virtual environment locale: `.\.venv\Scripts\python.exe -m pytest -v` `[D]`.
  * Solo test lenti di accettazione Monte Carlo: `pytest -m slow` `[D]`.
  * Esecuzione completa di tutti i test (inclusi i test slow): `pytest -o addopts=""` `[D]`.
* Esecuzione degli script di simulazione ed esperimento:
  * Esperimento US-C1.1 (trade-off crescita/varianza vs lambda): `python scripts/us_c1_1_growth_vs_lambda.py` `[D]`.
  * Esperimento US-C1.2 (errore di stima e confronto regole): `python scripts/us_c1_2_estimation_error.py` `[D]`.
  * Esperimento US-C2.2 e US-C2.3 (falso rigetto ANOVA e calibrazione block bootstrap): `python scripts/us_c2_anova_autocorrelation.py` `[D]`.
  * Esecuzione tramite l'interprete del virtual environment locale: `.\.venv\Scripts\python.exe scripts\us_c2_anova_autocorrelation.py` `[D]`.
* Variabili d'ambiente richieste:
  * Nessuna variabile d'ambiente richiesta nei file di configurazione `[V]`.
  * Nessuna variabile d'ambiente letta nel codice sorgente di `src/` o negli script di `scripts/` `[V]`.
* File di configurazione richiesti:
  * `pyproject.toml` (configurazione del pacchetto, metadati, dipendenze, target di build e marker pytest) `[V]`.
  * Nessun file `.env` presente o richiesto `[V]`.
  * La directory `config/` contiene unicamente il file placeholder `.gitkeep` `[V]`.
  * Il file `config/split.toml` non esiste nel filesystem `[V]`.
  * La directory `data/raw/` contiene unicamente il file placeholder `.gitkeep` `[V]`.
  * La directory `data/raw/E0/` non esiste nel filesystem `[V]`.

### 3. Albero delle directory

* `.` (radice): File di configurazione di progetto (`pyproject.toml`, `uv.lock`, `.gitignore`, `LICENSE`) `[V]`.
* `.agent/`: Documentazione di processo, tracciamento del backlog (`BACKLOG.md`), protocollo operativo (`PROTOCOLLO.md`), scheda tecnica (`SCHEDA.md`) e mappa architetturale (`MAPPA.md`) `[V]`.
* `.agent/report/`: Report formali di chiusura dei task implementativi completati da T1 a T13 (`T1.md` ... `T13.md`) `[V]`.
* `.github/workflows/`: Pipeline di integrazione continua GitHub Actions per l'esecuzione automatizzata dei test (`test.yml`) `[V]`.
* `config/`: Directory destinata ai file di configurazione congelati (attualmente contiene unicamente `.gitkeep`) `[V]`.
* `data/raw/`: Directory destinata allo storage dei dataset storici grezzi (attualmente contiene unicamente `.gitkeep`) `[V]`.
* `results/`: Directory di destinazione dei file tabellari CSV generati dagli script di simulazione (`.gitkeep`, `us_c1_1_growth_vs_lambda.csv`, `us_c1_2_estimation_error.csv`, `us_c2_anova_autocorrelation.csv`) `[V]`.
* `scripts/`: Script Python eseguibili per la conduzione degli esperimenti Monte Carlo e la generazione delle figure di tesi `[V]`.
* `src/shk/`: Radice del codice sorgente del pacchetto Python `shk` `[V]`.
* `src/shk/kelly/`: Sottopacchetto dedicato alle formule analitiche, al motore di simulazione, ai modelli di rumore di stima, alle regole di staking e agli scenari per il criterio di Kelly `[V]`.
* `src/shk/stats/`: Sottopacchetto dedicato all'analisi statistica, all'ANOVA a una via (singola e vettorizzata), alla generazione di serie temporali AR(1) e alla calibrazione della soglia per moving block bootstrap `[V]`.
* `tests/`: Suite completa di test unitari, test di conformità statistica e test di accettazione Monte Carlo basati su pytest `[V]`.
* `thesis/figures/`: Directory per le figure PNG ad alta risoluzione generate dagli script per la tesi (`.gitkeep`, `us_c1_1_growth_vs_lambda.png`, `us_c1_2_estimation_error.png`, `us_c2_anova_autocorrelation.png`) `[V]`.

### 4. Moduli principali

Il progetto include 10 moduli Python applicativi principali in `src/shk/`. Sono esclusi da questo elenco e dichiarati:
* Moduli di inizializzazione package esclusi: `src/shk/__init__.py` (espone solo `__version__`), `src/shk/kelly/__init__.py` (re-esporta `kelly_fraction` e `log_growth_rate`), `src/shk/stats/__init__.py` (contiene solo la docstring del sottopacchetto) `[V]`.
* Script esclusi: `scripts/us_c1_1_growth_vs_lambda.py`, `scripts/us_c1_2_estimation_error.py`, `scripts/us_c2_anova_autocorrelation.py` (script di conduzione esperimenti, descritti nella Sezione 5) `[V]`.
* Suite di test esclusa: tutti gli 11 moduli di test in `tests/` (dettagliati nella Sezione 8) `[V]`.

I 10 moduli principali:

1. `src/shk/kelly/core.py`
   * Responsabilità: Fornisce le formule analitiche esatte in forma chiusa per il criterio di Kelly, la crescita logaritmica attesa e il capitale finale atteso su scommesse binarie `[V]`.
   * Espone: `kelly_fraction(p, b)`, `log_growth_rate(f, p, b)`, `expected_final_wealth(f, p, b, T, b0=1.0)` `[V]`.
   * Dipendenze interne: Nessuna `[V]`.

2. `src/shk/kelly/simulate.py`
   * Responsabilità: Esegue l'estrazione bernoulliana di esiti e simula in modo vettorizzato l'evoluzione temporale del log-wealth supportando frazioni broadcastabili `[V]`.
   * Espone: `draw_outcomes(p, T, M, rng)`, `simulate_growth(outcomes, fractions, b)`, `log_wealth_paths(outcomes, f, b)` `[V]`.
   * Dipendenze interne: Nessuna `[V]`.

3. `src/shk/kelly/estimation.py`
   * Responsabilità: Modella perturbazioni deterministiche relative e rumore di stima gaussiano con saturazione vincolata in [0, 1] `[V]`.
   * Espone: `relative_perturbation(p, delta)`, `noisy_estimates(p, sigma_p, T, M, rng)` `[V]`.
   * Dipendenze interne: Nessuna `[V]`.

4. `src/shk/kelly/staking.py`
   * Responsabilità: Implementa il calcolo delle frazioni di puntata con moltiplicatore di Kelly, la regola plug-in adattiva e i momenti empirici di staking `[V]`.
   * Espone: `kelly_staking(p_hat, b, lam=1.0)`, `StakingMoments` (NamedTuple), `staking_moments(f_hat, f_star)`, `plugin_staking(p_hat, b, sigma_p)` `[V]`.
   * Dipendenze interne: Nessuna `[V]`.

5. `src/shk/kelly/scenarios.py`
   * Responsabilità: Centralizza la configurazione immutabile degli scenari Kelly, la riproducibilità dei generatori casuali e l'orchestrazione del workflow di simulazione `[V]`.
   * Espone: `Scenario` (dataclass frozen), `BASE_SCENARIO`, `SUBTLE_SCENARIO`, `SEED`, `spawn_generators(seed=SEED)`, `draw_scenario_outcomes(scenario, rng)`, `simulate_scenario(scenario, outcomes, p_hat, lam=1.0)` `[V]`.
   * Dipendenze interne: `src/shk/kelly/simulate.py`, `src/shk/kelly/staking.py` `[V]`.

6. `src/shk/kelly/metrics.py`
   * Responsabilità: Calcola metriche empiriche di rendimento e indicatori di rischio (tasso di crescita mediano, capitale finale mediano/medio, massimo drawdown, frequenza di perdita) su matrici di log-wealth `[V]`.
   * Espone: `final_log_wealth(paths)`, `median_growth_rate(paths)`, `median_final_wealth(paths)`, `mean_final_wealth(paths)`, `max_drawdown(paths)`, `fraction_below_start(paths)` `[V]`.
   * Dipendenze interne: Nessuna `[V]`.

7. `src/shk/stats/anova.py`
   * Responsabilità: Implementa il calcolo esatto dell'ANOVA a una via per singoli gruppi e in modalità multidimensionale vettorizzata su collezioni di serie temporali `[V]`.
   * Espone: `OneWayAnovaResult` (NamedTuple), `oneway_anova(groups)`, `oneway_anova_vectorized(values, labels)` `[V]`.
   * Dipendenze interne: Nessuna `[V]`.

8. `src/shk/stats/timeseries.py`
   * Responsabilità: Genera serie temporali stazionarie gaussiane AR(1) con condizione iniziale campionata dalla distribuzione stazionaria e innovazioni vettorizzate `[V]`.
   * Espone: `generate_ar1_series(phi, n, m, rng)` `[V]`.
   * Dipendenze interne: Nessuna `[V]`.

9. `src/shk/stats/calibration.py`
   * Responsabilità: Calcola la soglia critica calibrata di una statistica test mediante moving block bootstrap su dati temporali `[V]`.
   * Espone: `moving_block_indices(n, block_length, n_boot, rng)`, `compute_order_statistic_index(b, alpha)`, `calibrate_threshold(data, statistic, block_length, n_boot, alpha, rng, vectorized=False)` `[V]`.
   * Dipendenze interne: Nessuna `[V]`.

10. `src/shk/stats/false_rejection.py`
    * Responsabilità: Conduce le simulazioni Monte Carlo del tasso di falso rigetto dell'ANOVA su serie AR(1) sia sotto soglia nominale che sotto soglia calibrata per block bootstrap `[V]`.
    * Espone: Costanti di simulazione (`PHI_VALUES`, `N_OBS`, `N_SERIES`, `ALPHA`, `SEED_C2`, `BLOCK_LENGTHS`, `N_BOOT`, `METHOD_NOMINAL`, `METHOD_BLOCK_BOOTSTRAP`, `DESIGN_CONTIGUOUS_2`, `DESIGN_CONTIGUOUS_38`, `DESIGN_RANDOM_2`, `DESIGNS`, `CSV_COLUMNS`), `PhiStreams` (NamedTuple), `RejectionResult` (dataclass frozen con metodo `to_row()`), `critical_value_nominal(k, n_obs, alpha)`, `monte_carlo_interval_99(alpha, n_series)`, `make_design_labels(design, n_obs)`, `spawn_c2_generators(seed)`, `compute_nominal_rejection_rates(seed)`, `compute_calibrated_rejection_rates(seed)` `[V]`.
    * Dipendenze interne: `src/shk/stats/anova.py`, `src/shk/stats/calibration.py`, `src/shk/stats/timeseries.py` `[V]`.

### 5. Punti di ingresso e flussi

Punti di ingresso dell'applicazione:
* Script CLI per l'esperimento C1.1: `python scripts/us_c1_1_growth_vs_lambda.py` `[V]`.
* Script CLI per l'esperimento C1.2: `python scripts/us_c1_2_estimation_error.py` `[V]`.
* Script CLI per gli esperimenti C2.2 e C2.3: `python scripts/us_c2_anova_autocorrelation.py` `[V]`.
* Runner di test automatizzati: `pytest` (o `.\.venv\Scripts\python.exe -m pytest`) `[V]`.
* Utilizzo come libreria modulare: `import shk`, `from shk.kelly import ...`, `from shk.stats import ...` `[V]`.

Esattamente tre flussi principali dell'applicazione:

* Flusso 1 — Simulazione del trade-off crescita/varianza e frazionamento di Kelly (Esperimento US-C1.1):
  1. `scripts/us_c1_1_growth_vs_lambda.py:run_experiment()` calcola la frazione ottimale $f^*$ invocando `kelly_fraction(p, b)` in `src/shk/kelly/core.py` `[V]`.
  2. Genera la matrice di esiti bernoulliani condivisa chiamando `draw_outcomes(p, t_steps, m_trajectories, rng)` in `src/shk/kelly/simulate.py` `[V]`.
  3. Per ciascun $\lambda \in [0.0, 2.5]$ (51 punti):
     a. Calcola le traiettorie di log-wealth invocando `log_wealth_paths(outcomes, f_val, b)` in `src/shk/kelly/simulate.py` (che delega a `simulate_growth`) `[V]`.
     b. Calcola le statistiche empiriche chiamando `median_growth_rate`, `median_final_wealth`, `mean_final_wealth`, `max_drawdown` e `fraction_below_start` in `src/shk/kelly/metrics.py` `[V]`.
     c. Dealloca la matrice delle traiettorie con `del paths` `[V]`.
     d. Calcola i benchmark analitici chiamando `log_growth_rate` ed `expected_final_wealth` in `src/shk/kelly/core.py` `[V]`.
  4. Scrive la tabella dei risultati `results/us_c1_1_growth_vs_lambda.csv` tramite `csv.DictWriter` `[V]`.
  5. Costruisce la figura a tre pannelli con Matplotlib e la esporta in `thesis/figures/us_c1_1_growth_vs_lambda.png` `[V]`.

* Flusso 2 — Simulazione dell'errore di stima e confronto regole di staking (Esperimento US-C1.2):
  1. `scripts/us_c1_2_estimation_error.py:run_experiment()` itera sugli scenari immutabili `BASE_SCENARIO` e `SUBTLE_SCENARIO` definiti in `src/shk/kelly/scenarios.py` `[V]`.
  2. Per ciascuno scenario:
     a. Deriva due generatori casuali indipendenti tramite `spawn_generators(SEED)` in `src/shk/kelly/scenarios.py` `[V]`.
     b. Estrae la matrice di esiti con `draw_scenario_outcomes(scenario, rng_outcomes)` in `src/shk/kelly/scenarios.py` `[V]`.
     c. Per l'errore deterministico ($\pm 10\%$): calcola la probabilità perturbata tramite `relative_perturbation(sc.p, delta)` in `src/shk/kelly/estimation.py`, calcola le traiettorie con `simulate_scenario(sc, outcomes, p_hat, lam=1.0)` in `src/shk/kelly/scenarios.py` (che invoca `kelly_staking` in `src/shk/kelly/staking.py` e `simulate_growth` in `src/shk/kelly/simulate.py`), ed estrae le metriche da `src/shk/kelly/metrics.py` `[V]`.
     d. Per ciascun $\sigma_p \in \{0.015, 0.0283, 0.045\}$: genera stime di probabilità con `noisy_estimates(sc.p, s, sc.T, sc.M, rng_noise)` in `src/shk/kelly/estimation.py`, calcola la frazione base $f̂$ con `kelly_staking(p_hat, sc.b, lam=1.0)` in `src/shk/kelly/staking.py`, ricava i momenti pooled con `staking_moments(f_hat, f_star)` in `src/shk/kelly/staking.py`, e simula e misura le diverse regole (`lambda_star`, `ratio_moments`, `lambda_linear`, `quarter_kelly`, `half_kelly`, `full_kelly`, e la regola plug-in con `plugin_staking` e `simulate_growth`) `[V]`.
  3. Scrive le 46 righe di risultati su `results/us_c1_2_estimation_error.csv` `[V]`.
  4. Genera la figura a due pannelli e la esporta in `thesis/figures/us_c1_2_estimation_error.png` `[V]`.

* Flusso 3 — Simulazione del tasso di falso rigetto dell'ANOVA e calibrazione per block bootstrap (Esperimenti US-C2.2 e US-C2.3):
  1. `scripts/us_c2_anova_autocorrelation.py:run_experiment()` richiama le funzioni orchestratrici `compute_nominal_rejection_rates()` e `compute_calibrated_rejection_rates()` in `src/shk/stats/false_rejection.py` `[V]`.
  2. Per il tasso nominale (`compute_nominal_rejection_rates`):
     a. Inizializza i flussi casuali indipendenti con `spawn_c2_generators(seed=SEED_C2)` `[V]`.
     b. Per ciascun $\phi \in \{0.0, 0.3, 0.5, 0.7\}$ genera 1000 serie AR(1) di lunghezza 380 con `generate_ar1_series` in `src/shk/stats/timeseries.py` `[V]`.
     c. Calcola le etichette di gruppo con `make_design_labels` e valuta le statistiche F in forma vettorizzata con `oneway_anova_vectorized` in `src/shk/stats/anova.py` per i disegni `contiguous_2`, `contiguous_38` e per il controllo casualizzato `random_2` (permutato per serie con `perm_rng`) `[V]`.
     d. Confronta la statistica F con i valori critici nominali da `critical_value_nominal` e determina il numero di rigetti su 1000 serie `[V]`.
  3. Per il tasso calibrato (`compute_calibrated_rejection_rates`):
     a. Riusa le stesse serie generate dal flusso `series_rng` per ciascun $\phi$ garantendo il confronto appaiato `[V]`.
     b. Suddivide il seme bootstrap con `spawn(len(BLOCK_LENGTHS))` ottenendo un generatore per ciascun $L \in \{7, 20, 40\}$ `[V]`.
     c. Per ciascuna delle 1000 serie, calcola la soglia critica calibrata invocando `calibrate_threshold` in `src/shk/stats/calibration.py` (con $B=999$, $\alpha=0.05$, `vectorized=True` e `oneway_anova_vectorized`) `[V]`.
     d. Confronta la F osservata di ciascuna serie con la soglia calibrata specifica di quella serie e conta i rigetti `[V]`.
  4. Scrive le 24 righe risultanti in `results/us_c2_anova_autocorrelation.csv` `[V]`.
  5. Costruisce la figura a due pannelli (pannello A nominale, pannello B calibrato) e la esporta in `thesis/figures/us_c2_anova_autocorrelation.png` `[V]`.

Replicazione e divergenze tra flussi ed esecuzioni di test:
* Flusso 1 vs `tests/test_us_c1_1_acceptance.py`:
  * Replicazione: Entrambi usano i medesimi parametri hardcoded ($p=0.60, b=1.0, T=1000, M=10000$, seed `20260905`, griglia di 51 valori di $\lambda$) `[V]`.
  * Divergenze: Lo script calcola tutte le metriche empiriche e analitiche salvando CSV e PNG su disco; i test calcolano unicamente crescita mediana e massimo drawdown eseguendo asserzioni numeriche in memoria `[V]`. Lo script genera gli esiti una sola volta per tutti i $\lambda$; i test rigenerano gli esiti all'interno di ciascuna singola funzione di test `[V]`.
* Flusso 2 vs `tests/test_us_c1_2_acceptance.py`:
  * Replicazione: Condividono le definizioni di scenario e il seed master `20260927` importandoli da `src/shk/kelly/scenarios.py` `[V]`.
  * Divergenze: Lo script esplora l'intera griglia di parametri ed esporta tabella CSV e grafici; i test di accettazione verificano singoli criteri puntuali (asimmetria sovrastima/sottostima nello scenario sottile, confronto di $\text{Var}(c)$ rispetto a 1, dominanza di $\lambda^*$ su 0.25 a $\sigma_p=0.0283$) `[V]`. I test includono verifiche unitarie di indipendenza degli esiti bernoulliani da $p̂$ e di invarianza della matrice esiti `[V]`.
* Flusso 3 vs `tests/test_us_c2_acceptance.py`:
  * Replicazione: Condividono costanti, definizioni dei disegni, seed `20260928` e funzioni orchestratrici importandoli da `src/shk/stats/false_rejection.py` `[V]`.
  * Divergenze: Lo script genera e sovrascrive direttamente CSV e PNG su disco; i test verificano la corrispondenza campo per campo tra i risultati ricalcolati in memoria e il CSV presente su disco (usando `math.isclose` per i float), e asseriscono proprietà teoriche (gonfiamento dei falsi rigetti da autocorrelazione, monotonicità in $\phi$, indipendenza dei flussi) `[V]`.

### 6. Modello dei dati

* Classi di dominio o dataclass strutturate:
  1. `Scenario` (`src/shk/kelly/scenarios.py`): dataclass congelata (`frozen=True`) che incapsula la tupla dei parametri sperimentali:
     * `name`: `str`, identificativo descrittivo dello scenario `[V]`.
     * `p`: `float`, probabilità reale di successo in $[0, 1]$ `[V]`.
     * `b`: `float`, quota decimale netta strettamente positiva ($b > 0$) `[V]`.
     * `T`: `int`, numero di passi temporali ($T > 0$) `[V]`.
     * `M`: `int`, numero di traiettorie indipendenti ($M > 0$) `[V]`.
     * Istanze predefinite nel modulo: `BASE_SCENARIO` (p=0.60, b=1.0, T=1000, M=10000) e `SUBTLE_SCENARIO` (p=0.52, b=1.0, T=380, M=10000) `[V]`.
  2. `StakingMoments` (`src/shk/kelly/staking.py`): `NamedTuple` contenente i momenti empirici del moltiplicatore normalizzato $c = \hat{f} / f^*$:
     * `mean_c`: `float`, media campionaria pooled $E[c]$ `[V]`.
     * `mean_c2`: `float`, momento secondo campionario pooled $E[c^2]$ `[V]`.
     * `var_c`: `float`, varianza campionaria pooled $\text{Var}(c) = E[c^2] - (E[c])^2$ `[V]`.
     * `fraction_zero`: `float`, quota pooled di puntate con frazione nulla `[V]`.
  3. `OneWayAnovaResult` (`src/shk/stats/anova.py`): `NamedTuple` per l'output dell'ANOVA a una via:
     * `ss_between`: `float`, devianza tra i gruppi `[V]`.
     * `ss_within`: `float`, devianza residua entro i gruppi `[V]`.
     * `ss_total`: `float`, devianza totale `[V]`.
     * `df_between`: `int`, gradi di libertà tra gruppi ($k - 1$) `[V]`.
     * `df_within`: `int`, gradi di libertà entro gruppi ($N - k$) `[V]`.
     * `ms_between`: `float`, quadrato medio tra gruppi `[V]`.
     * `ms_within`: `float`, quadrato medio entro gruppi `[V]`.
     * `f_statistic`: `float`, statistica F di Fisher `[V]`.
     * `p_value`: `float`, p-value associato `[V]`.
  4. `PhiStreams` (`src/shk/stats/false_rejection.py`): `NamedTuple` contenente la terna di flussi casuali per ciascun $\phi$:
     * `series_rng`: `np.random.Generator`, generatore per le serie AR(1) `[V]`.
     * `perm_rng`: `np.random.Generator`, generatore per le permutazioni casuali del disegno random_2 `[V]`.
     * `boot_seed`: `np.random.SeedSequence`, sequenza di semi per il bootstrap, ripartita per ciascun $L$ `[V]`.
  5. `RejectionResult` (`src/shk/stats/false_rejection.py`): dataclass congelata (`frozen=True`) che memorizza il risultato del falso rigetto:
     * `design`: `str`, disegno sperimentale `[V]`.
     * `phi`: `float`, coefficiente autoregressivo `[V]`.
     * `method`: `str`, metodo impiegato ("nominal" o "block_bootstrap") `[V]`.
     * `block_length`: `str`, lunghezza blocco bootstrap ("" per nominale, o valore numerico stringa) `[V]`.
     * `n_series`: `int`, numero di serie simulate (1000) `[V]`.
     * `rejections`: `int`, conteggio dei rigetti `[V]`.
     * `rejection_rate`: `float`, tasso empirico di rigetto `[V]`.
     * `critical_value_mean`: `float`, valore critico nominale o media delle soglie calibrate `[V]`.
     * `mc_lower_99`: `float`, estremo inferiore intervallo Monte Carlo al 99% `[V]`.
     * `mc_upper_99`: `float`, estremo superiore intervallo Monte Carlo al 99% `[V]`.
     * Metodo `to_row()`: restituisce il record come dizionario per la serializzazione CSV `[V]`.
* Strutture dati in circolo:
  1. Matrice di esiti (`outcomes`): `np.ndarray` shape `(M, T)`, `dtype=bool` (`True` = vincita) `[V]`.
  2. Matrice o scalare delle stime (`p_hat`): `np.ndarray` shape `(M, T)` o float, con valori in $[0.0, 1.0]$ `[V]`.
  3. Frazioni di scommessa (`fractions`): scalare float o `np.ndarray` con forme broadcastabili a `(M, T)` (`()`, `(T,)`, `(1, T)`, `(M, 1)`, `(M, T)`), con elementi in $[0.0, 1.0)$ `[V]`.
  4. Matrice delle traiettorie di log-wealth (`paths`): `np.ndarray` shape `(M, T + 1)`, `dtype=float64`, con colonna 0 nulla `[V]`.
  5. Vettori di metriche e drawdown: `final_log_wealth` (`(M,)`), `max_drawdown` (`(M,)` float in $[0.0, 1.0)$) `[V]`.
  6. Matrice delle serie temporali (`series`): `np.ndarray` shape `(m, n)`, `dtype=float64` `[V]`.
  7. Vettore di etichette (`labels`): `np.ndarray` 1D shape `(N,)`, `dtype=int64`, contenente valori in $0..k-1$ tutti presenti `[V]`.
  8. Matrice degli indici di bootstrap (`indices`): `np.ndarray` shape `(n_boot, n)`, `dtype=int64` `[V]`.
  9. Record tabellari: dizionari Python serializzati su file CSV con campi numerici float o stringhe vuote per campi non applicabili `[V]`.
* Schema di persistenza:
  * Nessun database o ORM presente nel codebase `[V]`.
  * Persistenza basata interamente su file flat CSV versionati in Git:
    * `results/us_c1_1_growth_vs_lambda.csv` (10 colonne) `[V]`.
    * `results/us_c1_2_estimation_error.csv` (12 colonne, 46 righe di dati) `[V]`.
    * `results/us_c2_anova_autocorrelation.csv` (10 colonne, 24 righe di dati) `[V]`.
    * `thesis/figures/us_c1_1_growth_vs_lambda.png` (figura a tre pannelli) `[V]`.
    * `thesis/figures/us_c1_2_estimation_error.png` (figura a due pannelli) `[V]`.
    * `thesis/figures/us_c2_anova_autocorrelation.png` (figura a due pannelli) `[V]`.

### 7. Convenzioni in vigore

* Naming:
  * Moduli e pacchetti: `snake_case` (`shk`, `kelly`, `stats`, `core.py`, `simulate.py`, `estimation.py`, `staking.py`, `scenarios.py`, `metrics.py`, `anova.py`, `timeseries.py`, `calibration.py`, `false_rejection.py`) `[V]`.
  * Funzioni e variabili: `snake_case` (`kelly_fraction`, `draw_outcomes`, `simulate_growth`, `oneway_anova`, `generate_ar1_series`, `calibrate_threshold`, `compute_nominal_rejection_rates`, ecc.) `[V]`.
  * Classi e tipi: `PascalCase` (`Scenario`, `StakingMoments`, `OneWayAnovaResult`, `PhiStreams`, `RejectionResult`) `[V]`.
  * Costanti: `UPPER_CASE` (`SEED`, `BASE_SCENARIO`, `SUBTLE_SCENARIO`, `PHI_VALUES`, `N_OBS`, `N_SERIES`, `ALPHA`, `SEED_C2`, `BLOCK_LENGTHS`, `N_BOOT`, `METHOD_NOMINAL`, `METHOD_BLOCK_BOOTSTRAP`, `DESIGNS`, `CSV_COLUMNS`, `FLOAT_CSV_COLUMNS`) `[V]`.
  * Variabili statistiche e matematiche: lettere matematiche convenzionali della letteratura ($p, b, f, T, M, b_0, \lambda, \sigma_p, c, \delta, \phi, n, m, k, N, L, B, \alpha$) `[V]`.
  * File e funzioni di test: prefisso `test_` `[V]`.
* Organizzazione dei file:
  * Codice di libreria in `src/shk/` `[V]`.
  * Suite di test in `tests/` `[V]`.
  * Script di simulazione ed esperimento in `scripts/` `[V]`.
  * File tabellari in `results/` e grafici in `thesis/figures/` `[V]`.
  * Tracciamento operativo, backlog, protocollo e report in `.agent/` `[V]`.
* Stile:
  * Type hints completi su argomenti e valori di ritorno in tutte le funzioni `[V]`.
  * Docstring conformi allo stile NumPy con sezioni `Parametri`, `Restituisce`, `Solleva` (o `Campi`, `Attributi`) `[V]`.
* Gestione degli errori:
  * Validazione difensiva all'inizio delle funzioni: `ValueError` per valori o dimensioni non conformi, `TypeError` per tipi non consentiti `[V]`.
  * Nei moduli di `src/shk/stats/`, controllo esplicito del tipo degli interi: `bool` e `float` sollevano `TypeError`, mentre gli interi nativi e `np.integer` vengono accettati `[V]`.
  * Nessun blocco `try...except` presente nei sorgenti in `src/` o negli script in `scripts/` `[V]`.
  * Messaggi delle eccezioni rigorosamente in lingua inglese `[V]`.
* Logging e output:
  * Nessun modulo o framework di logging impiegato nel codebase `[V]`.
  * Nessuna chiamata a `print()` presente nei sorgenti in `src/` o negli script in `scripts/` `[V]`.
* Lingua:
  * Commenti e docstring redatti in lingua italiana `[V]`.
  * Identificatori, messaggi delle eccezioni e nomi dei test redatti in lingua inglese `[V]`.
* Pattern ricorrenti:
  * Vettorizzazione NumPy completa per eliminare i cicli espliciti sulle traiettorie o serie stocastiche `[V]`.
  * Tracciabilità statistica e isolamento tramite generatori NumPy `Generator` passati per argomento e flussi indipendenti tramite `SeedSequence.spawn` `[V]`.
  * Script sperimentali: impostazione `matplotlib.use("Agg")` prima di pyplot; funzione `run_experiment()` senza parametri richiamata dal blocco `__main__`; assenza di argomenti CLI; salvataggio CSV con `csv.DictWriter` e PNG con `dpi=150` `[V]`.
  * Deallocazione della memoria con `del paths` nei cicli Monte Carlo `[V]`.
* Incoerenze rilevate tra parti diverse del progetto (escluse le convenzioni deliberate):
  1. `expected_final_wealth` è implementata in `src/shk/kelly/core.py`, ma non è re-esportata in `src/shk/kelly/__init__.py` a differenza di `kelly_fraction` e `log_growth_rate` `[V]`.
  2. Disallineamento tra lockfile locale e CI: alla radice è presente `uv.lock`, ma il workflow `.github/workflows/test.yml` installa con `pip install -e ".[dev]"` senza vincolare le versioni `[V]`.
  3. Validazione degli interi non uniforme tra C1 e C2: `draw_outcomes` e `noisy_estimates` in C1 non validano il tipo esatto degli interi $T$ e $M$ (accettando `True` come 1), a differenza dei moduli di C2 (`generate_ar1_series`, `moving_block_indices`, `oneway_anova_vectorized`) che sollevano `TypeError` per i booleani `[V]`.
  4. Contraddizione documentale nella docstring di `src/shk/stats/calibration.py`: nello schema metodologico (a.1) per l'ANOVA F il dato indicato è "la serie della risposta", in contrasto con il principio generale (c) che impone al chiamante di imporre $H_0$ prima di invocare la calibrazione `[V]`.
  5. In `tests/test_metrics.py:test_metrics_error_conditions`, la verifica del sollevamento di `ValueError` su array 1D o con colonne insufficienti viene eseguita su quattro metriche, ma viene omessa per `median_final_wealth` e `mean_final_wealth` `[V]`.
  6. Lo script `scripts/us_c1_1_growth_vs_lambda.py` hardcoda i parametri di simulazione all'interno di `run_experiment()` anziché importarli da `src/shk/kelly/scenarios.py` (adottato invece da C1.2) `[V]`.

### 8. Test

* Posizione dei test: Directory `tests/` `[V]`.
* Tipologia di test:
  * Test unitari analitici sulle formule matematiche di Kelly (`tests/test_kelly_core.py`) `[V]`.
  * Test unitari di simulazione, broadcasting e log-wealth (`tests/test_simulate.py`) `[V]`.
  * Test unitari su perturbazioni e stime gaussiane con saturazione (`tests/test_estimation.py`) `[V]`.
  * Test unitari su frazioni di Kelly, momenti empirici e regola plug-in (`tests/test_staking.py`) `[V]`.
  * Test unitari sulle metriche di rendimento e drawdown (`tests/test_metrics.py`) `[V]`.
  * Test di conformità su ANOVA a una via, concordanza con `scipy.stats.f_oneway`, partizione della devianza e vettorizzazione (`tests/test_anova.py`) `[V]`.
  * Test unitari e statistici su serie AR(1), forma, riproducibilità, varianze e autocorrelazione pooled (`tests/test_timeseries.py`) `[V]`.
  * Test unitari su indici di blocco, statistica d'ordine e calibrazione della soglia per moving block bootstrap (`tests/test_calibration.py`) `[V]`.
  * Test di accettazione end-to-end per US-C1.1 interamente marcati `@pytest.mark.slow` (`tests/test_us_c1_1_acceptance.py`) `[V]`.
  * Test di accettazione per US-C1.2, veloci e marcati `@pytest.mark.slow` (`tests/test_us_c1_2_acceptance.py`) `[V]`.
  * Test di accettazione per US-C2.2 e US-C2.3, veloci e marcati `@pytest.mark.slow` con fixture di modulo (`tests/test_us_c2_acceptance.py`) `[V]`.
* Modalità di lancio:
  * Esecuzione predefinita (solo test veloci, esclude i test slow tramite `addopts = "-m 'not slow'"` in `pyproject.toml`): `pytest -v` `[V]`.
  * Esecuzione tramite Python del venv: `.\.venv\Scripts\python.exe -m pytest -v` `[D]`.
  * Esecuzione dei soli test lenti di accettazione Monte Carlo: `pytest -m slow` `[D]`.
  * Esecuzione integrale di tutti i test: `pytest -o addopts=""` `[D]`.
* Copertura desunta leggendo il codice dei file di test:
  * Funzioni e classi pubbliche che compaiono esplicitamente nelle asserzioni dei test:
    * `kelly_fraction` (in `test_kelly_core.py`, `test_staking.py`, `test_us_c1_1_acceptance.py`, `test_us_c1_2_acceptance.py`) `[V]`.
    * `log_growth_rate` (in `test_kelly_core.py`) `[V]`.
    * `draw_outcomes` (in `test_simulate.py`, `test_us_c1_1_acceptance.py`) `[V]`.
    * `simulate_growth` (in `test_simulate.py`) `[V]`.
    * `log_wealth_paths` (in `test_simulate.py`, `test_us_c1_1_acceptance.py`, `test_us_c1_2_acceptance.py`) `[V]`.
    * `relative_perturbation` (in `test_estimation.py`) `[V]`.
    * `noisy_estimates` (in `test_estimation.py`, `test_us_c1_2_acceptance.py`) `[V]`.
    * `kelly_staking` (in `test_staking.py`, `test_us_c1_2_acceptance.py`) `[V]`.
    * `StakingMoments` (in `test_staking.py`) `[V]`.
    * `staking_moments` (in `test_staking.py`, `test_us_c1_2_acceptance.py`) `[V]`.
    * `plugin_staking` (in `test_staking.py`) `[V]`.
    * `Scenario` (in `test_us_c1_2_acceptance.py`) `[V]`.
    * `BASE_SCENARIO` (in `test_us_c1_2_acceptance.py`) `[V]`.
    * `SUBTLE_SCENARIO` (in `test_us_c1_2_acceptance.py`) `[V]`.
    * `spawn_generators` (in `test_us_c1_2_acceptance.py`) `[V]`.
    * `draw_scenario_outcomes` (in `test_us_c1_2_acceptance.py`) `[V]`.
    * `simulate_scenario` (in `test_us_c1_2_acceptance.py`) `[V]`.
    * `final_log_wealth` (in `test_metrics.py`) `[V]`.
    * `median_growth_rate` (in `test_metrics.py`, `test_us_c1_1_acceptance.py`, `test_us_c1_2_acceptance.py`) `[V]`.
    * `median_final_wealth` (in `test_metrics.py`) `[V]`.
    * `mean_final_wealth` (in `test_metrics.py`) `[V]`.
    * `max_drawdown` (in `test_metrics.py`, `test_us_c1_1_acceptance.py`) `[V]`.
    * `fraction_below_start` (in `test_metrics.py`) `[V]`.
    * `OneWayAnovaResult` (in `test_anova.py`) `[V]`.
    * `oneway_anova` (in `test_anova.py`) `[V]`.
    * `oneway_anova_vectorized` (in `test_anova.py`, `test_calibration.py`, `test_us_c2_acceptance.py`) `[V]`.
    * `generate_ar1_series` (in `test_timeseries.py`, `test_us_c2_acceptance.py`) `[V]`.
    * `moving_block_indices` (in `test_calibration.py`) `[V]`.
    * `compute_order_statistic_index` (in `test_calibration.py`) `[V]`.
    * `calibrate_threshold` (in `test_calibration.py`) `[V]`.
    * `ALPHA` (in `test_us_c2_acceptance.py`) `[V]`.
    * `BLOCK_LENGTHS` (in `test_us_c2_acceptance.py`) `[V]`.
    * `CSV_COLUMNS` (in `test_us_c2_acceptance.py`) `[V]`.
    * `FLOAT_CSV_COLUMNS` (in `test_us_c2_acceptance.py`) `[V]`.
    * `DESIGNS` (in `test_us_c2_acceptance.py`) `[V]`.
    * `DESIGN_CONTIGUOUS_2` (in `test_us_c2_acceptance.py`) `[V]`.
    * `DESIGN_CONTIGUOUS_38` (in `test_us_c2_acceptance.py`) `[V]`.
    * `DESIGN_RANDOM_2` (in `test_us_c2_acceptance.py`) `[V]`.
    * `METHOD_BLOCK_BOOTSTRAP` (in `test_us_c2_acceptance.py`) `[V]`.
    * `N_OBS` (in `test_us_c2_acceptance.py`) `[V]`.
    * `N_SERIES` (in `test_us_c2_acceptance.py`) `[V]`.
    * `PHI_VALUES` (in `test_us_c2_acceptance.py`) `[V]`.
    * `SEED_C2` (in `test_us_c2_acceptance.py`) `[V]`.
    * `RejectionResult` (in `test_us_c2_acceptance.py`) `[V]`.
    * `compute_nominal_rejection_rates` (in `test_us_c2_acceptance.py`) `[V]`.
    * `compute_calibrated_rejection_rates` (in `test_us_c2_acceptance.py`) `[V]`.
    * `critical_value_nominal` (in `test_us_c2_acceptance.py`) `[V]`.
    * `make_design_labels` (in `test_us_c2_acceptance.py`) `[V]`.
    * `monte_carlo_interval_99` (in `test_us_c2_acceptance.py`) `[V]`.
  * Funzioni e classi pubbliche che NON compaiono MAI nelle asserzioni dei test:
    * `expected_final_wealth` (definita in `src/shk/kelly/core.py:97-144`, usata nello script C1.1, priva di unit test dedicati) `[V]`.
    * `PhiStreams` (definita in `src/shk/stats/false_rejection.py:48-65`, usata internamente in `spawn_c2_generators`, non asserita direttamente nei test) `[V]`.
    * `spawn_c2_generators` (definita in `src/shk/stats/false_rejection.py:248-297`, non invocata direttamente nei test) `[V]`.
    * `METHOD_NOMINAL` (costante definita in `src/shk/stats/false_rejection.py:22`, non usata direttamente nei test) `[V]`.
    * `run_experiment` dei tre script in `scripts/` (privi di test di integrazione automatizzati) `[V]`.
  * Nota vincolo: Conteggi numerici di test passati, tempi di esecuzione o percentuali esatte di copertura non vengono riportati in quanto richiederebbero l'esecuzione della suite, vietata dal vincolo di sola lettura `[V]`. Se tali informazioni fossero ritenute indispensabili, la risposta corretta è che servirebbe eseguire la suite di test `[V]`.
* Test con asserzioni dipendenti da seed fissi, tolleranze numeriche o costanti empiriche:
  * `tests/test_kelly_core.py:13`: tolleranza `abs(actual - expected) < 1e-12` `[V]`.
  * `tests/test_kelly_core.py:32`: tolleranza `pytest.approx(0.020136, abs=1e-6)` `[V]`.
  * `tests/test_kelly_core.py:39`: tolleranza `pytest.approx(-0.002447, abs=1e-6)` `[V]`.
  * `tests/test_kelly_core.py:47`: tolleranza di griglia `abs(f_argmax - 0.20) <= step` `[V]`.
  * `tests/test_simulate.py:11`: seed fisso `np.random.default_rng(42)` `[V]`.
  * `tests/test_simulate.py:22-23`: seed fisso `np.random.default_rng(12345)` `[V]`.
  * `tests/test_simulate.py:32`: seed fisso `np.random.default_rng(999)` `[V]`.
  * `tests/test_simulate.py:38`: tolleranza empirica stocastica `abs(empirical_p - p) < 0.01` `[V]`.
  * `tests/test_simulate.py:43`: seed fisso `np.random.default_rng(42)` `[V]`.
  * `tests/test_simulate.py:78`: tolleranza numerica `np.testing.assert_allclose(actual, expected, rtol=1e-12)` `[V]`.
  * `tests/test_simulate.py:83`: seed fisso `np.random.default_rng(7)` `[V]`.
  * `tests/test_simulate.py:94`: seed fisso `np.random.default_rng(21)` `[V]`.
  * `tests/test_simulate.py:128`: tolleranza `rtol=1e-12` `[V]`.
  * `tests/test_simulate.py:133`: seed fisso `np.random.default_rng(101)` `[V]`.
  * `tests/test_simulate.py:143`: tolleranza `rtol=1e-12` `[V]`.
  * `tests/test_estimation.py:13-14`: tolleranze `abs(...) < 1e-12` `[V]`.
  * `tests/test_estimation.py:27-29`: seed fissi `np.random.default_rng(42)` e `(43)` `[V]`.
  * `tests/test_estimation.py:44`: seed fisso `np.random.default_rng(20260927)` `[V]`.
  * `tests/test_estimation.py:52-53`: tolleranze empiriche `abs(mean_emp - p) < 0.001` e `abs(std_emp - sigma_p) < 0.001` `[V]`.
  * `tests/test_estimation.py:58`: seed fisso `np.random.default_rng(999)` `[V]`.
  * `tests/test_estimation.py:70`: seed fisso `np.random.default_rng(123)` `[V]`.
  * `tests/test_estimation.py:82`: seed fisso `np.random.default_rng(42)` `[V]`.
  * `tests/test_staking.py:20-21, 29`: tolleranze numeriche `1e-12` `[V]`.
  * `tests/test_staking.py:44`: tolleranza assoluta `atol=1e-12` `[V]`.
  * `tests/test_staking.py:55`: tolleranza numerica `1e-12` `[V]`.
  * `tests/test_staking.py:61`: tolleranza relativa `rtol=1e-12` `[V]`.
  * `tests/test_staking.py:71, 76, 80, 100, 104`: tolleranze float `pytest.approx(...)` `[V]`.
  * `tests/test_staking.py:155-158, 163-166`: tolleranze `abs(...) < 1e-12` `[V]`.
  * `tests/test_staking.py:204, 214, 220, 226, 229`: tolleranze numeriche assolute `1e-12` `[V]`.
  * `tests/test_metrics.py:43, 52, 61, 82`: tolleranze float `pytest.approx(...)` `[V]`.
  * `tests/test_metrics.py:72`: tolleranza assoluta `atol=1e-12` `[V]`.
  * `tests/test_anova.py:32-34, 37`: tolleranze relative `1e-12` `[V]`.
  * `tests/test_anova.py:38`: tolleranza relativa `1e-10` `[V]`.
  * `tests/test_anova.py:53, 54, 65, 66, 78, 79, 92, 93`: concordanza con scipy a tolleranza `1e-12` (F) e `1e-10` (p-value), con seed `20260928`, `20260929`, `20260930` `[V]`.
  * `tests/test_anova.py:140, 144`: tolleranze relative partizione devianza `1e-12` `[V]`.
  * `tests/test_anova.py:154, 175`: seed fisso `20260931` e tolleranza `1e-12` `[V]`.
  * `tests/test_anova.py:180, 191, 206`: seed fissi `20260932`, `98765` e tolleranza `1e-12` `[V]`.
  * `tests/test_anova.py:211, 220`: seed fisso `20260933` e tolleranza `1e-12` `[V]`.
  * `tests/test_timeseries.py:16`: seed fisso `np.random.default_rng(42)` `[V]`.
  * `tests/test_timeseries.py:35-37`: seed fissi `12345` e `54321` `[V]`.
  * `tests/test_timeseries.py:57`: seed fisso `20260928` `[V]`.
  * `tests/test_timeseries.py:70, 75`: tolleranze empiriche varianza `< 0.15` (15% relativo) su parametri $\phi \in \{0.0, 0.3, 0.7\}$ `[V]`.
  * `tests/test_timeseries.py:86`: tolleranza empirica autocorrelazione lag-1 $|diff| < 0.02$ `[V]`.
  * `tests/test_timeseries.py:98, 122, 133, 142, 164`: seed fisso `42` `[V]`.
  * `tests/test_calibration.py:23`: seed fisso `20260928` `[V]`.
  * `tests/test_calibration.py:60`: seed fisso `42` `[V]`.
  * `tests/test_calibration.py:77, 90`: seed fissi `12345` e `99999` `[V]`.
  * `tests/test_calibration.py:137, 145, 157`: seed fissi `42` e `20260928` e tolleranza `rel_tol=1e-12` `[V]`.
  * `tests/test_calibration.py:175, 181`: seed fissi `100` e `777` e tolleranza `rel_tol=1e-12` `[V]`.
  * `tests/test_calibration.py:223, 231, 245, 255`: seed fissi `1`, `20260928`, `2` `[V]`.
  * `tests/test_calibration.py:276, 283, 289`: seed fissi `3`, `12345`, `54321` `[V]`.
  * `tests/test_calibration.py:348, 376, 429, 443, 470, 488`: seed fisso `42` `[V]`.
  * `tests/test_us_c1_1_acceptance.py:23, 47, 73, 92`: seed fisso `np.random.default_rng(20260905)` `[V]`.
  * `tests/test_us_c1_1_acceptance.py:37`: tolleranza numerica `abs(best_lambda - 1.0) < 1e-6` `[V]`.
  * `tests/test_us_c1_1_acceptance.py:63`: tolleranza empirica stocastica `np.all(diffs >= -0.01)` `[V]`.
  * `tests/test_us_c1_1_acceptance.py:78, 82`: costante empirica di zero-crossing $\lambda = 1.946$ e soglia $|g_{\text{med}}| < 0.002$ `[V]`.
  * `tests/test_us_c1_1_acceptance.py:97`: costante empirica di sovrainvestimento $\lambda = 2.5$ `[V]`.
  * `tests/test_us_c1_2_acceptance.py:27-28, 45, 58, 84, 108, 125, 148`: seed master predefinito `SEED = 20260927` `[V]`.
  * `tests/test_us_c1_2_acceptance.py:52`: tolleranza `rtol=1e-12` `[V]`.
  * `tests/test_us_c1_2_acceptance.py:83, 107, 124, 147`: costante rumore $\sigma_p = 0.0283$ `[V]`.
  * `tests/test_us_c1_2_acceptance.py:96`: tolleranza empirica Monte Carlo `abs(moments.var_c - reference) < 0.005` `[V]`.
  * `tests/test_us_c2_acceptance.py:49, 67, 84, 113, 125, 133, 182, 307`: seed master predefinito `SEED_C2 = 20260928` `[V]`.
  * `tests/test_us_c2_acceptance.py:53, 71, 234, 245, 355, 374, 381`: tolleranze di confronto float `1e-9` `[V]`.
  * `tests/test_us_c2_acceptance.py:139`: seed fisso derivato `stream_seeds[1]` `[V]`.
  * `tests/test_us_c2_acceptance.py:200-205, 333-338`: tolleranza di confronto float per il file CSV `math.isclose(..., rel_tol=1e-12, abs_tol=0.0)` `[V]`.

### 9. Zone fragili

1. Test di accettazione slow con fallimento noto su risultato empirico inatteso (T12):
   * In `tests/test_us_c2_acceptance.py:350-363`, `test_acceptance_calibrated_phi_zero_within_mc_interval` fallisce sistematicamente a $\phi = 0.0$ con $L=20$ (29 rigetti su 1000, sotto l'estremo inferiore dell'intervallo 99% pari a 32.25) `[V]`.
   * La calibrazione viene eseguita sulla serie grezza senza previa imposizione dell'ipotesi nulla $H_0$ `[V]`.
   * Il fallimento non è una regressione accidentale ma un risultato noto documentato nel backlog; non deve essere alterato allentando i parametri del test `[V]`.

2. Assenza totale di test automatizzati per `expected_final_wealth`:
   * Implementata in `src/shk/kelly/core.py:97-144` e impiegata nello script `scripts/us_c1_1_growth_vs_lambda.py` `[V]`.
   * Non è richiamata in alcun modulo di test sotto `tests/` `[V]`.
   * Regressioni analitiche o refactoring errati su tale funzione non verrebbero rilevati dalla suite `[V]`.

3. Rischio di rifiuto da parte di `simulate_growth` per saturazione di stime rumorose a $p̂ = 1.0$:
   * In `src/shk/kelly/estimation.py`, `noisy_estimates` applica `np.clip` saturando i valori in $[0, 1]$ `[V]`.
   * In presenza di stime saturate esattamente a $1.0$, `kelly_staking(1.0, b, lam)` restituisce $\lambda \cdot 1.0$ `[V]`.
   * Con $\lambda \ge 1.0$, la frazione risultante è $\ge 1.0$, valore che `simulate_growth` rifiuta sollevando `ValueError` (`fractions in [0, 1)`) `[V]`.

4. Duplicazione dei parametri di simulazione nello script C1.1:
   * I parametri ($p=0.60, b=1.0, T=1000, M=10000$, seed `20260905`, griglia di 51 punti) sono hardcoded sia in `scripts/us_c1_1_growth_vs_lambda.py:30-36` sia in `tests/test_us_c1_1_acceptance.py` `[V]`.
   * Un'eventuale modifica futura dei parametri dell'esperimento rischia di disallineare lo script pubblicato e i test di accettazione `[V]`.

5. Dipendenze senza vincolo di versione e mancato utilizzo del lockfile in CI:
   * Il file `pyproject.toml` elenca `numpy`, `scipy`, `matplotlib` e `pytest` senza specificare vincoli di versione minimi o precisi `[V]`.
   * Il workflow di CI `.github/workflows/test.yml` esegue `pip install -e ".[dev]"` ignorando il file `uv.lock` presente alla radice `[V]`.
   * Aggiornamenti minori delle librerie esterne possono introdurre scostamenti numerici sull'ultima cifra decimale o alterazioni nelle sequenze pseudo-casuali `[D]`.

6. I test lenti di accettazione Monte Carlo sono esclusi dalla pipeline di CI:
   * In `pyproject.toml`, l'opzione `addopts = "-m 'not slow'"` esclude tutti i test marcati `@pytest.mark.slow` `[V]`.
   * Il runner GitHub Actions in `.github/workflows/test.yml` esegue unicamente `pytest -v`, saltando i test slow `[V]`.
   * Regressioni statistiche o numeriche su larga scala possono essere rilevate solo eseguendo manualmente `pytest -m slow` `[V]`.

7. Incompletezza dei test di validazione degli argomenti in `tests/test_metrics.py`:
   * In `tests/test_metrics.py:test_metrics_error_conditions`, la verifica del sollevamento di `ValueError` su array 1D o con meno di 2 colonne viene omessa per `median_final_wealth` e `mean_final_wealth` `[V]`.

8. Sovrascrittura distruttiva dei file di output versionati:
   * L'esecuzione degli script `scripts/us_c1_1_growth_vs_lambda.py`, `scripts/us_c1_2_estimation_error.py` e `scripts/us_c2_anova_autocorrelation.py` sovrascrive direttamente le tabelle CSV in `results/` e le figure PNG in `thesis/figures/` `[V]`.

9. Working tree sporco con modifiche non committate:
   * Il file `.agent/BACKLOG.md` risulta modificato localmente nel working tree (341 righe inserite relative alla pianificazione di Story S3 / C3) `[V]`.

10. Incoerenza documentale nella docstring di `src/shk/stats/calibration.py`:
    * Al punto (a.1), per l'ANOVA F il dato di input viene indicato come "la serie della risposta", in contraddizione con il punto (c) che impone al chiamante di sottoporre dati in cui l'ipotesi nulla $H_0$ sia già stata imposta `[V]`.

### 10. Limiti di questa mappa

* Cosa non è stato ispezionato e perché:
  * Non è stato eseguito alcun codice Python, script di simulazione o comando di test `[V]`.
  * Non sono stati misurati sperimentalmente i tempi di calcolo né i consumi di memoria `[V]`.
  * Non sono state interrogate le API remote di GitHub per lo storico delle pull request o dei workflow `[V]`.
  * Tutte le omissioni sono dovute al rispetto vincolante del vincolo assoluto di sola lettura, che vieta qualsiasi comando con possibili effetti collaterali (scrittura cache, generazione file o sincronizzazione ambienti) `[V]`.
* Cosa resta incerto:
  * Il tempo effettivo di esecuzione della suite veloce e della suite lenta su questo specifico ambiente (richiederebbe l'esecuzione vietata della suite) `[V]`.
  * Se l'attuale working tree sporco passi interamente la suite veloce nel venv senza errori (richiederebbe l'esecuzione di pytest) `[V]`.
* Sezioni in prevalenza `[D]`:
  * Sezione 2 ("Come si esegue"): i comandi locali `uv sync`, `pip install -e .`, `hatch build`, `pytest -m slow`, `pytest -o addopts=""` e l'avvio degli script Python sono dedotti dalle convenzioni standard degli strumenti di sviluppo Python in assenza di un file di orchestrazione (es. Makefile) `[V]`.
* Domande che farei se dovessi lavorare su questo progetto senza altro contesto:
  1. Qual è la decisione definitiva sul seguito di T12 (US-C2.3): si intende implementare una variante che imponga $H_0$ (es. centrando le serie per gruppo prima del bootstrap), oppure si preferisce marcare il test come `xfail` documentando il limite teorico misurato?
  2. Per quale motivo `expected_final_wealth` non viene re-esportata in `src/shk/kelly/__init__.py` e non dispone di unit test in `tests/test_kelly_core.py`?
  3. È pianificata l'adozione di `uv` nella pipeline GitHub Actions (`.github/workflows/test.yml`) per garantire che l'ambiente CI utilizzi le versioni esattamente bloccate in `uv.lock`?
  4. Per la nuova Story S3, le funzioni di C1 (`draw_outcomes` e `noisy_estimates`) devono essere aggiornate per validare il tipo degli interi (`TypeError` su bool/float) analogamente ai moduli di C2?
  5. Il file `.agent/BACKLOG.md` (attualmente modificato localmente con 341 righe per Story S3) deve essere committato dal programmatore prima di avviare il Task 14?

### 11. Comandi eseguiti

Elenco completo di tutti i comandi eseguiti durante la presente sessione di mappatura:

1. `git status` — Esito: codice 0. Rilevato branch `main` allineato a `origin/main`, working tree sporco con `modified: .agent/BACKLOG.md`.
2. `git branch` — Esito: codice 0. Verificato il branch locale corrente `* main`.
3. `git remote -v` — Esito: codice 0. Ispezionati gli URL fetch e push del remote `origin`.
4. `git log -n 5 --oneline` — Esito: codice 0. Ispezionati gli hash e i titoli sintetici degli ultimi 5 commit.
5. `git diff` — Esito: codice 0. Ispezionate le modifiche non committate nel file `.agent/BACKLOG.md`.
6. `git branch -a` — Esito: codice 0. Verificato l'elenco di tutti i branch locali e remoti.
7. `git log -n 5` — Esito: codice 0. Ispezionati i messaggi estesi e i metadati degli ultimi 5 commit.
8. `git log -n 1 115e600` — Esito: codice 0. Esaminati i dettagli del commit di merge `115e600` relativo a Story S2 / C2 (#16).
9. `git diff --stat` — Esito: codice 0. Quantificate le modifiche non staged su `.agent/BACKLOG.md` (341 inserimenti, 2 cancellazioni).
10. `git status --ignored` — Esito: codice 0. Ispezionati i file e le directory ignorate dal controllo di versione nel filesystem locale.
11. `git diff --name-only 4b825dc642cb6eb9a060e54bf8d69288fbee4904 HEAD` — Esito: codice 0. Estratto l'inventario completo di tutti i file tracciati nel commit HEAD confrontato con il tree vuoto di Git.
12. `git status` — Esito: codice 0. Verifica finale del working tree dopo la scrittura della mappa.

Dichiarazione:
Tutti i comandi eseguiti sono comandi git di sola lettura appartenenti all'insieme consentito (`git status`, `git log`, `git branch`, `git remote -v`, `git diff`). Nessun comando al di fuori di tale insieme è stato eseguito. Nessun codice del progetto, script o suite di test è stato eseguito. Nessun file o directory è stato modificato o creato nel filesystem, ad eccezione dell'autorizzata scrittura del file `.agent/MAPPA.md`.
