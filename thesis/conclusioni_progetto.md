# Analisi del lavoro svolto: agente Structural-Hybrid Kelly

Questo documento riassume che cosa è stato implementato, con quali scelte e con quali risultati. Riguarda il sistema gerarchico proposto per KellyBench: un modello che prevede, un supervisore che riconosce il degrado e un ricalibratore che decide quanto puntare.

Formule, parametri e seed sono descritti per esteso in `thesis/metodi_implementati.md`. I numeri citati sono in `thesis/numeri.md`, ciascuno con il CSV e la riga da cui viene.

## 1. Obiettivo e impianto

La proposta di partenza è un agente gerarchico. Su di essa si costruisce il resto:
- **Modulo 1, il lavoratore**: prevede le probabilità 1X2 di ogni partita e propone la puntata.
- **Modulo 2, il supervisore**: osserva come cambia l'errore del Modulo 1 nel tempo e, con l'ANOVA sui residui, dà l'allarme.
- **Modulo 3, il ricalibratore**: con la decomposizione di Oaxaca-Blinder separa la parte del cambiamento dovuta a una diversa composizione delle partite (compositiva, errore nei dati) da quella dovuta a un cambiamento della relazione fra covariate ed errore (strutturale), e ne ricava la frazione di Kelly da puntare.

I nomi seguono lo schema del relatore. Nel codice, e nella sezione 3.4, «Modulo 2» indica la decomposizione di Oaxaca-Blinder. Lo schema completo è l'agente C3 (§3.5 e `thesis/agenti_e_architettura.md` §3.3). La sintesi per il relatore è in `thesis/schema_relatore.md`.

Lo schema è confrontato, sulle stesse partite e con le stesse quote, con lo stesso lavoratore senza supervisore: Kelly pieno (A) e quarto di Kelly (B_0.25), che è anche la puntata dello schema senza allarme. Così si misura che cosa aggiunge il supervisore. L'obiettivo misurato è il profilo di rischio e di crescita del bankroll, non soltanto il rendimento. Gli agenti di confronto nati dalle note di progetto (C0, C1, C2, D, E, B_0.10) sono sul branch `confronti-controllo`.

## 2. Dati e protocollo

- **Ambiente.** Replica locale, non l'endpoint OpenReward, per avere il controllo completo di seed, scenari e vincoli.
  - Dati: i CSV della Premier League di football-data.co.uk, stagioni dal 1993-94 al 2023-24.
  - Quote: la terna Bet365 pre-partita, l'unica completa in tutte le stagioni dal 2002-03.
  - Quote complete esistono dal 2000-01, quindi le stagioni precedenti servono solo come storia per i rating.
- **Split temporale congelato prima di guardare i risultati.**
  - Training: 2000-01, 2010-11, 2020-21. Validazione: le altre 19 stagioni dal 2002-03 al 2022-23. Test: 2023-24, la stagione di KellyBench.
  - Il test è rimasto bloccato nel codice finché i parametri non sono stati congelati.
- **Anti-leakage per costruzione.** Per prevedere una partita si usano solo le partite con data strettamente anteriore, e della partita solo identificativi e quote pre-partita. Un test automatico lo verifica, anche sul 2023-24 (0 violazioni su 380 partite).
- **Protocollo anti-overfitting.**
  - Tutti i parametri liberi si calibrano sulle sole tre stagioni di training.
  - Poi si congelano in un file (`config/frozen_params.toml`), che viene committato. Solo dopo si sblocca il test, con un commit successivo.
  - Il 2023-24 è stato eseguito una volta sola. Lo schema del relatore è stato costruito dopo: sul 2023-24 è eseguito una volta, come risultato esplorativo (§4.9).
  - Con il secondo Modulo 1 (Dixon-Coles) la procedura è identica, con un proprio file congelato (`config/frozen_params_dc.toml`).
  - La validazione serve a stimare le prestazioni, non a scegliere parametri.

## 3. Componenti e scelte di implementazione

### 3.1 Dalle quote alle probabilità di mercato
- **Metodo principale: Shin.** Il de-vigging toglie il margine del bookmaker dalle quote; si confrontano cinque metodi (proporzionale, additivo, power, Shin, odds ratio).
  - Shin modella il margine come difesa dal trading informato e, a differenza del proporzionale, tiene conto del favourite-longshot bias.
  - Il proporzionale è il controllo, e tutti e cinque i metodi entrano in un'analisi di sensibilità.
- **Divergenza fra metodi.** È dello stesso ordine di un edge plausibile: fino a 6.3 punti percentuali sul singolo esito, 3.5 al 99° percentile, contro un edge di riferimento di 2 punti. In punti è massima sui favoriti, in termini relativi sugli outsider. Per questo la scelta del metodo va giustificata e la sensibilità va riportata.

### 3.2 Modulo 1
- **Elo con il mapping di Davidson.** L'Elo dà un punteggio atteso, ma gli esiti sono tre; il pareggio si modella col parametro ν di Davidson, che rende il pareggio meno probabile quando lo squilibrio cresce.
  - K, vantaggio casalingo e ν sono calibrati sul solo training, in modo espansivo: ogni fit usa le stagioni di training fino alla sua.
  - Le neopromosse mai viste partono dalla media dei rating delle ultime tre retrocesse.
- **Usato raw, senza ricalibrazione.** In validazione le versioni ricalibrate (Platt, isotonica) avevano log-loss peggiore.
- **Dixon-Coles come secondo Modulo 1**, per verificare che le conclusioni non dipendano dal modello: Poisson con correzione τ dei punteggi bassi, pesatura temporale esponenziale, prior gaussiano sulle neopromosse.
  - La variante senza prior (σ = ∞) è esclusa: per una squadra senza storia che nelle prime partite non segna o non subisce gol, lo stimatore di massima verosimiglianza non esiste.

### 3.3 Il test decisivo: il modello batte il mercato?
- **Lo stimatore.** ĝ = media su tutte le partite di ln p̂(esito) − ln q(esito): positivo se il modello assegna all'esito realizzato più probabilità del mercato.
- **Lo stesso test con qualunque modello.** Se ĝ è negativo, nessuna regola di puntata può creare un edge: si può solo perdere meno.

### 3.4 Oaxaca-Blinder sui residui («Modulo 2» nel codice)
- **Variabile osservata.** δ = ln p̂(esito) − ln q(esito) per partita: la stessa quantità di ĝ, partita per partita.
- **Covariate**, tutte note prima della partita:
  - log-rapporto delle quote casa/trasferta;
  - entropia delle probabilità di mercato e di quelle del modello;
  - flag di squadra neopromossa;
  - posizione della partita nella stagione.
  - Il differenziale Elo è stato escluso da una regola sulla collinearità (VIF ≤ 5) fissata prima di guardare i dati.
- **I due gruppi, in un contesto sequenziale.** A ogni data di decisione si confrontano due finestre adiacenti di partite già giocate: le ultime W (gruppo recente) e le W precedenti (gruppo di riferimento).
  - Con meno di 2W partite disponibili il supervisore è inattivo.
  - La finestra dello schema è W = 40, congelata dalla calibrazione sul training; le analisi diagnostiche usano anche W = 80, 120 e 190.
- **Decomposizione.** Oaxaca-Blinder three-fold, implementata a mano con OLS via QR: differenza = compositiva + strutturale + interazione.
  - La quota strutturale π = |S| / (|C| + |S| + |I|) usa i valori assoluti, perché le componenti possono avere segni opposti.
  - Sono calcolate anche le two-fold con sei riferimenti, per misurare l'indeterminatezza della scelta del riferimento.
- **Validazione dell'implementazione.** Su dati sintetici con componenti note, la decomposizione le recupera; la somma delle componenti coincide con la differenza totale entro l'errore di macchina.
- **Errore strutturale.** Si diagnostica quando il degrado a composizione fissa, T = −S, supera una soglia calibrata col block bootstrap sotto l'ipotesi nulla.
- **Supporto comune.** Una partita è "fuori supporto" se nella finestra di riferimento ci sono meno di 5 partite con caratteristiche simili; è il caso tipico delle neopromosse (analisi diagnostica, §4.6).

### 3.5 Lo schema del relatore
- **Allarme (supervisore).** Fra le ultime 40 partite e le 40 precedenti: ANOVA a una via sulla media di δ (conta solo se peggiora) e test di Brown-Forsythe sulla dispersione (conta solo se cresce). C3 dà l'allarme se basta uno dei due, C3_and se servono entrambi. Soglie calibrate sul training col block bootstrap, al più il 5% di falsi allarmi.
- **Diagnosi (ricalibratore).** Con l'allarme, errore strutturale se T = −S supera la soglia, altrimenti errore di composizione.
- **Puntata.** λ = 0.25 senza allarme, 0.1875 con errore di composizione, 0 con errore strutturale: finché dura l'allarme (C3, C3_and) o fino a fine stagione (C3_stop). La puntata è λ volte il Kelly pieno sull'esito scelto.
- **Parametri.** W, κ e la soglia strutturale sono congelati; le sole quantità calibrate per lo schema sono le soglie dell'allarme.

### 3.6 Agenti confrontati

| Agente | Regola |
|---|---|
| A | Kelly pieno: il lavoratore da solo |
| B_0.25 | Quarto di Kelly: il lavoratore senza supervisore |
| C3, C3_stop, C3_and | Lo schema del relatore (§3.5) |

- **Selezione e ripiego.** Tutti gli agenti scelgono per ogni partita l'esito con EV stimato massimo e puntano solo se l'EV è positivo (le regole alternative del lavoratore sono in §4.7). Il supervisore cambia solo le frazioni, mai le previsioni né la scelta dell'esito: così il confronto isola la regola di puntata.

### 3.7 Ambiente di backtest
- **Esecuzione appaiata.** Gli agenti girano sulla stessa sequenza di date, con le stesse previsioni, quote ed esiti.
- **Bankroll e floor.** Il bankroll iniziale è £220. La puntata minima F vale £0.01 nella configurazione principale e £1 in quella alternativa, oltre al caso senza floor.
- **Vincoli di KellyBench.**
  - Almeno una puntata per data: se l'agente non punta, l'ambiente piazza una puntata minima sull'esito a EV stimato massimo.
  - Rovina assorbente se la ricchezza scende sotto il floor.
- **Più puntate nella stessa data.** Si piazzano in ordine di EV stimato finché la loro somma non supera la ricchezza.
  - È una semplificazione dichiarata: non è un'ottimizzazione congiunta del Kelly multi-esito.

### 3.8 Inferenza
- **Il problema n = 1.** Una stagione è una sola traiettoria, autocorrelata e dipendente dal percorso.
- **I seed.** Ogni seed è una stagione ricostruita per stationary bootstrap delle date: ogni data porta con sé tutte le sue partite.
  - La lunghezza media dei blocchi è scelta automaticamente con il metodo di Politis-White.
  - 500 seed per stagione, numero congelato da un'analisi di potenza sul training.
- **Intervalli.** Per ĝ, bootstrap a due livelli: stagioni come cluster indipendenti e serie ricampionata dentro la stagione; con soli 19 cluster si usa una correzione t per il numero di cluster.
- **Soglie calibrate dove i test nominali non valgono.** Per ANOVA, Z-test, Breusch-Pagan e soglia strutturale la soglia è calibrata col block bootstrap sotto l'ipotesi nulla. È lo stesso rimedio all'autocorrelazione applicato a tutti gli strumenti.

## 4. Risultati

### 4.1 Il modello non batte il mercato
- **Bet365.** ĝ = −0.0222, IC 95% [−0.0298, −0.0147].
- **Pinnacle chiusura.** ĝ = −0.0316, IC 95% [−0.0436, −0.0196].
- **2023-24.** ĝ = −0.0427 (Bet365).
- **Dixon-Coles.** Migliora la log-loss (0.9709 contro 0.9795), ma ĝ resta negativo (−0.0136).
- **Robustezza del segno.** È lo stesso con i cinque metodi di de-vigging, pooled e sul test.

Di conseguenza tutti gli agenti che puntano perdono in valore atteso, e il supervisore può solo ridurre la perdita.

### 4.2 Autocorrelazione: l'ANOVA nominale non è utilizzabile sulle serie di errori
- **F nominale.** Su serie AR(1) senza differenze fra i gruppi, rigetta falsamente il 3.7% a φ = 0 (atteso 5%), ma il 14.9%, 25.3% e 39.9% a φ = 0.3, 0.5, 0.7.
- **Soglia calibrata.** Col block bootstrap della serie centrata riporta il tasso entro l'intervallo Monte Carlo [3.2%, 6.8%] con blocchi di 7 e 20 (3.9% e 5.6%), non con blocchi di 40 (8.1%). È un limite da dichiarare.

### 4.3 Z-test per giornata
Sulle 19 stagioni di validazione sono attesi 1.9 allarmi falsi per stagione:

| Metodo | Allarmi |
|---|---|
| Z-test per matchday, soglia nominale | 53 |
| Z-test per matchday, soglia calibrata (blocchi di 20 o 40) | 43 |

### 4.4 Eteroschedasticità: il segnale atteso non c'è
- **Soglia nominale.** Breusch-Pagan e White rigettano in tutte le 19 stagioni, ma per costruzione: la varianza della log-loss dipende dall'incertezza della previsione.
- **Soglia calibrata.** I rigetti scendono a 0–1. I test sulla varianza nel corso della stagione (Breusch-Pagan sul tempo, Goldfeld-Quandt, ARCH, varianza mobile) danno 0–3 rigetti su 19.

Non c'è evidenza di una varianza che cresce durante la stagione oltre quella già presente nel training. È il segnale su cui si basa l'allarme dello schema del relatore, che quindi scatta poco: circa 1,6 volte per stagione (§4.7).

### 4.5 Il floor rende possibile la rovina
- **Senza floor.** La rovina è esattamente zero, sul calendario sintetico e su quello reale.
- **Con il floor**, sul calendario reale:

| Agente | Rovina con £0.01 | Rovina con £1 |
|---|---|---|
| Kelly pieno | 17.9% | 69.0% |
| Quarto di Kelly | — | 0.49% |

- **Soglia.** Sul calendario sintetico la rovina compare fra un rapporto bankroll/floor di 100 (3.3%) e di 31.6 (59.6%).
- **Accelerazione.** Il tempo medio di rovina è 13 volte più breve del limite teorico.

È una predizione falsificabile confermata: il floor rompe la struttura moltiplicativa di Kelly proprio quando il bankroll è basso.

### 4.6 La decomposizione distingue poco i due tipi di cambiamento sui dati reali
- **Sui dati sintetici** la decomposizione funziona.
- **Sospensione Covid del 2019-20**, il caso in cui ci si aspettava un cambiamento strutturale:
  - componente strutturale −0.0004, quota strutturale 0.014;
  - componente compositiva 0.0116, interazione −0.0163;
  - tutti gli intervalli comprendono lo zero.
- **Passaggio fra stagioni**, dove ci si aspettava un cambiamento compositivo: la quota compositiva non domina.
- **Neopromosse.** Il difference-in-differences del loro errore, fra inizio e resto della stagione, vale −0.0187, IC [−0.0397, 0.0025].

Sui dati reali le due componenti non si separano dove la teoria lo prevede: è il risultato da discutere.

### 4.7 Lo schema del relatore contro il lavoratore senza supervisore
Somma sulle 19 stagioni di validazione della mediana di ln W_T, configurazione £0.01, 500 seed appaiati (`results/us_c10_scheme_validation_summary.csv`):

| Agente | Somma delle mediane | Accensioni per stagione | Date con λ = 0 |
|---|---|---|---|
| A, Kelly pieno | −116.89 | – | – |
| B_0.25, quarto di Kelly | −10.87 | – | – |
| C3 | −10.62 | 1.6 | 1.5% |
| C3_stop | −7.51 | 1.6 | 26% |
| C3_and | −10.67 | 1.5 | 1.4% |

- **C3 contro B_0.25:** mai peggiore in mediana, migliore in 5 stagioni su 19.
- **C3_stop contro B_0.25:** mai peggiore, migliore in 9 stagioni su 19.
- **C3_and:** quasi come C3; migliore di B_0.25 in 8 stagioni su 19.
- **Lettura.** Lo schema funziona come descritto, ma interviene poco: il segnale che cerca è raro (§4.4), e dopo l'allarme torna al quarto di Kelly. Con un vantaggio negativo ogni riduzione della puntata riduce la perdita, per questo la versione che resta ferma fino a fine stagione è la migliore.

**Il lavoratore sceglie l'esito.** Come chiesto dal relatore, il lavoratore può anche scegliere l'esito con tre regole: EV massimo (R1, quella usata finora), maggior vantaggio sul mercato (R2), esito più probabile (R3). Ogni regola è provata da sola, con il freno fisso λ = 0,25 e con lo schema C3 (`thesis/agenti_e_architettura.md` §4, `results/us_c11_worker_rules_summary.csv`).
- R3 perde meno di R1 in 13 stagioni su 19, perché punta su circa metà delle partite; R2 è come R1, un po' peggio.
- Per ogni regola lo schema non è mai peggiore del freno fisso ed è migliore in 5–6 stagioni su 19.
- Nessuna regola dà un guadagno: la migliore combinazione, R3 con lo schema, ha una somma delle mediane di −7.60.

### 4.8 Robustezza
- **Modulo 1.** Con Dixon-Coles il modello migliora la log-loss ma ĝ resta negativo (§4.1); l'esecuzione congelata con Dixon-Coles è in `results/us_c8_3_validation_summary_dc.csv`.
- **De-vigging.** Il segno di ĝ è lo stesso con tutti e cinque i metodi, pooled e sul test.

### 4.9 La stagione 2023-24 come in KellyBench, partendo da £100 000
**L'esperimento.** Come in KellyBench, ogni agente vive la stagione 2023-24 data per data, partendo da £100 000: il bankroll iniziale a cui il paper riscala i risultati (Tabella 2).
- Gli esiti sono quelli veri, non stagioni ricostruite.
- Parametri congelati e Modulo 1 Elo sono quelli dell'esecuzione sul test; non si cambia nulla.
- Il floor di KellyBench non è certo, quindi la simulazione è ripetuta senza floor e con floor di £0.01 e £1.
- Con £100 000 il floor quasi non conta: il bankroll finale cambia al più di qualche decina di sterline.
- Verifica: senza floor la log-ricchezza di A e B_0.25 coincide esattamente con quella dell'esecuzione sul test.

**Bankroll finale**, floor £0.01 (`results/kellybench_2023_24.csv`, figura `thesis/figures/kellybench_2023_24.png`):

| Agente | Bankroll finale | Rendimento della stagione | Drawdown massimo | Rendimento per £ puntata |
|---|---|---|---|---|
| A, Kelly pieno | £14 | −99.99% | 99.99% | −34.0% |
| B_0.25, quarto di Kelly | £24 358 | −75.6% | 75.6% | −20.1% |
| C3, schema del relatore | £24 424 | −75.6% | 75.6% | −20.2% |
| C3_stop | £24 424 | −75.6% | 75.6% | −20.2% |
| C3_and | £26 755 | −73.2% | 73.2% | −20.0% |

Lo schema è stato costruito dopo l'esecuzione unica sul test, quindi le sue righe sono un'esecuzione esplorativa, fatta una sola volta con i parametri congelati.

**Lettura.**
- **Il quadro di KellyBench si riproduce.** Puntare con un modello che non batte il mercato fa perdere, e la perdita cresce con la frazione: Kelly pieno azzera quasi il bankroll, come i modelli che nel paper vanno in rovina. Con £100 000 nessun agente va in rovina in senso stretto.
- **Lo schema cambia poco il quarto di Kelly**, come in validazione: l'allarme è raro e nella stagione non separa C3 da C3_stop.

## 5. Lettura rispetto all'ipotesi iniziale

| Ipotesi | Esito |
|---|---|
| Un floor di puntata rende possibile la rovina di un agente Kelly | confermata |
| L'ANOVA e lo Z-test nominali sono inaffidabili su serie autocorrelate; la calibrazione col block bootstrap è il rimedio | confermata, con il limite dei blocchi lunghi |
| Il segno di ĝ non dipende dal modello previsivo né dal metodo di de-vigging | confermata |
| Il modello batte il mercato | non confermata: ĝ < 0 ovunque |
| L'eteroschedasticità crescente segnala il degrado | non confermata: con soglie corrette non si osserva |
| La decomposizione distingue in modo netto il cambiamento compositivo da quello strutturale sui dati reali | non confermata, anche se l'implementazione è corretta sui dati sintetici |
| Lo schema del relatore riduce le perdite rispetto al lavoratore senza supervisore | in parte: mai peggiore, ma il guadagno è piccolo, tranne con lo stop fino a fine stagione |
| L'agente batte il mercato | non confermata, anche nella stagione 2023-24 giocata come in KellyBench con £100 000 |

## 6. Limiti e parti non implementate

**Scelte semplificative**
- Una sola puntata per partita, sull'esito a EV massimo (le regole alternative R2 e R3 sono in §4.7); nessun Kelly multi-esito né ottimizzazione congiunta delle puntate della stessa data.
- Dopo un errore strutturale lo schema azzera la puntata, ma non ri-parametrizza né cambia il modello: il relatore ha indicato il moltiplicatore sulla puntata come prima scelta.
- Scenari: al posto dei cinque di KellyBench, tre stagioni di training, 19 di validazione e il 2023-24. La variante "literature" del 2023-24 non è ricostruibile dai dati pubblici.
- Il valore del floor (£0.01 o £1) non è verificato sul codice di KellyBench: per questo i risultati sono riportati con entrambi.

**Parti non implementate**
- Modelli previsivi: solo Elo e Dixon-Coles. Il lavoratore LLM è predisposto ma non ancora eseguito.
- L'agente autonomo come quello di KellyBench (opzione B del relatore) è fuori dalla tesi.
- Non implementati: la regressione RIF, una baseline con Kelly bayesiano e la valutazione dell'agente sulla rubrica a 44 punti di KellyBench.

## 7. Riproducibilità e materiale disponibile

**Esecuzione**
- Tutti i risultati si rigenerano da zero con `scripts/reproduce_all.py`, partendo dai CSV di football-data.co.uk. I CSV grezzi sono verificati con un manifesto SHA256.
- Un secondo manifesto confronta ogni risultato con la versione salvata.
- I file congelati in `config/` sono dati d'ingresso: la calibrazione che li ha scritti è sul branch `confronti-controllo`.
- Le versioni dei pacchetti sono registrate in `results/environment.txt`.
- La procedura è descritta nel `README.md`.

**Materiale per la tesi**

| Cosa | Dove |
|---|---|
| Descrizione tecnica dei metodi, con i riferimenti al codice | `thesis/metodi_implementati.md` |
| Numeri citabili, ciascuno con CSV e riga di provenienza | `thesis/numeri.md` |
| Tabelle in LaTeX (booktabs) e CSV | `thesis/tables/` |
| Figure vettoriali | `thesis/figures/tesi_*.pdf` |
| Risultati completi | `results/` |
