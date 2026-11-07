# Disegno: una popolazione di strategie che evolve (dinamica evolutiva)

Stato (6 novembre 2026): implementata ed eseguita con le tre scelte proposte nel §7; i risultati sono nel §8. Codice in `src/shk/model/population.py` (dinamica) e `src/shk/model/population_run.py` (strategie), esperimento in `scripts/us_c21_population.py`, figura in `scripts/us_c21_population_figure.py`, test in `tests/test_population.py` e `tests/test_us_c21_acceptance.py`. Nasce dalla risposta del relatore: il lavoro va nella direzione giusta; vuole ancora qualche tentativo, a scelta dello studente, basato sulla dinamica evolutiva; poi si passa alla scrittura. Fra le letture possibili è stata scelta quella della popolazione di strategie che si contendono il capitale.

## 1. L'idea

Oggi ogni agente gioca da solo: il quarto di Kelly, lo schema nelle sue versioni, le tre regole di scelta dell'esito. Qui le stesse strategie giocano **insieme**, ciascuna con una quota del capitale. Dopo ogni giornata la quota di ogni strategia cresce o cala secondo quanto ha reso: la selezione naturale applicata al capitale (dinamica del replicatore). Una piccola **mutazione** ridistribuisce ogni giorno una parte del capitale fra tutte le strategie, così nessuna si estingue e una strategia può tornare a crescere quando le condizioni cambiano.

Il legame con Kelly è diretto. Nella *evolutionary finance* la ricchezza di chi punta con frazioni del proprio capitale evolve proprio con la dinamica del replicatore, e la regola di Kelly è quella che sopravvive alla selezione di mercato (Blume ed Easley 1992; Lensberg e Schenk-Hoppé 2007, che la fanno emergere con un approccio darwiniano; Evstigneev, Hens e Schenk-Hoppé per la rassegna). I riferimenti vanno verificati prima di citarli nella tesi.

La domanda di ricerca è un confronto fra due modi di accorgersi che il modello invecchia:
- lo **schema del relatore** guarda gli errori del modello rispetto al mercato (ANOVA, Brown-Forsythe, Oaxaca), cioè un segnale prima del risultato economico;
- la **popolazione** guarda solo i guadagni realizzati, molto più rumorosi, e sposta il capitale verso chi rende di più.

## 2. Perché si può fare senza toccare l'ambiente

Senza puntata minima (configurazione «nessun floor») ogni puntata è una frazione del capitale corrente, e lo schema decide in base a δ, che non dipende dal capitale. Quindi il rendimento giornaliero R_i(d) = W_i(d+1) / W_i(d) di ogni strategia non dipende da quanto capitale le è affidato. Ne segue che la popolazione si calcola **esattamente** dai percorsi del capitale delle singole strategie:

W_pop(d+1) = W_pop(d) · Σ_i s_i(d) · R_i(d)

dove s_i(d) è la quota della strategia i alla giornata d. `run_paired_backtest` restituisce già la ricchezza giornata per giornata (`AgentRun.wealth`, forma (M, D+1)); oggi gli script ne salvano solo le metriche finali, quindi le strategie vanno rieseguite salvando i percorsi.

Con la puntata minima obbligatoria di KellyBench questo non vale più (la puntata minima pesa di più su una strategia con poco capitale): la popolazione si studia solo senza floor, e va dichiarato.

## 3. La regola evolutiva

Replicatore con mutazione, in tempo discreto, una giornata per passo:

s_i(d+1) = (1 − μ) · s_i(d) · R_i(d) / Σ_j s_j(d) · R_j(d) + μ / N

- **μ = 0**: selezione pura. Equivale a dividere il capitale all'inizio e non ribilanciare mai; è il riferimento.
- **μ > 0**: mutazione. Ogni giorno una frazione μ del capitale è ridistribuita in parti uguali; una strategia sfavorita non scende mai sotto μ/N.
- Quote iniziali uguali (1/N).

Un solo parametro libero, μ. Lo si sceglie **solo sulle stagioni di training** (2000-01, 2010-11, 2020-21), su una griglia fissata prima, per esempio {0; 0,001; 0,005; 0,01; 0,02; 0,05}, massimizzando la media del logaritmo del capitale finale. Nelle stagioni di valutazione si riportano anche gli altri valori, come analisi di sensibilità, senza sceglierli lì.

**Generazioni fra stagioni** (variante). Ogni stagione è una generazione: il capitale riparte da 100 come sempre, ma le quote iniziali della stagione k+1 sono quelle finali della stagione k (mescolate con μ). La popolazione «ricorda» quali strategie hanno funzionato. Usa solo informazione passata, quindi non viola la separazione dei dati. Le stagioni di training e il 2001-02 restano fuori dalla catena: la quota passa direttamente da una stagione di valutazione alla successiva.

## 4. La popolazione

Strategie già esistenti, tutte con il modello Elo, così si confrontano a parità di previsioni:

| Strategia | Da dove viene |
| --- | --- |
| Kelly pieno, valore atteso più alto | agente A |
| Quarto di Kelly, con ciascuna delle tre regole di scelta dell'esito | B_0.25 e lavoratori R1, R2, R3 |
| Schema, 40 partite precedenti, riprende quando l'allarme si spegne, regole R1 e R3 | C3 |
| Schema, 40 partite precedenti, fermo fino a fine stagione, regola R1 | C3_stop |
| Schema, stagione di calibrazione, riprende e fermo, regole R1 e R3 | C3_ref, C3_ref_stop |

Circa 11 strategie. Due varianti, da decidere:
- **con la «cassa»**, cioè una strategia che non punta mai. È la scelta standard in evolutionary finance; con un vantaggio negativo la selezione porterà il capitale verso di lei, e questo va mostrato perché conferma il risultato del paper. Proposta: popolazione principale senza cassa (si deve scommettere, come in KellyBench), cassa come variante;
- **con Dixon-Coles**: aggiunge strategie con previsioni diverse, quindi più varietà per la selezione. Richiede di eseguirle a parte e combinarle dopo, con gli stessi esiti e gli stessi ricampionamenti; è corretto per la proprietà del §2. Proposta: rimandare, come estensione.

## 5. Valutazione

Stesso protocollo di oggi: 19 stagioni vere di valutazione come risultato principale, 500 stagioni ricostruite come misura dell'incertezza, con gli stessi seed degli esperimenti precedenti; il 2023-24 una volta sola alla fine, come prova esplorativa.

Per ogni versione della popolazione (μ scelto sul training, con e senza generazioni):
- capitale rimasto in una stagione tipica (media geometrica sulle 19 stagioni), come nelle tabelle attuali;
- stagioni meglio / peggio del quarto di Kelly e della migliore strategia singola, quella dello schema fermo fino a fine stagione;
- come si spostano le quote: quali strategie prendono il capitale, in quanto tempo, e se con il modello vecchio (2016-20) il capitale va verso le versioni dello schema prima di quanto faccia l'allarme.

Grafici previsti, con la spiegazione per il relatore:
1. le quote delle strategie lungo una stagione tipica (aree sovrapposte);
2. con le generazioni, le quote a inizio stagione dal 2002-03 al 2022-23;
3. capitale per stagione, popolazione contro quarto di Kelly e schema, come la figura 2 attuale.

**Controllo di correttezza.** Con tutta la quota su una sola strategia e μ = 0 la popolazione deve restituire esattamente il capitale di quella strategia già pubblicato nei CSV esistenti; con gli stessi seed le strategie rieseguite devono coincidere con i risultati attuali.

**Che cosa ci si aspetta, onestamente.** Poiché ogni strategia perde in media contro il mercato, la selezione premierà quella che perde meno, probabilmente una versione ferma fino a fine stagione. Se la popolazione batte il quarto di Kelly ma non la migliore strategia singola, il risultato è comunque utile: la popolazione arriva vicino alla migliore **senza sapere in anticipo** quale sia, mentre la migliore strategia singola è scelta dopo aver visto i risultati.

## 6. Interventi sul codice

1. `src/shk/model/population.py`: funzioni pure che, dati i rendimenti giornalieri (strategie × giornate), calcolano quote e capitale della popolazione, con μ e con o senza generazioni. Test unitari: conservazione delle quote (somma 1), caso μ = 0 uguale al buy-and-hold, caso a una sola strategia, quota minima μ/N.
2. `src/shk/model/population_run.py`: per ogni stagione esegue le strategie del §4 in un unico backtest appaiato senza floor e restituisce i percorsi del capitale (stagione vera e 500 ricostruite).
3. `scripts/us_c21_population.py`: scelta di μ sul training, valutazione, CSV in `results/` e figure in `thesis/figures/`.
4. Aggiornamento di `results/MANIFEST.sha256`, di `thesis/numeri.md` e di una sezione nel documento per il relatore.

Nessuna modifica all'ambiente, agli agenti esistenti o ai parametri congelati.

## 7. Decisioni da prendere prima di iniziare

1. Popolazione principale senza cassa, cassa come variante? (proposta: sì)
2. Le generazioni fra stagioni come versione principale o come variante? (proposta: variante; la principale riparte ogni stagione da quote uguali, come gli altri agenti)
3. Dixon-Coles subito o dopo? (proposta: dopo)

Scelte adottate: popolazione principale senza cassa e cassa come variante; generazioni come variante; Dixon-Coles rimandato.

## 8. Risultati (500 seed, modello Elo, senza puntata minima)

**μ scelto sul training: 0, in tutte le versioni.** L'obiettivo sul training scende in modo monotono con μ, da −0,083 (μ = 0) a −0,123 (μ = 0,1) senza cassa (`results/us_c21_population_mu.csv`). La mutazione continua a restituire capitale anche alle strategie che perdono molto, in primo luogo al Kelly pieno, e con un vantaggio negativo questo costa. Con μ = 0, dentro una stagione la popolazione equivale a dividere il capitale in parti uguali all'inizio senza ribilanciare: il capitale finale è la media di quelli delle strategie (verificato nei test).

Capitale rimasto in una stagione tipica (media geometrica sulle 19 stagioni vere; fra parentesi le stagioni ricostruite, mediana sulle 500 e poi media geometrica) e stagioni meglio / peggio:

| Versione | Capitale rimasto | Ricostruite | Contro il quarto di Kelly | Contro la migliore strategia singola |
| --- | --- | --- | --- | --- |
| Quarto di Kelly, da solo | 57% | 56% | – | – |
| Migliore strategia singola, scelta dopo (esito più probabile, stagione di calibrazione, fermo) | 77% | 87% | 15 / 4 | – |
| Popolazione, quote uguali a inizio stagione | 62% | 64% | 10 / 9 | 3 / 16 |
| Come sopra, con la cassa | 66% | 68% | 12 / 7 | 3 / 16 |
| Popolazione con le generazioni | 70% | 77% | 13 / 6 | 4 / 15 |
| Popolazione con le generazioni e la cassa | 88% | 89% | 15 / 4 | 14 / 5 |

Che cosa si vede:
- **Dentro una stagione la selezione è troppo lenta.** In circa 100 giornate i rendimenti delle strategie si separano poco: la popolazione resta vicina alla media delle strategie (62%) e batte il quarto di Kelly in 10 stagioni su 19, quasi come per caso.
- **Fra una stagione e l'altra la selezione funziona.** Con le generazioni il capitale si sposta verso le versioni dello schema che si fermano fino a fine stagione: a fine 2022-23 il 54% è sullo schema con confronto con la stagione di calibrazione, regola dell'esito più probabile, fermo fino a fine stagione, cioè proprio la strategia che a posteriori è la migliore. La popolazione conserva il 70%, quanto le singole versioni dello schema ferme fino a fine stagione con la regola del valore atteso (71%), senza sapere in anticipo quale strategia sarebbe stata la migliore. Il Kelly pieno si estingue in due stagioni.
- **Con la cassa la selezione smette di scommettere.** Con le generazioni la quota della cassa sale dall'8% al 99% a fine 2022-23, e il capitale tipico arriva all'88%. È la conferma, per via evolutiva, del risultato di KellyBench: con un vantaggio negativo la strategia che sopravvive è non puntare.
- **Popolazione e schema rispondono alla stessa domanda in modo diverso.** Lo schema si accorge che il modello invecchia guardando gli errori rispetto al mercato; la popolazione lo scopre solo dai guadagni, e le servono alcune stagioni. Dal 2011-12 in poi, con il modello calibrato sul 2010-11 che invecchia, la popolazione con le generazioni conserva il 65%, contro il 52% del quarto di Kelly e il 69% della migliore strategia singola.

Figura: `thesis/figures/us_c21_population_shares.png`, quote del capitale a inizio stagione per famiglia di strategie, senza e con la cassa.

Limiti da dichiarare: vale solo senza puntata minima (§2); μ è scelto su tre stagioni di training, dove il modello è valutato sui dati su cui è stato calibrato; la popolazione contiene strategie scelte dopo aver visto la validazione (lo schema con confronto con la stagione di calibrazione e la regola dell'esito più probabile), quindi anche la popolazione eredita quella scelta.

## 9. Secondo tentativo: le strategie evolvono (variazione, selezione, ereditarietà)

Nella popolazione del §1-8 le strategie sono fisse e cambia solo la quota di capitale: c'è selezione ed ereditarietà, ma non variazione. Qui cambiano le strategie stesse.

**Geni.** Ogni strategia è un genoma di cinque geni, tutti parametri che lo schema accetta già, così che nessuna soglia dell'allarme vada ricalibrata (`src/shk/model/evolution.py`):
- frazione di Kelly senza allarme (λ), in [0,005; 1];
- riduzione della puntata con errore nei dati (κ, λ diventa λ·κ), in [0; 1];
- supervisore: nessuno, confronto con le 40 partite precedenti, confronto con la stagione di calibrazione;
- dopo un errore strutturale: riprende quando l'allarme si spegne, o fermo fino a fine stagione;
- regola di scelta dell'esito: R1, R2, R3.

**Ciclo.** Una generazione è una stagione di validazione, in ordine dal 2002-03 al 2022-23. 20 genomi iniziali casuali giocano la stagione vera (senza puntata minima, capitale iniziale 1); sopravvive la metà con il capitale finale più alto, e ogni sopravvissuto ha un figlio mutato (λ moltiplicato per exp(N(0; 0,3)), κ + N(0; 0,1), ogni gene discreto cambiato con probabilità 0,1). Parametri fissati prima di guardare i risultati. 30 evoluzioni indipendenti (seed diversi) per variante; si riportano mediana e 5-95%.

**Due varianti.** «Libera»: evolvono tutti i geni. «Quarto di Kelly fisso»: λ = 0,25 sempre, si è obbligati a puntare, evolvono supervisore, κ, stop e regola.

**Misure.** Popolazione: capitale finale con il capitale diviso in parti uguali fra i 20 genomi della generazione, cioè quanto ottiene chi segue l'evoluzione senza sapere quale genoma vincerà. Campione: il genoma migliore della stagione precedente.

**Controllo.** I genomi (0,25; 0,75; nessuno; –; R1), (0,25; 0,75; precedenti; fermo; R1) e (0,25; 0,75; calibrazione; fermo; R3) riproducono esattamente il quarto di Kelly, lo schema fermo e lo schema migliore già pubblicati (`tests/test_us_c22_acceptance.py`).

### Risultati (`results/us_c22_evolution_*.csv`, figura `thesis/figures/us_c22_evolution.png`)

| Variante | Popolazione: capitale tipico (mediana, 5-95%) | Campione | Stagioni meglio / peggio del quarto di Kelly (popolazione, mediana) |
| --- | --- | --- | --- |
| Libera | 98% (97-99%) | 99% | – |
| Quarto di Kelly fisso | 70% (65-75%) | 66% | 13 / 6 |
| Riferimenti: quarto di Kelly 57%; quarto di Kelly con l'esito più probabile 68%; schema migliore scelto dopo 77% | | | |

- **Libera: l'evoluzione smette di scommettere.** La frazione di Kelly media scende da 0,20 a 0,03 dopo una stagione, a 0,013 dopo due, poi verso il minimo consentito (0,005). Con puntate così piccole gli altri geni non contano più e derivano a caso. È la stessa conclusione della cassa (§8) e di KellyBench, ottenuta per via evolutiva.
- **Quarto di Kelly fisso: l'evoluzione sceglie lo schema del relatore.** A fine 2022-23 tutte le strategie hanno un supervisore (dal 65% iniziale), l'88% si ferma fino a fine stagione dopo un errore strutturale, circa il 90% punta sull'esito più probabile, e κ scende a circa 0,3 (dopo un errore nei dati si punta meno di quanto previsto dallo schema, 0,75). Il genoma più frequente nell'ultima generazione è: supervisore con le 40 partite precedenti, fermo fino a fine stagione, esito più probabile.
- **Ma non il confronto con la stagione di calibrazione.** La quota con quel supervisore crolla al 5% entro la quarta stagione (2005-06) e non risale più sopra il 22%: nelle prime stagioni, con il modello appena calibrato, il confronto con la stagione di calibrazione non dà vantaggi, e l'evoluzione lo elimina prima che il modello invecchi. È un effetto di contingenza storica: la selezione premia ciò che funziona adesso, non ciò che servirà dopo.
- **Capitale.** La popolazione con il quarto di Kelly fisso conserva il 70%, contro il 57% del quarto di Kelly e il 68% del quarto di Kelly con l'esito più probabile; resta sotto lo schema migliore scelto a posteriori (77%), che batte in 7 stagioni su 19. Il campione (66%) fa peggio della popolazione: il migliore di una stagione non è il migliore della successiva, perché una sola stagione è un segnale rumoroso.

Limiti: la fitness è il capitale di una sola stagione vera, molto rumorosa; i parametri dell'evoluzione (20 genomi, metà sopravvive, intensità delle mutazioni) sono fissati a priori e non esplorati; vale senza puntata minima; la regola R3 e il confronto con la stagione di calibrazione fanno parte dei geni possibili ma sono stati individuati dopo aver visto la validazione.
