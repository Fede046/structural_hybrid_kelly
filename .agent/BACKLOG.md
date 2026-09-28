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

## Story S2 — C2 ANOVA a mano, autocorrelazione e calibrazione per block bootstrap
Aperta il 2026-09-28.

**Interpretazione:** unisce US-C2.1, US-C2.2 e US-C2.3. Si implementa l'ANOVA a una via a mano e la si verifica contro scipy; si misura quanto spesso la F rigetta a torto su serie AR(1) senza effetto quando i gruppi sono blocchi contigui nel tempo; si scrive una funzione generica che calibra la soglia di una statistica qualunque per moving block bootstrap e si misura quanto riporta il tasso di falso rigetto verso il nominale.

**Assunzioni fatte:**
- Scelte del supervisore su delega esplicita del programmatore (2026-09-28): disegni dei gruppi, griglia di L e natura dei criteri come descritti nei task T10 e T12.
- Codice nuovo in un sottopacchetto src/shk/stats/, separato da src/shk/kelly/; nessuna modifica a src/shk/kelly/.
- Serie: n = 380 osservazioni (una stagione, note 1.2 §10.2), 1000 serie per ogni φ, φ ∈ {0.0, 0.3, 0.5, 0.7}, con φ = 0 come controllo; innovazioni N(0, 1) e partenza stazionaria.
- Disegni dei gruppi: contiguous_2 (due metà contigue da 190, disegno principale), contiguous_38 (38 blocchi contigui da 10, le giornate della C5.2), random_2 (le stesse etichette di contiguous_2 applicate alla serie permutata a caso, cioè assegnazione casuale). Un controllo rapido del supervisore indica che l'assegnazione casuale non gonfia la F: per questo random_2 è un controllo informativo.
- Soglia nominale: α = 0.05, rigetto se F > quantile 0.95 della F(k−1, N−k).
- "Sensibilmente sopra il 5%" = sopra l'estremo superiore dell'intervallo Monte Carlo al 99% attorno a 0.05, cioè 0.05 + 2.576·√(0.05·0.95/1000); con 1000 serie l'intervallo è circa [0.0322, 0.0678].
- Block bootstrap: moving block bootstrap, B = 999 ricampionamenti; L ∈ {7, 20, 40} (circa n^(1/3), √n e n/10), fissate prima di vedere i risultati e tutte riportate. Soglia calibrata = statistica d'ordine ⌈(1 − α)(B + 1)⌉ (la 950-esima con B = 999); rigetto se la statistica osservata supera la soglia.
- Seed: SEED_C2 = 20260928, distinto dal SEED di C1; confronti appaiati (per ogni φ le stesse serie per tutti i disegni, per la F nominale e per ogni L).
- Dipendenze: scipy e numpy sono già dipendenze runtime [V, R2@2026-09-27]; nessuna dipendenza nuova.
- Nessun task di ricognizione: la story poggia su layout del pacchetto [V, R1@2026-09-27], dipendenze e configurazione pytest [V, R2@2026-09-27], convenzioni degli script [V, R2@2026-09-27] e schema dei generatori con SeedSequence.spawn [V, R10@2026-09-27]; la scheda è aggiornata a R16, che copre l'ultimo task chiuso (T7).
- Stato git dopo T7 (branch e commit dei file di T7) non confermato: non serve a nessun task, perché nessun task esegue operazioni git.

**Domande aperte:**

### Task 8 — ANOVA a una via calcolata a mano e verificata contro scipy
Stato: da fare

Obiettivo: esiste in src/shk/stats/anova.py un'ANOVA a una via calcolata a mano (SS_between, SS_within, SS_total, gradi di libertà, F, p-value), in versione per un singolo dataset e in versione vettorizzata su molte serie, che coincide con scipy.stats.f_oneway.

Dipende da: nessuno.

Contesto: il pacchetto shk ha i sorgenti in src/shk/ [V, R1@2026-09-27]; scipy è dipendenza runtime [V, R2@2026-09-27]. L'unico sottopacchetto documentato è src/shk/kelly/ [V, R1@2026-09-27]; che src/shk/stats/ non esista ancora è dedotto [D]. Convenzioni: type hints completi, docstring stile NumPy con sezioni Parametri / Restituisce / Solleva, validazione in apertura con ValueError per i valori e TypeError per i tipi [V, R1@2026-09-27]. Dataset di prova (toy): A = {4, 7}, B = {2, 9, 3}; valori esatti attesi (ricalcolo del supervisore [D], da confermare nel test): SS_between = 5/6, SS_within = 199/6, SS_total = 34, gradi di libertà (1, 3), F = 15/199.

Da verificare prima di iniziare: che src/shk/stats/ e tests/test_anova.py non esistano già; se esistono, fermarsi e riportarlo.

Passi richiesti:
1. Creare src/shk/stats/__init__.py con una docstring di modulo in italiano.
2. Creare src/shk/stats/anova.py con una funzione per un singolo dataset che riceve una sequenza di gruppi (array 1D) e restituisce un risultato immutabile con ss_between, ss_within, ss_total, df_between, df_within, ms_between, ms_within, f_statistic, p_value. Le SS e la F si calcolano dalle definizioni (medie di gruppo e media generale); solo il p-value usa scipy.stats.f.sf.
3. Nello stesso modulo, una funzione vettorizzata che riceve values di forma (..., N) ed etichette intere di forma (N,), con valori 0..k−1 tutti presenti, e restituisce la F per ogni serie lungo gli assi iniziali, senza cicli Python sulle serie.
4. Validazione: almeno 2 gruppi, ogni gruppo non vuoto, valori finiti, N > k (df_within > 0); per la versione vettorizzata, etichette 1D intere di lunghezza pari all'ultimo asse di values, ciascuna fra 0 e k−1 presente almeno una volta.
5. Scrivere tests/test_anova.py (suite veloce) con i test dei criteri qui sotto.
6. Eseguire pytest -v e riportare l'esito.

Vincoli:
- Nessun commit e nessuna operazione git che modifichi lo stato del repository.
- Commenti e docstring in italiano; identificatori, messaggi delle eccezioni e nomi dei test in inglese.
- Rispettare le convenzioni della sezione "Convenzioni del progetto" di .agent/PROTOCOLLO.md.
- Non usare scipy.stats.f_oneway nel codice di libreria: solo nei test, come riferimento.
- Nessun try:, print( o logging in src/.
- Non toccare src/shk/kelly/, i test esistenti, gli script e i risultati di C1.
- Nessuna dipendenza nuova.
- Prima di scrivere codice, proporre il piano e fare le domande necessarie.
- A fine task, scrivere il report in .agent/report/T8.md (unico file di .agent/ modificabile) con, in sezioni distinte: percorsi dei file modificati, creati o rimossi; esito di ciascun criterio di accettazione; valori misurati; deviazioni dal piano; cose non fatte; comandi eseguiti. Fatti e valori senza giudizi; interpretazioni solo in una sezione a parte, se richieste.

Criteri di accettazione:
- Sul toy dataset: ss_between = 5/6, ss_within = 199/6, ss_total = 34, df_between = 1, df_within = 3, f_statistic = 15/199, con tolleranza relativa 1e-12 rispetto alle frazioni esatte.
- Sul toy dataset e su almeno tre dataset casuali generati con seed fisso (con k diversi fra loro e gruppi di dimensioni diverse), f_statistic coincide con quella di scipy.stats.f_oneway con tolleranza relativa 1e-12 e p_value con tolleranza relativa 1e-10; entrambi i valori sono calcolati nel test in float64, non letti da un file.
- SS_total = SS_between + SS_within con tolleranza relativa 1e-12 sul toy e sui dataset casuali, dove SS_total è calcolata in modo indipendente come somma dei quadrati degli scarti dalla media generale.
- La funzione vettorizzata, su un batch di almeno 10 serie casuali con etichette fisse, restituisce per ogni serie la stessa F della funzione per singolo dataset, con tolleranza relativa 1e-12.
- Ogni condizione di validazione del passo 4 solleva l'eccezione prevista (ValueError o TypeError), verificata da un test.
- La suite veloce (pytest -v) passa per intero.

Da misurare e riportare, senza farlo tornare: i valori di SS_between, SS_within, SS_total, F e p-value sul toy, con 15 cifre significative.

Esito: —

### Task 9 — Generatore di serie AR(1) stazionarie
Stato: da fare

Obiettivo: esiste in src/shk/stats/timeseries.py una funzione che genera m serie AR(1) stazionarie indipendenti di lunghezza n, con coefficiente φ noto, a partire da un np.random.Generator passato come argomento.

Dipende da: nessuno.

Contesto: l'RNG entra sempre come argomento np.random.Generator e non viene mai creato dentro le funzioni di libreria; i tipi sbagliati danno TypeError [V, R5@2026-09-27 e R6@2026-09-27]. Vettorizzazione NumPy lungo l'asse delle serie [V, R1@2026-09-27]. Modello: x_t = φ·x_{t−1} + ε_t, con ε_t ~ N(0, 1) indipendenti e x_0 ~ N(0, 1/(1 − φ²)), così che la serie sia stazionaria fin dal primo istante con varianza 1/(1 − φ²) e autocorrelazione φ^h a ritardo h (teoria, non verificata nel codice). Che src/shk/stats/timeseries.py non esista è dedotto [D].

Da verificare prima di iniziare: che src/shk/stats/timeseries.py e tests/test_timeseries.py non esistano già; se esistono, fermarsi e riportarlo.

Passi richiesti:
1. Creare src/shk/stats/timeseries.py con una funzione (phi, n, m, rng) che restituisce un ndarray float64 di forma (m, n), con righe = serie e colonne = tempo; il ciclo è ammesso solo lungo il tempo, vettorizzato sulle m serie.
2. Validazione: phi finito con |phi| < 1, n ≥ 2 intero, m ≥ 1 intero (ValueError); rng non np.random.Generator (TypeError).
3. Scrivere tests/test_timeseries.py (suite veloce) con i test dei criteri qui sotto.
4. Eseguire pytest -v e riportare l'esito.

Vincoli:
- Nessun commit e nessuna operazione git che modifichi lo stato del repository.
- Commenti e docstring in italiano; identificatori, messaggi delle eccezioni e nomi dei test in inglese.
- Rispettare le convenzioni della sezione "Convenzioni del progetto" di .agent/PROTOCOLLO.md.
- Type hints completi; docstring stile NumPy con Parametri / Restituisce / Solleva, che riporta il modello e la partenza stazionaria.
- Nessun try:, print( o logging in src/.
- Non toccare src/shk/kelly/ né src/shk/stats/anova.py.
- Nessuna dipendenza nuova.
- Prima di scrivere codice, proporre il piano e fare le domande necessarie.
- A fine task, scrivere il report in .agent/report/T9.md (unico file di .agent/ modificabile) con, in sezioni distinte: percorsi dei file modificati, creati o rimossi; esito di ciascun criterio di accettazione; valori misurati; deviazioni dal piano; cose non fatte; comandi eseguiti. Fatti e valori senza giudizi; interpretazioni solo in una sezione a parte, se richieste.

Criteri di accettazione:
- L'output ha forma (m, n) e dtype float64.
- Due chiamate con generatori creati dallo stesso seed danno array identici; generatori con seed diversi danno array diversi.
- Con φ ∈ {0.0, 0.3, 0.7}, m = 2000, n = 380 e seed fisso: la varianza empirica fra le serie, calcolata alla prima e all'ultima colonna, dista meno del 15% relativo da 1/(1 − φ²); l'autocorrelazione a ritardo 1, calcolata in forma pooled su tutte le coppie (x_t, x_{t+1}) come Σ x_t·x_{t+1} / Σ x_t² (media teorica 0, non stimata), dista meno di 0.02 da φ. Le tolleranze sono fissate qui e non vanno modificate.
- Ogni condizione di validazione del passo 2 solleva l'eccezione prevista, verificata da un test.
- La suite veloce (pytest -v) passa per intero.

Da misurare e riportare, senza farlo tornare: per ogni φ del terzo criterio, la varianza empirica alla prima e all'ultima colonna e l'autocorrelazione pooled a ritardo 1.

Esito: —

### Task 10 — Tasso di falso rigetto della F su serie AR(1) (US-C2.2)
Stato: da fare

Obiettivo: uno script riproducibile misura, per φ ∈ {0.0, 0.3, 0.5, 0.7} e per tre disegni dei gruppi, la quota di serie AR(1) senza alcun effetto di gruppo su cui la F rigetta a α = 0.05, e la scrive in un CSV e in una figura per la tesi.

Dipende da: Task 8, Task 9.

Contesto: la F per molte serie si calcola con la funzione vettorizzata di src/shk/stats/anova.py (Task 8); le serie con la funzione di src/shk/stats/timeseries.py (Task 9). Convenzioni degli script: matplotlib.use("Agg") prima di importare pyplot, import diretti da shk.<sottopacchetto>.<modulo>, parametri in run_experiment() senza argomenti, nessun argomento da riga di comando [V, R2@2026-09-27]; nome scripts/us_<storia>_<descrizione>.py con lo stesso nome base per CSV e PNG [V, R16@2026-09-27]; CSV in results/, figure in thesis/figures/, entrambi versionati [V, R2@2026-09-27]; nel CSV float nativi (str) e stringa vuota per i non applicabili (decisione S1). Parametri condivisi fra script e test definiti in un solo modulo di libreria e importati, come per scenarios.py [V, R10@2026-09-27], perché la duplicazione fra script e test è una zona fragile nota [V, R2@2026-09-27]. Schema dei generatori con SeedSequence.spawn [V, R10@2026-09-27]. Marker slow e addopts "-m 'not slow'" [V, R2@2026-09-27].

Da verificare prima di iniziare: che src/shk/stats/false_rejection.py, scripts/us_c2_anova_autocorrelation.py e tests/test_us_c2_acceptance.py non esistano già; se esistono, fermarsi e riportarlo.

Passi richiesti:
1. Creare src/shk/stats/false_rejection.py con le costanti PHI_VALUES = (0.0, 0.3, 0.5, 0.7), N_OBS = 380, N_SERIES = 1000, ALPHA = 0.05, SEED_C2 = 20260928 e i nomi dei disegni contiguous_2, contiguous_38 e random_2.
2. Nello stesso modulo, la costruzione dei generatori: SeedSequence(SEED_C2).spawn(len(PHI_VALUES)) dà un figlio per ogni φ, nell'ordine di PHI_VALUES; ogni figlio si divide con spawn(3) in tre flussi, nell'ordine: serie, permutazioni per random_2, bootstrap. Il terzo flusso non si usa in questo task, ma va già creato perché il Task 12 lo userà senza cambiare i primi due.
3. Nello stesso modulo, le etichette dei disegni: contiguous_k assegna l'osservazione t al gruppo ⌊t·k/N_OBS⌋ (k = 2 dà due blocchi da 190, k = 38 dà 38 blocchi da 10); random_2 usa le etichette di contiguous_2 applicate a ogni serie permutata con una permutazione casuale propria, presa dal flusso delle permutazioni.
4. Nello stesso modulo, una funzione che per ogni φ genera una sola matrice di N_SERIES serie dal flusso delle serie, la usa per tutti e tre i disegni, e restituisce per ogni coppia (disegno, φ) il numero di rigetti, il tasso, il valore critico nominale e l'intervallo Monte Carlo al 99% attorno ad ALPHA: ALPHA ± 2.576·√(ALPHA·(1 − ALPHA)/N_SERIES). Rigetto se F > scipy.stats.f.ppf(1 − ALPHA, k − 1, N_OBS − k).
5. Creare scripts/us_c2_anova_autocorrelation.py con run_experiment() che scrive results/us_c2_anova_autocorrelation.csv con le colonne design, phi, method, block_length, n_series, rejections, rejection_rate, critical_value_mean, mc_lower_99, mc_upper_99. In questo task method vale sempre "nominal", block_length è stringa vuota e critical_value_mean è il valore critico nominale.
6. Lo script scrive thesis/figures/us_c2_anova_autocorrelation.png con un pannello A: tasso di falso rigetto contro φ per i tre disegni, linea orizzontale a ALPHA e banda dell'intervallo al 99%. Il layout deve lasciare spazio a un pannello B che aggiungerà il Task 12.
7. Scrivere tests/test_us_c2_acceptance.py con i test dei criteri vincolanti, che importano parametri e funzione da src/shk/stats/false_rejection.py senza ripeterli. Lasciarli nella suite veloce se l'intero file gira in meno di 10 secondi; altrimenti marcarli @pytest.mark.slow e riportarlo come deviazione.
8. Eseguire lo script due volte e confrontare i CSV byte per byte; eseguire pytest -v e, se ci sono test marcati slow, pytest -m slow.

Vincoli:
- Nessun commit e nessuna operazione git che modifichi lo stato del repository. Il CSV e il PNG generati vanno versionati: elencarli nel report come file da committare, senza committarli.
- Commenti e docstring in italiano; identificatori, messaggi delle eccezioni e nomi dei test in inglese.
- Rispettare le convenzioni della sezione "Convenzioni del progetto" di .agent/PROTOCOLLO.md.
- Type hints completi; docstring stile NumPy; nessun try:, print( o logging in src/ e scripts/.
- Non toccare src/shk/kelly/, gli script e i risultati di C1, né src/shk/stats/anova.py e src/shk/stats/timeseries.py (se sembra necessario cambiarli, fermarsi e chiedere).
- Non modificare φ, N_OBS, N_SERIES, SEED_C2, i disegni o l'intervallo per far cambiare l'esito dei criteri.
- Nessuna dipendenza nuova.
- Prima di scrivere codice, proporre il piano e fare le domande necessarie.
- A fine task, scrivere il report in .agent/report/T10.md (unico file di .agent/ modificabile) con, in sezioni distinte: percorsi dei file modificati, creati o rimossi; esito di ciascun criterio di accettazione; valori misurati; deviazioni dal piano; cose non fatte; comandi eseguiti, con durata dello script. Fatti e valori senza giudizi; interpretazioni solo in una sezione a parte, se richieste.

Criteri di accettazione:
- contiguous_2, φ = 0.0: il tasso di falso rigetto sta dentro l'intervallo Monte Carlo al 99% (estremi inclusi).
- contiguous_2, φ ∈ {0.3, 0.5, 0.7}: il tasso di falso rigetto è strettamente maggiore dell'estremo superiore dell'intervallo al 99%.
- contiguous_2: il tasso è strettamente crescente lungo φ = 0.0, 0.3, 0.5, 0.7.
- Per ogni φ i tre disegni usano la stessa matrice di serie: un test verifica che la matrice dipende solo da SEED_C2 e dall'indice di φ, e che la funzione non ne genera altre.
- Il CSV ha 12 righe di dati (3 disegni × 4 φ) e le colonne del passo 5, nell'ordine indicato; due esecuzioni dello script producono CSV identici byte per byte.
- Il PNG esiste in thesis/figures/us_c2_anova_autocorrelation.png.
- La suite veloce (pytest -v) passa per intero, e anche pytest -m slow se il task ha aggiunto test slow.

Da misurare e riportare, senza farlo tornare: il tasso di falso rigetto e il numero di rigetti per ogni coppia (disegno, φ), compresi tutti i valori di contiguous_38 e random_2, che non hanno soglie; gli estremi dell'intervallo al 99% calcolati; i valori critici nominali per k = 2 e k = 38.

Esito: —

### Task 11 — Calibrazione generica della soglia per moving block bootstrap
Stato: da fare

Obiettivo: esiste in src/shk/stats/calibration.py una funzione generica che, dati una serie (o una matrice con il tempo sull'asse 0) e una statistica di test qualunque, restituisce la soglia calibrata al livello α per moving block bootstrap; la docstring del modulo documenta che è il rimedio unico per i quattro strumenti di §8.

Dipende da: Task 8 (la F vettorizzata serve come una delle statistiche di prova nei test).

Contesto: l'RNG entra come argomento np.random.Generator [V, R5@2026-09-27]. Moving block bootstrap: ogni ricampionamento concatena ⌈n/L⌉ blocchi di L righe consecutive, con inizio estratto uniformemente fra 0 e n − L, e si tronca a n righe; le righe si ricampionano intere, così una matrice mantiene la struttura fra colonne. Soglia = statistica d'ordine ⌈(1 − α)(B + 1)⌉ delle B statistiche ricampionate (decisione S2). I quattro strumenti di §8 (lista prerequisiti, §8, "Rimedio unificato all'autocorrelazione"): ANOVA F, FWER dello Z-test per giornata (C5.2), Difference-in-Differences, Breusch-Pagan (C6.4). Imporre H₀ nei dati passati (per esempio residui o serie centrate) è compito di chi chiama la funzione, non della funzione. Che src/shk/stats/calibration.py non esista è dedotto [D].

Da verificare prima di iniziare: che src/shk/stats/calibration.py e tests/test_calibration.py non esistano già; se esistono, fermarsi e riportarlo.

Passi richiesti:
1. Creare src/shk/stats/calibration.py con una funzione che restituisce gli indici di B ricampionamenti moving block, come array intero di forma (B, n), dati n, L, B e rng.
2. Nello stesso modulo, la funzione di calibrazione con parametri: data (tempo sull'asse 0, 1D o più dimensioni), statistic (callable), block_length, n_boot, alpha, rng e un flag vectorized. Con vectorized falso, statistic riceve un ricampionamento della forma di data e restituisce uno scalare; con vectorized vero, riceve l'intero array dei ricampionamenti, di forma (B, *data.shape), e restituisce un array (B,). La funzione restituisce la soglia come float.
3. Validazione: data con almeno una dimensione e valori finiti; 1 ≤ block_length ≤ n; n_boot ≥ 1; 0 < alpha < 1; statistic callable (TypeError); rng np.random.Generator (TypeError); con vectorized vero, output di forma diversa da (B,) → ValueError; statistiche non finite → ValueError.
4. Docstring del modulo in italiano che (a) nomina i quattro strumenti di §8 e dice per ciascuno quale dato passare sotto H₀ e quale statistica; (b) dichiara che la calibrazione dipende dalla lunghezza dei blocchi e rimanda a results/us_c2_anova_autocorrelation.csv per la dipendenza misurata; (c) dichiara che imporre H₀ nei dati spetta a chi chiama.
5. Scrivere tests/test_calibration.py (suite veloce) con i test dei criteri qui sotto.
6. Eseguire pytest -v e riportare l'esito.

Vincoli:
- Nessun commit e nessuna operazione git che modifichi lo stato del repository.
- Commenti e docstring in italiano; identificatori, messaggi delle eccezioni e nomi dei test in inglese.
- Rispettare le convenzioni della sezione "Convenzioni del progetto" di .agent/PROTOCOLLO.md.
- Type hints completi; docstring stile NumPy; nessun try:, print( o logging in src/.
- La funzione non conosce l'ANOVA né l'AR(1): nessun import da anova.py, timeseries.py o false_rejection.py dentro calibration.py.
- Non implementare lo stationary bootstrap né la scelta automatica di L.
- Non toccare src/shk/kelly/ e gli altri moduli di src/shk/stats/.
- Nessuna dipendenza nuova.
- Prima di scrivere codice, proporre il piano e fare le domande necessarie.
- A fine task, scrivere il report in .agent/report/T11.md (unico file di .agent/ modificabile) con, in sezioni distinte: percorsi dei file modificati, creati o rimossi; esito di ciascun criterio di accettazione; valori misurati; deviazioni dal piano; cose non fatte; comandi eseguiti. Fatti e valori senza giudizi; interpretazioni solo in una sezione a parte, se richieste.

Criteri di accettazione:
- Gli indici hanno forma (B, n), stanno in [0, n); dentro ogni blocco gli indici consecutivi differiscono di 1; ogni inizio di blocco sta in [0, n − L].
- Con L = n ogni ricampionamento è la serie originale.
- Con data 2D, ogni riga ricampionata coincide con una riga intera dell'originale.
- La soglia coincide con la statistica d'ordine ⌈(1 − α)(B + 1)⌉ delle statistiche ricampionate, ricalcolate nel test con lo stesso seed.
- Con lo stesso seed, vectorized vero e vectorized falso danno la stessa soglia.
- La funzione è usata nei test con almeno due statistiche diverse: la F vettorizzata del Task 8 con etichette fisse su dati 1D, e una statistica su dati 2D (per esempio la media della prima colonna divisa per l'errore standard ingenuo).
- Stesso seed → stessa soglia; seed diverso → soglia in generale diversa.
- Ogni condizione di validazione del passo 3 solleva l'eccezione prevista, verificata da un test.
- La docstring del modulo contiene i tre elementi (a), (b), (c) del passo 4.
- La suite veloce (pytest -v) passa per intero.

Esito: —

### Task 12 — Tasso di falso rigetto con soglia calibrata (US-C2.3)
Stato: da fare

Obiettivo: lo script dell'esperimento C2 misura anche, per il disegno contiguous_2, per ogni φ e per ogni L ∈ {7, 20, 40}, il tasso di falso rigetto con la soglia calibrata per moving block bootstrap sulle stesse serie usate per la F nominale, e lo aggiunge al CSV e alla figura.

Dipende da: Task 10, Task 11.

Contesto: src/shk/stats/false_rejection.py (Task 10) definisce parametri, generatori, disegni e tassi nominali, e crea già per ogni φ un terzo flusso riservato al bootstrap; src/shk/stats/calibration.py (Task 11) fornisce la calibrazione generica; la F vettorizzata è in src/shk/stats/anova.py (Task 8). Lo script e il CSV sono scripts/us_c2_anova_autocorrelation.py e results/us_c2_anova_autocorrelation.csv, con colonna method e block_length già previste (Task 10). Rieseguire uno script sovrascrive CSV e PNG versionati [V, R2@2026-09-27 e R16@2026-09-27]. Marker slow [V, R2@2026-09-27]; i test slow non girano in CI [V, R2@2026-09-27].

Da verificare prima di iniziare: nessuna.

Passi richiesti:
1. In src/shk/stats/false_rejection.py aggiungere BLOCK_LENGTHS = (7, 20, 40) e N_BOOT = 999, e la divisione del flusso bootstrap di ogni φ con spawn(len(BLOCK_LENGTHS)): un generatore per ogni L, nell'ordine di BLOCK_LENGTHS, usato in sequenza sulle N_SERIES serie.
2. Nello stesso modulo, una funzione che per contiguous_2, per ogni φ e per ogni L calibra la soglia serie per serie con la funzione del Task 11: data = la serie, statistic = la F vettorizzata con le etichette di contiguous_2, vectorized vero, ALPHA. Rigetto se la F osservata supera la soglia di quella serie. Restituisce rigetti, tasso e media delle soglie. Le serie devono essere le stesse del Task 10, generate dallo stesso flusso: i tassi nominali già scritti non devono cambiare.
3. Estendere run_experiment() perché aggiunga al CSV le righe con method = "block_bootstrap", design = contiguous_2, block_length = L e critical_value_mean = media delle soglie calibrate, lasciando invariate le 12 righe nominali.
4. Estendere la figura con un pannello B: per contiguous_2, tasso nominale e tassi calibrati (una curva per L) contro φ, con la linea a ALPHA e la banda al 99%.
5. Aggiungere a tests/test_us_c2_acceptance.py i test dei criteri vincolanti di questo task, marcati @pytest.mark.slow.
6. Eseguire lo script due volte e confrontare i CSV byte per byte; eseguire pytest -v e pytest -m slow; riportare la durata dello script.

Vincoli:
- Nessun commit e nessuna operazione git che modifichi lo stato del repository. Il CSV e il PNG rigenerati vanno versionati: elencarli nel report come file da committare, senza committarli.
- Commenti e docstring in italiano; identificatori, messaggi delle eccezioni e nomi dei test in inglese.
- Rispettare le convenzioni della sezione "Convenzioni del progetto" di .agent/PROTOCOLLO.md.
- Type hints completi; docstring stile NumPy; nessun try:, print( o logging in src/ e scripts/.
- Non modificare L, N_BOOT, ALPHA, φ, SEED_C2 o la regola della statistica d'ordine per avvicinare i tassi calibrati al 5%.
- Non modificare src/shk/stats/calibration.py, anova.py e timeseries.py; se sembra necessario, fermarsi e chiedere.
- Non calibrare contiguous_38 e random_2.
- Nessuna dipendenza nuova.
- Prima di scrivere codice, proporre il piano e fare le domande necessarie.
- A fine task, scrivere il report in .agent/report/T12.md (unico file di .agent/ modificabile) con, in sezioni distinte: percorsi dei file modificati, creati o rimossi; esito di ciascun criterio di accettazione; valori misurati; deviazioni dal piano; cose non fatte; comandi eseguiti, con durata dello script. Fatti e valori senza giudizi; interpretazioni solo in una sezione a parte, se richieste.

Criteri di accettazione:
- Le 12 righe nominali del CSV sono identiche a quelle prodotte dal Task 10.
- contiguous_2, φ = 0.0: per ogni L il tasso calibrato sta dentro l'intervallo Monte Carlo al 99% (estremi inclusi).
- contiguous_2, φ ∈ {0.3, 0.5, 0.7}: per ogni L il tasso calibrato è strettamente minore del tasso nominale sulle stesse serie.
- Il CSV ha 24 righe di dati (12 nominali + 4 φ × 3 L calibrate); due esecuzioni dello script producono CSV identici byte per byte.
- Il PNG contiene i pannelli A e B.
- pytest -v e pytest -m slow passano per intero.

Da misurare e riportare, senza farlo tornare: per ogni coppia (φ, L), il tasso calibrato, il numero di rigetti, se il tasso sta dentro l'intervallo al 99% e la media delle soglie calibrate confrontata con il valore critico nominale. Se per qualche coppia il tasso calibrato resta sopra l'intervallo, è un risultato sui limiti del block bootstrap da riportare, non un difetto da correggere.

Esito: —

### Fuori scope di S2
- Calibrazione per contiguous_38 e random_2.
- Stationary bootstrap (Politis–Romano) e scelta automatica della lunghezza dei blocchi (Politis–White).
- Errori standard HAC / Newey–West e correzione per n_eff.
- Applicazione della calibrazione a Z-test, DiD e Breusch-Pagan: spetta a C5.2, C6.4 e C8, che riusano src/shk/stats/calibration.py.
- Intervalli di confidenza di η² per block bootstrap (C8).
- Gestore canonico delle dipendenze (pip contro uv).

### Resta al programmatore per S2
- US-C2.1: saper dire a voce quali sono i gradi di libertà (k − 1 e N − k) e perché.
- US-C2.2, Definition of Done: portare in tesi la tabella φ → tasso di falso rigetto (da results/us_c2_anova_autocorrelation.csv) e la figura.
- Correggere l'esercizio di §1.2 delle note: con il fattore assegnato a caso la F non si gonfia; serve un fattore allineato col tempo (confronto contiguous_2 contro random_2 nel CSV).
- Scegliere, sulla base del CSV, quale L adottare nelle story che riusano la calibrazione (C5.2, C6.4, C8), e scrivere in tesi il limite misurato del rimedio.
- Committare CSV e PNG generati dai Task 10 e 12.