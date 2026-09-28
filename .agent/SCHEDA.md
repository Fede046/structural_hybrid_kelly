# Scheda del progetto
Origine: mappa del 2026-09-28, report fino a R2@2026-09-28

## Stato repo
Radice: c:\Users\malse\Documents\GitHub\structural_hybrid_kelly [V, R1@2026-09-28]
Branch corrente C2 a 1e7813d "C1 (#14)", allineato a origin/C2 rispetto all'ultimo fetch locale (nessun git fetch eseguito); main punta allo stesso commit 1e7813d [V, R1@2026-09-28]
Working tree al momento di R1: .agent/BACKLOG.md modificato (story S2, +250/−1), .agent/MAPPA.md modificato, C1.1.md cancellato; niente di staged, nessun file non tracciato [V, R1@2026-09-28]
La cancellazione di C1.1.md è del programmatore, non di un task, e non è committata [V, dichiarazione del programmatore 2026-09-28]
.agent/PROTOCOLLO.md è stato aggiunto dal programmatore dopo R2 [V, dichiarazione del programmatore 2026-09-28]; il suo stato in git (non tracciato, staged o committato) non è verificato [D]
Branch C1 a 362c739 (merge di main in C1); nella sua storia T6 = 9f6206c, T7 = 9cb04e9, poi e8f1bba "Document S1 completion and C1.2 closure" [V, R2@2026-09-28]
src, tests, scripts, results, thesis, pyproject.toml e .github sono identici fra C1 e HEAD [V, R2@2026-09-28]
Il contenuto dei commit 9cb04e9, e8f1bba e 362c739, successivi all'ultimo report del 2026-09-27 (R16), non è stato letto; per questo i fatti marcati "era V" più sotto sono [D] [V, R2@2026-09-28 per i commit]
Branch locale feature/US-C1.1-Trade-off-crescita/varianza a 1ff7301 [V, R1@2026-09-28]; probabile residuo della PR #4 [D]
Remote origin: https://github.com/Fede046/structural_hybrid_kelly.git [V, R1@2026-09-28]
File tracciati in .agent/ al momento di R2: BACKLOG.md, MAPPA.md, SCHEDA.md, report/T1.md … report/T7.md [V, R2@2026-09-28]

## Stack e comandi
Pacchetto structural-hybrid-kelly 0.1.0 (pyproject.toml e src/shk/__init__.py), importabile come shk, sorgenti in src/shk/ [V, R1@2026-09-28]
requires-python >=3.11; la CI usa Python 3.12 [V, R1@2026-09-28]
Build backend hatchling; build con hatch build o python -m build [D]
Dipendenze runtime numpy, scipy, matplotlib; dev solo pytest; nessun vincolo di versione [V, R1@2026-09-28]
uv.lock presente alla radice [V, R1@2026-09-28]; uv sync come alternativa locale [D]
Installazione usata dalla CI: pip install -e ".[dev]", senza uv.lock [V, R1@2026-09-28]
CI: .github/workflows/test.yml esegue pytest -v [V, R1@2026-09-28]; trigger su push verso main e su pull_request [D, era V R2@2026-09-27]
Test veloci: pytest -v; addopts = "-m 'not slow'" in pyproject.toml esclude i test slow [V, R1@2026-09-28]
Solo test slow: pytest -m slow [D, era V R4@2026-09-27]; tutti i test: pytest -o addopts="" [D]
Baseline: 44 test veloci e 9 slow (4 di accettazione C1.1, 5 di C1.2), tutti verdi [D, era V R14@2026-09-27]
Esperimenti: python scripts/us_c1_1_growth_vs_lambda.py e python scripts/us_c1_2_estimation_error.py dalla radice, con shk installato [D]
Lo script C1.2 dura circa 70 s e due esecuzioni danno CSV identici byte per byte [D, era V R16@2026-09-27]
Nessun .env presente; config/ e data/raw/ contengono solo .gitkeep [V, R1@2026-09-28, inventario git completo]
Nessuna variabile d'ambiente richiesta [D]

## Moduli e responsabilità
src/shk/__init__.py — espone __version__ [V, R1@2026-09-28]
src/shk/kelly/__init__.py — re-esporta kelly_fraction e log_growth_rate tramite __all__; expected_final_wealth non è re-esportata [V, R1@2026-09-28]
src/shk/kelly/core.py — formule chiuse per scommessa binaria: kelly_fraction(p, b), log_growth_rate(f, p, b), expected_final_wealth(f, p, b, T, b0=1.0) alle righe 97-144; nessun import interno [V, R1@2026-09-28]
src/shk/kelly/core.py — kelly_fraction calcola (b·p − q)/b, restituisce 0.0 se ≤ 0, accetta solo scalari [D, era V R7@2026-09-27]
src/shk/kelly/simulate.py — draw_outcomes(p, T, M, rng) → (M, T) bool, True = vincita; simulate_growth(outcomes, fractions, b) → log-wealth (M, T+1) float64 con colonna 0 nulla, frazioni broadcastabili da (), (T,), (1, T), (M, 1), (M, T), rifiuta frazioni fuori da [0, 1); log_wealth_paths(outcomes, f, b) delega a simulate_growth; nessun import interno [V, R1@2026-09-28]
src/shk/kelly/simulate.py — fattori logaritmici np.log(1 + b*f) e np.log(1 - f), senza log1p (righe 142-143) [D, era V R5@2026-09-27]
src/shk/kelly/estimation.py — relative_perturbation(p, delta) e noisy_estimates(p, sigma_p, T, M, rng): stime saturate in [0, 1] con np.clip; nessun import interno [V, R1@2026-09-28]
src/shk/kelly/staking.py — kelly_staking(p_hat, b, lam=1.0), StakingMoments (NamedTuple: mean_c, mean_c2, var_c, fraction_zero), staking_moments(f_hat, f_star), plugin_staking(p_hat, b, sigma_p); non importa core.py [V, R1@2026-09-28]
src/shk/kelly/staking.py — kelly_staking = lam·max(0, (b·p_hat − (1 − p_hat))/b), senza limite superiore su lam e sulla frazione; plugin_staking = λ_t·kelly_staking(p_hat, b) con λ_t = 1/(1 + (o·sigma_p/EV̂)²), o = b + 1, EV̂ = p_hat·o − 1, e 0.0 dove EV̂ ≤ 0 [D, era V R8@2026-09-27 e R14@2026-09-27]
src/shk/kelly/scenarios.py — dataclass frozen Scenario(name, p, b, T, M); BASE_SCENARIO (0.60, 1.0, 1000, 10000), SUBTLE_SCENARIO (0.52, 1.0, 380, 10000); SEED = 20260927; spawn_generators(seed=SEED); draw_scenario_outcomes(scenario, rng); simulate_scenario(scenario, outcomes, p_hat, lam=1.0); importa simulate.py e staking.py [V, R1@2026-09-28]
src/shk/kelly/scenarios.py — spawn_generators restituisce due generatori da SeedSequence.spawn(2), il primo per gli esiti e il secondo per il rumore di stima [D, era V R10@2026-09-27]
src/shk/kelly/metrics.py — su paths: final_log_wealth, median_growth_rate, median_final_wealth, mean_final_wealth, max_drawdown ((M,) in [0, 1)), fraction_below_start; nessun import interno [V, R1@2026-09-28]
src/shk/kelly/metrics.py — median_growth_rate = mediana di ln(B_T/B_0)/T con T = paths.shape[1] − 1; il drawdown mediano si calcola con np.median(max_drawdown(paths)); fraction_below_start = quota con B_T < B_0 [D, era V R9@2026-09-27 e R13@2026-09-27]
Classi del pacchetto: Scenario e StakingMoments [V, R1@2026-09-28]; nessun'altra [D]
Persistenza: solo CSV in results/ e PNG in thesis/figures/ [V, R1@2026-09-28]; nessun database [D]
src/shk/stats/ non esiste; non esistono tests/test_anova.py, tests/test_timeseries.py, tests/test_calibration.py, tests/test_us_c2_acceptance.py né scripts/us_c2_* [V, R1@2026-09-28, inventario git completo e nessun file non tracciato]

## Flussi principali
Esperimento C1.1 (scripts/us_c1_1_growth_vs_lambda.py, run_experiment() dal blocco __main__): parametri locali p=0.60, b=1.0, T=1000, M=10000, seed 20260905, 51 valori di λ in [0, 2.5] (righe 30-36) [V, R1@2026-09-28]
Esperimento C1.1, sequenza: f* con kelly_fraction; una sola matrice di esiti con draw_outcomes; per ogni λ log_wealth_paths, cinque metriche empiriche, del paths, benchmark con log_growth_rate ed expected_final_wealth [V, R1@2026-09-28]
Esperimento C1.1: la frazione passata a log_wealth_paths è λ·f* [D]
Esperimento C1.1, output: results/us_c1_1_growth_vs_lambda.csv (10 colonne) e thesis/figures/us_c1_1_growth_vs_lambda.png (tre pannelli) [V, R1@2026-09-28]
Esperimento C1.1, colonne del CSV: lambda, f, median_growth_rate, analytic_growth_rate, median_final_wealth, mean_final_wealth_mc, mean_final_wealth_analytic, drawdown_median, drawdown_p95, fraction_below_start [D, era V R1@2026-09-27]
Accettazione C1.1: tests/test_us_c1_1_acceptance.py, tutto @pytest.mark.slow, parametri ripetuti a mano, esiti rigenerati in ogni test con seed 20260905; asserzioni: picco della mediana a λ=1.0, drawdown mediano non decrescente con tolleranza −0.01, |g mediano| < 0.002 a λ=1.946, crescita negativa a λ=2.5 [V, R1@2026-09-28]
Esperimento C1.2 (scripts/us_c1_2_estimation_error.py, run_experiment()): scenari e SEED da scenarios.py; per ogni combinazione spawn_generators(SEED), esiti con draw_scenario_outcomes, errore deterministico ±10% con relative_perturbation, e per σ_p ∈ {0.015, 0.0283, 0.045} p̂ da noisy_estimates, f̂ da kelly_staking con lam=1, momenti da staking_moments, regole lambda_star, ratio_moments, lambda_linear, quarter_kelly, half_kelly, full_kelly, plugin [V, R1@2026-09-28]
Esperimento C1.2, output: results/us_c1_2_estimation_error.csv (12 colonne, 46 righe = 2 scenari × (2 + 3 × 7)) e thesis/figures/us_c1_2_estimation_error.png (due pannelli) [V, R1@2026-09-28; conteggio righe ricalcolato dal supervisore]
Esperimento C1.2, CSV: colonne scenario, sigma_p, rule, lambda, mean_c, mean_c2, var_c_empirical, var_c_linear, fraction_f_hat_zero, median_growth_rate, median_drawdown, fraction_below_start; regole deterministiche overestimation_10pct e underestimation_10pct; float nativi e stringa vuota per i non applicabili [D, era V R16@2026-09-27]
Accettazione C1.2: tests/test_us_c1_2_acceptance.py importa scenari e SEED da scenarios.py; i test veloci verificano esiti indipendenti da p̂ e matrice esiti non modificata; i test slow verificano asimmetria ±10% nello scenario sottile, Var(c) con σ_p = 0.0283 (base entro 0.005 dal riferimento, confronto con 1) e λ* contro λ = 0.25 [V, R1@2026-09-28]
Uso come libreria: from shk.kelly import kelly_fraction, log_growth_rate; expected_final_wealth solo da shk.kelly.core [V, R1@2026-09-28]
Valori analitici (p=0.6, b=1): f*=0.2; g(0.2)=0.020136; g(0.4)=−0.002447; g(0.5)≈−0.0340; zero di g a f≈0.3894, cioè λ≈1.9470; una vincita in più o in meno su T=1000 sposta la crescita mediana di circa 0.0008 [D, ricalcolo del supervisore]
Le costanti di tests/test_kelly_core.py:32 e :39 e il λ=1.946 dell'accettazione C1.1 sono valori analitici, non empirici [D, ricalcolo del supervisore]
Var(c) attesa a σ_p = 0.0283: circa 0.080 nello scenario base, circa 1.28 in quello sottile (troncamento a zero incluso) [D, ricalcolo del supervisore]

## Convenzioni da rispettare
Naming: snake_case per moduli, funzioni e variabili; PascalCase per le classi; UPPER_CASE per le costanti; lettere matematiche standard (p, b, f, T, M, b0, λ, σ_p, c, δ) [V, R1@2026-09-28]
Lingua: identificatori, nomi dei test e messaggi di eccezione in inglese; commenti e docstring in italiano [V, R1@2026-09-28]
Type hints completi su argomenti e ritorni; docstring stile NumPy con sezioni Parametri / Restituisce / Solleva [V, R1@2026-09-28]
Validazione in apertura di funzione: ValueError per i valori, TypeError per i tipi (anche per un rng che non sia np.random.Generator) [V, R1@2026-09-28]
Nessuna occorrenza di try:, print( o logging in src/ e scripts/ [V, R2@2026-09-28]
L'RNG entra come argomento, mai creato dentro le funzioni di libreria; flussi indipendenti con np.random.SeedSequence.spawn [V, R1@2026-09-28 per spawn; D, era V R5@2026-09-27 e R6@2026-09-27 per il resto]
Vettorizzazione NumPy senza cicli su M e T nel motore; del paths nei loop Monte Carlo [V, R1@2026-09-28]
Script di esperimento: matplotlib.use("Agg") in apertura, run_experiment() chiamata dal blocco __main__ [V, R1@2026-09-28]; nessun argomento da riga di comando [D, era V R2@2026-09-27]
Parametri condivisi fra script e test in un modulo di libreria importato da entrambi, come scenarios.py per C1.2; C1.1 è l'eccezione storica [V, R1@2026-09-28]
Nomi: scripts/us_<storia>_<descrizione>.py, con lo stesso nome base per results/<nome>.csv e thesis/figures/<nome>.png, entrambi versionati [V, R1@2026-09-28]
Test in tests/test_*.py; i Monte Carlo su larga scala si marcano @pytest.mark.slow [V, R1@2026-09-28]
Commit fatti solo dal programmatore, a mano; Cline scrive in .agent/ solo MAPPA.md in mappatura e report/T<N>.md in esecuzione [V, testo di .agent/PROTOCOLLO.md fornito dal programmatore 2026-09-28]
.agent/PROTOCOLLO.md, sezione "Convenzioni del progetto": nessuna convenzione aggiuntiva per questo progetto; valgono le regole di base dei prompt e quelle di questa sezione [V, testo di .agent/PROTOCOLLO.md fornito dal programmatore 2026-09-28]
Documenti di processo in .agent/: PROTOCOLLO.md, BACKLOG.md, MAPPA.md, SCHEDA.md, report/T<n>.md [V, R2@2026-09-28 e dichiarazione del programmatore 2026-09-28]
Nessun documento di storia alla radice: C1.1.md è stato cancellato dal programmatore [V, dichiarazione del programmatore 2026-09-28]

## Zone fragili da non toccare senza avviso
noisy_estimates può restituire p̂ = 1 per saturazione; kelly_staking dà allora lam·1, e con lam ≥ 1 la frazione è ≥ 1, che simulate_growth rifiuta con ValueError [V, R1@2026-09-28]. Con p ≤ 0.6 e σ_p ≤ 0.045 l'evento dista almeno 8.9 deviazioni standard [D, ricalcolo del supervisore]
expected_final_wealth (core.py:97-144) è usata dallo script C1.1 [V, R1@2026-09-28] e non ha test [D, era V R2@2026-09-27: 0 occorrenze in tests/]
Parametri di C1.1 duplicati fra scripts/us_c1_1_growth_vs_lambda.py:30-36 e tests/test_us_c1_1_acceptance.py: cambiarli da una parte sola disallinea esperimento e verifica [V, R1@2026-09-28]
I test slow non girano in CI: dopo modifiche a simulate.py, staking.py, scenarios.py o metrics.py vanno lanciati a mano [V, R1@2026-09-28]
Rieseguire uno script di esperimento sovrascrive CSV e PNG versionati: ogni task che rigenera un esperimento deve dire se committarli [V, R1@2026-09-28]
Dipendenze senza vincolo di versione e CI che installa con pip ignorando uv.lock [V, R1@2026-09-28]; NumPy non garantisce la stabilità del flusso di Generator fra versioni, e i test con tolleranze empiriche possono rompersi [D]
tests/test_metrics.py:test_metrics_error_conditions non verifica il ValueError di median_final_wealth e mean_final_wealth [V, R1@2026-09-28]
Il test del drawdown non decrescente (tolleranza −0.01) è l'unica asserzione di accettazione C1.1 di cui non si è stimata la robustezza al seed e alla versione di NumPy [D]

## Punti ancora incerti
Gestore canonico delle dipendenze (pip + pyproject oppure uv + uv.lock), non deciso dal programmatore. Blocca: se un task che aggiunge o fissa una dipendenza debba rigenerare uv.lock e se la CI vada migrata a uv. Si procede con pyproject.toml come fonte di verità, l'unica verificata dalla CI; un task che tocca le dipendenze modifica pyproject.toml e segnala uv.lock come da aggiornare. S2 non aggiunge dipendenze.

## Ultimo aggiornamento
R2@2026-09-28 — task di scrittura chiusi dopo la mappa del 2026-09-28: nessuno