# Backlog

## Story S1 — C1 Simulatore Kelly: motore riusabile ed errore di stima
Aperta il 2026-09-27.

**Interpretazione:** US-C1.1 è chiusa; questa story unisce US-C1.3 (motore di crescita separato dalla regola di staking, seed riproducibile) e US-C1.2 (puntare su p̂ ≠ p, asimmetria sovra/sottostima, Var(c) empirica, λ* contro quarto-Kelly). C1.3 viene prima perché il rumore di stima per scommessa richiede frazioni diverse a ogni passo. I task sono 7: il punto di stacco è dopo T5 (infrastruttura e primi due criteri di C1.2; poi λ* e artefatti per la tesi). Dopo T5 la lista dei task chiusi in SCHEDA.md supera quattro elementi: prima di T6 va rifatta la mappatura.

**Assunzioni fatte:**
- US-C1.1 è chiusa: script, test di accettazione e output CSV/PNG versionati [V, R2@2026-09-27].
- Scenario base: p = 0.60, b = 1.0, T = 1000, M = 10000, come in C1.1 [V, R2@2026-09-27].
- Scenario sottile ("edge compatibile con Ω ≈ 5.3%"): p = 0.52, quota decimale o = 2.00 (b = 1.0), T = 380 (una stagione), M = 10000. È lo scenario con edge reale del 4% delle note di tesi 2.5 §7.2. Scelta del supervisore, da confermare dal programmatore.
- Modello dell'errore di stima: p̂ per singola scommessa, p̂_{m,t} = p + ε_{m,t}, con ε gaussiano indipendente, deviazione standard σ_p ∈ {0.015, 0.0283, 0.045}, riportato in [0, 1]. Valori dalle note 2.5 §3.3 e 3.2 §7. Coerente con il Modulo 3 della tesi, dove p̂_t cambia a ogni scommessa.
- Frazione stimata f̂ = max(0, p̂ − (1 − p̂)/b); c = f̂/f*. Il troncamento a zero è il meccanismo indicato dalla nota 3.4 §4.2.
- "L'errore di stima domina il segnale" si legge come Var(c) > 1: la dispersione della puntata supera la puntata ottima stessa.
- Il "λ fisso" del quarto criterio di C1.2 è il quarto-Kelly, λ = 0.25, come nella Definition of Done.
- Var(c) si stima in forma pooled su tutte le scommesse simulate, non per singola scommessa (note 3.2 §7.5).
- Il criterio di asimmetria ±10% è vincolante solo nello scenario sottile. Nel base il vantaggio analitico della sottostima è minimo (crescita 0.01231 contro 0.01282 per scommessa) e si inverte se la mediana delle vincite si sposta di due unità, quindi lì è informativo [D, ricalcolo del supervisore].
- Fatti usati senza farli riverificare: draw_outcomes(p, T, M, rng) da riga 6 di src/shk/kelly/simulate.py, con validazione e rng di tipo np.random.Generator [V, R2@2026-09-27]; log_wealth_paths(outcomes, f, b) da riga 49 dello stesso file, senza validazione, output (M, T+1) float64 con colonna 0 nulla [V, R2@2026-09-27]; comando dei test veloci pytest -v con addopts "-m 'not slow'" [V, R2@2026-09-27]; convenzioni di stile e di script [V, R1@2026-09-27 e R2@2026-09-27].

**Domande aperte:**

### Task 1 — Motore di crescita che riceve le frazioni dall'esterno
Stato: fatto

Obiettivo: in src/shk/kelly/simulate.py esiste un motore che calcola le traiettorie di log-wealth da una matrice di esiti e da frazioni ricevute dall'esterno, anche diverse per traiettoria e per passo; log_wealth_paths ne diventa un caso particolare con risultati invariati.

Dipende da: nessuno.

Contesto:
- src/shk/kelly/simulate.py: draw_outcomes(p, T, M, rng) da riga 6 restituisce ndarray (M, T) bool, True = vincita [V, R2@2026-09-27]; log_wealth_paths(outcomes, f, b) da riga 49 restituisce ndarray (M, T+1) float64 di ln(B_t/B_0), colonna 0 tutta 0.0, e non valida gli input [V, R2@2026-09-27].
- La docstring di log_wealth_paths alle righe 77-81 dichiara ancora NotImplementedError, pur essendo la funzione implementata [V, R1@2026-09-27].
- tests/test_simulate.py contiene docstring obsolete che annunciano NotImplementedError alle righe 71-72 e 88-89 [V, R1@2026-09-27].
- log_wealth_paths è usata da scripts/us_c1_1_growth_vs_lambda.py e da tests/test_us_c1_1_acceptance.py [V, R1@2026-09-27].
- Convenzioni: type hints completi; docstring stile NumPy con sezioni Parametri / Restituisce / Solleva; validazione in apertura di funzione con ValueError per i valori e TypeError per i tipi; nessun try, print o logging [V, R1@2026-09-27 e R2@2026-09-27].

Da verificare prima di iniziare:
- Il corpo di log_wealth_paths: si assume che sommi cumulativamente ln(1 + f·b) sulle vincite e ln(1 − f) sulle perdite [D].
- Tutti gli usi di log_wealth_paths nel repository, oltre ai due noti: cercarli con git grep [D].
- Quali test di tests/test_simulate.py esercitano log_wealth_paths e con quali tolleranze [D].

Passi richiesti:
1. Leggere src/shk/kelly/simulate.py dalla riga 49 alla fine e tests/test_simulate.py; eseguire git grep -n "log_wealth_paths".
2. Proporre il piano: nome del motore; forme ammesse per le frazioni (scalare, un valore per traiettoria, matrice (M, T)); validazioni previste. Attendere conferma.
3. Implementare il motore in src/shk/kelly/simulate.py, con validazione: frazioni in [0, 1) elemento per elemento, b > 0, outcomes ndarray bool 2D, forma delle frazioni compatibile con outcomes.
4. Riscrivere log_wealth_paths come chiamata al motore con frazione scalare e correggere la sua docstring obsoleta.
5. Aggiungere test in tests/test_simulate.py per i criteri 2, 3 e 5; correggere le docstring obsolete alle righe 71-72 e 88-89.
6. Eseguire pytest -v e pytest -m slow.

Vincoli:
- Non modificare draw_outcomes, src/shk/kelly/core.py, src/shk/kelly/metrics.py, scripts/us_c1_1_growth_vs_lambda.py, tests/test_us_c1_1_acceptance.py, results/, thesis/.
- Non eseguire lo script di C1.1: sovrascriverebbe output versionati.
- Il motore non riceve p né p̂ e non importa nulla da core.py: la regola di staking resta fuori.
- Nessun commit e nessuna operazione git che modifichi lo stato del repository.
- Commenti e docstring in italiano; identificatori, messaggi delle eccezioni e nomi dei test in inglese (è la convenzione del progetto).
- Prima di scrivere codice, proporre il piano e fare le domande necessarie.
- A fine task scrivere .agent/report/T1.md, unico file di .agent/ che si può toccare, con sezioni distinte: percorsi dei file modificati, creati o rimossi; esito di ciascun criterio; valori misurati; deviazioni dal piano; cose non fatte; comandi eseguiti.

Criteri di accettazione:
1. Il motore accetta frazioni scalari, per traiettoria e per passo (M, T), e restituisce (M, T+1) float64 con colonna 0 nulla.
2. Caso calcolato a mano, M = 1, T = 3, esiti [vinta, persa, vinta], frazioni [0.1, 0.2, 0.3], b = 1: le traiettorie valgono 0, ln 1.1, ln 1.1 + ln 0.8, ln 1.1 + ln 0.8 + ln 1.3, entro 1e-12.
3. Una frazione scalare e una matrice (M, T) con lo stesso valore costante danno lo stesso risultato (rtol 1e-12).
4. La firma del motore non contiene p né p̂ e simulate.py non importa da core.py.
5. Frazione < 0 o ≥ 1, b ≤ 0 oppure forma incompatibile sollevano ValueError; outcomes non booleano solleva TypeError; i messaggi sono in inglese.
6. pytest -v e pytest -m slow passano, senza modificare nessuna asserzione dei test di C1.1.
7. Nessuna docstring di simulate.py o di tests/test_simulate.py dichiara più NotImplementedError.

Esito: 2026-09-27 — file toccati: src/shk/kelly/simulate.py, tests/test_simulate.py. Deviazioni: motore chiamato simulate_growth(outcomes, fractions, b); frazioni accettate solo con broadcasting NumPy standard verso (M, T), cioè scalare, (T,), (1, T), (M, 1), (M, T), e una frazione per traiettoria si passa come (M, 1); aggiunto il rifiuto delle frazioni non finite; criterio 4 verificato con git grep e firma nel report invece che con un test. Non fatto: nulla. Confermato nel Task 2 (R5): le formule dei fattori logaritmici sono np.log(1 + b*f) e np.log(1 - f), senza log1p. Valori misurati: pytest -v 26 passati e 4 deselezionati; pytest -m slow 4 passati (12.75 s); discrepanza 0.0 sui criteri 2 e 3; log_wealth_paths e simulate_growth danno array identici. Report: .agent/report/T1.md.

### Task 2 — Generatore di stime perturbate p̂
Stato: fatto

Obiettivo: esiste un modulo che produce stime p̂ di p, sia con perturbazione relativa deterministica sia con rumore gaussiano indipendente per ogni scommessa, riproducibili dato il generatore casuale.

Dipende da: nessuno.

Contesto:
- File nuovo src/shk/kelly/estimation.py.
- Il generatore casuale si passa come argomento np.random.Generator, come in draw_outcomes, e si valida con TypeError [V, R2@2026-09-27].
- Convenzioni di stile e validazione come nel resto di src/shk/kelly/ [V, R1@2026-09-27].
- Modello: perturbazione relativa p̂ = p·(1 + δ); rumore per scommessa p̂_{m,t} = p + ε_{m,t}, con ε gaussiano indipendente di deviazione standard σ_p, matrice di forma (M, T), valori riportati in [0, 1].

Da verificare prima di iniziare: nessuna.

Passi richiesti:
1. Proporre il piano: nomi delle funzioni e comportamento ai bordi di [0, 1]. Attendere conferma.
2. Implementare in src/shk/kelly/estimation.py la perturbazione relativa deterministica.
3. Implementare nello stesso file il rumore gaussiano per scommessa, con rng passato come argomento.
4. Scrivere tests/test_estimation.py con i criteri sotto.
5. Eseguire pytest -v.

Vincoli:
- Non modificare file esistenti in src/, tests/, scripts/, results/, thesis/.
- Il modulo non calcola frazioni di puntata e non importa da simulate.py.
- Nessun commit e nessuna operazione git che modifichi lo stato del repository.
- Commenti e docstring in italiano; identificatori, messaggi delle eccezioni e nomi dei test in inglese (è la convenzione del progetto).
- Prima di scrivere codice, proporre il piano e fare le domande necessarie.
- A fine task scrivere .agent/report/T2.md, unico file di .agent/ che si può toccare, con sezioni distinte: percorsi dei file modificati, creati o rimossi; esito di ciascun criterio; valori misurati; deviazioni dal piano; cose non fatte; comandi eseguiti.

Criteri di accettazione:
1. Perturbazione relativa: p = 0.60 con δ = +0.10 dà 0.66, con δ = −0.10 dà 0.54, entro 1e-12.
2. Due generatori creati con lo stesso seed producono matrici di rumore identiche; seed diversi producono matrici diverse.
3. Con p = 0.52, σ_p = 0.0283, M = T = 1000: media empirica di p̂ entro 0.001 da p e deviazione standard empirica entro 0.001 da σ_p.
4. Tutti i valori prodotti stanno in [0, 1].
5. p fuori da [0, 1] o σ_p < 0 sollevano ValueError; un rng che non sia np.random.Generator solleva TypeError.
6. pytest -v passa.

Esito: 2026-09-27 — file toccati: src/shk/kelly/estimation.py (creato), tests/test_estimation.py (creato). Deviazioni: nessuna; funzioni relative_perturbation(p, delta) e noisy_estimates(p, sigma_p, T, M, rng); valori fuori da [0, 1] saturati agli estremi con clipping; sigma_p = 0 ammesso e restituisce p costante; delta non finito rifiutato con ValueError. Non fatto: nulla. Valori misurati: criterio 3 con seed 20260927, media 0.52000381 e deviazione standard 0.02831994; criterio 1 con errore 0.0; pytest -v 32 passati (6 nuovi) e 4 deselezionati. Controllo iniziale: il commit 52f0cba sul branch C1 contiene solo i file del Task 1 e .agent/. Report: .agent/report/T2.md.

### Task 3 — Regola di staking Kelly sulla stima, con troncamento e moltiplicatore λ
Stato: fatto

Obiettivo: esiste una regola di staking che trasforma stime p̂ (scalari o matrici) nelle frazioni f = λ · max(0, f*(p̂, b)), da passare al motore, senza che il motore venga toccato.

Dipende da: Task 1 (formato delle frazioni accettato dal motore).

Contesto:
- File nuovo src/shk/kelly/staking.py.
- kelly_fraction(p, b) sta in src/shk/kelly/core.py e valida gli input [V, R1@2026-09-27].
- b è la quota netta: con p = 0.6 e b = 1 si ottiene f* = 0.2 [D, ricalcolo del supervisore].
- Formula della regola: f̂ = max(0, p̂ − (1 − p̂)/b), poi f = λ·f̂, con λ ≥ 0.

Da verificare prima di iniziare:
- Formula esatta di kelly_fraction e suo comportamento con edge negativo: solleva un'eccezione, restituisce un valore negativo o restituisce 0 [D].
- Se kelly_fraction accetta array NumPy o solo scalari [D].
- Se kelly_fraction non è vettoriale o non tronca, la regola calcola la formula in proprio, e un test ne verifica l'accordo con kelly_fraction sui valori scalari validi.

Passi richiesti:
1. Leggere kelly_fraction in src/shk/kelly/core.py e riportare formula e comportamento con edge negativo.
2. Proporre il piano: nome della funzione e trattamento dell'edge negativo. Attendere conferma.
3. Implementare la regola in src/shk/kelly/staking.py.
4. Scrivere tests/test_staking.py con i criteri sotto.
5. Eseguire pytest -v e controllare con git diff --stat che simulate.py non sia cambiato in questo task.

Vincoli:
- Non modificare src/shk/kelly/simulate.py, core.py, metrics.py, né i file di C1.1.
- La regola non esegue simulazioni e non importa da simulate.py.
- Nessun commit e nessuna operazione git che modifichi lo stato del repository.
- Commenti e docstring in italiano; identificatori, messaggi delle eccezioni e nomi dei test in inglese (è la convenzione del progetto).
- Prima di scrivere codice, proporre il piano e fare le domande necessarie.
- A fine task scrivere .agent/report/T3.md, unico file di .agent/ che si può toccare, con sezioni distinte: percorsi dei file modificati, creati o rimossi; esito di ciascun criterio; valori misurati; deviazioni dal piano; cose non fatte; comandi eseguiti.

Criteri di accettazione:
1. p̂ = 0.60, b = 1, λ = 1 dà 0.2 e coincide con kelly_fraction(0.6, 1.0) entro 1e-12.
2. p̂ = 0.468, b = 1 (edge negativo) dà esattamente 0.
3. Con λ = 0.25 la frazione è un quarto di quella con λ = 1, elemento per elemento.
4. L'output ha la stessa forma dell'input: scalare, vettore (M,) o matrice (M, T).
5. λ < 0, b ≤ 0 o p̂ fuori da [0, 1] sollevano ValueError.
6. git diff --stat non mostra modifiche a src/shk/kelly/simulate.py introdotte in questo task.
7. pytest -v passa.

Esito: 2026-09-27 — file toccati: src/shk/kelly/staking.py (creato), tests/test_staking.py (creato). Deviazioni: funzione kelly_staking(p_hat, b, lam=1.0); formula calcolata in proprio perché kelly_fraction accetta solo scalari (core.py righe 37, 45, 48), con lo stesso ordine di operazioni di core.py; uno scalare o un array 0-dimensionale in ingresso dà un float Python; la frazione non è limitata sotto 1 e una frazione ≥ 1 viene rifiutata a valle da simulate_growth (documentato nella docstring); rifiutati anche b e λ non finiti. Non fatto: nulla. Valori misurati: errore 0.0 contro kelly_fraction su p̂ = 0.60 e sulla griglia con edge positivo; 0.0 esatto con p̂ = 0.468; pytest -v 38 passati (6 nuovi) e 4 deselezionati; git diff --stat senza modifiche a simulate.py. Report: .agent/report/T3.md.

### Task 4 — Simulazione con p̂ ≠ p e asimmetria sovrastima/sottostima
Stato: fatto

Obiettivo: un test di accettazione mostra che il simulatore punta secondo p̂ mentre gli esiti seguono p, e che nello scenario sottile sovrastimare p del 10% relativo danneggia la crescita mediana più che sottostimarlo della stessa quantità.

Dipende da: Task 1, Task 2, Task 3.

Contesto:
- Motore delle traiettorie in src/shk/kelly/simulate.py (Task 1); stime p̂ in src/shk/kelly/estimation.py (Task 2); regola di staking in src/shk/kelly/staking.py (Task 3).
- median_growth_rate(paths) e max_drawdown(paths) stanno in src/shk/kelly/metrics.py [V, R1@2026-09-27].
- Scenario base: p = 0.60, b = 1.0, T = 1000, M = 10000.
- Scenario sottile: p = 0.52, b = 1.0 (quota 2.00), T = 380, M = 10000.
- I due scenari si definiscono una volta sola, in un modulo nuovo sotto src/shk/kelly/ (proposta: scenarios.py), importabile da test e script. Serve a non ripetere la duplicazione di parametri fra script e test che esiste in C1.1.
- Valori analitici di orientamento nello scenario sottile: p̂ = 0.572 dà f̂ = 0.144 e crescita per scommessa ≈ −0.0047; p̂ = 0.468 dà f̂ = 0, cioè nessuna puntata e crescita 0 [D, ricalcolo del supervisore].
- I test di accettazione Monte Carlo si marcano @pytest.mark.slow; la CI non li esegue mai [V, R2@2026-09-27].

Da verificare prima di iniziare:
- Che median_growth_rate restituisca la mediana di ln(B_T/B_0)/T sulle traiettorie [D].
- Che max_drawdown restituisca un valore per traiettoria [D].

Passi richiesti:
1. Proporre il piano: modulo degli scenari; funzione che compone esiti estratti con p, frazioni calcolate da p̂ e motore; derivazione di due generatori indipendenti da un unico seed fisso, uno per gli esiti e uno per il rumore di stima. Attendere conferma.
2. Implementare il modulo degli scenari e la funzione di composizione.
3. Scrivere tests/test_us_c1_2_acceptance.py con i test del criterio 1, marcati slow se superano pochi secondi.
4. Scrivere il test dell'asimmetria nello scenario sottile, marcato slow.
5. Misurare i valori informativi ed eseguire pytest -v e pytest -m slow.

Vincoli:
- Non modificare il motore in simulate.py, né core.py, metrics.py o i file di C1.1.
- Il seed è fisso e dichiarato nel modulo degli scenari.
- Nessun commit e nessuna operazione git che modifichi lo stato del repository.
- Commenti e docstring in italiano; identificatori, messaggi delle eccezioni e nomi dei test in inglese (è la convenzione del progetto).
- Prima di scrivere codice, proporre il piano e fare le domande necessarie.
- A fine task scrivere .agent/report/T4.md, unico file di .agent/ che si può toccare, con sezioni distinte: percorsi dei file modificati, creati o rimossi; esito di ciascun criterio; valori misurati; deviazioni dal piano; cose non fatte; comandi eseguiti.

Criteri di accettazione:
1. A parità di seed, la matrice degli esiti è identica qualunque sia p̂: gli esiti dipendono solo da p.
2. Con p̂ = p, le traiettorie coincidono con log_wealth_paths(outcomes, kelly_fraction(p, b), b) entro rtol 1e-12.
3. Scenario sottile: con p̂ = 1.1·p la crescita mediana è negativa; con p̂ = 0.9·p è esattamente 0; quindi la sovrastima danneggia più della sottostima.
4. pytest -v e pytest -m slow passano.

Da misurare e riportare, senza farlo tornare: crescita mediana e drawdown mediano con p̂ = 1.1·p e p̂ = 0.9·p, in entrambi gli scenari, con la loro differenza. Nello scenario base il segno della differenza è il risultato: non modificare parametri, seed o T per ottenerne uno.

Esito: 2026-09-27 — file toccati: src/shk/kelly/scenarios.py (creato), tests/test_us_c1_2_acceptance.py (creato). Deviazioni: la composizione è divisa in due funzioni, draw_scenario_outcomes(scenario, rng) e simulate_scenario(scenario, outcomes, p_hat, lam=1.0), quest'ultima senza generatori e senza modificare outcomes; seed SEED = 20260927 con spawn_generators(seed) su SeedSequence.spawn(2) (primo generatore per gli esiti, secondo per il rumore); criteri 1 e 2 nella suite veloce con scenario ridotto, criterio 3 marcato slow. Non fatto: nulla. Valori misurati (seed 20260927). Scenario sottile: mediana delle vincite 198; con sovrastima crescita mediana −0.00437141 e drawdown mediano 0.98145658; con sottostima crescita 0.0 e drawdown 0.0; differenze −0.00437141 e +0.98145658. Scenario base: mediana delle vincite 600; con sovrastima crescita mediana 0.01231405 e drawdown mediano 0.99969185; con sottostima crescita 0.01282398 e drawdown 0.63474934; differenze −0.00050993 (crescita) e +0.36494251 (drawdown). Test: pytest -v 40 passati; pytest -m slow 5 passati (12.54 s). Report: .agent/report/T4.md.
### Task 5 — Var(c) empirica e dominanza dell'errore di stima
Stato: fatto

Obiettivo: una funzione stima dalle frazioni simulate i momenti di c = f̂/f*, e un test di accettazione mostra che nello scenario sottile l'errore di stima domina il segnale (Var(c) > 1) mentre nel base no.

Dipende da: Task 2, Task 3, Task 4 (modulo degli scenari).

Contesto:
- f̂ è la frazione della regola di Task 3 con λ = 1 applicata a p̂ con rumore per scommessa (Task 2); f* è la frazione ottima calcolata con il p vero.
- La funzione restituisce E[c], E[c²], Var(c) e la quota di scommesse con f̂ = 0, stimati in forma pooled su tutte le M·T scommesse. Sta in src/shk/kelly/estimation.py oppure in staking.py, a scelta motivata nel piano.
- Formula lineare di propagazione, senza troncamento: Var(c) = (o·σ_p/EV)², con o = b + 1 ed EV = p·o − 1 (note di tesi 3.2).
- Nello scenario base con σ_p = 0.0283 la formula dà 0.0801, e il troncamento vi è trascurabile (probabilità di f̂ = 0 dell'ordine di 2e-4) [D, ricalcolo del supervisore].

Da verificare prima di iniziare: nessuna.

Passi richiesti:
1. Proporre il piano: posizione della funzione e interfaccia. Attendere conferma.
2. Implementare la funzione dei momenti di c.
3. Aggiungere a tests/test_us_c1_2_acceptance.py i test dei criteri 1-3, usando gli scenari del modulo creato in Task 4.
4. Misurare i valori informativi ed eseguire pytest -v e pytest -m slow.

Vincoli:
- Non modificare il motore in simulate.py, né core.py, metrics.py o i file di C1.1.
- Nessun commit e nessuna operazione git che modifichi lo stato del repository.
- Commenti e docstring in italiano; identificatori, messaggi delle eccezioni e nomi dei test in inglese (è la convenzione del progetto).
- Prima di scrivere codice, proporre il piano e fare le domande necessarie.
- A fine task scrivere .agent/report/T5.md, unico file di .agent/ che si può toccare, con sezioni distinte: percorsi dei file modificati, creati o rimossi; esito di ciascun criterio; valori misurati; deviazioni dal piano; cose non fatte; comandi eseguiti.

Criteri di accettazione:
1. Scenario base, σ_p = 0.0283: Var(c) empirica entro 0.005 da (o·σ_p/EV)² = 0.0801 (verifica della catena Var(p̂) → Var(f̂) → Var(c)).
2. Scenario base, σ_p = 0.0283: Var(c) < 1.
3. Scenario sottile, σ_p = 0.0283: Var(c) > 1.
4. pytest -v e pytest -m slow passano.

Da misurare e riportare, senza farlo tornare: per entrambi gli scenari e per σ_p ∈ {0.015, 0.0283, 0.045}: E[c], E[c²], Var(c) empirica, Var(c) dalla formula lineare (o·σ_p/EV)², quota di scommesse con f̂ = 0. Non modificare σ_p né gli scenari per spostare questi valori.

Esito: 2026-09-27 — file toccati: src/shk/kelly/staking.py, tests/test_staking.py, tests/test_us_c1_2_acceptance.py. Deviazioni: funzione staking_moments(f_hat, f_star) con risultato StakingMoments(mean_c, mean_c2, var_c, fraction_zero), in staking.py perché estimation.py per vincolo non tratta frazioni; test unitario in tests/test_staking.py; riferimento del criterio 1 calcolato dai parametri dello scenario; generatore del rumore nuovo da spawn_generators(SEED)[1] per ogni combinazione di scenario e σ_p. Non fatto: nulla. Valori misurati (seed 20260927; per ogni riga E[c], E[c²], Var(c) empirica, Var(c) lineare, quota f̂ = 0). Base σ_p 0.015: 0.999988, 1.022479, 0.022503, 0.022500, 0.000000. Base σ_p 0.0283: 0.999991, 1.080053, 0.080072, 0.080089, 0.000203. Base σ_p 0.045: 1.002022, 1.201864, 0.197815, 0.202500, 0.013098. Sottile σ_p 0.015: 1.031868, 1.543004, 0.478253, 0.562500, 0.091241. Sottile σ_p 0.0283: 1.199995, 2.721659, 1.281670, 2.002225, 0.239729. Sottile σ_p 0.045: 1.484927, 4.884419, 2.679412, 5.062500, 0.328173. Test: pytest -v 42 passati; pytest -m slow 7 passati (13.39 s). Report: .agent/report/T5.md.

### Task 6 — λ* contro quarto-Kelly
Stato: da fare

Obiettivo: un test di accettazione mostra che, con rumore di stima per scommessa, λ* = 1/(1 + Var(c)), con Var(c) empirica, dà una crescita mediana maggiore del quarto-Kelly fisso; le varianti di λ previste dalla tesi sono misurate e riportate.

Dipende da: Task 1, Task 2, Task 3, Task 4, Task 5.

Contesto:
- Frazione giocata: f = λ·f̂, con f̂ dalla regola di Task 3 applicata a p̂ con rumore per scommessa (Task 2); Var(c), E[c] ed E[c²] dalla funzione di Task 5.
- Il confronto è appaiato: stessi esiti e stesse stime p̂ per tutti i valori di λ.
- Regola plug-in per scommessa, dalle note di tesi 3.2 §7.5: λ_t = 1/(1 + (o·σ_p/EV̂_t)²), con EV̂_t = p̂_t·o − 1, e f = 0 quando EV̂_t ≤ 0. È una nuova regola di staking da aggiungere in src/shk/kelly/staking.py senza toccare il motore.
- Scenari nel modulo creato in Task 4.

Da verificare prima di iniziare:
- Lo stato dei file toccati dai Task 1-5, leggendo i report in .agent/report/T1.md … T5.md e il campo Esito di questo backlog [D, finché la scheda non viene rimappata].

Passi richiesti:
1. Leggere i report T1-T5 e confrontarli con il codice attuale.
2. Proporre il piano: regola plug-in e struttura dei test. Attendere conferma.
3. Implementare la regola plug-in in src/shk/kelly/staking.py.
4. Aggiungere a tests/test_us_c1_2_acceptance.py il test del criterio 1, marcato slow.
5. Misurare i valori informativi ed eseguire pytest -v e pytest -m slow; controllare con git diff --stat che simulate.py non sia cambiato in questo task.

Vincoli:
- Non modificare il motore in simulate.py, né core.py, metrics.py o i file di C1.1.
- Nessun commit e nessuna operazione git che modifichi lo stato del repository.
- Commenti e docstring in italiano; identificatori, messaggi delle eccezioni e nomi dei test in inglese (è la convenzione del progetto).
- Prima di scrivere codice, proporre il piano e fare le domande necessarie.
- A fine task scrivere .agent/report/T6.md, unico file di .agent/ che si può toccare, con sezioni distinte: percorsi dei file modificati, creati o rimossi; esito di ciascun criterio; valori misurati; deviazioni dal piano; cose non fatte; comandi eseguiti.

Criteri di accettazione:
1. In entrambi gli scenari, con σ_p = 0.0283, la crescita mediana con λ* = 1/(1 + Var(c) empirica) è maggiore della crescita mediana con λ = 0.25.
2. git diff --stat non mostra modifiche a src/shk/kelly/simulate.py introdotte in questo task.
3. pytest -v e pytest -m slow passano.

Da misurare e riportare, senza farlo tornare: per entrambi gli scenari e per σ_p ∈ {0.015, 0.0283, 0.045}, crescita mediana, drawdown mediano e quota di traiettorie sotto il capitale iniziale con queste regole: λ* = 1/(1 + Var(c) empirica); λ = E[c]/E[c²]; λ = 1/(1 + (o·σ_p/EV)²) con la formula lineare; λ = 0.25; λ = 0.5; λ = 1; regola plug-in per scommessa. Per ogni combinazione, indicare se λ* batte λ = 0.25. Non modificare σ_p, scenari o seed per far vincere o perdere una regola.

Esito: —

### Task 7 — Script dell'esperimento C1.2, CSV e figura per la tesi
Stato: da fare

Obiettivo: uno script riproducibile rigenera tutte le misure dei Task 4-6 in un CSV e in una figura a due pannelli destinata alla tesi.

Dipende da: Task 4, Task 5, Task 6.

Contesto:
- Modello da seguire: scripts/us_c1_1_growth_vs_lambda.py. Usa matplotlib.use("Agg") prima di importare pyplot, importa direttamente da shk.kelly.<modulo>, tiene i parametri locali in run_experiment() e non legge argomenti da riga di comando; il blocco __main__ chiama run_experiment() [V, R2@2026-09-27].
- Gli output vanno in results/ e thesis/figures/ e sono versionati [V, R2@2026-09-27].
- Nome dei file: scripts/us_c1_2_estimation_error.py, results/us_c1_2_estimation_error.csv, thesis/figures/us_c1_2_estimation_error.png, secondo lo schema us_<storia>_<descrizione> [D, dedotto da un solo esempio].
- In questo script i parametri degli scenari vengono dal modulo creato in Task 4, non sono ripetuti.
- Il flusso di np.random.Generator non è garantito stabile fra versioni di NumPy, e le dipendenze non hanno versione fissata [D].

Da verificare prima di iniziare:
- Lo stato dei file toccati dai Task 1-6, leggendo i report in .agent/report/ [D, finché la scheda non viene rimappata].

Passi richiesti:
1. Proporre il piano: colonne del CSV e contenuto dei due pannelli. Attendere conferma.
2. Scrivere lo script con run_experiment(); il CSV ha una riga per combinazione di scenario, σ_p e regola, con le quantità misurate nei Task 4-6.
3. Figura a due pannelli. Pannello A: crescita mediana in funzione dell'errore relativo su p̂, da −20% a +20%, per entrambi gli scenari. Pannello B: crescita mediana in funzione di λ con σ_p = 0.0283, per entrambi gli scenari, con λ* e λ = 0.25 marcati.
4. Eseguire lo script due volte e confrontare i due CSV prodotti.
5. Eseguire pytest -v e pytest -m slow.

Vincoli:
- Non modificare codice in src/ né i file di C1.1; non rieseguire lo script di C1.1.
- Nessun print, logging o try nello script.
- Nessun commit e nessuna operazione git che modifichi lo stato del repository: CSV e PNG li committa il programmatore.
- Commenti e docstring in italiano; identificatori, messaggi delle eccezioni e nomi dei test in inglese (è la convenzione del progetto).
- Prima di scrivere codice, proporre il piano e fare le domande necessarie.
- A fine task scrivere .agent/report/T7.md, unico file di .agent/ che si può toccare, con sezioni distinte: percorsi dei file modificati, creati o rimossi; esito di ciascun criterio; valori misurati; deviazioni dal piano; cose non fatte; comandi eseguiti.

Criteri di accettazione:
1. Lo script produce results/us_c1_2_estimation_error.csv e thesis/figures/us_c1_2_estimation_error.png.
2. Due esecuzioni consecutive producono CSV identici byte per byte (seed impostabile e risultati riproducibili).
3. I valori del CSV coincidono con quelli riportati nei report T4, T5 e T6, entro 1e-12.
4. Lo script rispetta le convenzioni del modello C1.1 elencate nel Contesto.
5. I file di C1.1 in results/ e thesis/figures/ non risultano modificati (git status).
6. pytest -v e pytest -m slow passano.

Esito: —

### Fuori scope di S1
- Barriera assorbente o floor nel motore (growth_engine con floor, note di tesi 2.5 §11.1): appartiene ai checkpoint successivi.
- Controllo di sanità sulle frequenze di drawdown ≈ α^(2/λ−1): le note 2.5 §10.4 lo collocano al checkpoint C1, ma nessuna story lo chiede. Può diventare una US-C1.4, se il programmatore la scrive.
- Errore di stima persistente per traiettoria o bias comune (note 2.5 §3.3).
- Stima di σ_p dai residui (Modulo 2) e λ* dinamico nel tempo.
- Kelly bayesiano o robusto (Baseline F).
- Correzioni aperte da C1.1: parametri duplicati fra script e test di C1.1, test di expected_final_wealth, re-export in __init__, allineamento della CI a uv.
- Scommesse simultanee e Kelly congiunto.

### Resta al programmatore per S1
- Definition of Done di US-C1.2: un caso numerico in cui λ* batte il quarto-Kelly fisso e uno in cui non lo fa. La tabella informativa del Task 6 fornisce i candidati, ma la scelta e la spiegazione sono sue.
- Confermare o correggere le scelte di scenario e di rumore elencate in Assunzioni fatte prima di avviare il Task 4.
- Commit del codice, del CSV e della figura al termine dei task.
- Rimappatura del progetto fra il Task 5 e il Task 6.