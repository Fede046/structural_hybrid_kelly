# Backlog
Ultimo task: T12

## Decisioni in vigore
- Scenario base: p = 0.60, b = 1.0 (quota 2.00), T = 1000, M = 10000, lo stesso di C1.1 — S1, 2026-09-27
- Scenario sottile: p = 0.52, b = 1.0 (quota 2.00), T = 380 (una stagione), M = 10000; rappresenta l'edge sottile compatibile con Ω ≈ 5.3% (note di tesi 2.5 §7.2). Scelta del supervisore, non ancora confermata dal programmatore — S1, 2026-09-27
- Gli scenari si definiscono solo in src/shk/kelly/scenarios.py (BASE_SCENARIO, SUBTLE_SCENARIO); test e script li importano, non li ripetono — S1, 2026-09-27
- Seed: SEED = 20260927 in scenarios.py; spawn_generators(SEED) dà due generatori indipendenti, il primo per gli esiti e il secondo per il rumore di stima; una coppia nuova per ogni combinazione di scenario e σ_p, e confronti sempre appaiati (stessi esiti e stesse stime per tutte le regole) — S1, 2026-09-27
- Errore di stima: p̂ diverso per ogni scommessa, p̂ = p + rumore gaussiano con deviazione standard σ_p, saturato in [0, 1]; valori di riferimento σ_p ∈ {0.015, 0.0283, 0.045} (note di tesi 2.5 §3.3 e 3.2 §7) — S1, 2026-09-27
- Frazione stimata f̂ = max(0, p̂ − (1 − p̂)/b), cioè troncata a zero; c = f̂/f*, con f* calcolata sul p vero — S1, 2026-09-27
- "L'errore di stima domina il segnale" significa Var(c) > 1 — S1, 2026-09-27
- Var(c), E[c] ed E[c²] si stimano in forma pooled su tutte le scommesse simulate, mai per singola scommessa (note di tesi 3.2 §7.5) — S1, 2026-09-27
- Il λ fisso di riferimento è il quarto-Kelly, λ = 0.25 — S1, 2026-09-27
- Metriche primarie: crescita mediana per scommessa (median_growth_rate), drawdown mediano (np.median(max_drawdown(paths))), quota di traiettorie sotto il capitale iniziale (fraction_below_start) — S1, 2026-09-27
- Il motore simulate_growth riceve le frazioni dall'esterno e non conosce p né p̂; ogni regola di staking sta in src/shk/kelly/staking.py. Le regole non limitano la frazione sotto 1: una frazione ≥ 1 la rifiuta il motore — S1, 2026-09-27
- Esperimenti: uno script scripts/us_<storia>_<descrizione>.py con run_experiment(), che scrive results/<stesso nome>.csv e thesis/figures/<stesso nome>.png, entrambi versionati; nel CSV float nativi (str) e stringa vuota per i valori non applicabili — S1, 2026-09-27
- Codice statistico in src/shk/stats/, separato da src/shk/kelly/ — S2, 2026-09-28
- Serie C2: n = 380 osservazioni (una stagione), 1000 serie per ogni φ, φ ∈ {0.0, 0.3, 0.5, 0.7} con φ = 0 come controllo; AR(1) con innovazioni N(0, 1) e partenza stazionaria, generate da generate_ar1_series (prima x_0 con size=m, poi le innovazioni in blocco) — S2, 2026-09-28
- Disegni dei gruppi: contiguous_2 (due metà da 190, principale), contiguous_38 (38 blocchi da 10, le giornate della C5.2), random_2 (etichette di contiguous_2 sulla serie permutata a caso, controllo) — S2, 2026-09-28
- Soglia nominale α = 0.05: rigetto se F > quantile 0.95 della F(k − 1, N − k). "Dentro/sopra il 5%" si giudica con l'intervallo Monte Carlo al 99% α ± 2.576·√(α(1 − α)/1000) ≈ [0.0322, 0.0678], estremi inclusi — S2, 2026-09-28
- Moving block bootstrap: B = 999, L ∈ {7, 20, 40} fissate prima dei risultati e tutte riportate; soglia = statistica d'ordine ⌈(1 − α)(B + 1)⌉ (la 950-esima); rigetto se la statistica osservata supera strettamente la soglia — S2, 2026-09-28
- Seed C2: SEED_C2 = 20260928; SeedSequence(SEED_C2).spawn(4), un figlio per φ, diviso con spawn(3) in serie, permutazioni, bootstrap; il flusso bootstrap si divide con spawn(3), un generatore per L usato in sequenza sulle serie; confronti appaiati (stesse serie per tutti i disegni, per la F nominale e per ogni L) — S2, 2026-09-28
- I parametri C2 (PHI_VALUES, N_OBS, N_SERIES, ALPHA, SEED_C2, disegni, BLOCK_LENGTHS, N_BOOT, CSV_COLUMNS) si definiscono solo in src/shk/stats/false_rejection.py; script e test li importano — S2, 2026-09-28
- Nel codice nuovo, interi di tipo sbagliato (bool, float) danno TypeError e interi fuori intervallo ValueError; interi NumPy accettati — S2, 2026-09-28
- Cline esegue ogni comando Python con .\.venv\Scripts\python.exe (es. .\.venv\Scripts\python.exe -m pytest -v): il suo terminale usa di default l'interprete di Anaconda, senza shk — programmatore, 2026-09-28

## Story chiuse
### S1 — C1 Simulatore Kelly: motore riusabile ed errore di stima — chiusa il 2026-09-27
Esito: unisce US-C1.3 e US-C1.2; tutti i criteri coperti da test (suite veloce 44, suite slow 9). Risultati in results/us_c1_2_estimation_error.csv e thesis/figures/us_c1_2_estimation_error.png; valori misurati nei report .agent/report/T4.md … T7.md.
Resta aperto: Definition of Done di US-C1.2 (scegliere un caso in cui λ* batte il quarto-Kelly e uno in cui no; dati nel report T6); confermare lo scenario sottile e il modello dell'errore di stima; eventuale US-C1.4 sul controllo delle frequenze di drawdown α^(2/λ−1) (note di tesi 2.5 §10.4).
- T1 — Motore di crescita che riceve le frazioni dall'esterno — fatto — file: src/shk/kelly/simulate.py, tests/test_simulate.py
- T2 — Generatore di stime perturbate p̂ — fatto — file: src/shk/kelly/estimation.py, tests/test_estimation.py
- T3 — Regola di staking Kelly sulla stima, con troncamento e moltiplicatore λ — fatto — file: src/shk/kelly/staking.py, tests/test_staking.py
- T4 — Simulazione con p̂ ≠ p e asimmetria sovrastima/sottostima — fatto — file: src/shk/kelly/scenarios.py, tests/test_us_c1_2_acceptance.py
- T5 — Var(c) empirica e dominanza dell'errore di stima — fatto — file: src/shk/kelly/staking.py, tests/test_staking.py, tests/test_us_c1_2_acceptance.py
- T6 — λ* contro quarto-Kelly — fatto — file: src/shk/kelly/staking.py, tests/test_staking.py, tests/test_us_c1_2_acceptance.py
- T7 — Script dell'esperimento C1.2, CSV e figura per la tesi — fatto — file: scripts/us_c1_2_estimation_error.py, results/us_c1_2_estimation_error.csv, thesis/figures/us_c1_2_estimation_error.png

## Story S2 — C2 ANOVA a mano, autocorrelazione e calibrazione per block bootstrap — aperta il 2026-09-28, T12 da rivedere
Esito: unisce US-C2.1, US-C2.2 e US-C2.3. T8–T11 chiusi con tutti i criteri coperti da test; T12 fermo sul criterio 2. Suite veloce 109 verde; suite slow 14, di cui 1 rossa per il risultato noto di T12. Risultati in results/us_c2_anova_autocorrelation.csv (12 righe nominali definitive + 12 calibrate) e thesis/figures/us_c2_anova_autocorrelation.png (pannelli A e B); valori misurati nei report .agent/report/T8.md … T12.md, riprodotti in modo indipendente dal supervisore.
- T8 — ANOVA a una via a mano, singola e vettorizzata, verificata contro scipy — fatto — file: src/shk/stats/__init__.py, src/shk/stats/anova.py, tests/test_anova.py
- T9 — Generatore di serie AR(1) stazionarie — fatto — file: src/shk/stats/timeseries.py, tests/test_timeseries.py
- T10 — Tasso di falso rigetto della F su serie AR(1), US-C2.2 — fatto — file: src/shk/stats/false_rejection.py, scripts/us_c2_anova_autocorrelation.py, tests/test_us_c2_acceptance.py, results/us_c2_anova_autocorrelation.csv, thesis/figures/us_c2_anova_autocorrelation.png
- T11 — Calibrazione generica della soglia per moving block bootstrap — fatto — file: src/shk/stats/calibration.py, tests/test_calibration.py
- T12 — Tasso di falso rigetto con soglia calibrata, US-C2.3 — da rivedere — file: src/shk/stats/false_rejection.py, scripts/us_c2_anova_autocorrelation.py, tests/test_us_c2_acceptance.py, results/us_c2_anova_autocorrelation.csv, thesis/figures/us_c2_anova_autocorrelation.png

Risultati principali (rigetti su 1000 serie, contiguous_2; nominale e calibrato per L = 7, 20, 40):
- φ = 0.0: nominale 37; calibrato 35, 29, 32
- φ = 0.3: nominale 149; calibrato 61, 57, 49
- φ = 0.5: nominale 253; calibrato 73, 52, 42
- φ = 0.7: nominale 399; calibrato 108, 65, 56
- Nominale, altri disegni per φ = 0.0, 0.3, 0.5, 0.7: contiguous_38 44, 843, 999, 1000; random_2 58, 35, 48, 45.

Perché T12 è da rivedere: il criterio "a φ = 0.0, per ogni L, tasso calibrato dentro l'intervallo al 99%" non passa (29 con L = 20 e 32 con L = 40, sotto l'estremo inferiore 32.25; con size vera 5%, P(X ≤ 29) ≈ 0.0007). Gli altri criteri passano. La soglia è calibrata sulla serie grezza, senza imporre H₀; ipotesi non verificata come causa: la soglia cresce con la differenza osservata fra le metà (a φ = 0, correlazione di rango fra F osservata e soglia 0.057, 0.19, 0.276 per L = 7, 20, 40). Decisione del programmatore 2026-09-28: nessuna modifica a criterio, parametri o test; test_acceptance_calibrated_phi_zero_within_mc_interval resta rosso fino al seguito deciso in una chat di backlog. Dettagli e criteri originali in .agent/report/T12.md.

Resta aperto:
- Seguito di T12 (decisione in chat di backlog). Proposta del supervisore: un task che calibra su serie centrate per gruppo (H₀ imposta) e aggiunge righe method = block_bootstrap_centered accanto a quelle attuali, con criteri scritti e datati prima di eseguire; alternativa: chiudere US-C2.3 documentando il limite misurato e marcando il test del criterio 2 come fallimento atteso dichiarato.
- Docstring di src/shk/stats/calibration.py: nello schema (a), per l'ANOVA F il dato è "la serie della risposta", in contraddizione con (c) "imporre H₀ spetta a chi chiama"; schema dettato dal supervisore, da correggere insieme al seguito di T12.
- Validazione del tipo degli interi in draw_outcomes e noisy_estimates (codice C1): non segue la convenzione del codice nuovo; da allineare con un task futuro o da lasciare come eccezione nota.

### Fuori scope di S2
- Calibrazione per contiguous_38 e random_2.
- Stationary bootstrap (Politis–Romano) e scelta automatica della lunghezza dei blocchi (Politis–White).
- Errori standard HAC / Newey–West e correzione per n_eff.
- Applicazione della calibrazione a Z-test, DiD e Breusch-Pagan: spetta a C5.2, C6.4 e C8, che riusano src/shk/stats/calibration.py.
- Intervalli di confidenza di η² per block bootstrap (C8).
- Gestore canonico delle dipendenze (pip contro uv).

### Resta al programmatore per S2
- US-C2.1: saper dire a voce quali sono i gradi di libertà (k − 1 e N − k) e perché.
- US-C2.2, Definition of Done: portare in tesi la tabella φ → tasso di falso rigetto (righe nominali di results/us_c2_anova_autocorrelation.csv, definitive) e la figura.
- Correggere l'esercizio di §1.2 delle note: con il fattore assegnato a caso la F non si gonfia; serve un fattore allineato col tempo (confronto contiguous_2 contro random_2 nel CSV).
- Scegliere quale L adottare nelle story che riusano la calibrazione (C5.2, C6.4, C8) e scrivere in tesi il limite misurato del rimedio: rimandato a dopo il seguito di T12.
- Committare CSV e PNG generati dai Task 10 e 12.