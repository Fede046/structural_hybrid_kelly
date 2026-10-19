# Analisi del lavoro svolto: agente Structural-Hybrid Kelly

Questo documento riassume che cosa è stato implementato, con quali scelte e con quali risultati. Riguarda il sistema gerarchico proposto per KellyBench: un modello che prevede, un supervisore che riconosce il degrado e un ricalibratore che decide quanto puntare.

Formule, parametri e seed sono descritti per esteso in `thesis/metodi_implementati.md`. I numeri citati sono in `thesis/numeri.md`, ciascuno con il CSV e la riga da cui viene.

## 1. Obiettivo e impianto

La proposta di partenza è un agente gerarchico. Su di essa si costruisce il resto:
- **Modulo 1, il lavoratore**: prevede le probabilità 1X2 di ogni partita.
- **Modulo 2, il supervisore**: osserva come cambia l'errore del Modulo 1 nel tempo. Con la decomposizione di Oaxaca-Blinder separa la parte del cambiamento dovuta a una diversa composizione delle partite (compositiva) da quella dovuta a un cambiamento della relazione fra covariate ed errore (strutturale).
- **Modulo 3, il ricalibratore**: traduce la diagnosi del supervisore nella frazione di Kelly da puntare.

L'agente è confrontato, sulle stesse partite e con le stesse quote, con le regole di puntata classiche e con un supervisore basato su drift detector standard. Così si misura che cosa aggiunge ciascun pezzo: è un'ablazione dell'architettura a più componenti. L'obiettivo misurato è il profilo di rischio e di crescita del bankroll, non soltanto il rendimento.

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
  - Tutti i parametri liberi degli agenti si calibrano sulle sole tre stagioni di training, con un unico obiettivo fissato prima: la log-ricchezza finale media nella configurazione principale.
  - Poi si congelano in un file (`config/frozen_params.toml`), che viene committato. Solo dopo si sblocca il test, con un commit successivo.
  - Il 2023-24 è stato eseguito una volta sola.
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

### 3.4 Modulo 2: il supervisore
- **Variabile osservata.** δ = ln p̂(esito) − ln q(esito) per partita: la stessa quantità di ĝ, partita per partita.
- **Covariate**, tutte note prima della partita:
  - log-rapporto delle quote casa/trasferta;
  - entropia delle probabilità di mercato e di quelle del modello;
  - flag di squadra neopromossa;
  - posizione della partita nella stagione.
  - Il differenziale Elo è stato escluso da una regola sulla collinearità (VIF ≤ 5) fissata prima di guardare i dati.
- **I due gruppi, in un contesto sequenziale.** A ogni data di decisione si confrontano due finestre adiacenti di partite già giocate: le ultime W (gruppo recente) e le W precedenti (gruppo di riferimento).
  - Con meno di 2W partite disponibili il supervisore è inattivo.
  - La finestra W ∈ {40, 80, 120, 190} è calibrata sul training.
- **Decomposizione.** Oaxaca-Blinder three-fold, implementata a mano con OLS via QR: differenza = compositiva + strutturale + interazione.
  - La quota strutturale π = |S| / (|C| + |S| + |I|) usa i valori assoluti, perché le componenti possono avere segni opposti.
  - Sono calcolate anche le two-fold con sei riferimenti, per misurare l'indeterminatezza della scelta del riferimento.
- **Validazione dell'implementazione.** Su dati sintetici con componenti note, la decomposizione le recupera; la somma delle componenti coincide con la differenza totale entro l'errore di macchina.
- **Allarme strutturale.** Scatta quando il degrado a composizione fissa, T = −S, supera una soglia calibrata col block bootstrap sotto l'ipotesi nulla.
- **Supporto comune.** Una partita è "fuori supporto" se nella finestra di riferimento ci sono meno di 5 partite con caratteristiche simili; è il caso tipico delle neopromosse.

### 3.5 Modulo 3: dal supervisore alla frazione
- **Formula.** La frazione ottima con stima rumorosa è λ* = E[c]/E[c²], con c = f̂/f* il rapporto fra frazione stimata e frazione vera.
  - Rispetto alla forma 1/(1 + Var(c)), questa tiene conto che la frazione stimata è troncata a zero: non si punta quando l'EV stimato è negativo.
- **La componente strutturale aumenta la varianza.** La varianza dell'errore di stima si ricava dalla dispersione di δ; una componente strutturale negativa la aumenta, e λ* si riduce.
- **Regole comuni.**
  - Se nella finestra recente il modello perde contro il mercato (media di δ ≤ 0), λ = 0.
  - Se il supervisore è inattivo, λ = 0.25 (quarto di Kelly).
- **Scelta della variante.** Fra tre varianti, quella usata è stata scelta su una verità sintetica, con λ* noto, prima di guardare i dati reali.

### 3.6 Agenti confrontati

| Agente | Regola |
|---|---|
| A | Kelly pieno |
| B_0.25, B_0.10 | Kelly frazionario fisso (quarto e decimo) |
| C0 | quarto di Kelly: è l'agente C con il supervisore spento |
| C1 | allarme binario: a ogni nuova accensione dell'allarme strutturale λ si moltiplica per κ |
| C2_global | λ graduata dal Modulo 3 |
| C2 | come C2_global, più l'astensione sulle partite fuori supporto |
| D_ADWIN, D_PH | quarto di Kelly ridotto di κ a ogni allarme di un drift detector standard (ADWIN, Page-Hinkley) |
| E | puntata minima permanente: punta solo quando l'ambiente lo obbliga |

- **Selezione e ripiego.** Tutti gli agenti scelgono per ogni partita l'esito con EV stimato massimo e puntano solo se l'EV è positivo. Il supervisore cambia solo le frazioni, mai le previsioni né la scelta dell'esito: così il confronto isola la regola di puntata.
- **I detector sono parte della baseline D.** ADWIN e Page-Hinkley vengono dalla libreria river, non sono reimplementati, e i loro parametri sono calibrati come quelli dell'agente C.
- **Ablazione.** C0 → C1 misura il valore del "rilevare"; C1 → C2 quello del "graduare"; C2 contro D misura il valore della decomposizione rispetto a un detector standard; C2 contro E dice se il framework serve.

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
  - 500 seed per stagione, da un'analisi di potenza sul training.
- **Intervalli.** Bootstrap a due livelli: stagioni come cluster indipendenti e seed dentro la stagione.
  - Con soli 19 cluster il percentile sottocopre; si usa quindi una correzione t per il numero di cluster, verificata con una simulazione di copertura.
  - Sul 2023-24, una stagione sola, l'intervallo viene dai soli seed.
- **Soglie calibrate dove i test nominali non valgono.** Per ANOVA, Z-test, Breusch-Pagan e allarme strutturale la soglia è calibrata col block bootstrap sotto l'ipotesi nulla. È lo stesso rimedio all'autocorrelazione applicato a tutti gli strumenti.

## 4. Risultati

### 4.1 Il modello non batte il mercato
- **Bet365.** ĝ = −0.0222, IC 95% [−0.0298, −0.0147].
- **Pinnacle chiusura.** ĝ = −0.0316, IC 95% [−0.0436, −0.0196].
- **2023-24.** ĝ = −0.0427 (Bet365).
- **Dixon-Coles.** Migliora la log-loss (0.9709 contro 0.9795), ma ĝ resta negativo (−0.0136).
- **Robustezza del segno.** È lo stesso con i cinque metodi di de-vigging, pooled e sul test.

Di conseguenza tutti gli agenti che puntano perdono in valore atteso, e la domanda corretta diventa quale regola limita meglio le perdite e il rischio.

### 4.2 Autocorrelazione: l'ANOVA nominale non è utilizzabile sulle serie di errori
- **F nominale.** Su serie AR(1) senza differenze fra i gruppi, rigetta falsamente il 3.7% a φ = 0 (atteso 5%), ma il 14.9%, 25.3% e 39.9% a φ = 0.3, 0.5, 0.7.
- **Soglia calibrata.** Col block bootstrap della serie centrata riporta il tasso entro l'intervallo Monte Carlo [3.2%, 6.8%] con blocchi di 7 e 20 (3.9% e 5.6%), non con blocchi di 40 (8.1%). È un limite da dichiarare.

### 4.3 Drift detector standard e Z-test
Sulle 19 stagioni di validazione sono attesi 1.9 allarmi falsi per stagione:

| Metodo | Allarmi |
|---|---|
| ADWIN, tarato sul training | 0 |
| Page-Hinkley | 20 |
| Z-test per matchday, soglia nominale | 53 |
| Z-test per matchday, soglia calibrata (blocchi di 20 o 40) | 43 |

I detector dicono quando qualcosa cambia, non quanto né di che tipo.

### 4.4 Eteroschedasticità: il segnale atteso non c'è
- **Soglia nominale.** Breusch-Pagan e White rigettano in tutte le 19 stagioni, ma per costruzione: la varianza della log-loss dipende dall'incertezza della previsione.
- **Soglia calibrata.** I rigetti scendono a 0–1. I test sulla varianza nel corso della stagione (Breusch-Pagan sul tempo, Goldfeld-Quandt, ARCH, varianza mobile) danno 0–3 rigetti su 19.

Non c'è evidenza di una varianza che cresce durante la stagione oltre quella già presente nel training. Per questo l'allarme dell'agente si basa sulla componente strutturale di Oaxaca-Blinder e non su un test di eteroschedasticità.

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

### 4.7 Confronti fra agenti
Differenze di log-ricchezza finale, configurazione £0.01:

| Confronto | Validazione, 19 stagioni: stima [IC 95%] | Test 2023-24 |
|---|---|---|
| C2 − D_ADWIN | +0.321 [0.187; 0.455] | +0.789 |
| C2 − D_PH | **−0.070** [−0.094; −0.045] | −0.163 |
| C2 − E | **−0.243** [−0.342; −0.144] | −0.596 |
| C1 − C0 (rilevare) | +0.298 [0.189; 0.407] | +0.669 |
| C2 − C1 (graduare) | +0.023 [−0.005; 0.051] | +0.120 |

- **Rispetto al Kelly frazionario fisso:** l'agente riduce molto le perdite (C1 − C0).
- **Rilevare e graduare:** quasi tutto il beneficio viene dal rilevare il degrado; il graduare aggiunge poco. A £0.01 è significativo solo sul test; in validazione lo è con il floor da £1 (+0.105, IC [0.043; 0.168]).
- **Contro la baseline con ADWIN:** C2 vince, ma ADWIN non dà allarmi e quella baseline coincide col quarto di Kelly.
- **Contro Page-Hinkley e la puntata minima:** C2 perde sia contro la baseline con Page-Hinkley sia contro E. Con un edge negativo, la politica migliore è puntare il meno possibile.

### 4.8 Robustezza
- **Modulo 1.** Il ranking degli agenti è stabile fra Elo e Dixon-Coles: τ di Kendall 0.857 in validazione e 0.762 sul test. I confronti danno la stessa conclusione in 138 casi su 160 in validazione e 140 su 160 sul test.
- **De-vigging.** Le conclusioni dei confronti hanno lo stesso segno con tutti e cinque i metodi in 260 casi su 262.

### 4.9 La stagione 2023-24 come in KellyBench, partendo da £100 000
**L'esperimento.** Come in KellyBench, ogni agente vive la stagione 2023-24 data per data, partendo da £100 000: il bankroll iniziale a cui il paper riscala i risultati (Tabella 2).
- Gli esiti sono quelli veri, non stagioni ricostruite.
- Agenti, parametri congelati e Modulo 1 Elo sono quelli dell'esecuzione sul test; non si cambia nulla.
- Il floor di KellyBench non è certo, quindi la simulazione è ripetuta senza floor e con floor di £0.01 e £1.
- Con £100 000 il floor quasi non conta: il bankroll finale cambia al più di qualche decina di sterline.
- Verifica: senza floor la log-ricchezza di ogni agente coincide esattamente con quella dell'esecuzione sul test.

**Bankroll finale**, floor £0.01 (`results/kellybench_2023_24.csv`, figura `thesis/figures/kellybench_2023_24.png`):

| Agente | Bankroll finale | Rendimento della stagione | Drawdown massimo | Rendimento per £ puntata |
|---|---|---|---|---|
| A, Kelly pieno | £14 | −99.99% | 99.99% | −34.0% |
| B_0.25 = C0 = D_ADWIN = C2_global | £24 358 | −75.6% | 75.6% | −20.1% |
| C1, allarme binario | £46 645 | −53.4% | 53.4% | −23.2% |
| C2, λ graduata con astensione | £57 315 | −42.7% | 56.9% | −22.4% |
| B_0.10, decimo di Kelly | £59 969 | −40.0% | 40.0% | −18.8% |
| D_PH, detector Page-Hinkley | £65 053 | −34.9% | 40.4% | −21.3% |
| E, puntata minima | £99 999.64 | −0.0004% | 0.0004% | −30.1% |

**Perché quattro agenti coincidono.** Sul 2023-24 C0, D_ADWIN e C2_global hanno la stessa traiettoria di B_0.25:
- ADWIN non dà allarmi;
- il Modulo 2 con la finestra di C2_global (190 partite) non si attiva mai nella stagione, perché la catena è tagliata alla stagione.

**Lettura.**
- **Il quadro di KellyBench si riproduce.** Puntare con un modello che non batte il mercato fa perdere, e la perdita cresce con la frazione: Kelly pieno azzera quasi il bankroll, come i modelli che nel paper vanno in rovina. Con £100 000 nessun agente va in rovina in senso stretto.
- **Rispetto alle regole fisse il supervisore riduce la perdita:** C2 perde il 42.7% contro il 75.6% del quarto di Kelly, ma resta dietro a D_PH, al decimo di Kelly e soprattutto alla puntata minima.
- **La puntata minima conserva il capitale**, come il seed di KellyBench passato alle puntate minime (−4.1% nel paper). È la conseguenza diretta di ĝ < 0.

## 5. Lettura rispetto all'ipotesi iniziale

| Ipotesi | Esito |
|---|---|
| Un floor di puntata rende possibile la rovina di un agente Kelly | confermata |
| Rilevare il degrado del modello riduce le perdite rispetto al Kelly frazionario fisso | confermata |
| L'ANOVA e lo Z-test nominali sono inaffidabili su serie autocorrelate; la calibrazione col block bootstrap è il rimedio | confermata, con il limite dei blocchi lunghi |
| Le conclusioni non dipendono dal modello previsivo né dal metodo di de-vigging | confermata |
| Il modello batte il mercato | non confermata: ĝ < 0 ovunque |
| L'eteroschedasticità crescente segnala il degrado | non confermata: con soglie corrette non si osserva |
| La decomposizione distingue in modo netto il cambiamento compositivo da quello strutturale sui dati reali | non confermata, anche se l'implementazione è corretta sui dati sintetici |
| Graduare la puntata con la decomposizione è meglio di un allarme binario | effetto piccolo: significativo sul test e, in validazione, solo con il floor da £1 |
| L'agente batte un detector standard (Page-Hinkley) | non confermata |
| L'agente batte la puntata minima | non confermata, anche nella stagione 2023-24 giocata come in KellyBench con £100 000 |

## 6. Limiti e parti non implementate

**Scelte semplificative**
- Una sola puntata per partita, sull'esito a EV massimo; nessun Kelly multi-esito né ottimizzazione congiunta delle puntate della stessa data.
- Scenari: al posto dei cinque di KellyBench, tre stagioni di training, 19 di validazione e il 2023-24. La variante "literature" del 2023-24 non è ricostruibile dai dati pubblici.
- Il valore del floor (£0.01 o £1) non è verificato sul codice di KellyBench: per questo i risultati sono riportati con entrambi.

**Parti non implementate**
- Modelli previsivi: solo Elo e Dixon-Coles. Bradley-Terry, i modelli score-driven e un Modulo 1 basato su LLM (per il costo) non ci sono.
- Detector: solo ADWIN e Page-Hinkley; DDM e CUSUM no.
- Non implementati: la regressione RIF, una baseline con Kelly bayesiano e la valutazione dell'agente sulla rubrica a 44 punti di KellyBench.

## 7. Riproducibilità e materiale disponibile

**Esecuzione**
- Tutti i risultati si rigenerano da zero con `scripts/reproduce_all.py`, partendo dai CSV di football-data.co.uk. I CSV grezzi sono verificati con un manifesto SHA256.
- Un secondo manifesto confronta ogni risultato con la versione salvata.
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
