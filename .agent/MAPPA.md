Mappa completa — 2026-09-27 — R1

### 0. Stato del repository

* Percorso assoluto della radice: `c:\Users\malse\Documents\GitHub\structural_hybrid_kelly` `[V]`.
* Branch corrente: `main` `[V]`.
* Stato del working tree: pulito (`working tree clean`) `[V]`.
* File modificati: nessuno `[V]`.
* File non tracciati: nessuno `[V]`.
* File ignorati rilevati nel filesystem: `.pytest_cache/`, `.venv/`, `src/shk/__pycache__/`, `src/shk/kelly/__pycache__/`, `tests/__pycache__/` `[V]`.
* Ultimi commit (totale 4 nella storia del repository):
  * `a7420cb` `create c1 (#5)` `[V]`
  * `6187309` `Feature/us c1.1 trade off crescita/varianza (#4)` `[V]`
  * `e5f339b` `Add GitHub Actions workflow for testing` `[V]`
  * `2da1266` `Initial commit` `[V]`
* Remote configurati:
  * `origin`: `https://github.com/Fede046/structural_hybrid_kelly.git` (fetch) `[V]`
  * `origin`: `https://github.com/Fede046/structural_hybrid_kelly.git` (push) `[V]`
* Stato rispetto al remote: `main` è allineato con `origin/main` (0 commit avanti, 0 commit indietro) `[V]`.
* Altri branch locali: `feature/US-C1.1-Trade-off-crescita/varianza` `[V]`.

### 1. Identikit

* Nome del progetto: `structural-hybrid-kelly` `[V]`.
* Descrizione: Libreria scientifica e ambiente di simulazione per l'analisi analitica e stocastica del criterio di Kelly e dei modelli ibridi strutturali `[V]`. Modella strategie di scommessa e investimento, valutando il trade-off crescita/varianza e metriche di rischio su traiettorie di capitale `[V]`.
* Stack: Python `[V]`.
* Linguaggi: Python 3 `[V]`.
* Versione Python minima supportata: `>=3.11` (specificata in `pyproject.toml`) `[V]`.
* Versione Python usata in CI: `3.12` (specificata in `.github/workflows/test.yml`) `[V]`.
* Versione del pacchetto: `0.1.0` (specificata in `pyproject.toml` e in `src/shk/__init__.py`) `[V]`.
* Gestore di pacchetti: `uv` (attestato dal lockfile `uv.lock` alla radice) `[V]`, con `pip` usato nella pipeline CI `[V]`.
* Build system: Hatchling (`hatchling.build` specificato in `pyproject.toml`) `[V]`.

### 2. Come si esegue

* Installazione dipendenze:
  * Tramite pip (attestato in CI): `pip install -e ".[dev]"` `[V]`.
  * Tramite uv: `uv sync` `[D]`.
* Avvio in sviluppo:
  * Non esiste un server interattivo né un daemon `[V]`.
  * Installazione in modalità editabile con `pip install -e .` `[V]`.
* Build:
  * Comando di build Hatch: `hatch build` oppure `python -m build` `[D]`.
* Lancio dei test:
  * Test veloci (suite predefinita, esclude i test slow tramite `addopts` in `pyproject.toml`): `pytest -v` `[V]`.
  * Test lenti di accettazione: `pytest -m "slow"` oppure `pytest -o addopts=""` `[D]`.
* Esecuzione script di simulazione ed esperimenti:
  * Esperimento US-C1.1: `python scripts/us_c1_1_growth_vs_lambda.py` `[D]`.
* Variabili d'ambiente richieste:
  * Nessuna variabile d'ambiente richiesta `[V]`.
* File di configurazione richiesti:
  * `pyproject.toml` (configurazione del pacchetto, dipendenze, build-system e parametri pytest) `[V]`.
  * Nessun file `.env` o file di configurazione runtime presente o richiesto `[V]`.
  * La directory `config/` contiene unicamente un file `.gitkeep` `[V]`.

### 3. Albero delle directory

* `.` (radice): File di configurazione del repository, licenza, lockfile e note di progetto `[V]`.
* `.github/workflows/`: Workflow di automazione CI/CD per GitHub Actions `[V]`.
* `config/`: Directory predisposta per file di configurazione futuri (attualmente vuota con `.gitkeep`) `[V]`.
* `data/raw/`: Directory per storage di dataset grezzi (attualmente vuota con `.gitkeep`) `[V]`.
* `results/`: Directory di destinazione dei risultati numerici e report CSV delle simulazioni `[V]`.
* `scripts/`: Script eseguibili autonomi per conduzione esperimenti e generazione grafici `[V]`.
* `src/shk/`: Radice del codice sorgente del pacchetto Python `shk` `[V]`.
* `src/shk/kelly/`: Modulo core dedicato alle formule matematiche, simulatore stocastico e metriche di Kelly `[V]`.
* `tests/`: Suite completa di test unitari e di accettazione basati su pytest `[V]`.
* `thesis/figures/`: Directory per le figure e i grafici generati destinati alla tesi/relazione `[V]`.

### 4. Moduli principali

Il repository contiene 6 moduli Python applicativi in totale (sono esclusi da questo elenco i 4 file di test residenti in `tests/`, trattati nella sezione 8 `[V]`):

1. `src/shk/__init__.py`
   * Responsabilità: Inizializza il package principale `shk` ed espone la versione del software `[V]`.
   * Espone: `__version__` `[V]`.
   * Dipendenze interne: Nessuna `[V]`.

2. `src/shk/kelly/__init__.py`
   * Responsabilità: Fornisce l'interfaccia pubblica di alto livello del modulo Kelly re-esportando le funzioni analitiche principali `[V]`.
   * Espone: `kelly_fraction`, `log_growth_rate` (tramite `__all__`) `[V]`.
   * Dipendenze interne: `src/shk/kelly/core.py` `[V]`.

3. `src/shk/kelly/core.py`
   * Responsabilità: Implementa le formule analitiche esatte in forma chiusa per il criterio di Kelly su scommesse binarie `[V]`.
   * Espone: `kelly_fraction(p, b)`, `log_growth_rate(f, p, b)`, `expected_final_wealth(f, p, b, T, b0=1.0)` `[V]`.
   * Dipendenze interne: Nessuna `[V]`.

4. `src/shk/kelly/simulate.py`
   * Responsabilità: Esegue simulazioni Monte Carlo vettorizzate per la generazione di esiti bernoulliani e traiettorie di log-wealth `[V]`.
   * Espone: `draw_outcomes(p, T, M, rng)`, `log_wealth_paths(outcomes, f, b)` `[V]`.
   * Dipendenze interne: Nessuna `[V]`.

5. `src/shk/kelly/metrics.py`
   * Responsabilità: Calcola metriche statistiche e indicatori di rischio su insiemi di traiettorie di log-wealth `[V]`.
   * Espone: `final_log_wealth(paths)`, `median_growth_rate(paths)`, `median_final_wealth(paths)`, `mean_final_wealth(paths)`, `max_drawdown(paths)`, `fraction_below_start(paths)` `[V]`.
   * Dipendenze interne: Nessuna (dipende solo dalle funzioni interne al modulo) `[V]`.

6. `scripts/us_c1_1_growth_vs_lambda.py`
   * Responsabilità: Esegue l'esperimento completo Monte Carlo US-C1.1 esportando i risultati aggregati in CSV e la figura a tre pannelli `[V]`.
   * Espone: `run_experiment()` e blocco CLI `__main__` `[V]`.
   * Dipendenze interne: `src/shk/kelly/core.py`, `src/shk/kelly/simulate.py`, `src/shk/kelly/metrics.py` `[V]`.

### 5. Punti di ingresso e flussi

Punti di ingresso dell'applicazione:
* Script CLI: `python scripts/us_c1_1_growth_vs_lambda.py` `[V]`.
* Framework di test: `pytest` `[V]`.
* Libreria importabile: `import shk` o `import shk.kelly` da script o interpreti esterni `[V]`.

Flussi principali dell'applicazione:

* Flusso 1 — Simulazione Monte Carlo ed esportazione risultati (esperimento US-C1.1):
  1. `scripts/us_c1_1_growth_vs_lambda.py:run_experiment()` calcola la frazione ottimale $f^*$ chiamando `kelly_fraction(p, b)` in `src/shk/kelly/core.py` `[V]`.
  2. Genera una matrice condivisa di esiti bernoulliani chiamando `draw_outcomes(p, t_steps, m_trajectories, rng)` in `src/shk/kelly/simulate.py` `[V]`.
  3. Per ciascun moltiplicatore $\lambda \in [0.0, 2.5]$ (51 punti):
     a. Calcola le traiettorie chiamando `log_wealth_paths(outcomes, f_val, b)` in `src/shk/kelly/simulate.py` `[V]`.
     b. Calcola le metriche empiriche chiamando `median_growth_rate`, `median_final_wealth`, `mean_final_wealth`, `max_drawdown`, `fraction_below_start` in `src/shk/kelly/metrics.py` `[V]`.
     c. Rilascia la memoria dell'array delle traiettorie con `del paths` `[V]`.
     d. Calcola i benchmark teorici chiamando `log_growth_rate` e `expected_final_wealth` in `src/shk/kelly/core.py` `[V]`.
  4. Scrive la tabella dei record su `results/us_c1_1_growth_vs_lambda.csv` tramite `csv.DictWriter` `[V]`.
  5. Costruisce il grafico a tre pannelli con Matplotlib e lo salva su `thesis/figures/us_c1_1_growth_vs_lambda.png` `[V]`.

* Flusso 2 — Suite di test di accettazione US-C1.1:
  1. Il runner pytest invoca i test in `tests/test_us_c1_1_acceptance.py` marcati con `@pytest.mark.slow` `[V]`.
  2. I test rigenerano indipendentemente le estrazioni chiamando `draw_outcomes` in `src/shk/kelly/simulate.py` con lo stesso seed `20260905` `[V]`.
  3. Iterano sui valori di $\lambda$ invocando `log_wealth_paths` e valutano `median_growth_rate` e `max_drawdown` da `src/shk/kelly/metrics.py` `[V]`.
  4. Verificano tramite asserzioni che il picco della mediana cada a $\lambda = 1.0$, la non-decrescenza del drawdown, lo zero-crossing a $\lambda = 1.946$ e la crescita negativa a $\lambda = 2.5$ `[V]`.

* Flusso 3 — Calcolo analitico puro del criterio di Kelly (uso come libreria):
  1. Un client esterno importa le funzioni da `shk.kelly` o `shk.kelly.core` `[V]`.
  2. Invoca `kelly_fraction(p, b)` per ricavare la frazione ottima $f^*$ con validazione dei parametri `[V]`.
  3. Invoca `log_growth_rate(f, p, b)` o `expected_final_wealth(f, p, b, T, b0)` per valutare la crescita teorica senza eseguire simulazioni campionarie `[V]`.

Replicazione e divergenza tra Flusso 1 e Flusso 2:
* Replicazione: Lo script `scripts/us_c1_1_growth_vs_lambda.py` e il modulo `tests/test_us_c1_1_acceptance.py` implementano esattamente gli stessi parametri di simulazione ($p=0.60$, $b=1.0$, $T=1000$, $M=10000$, seed `20260905`, griglia di 51 punti da $0.0$ a $2.5$) `[V]`.
* Divergenze:
  1. Lo script calcola tutte e 5 le metriche empiriche e i valori analitici, mentre i test di accettazione calcolano unicamente `median_growth_rate` e `max_drawdown` `[V]`.
  2. Lo script esegue la generazione della matrice di esiti una volta sola e itera su tutti i $\lambda$, mentre i test di accettazione ripetono l'estrazione e i cicli separatamente all'interno di ogni singola funzione di test `[V]`.
  3. Lo script produce artefatti persistenti su disco (file CSV e figura PNG), mentre i test verificano unicamente asserzioni numeriche in memoria `[V]`.

### 6. Modello dei dati

* Classi di dominio o ORM: nessuna classe di dominio definita nel codebase `[V]`.
* Schema di persistenza strutturato (database/tabelle): nessuno `[V]`.
* Strutture dati in circolo:
  1. Scalari primitivi:
     * `p`: `float`, probabilità di vincita vincolata a $[0.0, 1.0]$ `[V]`.
     * `b`: `float`, quota decimale netta strettamente positiva ($b > 0$) `[V]`.
     * `f`: `float`, frazione di bankroll vincolata a $[0.0, 1.0)$ `[V]`.
     * `T`: `int`, numero di scommesse/passi temporali ($T > 0$ o $T \ge 0$) `[V]`.
     * `M`: `int`, numero di traiettorie indipendenti ($M > 0$) `[V]`.
     * `b0`: `float`, capitale iniziale normalizzato ($b_0 > 0$, default 1.0) `[V]`.
  2. Matrice di esiti (`outcomes`):
     * `np.ndarray`, shape `(M, T)`, `dtype=bool` `[V]`.
     * Ciascun elemento rappresenta l'esito della scommessa ($t$) per la traiettoria ($m$): `True` = vincita, `False` = perdita `[V]`.
  3. Matrice delle traiettorie di log-wealth (`paths`):
     * `np.ndarray`, shape `(M, T + 1)`, `dtype=float64` `[V]`.
     * Contiene $\ln(B_t / B_0)$ al variare di $t \in [0, T]$ per ciascuna traiettoria `[V]`.
     * La colonna 0 è interamente pari a $0.0$, corrispondente a $B_0 = 1.0$ `[V]`.
  4. Vettori di metriche aggregate:
     * `final_log_wealth`: `np.ndarray` 1D di shape `(M,)`, float64 `[V]`.
     * `max_drawdown`: `np.ndarray` 1D di shape `(M,)`, float64 con valori in $[0.0, 1.0)$ `[V]`.
  5. Record tabellari dell'esperimento:
     * Dizionario Python con 10 campi numerici (`lambda`, `f`, `median_growth_rate`, `analytic_growth_rate`, `median_final_wealth`, `mean_final_wealth_mc`, `mean_final_wealth_analytic`, `drawdown_median`, `drawdown_p95`, `fraction_below_start`) `[V]`.
  6. File di persistenza flat:
     * `results/us_c1_1_growth_vs_lambda.csv`: esportazione CSV con intestazione dei campi tabellari sopra citati `[V]`.

### 7. Convenzioni in vigore

* Naming:
  * Moduli e package: snake_case (`shk`, `kelly`, `core.py`, `simulate.py`, `metrics.py`) `[V]`.
  * Funzioni: snake_case (`kelly_fraction`, `draw_outcomes`, `log_wealth_paths`, `max_drawdown`) `[V]`.
  * Variabili matematiche: lettere singole o formule standard coerenti con la letteratura ($p, b, f, T, M, b_0, \lambda$) `[V]`.
  * Test: prefisso `test_` per file e funzioni di test `[V]`.
* Organizzazione dei file:
  * Codice di libreria isolato in `src/shk/` `[V]`.
  * Suite di test in `tests/` `[V]`.
  * Script operativi in `scripts/` `[V]`.
  * Artefatti e output numerici separati in `results/` e `thesis/figures/` `[V]`.
* Stile:
  * Type hints completi su argomenti e valori di ritorno delle funzioni `[V]`.
  * Docstring complete conformi allo stile NumPy/Sphinx con blocchi `Parametri`, `Restituisce`, `Solleva` `[V]`.
* Gestione degli errori:
  * Validazione difensiva con sollevamento immediato di `ValueError` e `TypeError` in apertura di funzione in `core.py`, `metrics.py` e `simulate.py:draw_outcomes` `[V]`.
  * Nessun blocco `try...except` presente nel codebase applicativo `[V]`.
  * Messaggi delle eccezioni rigorosamente in lingua inglese `[V]`.
* Logging:
  * Nessun modulo di logging configurato o utilizzato nel progetto `[V]`.
  * Nessuna chiamata a `print()` presente nel codice o negli script `[V]`.
* Lingua dei commenti:
  * Commenti e docstring scritti in italiano `[V]`.
  * Identificatori, eccezioni e nomi dei test in lingua inglese `[V]`.
* Pattern ricorrenti:
  * Vettorizzazione NumPy completa per eliminare i cicli iterativi lenti in Python lungo l'asse delle $M$ traiettorie (`np.where`, `np.cumsum`, `np.maximum.accumulate`) `[V]`.
  * Pulizia manuale della memoria tramite `del paths` nei loop Monte Carlo intensivi `[V]`.
* Incoerenze rilevate tra parti diverse del progetto:
  1. `expected_final_wealth` è implementata in `src/shk/kelly/core.py` ma non è re-esportata in `src/shk/kelly/__init__.py`, a differenza di `kelly_fraction` e `log_growth_rate` `[V]`.
  2. Assenza di validazione dei parametri in `src/shk/kelly/simulate.py:log_wealth_paths`: mentre `draw_outcomes` e tutte le funzioni di `core.py` e `metrics.py` convalidano argomenti e intervalli sollevando `ValueError`/`TypeError`, `log_wealth_paths` non verifica gli input `f`, `b` e `outcomes` `[V]`.
  3. Docstring non allineata allo stato del codice in `src/shk/kelly/simulate.py:log_wealth_paths`: le righe 77-81 dichiarano che la funzione solleva `NotImplementedError` perché lasciata da implementare a mano, mentre la funzione è effettivamente implementata `[V]`.
  4. Docstring non allineate in `tests/test_simulate.py`: le docstring alle righe 71-72 e 88-89 avvisano che i test falliranno con `NotImplementedError`, contrariamente allo stato attuale del codice `[V]`.
  5. Disallineamento degli strumenti tra locale e CI: la repository include `uv.lock` generato da `uv`, ma il workflow CI `.github/workflows/test.yml` utilizza `pip` senza fare riferimento a `uv` o a `uv.lock` `[V]`.

### 8. Test

* Posizione dei test: Directory `tests/` `[V]`.
* Tipologia di test:
  * Test unitari analitici (`tests/test_kelly_core.py`) `[V]`.
  * Test unitari di simulazione vettoriale (`tests/test_simulate.py`) `[V]`.
  * Test unitari per metriche statistiche e drawdown (`tests/test_metrics.py`) `[V]`.
  * Test di accettazione end-to-end con simulazioni Monte Carlo su larga scala (`tests/test_us_c1_1_acceptance.py`), marcati con `@pytest.mark.slow` `[V]`.
* Modalità di lancio:
  * Esecuzione predefinita (solo test veloci, esclude i test slow tramite `addopts` in `pyproject.toml`): `pytest -v` `[V]`.
  * Esecuzione completa o dei soli test lenti: `pytest -o addopts=""` oppure `pytest -m "slow"` `[D]`.
* Copertura dedotta leggendo il codice dei test:
  * Funzioni pubbliche presenti nelle asserzioni dei test:
    * `kelly_fraction` (in `tests/test_kelly_core.py` e `tests/test_us_c1_1_acceptance.py`) `[V]`.
    * `log_growth_rate` (in `tests/test_kelly_core.py`) `[V]`.
    * `draw_outcomes` (in `tests/test_simulate.py` e `tests/test_us_c1_1_acceptance.py`) `[V]`.
    * `log_wealth_paths` (in `tests/test_simulate.py` e `tests/test_us_c1_1_acceptance.py`) `[V]`.
    * `final_log_wealth` (in `tests/test_metrics.py`) `[V]`.
    * `median_growth_rate` (in `tests/test_metrics.py` e `tests/test_us_c1_1_acceptance.py`) `[V]`.
    * `median_final_wealth` (in `tests/test_metrics.py`) `[V]`.
    * `mean_final_wealth` (in `tests/test_metrics.py`) `[V]`.
    * `max_drawdown` (in `tests/test_metrics.py` e `tests/test_us_c1_1_acceptance.py`) `[V]`.
    * `fraction_below_start` (in `tests/test_metrics.py`) `[V]`.
  * Funzioni pubbliche che NON compaiono MAI nelle asserzioni dei test:
    * `expected_final_wealth` (definita in `src/shk/kelly/core.py`, usata in `scripts/us_c1_1_growth_vs_lambda.py`, non ha alcun test associato) `[V]`.
    * `run_experiment` (definita in `scripts/us_c1_1_growth_vs_lambda.py`, priva di test automatizzati) `[V]`.
  * Nota vincolo: Non vengono riportati numeri di test passati, tempi di esecuzione o percentuali numeriche di copertura, in quanto richiederebbero l'esecuzione della suite di test che è vietata dal vincolo di sola lettura `[V]`.
* Test con asserzioni dipendenti da seed fissi, tolleranze numeriche o costanti empiriche:
  * `tests/test_kelly_core.py:13`: tolleranza `abs(actual - expected) < 1e-12` `[V]`.
  * `tests/test_kelly_core.py:32`: tolleranza e valore atteso empirico `pytest.approx(0.020136, abs=1e-6)` `[V]`.
  * `tests/test_kelly_core.py:39`: tolleranza e valore atteso empirico `pytest.approx(-0.002447, abs=1e-6)` `[V]`.
  * `tests/test_kelly_core.py:44`: passo della griglia `retstep=True` e tolleranza `abs(f_argmax - 0.20) <= step` `[V]`.
  * `tests/test_simulate.py:11`: seed fisso `np.random.default_rng(42)` `[V]`.
  * `tests/test_simulate.py:22-23`: seed fisso `np.random.default_rng(12345)` `[V]`.
  * `tests/test_simulate.py:32`: seed fisso `np.random.default_rng(999)` `[V]`.
  * `tests/test_simulate.py:38`: tolleranza empirica stocastica `abs(empirical_p - p) < 0.01` `[V]`.
  * `tests/test_simulate.py:43`: seed fisso `np.random.default_rng(42)` `[V]`.
  * `tests/test_simulate.py:82`: tolleranza numerica `np.testing.assert_allclose(actual, expected, rtol=1e-12)` `[V]`.
  * `tests/test_simulate.py:91`: seed fisso `np.random.default_rng(7)` `[V]`.
  * `tests/test_metrics.py:43, 52, 61, 82`: tolleranze di confronto float `pytest.approx(...)` `[V]`.
  * `tests/test_metrics.py:72`: tolleranza numerica assoluta `np.testing.assert_allclose(actual, expected, atol=1e-12)` `[V]`.
  * `tests/test_us_c1_1_acceptance.py:23`: seed fisso `np.random.default_rng(20260905)` `[V]`.
  * `tests/test_us_c1_1_acceptance.py:37`: tolleranza numerica `abs(best_lambda - 1.0) < 1e-6` `[V]`.
  * `tests/test_us_c1_1_acceptance.py:47`: seed fisso `np.random.default_rng(20260905)` `[V]`.
  * `tests/test_us_c1_1_acceptance.py:63`: tolleranza empirica per rumore stocastico `np.all(diffs >= -0.01)` `[V]`.
  * `tests/test_us_c1_1_acceptance.py:73`: seed fisso `np.random.default_rng(20260905)` `[V]`.
  * `tests/test_us_c1_1_acceptance.py:78, 82`: costante empirica di zero crossing `lambda = 1.946` e soglia `abs(g_med) < 0.002` `[V]`.
  * `tests/test_us_c1_1_acceptance.py:92`: seed fisso `np.random.default_rng(20260905)` `[V]`.
  * `tests/test_us_c1_1_acceptance.py:97`: costante empirica sovrainvestimento `lambda = 2.5` `[V]`.

### 9. Zone fragili

1. Funzione `expected_final_wealth` completamente sprovvista di test:
   * Definita in `src/shk/kelly/core.py` (linee 97-144) e utilizzata nello script `scripts/us_c1_1_growth_vs_lambda.py` `[V]`.
   * Non è presente in alcun file di test in `tests/` `[V]`.
   * Eventuali regressioni analitiche o numeriche passerebbero inosservate durante l'esecuzione di `pytest` `[V]`.

2. Assenza di controlli di validità degli argomenti in `log_wealth_paths`:
   * In `src/shk/kelly/simulate.py`, `log_wealth_paths` non valida che `f < 1.0`, `b > 0` o che `outcomes` sia booleano `[V]`.
   * Se $f \ge 1.0$, l'argomento $1 - f$ del logaritmo diventa non positivo, provocando warning NumPy e generazione di `-inf` o `nan` che inficiano a cascata tutti i calcoli delle metriche `[V]`.

3. Replicazione non sincronizzata tra script e test di accettazione:
   * I parametri della simulazione ($p=0.60, b=1.0, T=1000, M=10000$, seed `20260905`, griglia di 51 punti da $0.0$ a $2.5$) sono hardcoded sia in `scripts/us_c1_1_growth_vs_lambda.py` sia in `tests/test_us_c1_1_acceptance.py` `[V]`.
   * Qualsiasi modifica futura ai parametri dello studio rischia di rompere i test o di creare disallineamenti tra l'esperimento pubblicato e la suite di verifica `[V]`.

4. Elevata sensibilità dei test di accettazione alle costanti numeriche e al seed:
   * `tests/test_us_c1_1_acceptance.py` fa affidamento sul seed `20260905` e su soglie empiriche rigide (es. `diffs >= -0.01`, zero-crossing fissato a `1.946`, `abs(g_med) < 0.002`) `[V]`.
   * Minime modifiche algoritmiche nella generazione dei numeri casuali di NumPy o nel passo della simulazione potrebbero determinare falsi negativi nei test `[V]`.

5. Rischio di dipendenze disallineate tra sviluppo locale e CI:
   * Il lockfile `uv.lock` esiste alla radice del repository `[V]`.
   * Il workflow GitHub Actions `.github/workflows/test.yml` utilizza `pip install -e ".[dev]"` senza fare riferimento a `uv` o a `uv.lock` `[V]`.
   * Nuove release di dipendenze transitive possono causare discrepanze o rotture nei test in ambiente CI non riproducibili in locale `[V]`.

6. Discrepanza documentale tra codice e docstring:
   * La docstring di `log_wealth_paths` in `src/shk/kelly/simulate.py` dichiara `NotImplementedError` pur essendo implementata `[V]`.
   * Le docstring di test in `tests/test_simulate.py` dichiarano che i test falliranno con `NotImplementedError` `[V]`.

7. Omissione nei test di validazione degli argomenti delle metriche:
   * `tests/test_metrics.py:test_metrics_error_conditions` testa l'eccezione `ValueError` per input non validi su 4 funzioni, ma omette di testarla esplicitamente su `median_final_wealth` e `mean_final_wealth` `[V]`.

### 10. Limiti di questa mappa

* Cosa non è stato ispezionato e perché:
  * Non è stato eseguito alcun modulo Python, script di simulazione o suite di test pytest `[V]`.
  * Non sono stati misurati empiricamente i tempi di esecuzione né il consumo reale di memoria della simulazione Monte Carlo `[V]`.
  * Non è stato verificato lo stato remoto dei workflow GitHub Actions tramite API o CLI esterna `[V]`.
  * Tutte le omissioni sopra descritte derivano dal vincolo di sola lettura del task, che proibisce la generazione di file o cache (`.pytest_cache/`, venv sync, file di output) `[V]`.

* Cosa resta incerto:
  * La durata temporale effettiva dell'esecuzione della suite marcata `@pytest.mark.slow` (richiederebbe l'esecuzione della suite) `[V]`.
  * La riuscita effettiva della build CI su GitHub Actions per l'ultimo commit `a7420cb` `[V]`.

* Sezioni in prevalenza `[D]`:
  * Sezione 2 ("Come si esegue"): i comandi `uv sync`, `hatch build` / `python -m build`, `pytest -m "slow"` e `python scripts/us_c1_1_growth_vs_lambda.py` sono dedotti dalle convenzioni di packaging e di esecuzione standard (`uv`, `hatchling`, `pytest`), non essendo codificati in file di automazione o script di task runner dedicati `[V]`.

* Domande che farei se dovessi lavorare su questo progetto senza altro contesto:
  1. È previsto l'adeguamento del workflow di CI `.github/workflows/test.yml` affinché utilizzi `uv` e verifichi la sincronizzazione con `uv.lock`, oppure l'installazione tramite `pip` è una scelta deliberata?
  2. Per quale motivo `expected_final_wealth` è stata omessa sia dal re-export in `src/shk/kelly/__init__.py` sia dalla suite di unit test in `tests/test_kelly_core.py`?
  3. C'è una motivazione architetturale per cui `log_wealth_paths` in `src/shk/kelly/simulate.py` non esegue la validazione dei parametri di input (`f`, `b`, `outcomes`) a differenza delle altre funzioni del pacchetto?
  4. Qual è lo scopo futuro previsto per le directory `config/` e `data/raw/`, attualmente popolate unicamente da file placeholder `.gitkeep`?
  5. Il file `C1.1.md` alla radice è una bozza provvisoria da migrare sotto una directory di documentazione (es. `thesis/` o `docs/`), o deve rimanere come documento di vertice della user story?

### 11. Comandi eseguiti

Elenco completo dei comandi eseguiti durante l'analisi:

1. `git status` — Esito: codice 0. Rilevato branch `main` allineato a `origin/main`, working tree pulito.
2. `git log -n 5 --oneline` — Esito: codice 0. Ispezionati gli ultimi 4 commit della storia del repository.
3. `git remote -v` — Esito: codice 0. Ispezionati gli URL fetch/push del remote `origin`.
4. `git branch -a` — Esito: codice 0. Ispezionati i branch locali e remoti.
5. `git diff` — Esito: codice 0. Verificata l'assenza di modifiche non committate nel working tree.
6. `git log --name-only` — Esito: codice 0. Rilevato l'inventario completo di tutti i file presenti e tracciati nel repository.
7. `git status --ignored` — Esito: codice 0. Ispezionati i file e le directory ignorate nel filesystem locale.
8. `git log -1` — Esito: codice 0. Verificati i metadati completi dell'ultimo commit su `main`.
9. `git log feature/US-C1.1-Trade-off-crescita/varianza -n 1 --oneline` — Esito: codice 0. Verificato l'ultimo commit del branch secondario.
10. `git log -n 5 --graph --decorate --oneline` — Esito: codice 0. Verificata la struttura grafica dei commit e i puntatori dei branch.
11. `git status` — Esito: codice 0. Verifica dello stato post-scrittura (rilevata unicamente la presenza del file non tracciato `.agent/`).

Dichiarazione:
Nessun comando al di fuori dei comandi git di sola lettura consentiti (`git status`, `git log`, `git branch`, `git remote -v`, `git diff`) è stato eseguito. Nessun codice del progetto, script o suite di test è stato eseguito. Nessun file o directory è stato modificato o creato nel filesystem, ad eccezione dell'autorizzata scrittura del file `.agent/MAPPA.md`.
