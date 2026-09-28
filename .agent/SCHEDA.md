Ecco il file SCHEDA.md aggiornato in base alle tue indicazioni:

# Scheda del progetto

Origine: mappa del 2026-09-28, report fino a R2@2026-09-28

## Stato repo

Radice: c:\Users\malse\Documents\GitHub\structural_hybrid_kelly [V, R1@2026-09-28]
Branch corrente C2 a 1e7813d "C1 (#14)", allineato a origin/C2 rispetto all'ultimo fetch locale (nessun git fetch eseguito); main punta allo stesso commit 1e7813d [V, R1@2026-09-28]
Working tree al momento di R1: .agent/BACKLOG.md modificato (story S2, +250/−1), .agent/MAPPA.md modificato, C1.1.md cancellato; niente di staged, nessun file non tracciato [V, R1@2026-09-28]. Dopo T8–T10 si aggiungono, non tracciati salvo commit del programmatore: src/shk/stats/**init**.py, anova.py, timeseries.py, false_rejection.py; scripts/us_c2_anova_autocorrelation.py; tests/test_anova.py, test_timeseries.py, test_us_c2_acceptance.py; results/us_c2_anova_autocorrelation.csv; thesis/figures/us_c2_anova_autocorrelation.png; .agent/report/T8.md … T10.md; esiste .venv/ nella radice [V, R7@2026-09-28], se sia ignorato da git non è verificato; stato attuale del working tree non verificato [D]
La cancellazione di C1.1.md è del programmatore, non di un task, e non è committata [V, dichiarazione del programmatore 2026-09-28]
.agent/PROTOCOLLO.md è stato aggiunto dal programmatore dopo R2 [V, dichiarazione del programmatore 2026-09-28]; il suo stato in git (non tracciato, staged o committato) non è verificato [D]
Branch C1 a 362c739 (merge di main in C1); nella sua storia T6 = 9f6206c, T7 = 9cb04e9, poi e8f1bba "Document S1 completion and C1.2 closure" [V, R2@2026-09-28]
src, tests, scripts, results, thesis, pyproject.toml e .github sono identici fra C1 e HEAD [V, R2@2026-09-28]
Il contenuto dei commit 9cb04e9, e8f1bba e 362c739, successivi all'ultimo report del 2026-09-27 (R16), non è stato letto; per questo i fatti marcati "era V" più sotto sono [D] [V, R2@2026-09-28 per i commit]
Branch locale feature/US-C1.1-Trade-off-crescita/varianza a 1ff7301 [V, R1@2026-09-28]; probabile residuo della PR #4 [D]
Remote origin: [https://github.com/Fede046/structural_hybrid_kelly.git](https://www.google.com/search?q=https://github.com/Fede046/structural_hybrid_kelly.git&utm_source=gemini) [V, R1@2026-09-28]
File tracciati in .agent/ al momento di R2: BACKLOG.md, MAPPA.md, SCHEDA.md, report/T1.md … report/T7.md [V, R2@2026-09-28]

## Stack e comandi

Pacchetto structural-hybrid-kelly 0.1.0 (pyproject.toml e src/shk/**init**.py), importabile come shk, sorgenti in src/shk/ [V, R1@2026-09-28]
requires-python >=3.11; la CI usa Python 3.12 [V, R1@2026-09-28]
Build backend hatchling; build con hatch build o python -m build [D]
Dipendenze runtime numpy, scipy, matplotlib; dev solo pytest; nessun vincolo di versione [V, R1@2026-09-28]
uv.lock presente alla radice [V, R1@2026-09-28]; uv sync come alternativa locale [D]
Installazione usata dalla CI: pip install -e ".[dev]", senza uv.lock [V, R1@2026-09-28]
CI: .github/workflows/test.yml esegue pytest -v [V, R1@2026-09-28]; trigger su push verso main e su pull_request [D, era V R2@2026-09-27]
Test veloci: pytest -v; addopts = "-m 'not slow'" in pyproject.toml esclude i test slow [V, R1@2026-09-28]. Cline esegue ogni comando Python con l'interprete del venv, esplicitamente: ..venv\Scripts\python.exe -m pytest -v, ..venv\Scripts\python.exe  [V, R7@2026-09-28; decisione del programmatore 2026-09-28]. Nel venv shk è installato in modalità editable [V, R7@2026-09-28]. Il terminale di Cline usa di default C:\Users\malse\anaconda3\python.exe (Python 3.12.7, pytest 7.4.4), dove shk non è installato [V, R6@2026-09-28]
Venv del progetto .venv: Python 3.12.7, pytest 9.1.1, NumPy 2.5.2 [V, R7@2026-09-28]
Solo test slow: pytest -m slow [D, era V R4@2026-09-27]; tutti i test: pytest -o addopts="" [D]
Baseline dopo T10: 90 test veloci (44 preesistenti + 23 in tests/test_anova.py + 13 in tests/test_timeseries.py + 10 in tests/test_us_c2_acceptance.py), tutti verdi nel venv, e 9 slow deselezionati [V, R9@2026-09-28]; test slow non rieseguiti dopo la mappa, verdi all'ultima esecuzione nota [D, era V R14@2026-09-27]
Esperimento C2: ..venv\Scripts\python.exe scripts\us_c2_anova_autocorrelation.py dalla radice, circa 3–3.5 s; due esecuzioni danno CSV identici byte per byte, SHA256 F03139516E5482BCAD698EEA76A7903DC3A3FE4DA3BC905950FE8072A7FC5B77 [V, R9@2026-09-28]
Esperimenti: ..venv\Scripts\python.exe scripts/us_c1_1_growth_vs_lambda.py e ..venv\Scripts\python.exe scripts/us_c1_2_estimation_error.py dalla radice [D]
Lo script C1.2 dura circa 70 s e due esecuzioni danno CSV identici byte per byte [D, era V R16@2026-09-27]
Nessun .env presente; config/ e data/raw/ contengono solo .gitkeep [V, R1@2026-09-28, inventario git completo]
Nessuna variabile d'ambiente richiesta [D]

## Moduli e responsabilità

src/shk/**init**.py — espone **version** [V, R1@2026-09-28]
src/shk/kelly/**init**.py — re-esporta kelly_fraction e log_growth_rate tramite **all**; expected_final_wealth non è re-esportata [V, R1@2026-09-28]
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
src/shk/stats/**init**.py — sola docstring di modulo in italiano, nessun import, nessuna re-esportazione, nessun **all** [V, R5@2026-09-28]
src/shk/stats/anova.py — OneWayAnovaResult (NamedTuple: ss_between, ss_within, ss_total, df_between, df_within, ms_between, ms_within, f_statistic, p_value); oneway_anova(groups) → OneWayAnovaResult, p-value con scipy.stats.f.sf; oneway_anova_vectorized(values, labels) → float se values è 1D, altrimenti ndarray di forma values.shape[:-1]; values e labels devono essere np.ndarray (TypeError), etichette intere 0..k−1 tutte presenti [V, R4@2026-09-28, test verdi]; medie di gruppo via matrice di incidenza, nessun ciclo sulle serie [D, piano R3]
src/shk/stats/timeseries.py — generate_ar1_series(phi, n, m, rng) → ndarray float64 di forma (m, n), righe = serie, colonne = tempo; estrazioni nell'ordine: x_0 ~ N(0, 1/(1 − φ²)) con size=m, poi innovazioni N(0, 1) in un blocco (m, n − 1); ciclo solo sul tempo; ValueError per φ non finito o |φ| ≥ 1, n < 2, m < 1; TypeError per n o m bool o non interi e per rng non Generator; interi NumPy accettati [V, R7@2026-09-28, test verdi; ordine delle estrazioni confermato dal ricalcolo del supervisore, identico a 15 cifre]
src/shk/stats/false_rejection.py — costanti PHI_VALUES = (0.0, 0.3, 0.5, 0.7), N_OBS = 380, N_SERIES = 1000, ALPHA = 0.05, SEED_C2 = 20260928, DESIGN_CONTIGUOUS_2 / DESIGN_CONTIGUOUS_38 / DESIGN_RANDOM_2 e DESIGNS in quest'ordine, CSV_COLUMNS (10 colonne); RejectionResult (dataclass frozen: design, phi, method, block_length, n_series, rejections, rejection_rate, critical_value_mean, mc_lower_99, mc_upper_99); PhiStreams (NamedTuple: series_rng, perm_rng, boot_seed come SeedSequence non usata); spawn_c2_generators(seed=SEED_C2) → tupla ordinata come PHI_VALUES; make_design_labels(design, n_obs=N_OBS) (random_2 → etichette di contiguous_2; disegno sconosciuto → ValueError); critical_value_nominal(k, n_obs, alpha); monte_carlo_interval_99(alpha, n_series); compute_nominal_rejection_rates(seed=SEED_C2) → 12 RejectionResult in ordine DESIGNS × PHI_VALUES, una sola chiamata a generate_ar1_series per φ, importata con from shk.stats.timeseries import generate_ar1_series; random_2 permuta ogni serie in sequenza con perm_rng.permutation(N_OBS) e np.take_along_axis [V, R9@2026-09-28, test verdi e 12 conteggi riprodotti dal supervisore; firme come da piano R8 approvato, D per i dettagli non testati]
scripts/us_c2_anova_autocorrelation.py — run_experiment() senza parametri; scrive il CSV con csv.DictWriter e CSV_COLUMNS, e il PNG con plt.subplots(1, 2): pannello A (tasso contro φ per i tre disegni, linea ad ALPHA, banda al 99%), pannello B nascosto con set_visible(False); etichette in italiano; savefig(dpi=150) [V, R9@2026-09-28 per esistenza e output; D per i dettagli del codice, piano R8]
tests/test_anova.py — 23 test veloci: toy, concordanza con f_oneway su toy e 3 dataset casuali, partizione della devianza, vettorizzata su (3, 4, 380) con contiguous_2 e k = 5 permutato, validazioni [V, R4@2026-09-28]
tests/test_timeseries.py — 13 test veloci: forma e dtype, riproducibilità, varianze e autocorrelazione pooled parametrizzate su φ ∈ {0.0, 0.3, 0.7} con seed 20260928, validazioni [V, R7@2026-09-28]
tests/test_us_c2_acceptance.py — 10 test veloci (3.67 s): criteri 1–3 su contiguous_2, conteggio delle chiamate a generate_ar1_series con monkeypatch, stesse serie per tutti i disegni con flussi ricostruiti da SeedSequence(SEED_C2), CSV confrontato campo per campo con compute_nominal_rejection_rates, esistenza del PNG, disegno sconosciuto [V, R9@2026-09-28]
Classi del pacchetto: Scenario, StakingMoments [V, R1@2026-09-28] e OneWayAnovaResult [V, R4@2026-09-28]; nessun'altra [D]
Persistenza: solo CSV in results/ e PNG in thesis/figures/ [V, R1@2026-09-28]; nessun database [D]
Non esistono src/shk/stats/calibration.py né tests/test_calibration.py [V, R1@2026-09-28; T8–T10 non li hanno creati, R4, R7 e R9@2026-09-28]

## Flussi principali

Esperimento C1.1 (scripts/us_c1_1_growth_vs_lambda.py, run_experiment() dal blocco **main**): parametri locali p=0.60, b=1.0, T=1000, M=10000, seed 20260905, 51 valori di λ in [0, 2.5] (righe 30-36) [V, R1@2026-09-28]
Esperimento C1.1, sequenza: f* con kelly_fraction; una sola matrice di esiti con draw_outcomes; per ogni λ log_wealth_paths, cinque metriche empiriche, del paths, benchmark con log_growth_rate ed expected_final_wealth [V, R1@2026-09-28]
Esperimento C1.1: la frazione passata a log_wealth_paths è λ·f* [D]
Esperimento C1.1, output: results/us_c1_1_growth_vs_lambda.csv (10 colonne) e thesis/figures/us_c1_1_growth_vs_lambda.png (tre pannelli) [V, R1@2026-09-28]
Esperimento C1.1, colonne del CSV: lambda, f, median_growth_rate, analytic_growth_rate, median_final_wealth, mean_final_wealth_mc, mean_final_wealth_analytic, drawdown_median, drawdown_p95, fraction_below_start [D, era V R1@2026-09-27]
Accettazione C1.1: tests/test_us_c1_1_acceptance.py, tutto @pytest.mark.slow, parametri ripetuti a mano, esiti rigenerati in ogni test con seed 20260905; asserzioni: picco della mediana a λ=1.0, drawdown mediano non decrescente con tolleranza −0.01, |g mediano| < 0.002 a λ=1.946, crescita negativa a λ=2.5 [V, R1@2026-09-28]
Esperimento C1.2 (scripts/us_c1_2_estimation_error.py, run_experiment()): scenari e SEED da scenarios.py; per ogni combinazione spawn_generators(SEED), esiti con draw_scenario_outcomes, errore deterministico ±10% con relative_perturbation, e per σ_p ∈ {0.015, 0.0283, 0.045} p̂ da noisy_estimates, f̂ da kelly_staking con lam=1, momenti da staking_moments, regole lambda_star, ratio_moments, lambda_linear, quarter_kelly, half_kelly, full_kelly, plugin [V, R1@2026-09-28]
Esperimento C1.2, output: results/us_c1_2_estimation_error.csv (12 colonne, 46 righe = 2 scenari × (2 + 3 × 7)) e thesis/figures/us_c1_2_estimation_error.png (due pannelli) [V, R1@2026-09-28; conteggio righe ricalcolato dal supervisore]
Esperimento C1.2, CSV: colonne scenario, sigma_p, rule, lambda, mean_c, mean_c2, var_c_empirical, var_c_linear, fraction_f_hat_zero, median_growth_rate, median_drawdown, fraction_below_start; float nativi e stringa vuota per i non applicabili [V, R8@2026-09-28]; regole deterministiche overestimation_10pct e underestimation_10pct [D, era V R16@2026-09-27]
Accettazione C1.2: tests/test_us_c1_2_acceptance.py importa scenari e SEED da scenarios.py; i test veloci verificano esiti indipendenti da p̂ e matrice esiti non modificata; i test slow verificano asimmetria ±10% nello scenario sottile, Var(c) con σ_p = 0.0283 (base entro 0.005 dal riferimento, confronto con 1) e λ* contro λ = 0.25 [V, R1@2026-09-28]
Esperimento C2 nominale: results/us_c2_anova_autocorrelation.csv, 12 righe method = nominal in ordine DESIGNS × PHI_VALUES; rigetti su 1000 serie per φ = 0.0, 0.3, 0.5, 0.7: contiguous_2 37, 149, 253, 399; contiguous_38 44, 843, 999, 1000; random_2 58, 35, 48, 45; intervallo al 99% [0.0322461452073078, 0.0677538547926922]; valori critici 3.866176954321902 (k = 2) e 1.445838076487165 (k = 38) [V, R9@2026-09-28 e ricalcolo del supervisore]
Uso come libreria: from shk.kelly import kelly_fraction, log_growth_rate; expected_final_wealth solo da shk.kelly.core [V, R1@2026-09-28]
Valori analitici (p=0.6, b=1): f*=0.2; g(0.2)=0.020136; g(0.4)=−0.002447; g(0.5)≈−0.0340; zero di g a f≈0.3894, cioè λ≈1.9470; una vincita in più o in meno su T=1000 sposta la crescita mediana di circa 0.0008 [D, ricalcolo del supervisore]
Le costanti di tests/test_kelly_core.py:32 e :39 e il λ=1.946 dell'accettazione C1.1 sono valori analitici, non empirici [D, ricalcolo del supervisore]
Var(c) attesa a σ_p = 0.0283: circa 0.080 nello scenario base, circa 1.28 in quello sottile (troncamento a zero incluso) [D, ricalcolo del supervisore]

## Convenzioni da rispettare

Naming: snake_case per moduli, funzioni e variabili; PascalCase per le classi; UPPER_CASE per le costanti; lettere matematiche standard (p, b, f, T, M, b0, λ, σ_p, c, δ) [V, R1@2026-09-28]
Lingua: identificatori, nomi dei test e messaggi di eccezione in inglese; commenti e docstring in italiano [V, R1@2026-09-28]
Type hints completi su argomenti e ritorni; docstring stile NumPy con sezioni Parametri / Restituisce / Solleva [V, R1@2026-09-28]
Validazione in apertura di funzione: ValueError per i valori, TypeError per i tipi; rng controllato con isinstance(rng, np.random.Generator) → TypeError [V, R5@2026-09-28]. Eccezione nel codice esistente: draw_outcomes e noisy_estimates non controllano il tipo di T e M (2.5 fallisce solo dentro NumPy con TypeError, True è accettato come 1) [V, R5@2026-09-28]. Il codice nuovo controlla anche il tipo degli interi (bool e non interi → TypeError), come generate_ar1_series [V, R7@2026-09-28]
Nessuna occorrenza di try:, print( o logging nei file tracciati di src/ e scripts/ [V, R4@2026-09-28, git grep], in src/shk/stats/**init**.py e anova.py [V, R5@2026-09-28] e in src/shk/stats/timeseries.py [V, R8@2026-09-28]; src/shk/stats/false_rejection.py e scripts/us_c2_anova_autocorrelation.py non controllati [D]
L'RNG entra come argomento, mai creato dentro le funzioni di libreria; flussi indipendenti con np.random.SeedSequence.spawn [V, R1@2026-09-28 per spawn; D, era V R5@2026-09-27 e R6@2026-09-27 per il resto]
Vettorizzazione NumPy senza cicli su M e T nel motore; del paths nei loop Monte Carlo [V, R1@2026-09-28]
Script di esperimento: matplotlib.use("Agg") prima di importare pyplot, run_experiment() senza parametri chiamata dal blocco **main**, nessun argomento da riga di comando, import diretti da shk..; CSV con csv.DictWriter, open(mode="w", newline="", encoding="utf-8"), lineterminator di default (\r\n), float nativi e stringa vuota per i non applicabili; PNG con plt.tight_layout() e savefig(dpi=150); etichette delle figure in italiano [V, R8@2026-09-28 su us_c1_2_estimation_error.py; R9@2026-09-28 per la lingua]
Parametri condivisi fra script e test in un modulo di libreria importato da entrambi, come scenarios.py per C1.2; C1.1 è l'eccezione storica [V, R1@2026-09-28]
Nomi: scripts/us_.py, con lo stesso nome base per results/.csv e thesis/figures/.png, entrambi versionati [V, R1@2026-09-28]
Test in tests/test*.py; i Monte Carlo su larga scala si marcano @pytest.mark.slow [V, R1@2026-09-28]
Commit fatti solo dal programmatore, a mano; Cline scrive in .agent/ solo MAPPA.md in mappatura e report/T.md in esecuzione [V, testo di .agent/PROTOCOLLO.md fornito dal programmatore 2026-09-28]
.agent/PROTOCOLLO.md, sezione "Convenzioni del progetto": nessuna convenzione aggiuntiva per questo progetto; valgono le regole di base dei prompt e quelle di questa sezione [V, testo di .agent/PROTOCOLLO.md fornito dal programmatore 2026-09-28]
Documenti di processo in .agent/: PROTOCOLLO.md, BACKLOG.md, MAPPA.md, SCHEDA.md, report/T.md [V, R2@2026-09-28 e dichiarazione del programmatore 2026-09-28]
Nessun documento di storia alla radice: C1.1.md è stato cancellato dal programmatore [V, dichiarazione del programmatore 2026-09-28]

## Zone fragili da non toccare senza avviso

noisy_estimates può restituire p̂ = 1 per saturazione; kelly_staking dà allora lam·1, e con lam ≥ 1 la frazione è ≥ 1, che simulate_growth rifiuta con ValueError [V, R1@2026-09-28]. Con p ≤ 0.6 e σ_p ≤ 0.045 l'evento dista almeno 8.9 deviazioni standard [D, ricalcolo del supervisore]
expected_final_wealth (core.py:97-144) è usata dallo script C1.1 [V, R1@2026-09-28] e non ha test [D, era V R2@2026-09-27: 0 occorrenze in tests/]
Parametri di C1.1 duplicati fra scripts/us_c1_1_growth_vs_lambda.py:30-36 e tests/test_us_c1_1_acceptance.py: cambiarli da una parte sola disallinea esperimento e verifica [V, R1@2026-09-28]
I test slow non girano in CI: dopo modifiche a simulate.py, staking.py, scenarios.py o metrics.py vanno lanciati a mano [V, R1@2026-09-28]
Rieseguire uno script di esperimento sovrascrive CSV e PNG versionati: ogni task che rigenera un esperimento deve dire se committarli [V, R1@2026-09-28]
Dipendenze senza vincolo di versione e CI che installa con pip ignorando uv.lock [V, R1@2026-09-28]; NumPy non garantisce la stabilità del flusso di Generator fra versioni, e i test con tolleranze empiriche possono rompersi [D]. Per default_rng(20260928).normal il flusso dà valori identici a 15 cifre con NumPy 2.4.4 e 2.5.2 [V, R7@2026-09-28 e ricalcolo del supervisore]
tests/test_metrics.py:test_metrics_error_conditions non verifica il ValueError di median_final_wealth e mean_final_wealth [V, R1@2026-09-28]
Il test del drawdown non decrescente (tolleranza −0.01) è l'unica asserzione di accettazione C1.1 di cui non si è stimata la robustezza al seed e alla versione di NumPy [D]
tests/test_us_c2_acceptance.py confronta il CSV versionato con compute_nominal_rejection_rates: ogni modifica a false_rejection.py che cambia i risultati richiede di rieseguire lo script prima dei test, altrimenti il test del CSV fallisce [D, dal piano approvato R8]
L'identità byte per byte del CSV C2 dipende anche dalla versione di scipy: il valore critico per k = 2 è 3.866176954321902 nel venv e 3.866176954321901 nell'ambiente del supervisore [V, R9@2026-09-28 e ricalcolo del supervisore]

## Punti ancora incerti

Gestore canonico delle dipendenze (pip + pyproject oppure uv + uv.lock), non deciso dal programmatore. Blocca: se un task che aggiunge o fissa una dipendenza debba rigenerare uv.lock e se la CI vada migrata a uv. Si procede con pyproject.toml come fonte di verità, l'unica verificata dalla CI; un task che tocca le dipendenze modifica pyproject.toml e segnala uv.lock come da aggiornare. S2 non aggiunge dipendenze.

## Ultimo aggiornamento

R9@2026-09-28 — task di scrittura chiusi dopo la mappa del 2026-09-28: T8, T9, T10