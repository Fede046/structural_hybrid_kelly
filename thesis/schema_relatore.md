# Structural-Hybrid Kelly: che cosa ho realizzato

Federico Malservigi, novembre 2026

Questo documento descrive come ho realizzato la soluzione Structural-Hybrid che mi ha proposto, come ho applicato le sue indicazioni e che cosa mostrano i risultati. Alla fine ci sono alcune domande su cui mi servirebbe una sua scelta prima di andare avanti.

## 1. In sintesi

- Ho realizzato lo schema com'era nella proposta:
  - il lavoratore prevede;
  - il supervisore controlla i residui con l'ANOVA e dà l'allarme;
  - il ricalibratore usa Blinder-Oaxaca per distinguere un errore nei dati da un errore strutturale e decide la puntata.
- Il supervisore agisce con un moltiplicatore sulla puntata del lavoratore, come da sua preferenza.
- Il lavoratore può anche scegliere l'esito su cui puntare, con tre regole diverse.
- Il lavoratore LLM (opzione A) è predisposto ma non ancora eseguito.
- Risultato principale: il modello previsivo non batte il mercato, quindi ogni agente che punta perde. Lo schema limita un po' le perdite rispetto al lavoratore senza supervisore.

## 2. Lo schema realizzato

**Modulo 1, il lavoratore.** Due modelli classici, Elo e Dixon-Coles, danno le probabilità di vittoria in casa, pareggio e vittoria in trasferta di ogni partita. La puntata proposta dal lavoratore è la frazione di Kelly calcolata su quelle probabilità.

**Modulo 2, il supervisore.** Dopo ogni partita guarda l'errore del lavoratore rispetto al mercato. Il residuo confronta due probabilità dell'esito reale, in scala logaritmica: quella data dal modello e quella implicita nelle quote, depurata dal margine del bookmaker. A ogni giornata il supervisore confronta le ultime 40 partite con le 40 precedenti, con due test:
- l'ANOVA a una via sulla media dei residui segnala se gli errori recenti sono peggiori;
- il test di Brown-Forsythe, cioè l'ANOVA sulle distanze dalla mediana, segnala se la dispersione è aumentata, quindi l'eteroschedasticità.

Ho provato due versioni dell'allarme: nella prima basta che peggiori la media o che cresca la dispersione; nella seconda devono succedere tutte e due le cose insieme («la media degli errori cresce e la varianza esplode»).

Le soglie non sono quelle nominali dell'ANOVA, perché le serie di errori sono autocorrelate. In quel caso l'ANOVA nominale dà molti falsi allarmi: in simulazione fino al 40% invece del 5%. Ho quindi calibrato le soglie sulle stagioni di training con un bootstrap a blocchi, così i falsi allarmi restano al più al 5%.

**Modulo 3, il ricalibratore.** Quando scatta l'allarme, la decomposizione di Blinder-Oaxaca divide il peggioramento dei residui in due parti:
- una dovuta a partite diverse (composizione, cioè errore nei dati);
- una dovuta a un cambiamento della relazione fra le caratteristiche delle partite e l'errore (struttura).

Se la parte strutturale supera una soglia calibrata, l'errore è strutturale; altrimenti è un errore nei dati. La puntata diventa:

| Situazione | Frazione della puntata di Kelly |
|---|---|
| Nessun allarme | 0,25 (quarto di Kelly) |
| Errore nei dati | 0,19, finché dura l'allarme |
| Errore strutturale | 0 |

Per l'errore strutturale ho seguito due letture di «finché il modello non viene ri-parametrizzato»:
- si torna a puntare quando l'allarme si spegne;
- si resta fermi fino a fine stagione, perché nel mio impianto il modello viene ri-parametrizzato solo fra una stagione e l'altra.

## 3. Come ho applicato le sue indicazioni

**Moltiplicatore o ri-parametrizzazione.** Ho realizzato il moltiplicatore: il supervisore scala la puntata proposta dal lavoratore e non tocca il modello. Non ho implementato né la ri-parametrizzazione del modello dopo un allarme né il cambio di modello.

**La scelta dell'esito.** Prima l'esito su cui puntare seguiva una regola fissa. Ora il lavoratore può sceglierlo con tre regole:
- l'esito con il valore atteso più alto, cioè la regola di prima;
- l'esito in cui il modello si discosta di più dal mercato;
- l'esito più probabile secondo il modello.

In tutti i casi si punta solo se il valore atteso stimato è positivo, e il supervisore agisce sulla puntata.

**Opzione A.** I lavoratori classici sono pronti; per ora li ho provati con l'Elo. Il lavoratore LLM sceglierà esito e puntata a partire da data, squadre, forma recente e classifica, senza vedere le quote. 

## 4. Come ho valutato

- **Dati.** Premier League, quote Bet365, stagioni dal 2000-01 al 2023-24.
- **Separazione dei dati.** Ho calibrato tutti i parametri su tre stagioni di training (2000-01, 2010-11, 2020-21) e poi li ho congelati. La valutazione è sulle altre 19 stagioni, dal 2002-03 al 2022-23. Il 2023-24, la stagione di KellyBench, l'ho usato come test una volta sola, alla fine. Lo schema l'ho costruito dopo, e su quella stagione l'ho provato una sola volta (§5).
- **Ambiente.** Ho riprodotto le regole di KellyBench: si gioca giornata per giornata, con una puntata minima obbligatoria, e si usano solo informazioni disponibili prima della partita.
- **Simulazioni.** Ogni stagione è giocata 500 volte. Ogni volta la stagione è ricostruita ricampionando le giornate, così si ottiene una distribuzione dei risultati e non un solo valore.
- **Riferimento.** Per vedere che cosa aggiunge il supervisore, lo schema è confrontato con lo stesso lavoratore senza supervisore, sulle stesse partite e con le stesse simulazioni:
  - con il Kelly pieno, cioè il lavoratore da solo;
  - con il quarto di Kelly fisso, cioè la puntata dello schema quando non c'è allarme.

## 5. Risultati

**Il modello non batte il mercato.** In media il modello assegna all'esito che si verifica una probabilità più bassa di quella del mercato. Lo misuro con la media, su tutte le partite, della differenza fra i logaritmi delle due probabilità: −0,022 con le quote Bet365, intervallo al 95% da −0,030 a −0,015. Resta negativa con Dixon-Coles e con tutti i metodi per togliere il margine dalle quote. Quindi ogni agente che punta perde in media, e il supervisore può solo ridurre la perdita.

Capitale rimasto a fine stagione, in una stagione tipica delle 19 di validazione:

| Agente | Quando scatta l'allarme | Dopo un errore strutturale | Capitale rimasto |
|---|---|---|---|
| Lavoratore da solo, Kelly pieno | – | – | 0,2% |
| Lavoratore con il quarto di Kelly, senza supervisore | – | – | 56% |
| Schema | Peggiora la media o cresce la varianza | Riprende quando l'allarme si spegne | 57% |
| Schema | Peggiorano media e varianza insieme | Riprende quando l'allarme si spegne | 57% |
| Schema | Peggiora la media o cresce la varianza | Fermo fino a fine stagione | 67% |

Il lavoratore qui sceglie l'esito con il valore atteso più alto. Per ogni agente: mediana sulle 500 simulazioni di ogni stagione, poi media geometrica sulle 19 stagioni.

**Che cosa si vede:**
- **Lo schema funziona come previsto, ma interviene poco.** Il segnale che cerca, una varianza degli errori che cresce, sui dati reali è raro: l'allarme scatta circa 1,6 volte per stagione. Lo schema non fa mai peggio del lavoratore senza supervisore; la versione che resta ferma fino a fine stagione fa meglio in 9 stagioni su 19.
- **Sui dati reali Oaxaca separa poco i due tipi di errore.** Sui dati simulati la decomposizione funziona. Nella sospensione per il Covid del 2019-20, dove mi aspettavo un errore strutturale, la parte strutturale è quasi nulla.
- **Più si riduce la puntata, meno si perde.** Con un vantaggio negativo, ogni riduzione della puntata riduce la perdita. Per questo la versione che resta ferma fino a fine stagione è la migliore delle tre: le altre, quando l'allarme si spegne, tornano al quarto di Kelly.
- **Lo schema funziona con tutte e tre le regole di scelta dell'esito.** Non fa mai peggio del lavoratore senza supervisore e fa meglio in 5–6 stagioni su 19.
- **La regola migliore è puntare sull'esito più probabile.** Si scommette su circa metà delle partite e si perde meno: con lo schema resta il 67% del capitale, invece del 57% con la regola del valore atteso più alto.

**La stagione 2023-24, quella di KellyBench.** L'ho giocata come in KellyBench: esiti veri, giornata per giornata, partendo da £100 000. Avevo già usato questa stagione come test prima di costruire lo schema, quindi il risultato dello schema è solo esplorativo: l'ho eseguito una volta sola, senza cambiare nessun parametro.

| Agente | Capitale finale |
|---|---|
| Lavoratore da solo, Kelly pieno | £14 |
| Lavoratore con il quarto di Kelly, senza supervisore | £24 358 |
| Schema, allarme se peggiora la media o cresce la varianza | £24 424 |
| Schema, come sopra ma fermo fino a fine stagione | £24 424 |
| Schema, allarme solo se peggiorano media e varianza insieme | £26 755 |

Come nelle 19 stagioni di validazione, lo schema cambia poco il risultato del quarto di Kelly.

## 6. Altre analisi di supporto

Ho fatto anche alcune analisi che lo schema non prevede, ma che aiutano a leggerne i risultati.

**Test di eteroschedasticità sui residui.** Per capire se il segnale che lo schema cerca esiste davvero, ho applicato ai residui del modello i test classici:
- Breusch-Pagan e White con le soglie nominali rigettano in tutte le 19 stagioni, ma solo perché la varianza dell'errore dipende per costruzione da quanto è incerta la previsione;
- con soglie calibrate col bootstrap i rigetti scendono a zero;
- i test sulla varianza che cresce nel corso della stagione (Breusch-Pagan sul tempo, Goldfeld-Quandt, ARCH) rigettano in 0–3 stagioni su 19.

Questo spiega perché l'allarme dello schema scatta di rado.

**Z-test per giornata.** È un modo più semplice di dare l'allarme: confronta l'errore medio di ogni giornata con quello del training. Sulle 19 stagioni, con 1,9 falsi allarmi attesi per stagione (36 in tutto), la soglia nominale dà 53 allarmi e quella calibrata 43. Anche qui, quindi, gli allarmi sono di poco sopra quelli attesi per caso.

**Le squadre neopromosse.** Mi aspettavo che fossero il caso tipico di errore nei dati, perché il modello le conosce poco. Ho confrontato l'errore sulle loro partite a inizio stagione e nel resto della stagione, al netto delle altre squadre (differenza nelle differenze): −0,019, con intervallo al 95% da −0,040 a +0,003. La differenza non è significativa.

**La puntata minima obbligatoria e la rovina.** KellyBench obbliga a puntare almeno un minimo a ogni giornata. Ho verificato che questa regola rende possibile la rovina, che con Kelly puro non può avvenire. Con il capitale iniziale di £220 dello scenario di KellyBench:
- senza puntata minima nessun agente va in rovina;
- con una puntata minima di £0,01 il Kelly pieno va in rovina nel 17,9% dei casi, con £1 nel 69,0%;
- il quarto di Kelly va in rovina solo con £1, nello 0,5% dei casi.

## 7. Che cosa resta da fare

- Le stesse prove dei lavoratori con il modello Dixon-Coles.
- Il lavoratore LLM, sulla stagione 2023-24, in modo esplorativo, per due motivi:
  - quella stagione è già stata usata come test;
  - l'LLM potrebbe conoscerne i risultati dal proprio addestramento.
- La stesura dei capitoli della tesi.

## 8. Domande per lei

1. **La puntata dell'LLM.** Il supervisore deve moltiplicare per 0,25 la puntata proposta dall'LLM anche senza allarme, come per i lavoratori classici? Oppure deve intervenire solo con l'allarme, lasciando invariata la puntata dell'LLM finché va tutto bene?
2. **Un tetto alla puntata dell'LLM.** Pensavo di non permettere più del 10% del capitale su una singola partita. Le va bene?
3. **La ri-parametrizzazione.** Lei aveva indicato il moltiplicatore come prima scelta: basta quello, o vuole che implementi anche la ri-parametrizzazione del modello dopo un errore strutturale?
4. **La versione principale.** Nella tesi presenterei come versione principale quella in cui basta che peggiori la media o che cresca la varianza, e si riprende a puntare quando l'allarme si spegne, con le altre come varianti. Le sembra corretto?

Il codice e tutti i risultati sono riproducibili e a sua disposizione.
