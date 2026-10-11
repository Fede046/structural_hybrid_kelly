# Scheda del progetto
Origine: mappa completa del 2026-10-11 a c427e33 (branch C6), report fino a R15@2026-10-11. Riferimenti: la numerazione R_n riparte da R1 a ogni mappa; un riferimento senza data appartiene alla serie 2026-10-11. Serie 2026-10-11: R1 = mappa, R2–R15 = risposte alla chat di scheda (in questa sessione la parte di Cline l'ha svolta il supervisore, in sola lettura). Serie precedenti: @2026-10-07 (R1 = mappa a 736f5cd, R2–R6 = risposte di Cline); @2026-09-29c (R1 = mappa a 27cf7a4); @2026-09-29b (R1 = mappa a 90a77a1, R2–R6 risposte, R7–R33 report di T20–T25); @2026-09-29 (R1 = mappa a 115e600, R2–R46 report di T14–T19); @2026-09-28 e @2026-09-27 più vecchie. I fatti su file non modificati fra 736f5cd e c427e33 conservano marker e riferimento originari [V l'elenco dei file toccati, R2]. I valori misurati in T26–T39 stanno nei report .agent/report/T26.md … T39.md; qui compaiono solo quelli riletti [D]

## Stato repo
Radice: C:\Users\malse\Documents\GitHub\structural_hybrid_kelly [V, R1]
Alla mappa: branch C6 a c427e33 "end c6", 2026-10-10 23:44:41 +0200; working tree pulito [V, R1 e R2]
C6 traccia origin/C6 ed è allineato secondo i ref locali; nessun git fetch eseguito, stato reale del remote non verificato [V, R1]
C6 = main + 4 commit: 833a4d8 "manca il backlog della C6" (2026-10-07), 6851ccf "T33-T34" (2026-10-09), 632d5a1 "d" (2026-10-09), c427e33 "end c6" (2026-10-10); main non ha commit assenti da C6 [V, R2 e R14]
main a 736f5cd "C5 (#20)", traccia origin/main [V, R1]
Remote origin: https://github.com/Fede046/structural_hybrid_kelly.git, fetch e push [V, R1]
Commit di story su main: 115e600 = S2/C2, 90a77a1 = S3/C3, 27cf7a4 = S4/C4 [V, R1@2026-09-29, R1@2026-09-29b, R1@2026-09-29c]; 736f5cd = S5/C5 [V, R1@2026-10-07]. S6/C6 non è in main [V, R14]. Il meccanismo è lo squash merge del PR [D]
File toccati fra 736f5cd e c427e33 [V, R2]:
- modificati: .agent/BACKLOG.md, .agent/MAPPA.md, .agent/SCHEDA.md, pyproject.toml (solo statsmodels nell'extra dev, R3), src/shk/kelly/metrics.py e tests/test_metrics.py (solo aggiunte, R3);
- aggiunti: .agent/report/T33.md … T39.md; src/shk/kelly/agents.py, environment.py, floor.py; src/shk/model/paired_backtest.py, floor_real_config.py, residual_heteroskedasticity.py; src/shk/stats/heteroskedasticity.py; script, CSV e PNG us_c6_2_paired_backtest, us_c6_3_floor_synthetic, us_c6_3_floor_real_config, us_c6_4_heteroskedasticity; tests/test_agents.py, test_environment.py, test_floor.py, test_hac_anova_lm.py, test_heteroskedasticity.py, test_us_c6_2_acceptance.py, test_us_c6_3_acceptance.py, test_us_c6_3_real_acceptance.py, test_us_c6_4_acceptance.py.
Nessun altro file è cambiato: moduli di C1–C5 tranne metrics.py, config/split.toml, uv.lock, .gitignore, CI e .agent/PROTOCOLLO.md sono quelli di 736f5cd [V, R2]
Branch [V, R1; contenuto di pre-c4 R1 e R3@2026-10-07]:
- locali: C6, main, pre-c4; ciascuno traccia il ramo omonimo di origin;
- pre-c4 parte da 90a77a1 con due commit assenti da main: 043b9a5 toglie .agent/ dall'indice, 5249f9b aggiunge .agent/ a .gitignore; nessuna delle due modifiche è in main né in C6.
File ignorati presenti: .pytest_cache/, .venv/, data/raw/E0/, tests/__pycache__/ con .pyc di pytest 7.4.4 e 9.1.1 [V, R1]; __pycache__ in scripts e src/shk [V, R1@2026-10-07]
Albero tracciato a c427e33 [V, R1]:
- src/shk/ con kelly/, stats/, data/, market/, model/;
- tests/ con 39 moduli, nessun conftest.py; scripts/ con 15 script;
- results/ con 15 CSV e .gitkeep; thesis/figures/ con 15 PNG e .gitkeep;
- config/ con split.toml e .gitkeep; data/raw/ con .gitkeep; .github/workflows/test.yml;
- .agent/ con PROTOCOLLO.md, BACKLOG.md, MAPPA.md, SCHEDA.md, report/T1.md … T39.md;
- alla radice pyproject.toml, uv.lock, .gitignore, LICENSE; nessun README.
data/raw/E0/ contiene 31 CSV, da 1993-94.csv a 2023-24.csv, non versionati (.gitignore esclude data/raw/* tranne .gitkeep) [V, R1]. Fonte football-data.co.uk, scaricati dal programmatore il 2026-09-29 nella finestra di KellyBench [V, R6 e R7@2026-09-29; fonte dalla decisione S3 in BACKLOG.md]
config/split.toml: chiavi frozen_on, test_unlocked, test_unlocked_on, training, validation, test; test_unlocked = false [V, R1]; non toccato da 736f5cd [V, R2]. Contenuto identico a quello di 2cea094 (2026-09-29 11:47:18) [V, R3–R6@2026-09-29b]; 2cea094 è ancora nella reflog locale come HEAD@{35} [V, R14]
Nessun .env [V, R1@2026-10-07]; nessuna variabile d'ambiente letta: nessun os.environ né getenv in src/, scripts/, tests/ [V, R1]

## Stack e comandi
Pacchetto structural-hybrid-kelly 0.1.0 (pyproject.toml e src/shk/__init__.py), importabile come shk da src/shk/ [V, R1]
requires-python >= 3.11; la CI usa Python 3.12 [V, R1]
Build hatchling, wheel con packages = ["src/shk"]; nessun [project.scripts] [V, R1]. Build con hatch build o python -m build [D]
Dipendenze runtime: numpy, scipy, matplotlib, pandas, river, senza vincoli di versione; extra dev: pytest, statsmodels, senza vincoli [V, R1 e R3]. statsmodels è entrato in T38 [V, R3]
uv.lock (non toccato da 736f5cd, R2): requires-dist del progetto con solo matplotlib, numpy, scipy, pytest; nessuna voce pandas, river o statsmodels [V, R3]. uv sync oggi non installerebbe pandas, river, statsmodels [D]
Gestione delle dipendenze, decisione del programmatore 2026-10-11: pyproject.toml è la fonte di verità; uv.lock lo rigenera a mano il programmatore; la CI resta con pip [decisione, chat di scheda 2026-10-11]
CI (.github/workflows/test.yml): trigger su push verso main e su pull_request; Python 3.12; python -m pip install --upgrade pip, pip install -e ".[dev]", pytest -v; nessuna cache, uv.lock non usato [V, R1]. Un push su C6 attiva la CI solo tramite una PR [V il trigger, R1]; se esista una PR di C6 e con che esito, non noto [D]
Esecuzioni note della CI [V, log forniti dal programmatore il 2026-09-28 e il 2026-09-29]:
- 2026-09-28: Linux, Python 3.12.14, pytest 9.1.1; prima di T13 falliva sul confronto dei float come stringhe;
- 2026-09-29, branch C4 dopo T24: 263 raccolti, 15 deselezionati, 237 passati, 9 saltati, 2 falliti, corretti in T25.
Esito della CI dopo T25 (PR di C5, 736f5cd, C6): non noto [D]
Venv .venv: Python 3.12.7 creato con python -m venv dall'interprete di Anaconda [V, R1]; numpy 2.5.2, scipy 1.18.1, pandas 3.0.6, matplotlib 3.11.1, river 0.26.1, pytest 9.1.1, shk editable [V, R1@2026-10-07]; statsmodels 0.15.0 installato in T38 [D, BACKLOG.md S6 dal report T38]
Interprete: Cline esegue ogni comando Python con .\.venv\Scripts\python.exe dalla radice (es. .\.venv\Scripts\python.exe -m pytest -v); il Python di default del suo terminale è Anaconda, senza shk [V, R6 e R7@2026-09-28; decisione del programmatore 2026-09-28]. In T39 Cline ha usato Anaconda contro la regola [D, BACKLOG.md S6]
Installazione: pip install -e ".[dev]" in CI [V, R1]; in locale con l'interprete del venv [D]
Test: pytest -v; pyproject.toml ha addopts = "-m 'not slow'" e registra il marker slow [V, R1]. Solo slow: pytest -m slow; tutti: pytest -o addopts="" [D]
Suite: 39 moduli, 407 definizioni def test_ di primo livello prima della parametrizzazione [V, R1]. Ultimo esito noto, dopo T39 nel venv: 452 passati, 16 deselezionati, 145.32 s [V che il report lo dice, R15: .agent/report/T39.md:99; non rieseguito]
Test slow: 14 funzioni in 5 file, 16 test [V, R11; conteggio ricalcolato dal supervisore]:
- 4 in test_us_c1_1_acceptance.py, 5 in test_us_c1_2_acceptance.py, 3 funzioni in test_us_c2_acceptance.py (5 test, l'ultima parametrizzata su tre φ), 1 in test_us_c4_1_acceptance.py (riga 239), 1 in test_us_c6_3_acceptance.py (riga 194, ricalcolo completo di T36);
- ultimi esiti: dei 14 di C1 e C2, 13 verdi e 1 rosso per il risultato noto, circa 117 s [V, R14@2026-09-28]; quello di C4 verde in 119.09 s [V, R23@2026-09-29b]; quello di C6.3 verde in 156.71 s [V che il report lo dice, R15: .agent/report/T36.md:238].
Esperimenti: python scripts/<nome>.py dalla radice, funzione chiamata dal blocco __main__ [V, R1]:
- 13 script chiamano run_experiment(); us_c6_3_floor_real_config.py e us_c6_4_heteroskedasticity.py chiamano main() [V, R1];
- C1.1, C1.2 e C2 scrivono in results/ e thesis/figures/ relativi alla directory corrente: vanno lanciati dalla radice [V i percorsi, R1; D la regola];
- gli altri dodici calcolano i percorsi da Path(__file__).resolve().parents[1] [V, R1];
- C3.2, C4.x, C5.x, C6.2, C6.3 reale e C6.4 leggono i dati con load_by_role e richiedono data/raw/E0/; C3.1 usa load_all_seasons su tutta la directory; C1.x, C2 e C6.3 sintetico non leggono dati [V, R1].
Durate e SHA256 noti dei CSV:
- C1.2: circa 70 s; CSV identici fra due esecuzioni [D, era V R16@2026-09-27];
- C2: circa 90 s; SHA256 6711B906A5D0170124BE816BAB04C336854CF7FF62DF135FDC18F22B84AB3831 sul CSV di allora [V, R14@2026-09-28], non ricalcolato sul versionato [D];
- C3.1: F9EEA7264F5457A1728EA609CD6660BCEE9779D450099D446CC30A919D73E15C [V, R14@2026-09-29];
- C3.2: 5e9743252db28de1c2c6e28b5584725f4c2f78f47d4d830e318922d88e77ce92 [V, R43 e R44@2026-09-29];
- C4.1: circa 49 s; 92716bc7e6aa6a7b798370a09d1b31b33b0c0a49311bf35cd810f7975489f282 [V, R23@2026-09-29b];
- C4.2: e076f16f6a39606a4fcba04be5679a1fa0d7ce9f1c44893df47df79e39dee3a9 [V, R26@2026-09-29b];
- C4.3: cc0d3577168ea47cc7f89b9d44f59c29be67062a2ad41634285d11e417ac2073 [V, R29@2026-09-29b];
- C5.1, C5.2, C5.3: nei report T28–T32 [D];
- C6.2 15.9 s; C6.3 sintetico 167 s; C6.3 reale 25.4 s; C6.4 28.3 s, SHA256 c98a6c96c7e561b8caafdddeabc56c9493414c6ba56cd4680bfe37485397b7fd [D, BACKLOG.md S6 dai report T35–T39].
File di configurazione: pyproject.toml e config/split.toml [V, R1]
Uso come libreria: from shk.kelly import kelly_fraction, log_growth_rate; il resto si importa dal modulo (es. shk.kelly.core.expected_final_wealth) [V, R1@2026-10-07]

## Moduli e responsabilità
src/shk/ ha 32 moduli applicativi (10 in kelly, 6 in stats, 4 in data, 2 in market, 10 in model) più 6 __init__.py [V, R1; conteggio ricalcolato dal supervisore]
__init__.py: src/shk espone __version__; kelly re-esporta kelly_fraction e log_growth_rate con __all__; stats, data, market e model hanno solo una docstring [V, R1]
Dipendenze fra sottopacchetti [V, R11 e R1]:
- kelly/ non importa da model/, data/, market/ né stats/; stats/, data/ e market/ non importano da model/;
- model/ importa da kelly/, stats/, data/ e market/;
- market/divergence.py importa nomi di data/split.py senza usarli [V, R1@2026-10-07].
src/shk/kelly/core.py — kelly_fraction(p, b), log_growth_rate(f, p, b), expected_final_wealth(f, p, b, T, b0=1.0) (righe 97-144); nessun import interno [V, R1@2026-10-07]. kelly_fraction = (b·p − q)/b, 0.0 se ≤ 0, solo scalari [D, era V R7@2026-09-27]
src/shk/kelly/simulate.py — nessun import interno [V, R1@2026-10-07]:
- draw_outcomes(p, T, M, rng) → bool (M, T), True = vincita;
- simulate_growth(outcomes, fractions, b) → log-ricchezza float64 (M, T+1) con colonna 0 nulla; frazioni broadcastabili da (), (T,), (1, T), (M, 1), (M, T); ValueError per frazioni fuori da [0, 1) [V, R1@2026-09-28 per il broadcasting];
- log_wealth_paths(outcomes, f, b) delega a simulate_growth.
src/shk/kelly/estimation.py — relative_perturbation(p, delta); noisy_estimates(p, sigma_p, T, M, rng), con clip in [0, 1] [V, R1@2026-10-07]
src/shk/kelly/scenarios.py — importa simulate.py e staking.py [V, R1]:
- Scenario (dataclass frozen: name, p, b, T, M); BASE_SCENARIO (0.60, 1.0, 1000, 10000); SUBTLE_SCENARIO (0.52, 1.0, 380, 10000); SEED = 20260927, senza Final [V, R1];
- spawn_generators(seed=SEED): SeedSequence(seed).spawn(2), esiti poi rumore [V, R1];
- draw_scenario_outcomes(scenario, rng); simulate_scenario(scenario, outcomes, p_hat, lam=1.0) [V, R1@2026-10-07].
src/shk/kelly/metrics.py — nessun import interno; modificato in T35 con sole aggiunte, quindi le funzioni precedenti sono invariate [V, R3]:
- su traiettorie di log-ricchezza (M, T+1): final_log_wealth, median_growth_rate, median_final_wealth, mean_final_wealth, fraction_below_start [V, R1@2026-10-07];
- max_drawdown → (M,) in [0, 1); richiede almeno 2 colonne (righe 141-142) [V, R4];
- su ricchezza in livelli (M, D+1), con _validate_wealth_matrix (TypeError per tipo; ValueError se non 2D, meno di 2 colonne, non finita, negativa o colonna 0 ≤ 0) [V, R4]:
  - wealth_max_drawdown(wealth) = max_t (1 − W_t / max_{s≤t} W_s), in [0, 1];
  - wealth_recovery_time(wealth) → (times int64, recovered bool): t* = primo indice del drawdown massimo; tempo = primo t > t* con W_t ≥ picco, meno t*; 0 e True se il drawdown è nullo; −1 e False se il picco non torna; ciclo Python sulle repliche.
src/shk/kelly/staking.py — non toccato in C6 [V, R2]; nessun import interno [V, R1@2026-10-07]:
- kelly_staking(p_hat, b, lam=1.0) = lam·max(0, (b·p̂ − (1 − p̂))/b), senza limite superiore; float per input 0-d, ndarray altrimenti; b solo scalare [V, R1@2026-10-07 e R1];
- StakingMoments (mean_c, mean_c2, var_c, fraction_zero), staking_moments(f_hat, f_star), plugin_staking(p_hat, b, sigma_p) [V, R1@2026-10-07]. plugin = λ_t·kelly_staking con λ_t = 1/(1 + (o·σ_p/EV̂)²), 0 dove EV̂ ≤ 0 [D, era V R8@2026-09-27];
- costanti (righe 224-229): BASE_LAMBDA = 0.25, KAPPA_GRID = (0.0, 0.25, 0.5, 0.75, 1.0), KAPPA_ADWIN = 1.0, KAPPA_PAGE_HINKLEY = 1.0, OUTCOME_LABELS = ("H", "D", "A") [V, R1];
- BaselineDBets (outcomes, odds, fractions) [V, R1@2026-10-07];
- compute_adaptive_lambda(match_dates, alarm_dates, kappa, base_lambda=BASE_LAMBDA): λ_j = base·κ^(allarmi con data < D_j); un kappa int dà TypeError (righe 297-298) [V, R1@2026-10-07];
- select_baseline_d_bets(probs, odds, lambdas): esito con p̂·o − 1 massimo (np.argmax, parità nell'ordine H, D, A), frazione kelly_staking solo se il massimo è > 0; ciclo Python per partita [V, R1@2026-10-07].
src/shk/kelly/backtest.py — motore su quote reali di C5.3; nessun import interno né funzione privata [V, R1 e R4@2026-10-07]:
- BacktestResult(dates, log_wealth); backtest_log_wealth(dates, fractions, odds, won), con dtype obbligati datetime64, float64, float64, bool [V, R1@2026-10-07];
- ValueError per frazioni fuori da [0, 1), somma delle frazioni di una data ≥ 1, quote ≤ 1 o non finite, date non ordinate [V, R1@2026-10-07];
- algoritmo: date distinte in ordine di prima comparsa; L_0 = 0; per data L += ln(1 + Σ f_i·r_i), r_i = o_i − 1 se vinta, −1 se persa (righe 125-138); input vuoto → log_wealth [0.0]; non conosce la ricchezza corrente [V, R4@2026-10-07].
src/shk/kelly/agents.py — agenti come classi; importa solo staking.py [V, R1]:
- NO_BET = −1; AGENT_A_LAMBDA = 1.0; AGENT_B_LAMBDAS = (0.25, 0.10); esiti 0 = H, 1 = D, 2 = A [V, R1];
- DateView(date, probs, odds) e AgentDecision(outcomes int64 con −1, fractions in [0, 1) nulle dove NO_BET, fallback_match, fallback_outcome): dataclass frozen, eq=False, con array copiati in viste non scrivibili di copie non scrivibili [V, R1];
- estimated_expected_values(probs, odds) = p·o − 1, con probs e odds (n, 3) finiti [V, R1];
- Agent (ABC) [V, R1]:
  - name in sola lettura, stringa non vuota;
  - decide(view): per partita l'esito con EV stimato massimo (np.argmax, parità H, D, A), selezionato solo se EV > 0; stake_fractions(view, p_hat, b) sui k selezionati con p_hat e b = o − 1 non scrivibili, anche con k = 0; uscita validata (ndarray floating (k,), finita, in [0, 1)); ripiego = argmax dell'EV sulla matrice (n, 3) appiattita, anche con EV ≤ 0;
  - __init_subclass__ solleva TypeError se una sottoclasse, anche tramite mixin, ridefinisce membri di Agent diversi da __init__ e stake_fractions;
- FractionalKellyAgent(name, lam): lam float o np.floating in (0, 1], TypeError per bool e int; frazioni con kelly_staking elemento per elemento; con lam = 1 e p̂ = 1 la frazione vale 1 e decide solleva ValueError [V, R1];
- MinimumStakeAgent(name): frazioni tutte nulle; la puntata viene dal ripiego dell'ambiente [V, R1];
- helper privati _is_real_numeric_dtype (riga 38), _read_only_view (56), _validate_outcome_matrices (82), _validate_stake_output (291) [V, R1].
src/shk/kelly/environment.py — ambiente passo-passo multi-agente; importa da agents.py NO_BET, Agent, AgentDecision, DateView, estimated_expected_values [V, R1]:
- duplica _is_real_numeric_dtype (riga 28) e _read_only_view (46) di agents.py [V, R1];
- floor_thresholds(min_stake, f_star, lam) → (B1, B2, B3) = (F/(λ·f*), F/(2·f*), F); solo float, f* in (0, 1), λ in (0, 1] [V, R1];
- place_date_stakes(wealth, view, decision, min_stake) → PlacedBets(stakes (M, n), outcomes (n,), n_forced, n_floored, n_dropped), solo per repliche attive [V, R6]:
  - nessuna puntata volontaria: con F > 0 una puntata F sul ripiego (n_forced = 1), con F = 0 nessuna puntata;
  - puntate volontarie: ordine per EV stimato decrescente, parità per indice di partita crescente; candidata = max(f·W, F) se F > 0, f·W se F = 0; si tiene il prefisso con somma cumulata ≤ W, le altre si contano in n_dropped; n_floored = puntate tenute con f·W < F; nessuna puntata forzata;
  - ValueError se una replica ha W < F (F > 0) o W ≤ 0 (F = 0);
- run_paired_backtest(agents, dates, probs, odds, outcomes, min_stake, record_stakes=False) → tuple[AgentRun] nell'ordine degli agenti [V, R1]:
  - validazioni: agenti Agent con nomi distinti; date datetime64 non decrescenti senza NaT; probs (N, 3) in [0, 1] con righe a somma 1 entro 1e-9; odds > 1; outcomes intero (M, N) in {0, 1, 2}; min_stake float finito ≥ 0;
  - date distinte in ordine di prima comparsa; una sola DateView per data, la stessa per tutti gli agenti; decide si chiama per ogni agente a ogni data, anche con tutte le repliche rovinate;
  - rovina, assorbente, all'inizio della data: W < F o W = 0 con F > 0, W ≤ 0 con F = 0; ruin_date_index = indice della data;
  - regolamento: W += Σ stake·(o − 1) per le vinte, − stake per le perse; N = 0 → wealth (M, 1) di uno;
- AgentRun: name, dates (D,), wealth (M, D+1) con colonna 0 = 1.0, ruined, ruin_date_index (−1 se mai), n_bets, n_forced, n_floored, n_dropped, staked e desired (M, D) solo con record_stakes; viste non scrivibili [V, R1].
src/shk/kelly/floor.py — esperimenti sintetici sul floor (C6.3); importa agents.py (FractionalKellyAgent), environment.py, staking.py [V, R1]:
- SEED_C6 = 20261009 (riga 21); spawn_t36_generators(seed): SeedSequence(seed).spawn(2)[0].spawn(3) → A, B, C; C.spawn(3), un figlio per configurazione [V, R1];
- Esperimento A: quota 2.5, EV vero −0.02, edge stimato 0.03, λ = 0.25, M = 10 000, orizzonti (150, 400, 1000, 3000) da 1000F e (150, 400, 1000) da 50F; valori della nota in NOTE_EXP_A_* (M = 80 000; 50F: 0.00149, 0.07616, 0.35760) [V, R8];
- Esperimento B: M = 10 000, T = 1000, orizzonti (150, 1000), 15 rapporti B0/F (10^1 … 10^7 a passo 0.5, più 220 e 22 000) [V, R8];
- Esperimento C: M = 1 000, quota 2.5, EXP_C_CONFIGS (ExpCConfig: ev_true, lam, edge_est, ratio, note_mu, note_bound, note_acceleration): a (−0.02, 0.25, 0.03, 50, −0.000119, 32 986, 23.0), b (−0.04, 1.00, 0.10, 220, −0.005905, 913, 1.3), c (−0.05, 1.00, 0.03, 200, −0.001293, 4 097, 2.2) [V, R8];
- FLOOR_SYNTHETIC_CSV_COLUMNS (32); DEFAULT_CHUNK_SIZE = 2 000 [V, R8];
- funzioni: classify_floor_regime, expected_ruin_time_bound, two_sample_mc_tolerance, synthetic_calendar, synthetic_match_data, draw_synthetic_outcomes, compute_ruin_rates_at_horizons, compute_ruin_times, run_paired_chunked (run_paired_backtest a blocchi di repliche, righe 578 e 603), run_experiment_a/b/c, evaluate_all_synthetic_experiments(seed=SEED_C6, chunk_size) → (record, risultati A, B, C) [V, R1 e R8].
src/shk/stats/anova.py — OneWayAnovaResult (ss_between, ss_within, ss_total, df_between, df_within, ms_between, ms_within, f_statistic, p_value); oneway_anova(groups), con p-value da scipy.stats.f.sf [V, R4@2026-09-28; firme R1]
oneway_anova_vectorized(values, labels) → float per values 1D, altrimenti ndarray di forma values.shape[:-1]; values e labels np.ndarray (TypeError altrimenti); etichette int 0..k−1, tutte presenti [V, R4@2026-09-28; firme R1]
src/shk/stats/timeseries.py — generate_ar1_series(phi, n, m, rng) → float64 (m, n) [V, R7@2026-09-28]:
- estrazioni: x_0 ~ N(0, 1/(1 − φ²)) con size=m, poi innovazioni N(0, 1) in blocco;
- ValueError per φ non finito o |φ| ≥ 1, n < 2, m < 1; TypeError per n o m bool o non interi, e per rng non Generator.
src/shk/stats/calibration.py — nessun import interno [V, R1]:
- moving_block_indices(n, block_length, n_boot, rng) → int64 (n_boot, n), inizi da rng.integers(0, n − L + 1, size=(n_boot, ⌈n/L⌉)) [V, R12@2026-09-28];
- compute_order_statistic_index(b, alpha) → ⌈(1 − α)(b + 1)⌉ con tolleranza 1e-9; ValueError se supera b [V, R1@2026-10-07 e R12@2026-09-28];
- calibrate_threshold(data, statistic, block_length, n_boot, alpha, rng, vectorized=False) → float: indici estratti una volta; statistica float64 (n_boot,) finita; soglia = elemento k − 1 delle statistiche ordinate [V, R12@2026-09-28].
calibration.py — la docstring si contraddice: lo schema (a) indica come dato dell'ANOVA F "la serie della risposta" (righe 18-20); il principio (c) dice che imporre H₀ spetta al chiamante (righe 35-39). Lo schema l'ha dettato il supervisore ed è da correggere [V, R1@2026-10-07 e R12@2026-09-28]
src/shk/stats/false_rejection.py — importa anova.py, calibration.py, timeseries.py [V, R1]:
- PHI_VALUES = (0.0, 0.3, 0.5, 0.7), N_OBS = 380, N_SERIES = 1000, ALPHA = 0.05, SEED_C2 = 20260928, BLOCK_LENGTHS = (7, 20, 40), N_BOOT = 999, senza Final (righe 13-34) [V, R1];
- DESIGN_CONTIGUOUS_2, DESIGN_CONTIGUOUS_38, DESIGN_RANDOM_2 e DESIGNS; CSV_COLUMNS (10); METHOD_NOMINAL, METHOD_BLOCK_BOOTSTRAP [V, R13 e R14@2026-09-28];
- PhiStreams (series_rng, perm_rng, boot_seed); RejectionResult (dataclass frozen con to_row()) [V, R1@2026-10-07];
- critical_value_nominal, monte_carlo_interval_99, make_design_labels, spawn_c2_generators [V, R1];
- compute_nominal_rejection_rates → 12 risultati, DESIGNS × PHI_VALUES [V, R13@2026-09-28];
- compute_calibrated_rejection_rates → 12 per contiguous_2, BLOCK_LENGTHS × PHI_VALUES; calibrate_threshold sulla serie grezza, H₀ non imposta [V, R13 e R14@2026-09-28].
FLOAT_CSV_COLUMNS non sta in false_rejection.py ma in tests/test_us_c2_acceptance.py:33 [V, R1@2026-10-07]
src/shk/stats/drift.py — ADWIN e PageHinkley da river.drift, e Z per matchday [V, R1]:
- importa calibration.py (calibrate_threshold, moving_block_indices), false_rejection.py (ALPHA, BLOCK_LENGTHS, N_BOOT) e pandas [V, R1];
- costanti: TARGET_ALARMS_PER_SEASON = 1.9, MATCHDAY_SIZE = 10, SEED_C5 = 20260929, N_VERIFICATION_RESAMPLES = 1000 [V, R1];
- griglie: ADWIN_GRID_DELTA (9 valori); PAGE_HINKLEY_GRID_DELTA × PAGE_HINKLEY_GRID_THRESHOLD (3 × 6); default di river 0.26.1 in ADWIN_DEFAULT_* e PAGE_HINKLEY_DEFAULT_* [V, R1@2026-10-07];
- valori congelati: ADWIN_DELTA = 0.002, PAGE_HINKLEY_DELTA = 0.05, PAGE_HINKLEY_THRESHOLD = 5.0 [V, R1];
- detector_params(detector); run_drift_detector(series, detector, params=None), con un'istanza nuova per chiamata e i default di river se params=None [V, R1@2026-10-07];
- select_best_candidate, calibrate_adwin, calibrate_page_hinkley, calibrate_drift_detectors → pd.DataFrame per la griglia [V, R1@2026-10-07];
- compute_matchday_z_scores, compute_resampled_matchday_abs_z, calibrate_matchday_z_threshold, verify_matchday_z_thresholds (converte int(n_resamples) alla riga 665 prima del controllo di tipo alla riga 666) [V, R1@2026-10-07];
- spawn_c5_generators(seed=SEED_C5, n_fits=3): SeedSequence(seed).spawn(n_fits) → per fit spawn(len(BLOCK_LENGTHS)) → per L spawn(2) (calibrazione, verifica) [V, R1].
src/shk/stats/heteroskedasticity.py — Breusch-Pagan (Koenker) e White a mano; nessun import interno [V, R1 e R10]:
- HeteroskedasticityTestResult e HeteroskedasticityBatchResult (NamedTuple) [V, R1]; campi non riletti [D];
- nominal_threshold(df, alpha) = chi2.ppf(1 − α, df); ols_residuals(y, x): residui di y ~ 1 + x via QR, costante aggiunta dalla funzione [V, R10];
- breusch_pagan_lm(resid, z): resid² su [1, z], variante Koenker; white_lm(resid, x): resid² su [1, x, quadrati e prodotti incrociati] [V, R10];
- bp_statistic(y, x, z=None) (z = x se None) e white_statistic(y, x): OLS poi test [V, R10];
- bp_statistic_batch(y, x, z=None) e white_statistic_batch(y, x): y (B, n), x (B, n, k) o (n, k) [V, R10];
- regressori standardizzati internamente, mai l'inversa di X'X [D, decisione S6 in BACKLOG.md].
src/shk/data/loading.py — DEFAULT_DATA_DIR = radice/data/raw/E0; load_all_seasons(data_dir=DEFAULT_DATA_DIR, seasons=None) [V, R1; R10 e R26@2026-09-29]:
- restituisce le colonne dei CSV più season (YYYY-YY, dal nome file); Date in datetime64[us] senza nulli; ordinamento stabile per season e Date;
- decodifica per file: BOM → utf-8-sig; UTF-8 valido → utf-8; altrimenti cp1252; Date con %d/%m/%y o %d/%m/%Y [V, R1].
loading.py — validazioni [V, R10 e R26@2026-09-29]:
- TypeError per data_dir non str né Path, e per seasons str o con elementi non str;
- FileNotFoundError per directory inesistente;
- ValueError per directory senza CSV, nome file non conforme, date miste, non conformi o fuori dalla finestra 1° luglio – 31 agosto, campi in eccesso non vuoti, colonne senza nome non vuote, seasons vuota o con stagione senza file.
src/shk/data/coverage.py — [V, R14–R17 e R45@2026-09-29; righe R1@2026-10-07]:
- NON_ODDS_COLUMNS; ColumnClassification (group_type, group_name, source, market, timing, kind);
- classify_column(name): group_type ∈ {1x2_prematch, 1x2_closing, aggregators, other_markets}, timing ∈ {prematch, closing}, kind ∈ {odds, line, count}; ValueError per colonne non di quota o sconosciute (riga 292);
- GROUP_TYPE_ORDER; COVERAGE_CSV_COLUMNS (12); compute_coverage(df) → una riga per stagione × gruppo presente.
src/shk/data/split.py — delega a loading.py [V, R1]:
- DEFAULT_SPLIT_CONFIG_PATH; TestSetLockedError(RuntimeError) con __test__ = False; SplitConfig (frozen_on, test_unlocked, test_unlocked_on, training, validation, test) [V, R1];
- read_split_config(config_path): chiavi esatte, ruoli disgiunti, test non vuoto, training e validation < min(test) [V, R1];
- load_by_role(role, config_path, data_dir), ruoli training, validation, test, history [V, R1]:
  - con il test bloccato, "test" dà TestSetLockedError prima di toccare i dati;
  - poi verifica, solo per nome, che ogni stagione configurata abbia un file, test compreso;
  - history = stagioni presenti, anteriori al primo anno di test, né di training né di validation.
src/shk/data/walkforward.py — importa coverage.py [V, R1]:
- PREMATCH_IDENTIFIERS; LeakageError(RuntimeError) [V, R1];
- get_prematch_whitelist(columns), per inclusione e con lru_cache: Div, Date, Time, HomeTeam, AwayTeam, season e le colonne con kind = odds e timing = prematch [V, R1];
- walkforward_split(df, seasons_to_predict), generatore: coppie con storia a Date strettamente anteriore e partita ridotta alla whitelist [V, R1];
- check_leakage(history, match, whitelist=None) → lista di violazioni; assert_no_leakage solleva LeakageError [V, R45@2026-09-29].
src/shk/market/devig.py — nessun import interno [V, R1]:
- implied_probabilities(odds) → (N, n); overround(odds) → (N,) = S − 1; devig_proportional;
- devig_additive: riga di NaN se un q ≤ 0;
- devig_power → (q, k): Newton vettorizzato da k = 1 con salvaguardia max(k − step, k/2), MAX_NEWTON_ITERATIONS = 50; RuntimeError se un mercato ha |Σq − 1| > 1e-12 (righe 189-193) [V, R1@2026-10-07].
devig.py — validazione: ndarray (N, n) con n ≥ 2 e dtype reale, quote finite > 1, conversione in float64 [V, R30–R36@2026-09-29]
src/shk/market/divergence.py — importa devig.py [V, R1]:
- ODDS_BINS (1, 1.5, 2, 3, 5, 10, inf), ODDS_BIN_LABELS, REFERENCE_EDGE = 0.02, B365_ODDS_COLUMNS, DIVERGENCE_CSV_COLUMNS (19) [V, R1];
- assign_odds_bin, con fasce chiuse a sinistra [V, R41 e R44@2026-09-29];
- compute_divergence_table: partite usate = B365 valida e additivo applicabile; p99 con np.percentile lineare [V, R41 e R44@2026-09-29];
- import non usati: Path (riga 4); DEFAULT_SPLIT_CONFIG_PATH, SplitConfig, read_split_config (riga 10) [V, R1@2026-10-07].
src/shk/model/elo.py — funzioni pure, senza RNG né accesso ai dati [V, R1]:
- elo_delta(r_home, r_away, h=0.0), solo scalari;
- expected_score(delta, s=400.0) = 1/(1 + 10^(−delta/s));
- elo_update(r_home, r_away, outcome, k, h=0.0, s=400.0): S = 1, 0.5, 0 per H, D, A, a somma zero;
- davidson_probabilities(delta, nu, s=400.0) e constant_draw_probabilities(delta, c, s=400.0) → (p_home, p_draw, p_away).
elo.py — tipi e validazioni:
- uno scalare reale dà float; un ndarray, anche 0-d, dà ndarray float64 [V, R16 e R17@2026-09-29b];
- TypeError per bool, non numerici, liste, stringhe, ndarray bool o complessi [V, R11@2026-09-29b];
- ValueError per valori non finiti, ν ≤ 0, c fuori da (0, 1), s ≤ 0, k < 0, outcome fuori da H, D, A [V, R11@2026-09-29b];
- assert nel codice alle righe 163, 168, 230, 281, 290, 345, 347, 354, 356 [V, R1]; import Any non usato [V, R1@2026-10-07].
src/shk/model/elo_predictor.py — importa walkforward.py ed elo.py [V, R1]:
- SEASON_REGEX (riga 13); compute_season_standings(matches), con almeno team, points, goal_diff, goals_for [V, R1 e R19@2026-09-29b];
- predict_elo_walkforward(...): via fornitore, con assert_no_leakage su ogni coppia [V, R1];
- predict_elo_fast(df, seasons_to_predict, k, h, nu, s=400.0, initial_rating=1500.0): passata unica, groupby per data, prima la previsione di tutte le partite della data e poi l'aggiornamento [V, R1];
- diagnose_season_transitions(df) [V, R1];
- output: DataFrame a 12 colonne (season, Date, HomeTeam, AwayTeam, rating_home, rating_away, delta, p_home, p_draw, p_away, home_promotion, away_promotion) [V, R1@2026-10-07].
elo_predictor.py — interni [V, R1@2026-10-07; righe 91, 212 e 282 R1]:
- _CALC_COLS = Date, season, HomeTeam, AwayTeam, FTR, FTHG, FTAG (righe 14-22), l'unico sottoinsieme su cui itera il percorso veloce (riga 475);
- _parse_season_start_year (riga 91); _validate_inputs; assert alla riga 282;
- _EloTracker (riga 212), classe con stato dei rating e regole d'ingresso stagionali.
elo_predictor.py — neopromosse:
- alla prima partita di una stagione si congela la classifica della precedente; le squadre mai viste prendono la media dei rating finali delle ultime tre, le tornanti riprendono l'ultimo rating attivo [V la regola, R1@2026-09-29c; D i dettagli];
- nella prima stagione del DataFrame tutte partono da initial_rating [V, R1@2026-09-29c].
elo_predictor.py — sui dati reali i due percorsi danno previsioni identiche byte per byte: SHA256 0b3048a7a170e7e149f6cb96c2790e36d3f05010a4d5ce35e1ea0febc1fcbce1 con K = 20, h = 60, ν = 1 [V, R21@2026-09-29b]
src/shk/model/elo_fit.py — importa split.py (SplitConfig), elo.py (expected_score), elo_predictor.py (predict_elo_fast) [V, R1]:
- costanti: SEASON_REGEX (riga 21); BOUNDS_K (5, 80), BOUNDS_H (0, 200), BOUNDS_NU (0.05, 3); INITIAL_PARAMS (30, 60, 1); OPTIMIZER_METHOD "Nelder-Mead", OPTIMIZER_OPTIONS; GRID_K, GRID_H (41 punti); WALKFORWARD_CSV_COLUMNS (15) [V, R1];
- tipi: EloFitParams (k, h, nu, c); EloCalibrationResult [V, R1];
- funzioni: parse_season_start_year (riga 96); derive_fit_schedule(training, validation=None), con SplitConfig o due collezioni; calibrate_single_fit (Nelder-Mead su K, h, ν); calibrate_all_fits [V, R1];
- compute_training_log_loss → (loss, preds), con clip a 1e-15 (riga 200; lo stesso nella baseline, riga 277) [V, R1@2026-10-07].
ELO_FITS (righe 321-340), congelato il 2026-09-29, coincide con la ricalibrazione entro rel_tol 1e-9 [V, R23@2026-09-29b; valori R1]:
- "2000-01": K = 10.318224689650037, h = 125.54022316884253, ν = 0.8062246331085681, c = 0.2657894736842105;
- "2010-11": K = 9.934776455088759, h = 127.87791672140764, ν = 0.8775613268630023, c = 0.2789473684210526;
- "2020-21": K = 7.928543266007228, h = 78.033626101627, ν = 0.7603760315281511, c = 0.25877192982456143.
src/shk/model/scoring.py — importa devig.py, elo_fit.py, elo_predictor.py [V, R1]:
- costanti: PINNACLE_CLOSING_START_SEASON = "2012-13", PINNACLE_START_YEAR = 2012, DEVIG_METHODS, SERIES_NAMES ("b365_prematch", "pinnacle_closing"), MATCH_KEYS (season, Date, HomeTeam, AwayTeam), CSV_COLUMNS (11) [V, R1];
- compute_log_loss puntuale, senza eps: ValueError se la probabilità realizzata è ≤ 0 (riga 114); compute_mean_log_loss; compute_g_hat_terms, compute_g_hat, compute_cumulative_g_hat [V, R1@2026-10-07];
- generate_validation_predictions(df, fits, schedule): predict_elo_fast con i parametri di ogni fit; ValueError per stagioni di validazione duplicate fra fit o conteggi diversi dal DataFrame [V, R1];
- import Any non usato [V, R1@2026-10-07].
scoring.py — allineamento e serie:
- align_predictions_with_odds(df_preds, df_raw): merge inner su MATCH_KEYS, prende da df_raw solo le colonne mancanti; ValueError per chiavi mancanti, duplicate o righe perse [V, R1];
- SeriesEvaluationData: conteggi di esclusione, df_used, p_model, q_proportional, q_additive, q_power (N×3), outcomes [V, R1@2026-10-07 e R27@2026-09-29b];
- prepare_series_evaluation(df_aligned, series, schedule), che può sollevare RuntimeError [V, R1@2026-10-07].
src/shk/model/recalibration.py — importa elo_fit.py, elo_predictor.py, scoring.py [V, R1]:
- costanti e tipi: PROB_LOWER_CLIP, PROB_UPPER_CLIP, OUTCOMES, CALIBRATION_CSV_COLUMNS (16); IsotonicModel, PlattModel, FitCalibrationMaps [V, R1];
- fit_isotonic_single (scipy.optimize.isotonic_regression), predict_isotonic_single, predict_platt_single; fit_platt_single, con RuntimeError se L-BFGS-B non converge (righe 300-303) [V, R1 e R1@2026-10-07];
- compute_brier_scores, brier_score, compute_reliability_table (10 fasce) [V, R1@2026-10-07];
- generate_fit_training_predictions: riceve fit_through senza usarlo (righe 322-336) [V, R1@2026-10-07];
- fit_all_calibration_maps; recalibrate_series_predictions (one-vs-rest, limite [1e-6, 1 − 1e-6], rinormalizzazione) [V, R1@2026-10-07 e R29–R30@2026-09-29b];
- import non usati: ELO_FITS, derive_fit_schedule, parse_season_start_year, MATCH_KEYS [V, R1@2026-10-07].
src/shk/model/residuals.py — importa elo_fit.py e scoring.py [V, R1]:
- REQUIRED_INPUT_COLUMNS (season, Date, HomeTeam, AwayTeam, FTR, FTHG, FTAG); RESIDUALS_COLUMNS (11): fit_through, role, season, Date, HomeTeam, AwayTeam, p_home, p_draw, p_away, FTR, log_loss [V, R1];
- compute_model_residuals(df, schedule, fits=None) [V, R1]:
  - validazione: generate_validation_predictions + align_predictions_with_odds;
  - training di ogni fit: compute_training_log_loss sulle stagioni ≤ fit, poi align_predictions_with_odds;
  - log_loss: compute_log_loss su tutte le righe; ordinamento per fit cronologico, ruolo (training poi validation), Date stabile;
- import MATCH_KEYS non usato [V, R1@2026-10-07].
src/shk/model/monitoring.py — 1351 righe: serie per scenario, record dei CSV di C5, Baseline D; non toccato in C6 [V, R1 e R2]
monitoring.py — import [V, R1]: backtest.py (BacktestResult, backtest_log_wealth, riga 15), metrics.py (max_drawdown), staking.py, elo_fit.py (parse_season_start_year), scoring.py (align_predictions_with_odds), drift.py, false_rejection.py (ALPHA, BLOCK_LENGTHS, N_BOOT), scipy.stats.norm
monitoring.py — contenuto per story [V, R1@2026-10-07]:
- C5.1: DRIFT_DETECTOR_CSV_COLUMNS (12), EXPECTED_MATCHES_PER_SEASON = 380 (riga 76), ScenarioSeries, extract_scenario_series, build_drift_records, generate_drift_detector_records;
- C5.2: DAILY_Z_TEST_CSV_COLUMNS (14), TrainingBaselineStats, compute_training_baseline_stats, build_daily_z_test_records, generate_daily_z_test_records;
- C5.3: BaselineDSeasonInput, KappaCalibrationRow (riga 744), KappaCalibrationResult, assemble_baseline_d_season_input (riga 787), BASELINE_D_CSV_COLUMNS (9), BaselineDValidationSeasonData, BaselineDAgentResult, build_baseline_d_season_data, evaluate_baseline_d_agents, generate_baseline_d_records;
- calibrate_baseline_d_kappa (riga 880; corpo alla riga 988), con default calibration_seasons=("2010-11", "2020-21").
monitoring.py — assemble_baseline_d_season_input(df_residuals, df_raw, season, fit_through, role="training", expected_matches=380) → BaselineDSeasonInput(season, dates datetime64[ns], probs (N, 3), odds B365H/D/A (N, 3), ftr object, log_loss), ordinato per Date; ValueError se le righe filtrate o allineate non sono expected_matches o mancano le colonne B365 [V, R1]. È l'input condiviso di C5.3, C6.2 e C6.3 reale [V, R1]
monitoring.py — campi delle classi di C5.3 [V, R5@2026-10-07]:
- BaselineDValidationSeasonData (righe 1030-1034): season, fit_through, season_input, adwin_alarm_dates, page_hinkley_alarm_dates;
- BaselineDAgentResult (righe 1060-1067): agent, kappa, final_log_wealth, n_bets, n_alarms (int | None), max_drawdown, backtest_result (BacktestResult), bets (BaselineDBets).
monitoring.py — esecuzione degli agenti di C5.3 [V, R5@2026-10-07]:
- evaluate_baseline_d_agents(season_data, base_lambda=BASE_LAMBDA, kappa_adwin=KAPPA_ADWIN, kappa_page_hinkley=KAPPA_PAGE_HINKLEY) → tupla di tre BaselineDAgentResult (righe 1141-1146); TypeError se season_data non è BaselineDValidationSeasonData;
- i tre agenti sono cablati nel corpo, senza lista né registro, e l'ordine di ritorno è fissato alla riga 1246: reference (righe 1179-1200, κ = 1.0 letterale alle righe 1184 e 1193), d_adwin (righe 1202-1222) e d_page_hinkley (righe 1224-1244) con κ dal parametro;
- generate_baseline_d_records ripete i tre nomi: nel dizionario agent_totals (righe 1295-1299, "kappa": 1.0 cablato per reference) e nella tupla dei totali (riga 1334);
- catena per ciascun agente: compute_adaptive_lambda → select_baseline_d_bets → backtest_log_wealth → float(max_drawdown(log_wealth.reshape(1, -1))[0]) (righe 1190, 1212, 1234).
src/shk/model/paired_backtest.py — C6.2; importa agents.py, environment.py, metrics.py (wealth_max_drawdown, wealth_recovery_time), elo_fit.py (parse_season_start_year), monitoring.py (assemble_baseline_d_season_input) [V, R1]:
- KELLYBENCH_INITIAL_BANKROLL_GBP = 220.0; CONFIGURATIONS = (("none", 0.0), ("gbp_0.01", 0.01/220), ("gbp_1", 1/220)); _FTR_OUTCOME_MAP H, D, A → 0, 1, 2; PAIRED_BACKTEST_CSV_COLUMNS (31) [V, R1];
- build_season_agents(min_stake): A (λ 1.0), B_0.25, B_0.10, più E solo se min_stake > 0 (righe 104-105): 3, 4 e 4 agenti, 11 combinazioni configurazione × agente [V, R5];
- evaluate_validation_seasons(df_residuals, df, schedule) → 209 righe "season" (19 × 11) e 11 "summary" [V, R1 e R13]:
  - per stagione di validazione, in ordine cronologico: assemble_baseline_d_season_input(role="validation"), esiti reali come matrice (1, N), run_paired_backtest per configurazione;
  - riga di stagione: final_wealth, final_log_wealth (vuota se W = 0), max_drawdown, recovery_dates (vuota se non recupera), ruined, ruin_date, contatori, roi = W − 1;
  - riepilogo: mediana di W, SD di ln W (ddof = 1) sulle stagioni non rovinate se sono più di una, tasso di rovina, drawdown mediano e massimo, tasso di recupero e mediana dei tempi, contatori sommati, ROI mediano, minimo e massimo; sum_final_log_wealth vuota se una stagione è rovinata (righe 284-287) [V, R5].
src/shk/model/floor_real_config.py — C6.3 reale; importa agents.py (MinimumStakeAgent), environment.py (AgentRun, DateView, run_paired_backtest), floor.py (SEED_C6), metrics.py (wealth_max_drawdown), devig.py (devig_proportional), elo_fit.py, monitoring.py, paired_backtest.py (CONFIGURATIONS, build_season_agents) [V, R1]:
- M_REPLICAS = 1 000; Z_99 = 2.576; THETA_THRESHOLDS = (0.5, 0.1); FLOOR_REAL_CSV_COLUMNS (22) [V, R1 e R13];
- outcomes_by_inversion(q, u): 0 se u < q_H, 1 se u < q_H + q_D, altrimenti 2; sample_match_outcomes(odds, rng, m_replicas=1000): q = devig_proportional(odds), u = rng.random((M, N)) [V, R7];
- compute_agent_e_analytic_roi(dates, odds, probs, min_stake) = F·Σ_d (1/S_d − 1), con S_d = Σ 1/o della partita di ripiego di E, scelta con le probabilità del modello [V, R1];
- SeasonRunArtifact (dataclass frozen); compute_season_metrics; compute_aggregate_metrics [V, R1];
- evaluate_floor_real_config(df_residuals, df, schedule, m_replicas=1000, seed=SEED_C6) → (220 record, artefatti per (config, agente)) [V, R1]:
  - ValueError se le stagioni di validazione non sono 19;
  - semi SeedSequence(seed).spawn(2)[1].spawn(19), uno per stagione in ordine cronologico; gli esiti si estraggono una volta per stagione e valgono per le tre configurazioni;
  - stesse probabilità e quote del Modulo 1 raw e di B365 di C6.2; per E anche il ROI analitico.
src/shk/model/residual_heteroskedasticity.py — C6.4; importa floor.py (SEED_C6), elo_fit.py, calibration.py (moving_block_indices), heteroskedasticity.py [V, R1]:
- ALPHA = 0.05, N_BOOT_CALIB = 999, N_VERIF_RESAMPLES = 1 000, BLOCK_LENGTHS = (7, 20, 40), ridefiniti invece che importati (righe 33-36); STATISTICS (bp_joint, bp_time, white) con gradi di libertà 2, 1, 5; BONFERRONI_LOWER/UPPER = 0.0153/0.0847; MATCHES_PER_SEASON = 380 (riga 49); HETEROSKEDASTICITY_CSV_COLUMNS (23) [V, R1 e R9];
- ScenarioData (season, role, fit_through, log_loss, entropy, t, date); TrainingData (fit_through, n_train, log_loss, entropy, date) [V, R9];
- compute_shannon_entropy(probs) = −Σ p·ln p per riga, con clip a 1e-15 [V, R9];
- extract_scenario_and_training_data(df_residuals, schedule, expected_matches=380) → 22 scenari in ordine cronologico, t = 1..380, e 3 serie di training (n_train 380, 760, 1140) [V, R9];
- compute_scenario_test_statistics, calibrate_block_bootstrap_thresholds, verify_calibrated_thresholds, binomial_exceedance_p_value(k, n=19, p=ALPHA) = P(X ≥ k) [V, R1 e R9];
- spawn_c6_4_generators(seed=SEED_C6, fits=("2000-01", "2010-11", "2020-21"), block_lengths): SeedSequence(seed).spawn(3)[2] → spawn per fit → spawn per L → spawn(2) (calibrazione, verifica) [V, R1];
- evaluate_residual_heteroskedasticity(df_residuals, schedule, seed=SEED_C6, alpha, block_lengths) → 105 record: 66 "scenario" (22 × 3 statistiche), 27 "verification" (3 fit × 3 L × 3), 12 "summary" (3 statistiche × 4 metodi) [V, R9 e R13].
scripts/ — quindici script us_c<story>_<n>_<nome>.py [V, R1]: us_c1_1_growth_vs_lambda, us_c1_2_estimation_error, us_c2_anova_autocorrelation, us_c3_1_data_coverage, us_c3_2_devig_divergence, us_c4_1_elo_walkforward, us_c4_2_g_hat, us_c4_3_calibration, us_c5_1_drift_detectors, us_c5_2_daily_z_test, us_c5_3_baseline_d, us_c6_2_paired_backtest, us_c6_3_floor_synthetic, us_c6_3_floor_real_config, us_c6_4_heteroskedasticity
Particolarità degli script di C1–C5 [V, R1@2026-10-07]:
- C1.1: p = 0.60, b = 1.0, T = 1000, M = 10000, seed 20260905 e 51 λ in [0, 2.5] cablati alle righe 30-36, λ = 1.946 alla riga 124; gli stessi valori sono ripetuti nel test;
- C3.1: load_all_seasons su tutta la directory (riga 29), 2023-24 compreso;
- C4.1: la docstring dice "script di calibrazione" ma usa ELO_FITS; costruisce le righe del CSV nello script (righe 52-105);
- C4.2: ĝ come np.mean(compute_g_hat_terms(...)); C4.3 rifà per conto suo la catena di C4.2;
- C5.1: riesegue run_drift_detector per la figura (righe 90-93); matchday 10/38 cablato alle righe 68-69, 97, 114, 134;
- C5.2: 1.9 cablato (righe 103, 137); int(s.split("-")[0]) alla riga 65;
- C5.3: etichetta "κ = 1.0" e asse fissato a ±0.05 (righe 75-76, 84).
Particolarità degli script di C6 [V, R1]:
- C6.2: run_experiment(), Agg, csv.DictWriter, dpi 150; figura a tre pannelli; linee di riferimento −0.041 (paper) e −0.051 (nota 3.4 §9) cablate (righe 131-132);
- C6.3 sintetico: run_experiment(), senza matplotlib.use("Agg"), modulo csv, dpi 300 (riga 166);
- C6.3 reale: main(), senza Agg, DataFrame.to_csv (riga 267), dpi 300 (riga 233), seed=SEED_C6;
- C6.4: main(), Agg, modulo csv (save_csv), dpi 300 (riga 266), seed=SEED_C6.
Nessuno script chiama calibrate_single_fit, calibrate_all_fits, calibrate_drift_detectors, calibrate_baseline_d_kappa, predict_elo_walkforward o diagnose_season_transitions [V, R1@2026-10-07; script di C6 non ricontrollati per questi nomi, D]
tests/ — 39 moduli [V, R1]:
- unitari: test_kelly_core, test_simulate, test_estimation, test_staking, test_metrics, test_backtest, test_agents, test_environment, test_floor, test_anova, test_timeseries, test_calibration, test_drift, test_heteroskedasticity, test_hac_anova_lm, test_data_loading, test_coverage, test_split, test_leakage, test_devig, test_elo, test_elo_predictor, test_scoring, test_recalibration, test_residuals;
- accettazione test_us_c1_1, c1_2, c2, c3_2, c4_1, c4_2, c4_3, c5_1, c5_2, c5_3, c6_2, c6_3, c6_3_real, c6_4 (_acceptance): controlli sintetici, controlli sui CSV e PNG versionati, ricalcoli dai dati reali.
Test sui dati reali saltati se data/raw/E0/ non ha CSV; _has_real_data è definita in 11 moduli [V, R11]
statsmodels compare solo in tests/: test_hac_anova_lm.py (ols, anova_lm) e test_heteroskedasticity.py (equivalenza su 50 dataset casuali, rel_tol 1e-9; guardia AST su src/ e scripts/, riga 330) [V, R1]
Copertura desunta dai file di test:
- mai nominate in un test [V, R1]: expected_final_wealth, spawn_c2_generators, calibrate_adwin, calibrate_page_hinkley, calibrate_all_fits, generate_fit_training_predictions, assemble_baseline_d_season_input, run_experiment_b, run_experiment_c, compute_season_metrics, extract_scenario_and_training_data, calibrate_block_bootstrap_thresholds, verify_calibrated_thresholds; tutte tranne expected_final_wealth sono raggiunte tramite altre funzioni [D per quelle di C6, V@2026-10-07 per le altre];
- solo importate, mai chiamate: build_baseline_d_season_data, extract_scenario_series, build_drift_records, build_daily_z_test_records [V, R1@2026-10-07];
- chiamate solo in test saltati senza dati, quindi mai in CI: calibrate_drift_detectors (test_drift.py:289), recalibrate_series_predictions (test_us_c4_3_acceptance.py:168-169), calibrate_baseline_d_kappa (test_us_c5_3_acceptance.py:158), generate_baseline_d_records (riga 336), load_by_role sui ruoli reali, diagnose_season_transitions sui dati reali (test_elo_predictor.py:351) [V, R1@2026-10-07]; evaluate_validation_seasons, evaluate_floor_real_config ed evaluate_residual_heteroskedasticity sui dati reali [V, R1];
- le altre funzioni pubbliche sono nominate in almeno un test [V, R1]; la presenza in un'asserzione non è verificata funzione per funzione [D];
- CSV versionati senza un test che li legga: C1.1, C1.2, C3.1 [V, R1@2026-10-07]; i quattro CSV di C6 hanno test che li leggono [V, R1];
- PNG senza test di esistenza: C1.1, C1.2, C3.1, C5.1, C5.3, e C4.1 (PNG_PATH definito ma non usato, test_us_c4_1_acceptance.py:25) [V, R1@2026-10-07]; C6.2 e C6.3 sintetico hanno un test di esistenza [V, R1]; C6.3 reale e C6.4 non verificati [D];
- test_metrics.py:test_metrics_error_conditions non verificava il ValueError di median_final_wealth e mean_final_wealth [V, R1@2026-09-29c]; test_metrics.py ha ricevuto solo aggiunte in T35 [V, R3], se coprano quel caso non verificato [D].
Classi del pacchetto [V, R1]:
- dati: Scenario, StakingMoments, BaselineDBets, BacktestResult, OneWayAnovaResult, PhiStreams, RejectionResult, ColumnClassification, SplitConfig, EloFitParams, EloCalibrationResult, SeriesEvaluationData, IsotonicModel, PlattModel, FitCalibrationMaps, ScenarioSeries, TrainingBaselineStats, BaselineDSeasonInput, KappaCalibrationRow, KappaCalibrationResult, BaselineDValidationSeasonData, BaselineDAgentResult, DateView, AgentDecision, PlacedBets, AgentRun, ExpCConfig, ExperimentARunResult, ExperimentBResult, ExperimentCConfigResult, SeasonRunArtifact, ScenarioData, TrainingData, HeteroskedasticityTestResult, HeteroskedasticityBatchResult; sono NamedTuple o dataclass frozen [V per quelle lette, D per ExperimentARunResult, ExperimentBResult, ExperimentCConfigResult];
- eccezioni: TestSetLockedError, LeakageError;
- con comportamento: _EloTracker, Agent (ABC) con FractionalKellyAgent e MinimumStakeAgent.
Persistenza: nessun database; config/split.toml; quindici CSV in results/ e quindici PNG omonimi in thesis/figures/, tutti versionati [V, R1]. Gli schemi dei CSV sono costanti *_CSV_COLUMNS; i record sono list[dict] con stringa vuota per i campi non applicabili, scritti con csv.DictWriter o il modulo csv, tranne C6.3 reale con DataFrame.to_csv [V, R1]
CSV versionati, colonne e righe di dati [V, R1@2026-10-07 per C1–C5; C6 R13]: us_c1_1_growth_vs_lambda (10, 51), us_c1_2_estimation_error (12, 46), us_c2_anova_autocorrelation (10, 24), us_c3_1_data_coverage (12, 477), us_c3_2_devig_divergence (19, 29), us_c4_1_elo_walkforward (15, 9 500), us_c4_2_g_hat (11, 33 066), us_c4_3_calibration (16, 144), us_c5_1_drift_detectors (12, 66), us_c5_2_daily_z_test (14, 860), us_c5_3_baseline_d (9, 60), us_c6_2_paired_backtest (31, 220: 209 season, 11 summary), us_c6_3_floor_real_config (22, 220: 209 season, 11 aggregate), us_c6_3_floor_synthetic (32, 47: esperimento A 14, B 30, C 3), us_c6_4_heteroskedasticity (23, 105: 66 scenario, 27 verification, 12 summary)
results/us_c5_3_baseline_d.csv: intestazione row_type, season, fit_through, agent, kappa, final_log_wealth, n_bets, n_alarms, max_drawdown [V, R6@2026-10-07]

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
- test: 2023-24, bloccato e non letto tramite load_by_role (380).
Schema espansivo: ogni fit j si stima sulle stagioni di training ≤ j e prevede le stagioni di validazione fino al fit successivo [V, R1]. Conteggi per fit, asseriti in test_residuals.py:283-297 [V, R1; stagioni ricalcolate dal supervisore]:
- fit 2000-01: training 380, validazione dal 2002-03 al 2009-10 (3 040);
- fit 2010-11: training 760, validazione dal 2011-12 al 2019-20 (3 420);
- fit 2020-21: training 1 140, validazione 2021-22 e 2022-23 (760); in tutto 9 500 righe di residui.
Catena comune sui dati reali, copiata negli script C4.x, C5.x, C6.2, C6.3 reale, C6.4 e nei test di ricalcolo [V, R1]:
1. read_split_config → derive_fit_schedule(cfg);
2. load_by_role("history" | "training" | "validation"), poi concatenazione e ordinamento stabile per Date nello script;
3. generate_validation_predictions(df, ELO_FITS, schedule) → predict_elo_fast per fit → _EloTracker → elo_delta, davidson_probabilities, elo_update;
4. align_predictions_with_odds(df_preds, df_full);
5. da C5 in poi, compute_model_residuals(df, schedule, ELO_FITS), che comprende i passi 3-4 e aggiunge il training di ogni fit.
C4.2 e C4.3, dopo la catena [V, R1@2026-10-07]:
- prepare_series_evaluation per "b365_prematch" e "pinnacle_closing" (devig_additive per le esclusioni, poi i tre metodi);
- compute_mean_log_loss, compute_g_hat_terms, compute_cumulative_g_hat;
- per C4.3: mappe isotonica e Platt sul training, ricalibrazione, reliability e Brier.
C5.1 e C5.2 [V, R1@2026-10-07]:
- C5.1: generate_drift_detector_records → extract_scenario_series (22 serie da 380: 3 di training e 19 di validazione) → build_drift_records → run_drift_detector, con un'istanza nuova per stagione;
- C5.2: generate_daily_z_test_records → compute_training_baseline_stats e serie di training per fit → build_daily_z_test_records, che usa spawn_c5_generators, calibrate_matchday_z_threshold (→ calibrate_threshold), verify_matchday_z_thresholds, compute_matchday_z_scores e run_drift_detector.
C5.3 [V, R1 e R5@2026-10-07]:
1. residui come sopra;
2. generate_baseline_d_records → per ogni stagione di validazione build_baseline_d_season_data (assemble_baseline_d_season_input con le quote B365H/D/A, run_drift_detector per i due detector);
3. evaluate_baseline_d_agents;
4. CSV con 57 righe di stagione (19 × 3 agenti) e 3 di totale; PNG delle differenze appaiate.
Definizioni di C5, dalle decisioni S5, scelte del supervisore su delega non ancora confermate [D, BACKLOG.md; implementazione non riletta salvo dove marcato]:
- matchday = blocco contiguo di 10 partite nell'ordine cronologico stabile;
- Z = (media della log-loss del matchday − μ_f)/(σ_f/√10), con μ_f e σ_f (ddof = 1) dal training del fit; allarme nominale se |Z| > z_0.975;
- parametri dei detector: la combinazione della griglia con la media di allarmi su 2000-01 e 2010-11 più vicina a 1.9;
- Baseline D: al più una puntata per partita (esito con p̂·o − 1 massimo se positivo) con quote B365 non de-viggate e p̂ raw; λ = 0.25·κ^allarmi, dove un allarme della data d conta dalle date successive [V la regola, R1@2026-10-07]; bankroll 1 a inizio stagione;
- κ scelto per detector sulla somma della log-ricchezza finale di 2010-11 e 2020-21; a parità vince il più grande.
CSV di C5.2: 860 righe = 722 + 114 + 6 + 18, conteggi asseriti in test_us_c5_2_acceptance.py:310-318 [V, R1@2026-10-07]. Interpretazione [D, ricalcolo del supervisore]: 722 = 19 stagioni × 38 matchday dello Z nominale; 114 = 19 × 6 metodi; 6 riepiloghi complessivi; 18 righe di verifica
C6.2 [V, R1 e R5]:
1. catena comune fino a compute_model_residuals;
2. evaluate_validation_seasons: per stagione di validazione assemble_baseline_d_season_input(role="validation"), FTR → 0/1/2 come una sola replica (M = 1);
3. per configurazione build_season_agents → run_paired_backtest → a ogni data DateView condivisa, decide per agente, controllo di rovina, place_date_stakes sulle repliche attive, regolamento;
4. metriche wealth_max_drawdown e wealth_recovery_time; CSV e figura.
C6.3 sintetico [V, R1 e R8]: evaluate_all_synthetic_experiments(SEED_C6) → spawn_t36_generators → run_experiment_a, b, c → run_paired_chunked → run_paired_backtest con FractionalKellyAgent su calendario a una partita per data
C6.3 reale [V, R1 e R7]: catena comune → evaluate_floor_real_config → per stagione assemble_baseline_d_season_input, sample_match_outcomes (M = 1 000 da q proporzionali di B365), poi run_paired_backtest per configurazione con gli agenti di build_season_agents → compute_season_metrics, compute_aggregate_metrics
C6.4 [V, R1 e R9; ordine interno dopo la calibrazione D]: catena comune → evaluate_residual_heteroskedasticity → extract_scenario_and_training_data → spawn_c6_4_generators → calibrate_block_bootstrap_thresholds (training del fit, B = 999) → verify_calibrated_thresholds (1 000 ricampionamenti) → statistiche LM per scenario contro soglie nominali e calibrate → riepiloghi binomiali sulle 19 stagioni di validazione
Repliche di logica nei test [V, R1@2026-10-07 salvo C6]:
- test_us_c5_3_acceptance.py:130-142 riscrive la regola di parità di κ invece di chiamare calibrate_baseline_d_kappa;
- test_us_c4_1_acceptance.py:188-220 duplica la costruzione delle righe di C4.1, senza strip di FTR e senza i controlli riga per riga dello script;
- test_us_c4_2_acceptance.py:109-166 confronta solo le 6 righe di riepilogo e usa compute_g_hat;
- test_us_c5_2_acceptance.py:424-436 reimplementa |z| > soglia sui valori del CSV;
- test_us_c1_2_acceptance.py usa 1.1·p e 0.9·p invece di relative_perturbation;
- test_us_c6_3_acceptance.py:93-95 rifà l'esperimento A con M = 100 e chunk 50, contro M = 10 000 e chunk 2 000 dello script [V, R1].
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
Risultati C5.3, da results/us_c5_3_baseline_d.csv [V, R6@2026-10-07]:
- sulle 19 stagioni, reference, d_adwin e d_page_hinkley hanno κ = 1.0, final_log_wealth totale −10.58001605492385 e 6 234 puntate ciascuno;
- allarmi: 0 per ADWIN e 20 per Page-Hinkley;
- final_log_wealth di d_adwin e di d_page_hinkley è identico a quello di reference in 19 stagioni su 19.
Con κ = 1 vale λ = 0.25 a ogni partita, qualunque sia il numero di allarmi: la Baseline D coincide col quarto-Kelly senza detector per costruzione [V la formula, R1@2026-10-07; D la conseguenza, confermata da R6@2026-10-07]
Risultati C6.2, righe summary di results/us_c6_2_paired_backtest.csv, esiti reali sulle 19 stagioni [V, R13; percentuali ricalcolate dal supervisore]:
- B_0.25 con F = 0: sum_final_log_wealth −10.58001605492385 e 6 234 puntate, uguali a C5.3;
- F = 0: ricchezza finale mediana A 0.00164, B_0.25 0.598, B_0.10 0.839; A scarta 28 puntate (6 206 + 28 = 6 234); nessuna rovina;
- rovina di A: 0, 4 e 14 stagioni su 19 con F = 0, £0.01, £1; B ed E mai in rovina;
- con £1: B_0.10 ha 2 608 puntate alzate al floor su 6 333 (41.2%), log-ricchezza totale da −2.981 a −3.502; B_0.25 da −10.580 a −10.665;
- E: 1 963 puntate, una per data; ricchezza finale mediana 0.99992 con £0.01 e 0.99241 con £1.
Risultati C6.3 reale, righe aggregate di results/us_c6_3_floor_real_config.csv, 19 000 traiettorie per agente e configurazione [V, R13]:
- con F = 0 nessuna rovina; con £0.01 solo A, 17.92%; con £1 A 68.97%, B_0.25 0.495%, B_0.10 0 con W minimo 0.159;
- ricchezza finale mediana con F = 0: A 0.00573, B_0.25 0.584, B_0.10 0.852;
- P(min W ≤ 0.5) con F = 0: A 0.983, B_0.25 0.554, B_0.10 0.050; P(min W ≤ 0.1): 0.888, 0.015, 0;
- ROI medio di E: −0.0237% con £0.01, −2.37% con £1;
- intervalli al 99% della rovina, confronto col ROI analitico e quote di puntate alzate: nei report [D, BACKLOG.md S6 da T37].
Risultati C6.3 sintetico, dai report [D, BACKLOG.md S6 da T36]:
- senza floor la rovina è 0 in ogni esperimento;
- partenza 50F con floor: 0.180%, 8.050%, 35.670% a 150, 400, 1000 scommesse, contro 0.149%, 7.616%, 35.760% della nota; partenza 1000F: 0;
- sweep a 1000 scommesse: 89.1% a B0/F = 10, 59.6% a 31.6, 3.3% a 100, 0 da 220 in su;
- tempo medio di rovina (a) 2 481 contro il limite 32 986, mediana 1 427, accelerazione circa 13× (la nota dice 23×).
Risultati C6.4, righe summary di results/us_c6_4_heteroskedasticity.csv, rigetti nelle 19 stagioni di validazione [V, R13]:
- bp_joint: nominale 19, calibrata L = 7, 20, 40: 1, 0, 1;
- white: nominale 19, calibrata 0, 0, 0;
- bp_time: 2 con ogni metodo, P(X ≥ 2) = 0.2453 sotto Binomiale(19, 0.05).
Altri valori di C6.4 (soglie calibrate, tassi di verifica, statistiche sul training) e di T38 (HAC su anova_lm: con typ=1 l'HAC è ignorato, con typ=2 e 3 l'F è il Wald HAC): nei report e in BACKLOG.md S6 [D]

## Convenzioni da rispettare
Naming: snake_case per moduli, funzioni e variabili; PascalCase per le classi; UPPER_CASE per le costanti, con Final nel codice nuovo (false_rejection.py e scenarios.py non lo usano); prefisso _ per gli helper interni; test con prefisso test_ [V, R1]
Lingua: commenti e docstring in italiano; identificatori, nomi dei test e messaggi delle raise in inglese [V, R1; nomi dei test con ricerca euristica, D]
Messaggi di assert e motivi di skip: in inglese nel codice nuovo; quelli in italiano già presenti restano finché un task non tocca il test per altri motivi [decisione del programmatore 2026-10-11]. Oggi in italiano in test_leakage, test_us_c3_2, test_us_c4_1, test_us_c5_2, test_us_c5_3, test_split.py:480 [V, R1@2026-10-07] e test_us_c6_3_real (righe 120-302, 324) [V, R1]
Accenti nelle docstring: misti fra "è" e "e'" (loading.py, split.py, floor_real_config.py, heteroskedasticity.py usano l'apostrofo) [V, R1]; nessuna regola fissata [D]
Type hints sulle funzioni pubbliche; docstring in stile NumPy con sezioni Parametri / Restituisce / Solleva [V, R1]
Validazione in apertura di funzione: TypeError per i tipi, ValueError per i valori; rng controllato con isinstance(rng, np.random.Generator) [V, R1 e R5@2026-09-28]
Nel codice da C2 in poi: bool e float al posto di un intero danno TypeError, gli interi NumPy sono accettati, una str non vale come collezione di str [V, R1@2026-10-07]. Eccezioni: in C1 draw_outcomes, noisy_estimates, expected_final_wealth e kelly_fraction non controllano il tipo [V, R1@2026-10-07]; in C6 sample_match_outcomes ed evaluate_floor_real_config danno ValueError per m_replicas bool o non intero [V, R7 e R1]
Eccezioni dedicate: TestSetLockedError, LeakageError. RuntimeError per mancata convergenza (devig_power, fit_platt_single) e in prepare_series_evaluation [V, R1@2026-10-07]
Nessun try/except in src/ e scripts/ [V, R11]; nessun print(, logging o warnings.warn in src/ e scripts/ [V, R1]; alcuni test lo verificano via AST (test_us_c6_3_real_acceptance.py:368-390, test_agents.py:784) [V, R1]
assert nel codice di libreria solo in elo.py ed elo_predictor.py, alle righe elencate in Moduli [V, R1]
RNG e semi [V, R1]:
- le funzioni di kelly/ e stats/ ricevono il Generator come argomento;
- le pipeline (spawn_generators, spawn_c2_generators, spawn_c5_generators, spawn_t36_generators, spawn_c6_4_generators, evaluate_floor_real_config, evaluate_all_synthetic_experiments, evaluate_residual_heteroskedasticity) ricevono un seed intero e derivano i flussi con SeedSequence.spawn;
- seed: 20260905 (C1.1, nello script), SEED = 20260927 (C1.2), SEED_C2 = 20260928, SEED_C5 = 20260929, SEED_C6 = 20261009; una story nuova usa un seed nuovo [V i valori; D la regola].
Organizzazione [V, R1 e R11; decisione S5 in BACKLOG.md]:
- kelly/: funzioni su array, agenti e ambiente di simulazione; non importa da shk.model né da shk.data;
- stats/: funzioni statistiche su array; eccezione drift.py, che usa pandas e restituisce DataFrame dalle calibrate_*;
- data/: I/O e split; market/: quote;
- model/: funzioni su DataFrame del Modulo 1 e costruzione dei record dei CSV di C4, C5 e C6.
Agenti: un agente nuovo è una sottoclasse di Agent che ridefinisce solo __init__ e stake_fractions; previsioni, quote e argomenti in sola lettura; il bankroll sta nell'ambiente [V, R1; decisione S6 in BACKLOG.md]
Vettorizzazione: nessun ciclo su M e T nel motore Monte Carlo [V, R1@2026-09-29c]. Cicli Python per data: backtest_log_wealth e run_paired_backtest (anche per agente; maschera dates == d sull'intero array) [V, R1]; per partita: select_baseline_d_bets; per replica: wealth_recovery_time [V, R4]; ordinamento con sorted per data in place_date_stakes [V, R6]
Script di esperimento, regola per quelli nuovi [decisione del programmatore 2026-10-11, convenzione di C1–C5, V, R1@2026-10-07]:
- scripts/us_c<story>_<n>_<nome>.py → results/<stesso nome>.csv e thesis/figures/<stesso nome>.png, entrambi versionati;
- matplotlib.use("Agg") prima di pyplot; run_experiment() senza parametri, dal blocco __main__; nessun argomento da riga di comando; nessun print;
- CSV con csv.DictWriter, float nativi e stringa vuota dove non applicabile; savefig(dpi=150); etichette in italiano;
- gli script di C6 che deviano (main(), dpi 300, to_csv) restano come sono; ai due di C6.3 va aggiunto Agg con un task dedicato, senza rigenerare i CSV.
Pipeline sui dati reali, regola per il codice nuovo [decisione del programmatore 2026-10-11]: la catena comune si estrae in una funzione di libreria in src/shk/model/residuals.py, che script e test nuovi usano; gli script e i test esistenti non si migrano. La funzione non esiste ancora [V, R1: nessuna funzione condivisa trovata; D che non ne esista una altrove]
Percorsi: script e test nuovi usano Path(__file__).resolve().parents[1]. Eccezioni storiche con percorsi relativi alla directory corrente: C1.1, C1.2, C2 e tests/test_us_c2_acceptance.py (righe 179, 257, 315) [V, R1 e R1@2026-10-07]
Parametri condivisi fra script e test stanno in un modulo di libreria [V, R1 e R1@2026-10-07]:
- C1.2 scenarios.py; C2 false_rejection.py; C3 coverage.py, divergence.py e split.toml;
- C4 elo_fit.py, scoring.py, recalibration.py; C5 drift.py, staking.py, monitoring.py;
- C6: agents.py (λ), floor.py (SEED_C6, EXP_*), paired_backtest.py (CONFIGURATIONS), floor_real_config.py (M_REPLICAS, THETA_THRESHOLDS), residual_heteroskedasticity.py;
- eccezioni storiche: C1.1, con i parametri cablati nello script e nel test; C6.2, con le linee −0.041 e −0.051 cablate nello script.
Test [V, R1 e decisioni S3–S4]:
- Monte Carlo su larga scala e test sui dati reali oltre 60 s si marcano @pytest.mark.slow; i test anti-leakage no; sotto i 60 s restano nella suite veloce (T35 ha marcato slow un test da 14.6 s contro la regola, poi corretto) [D, BACKLOG.md S6];
- i test sui dati reali si saltano con motivo esplicito, tramite _has_real_data o una condizione equivalente su DEFAULT_DATA_DIR;
- un test che controlla solo il CSV versionato non basta, perché in CI mancano i dati grezzi [V, R31 e R33@2026-09-29b];
- se il CSV versionato manca, C4.1 e C6.3 reale saltano, mentre C4.2, C4.3, C5.2, C5.3 asseriscono che esiste [V, R1 e R1@2026-10-07].
Dati reali nel codice nuovo solo con read_split_config e load_by_role [V, R1 e R26@2026-09-29]:
- load_all_seasons è ammessa solo in loading.py, split.py, coverage.py e scripts/us_c3_1_data_coverage.py;
- un test di guardia AST in tests/test_split.py (righe 437-454) lo verifica, scandendo solo src/ e scripts/;
- i test in tests/ la usano liberamente.
Probabilità 1X2: ndarray (N, 3) in ordine H, D, A con righe a somma 1; previsioni walk-forward, prima dell'aggiornamento della stessa data. Esiti come stringhe H, D, A nei DataFrame e come interi 0, 1, 2 (NO_BET = −1) negli agenti e nell'ambiente [V, R1]
Processo [V, PROTOCOLLO.md; non toccato in C6, R2]:
- i commit li fa solo il programmatore, a mano;
- ogni story ha un branch di lavoro che entra in main come un solo commit;
- Cline scrive in .agent/ solo MAPPA.md in mappatura e report/T<n>.md in esecuzione; .agent/ è versionato [V, R1];
- la sezione "Convenzioni del progetto" di PROTOCOLLO.md non ha convenzioni aggiuntive [V, R1].

## Zone fragili da non toccare senza avviso
test_acceptance_calibrated_phi_zero_within_mc_interval (tests/test_us_c2_acceptance.py, slow) fallisce per un risultato noto [V, R14@2026-09-28; decisione del programmatore 2026-09-28; non rieseguito dopo]:
- 29 rigetti su 1000 a φ = 0 con L = 20, sotto l'estremo 32.25 dell'intervallo al 99%;
- è il T12 da rivedere, non una regressione: non si sistema allentando tolleranze o parametri.
Tarature e costanti congelate, che non si modificano [D, decisioni S4–S6 in BACKLOG.md]: ELO_FITS, ADWIN_DELTA, PAGE_HINKLEY_DELTA, PAGE_HINKLEY_THRESHOLD, KAPPA_ADWIN, KAPPA_PAGE_HINKLEY, SEED_C6, CONFIGURATIONS, M_REPLICAS, THETA_THRESHOLDS. Nessuno script ricalibra le prime sei; si riverificano solo con test locali [V, R1@2026-10-07]
Una modifica a elo.py, elo_predictor.py, elo_fit.py, scoring.py, residuals.py o recalibration.py che cambia previsioni o metriche rende incoerenti ELO_FITS, le tarature di C5 e i CSV di C4, C5 e C6: vanno ricalibrati e rigenerati. Lo segnalano solo in locale i test di ricalcolo e di taratura [D]
Ricalcoli contro CSV versionati con tolleranza 1e-12: tests/test_us_c6_2_acceptance.py:309-338, tests/test_us_c6_3_real_acceptance.py:322-375 (M = 1 000, SEED_C6), tests/test_us_c6_4_acceptance.py:255-270 (SEED_C6), più il ricalcolo slow di C6.3 sintetico (test_us_c6_3_acceptance.py:195) [V, R1]. Qualunque modifica a kelly/agents.py, environment.py, floor.py, metrics.py, ai moduli di model/ di C6 o alle versioni di numpy e scipy li fa divergere [D]
Due motori di backtest [V, R1 e R11]:
- C5.3 usa backtest_log_wealth (kelly/backtest.py), C6 l'ambiente (kelly/environment.py);
- l'equivalenza con F = 0 (B_0.25 contro il riferimento di C5.3, entro 1e-12, 6 234 puntate) la verifica sui CSV versionati tests/test_us_c6_2_acceptance.py:60, anche in CI; il ricalcolo dai dati reali alla riga 108 gira solo in locale;
- backtest_log_wealth riceve frazioni già calcolate e non conosce la ricchezza: non regge floor né puntate minime [V, R4@2026-10-07];
- con λ = 1 e più partite nella stessa data backtest_log_wealth può sollevare ValueError per somma delle frazioni ≥ 1; l'ambiente invece scarta le puntate oltre W [V, R1@2026-10-07 e R6].
Gerarchia dei semi di C6 su tre file [V, R1]: spawn(2)[0] in floor.py:165-168 (T36), spawn(2)[1] in floor_real_config.py:439-441 (T37), spawn(3)[2] in residual_heteroskedasticity.py:340-342 (T39). Che i figli di una SeedSequence nuova dipendano solo dalla posizione, per cui spawn(2)[i] = spawn(3)[i], è la semantica documentata di numpy ma non è verificata nel codice del venv (sorgente .pyx assente) [D, R12]. Cambiare il numero o l'ordine dei figli cambia i CSV di C6
Costanti cablate legate allo split [V, R1]: 19 stagioni di validazione in evaluate_floor_real_config (spawn(19) e ValueError se non 19) e in binomial_exceedance_p_value (n = 19); 380 partite in monitoring.py:76 e residual_heteroskedasticity.py:49; fit ("2000-01", "2010-11", "2020-21") come default di spawn_c6_4_generators. Un altro split le rompe [D]
C6 dipende da C5 [V, R1]: paired_backtest.py e floor_real_config.py prendono l'input da monitoring.assemble_baseline_d_season_input; floor_real_config.py e residual_heteroskedasticity.py prendono SEED_C6 da kelly/floor.py. Una modifica a monitoring.py tocca C5.3, C6.2 e C6.3 reale
Semantica del floor implementata [V, R6; scelte su delega da confermare, BACKLOG.md S6]: il floor alza anche le puntate volontarie (max(f·W, F)); la rovina è W < F stretto; le puntate oltre W si scartano per EV stimato; la variante "salta le puntate sotto F" non esiste
Con F = 0 la rovina per assorbimento è impossibile per costruzione (Σ f < 1); il rischio si legge su P(min W ≤ θ) e sul drawdown [D, BACKLOG.md S6; coerente con R13]
FractionalKellyAgent con λ = 1 e p̂ = 1 dà frazione 1 e ValueError in decide [V, R1]; col Modulo 1 non accade [D]
Helper duplicati: _is_real_numeric_dtype e _read_only_view identici in agents.py (38, 56) ed environment.py (28, 46); ALPHA e BLOCK_LENGTHS ridefiniti in residual_heteroskedasticity.py:33-36 invece di importarli da false_rejection.py [V, R1]
ExpCConfig "a" porta note_acceleration = 23.0 della nota, che la misura di T36 smentisce (circa 13×) [V il valore, R8; D la misura, BACKLOG.md S6]
Script di C6.3 senza matplotlib.use("Agg"): in un ambiente senza display possono fallire [V l'assenza, R1; D la conseguenza]; correzione decisa il 2026-10-11, vedi Convenzioni
Baseline D degenerata [V, R1@2026-10-07, R5 e R6@2026-10-07; D la conseguenza sulla figura]:
- con KAPPA_ADWIN = KAPPA_PAGE_HINKLEY = 1.0 i due agenti D puntano come il riferimento (vedi Flussi);
- il κ del riferimento è 1.0 letterale in monitoring.py (righe 1184, 1193, 1295-1299);
- lo script C5.3 cabla l'etichetta "κ = 1.0" e l'asse ±0.05: cambiando le costanti la figura non si aggiorna.
max_drawdown richiede almeno 2 colonne: una stagione senza date darebbe ValueError in evaluate_baseline_d_agents [V il reshape, R5@2026-10-07; D la conseguenza]; lo stesso vincolo vale per wealth_max_drawdown e wealth_recovery_time [V, R4]
Agenti cablati in monitoring.py: evaluate_baseline_d_agents e generate_baseline_d_records ripetono i tre nomi, quindi un agente nuovo di C5 tocca entrambe le funzioni [V, R5@2026-10-07]; per C6 vale invece build_season_agents [V, R5]
CSV accoppiati [V i test, R1@2026-10-07 e R1; D la conseguenza]:
- test_us_c4_3_acceptance.py::test_raw_g_hat_matches_t23 confronta C4.3 con C4.2;
- test_us_c5_2_acceptance.py::test_versioned_csv_alarms_match_c5_1 confronta C5.2 con C5.1;
- test_us_c6_2_acceptance.py:60 confronta C6.2 con C5.3;
- rigenerarne uno solo li fa divergere.
Rieseguire uno script sovrascrive CSV e PNG versionati: ogni task che rigenera un esperimento dice se vanno committati [V, R1@2026-10-07]
Dipendenze senza vincoli e CI senza lockfile:
- la CI installa le ultime versioni [V, R1];
- i conteggi esatti degli allarmi (test_drift.py:324-335 e CSV di C5) dipendono da river 0.26.1 [D];
- NumPy non garantisce la stabilità dei flussi di Generator fra versioni, e i ricalcoli di C6 sono a 1e-12 [D];
- il valore critico C2 per k = 2 differisce all'ultima cifra fra venv e CI [V, R9 e R15@2026-09-28];
- scipy.optimize.isotonic_regression (recalibration.py) richiede uno scipy recente, senza vincolo minimo dichiarato [D];
- uv.lock non ha pandas, river né statsmodels [V, R3].
Test slow e test sui dati reali non girano in CI, per addopts e per data/raw/* ignorato [V, R1]. Vanno lanciati a mano dopo modifiche a kelly/, stats/ o model/ [D]. Nella suite veloce locale restano ricalcoli sui dati reali: test_leakage.py (circa 8 s) [V, R46@2026-09-29], test_us_c6_4_acceptance.py (15.7 s) [V che il report lo dice, R15: T39.md:127], test_us_c6_3_real_acceptance.py (durata non nota) [D]
Blocco del test set aggirato da due percorsi ammessi [V, R1]:
- scripts/us_c3_1_data_coverage.py:29 e tests/test_data_loading.py:312 chiamano load_all_seasons su tutta la directory, 2023-24 compreso;
- results/us_c3_1_data_coverage.csv ha 35 righe del 2023-24 [V, R1@2026-10-07];
- il test di guardia AST non scandisce tests/.
config/split.toml è congelato e non si modifica. Lo sblocco del test lo fa solo il programmatore, a mano e con commit, dopo il congelamento dei parametri (US-C8.2) [V, decisione S3]
La prova del congelamento dello split dipende da 2cea094, raggiungibile solo dalla reflog locale (HEAD@{35} il 2026-10-11, R14): una garbage collection può eliminarlo alla scadenza della voce, per default circa 30 giorni dopo il 2026-09-29, cioè verso il 2026-10-29 [V la presenza, R14; D la scadenza]
load_by_role richiede il file di ogni stagione configurata, test compreso, anche per caricare training [V, R1]
walkforward_split è un generatore: le validazioni scattano alla prima iterazione, non alla chiamata [V, R1]
classify_column solleva ValueError su colonne non catalogate, quindi file E0 con colonne nuove fermano audit e fornitore walk-forward; estendere coverage.py cambia i campi esposti dal fornitore [V, R1@2026-10-07 e R45–R46@2026-09-29]
Errori che fermano un calcolo intero [V, R1@2026-10-07]: devig_power solleva RuntimeError se anche un solo mercato non converge; fit_platt_single se L-BFGS-B non converge
devig_additive dà righe di NaN da escludere per tutti i metodi; test_devig.py:test_extreme_markets salta quei mercati [V, R35@2026-09-29]
noisy_estimates può dare p̂ = 1 per saturazione; con lam ≥ 1 kelly_staking dà frazioni ≥ 1, che simulate_growth rifiuta [V, R1@2026-10-07]. Con p ≤ 0.6 e σ_p ≤ 0.045 l'evento dista almeno 8.9 deviazioni standard [D, ricalcolo del supervisore]
elo_predictor.py: il percorso veloce itera solo su _CALC_COLS, quindi un calcolo che usa un'altra colonna deve aggiungerla lì [V la riga 475, R1@2026-10-07; D la regola]. Dopo ogni modifica al file, confrontare lo SHA256 delle previsioni con quello di riferimento (vedi Moduli) [V, R21@2026-09-29b]
Duplicazioni [V, R1 e R1@2026-10-07]:
- catena comune sui dati reali copiata in nove script e nei test di ricalcolo (vedi Flussi);
- parsing della stagione: parse_season_start_year (elo_fit.py:96) e _parse_season_start_year (elo_predictor.py:91), con SEASON_REGEX in entrambi; regex in loading.py e split.py; int(s.split("-")[0]) in split.py e nello script C5.2;
- due log-loss: compute_training_log_loss con clip a 1e-15 (elo_fit.py:200 e :277) e compute_log_loss con ValueError per p ≤ 0 (scoring.py:114); test_residuals.py:345 le confronta entro 1e-12;
- matchday da 10 e 38 cablato invece di MATCHDAY_SIZE: monitoring.py:258 e :429, script C5.1 e C5.2;
- _has_real_data definita in 11 moduli di test.
Test che cercano frasi esatte nelle docstring: test_calibration.py:322-338, test_staking.py:405-410, test_us_c5_3_acceptance.py:122-127. La correzione della docstring di calibration.py deve preservarle [V, R1@2026-10-07]
Asserzioni legate a seed, tolleranze o costanti empiriche, che si rompono se cambiano RNG, versioni o dati [V, R1 e R1@2026-10-07]:
- conteggi reali cablati: test_split.py:483-491, test_leakage.py:434-436, test_residuals.py:283-297, test_us_c4_1_acceptance.py:123-150, test_us_c4_2_acceptance.py:137-139, test_elo_predictor.py:366-386, test_us_c5_2_acceptance.py:310-318, test_us_c6_2_acceptance.py:104-105 (6 234);
- medie empiriche di log-loss: test_residuals.py:311-326 (abs 5e-7);
- allarmi esatti di river: test_drift.py:324-335;
- tassi Monte Carlo entro un intervallo: test_us_c2_acceptance.py, test_us_c5_2_acceptance.py:451-457, test_heteroskedasticity.py:302-305 (0.0322–0.0678 con seed fisso), test_floor.py:73, 82, 91 (μ con rel_tol 0.005);
- seed e tolleranze empiriche in test_us_c1_1, test_us_c1_2, test_simulate, test_estimation, test_timeseries, test_devig, test_drift, test_calibration (th1 != th3 dipende dai seed 12345 e 54321), test_environment, test_metrics, test_us_c6_3_real, test_us_c6_4.
pandas 3: Date esce in datetime64[us] [V, R10@2026-09-29]; le colonne di testo hanno di default il dtype stringa [D]
Branch pre-c4: toglie .agent/ dal tracciamento e lo aggiunge a .gitignore, contro il versionamento di .agent/ in vigore [V, R3@2026-10-07]. Non va unito senza decisione del programmatore [D]

## Punti ancora incerti
Esito della CI su 736f5cd, sulla PR di C5 e su C6 (statsmodels via .[dev], river, 135 test nuovi).
- Blocca: se la prossima story deve partire con una correzione della CI.
- Si procede: il programmatore apre la PR di C6 verso main e ne legge l'esito; il primo task della story successiva la mette fra le verifiche iniziali.
Seguito di C6.4 e premessa del Modulo 2 (varianza non costante nel tempo, non dimostrata da BP temporale).
- Blocca: la progettazione di C7–C8 e quali funzioni di residual_heteroskedasticity.py e heteroskedasticity.py andranno riusate.
- Si procede: nessun task di codice finché una chat di backlog non decide (alternative in BACKLOG.md, S6 "Resta aperto").
Versione del Modulo 1: raw, adottata in C5 e C6 su delega, senza conferma.
- Blocca: le probabilità del Modulo 1 di C8.
- Alternative: (a) raw, la migliore su B365; (b) Platt, marginalmente migliore su Pinnacle (0.980927 contro 0.981229); (c) isotonica, peggiore ovunque.
- Si procede con raw.
Imposizione di H₀ prima del block bootstrap, e scelta di L.
- Blocca: la chiusura di T12, la correzione della docstring di calibration.py e la L delle soglie calibrate di C8.
- Si procede lasciando il test rosso e senza toccare calibration.py né false_rejection.py; in C5.2 e C6.4 la soglia è calibrata sul training del fit, dove H₀ vale per costruzione, e in C6.4 i conteggi non dipendono da L [V i conteggi, R13; D il resto].
Scelte di S6 su delega, da confermare (semantica del floor, B0 = £220 con F = £0.01 e £1, esiti di T37 dalle q proporzionali, θ = 0.5 e 0.1, statistiche di C6.4).
- Blocca: l'Agente C, la variante del floor che salta le puntate sotto F e il riuso dell'ambiente in C8.
- Si procede: il codice le implementa come descritto in Moduli.
Lettura del 2023-24 da parte dello script C3.1 e di tests/test_data_loading.py:312.
- Blocca: l'affermazione in tesi (US-C3.3) che il test set non è mai stato letto.
- Alternative: (a) dichiararla come eccezione ammessa, limitata a copertura e caricamento; (b) un task che esclude le stagioni bloccate da script e test e rigenera il CSV di C3.1; (c) in più, estendere il test di guardia a tests/.
- Si procede: nessun task di C6 legge il test.
Prova del congelamento dello split.
- Blocca: la data da dichiarare in US-C3.3 e la conservazione di 2cea094, che dalla reflog può sparire verso il 2026-10-29.
- Alternative: (a) dichiarare 90a77a1, con contenuto identico; (b) un tag su 2cea094 pubblicato su origin dal programmatore; (c) affidarsi al ref del PR #17 su GitHub, non verificato.
- Si procede: nessun task di codice dipende dalla scelta.
Stagione di training 2000-01 senza B365.
- Blocca: gli esperimenti di C8 alimentati da quote B365 su quello scenario; in C3.2, nella calibrazione di κ e in C6 è escluso o non usato.
- Alternative: (a) dichiararlo e procedere con 2010-11 e 2020-21; (b) per il solo 2000-01 un'altra terna completa (GB, IW, SB o WH); (c) rivedere lo scenario in una chat di backlog.
- Si procede: le stagioni di validazione hanno tutte B365.
Versionamento dei CSV E0.
- Blocca: se la CI potrà mai verificare le pipeline su dati reali; decisione del programmatore dopo il controllo della licenza.
- Si procede: i test sui dati reali girano in locale.

## Ultimo aggiornamento
R15@2026-10-11 — task di scrittura chiusi dopo la mappa del 2026-10-11: nessuno