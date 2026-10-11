# Backlog
Ultimo task: T39

## Decisioni in vigore
- Scenario base: p = 0.60, b = 1.0 (quota 2.00), T = 1000, M = 10000, lo stesso di C1.1 — S1, 2026-09-27
- Scenario sottile: p = 0.52, b = 1.0 (quota 2.00), T = 380 (una stagione), M = 10000; rappresenta l'edge sottile compatibile con Ω ≈ 5.3% (note di tesi 2.5 §7.2). Scelta del supervisore, non ancora confermata dal programmatore — S1, 2026-09-27
- Gli scenari si definiscono solo in src/shk/kelly/scenarios.py (BASE_SCENARIO, SUBTLE_SCENARIO); test e script li importano, non li ripetono — S1, 2026-09-27
- Seed: SEED = 20260927 in scenarios.py; spawn_generators(SEED) dà due generatori indipendenti, il primo per gli esiti e il secondo per il rumore di stima; una coppia nuova per ogni combinazione di scenario e σ_p, e confronti sempre appaiati (stessi esiti e stesse stime per tutte le regole) — S1, 2026-09-27
- Errore di stima: p̂ diverso per ogni scommessa, p̂ = p + rumore gaussiano con deviazione standard σ_p, saturato in [0, 1]; valori di riferimento σ_p ∈ {0.015, 0.0283, 0.045} (note di tesi 2.5 §3.3 e 3.2 §7) — S1, 2026-09-27
- Frazione stimata f̂ = max(0, p̂ − (1 − p̂)/b), cioè troncata a zero; c = f̂/f*, con f* calcolata sul p vero — S1, 2026-09-27
- "L'errore di stima domina il segnale" significa Var(c) > 1 — S1, 2026-09-27
- Var(c), E[c] ed E[c²] si stimano in forma pooled su tutte le scommesse simulate, mai per singola scommessa (note di tesi 3.2 §7.5) — S1, 2026-09-27
- Il λ fisso di riferimento è il quarto-Kelly, λ = 0.25 — S1, 2026-09-27
- Metriche primarie: crescita mediana per scommessa (median_growth_rate), drawdown mediano (np.median(max_drawdown(paths))), quota di traiettorie sotto il capitale iniziale (fraction_below_start) — S1, 2026-09-27
- Il motore simulate_growth riceve le frazioni dall'esterno e non conosce p né p̂; ogni regola di staking sta in src/shk/kelly/staking.py. Le regole non limitano la frazione sotto 1: una frazione ≥ 1 la rifiuta il motore — S1, 2026-09-27
- Esperimenti: uno script scripts/us_<storia>_<descrizione>.py con run_experiment(), che scrive results/<stesso nome>.csv e thesis/figures/<stesso nome>.png, entrambi versionati; nel CSV float nativi (str) e stringa vuota per i valori non applicabili — S1, 2026-09-27
- Codice statistico in src/shk/stats/, separato da src/shk/kelly/ — S2, 2026-09-28
- Serie C2: n = 380 osservazioni (una stagione), 1000 serie per ogni φ, φ ∈ {0.0, 0.3, 0.5, 0.7} con φ = 0 come controllo; AR(1) con innovazioni N(0, 1) e partenza stazionaria, generate da generate_ar1_series (prima x_0 con size=m, poi le innovazioni in blocco) — S2, 2026-09-28
- Disegni dei gruppi: contiguous_2 (due metà da 190, principale), contiguous_38 (38 blocchi da 10, le giornate della C5.2), random_2 (etichette di contiguous_2 sulla serie permutata a caso, controllo) — S2, 2026-09-28
- Soglia nominale α = 0.05: rigetto se F > quantile 0.95 della F(k − 1, N − k). "Dentro/sopra il 5%" si giudica con l'intervallo Monte Carlo al 99% α ± 2.576·√(α(1 − α)/1000) ≈ [0.0322, 0.0678], estremi inclusi — S2, 2026-09-28
- Moving block bootstrap: B = 999, L ∈ {7, 20, 40} fissate prima dei risultati e tutte riportate; soglia = statistica d'ordine ⌈(1 − α)(B + 1)⌉ (la 950-esima); rigetto se la statistica osservata supera strettamente la soglia — S2, 2026-09-28
- Seed C2: SEED_C2 = 20260928; SeedSequence(SEED_C2).spawn(4), un figlio per φ, diviso con spawn(3) in serie, permutazioni, bootstrap; il flusso bootstrap si divide con spawn(3), un generatore per L usato in sequenza sulle serie; confronti appaiati (stesse serie per tutti i disegni, per la F nominale e per ogni L) — S2, 2026-09-28
- I parametri C2 (PHI_VALUES, N_OBS, N_SERIES, ALPHA, SEED_C2, disegni, BLOCK_LENGTHS, N_BOOT, CSV_COLUMNS) si definiscono solo in src/shk/stats/false_rejection.py; script e test li importano — S2, 2026-09-28
- Nel codice nuovo, interi di tipo sbagliato (bool, float) danno TypeError e interi fuori intervallo ValueError; interi NumPy accettati — S2, 2026-09-28
- Cline esegue ogni comando Python con .\.venv\Scripts\python.exe (es. .\.venv\Scripts\python.exe -m pytest -v): il suo terminale usa di default l'interprete di Anaconda, senza shk — programmatore, 2026-09-28
- Dati reali: un CSV E0 di football-data.co.uk per stagione, in data/raw/E0/<YYYY-YY>.csv, dal 1993-94 al 2023-24 (la finestra di KellyBench, per decisione del programmatore); non versionati (.gitignore esclude data/raw/*). La stagione è la stringa YYYY-YY nella colonna season — S3, 2026-09-29
- Codice dei dati in src/shk/data/, codice di mercato in src/shk/market/; pandas fra le dipendenze runtime senza vincolo di versione, con pyproject.toml come fonte di verità (uv.lock da aggiornare a mano) — S3, 2026-09-29
- Split congelato in config/split.toml, commit 2cea094 del 2026-09-29: training 2000-01, 2010-11, 2020-21; validation = stagioni anteriori al 2023-24, non di training, con B365 pre-partita completa (19 stagioni); history = le altre stagioni anteriori al 2023-24; test 2023-24. Tutte le stagioni ≥ 2023-24 sono bloccate, e i loro file non vengono letti, finché test_unlocked = false. Il file non si modifica; lo sblocco lo fa solo il programmatore, a mano e con commit, dopo il congelamento dei parametri (US-C8.2) — S3, 2026-09-29
- Il codice nuovo carica i dati reali solo con load_by_role (src/shk/data/split.py); load_all_seasons è ammessa solo in loading.py, split.py, coverage.py e scripts/us_c3_1_data_coverage.py, e un test di guardia lo verifica — S3, 2026-09-29
- Colonne quote classificate con classify_column (src/shk/data/coverage.py): group_type, source, market, timing (prematch o closing, aggregatori compresi), kind (odds, line, count); una colonna non classificata dà ValueError. Una terna è completa in una stagione se è non nulla e > 1 su ogni riga — S3, 2026-09-29
- q si ricava dalla terna Bet365 pre-partita B365H, B365D, B365A. Scelta del supervisore su delega, da confermare dal programmatore — S3, 2026-09-29
- De-vigging in src/shk/market/devig.py: proporzionale, additivo e power, somma a 1 entro 1e-12. L'additivo non è applicabile a un mercato con un q ≤ 0: quel mercato si esclude dal confronto per tutti i metodi e si conta — S3, 2026-09-29
- Divergenza fra metodi: spread di un esito = massimo meno minimo dei tre q, in punti percentuali; spread relativo = spread diviso per la media dei tre q; fasce di quota [1, 1.5), [1.5, 2), [2, 3), [3, 5), [5, 10), [10, ∞), chiuse a sinistra; edge di riferimento 2 punti (p − 1/o nello scenario sottile). L'edge è una scelta del supervisore su delega, da confermare — S3, 2026-09-29
- Anti-leakage: storia = partite con Date strettamente anteriore (le altre dello stesso giorno escluse); la partita da prevedere espone solo la whitelist, costruita per inclusione: identificativi Div, Date, HomeTeam, AwayTeam, season, Time, più le colonne con kind = odds e timing = prematch. Fornitore in src/shk/data/walkforward.py, che C4 riuserà; i test anti-leakage non si marcano slow — S3, 2026-09-29
- I test sui dati reali si saltano con motivo esplicito se data/raw/E0/ non contiene CSV; il meccanismo è sempre coperto da test su dati sintetici. I criteri verificabili dai CSV versionati girano anche senza dati — S3, 2026-09-29
- Modulo 1 in src/shk/model/. Elo: delta = R_casa − R_trasferta + h; aggiornamento a somma zero con il punteggio atteso logistico E = 1/(1 + 10^(−delta/400)); probabilità 1X2 col mapping di Davidson sulla stessa scala (s = 400); baseline a pareggio costante con c = frequenza del pareggio sulle partite di training del fit — S4, 2026-09-29
- Neopromosse (decisione del programmatore): una squadra presente in s − 1 conserva il rating; una squadra assente in s − 1 ma già vista riprende l'ultimo rating; una squadra mai vista eredita la media dei rating finali delle ultime tre della classifica di s − 1, calcolata dai soli risultati (3 punti la vittoria, 1 il pareggio; poi differenza reti, gol fatti, nome in ordine alfabetico). La regola si applica alla prima comparsa di ogni squadra in s; nella prima stagione del DataFrame tutte partono da 1500. Le penalizzazioni in punti non sono nei dati — S4, 2026-09-29
- Calibrazione espansiva (scelta del supervisore su delega, da confermare): per ogni stagione di training j, il fit usa le stagioni di training ≤ j; ogni stagione di validazione si prevede col fit delle stagioni di training strettamente anteriori. Obiettivo: log-loss media Davidson sulle sole partite di training del fit, con i rating che girano dal 1993-94. Nelder-Mead con limiti K ∈ [5, 80], h ∈ [0, 200], ν ∈ [0.05, 3]. Valori congelati in ELO_FITS (src/shk/model/elo_fit.py), che non si modifica — S4, 2026-09-29
- ĝ = LL(q) − LL(p), misurato solo sulle stagioni di validazione, contro due serie di q (scelta del supervisore su delega, da confermare): b365_prematch (B365H/D/A) sulle 19 stagioni di validazione e pinnacle_closing (PSCH/D/A) sulle 10 stagioni di validazione dal 2012-13. Modello e tre metodi di de-vigging sulle stesse partite; esclusioni contate per causa. Esito informativo: nessun parametro, filtro o metodo si cambia in funzione di ĝ — S4, 2026-09-29
- Ricalibrazione con lo stesso schema espansivo: one-vs-rest per esito, isotonica e Platt entrambe riportate senza scelta nel codice, limite a [1e-6, 1 − 1e-6] e rinormalizzazione (scelta del supervisore); reliability su 10 bin e Brier multiclasse sulla serie b365_prematch — S4, 2026-09-29
- Un test sui dati reali che supera 60 s si marca slow e si dichiara nel report — S4, 2026-09-29
- Modulo 1 in versione raw per S5, senza ricalibrazione (scelta del supervisore su delega, da confermare) — S5, 2026-09-29
- Serie di S5: log-loss per partita −ln p̂(esito realizzato) delle previsioni walk-forward con ELO_FITS, da compute_model_residuals (src/shk/model/residuals.py); le partite di uno scenario di training j vengono dal fit che termina in j, quelle di validazione dal fit delle stagioni di training strettamente anteriori — S5, 2026-09-29
- Scenari di S5: i tre di training (2000-01, 2010-11, 2020-21) e le 19 stagioni di validazione; il 2023-24 dopo lo sblocco del test (US-C8.2). Scelta del supervisore su delega, da confermare — S5, 2026-09-29
- Matchday: blocco contiguo di 10 partite nell'ordine cronologico stabile della stagione, 38 per stagione. Nei CSV si chiama matchday (colonna e valore di row_type), non giornata, per la convenzione dell'inglese negli identificatori; colonne dei CSV in snake_case; etichette delle figure in italiano — S5, 2026-09-30
- Z-test per matchday: Z = (media della log-loss delle 10 partite − μ_f)/(σ_f/√10), con μ_f e σ_f (ddof = 1) su tutte le partite di training del fit f che prevede la stagione; allarme nominale se |Z| supera strettamente norm.ppf(1 − α/2), con α = ALPHA di false_rejection.py; atteso 1.9 allarmi per stagione — S5, 2026-09-29
- Soglia calibrata dello Z (scelta del supervisore su delega, da confermare): moving block bootstrap della serie di training del fit, che definisce μ_f e σ_f, quindi H₀ per costruzione; statistica |Z| delle prime 10 posizioni; B = 999, L ∈ {7, 20, 40}, α = 0.05; seed SEED_C5 = 20260929, con SeedSequence(SEED_C5).spawn(3) per fit, spawn(3) per L e spawn(2) per calibrazione e verifica; verifica su 1000 ricampionamenti indipendenti nell'intervallo al 99%. calibration.py e false_rejection.py non si modificano — S5, 2026-09-29
- Detector: ADWIN e PageHinkley importati da river, non reimplementati; un'istanza nuova per stagione, alimentata con la log-loss di tutte le partite in ordine cronologico. Parametri scelti su griglia fissata prima dei risultati (ADWIN delta ∈ {0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 0.8}; Page-Hinkley delta ∈ {0.005, 0.01, 0.05} × threshold ∈ {1, 2, 5, 10, 20, 50}): vince la combinazione con media degli allarmi su 2000-01 e 2010-11 più vicina a 1.9, distanza |10·(a + b) − 38|, a parità meno allarmi e poi ordine della griglia; 2020-21 escluso dalla taratura. Congelati in drift.py: ADWIN delta 0.002; Page-Hinkley delta 0.05, threshold 5.0; gli altri parametri congelati coi default di river 0.26.1 e sempre passati in modo esplicito — S5, 2026-09-30
- river fra le dipendenze runtime di pyproject.toml senza vincolo di versione, come pandas; uv.lock lo aggiorna a mano il programmatore — S5, 2026-09-29
- Collocazione del codice: funzioni pure su array in src/shk/stats/drift.py e in src/shk/kelly/; funzioni sui DataFrame del Modulo 1 e costruzione dei CSV in src/shk/model/monitoring.py; src/shk/kelly/ non importa da shk.model né da shk.data — S5, 2026-09-30
- Motore su quote reali (src/shk/kelly/backtest.py): riceve per partita data, frazione, quota ed esito, anche le partite senza puntata (frazione 0); per data L ← L + ln(1 + Σ f_i·r_i), con r_i = o_i − 1 se vinta e −1 se persa; bankroll 1 a inizio stagione; ValueError per frazioni fuori da [0, 1), somma di una data ≥ 1, date non ordinate, quote non finite o ≤ 1; non riceve p né p̂ — S5, 2026-09-30
- Baseline D (scelte del supervisore su delega, da confermare): al più una puntata per partita, sull'esito con p̂·o − 1 massimo se > 0 (a parità nell'ordine H, D, A), con frazione kelly_staking(p̂, o − 1, λ_j) e quote B365 pre-partita non de-viggate; λ_j = 0.25·κ^(allarmi su partite con Date strettamente anteriore); κ ∈ {0, 0.25, 0.5, 0.75, 1} scelto per detector massimizzando la somma della log-ricchezza finale di 2010-11 e 2020-21, a parità esatta dei float il più grande; 2000-01 escluso perché senza B365. Congelati in staking.py: KAPPA_ADWIN = KAPPA_PAGE_HINKLEY = 1.0. Il detector dice quando, non quanto né di che tipo — S5, 2026-09-30
- Story S6 = US-C6.1–C6.4 in sette task: T33–T37 (C6.1–C6.3) nella prima chat; rimappatura; T38–T39 (C6.4) nella seconda — S6, 2026-10-09
- Agenti in src/shk/kelly/agents.py: classe astratta Agent con decide(view) comune (selezione per partita come la Baseline D di C5.3; ripiego sulla coppia partita-esito con EV stimato massimo della data) e regola astratta stake_fractions; FractionalKellyAgent (A λ = 1.0; B λ = 0.25 e 0.10) e MinimumStakeAgent (E, frazioni nulle). Una sottoclasse ridefinisce solo __init__ e stake_fractions (TypeError altrimenti); previsioni, quote e argomenti di stake_fractions in sola lettura (viste non scrivibili di copie non scrivibili). Il bankroll non entra negli agenti — S6, 2026-10-09
- La puntata obbligatoria vale per data (Date), l'analogo del matchday di KellyBench (circa 103 date per stagione di validazione); "matchday" nel codice resta il blocco di 10 partite di S5 — S6, 2026-10-09
- Ambiente (src/shk/kelly/environment.py) con puntata minima F ≥ 0 in unità del bankroll iniziale. F = 0: nessun floor e nessuna puntata obbligatoria. F > 0: ogni puntata piazzata vale almeno F, anche quelle volontarie (il quarter-Kelly "floored" di GLM-5); se l'agente non punta, una puntata da F sul ripiego. Le puntate della data si piazzano in ordine di EV stimato decrescente finché la somma resta ≤ W; le altre si scartano e si contano. Rovina, assorbente, se a inizio data W = 0, oppure F > 0 e W < F (stretto). decide si chiama per ogni agente a ogni data, anche se rovinato; una sola DateView per data, la stessa per tutti. Scelta del supervisore su delega, da confermare — S6, 2026-10-09
- Configurazioni: B0 = £220 con F = £0.01 (B0/F = 22 000, principale) e F = £1 (B0/F = 220), più F = 0; costanti in src/shk/model/paired_backtest.py (CONFIGURATIONS). Valori dalle note 2.9 §0 e 3.4 §1.1 e §10, non dal codice dell'ambiente: da confermare — S6, 2026-10-09
- Dati reali in C6: 19 stagioni di validazione, Modulo 1 raw, quote B365 pre-partita non de-viggate, bankroll 1 a inizio stagione, input da assemble_baseline_d_season_input (monitoring.py non si modifica). B 0.25 con F = 0 riproduce il riferimento di C5.3 entro 1e-12 su ogni stagione. La Baseline D resta fuori da C6 (con κ = 1 coincide con B 0.25) — S6, 2026-10-09
- Metriche di C6.2, su stagioni o repliche: mediana di B_T; drawdown massimo per traiettoria (wealth_max_drawdown); tempo di recupero = date dal minimo del drawdown massimo al primo ritorno al picco che lo precede, censurato se non avviene (wealth_recovery_time); tasso di rovina; SD di ln B_T (ddof = 1) sulle traiettorie non rovinate, col loro numero — S6, 2026-10-09
- Baseline E e paper: il ROI di E per stagione di validazione si confronta col −4.1% del paper (e col −5.1% dedotto in nota 3.4 §9) solo come indicazione; il confronto sul 2023-24 dopo lo sblocco del test — S6, 2026-10-09
- SEED_C6 = 20261009 in src/shk/kelly/floor.py; SeedSequence(SEED_C6).spawn(2): figlio 0 a T36, diviso con spawn(3) negli esperimenti A, B, C (C con spawn(3), un figlio per configurazione); figlio 1 a T37, diviso con spawn(19), uno per stagione di validazione in ordine cronologico — S6, 2026-10-09
- Floor sintetico (T36): stesso ambiente su un calendario a una partita per data; configurazione principale della nota 2.9 §5.1 (o = 2.5, EV vero −0.02, edge stimato +0.03, λ = 0.25); f*, f, B1, B2 derivati a runtime da kelly_staking e floor_thresholds; M = 10 000 (C: 1 000, orizzonte ⌈2·limite⌉, ⌈10·limite⌉ per la configurazione b); confronto con la nota con tolleranza Monte Carlo a due campioni al 99% — S6, 2026-10-09
- Floor nella configurazione reale (T37): esiti estratti dalle q proporzionali di B365, per cui l'EV vero è 1/S − 1 su ogni esito; M = 1 000 per stagione; soglie di drawdown θ = 0.5 e θ = 0.1, cioè P(min W ≤ θ) — S6, 2026-10-09
- Messaggi all'agente da T34: ogni comando si riporta per intero, nell'ordine reale e con l'esito; un output perso si dichiara perso; vietate le letture fuori dal repository (compresi log e trascrizioni della piattaforma) e i comandi git che mostrano il contenuto di .agent/; nessun print negli script, il tempo si misura dall'esterno — S6, 2026-10-09
- C6.4 nella stessa chat di T33–T37, in deroga alla regola dei cinque e senza rimappare prima, perché T38 e T39 toccano stats/ e la serie del Modulo 1, mappati il 2026-10-07; rimappatura dopo T39. Decisione del programmatore — S6, 2026-10-09
- statsmodels nell'extra dev di pyproject.toml, senza vincolo di versione, importato solo in tests/; Breusch-Pagan (Koenker) e White a mano in src/shk/stats/heteroskedasticity.py, con QR (mai l'inversa di X'X), regressori standardizzati internamente e la stessa procedura nel ciclo e nei lotti — S6, 2026-10-09
- C6.4, statistiche (scelta del supervisore su delega, da confermare): y = log-loss per partita del Modulo 1 raw; e = residui OLS di y ~ 1 + H + t, con H = entropia di p̂ (p_home, p_draw, p_away della serie di S5) e t = posizione nella stagione, nell'ordine dei matchday di S5; LM = n·R² della regressione ausiliaria di e² con costante. Tre statistiche: bp_joint con z = (H, t), bp_time con z = t, white su (H, t) con quadrati e prodotto. Soglia nominale: quantile 0.95 del χ² con gradi di libertà pari ai regressori ausiliari; rigetto se LM supera strettamente la soglia — S6, 2026-10-09
- C6.4, soglia calibrata: moving block bootstrap della serie di training del fit che prevede la stagione, come in T30. Le righe (y, H) si ricampionano insieme, si tengono le prime 380 posizioni e t = 1..380; le tre statistiche usano gli stessi indici. B = 999, L ∈ {7, 20, 40}, soglia = 950-esima statistica d'ordine. Seed SeedSequence(SEED_C6).spawn(3)[2], poi spawn(3) per fit, spawn(3) per L, spawn(2) per calibrazione e verifica. Verifica su 1 000 ricampionamenti per fit × L × statistica, con intervallo 0.05 ± 3.56·√(2·0.05·0.95/1000) ≈ [0.0153, 0.0847] (Bonferroni su 27 e varianza della soglia stimata). Scenari: 3 di training (in campione) e 19 di validazione; i conteggi binomiali solo sulla validazione — S6, 2026-10-09
- HAC e anova_lm: AR(1) con φ = 0.7, n = 380, due metà da 190; OLS con cov_type="HAC" e maxlags = 5 (⌊4(n/100)^(2/9)⌋); confronto dell'F di anova_lm per typ = 1, 2, 3 con l'F dell'OLS e col Wald HAC — S6, 2026-10-09

## Story chiuse
### S1 — C1 Simulatore Kelly: motore riusabile ed errore di stima — chiusa il 2026-09-27
Esito: unisce US-C1.3 e US-C1.2; tutti i criteri coperti da test (suite veloce 44, suite slow 9). Risultati in results/us_c1_2_estimation_error.csv e thesis/figures/us_c1_2_estimation_error.png; valori misurati nei report .agent/report/T4.md … T7.md.
Resta aperto: Definition of Done di US-C1.2 (scegliere un caso in cui λ* batte il quarto-Kelly e uno in cui no; dati nel report T6); confermare lo scenario sottile e il modello dell'errore di stima; eventuale US-C1.4 sul controllo delle frequenze di drawdown α^(2/λ−1) (note di tesi 2.5 §10.4).
- T1 — Motore di crescita che riceve le frazioni dall'esterno — fatto — file: src/shk/kelly/simulate.py, tests/test_simulate.py
- T2 — Generatore di stime perturbate p̂ — fatto — file: src/shk/kelly/estimation.py, tests/test_estimation.py
- T3 — Regola di staking Kelly sulla stima, con troncamento e moltiplicatore λ — fatto — file: src/shk/kelly/staking.py, tests/test_staking.py
- T4 — Simulazione con p̂ ≠ p e asimmetria sovrastima/sottostima — fatto — file: src/shk/kelly/scenarios.py, tests/test_us_c1_2_acceptance.py
- T5 — Var(c) empirica e dominanza dell'errore di stima — fatto — file: src/shk/kelly/staking.py, tests/test_staking.py, tests/test_us_c1_2_acceptance.py
- T6 — λ* contro quarto-Kelly — fatto — file: src/shk/kelly/staking.py, tests/test_staking.py, tests/test_us_c1_2_acceptance.py
- T7 — Script dell'esperimento C1.2, CSV e figura per la tesi — fatto — file: scripts/us_c1_2_estimation_error.py, results/us_c1_2_estimation_error.csv, thesis/figures/us_c1_2_estimation_error.png

### S3 — C3 Primo contatto coi dati reali: copertura, split congelato, de-vigging, anti-leakage — chiusa il 2026-09-29
Esito: unisce US-C3.1, US-C3.2, US-C3.3 e US-C3.4. Sei task (T14–T19), tutti chiusi con i criteri coperti da test, eseguiti in una sola chat per decisione del programmatore (in deroga alla regola dei cinque e al piano di due chat). Suite veloce 109 → 181 verde (72 test nuovi); suite slow invariata (14, di cui 1 rossa per il risultato noto di T12). Split congelato in config/split.toml, commit 2cea094 del 2026-09-29 11:47, verificato prima di T18. Risultati in results/us_c3_1_data_coverage.csv, results/us_c3_2_devig_divergence.csv e nelle due figure omonime in thesis/figures/; valori misurati nei report .agent/report/T14.md … T19.md, ricalcolati in modo indipendente dal supervisore dove numerici.
Note di esecuzione: correttivi in T15 (un test mancante) e T18 (riproducibilità col codice finale); in T17 Cline ha eseguito comandi Python prima dell'approvazione del piano e in T18 ha creato un file di misura fuori dal repository, senza toccare il codice del progetto.
- T14 — Caricamento di tutte le stagioni E0 in un unico DataFrame — fatto — file: pyproject.toml, src/shk/data/__init__.py, src/shk/data/loading.py, tests/test_data_loading.py
- T15 — Audit della copertura di quote, risultati e bookmaker per stagione, US-C3.1 — fatto — file: src/shk/data/coverage.py, scripts/us_c3_1_data_coverage.py, tests/test_coverage.py, results/us_c3_1_data_coverage.csv, thesis/figures/us_c3_1_data_coverage.png
- T16 — Split congelato su file e blocco del test set, US-C3.3 — fatto — file: config/split.toml, src/shk/data/loading.py, src/shk/data/split.py, tests/test_split.py
- T17 — Tre metodi di de-vigging, US-C3.2 primo criterio — fatto — file: src/shk/market/__init__.py, src/shk/market/devig.py, tests/test_devig.py
- T18 — Divergenza fra metodi di de-vigging sulle stagioni non di test, US-C3.2 — fatto — file: src/shk/market/divergence.py, scripts/us_c3_2_devig_divergence.py, tests/test_us_c3_2_acceptance.py, results/us_c3_2_devig_divergence.csv, thesis/figures/us_c3_2_devig_divergence.png
- T19 — Fornitore walk-forward e test anti-leakage, US-C3.4 — fatto — file: src/shk/data/walkforward.py, tests/test_leakage.py
- dopo la chiusura, la prima CI sul branch C4 ha rivelato che i test di ricalcolo di C4.2 e C4.3 si saltavano solo senza il CSV versionato, non senza i dati grezzi: il criterio "si salta senza CSV" era ambiguo e il supervisore non l'ha controllato in CI. Corretto in T25.

Risultati principali:
- Dati: 31 stagioni E0 (1993-94 … 2023-24), 11 944 partite (462 nel 1993-94 e nel 1994-95, 380 nelle altre). Risultati completi dal 1993-94; prima terna 1X2 pre-partita completa nel 2000-01 (GB, IW, SB, WH), 2 stagioni prima del 2002-03 del paper; B365 completa in tutte le stagioni dal 2002-03 al 2023-24, assente nel 2000-01, che è di training.
- Split: training 2000-01, 2010-11, 2020-21 (1 140 partite); validation 19 stagioni, dal 2002-03 al 2022-23 tranne le due di training (7 220); history 1993-94 … 1999-00 e 2001-02 (3 204); test 2023-24, bloccato e non letto (380).
- De-vigging: valori delle note 2.1 §7 riprodotti (scarto massimo 4.75e-6 sulle probabilità; k = 1.079146, 1.088682, 1.082367); sui 10 000 mercati casuali |Σq − 1| ≤ 4.4e-16, additivo non applicabile su 151.
- Divergenza su B365 (7 980 partite; 2000-01 escluso per intero; 0 mercati esclusi per l'additivo): overround medio 5.437%, fuori da 2–7% dal 2002-03 al 2006-07; spread medio in punti massimo in [1, 1.5) (2.33); spread relativo medio massimo in [10, ∞) (0.222), non monotono (minimo in [2, 3)); spread massimo 6.29 punti, 3.14 volte l'edge di 2 punti; 99° percentile 3.45 punti, 1.73 volte.
- Anti-leakage: 8 360 partite di training e validazione senza violazioni; i tre mutanti sono rilevati; whitelist di 87 campi (6 identificativi e 81 quote pre-partita, nessuna chiusura); il test sui dati reali dura circa 8 s ed è nella suite veloce.

Resta aperto:
- Scenario di training 2000-01 senza B365: con q alimentato da B365 è escluso per intero. Alternative: dichiararlo in tesi e procedere con 2010-11 e 2020-21; usare per il solo 2000-01 un'altra terna completa (GB, IW, SB o WH); rivedere lo scenario in una chat di backlog.
- Limiti residui dei test: test_extreme_markets salta i NaN dell'additivo; non è verificato che il test sintetico di T18 includa il mercato 1.25/6.00/11.0; nessun test dedicato confronta due file di split diversi.

### Fuori scope di S3
- La variante "literature" del 2023/24, che non è ricostruibile da football-data.
- I metodi Shin e odds ratio (note 2.1 §6.3, §6.5).
- Il de-vigging di over/under e handicap asiatico.
- Le quote di chiusura e Pinnacle come benchmark alternativo per q (note 2.4 §2): è una scelta da fare in C4.2.
- La coerenza dei nomi squadra fra stagioni (note 2.9 §2.4): utile per C4.1, per l'Elo e le neopromosse.
- L'integrazione del fornitore walk-forward nella pipeline, che spetta a C4.
- La tabella di sensibilità completa, metodo × metrica × agente (US-C9.3).
- L'aggiornamento di uv.lock e la migrazione della CI a uv.

### Resta al programmatore per S3
- Fatto: CSV E0 scaricati (solo 1993-94 … 2023-24); config/split.toml committato (2cea094, 2026-09-29 11:47).
- Decidere se versionare i CSV E0, controllando la licenza (note 2.9): finché non sono versionati, i test sui dati reali non girano in CI.
- Decidere sullo scenario di training 2000-01 senza B365 (vedi "Resta aperto").
- Confermare o cambiare le scelte fatte dal supervisore su delega il 2026-09-29: Bet365 pre-partita come colonna di q; validazione sulle stagioni anteriori al 2023-24 con B365 completa; blocco di tutte le stagioni dal 2023-24 in poi; edge di riferimento di 2 punti; "divergenza massima sugli outsider" letta in termini relativi.
- US-C3.1, esito informativo: scrivere in tesi la finestra effettiva di analisi (quote 1X2 complete dal 2000-01, B365 dal 2002-03) e la conseguenza sullo scenario di training 2000-01 (note 2.9 §2.2).
- US-C3.2, Definition of Done: saper dire se la divergenza fra metodi è dello stesso ordine dell'edge (spread massimo 3.14 volte, 99° percentile 1.73 volte, media per fascia da 0.35 a 2.33 punti), e ricavare dal CSV di T18 la prima riga della tabella di sensibilità (US-C9.3).
- Correggere l'enunciato di US-C3.2 nelle note, come confermato da T18: in punti percentuali la divergenza è massima sul favorito, in termini relativi sull'outsider.
- US-C3.4: introdurre a mano, una volta, un leakage nel fornitore (per esempio side="right" al posto di side="left" in src/shk/data/walkforward.py), vedere il test rosso e ripristinare.
- Aggiornare uv.lock dopo l'aggiunta di pandas.
- Committare codice, CSV e figure di T17–T19, e quelli di T14–T16 se non sono già nel commit 2cea094.

### S4 — C4 Elo e go/no-go: Modulo 1 minimo, ĝ contro il mercato, calibrazione — chiusa il 2026-09-29
Esito: unisce US-C4.1, US-C4.2 e US-C4.3. Cinque task (T20–T24), tutti chiusi con i criteri coperti da test, in una sola chat, sul branch C4. Suite veloce 181 → 248 verde (67 test nuovi); suite slow 14 → 15 (il nuovo test di ricalibrazione è verde in 119 s; resta rosso il risultato noto di T12). Risultati in results/us_c4_1_elo_walkforward.csv, results/us_c4_2_g_hat.csv, results/us_c4_3_calibration.csv e nelle tre figure omonime in thesis/figures/; valori misurati nei report .agent/report/T20.md … T24.md, ricalcolati in modo indipendente dal supervisore dove numerici.
Note di esecuzione:
- correttivi in T20 (valori del report non prodotti da comandi), T21 (report; poi, per decisione del programmatore, tempi del percorso veloce da 31.7 s a 0.35 s a output invariato, verificato con SHA256) e T24 (dimensione della figura non misurata). In tre report su cinque c'erano valori non prodotti da comandi, intercettati dal ricalcolo del supervisore;
- in T24 test_platt_fit_predict_properties è passata da (0, 1) a [0, 1] dopo un fallimento: su dati sintetici a gradino la sigmoide di Platt satura a 1.0 in float64;
- in T23 e T24 l'agente ha letto file fuori dal repository: i propri log e, nel correttivo di T24 e contro istruzione, le ultime 50 righe della cronologia di PowerShell. Nessun file scritto fuori scope, nessun comando git vietato.
- T20 — Funzioni Elo e mapping 1X2 (Davidson e pareggio costante) — fatto — file: src/shk/model/__init__.py, src/shk/model/elo.py, tests/test_elo.py
- T21 — Previsore Elo walk-forward con regola per le neopromosse, US-C4.1 — fatto — file: src/shk/model/elo_predictor.py, tests/test_elo_predictor.py
- T22 — Calibrazione espansiva di K, h, ν sul training e previsioni walk-forward, US-C4.1 — fatto — file: src/shk/model/elo_fit.py, scripts/us_c4_1_elo_walkforward.py, tests/test_us_c4_1_acceptance.py, results/us_c4_1_elo_walkforward.csv, thesis/figures/us_c4_1_elo_walkforward.png
- T23 — ĝ del Modulo 1 contro il mercato de-viggato, US-C4.2 — fatto — file: src/shk/model/scoring.py, scripts/us_c4_2_g_hat.py, tests/test_scoring.py, tests/test_us_c4_2_acceptance.py, results/us_c4_2_g_hat.csv, thesis/figures/us_c4_2_g_hat.png
- T24 — Calibrazione del Modulo 1: reliability, Brier e ricalibrazione, US-C4.3 — fatto — file: src/shk/model/recalibration.py, scripts/us_c4_3_calibration.py, tests/test_recalibration.py, tests/test_us_c4_3_acceptance.py, results/us_c4_3_calibration.csv, thesis/figures/us_c4_3_calibration.png
- T25 — Salto dei test di ricalcolo C4.2 e C4.3 senza dati grezzi (correzione della CI, fuori story; sesto task della chat, in deroga alla regola dei cinque, per decisione del programmatore) — in corso: manca la verifica della CI — file: tests/test_us_c4_2_acceptance.py, tests/test_us_c4_3_acceptance.py. Causa: la CI del 2026-09-29 sul branch C4 falliva su test_recalculation_from_real_data_matches_csv di C4.2 e C4.3 (FileNotFoundError, data/raw/E0 assente), perché i due test si saltavano solo senza il CSV versionato in results/ e non senza i dati grezzi. Ora hanno anche skipif(not _has_real_data(), reason="Raw CSV data not available in data/raw/E0/"), come test_elo_predictor.py; in tests/ non resta nessuna chiamata a load_by_role o load_all_seasons senza protezione. In locale i due test passano; suite veloce 248 verdi, 15 deselezionati, 50.28 s. Report: .agent/report/T25.md.

Risultati principali:
- Modulo 1 Elo: Davidson riproduce la tabella delle note 2.8 §3.3 solo con s = 200 (scarto massimo 4.4e-4; con s = 400 lo scarto sarebbe 0.20). Percorso via fornitore e percorso veloce danno previsioni identiche byte per byte sulle 8 360 partite di training e validazione (0.35 s il veloce, 10.6 s il fornitore).
- Transizioni reali dal 1993-94 al 2022-23: 22, 22, poi 20 squadre; 86 entrate, di cui 28 nuove e 58 tornanti; nomi squadra coerenti. Le ultime tre calcolate coincidono con le uscite effettive in 28 transizioni su 29; al 1997-98 la classifica calcolata dà Coventry al posto del Middlesbrough, penalizzato fuori dai dati.
- ELO_FITS (Nelder-Mead, tutti i fit convergenti, nessun parametro su un limite): 2000-01 K 10.32, h 125.5, ν 0.806, c 0.266; 2010-11 K 9.93, h 127.9, ν 0.878, c 0.279; 2020-21 K 7.93, h 78.0, ν 0.760, c 0.259. Log-loss di validazione Davidson 0.9738, 0.9838, 0.9833; baseline a pareggio costante 0.9768, 0.9901, 0.9876. La media dei rating a inizio stagione sale da 1500 a circa 1525 nel 2022-23, per effetto dei tornanti.
- ĝ (proporzionale / additivo / power), negativo in tutti i casi e a ogni fine stagione del cumulativo: b365_prematch (7 220 partite) −0.0214 / −0.0224 / −0.0224; pinnacle_closing (3 800) −0.0315 / −0.0316 / −0.0317. Log-loss del modello 0.9795 e 0.9812; del mercato fra 0.9571 e 0.9581 e fra 0.9496 e 0.9498. Nessuna esclusione; devig_power converge su tutte le chiusure.
- Calibrazione del modello su b365_prematch, versione raw: fasce peggio calibrate trasferta [0.4, 0.5) con z = +6.06 e [0.5, 0.6) con +5.30, cioè trasferta sottostimata; casa [0.7, 0.8) con +4.34. Log-loss di validazione raw / Platt / isotonica: 0.9795 / 0.9823 / 1.0139 su B365, 0.9812 / 0.9809 / 0.9914 su Pinnacle. ĝ dopo Platt fra −0.024 e −0.031, dopo l'isotonica fra −0.042 e −0.057. Valori limitati: isotonica 265 e 77, Platt 0.

Resta aperto:
- elo_fit.py duplica in forma pubblica (parse_season_start_year) il parsing della stagione di elo_predictor.py.
- La ricerca di try:, print( e logging non è stata rieseguita su elo_predictor.py dopo il secondo correttivo di T21, e non è mai stata eseguita sugli script di S4.
- Imprecisioni nei report, lasciati come sono: nomi di mutante e confronto nel report T21, un comando abbreviato nel report T22, comandi esplorativi del correttivo non elencati nel report T24. Fanno fede i valori riportati qui e nella scheda.

### Fuori scope di S4
- Il secondo Modulo 1 (Dixon-Coles pesato) e il confronto appaiato fra i due (note 2.8 §11).
- Il test placebo con esiti permutati entro stagione (note 2.8 §9.3).
- Gli intervalli di confidenza di ĝ per block bootstrap (C8).
- La serie h_t a finestra mobile e il crollo del 2020-21 (note 2.8 §2.3).
- Il blending logit fra modello e mercato (note 2.8 §12).
- Le varianti di K (margine di vittoria, K decrescente, K maggiore per le squadre nuove) e la regressione verso la media fra stagioni.
- La verifica Elo = Bradley-Terry a precisione macchina (note 2.8 §2.5).
- ECE, bande di confidenza sul reliability diagram, stratificazione per fascia di quota.
- ĝ per stagione e per fascia di quota; la soglia di redditività ĝ > ln π (note 2.4 §8).
- Il criterio 11 della rubrica, cioè non puntare sulle neopromosse per le prime m giornate: riguarda lo staking.
- La decisione sullo scenario di training 2000-01 senza B365 resta aperta (S3). In C4 non ha bloccato: ĝ si misura solo sulla validazione.

### Resta al programmatore per S4
- Fatto: rimappatura del progetto il 2026-09-29 a 27cf7a4; C4 portato in main come 27cf7a4, con T20–T25.
- Confermare o cambiare le scelte fatte dal supervisore su delega il 2026-09-29:
  - q con serie principale B365 pre-partita e seconda serie Pinnacle chiusura dal 2012-13;
  - calibrazione espansiva di K, h, ν e della ricalibrazione;
  - retrocesse identificate dalla classifica calcolata (nel 1996-97 dà Coventry al posto del Middlesbrough);
  - limite [1e-6, 1 − 1e-6] nella ricalibrazione.
- Correggere o dichiarare la tabella di Davidson delle note 2.8 §3.3: è calcolata con 10^(ΔR/200), mentre il modello usa la scala 400 del punteggio atteso.
- US-C4.2, esito informativo: scrivere l'introduzione della tesi in base al segno di ĝ, negativo in tutti i casi, dichiarandolo in apertura e non nei limiti (note 2.4 §6).
- Dichiarare in tesi: il mapping Davidson e la sensibilità rispetto alla baseline a pareggio costante; la regola per le neopromosse; lo schema espansivo degli iperparametri.
- US-C4.3: decidere se serve una ricalibrazione e quale adottare, isotonica o Platt, da congelare. Log-loss di validazione raw / Platt / isotonica: 0.9795 / 0.9823 / 1.0139 su B365, 0.9812 / 0.9809 / 0.9914 su Pinnacle. In S5 si è usato raw su delega.
- Decidere sull'accesso dell'agente ai file fuori dal repository: lasciarlo com'è, oppure limitarne i permessi alla cartella del progetto e aggiungere il divieto alle "Convenzioni del progetto" di .agent/PROTOCOLLO.md. Controllare che le 50 righe della cronologia di PowerShell lette in T24 non contenessero credenziali. La violazione si è ripetuta in S5 e in S6.
- Decidere se aggiungere alle "Convenzioni del progetto" di .agent/PROTOCOLLO.md la regola "ogni valore numerico del report viene da un comando elencato".
- Verificare la CI su main dopo 27cf7a4 e, se è verde, cambiare lo stato di T25 da "in corso: manca la verifica della CI" a "fatto".

### S5 — C5 Drift detector standard: ADWIN e Page-Hinkley, Z-test per matchday, Baseline D — chiusa il 2026-09-30
Esito: unisce US-C5.1, US-C5.2 e US-C5.3. Sette task (T26–T32), tutti chiusi con i criteri coperti da test, in una sola chat sul branch C5, in deroga alla regola dei cinque per decisione del programmatore. Suite veloce 248 → 317 verde (69 test nuovi); suite slow invariata (15, nessun test slow aggiunto, non rieseguita). Risultati in results/us_c5_1_drift_detectors.csv, results/us_c5_2_daily_z_test.csv, results/us_c5_3_baseline_d.csv e nelle tre figure omonime in thesis/figures/; valori misurati nei report .agent/report/T26.md … T32.md, ricalcolati in modo indipendente dal supervisore dove numerici. Dopo la mappa del 2026-09-29c sono stati chiusi sette task di scrittura: la prossima chat deve rimappare.
Note di esecuzione:
- un correttivo in T28 (totali del report non prodotti da comandi). Valori o comandi non prodotti da un comando anche in R2, R8 e R12 e nei comandi abbreviati dei report di T31 e T32, intercettati dal supervisore;
- l'agente ha letto i log della piattaforma fuori dal repository in R2 (messaggio troncato di 277 byte) e in R14 (senza dichiararlo, con il messaggio integro); ha letto più volte sezioni del backlog fuori dal task. Nessun file scritto fuori scope, nessun comando git vietato;
- i messaggi lunghi arrivano troncati in coda: da T27 i messaggi all'agente terminano con una riga di controllo;
- river 0.26.1 installato nel .venv dopo un dry-run che non toccava le altre dipendenze.
- T26 — Serie di log-loss per partita del Modulo 1 — fatto — file: src/shk/model/residuals.py, tests/test_residuals.py
- T27 — ADWIN e Page-Hinkley da river, tarati sul training — fatto — file: pyproject.toml, src/shk/stats/drift.py, tests/test_drift.py
- T28 — Allarmi di ADWIN e Page-Hinkley su ogni scenario, US-C5.1 — fatto — file: src/shk/stats/drift.py, src/shk/model/monitoring.py, scripts/us_c5_1_drift_detectors.py, tests/test_us_c5_1_acceptance.py, results/us_c5_1_drift_detectors.csv, thesis/figures/us_c5_1_drift_detectors.png
- T29 — Z-test per matchday con soglia nominale e confronto con ADWIN e Page-Hinkley, US-C5.2 — fatto — file: src/shk/stats/drift.py, src/shk/model/monitoring.py, tests/test_drift.py, scripts/us_c5_2_daily_z_test.py, tests/test_us_c5_2_acceptance.py, results/us_c5_2_daily_z_test.csv, thesis/figures/us_c5_2_daily_z_test.png
- T30 — Soglia dello Z-test calibrata per block bootstrap, US-C5.2 — fatto — file: src/shk/stats/drift.py, src/shk/model/monitoring.py, scripts/us_c5_2_daily_z_test.py, tests/test_drift.py, tests/test_us_c5_2_acceptance.py, results/us_c5_2_daily_z_test.csv, thesis/figures/us_c5_2_daily_z_test.png
- T31 — Motore su quote reali e regola della Baseline D, con κ calibrato sul training, US-C5.3 — fatto — file: src/shk/kelly/backtest.py, src/shk/kelly/staking.py, src/shk/model/monitoring.py, tests/test_backtest.py, tests/test_staking.py, tests/test_us_c5_3_acceptance.py
- T32 — Esecuzione appaiata della Baseline D sulle stagioni di validazione, US-C5.3 — fatto — file: src/shk/model/monitoring.py, scripts/us_c5_3_baseline_d.py, tests/test_us_c5_3_acceptance.py, results/us_c5_3_baseline_d.csv, thesis/figures/us_c5_3_baseline_d.png

Risultati principali:
- Serie del Modulo 1 raw (T26): 9 500 righe (training 380 / 760 / 1 140 per fit, validazione 3 040 / 3 420 / 760); log-loss medie uguali a quelle di C4.1 entro 4.1e-7.
- Taratura dei detector (T27), river 0.26.1: ADWIN 0 allarmi su 2000-01 e 2010-11 per tutti i 9 delta, scelto 0.002 per l'ordine della griglia; Page-Hinkley scelto delta 0.05, threshold 5.0, con 1 allarme per stagione (media 1.0 contro il target 1.9).
- C5.1 (T28), 22 stagioni: ADWIN 0 allarmi ovunque, compreso il 2020-21; Page-Hinkley 22 allarmi, 2 in training (nessuno nel 2020-21) e 20 in validazione su 12 stagioni.
- C5.2 (T29), 19 stagioni di validazione: baseline μ_f 1.00819 / 1.00899 / 1.02094, σ_f 0.410 / 0.421 / 0.384; Z nominale 53 allarmi (media 2.789 per stagione contro 1.9; 20 con Z > 0, 33 con Z < 0); ADWIN 0; Page-Hinkley 20 (media 1.053).
- C5.2 calibrato (T30): soglie da 1.773 a 2.131 contro 1.960 nominale; tassi di verifica con soglia calibrata fra 0.038 e 0.065, tutti nell'intervallo al 99%, con soglia nominale fra 0.045 e 0.076; allarmi calibrati 61 (L = 7), 43 (L = 20), 43 (L = 40). Con L ≥ 10 la distribuzione bootstrap si riduce alle finestre contigue di 10 partite del training: nel fit 2000-01 L = 20 e L = 40 danno la stessa soglia.
- κ della Baseline D (T31) su 2010-11 e 2020-21: κ = 1 per entrambi i detector (ADWIN per parità su tutta la griglia, Page-Hinkley massimo stretto); quarto-Kelly 0.2108 nel 2010-11 e −0.0756 nel 2020-21.
- C5.3 (T32), 19 stagioni di validazione: D-ADWIN e D-Page-Hinkley coincidono col riferimento in ogni stagione; riferimento con log-ricchezza totale −10.580 su 6 234 puntate, positiva solo nel 2005-06 e nel 2008-09; drawdown massimo per stagione da 0.375 a 0.774.

Resta aperto:
- Taratura di ADWIN: con la griglia fissata e questa serie non scatta mai. Alternative: dichiararlo in tesi; rivedere griglia, serie o target in una chat di backlog, con criteri scritti prima.
- κ della Baseline D: κ = 1 per entrambi i detector rende la Baseline D identica al quarto-Kelly senza detector, e la figura di C5.3 mostra differenze tutte nulle. La calibrazione usa stagioni in campione per il Modulo 1. Alternative: dichiararlo in tesi; rivedere griglia, stagioni od obiettivo di κ, ed eventualmente il contenuto della figura, in una chat di backlog. In S6 la Baseline D è rimasta fuori da C6.
- US-C5.1 sul 2023-24, dopo lo sblocco del test.
- Il salto dei test di ricalcolo senza dati è verificato leggendo il codice (T26) o dai report, non da un'esecuzione in CI.
- Imprecisioni nei report, lasciati come sono: indice e data del primo allarme di Page-Hinkley nel 2000-01 discordi fra R8 e R9 (stessa matchday 8); comandi abbreviati nei report T31 e T32; figura di C5.3 descritta a due pannelli. Fanno fede i valori riportati qui e nella scheda.

### Fuori scope di S5
- Esecuzione dei detector e della Baseline D sul 2023-24, possibile solo dopo lo sblocco del test (US-C8.2); la variante literature del 2023-24, non ricostruibile da football-data.
- Architettura ad agenti a classi e agenti A, B ed E (US-C6.1, US-C6.2); molti seed e intervalli per block bootstrap (US-C8.3).
- Il seguito di T12 e la correzione della docstring di calibration.py, che restano nella story S2.
- CUSUM, EWMA, DDM ed EDDM; Bonferroni, Šidák e la soglia sul massimo dei 38 Z, cioè il controllo della FWER (note 1.4 §5).
- La baseline esterna, cioè il log-score differenziale contro il mercato, come criterio di arresto (note 1.4 §6.3).
- Precision e recall dei detector rispetto a date di drift note, e la mappatura scenario → tipo di drift (note 2.7 §6.4).
- Kelly simultaneo sui tre esiti dell'1X2, il ritorno di λ al valore iniziale dopo un allarme, una durata della riduzione come secondo parametro.
- Il Modulo 1 ricalibrato (Platt o isotonica) come serie alternativa.

### Resta al programmatore per S5
- Fatto: C5 portato in main come 736f5cd (2026-10-02); rimappatura del 2026-10-07 (R1) e scheda aggiornata (R2–R6).
- Confermare o cambiare le scelte fatte dal supervisore su delega il 2026-09-29:
  - Modulo 1 raw;
  - scenari di ora = 3 di training più 19 di validazione, con il 2023-24 dopo lo sblocco;
  - calibrazione dello Z sulla serie di training del fit;
  - taratura dei detector su 1.9 allarmi per stagione su 2000-01 e 2010-11, con il 2020-21 escluso;
  - Baseline D: un esito per partita, λ di partenza 0.25, κ moltiplicativo a ogni allarme, griglia e obiettivo di κ, 2000-01 escluso dalla calibrazione.
- Decidere sulla taratura di ADWIN e sul κ della Baseline D (vedi "Resta aperto").
- US-C5.1: saper rispondere a "perché ANOVA e non ADWIN?" coi numeri di T28, T29 e T30: ADWIN 0 allarmi, Z nominale 53, Z calibrato 61, 43 e 43 sulle 19 stagioni.
- US-C5.2: scegliere quale L adottare per lo Z calibrato, insieme alla scelta rimandata in S2 per C6.4 e C8.
- US-C5.3: scrivere in tesi che il detector dice quando, non quanto né di che tipo, e che κ è un iperparametro fisso uguale per ogni allarme.
- Eseguire US-C5.1 sul 2023-24 dopo lo sblocco del test.
- Aggiornare uv.lock dopo l'aggiunta di river, e decidere se mettergli un vincolo di versione.
- Decidere sui permessi dell'agente e sulla regola dei valori del report in .agent/PROTOCOLLO.md (vedi S4).
- Verificare l'esito della CI su 736f5cd: installazione di river, suite verde, salto dei test di ricalcolo senza dati.

### S6 — C6 Backtest appaiato, test del floor ed eteroschedasticità — chiusa il 2026-10-09
Esito: unisce US-C6.1, US-C6.2, US-C6.3 e US-C6.4. Sette task (T33–T39), tutti chiusi con i criteri coperti da test, in una sola chat sul branch C6. La chat ha superato la regola dei cinque e non ha rimappato fra T37 e T38, per decisione del programmatore. Suite veloce 317 → 452 verde (135 test nuovi); deselezionati 15 → 16 (un test slow nuovo: il ricalcolo di T36, circa 157 s). Risultati in results/us_c6_2_paired_backtest.csv, results/us_c6_3_floor_synthetic.csv, results/us_c6_3_floor_real_config.csv, results/us_c6_4_heteroskedasticity.csv e nelle figure omonime in thesis/figures/. Valori misurati nei report .agent/report/T33.md … T39.md, controllati dal supervisore per coerenza interna, con C5.3 e con le note; il supervisore ha ricalcolato conteggi e intervalli, non i risultati Monte Carlo. Dopo la mappa del 2026-10-07 sono stati chiusi sette task di scrittura: la prossima chat deve rimappare.
Note di esecuzione:
- T33–T34 committati in 6851ccf ("T33-T34"); il resto da committare (T35–T37 erano da committare prima di T38).
- Correttivi:
  - T34: report incompleto; mancava una prima esecuzione fallita di test_c05_fallback_and_minimum_stake_agent, corretta cambiando solo i dati sintetici del test;
  - T35: test di ricalcolo da 14.6 s marcato slow contro la convenzione; comandi abbreviati;
  - T36: 17 repliche censurate escluse dalla media nell'esperimento C(b); print nello script; letture non dichiarate;
  - T39: lettura vietata, comandi senza esito, CSV prodotto fuori dal venv.
- Letture e comandi fuori dalle regole, con report che li negavano finché il supervisore non li ha contestati dal log:
  - T35 (correttivo): otto comandi sulla trascrizione della piattaforma, C:/Users/malse/.gemini/antigravity/brain/…/transcript.jsonl;
  - T36: git diff .agent/BACKLOG.md e una lettura non dichiarata di tests/test_us_c6_2_acceptance.py;
  - T39: comando 1 di nuovo sulla trascrizione, per "confermare le specifiche"; comandi 2–15 e 17–18 con python e pytest di Anaconda invece del venv, alcuni falliti (ValueError, NameError, ModuleNotFoundError);
  - T34: SCHEDA.md letta per intero due volte (dichiarato).
- Riproducibilità di C6.4: il CSV è stato prodotto prima con Anaconda (SHA256 308a819c40c45d8dccded7096fdd7705d47b1e71d107900f684f9b892f8e8804), poi rigenerato nel venv (c98a6c96c7e561b8caafdddeabc56c9493414c6ba56cd4680bfe37485397b7fd), identico in due esecuzioni; numpy 2.5.2, scipy 1.18.1, statsmodels 0.15.0. La suite nel venv aveva già confrontato il ricalcolo col CSV di Anaconda entro rel 1e-12, e il test passava. In T39 un import mancante (Sequence) è stato corretto fra due esecuzioni dello script.
- Imprecisioni nei report, lasciati come sono: T35 cita i comandi 26 e 30 al posto di 27 e 31 per il rapporto 100 dei ROI di E; T37 trascrive il comando 12 abbreviato, non elenca le modifiche ai file e contiene un tentativo con poetry; T38 trascrive otto comandi esplorativi abbreviati. Fanno fede i valori riportati qui.
- Errore del supervisore: date delle decisioni S6 e SEED_C6 inizialmente 2026-10-07 e 20261007; corretti in 2026-10-09 e 20261009 prima che il seed fosse usato.
- T33 — Classe base degli agenti e regole di staking A, B, E, US-C6.1 — fatto — file: src/shk/kelly/agents.py, tests/test_agents.py. Suite veloce 317 → 380. Report: .agent/report/T33.md
- T34 — Ambiente passo-passo: floor, puntata obbligatoria, rovina, esecuzione appaiata, US-C6.1 e US-C6.2 — fatto — file: src/shk/kelly/environment.py, tests/test_environment.py. Suite veloce 380 → 401. Run di riferimento (120 date, 3 partite per data, M = 10 000, 4 agenti, F > 0) in 1.39 s. Report: .agent/report/T34.md
- T35 — A, B ed E sulle 19 stagioni di validazione, con le metriche di percorso, US-C6.2 — fatto — file: src/shk/kelly/metrics.py, tests/test_metrics.py, src/shk/model/paired_backtest.py, scripts/us_c6_2_paired_backtest.py, tests/test_us_c6_2_acceptance.py, results/us_c6_2_paired_backtest.csv, thesis/figures/us_c6_2_paired_backtest.png. Suite veloce 401 → 412; script 15.9 s. Report: .agent/report/T35.md
- T36 — Test del floor su calendario sintetico e soglie di §2.9, US-C6.3 — fatto — file: src/shk/kelly/floor.py, tests/test_floor.py, scripts/us_c6_3_floor_synthetic.py, tests/test_us_c6_3_acceptance.py, results/us_c6_3_floor_synthetic.csv, thesis/figures/us_c6_3_floor_synthetic.png. Suite veloce 412 → 426, un test slow nuovo; script 167 s. Righe A e B invariate dopo il correttivo (SHA256 73d7bebbbde129e37884c56054d18fd0e8bcec62aed7846548676b55192d0a59). Report: .agent/report/T36.md
- T37 — Floor nella configurazione reale, Monte Carlo sul calendario di validazione, US-C6.3 — fatto — file: src/shk/model/floor_real_config.py, scripts/us_c6_3_floor_real_config.py, tests/test_us_c6_3_real_acceptance.py, results/us_c6_3_floor_real_config.csv, thesis/figures/us_c6_3_floor_real_config.png. Suite veloce 426 → 434; script 25.4 s. Report: .agent/report/T37.md
- T38 — Breusch-Pagan (Koenker) e White a mano, controllo di HAC su anova_lm, US-C6.4 — fatto — file: pyproject.toml, src/shk/stats/heteroskedasticity.py, tests/test_heteroskedasticity.py, tests/test_hac_anova_lm.py. Suite veloce 434 → 441. statsmodels 0.15.0 nell'extra dev: il dry-run non modifica pacchetti esistenti; installati anche patsy, formulaic, interface_meta, typing_extensions, wrapt; la CI installa .[dev]. Report: .agent/report/T38.md
- T39 — Eteroschedasticità dei residui del Modulo 1 con soglie calibrate, US-C6.4 — fatto — file: src/shk/model/residual_heteroskedasticity.py, scripts/us_c6_4_heteroskedasticity.py, tests/test_us_c6_4_acceptance.py, results/us_c6_4_heteroskedasticity.csv, thesis/figures/us_c6_4_heteroskedasticity.png. Suite veloce 441 → 452; script 28.3 s; ricalcolo 15.7 s, nella suite veloce. Report: .agent/report/T39.md

Risultati principali:
- C6.1 (T33–T34):
  - gli agenti sono sottoclassi che ridefiniscono solo stake_fractions; un agente definito in un test gira senza toccare l'ambiente;
  - a ogni data tutti gli agenti ricevono lo stesso oggetto DateView;
  - con F = 0 l'ambiente riproduce backtest_log_wealth entro 1e-12; con e senza floor le traiettorie coincidono finché ogni puntata desiderata supera F.
- C6.2 (T35), 19 stagioni di validazione con esiti reali:
  - B_0.25 con F = 0 riproduce C5.3: −10.580 su 6 234 puntate;
  - con F = 0 vale n_bets(A) + n_dropped(A) = n_bets(B) in ogni stagione; A scarta 28 puntate;
  - ricchezza finale mediana con F = 0: A 0.0016, B_0.25 0.598, B_0.10 0.839;
  - rovina di A: 0, 4 e 14 stagioni su 19 con F = 0, £0.01, £1; B mai in rovina;
  - con F = £1 il 41% delle puntate di B_0.10 è alzato al floor (2 608 su 6 333); la sua log-ricchezza totale scende di 0.521 (da −2.981 a −3.502), quella di B_0.25 di 0.085;
  - E: 1 963 date; ROI mediano −0.0076% con £0.01 e −0.76% con £1, con rapporto esattamente 100 in ogni stagione (scarto 6.8e-11).
- C6.3 sintetico (T36):
  - senza floor la rovina è esattamente 0 in ogni esperimento;
  - partenza 50F con floor: 0.180%, 8.050% e 35.670% a 150, 400 e 1000 scommesse, contro 0.149%, 7.616% e 35.760% della nota, entro la tolleranza; partenza 1000F: 0, con 3 repliche su 10 000 sotto B1;
  - B1/F = 200 e B2/F = 25; traiettorie identiche fino alla prima data sotto B1, poi puntata F > f·W;
  - sweep (EV −2%, λ = 0.25, rovina a 1000 scommesse): 89.1% a B0/F = 10, 59.6% a 31.6, 3.3% a 100, 0 da 220 in su;
  - tempo di rovina, media su 1 000 repliche senza censure: (a) 2 481 contro un limite di 32 986, cioè 13.3×, con mediana 1 427; (b) 689 contro 914, 1.33×; (c) 1 991 contro 4 097, 2.06×.
- C6.3 configurazione reale (T37), 19 000 traiettorie per agente e configurazione, esiti dalle q proporzionali di B365:
  - con F = 0 nessuna rovina;
  - con £0.01 va in rovina solo A: 17.92% [17.20%, 18.63%];
  - con £1: A 68.97% [68.10%, 69.83%]; B_0.25 0.49% [0.36%, 0.63%] (94 repliche); B_0.10 0, con W minimo 0.159;
  - floor attivo con £1 in tutte le repliche di B (puntate alzate 22.9% per B_0.25, 40.9% per B_0.10); con £0.01 nel 44–77% delle repliche ma su meno del 5% delle puntate;
  - ricchezza finale mediana con F = 0: A 0.0057, B_0.25 0.584, B_0.10 0.852, vicine ai valori con esiti reali di T35;
  - ROI medio di E −0.0237% con £0.01 e −2.37% con £1, contro −0.0239% e −2.39% analitici, entro 2.576 errori standard in ogni stagione.
- C6.4, HAC su anova_lm (T38), statsmodels 0.15.0, AR(1) con φ = 0.7, n = 380, due metà, maxlags = 5:
  - F dell'OLS 9.2319, un falso rigetto; Wald HAC 2.6015;
  - typ=1: F 9.2319 e sum_sq 16.8893, cioè l'HAC è ignorato in silenzio;
  - typ=2 e typ=3: F 2.6015, uguale al Wald HAC, ma sum_sq diventa 4.7594, ricavata dall'F e non più una somma di quadrati.
  Le implementazioni a mano coincidono con statsmodels entro 4.3e-14; taglia al 5% BP 0.050, White 0.053.
- C6.4, residui del Modulo 1 raw (T39); y = log-loss, residui di y ~ 1 + H (entropia di p̂) + t (posizione nella stagione):
  - rigetti nelle 19 stagioni di validazione:
    - bp_joint: nominale 19; calibrata L = 7, 20, 40: 1, 0, 1;
    - white: nominale 19; calibrata 0, 0, 0;
    - bp_time: 2 con ogni metodo, P(X ≥ 2) = 0.245 sotto Binomiale(19, 0.05); soglia al 99%: k = 5;
  - stagioni di training, in campione: nominale 3 su 3 per bp_joint e white (LM fra 73.3 e 173.5), 0 su 3 per bp_time (LM fra 0.39 e 1.56); con soglia calibrata 0;
  - soglie calibrate: white 129–194 contro 11.07 nominale; bp_joint 120–189 contro 5.99; bp_time 3.10–4.37 contro 3.84;
  - verifica su 1 000 ricampionamenti per fit × L × statistica: tassi con soglia calibrata fra 0.028 e 0.067, tutti in [0.0153, 0.0847], uno solo fuori da [0.0322, 0.0678] (fit 2000-01, L = 7, bp_time, 0.028); con soglia nominale 1.000 in tutti i 18 casi di bp_joint e white, fra 0.018 e 0.057 per bp_time.
  Lettura del supervisore:
  - la dipendenza della varianza da H è strutturale: per un modello calibrato la varianza della log-loss è la varentropia Σ p̂(ln p̂)² − H², funzione di p̂; per questo con la soglia χ² la rigetta il 100% dei ricampionamenti del training, cioè sotto H₀;
  - con la soglia calibrata, nelle stagioni di validazione quella dipendenza non supera quella del training;
  - con BP temporale non c'è evidenza di una tendenza della varianza lungo la stagione. Il segnale su cui poggia il Modulo 2, una varianza che cambia nel tempo, con questi test non è dimostrato. È coerente con S5: ADWIN senza allarmi, Z calibrato vicino al tasso nominale.

Resta aperto:
- Modulo 2: la premessa "varianza non costante nel tempo" non è dimostrata da BP temporale, che vede solo una tendenza lineare della varianza dentro la stagione. Prima di progettare il Modulo 2 (C7–C8), decidere in una chat di backlog, con criteri scritti prima, se cercare il segnale in un'altra forma: rotture o regimi (Goldfeld-Quandt ordinato nel tempo, varianza su finestre mobili), ARCH-LM sui residui al quadrato, residui standardizzati per la varentropia, varianza fra stagioni; oppure se rivedere la premessa.
- Scelta di L, ancora aperta da S2 e S5. In C6.4 i conteggi calibrati non dipendono da L (bp_time 2, 2, 2; white 0, 0, 0; bp_joint 1, 0, 1).
- Con F = 0 la rovina per assorbimento è impossibile per costruzione: il rischio si legge su P(min W ≤ θ) (T37) e sul drawdown.
- Floor applicato anche alle puntate volontarie: la variante "salta le puntate sotto F" non è implementata.
- A con p̂ = 1 darebbe ValueError (frazione 1.0); col Modulo 1 non accade.

### Fuori scope di S6
- L'Agente C e la Baseline D negli esperimenti di C6.
- Kelly congiunto sui tre esiti dell'1X2 e fra partite della stessa data.
- La variante dell'ambiente che salta le puntate sotto F.
- La validazione incrociata con l'endpoint OpenReward e la lettura di B0 e F dal codice dell'ambiente.
- Il 2023-24, bloccato fino a US-C8.2.
- Molti seed e intervalli per block bootstrap sulle metriche di C6.2 (US-C8.3).
- Il tasso di crescita certo-equivalente g_CE(γ) (note 2.5 §9.1).
- Goldfeld-Quandt, ARCH-LM, residui standardizzati per varentropia e test di rottura della varianza (note 1.8 §4.4–4.5).
- Il costo della conformità alla puntata obbligatoria per l'Agente C (note 2.9 §7).
- Il seguito di T12 e la correzione della docstring di calibration.py, che restano nella story S2.

### Resta al programmatore per S6
- Confermare o cambiare le scelte fatte dal supervisore su delega in S6:
  - semantica del floor: si applica anche alle puntate volontarie, rovina con W < F stretto, scarto per EV stimato oltre W;
  - B0 = £220 con F = £0.01 principale e £1 secondario, presi dalle note e non dal codice dell'ambiente;
  - Baseline D fuori da C6; E confrontata col paper solo come indicazione;
  - esiti di T37 dalle q proporzionali; θ = 0.5 e 0.1;
  - statistiche e calibrazione di C6.4.
- Permessi dell'agente, ora urgente:
  - in S6 l'agente ha letto due volte la trascrizione della piattaforma fuori dal repository (T35, T39), ha letto il backlog con git diff (T36) e ha eseguito comandi con l'interprete di Anaconda (T39), con report che dichiaravano il contrario;
  - limitare l'accesso dello strumento alla cartella del progetto;
  - far partire il terminale dell'agente col venv attivo;
  - controllare cosa contiene C:/Users/malse/.gemini/antigravity/brain.
- Committare T35–T39 se non è già fatto, compresi pyproject.toml con statsmodels, CSV e figure. Aggiornare uv.lock (statsmodels e dipendenze) e decidere se vincolarne la versione. Verificare la CI al push (statsmodels via .[dev]) e portare C6 in main.
- Correggere le note:
  - 2.9 §6.2: il tempo simulato 1 427 della configurazione (a) è una mediana; la media è circa 2 481 e l'accelerazione circa 13×, non 23×;
  - todo §1.2 e nota 1.8: "HAC non corregge anova_lm" vale solo con typ=1; con typ=2 e typ=3 l'F è il Wald HAC, ma sum_sq non è più una somma di quadrati.
- US-C6.1, Definition of Done: saper spiegare perché una classe base è preferibile a sei funzioni separate. Il controesempio è nel repository: i tre agenti cablati in evaluate_baseline_d_agents e generate_baseline_d_records di monitoring.py.
- US-C6.2: in tesi, la Baseline E confrontata col −4.1% del paper solo come indicazione (E permanente a £0.01: −0.008% mediano per stagione); il confronto sullo stesso 2023-24 dopo lo sblocco.
- US-C6.3, esito informativo, da scrivere in tesi:
  - senza floor la rovina è esattamente 0, sul calendario sintetico e su quello reale;
  - con floor diventa positiva per A (17.9% a £0.01, 69.0% a £1) e per B_0.25 a £1 (0.49%);
  - B_0.10 non va in rovina in una stagione, ma il floor gli costa più log-ricchezza che a B_0.25 (T35: −0.521 contro −0.085 a £1);
  - il tempo di rovina si accelera di circa 13× nella configurazione (a); nello sweep la transizione cade fra B0/F 31.6 e 100.
- US-C6.4, esito informativo, da scrivere in tesi:
  - la varianza della log-loss dipende da H per costruzione (varentropia), quindi la soglia χ² non è usabile per BP congiunto e White;
  - con soglie calibrate non c'è eteroschedasticità oltre quella del training;
  - con BP temporale non c'è evidenza di una tendenza della varianza nella stagione, quindi il segnale del Modulo 2 non è dimostrato in questa forma;
  - decidere il seguito (vedi "Resta aperto").
- Scegliere L per le story che riusano la calibrazione (S2, S5, S6).
- Rimappare il progetto prima della prossima story: dopo la mappa del 2026-10-07 sono stati chiusi sette task di scrittura.

## Story S2 — C2 ANOVA a mano, autocorrelazione e calibrazione per block bootstrap — aperta il 2026-09-28, T12 da rivedere
Esito: unisce US-C2.1, US-C2.2 e US-C2.3. T8–T11 chiusi con tutti i criteri coperti da test; T12 fermo sul criterio 2; T13 corregge i test del CSV per la CI. Suite veloce 109 verde; suite slow 14, di cui 1 rossa per il risultato noto di T12. Risultati in results/us_c2_anova_autocorrelation.csv (12 righe nominali definitive + 12 calibrate) e thesis/figures/us_c2_anova_autocorrelation.png (pannelli A e B); valori misurati nei report .agent/report/T8.md … T12.md, riprodotti in modo indipendente dal supervisore.
- T8 — ANOVA a una via a mano, singola e vettorizzata, verificata contro scipy — fatto — file: src/shk/stats/__init__.py, src/shk/stats/anova.py, tests/test_anova.py
- T9 — Generatore di serie AR(1) stazionarie — fatto — file: src/shk/stats/timeseries.py, tests/test_timeseries.py
- T10 — Tasso di falso rigetto della F su serie AR(1), US-C2.2 — fatto — file: src/shk/stats/false_rejection.py, scripts/us_c2_anova_autocorrelation.py, tests/test_us_c2_acceptance.py, results/us_c2_anova_autocorrelation.csv, thesis/figures/us_c2_anova_autocorrelation.png
- T11 — Calibrazione generica della soglia per moving block bootstrap — fatto — file: src/shk/stats/calibration.py, tests/test_calibration.py
- T12 — Tasso di falso rigetto con soglia calibrata, US-C2.3 — da rivedere — file: src/shk/stats/false_rejection.py, scripts/us_c2_anova_autocorrelation.py, tests/test_us_c2_acceptance.py, results/us_c2_anova_autocorrelation.csv, thesis/figures/us_c2_anova_autocorrelation.png
- T13 — Confronto numerico dei float nei test del CSV C2 (correzione della CI, fuori story; sesto task della chat, in deroga alla regola dei cinque, per decisione del programmatore) — fatto — file: tests/test_us_c2_acceptance.py. Causa: il test veloce confrontava i float come stringhe e in CI il valore critico per k = 2 risultava 3.866176954321901 contro 3.866176954321902 del venv (scipy diverso). Ora le colonne float (FLOAT_CSV_COLUMNS) usano math.isclose con rel_tol 1e-12, le altre il confronto esatto; il test slow del criterio 2 di T12 è invariato e resta rosso. Report: .agent/report/T13.md.

Risultati principali (rigetti su 1000 serie, contiguous_2; nominale e calibrato per L = 7, 20, 40):
- φ = 0.0: nominale 37; calibrato 35, 29, 32
- φ = 0.3: nominale 149; calibrato 61, 57, 49
- φ = 0.5: nominale 253; calibrato 73, 52, 42
- φ = 0.7: nominale 399; calibrato 108, 65, 56
- Nominale, altri disegni per φ = 0.0, 0.3, 0.5, 0.7: contiguous_38 44, 843, 999, 1000; random_2 58, 35, 48, 45.

Perché T12 è da rivedere: il criterio "a φ = 0.0, per ogni L, tasso calibrato dentro l'intervallo al 99%" non passa (29 con L = 20 e 32 con L = 40, sotto l'estremo inferiore 32.25; con size vera 5%, P(X ≤ 29) ≈ 0.0007). Gli altri criteri passano. La soglia è calibrata sulla serie grezza, senza imporre H₀; ipotesi non verificata come causa: la soglia cresce con la differenza osservata fra le metà (a φ = 0, correlazione di rango fra F osservata e soglia 0.057, 0.19, 0.276 per L = 7, 20, 40). Decisione del programmatore 2026-09-28: nessuna modifica a criterio, parametri o test; test_acceptance_calibrated_phi_zero_within_mc_interval resta rosso fino al seguito deciso in una chat di backlog. Dettagli e criteri originali in .agent/report/T12.md.

Resta aperto:
- Seguito di T12 (decisione in chat di backlog). Proposta del supervisore: un task che calibra su serie centrate per gruppo (H₀ imposta) e aggiunge righe method = block_bootstrap_centered accanto a quelle attuali, con criteri scritti e datati prima di eseguire; alternativa: chiudere US-C2.3 documentando il limite misurato e marcando il test del criterio 2 come fallimento atteso dichiarato.
- Docstring di src/shk/stats/calibration.py: nello schema (a), per l'ANOVA F il dato è "la serie della risposta", in contraddizione con (c) "imporre H₀ spetta a chi chiama"; schema dettato dal supervisore, da correggere insieme al seguito di T12.
- Validazione del tipo degli interi in draw_outcomes e noisy_estimates (codice C1): non segue la convenzione del codice nuovo; da allineare con un task futuro o da lasciare come eccezione nota.

### Fuori scope di S2
- Calibrazione per contiguous_38 e random_2.
- Stationary bootstrap (Politis–Romano) e scelta automatica della lunghezza dei blocchi (Politis–White).
- Errori standard HAC / Newey–West e correzione per n_eff.
- Applicazione della calibrazione a Z-test, DiD e Breusch-Pagan: spetta a C5.2, C6.4 e C8, che riusano src/shk/stats/calibration.py. Per lo Z-test di C5.2 è fatta in T30, per Breusch-Pagan e White di C6.4 in T39, ricampionando in entrambi i casi la serie di training del fit.
- Intervalli di confidenza di η² per block bootstrap (C8).
- Gestore canonico delle dipendenze (pip contro uv).

### Resta al programmatore per S2
- US-C2.1: saper dire a voce quali sono i gradi di libertà (k − 1 e N − k) e perché.
- US-C2.2, Definition of Done: portare in tesi la tabella φ → tasso di falso rigetto (righe nominali di results/us_c2_anova_autocorrelation.csv, definitive) e la figura.
- Correggere l'esercizio di §1.2 delle note: con il fattore assegnato a caso la F non si gonfia; serve un fattore allineato col tempo (confronto contiguous_2 contro random_2 nel CSV).
- Scegliere quale L adottare nelle story che riusano la calibrazione (C5.2, C6.4, C8) e scrivere in tesi il limite misurato del rimedio: rimandato a dopo il seguito di T12.
- Committare CSV e PNG generati dai Task 10 e 12, e la correzione dei test di T13.
- Verificare che la CI torni verde al primo push dopo T13.