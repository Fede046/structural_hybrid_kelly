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
- Risultato principale: il modello previsivo non batte il mercato, quindi ogni agente che punta perde.
- Se il supervisore confronta gli errori recenti con quelli delle 40 partite precedenti, lo schema interviene poco. Se li confronta con quelli della stagione su cui il modello è stato calibrato, si accorge che il modello invecchia e il mercato lo supera: punta meno proprio allora e conserva più capitale: in una stagione tipica il 71%, contro il 57% del lavoratore senza supervisore, e fa meglio in 14 stagioni su 19.

## 2. Lo schema realizzato

**Modulo 1, il lavoratore.** Due modelli classici, Elo e Dixon-Coles, danno le probabilità di vittoria in casa, pareggio e vittoria in trasferta di ogni partita. La puntata proposta dal lavoratore è la frazione di Kelly calcolata su quelle probabilità.

**Modulo 2, il supervisore.** Dopo ogni partita guarda l'errore del lavoratore rispetto al mercato. Il residuo confronta due probabilità dell'esito reale, in scala logaritmica: quella data dal modello e quella implicita nelle quote, depurata dal margine del bookmaker. A ogni giornata il supervisore confronta le ultime 40 partite con le 40 precedenti, con due test:
- l'ANOVA a una via sulla media dei residui segnala se gli errori recenti sono peggiori;
- il test di Brown-Forsythe, cioè l'ANOVA sulle distanze dalla mediana, segnala se la dispersione è aumentata, quindi l'eteroschedasticità.

Ho provato due versioni dell'allarme: nella prima basta che peggiori la media o che cresca la dispersione; nella seconda devono succedere tutte e due le cose insieme («la media degli errori cresce e la varianza esplode»).

Ho provato anche due modi di scegliere il confronto:
- **le 40 partite precedenti**, cioè il confronto fra un periodo e quello subito prima;
- **la stagione su cui il modello è stato calibrato**, cioè il confronto fra gli errori di oggi e quelli del momento in cui il modello «era a posto». Il modello peggiora lentamente, di stagione in stagione: il confronto con il periodo subito prima non lo vede, quello con la stagione di calibrazione sì.

Le soglie non sono quelle nominali dell'ANOVA, perché le serie di errori sono autocorrelate. In quel caso l'ANOVA nominale dà molti falsi allarmi: in simulazione fino al 40% invece del 5%. Ho quindi calibrato le soglie sulle stagioni di training con un bootstrap a blocchi, così i falsi allarmi restano al più al 5%.

**Modulo 3, il ricalibratore.** Quando scatta l'allarme, la decomposizione di Blinder-Oaxaca divide il peggioramento dei residui in due parti:
- una dovuta a partite diverse (composizione, cioè errore nei dati);
- una dovuta a un cambiamento della relazione fra le caratteristiche delle partite e l'errore (struttura).

Se la parte strutturale supera una soglia calibrata, l'errore è strutturale; altrimenti è un errore nei dati. La puntata diventa:

| Situazione         | Frazione della puntata di Kelly |
| ------------------ | ------------------------------- |
| Nessun allarme     | 0,25 (quarto di Kelly)          |
| Errore nei dati    | 0,19, finché dura l'allarme     |
| Errore strutturale | 0                               |

Per l'errore strutturale ho seguito due letture di «finché il modello non viene ri-parametrizzato»:
- si torna a puntare quando l'allarme si spegne;
- si resta fermi fino a fine stagione, perché nel mio impianto il modello viene ri-parametrizzato solo fra una stagione e l'altra.

## 3. Come ho applicato le sue indicazioni

**Moltiplicatore o ri-parametrizzazione.** Ho realizzato il moltiplicatore: il supervisore scala la puntata proposta dal lavoratore e non tocca il modello. Per provare anche la seconda strada ho ri-parametrizzato il modello ogni anno: prima di ogni stagione lo ricalibro sulla stagione precedente. Prima della partita il modello si avvicina al mercato (in 14 stagioni su 18), ma non prevede meglio i risultati, e il capitale peggiora in tutte le versioni: con lo schema fermo fino a fine stagione resta il 67% invece del 71%, con il quarto di Kelly il 46% invece del 57%. Il motivo è che una stagione sola è poca per stimare bene i parametri. Per esempio, sul 2020-21, giocato a porte chiuse, il vantaggio del campo stimato è nullo, e il modello se lo porta nel 2021-22, quando il pubblico era tornato. Lo schema resta utile anche sul modello ricalibrato: fa meglio del quarto di Kelly in 12–13 stagioni su 19. Non ho implementato né la ri-parametrizzazione subito dopo un allarme né il cambio di modello.

**La scelta dell'esito.** Per ogni partita il modello dà tre probabilità (casa, pareggio, trasferta), ma il lavoratore punta su un solo esito. La regola di scelta decide quale. Ne ho provate tre, nessuna con parametri da stimare:
- **valore atteso più alto**: l'esito per cui probabilità del modello × quota − 1 è massimo. È la regola usata finora, e quella della tabella principale (§5);
- **scarto maggiore dal mercato**: l'esito in cui la probabilità del modello supera di più quella implicita nelle quote, depurata dal margine;
- **esito più probabile**: l'esito a cui il modello dà la probabilità più alta, senza guardare le quote.

Scelto l'esito, il resto è uguale per tutte e tre. Si punta solo se il valore atteso stimato di quell'esito è positivo, altrimenti si salta la partita. La puntata è la frazione di Kelly su quell'esito, e il supervisore la moltiplica come al solito. La regola cambia quindi su quale esito si punta, non quanto.

Un esempio: con quote 1,90 / 3,60 / 4,50 e probabilità del modello 0,48 / 0,30 / 0,22, le prime due regole scelgono il pareggio (valore atteso +8%). La terza sceglie la vittoria in casa, che ha valore atteso negativo (−9%), quindi su quella partita non si punta. È il motivo per cui con la terza regola si scommette su meno partite (§5).

Le tre regole le ho provate con il modello Elo; con Dixon-Coles non ancora.

**Opzione A.** I lavoratori classici sono pronti. Il lavoratore LLM sceglierà esito e puntata a partire da data, squadre, forma recente e classifica, senza vedere le quote. 

## 4. Come ho valutato

- **Dati.** Premier League, quote Bet365, stagioni dal 2000-01 al 2023-24.
- **Separazione dei dati.** Ho calibrato tutti i parametri su tre stagioni di training (2000-01, 2010-11, 2020-21) e poi li ho congelati. La valutazione è sulle altre 19 stagioni, dal 2002-03 al 2022-23. Il 2023-24, la stagione di KellyBench, l'ho usato come test una volta sola, alla fine. Lo schema l'ho costruito dopo, e su quella stagione l'ho provato una sola volta (§5).
- **Quale modello in quale stagione.** Ogni stagione di valutazione usa i parametri dell'ultima stagione di training che la precede: quelli del 2000-01 dal 2002-03 al 2009-10, quelli del 2010-11 dal 2011-12 al 2019-20, quelli del 2020-21 dal 2021-22 al 2023-24. Il modello quindi non viene aggiornato ogni anno e invecchia fino a nove stagioni. Il 2001-02 è escluso perché mancano quote complete.
- **Ambiente.** Ho riprodotto le regole di KellyBench: si gioca giornata per giornata, con una puntata minima obbligatoria, e si usano solo informazioni disponibili prima della partita.
- **Ogni stagione è una partita a sé.** Ogni stagione parte dallo stesso capitale, e quello che resta a fine stagione non passa alla successiva, come in KellyBench, dove si gioca una sola stagione.
- **Stagioni vere.** Il risultato principale è quello delle stagioni vere, ognuna giocata una volta, come in KellyBench.
- **Stagioni ricostruite, solo come misura dell'incertezza.** Per vedere quanto conta la fortuna, ogni stagione è anche ricostruita 500 volte ricampionando le giornate. Le partite, le quote e i risultati sono veri, ma alcune giornate si ripetono e altre saltano. Questo altera proprio la sequenza nel tempo che il supervisore osserva, quindi non le uso come risultato principale.
- **Riferimento.** Per vedere che cosa aggiunge il supervisore, lo schema è confrontato con lo stesso lavoratore senza supervisore, sulle stesse partite e con le stesse simulazioni:
  - con il Kelly pieno, cioè il lavoratore da solo;
  - con il quarto di Kelly fisso, cioè la puntata dello schema quando non c'è allarme.

## 5. Risultati

**Il modello non batte il mercato.** In media il modello assegna all'esito che si verifica una probabilità più bassa di quella del mercato. Lo misuro con la media, su tutte le partite, della differenza fra i logaritmi delle due probabilità: −0,022 con le quote Bet365, intervallo al 95% da −0,030 a −0,015. Resta negativa con Dixon-Coles e con tutti i metodi per togliere il margine dalle quote. Quindi ogni agente che punta perde in media, e il supervisore può solo ridurre la perdita.

Capitale rimasto a fine stagione nelle 19 stagioni vere di validazione:

| Agente                                               | Confronto con            | Quando scatta l'allarme                | Dopo un errore strutturale          | Capitale rimasto | Stagioni meglio / peggio del quarto di Kelly | Stagioni ricostruite |
| ---------------------------------------------------- | ------------------------ | -------------------------------------- | ----------------------------------- | ---------------- | -------------------------------------------- | -------------------- |
| Lavoratore da solo, Kelly pieno                      | –                        | –                                      | –                                   | 0,2%             | 0 / 19                                       | 0,2%                 |
| Lavoratore con il quarto di Kelly, senza supervisore | –                        | –                                      | –                                   | 57%              | –                                            | 56%                  |
| Schema                                               | 40 partite precedenti    | Peggiora la media o cresce la varianza | Riprende quando l'allarme si spegne | 60%              | 10 / 6                                       | 57%                  |
| Schema                                               | 40 partite precedenti    | Peggiorano media e varianza insieme    | Riprende quando l'allarme si spegne | 56%              | 6 / 7                                        | 57%                  |
| Schema                                               | 40 partite precedenti    | Peggiora la media o cresce la varianza | Fermo fino a fine stagione          | 71%              | 12 / 4                                       | 67%                  |
| Schema                                               | Stagione di calibrazione | Peggiora la media o cresce la varianza | Riprende quando l'allarme si spegne | 62%              | 14 / 5                                       | 62%                  |
| Schema                                               | Stagione di calibrazione | Peggiora la media o cresce la varianza | Fermo fino a fine stagione          | 71%              | 14 / 5                                       | 79%                  |

Il lavoratore qui sceglie l'esito con il valore atteso più alto. Il capitale rimasto è la quota del capitale iniziale che resta a fine stagione; nella tabella c'è la media geometrica sulle 19 stagioni vere, cioè il valore di una stagione tipica. Nell'ultima colonna c'è, per confronto, il valore sulle stagioni ricostruite: la mediana sulle 500 di ogni stagione, poi la media geometrica.

**Che cosa si vede:**
- **Confrontando con le 40 partite precedenti, lo schema interviene poco.** L'allarme scatta circa 1,6 volte per stagione, quanto ci si aspetta dai soli falsi allarmi. Ho verificato che non è un errore: se nei dati inserisco un peggioramento abbastanza forte, l'ANOVA lo trova; i cambiamenti da un periodo al successivo sono troppo piccoli per 40 partite contro 40. Lo schema fa meglio del lavoratore senza supervisore in 10 stagioni su 19 e peggio in 6; la versione che resta ferma fino a fine stagione fa meglio in 12 e peggio in 4.
- **Confrontando con la stagione di calibrazione, il segnale che lei si aspettava c'è.** Gli errori del modello rispetto al mercato peggiorano in media e soprattutto diventano più dispersi man mano che il modello invecchia: per il modello calibrato sul 2010-11 la dispersione passa da 0,136 a 0,19–0,20 nelle stagioni 2017-20, e nelle stagioni dal 2016-17 al 2019-20 l'allarme sulla dispersione è acceso in due giornate su tre o più. L'allarme scatta circa 5 volte per stagione e lo schema batte il lavoratore senza supervisore in 14 stagioni su 19 (peggio in 5). Sulle stagioni vere, però, il guadagno non si concentra in quelle in cui il modello è più vecchio: è distribuito fra stagioni con il modello giovane e con il modello vecchio. L'errore del modello da solo, senza il confronto con il mercato, non peggiora: è il mercato che migliora e lo lascia indietro, un cambiamento strutturale nel senso del suo schema.
- **Due cautele su questo risultato.** Ho scelto questo confronto dopo aver visto, sulle stagioni di valutazione, quanto spesso scattava l'allarme (non i guadagni). E con un vantaggio negativo puntare meno aiuta comunque: la versione ferma fino a fine stagione non punta nel 59% delle giornate.
- **Sui dati reali Oaxaca separa poco i due tipi di errore.** Sui dati simulati la decomposizione funziona. Nella sospensione per il Covid del 2019-20, dove mi aspettavo un errore strutturale, la parte strutturale è quasi nulla. Ho trovato due motivi. Il primo: le caratteristiche delle partite spiegano solo il 2,5% della variabilità dell'errore, che dipende quasi tutto da quale esito è uscito; quindi la parte «dati» resta piccola per forza. Il secondo: la posizione della partita nella stagione, fra due finestre consecutive, non si sovrappone mai, e rende le componenti molto rumorose. Togliendola le diagnosi diventano più stabili e meno spesso «strutturali» (dal 51% al 42% delle giornate con allarme), ma il risultato in capitale non migliora: lo schema la tiene, come era stata scelta prima di vedere i risultati. Un rimedio più efficace è scomporre l'errore «atteso» invece di quello realizzato, cioè la distanza fra modello e mercato prima della partita, che non dipende dall'esito: le caratteristiche delle partite ne spiegano il 41%. Così la diagnosi diventa coerente con il suo schema: fra due periodi vicini l'errore risulta quasi sempre «nei dati» (95% dei casi), mentre rispetto alla stagione di calibrazione è strutturale quasi una volta su due. Il capitale resta però più o meno lo stesso.
- **Più si riduce la puntata, meno si perde.** Con un vantaggio negativo, ogni riduzione della puntata riduce la perdita. Per questo le versioni che restano ferme fino a fine stagione sono le migliori: le altre, quando l'allarme si spegne, tornano al quarto di Kelly.

**Le tre regole di scelta dell'esito.** La tabella sopra usa la regola del valore atteso più alto. Qui la stessa prova con le tre regole (modello Elo, 19 stagioni vere, capitale rimasto in una stagione tipica; fra parentesi le stagioni in cui lo schema fa meglio / peggio del quarto di Kelly con la stessa regola):

| Regola di scelta dell'esito | Partite su cui si punta | Quarto di Kelly, senza supervisore | Schema, confronto con le 40 partite precedenti | Schema, confronto con la stagione di calibrazione, fermo fino a fine stagione |
| --------------------------- | ----------------------- | ---------------------------------- | ---------------------------------------------- | ----------------------------------------------------------------------------- |
| Valore atteso più alto      | 86%                     | 57%                                | 60% (10 / 6)                                   | 71% (14 / 5)                                                                  |
| Scarto maggiore dal mercato | 86%                     | 55%                                | 58% (10 / 6)                                   | non provato                                                                   |
| Esito più probabile         | 39%                     | 68%                                | 70% (11 / 5)                                   | 77% (13 / 6)                                                                  |

Che cosa si vede:
- **La regola conta più del supervisore.** Passando dal valore atteso più alto all'esito più probabile, il quarto di Kelly conserva il 68% del capitale invece del 57%. Il motivo principale è che si punta su meno partite, circa 4 su 10 invece di quasi 9 su 10: con un modello che in media perde contro il mercato, puntare meno vuol dire perdere meno.
- **Il supervisore aiuta allo stesso modo con tutte le regole.** Con il confronto con le 40 partite precedenti aggiunge 2–3 punti di capitale e fa meglio in 10–11 stagioni su 19 (peggio in 5–6). Con il confronto con la stagione di calibrazione e lo schema fermo fino a fine stagione aggiunge di più: 14 punti con il valore atteso più alto, 9 con l'esito più probabile.
- **La combinazione migliore** è l'esito più probabile insieme al confronto con la stagione di calibrazione: 77% del capitale. Anche questa combinazione l'ho scelta dopo aver visto i risultati.

**La stagione 2023-24, quella di KellyBench.** L'ho giocata come in KellyBench, partendo da £100 000. Avevo già usato questa stagione come test prima di costruire lo schema, quindi i risultati dello schema sono solo esplorativi e non ho cambiato nessun parametro. Il risultato è quello della stagione vera. Per vedere quanto conta la fortuna l'ho giocata anche su 500 stagioni ricostruite, ricampionando le giornate come per la valutazione (senza puntata minima, perché così il risultato in sterline non dipende dal capitale iniziale).

| Agente                                                                             | Stagione vera | Mediana delle 500 stagioni | 90% delle stagioni fra | Stagioni in cui fa meglio del quarto di Kelly |
| ---------------------------------------------------------------------------------- | ------------- | -------------------------- | ---------------------- | --------------------------------------------- |
| Lavoratore da solo, Kelly pieno                                                    | £14           | £16                        | £0 e £1 564            | 0%                                            |
| Lavoratore con il quarto di Kelly, senza supervisore                               | £24 358       | £24 564                    | £8 555 e £71 172       | –                                             |
| Schema, 40 partite precedenti, allarme se peggiora la media o cresce la varianza   | £24 424       | £25 750                    | £8 701 e £74 411       | 60%                                           |
| Come sopra, fermo fino a fine stagione                                             | £24 424       | £41 169                    | £11 991 e £106 895     | 73%                                           |
| Schema, 40 partite precedenti, allarme solo se peggiorano media e varianza insieme | £26 755       | £26 124                    | £8 907 e £72 300       | 69%                                           |
| Schema, confronto con la stagione di calibrazione                                  | £24 944       | £26 391                    | £9 158 e £71 336       | 59%                                           |
| Come sopra, fermo fino a fine stagione                                             | £24 944       | £51 185                    | £18 409 e £100 497     | 77%                                           |

Che cosa si vede:
- **Nella stagione vera lo schema cambia poco**, in tutte le versioni. Il modello usato nel 2023-24 è calibrato sul 2020-21, quindi è ancora «giovane»: la dispersione dei suoi errori è la stessa della stagione di calibrazione (0,181 contro 0,186) e l'allarme scatta solo nell'1% delle giornate.
- **Sulle stagioni ricostruite lo schema fa meglio del quarto di Kelly nel 59–77% dei casi**, e le versioni ferme fino a fine stagione conservano molto più capitale (mediana da £24 564 a £41 169 e £51 185). È però in buona parte un effetto del ricampionamento, come spiego nel punto seguente.
- **La differenza fra stagione vera e ricostruite** viene dal ricampionamento: una stagione ricostruita ripete alcune giornate e ne salta altre, e questo crea più spesso un periodo di errori anomali che fa scattare l'allarme (2–3 accensioni per stagione invece di quasi nessuna). La stagione vera è una sola fra quelle possibili, e lì l'allarme non è scattato.

## 6. Altre analisi di supporto

Ho fatto anche alcune analisi che lo schema non prevede, ma che aiutano a leggerne i risultati.

**Test di eteroschedasticità sui residui.** Per capire se il segnale che lo schema cerca esiste davvero, ho applicato ai residui del modello i test classici:
- Breusch-Pagan e White con le soglie nominali rigettano in tutte le 19 stagioni, ma solo perché la varianza dell'errore dipende per costruzione da quanto è incerta la previsione;
- con soglie calibrate col bootstrap i rigetti scendono a zero;
- i test sulla varianza che cresce nel corso della stagione (Breusch-Pagan sul tempo, Goldfeld-Quandt, ARCH) rigettano in 0–3 stagioni su 19.

Questo spiega perché l'allarme scatta di rado quando confronta due periodi vicini: dentro una stagione la varianza non cresce. Cresce invece fra una stagione e l'altra, ed è ciò che vede il confronto con la stagione di calibrazione.

**Z-test per giornata.** È un modo più semplice di dare l'allarme: confronta l'errore medio di ogni giornata con quello del training. Sulle 19 stagioni, con 1,9 falsi allarmi attesi per stagione (36 in tutto), la soglia nominale dà 53 allarmi e quella calibrata 43. Anche qui, quindi, gli allarmi sono di poco sopra quelli attesi per caso.

**Le squadre neopromosse.** Mi aspettavo che fossero il caso tipico di errore nei dati, perché il modello le conosce poco. Ho confrontato l'errore sulle loro partite a inizio stagione e nel resto della stagione, al netto delle altre squadre (differenza nelle differenze): −0,019, con intervallo al 95% da −0,040 a +0,003. La differenza non è significativa.

**Le stagioni di training e il Covid.** Le stagioni di training sono una ogni dieci anni, e per questa regola una di esse è il 2020-21, giocato quasi tutto a porte chiuse. Nel modello usato dal 2021-22 al 2023-24 pesa per un terzo e abbassa il vantaggio del campo stimato da circa 128 a 78 punti Elo. Ho fatto due verifiche, senza cambiare la separazione dei dati:
- **Senza il 2020-21 il modello va peggio.** Ho previsto il 2021-22 e il 2022-23 con il modello calibrato fino al 2010-11, che non contiene il Covid. Lo scarto dal mercato peggiora, da −0,032 a −0,040 per partita. Il vantaggio del campo si era già ridotto prima del Covid: quel modello prevede il 47,7% di vittorie in casa, contro il 45,7% reale. Il problema quindi non è il Covid, ma la distanza dall'ultima calibrazione.
- **Una calibrazione in più sul 2015-16 migliora le previsioni, non il capitale.** L'ho usata per le stagioni dal 2016-17 al 2019-20, al posto di quella del 2010-11. Il modello prevede meglio: lo scarto dal mercato passa da −0,031 a −0,025. Il capitale però non migliora: il quarto di Kelly scende dal 57% al 54%, lo schema fermo fino a fine stagione resta al 70% (71% prima). In quelle stagioni le squadre di casa vincevano più di quanto dicesse il mercato (46,9% contro 44,9%). Il modello vecchio dava loro più del mercato (47,7%) e su quelle puntate guadagnava; il nuovo è più vicino al mercato (45,4%) e perde quel vantaggio. Lo schema invece regge: con la nuova calibrazione batte il quarto di Kelly in 17 stagioni su 19.

Le conclusioni, quindi, non dipendono dalla scelta delle stagioni di training.

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
3. **La ri-parametrizzazione.** Lei aveva indicato il moltiplicatore come prima scelta, e la ri-parametrizzazione annuale che ho provato va peggio del modello calibrato una volta sola. Basta il moltiplicatore, o vuole che provi anche a ri-parametrizzare il modello subito dopo un errore strutturale?
4. **La versione principale.** Nella tesi presenterei come versione principale quella che confronta gli errori recenti con la stagione di calibrazione del modello, con allarme se peggiora la media o cresce la varianza, e le altre come varianti. Le sembra corretto?

Il codice e tutti i risultati sono riproducibili e a sua disposizione.
