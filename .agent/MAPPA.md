Mappa completa — 2026-10-11 — R1

Legenda: `[V]` verificato in questa sessione (file aperto o ricerca eseguita); `[D]` dedotto (nome, convenzione, struttura, documenti di `.agent/`), non riletto nel codice. Percorsi sempre dalla radice del repository. Mappa precedente: `.agent/MAPPA.md` del 2026-10-07 [V, intestazione letta prima della sovrascrittura].

### 0. Stato del repository

- Radice: `C:\Users\malse\Documents\GitHub\structural_hybrid_kelly` [V].
- Branch corrente: `C6` [V].
- Working tree pulito all'inizio della mappatura [V]. Dopo la scrittura di questo file sarà modificato `.agent/MAPPA.md`, che è tracciato da git [V: compare in `git ls-files`].
- Ultimi cinque commit [V]:
  - `c427e33 end c6`
  - `632d5a1 d`
  - `6851ccf T33-T34`
  - `833a4d8 manca il backlog della C6`
  - `736f5cd C5 (#20)`
- Remote: `origin https://github.com/Fede046/structural_hybrid_kelly.git` (fetch e push) [V].
- `C6` traccia `origin/C6` ed è allineato ("up to date") [V], secondo i ref locali: nessun `git fetch` è stato eseguito, quindi lo stato reale del remote non è controllato [V].
- Altri branch locali: `main` su `736f5cd` (traccia `origin/main`) e `pre-c4` su `5249f9b` (traccia `origin/pre-c4`) [V].

### 1. Identikit

- Nome: `structural-hybrid-kelly`, versione `0.1.0` [V, `pyproject.toml`]. Il pacchetto importabile è `shk` [V, `src/shk/__init__.py`, `pyproject.toml` → `packages = ["src/shk"]`].
- Cosa fa: codice di ricerca per una tesi [D, dalla directory `thesis/figures/`]. Studia il criterio di Kelly in forma analitica e simulata, e lo applica alle partite di Premier League (divisione `E0`) con un modello Elo-Davidson walk-forward e quote B365 [V, moduli `src/shk/kelly/`, `src/shk/model/elo*.py`, `src/shk/market/divergence.py`]. Comprende anche drift detection (ADWIN, Page-Hinkley), test di eteroschedasticità e backtest appaiati di agenti di scommessa [V].
- Linguaggio: Python [V]. Richiesto `>=3.11` [V, `pyproject.toml`]. La CI usa 3.12 [V, `.github/workflows/test.yml`]. Il `.venv` locale è Python 3.12.7, creato da anaconda [V, `.venv/pyvenv.cfg`].
- Dipendenze runtime: `numpy`, `scipy`, `matplotlib`, `pandas`, `river`, nessuna con versione vincolata [V, `pyproject.toml`].
- Dipendenze dev: `pytest`, `statsmodels` [V].
- Build system: `hatchling` [V].
- Gestore pacchetti: `uv.lock` è presente e versionato [V], quindi uv è usato in locale [D]. La CI usa invece `pip install -e ".[dev]"` e ignora `uv.lock` [V].

### 2. Come si esegue

- Installazione: `pip install -e ".[dev]"` [V, step della CI]. In alternativa `uv sync` [D, dalla presenza di `uv.lock`; nessun file lo documenta].
- Avvio in sviluppo: non esiste un server né un entry point [V: `pyproject.toml` non ha `[project.scripts]`]. Gli esperimenti sono script standalone: `python scripts/us_c<X>_<Y>_<nome>.py` [D: nessun file documenta il comando]. Ciascuno ha un blocco `if __name__ == "__main__":` [V].
- Build: `hatchling` produce un wheel di `src/shk` [V]. Nessun comando di build è documentato [V: nessun README nella radice, cfr. `ls -la`].
- Test: `pytest -v` [V, CI]. `pyproject.toml` imposta `addopts = "-m 'not slow'"`, quindi i test `slow` sono esclusi di default [V]. Per lanciarli serve `pytest -m slow` [D].
- Variabili d'ambiente lette: nessuna [V: ricerca di `os.environ` e `getenv` in `src/`, `scripts/` e `tests/` senza risultati].
- File di configurazione richiesti:
  - `config/split.toml`, con le chiavi `frozen_on`, `test_unlocked`, `test_unlocked_on`, `training`, `validation`, `test` [V].
  - I CSV grezzi in `data/raw/E0/<YYYY-YY>.csv` [V, `src/shk/data/loading.py:14`]. In locale ce ne sono 31, dal `1993-94` al `2023-24` [V]. Non sono versionati: `.gitignore` esclude `data/raw/*` [V]. Da quale fonte vengano non lo so: non ho cercato nel repository.
- Prerequisito degli script: il pacchetto `shk` deve essere importabile [V: gli script fanno `from shk...` senza manipolare `sys.path`; ricerca di `sys.path` in `scripts/` senza risultati].

### 3. Albero delle directory

- `src/shk/`: pacchetto della libreria [V].
  - `src/shk/data/`: caricamento dei CSV E0, split congelato e blocco del test set, audit di copertura, fornitore walk-forward e controlli anti-leakage [V].
  - `src/shk/kelly/`: formule di Kelly, staking, simulazione Monte Carlo, metriche, agenti, ambiente di backtest appaiato, esperimenti sintetici sul floor [V].
  - `src/shk/market/`: de-vigging (proporzionale, additivo, power) e divergenza fra metodi per fascia di quota [V].
  - `src/shk/model/`: Elo-Davidson, calibrazione dei fit, predittore walk-forward, scoring (log-loss, ĝ), ricalibrazione, residui, monitoraggio (drift, z-test, Baseline D) e pipeline C6 (backtest appaiato, floor reale, eteroschedasticità) [V].
  - `src/shk/stats/`: ANOVA, calibrazione per moving block bootstrap, drift detector, falso rigetto, test BP/White, serie AR(1) [V].
- `scripts/`: 15 script `us_c<X>_<Y>_*.py`, uno per esperimento o user story. Ciascuno scrive un CSV in `results/` e una figura in `thesis/figures/` [V].
- `tests/`: 25 file di test unitari, uno per modulo [V]. Più 14 file di accettazione `test_us_c<X>_<Y>_acceptance.py` [V].
- `results/`: 15 CSV versionati, output degli script [V]. I test di accettazione li rileggono [V].
- `thesis/figures/`: 15 PNG versionati, output degli script [V].
- `config/`: contiene `split.toml` [V].
- `data/raw/`: CSV grezzi, non versionati, a parte `.gitkeep` [V].
- `.agent/`: file di stato del protocollo [V]:
  - `PROTOCOLLO.md`;
  - `SCHEDA.md`;
  - `BACKLOG.md`;
  - `MAPPA.md`;
  - `report/T1.md` … `report/T39.md`.
- `.github/workflows/`: un solo workflow, `test.yml` [V].
- Esclusi da questa mappa: `.venv/`, `.pytest_cache/`, `tests/__pycache__/` (presenti in locale [V], ignorati da `.gitignore` [V]).

### 4. Moduli principali

Ho scelto i dieci moduli della pipeline sui dati reali e del backtest di C6.

Esclusi:
- `src/shk/data/walkforward.py` e `src/shk/data/coverage.py`;
- `src/shk/market/devig.py` e `src/shk/market/divergence.py`;
- `src/shk/model/elo.py`, `src/shk/model/recalibration.py`, `src/shk/model/floor_real_config.py` e `src/shk/model/residual_heteroskedasticity.py`;
- `src/shk/kelly/` tranne `agents.py` ed `environment.py` (cioè `core.py`, `staking.py`, `simulate.py`, `metrics.py`, `scenarios.py`, `estimation.py`, `backtest.py`, `floor.py`);
- tutto `src/shk/stats/`.

Di questi esclusi ho letto solo docstring, firme, costanti e import [V].

1. `src/shk/data/loading.py`
   - Responsabilità: carica e valida i CSV di stagione in un unico DataFrame [V]. Si occupa della decodifica (BOM, utf-8 o cp1252), delle righe irregolari, delle colonne senza nome, del formato delle date e della finestra stagionale [V].
   - Espone: `load_all_seasons(data_dir, seasons)` e `DEFAULT_DATA_DIR` [V].
   - Dipende da: nessun modulo interno [V].
2. `src/shk/data/split.py`
   - Responsabilità: legge e valida `config/split.toml`, poi carica le partite per ruolo bloccando il test set [V].
   - Espone: `read_split_config`, `load_by_role(role)` con i ruoli `training`, `validation`, `test` e `history` [V]. Espone anche `SplitConfig` (NamedTuple), `TestSetLockedError` e `DEFAULT_SPLIT_CONFIG_PATH` [V].
   - Dipende da: `shk.data.loading` [V].
3. `src/shk/model/elo_predictor.py`
   - Responsabilità: previsioni Elo walk-forward 1X2, con una regola d'ingresso per le neopromosse [V].
   - Espone [V]:
     - `predict_elo_walkforward`: passa dal fornitore walk-forward con `assert_no_leakage`;
     - `predict_elo_fast`: passata unica raggruppata per data;
     - `compute_season_standings`;
     - `diagnose_season_transitions`.
   - Dipende da: `shk.data.walkforward` e `shk.model.elo` [V].
4. `src/shk/model/elo_fit.py`
   - Responsabilità: calibra (K, h, ν) con Nelder-Mead, deriva lo schema dei fit dallo split e contiene i parametri congelati [V].
   - Espone: `ELO_FITS` (fit `2000-01`, `2010-11` e `2020-21`, calibrati il 2026-09-29 [V, commento a `src/shk/model/elo_fit.py:320`]), `derive_fit_schedule`, `parse_season_start_year`, `compute_training_log_loss`, `calibrate_single_fit`, `calibrate_all_fits` ed `EloFitParams` [V].
   - Dipende da: `shk.data.split.SplitConfig`, `shk.model.elo` e `shk.model.elo_predictor` [V].
5. `src/shk/model/scoring.py`
   - Responsabilità: log-loss, termini ĝ, previsioni di validazione per fit e allineamento delle previsioni alle righe grezze [V].
   - Espone: `compute_log_loss`, `compute_mean_log_loss`, `compute_g_hat*`, `generate_validation_predictions`, `align_predictions_with_odds`, `prepare_series_evaluation` e `MATCH_KEYS` (season, Date, HomeTeam, AwayTeam) [V].
   - Dipende da: `shk.market.devig`, `shk.model.elo_fit` e `shk.model.elo_predictor` [V].
6. `src/shk/model/residuals.py`
   - Responsabilità: produce il DataFrame dei residui del Modulo 1 raw, cioè la log-loss per partita su training e validazione di ogni fit [V].
   - Espone: `compute_model_residuals(df, schedule, fits)` e `RESIDUALS_COLUMNS` (11 colonne) [V].
   - Dipende da: `shk.model.elo_fit` e `shk.model.scoring` [V].
7. `src/shk/model/monitoring.py` (1351 righe [V])
   - Responsabilità: serie per scenario, record dei drift detector (C5.1), z-test giornaliero (C5.2) e Baseline D con calibrazione di κ (C5.3) [V].
   - Espone: `extract_scenario_series`, `generate_drift_detector_records`, `generate_daily_z_test_records`, `assemble_baseline_d_season_input`, `calibrate_baseline_d_kappa`, `evaluate_baseline_d_agents`, `generate_baseline_d_records` e varie NamedTuple [V].
   - Dipende da: `shk.kelly.backtest`, `shk.kelly.metrics`, `shk.kelly.staking`, `shk.model.elo_fit`, `shk.model.scoring`, `shk.stats.drift` e `shk.stats.false_rejection` [V].
8. `src/shk/kelly/agents.py`
   - Responsabilità: agenti di scommessa con una base comune [V]. La base `Agent` sceglie l'esito, valida e fissa il ripiego. Le sottoclassi ridefiniscono solo `__init__` e `stake_fractions`; il vincolo è imposto in `__init_subclass__` [V].
   - Espone: `Agent`, `FractionalKellyAgent`, `MinimumStakeAgent`, `DateView`, `AgentDecision`, `estimated_expected_values`, `NO_BET`, `AGENT_A_LAMBDA` e `AGENT_B_LAMBDAS` [V].
   - Dipende da: `shk.kelly.staking` [V].
9. `src/shk/kelly/environment.py`
   - Responsabilità: ambiente passo-passo multi-agente [V]. Gestisce la ricchezza, il floor F, la puntata forzata di ripiego, la rovina e il regolamento [V].
   - Espone: `run_paired_backtest`, `place_date_stakes`, `floor_thresholds`, `AgentRun` e `PlacedBets` [V]. `DateView` è importato da `agents` e riesportato di fatto: `src/shk/model/floor_real_config.py` lo importa da qui [V].
   - Dipende da: `shk.kelly.agents` [V].
10. `src/shk/model/paired_backtest.py`
    - Responsabilità: esegue gli agenti A, B_0.25, B_0.10 ed E sulle 19 stagioni di validazione, con 3 configurazioni di floor (`none`, `gbp_0.01`, `gbp_1`, normalizzate su £220) [V].
    - Espone: `evaluate_validation_seasons`, `build_season_agents`, `CONFIGURATIONS` e `PAIRED_BACKTEST_CSV_COLUMNS` (31 colonne) [V].
    - Dipende da: `shk.kelly.agents`, `shk.kelly.environment`, `shk.kelly.metrics`, `shk.model.elo_fit` e `shk.model.monitoring` [V].

### 5. Punti di ingresso e flussi

Punti di ingresso: i 15 file di `scripts/` [V]. Tredici chiamano `run_experiment()` [V]. Due chiamano `main()`: `scripts/us_c6_3_floor_real_config.py` e `scripts/us_c6_4_heteroskedasticity.py` [V]. A questi si aggiunge la suite `pytest` [V]. Non esistono entry point installati [V].

**Flusso 1 — preparazione dei dati reali e residui del Modulo 1** (prefisso comune agli script da C4 a C6)
- Il prefisso è identico in `scripts/us_c5_*.py`, `scripts/us_c6_2_paired_backtest.py`, `scripts/us_c6_3_floor_real_config.py` e `scripts/us_c6_4_heteroskedasticity.py` [V]. Negli script C4 l'avvio è lo stesso (`load_by_role` per tre ruoli) [V]; il resto della catena lì non l'ho riletto [D].
- Catena:
  1. `read_split_config()` [V];
  2. `load_by_role("history")`, `load_by_role("training")` e `load_by_role("validation")` → `load_all_seasons(seasons=…)` [V];
  3. `pd.concat` e ordinamento stabile per `Date` [V];
  4. `derive_fit_schedule(cfg)` [V];
  5. `compute_model_residuals(df, schedule, ELO_FITS)` [V]. A sua volta chiama:
     - per la validazione, `generate_validation_predictions` → `predict_elo_fast` [V];
     - per il training di ogni fit, `compute_training_log_loss` [V];
     - per entrambi, `align_predictions_with_odds` e poi `compute_log_loss` [V].
- Replicato: nei test di accettazione su dati reali, con gli stessi passi e gli stessi parametri [V]. Esempi: `tests/test_us_c6_2_acceptance.py:109-119` e `:311-321`, `tests/test_us_c6_3_real_acceptance.py:328-337`, `tests/test_us_c6_4_acceptance.py:255-265`, `tests/test_us_c5_*_acceptance.py` [V]. Divergenze nei parametri di questi esempi: nessuna [V].

**Flusso 2 — backtest appaiato C6.2**
- Catena (`scripts/us_c6_2_paired_backtest.py`):
  1. Flusso 1;
  2. `evaluate_validation_seasons(df_residuals, df, schedule)` [V]. Per ogni stagione di validazione:
     - `assemble_baseline_d_season_input(role="validation")` (`src/shk/model/monitoring.py`) [V];
     - FTR trasformato in interi 0/1/2 [V];
     - per ogni configurazione, `build_season_agents(min_stake)` → `run_paired_backtest` [V]. Per ogni data, `run_paired_backtest` chiama `Agent.decide` e poi `place_date_stakes` [V];
     - metriche `wealth_max_drawdown` e `wealth_recovery_time` [V];
  3. 209 righe di stagione e 11 di riepilogo, scritte in `results/us_c6_2_paired_backtest.csv` [V, docstring], più la figura `thesis/figures/us_c6_2_paired_backtest.png` [V].
- Replicato: in `tests/test_us_c6_2_acceptance.py:309-338`, ricalcolo confrontato col CSV versionato con `rel_tol=1e-12` [V]. Stessi parametri; il test non rigenera la figura, ne controlla solo l'esistenza [V, `:305-307`].
- Variante: `evaluate_floor_real_config` (`src/shk/model/floor_real_config.py:383`) rifà lo stesso giro [V], con due differenze:
  - gli esiti sono M = 1000 repliche estratte da `sample_match_outcomes` sulle quote B365 [V];
  - i semi vengono da `SeedSequence(SEED_C6).spawn(2)[1].spawn(19)` [V].
- La variante è replicata in `tests/test_us_c6_3_real_acceptance.py:339-344` con `m_replicas=1000` e `seed=SEED_C6`, cioè i default [V].

**Flusso 3 — esperimenti sintetici sul floor (C6.3)**
- Catena (`scripts/us_c6_3_floor_synthetic.py:176`):
  1. `evaluate_all_synthetic_experiments()` [V];
  2. `spawn_t36_generators(SEED_C6)`, che usa `SeedSequence(seed).spawn(2)[0].spawn(3)` [V];
  3. `run_experiment_a`, `run_experiment_b` e `run_experiment_c` [V];
  4. `run_paired_chunked` → `run_paired_backtest` [D: `floor.py` importa `run_paired_backtest` e definisce `run_paired_chunked`, ma il corpo non l'ho letto].
- Replicato:
  - `tests/test_us_c6_3_acceptance.py:195-197` (slow) chiama `evaluate_all_synthetic_experiments(seed=SEED_C6)` con il `chunk_size` di default [V].
  - `tests/test_us_c6_3_acceptance.py:93-95` chiama `run_experiment_a(rng_a, m_replicas=100, chunk_size=50)` [V]. Diverge dallo script: lo script usa i default `EXP_A_M = 10_000` (`src/shk/kelly/floor.py:31`) e `DEFAULT_CHUNK_SIZE = 2_000` (`:134`) [V].

Due motori di backtest:
- `src/shk/model/monitoring.py:15` usa `shk.kelly.backtest.backtest_log_wealth` per la Baseline D di C5.3 [V].
- C6 usa `shk.kelly.environment.run_paired_backtest` [V].
- `tests/test_us_c6_2_acceptance.py:61-105` verifica che B_0.25 con F = 0 coincida con C5.3: entro 1e-12, con 6234 puntate totali [V].

### 6. Modello dei dati

Non esistono classi di dominio ORM né persistenza: niente database e niente migrazioni [V]. Le uniche persistenze sono i CSV di output e `config/split.toml`. Le strutture in circolo sono queste.

- **DataFrame grezzo E0**:
  - colonne originali dei CSV, più `season` (stringa `YYYY-YY`) [V, `src/shk/data/loading.py`];
  - `Date` convertita in datetime64 [V];
  - ordinato stabilmente per `season` e `Date` [V].
  - Le colonne usate a valle sono `HomeTeam`, `AwayTeam`, `FTR`, `FTHG`, `FTAG` [V, `REQUIRED_INPUT_COLUMNS` in `src/shk/model/residuals.py:28`] e `B365H`, `B365D`, `B365A` [V, `src/shk/model/monitoring.py`, `src/shk/market/divergence.py:33`].
- **`SplitConfig`** (NamedTuple, `src/shk/data/split.py:27`): contiene date di congelamento e sblocco e tuple di stagioni per ruolo [V].
  - Valori attuali: training `2000-01`, `2010-11` e `2020-21`; 19 stagioni di validazione; test `2023-24` bloccato [V, `config/split.toml`].
  - Il ruolo `history` comprende le stagioni anteriori al test e non assegnate [V, `load_by_role`].
- **Schema dei fit**: `dict[fit_through, {"training": [...], "validation": [...]}]` [V, `derive_fit_schedule`].
- **`EloFitParams`** (k, h, nu, c) [V, `src/shk/model/elo_fit.py:68` e `:321`].
- **DataFrame dei residui**: 11 colonne `RESIDUALS_COLUMNS` [V]:
  - `fit_through`, `role`, `season`, `Date`, `HomeTeam`, `AwayTeam`;
  - `p_home`, `p_draw`, `p_away`;
  - `FTR`, `log_loss`.
  - Ha 9500 righe sui dati reali [V, asserzione `tests/test_residuals.py:297`].
- **`BaselineDSeasonInput`** (`src/shk/model/monitoring.py:717`): `season`, `dates` (datetime64), `probs` e `odds` di forma (N, 3), `ftr` (stringhe H/D/A), `log_loss` [V].
- **Vista di un giorno e decisione** (`src/shk/kelly/agents.py`):
  - `DateView` (date, probs, odds) e `AgentDecision` (outcomes, fractions, fallback_match, fallback_outcome) [V];
  - sono dataclass frozen con array in sola lettura [V].
- **Esiti dell'ambiente** (`src/shk/kelly/environment.py`):
  - `PlacedBets` e `AgentRun`: wealth di forma (M, D+1), ruined, ruin_date_index e contatori [V];
  - anche qui array in sola lettura [V].
- **Codifica degli esiti** [V]:
  - interi 0 = H, 1 = D, 2 = A, `NO_BET = -1` negli agenti e nell'ambiente;
  - stringhe `"H"`, `"D"`, `"A"` nei DataFrame;
  - la conversione avviene in `src/shk/model/paired_backtest.py` (`_FTR_OUTCOME_MAP`).
- **Record di output**: liste di `dict` con chiavi uguali a una tupla `*_CSV_COLUMNS` per modulo [V]. Esempi: `PAIRED_BACKTEST_CSV_COLUMNS`, `FLOOR_REAL_CSV_COLUMNS`, `BASELINE_D_CSV_COLUMNS`, `HETEROSKEDASTICITY_CSV_COLUMNS`, `DRIFT_DETECTOR_CSV_COLUMNS`. Gli script li scrivono con `csv.DictWriter` o `DataFrame.to_csv` [V].

### 7. Convenzioni in vigore

- **Lingua**:
  - docstring e commenti in italiano [V, in tutti i moduli letti];
  - messaggi delle eccezioni in inglese [V, campioni in `loading.py`, `split.py`, `agents.py`, `environment.py`, `paired_backtest.py`, `monitoring.py`];
  - nomi dei test in inglese [V: una ricerca di parole italiane comuni nei nomi `def test_` non ha dato risultati; è una ricerca euristica].
- **Docstring**: stile numpy con sezioni in italiano `Parametri`, `Restituisce`, `Solleva` [V].
- **Validazione degli input**: esplicita e severa [V]. Usa `isinstance` escludendo `bool` dagli interi e dai float, controlla la finitezza e solleva `TypeError` o `ValueError` [V].
- **Costanti**: a livello di modulo in MAIUSCOLO con `Final[...]` [V]. Ogni output CSV ha la sua tupla `*_CSV_COLUMNS` [V].
- **Riproducibilità**: semi fissi con gerarchie di `np.random.SeedSequence.spawn` [V]:
  - `SEED = 20260927` in `src/shk/kelly/scenarios.py:9`;
  - `SEED_C2 = 20260928` in `src/shk/stats/false_rejection.py:17`;
  - `SEED_C5 = 20260929` in `src/shk/stats/drift.py:25`;
  - `SEED_C6 = 20261009` in `src/shk/kelly/floor.py:21`;
  - il seed locale `20260905` in `scripts/us_c1_1_growth_vs_lambda.py:35`.
- **Logging e output a console**: nessun `print(` in `src/` e `scripts/` [V, ricerca]. Nessun `import logging`, `getLogger` o `warnings.warn` [V, ricerca]. Alcuni test lo verificano via AST [V, `tests/test_us_c6_3_real_acceptance.py:368-390`, `tests/test_agents.py:784`].
- **Script**:
  - impostano `matplotlib.use("Agg")` [V];
  - scrivono in `results/` e `thesis/figures/` [V];
  - salvano le figure a 150 o 300 dpi [V].
- **Nessun TODO, FIXME, XXX o HACK** in `src/`, `scripts/`, `tests/` e `.github/` [V, ricerca].

Incoerenze rilevate:
- **Costanti senza `Final`**: in `src/shk/stats/false_rejection.py:13-34` e `src/shk/kelly/scenarios.py:9` [V], mentre negli altri moduli usano `Final` [V].
- **Percorsi di output degli script**:
  - `scripts/us_c1_1_growth_vs_lambda.py:86-87`, `scripts/us_c1_2_estimation_error.py:147-148` e `scripts/us_c2_anova_autocorrelation.py:40-41` usano `os.path` relativo alla directory corrente [V];
  - gli altri script usano `Path(__file__).resolve().parents[1]` [V].
- **Funzione d'ingresso degli script**: `run_experiment()` in 13 script, `main()` in 2 [V, cfr. §5].
- **Backend `Agg`**: manca `matplotlib.use("Agg")` in `scripts/us_c6_3_floor_real_config.py` e `scripts/us_c6_3_floor_synthetic.py` [V: la ricerca lo trova negli altri 13].
- **Accenti**: alcune docstring scrivono l'accento come apostrofo (`e'`, `probabilita'`, `eteroschedasticita'`) [V, `src/shk/data/loading.py`, `src/shk/data/split.py`, `src/shk/model/floor_real_config.py`, `src/shk/stats/heteroskedasticity.py`]. Altre usano `è` e `à` [V, `src/shk/kelly/agents.py`, `src/shk/model/residual_heteroskedasticity.py`].
- **Sottolineatura delle sezioni docstring**: 10 trattini in `loading.py` e `split.py`, 9 negli altri moduli letti [V].
- **Lingua dei motivi di skip e dei messaggi di assert nei test**: mista [V]. Esempi:
  - in inglese: `"Requires real data in data/raw/E0"` (`tests/test_us_c6_2_acceptance.py:108`);
  - in italiano: `"Dati reali non presenti sul filesystem"` (`tests/test_us_c5_2_acceptance.py:476`) e `"Attese 1140 partite training…"` (`tests/test_leakage.py:434`).
  
  La SCHEDA la registra come decisione aperta [D, `.agent/SCHEDA.md`].
- **`assert` usati per il narrowing dei tipi nel codice di libreria**: `src/shk/model/elo.py:163-356` (9 occorrenze) e `src/shk/model/elo_predictor.py:282` [V].
- **Helper privati duplicati e non condivisi**: `_is_real_numeric_dtype` e `_read_only_view` sono identici in `src/shk/kelly/agents.py:38,56` e `src/shk/kelly/environment.py:28,46` [V].
- **Parsing della stagione `YYYY-YY` ripetuto**:
  - `SEASON_REGEX` in `src/shk/model/elo_fit.py:21` e in `src/shk/model/elo_predictor.py:13` [V];
  - `parse_season_start_year` (`elo_fit.py:96`) e `_parse_season_start_year` (`elo_predictor.py:91`) [V];
  - regex locali in `src/shk/data/loading.py` e `src/shk/data/split.py` [V].
- **`ALPHA` e `BLOCK_LENGTHS` ridefiniti**: in `src/shk/model/residual_heteroskedasticity.py:33,36` invece di importarli da `src/shk/stats/false_rejection.py:16,19`, come fanno `src/shk/stats/drift.py` e `src/shk/model/monitoring.py` [V].

### 8. Test

- **Dove**: `tests/`, struttura piatta, 39 file [V]. Le funzioni `def test_` di primo livello sono 407 [V, ricerca]; la parametrizzazione ne moltiplica il numero effettivo [D].
- **Tipi** [V]:
  - test unitari per modulo (`test_<modulo>.py`);
  - test di accettazione per user story (`test_us_c<X>_<Y>_acceptance.py`), che verificano criteri statistici, la coerenza dei CSV versionati in `results/` e il ricalcolo dai dati reali;
  - controlli AST di convenzione, per esempio in `tests/test_heteroskedasticity.py:330` e `tests/test_split.py:437-454`.
- **Test confrontati con implementazioni esterne**: `tests/test_hac_anova_lm.py` e `tests/test_heteroskedasticity.py` usano `statsmodels` come riferimento [V].
- **Test `slow`**: marcati in 6 file [V]:
  - `tests/test_us_c1_1_acceptance.py`;
  - `tests/test_us_c1_2_acceptance.py`;
  - `tests/test_us_c2_acceptance.py`;
  - `tests/test_us_c4_1_acceptance.py`;
  - `tests/test_us_c6_3_acceptance.py`, solo `:194-195`.

  Sono esclusi di default da `addopts` [V].
- **Test su dati reali**: vengono saltati se `data/raw/E0/` manca o non contiene CSV [V, funzioni `_has_real_data` e `pytest.skip`]. In CI quindi non girano mai [D: la CI non scarica dati e `.gitignore` li esclude, cfr. §9].
- **Come si lanciano**: `pytest -v` [V, CI]; `pytest -m slow` per i lenti [D].
- **Numeri di esecuzione**: non riportati. Servirebbe eseguire la suite.

Funzioni e classi pubbliche di `src/shk/` mai nominate in nessun file di `tests/` [V, ricerca per nome intero; alcune possono essere esercitate indirettamente, per esempio `assemble_baseline_d_season_input` tramite `evaluate_validation_seasons` [D]]:
- `src/shk/kelly/core.py`: `expected_final_wealth`.
- `src/shk/kelly/floor.py`: `run_experiment_b`, `run_experiment_c`, `ExpCConfig`, `ExperimentARunResult`, `ExperimentBResult`, `ExperimentCConfigResult`.
- `src/shk/model/elo_fit.py`: `calibrate_all_fits`, `EloCalibrationResult`.
- `src/shk/model/floor_real_config.py`: `compute_season_metrics`.
- `src/shk/model/monitoring.py`: `assemble_baseline_d_season_input`, `KappaCalibrationRow`, `BaselineDAgentResult`.
- `src/shk/model/recalibration.py`: `generate_fit_training_predictions`, `IsotonicModel`, `PlattModel`, `FitCalibrationMaps`.
- `src/shk/model/residual_heteroskedasticity.py`: `extract_scenario_and_training_data`, `calibrate_block_bootstrap_thresholds`, `verify_calibrated_thresholds`, `ScenarioData`, `TrainingData`.
- `src/shk/stats/drift.py`: `calibrate_adwin`, `calibrate_page_hinkley`.
- `src/shk/stats/false_rejection.py`: `spawn_c2_generators`, `PhiStreams`.

Tutte le altre funzioni e classi pubbliche di primo livello sono nominate almeno una volta nei test [V]. Che compaiano dentro un'asserzione, e non solo in un import o in una chiamata di preparazione, non l'ho verificato funzione per funzione [D].

Test le cui asserzioni dipendono da seed fissi, tolleranze o costanti empiriche [V, righe lette o trovate con la ricerca]:
- **Conteggi empirici sui dati reali**:
  - `tests/test_split.py:483-491` (1140, 7220, 3204);
  - `tests/test_leakage.py:434-436` (1140, 7220, 8360);
  - `tests/test_residuals.py:283-297` (380, 760, 1140, 3040, 3420, 760, 9500);
  - `tests/test_drift.py:318-319`;
  - `tests/test_us_c4_1_acceptance.py:123-150`;
  - `tests/test_us_c3_2_acceptance.py:208`.
- **Medie empiriche di log-loss**: `tests/test_residuals.py:311-326`, `pytest.approx(…, abs=5e-7)` [V].
- **Totale di puntate empirico**: `tests/test_us_c6_2_acceptance.py:104-105`, 6234 [V].
- **Ricalcolo contro CSV versionato con tolleranza 1e-12**:
  - `tests/test_us_c6_2_acceptance.py:334-336`;
  - `tests/test_us_c6_3_real_acceptance.py:373-375`, che usa anche `SEED_C6` e 1000 repliche;
  - `tests/test_us_c6_4_acceptance.py:267-270`, che usa `SEED_C6`.
- **Costanti Monte Carlo**: `tests/test_floor.py:73,82,91` (μ empiriche con `rel_tol=0.005`) [V].
- **Valori numerici attesi**: `tests/test_kelly_core.py:32,39` (`approx(…, abs=1e-6)`) [V].
- **Banda di rigetto con `default_rng` a seed fisso**: `tests/test_heteroskedasticity.py:302-305` (0.0322–0.0678) [V].
- **Seed di modulo** [V]:
  - `SEED_C2` in `tests/test_us_c2_acceptance.py`, da `:49` a `:372`;
  - `SEED` in `tests/test_us_c1_2_acceptance.py:27-148`;
  - `SEED_C6` in `tests/test_us_c6_3_acceptance.py:93-95,197`.
- **`np.random.default_rng(<intero>)` con seed letterale** [V, conteggio per file]:
  - `tests/test_calibration.py` (21);
  - `tests/test_timeseries.py` (11);
  - `tests/test_anova.py` (10);
  - `tests/test_simulate.py` (8);
  - `tests/test_drift.py` e `tests/test_estimation.py` (7 ciascuno);
  - `tests/test_heteroskedasticity.py` e `tests/test_us_c6_3_real_acceptance.py` (4 ciascuno);
  - `tests/test_us_c1_1_acceptance.py` (4);
  - `tests/test_devig.py`, `tests/test_environment.py`, `tests/test_floor.py` e `tests/test_us_c6_4_acceptance.py` (2 ciascuno);
  - `tests/test_hac_anova_lm.py` e `tests/test_metrics.py` (1 ciascuno).
- **Tolleranze numeriche** (`rel_tol`, `abs_tol`, `atol`, `rtol`, `approx`, `assert_allclose`): presenti in 27 file [V, ricerca]. I più densi:
  - `tests/test_heteroskedasticity.py` (21);
  - `tests/test_staking.py` (21);
  - `tests/test_us_c6_2_acceptance.py` (15);
  - `tests/test_us_c5_3_acceptance.py` (14).

### 9. Zone fragili

- **Pipeline del Flusso 1 copiata**: carico per ruolo, concateno, ordino, derivo lo schema e calcolo i residui [V]. La sequenza è ripetuta testualmente in almeno 9 script (da `scripts/us_c4_1_elo_walkforward.py` a `scripts/us_c6_4_heteroskedasticity.py`) e in numerosi test di accettazione [V, ricerca di `load_by_role(` e `compute_model_residuals(`]. Non c'è una funzione condivisa [V: nessuna in `src/` ne incapsula la sequenza, per quanto letto].
- **Due motori di backtest**: `src/shk/kelly/backtest.py` (C5.3) e `src/shk/kelly/environment.py` (C6) [V]. L'equivalenza è garantita da `tests/test_us_c6_2_acceptance.py:61-105`, che richiede i dati reali e quindi in CI viene saltato [V, `skipif` alla riga 108; il test alla riga 61 legge solo i CSV versionati: non l'ho riletto per intero, D].
- **Accoppiamenti fra strati**:
  - `src/shk/model/paired_backtest.py` e `src/shk/model/floor_real_config.py` dipendono da `src/shk/model/monitoring.py` per `assemble_baseline_d_season_input` [V]: C6 dipende da un modulo di C5.
  - `SEED_C6` è definito in `src/shk/kelly/floor.py:21` e importato da `src/shk/model/floor_real_config.py`, `src/shk/model/residual_heteroskedasticity.py`, dagli script e dai test [V].
- **Gerarchia dei semi di C6 distribuita su tre file** [V]:
  - `spawn(2)[0]` in `src/shk/kelly/floor.py:165-168`;
  - `spawn(2)[1]` in `src/shk/model/floor_real_config.py:439-441`;
  - `spawn(3)[2]` in `src/shk/model/residual_heteroskedasticity.py:340-342`.
  
  L'indipendenza dei flussi dipende dal fatto che i figli di una `SeedSequence` nuova siano indicizzati per posizione [D]. Una modifica a uno dei tre file cambia i CSV versionati, che i test confrontano a 1e-12 [V].
- **Costanti cablate legate allo split**:
  - 19 stagioni di validazione in `evaluate_floor_real_config` (`src/shk/model/floor_real_config.py:383` e seguenti; `spawn(19)` e controllo `!= 19`) [V];
  - `n: int = 19` di default in `binomial_exceedance_p_value` (`src/shk/model/residual_heteroskedasticity.py:511`) [V];
  - 380 partite per stagione in `src/shk/model/monitoring.py:76` e in `src/shk/model/residual_heteroskedasticity.py:49` [V];
  - il fit `("2000-01", "2010-11", "2020-21")` come default di `spawn_c6_4_generators` [V].
  
  Una modifica a `config/split.toml` non si propaga [D].
- **CSV versionati confrontati a 1e-12**:
  - `pyproject.toml` non vincola le versioni [V], e la CI installa con `pip` ignorando `uv.lock` [V];
  - un aggiornamento di numpy, scipy, pandas o river può cambiare i risultati [D].
  - `scipy.optimize.isotonic_regression` (`src/shk/model/recalibration.py`) esiste solo nelle versioni recenti di scipy [D], e nessun vincolo minimo è dichiarato [V].
- **Copertura della CI** (`.github/workflows/test.yml`):
  - gira solo su push a `main` e sulle pull request [V], quindi i push su `C6` senza PR non la attivano [V];
  - non scarica i dati grezzi, quindi tutti i test su dati reali sono saltati [D, per costruzione];
  - non esegue mai i test `slow` [V, `addopts`].
  
  I file e i comandi referenziati dal workflow esistono (`pyproject.toml`, extra `dev`) [V].
- **Ricalcolo pesante non marcato `slow`**: `tests/test_us_c6_3_real_acceptance.py:322` rifà il Monte Carlo completo con 1000 repliche × 19 stagioni × 3 configurazioni senza marker `slow` [V]. Gira in ogni `pytest` locale con i dati presenti [D].
- **Test noto rosso**: `test_acceptance_calibrated_phi_zero_within_mc_interval` (`tests/test_us_c2_acceptance.py`, slow) fallisce per un risultato noto [D, `.agent/SCHEDA.md:374`, non rieseguito].
- **Lettura del test set**:
  - `scripts/us_c3_1_data_coverage.py:29` chiama `load_all_seasons()` senza filtro, e quindi legge anche `2023-24` [V];
  - lo stesso vale per `tests/test_data_loading.py:312` [V];
  - `tests/test_split.py:437-454` ammette esplicitamente lo script come eccezione [V].
- **Moduli molto lunghi**: `src/shk/model/monitoring.py` (1351 righe) e `src/shk/kelly/floor.py` (1207 righe) [V].
- **Script C1 e C2 dipendenti dalla directory di lavoro** (cfr. §7): lanciati da un'altra directory scrivono altrove [D].
- **Script C6.3 senza backend `Agg`** (cfr. §7): possono fallire in ambienti senza display [D].
- **`assert` nel codice di libreria**: vengono disattivati con `python -O` [D: comportamento standard di Python].
- **Funzioni pubbliche mai nominate nei test**: elenco in §8.

### 10. Limiti di questa mappa

- **Moduli letti solo per docstring, firme, costanti e import**: tutti quelli esclusi in §4. Per questi le affermazioni sul comportamento interno sono assenti o `[D]`.
- **Non letti affatto**:
  - il contenuto dei CSV in `results/` e dei PNG;
  - gran parte dei file di test, salvo le righe citate;
  - i report `.agent/report/T*.md`;
  - `.agent/BACKLOG.md`.
  
  `.agent/SCHEDA.md` è stato letto solo nelle ultime 30 righe e in alcune righe trovate con la ricerca.
- **Non eseguito niente**: quindi non so se la suite oggi passa, quanto dura, né se i CSV versionati coincidono col codice attuale. Servirebbe eseguire `pytest` e, per i test su dati reali e `slow`, `pytest -m slow`.
- **Remote non interrogato**: niente `fetch`, quindi "allineato a origin/C6" riflette solo i ref locali.
- **Sezioni in prevalenza `[D]`**: nessuna nel complesso. Le parti `[D]` si concentrano in §2 (comandi non documentati) e in §9 (conseguenze delle fragilità).

Domande che farei:
1. Da quale fonte e con quale procedura si ottengono i CSV di `data/raw/E0/`? Esiste una verifica d'integrità (checksum) dei file?
2. Lo strumento di riferimento per l'ambiente è uv o pip? Quale comando usa il programmatore per lanciare gli script?
3. I CSV in `results/` sono stati rigenerati tutti con l'ultimo codice di `C6`? Si rigenerano a ogni modifica o solo a chiusura della story?
4. La CI dovrebbe girare anche sul branch `C6`, o solo sulle PR verso `main`?
5. I test lenti (`-m slow`) e quelli su dati reali vengono lanciati prima di ogni merge, e da chi?
6. `test_acceptance_calibrated_phi_zero_within_mc_interval` è ancora rosso, ed è accettato che lo resti?
7. Il motore di `src/shk/kelly/backtest.py` resta in uso dopo C6, o è destinato a essere sostituito dall'ambiente?
8. La configurazione dello split (19 stagioni di validazione, 380 partite) è considerata definitiva, visto che compare cablata nel codice?

### 11. Comandi eseguiti

Tutti tramite lo strumento Bash (Git Bash), in sola lettura, con `cd /c/Users/malse/Documents/GitHub/structural_hybrid_kelly` in testa a ciascuno. Le scritture sono state una sola: questo file, tramite lo strumento di scrittura file.

1. `pwd && git status && git branch -vv && git log --oneline -5 && git remote -v`
2. `git ls-files | head -300 && ls -la && ls -la .agent`
3. `cat .agent/PROTOCOLLO.md pyproject.toml .github/workflows/test.yml .gitignore config/split.toml`, poi `ls -la data data/raw` e `wc -l src/shk/*.py src/shk/*/*.py scripts/*.py tests/*.py`
4. `head -5 .agent/MAPPA.md`, `tail -30 .agent/SCHEDA.md`, `ls data/raw/E0 | head -50`, `ls data/raw/E0 | wc -l`, `ls .pytest_cache .venv` e `cat .venv/pyvenv.cfg`
5. `cat` dei sei `__init__.py`, di `src/shk/data/loading.py` e di `src/shk/data/split.py`
6. Ciclo `for` su `src/shk/*/*.py`: `head -3` più `grep -nE` di `def`, `class`, costanti e import `shk`
7. `grep -nE` delle costanti di modulo e `grep -nA8` degli import interni multilinea in `src/shk/*/*.py`
8. `sed -n` di `src/shk/kelly/agents.py` (righe 1-130 e 200-603, filtrate con `grep -v` delle righe vuote)
9. `sed -n` di sezioni di `src/shk/kelly/environment.py`
10. `sed -n` di `src/shk/model/paired_backtest.py`, filtrato con `grep`
11. `cat scripts/us_c6_2_paired_backtest.py` e `grep -nE` di import, IO, seed e `__main__` in `scripts/*.py`
12. `grep -n 'matplotlib.use' scripts/*.py` e `sed -n` di sezioni di `src/shk/model/elo_fit.py`
13. `sed -n` di `src/shk/model/residuals.py` e di `src/shk/model/scoring.py` (righe 218-335)
14. `sed -n` di `src/shk/model/monitoring.py` (righe 1-14 e 717-880)
15. `sed -n 383,521p src/shk/model/floor_real_config.py`, più le prime righe
16. `sed -n` di `src/shk/model/floor_real_config.py` (righe 138-204) e di sezioni di `src/shk/kelly/floor.py`
17. `sed -n` di `src/shk/model/residual_heteroskedasticity.py` e di `src/shk/stats/drift.py`, più `grep -n 'SeedSequence|default_rng|spawn('` in `src/shk/*/*.py`
18. Conteggio degli import esterni (`grep | awk | sort | uniq -c`) e `sed -n` di `src/shk/data/walkforward.py`
19. `sed -n` di `src/shk/model/elo_predictor.py` (righe 212-240 e 378-489)
20. `grep -nE` di marker, skip e uso dei dati reali in `tests/*.py`
21. Ciclo `for` sui `tests/test_us_c*.py` con conteggi `grep -c`, e `grep -nE` dei percorsi `results/` nei test C5 e C6
22. `grep -nE` di `evaluate_`, seed e `m_replicas` nei test di accettazione
23. `sed -n` di `tests/test_us_c6_2_acceptance.py` e di `tests/test_us_c6_3_real_acceptance.py`
24. `grep` di `print(`, logging, variabili d'ambiente, TODO/FIXME, `assert` in `src/` e `os.path` negli script. Il `grep -rn` su `tests` ha toccato anche file `.pyc` in `tests/__pycache__/` (solo lettura).
25. `grep` della lingua dei nomi dei test e dei motivi di skip, `grep` di `requires-python` e `ls tests/__pycache__ | sed | sort | uniq -c`
26. Ciclo `for` sulle funzioni pubbliche di `src/shk/*/*.py` con `grep -lw` su `tests/*.py`. È terminato con exit code 1: lo ha restituito l'ultimo test `[ … ] && echo` del ciclo, non un errore. L'output era completo.
27. `grep -cE` delle tolleranze, `grep -nE` delle costanti nelle asserzioni e conteggio di `default_rng(<intero>)` in `tests/*.py`
28. `grep -nE` di `rosso`, `xfail` e `fallisc` in `.agent/SCHEDA.md` e in `tests/*.py`, `sed -n 280,300p tests/test_heteroskedasticity.py` e `grep -nE '6234' tests/*.py`
29. `grep` e `sed -n` per confrontare i parametri di script e test di C6.3 e C6.4 (`scripts/us_c6_3_floor_synthetic.py`, `tests/test_us_c6_3_acceptance.py`, `src/shk/kelly/floor.py:689-700`, `scripts/us_c6_4_heteroskedasticity.py`, `tests/test_us_c6_4_acceptance.py`)
30. `grep -nA1 '__main__' scripts/*.py`, conteggio di `def test_`, `grep statsmodels tests/*.py` e `sed -n 1,30p src/shk/kelly/staking.py`

Nessun comando vietato è stato eseguito:
- nessuna esecuzione di Python, `pytest`, `uv` o degli script;
- nessun comando git che modifichi lo stato;
- nessun `fetch`.
