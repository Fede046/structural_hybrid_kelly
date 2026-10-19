# Analisi conclusiva del progetto Structural-Hybrid Kelly

Stato al 2026-10-19, dopo i task T1–T66 di `.agent/BACKLOG.md`. Confronta quanto è stato fatto con la proposta del relatore (`docs/dialogo_Tesi.md`) e con la checklist `docs/note/todo_prerequisiti_tesi_v4.md`. I numeri citati vengono da `thesis/numeri.md` (con la loro provenienza) o, dove indicato, dai report dei task in `.agent/report/`.

## 1. In sintesi: il progetto è finito?

**La parte di codice e di sperimentazione è finita.**
- I nove checkpoint di programmazione del TODO (C1–C9, §12) sono implementati e testati.
- Le 12 story del backlog sono eseguite: Elo e Dixon-Coles come Modulo 1, Modulo 2, Modulo 3, agenti A–E, backtest appaiato, intervalli, test set 2023-24 eseguito una sola volta, robustezza.
- Riproducibilità: README, manifesti SHA256, esecutore unico.
- Materiale per la tesi: 15 tabelle LaTeX, 10 figure PDF, 129 numeri citabili e il documento dei metodi `thesis/metodi_implementati.md`.
- Suite veloce: 780 test passati.

**La tesi invece non è finita.** Mancano quasi tutta la parte di studio e di scrittura del TODO e alcune decisioni da prendere col relatore. Ci sono anche pochi residui tecnici. Il dettaglio è nella § 6.

**Il messaggio più importante per la stesura.** I risultati non confermano la versione forte della proposta del dialogo ("un agente con ANOVA e Oaxaca in the loop … batte il mercato"):
- il Modulo 1 non batte il mercato (ĝ < 0 ovunque);
- l'eteroschedasticità "che esplode" non si osserva, con soglie corrette;
- l'agente C non batte la puntata minima (E) né il detector Page-Hinkley (D_PH).

Confermano invece una versione più modesta e difendibile, centrata sul profilo di rischio e non sul battere il mercato. È la riformulazione già prevista dal TODO (§10, "Obiettivo"). Va discussa col relatore prima di scrivere introduzione e conclusioni.

## 2. Che cosa si voleva dimostrare

Dal dialogo col relatore, il sistema "Structural-Hybrid" è gerarchico:
1. Modulo 1 (lavoratore): prevede.
2. Modulo 2 (supervisore): monitora i residui con l'ANOVA; se l'eteroschedasticità aumenta, dà l'allarme.
3. Modulo 3 (ricalibratore): con Oaxaca-Blinder separa l'errore compositivo, cioè del dato, da quello strutturale, cioè del regime, e riduce lo stake di conseguenza: poco nel primo caso, fino a zero nel secondo.

Il TODO v4 riposiziona la tesi in tre modi:
- **Obiettivo.** Il profilo di rischio, non il battere il mercato.
- **Contributo.** L'ablazione dello scaffold multi-agente che gli autori di KellyBench dichiarano di non aver eseguito.
- **Due soglie di valore**, entrambe con baseline obbligatorie:
  - "se C non batte D (drift detector standard), il contributo originale non esiste";
  - "se C non batte E (puntata minima), il framework non serve".

## 3. Cosa è stato fatto, checkpoint per checkpoint

| Checkpoint del TODO | Story e task | Stato | Dove |
|---|---|---|---|
| C1 Simulatore Kelly | S1, T1–T7 | fatto | `src/shk/kelly/` |
| C2 ANOVA a mano e falso rigetto | S2, T8–T13; T40 | fatto; T12 resta "da rivedere" (§ 6) | `src/shk/stats/` |
| C3 Dati reali, de-vigging, split, anti-leakage | S3, T14–T19; T41, T43 | fatto | `src/shk/data/`, `src/shk/market/` |
| C4 Elo e go/no-go su ĝ | S4, T20–T25; T57 | fatto | `src/shk/model/elo*.py`, `scoring.py`, `g_hat_inference.py` |
| C5 Drift detector, Z-test, Baseline D | S5, T26–T32; T50 | fatto | `src/shk/stats/drift.py`, `model/monitoring.py`, `stateful_agents.py` |
| C6 Backtest appaiato, floor, eteroschedasticità | S6, T33–T39; T44 | fatto | `src/shk/kelly/agents.py`, `environment.py`, `floor.py` |
| C7 Oaxaca-Blinder e Modulo 2 | S8, T45–T49 | fatto | `src/shk/stats/oaxaca.py`, `model/module2*.py` |
| C8 Modulo 3, agente C, calibrazione, congelamento, intervalli, test set | S9–S10, T50–T58 | fatto | `model/module3.py`, `agent_c.py`, `training_calibration.py`, `comparisons.py`, `test_run.py` |
| C9 Dixon-Coles e robustezza | S11, T59–T63 | fatto (senza la rubrica a 44 punti) | `model/dixon_coles*.py`, `robustness.py`, `devig_sensitivity.py` |
| Riproducibilità e materiale per la tesi | S12, T64–T66 | fatto (report T66 da completare) | `README.md`, `scripts/reproduce_all.py`, `thesis/` |

## 4. Risultati principali

### 4.1 Il go/no-go: il Modulo 1 non batte il mercato
- ĝ = media di ln p̂(x) − ln q(x) è negativo in tutte le configurazioni.
- Con B365 e Shin vale −0.0222, IC 95% [−0.0298, −0.0147]; con Pinnacle chiusura −0.0316, IC [−0.0436, −0.0196].
- Il segno è lo stesso con i cinque metodi di de-vigging e anche sul 2023-24 (B365 Shin −0.0427).
- Con Dixon-Coles la log-loss migliora (0.9709 contro 0.9795 in validazione) ma ĝ resta negativo (−0.0136).

Conseguenza, già prevista dal TODO §1.1: nessuna regola di staking crea edge. Tutti gli agenti che puntano perdono in valore atteso. La tesi va aperta con questo fatto (decisione S4).

### 4.2 Autocorrelazione: perché l'ANOVA nominale non si può usare
- Su serie AR(1) senza differenze fra i gruppi, la F nominale (due metà) rigetta il 3.7% a φ = 0, ma il 14.9%, 25.3% e 39.9% a φ = 0.3, 0.5, 0.7.
- Con 38 blocchi rigetta l'84.3% già a φ = 0.3.
- La soglia calibrata col block bootstrap della serie centrata riporta il tasso nell'intervallo Monte Carlo [0.0322, 0.0678] con L = 7 (0.039) e L = 20 (0.056), ma non con L = 40 (0.081).

È il "rimedio unificato" del TODO §8, applicato anche a Z-test, Breusch-Pagan e soglia di C1. Il limite con L = 40 va dichiarato.

### 4.3 Drift detector: perché ANOVA/Z e non ADWIN
Sulle 19 stagioni di validazione, con la log-loss del Modulo 1, attesi 1.9 allarmi per stagione:

| Metodo | Allarmi |
|---|---|
| ADWIN | 0 |
| Page-Hinkley | 20 |
| Z per matchday, soglia nominale | 53 |
| Z calibrato, L = 20 e L = 40 | 43 |

ADWIN, tarato sul training, non scatta mai. Detector e Z dicono solo *quando*; per *quanto* e *di che tipo* serve la decomposizione.

### 4.4 Eteroschedasticità: il segnale del dialogo non si osserva
- Breusch-Pagan congiunto e White con soglia χ² nominale rigettano in 19 stagioni su 19. È un effetto per costruzione: la varianza della log-loss dipende dall'entropia della previsione (varentropia).
- Con soglie calibrate i rigetti scendono a 0–1. Breusch-Pagan temporale dà 2 rigetti su 19, e così Goldfeld-Quandt, ARCH-LM e log-varianza mobile (T44): non c'è evidenza di varianza che cresce nella stagione.

L'allarme "l'eteroschedasticità aumenta" previsto nel dialogo non si osserva, una volta corretta la soglia. Per questo l'allarme dell'agente C è la componente strutturale di Oaxaca-Blinder (T = −S), non un test di eteroschedasticità.

### 4.5 Floor: la predizione falsificabile del TODO §2.9 è confermata
- Senza floor la rovina è esattamente 0, sul calendario sintetico e su quello reale.
- Col floor diventa positiva: Kelly pieno (A) 17.9% con £0.01 e 69.0% con £1; quarto-Kelly 0.49% con £1.
- Sul calendario sintetico la transizione cade fra B0/F = 31.6 (rovina 59.6% a 1000 date) e 100 (3.3%).
- Il tempo di rovina simulato è 13.3 volte più breve del limite teorico, non 23 come nella nota 2.9.

### 4.6 Modulo 2: Oaxaca-Blinder distingue poco i due tipi di drift
- Su dati sintetici con verità nota la decomposizione recupera le componenti (T45).
- Sui dati reali, nello scenario "strutturale atteso" (sospensione del 2019-20) la componente strutturale vale −0.0004 e la quota strutturale π 0.014. La componente compositiva vale 0.0116, l'interazione −0.0163; tutti gli intervalli comprendono 0.
- Alle transizioni fra stagioni la quota compositiva non domina (T48).
- Il DiD delle neopromosse è −0.0187, IC [−0.0397, 0.0025].

È il punto che il backlog indica come "risultato centrale, da indagare e non aggirare" (US-C7.3).

### 4.7 Confronti fra agenti

| Differenza (validazione, £0.01) | Stima e IC 95% | Lettura |
|---|---|---|
| C2 − D_ADWIN | +0.321 [0.187; 0.455] | C2 meglio di D_ADWIN, che con ADWIN muto coincide col quarto-Kelly |
| C2 − D_PH | −0.070 [−0.094; −0.045] | **C2 peggio di D_PH** |
| C2 − E | −0.243 [−0.342; −0.144] | **C2 peggio della puntata minima** |
| C1 − C0 ("rilevare") | +0.298 [0.189; 0.407] | il guadagno viene quasi tutto dal rilevare |
| C2 − C1 ("graduare") | +0.023 [−0.005; 0.051] | graduare non è significativo in validazione |

- **Validazione.** Valori pooled sulle 19 stagioni, intervallo bootstrap a due livelli con correzione t per cluster.
- **Test 2023-24.** Una stagione, intervallo dai soli seed: gli stessi segni, con graduare +0.120 [0.100; 0.139].
- **Le due soglie del TODO.**
  - C batte la Baseline D con ADWIN (che non dà allarmi) ma non quella con Page-Hinkley.
  - C non batte E.
  - Il framework riduce le perdite rispetto al Kelly frazionario fisso (C0 = B_0.25), ma non rispetto al non puntare quasi niente.

Questo è coerente con ĝ < 0: se l'edge è negativo, la politica migliore è puntare il meno possibile.

### 4.8 Robustezza
- **Modulo 1.** Il ranking degli agenti è stabile fra Elo e Dixon-Coles: τ_b di Kendall 0.857 in validazione e 0.762 sul test, con £0.01. Le conclusioni dei confronti restano le stesse in 138 confronti su 160 in validazione e 140 su 160 sul test (report T62).
- **De-vigging.** Le conclusioni hanno lo stesso segno con tutti e cinque i metodi in 260 casi su 262; i due che cambiano sono a £1 e su metriche secondarie (T63).

## 5. Scelte di implementazione

Le formule, i parametri e le date delle decisioni sono in `thesis/metodi_implementati.md`. Qui ci sono le scelte che cambiano l'interpretazione, con il motivo.

**Dati e ambiente**
1. **Replica locale** su football-data.co.uk (E0, dal 1993-94 al 2023-24), non l'endpoint OpenReward. Motivo: controllo completo su seed e scenari.
   - Lo split è congelato (commit `90a77a1`): training 2000-01, 2010-11, 2020-21; 19 stagioni di validazione; test 2023-24.
   - Al posto dei 5 scenari di KellyBench: 3 di training, 19 di validazione e 1 di test. La variante "literature" del 2023-24 non è ricostruibile.
2. **q dalla terna B365 pre-partita**, de-viggata con Shin come metodo principale; il proporzionale è il controllo e i cinque metodi entrano nella sensibilità. Nel 2000-01, senza B365, il Modulo 2 usa la terna con overround più vicino (SB).
3. **Anti-leakage per costruzione**: la storia ha solo Date strettamente anteriore e la partita espone solo la whitelist dei campi pre-partita. Test automatico, anche sul 2023-24 (0 violazioni).
4. **Ambiente**:
   - B0 = £220, floor F = 0, £0.01 (principale, B0/F = 22 000) e £1;
   - una puntata obbligatoria per data, sul ripiego a EV stimato massimo;
   - con più puntate in una data, si piazzano in ordine di EV finché la somma non supera la ricchezza;
   - rovina assorbente se W < F.

**Modulo 1**

5. **Elo-Davidson raw**, senza ricalibrazione: era migliore di Platt e dell'isotonica in validazione. La scala è s = 400; la tabella della nota 2.8 usa 200.
   - Neopromosse mai viste: media dei rating delle ultime tre della stagione precedente.
   - Calibrazione espansiva di K, h, ν sul solo training.
6. **Dixon-Coles come secondo Modulo 1**: τ, pesatura temporale ξ e prior gaussiano σ sulle neopromosse. σ = ∞ è esclusa perché per una squadra senza storia lo stimatore non esiste.

**Modulo 2**

7. **Risposta** δ = ln p̂(x) − ln q(x), con la stessa forma di ĝ, non la log-loss.
8. **Covariate** pre-partita: log-rapporto delle quote, entropia del mercato, flag neopromossa, posizione nella stagione, entropia del modello. L'Elo è stato tolto dalla regola sul VIF.
9. **Gruppi**: due finestre scorrevoli adiacenti di W partite anteriori alla data, A (vecchia) e B (recente). È la "definizione operativa dei due gruppi" del TODO §1.5, da portare al relatore.
10. **Decomposizione** three-fold; quota strutturale π = |S|/(|C| + |S| + |I|), come nella nota 1.5.

**Modulo 3**

11. **λ\* con il troncamento a zero**, λ* = E[c]/E[c²]. Non è la formula del TODO λ* = 1/(1 + Var(c)), che vale solo senza troncamento.
    - σ² si stima dalla dispersione di δ, gonfiata dalla componente strutturale negativa (candidata P3, scelta su verità sintetica in T51).
    - λ = 0 se ĝ della finestra è ≤ 0; λ = 0.25 se il Modulo 2 non è attivo.

**Agenti e baseline**

12. **Una sola puntata per partita**, sull'esito a EV stimato massimo: non è il Kelly multi-esito né l'ottimizzazione congiunta delle puntate simultanee del TODO §2.5–2.6. Il supervisore cambia solo le frazioni, mai le previsioni.
13. **Agente C in tre bracci di ablazione**:
    - C1: allarme binario T = −S > soglia, λ = 0.25·κ^accensioni;
    - C2_global: λ graduata dal Modulo 3;
    - C2: come C2_global, più l'astensione sulle partite fuori supporto, cioè con meno di 5 partite simili nella finestra A.
14. **Baseline D** con ADWIN e Page-Hinkley di river, alimentati con δ, con κ e parametri ricalibrati con lo stesso obiettivo di C.

**Inferenza e protocollo**

15. **Seed** = stagione ricostruita per stationary bootstrap delle date, con lunghezza dei blocchi di Politis-White; 500 seed per stagione dall'analisi di potenza.
16. **Intervalli**: bootstrap a due livelli (stagioni come cluster, seed dentro), con la correzione t per i pochi cluster; sul test, una stagione, intervallo dai soli seed.
17. **Anti-overfitting**:
    - calibrazione sul solo training con un obiettivo unico: log-ricchezza finale media a £0.01;
    - parametri congelati in `config/frozen_params.toml` e committati (`9f30b30`) prima di sbloccare il test (`a5abca4`);
    - lo stesso con Dixon-Coles (`b4c4e8a`);
    - il 2023-24 è stato eseguito una sola volta.

## 6. Cosa manca

### 6.1 Residui tecnici nel repository (piccoli)
- **Commit**: le uscite di T62–T66 non sono ancora committate (codice, CSV, figure, manifesti, `thesis/`). Alcune fonti delle tabelle (us_c8_5_test_run_dc, us_c9_2_robustness, us_c9_3_devig_sensitivity) sono nel manifesto ma non in git.
- **Report di T66** da completare (`.agent/report/T66.md`): il documento e il test sono fatti e verdi.
- **T12 "da rivedere"** e un test slow noto rosso: la calibrazione centrata con L = 40 resta fuori dall'intervallo (0.081). È un risultato da dichiarare, non un bug.
- **T25**: manca la verifica della CI su GitHub.
- **Manutenzione**:
  - `uv.lock` da rigenerare (pandas, river, statsmodels, arch);
  - tag del commit dello split `2cea094` da pubblicare su origin (il backlog lo segnalava come urgente prima del 2026-10-29);
  - licenza di football-data.co.uk da controllare prima di citarla o versionare i CSV.

### 6.2 Fuori scope per decisione (nel TODO, non implementati)
- Baseline F (Kelly bayesiano o robusto), TODO §2.3 e §5.3 (🟡).
- RIF regression, TODO §1.7: in attesa della risposta del relatore.
- Bradley-Terry e modelli score-driven o state-space come Modulo 1.
- DDM, EDDM e CUSUM: solo ADWIN e Page-Hinkley sono implementati.
- Kelly multi-esito e puntate simultanee ottimizzate insieme (§ 5, punto 12).
- Over/under e handicap asiatico; xG, infortuni e formazioni (non disponibili storicamente).
- Endpoint OpenReward e worker LLM (vincolo di budget).
- Controllo analitico delle frequenze di drawdown α^(2/λ−1) (US-C1.4 eventuale).

### 6.3 Non codice: studio, relatore e scrittura (la parte più grande)

**Da fare subito (TODO §0)**
- Leggere per intero KellyBench, verificare riga per riga la scheda fattuale e lo stato editoriale.
- Chiarire il valore reale del floor e di B0, £0.01 o £1: le conclusioni di C6.3 ne dipendono.

**Paper del relatore (TODO §4)**
- Ricalcolare le tabelle dei tre paper e portargli le discrepanze di §4.1.

**Domande al relatore (TODO §10), con i risultati della § 4**
- La riformulazione dell'obiettivo: profilo di rischio, non battere il mercato.
- Come presentare che l'eteroschedasticità non dà il segnale atteso e che C non batte E e D_PH.
- Implementare o no la RIF regression.
- La definizione operativa dei gruppi OB (US-C7.2) e la mappatura componente strutturale → Var(c) → λ* (T51), da mandargli.

**Discussione (TODO §3.4–3.5)**
- La tabella "modo di fallimento di KellyBench → meccanismo": il framework lo previene, lo attenua o non lo tocca.
- L'autovalutazione dell'agente C sulla rubrica a 44 punti.

**Letteratura (TODO §6)**
- Fonti originali e bibliografia verificata.

**Scrittura (TODO §7)**
- I capitoli della tesi, con la sezione dei limiti dall'inizio.
- In apertura: ĝ < 0 e "nessuna regola di staking crea edge".

**Orale e Definition of Done**
- Risposte pronte: "perché Shin?", "perché ANOVA e non ADWIN?", le due formule di R², "perché una classe base?".
- Il paragrafo della nota 1.5 §9.6.
- Le Definition of Done rimaste: per US-C1.2, un caso in cui λ* batte il quarto-Kelly e uno in cui no.
- La checklist di readiness del TODO §11.

### 6.4 Note da correggere segnalate dal lavoro
- Nota 2.8 §3.3: la tabella di Davidson è con scala 200; il modello usa 400.
- Nota 2.9 §6.2: l'accelerazione è circa 13× (tempo medio), non 23×; 1 427 è il tempo mediano.
- TODO §1.8: "HAC non corregge anova_lm" vale solo con typ=1 (T38).
- Enunciato di US-C3.2: la divergenza fra metodi è massima sul favorito in punti percentuali e sull'outsider in termini relativi.

## 7. Dove trovare cosa

| Cosa | Dove |
|---|---|
| Formule, parametri, seed, esclusioni | `thesis/metodi_implementati.md` |
| Numeri citabili con provenienza | `thesis/numeri.md` |
| Tabelle LaTeX e CSV | `thesis/tables/` (`scripts/build_thesis_tables.py`) |
| Figure finali | `thesis/figures/tesi_*.pdf` (`scripts/build_thesis_figures.py`) |
| Riproduzione dei risultati | `README.md`, `scripts/reproduce_all.py`, `results/MANIFEST.sha256` |
| Decisioni e report dei task | `.agent/BACKLOG.md`, `.agent/report/T<N>.md` |
