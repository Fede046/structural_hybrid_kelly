Mappa completa — 2026-09-29 — R1

### 0. Stato del repository

* Percorso assoluto della radice: `c:\Users\malse\Documents\GitHub\structural_hybrid_kelly` `[V]`.
* Branch corrente: `main` `[V]`.
* Stato del working tree: pulito (`nothing to commit, working tree clean`) `[V]`.
* File modificati non staged: nessuno `[V]`.
* File modificati staged: nessuno `[V]`.
* File non tracciati: nessuno `[V]`.
* File ignorati rilevati nel filesystem locale:
  * `.pytest_cache/` `[V]`.
  * `.venv/` `[V]`.
  * `data/raw/E0/` (directory contenente i 31 CSV delle stagioni storiche dal 1993-94 al 2023-24) `[V]`.
  * `src/shk/__pycache__/` `[V]`.
  * `src/shk/data/__pycache__/` `[V]`.
  * `src/shk/kelly/__pycache__/` `[V]`.
  * `src/shk/market/__pycache__/` `[V]`.
  * `src/shk/stats/__pycache__/` `[V]`.
  * `tests/__pycache__/` `[V]`.
* Ultimi cinque commit in forma breve (dalla storia di Git sul branch `main`):
  * `90a77a1` `C3 (#17)` `[V]`
  * `115e600` `C2 (#16)` `[V]`
  * `1e7813d` `C1 (#14)` `[V]`
  * `640b906` `C1 (#13)` `[V]`
  * `a7420cb` `create c1 (#5)` `[V]`
* Remote configurati:
  * `origin`: `https://github.com/Fede046/structural_hybrid_kelly.git` (fetch) `[V]`
  * `origin`: `https://github.com/Fede046/structural_hybrid_kelly.git` (push) `[V]`
* Allineamento rispetto al remote: `main` è allineato a `origin/main` (`up to date`, 0 commit avanti, 0 commit indietro rispetto all'ultimo fetch locale) `[V]`.
* Altri branch locali: nessuno (è presente solo `main`) `[V]`.
* Branch remoti: `origin/HEAD -> origin/main`, `origin/main` `[V]`.

### 1. Identikit

* Nome del progetto: `structural-hybrid-kelly` `[V]`.
* Descrizione: Libreria scientifica e ambiente di simulazione per l'analisi analitica e stocastica del criterio di Kelly, modelli ibridi strutturali, inferenza statistica (ANOVA, autocorrelazione, block bootstrap) e pipeline su dati reali di scommesse calcistiche (Premier League E0, de-vigging, split protetto, walk-forward anti-leakage) `[V]`.
* Stack: Python `[V]`.
* Linguaggi: Python 3 `[V]`.
* Versioni:
  * Versione Python minima supportata: `>=3.11` (dichiarata in `pyproject.toml`) `[V]`.
  * Versione Python impiegata nella CI: `3.12` (specificata in `.github/workflows/test.yml`) `[V]`.
  * Versione del pacchetto: `0.1.0` (dichiarata in `pyproject.toml` e in `src/shk/__init__.py`) `[V]`.
* Gestore di pacchetti: `uv` (attestato dal lockfile `uv.lock` alla radice) `[V]`, con `pip` impiegato nel workflow di CI `[V]`.
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
  * Esperimento US-C1.2 (errore di stima e confronto regole di staking): `python scripts/us_c1_2_estimation_error.py` `[D]`.
  * Esperimento US-C2.2 e US-C2.3 (falso rigetto ANOVA e calibrazione block bootstrap): `python scripts/us_c2_anova_autocorrelation.py` `[D]`.
  * Esperimento US-C3.1 (audit di copertura dati, quote e bookmaker): `python scripts/us_c3_1_data_coverage.py` `[D]`.
  * Esperimento US-C3.2 (analisi della divergenza tra metodi di de-vigging): `python scripts/us_c3_2_devig_divergence.py` `[D]`.
  * Esecuzione tramite l'interprete del virtual environment locale: `.\.venv\Scripts\python.exe scripts\<nome_script>.py` `[D]`.
* Variabili d'ambiente richieste:
  * Nessuna variabile d'ambiente richiesta nei file di configurazione `[V]`.
  * Nessuna variabile d'ambiente letta nel codice sorgente di `src/` o negli script di `scripts/` `[V]`.
* File di configurazione richiesti:
  * `pyproject.toml` (configurazione del pacchetto, metadati, dipendenze `numpy`, `scipy`, `matplotlib`, `pandas`, build backend e marker pytest) `[V]`.
  * `config/split.toml` (configurazione congelata dello split delle stagioni Premier League in ruoli training, validation e test, con flag `test_unlocked = false`) `[V]`.
  * Nessun file `.env` presente o richiesto `[V]`.
  * La directory `data/raw/` contiene unicamente il file placeholder versionato `.gitkeep` `[V]`.
  * La directory `data/raw/E0/` è presente localmente ma esclusa dal versionamento tramite `.gitignore` `[V]`.

### 3. Albero delle directory

* `.` (radice): File di configurazione di progetto (`pyproject.toml`, `uv.lock`, `.gitignore`, `LICENSE`) `[V]`.
* `.agent/`: Documentazione di processo, tracciamento del backlog (`BACKLOG.md`), protocollo operativo (`PROTOCOLLO.md`), scheda tecnica (`SCHEDA.md`) e mappa architetturale (`MAPPA.md`) `[V]`.
* `.agent/report/`: Report formali di chiusura dei task implementativi completati da T1 a T19 (`T1.md` ... `T19.md`) `[V]`.
* `.github/workflows/`: Pipeline di integrazione continua GitHub Actions per l'esecuzione automatizzata della test suite (`test.yml`) `[V]`.
* `config/`: Directory per le configurazioni congelate del progetto (`.gitkeep`, `split.toml`) `[V]`.
* `data/raw/`: Directory per i dataset grezzi scaricati esternamente (`.gitkeep`, sottodirectory non tracciata `E0/`) `[V]`.
* `results/`: Directory di destinazione dei file tabellari CSV generati dagli esperimenti e versionati in Git (`.gitkeep`, `us_c1_1_growth_vs_lambda.csv`, `us_c1_2_estimation_error.csv`, `us_c2_anova_autocorrelation.csv`, `us_c3_1_data_coverage.csv`, `us_c3_2_devig_divergence.csv`) `[V]`.
* `scripts/`: Script Python eseguibili per la conduzione degli esperimenti scientifici e la generazione delle figure di tesi `[V]`.
* `src/shk/`: Radice del codice sorgente del pacchetto Python `shk` `[V]`.
* `src/shk/kelly/`: Sottopacchetto dedicato alle formule analitiche, alla simulazione stocastica, ai modelli di errore di stima e alle regole di staking per il criterio di Kelly `[V]`.
* `src/shk/stats/`: Sottopacchetto dedicato all'analisi statistica, all'ANOVA a una via (singola e vettorizzata), alla generazione di serie temporali AR(1) e alla calibrazione per moving block bootstrap `[V]`.
* `src/shk/data/`: Sottopacchetto per l'ingestione, la validazione, l'audit di copertura, il partizionamento congelato dei dati storici e la fornitura walk-forward anti-leakage `[V]`.
* `src/shk/market/`: Sottopacchetto per la modellazione dei mercati di scommesse a quote decimali, de-vigging (proporzionale, additivo, power) e analisi della divergenza `[V]`.
* `tests/`: Suite completa di test unitari, test di conformità statistica e test di accettazione Monte Carlo basati su pytest `[V]`.
* `thesis/figures/`: Directory delle figure PNG ad alta risoluzione generate dagli script per la tesi (`.gitkeep`, `us_c1_1_growth_vs_lambda.png`, `us_c1_2_estimation_error.png`, `us_c2_anova_autocorrelation.png`, `us_c3_1_data_coverage.png`, `us_c3_2_devig_divergence.png`) `[V]`.

### 4. Moduli principali

Il pacchetto `shk` comprende complessivamente 16 moduli applicativi in `src/shk/`. In conformità al limite di massimo dieci moduli principali, vengono selezionati i 10 moduli architetturalmente più rilevanti.
Sono esclusi da questo elenco e dichiarati:
* Moduli esclusi del sottopacchetto `kelly`:
  * `src/shk/kelly/estimation.py` (responsabile dei modelli di perturbazione deterministica e rumore gaussiano delle probabilità, ancillare rispetto a simulazione e staking) `[V]`.
  * `src/shk/kelly/metrics.py` (responsabile del calcolo delle metriche empiriche e di drawdown su matrici di log-wealth) `[V]`.
* Moduli esclusi del sottopacchetto `stats`:
  * `src/shk/stats/timeseries.py` (responsabile della generazione stazionaria di serie AR(1)) `[V]`.
  * `src/shk/stats/false_rejection.py` (responsabile dell'orchestrazione delle simulazioni Monte Carlo del tasso di falso rigetto) `[V]`.
* Moduli esclusi dei sottopacchetti `data` e `market`:
  * `src/shk/data/coverage.py` (responsabile dell'audit e della classificazione delle colonne di quota per la story US-C3.1) `[V]`.
  * `src/shk/market/divergence.py` (responsabile del calcolo della tabella di divergenza per fasce di quota dell'esperimento US-C3.2) `[V]`.
* Moduli di inizializzazione esclusi: `src/shk/__init__.py`, `src/shk/kelly/__init__.py`, `src/shk/stats/__init__.py`, `src/shk/data/__init__.py`, `src/shk/market/__init__.py` `[V]`.
* Script esclusi: i 5 script in `scripts/` (descritti nella Sezione 5) `[V]`.
* Test esclusi: tutti i 17 moduli di test in `tests/` (dettagliati nella Sezione 8) `[V]`.

I 10 moduli principali selezionati:

1. `src/shk/kelly/core.py`
   * Responsabilità: Fornisce le formule analitiche esatte in forma chiusa per la frazione di Kelly, il tasso di crescita logaritmico atteso e il capitale finale atteso su scommesse binarie `[V]`.
   * Espone: `kelly_fraction(p, b)`, `log_growth_rate(f, p, b)`, `expected_final_wealth(f, p, b, T, b0=1.0)` `[V]`.
   * Dipendenze interne: Nessuna `[V]`.

2. `src/shk/kelly/simulate.py`
   * Responsabilità: Gestisce l'estrazione stocastica bernoulliana degli esiti e simula in modo vettorizzato l'evoluzione temporale del log-wealth con supporto a frazioni broadcastabili `[V]`.
   * Espone: `draw_outcomes(p, T, M, rng)`, `simulate_growth(outcomes, fractions, b)`, `log_wealth_paths(outcomes, f, b)` `[V]`.
   * Dipendenze interne: Nessuna `[V]`.

3. `src/shk/kelly/staking.py`
   * Responsabilità: Implementa il calcolo delle frazioni di puntata con moltiplicatore di Kelly, i momenti empirici del moltiplicatore normalizzato e la regola plug-in adattiva `[V]`.
   * Espone: `kelly_staking(p_hat, b, lam=1.0)`, `StakingMoments` (NamedTuple: `mean_c`, `mean_c2`, `var_c`, `fraction_zero`), `staking_moments(f_hat, f_star)`, `plugin_staking(p_hat, b, sigma_p)` `[V]`.
   * Dipendenze interne: Nessuna `[V]`.

4. `src/shk/kelly/scenarios.py`
   * Responsabilità: Centralizza la configurazione immutabile degli scenari Kelly, la derivazione riproducibile dei flussi casuali e l'orchestrazione delle simulazioni di scenario `[V]`.
   * Espone: `Scenario` (dataclass frozen), `BASE_SCENARIO`, `SUBTLE_SCENARIO`, `SEED`, `spawn_generators(seed=SEED)`, `draw_scenario_outcomes(scenario, rng)`, `simulate_scenario(scenario, outcomes, p_hat, lam=1.0)` `[V]`.
   * Dipendenze interne: `src/shk/kelly/simulate.py`, `src/shk/kelly/staking.py` `[V]`.

5. `src/shk/stats/anova.py`
   * Responsabilità: Implementa il calcolo esatto dell'ANOVA a una via per singoli gruppi e in modalità multidimensionale vettorizzata su insiemi di serie temporali `[V]`.
   * Espone: `OneWayAnovaResult` (NamedTuple), `oneway_anova(groups)`, `oneway_anova_vectorized(values, labels)` `[V]`.
   * Dipendenze interne: Nessuna `[V]`.

6. `src/shk/stats/calibration.py`
   * Responsabilità: Calcola la soglia critica calibrata di una statistica test mediante moving block bootstrap su dati serialmente correlati `[V]`.
   * Espone: `moving_block_indices(n, block_length, n_boot, rng)`, `compute_order_statistic_index(b, alpha)`, `calibrate_threshold(data, statistic, block_length, n_boot, alpha, rng, vectorized=False)` `[V]`.
   * Dipendenze interne: Nessuna `[V]`.

7. `src/shk/data/loading.py`
   * Responsabilità: Esegue l'ingestione, la decodifica deterministica multipiattaforma e la validazione strutturale e temporale dei file CSV storici delle stagioni di Premier League in un unico DataFrame `[V]`.
   * Espone: `DEFAULT_DATA_DIR`, `load_all_seasons(data_dir=DEFAULT_DATA_DIR, seasons=None)` `[V]`.
   * Dipendenze interne: Nessuna `[V]`.

8. `src/shk/data/split.py`
   * Responsabilità: Gestisce la configurazione congelata dello split temporale e impone una barriera I/O protetta che blocca l'accesso al test set e carica i dati per ruolo `[V]`.
   * Espone: `DEFAULT_SPLIT_CONFIG_PATH`, `TestSetLockedError` (RuntimeError), `SplitConfig` (NamedTuple), `read_split_config(config_path=DEFAULT_SPLIT_CONFIG_PATH)`, `load_by_role(role, config_path=DEFAULT_SPLIT_CONFIG_PATH, data_dir=DEFAULT_DATA_DIR)` `[V]`.
   * Dipendenze interne: `src/shk/data/loading.py` `[V]`.

9. `src/shk/data/walkforward.py`
   * Responsabilità: Fornisce le coppie sequenziali storia-partita per validazione walk-forward ridotte alla sola whitelist ed esegue i controlli anti-leakage temporale e di contenuto `[V]`.
   * Espone: `PREMATCH_IDENTIFIERS`, `LeakageError` (RuntimeError), `get_prematch_whitelist(columns)`, `check_leakage(history, match, whitelist=None)`, `walkforward_split(df, seasons_to_predict)`, `assert_no_leakage(history, match, whitelist=None)` `[V]`.
   * Dipendenze interne: `src/shk/data/coverage.py` `[V]`.

10. `src/shk/market/devig.py`
    * Responsabilità: Implementa la stima delle probabilità eque tramite i tre metodi di de-vigging per mercati a quote decimali (proporzionale, additivo e power con risolutore Newton salvaguardato) `[V]`.
    * Espone: `MAX_NEWTON_ITERATIONS`, `implied_probabilities(odds)`, `overround(odds)`, `devig_proportional(odds)`, `devig_additive(odds)`, `devig_power(odds)` `[V]`.
    * Dipendenze interne: Nessuna `[V]`.

### 5. Punti di ingresso e flussi

Punti di ingresso dell'applicazione:
* Script CLI per l'esperimento C1.1 (trade-off crescita/varianza): `python scripts/us_c1_1_growth_vs_lambda.py` `[V]`.
* Script CLI per l'esperimento C1.2 (errore di stima e regole di staking): `python scripts/us_c1_2_estimation_error.py` `[V]`.
* Script CLI per gli esperimenti C2.2 e C2.3 (falso rigetto ANOVA e bootstrap): `python scripts/us_c2_anova_autocorrelation.py` `[V]`.
* Script CLI per l'esperimento C3.1 (audit copertura dati storici Premier League): `python scripts/us_c3_1_data_coverage.py` `[V]`.
* Script CLI per l'esperimento C3.2 (divergenza de-vigging su stagioni non di test): `python scripts/us_c3_2_devig_divergence.py` `[V]`.
* Runner di test automatizzati: `pytest` (o `.\.venv\Scripts\python.exe -m pytest`) `[V]`.
* Utilizzo come libreria scientifica: `import shk`, `from shk.kelly import ...`, `from shk.stats import ...`, `from shk.data import ...`, `from shk.market import ...` `[V]`.

Esattamente tre flussi principali dell'applicazione:

* Flusso 1 — Simulazione stocastica dell'errore di stima e confronto regole di staking (Esperimento US-C1.2):
  1. `scripts/us_c1_2_estimation_error.py:run_experiment()` itera sugli scenari `BASE_SCENARIO` e `SUBTLE_SCENARIO` definiti in `src/shk/kelly/scenarios.py` `[V]`.
  2. Per ciascuno scenario:
     a. Istanzia due generatori casuali indipendenti tramite `spawn_generators(SEED)` in `src/shk/kelly/scenarios.py` `[V]`.
     b. Estrae la matrice di esiti bernoulliani con `draw_scenario_outcomes(scenario, rng_outcomes)` in `src/shk/kelly/scenarios.py` (che delega a `draw_outcomes` in `src/shk/kelly/simulate.py`) `[V]`.
     c. Per l'errore deterministico ($\pm 10\%$): calcola le probabilità perturbate con `relative_perturbation` in `src/shk/kelly/estimation.py`, simula le traiettorie con `simulate_scenario` in `src/shk/kelly/scenarios.py` (che calcola le puntate con `kelly_staking` in `src/shk/kelly/staking.py` ed evolve il capitale con `simulate_growth` in `src/shk/kelly/simulate.py`), e calcola le metriche empiriche richiamando `src/shk/kelly/metrics.py` `[V]`.
     d. Per ciascun $\sigma_p \in \{0.015, 0.0283, 0.045\}$: genera stime di probabilità con `noisy_estimates` in `src/shk/kelly/estimation.py`, ricava la frazione stimata con `kelly_staking` in `src/shk/kelly/staking.py`, valuta i momenti pooled con `staking_moments` in `src/shk/kelly/staking.py`, e simula e misura le varie regole di allocazione (`lambda_star`, `ratio_moments`, `lambda_linear`, `quarter_kelly`, `half_kelly`, `full_kelly`, e la regola adattiva `plugin_staking` combinata con `simulate_growth`) `[V]`.
  3. Scrive le 46 righe di risultati su `results/us_c1_2_estimation_error.csv` tramite `csv.DictWriter` `[V]`.
  4. Costruisce il grafico a due pannelli ed esporta la figura in `thesis/figures/us_c1_2_estimation_error.png` `[V]`.

* Flusso 2 — Valutazione del tasso di falso rigetto dell'ANOVA e calibrazione per block bootstrap (Esperimenti US-C2.2 e US-C2.3):
  1. `scripts/us_c2_anova_autocorrelation.py:run_experiment()` richiama le funzioni orchestratrici in `src/shk/stats/false_rejection.py` `[V]`.
  2. Per il tasso nominale (`compute_nominal_rejection_rates`):
     a. Inizializza i flussi casuali con `spawn_c2_generators(seed=SEED_C2)` in `src/shk/stats/false_rejection.py` `[V]`.
     b. Per ciascun $\phi \in \{0.0, 0.3, 0.5, 0.7\}$, genera 1000 serie stazionarie AR(1) con `generate_ar1_series` in `src/shk/stats/timeseries.py` `[V]`.
     c. Costruisce le etichette con `make_design_labels` e valuta le statistiche F in forma vettorizzata con `oneway_anova_vectorized` in `src/shk/stats/anova.py` per i disegni `contiguous_2`, `contiguous_38` e per il controllo permutato `random_2` `[V]`.
     d. Confronta la F osservata con il valore critico da `critical_value_nominal` e conta i rigetti su 1000 serie `[V]`.
  3. Per il tasso calibrato (`compute_calibrated_rejection_rates`):
     a. Riusa le stesse serie generate dal flusso `series_rng` per ciascun $\phi$ garantendo il confronto appaiato `[V]`.
     b. Ripartisce il flusso bootstrap per ciascun $L \in \{7, 20, 40\}$ `[V]`.
     c. Per ciascuna serie, calcola la soglia critica calibrata con `calibrate_threshold` in `src/shk/stats/calibration.py` (usando `moving_block_indices`, `compute_order_statistic_index` e `oneway_anova_vectorized` con $B=999, \alpha=0.05$) `[V]`.
     d. Determina i rigetti confrontando la F empirica con la soglia calibrata specifica di ciascuna serie `[V]`.
  4. Scrive le 24 righe risultanti in `results/us_c2_anova_autocorrelation.csv` `[V]`.
  5. Genera la figura a due pannelli ed esporta in `thesis/figures/us_c2_anova_autocorrelation.png` `[V]`.

* Flusso 3 — Pipeline dati reali: caricamento protetto, divergenza di de-vigging e walk-forward anti-leakage (Esperimenti US-C3.2, US-C3.3 e US-C3.4):
  1. `scripts/us_c3_2_devig_divergence.py:run_experiment()` legge la configurazione congelata invocando `read_split_config()` in `src/shk/data/split.py` `[V]`.
  2. Carica le partite non-test invocando `load_by_role("training")` e `load_by_role("validation")` in `src/shk/data/split.py` (che delega a `load_all_seasons` in `src/shk/data/loading.py`, impedendo l'accesso alle stagioni bloccate) e concatena i DataFrame `[V]`.
  3. Invoca `compute_divergence_table` in `src/shk/market/divergence.py` per valutare la divergenza su 7 980 partite con quota Bet365 valida:
     a. Calcola l'overround con `overround` in `src/shk/market/devig.py` `[V]`.
     b. Applica i tre metodi di de-vigging: `devig_proportional`, `devig_additive` (escludendo mercati non applicabili) e `devig_power` (risolutore Newton-Raphson salvaguardato) in `src/shk/market/devig.py` `[V]`.
     c. Assegna ciascuna quota alla corrispondente fascia con `assign_odds_bin` e aggrega gli spread assoluti e relativi a livello di fascia, stagione e complessivo `[V]`.
  4. Scrive la tabella di 29 righe in `results/us_c3_2_devig_divergence.csv` ed esporta la figura a due pannelli in `thesis/figures/us_c3_2_devig_divergence.png` `[V]`.
  5. In fase di previsione delle scommesse (US-C3.4), `walkforward_split` in `src/shk/data/walkforward.py` scorre le partite in ordine cronologico, esponendo la storia pregressa strictly anteriore e riducendo la singola partita alla sola whitelist pre-partita ottenuta tramite `get_prematch_whitelist` (escludendo quote di chiusura, statistiche e risultati), mentre `assert_no_leakage` verifica l'assenza di contaminazione temporale e di contenuto `[V]`.

Replicazione e divergenze tra flussi ed esecuzioni di test:
* Flusso 1 vs `tests/test_us_c1_2_acceptance.py`:
  * Replicazione: Condividono le definizioni di scenario e il seed master `20260927` importandoli da `src/shk/kelly/scenarios.py` `[V]`.
  * Divergenze: Lo script esplora l'intera griglia di parametri esportando CSV e grafici; i test di accettazione verificano singoli criteri puntuali (asimmetria sovrastima/sottostima, $\text{Var}(c)$ a $\sigma_p=0.0283$, dominanza di $\lambda^*$ su quarto-Kelly) e controllano l'invarianza della matrice esiti `[V]`.
* Flusso 2 vs `tests/test_us_c2_acceptance.py`:
  * Replicazione: Condividono costanti, seed `20260928` e funzioni orchestratrici importandoli da `src/shk/stats/false_rejection.py` `[V]`.
  * Divergenze: Lo script scrive direttamente su disco; i test verificano la corrispondenza dei valori calcolati in memoria con il CSV versionato (usando `math.isclose` per i float) e asseriscono proprietà teoriche (gonfiamento dei falsi rigetti sotto autocorrelazione, monotonicità in $\phi$) `[V]`.
* Flusso 3 vs `tests/test_us_c3_2_acceptance.py`, `tests/test_split.py` e `tests/test_leakage.py`:
  * Replicazione: Condividono costanti, fasce di quota, file di split `config/split.toml` e funzioni di de-vigging e walk-forward importandoli dai moduli di libreria `[V]`.
  * Divergenze: Lo script opera sull'insieme delle 22 stagioni non-test producendo CSV e PNG; i test verificano la consistenza del file CSV versionato (proprietà matematiche della somma a 1 entro 1e-12, limiti di overround medio, massimo spread relativo nella fascia estrema), la correttezza del blocco I/O del test set e il fallimento rilevato su 3 fornitori mutanti deliberatamente affetti da leakage `[V]`. Inoltre, i test che operano sui file grezzi di `data/raw/E0/` vengono saltati con motivo esplicito se la directory locale è assente `[V]`.

### 6. Modello dei dati

* Classi di dominio o dataclass strutturate:
  1. `Scenario` (`src/shk/kelly/scenarios.py`): dataclass congelata (`frozen=True`) per i parametri di simulazione Kelly:
     * `name`: `str`, nome descrittivo `[V]`.
     * `p`: `float`, probabilità reale di successo in $[0, 1]$ `[V]`.
     * `b`: `float`, quota netta decimale ($b > 0$) `[V]`.
     * `T`: `int`, numero di passi temporali ($T > 0$) `[V]`.
     * `M`: `int`, numero di traiettorie stocastiche ($M > 0$) `[V]`.
     * Istanze predefinite: `BASE_SCENARIO` (p=0.60, b=1.0, T=1000, M=10000) e `SUBTLE_SCENARIO` (p=0.52, b=1.0, T=380, M=10000) `[V]`.
  2. `StakingMoments` (`src/shk/kelly/staking.py`): `NamedTuple` per i momenti empirici di $c = \hat{f} / f^*$:
     * `mean_c`: `float`, media campionaria pooled $E[c]$ `[V]`.
     * `mean_c2`: `float`, momento secondo campionario pooled $E[c^2]$ `[V]`.
     * `var_c`: `float`, varianza campionaria pooled $\text{Var}(c) = E[c^2] - (E[c])^2$ `[V]`.
     * `fraction_zero`: `float`, frequenza di puntate nulle `[V]`.
  3. `OneWayAnovaResult` (`src/shk/stats/anova.py`): `NamedTuple` per i risultati dell'ANOVA a una via:
     * `ss_between`: `float`, devianza tra i gruppi `[V]`.
     * `ss_within`: `float`, devianza residua entro i gruppi `[V]`.
     * `ss_total`: `float`, devianza totale `[V]`.
     * `df_between`: `int`, gradi di libertà tra gruppi ($k - 1$) `[V]`.
     * `df_within`: `int`, gradi di libertà entro gruppi ($N - k$) `[V]`.
     * `ms_between`: `float`, quadrato medio tra gruppi `[V]`.
     * `ms_within`: `float`, quadrato medio entro gruppi `[V]`.
     * `f_statistic`: `float`, statistica F di Fisher `[V]`.
     * `p_value`: `float`, p-value associato `[V]`.
  4. `PhiStreams` (`src/shk/stats/false_rejection.py`): `NamedTuple` per i flussi casuali di ciascun $\phi$:
     * `series_rng`: `np.random.Generator`, generatore per le serie AR(1) `[V]`.
     * `perm_rng`: `np.random.Generator`, generatore per le permutazioni del disegno random_2 `[V]`.
     * `boot_seed`: `np.random.SeedSequence`, sequenza di semi per il bootstrap, suddivisa per ciascun $L$ `[V]`.
  5. `RejectionResult` (`src/shk/stats/false_rejection.py`): dataclass congelata (`frozen=True`) per i conteggi di rigetto:
     * `design`: `str`, disegno sperimentale `[V]`.
     * `phi`: `float`, coefficiente AR(1) `[V]`.
     * `method`: `str`, metodo ("nominal" o "block_bootstrap") `[V]`.
     * `block_length`: `str`, lunghezza del blocco ("" per nominale o stringa numerica) `[V]`.
     * `n_series`: `int`, numero di serie simulate (1000) `[V]`.
     * `rejections`: `int`, conteggio dei rigetti `[V]`.
     * `rejection_rate`: `float`, frequenza empirica di rigetto `[V]`.
     * `critical_value_mean`: `float`, valore critico nominale o media delle soglie calibrate `[V]`.
     * `mc_lower_99`: `float`, estremo inferiore intervallo Monte Carlo al 99% `[V]`.
     * `mc_upper_99`: `float`, estremo superiore intervallo Monte Carlo al 99% `[V]`.
     * Metodo `to_row()`: restituisce il record come dizionario per la serializzazione CSV `[V]`.
  6. `ColumnClassification` (`src/shk/data/coverage.py`): `NamedTuple` per i metadati delle colonne CSV:
     * `group_type`: `str` (`1x2_prematch`, `1x2_closing`, `aggregators`, `other_markets`) `[V]`.
     * `group_name`: `str` `[V]`.
     * `source`: `str` (nome bookmaker o aggregatore) `[V]`.
     * `market`: `str` (`1x2`, `over_under_2.5`, `asian_handicap`) `[V]`.
     * `timing`: `str` (`prematch`, `closing`) `[V]`.
     * `kind`: `str` (`odds`, `line`, `count`) `[V]`.
  7. `SplitConfig` (`src/shk/data/split.py`): `NamedTuple` per la configurazione congelata dello split:
     * `frozen_on`: `datetime.date`, data di congelamento `[V]`.
     * `test_unlocked`: `bool`, flag di sblocco del test set `[V]`.
     * `test_unlocked_on`: `datetime.date | str`, data di sblocco (o stringa vuota) `[V]`.
     * `training`: `tuple[str, ...]`, stagioni di training `[V]`.
     * `validation`: `tuple[str, ...]`, stagioni di validazione `[V]`.
     * `test`: `tuple[str, ...]`, stagioni di test `[V]`.
  8. Eccezioni di dominio personalizzate:
     * `TestSetLockedError` (`src/shk/data/split.py`): sottoclasse di `RuntimeError` con `__test__ = False`, sollevata quando si tenta di accedere al test set bloccato `[V]`.
     * `LeakageError` (`src/shk/data/walkforward.py`): sottoclasse di `RuntimeError`, sollevata quando viene rilevato data leakage temporale o di contenuto `[V]`.

* Strutture dati in circolo:
  1. Matrice di esiti (`outcomes`): `np.ndarray` shape `(M, T)`, `dtype=bool` (`True` = vincita) `[V]`.
  2. Matrice di stime (`p_hat`): `np.ndarray` shape `(M, T)` o float, in $[0.0, 1.0]$ `[V]`.
  3. Frazioni di scommessa (`fractions`): scalare float o `np.ndarray` broadcastabile a `(M, T)`, in $[0.0, 1.0)$ `[V]`.
  4. Matrice delle traiettorie di log-wealth (`paths`): `np.ndarray` shape `(M, T + 1)`, `dtype=float64`, con colonna 0 nulla `[V]`.
  5. Matrice di serie temporali (`series`): `np.ndarray` shape `(m, n)`, `dtype=float64` `[V]`.
  6. Vettore di etichette (`labels`): `np.ndarray` 1D shape `(N,)`, `dtype=int64`, con classi $0..k-1$ `[V]`.
  7. Matrice di quote decimali (`odds`): `np.ndarray` 2D shape `(N, n)` con $n \ge 2$, `dtype=float64`, valori strettamente $> 1.0$ e finiti `[V]`.
  8. Matrice di probabilità de-viggati (`q`): `np.ndarray` 2D shape `(N, n)`, `dtype=float64`, con somma per riga pari a 1 entro 1e-12 (o `np.nan` per mercati non applicabili nel metodo additivo) `[V]`.
  9. DataFrame consolidati di partite (`df`): `pd.DataFrame` contenente partite con colonna `season` (stringa `YYYY-YY`), `Date` (datetime64), quote decimali e colonne informative `[V]`.
  10. Whitelist di colonne pre-partita: tupla di stringhe ottenuta per inclusione esplicita di identificativi e quote pre-partita `[V]`.

* Schema di persistenza:
  * Nessun database relazionale o ORM presente nel codebase `[V]`.
  * Configurazione dichiarativa versionata su file TOML:
    * `config/split.toml` `[V]`.
  * Persistenza dei risultati sperimentali su file flat CSV versionati in Git:
    * `results/us_c1_1_growth_vs_lambda.csv` (10 colonne) `[V]`.
    * `results/us_c1_2_estimation_error.csv` (12 colonne, 46 righe) `[V]`.
    * `results/us_c2_anova_autocorrelation.csv` (10 colonne, 24 righe) `[V]`.
    * `results/us_c3_1_data_coverage.csv` (12 colonne, 477 righe) `[V]`.
    * `results/us_c3_2_devig_divergence.csv` (19 colonne, 29 righe) `[V]`.
  * Persistenza dei grafici per la tesi su file PNG versionati in Git:
    * `thesis/figures/us_c1_1_growth_vs_lambda.png` `[V]`.
    * `thesis/figures/us_c1_2_estimation_error.png` `[V]`.
    * `thesis/figures/us_c2_anova_autocorrelation.png` `[V]`.
    * `thesis/figures/us_c3_1_data_coverage.png` `[V]`.
    * `thesis/figures/us_c3_2_devig_divergence.png` `[V]`.
  * Storage dei dati grezzi su file system locale:
    * File CSV non versionati in `data/raw/E0/` (da `1993-94.csv` a `2023-24.csv`, esclusi tramite `.gitignore`) `[V]`.

### 7. Convenzioni in vigore

* Naming:
  * Moduli e pacchetti: `snake_case` (`shk`, `kelly`, `stats`, `data`, `market`, `core.py`, `simulate.py`, `estimation.py`, `staking.py`, `scenarios.py`, `metrics.py`, `anova.py`, `timeseries.py`, `calibration.py`, `false_rejection.py`, `loading.py`, `coverage.py`, `split.py`, `walkforward.py`, `devig.py`, `divergence.py`) `[V]`.
  * Funzioni e variabili: `snake_case` (`kelly_fraction`, `draw_outcomes`, `simulate_growth`, `oneway_anova`, `generate_ar1_series`, `calibrate_threshold`, `load_all_seasons`, `read_split_config`, `load_by_role`, `classify_column`, `devig_proportional`, `devig_power`, `walkforward_split`, `assert_no_leakage`) `[V]`.
  * Classi e tipi: `PascalCase` (`Scenario`, `StakingMoments`, `OneWayAnovaResult`, `PhiStreams`, `RejectionResult`, `ColumnClassification`, `SplitConfig`, `TestSetLockedError`, `LeakageError`) `[V]`.
  * Costanti: `UPPER_CASE` (`SEED`, `BASE_SCENARIO`, `SUBTLE_SCENARIO`, `PHI_VALUES`, `N_OBS`, `N_SERIES`, `ALPHA`, `SEED_C2`, `BLOCK_LENGTHS`, `N_BOOT`, `DEFAULT_DATA_DIR`, `DEFAULT_SPLIT_CONFIG_PATH`, `COVERAGE_CSV_COLUMNS`, `NON_ODDS_COLUMNS`, `ODDS_BINS`, `REFERENCE_EDGE`, `MAX_NEWTON_ITERATIONS`, `PREMATCH_IDENTIFIERS`) `[V]`.
  * Variabili matematiche: simboli convenzionali della letteratura ($p, b, f, T, M, b_0, \lambda, \sigma_p, c, \delta, \phi, n, m, k, N, L, B, \alpha, \pi, S, q$) `[V]`.
  * File e funzioni di test: prefisso `test_` `[V]`.
* Organizzazione dei file:
  * Codice di libreria modulare sotto `src/shk/` `[V]`.
  * Suite di test sotto `tests/` `[V]`.
  * Script di simulazione ed esperimento sotto `scripts/` `[V]`.
  * File di configurazione congelati sotto `config/` `[V]`.
  * Tabelle CSV dei risultati in `results/` e figure in `thesis/figures/` `[V]`.
  * Tracciamento operativo del backlog, protocollo e report in `.agent/` `[V]`.
* Stile e tipizzazione:
  * Type hints completi su argomenti e valori di ritorno in tutte le funzioni pubbliche e private `[V]`.
  * Docstring complete conformi allo stile NumPy con sezioni `Parametri`, `Restituisce`, `Solleva` (o `Campi`, `Attributi`) `[V]`.
* Gestione degli errori:
  * Validazione difensiva all'inizio di ogni funzione: `ValueError` per valori o forme non conformi, `TypeError` per tipi non consentiti `[V]`.
  * Validazione rigorosa del tipo degli interi: `bool` e `float` sollevano `TypeError` nel codice recente di C2 e C3, mentre gli interi nativi e `np.integer` vengono accettati `[V]`.
  * Eccezioni specializzate di runtime per la violazione di vincoli strutturali (`TestSetLockedError`, `LeakageError`) `[V]`.
  * Assenza totale di blocchi `try...except` nel codice sorgente di `src/` e negli script di `scripts/` `[V]`.
  * Messaggi di eccezione rigorosamente in lingua inglese `[V]`.
* Logging e output:
  * Nessun framework o modulo di logging utilizzato nel codebase `[V]`.
  * Nessuna chiamata a `print()` presente nei sorgenti di `src/` o negli script di `scripts/` `[V]`.
* Lingua:
  * Commenti e docstring redatti in lingua italiana `[V]`.
  * Identificatori, messaggi di errore e nomi dei test redatti in lingua inglese `[V]`.
* Pattern architetturali ricorrenti:
  * Vettorizzazione NumPy completa per eliminare loop espliciti sulle simulazioni `[V]`.
  * Isolamento e tracciabilità stocastica passando l'RNG come argomento (`Generator`) e derivando flussi indipendenti tramite `SeedSequence.spawn` `[V]`.
  * Struttura fissa degli script di esperimento: `matplotlib.use("Agg")` prima di pyplot; funzione `run_experiment()` senza parametri richiamata da `if __name__ == "__main__":`; salvataggio CSV con `csv.DictWriter` e salvataggio PNG con `dpi=150` `[V]`.
  * Barriera I/O per i dati reali: accesso obbligato tramite `load_by_role`, con test di guardia AST che vieta l'uso di `load_all_seasons` all'esterno dei 4 file ammessi `[V]`.
  * Costruzione per inclusione esplicita (whitelist) dei campi pre-partita per impedire data leakage nel walk-forward `[V]`.
* Incoerenze rilevate tra parti diverse del progetto (escluse le convenzioni deliberate):
  1. `expected_final_wealth` è implementata in `src/shk/kelly/core.py`, ma non è re-esportata in `src/shk/kelly/__init__.py` a differenza di `kelly_fraction` e `log_growth_rate` `[V]`.
  2. Disallineamento tra lockfile locale e CI: alla radice è presente `uv.lock`, ma non è stato aggiornato con `pandas` aggiunto in S3 (T14) `[V]`, e il workflow di CI `.github/workflows/test.yml` installa le dipendenze con `pip install -e ".[dev]"` senza vincolare le versioni `[V]`.
  3. Validazione degli interi non uniforme tra C1 e C2/C3: `draw_outcomes` e `noisy_estimates` in C1 non validano il tipo esatto degli interi $T$ e $M$ (accettando `True` come 1) `[V]`, a differenza dei moduli di C2 e C3 (`generate_ar1_series`, `moving_block_indices`, `oneway_anova_vectorized`, `load_all_seasons`, `walkforward_split`) che sollevano `TypeError` per i booleani e tipi errati `[V]`.
  4. Contraddizione documentale nella docstring di `src/shk/stats/calibration.py`: nello schema (a.1) per l'ANOVA F il dato indicato è "la serie della risposta", in contrasto con il principio generale (c) che impone al chiamante di imporre $H_0$ prima di calibrare `[V]`.
  5. Incompletezza dei test di validazione in `tests/test_metrics.py`: `test_metrics_error_conditions` verifica il sollevamento di `ValueError` su array 1D o con colonne insufficienti per quattro metriche, ma omette `median_final_wealth` e `mean_final_wealth` `[V]`.
  6. Hardcoding dei parametri nello script `scripts/us_c1_1_growth_vs_lambda.py`: i parametri di simulazione sono cablati dentro `run_experiment()` anziché essere importati da un modulo di configurazione condiviso (come fatto da C1.2 con `scenarios.py`, C2 con `false_rejection.py` e C3 con `split.toml`/`divergence.py`) `[V]`.
  7. I test sui dati reali vengono skippati in CI: i file CSV di `data/raw/E0/` sono esclusi dal versionamento in `.gitignore`, quindi la pipeline di CI non esegue mai i test reali di `test_data_loading.py`, `test_split.py`, `test_leakage.py` e `test_us_c3_2_acceptance.py` `[V]`.
  8. In `tests/test_devig.py`, il test `test_extreme_markets` esclude i mercati NaN per il metodo additivo senza verificare esplicitamente che i NaN siano effettivamente attesi, rischiando di mascherare eventuali NaN spuri `[V]`.

### 8. Test

* Posizione dei test: Directory `tests/` `[V]`.
* Tipologia di test:
  * Test unitari analitici sulle formule matematiche del criterio di Kelly (`tests/test_kelly_core.py`) `[V]`.
  * Test unitari di simulazione, broadcasting e log-wealth (`tests/test_simulate.py`) `[V]`.
  * Test unitari su perturbazioni e rumore gaussiano con clipping (`tests/test_estimation.py`) `[V]`.
  * Test unitari su frazioni di Kelly, momenti empirici e regola plug-in (`tests/test_staking.py`) `[V]`.
  * Test unitari sulle metriche di rendimento e drawdown (`tests/test_metrics.py`) `[V]`.
  * Test di conformità su ANOVA a una via, concordanza con `scipy.stats.f_oneway` e vettorizzazione (`tests/test_anova.py`) `[V]`.
  * Test unitari e statistici su serie AR(1), riproducibilità, varianza e autocorrelazione (`tests/test_timeseries.py`) `[V]`.
  * Test unitari su indici di blocco, statistica d'ordine e calibrazione della soglia per moving block bootstrap (`tests/test_calibration.py`) `[V]`.
  * Test unitari e di robustezza sul caricamento delle stagioni E0, decodifica e date (`tests/test_data_loading.py`) `[V]`.
  * Test unitari sulla classificazione di colonne e audit di copertura (`tests/test_coverage.py`) `[V]`.
  * Test unitari e architetturali sullo split congelato, blocco del test set e guardia AST (`tests/test_split.py`) `[V]`.
  * Test unitari sui metodi di de-vigging proporzionale, additivo e power, valori di riferimento e mercati estremi (`tests/test_devig.py`) `[V]`.
  * Test unitari e sui mutanti anti-leakage per il fornitore walk-forward (`tests/test_leakage.py`) `[V]`.
  * Test di accettazione end-to-end per US-C1.1 marcati `@pytest.mark.slow` (`tests/test_us_c1_1_acceptance.py`) `[V]`.
  * Test di accettazione per US-C1.2, veloci e marcati slow (`tests/test_us_c1_2_acceptance.py`) `[V]`.
  * Test di accettazione per US-C2.2 e US-C2.3, veloci e marcati slow (`tests/test_us_c2_acceptance.py`) `[V]`.
  * Test di accettazione per US-C3.2 sulla divergenza tra metodi di de-vigging (`tests/test_us_c3_2_acceptance.py`) `[V]`.
* Modalità di lancio:
  * Esecuzione predefinita (solo test veloci, esclude i test slow tramite `addopts = "-m 'not slow'"` in `pyproject.toml`): `pytest -v` `[V]`.
  * Esecuzione tramite l'interprete Python del venv: `.\.venv\Scripts\python.exe -m pytest -v` `[D]`.
  * Esecuzione dei soli test lenti di accettazione Monte Carlo: `pytest -m slow` `[D]`.
  * Esecuzione integrale di tutti i test (inclusi i test slow): `pytest -o addopts=""` `[D]`.
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
    * `ALPHA`, `BLOCK_LENGTHS`, `CSV_COLUMNS`, `FLOAT_CSV_COLUMNS`, `DESIGNS`, `DESIGN_CONTIGUOUS_2`, `DESIGN_CONTIGUOUS_38`, `DESIGN_RANDOM_2`, `METHOD_BLOCK_BOOTSTRAP`, `N_OBS`, `N_SERIES`, `PHI_VALUES`, `SEED_C2`, `RejectionResult`, `compute_nominal_rejection_rates`, `compute_calibrated_rejection_rates`, `critical_value_nominal`, `make_design_labels`, `monte_carlo_interval_99` (in `test_us_c2_acceptance.py`) `[V]`.
    * `DEFAULT_DATA_DIR`, `load_all_seasons` (in `test_data_loading.py`, `test_split.py`) `[V]`.
    * `COVERAGE_CSV_COLUMNS`, `NON_ODDS_COLUMNS`, `ColumnClassification`, `classify_column`, `compute_coverage` (in `test_coverage.py`) `[V]`.
    * `DEFAULT_SPLIT_CONFIG_PATH`, `TestSetLockedError`, `SplitConfig`, `read_split_config`, `load_by_role` (in `test_split.py`, `test_us_c3_2_acceptance.py`, `test_leakage.py`) `[V]`.
    * `implied_probabilities`, `overround`, `devig_proportional`, `devig_additive`, `devig_power` (in `test_devig.py`) `[V]`.
    * `ODDS_BINS`, `ODDS_BIN_LABELS`, `REFERENCE_EDGE`, `DIVERGENCE_CSV_COLUMNS`, `assign_odds_bin`, `compute_divergence_table` (in `test_us_c3_2_acceptance.py`) `[V]`.
    * `LeakageError`, `get_prematch_whitelist`, `check_leakage`, `walkforward_split`, `assert_no_leakage` (in `test_leakage.py`) `[V]`.
  * Funzioni e classi pubbliche che NON compaiono MAI nelle asserzioni dei test:
    * `expected_final_wealth` (definita in `src/shk/kelly/core.py:97-144`, utilizzata nello script C1.1, priva di unit test) `[V]`.
    * `PhiStreams` (definita in `src/shk/stats/false_rejection.py:48-65`, utilizzata internamente, non asserita direttamente nei test) `[V]`.
    * `spawn_c2_generators` (definita in `src/shk/stats/false_rejection.py:248-297`, non invocata direttamente nei test) `[V]`.
    * `METHOD_NOMINAL` (definita in `src/shk/stats/false_rejection.py:22`, non usata direttamente nei test) `[V]`.
    * `MAX_NEWTON_ITERATIONS` (definita in `src/shk/market/devig.py:7`, costante non testata puntualmente) `[V]`.
    * `GROUP_TYPE_ORDER` (definita in `src/shk/data/coverage.py:68-74`, usata nello script C3.1, non asserita nei test) `[V]`.
    * `PREMATCH_IDENTIFIERS` (definita in `src/shk/data/walkforward.py:13-15`, non testata direttamente) `[V]`.
    * `B365_ODDS_COLUMNS` (definita in `src/shk/market/divergence.py:33`, non asserita direttamente nei test) `[V]`.
    * `run_experiment` dei cinque script in `scripts/` (privi di test di integrazione automatizzati) `[V]`.
  * Nota vincolo: Conteggi numerici di test passati, tempi di esecuzione o percentuali esatte di copertura non vengono riportati in quanto richiederebbero l'esecuzione della suite, vietata dal vincolo di sola lettura `[V]`. Se tali informazioni fossero ritenute indispensabili, servirebbe eseguire la suite di test `[V]`.
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
  * `tests/test_devig.py:28-31, 44-47, 60-63`: tolleranza `5e-6` su probabilità e `5e-5` su esponente k `[V]`.
  * `tests/test_devig.py:67, 82, 90, 95, 190, 194, 195, 204, 207, 208`: tolleranza numerica somma a uno `<= 1e-12` `[V]`.
  * `tests/test_devig.py:76, 162`: seed fisso `np.random.default_rng(20260929)` `[V]`.
  * `tests/test_devig.py:112-116, 121-125`: tolleranza numerica `atol=1e-15` su mercati S=1 `[V]`.
  * `tests/test_us_c3_2_acceptance.py:161-163`: tolleranza errore somma a uno `<= 1e-12` `[V]`.
  * `tests/test_us_c3_2_acceptance.py:172`: soglia empirica di overround medio complessivo `0.01 <= ovr <= 0.15` `[V]`.
  * `tests/test_us_c3_2_acceptance.py:248`: tolleranza di ricalcolo float da dati reali `math.isclose(f_csv, f_rec, rel_tol=1e-12, abs_tol=1e-12)` `[V]`.

### 9. Zone fragili

1. Test di accettazione slow con fallimento noto su risultato empirico inatteso (T12):
   * In `tests/test_us_c2_acceptance.py:350-363`, `test_acceptance_calibrated_phi_zero_within_mc_interval` fallisce sistematicamente a $\phi = 0.0$ con $L=20$ (29 rigetti su 1000, sotto l'estremo inferiore dell'intervallo 99% pari a 32.25) `[V]`.
   * La calibrazione viene eseguita sulla serie grezza senza previa imposizione dell'ipotesi nulla $H_0$ `[V]`.
   * Il fallimento è un risultato noto documentato nel backlog; non deve essere alterato allentando i parametri o le tolleranze del test `[V]`.

2. Assenza totale di test automatizzati per `expected_final_wealth`:
   * Implementata in `src/shk/kelly/core.py:97-144` e impiegata nello script `scripts/us_c1_1_growth_vs_lambda.py` `[V]`.
   * Non è richiamata in alcun modulo di test sotto `tests/` `[V]`.
   * Eventuali regressioni analitiche o refactoring errati su tale funzione non verrebbero rilevati dalla suite `[V]`.

3. Rischio di rifiuto da parte di `simulate_growth` per saturazione di stime rumorose a $p̂ = 1.0$:
   * In `src/shk/kelly/estimation.py`, `noisy_estimates` applica `np.clip` saturando i valori in $[0, 1]$ `[V]`.
   * In presenza di stime saturate esattamente a $1.0$, `kelly_staking(1.0, b, lam)` restituisce $\lambda \cdot 1.0$ `[V]`.
   * Con $\lambda \ge 1.0$, la frazione risultante è $\ge 1.0$, valore che `simulate_growth` rifiuta sollevando `ValueError` (`fractions in [0, 1)`) `[V]`.

4. Duplicazione dei parametri di simulazione nello script C1.1:
   * I parametri ($p=0.60, b=1.0, T=1000, M=10000$, seed `20260905`, griglia di 51 punti) sono hardcoded sia in `scripts/us_c1_1_growth_vs_lambda.py:30-36` sia in `tests/test_us_c1_1_acceptance.py` `[V]`.
   * Una modifica futura dei parametri dell'esperimento rischia di disallineare lo script pubblicato e i test di accettazione `[V]`.

5. Dipendenze senza vincolo di versione e disallineamento del lockfile in CI:
   * Il file `pyproject.toml` elenca `numpy`, `scipy`, `matplotlib`, `pandas` e `pytest` senza specificare vincoli di versione minimi o precisi `[V]`.
   * Il lockfile `uv.lock` alla radice non è aggiornato con `pandas` aggiunto durante la Story S3 `[V]`.
   * Il workflow di CI `.github/workflows/test.yml` esegue `pip install -e ".[dev]"` ignorando il file `uv.lock` `[V]`.
   * Aggiornamenti minori delle librerie esterne possono introdurre scostamenti numerici sull'ultima cifra decimale o alterazioni nelle sequenze pseudo-casuali `[D]`.

6. I test slow di accettazione Monte Carlo e i test su dati reali sono esclusi dalla CI:
   * In `pyproject.toml`, l'opzione `addopts = "-m 'not slow'"` esclude tutti i test marcati `@pytest.mark.slow` `[V]`.
   * Il runner GitHub Actions in `.github/workflows/test.yml` esegue unicamente `pytest -v`, saltando i test slow `[V]`.
   * I file in `data/raw/E0/` sono esclusi dal versionamento in `.gitignore`, quindi in CI i test sui dati reali vengono sistematicamente skippati `[V]`.

7. Blocco globale del de-vigging power su mancata convergenza numerica:
   * In `src/shk/market/devig.py`, `devig_power` solleva `RuntimeError` se anche un solo mercato non converge entro la tolleranza 1e-12 in 50 iterazioni `[V]`.
   * In presenza di mercati con quote fortemente anomale o malformate, l'intero batch o l'esperimento viene interrotto bruscamente anziché segnalare o isolare la riga `[V]`.

8. Rigidità del parser di colonne in `src/shk/data/coverage.py`:
   * `classify_column` solleva `ValueError` su qualunque colonna non catalogata esplicitamente nelle sue regole interne `[V]`.
   * L'aggiunta di nuovi CSV con intestazioni leggermente diverse o nuove stagioni storiche interrompe l'audit e l'ingestione walk-forward finché il dizionario interno di classificazione non viene esteso `[V]`.

9. Accoppiamento tra tabelle CSV generate e asserzioni di test:
   * `tests/test_us_c2_acceptance.py` e `tests/test_us_c3_2_acceptance.py` verificano la concordanza con i file CSV versionati su disco `[V]`.
   * Rieseguire gli script in un ambiente con minime discrepanze numeriche o alterare la logica interna senza ri-eseguire e aggiornare i CSV fa fallire i test `[V]`.

10. Vincolo del test di guardia AST su `load_all_seasons`:
    * In `tests/test_split.py`, un test di guardia ispeziona l'AST dell'intero repository e fallisce se `load_all_seasons` viene richiamata o importata al di fuori dei quattro file ammessi (`loading.py`, `split.py`, `coverage.py`, `us_c3_1_data_coverage.py`) `[V]`.
    * Qualsiasi nuovo codice che necessiti dei dati deve necessariamente passare da `load_by_role` `[V]`.

11. Stagione di training 2000-01 priva di quote Bet365:
    * `config/split.toml` include `2000-01` nel ruolo di training, ma tale stagione è priva delle quote `B365H`, `B365D`, `B365A` `[V]`.
    * Qualsiasi pipeline basata su quote Bet365 (come l'esperimento US-C3.2) finisce per escludere integralmente tutte le 380 partite di questa stagione di training `[V]`.

### 10. Limiti di questa mappa

* Cosa non è stato ispezionato e perché:
  * Non è stato eseguito il codice del progetto né la suite di test (`pytest`, script in `scripts/`), in conformità al vincolo assoluto di sola lettura che vieta la creazione di cache o alterazioni dell'ambiente `[V]`.
  * Non sono stati aperti i file binari grafici PNG in `thesis/figures/` (ispezionati solo per esistenza e dimensione) `[V]`.
  * Non sono state lette riga per riga tutte le 11 944 righe dei 31 CSV grezzi in `data/raw/E0/`, verificando solo l'esistenza locale e le regole di caricamento e test `[V]`.
* Cosa resta incerto:
  * Non è verificato se la suite di test completa sia attualmente verde al 100% nell'ambiente locale o se il test slow noto continui ad essere l'unico fallimento `[D]`.
  * L'esito dell'ultima build della pipeline GitHub Actions su `main` non è verificato (non è stata interrogata l'API remota di GitHub) `[D]`.
  * Non è nota la decisione finale circa la risoluzione metodologica del test slow T12 (imposizione di $H_0$ centrata sul bootstrap) `[D]`.
  * Non è nota la decisione sull'armonizzazione della gestione dipendenze (`uv.lock` disallineato rispetto all'aggiunta di pandas in `pyproject.toml`) `[D]`.
* Quali sezioni sono in prevalenza `[D]`:
  * Nessuna sezione è in prevalenza `[D]`. Le sezioni sono a larga maggioranza composte da affermazioni verificate `[V]`, con deduzioni `[D]` limitate unicamente a comandi shell ipotetici non scritti nei file di configurazione (es. `uv sync`, `hatch build`), a effetti collaterali ipotetici di librerie esterne non verificate a runtime, e al comportamento futuro su dati non ancora presenti.
* Domande per chi lavora sul progetto:
  1. Si intende aggiornare il file `uv.lock` con la dipendenza `pandas` introdotta in C3, oppure il progetto intende convergere unicamente su `pip` e `pyproject.toml` per l'ambiente di CI e di sviluppo?
  2. Come si intende gestire nella tesi e nei modelli previsionali di C4/C8 la stagione di training `2000-01`, vista l'assenza completa delle quote Bet365 pre-partita? Verrà sostituita con un'altra stagione o si impiegherà un bookmaker alternativo (es. IW, WH, GB)?
  3. Per quanto riguarda il test slow noto di C2 (T12), è pianificato un task dedicato per imporre l'ipotesi nulla $H_0$ mediante centratura dei residui prima del moving block bootstrap, allineando codice e docstring?
  4. Si prevede di introdurre un meccanismo di caching o di mock sintetico nella pipeline di CI per consentire l'esecuzione automatizzata dei test di integrazione sui dati reali senza dover versionare i CSV di `data/raw/E0/`?

### 11. Comandi eseguiti

1. `git status` (verifica dello stato del branch, del working tree e dell'indice) `[V]`.
2. `git log -n 5 --oneline` (ispezione della cronologia recente dei commit sul branch `main`) `[V]`.
3. `git branch -a` (elenco dei branch locali e remoti configurati) `[V]`.
4. `git remote -v` (verifica delle URL dei remote configurati) `[V]`.
5. `git diff` (verifica puntuale dell'assenza di differenze nel working tree) `[V]`.
6. `git log -n 1 --stat 90a77a1` (ispezione dei file toccati e introdotti dal commit C3 #17) `[V]`.
7. `git log --name-only -n 5` (ispezione della cronologia e dei file tracciati nei commit recenti) `[V]`.
8. `git status --ignored` (ispezione dei file e delle directory ignorate nel filesystem locale) `[V]`.
9. `git log -n 1 --stat 115e600` (ispezione dei file toccati e introdotti dal commit C2 #16) `[V]`.
