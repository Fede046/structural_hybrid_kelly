# Gli agenti, l'architettura e le differenze con KellyBench

Questo documento spiega, in italiano e senza dare nulla per scontato, come funziona ogni agente del progetto, come è fatta l'architettura e che cosa cambia rispetto a KellyBench e rispetto all'esecuzione con DeepSeek Flash come Modulo 1. I parametri citati sono quelli di `config/frozen_params.toml` (Modulo 1 Elo); i dettagli di formule e file sono in `thesis/metodi_implementati.md`.

Il progetto contiene solo ciò che il relatore ha chiesto: il suo schema (lavoratore, supervisore, ricalibratore) e i due riferimenti che servono a misurarlo, cioè lo stesso lavoratore senza supervisore. Gli agenti di confronto nati dalle note di progetto (C0, C1, C2, D con ADWIN e Page-Hinkley, la puntata minima E, B_0.10) sono sul branch `confronti-controllo`. La sintesi per il relatore è in `thesis/schema_relatore.md`.

## 1. Il quadro in una pagina

```mermaid
flowchart LR
    D[Dati e quote Bet365\nsolo date anteriori] --> M1[Modulo 1, lavoratore\nprevede p̂ 1X2 e propone la puntata]
    Q[Quote lorde] --> M1
    M1 --> M2[Modulo 2, supervisore\nANOVA sui residui δ: allarme]
    M2 --> M3[Modulo 3, ricalibratore\nOaxaca-Blinder: errore nei dati o strutturale]
    M3 --> P[Puntata\nf = λ · f_w]
    P --> E[Ambiente\nbankroll, floor, rovina]
    E -->|esiti veri, dopo il regolamento| M2
```

- **Modulo 1, il lavoratore.** Prevede le probabilità p̂ = (casa, pareggio, trasferta) e propone una puntata f_w, il Kelly pieno sull'esito scelto. Nel progetto è un Elo con il mapping di Davidson; Dixon-Coles è il secondo modello.
- **Modulo 2, il supervisore.** Guarda come cambia nel tempo l'errore δ = ln p̂(esito) − ln q(esito), dove q è la probabilità del mercato senza margine (de-vigging di Shin). Con l'ANOVA sulla media e sulla dispersione di δ decide se dare l'allarme.
- **Modulo 3, il ricalibratore.** Con la decomposizione di Oaxaca-Blinder separa un cambiamento di composizione delle partite (errore nei dati) da un cambiamento strutturale, e ne ricava la frazione λ: la puntata è f = λ · f_w.

**I nomi nel codice.** Per ragioni storiche `src/shk/model/module2.py` contiene la decomposizione di Oaxaca-Blinder, che nello schema sta nel Modulo 3. L'ANOVA dell'allarme e la risposta sono in `src/shk/model/agent_c.py` (`scheme_statistics`, `SchemeAgent`).

## 2. Cosa fanno tutti gli agenti

Per ogni data della stagione l'ambiente chiede a ogni agente le frazioni da puntare. Le regole comuni sono queste:

1. **Che cosa si punta.** Per ogni partita il lavoratore sceglie un esito: per default quello con il valore atteso stimato più alto, EV = p̂·quota − 1, calcolato sulle quote lorde Bet365 (le altre regole sono in §4). Si punta solo se EV > 0 e al più una volta per partita.
2. **Quanto.** La frazione è f = λ · max(0, (b·p̂ − (1 − p̂)) / b), con b = quota − 1. λ = 1 è il Kelly pieno, λ = 0,25 il quarto di Kelly. Gli agenti differiscono per come scelgono λ.
3. **Più partite nella stessa data.** Le puntate si piazzano in ordine di EV decrescente finché la somma non supera il bankroll; le altre si scartano.
4. **Floor e puntata obbligatoria.** Con un floor F > 0 ogni puntata vale almeno F. KellyBench obbliga a puntare almeno una volta per data: se un agente non punta, l'ambiente piazza F sull'esito a EV stimato massimo.
5. **Rovina.** Se il bankroll scende sotto F l'agente non può più puntare e il gioco finisce per lui.
6. **Niente informazione dal futuro.** Gli esiti di una data arrivano agli agenti solo dopo il regolamento di tutti.

## 3. Gli agenti

| Agente | Regola di λ | Cosa rappresenta |
|---|---|---|
| **A** | λ = 1 sempre | Il lavoratore da solo, Kelly pieno |
| **B_0.25** | λ = 0,25 sempre | Il lavoratore con il quarto di Kelly, senza supervisore: è anche la puntata dello schema quando non c'è allarme |
| **C3** | Allarme ANOVA, poi Oaxaca: 0,25, 0,1875 oppure 0 | Lo schema del relatore |
| **C3_stop** | Come C3, ma dopo un errore strutturale 0 fino a fine stagione | Lettura alla lettera di «finché il modello non viene ri-parametrizzato» |
| **C3_and** | Come C3, con l'allarme solo se peggiorano media e varianza insieme | Lettura alla lettera di «la media degli errori cresce e la varianza esplode» |
| **C3_ref**, **C3_ref_stop** | Come C3 e C3_stop, ma confrontando le ultime 40 partite con la stagione di calibrazione del modello | Il confronto con il momento in cui il modello «era a posto» (§3.4) |

**Stagioni vere e stagioni ricostruite** (decisione del 2026-11-05; `scripts/us_c19_real_seasons.py`, `results/us_c19_real_seasons.csv`, modulo `shk.model.real_seasons`). Il risultato principale è la stagione vera, giocata una volta come in KellyBench: la realizzazione osservata, già presente in ogni sintesi. Le 500 stagioni ricostruite per stationary bootstrap delle date usano partite, quote e risultati veri, ma ripetono alcune giornate e ne saltano altre: alterano proprio la sequenza nel tempo che il supervisore osserva, e restano solo come misura dell'incertezza (quantili, rovina). us_c19 non esegue nulla di nuovo: legge le sintesi versionate. Capitale tipico = exp(media sulle 19 stagioni di ln W_T), configurazione £0,01; «meglio / peggio» rispetto al riferimento appaiato, stagione per stagione.

| Agente | Riferimento | Stagioni vere | Meglio / peggio | Ricostruite (mediana) |
|---|---|---|---|---|
| A | B_0.25 | 0,2% | 0 / 19 | 0,2% |
| B_0.25 | – | 57,3% | – | 56,4% |
| C3 | B_0.25 | 59,7% | 10 / 6 | 57,2% |
| C3_stop | B_0.25 | 71,0% | 12 / 4 | 67,3% |
| C3_and | B_0.25 | 56,4% | 6 / 7 | 57,0% |
| C3_ref | B_0.25 | 61,8% | 14 / 5 | 61,7% |
| C3_ref_stop | B_0.25 | 70,8% | 14 / 5 | 78,9% |
| R3_brake | – | 67,5% | – | 66,2% |
| R3_C3_ref | R3_brake | 69,0% | 13 / 6 | 71,0% |
| R3_C3_ref_stop | R3_brake | 76,7% | 13 / 6 | 86,7% |

Le conclusioni sono le stesse, ma più deboli. Sulle ricostruite (mediana delle differenze appaiate per seed, §3.3) lo schema con finestre adiacenti non era mai peggiore di B_0.25; sulle stagioni vere lo è in 4–7 stagioni. Le versioni ferme fino a fine stagione guadagnano meno sulle stagioni vere che sulle ricostruite (C3_ref_stop 71% contro 79%): il ricampionamento crea più spesso periodi di errori anomali che accendono l'allarme (§3.3). Le sezioni seguenti riportano i risultati delle ricostruite come erano; la tabella qui sopra è il riferimento.

### 3.1 Un esempio concreto

Tutti gli agenti ricevono la stessa p̂ e le stesse quote e usano la stessa formula di puntata. Cambia solo λ.

- Una partita ha quota 2,50 sull'esito che il modello preferisce, e il modello gli dà probabilità p̂ = 0,45.
- Valore atteso stimato: EV = 0,45 × 2,50 − 1 = **+0,125**. È positivo, quindi si può puntare.
- Con b = quota − 1 = 1,5, il Kelly pieno è f* = (b·p̂ − (1 − p̂)) / b = (0,675 − 0,55) / 1,5 = **0,0833**, cioè l'8,33% del bankroll.
- Ogni agente moltiplica f* per il proprio λ. Con un bankroll di £100 000:

| λ | Puntata | Agente |
|---|---|---|
| 1 | £8 333 | A |
| 0,25 | £2 083 | B_0.25, e lo schema senza allarme |
| 0,1875 | £1 563 | Lo schema con un errore nei dati |
| 0 | £0 | Lo schema con un errore strutturale (resta solo la puntata obbligatoria) |

### 3.2 A e B_0.25: il lavoratore senza supervisore

- **A** è il caso limite. Se il modello avesse ragione, il Kelly pieno farebbe crescere il capitale più in fretta. Ma il modello sbaglia, e il Kelly pieno amplifica ogni errore: nel 2023-24 chiude a £14.
- **B_0.25** è il Kelly prudente: riduce la puntata perché p̂ è solo una stima. È il riferimento dello schema, perché lo schema senza allarme punta esattamente come lui. La differenza fra lo schema e B_0.25 misura quindi quello che aggiunge il supervisore.

### 3.3 C3, C3_stop e C3_and: lo schema del relatore

Il prof. Roccetti ha descritto questo schema:
- il supervisore controlla i residui con l'ANOVA e dà l'allarme quando cresce l'eteroschedasticità;
- il ricalibratore usa Oaxaca-Blinder per capire che tipo di errore è;
- con un errore nei dati (di composizione) si riduce un po' la puntata;
- con un errore strutturale il rischio va quasi a zero finché il modello non viene ri-parametrizzato, o si cambia modello.

C3 implementa esattamente questo ordine.

**Come funziona, a ogni data.** Si prendono le ultime 40 partite già giocate (B, recenti) e le 40 precedenti (A, riferimento). I residui sono δ = ln p̂(esito) − ln q(esito).

1. **Allarme (Modulo 2, ANOVA).** Due test fra A e B:
   - l'ANOVA a una via sulla media di δ. Conta solo se B è peggiore di A;
   - il test di Brown-Forsythe, cioè l'ANOVA sulle distanze dalla mediana. È il test di eteroschedasticità. Conta solo se B è più dispersa di A.

   In C3 e C3_stop l'allarme è acceso se uno dei due supera la sua soglia. Le soglie sono calibrate sul training con un block bootstrap della serie di δ, a livello 2,5% ciascuna, quindi al più il 5% di falsi allarmi in tutto. Le soglie nominali dell'ANOVA non vanno bene: con serie autocorrelate darebbero molti più falsi allarmi (`conclusioni_progetto.md` §4.2).

   **C3_and** prende alla lettera la mail («la media degli errori cresce e la varianza esplode»): l'allarme è acceso solo se li superano tutti e due. Le sue soglie sono calibrate insieme, sugli stessi ricampionamenti: sono i quantili allo stesso livello per le due F, il più basso con cui la quota di ricampionamenti in cui entrambe superano la soglia resta al 5%. Sono quindi più basse di quelle di C3, e i falsi allarmi restano al 5%.
2. **Diagnosi (Modulo 3, Oaxaca).** Solo con l'allarme acceso si guarda la componente strutturale S della scomposizione three-fold:
   - **errore strutturale** se −S supera una soglia calibrata sul training, cioè se la relazione fra covariate ed errore è peggiorata in modo significativo;
   - altrimenti **errore di composizione**, cioè nei dati.
3. **Puntata (Kelly).**

| Diagnosi | λ |
|---|---|
| Nessun allarme | 0,25 |
| Errore di composizione | 0,25 · κ = 0,1875, finché dura l'allarme |
| Errore strutturale, **C3** e **C3_and** | 0 finché dura l'allarme, poi di nuovo 0,25 |
| Errore strutturale, **C3_stop** | 0 fino a fine stagione |

**Perché C3_stop.** Nel progetto il Modulo 1 si ri-parametrizza solo ai fit (2000-01, 2010-11, 2020-21), mai durante una stagione. Quindi «finché il modello non viene ri-parametrizzato», preso alla lettera, vuol dire fino a fine stagione: è C3_stop. C3 è la lettura più morbida, in cui si ricomincia appena l'allarme si spegne.

**Parametri.** W = 40, κ = 0,75 e la soglia strutturale per fit sono valori congelati in `config/frozen_params.toml` (chiavi storiche `c1_window`, `c1_kappa`, `c1_thresholds`). Vengono dalla calibrazione sul training del 2026-10, che allora sceglieva i parametri di un agente di confronto (C1) con la stessa finestra e la stessa soglia; quella calibrazione è sul branch `confronti-controllo`. Le sole quantità calibrate per lo schema sono le soglie dell'allarme (due per C3, due per C3_and), in `results/us_c10_scheme_thresholds.csv`.

**Risultati sulla validazione.** 19 stagioni × 500 seed, gli stessi dell'esecuzione congelata, configurazione £0,01; script `scripts/us_c10_scheme_validation.py`. B_0.25, rieseguito come riferimento, coincide bit per bit con l'esecuzione congelata, quindi i confronti sono appaiati.

| Agente | Somma sulle stagioni della mediana di ln W_T | Accensioni medie per stagione | Date con λ = 0 |
|---|---|---|---|
| B_0.25 | −10,87 | – | – |
| C3 | −10,62 | 1,6 | 1,5% |
| C3_stop | −7,51 | 1,6 | 26% |
| C3_and | −10,67 | 1,5 | 1,4% |

- **C3 contro B_0.25.** C3 non è mai peggiore in mediana: è migliore in 5 stagioni su 19 e uguale nelle altre. Il guadagno è piccolo (+0,24 in media sul totale) perché l'allarme ANOVA scatta poco, circa 1,6 volte per stagione: con soglie calibrate, una varianza degli errori che cresce sui dati reali è rara (`conclusioni_progetto.md` §4.4).
- **C3_stop contro B_0.25.** C3_stop è migliore in 9 stagioni su 19 e mai peggiore, con il totale più alto nel 96% dei seed.
- **Sulle stagioni vere** (us_c19) il quadro è meno pulito: C3 è migliore di B_0.25 in 10 stagioni e peggiore in 6, C3_stop in 12 e 4, C3_and in 6 e 7.
- **C3_and contro C3.** Il risultato è quasi lo stesso. L'allarme congiunto non è più raro (1,5 accensioni per stagione), perché le sue soglie sono più basse. Rispetto a B_0.25, C3_and è migliore in 8 stagioni su 19 e mai peggiore; rispetto a C3 la differenza appaiata è +0,03 sul totale (meglio in 4 stagioni, peggio in 1).
- **Lettura.** Il modello non batte il mercato in nessuna stagione, quindi ogni riduzione della puntata riduce la perdita. Lo schema funziona come previsto: riduce poco con errori di composizione e azzera con errori strutturali. Il segnale che cerca, però, è raro, e quando l'allarme si spegne lo schema torna al quarto di Kelly: per questo migliora poco il lavoratore senza supervisore, tranne nella versione che resta ferma fino a fine stagione.

**Perché l'allarme scatta poco** (`scripts/us_c12_anova_power.py`, `results/us_c12_anova_power.csv`). Non è un errore dell'implementazione: l'ANOVA funziona, ma fra due finestre vicine non c'è un cambiamento abbastanza grande da superare il rumore. Il cambiamento c'è fra una stagione e l'altra, e lo vede il confronto con la stagione di calibrazione (§3.4).
- **Sui dati reali gli allarmi sono quelli del caso.** Nelle date con almeno 80 partite alle spalle l'allarme è acceso nel 4,8% dei casi: 2,6% per la media e 2,2% per la dispersione, cioè il livello fissato (2,5% + 2,5%).
- **Con un cambiamento vero l'ANOVA lo trova.** Inserendo un peggioramento nei δ reali a metà stagione (partita 190), le stagioni con allarme nelle 10 date successive sono: 32% senza cambiamento (solo falsi allarmi), 42% con la media peggiore di 0,05, 68% con 0,10, 95% con 0,20; 42% con la varianza ×1,5, 53% con la varianza ×2.
- **Il rumore è grande rispetto al segnale.** Con 40 partite contro 40, la media deve peggiorare di almeno 0,07–0,11 (secondo il fit) perché la F superi la soglia, mentre lo svantaggio medio del modello rispetto al mercato è circa 0,02 per partita.
- **Non dipende dal residuo scelto.** Con la log-loss del modello al posto di δ l'allarme è acceso nel 5,0% delle date, di nuovo il livello del caso.

**Il 2023-24.** Lo schema è stato costruito dopo l'esecuzione unica sul test, quando il 2023-24 era già stato visto. È stato eseguito una volta sola sulla stagione giocata come in KellyBench (£100 000, floor £0,01, esiti veri), con i parametri congelati: è un risultato esplorativo, non una conferma (`results/kellybench_2023_24.csv`).

| Agente | Bankroll finale | Rendimento | Puntate |
|---|---|---|---|
| A | £14 | −99,99% | 361 |
| B_0.25 | £24 358 | −75,6% | 361 |
| C3 | £24 424 | −75,6% | 361 |
| C3_stop | £24 424 | −75,6% | 361 |
| C3_and | £26 755 | −73,2% | 352 |
| C3_ref | £24 944 | −75,1% | 361 |
| C3_ref_stop | £24 944 | −75,1% | 361 |

Come in validazione, lo schema cambia poco il risultato del quarto di Kelly; C3 e C3_stop coincidono perché nella stagione non c'è un errore strutturale che li separi. C3_ref e C3_ref_stop (§3.4) sono stati eseguiti dopo, anche loro una sola volta: il modello del 2023-24 è calibrato sul 2020-21, la dispersione di δ è quella della calibrazione (0,181 contro 0,186) e l'allarme scatta nell'1% delle date, quindi cambiano poco anche loro.

**Il 2023-24 su 500 stagioni ricostruite** (`scripts/us_c14_test_scheme_seeds.py`, `results/us_c14_test_scheme_seeds_summary.csv`; seed "block" dell'esecuzione unica, quindi A e B_0.25 coincidono con essa; senza floor, capitale riportato a £100 000):

| Agente | Stagione vera | Mediana | 5%–95% | Seed migliori di B_0.25 |
|---|---|---|---|---|
| A | £14 | £16 | £0–£1 564 | 0% |
| B_0.25 | £24 358 | £24 564 | £8 555–£71 172 | – |
| C3 | £24 424 | £25 750 | £8 701–£74 411 | 60% |
| C3_stop | £24 424 | £41 169 | £11 991–£106 895 | 73% |
| C3_and | £26 755 | £26 124 | £8 907–£72 300 | 69% |
| C3_ref | £24 944 | £26 391 | £9 158–£71 336 | 59% |
| C3_ref_stop | £24 944 | £51 185 | £18 409–£100 497 | 77% |

Sulle stagioni ricostruite l'allarme scatta 2–2,8 volte per stagione, contro quasi nessuna volta nella stagione vera: il ricampionamento delle date ripete alcune giornate e crea più spesso periodi di errori anomali. Le versioni ferme fino a fine stagione ne approfittano di più.

### 3.4 C3_ref e C3_ref_stop: il confronto con la stagione di calibrazione

**L'idea.** Il modello peggiora lentamente, di stagione in stagione, perché si ri-parametrizza solo ai fit. Due finestre di 40 partite vicine sono degradate allo stesso modo, e la loro differenza resta sotto il rumore (§3.3). La variante confronta invece le ultime 40 partite con **la stagione su cui il modello è stato calibrato** (la stagione di training del fit, 380 partite), cioè con il momento in cui il modello «era a posto».

**Come funziona.** Tutto il resto è come in C3:
- allarme con l'ANOVA sulla media e con Brown-Forsythe sulla dispersione, con segno, fra la stagione di calibrazione e le ultime 40 partite (gruppi di dimensione diversa);
- diagnosi con la three-fold di Oaxaca-Blinder fra gli stessi due gruppi;
- λ = 0,25, 0,1875 o 0, finché dura l'allarme (C3_ref) o fino a fine stagione (C3_ref_stop).

Le soglie di media, dispersione e componente strutturale sono calibrate sul training (`results/us_c13_scheme_reference_thresholds.csv`): si ricampionano a blocchi 40 righe della stagione di calibrazione e si confrontano con la stagione intera, al 2,5% per media e dispersione e al 5% per −S. W = 40 e κ = 0,75 restano quelli congelati.

**È una variante scelta dopo.** L'ho trovata provando segnali diversi sulla validazione e guardando solo quanto spesso scattava l'allarme, non i rendimenti: con le finestre adiacenti l'allarme è al livello del caso con qualunque misura dell'errore (δ, log-loss, Brier) e finestra (40, 80, 120); con il riferimento fisso e δ scatta molto più spesso, e con la log-loss no.

**Il segnale.** L'allarme cresce con l'età del modello. Per il modello calibrato sul 2010-11 (quota di date con allarme, W = 40):

| Stagione | Allarme sulla media | Allarme sulla dispersione |
|---|---|---|
| 2011-12 | 17% | 43% |
| 2014-15 | 2% | 0% |
| 2016-17 | 30% | 65% |
| 2017-18 | 27% | 73% |
| 2018-19 | 49% | 66% |
| 2019-20 | 5% | 76% |

La dispersione di δ passa da 0,136 nella stagione di calibrazione a 0,19–0,20 nel 2017-20. La log-loss del modello, invece, non peggiora rispetto alla calibrazione: è il mercato che migliora e lascia indietro il modello.

**Risultati sulla validazione** (`scripts/us_c13_scheme_reference.py`, 19 stagioni × 500 seed, gli stessi delle altre esecuzioni; B_0.25 coincide bit per bit, configurazione £0,01):

| Agente | Somma delle mediane di ln W_T | Accensioni per stagione | Date con λ = 0 |
|---|---|---|---|
| B_0.25 | −10,87 | – | – |
| C3 | −10,62 | 1,6 | 1,5% |
| C3_stop | −7,51 | 1,6 | 26% |
| C3_ref | −9,19 | 4,5 | 15% |
| C3_ref_stop | −4,50 | 4,5 | 64% |

- **C3_ref contro B_0.25:** migliore in 15 stagioni su 19, peggiore in 2; totale più alto nel 90% dei seed. Contro C3: migliore in 14, peggiore in 3.
- **C3_ref_stop contro B_0.25:** migliore in 15 stagioni su 19, peggiore in 2; totale più alto nel 97% dei seed. Contro C3_stop: migliore in 16, peggiore in 2.
- **Sulle stagioni vere** (us_c19): C3_ref e C3_ref_stop sono migliori di B_0.25 in 14 stagioni su 19 e peggiori in 5; capitale tipico 62% e 71% contro 57%. L'allarme scatta 4,8 volte per stagione e C3_ref_stop non punta nel 59% delle date.
- **Dove guadagna.** Sulla mediana delle ricostruite C3_ref guadagna di più nelle stagioni in cui il modello è vecchio (dal sesto anno dopo il fit: +0,15 per stagione contro +0,05; Spearman fra età e guadagno 0,38). Sulle stagioni vere no: +0,06 contro +0,09, Spearman −0,06. Anche per C3_ref_stop sulle stagioni vere il guadagno non dipende dall'età del modello. L'allarme è più acceso dove il modello è vecchio, ma il guadagno in capitale non segue.
- **Cautele.** La variante è stata scelta dopo aver visto la validazione (solo le frequenze d'allarme). Con un vantaggio negativo puntare meno aiuta comunque: C3_ref_stop non punta nel 64% delle date. Sul 2023-24, eseguita una volta in modo esplorativo, cambia poco (§3.3).

### 3.5 Perché Oaxaca-Blinder separa poco i due tipi di errore

Verifica in `scripts/us_c15_oaxaca_position.py`, `results/us_c15_oaxaca_position.csv`.

**1. Le covariate spiegano quasi niente di δ.** L'R² della regressione di δ sulle covariate congelate è 0,025 in mediana fra le stagioni: δ dipende quasi tutto dall'esito uscito, non dal tipo di partita. La componente compositiva resta quindi piccola per costruzione, e quasi tutto il cambiamento finisce nella strutturale (soprattutto lo spostamento dell'intercetta).

**2. «position» non si sovrappone fra finestre adiacenti.** La finestra A contiene le partite precedenti alla B (per esempio 1–40 e 41–80), quindi la decomposizione estrapola l'effetto della posizione. Sulle finestre adiacenti della validazione (deviazione standard delle componenti):

| Componente | Con «position» | Senza «position» |
|---|---|---|
| Totale | 0,049 | 0,049 |
| Compositiva | 0,117 | 0,014 |
| Strutturale | 0,124 | 0,049 |
| Interazione | 0,164 | 0,019 |

Con «position» compositiva e interazione si compensano (correlazione −0,71). Con il riferimento fisso il problema è minore, perché le ultime W partite cadono dentro le posizioni della stagione di calibrazione.

**Lo schema senza «position».** Soglie di media e dispersione invariate, soglia strutturale ricalibrata sul training; 100 seed appaiati. Gli allarmi non cambiano (l'ANOVA non usa le covariate); cambia la diagnosi:

| Disegno | Giornate con allarme (stagioni osservate) | Strutturali, con «position» | Strutturali, senza |
|---|---|---|---|
| Finestre adiacenti (C3) | 77 | 51% | 42% |
| Riferimento fisso (C3_ref) | 608 | 42% | 32% |

| Agente | Capitale tipico, con «position» | Senza «position» |
|---|---|---|
| B_0.25 | 54,5% | – |
| C3 | 55,2% | 55,1% |
| C3_stop | 65,5% | 64,1% |
| C3_ref | 60,7% | 60,4% |
| C3_ref_stop | 78,3% | 73,6% |

Senza «position» la diagnosi è più stabile e meno spesso strutturale, quindi lo schema punta di più e, con un vantaggio negativo, perde un po' di più. La conclusione non dipende da questa covariata, e lo schema tiene la specificazione congelata, scelta prima dei risultati.

**Oaxaca sull'errore atteso** (`scripts/us_c16_oaxaca_expected.py`, `results/us_c16_oaxaca_expected.csv`). Il rimedio al primo problema è cambiare la risposta: invece di δ realizzato si scompone l'errore atteso E_q[δ] = Σ q·ln(p̂/q) = −KL(q ‖ p̂), la distanza fra modello e mercato prima della partita, che non dipende dall'esito. La sua media coincide con quella di δ (−0,022), come deve essere se il mercato è calibrato. L'allarme ANOVA resta su δ realizzato; cambia solo la diagnosi, con soglie strutturali ricalibrate sul training.
- **Le covariate spiegano molto di più:** R² mediano 0,41 contro 0,025.
- **Le componenti non sono più dominate dal rumore:** sulle finestre adiacenti senza «position» le deviazioni standard di compositiva, strutturale e interazione sono 0,0036, 0,0046 e 0,0020, contro 0,0059 del totale.
- **La diagnosi diventa coerente con la teoria:** con le finestre adiacenti solo il 5% delle giornate con allarme risulta strutturale (fra due periodi vicini cambiano le partite, non il modello); con il riferimento fisso il 47% (rispetto alla calibrazione il modello è cambiato).
- **Il capitale non migliora** (100 seed appaiati):

| Agente | Errore atteso | Errore realizzato |
|---|---|---|
| C3 | 55,1% | 55,2% |
| C3_stop | 58,7% | 65,5% |
| C3_ref | 61,9% | 60,7% |
| C3_ref_stop | 76,4% | 78,3% |

Con le finestre adiacenti le diagnosi strutturali quasi spariscono, quindi C3_stop si ferma di rado e perde di più. La separazione fra i due tipi di errore diventa credibile, ma con un vantaggio negativo conviene comunque fermarsi spesso. È una variante scelta dopo aver visto i dati; misura la distanza dal mercato, non dalla realtà.

### 3.6 La ri-parametrizzazione annuale del modello

**L'idea.** Per l'errore strutturale il relatore indica, come seconda scelta, di ri-parametrizzare il modello. Nel progetto l'Elo si calibra solo ai fit 2000-01, 2010-11 e 2020-21, e invecchia (§3.4). La prova più semplice: prima di ogni stagione di validazione K, h e ν si ricalibrano sulla stagione precedente con quote B365 (per il 2002-03 il 2000-01, perché il 2001-02 non ha B365), con `elo_fit.calibrate_single_fit`, quindi con soli dati passati. Modulo `shk.model.elo_refit`, script `scripts/us_c18_elo_refit.py`.

**Il modello.** Parametri in `results/us_c18_elo_refit_params.csv`, confronto per stagione in `results/us_c18_elo_refit_aging.csv`.
- K va da 5 a 42 da un anno all'altro: una stagione sola stima i parametri con molto rumore. Sul 2020-21, giocato a porte chiuse, h = 0 e K = 5 (ai limiti): il modello porta nel 2021-22 un vantaggio del campo nullo.
- L'errore atteso E_q[δ] si avvicina a zero in 14 stagioni su 18 (media da −0,0227 a −0,0201), ma ĝ e log-loss migliorano solo in 7: in media ĝ passa da −0,0222 a −0,0225 e la log-loss da 0,9795 a 0,9798. Il modello ricalibrato è più vicino al mercato, non alla realtà.

**Lo schema sul modello ricalibrato.** B_0.25, C3_ref e C3_ref_stop sulle 19 stagioni × 500 seed, gli stessi di us_c13; soglie del riferimento fisso calibrate su ogni stagione di calibrazione (`results/us_c18_elo_refit_thresholds.csv`). Capitale tipico (£0,01):

| Agente | Modello congelato (us_c13) | Ricalibrato ogni anno |
|---|---|---|
| B_0.25 | 56% | 45% |
| C3_ref | 62% | 50% |
| C3_ref_stop | 79% | 72% |

- **Ricalibrare non aiuta:** tutti gli agenti perdono di più; il modello ricalibrato fa meglio di quello congelato solo in 6 stagioni su 19. Sulle stagioni vere il capitale tipico è 46% contro 57% (B_0.25), 53% contro 62% (C3_ref), 67% contro 71% (C3_ref_stop).
- **Lo schema resta utile:** C3_ref è meglio di B_0.25 in 15 stagioni su 19 e C3_ref_stop in 17 (sulle stagioni vere 13 e 12, peggio in 4 e 5). L'allarme scatta un po' meno (4,0 volte per stagione contro 4,5), perché il riferimento è sempre la stagione appena passata.
- **Lettura:** in questa forma la seconda opzione del relatore va peggio del moltiplicatore. Una ri-parametrizzazione su più stagioni, o solo dopo un errore strutturale, non è stata provata.

## 4. Il lavoratore sceglie l'esito: regole R1, R2, R3

Il relatore ha chiesto di far scegliere l'esito anche al lavoratore («proverei anche a differenziare») e ha scelto l'opzione A: lavoratori classici più un LLM, con il supervisore che agisce sulla puntata. Il disegno è in `thesis/disegno_lavoratore.md`; qui c'è la fase 1, con i lavoratori classici.

**Le regole.** Per ogni partita il lavoratore indica un esito candidato. Si punta solo se l'EV stimato del candidato è positivo; la frazione proposta è il Kelly pieno f_w su quell'esito.
- **R1, EV massimo:** la regola di §2.
- **R2, maggior vantaggio sul mercato:** l'esito con p̂ − q massimo, con q dal de-vigging di Shin.
- **R3, esito più probabile:** l'esito con p̂ massimo.

Nessuna regola ha parametri. Il ripiego (la puntata obbligatoria quando nessuna partita della data ha EV > 0) non cambia.

**Le versioni.** Ogni regola è provata in tre versioni, con f = λ · f_w:

| Versione | λ |
|---|---|
| Da solo | 1 (Kelly pieno) |
| Freno | 0,25 fisso |
| Schema C3 | dal supervisore, come in §3.3 |

Il supervisore non viene ricalibrato: finestre, soglie e κ sono quelli congelati. δ non dipende dalla regola, perché usa l'esito reale.

**Risultati sulla validazione.** 19 stagioni × 500 seed, gli stessi dell'esecuzione congelata, configurazione £0,01; script `scripts/us_c11_worker_rules.py`, sintesi in `results/us_c11_worker_rules_summary.csv`. Le tre versioni di R1 coincidono bit per bit con A, B_0.25 e C3 delle altre esecuzioni, quindi tutti i confronti sono appaiati.

Somma sulle stagioni della mediana di ln W_T (fra parentesi le puntate medie per stagione):

| Regola | Da solo | Freno | Schema C3 |
|---|---|---|---|
| R1 | −116,89 (304) | −10,87 (333) | −10,62 (330) |
| R2 | −119,55 (302) | −11,52 (333) | −11,27 (330) |
| R3 | −62,17 (177) | −7,84 (179) | −7,60 (178) |

Da solo, con Kelly pieno, il lavoratore va in rovina nel 29% dei seed con R1, nel 31% con R2 e nel 5% con R3. Con λ ≤ 0,25 nessuna versione va in rovina.

- **R3 è la regola migliore.** A parità di versione, R3 è meglio di R1 in mediana in 13 stagioni su 19 con freno o schema, e in 17 su 19 da solo. Punta su circa metà delle partite: sceglie solo i favoriti che hanno anche EV stimato positivo, e quindi si espone meno.
- **R2 è come R1, un po' peggio.** È peggiore in 10 stagioni su 19 con freno o schema. Scegliere dove p̂ si allontana di più dal mercato vuol dire puntare proprio dove il modello sbaglia di più.
- **Schema contro freno.** Per tutte e tre le regole lo schema non è mai peggiore del freno fisso ed è migliore in 5–6 stagioni su 19: il suo effetto non dipende dalla regola di scelta. Sulle stagioni vere è migliore in 10–11 stagioni e peggiore in 5–6, per tutte e tre le regole (us_c19).
- **Lettura.** Nessuna regola fa battere il mercato al modello. Cambiare la regola di scelta riduce l'esposizione, ma non crea un vantaggio.

**R3 con il riferimento fisso** (`scripts/us_c17_r3_reference.py`, `results/us_c17_r3_reference_summary.csv`; modulo `shk.model.worker_reference_run`). Combina la regola migliore (R3) con lo schema a riferimento fisso di §3.4: versioni R3_brake (λ = 0,25 fisso), R3_C3_ref e R3_C3_ref_stop, con le soglie di us_c13 e gli stessi seed. R3_brake coincide con quello di us_c11, quindi i confronti sono appaiati. Capitale tipico (exp della media sulle stagioni della mediana di ln W_T, £0,01):

| Versione | Con R1 (us_c11, us_c13) | Con R3 |
|---|---|---|
| Freno 0,25 | 56% | 66% |
| C3_ref | 62% | 71% |
| C3_ref_stop | 79% | 87% |

R3_C3_ref_stop è meglio di R3_brake in 14 stagioni su 19 e di C3_ref_stop (R1) in 15; R3_C3_ref è meglio di R3_brake e di C3_ref in 12. Sulle stagioni vere (us_c19) il capitale tipico è 68% (R3_brake), 69% (R3_C3_ref) e 77% (R3_C3_ref_stop), contro 57%, 62% e 71% con R1; R3_C3_ref_stop è meglio di R3_brake in 13 stagioni e peggio in 6, e di C3_ref_stop in 12 e peggio in 7. Gli effetti della regola e del riferimento fisso si sommano: entrambi riducono l'esposizione. È una combinazione scelta dopo aver visto la validazione.

## 5. Architettura: il progetto e KellyBench

I punti su KellyBench vengono dalla pagina dei risultati e dal paper (arXiv 2604.27865) e dalle note del progetto; verificali sul PDF prima di citarli.

| | **KellyBench** | **Questo progetto** |
|---|---|---|
| **Chi decide** | Un LLM autonomo che lavora in un sandbox con Python, senza internet, con 500–1000 chiamate a strumenti per episodio | Codice fisso: un modello previsivo (Elo) e regole di puntata scritte a mano |
| **Come prevede** | Ogni modello costruisce da sé modelli di machine learning dai dati storici | Un Elo con Davidson (Modulo 1), calibrato sul training con parametri congelati |
| **Chi calibra la puntata** | Lo stesso LLM, spesso con Kelly dichiarato ma applicato male | Il supervisore e il ricalibratore, separati dal modello previsivo |
| **Dati** | Risultati dal 1993, statistiche avanzate, formazioni, quote | Solo risultati e quote Bet365 1X2 pre-partita; niente Over/Under né statistiche |
| **Scenari** | Più scenari, con stagioni di training e la 2023-24 | 3 stagioni di training, 19 di validazione, la 2023-24 di test |
| **Ripetizioni** | 5 seed per modello: ogni seed è un LLM che ragiona in modo diverso | Gli agenti sono deterministici: il risultato è la stagione vera, una traiettoria; l'incertezza si misura con 500 stagioni ricostruite |
| **Bankroll** | £100 000 riscalati (lo scenario sottostante parte da £220) | Entrambe le scale; i risultati riportati usano £100 000 |
| **Risultato** | Rendimento medio, rovina in almeno un seed, rubrica di sofisticazione | Log-ricchezza, drawdown, rovina, confronti appaiati |
| **Dove gira** | Endpoint di OpenReward, a pagamento a consumo | Replica locale, con controllo completo di seed e scenari |

La differenza di fondo è questa: in KellyBench il tipo di agente è lo stesso per tutti (un LLM che fa tutto) e si misura quanto bene lo fa. Nel progetto l'architettura è scomposta in moduli, e si misura che cosa aggiunge il supervisore confrontando lo stesso lavoratore con e senza.

Altre conseguenze pratiche:
- Nel progetto un seed costa quasi nulla e se ne usano centinaia; nel paper un seed è una run completa di un LLM.
- Gli LLM del paper possono fallire per ragioni che qui non esistono (dimenticare di aggiornare i calcoli, puntare cifre a caso). Qui le regole sono codice.
- Il progetto non implementa la rubrica di sofisticazione né i dati avanzati di KellyBench.

## 6. Cosa cambia con DeepSeek Flash come Modulo 1

Rispetto alla struttura originale con Elo, la variante in `scripts/kellybench_llm_module1.py` cambia una sola cosa: chi produce p̂. Il resto (supervisore, ricalibratore, agenti, parametri congelati, ambiente) resta uguale.

| | **Struttura originale (Elo)** | **Variante con Flash come Modulo 1** |
|---|---|---|
| **Chi prevede p̂** | Elo-Davidson | DeepSeek Flash, via API |
| **Informazione** | Risultati precedenti | Data, squadre, ultime 5 partite e classifica parziale, solo con date anteriori; **mai le quote né l'esito** |
| **Determinismo** | Stesso risultato a ogni esecuzione | Stocastico: 5 esecuzioni diverse, poi la media |
| **Calibrazione** | Parametri calibrati sul training con δ dell'Elo | **Gli stessi parametri**, ma calibrati sul comportamento dell'Elo, non dell'LLM |
| **Probabilità estreme** | Mai vicine a 0 | Limitate a un minimo di 0,02, altrimenti ln p̂ esplode |
| **Protocollo** | Test eseguito una volta, fuori dalla riesecuzione | Esplorativo: il 2023-24 è già stato usato |
| **Dove scrive** | `results/` | Solo `build/llm/`, fuori dal manifesto |

Che cosa cambia rispetto a come KellyBench usa DeepSeek:
- **Nel paper** DeepSeek V4 Pro è l'agente intero: costruisce modelli, decide le puntate e usa gli strumenti. **Qui** Flash fa solo il Modulo 1: le puntate le decide lo schema.
- Il confronto con Pro misura quindi due cose insieme: la differenza fra i modelli e la differenza fra «LLM come agente» e «LLM come previsore dentro il sistema». Nella discussione della tesi vanno tenute separate.

Limiti da dichiarare per la variante:
- **Contaminazione:** Flash può conoscere gli esiti del 2023-24 dal proprio addestramento, quindi le previsioni potrebbero essere troppo buone.
- **Parametri non adatti:** finestre, soglie e κ sono stati scelti con l'Elo e non vengono ricalibrati.
- **Modalità di ragionamento:** è attiva di default; il parametro per spegnerla non è documentato nelle pagine che ho letto, e si può passare con `--extra-json`.

## 7. Dove guardare nel codice

| Cosa | File |
|---|---|
| Regole di puntata di A e B_0.25 | `src/shk/kelly/agents.py` |
| Kelly e puntate | `src/shk/kelly/staking.py`, `src/shk/kelly/core.py` |
| Ambiente, floor, rovina | `src/shk/kelly/environment.py` |
| Supervisore (ANOVA) e schema C3 | `src/shk/model/agent_c.py` (`Module2Supervisor`, `scheme_statistics`, `SchemeAgent`) |
| Ricalibratore, Oaxaca-Blinder (nel codice «Modulo 2») | `src/shk/stats/oaxaca.py`, `src/shk/model/module2.py` |
| Esecuzione dello schema sulla validazione | `src/shk/model/scheme_run.py`, `scripts/us_c10_scheme_validation.py` |
| Regole di scelta dell'esito del lavoratore | `src/shk/kelly/outcome_rules.py`, `src/shk/model/worker_run.py`, `src/shk/model/worker_reference_run.py` |
| Ri-parametrizzazione annuale dell'Elo | `src/shk/model/elo_refit.py`, `scripts/us_c18_elo_refit.py` |
| Costruzione degli agenti congelati | `src/shk/model/frozen_agents.py` |
| Stagione 2023-24 come KellyBench | `scripts/kellybench_2023_24.py`, `src/shk/model/kellybench_run.py` |
| Variante con LLM | `scripts/kellybench_llm_module1.py`, `src/shk/model/llm_module1.py` |
