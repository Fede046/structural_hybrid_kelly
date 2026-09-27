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

Esito: 2026-09-27 — file toccati: src/shk/kelly/simulate.py, tests/test_simulate.py. Deviazioni: motore chiamato simulate_growth(outcomes, fractions, b); frazioni accettate solo con broadcasting NumPy standard verso (M, T), cioè scalare, (T,), (1, T), (M, 1), (M, T), e una frazione per traiettoria si passa come (M, 1); aggiunto il rifiuto delle frazioni non finite; criterio 4 verificato con git grep e firma nel report invece che con un test. Non fatto: nulla. Da confermare nel Task 2: che le formule dei fattori logaritmici siano rimaste np.log(1 + b*f) e np.log(1 - f), senza log1p. Valori misurati: pytest -v 26 passati e 4 deselezionati; pytest -m slow 4 passati (12.75 s); discrepanza 0.0 sui criteri 2 e 3; log_wealth_paths e simulate_growth danno array identici. Report: .agent/report/T1.md.

### Task 2 — Generatore di stime perturbate p̂
Stato: da fare

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

Esito: —

### Task 3 — Regola di staking Kelly sulla stima, con troncamento e moltiplicatore λ
Stato: da fare

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

Esito: —

### Task 4 — Simulazione con p̂ ≠ p e asimmetria sovrastima/sottostima
Stato: da fare

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

Da misurare e riportare, senza farlo tornare: crescita mediana e drawdown mediano con p̂ = 1.1·p e p̂ = 0.9·p, in entrambi gli scenari, con la loro differenza. Nello scenario base il segno della