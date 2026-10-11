---
Titolo: "TODO — Prerequisiti per la tesi Structural-Hybrid Kelly Agent"
Autore: Riccardo
Data: 2026-09-04
Versione: v4 — documento unificato con checkpoint di programmazione
Tags:
  - tesi
  - structural-hybrid-kelly
  - prerequisiti
  - checklist
---

# TODO — Prerequisiti tesi "Structural-Hybrid Kelly Agent" (v4)

> [!abstract] Come usare questo file
> Checklist operativa di tutto ciò che devo **sapere e saper fare prima e durante** lo sviluppo della tesi.
>
> **Legenda priorità:** 🔴 bloccante · 🟡 importante, procedibile in parallelo · 🟢 utile/opzionale
> **Legenda stato:** ✅ risolto · ❌ escluso con motivazione
> **⚙️ C1–C9** = checkpoint di programmazione, dettagliati in §12

> [!warning]+ Cosa cambia rispetto al v3
> - **Documento unico**: fuse la checklist v2 e l'espansione v3 di §2–§3. Non ci sono più file separati.
> - **§2 e §3 in capitoletti**: da elenchi piatti a §2.1–§2.9 e §3.1–§3.6.
> - **Nuova §12 — checkpoint di programmazione**: nove momenti in cui si scrive codice, distribuiti tra i blocchi di teoria. Non uno per argomento, non zero: uno per grappolo.
> - **Nessuna scadenza.** L'ordinamento è per dipendenza logica: cosa sblocca cosa.

> [!important]+ Le due esclusioni permanenti, con la loro ragione
> Non sono rinvii. Sono decisioni, e vanno tenute distinte tra loro.
>
> 1. **Ingiustizia epistemica** — esclusa perché **falsificata dal paper stesso**: la rubrica assegna 2 punti al Kelly frazionario contro 1 al Full Kelly. La gestione prudente del rischio è premiata, non penalizzata.
> 2. **Worker LLM** — vincolo di **budget**, non di scope: ≈ $2.000 per singolo seed su un modello di frontiera. Resta domanda aperta al relatore (§10), non decisione già presa.

---

## 0. Da fare subito, prima di tutto il resto 🔴

- [ ] **Leggere per intero `KellyBenchPaper.pdf`**, con attenzione a: §3 (ambiente, dati, tool, reward), §4.1 (modi di fallimento), Tabella 2 (risultati), Tabella 3 (prevalenza fallimenti), Tabella 5 (rubrica), §4.2.1 (ablazioni harness/letteratura), §5.1 (limiti), Appendice A (narrative per modello)
- [ ] Verificare riga per riga la **scheda fattuale §1 del piano** contro il PDF, e correggere ciò che non torna
- [ ] Verificare lo **stato editoriale** del paper (peer-reviewed? preprint? dove?) — prassi sistematica del relatore
- [ ] **Verificare il floor di puntata**: il testo cita sia £0.01 come strategia di conservazione, sia un floor di £1 che nella narrativa GLM-5 converte il Kelly frazionario in staking piatto. Chiarire il vincolo reale — ci poggia una delle critiche difendibili (§2.9)
- [ ] Verificare accessibilità e costi dell'endpoint **OpenReward**
- [ ] **Mandare la mail al relatore** con le domande di §10 — sono sul percorso critico, la risposta condiziona scelte strutturali

---

## 1. Fondamenti statistici — da conoscere a menadito

> [!important]+ Perché questa è la sezione più importante
> Modulo 2 e Modulo 3 sono un'orchestrazione di 5-6 strumenti statistici classici. Se questi non sono saldi, formalizzazione, esperimenti e discussione crollano.

### 1.1 Criterio di Kelly 🔴

- [x] Derivazione della formula di Kelly (massimizzazione dell'utilità logaritmica del bankroll)
- [x] Formula base: $f^* = (bp - q)/b$
- [x] Perché il Full Kelly è ad altissima varianza (volatilità di crescita a parità di edge)
- [x] Kelly frazionario: perché e come si usa (Thorp, MacLean, Ziemba)
- [x] Rischio di rovina e sua dipendenza dalla frazione usata
- [x] **Tasso di crescita certo-equivalente**: metrica corretta per confrontare frazioni diverse, perché rende esplicito il trade-off crescita/varianza. Senza, il confronto tra agenti A–F è ambiguo
- [x] 🔴 **Nessuna regola di staking crea edge**: con vig ~5.3%, se il Modulo 1 non batte la linea di chiusura l'EV resta negativo per ogni $\lambda$. È il vincolo che definisce cosa la tesi può e non può dimostrare
- [x] 🟡 Forma di divergenza: $g(p; p^*, q) = D_{KL}(p^*\|q) - D_{KL}(p^*\|p)$

> [!tip] ⚙️ **Checkpoint C1** — simulatore Kelly, mediana vs media, effetto della frazione. Vedi §12

### 1.2 ANOVA di Fisher e partizione della varianza 🔴 *(in corso)*

- [ ] Scomposizione della devianza totale in spiegata + residua
- [ ] Collegamento tra ANOVA a una via e R²
- [ ] Applicazione fuori dal contesto "gruppi sperimentali": nel Paper 1 confronta varianza spiegata da un fattore vs varianza totale. Schema da riusare per: varianza del rendimento spiegata da "tipo di partita" vs varianza totale
- [ ] 🔴 **Capire dove lo schema si rompe**: le osservazioni di un bankroll non sono indipendenti (autocorrelazione + compounding). Saper spiegare a voce perché e cosa si usa al posto (§8)

> [!tip] ⚙️ **Checkpoint C2** — SS a mano vs scipy, e tasso di falso rigetto su serie autocorrelata. Vedi §12

### 1.3 Effect size: R², Cohen's d, OVL 🔴

- [ ] $d = \Delta/\sigma$ e soglie convenzionali (0.2 / 0.5 / 0.8)
- [ ] $z = d/\sqrt{2}$, $P = \Phi(z)$
- [ ] $\text{OVL} = 2\Phi(-|d|/2)$ — cosa misura e come si interpreta
- [ ] 🔴 **Chiarire l'incoerenza tra due formule di R²**:
      - Paper 1 (Eq. 1): $R^2 = \Delta^2/\sigma^2 = d^2$ → con d = 0.11 dà **1.2%**
      - Conversione standard d → r² per due gruppi bilanciati: $R^2 = d^2/(d^2+4)$ → con d = 0.11 dà **0.3%**
      Sono quantità diverse. Il Paper 1 usa la prima come **upper bound dichiarato sotto il proprio framework**. Saper spiegare a voce quale uso e perché — altrimenti è una domanda letale all'orale
- [ ] **Punto metodologico da saper argomentare**: perché con N grande un p-value bassissimo non implica un effetto rilevante (Eq. 6: $n = (3.89\,\sigma/\Delta)^2$, dove 3.89 = $z_{\alpha/2} + z_\beta$ per α = 0.05 e potenza 80%)
- [ ] ⚠️ Discrepanza rilevata: la costante 3.89 implica potenza ~78.5%, non 80%. Portarla al relatore
- [ ] ⚠️ Su dati log-normali la formula chiusa di P dà il segno sbagliato; lo stimatore per conteggio dà la risposta corretta

### 1.4 Z-test di divergenza da una baseline nota 🔴

- [ ] Formula (CMES, Eq. 2): $Z = (OBS - I_C)/\sqrt{(1-I_C)I_C/N}$
- [ ] Quando si usa un test di proporzione a un campione contro riferimento noto, invece del confronto a due campioni
- [ ] Soglia $|Z| > 1.96$ e cosa significa dichiarare un gruppo "outlier strutturale"
- [ ] 🔴 **Controllo per test ripetuti**: un test per giornata a α = 0.05 su 38 giornate dà ~2 falsi allarmi attesi anche senza drift. Alpha spending e/o calibrazione della soglia via Monte Carlo sotto H₀ di stazionarietà
- [ ] 🔴 **Il problema della baseline non esterna**: nei paper del relatore $I_C$ è un riferimento nazionale indipendente. Nella tesi il riferimento deriva dalla stessa storia da cui il modello è stimato. Capire cosa cambia e come dichiararlo
- [ ] ⚠️ Discrepanza Paper 3: probabile errore di virgola (Z = −22.51 ricalcolato vs −225.1 pubblicato)

### 1.5 Decomposizione Oaxaca-Blinder 🔴

- [ ] Origine (Oaxaca 1973, Blinder 1973 — differenziali salariali) e riadattamento in epidemiologia
- [ ] Logica generale: differenza osservata = componente compositiva/spiegata (endowments) + componente non spiegata/strutturale (coefficients)
- [ ] Riprodurre a mano la **decomposizione moltiplicativa** del paper vitiligine: $HR = HR_{str} \times HR_{res}$ — ⚠️ il paper la presenta come **standardizzazione diretta per età con decomposizione moltiplicativa**, non come OB in senso stretto (OB è basata su regressione). Non confondere le due
- [ ] Riprodurre la **decomposizione additiva w/b** del paper CMES (Eq. 5, Tabella 5)
- [ ] Capire la differenza tra le varianti e quale userò nel dominio scommesse
- [ ] 🔴 **Definizione operativa dei due gruppi in contesto sequenziale** — il punto tecnico più delicato dell'intera tesi. OB richiede due gruppi con covariate e una regressione per gruppo. Definizione proposta: *finestra pre-rottura* vs *finestra post-rottura*, regressione dell'errore di previsione su covariate osservabili (fascia di quota, casa/trasferta, differenziale Elo, flag squadra nuova, giornata), decomposizione della differenza di errore medio. Scriverla per esteso e portarla al relatore
- [ ] 🟡 Indeterminatezza della decomposizione (quale gruppo fa da riferimento) e soluzioni standard (Neumark, Oaxaca-Ransom)
- [ ] 🟡 Gerarchia: OLS ⊂ RIF regression, Oaxaca-Blinder ⊂ RIF decomposition

> [!tip] ⚙️ **Checkpoint C7** — OB custom, validata su dati sintetici a decomposizione nota. Vedi §12

### 1.6 Difference-in-Differences 🔴

- [ ] Logica classica (trattamento vs controllo, prima vs dopo)
- [ ] **Attenzione**: nel paper CMES il DiD non è nella forma canonica temporale ma "spaziale/strutturale" (Eq. 3–4: $Diff_L = (OBS_L - I_C)/I_C$, poi $DiD = Diff_{L,E} - Diff_{L,NE}$). Capire la variante prima di riproporla e saper argomentare perché è valida
- [ ] Assunzione di parallel trends: come si traduce nella versione spaziale/strutturale, e nella mia versione sequenziale (dove il tempo torna a esserci davvero)
- [ ] ⚠️ Discrepanza Paper 3: incoerenza di scala Eq. 5 vs Tabella 5 (il lato destro somma 3.44, non $\ln(1.27) = 0.239$)

### 1.7 Recentered Influence Function (RIF) regression 🟡

- [ ] Cos'è e in cosa differisce da una OLS classica (Firpo, Fortin, Lemieux 2009)
- [ ] A cosa serve nel paper CMES: riproiettare il contesto locale su un riferimento più ampio
- [ ] RIF sulla varianza: perché è lo strumento naturale se l'oggetto di interesse è la dispersione e non la media
- [ ] Decidere col relatore se implementarla o solo richiamarla concettualmente

### 1.8 Eteroschedasticità 🔴

- [ ] Definizione: varianza dell'errore non costante, spesso crescente con la media
- [ ] Test standard (Breusch-Pagan, White)
- [ ] Correzione HAC (Newey & West 1987)
- [ ] ⚠️ **Errore silenzioso noto**: statsmodels HAC **non** corregge `anova_lm`. Verificarlo esplicitamente
- [ ] Perché è il segnale d'allarme del Modulo 2

> [!tip] ⚙️ **Checkpoint C6** — Breusch-Pagan sui residui del Modulo 1 dentro il loop di backtest. Vedi §12

### 1.9 Concept drift detection 🔴

> [!danger] Perché è bloccante
> ADWIN, Page-Hinkley, DDM e CUSUM fanno già quello che fa il Modulo 2: rilevare quando un modello smette di funzionare. Sono lo standard consolidato. Se la tesi non li include come baseline, la prima domanda della commissione — *"perché ANOVA e non ADWIN?"* — resta senza risposta e il contributo è invalidabile.
> Risposta corretta, da dimostrare empiricamente: i detector standard dicono **quando**, il framework proposto dice **quanto** e **di che tipo**, e solo la seconda informazione si mappa su una regola di staking graduata.

- [ ] CUSUM (Page 1954) e Page-Hinkley (Hinkley 1971): logica e parametrizzazione
- [ ] ADWIN (Bifet & Gavaldà 2007): finestra adattiva, garanzie teoriche
- [ ] DDM / EDDM: rilevamento basato sul tasso di errore
- [ ] Gama et al. (2014): tassonomia drift graduale/improvviso/ricorrente
- [ ] 🔴 **Mappatura sulla tassonomia propria**: virtual drift → compositivo, real drift → strutturale. Operativizza una distinzione irrisolta da vent'anni nella letteratura
- [ ] Saper posizionare il proprio framework: cosa aggiunge, cosa non aggiunge

> [!tip] ⚙️ **Checkpoint C5** — ADWIN e Page-Hinkley da `river` sui residui reali, soglia calibrata Monte Carlo. Vedi §12

---

## 2. Dominio scommesse sportive / mercati 🔴

### 2.1 Da quota a probabilità implicita 🔴

- [ ] Quota decimale $o$: payout lordo per unità puntata. Vincita netta $b = o - 1$
- [ ] Probabilità implicita grezza: $\tilde{p} = 1/o$
- [ ] Formati alternativi (frazionario UK, americano), per non restare bloccato se una fonte li usa
- [ ] Verificare in che formato sono le quote di `football-data.co.uk` (colonne `B365H/D/A`, `PSH/D/A`, ecc.)
- [ ] 🔴 **Distinguere sempre $\tilde{p}$ (grezza, somma > 1) da $q$ (de-viggata, somma = 1)**. Nella formula di crescita compare $q$, mai $\tilde{p}$. Usare la grezza gonfia l'edge, ed è un errore silenzioso
- [ ] Quote di bookmaker diversi sullo stesso match: quale usare, o se aggregarle (media, mediana, best price). La scelta cambia l'overround effettivo

### 2.2 Overround, vig e metodi di de-vigging 🔴

*È la scelta metodologica che si propaga su ogni risultato successivo.*

- [ ] Definizione: $\Omega = \sum_i 1/o_i - 1$. Nel setup KellyBench $\Omega \approx 5.3\%$
- [ ] Perché $\Omega > 0$: margine del bookmaker, non errore di misura
- [ ] **Proporzionale (normalizzazione multiplicativa)**: $q_i = \tilde{p}_i / \sum_j \tilde{p}_j$. Semplice, ma assume margine distribuito proporzionalmente — falso in presenza di favourite-longshot bias
- [ ] **Additivo**: $q_i = \tilde{p}_i - \Omega/n$. Margine in parti uguali
- [ ] **Shin (1992, 1993)**: modella il margine come derivante da insider trading; soluzione numerica per il parametro $z$. Studiare la derivazione, non solo la formula
- [ ] **Power / Vovk-Zhdanov**: $q_i \propto \tilde{p}_i^{\,k}$, con $k$ risolto perché la somma faccia 1
- [ ] **Odds ratio method**: quarta famiglia, per completezza della rassegna
- [ ] 🔴 **Favourite-longshot bias**: le quote alte sono sistematicamente sopravvalutate. Il proporzionale non lo corregge, Shin e power sì in modo diverso. Se le scommesse si concentrano in una fascia di quota, la scelta del metodo *è* il risultato
- [ ] 🔴 **Analisi di sensibilità**: rieseguire la pipeline con almeno tre metodi e riportare come cambiano edge e risultati. Se cambia il segno, va detto in apertura
- [ ] 🟡 **Confronto empirico**: quale de-vigging produce probabilità meglio calibrate sui dati storici? Decidibile con reliability diagram e log-loss — giustifica la scelta invece di postularla
- [ ] Collegamento: la fascia di quota è covariata per la decomposizione OB (§1.5). Il de-vigging ne determina i valori

> [!danger] Domanda letale all'orale
> *"Perché ha scelto questo metodo di de-vigging?"* — se la risposta è "è quello standard", la domanda dopo è *"e con gli altri cosa succede?"*. Serve una tabella di sensibilità pronta.

> [!tip] ⚙️ **Checkpoint C3** — caricamento dati reali + tre metodi di de-vigging a confronto. Vedi §12

### 2.3 Edge, stima ed errore di stima 🔴

- [ ] Definizione base: $\text{edge} = \hat{p} - q$
- [ ] Perché l'edge additivo non è la quantità che entra in Kelly: $f^*$ dipende congiuntamente da $p$ e $b$, non dalla sola differenza
- [ ] Formulazione in valore atteso: $EV = \hat{p}\,o - 1$, e $f^* = EV/b$
- [ ] 🔴 **Sensibilità dell'errore di stima**: sovrastimare $p$ del 10% relativo può più che raddoppiare $f^*$ quando l'edge è sottile. Con $\Omega \approx 5.3\%$ gli edge veri sono piccoli e il rapporto rumore/segnale è alto
- [ ] 🔴 **Collegamento al risultato proprio**: $\lambda^* = 1/(1 + \text{Var}(c))$, con $c = \hat{f}/f^*$. $\text{Var}(c)$ si alimenta esattamente di questo errore di stima
- [ ] 🔴 **Propagazione dell'incertezza**: da $\text{Var}(\hat{p})$ a $\text{Var}(\hat{f})$ a $\text{Var}(c)$. Scrivere la catena per esteso — è ciò che rende $\lambda^*$ operativa e non solo elegante
- [ ] Definire *a priori* la **soglia minima di edge** sotto cui non si punta, e giustificarla
- [ ] 🟡 **Kelly bayesiano/robusto**: $p$ come distribuzione a posteriori invece che stima puntuale. È la Baseline F, e il confronto con $\lambda^*$ è teoricamente interessante

### 2.4 Closing line value ed efficienza di mercato 🔴

*Contiene il test che determina l'interpretazione di tutti i risultati successivi.*

- [ ] Quote di apertura vs chiusura: cosa succede in mezzo (flusso scommesse, notizie, formazioni)
- [ ] Perché la **closing line** è il miglior stimatore pubblico della probabilità vera
- [ ] **CLV** come standard operativo per la presenza di edge nella pratica professionale
- [ ] Efficienza di mercato in forma debole/semiforte nei mercati sportivi: cosa dice la letteratura empirica
- [ ] 🔴 **KellyBench usa quote di chiusura** — compito più difficile. Da dichiarare esplicitamente
- [ ] 🔴 **Il test decisivo**: log-loss del Modulo 1 contro log-loss del mercato de-viggato. Se il modello non batte la linea, l'EV è negativo per ogni $\lambda$. La tesi resta valida ma dimostra qualcosa di diverso, e va detto in apertura
- [ ] 🔴 **Stimatore proprio**: $\hat{g} = \frac{1}{T}\sum_t [\ln p_t(x_t) - \ln q_t(x_t)]$. Unico segnale di edge falsificabile *ex-ante*
- [ ] 🔴 **Formalizzazione di $\hat{g}$ come sottosezione di tesi**: non-distorsione, intervalli via block bootstrap, comportamento sotto drift
- [ ] 🟡 Quando $\hat{g} < 0$ l'azione corretta è smettere di puntare. Verificare l'interazione col vincolo di almeno una scommessa per giornata (§2.9)
- [ ] Riferimento: GPT-5.4 ha misurato 0.974 vs 0.971 ed è passato alle puntate minime — comportamento corretto, termine di paragone per l'Agente C

> [!tip] ⚙️ **Checkpoint C4** — Elo funzionante e primo calcolo di $\hat{g}$. È il go/no-go. Vedi §12

### 2.5 Varianza della singola scommessa vs varianza del bankroll 🔴

- [ ] Varianza della singola puntata: $\text{Var} = f^2 b^2 p(1-p)$ — ⚠️ **vale per una scommessa singola, non per un portafoglio simultaneo**
- [ ] Portafoglio: serve la matrice di covarianza. Scommesse sulla stessa giornata su squadre diverse sono debolmente correlate; sullo stesso match fortemente
- [ ] 🟡 **Kelly per scommesse simultanee**: con vincolo di bankroll condiviso non ha soluzione in forma chiusa in generale. Ottimizzazione numerica o approssimazione — decidere e dichiarare
- [ ] **Compounding**: $B_T = B_0 \prod_t (1 + f_t r_t)$
- [ ] Perché il logaritmo rende additivo il processo moltiplicativo — filo conduttore metodologico dell'intera tesi
- [ ] **Path dependence**: l'ordine degli esiti conta. Due sequenze con gli stessi esiti in ordine diverso danno lo stesso $B_T$ solo in assenza di floor e vincoli — ed è il punto di §2.9
- [ ] Distribuzione log-normale del bankroll: media aritmetica $\neq$ mediana. Riportare la mediana come metrica primaria, e spiegare perché
- [ ] 🔴 **Il problema n = 1**: una traiettoria è una singola realizzazione autocorrelata. 380 partite non sono 380 osservazioni indipendenti. Rimedio: molti seed + block bootstrap (§8)
- [ ] Metriche da definire *a priori*: probabilità di rovina, massimo drawdown, tempo di recupero, deviazione standard del log-wealth, tasso di crescita certo-equivalente
- [ ] 🟡 **Tempo di primo passaggio** e teoria dei processi di rovina: espressioni analitiche per la probabilità di drawdown sotto Kelly frazionario, utili come controllo di sanità sui risultati simulati

### 2.6 Struttura dei mercati calcistici 🟡

- [ ] Mercato 1X2 (tre esiti) — quello di KellyBench. Verificare se l'ambiente ne consente altri
- [ ] Over/under e handicap asiatico: struttura e differenze. Se consentiti, cambiano lo spazio delle azioni
- [ ] Perché tre esiti rendono necessario il **Kelly multi-esito** e non la formula binaria
- [ ] Scommesse simultanee nella stessa giornata: correlazione e vincolo di bankroll condiviso
- [ ] Exchange vs bookmaker tradizionale: struttura della commissione, implicazioni sull'overround
- [ ] 🟢 Liquidità, limiti di puntata, impatto di mercato (Benter 2008). Nel backtest è irrilevante perché non c'è impatto, ma **va dichiarato come limite**: un edge che sopravvive in simulazione può non sopravvivere all'esecuzione

### 2.7 Concept drift nei mercati sportivi 🔴

*È il ponte tra §1.9 e il Modulo 2.*

- [ ] Fonti di drift: mercato dei trasferimenti, cambio allenatore, infortuni chiave, cambi di regolamento, composizione della lega
- [ ] 🔴 **Neopromosse come caso limite OOD**: nessuno storico in Premier League, Elo da inizializzare arbitrariamente, il modello estrapola invece di interpolare
- [ ] 🔴 **Doppio drift**: sia il modello sia il mercato si adattano, a velocità diverse. L'edge dipende dalla *differenza* tra le due velocità. Se il mercato riprezza prima, il drift si traduce immediatamente in EV negativo
- [ ] 🔴 **Mappatura sulla tassonomia propria**: virtual drift (cambia $P(X)$) → **componente compositiva**; real drift (cambia $P(y|X)$) → **componente strutturale**. Collegamento a Gama et al. (2014), contributo da portare al relatore
- [ ] Drift improvviso / graduale / ricorrente / incrementale: quali dei cinque scenari KellyBench corrispondono a quali tipi
- [ ] 🔴 **Perché il tipo determina la risposta**: compositivo → modello ancora valido, riduzione modesta; strutturale → modello degradato, riduzione forte o stop. Un detector binario non può distinguerli, ed è l'intera tesi
- [ ] 🟡 **Drift ricorrente stagionale**: inizio stagione, mercato invernale, fine stagione con squadre senza obiettivi. Se rilevabile nei dati è un caso di studio ideale, perché è compositivo per costruzione

### 2.8 Modelli previsivi calcistici 🔴

- [ ] **Elo**: formula di aggiornamento, fattore K, vantaggio casalingo, inizializzazione, gestione neopromosse
- [ ] Da rating Elo a probabilità 1X2: mapping esplicito, perché Elo nasce per due esiti e qui ce ne sono tre
- [ ] **Poisson indipendente**: gol casa e trasferta come Poisson indipendenti con parametri attacco/difesa
- [ ] **Dixon-Coles (1997)**: correzione $\tau$ per i punteggi bassi (0-0, 1-0, 0-1, 1-1), dove l'indipendenza fallisce empiricamente. Pesatura temporale esponenziale
- [ ] Stima dei parametri Dixon-Coles: massima verosimiglianza, vincoli di identificabilità, convergenza
- [ ] **Bradley-Terry**: confronto a coppie, relazione con Elo
- [ ] 🟡 **Modelli score-driven / state-space** (filtro di Kalman, GAS): la rubrica KellyBench li considera più sofisticati di Elo/medie esponenziali (2 punti vs 1). Rilevante per §3.5
- [ ] 🟡 **xG, infortuni, formazioni**: verificare disponibilità storica — quasi certamente non risalgono al 2002-03, il che crea un vincolo di finestra
- [ ] **Walk-forward validation**: nessun dato futuro nel training. Test anti-leakage automatico a ogni run
- [ ] **Calibrazione**: reliability diagram, Brier score, log-loss, calibrazione isotonica o di Platt. Un modello può ordinare bene e calibrare male — per Kelly conta la calibrazione, non l'ordinamento
- [ ] 🔴 **Confronto appaiato tra Moduli 1**: eseguire l'impianto con Elo e con Dixon-Coles. Se il ranking tra regole di staking si conserva, il contributo è robusto al modello sottostante. Se non si conserva, è un risultato ancora più interessante

> [!important] Perché il confronto tra due Moduli 1 vale la pena
> Con un solo modello, "il Modulo 1 non è il contributo" è un'affermazione. Con due, è una dimostrazione: mostrare che il ranking regge su modelli diversi chiude in anticipo una domanda ovvia della commissione.

> [!tip] ⚙️ **Checkpoint C9** — Dixon-Coles come secondo Modulo 1, rerun completo. Vedi §12

### 2.9 Vincoli operativi dell'ambiente 🔴

- [ ] 🔴 **Disponibilità storica**: risultati dal 1993–94, **quote solo dal 2002–03**. Nessun backtest con edge può partire prima. Verificare direttamente sul CSV, colonna per colonna
- [ ] 🔴 **Floor di puntata**: chiarire se £0.01 o £1 (vedi §0)
- [ ] 🔴 **Predizione falsificabile propria**: un floor rompe la struttura moltiplicativa di Kelly esattamente quando l'agente è più in difficoltà (bankroll basso → frazione ottimale sotto il floor → puntata forzata sovradimensionata), rendendo la rovina possibile con probabilità positiva
- [ ] 🔴 **Test empirico**: stesso agente con e senza floor, confronto dei tassi di rovina. Costo trascurabile, valore alto
- [ ] 🟡 **Derivazione analitica**: sotto quale rapporto bankroll/floor la struttura si rompe? Esiste una soglia in forma chiusa? Se sì, è un risultato pulito da affiancare a $\lambda^*$
- [ ] Vincolo di almeno una scommessa per giornata: interazione col floor e con "smetti di puntare" quando $\hat{g} < 0$
- [ ] Struttura a episodi con **disclosure progressiva**: giorno per giorno, solo i dati disponibili a quel momento
- [ ] Endpoint OpenReward vs replica locale → **domanda al relatore**
- [ ] Licenza d'uso di `football-data.co.uk` per una tesi

> [!tip] ⚙️ **Checkpoint C6** — il test del floor, dentro il loop di backtest. Vedi §12

---

## 3. IA / agenti / LLM

### 3.1 Agente LLM: definizione operativa 🟡

- [ ] Ciclo osserva–pensa–agisci; cosa significa "tool use" in pratica
- [ ] Gestione del contesto su orizzonte lungo: nel paper 500–900 tool call e 32–450 milioni di token per episodio
- [ ] Perché l'orizzonte lungo è il problema difficile: coerenza di strategia su una stagione intera
- [ ] 🟡 **Vincolo di budget**: ≈ $2.000 per singolo seed su un modello di frontiera. È la giustificazione quantitativa per un Modulo 1 classico, da citare in tesi
- [ ] 🟢 Se il budget esistesse: gestione chiamate API, riproducibilità (seed, temperature), logging dei ragionamenti

### 3.2 Pattern Worker / Supervisor 🔴

*È l'architettura dell'Agente C.*

- [ ] Logica generale: un componente esegue, un altro monitora e corregge
- [ ] 🔴 **L'Agente C è un Worker/Supervisor non-LLM**: Modulo 1 (worker) → Modulo 2 (supervisore) → Modulo 3 (ricalibratore). Sostanza architetturale identica, implementazione diversa
- [ ] 🔴 **Posizionamento della tesi**: gli autori di KellyBench dichiarano di **non aver eseguito** l'ablazione dello scaffold multi-agente. La tesi la esegue, con componenti deterministici e interpretabili
- [ ] **Separazione delle responsabilità**: il supervisore non deve poter cambiare le previsioni, solo la frazione. Se le cambiasse, il confronto appaiato perderebbe significato
- [ ] Differenza tra scaffold (struttura di controllo) e capacità del modello sottostante — è la distinzione che l'ablazione isola
- [ ] 🟡 **Ablazione interna dell'Agente C**: col supervisore disattivato, e col supervisore che rileva ma non gradua. Isola il contributo della decomposizione da quello del semplice monitoraggio

### 3.3 Generalizzazione fuori distribuzione 🟡

- [ ] Cosa significa OOD in termini di $P(X)$ e $P(y|X)$
- [ ] Perché la neopromossa è un caso da manuale: covariate fuori dal supporto del training
- [ ] Collegamento: OOD è il termine ML per ciò che in §2.7 è drift compositivo estremo
- [ ] Come si manifesta nelle metriche: log-loss peggiore su un sottoinsieme identificabile — esattamente ciò che la regressione OB dovrebbe attribuire alla componente compositiva
- [ ] 🟡 Rilevamento OOD vs rilevamento di drift: letterature separate che qui convergono

### 3.4 Modi di fallimento documentati in KellyBench 🔴

*La tesi spiega questi fallimenti: vanno conosciuti in dettaglio.*

- [ ] §4.1 del paper: tassonomia dei modi di fallimento
- [ ] Tabella 3: prevalenza di ciascun modo
- [ ] Appendice A: narrative per modello — almeno GPT-5.4 e GLM-5
- [ ] 🔴 **Per ciascun modo, una riga**: il framework lo previene, lo attenua, o non lo tocca? La risposta onesta sarà mista, e dirlo è più forte che sostenere il contrario
- [ ] 🔴 **Label leakage**: 6 seed su 24 hanno avuto leakage nelle proprie pipeline. È il fallimento più facile da replicare per errore → test automatico a ogni run
- [ ] Il seed passato alle puntate minime permanenti ha chiuso a −4.1%, meglio di quasi tutti gli altri → **è la Baseline E, e la ragione per cui è severa**
- [ ] 🟡 **Tabella fallimento → meccanismo**: per ogni modo, quale componente interviene e come. Materiale del capitolo di discussione

### 3.5 Sofisticazione come misura di processo 🟡

- [ ] Rubrica a 44 punti costruita con esperti: valutare il **processo** e non solo l'esito
- [ ] Perché è interessante: separa "ha guadagnato" da "ha ragionato bene", distinzione centrale in un dominio ad alta varianza dove l'esito è rumoroso
- [ ] 🔴 **Fatto che falsifica la vecchia cornice retorica**: 2 punti al Kelly frazionario contro 1 al Full Kelly. Non c'è ingiustizia epistemica contro la prudenza — è premiata
- [ ] 🟡 **Autovalutazione dell'Agente C sulla scala a 44 punti**: comparabilità diretta coi risultati pubblicati su una dimensione che non è il rendimento
- [ ] 🟡 Se il Modulo 1 include modelli score-driven, l'Agente C guadagna punti per costruzione. Verificare se è artefatto o misura sensata
- [ ] 🟡 **Limite della rubrica**: presuppone che la sofisticazione riconoscibile coincida con quella efficace. Non è ovvio — critica costruttiva legittima

### 3.6 Lessico RL 🟢

- [ ] Stato, azione, policy, reward, orizzonte — per leggere la letteratura senza inciampare
- [ ] Perché la tesi **non** è RL: nessun apprendimento della policy, la regola di staking è derivata analiticamente
- [ ] 🟢 Bandit setting e perché non si applica: qui le quote sono date e il feedback è completo, non solo sul braccio scelto
- [ ] ❌ **Ingiustizia epistemica — esclusa perché falsificata dal paper** (vedi §3.5)

---

## 4. Padronanza totale dei tre paper del relatore 🔴

> [!tip] Metodo
> Non limitarsi a leggerli: **riprodurre ogni tabella**, ricalcolando dai dati grezzi. Se un conto non torna, è lì che sta la comprensione reale.

- [ ] **Paper 1 (Reproductive History)**: ricalcolare R², Cohen's d, z, P, OVL da Δ = 1.0 e σ = 9.1
      *Attesi: R² ≈ 1.2%, d ≈ 0.110, z ≈ 0.077, P ≈ 53.1%, OVL ≈ 95.6%*
- [ ] Paper 1: ricalcolare Eq. 6 e capire da dove viene la costante 3.89
- [ ] **Paper 2 (Vitiligine)**: ricalcolare IR(NV, Expected), IR(V, Expected), HR structural, HR residual, HR corrected dalla Tabella 2
      *Attesi: HR_str ≈ 1.2104, HR_res ≈ 2.2423, prodotto ≈ 2.714, HR_corr ≈ 1.0025; IR attesa NV 2.2146/10.000 vs osservata 0.67/10.000*
- [ ] Paper 2: perché l'assenza di intervalli di confidenza è dichiarata come limite, e con quale motivazione (rapporti di medie ponderate non producono una stima di varianza adatta ai metodi standard) — **rilevante perché nella tesi il bootstrap costa quasi nulla e quella giustificazione non si trasferisce**
- [ ] **Paper 3 (CMES)**: ricalcolare Z-score (Eq. 2), Diff_L e DiD (Eq. 3–4), decomposizione w/b (Eq. 5) dalla Tabella 2
- [ ] Paper 3: scrivere in autonomia, senza guardare, la tupla $S = \langle L, C, D, OBS, OBS_E, OBS_{NE}, N, I_C, RF_{OBS}, RRF\rangle$ e la sua interpretazione — è il template da riadattare
- [ ] 🔴 **Per ciascun paper, elencare quali assunzioni si rompono nel trasferimento al dominio scommesse.** Almeno:
      1. Non ho due coorti statiche ma una serie temporale
      2. Il riferimento $I_C$ non è esterno e indipendente ma deriva dagli stessi dati storici del modello
      3. Le osservazioni non sono indipendenti: il bankroll compone, quindi l'ordine conta

### 4.1 Discrepanze rilevate — da portare al relatore 🔴

- [ ] Paper 1: σ è SD di popolazione, non SD entro gruppo
- [ ] Paper 1: la costante 3.89 implica potenza ~78.5%, non 80%
- [ ] Paper 1: il simbolo R² è usato per due oggetti diversi (§0.1 vs §6)
- [ ] Paper 1: oscillazione notazionale N vs n
- [ ] Paper 1: d = 1.0/9.1 = 0.11 — la scelta del denominatore è una mossa argomentativa, non puramente tecnica
- [ ] Paper 2: le percentuali di colonna della coorte V sommano a 98.99%, non 100%
- [ ] Paper 3: probabile errore di virgola (Z = −22.51 ricalcolato vs −225.1 pubblicato)
- [ ] Paper 3: incoerenza di scala Eq. 5 vs Tabella 5 (somma 3.44 vs $\ln(1.27) = 0.239$)
- [ ] Note: ω² e R²_adj presentati come equivalenti in §6.3, ma sono stimatori distinti
- [ ] Note: esercizio 4 §13 dà d ≈ 0.112, il valore corretto è 0.110

---

## 5. Competenze tecniche / dati 🔴

*Cosa serve saper usare. **Quando** si esercita è in §12.*

### 5.1 Python / stack statistico

- [ ] pandas (serie temporali di partite e quote)
- [ ] numpy / scipy.stats
- [ ] statsmodels (regressioni, ANOVA)
- [ ] 🔴 **Programmazione a oggetti**: lacuna dichiarata. Si impara al checkpoint C6, quando gli agenti condividono comportamento e una classe base risolve un problema reale invece che teorico
- [ ] 🟡 `river` o `scikit-multiflow` per i drift detector (ADWIN, Page-Hinkley pronti all'uso)
- [ ] 🟢 Oaxaca-Blinder: nessuno standard consolidato in Python. **Implementazione custom preferibile** (~50 righe): rende la decomposizione parte del contributo e ne garantisce la trasparenza
- [ ] 🟡 Block bootstrap: moving block / stationary bootstrap di Politis-Romano
- [ ] 🟡 Controllo di versione (git) e struttura di progetto riproducibile

### 5.2 Dati e ambiente

- [ ] Decidere: **endpoint OpenReward** (comparabilità) vs **replica locale** (controllo) → relatore
- [ ] Se replica locale: `football-data.co.uk` è quasi certamente la fonte (le variabili elencate coincidono). Verificare licenza
- [ ] 🔴 **Disponibilità storica**: quote solo dal 2002–03. Nessun errore è più facile da fare né più fatale
- [ ] 🟡 Statistiche aggiuntive (xG, infortuni, formazioni) per un Modulo 1 più ricco
- [ ] Simulatore a episodi con **disclosure progressiva** + **test automatico anti-leakage a ogni run**
- [ ] Replicare i vincoli dell'ambiente originale (almeno una scommessa per giornata, floor)

### 5.3 Implementazione agenti

- [ ] Modulo 1: Elo, poi Dixon-Coles, con walk-forward validation
- [ ] 🔴 **Verifica onesta dell'edge**: log-loss modello vs mercato. Se non batte la closing line va detto in apertura
- [ ] Baseline A: Full Kelly ingenuo
- [ ] Baseline B: Kelly frazionario fisso (0.25 e 0.10)
- [ ] **Agente C: Structural-Hybrid** (Lavoratore + Supervisore + Ricalibratore)
- [ ] 🔴 **Baseline D: Kelly frazionario con drift detector standard** — *se C non batte D, il contributo originale non esiste*
- [ ] 🔴 **Baseline E: puntata minima permanente** — *se C non batte E, il framework non serve*
- [ ] 🟡 Baseline F: Kelly bayesiano/robusto con incertezza sui parametri
- [ ] Esecuzione **appaiata**: tutti gli agenti sulla stessa sequenza, l'unica differenza è la regola di staking

---

## 6. Letteratura da reperire e leggere

- [x] ✅ **Grady et al. (2026) — KellyBench** — *nel progetto*
- [ ] 🔴 Kelly J.L. (1956) — *A New Interpretation of Information Rate*
- [ ] 🔴 Oaxaca (1973), Blinder (1973) — articoli originali
- [ ] 🔴 Jann B. (2008) — *The Blinder-Oaxaca decomposition for linear regression models*, Stata Journal
- [ ] 🔴 Bifet & Gavaldà (2007) — ADWIN
- [ ] 🔴 Gama et al. (2014) — survey su concept drift adaptation
- [ ] 🟡 Thorp (1997/2008), MacLean & Ziemba — Kelly frazionario
- [ ] 🟡 Dixon & Coles (1997) — modello Poisson per il calcio
- [ ] 🟡 Shin (1992, 1993) — de-vigging con insider trading
- [ ] 🟡 Firpo, Fortin, Lemieux (2009) — *Unconditional Quantile Regressions*
- [ ] 🟡 Benter (2008) — Kelly frazionario e impatto di mercato
- [ ] 🟡 Politis & Romano (1994), Künsch (1989) — block bootstrap
- [ ] 🟡 Newey & West (1987) — HAC
- [ ] 🟢 Cohen J. (1988) — *Statistical Power Analysis for the Behavioral Sciences*
- [ ] 🟢 Page (1954), Hinkley (1971) — CUSUM e Page-Hinkley
- [ ] 🟢 Fisher (1918, 1925, 1935) — fonti originali della decomposizione

---

## 7. Scrittura e metodo — lo stile del relatore 🟡

- [ ] Schema argomentativo ricorrente nei tre paper: (a) risultato pubblicato sotto scrutinio, (b) tecnica classica di decomposizione/effect-size, (c) il segnale collassa o si ridimensiona, (d) raccomandazioni generalizzabili
- [ ] 🔴 **Adattarlo, non copiarlo**: qui il segnale *non collassa*. I risultati di KellyBench reggono. La tesi non fa (c) ma qualcosa di diverso: prende un fallimento documentato e ne fornisce una spiegazione strutturata più una correzione testabile. Variante costruttiva dello stesso schema, da presentare come tale
- [ ] Ogni paper dichiara i propri limiti in una sezione dedicata — preparare la stessa fin da subito
- [ ] Verificare e dichiarare lo stato editoriale di ogni fonte usata
- [ ] 🟡 **Scrivere in parallelo, non alla fine**: introduzione e background non dipendono da alcun risultato e sono metà della tesi

---

## 8. Impianto inferenziale 🔴

> [!danger] Il problema n = 1
> Una traiettoria di bankroll è **una singola realizzazione**, autocorrelata e path-dependent. Le 380 partite di una stagione non sono 380 osservazioni indipendenti sul rendimento. Applicare R² e Cohen's d come se lo fossero è esattamente l'errore che il Paper 1 denuncia negli altri: sarebbe autolesionistico commetterlo in una tesi che si fonda su quel paper.

- [ ] Usare **tutti e 5 gli scenari** di KellyBench, più stagioni aggiuntive dal 2002–03
- [ ] **Molti seed** per configurazione (con Modulo 1 classico il costo è trascurabile)
- [ ] **Block bootstrap** sui residui per gli intervalli, non bootstrap iid
- [ ] Confronti **appaiati** tra agenti sulla stessa sequenza di eventi
- [ ] Riportare il **tasso di falsi allarmi** del Modulo 2 come metrica di prima classe, non nasconderlo
- [ ] Definire *a priori* metriche primarie (rovina, drawdown massimo, SD del log-wealth, tempo di recupero, crescita certo-equivalente) e secondarie
- [ ] 🔴 **Rimedio unificato all'autocorrelazione**: la calibrazione Monte Carlo della soglia via block bootstrap risolve lo stesso problema per ANOVA F, FWER dello Z-test, DiD e Breusch-Pagan. È un filo conduttore, non quattro rimedi separati

> [!tip] ⚙️ **Checkpoint C8** — block bootstrap e intervalli su tutti gli agenti. Vedi §12

---

## 9. Protocollo anti-overfitting 🔴

> [!important] Senza questo la tesi è indifendibile
> La regola di ricalibrazione ha parametri liberi: soglie, ampiezza finestra, forma funzionale di g. Tararli guardando i risultati produce overfitting travestito da framework.

- [ ] Calibrare i parametri **esclusivamente** sugli scenari di training (2000/01, 2010/11, 2020/21)
- [ ] **Congelare i parametri per iscritto e con data**, prima di eseguire qualunque run sul test set 2023/24
- [ ] Tenere un log delle configurazioni provate, incluse quelle scartate — la trasparenza sui gradi di libertà del ricercatore è essa stessa un contributo
- [ ] Validazione fuori campione su stagioni non usate né in calibrazione né in test

> [!danger] Lo split va congelato al checkpoint C3
> Prima di guardare qualsiasi risultato. Non dopo aver "dato un'occhiata" ai dati di test.

---

## 10. Domande aperte da portare al relatore 🔴

- [x] ✅ ~~Il paper Taylor et al. è reperibile?~~ → **sì, nel progetto. Primo autore Grady, non Taylor**
- [ ] **Riposizionamento**: d'accordo nell'abbandonare l'argomento dell'ingiustizia epistemica (falsificato dal paper) e riposizionare la tesi come *ablazione multi-agente che gli autori dichiarano di non aver eseguito*?
- [ ] **Obiettivo**: conferma che il target è il profilo di rischio e non "battere il mercato"?
- [ ] Il Modulo 1 deve essere un vero LLM o è accettabile un modello classico? Budget disponibile, dato che il paper riporta ≈ $2.000 per seed
- [ ] Ambiente: endpoint OpenReward o replica locale?
- [ ] Quanto della formalizzazione va ripreso quasi 1:1 dal paper CMES con citazione esplicita e quanto sviluppato come contributo originale?
- [ ] **Intervalli di confidenza**: impianto inferenziale completo o stime deterministiche?
- [ ] **Baseline D**: conferma che il confronto con i drift detector standard è imprescindibile?
- [ ] **Discrepanze §4.1**: come e quando presentarle
- [ ] **Risultati teorici propri**: $\lambda^* = 1/(1+\text{Var}(c))$, mappatura virtual/real drift, falsificabilità del floor, $\hat{g}$ come unico segnale ex-ante. Sono contributi originali o già noti in letteratura?
- [ ] Target di pubblicazione: taglio IA/agenti o metodologia statistica?

---

## 11. Checklist di readiness prima di iniziare a scrivere

- [ ] Ho letto integralmente KellyBench e verificato la scheda fattuale del piano
- [ ] So spiegare a voce, senza appunti, tutte le formule della §1 — inclusa la distinzione tra le due formule di R²
- [ ] So argomentare in trenta secondi perché nessuna regola di staking può creare edge, e cosa implica
- [ ] Ho ricalcolato tutte le tabelle numeriche dei tre paper (§4)
- [ ] Ho elencato per iscritto le assunzioni che si rompono nel trasferimento di dominio
- [ ] Ho un dataset/ambiente pronto e validato, con test anti-leakage automatico che passa
- [ ] Ho verificato l'edge reale del Modulo 1 contro la closing line, e so cosa dire se non ce n'è
- [ ] Ho una bozza scritta della tupla di stato adattata al dominio scommesse
- [ ] Ho la definizione operativa scritta dei due gruppi per la decomposizione OB in contesto sequenziale
- [ ] Ho congelato per iscritto i parametri del Modulo 3 prima di toccare il test set
- [ ] Ho discusso con il relatore tutti i punti della §10

---

## 12. ⚙️ Checkpoint di programmazione

> [!important]+ Il principio
> Non si scrive codice dopo ogni punto teorico, e non si studia per mesi senza scrivere niente. **Un checkpoint per grappolo di teoria.**
>
> Ogni checkpoint ha due proprietà:
> 1. **Verifica** un'affermazione teorica appena studiata, invece di applicarla genericamente. Se la teoria dice "qui lo schema si rompe", il codice deve *mostrarlo rompersi*.
> 2. **È cumulativo**: il codice di ogni checkpoint entra nel progetto finale. Non è esercizio usa-e-getta. Arrivato a C9 l'impianto è implementato, senza che ci sia mai stata una "fase implementazione" separata.
>
> Durata indicativa: mezza giornata l'uno, tranne C6 e C8 che sono più lunghi.

### C1 — Simulatore Kelly
**Dopo:** §1.1 ✅ (fattibile subito) · **Dati richiesti:** nessuno

- [ ] Simulare N scommesse ripetute con $p$ e $b$ noti, bankroll che compone
- [ ] Confrontare Full Kelly, mezzo, quarto: crescita mediana, drawdown massimo, dispersione finale
- [ ] **Verifica teorica**: la *mediana* del bankroll è massimizzata a $f^*$, la *media* no. Vederlo elimina per sempre la confusione tra le due
- [ ] Aggiungere un edge stimato con errore ($\hat{p} \neq p$) e osservare quanto degrada la crescita → prepara §2.3 e $\lambda^*$

### C2 — ANOVA a mano e dove si rompe
**Dopo:** §1.2 · **Dati richiesti:** nessuno

- [ ] Ricalcolare $SS_{between}$, $SS_{within}$, F sul toy dataset (A = {4, 7}, B = {2, 9, 3}) e confrontare con `scipy.stats.f_oneway`
- [ ] 🔴 **Il pezzo che conta**: generare 1000 serie autocorrelate *senza alcun effetto reale*, applicare la F, contare quante volte rigetta. Il tasso sarà ben sopra il 5%
- [ ] Ripetere con soglia calibrata via block bootstrap e verificare che torni al 5%
- [ ] Questo codice diventa il template del rimedio unificato di §8

### C3 — Primo contatto coi dati reali
**Dopo:** §2.1 + §2.2 · **Dati richiesti:** CSV `football-data.co.uk`

- [ ] Caricare le stagioni, ispezionare le colonne, contare le righe per stagione
- [ ] 🔴 **Verificare da quale stagione le colonne delle quote non sono vuote** — chiude il punto più fatale di §2.9 e §5.2
- [ ] Implementare tre metodi di de-vigging (proporzionale, additivo, power) e confrontare le $q$ risultanti sulle stesse partite
- [ ] Osservare dove i metodi divergono di più (sarà sugli outsider: è il favourite-longshot bias, visto invece che letto)
- [ ] 🔴 **Congelare lo split train/test per iscritto e con data** (§9), prima di guardare qualsiasi risultato
- [ ] Scrivere il test anti-leakage e farlo girare

### C4 — Elo e il go/no-go
**Dopo:** §2.8 (parte Elo) + §2.4 · **Dati richiesti:** C3 completato

- [ ] Implementare Elo con walk-forward: rating aggiornati solo con partite già giocate
- [ ] Mapping Elo → probabilità 1X2
- [ ] Calcolare log-loss del modello e log-loss del mercato de-viggato sulle stesse partite
- [ ] 🔴 **Calcolare $\hat{g} = \frac{1}{T}\sum_t [\ln p_t(x_t) - \ln q_t(x_t)]$** e guardarne il segno
- [ ] Reliability diagram: il modello è calibrato o solo ordinato bene?

> [!danger] Questo è il momento che determina cosa la tesi dimostra
> Se $\hat{g} < 0$ la tesi resta valida ma cambia interpretazione, e va detto in apertura. Saperlo presto significa scrivere l'introduzione una volta sola.

### C5 — Drift detector standard
**Dopo:** §1.9 + §1.4 · **Dati richiesti:** C4 completato

- [ ] Importare ADWIN e Page-Hinkley da `river` (non reimplementarli)
- [ ] Farli girare sulla serie dei residui del Modulo 1: quando scattano?
- [ ] Applicare lo Z-test giornata per giornata e contare i falsi allarmi su una stagione senza drift noto
- [ ] 🔴 Calibrare la soglia via Monte Carlo sotto H₀ e verificare che il tasso torni al nominale — è §1.4 vista funzionare
- [ ] **Nasce qui la Baseline D**

### C6 — Backtest appaiato e il test del floor
**Dopo:** §2.5 + §1.8 + §3.2 · **Dati richiesti:** C5 completato · *checkpoint lungo*

- [ ] Loop di backtest: stessa sequenza di partite per tutti gli agenti, solo la regola di staking cambia
- [ ] Baseline A (Full Kelly), B (frazionario fisso), E (puntata minima permanente)
- [ ] 🔴 **Qui serve l'OOP**: gli agenti condividono l'80% del comportamento e differiscono per la regola di staking. È il momento in cui una classe base risolve un problema reale — si impara facendo questo, non leggendo un capitolo
- [ ] Breusch-Pagan sui residui: l'eteroschedasticità è visibile?
- [ ] 🔴 **Test del floor**: stesso agente con floor e senza, confronto dei tassi di rovina. Verifica della predizione falsificabile di §2.9
- [ ] Registrare mediana, drawdown massimo, tempo di recupero, tasso di rovina

### C7 — Oaxaca-Blinder
**Dopo:** §1.5 + §2.7 · **Dati richiesti:** C6 completato · **è il contributo, si scrive a mano**

- [ ] 🔴 **Prima sui dati sintetici**: generare due gruppi con differenza di composizione *nota* e differenza strutturale *nota*, e verificare che l'implementazione recuperi entrambe. Se non le recupera lì, non ci si può fidare sui dati reali
- [ ] Poi guardare le distribuzioni reali delle covariate proposte (fascia di quota, casa/trasferta, differenziale Elo, flag neopromossa, giornata): quante partite per cella? Il flag neopromossa ha abbastanza casi?
- [ ] Scrivere la definizione operativa dei due gruppi *dopo* aver visto le distribuzioni, non prima
- [ ] Implementare la decomposizione (~50 righe), verificare che le componenti sommino alla differenza totale
- [ ] Testare l'indeterminatezza: cambiare gruppo di riferimento e osservare quanto cambiano le componenti
- [ ] **Nasce qui il Modulo 2**

### C8 — Impianto inferenziale
**Dopo:** §8 · **Dati richiesti:** C7 completato · *checkpoint lungo*

- [ ] Modulo 3 con $\lambda^* = 1/(1+\text{Var}(c))$ → **Agente C completo**
- [ ] 🔴 Calibrazione dei parametri **solo** sugli scenari di training, poi congelamento per iscritto, *poi* il test set
- [ ] Block bootstrap (moving block / stationary) sui residui, intervalli di confidenza per tutte le metriche
- [ ] Molti seed, tutti e 5 gli scenari, confronto appaiato C vs D vs E
- [ ] Tasso di falsi allarmi del Modulo 2 riportato come metrica di prima classe
- [ ] Ablazione interna: supervisore spento, supervisore che rileva ma non gradua

### C9 — Secondo Modulo 1 e robustezza
**Dopo:** §2.8 (parte Dixon-Coles) · **Dati richiesti:** C8 completato

- [ ] Implementare Dixon-Coles con correzione $\tau$ e pesatura temporale
- [ ] Rieseguire l'intero impianto col nuovo Modulo 1
- [ ] 🔴 Il ranking tra regole di staking si conserva? Se sì, il contributo è robusto al modello sottostante
- [ ] Analisi di sensibilità del de-vigging (§2.2): rerun con i tre metodi
- [ ] 🟡 Autovalutazione dell'Agente C sulla rubrica a 44 punti (§3.5)

---

### Riepilogo checkpoint

| ⚙️     | Dopo quale teoria | Cosa verifica                       | Cosa produce                   |
| ------ | ----------------- | ----------------------------------- | ------------------------------ |
| **C1** | §1.1              | Mediana ≠ media sotto compounding   | Simulatore Kelly               |
| **C2** | §1.2              | L'autocorrelazione gonfia la F      | Template calibrazione MC       |
| **C3** | §2.1, §2.2        | Divergenza tra metodi di de-vigging | Dati caricati, split congelato |
| **C4** | §2.4, §2.8        | Il modello batte la closing line?   | Modulo 1 + $\hat{g}$           |
| **C5** | §1.9, §1.4        | Falsi allarmi su test ripetuti      | Baseline D                     |
| **C6** | §2.5, §1.8, §3.2  | Il floor rende possibile la rovina  | Backtest + baseline A/B/E      |
| **C7** | §1.5, §2.7        | OB recupera componenti note         | **Modulo 2**                   |
| **C8** | §8                | Gli intervalli reggono?             | **Modulo 3** + Agente C        |
| **C9** | §2.8              | Il ranking è robusto al Modulo 1    | Confronto Elo vs DC            |

> [!danger] I tre punti critici in qualunque ordinamento
> 1. **C4 / §2.4** — il test su $\hat{g}$ determina l'interpretazione di tutto il resto
> 2. **C3 / §2.9** — floor e disponibilità quote, prima di scrivere il backtest, non dopo
> 3. **§3.4** — modi di fallimento, perché sono l'oggetto che la tesi dichiara di spiegare

---

## Collegamenti

- [[§1.1 Criterio di Kelly]] · [[§1.2 ANOVA]] · [[§1.3 Effect size]] · [[§1.5 Oaxaca-Blinder]]
- [[§1.9 Concept drift detection]] · [[§2.2 Formula lambda ottimale]] · [[§8 Impianto inferenziale]]
- [[Piano tesi Structural Hybrid Kelly v2]]
