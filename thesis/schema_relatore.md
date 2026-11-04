# Lo schema del relatore e il progetto

Questo documento confronta, punto per punto, la soluzione Structural-Hybrid proposta dal relatore con quello che il progetto implementa: che cosa è fatto alla lettera, che cosa è interpretato, che cosa manca e che cosa dicono i risultati.

Le richieste del relatore sono riassunte con parole mie: le sue mail sono riservate e non sono riportate. I dettagli tecnici sono in `thesis/agenti_e_architettura.md` e i risultati in `thesis/conclusioni_progetto.md`; qui ci sono solo i rimandi.

## 1. Lo schema in breve

**La proposta.** Un agente gerarchico, in cui chi scommette è solo il braccio e un agente di secondo livello controlla il rischio:
- **Modulo 1, il lavoratore:** fa le previsioni, con modelli classici o con un LLM.
- **Modulo 2, il supervisore:** controlla i residui del lavoratore con l'ANOVA. Quando l'eteroschedasticità aumenta, cioè la media degli errori cresce e la varianza esplode, dà l'allarme.
- **Modulo 3, il ricalibratore:** con la decomposizione di Blinder-Oaxaca capisce che tipo di errore è:
  - un errore nei dati (per esempio un infortunio improvviso): si riduce un po' la puntata;
  - un errore strutturale (il mercato è cambiato, la squadra è cambiata): il rischio va quasi a zero finché il modello non viene ri-parametrizzato, oppure si cambia modello.

L'ipotesi del relatore è che un agente così, consapevole dei propri limiti, non solo non fallisca ma batta il mercato.

**Le tre risposte successive**, a domande mie:
1. **Che cosa fa l'allarme strutturale?** Un moltiplicatore che riduce la puntata del lavoratore, oppure far ri-parametrizzare il modello: vanno bene entrambi, con preferenza per il moltiplicatore.
2. **Chi sceglie l'esito su cui puntare?** Il relatore propone di provare anche a far scegliere l'esito al lavoratore, invece della sola regola fissa.
3. **Su che lavoratore si dimostra il supervisore?** Opzione A: lavoratori classici (Elo, Dixon-Coles) e un LLM che sceglie esito e puntata senza costruirsi i modelli, con il supervisore che agisce sulla puntata. L'agente autonomo come quello di KellyBench (opzione B) non è richiesto.

## 2. Confronto punto per punto

| Richiesta | Come è implementata | Dove | Stato |
|---|---|---|---|
| Lavoratore con modelli classici | Elo e Dixon-Coles danno le probabilità 1X2 di ogni partita | `src/shk/model/module1.py`; `conclusioni_progetto.md` §3.2 | Fatto |
| Lavoratore LLM | DeepSeek Flash, con data, squadre, forma recente e classifica, senza quote | `src/shk/model/llm_module1.py` (predisposto, non versionato) | Da fare: fase 2 |
| Supervisore: ANOVA sui residui | Agente C3. Due test fra le ultime 40 partite e le 40 precedenti: ANOVA a una via sulla media degli errori e Brown-Forsythe (ANOVA sulle distanze dalla mediana) sulla dispersione | `src/shk/model/agent_c.py` (`scheme_statistics`); `agenti_e_architettura.md` §3.7 | Fatto |
| Allarme quando media e varianza crescono | C3 dà l'allarme se uno dei due test supera la soglia; C3_and, alla lettera, solo se la superano tutti e due | `agent_c.py` (`SchemeAgent`, `alarm`) | Fatto, in due versioni |
| Ricalibratore: Oaxaca separa dato e struttura | Decomposizione three-fold dei residui; errore strutturale se la componente strutturale supera la soglia calibrata, altrimenti errore di composizione | `src/shk/stats/oaxaca.py`, `src/shk/model/module2.py` | Fatto |
| Errore nei dati: ridurre un po' la puntata | λ da 0,25 a 0,25 · 0,75 = 0,1875 finché dura l'allarme | `SchemeAgent` | Fatto |
| Errore strutturale: rischio quasi a zero finché il modello non è ri-parametrizzato | λ = 0. C3 riparte quando l'allarme si spegne; C3_stop resta a zero fino a fine stagione, perché il Modulo 1 si ri-parametrizza solo ai fit | `SchemeAgent` (`stop`) | Fatto, in due letture |
| Errore strutturale: cambiare modello | – | – | Non implementato |
| Risposta 1: moltiplicatore sulla puntata | La puntata è f = λ · f_w: il supervisore scala la frazione proposta dal lavoratore senza toccarlo | `src/shk/kelly/agents.py` | Fatto |
| Risposta 1: ri-parametrizzare il modello dopo l'allarme | Il Modulo 1 si ricalibra solo ai fit 2000-01, 2010-11, 2020-21, mai per un allarme | – | Non implementato (seconda scelta del relatore) |
| Risposta 2: il lavoratore sceglie l'esito | Tre regole: EV massimo (R1, quella di prima), maggior vantaggio sul mercato (R2), esito più probabile (R3), ciascuna da sola, con freno fisso e con i supervisori | `src/shk/kelly/outcome_rules.py`, `src/shk/model/worker_run.py`; `agenti_e_architettura.md` §3.8 | Fatto con l'Elo; Dixon-Coles da fare |
| Risposta 3: opzione A | Lavoratori classici fatti; LLM da fare. L'opzione B è dichiarata come limite | `thesis/disegno_lavoratore.md` | In corso |

## 3. Le scelte di interpretazione

Lo schema non fissa alcuni dettagli. Queste sono le scelte fatte, con il motivo:
- **Che cosa sono i residui.** δ = ln p̂(esito reale) − ln q(esito reale), dove q è la probabilità del mercato senza margine (de-vigging di Shin). Misura quanto il modello sbaglia rispetto al mercato, che è ciò che conta per scommettere.
- **«Eteroschedasticità che aumenta».** Conta solo se le partite recenti sono più disperse delle precedenti; allo stesso modo, il test sulla media conta solo se gli errori recenti sono peggiori. Un miglioramento non deve far scattare l'allarme.
- **Le soglie.** Le soglie nominali dell'ANOVA non valgono su serie di errori autocorrelate (`conclusioni_progetto.md` §4.2). Sono calibrate sul training con il block bootstrap, al 5% di falsi allarmi in tutto.
- **La puntata senza allarme.** Lo schema non dice quanto puntare quando va tutto bene. Si usa il quarto di Kelly (λ = 0,25), la stessa base degli altri agenti.
- **«Ridurre un po'».** κ = 0,75 e la soglia della componente strutturale sono quelli già congelati per C1: C3 non ha parametri calibrati di nuovo.
- **«Finché il modello non viene ri-parametrizzato».** Due letture: fino a quando l'allarme si spegne (C3) o fino a fine stagione (C3_stop).

## 4. Che cosa c'è in più rispetto allo schema

Il progetto contiene anche agenti che non vengono dallo schema ma dalle note di progetto. Servono da confronto (ablazione):
- **C1:** usa direttamente la componente strutturale di Oaxaca come allarme, senza ANOVA, e riduce λ a ogni allarme.
- **C2:** non ha allarme; gradua λ in modo continuo con la formula λ*.
- **D_ADWIN, D_PH:** lo stesso Kelly frazionario con un detector di drift standard al posto del supervisore.
- **A, B, C0, E:** Kelly pieno, Kelly frazionario fisso e puntata minima.

C1 e C2 non hanno l'ANOVA perché, con soglie corrette, l'eteroschedasticità crescente non si osserva (`conclusioni_progetto.md` §4.4). C3 rimette l'ANOVA per seguire lo schema.

**I nomi nel codice.** Per ragioni storiche nel codice «Modulo 2» è Oaxaca-Blinder (`shk.model.module2`) e «Modulo 3» è la formula λ* (`shk.model.module3`). Nei documenti si usano i nomi del relatore; la corrispondenza è in `agenti_e_architettura.md` §1.

## 5. Le ipotesi dello schema alla prova

Risultati sulle 19 stagioni di validazione, 500 seed, floor di £0,01 (somma sulle stagioni della mediana di ln W_T). C3 non è stato eseguito sul test 2023-24, già usato una volta.

| Ipotesi dello schema | Esito | Dove |
|---|---|---|
| L'agente batte il mercato | No. Il vantaggio stimato del modello sul mercato è negativo, con l'Elo e con Dixon-Coles; nessun agente che punta guadagna | `conclusioni_progetto.md` §4.1 |
| L'eteroschedasticità crescente segnala il degrado | Poco. Con soglie corrette i test sulla varianza rigettano in 0–3 stagioni su 19; l'allarme di C3 scatta circa 1,6 volte per stagione | §4.4 |
| Oaxaca distingue errore nei dati ed errore strutturale | Sui dati sintetici sì; sui dati reali le due componenti non si separano dove ci si aspetta (per esempio la sospensione Covid) | §4.6 |
| Lo schema limita le perdite | Un poco. Rispetto al quarto di Kelly fisso (−10,87), C3 arriva a −10,62 e C3_stop a −7,51, senza mai fare peggio in mediana. Gli agenti che puntano meno perdono meno: C1 −5,14, C2 −5,02, D_PH −3,43 | `agenti_e_architettura.md` §3.7 |
| Con l'allarme congiunto (media e varianza) va meglio | No: C3_and dà −10,67, quasi come C3 | §3.7 |
| Il supervisore funziona con lavoratori diversi | Sì: con le tre regole di scelta dell'esito, C1 e C2 battono il freno fisso in 15–18 stagioni su 19; C3 non è mai peggiore | §3.8 |

**Lettura.** Lo schema è implementato e si comporta come descritto: riduce poco la puntata con errori di composizione e la azzera con errori strutturali. Il suo effetto è piccolo per due ragioni:
- il segnale che cerca, una varianza degli errori che esplode, sui dati reali è raro;
- il modello non batte il mercato, quindi vince chi punta meno, e lo schema punta di più degli agenti che riducono λ in modo permanente (C1) o continuo (C2).

## 6. Che cosa resta da fare

- **Fase 1 con Dixon-Coles:** le stesse regole del lavoratore con l'altro modello classico.
- **Fase 2, il lavoratore LLM:** sceglie esito e puntata senza vedere le quote, sul 2023-24, in modo esplorativo. Prima vanno decise due cose (`disegno_lavoratore.md` §8):
  - come si combinano λ e la puntata proposta dall'LLM;
  - il tetto alla puntata, proposto al 10% del bankroll.
- **Ri-parametrizzare o cambiare modello dopo un allarme strutturale:** non implementato. Il relatore preferisce il moltiplicatore sulla puntata, che è fatto; questa parte è facoltativa.
- **Opzione B**, l'agente autonomo come quello di KellyBench: fuori dal perimetro della tesi, da dichiarare come limite.
