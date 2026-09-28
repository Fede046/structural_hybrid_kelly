Mappa completa — 2026-09-28 — R1

### 0. Stato del repository

* Percorso assoluto della radice: `c:\Users\malse\Documents\GitHub\structural_hybrid_kelly` `[V]`.
* Branch corrente: `C2` `[V]`.
* Stato del working tree: sporco `[V]`.
* File modificati non staged:
  * `.agent/BACKLOG.md` (modificato con l'inserimento delle specifiche per la Story S2 / C2) `[V]`.
  * `.agent/MAPPA.md` (aggiornato nella presente sessione) `[V]`.
* File rimossi nel working tree (non staged):
  * `C1.1.md` (risulta rimosso dal filesystem locale rispetto al commit HEAD) `[V]`.
* File modificati staged: nessuno `[V]`.
* File non tracciati: nessuno `[V]`.
* File ignorati rilevati nel filesystem locale: `.pytest_cache/`, `.venv/`, `src/shk/__pycache__/`, `src/shk/kelly/__pycache__/`, `tests/__pycache__/` `[V]`.
* Ultimi cinque commit in forma breve (dalla storia di Git su branch `C2`):
  * `1e7813d` `C1 (#14)` `[V]`
  * `640b906` `C1 (#13)` `[V]`
  * `a7420cb` `create c1 (#5)` `[V]`
  * `6187309` `Feature/us c1.1 trade off crescita/varianza (#4)` `[V]`
  * `e5f339b` `Add GitHub Actions workflow for testing` `[V]`
* Remote configurati:
  * `origin`: `https://github.com/Fede046/structural_hybrid_kelly.git` (fetch) `[V]`
  * `origin`: `https://github.com/Fede046/structural_hybrid_kelly.git` (push) `[V]`
* Allineamento rispetto al remote: `C2` è allineato a `origin/C2` (0 commit avanti, 0 commit indietro) `[V]`.
* Altri branch locali:
  * `C1` (punta al commit `362c739`) `[V]`
  * `feature/US-C1.1-Trade-off-crescita/varianza` (punta al commit `1ff7301`) `[V]`
  * `main` (punta al commit `1e7813d`) `[V]`

### 1. Identikit

* Nome del progetto: `structural-hybrid-kelly` `[V]`.
* Descrizione: Libreria scientifica e ambiente di simulazione per l'analisi del criterio di Kelly e dei modelli ibridi strutturali `[V]`. Modella strategie di scommessa e investimento, valutando il trade-off crescita/varianza e metriche di rischio sotto errore di stima `[V]`.
* Stack: Python `[V]`.
* Linguaggi: Python 3 `[V]`.
* Versioni:
  * Versione Python minima supportata: `>=3.11` (specificata in `pyproject.toml`) `[V]`.
  * Versione Python impiegata nella CI: `3.12` (specificata in `.github/workflows/test.yml`) `[V]`.
  * Versione del pacchetto: `0.1.0` (dichiarata in `pyproject.toml` e in `src/shk/__init__.py`) `[V]`.
* Gestore di pacchetti: `uv` (attestato dalla presenza di `uv.lock` alla radice) `[V]`, con `pip` utilizzato nel runner di CI `[V]`.
* Build system: Hatchling (`hatchling.build` specificato in `pyproject.toml`) `[V]`.

### 2. Come si esegue

* Installazione delle dipendenze:
  * Tramite pip (attestato in CI): `pip install -e ".[dev]"` `[V]`.
  * Tramite uv: `uv sync` `[D]`.
* Avvio in sviluppo:
  * Non è presente alcun server interattivo né daemon in background `[V]`.
  * Installazione in modalità editabile: `pip install -e .` `[D]`.
* Build del pacchetto:
  * Comando di build Hatch: `hatch build` oppure `python -m build` `[D]`.
* Lancio dei test:
  * Test veloci (suite predefinita, esclude i test slow tramite `addopts = "-m 'not slow'"` in `pyproject.toml`): `pytest -v` `[V]`.
  * Test lenti di accettazione Monte Carlo: `pytest -m slow` `[D]`.
  * Esecuzione completa di tutti i test: `pytest -o addopts=""` `[D]`.
* Esecuzione degli script sperimentali:
  * Esperimento US-C1.1: `python scripts/us_c1_1_growth_vs_lambda.py` `[D]`.
  * Esperimento US-C1.2: `python scripts/us_c1_2_estimation_error.py` `[D]`.
* Variabili d'ambiente richieste:
  * Nessuna variabile d'ambiente richiesta `[V]`.
* File di configurazione richiesti:
  * `pyproject.toml` (configurazione pacchetto, metadati, dipendenze runtime/dev, build system e marker pytest) `[V]`.
  * Nessun file `.env` presente o richiesto `[V]`.
  * La directory `config/` contiene unicamente il file placeholder `.gitkeep` `[V]`.
  * La directory `data/raw/` contiene unicamente il file placeholder `.gitkeep` `[V]`.

### 3. Albero delle directory

* `.` (radice): File di configurazione di progetto (`pyproject.toml`, `uv.lock`, `.gitignore`, `LICENSE`) e note descrittive (`C1.1.md`, tracciato in HEAD ma non presente nel working tree) `[V]`.
* `.agent/`: Documentazione di processo, tracciamento del backlog (`BACKLOG.md`), mappa e scheda del supervisore `[V]`.
* `.agent/report/`: Report formali di chiusura per i singoli task implementativi completati (T1..T7) `[V]`.
* `.github/workflows/`: Pipeline di integrazione continua GitHub Actions (`test.yml`) `[V]`.
* `config/`: Directory predisposta per file di configurazione futuri (attualmente contiene solo `.gitkeep`) `[V]`.
* `data/raw/`: Directory per storage di dataset grezzi (attualmente contiene solo `.gitkeep`) `[V]`.
* `results/`: Directory di destinazione dei report tabellari CSV generati dalle simulazioni `[V]`.
* `scripts/`: Script eseguibili per la conduzione degli esperimenti e la generazione delle figure `[V]`.
* `src/shk/`: Radice del codice sorgente del pacchetto Python `shk` `[V]`.
* `src/shk/kelly/`: Modulo contenente formule analitiche, motore di simulazione, modelli di perturbazione/rumore, regole di staking e scenari sperimentali `[V]`.
* `tests/`: Suite di unit test e test di accettazione basati sul framework pytest `[V]`.
* `thesis/figures/`: Directory per le figure PNG ad alta risoluzione generate dagli script per la tesi `[V]`.

### 4. Moduli principali

Il progetto include 10 moduli Python applicativi ed eseguibili (sono esclusi da questo elenco i 7 moduli di test situati in `tests/`, dettagliati nella Sezione 8 `[V]`):

1. `src/shk/__init__.py`
   * Responsabilità: Inizializza il pacchetto principale `shk` ed espone la versione del software `[V]`.
   * Espone: `__version__` `[V]`.
   * Dipendenze interne: Nessuna `[V]`.

2. `src/shk/kelly/__init__.py`
   * Responsabilità: Fornisce l'interfaccia pubblica del sottomodulo Kelly re-esportando le funzioni analitiche fondamentali `[V]`.
   * Espone: `kelly_fraction`, `log_growth_rate` (tramite `__all__`) `[V]`.
   * Dipendenze interne: `src/shk/kelly/core.py` `[V]`.

3. `src/shk/kelly/core.py`
   * Responsabilità: Implementa le formule analitiche esatte in forma chiusa per il criterio di Kelly e la crescita attesa su scommesse binarie `[V]`.
   * Espone: `kelly_fraction(p, b)`, `log_growth_rate(f, p, b)`, `expected_final_wealth(f, p, b, T, b0=1.0)` `[V]`.
   * Dipendenze interne: Nessuna `[V]`.

4. `src/shk/kelly/simulate.py`
   * Responsabilità: Esegue la generazione bernoulliana di esiti stocastici e simula l'evoluzione vettorizzata del log-wealth con supporto a frazioni broadcastabili `[V]`.
   * Espone: `draw_outcomes(p, T, M, rng)`, `simulate_growth(outcomes, fractions, b)`, `log_wealth_paths(outcomes, f, b)` `[V]`.
   * Dipendenze interne: Nessuna `[V]`.

5. `src/shk/kelly/estimation.py`
   * Responsabilità: Genera stime di probabilità soggette a perturbazione relativa deterministica o a rumore gaussiano con saturazione in [0, 1] `[V]`.
   * Espone: `relative_perturbation(p, delta)`, `noisy_estimates(p, sigma_p, T, M, rng)` `[V]`.
   * Dipendenze interne: Nessuna `[V]`.

6. `src/shk/kelly/staking.py`
   * Responsabilità: Implementa il calcolo delle frazioni di puntata secondo il criterio di Kelly, il moltiplicatore frazionario, la regola plug-in e i momenti empirici di staking `[V]`.
   * Espone: `kelly_staking(p_hat, b, lam=1.0)`, `StakingMoments`, `staking_moments(f_hat, f_star)`, `plugin_staking(p_hat, b, sigma_p)` `[V]`.
   * Dipendenze interne: `src/shk/kelly/core.py` (usato concettualmente come riferimento per l'ordine operativo, non importato direttamente) `[V]`.

7. `src/shk/kelly/scenarios.py`
   * Responsabilità: Centralizza le definizioni immutabili degli scenari, la riproducibilità statistica dei generatori e la composizione del workflow di simulazione `[V]`.
   * Espone: `Scenario`, `BASE_SCENARIO`, `SUBTLE_SCENARIO`, `SEED`, `spawn_generators(seed=SEED)`, `draw_scenario_outcomes(scenario, rng)`, `simulate_scenario(scenario, outcomes, p_hat, lam=1.0)` `[V]`.
   * Dipendenze interne: `src/shk/kelly/simulate.py`, `src/shk/kelly/staking.py` `[V]`.

8. `src/shk/kelly/metrics.py`
   * Responsabilità: Calcola metriche statistiche ed indicatori di rischio empirico (tasso di crescita mediano, drawdown massimo, frequenza di perdita) su matrici di traiettorie `[V]`.
   * Espone: `final_log_wealth(paths)`, `median_growth_rate(paths)`, `median_final_wealth(paths)`, `mean_final_wealth(paths)`, `max_drawdown(paths)`, `fraction_below_start(paths)` `[V]`.
   * Dipendenze interne: Nessuna `[V]`.

9. `scripts/us_c1_1_growth_vs_lambda.py`
   * Responsabilità: Esegue l'esperimento Monte Carlo US-C1.1 sul trade-off crescita/varianza al variare di $\lambda$, esportando il report CSV e la figura a tre pannelli `[V]`.
   * Espone: `run_experiment()` e blocco CLI `__main__` `[V]`.
   * Dipendenze interne: `src/shk/kelly/core.py`, `src/shk/kelly/simulate.py`, `src/shk/kelly/metrics.py` `[V]`.

10. `scripts/us_c1_2_estimation_error.py`
    * Responsabilità: Esegue l'esperimento Monte Carlo US-C1.2 sull'errore di stima di $p$ e il confronto tra euristiche di frazionamento, esportando il report CSV e la figura a due pannelli `[V]`.
    * Espone: `run_experiment()` e blocco CLI `__main__` `[V]`.
    * Dipendenze interne: `src/shk/kelly/core.py`, `src/shk/kelly/estimation.py`, `src/shk/kelly/simulate.py`, `src/shk/kelly/staking.py`, `src/shk/kelly/metrics.py`, `src/shk/kelly/scenarios.py` `[V]`.

### 5. Punti di ingresso e flussi

Punti di ingresso dell'applicazione:
* Script CLI per l'esperimento C1.1: `python scripts/us_c1_1_growth_vs_lambda.py` `[V]`.
* Script CLI per l'esperimento C1.2: `python scripts/us_c1_2_estimation_error.py` `[V]`.
* Runner di test: `pytest` `[V]`.
* Uso come libreria importabile: `import shk` o import specifici dai moduli `shk.kelly.*` `[V]`.

Tre flussi principali dell'applicazione:

* Flusso 1 — Simulazione trade-off crescita/varianza al variare di $\lambda$ (Esperimento US-C1.1):
  1. `scripts/us_c1_1_growth_vs_lambda.py:run_experiment()` calcola la frazione ottimale $f^*$ invocando `kelly_fraction(p, b)` in `src/shk/kelly/core.py` `[V]`.
  2. Genera la matrice di esiti bernoulliani condivisa chiamando `draw_outcomes(p, t_steps, m_trajectories, rng)` in `src/shk/kelly/simulate.py` `[V]`.
  3. Per ciascun $\lambda \in [0.0, 2.5]$ (51 punti):
     a. Calcola le traiettorie temporali invocando `log_wealth_paths(outcomes, f_val, b)` in `src/shk/kelly/simulate.py` (che delega a `simulate_growth`) `[V]`.
     b. Calcola le statistiche empiriche chiamando `median_growth_rate`, `median_final_wealth`, `mean_final_wealth`, `max_drawdown`, `fraction_below_start` in `src/shk/kelly/metrics.py` `[V]`.
     c. Rilascia la memoria dell'array delle traiettorie con `del paths` `[V]`.
     d. Calcola i benchmark analitici chiamando `log_growth_rate` ed `expected_final_wealth` in `src/shk/kelly/core.py` `[V]`.
  4. Scrive il file tabellare `results/us_c1_1_growth_vs_lambda.csv` tramite `csv.DictWriter` `[V]`.
  5. Costruisce la figura a tre pannelli con Matplotlib e la salva su `thesis/figures/us_c1_1_growth_vs_lambda.png` `[V]`.

* Flusso 2 — Simulazione impatto errore di stima e confronto regole di staking (Esperimento US-C1.2):
  1. `scripts/us_c1_2_estimation_error.py:run_experiment()` itera sugli scenari immutabili `BASE_SCENARIO` e `SUBTLE_SCENARIO` definiti in `src/shk/kelly/scenarios.py` `[V]`.
  2. Per ciascun scenario e combinazione di parametri:
     a. Genera una coppia di generatori indipendenti tramite `spawn_generators(SEED)` in `src/shk/kelly/scenarios.py` `[V]`.
     b. Genera la matrice di esiti con `draw_scenario_outcomes(scenario, rng_outcomes)` in `src/shk/kelly/scenarios.py` `[V]`.
     c. Per l'errore deterministico ($\pm 10\%$): calcola la probabilità perturbata tramite `relative_perturbation(sc.p, delta)` in `src/shk/kelly/estimation.py`, genera le traiettorie con `simulate_scenario(sc, outcomes, p_hat, lam=1.0)` in `src/shk/kelly/scenarios.py` (che chiama `kelly_staking` in `src/shk/kelly/staking.py` e `simulate_growth` in `src/shk/kelly/simulate.py`), e calcola le metriche da `src/shk/kelly/metrics.py` `[V]`.
     d. Per ciascun $\sigma_p \in \{0.015, 0.0283, 0.045\}$: genera la matrice di stime con `noisy_estimates(sc.p, s, sc.T, sc.M, rng_noise)` in `src/shk/kelly/estimation.py`, calcola la matrice delle frazioni base $f̂$ con `kelly_staking(p_hat, sc.b, lam=1.0)` in `src/shk/kelly/staking.py`, calcola i momenti di staking con `staking_moments(f_hat, f_star)` in `src/shk/kelly/staking.py`, e simula e misura le diverse regole (`lambda_star`, `ratio_moments`, `lambda_linear`, `quarter_kelly`, `half_kelly`, `full_kelly`, e la regola plug-in con `plugin_staking` e `simulate_growth`) `[V]`.
  3. Scrive le 46 righe di risultati su `results/us_c1_2_estimation_error.csv` `[V]`.
  4. Genera la figura a due pannelli e la esporta in `thesis/figures/us_c1_2_estimation_error.png` `[V]`.

* Flusso 3 — Calcolo e simulazione modulare del criterio di Kelly (uso come libreria):
  1. Un programma esterno importa i moduli dal sottopacchetto `shk.kelly` `[V]`.
  2. Valuta i parametri ottimi teorici con `kelly_fraction` e `log_growth_rate` in `src/shk/kelly/core.py` `[V]`.
  3. Applica un modello di rumore alle stime con `noisy_estimates` o `relative_perturbation` in `src/shk/kelly/estimation.py` `[V]`.
  4. Calcola le frazioni scommesse tramite `kelly_staking` o `plugin_staking` in `src/shk/kelly/staking.py` `[V]`.
  5. Esegue la simulazione stocastica vettorizzata chiamando `simulate_growth` in `src/shk/kelly/simulate.py` `[V]`.
  6. Estrae metriche e distribuzioni empiriche richiamando le funzioni in `src/shk/kelly/metrics.py` `[V]`.

Replicazione e divergenze tra flussi ed esecuzioni di test:
* Flusso 1 vs `tests/test_us_c1_1_acceptance.py`:
  * Replicazione: Entrambi usano i medesimi parametri hardcoded ($p=0.60, b=1.0, T=1000, M=10000$, seed `20260905`, 51 valori di $\lambda$ da $0.0$ a $2.5$) `[V]`.
  * Divergenze:
    1. Lo script calcola tutte le metriche empiriche e analitiche salvando CSV e PNG su disco; i test calcolano solo `median_growth_rate` e `max_drawdown` ed eseguono asserzioni numeriche in memoria `[V]`.
    2. Lo script genera gli esiti una sola volta per tutti i $\lambda$; i test ripetono la generazione degli esiti in ciascuna singola funzione di test `[V]`.
* Flusso 2 vs `tests/test_us_c1_2_acceptance.py`:
  * Replicazione: Entrambi condividono le definizioni di scenario e il seed master `20260927` importandoli da `src/shk/kelly/scenarios.py` `[V]`.
  * Divergenze:
    1. Lo script esplora l'intera griglia di parametri ed esporta tabella CSV e grafici; i test di accettazione verificano singoli criteri puntuali (asimmetria sovrastima/sottostima nello scenario sottile, confronto di $Var(c)$ rispetto a $1$, dominanza di $\lambda^*$ su $0.25$ a $\sigma_p = 0.0283$) `[V]`.
    2. I test includono verifiche unitarie di indipendenza degli esiti bernoulliani da $p̂$ e di invarianza per effetto collaterale della matrice esiti `[V]`.

### 6. Modello dei dati

* Classi di dominio o dataclass strutturate:
  1. `Scenario` (`src/shk/kelly/scenarios.py`): dataclass congelata (`frozen=True`) che incapsula la tupla dei parametri sperimentali:
     * `name`: `str`, identificativo descrittivo dello scenario `[V]`.
     * `p`: `float`, probabilità reale di successo in $[0, 1]$ `[V]`.
     * `b`: `float`, quota decimale netta strettamente positiva ($b > 0$) `[V]`.
     * `T`: `int`, numero di passi temporali ($T > 0$) `[V]`.
     * `M`: `int`, numero di traiettorie indipendenti ($M > 0$) `[V]`.
     * Istanze singleton definite nel modulo: `BASE_SCENARIO` (p=0.60, b=1.0, T=1000, M=10000) e `SUBTLE_SCENARIO` (p=0.52, b=1.0, T=380, M=10000) `[V]`.
  2. `StakingMoments` (`src/shk/kelly/staking.py`): `NamedTuple` contenente i momenti empirici del moltiplicatore normalizzato $c = f̂ / f^*$:
     * `mean_c`: `float`, media campionaria pooled $E[c]$ `[V]`.
     * `mean_c2`: `float`, momento secondo campionario pooled $E[c^2]$ `[V]`.
     * `var_c`: `float`, varianza campionaria pooled $Var(c) = E[c^2] - (E[c])^2$ `[V]`.
     * `fraction_zero`: `float`, quota di scommesse in cui la frazione è troncata a 0.0 `[V]`.
* Strutture dati in circolo:
  1. Scalari primitivi:
     * `p`: `float`, probabilità in $[0.0, 1.0]$ `[V]`.
     * `b`: `float`, quota netta ($b > 0$) `[V]`.
     * `f`: `float`, frazione di scommessa in $[0.0, 1.0)$ `[V]`.
     * `lam`: `float`, moltiplicatore di Kelly ($\ge 0$) `[V]`.
     * `sigma_p`: `float`, deviazione standard del rumore ($\ge 0$) `[V]`.
     * `delta`: `float`, perturbazione deterministica finita `[V]`.
     * `T`, `M`: `int`, orizzonte temporale e numero di simulazioni `[V]`.
     * `b0`: `float`, capitale iniziale normalizzato ($b_0 > 0$, default 1.0) `[V]`.
  2. Matrice di esiti (`outcomes`):
     * `np.ndarray`, shape `(M, T)`, `dtype=bool` (`True` = vincita, `False` = perdita) `[V]`.
  3. Matrice o vettore delle stime (`p_hat`):
     * `np.ndarray` (shape `(M, T)`) o scalare float, con valori saturati in $[0.0, 1.0]$ `[V]`.
  4. Frazioni di scommessa (`fractions`):
     * Scalare float o `np.ndarray` con forme ammesse broadcastabili verso `(M, T)`: `()`, `(T,)`, `(1, T)`, `(M, 1)`, `(M, T)`, con elementi in $[0.0, 1.0)$ `[V]`.
  5. Matrice delle traiettorie di log-wealth (`paths`):
     * `np.ndarray`, shape `(M, T + 1)`, `dtype=float64`, dove la colonna 0 è interamente nulla ($B_0 = 1.0$) `[V]`.
  6. Vettori di metriche e drawdown:
     * `final_log_wealth`: `np.ndarray` 1D shape `(M,)` `[V]`.
     * `max_drawdown`: `np.ndarray` 1D shape `(M,)`, float64 vincolato in $[0.0, 1.0)$ `[V]`.
  7. Record tabellari:
     * Dizionari Python serializzati su file CSV con campi numerici float o stringhe vuote per valori non applicabili `[V]`.
* Schema di persistenza:
  * Nessun database, tabella relazionale o ORM presente nel codebase `[V]`.
  * Persistenza basata interamente su file flat versionati in Git:
    * `results/us_c1_1_growth_vs_lambda.csv` (10 colonne) `[V]`.
    * `results/us_c1_2_estimation_error.csv` (12 colonne, 46 righe di dati) `[V]`.
    * `thesis/figures/us_c1_1_growth_vs_lambda.png` (figura a tre pannelli) `[V]`.
    * `thesis/figures/us_c1_2_estimation_error.png` (figura a due pannelli) `[V]`.

### 7. Convenzioni in vigore

* Naming:
  * Moduli e cartelle: snake_case (`shk`, `kelly`, `core.py`, `simulate.py`, `estimation.py`, `staking.py`, `scenarios.py`, `metrics.py`) `[V]`.
  * Funzioni e metodi: snake_case (`kelly_fraction`, `draw_outcomes`, `simulate_growth`, `noisy_estimates`, `plugin_staking`, `max_drawdown`) `[V]`.
  * Classi e tipi: PascalCase (`Scenario`, `StakingMoments`) `[V]`.
  * Costanti: UPPER_CASE (`SEED`, `BASE_SCENARIO`, `SUBTLE_SCENARIO`) `[V]`.
  * Variabili statistiche e matematiche: lettere matematiche convenzionali della letteratura ($p, b, f, T, M, b_0, \lambda, \sigma_p, c, \delta$) `[V]`.
  * Test: prefisso `test_` su file e funzioni di test `[V]`.
* Organizzazione dei file:
  * Sorgenti di libreria incapsulati in `src/shk/` `[V]`.
  * Suite di test automatizzati raccolta in `tests/` `[V]`.
  * Script operativi raccolti in `scripts/` `[V]`.
  * Dati di output separati in `results/` (tabelle CSV) e `thesis/figures/` (immagini PNG) `[V]`.
  * Tracciamento operativo, backlog e schede in `.agent/` `[V]`.
* Stile:
  * Type hints completi e rigorosi su argomenti e valori di ritorno in tutte le funzioni `[V]`.
  * Docstring conformi allo stile NumPy con sezioni `Parametri`, `Restituisce`, `Solleva` `[V]`.
* Gestione degli errori:
  * Validazione difensiva sistematica in apertura di funzione: `ValueError` per valori o dimensioni non ammissibili, `TypeError` per tipi non conformi (es. tipo di generatore casuale o array booleano) `[V]`.
  * Nessun blocco `try...except` presente nei sorgenti in `src/` o negli script in `scripts/` `[V]`.
  * Messaggi di errore delle eccezioni rigorosamente in lingua inglese `[V]`.
* Logging:
  * Nessun modulo o framework di logging utilizzato nel progetto `[V]`.
  * Nessuna chiamata a `print()` presente nei sorgenti in `src/` o negli script in `scripts/` `[V]`.
* Lingua:
  * Commenti e docstring redatti in lingua italiana `[V]`.
  * Identificatori, messaggi delle eccezioni e nomi dei test redatti in lingua inglese `[V]`.
* Pattern ricorrenti:
  * Vettorizzazione NumPy completa per eliminare i cicli espliciti lungo le $M$ traiettorie e lungo i $T$ passi temporali nel motore di simulazione (`np.where`, `np.cumsum`, `np.maximum.accumulate`, `np.clip`) `[V]`.
  * Indipendenza e riproducibilità statistica tramite `np.random.SeedSequence.spawn` per derivare flussi casuali distinti e isolati `[V]`.
  * Deallocazione esplicita della memoria nei loop intensivi tramite `del paths` `[V]`.
  * Impostazione preventiva del backend Matplotlib con `matplotlib.use("Agg")` in apertura degli script di simulazione `[V]`.
* Incoerenze rilevate tra parti diverse del progetto:
  1. `expected_final_wealth` è implementata in `src/shk/kelly/core.py`, ma non è re-esportata in `src/shk/kelly/__init__.py` a differenza di `kelly_fraction` e `log_growth_rate` `[V]`.
  2. Disallineamento tra lockfile locale e automazione CI: alla radice è presente `uv.lock`, ma il workflow CI `.github/workflows/test.yml` installa le dipendenze con `pip install -e ".[dev]"` senza fare riferimento a `uv` e senza bloccare le versioni delle dipendenze `[V]`.
  3. Nel modulo `tests/test_metrics.py:test_metrics_error_conditions`, la verifica del sollevamento di `ValueError` su array 1D o con colonne insufficienti viene eseguita su `final_log_wealth`, `median_growth_rate`, `max_drawdown` e `fraction_below_start`, ma viene omessa per `median_final_wealth` e `mean_final_wealth` `[V]`.
  4. Duplicazione dei parametri nello script C1.1: `scripts/us_c1_1_growth_vs_lambda.py` hardcoda i parametri di simulazione all'interno di `run_experiment()` anziché sfruttare la centralizzazione offerta dal modulo `src/shk/kelly/scenarios.py` (usato invece da C1.2) `[V]`.
  5. Il file `C1.1.md` risulta tracciato in HEAD alla radice del repository come file non categorizzato ma rimosso nel working tree locale `[V]`.

### 8. Test

* Posizione dei test: Directory `tests/` `[V]`.
* Tipologia di test:
  * Test unitari analitici sulle formule matematiche esatte (`tests/test_kelly_core.py`) `[V]`.
  * Test unitari di simulazione vettoriale, broadcasting e accumulo logaritmico (`tests/test_simulate.py`) `[V]`.
  * Test unitari sulle stime perturbate e rumore gaussiano saturato (`tests/test_estimation.py`) `[V]`.
  * Test unitari sulle regole di staking, moltiplicatori, momenti e regola plug-in (`tests/test_staking.py`) `[V]`.
  * Test unitari sulle metriche di log-wealth e drawdown (`tests/test_metrics.py`) `[V]`.
  * Test di accettazione end-to-end con simulazioni stocastiche per US-C1.1 (`tests/test_us_c1_1_acceptance.py`), interamente marcati `@pytest.mark.slow` `[V]`.
  * Test di accettazione end-to-end per US-C1.2 (`tests/test_us_c1_2_acceptance.py`), comprendenti test veloci e test marcati `@pytest.mark.slow` `[V]`.
* Modalità di lancio:
  * Esecuzione predefinita (solo test veloci, esclude i test slow tramite `addopts = "-m 'not slow'"` in `pyproject.toml`): `pytest -v` `[V]`.
  * Esecuzione dei soli test lenti di accettazione: `pytest -m slow` `[D]`.
  * Esecuzione integrale dell'intera suite: `pytest -o addopts=""` `[D]`.
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
  * Funzioni pubbliche che NON compaiono MAI nelle asserzioni dei test:
    * `expected_final_wealth` (implementata in `src/shk/kelly/core.py:97-144`, usata nello script `scripts/us_c1_1_growth_vs_lambda.py`, completamente priva di test) `[V]`.
    * `run_experiment` di `scripts/us_c1_1_growth_vs_lambda.py` (priva di test di integrazione automatizzati) `[V]`.
    * `run_experiment` di `scripts/us_c1_2_estimation_error.py` (priva di test di integrazione automatizzati) `[V]`.
  * Nota vincolo: Conteggi esatti di test passati, tempi di esecuzione o percentuali numeriche di copertura non vengono riportati in quanto richiederebbero l'esecuzione della suite, vietata dal vincolo di sola lettura `[V]`.
* Test con asserzioni dipendenti da seed fissi, tolleranze numeriche o costanti empiriche:
  * `tests/test_kelly_core.py:13`: tolleranza `abs(actual - expected) < 1e-12` `[V]`.
  * `tests/test_kelly_core.py:32`: tolleranza e valore atteso `pytest.approx(0.020136, abs=1e-6)` `[V]`.
  * `tests/test_kelly_core.py:39`: tolleranza e valore atteso `pytest.approx(-0.002447, abs=1e-6)` `[V]`.
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
  * `tests/test_metrics.py:33`: tolleranza `np.testing.assert_allclose` `[V]`.
  * `tests/test_metrics.py:43, 52, 61, 82`: tolleranze float `pytest.approx(...)` `[V]`.
  * `tests/test_metrics.py:72`: tolleranza assoluta `atol=1e-12` `[V]`.
  * `tests/test_us_c1_1_acceptance.py:23`: seed fisso `np.random.default_rng(20260905)` `[V]`.
  * `tests/test_us_c1_1_acceptance.py:37`: tolleranza numerica `abs(best_lambda - 1.0) < 1e-6` `[V]`.
  * `tests/test_us_c1_1_acceptance.py:47`: seed fisso `np.random.default_rng(20260905)` `[V]`.
  * `tests/test_us_c1_1_acceptance.py:63`: tolleranza empirica stocastica `np.all(diffs >= -0.01)` `[V]`.
  * `tests/test_us_c1_1_acceptance.py:73`: seed fisso `np.random.default_rng(20260905)` `[V]`.
  * `tests/test_us_c1_1_acceptance.py:78, 82`: costante empirica di zero-crossing `lambda = 1.946` e soglia `abs(g_med) < 0.002` `[V]`.
  * `tests/test_us_c1_1_acceptance.py:92`: seed fisso `np.random.default_rng(20260905)` `[V]`.
  * `tests/test_us_c1_1_acceptance.py:97`: costante empirica di sovrainvestimento `lambda = 2.5` `[V]`.
  * `tests/test_us_c1_2_acceptance.py:27-28`: seed master predefinito `SEED = 20260927` `[V]`.
  * `tests/test_us_c1_2_acceptance.py:45`: seed master predefinito `SEED = 20260927` `[V]`.
  * `tests/test_us_c1_2_acceptance.py:52`: tolleranza `rtol=1e-12` `[V]`.
  * `tests/test_us_c1_2_acceptance.py:58`: seed master predefinito `SEED = 20260927` `[V]`.
  * `tests/test_us_c1_2_acceptance.py:84`: seed master predefinito `SEED = 20260927` `[V]`.
  * `tests/test_us_c1_2_acceptance.py:96`: tolleranza empirica Monte Carlo `abs(moments.var_c - reference) < 0.005` a $\sigma_p = 0.0283$ `[V]`.
  * `tests/test_us_c1_2_acceptance.py:108`: seed master predefinito `SEED = 20260927` e costante rumore $\sigma_p = 0.0283$ `[V]`.
  * `tests/test_us_c1_2_acceptance.py:125`: seed master predefinito `SEED = 20260927` e costante rumore $\sigma_p = 0.0283$ `[V]`.
  * `tests/test_us_c1_2_acceptance.py:148`: seed master predefinito `SEED = 20260927` e costante rumore $\sigma_p = 0.0283$ `[V]`.

### 9. Zone fragili

1. Funzione `expected_final_wealth` completamente sprovvista di test automatizzati:
   * Definita in `src/shk/kelly/core.py:97-144` e impiegata nello script `scripts/us_c1_1_growth_vs_lambda.py` `[V]`.
   * Non è richiamata in alcun test di `tests/` `[V]`.
   * Errori analitici o regressioni numeriche su questa formula passerebbero inosservati `[V]`.

2. Saturazione delle stime a $p̂ = 1.0$ e potenziale rifiuto da parte di `simulate_growth`:
   * La funzione `noisy_estimates` in `src/shk/kelly/estimation.py` satura i valori generati nell'intervallo $[0, 1]$ tramite `np.clip` `[V]`.
   * Con stime saturate a $1.0$, `kelly_staking(1.0, b, lam)` restituisce $\lambda \cdot 1.0$ `[V]`.
   * Se $\lambda \ge 1.0$, la frazione risultante è $\ge 1.0$, che viene deliberatamente rifiutata con `ValueError` da `simulate_growth` (`fractions in [0, 1)`) `[V]`.

3. Duplicazione dei parametri di simulazione C1.1:
   * I parametri ($p=0.60, b=1.0, T=1000, M=10000$, seed `20260905`, griglia di 51 punti da $0.0$ a $2.5$) sono hardcoded sia in `scripts/us_c1_1_growth_vs_lambda.py:30-36` sia in `tests/test_us_c1_1_acceptance.py` `[V]`.
   * Eventuali modifiche future ai parametri rischiano di creare disallineamenti tra l'esperimento pubblicato e la suite di verifica `[V]`.

4. Rischio di dipendenze non vincolate e mancato utilizzo del lockfile in CI:
   * Il file `pyproject.toml` dichiara le dipendenze runtime (`numpy`, `scipy`, `matplotlib`) e dev (`pytest`) senza alcun vincolo di versione minima o massima `[V]`.
   * Il workflow di CI `.github/workflows/test.yml` esegue `pip install -e ".[dev]"` ignorando il file `uv.lock` presente alla radice `[V]`.
   * Variazioni stocastiche introdotte da minor release di NumPy possono causare fallimenti imprevisti nei test con tolleranze empiriche in ambiente CI `[D]`.

5. I test lenti di accettazione Monte Carlo non vengono eseguiti nella pipeline CI:
   * Il file `pyproject.toml` specifica `addopts = "-m 'not slow'"` `[V]`.
   * Il workflow di CI esegue unicamente `pytest -v`, deselezionando tutti i test di accettazione Monte Carlo marcati `@pytest.mark.slow` `[V]`.
   * Regressioni prestazionali o numeriche su larga scala non vengono intercettate durante i controlli push e pull request `[V]`.

6. Omissione nei test di validazione degli argomenti delle metriche:
   * In `tests/test_metrics.py:test_metrics_error_conditions`, la verifica del sollevamento di `ValueError` per forme errate (array 1D o con colonne insufficienti) viene omessa per `median_final_wealth` e `mean_final_wealth` `[V]`.

7. Rigenerazione distruttiva di CSV e figure versionate:
   * L'esecuzione degli script `scripts/us_c1_1_growth_vs_lambda.py` e `scripts/us_c1_2_estimation_error.py` sovrascrive direttamente i file CSV e PNG versionati in Git sotto `results/` e `thesis/figures/` `[V]`.

8. Working tree con modifiche non committate:
   * Il file `.agent/BACKLOG.md` risulta modificato localmente nel working tree (250 righe aggiunte per la pianificazione di Story S2/C2) `[V]`.
   * Il file `.agent/MAPPA.md` risulta modificato localmente nel working tree a seguito della presente mappatura `[V]`.
   * Il file `C1.1.md` risulta cancellato nel working tree locale rispetto all'indice HEAD `[V]`.

### 10. Limiti di questa mappa

* Cosa non è stato ispezionato e perché:
  * Non è stato eseguito alcun codice Python, script di simulazione o suite di test `[V]`.
  * Non sono stati misurati empiricamente i tempi di esecuzione né il consumo di memoria degli script e della suite di test `[V]`.
  * Non sono state interrogate API remote di GitHub per verificare lo stato di esecuzione dei workflow o lo storico dei pull request `[V]`.
  * Tutte le omissioni sopra indicate derivano dal vincolo assoluto di sola lettura del task, finalizzato a garantire l'assenza totale di effetti collaterali (scrittura cache, sincronizzazione venv, rigenerazione file di output) `[V]`.

* Cosa resta incerto:
  * Il tempo effettivo di esecuzione della suite integrale di test (inclusi i test marcati `@pytest.mark.slow`), che richiederebbe l'esecuzione vietata della suite `[V]`.

* Sezioni in prevalenza `[D]`:
  * Sezione 2 ("Come si esegue"): i comandi `uv sync`, `pip install -e .`, `hatch build` / `python -m build`, `pytest -m slow`, `pytest -o addopts=""` e i comandi di lancio degli script Python sono dedotti dalle convenzioni standard degli strumenti di sviluppo, non essendo codificati in specifici file di automazione (es. Makefile o taskfile) `[V]`.

* Domande che farei se dovessi lavorare su questo progetto senza altro contesto:
  1. È previsto un refactoring dello script C1.1 (`scripts/us_c1_1_growth_vs_lambda.py`) e dei relativi test di accettazione affinché adottino il modulo `src/shk/kelly/scenarios.py`, analogamente a quanto realizzato per C1.2, eliminando l'hardcoding duplicato dei parametri?
  2. Per quale motivo `expected_final_wealth` continua a non essere re-esportata in `src/shk/kelly/__init__.py` e non dispone di unit test dedicati in `tests/test_kelly_core.py`?
  3. È pianificata l'adozione di `uv` nel workflow di integrazione continua `.github/workflows/test.yml` per garantire che l'ambiente CI utilizzi le versioni esattamente bloccate in `uv.lock`?
  4. Per la nuova Story S2 (C2), le nuove cartelle e moduli descritti nel backlog (`src/shk/stats/`, `tests/test_anova.py`, ecc.) devono seguire un analogo modulo `scenarios.py` per centralizzare parametri come `SEED_C2` e la sequenza dei generatori?
  5. Qual è lo stato previsto per il file `C1.1.md` (attualmente cancellato nel working tree locale rispetto al commit HEAD): deve essere ripristinato, spostato o rimosso definitivamente dal repository?

### 11. Comandi eseguiti

Elenco completo dei comandi eseguiti durante la sessione di mappatura:

1. `git status` — Esito: codice 0. Rilevato branch `C2` allineato a `origin/C2`, working tree sporco con `modified: .agent/BACKLOG.md`.
2. `git log -n 5` — Esito: codice 0. Ispezionati gli ultimi 5 commit con relativi messaggi estesi.
3. `git log -n 5 --oneline` — Esito: codice 0. Ispezionati gli hash brevi e i titoli degli ultimi 5 commit.
4. `git branch` — Esito: codice 0. Rilevati i branch locali `C1`, `C2`, `feature/US-C1.1-Trade-off-crescita/varianza`, `main`.
5. `git remote -v` — Esito: codice 0. Ispezionati gli URL fetch e push del remote `origin`.
6. `git diff` — Esito: codice 0. Esaminate le modifiche non committate nel file `.agent/BACKLOG.md`.
7. `git log -n 1 --name-only 1e7813d` — Esito: codice 0. Verificati i file toccati dal commit `1e7813d`.
8. `git log -n 1 --name-only 640b906` — Esito: codice 0. Verificati i file toccati dal commit `640b906`.
9. `git log -n 1 --name-only 6187309` — Esito: codice 0. Verificati i file toccati dal commit `6187309`.
10. `git log -n 10 --oneline` — Esito: codice 0. Verificata la storia completa dei commit del repository (totale 6 commit).
11. `git log --oneline --decorate -n 6` — Esito: codice 0. Ispezionati i puntatori di tutti i branch locali e remoti.
12. `git log -n 1 --oneline C1` — Esito: codice 0. Ispezionato l'ultimo commit del branch locale `C1`.
13. `git branch -v -a` — Esito: codice 0. Verificato lo stato di tutti i branch locali e remoti con i relativi hash.
14. `git diff --stat` — Esito: codice 0. Quantificate le modifiche non staged su `.agent/BACKLOG.md` (250 inserimenti, 1 cancellazione).
15. `git diff --name-only 4b825dc642cb6eb9a060e54bf8d69288fbee4904 HEAD` — Esito: codice 0. Rilevato l'inventario completo di tutti i file tracciati nel commit HEAD confrontato con il tree vuoto di Git.
16. `git status --ignored` — Esito: codice 0. Ispezionati i file e le directory ignorate nel filesystem locale.
17. `git status` — Esito: codice 0. Verifica dello stato prima della prima scrittura della mappa.
18. `git status` — Esito: codice 0. Verifica dello stato dopo la scrittura della mappa; rilevata la presenza di `deleted: C1.1.md` nel working tree locale.
19. `git diff C1.1.md` — Esito: codice 1 (fallito). Segnalato `fatal: ambiguous argument 'C1.1.md': unknown revision or path not in the working tree`.
20. `git diff -- C1.1.md` — Esito: codice 0. Verificato il diff relativo alla rimozione di `C1.1.md` nel working tree rispetto all'indice.
21. `git status` — Esito: codice 0. Verifica dello stato del repository.
22. `git status` — Esito: codice 0. Verifica finale dello stato del repository.

Dichiarazione:
Tutti i comandi eseguiti sono comandi git di sola lettura appartenenti all'insieme consentito (`git status`, `git log`, `git branch`, `git remote -v`, `git diff`). Nessun comando al di fuori di tale insieme è stato eseguito. Nessun codice del progetto, script o suite di test è stato eseguito. Nessun file o directory è stato modificato o creato nel filesystem, ad eccezione dell'autorizzata scrittura del file `.agent/MAPPA.md`.
