# Backlog
Ultimo task: T32

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
- S5 in una sola chat di esecuzione fino a T32, in deroga alla regola dei cinque task, per decisione del programmatore; la chat successiva dovrà rimappare (contatore a 7) — S5, 2026-09-30
- Nei CSV di S5 il blocco di 10 partite si chiama matchday (colonna e valore di row_type), non giornata, per la convenzione dell'inglese negli identificatori; le etichette delle figure restano in italiano — S5, 2026-09-30

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
- Confermare o cambiare le scelte fatte dal supervisore su delega il 2026-09-29:
  - q con serie principale B365 pre-partita e seconda serie Pinnacle chiusura dal 2012-13;
  - calibrazione espansiva di K, h, ν e della ricalibrazione;
  - retrocesse identificate dalla classifica calcolata (nel 1996-97 dà Coventry al posto del Middlesbrough);
  - limite [1e-6, 1 − 1e-6] nella ricalibrazione.
- Correggere o dichiarare la tabella di Davidson delle note 2.8 §3.3: è calcolata con 10^(ΔR/200), mentre il modello usa la scala 400 del punteggio atteso.
- US-C4.2, esito informativo: scrivere l'introduzione della tesi in base al segno di ĝ, negativo in tutti i casi, dichiarandolo in apertura e non nei limiti (note 2.4 §6).
- Dichiarare in tesi: il mapping Davidson e la sensibilità rispetto alla baseline a pareggio costante; la regola per le neopromosse; lo schema espansivo degli iperparametri.
- US-C4.3: decidere se serve una ricalibrazione e quale adottare, isotonica o Platt, da congelare. Log-loss di validazione raw / Platt / isotonica: 0.9795 / 0.9823 / 1.0139 su B365, 0.9812 / 0.9809 / 0.9914 su Pinnacle.
- Decidere sull'accesso dell'agente ai file fuori dal repository: lasciarlo com'è, oppure limitarne i permessi alla cartella del progetto e aggiungere il divieto alle "Convenzioni del progetto" di .agent/PROTOCOLLO.md. Controllare che le 50 righe della cronologia di PowerShell lette in T24 non contenessero credenziali.
- Decidere se aggiungere alle "Convenzioni del progetto" di .agent/PROTOCOLLO.md la regola "ogni valore numerico del report viene da un comando elencato".
- Rimappare il progetto prima della prossima story: dopo la mappa del 2026-09-29b sono stati chiusi cinque task di scrittura.
- Committare codice, CSV e figure di T24 (T20–T23 sono in 7f8e928, 4710045, 15b2204, d329766), verificare la CI al primo push del branch C4 e portare C4 in main.
- Committare T25 (T20–T24 sono in 7f8e928, 4710045, 15b2204, d329766, dc9d8f2), verificare che la CI del branch C4 sia verde e portare C4 in main. Con la CI verde, cambiare lo stato di T25 da "in corso: manca la verifica della CI" a "fatto".

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
- Applicazione della calibrazione a Z-test, DiD e Breusch-Pagan: spetta a C5.2, C6.4 e C8, che riusano src/shk/stats/calibration.py.
- Intervalli di confidenza di η² per block bootstrap (C8).
- Gestore canonico delle dipendenze (pip contro uv).

### Resta al programmatore per S2
- US-C2.1: saper dire a voce quali sono i gradi di libertà (k − 1 e N − k) e perché.
- US-C2.2, Definition of Done: portare in tesi la tabella φ → tasso di falso rigetto (righe nominali di results/us_c2_anova_autocorrelation.csv, definitive) e la figura.
- Correggere l'esercizio di §1.2 delle note: con il fattore assegnato a caso la F non si gonfia; serve un fattore allineato col tempo (confronto contiguous_2 contro random_2 nel CSV).
- Scegliere quale L adottare nelle story che riusano la calibrazione (C5.2, C6.4, C8) e scrivere in tesi il limite misurato del rimedio: rimandato a dopo il seguito di T12.
- Committare CSV e PNG generati dai Task 10 e 12, e la correzione dei test di T13.
- Verificare che la CI torni verde al primo push dopo T13.

## Story S5 — C5 Drift detector standard: ADWIN e Page-Hinkley, Z-test per giornata, Baseline D
Aperta il 2026-09-29.

**Interpretazione:** far girare ADWIN e Page-Hinkley di river sulla log-loss per partita del Modulo 1, tarati sul training, e registrare quando scattano su ogni scenario; misurare i falsi allarmi dello Z-test per giornata, con soglia nominale e con soglia calibrata per block bootstrap, accanto a quelli dei due detector; costruire la Baseline D, Kelly frazionario che riduce la frazione a ogni allarme con κ calibrato sul training e congelato, ed eseguirla in modo appaiato. Unisce US-C5.1, US-C5.2 e US-C5.3 in una sola story di sette task (T26–T32), per decisione del programmatore del 2026-09-29, in deroga alla regola dei cinque.

**Assunzioni fatte:**
- Scelte del supervisore su delega, da confermare: le tre domande del 2026-09-29 sono rimaste senza risposta e il programmatore ha chiesto di procedere.
  - Modulo 1 in versione raw, senza ricalibrazione: è la migliore su B365 per log-loss, Brier e ĝ [V, R29@2026-09-29b].
  - "Cinque scenari": ora i tre scenari di training (2000-01, 2010-11, 2020-21) e, in più, le 19 stagioni di validazione. Il 2023-24 resta un criterio aperto, da eseguire dopo lo sblocco del test (US-C8.2); la variante literature non è ricostruibile da football-data (fuori scope di S3).
  - Soglia calibrata dello Z-test: moving block bootstrap della serie di log-loss di training del fit, cioè della serie che definisce la baseline dello Z. H₀ vale per costruzione, perché si ricampiona il riferimento e non la stagione sotto test: il problema di T12 non si presenta [D, ragionamento del supervisore]. src/shk/stats/calibration.py si riusa senza modificarlo; il seguito di T12 resta nella story S2.
- Serie: log-loss per partita, −ln p̂(esito realizzato), delle previsioni walk-forward con ELO_FITS. Le partite di uno scenario di training j si prendono dal fit che termina in j (lo stesso di C4.1, con gli iperparametri stimati anche su j); le partite di validazione dal fit delle stagioni di training strettamente anteriori (decisione S4).
- Giornata: blocco contiguo di 10 partite nell'ordine cronologico stabile della stagione (decisione S2, disegno contiguous_38). Tutte le stagioni usate hanno 380 partite, cioè 38 giornate [V, R10@2026-09-29].
- Z-test per giornata: Z = (media della log-loss delle 10 partite − μ_f) / (σ_f / √10), con μ_f e σ_f (ddof = 1) calcolate sulle partite di training del fit f che prevede la stagione; allarme nominale se |Z| > z_0.975 (α = 0.05); atteso nominale 38 × 0.05 = 1.9 allarmi per stagione.
- "Stagione senza drift noto": ciascuna delle 19 stagioni di validazione, con conteggio per stagione e media; nessuna stagione viene scelta dopo averne visto l'esito.
- Detector: un'istanza nuova per ogni stagione, alimentata nell'ordine cronologico con la log-loss di tutte le partite; un allarme è un aggiornamento in cui river segnala drift. Parametri scelti su una griglia fissata nel testo di T27, prima dei risultati: vince la combinazione il cui numero medio di allarmi su 2000-01 e 2010-11 è più vicino a 1.9, cioè allo stesso tasso di falsi allarmi dello Z nominale (note 1.9 §10). Il 2020-21 resta fuori dalla taratura perché ha un drift noto (COVID).
- river fra le dipendenze runtime di pyproject.toml senza vincolo di versione, come pandas (decisione S3); uv.lock lo aggiorna a mano il programmatore.
- Baseline D (scelte del supervisore su delega, da confermare):
  - per ogni partita si punta al più su un esito, quello con p̂·o − 1 massimo se positivo, con frazione kelly_staking(p̂, o − 1, λ_t); quote B365 pre-partita non de-viggate; p̂ del Modulo 1 raw;
  - λ_t vale 0.25 a inizio stagione (quarto-Kelly, decisione S1) ed è moltiplicato per κ a ogni allarme; un allarme su una partita della data d cambia λ solo per le partite con Date > d (stessa regola dell'anti-leakage di S3);
  - bankroll 1 a inizio di ogni stagione; le puntate della stessa data si decidono sul bankroll di inizio data e si regolano insieme;
  - κ ∈ {0, 0.25, 0.5, 0.75, 1}, scelto per ciascun detector massimizzando la somma della log-ricchezza finale di 2010-11 e 2020-21; a parità vince il κ più grande. κ = 1 coincide col quarto-Kelly senza detector;
  - il 2000-01 non entra nella calibrazione di κ perché non ha B365 [V, R14@2026-09-29]. La scheda dice "C5 non usa le quote di training": per US-C5.3 non vale;
  - esecuzione appaiata, per ora, fra D-ADWIN, D-Page-Hinkley e il riferimento κ = 1, sulle 19 stagioni di validazione; gli agenti A, B ed E arrivano con C6.
- Nessun task di sola ricognizione: ogni voce [D] riguarda un solo task e sta nella sua riga "Da verificare prima di iniziare", per decisione del programmatore sul numero di task.
- Fatti [V] su cui non si fa verificare nulla: ELO_FITS congelato [V, R23@2026-09-29b]; split congelato, read_split_config e load_by_role [V, R26@2026-09-29 e R1@2026-09-29c]; log-loss di C4.1 e C4.2 [V, R23 e R26@2026-09-29b]; firme di calibration.py [V, R12@2026-09-28 e R1@2026-09-29c]; costanti di false_rejection.py [V, R13 e R14@2026-09-28].

**Domande aperte:** nessuna bloccante. Le scelte su delega qui sopra vanno confermate dal programmatore.

### Task 26 — Serie di log-loss per partita del Modulo 1
Stato: fatto

Obiettivo: una funzione di libreria in src/shk/model/residuals.py restituisce la log-loss per partita del Modulo 1 raw, per le partite di training di ciascun fit e per le stagioni di validazione, in ordine cronologico stabile, e riproduce le log-loss medie di C4.1.

Dipende da: nessuno.

Contesto:
- Modulo 1 Elo con parametri congelati in ELO_FITS (src/shk/model/elo_fit.py), fit "2000-01", "2010-11", "2020-21" [V, R23@2026-09-29b]. derive_fit_schedule(training, validation) dà per ogni fit le stagioni di training ≤ j e le stagioni di validazione che prevede [V, R1@2026-09-29c]: il fit 2000-01 prevede dal 2002-03 al 2009-10, il 2010-11 dal 2011-12 al 2019-20, il 2020-21 il 2021-22 e il 2022-23 [D, dai conteggi di C4.1].
- src/shk/model/scoring.py: compute_log_loss (puntuale), generate_validation_predictions(df, fits, schedule) alla riga 218, che chiama predict_elo_fast con i parametri di ciascun fit [V, R1@2026-09-29c].
- src/shk/model/elo_fit.py: compute_training_log_loss → (loss, preds) [V, R1@2026-09-29c]. src/shk/model/recalibration.py: generate_fit_training_predictions alle righe 322-337 [V l'esistenza, R1@2026-09-29c; D il comportamento].
- Probabilità del Modulo 1: matrici (N, 3) in ordine H, D, A, righe a somma 1, previsioni walk-forward prima dell'aggiornamento della stessa data [V, R1@2026-09-29c]. Le metriche di scoring.py non usano eps: una probabilità ≤ 0 per l'esito realizzato dà ValueError [D].
- Dati reali solo con read_split_config e load_by_role ("history", "training", "validation") di src/shk/data/split.py, come negli script C4 [V, R1@2026-09-29c]. Il ruolo "test" è bloccato e non si legge.
- Valori di riferimento, riportati con sei decimali [V, R23 e R26@2026-09-29b]: log-loss media di training 1.008189 (fit 2000-01, 380 partite), 1.008987 (fit 2010-11, 760), 1.020937 (fit 2020-21, 1 140); di validazione 0.973761 (3 040), 0.983832 (3 420), 0.983300 (760); sulle 7 220 partite di validazione insieme 0.979536.
- results/us_c4_1_elo_walkforward.csv ha 15 colonne e 9 500 righe [V, R1@2026-09-29c]; che siano le 2 280 righe di training dei tre fit più le 7 220 di validazione è dedotto dal conteggio [D].

Da verificare prima di iniziare:
- che cosa restituiscono compute_training_log_loss e generate_fit_training_predictions (colonne, ordine, fit di appartenenza), e se una delle due dà già le previsioni di training per partita;
- quali colonne restituisce generate_validation_predictions e da quale colonna si ricava l'esito realizzato;
- il contenuto di results/us_c4_1_elo_walkforward.csv, solo in lettura.

Passi richiesti:
1. Verificare le voci qui sopra leggendo il codice, senza eseguire nulla, e riportarle nel piano.
2. Proporre il piano: nome e firma della funzione, colonne restituite, funzioni esistenti riusate.
3. Creare src/shk/model/residuals.py con una funzione che, dati i dati caricati e lo schedule, restituisce un DataFrame con almeno le colonne season, Date, HomeTeam, AwayTeam, fit_through, role ("training" o "validation"), p_home, p_draw, p_away, FTR e log_loss = −ln della probabilità dell'esito realizzato. Una partita di training compare una volta per ogni fit che la include. Righe ordinate per fit, ruolo e ordine cronologico stabile.
4. Validazioni in apertura di funzione.
5. Scrivere tests/test_residuals.py: test sintetici (colonne, ordine, log_loss uguale a −ln p calcolato a mano su poche righe, validazioni) e test sui dati reali contro i valori di riferimento, saltati senza dati.
6. Eseguire la suite veloce.

Vincoli:
- Non modificare elo.py, elo_predictor.py, elo_fit.py, scoring.py, recalibration.py: una modifica che cambia previsioni o metriche rende incoerenti ELO_FITS e i CSV di C4. Non modificare calibration.py, false_rejection.py né config/split.toml.
- Modulo 1 in versione raw: nessuna ricalibrazione.
- Nessun commit e nessuna operazione git che modifichi lo stato del repository: i commit li fa il programmatore a mano.
- Commenti e docstring in italiano; identificatori, messaggi delle eccezioni e nomi dei test in inglese. Non è un'incoerenza: è la convenzione.
- Rispettare le eventuali convenzioni aggiuntive della sezione "Convenzioni del progetto" di .agent/PROTOCOLLO.md.
- Prima di scrivere codice, proporre il piano e fare le domande necessarie; nessun comando Python prima dell'approvazione del piano.
- Ogni comando Python con .\.venv\Scripts\python.exe dalla radice del repository.
- Codice: type hints completi; docstring in stile NumPy (Parametri / Restituisce / Solleva); TypeError per i tipi e ValueError per i valori, in apertura di funzione; interi bool o float → TypeError; nessun try:, print( o logging in src/ e scripts/.
- Dati reali solo con read_split_config e load_by_role; load_all_seasons non si usa; il ruolo "test" non si legge.
- Test sui dati reali saltati con motivo esplicito tramite _has_real_data o una condizione equivalente su DEFAULT_DATA_DIR; marcati slow se superano 60 s, e dichiarati nel report.
- Non leggere né scrivere file fuori dal repository.
- A fine task, scrivere il report in .agent/report/T26.md, unico file di .agent/ che si può toccare, con in sezioni distinte: percorsi dei file modificati, creati o rimossi; esito di ciascun criterio di accettazione; valori misurati; deviazioni dal piano; cose non fatte; comandi eseguiti. Fatti e valori senza giudizi; interpretazioni solo in una sezione a parte, e solo se richieste. Ogni valore numerico del report viene da un comando elencato.

Criteri di accettazione:
- Sui dati reali, righe di training per fit 380, 760 e 1 140, e righe di validazione 3 040, 3 420 e 760.
- Log-loss media per fit e ruolo uguale ai valori di riferimento entro 5e-7 (i riferimenti hanno sei decimali); sulle 7 220 righe di validazione 0.979536 entro 5e-7.
- log_loss finita e positiva su tutte le righe; ordine cronologico stabile per fit e ruolo.
- Nessuna lettura del ruolo "test"; il test di guardia di tests/test_split.py resta verde.
- Test sintetici verdi anche senza dati; test sui dati reali saltati con motivo esplicito senza dati; suite veloce tutta verde.

Esito: 2026-09-30 — file toccati: src/shk/model/residuals.py, tests/test_residuals.py (entrambi creati; nessun file esistente modificato). Funzione compute_model_residuals(df, schedule, fits=None), con fits=None → ELO_FITS; costante RESIDUALS_COLUMNS; 11 colonne in ordine fit_through, role, season, Date, HomeTeam, AwayTeam, p_home, p_draw, p_away, FTR, log_loss; Date col dtype di df. Previsioni di training dalle preds di compute_training_log_loss, di validazione da generate_validation_predictions (fit_through da schedule); FTR con align_predictions_with_odds; log_loss con compute_log_loss. 9 test: 5 sintetici; 4 sui dati reali, tramite una fixture scope="module" che senza CSV chiama pytest.skip("Real data in data/raw/E0 not available"). _has_real_data è definita localmente, come negli altri moduli di test; tests/conftest.py non esiste. Deviazioni: alla prima esecuzione i 5 test sintetici fallivano (EloFitParams istanziato senza c); corretti, e le assegnazioni di colonna in residuals.py sono state riscritte con .assign su copie per eliminare dei PerformanceWarning. In ricognizione (R2) l'agente ha letto due log della piattaforma fuori dal repository (C:\Users\malse\.gemini\antigravity\brain\…\transcript.jsonl e transcript_full.jsonl), perché il messaggio gli era arrivato troncato di 277 byte; da allora nessuna lettura esterna. Non fatto: nessuno; il salto dei test senza dati è verificato leggendo il codice, e in esecuzione lo verificherà la CI. Valori misurati: righe di training 380 / 760 / 1 140, di validazione 3 040 / 3 420 / 760, totale 9 500; log-loss media di training 1.00818933 / 1.00898737 / 1.02093662, di validazione 0.97376082 / 0.98383215 / 0.98330012, aggregata 0.97953559 (scarto massimo dai riferimenti 4.1e-7); media di training uguale alla loss di compute_training_log_loss entro 1e-12; compute_model_residuals sui dati reali 1.70 s; suite veloce 257 verdi, 15 deselezionati, 45.36 s. Report: .agent/report/T26.md.

### Task 27 — ADWIN e Page-Hinkley da river, tarati sul training
Stato: fatto

Obiettivo: src/shk/stats/drift.py esegue ADWIN e Page-Hinkley importati da river su una serie di log-loss e ne restituisce gli allarmi; i parametri dei due detector sono scelti sul training con la griglia e la regola fissate qui, e congelati in costanti.

Dipende da: T26.

Contesto:
- river non è fra le dipendenze di pyproject.toml [V, R1@2026-09-29c]; se sia installato nel .venv non è verificato [D]. Le dipendenze non hanno vincoli di versione, pyproject.toml è la fonte di verità e la CI installa con pip install -e ".[dev]" ignorando uv.lock [V, R1@2026-09-29c].
- In src/shk/ non c'è nessun modulo di drift detection [D, dall'elenco dei moduli di R1@2026-09-29c]. Il codice statistico sta in src/shk/stats/ (decisione S2); src/shk/stats/__init__.py contiene solo una docstring [V, R5@2026-09-28].
- La log-loss per partita la dà la funzione di T26 in src/shk/model/residuals.py.
- Target della taratura: 1.9 = 38 × 0.05, gli allarmi attesi in una stagione dallo Z-test nominale per giornata.

Da verificare prima di iniziare:
- se river è installato nel .venv e in quale versione;
- nella versione installata: nomi delle classi (river.drift.ADWIN, river.drift.PageHinkley), parametri e valori di default, metodo di aggiornamento e attributo che segnala il drift, parametro mode di PageHinkley e suo default;
- l'esito di T26: nome della funzione e colonne restituite.

Passi richiesti:
1. Verificare le voci qui sopra e riportare versione e API nel piano.
2. Proporre il piano, compresa l'eventuale installazione di river nel .venv con .\.venv\Scripts\python.exe -m pip, da eseguire solo dopo l'approvazione.
3. Aggiungere river alle dipendenze runtime di pyproject.toml, senza vincolo di versione. Non toccare uv.lock.
4. Creare src/shk/stats/drift.py con una funzione che esegue un detector su una serie 1D, con un'istanza nuova a ogni chiamata, e restituisce gli indici (base 0) degli aggiornamenti in cui river segnala drift.
5. Griglia, fissata qui e non modificabile: ADWIN con delta ∈ {0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 0.8} e gli altri parametri al default; Page-Hinkley con delta ∈ {0.005, 0.01, 0.05} per threshold ∈ {1, 2, 5, 10, 20, 50} e gli altri parametri al default della versione installata, da riportare nel report.
6. Taratura: per ogni combinazione, contare gli allarmi sulla log-loss delle partite della stagione 2000-01 (fit 2000-01) e della stagione 2010-11 (fit 2010-11, solo le partite di quella stagione), con un'istanza nuova per stagione. Scegliere, per ciascun detector, la combinazione con media dei due conteggi più vicina a 1.9; a parità, quella con meno allarmi totali; poi la prima nell'ordine della griglia.
7. Congelare in costanti di drift.py la griglia, il target e i parametri scelti.
8. Scrivere tests/test_drift.py:
   - sintetici: serie stazionaria contro serie con salto di media di 5 deviazioni standard a metà, con i parametri di default di river, e almeno un allarme dopo il salto; indici in [0, n); due chiamate sulla stessa serie danno lo stesso risultato; validazioni;
   - sui dati reali: la taratura ricalcolata dà i parametri congelati; saltato senza dati, slow se supera 60 s.
9. Eseguire la suite veloce.

Vincoli:
- ADWIN e Page-Hinkley si importano da river e non si reimplementano.
- Griglia, target e regola di scelta non si cambiano dopo aver visto i risultati.
- In questo task non si fanno girare i detector sul 2020-21, sulle stagioni di validazione né sul 2023-24.
- Non modificare i moduli di src/shk/model/ né calibration.py, false_rejection.py e config/split.toml.
- Nessun commit e nessuna operazione git che modifichi lo stato del repository: i commit li fa il programmatore a mano.
- Commenti e docstring in italiano; identificatori, messaggi delle eccezioni e nomi dei test in inglese. Non è un'incoerenza: è la convenzione.
- Rispettare le eventuali convenzioni aggiuntive della sezione "Convenzioni del progetto" di .agent/PROTOCOLLO.md.
- Prima di scrivere codice, proporre il piano e fare le domande necessarie; nessun comando Python prima dell'approvazione del piano.
- Ogni comando Python con .\.venv\Scripts\python.exe dalla radice del repository.
- Codice: type hints completi; docstring in stile NumPy (Parametri / Restituisce / Solleva); TypeError per i tipi e ValueError per i valori, in apertura di funzione; interi bool o float → TypeError; nessun try:, print( o logging in src/ e scripts/.
- Dati reali solo con read_split_config e load_by_role; load_all_seasons non si usa; il ruolo "test" non si legge.
- Test sui dati reali saltati con motivo esplicito tramite _has_real_data o una condizione equivalente su DEFAULT_DATA_DIR; marcati slow se superano 60 s, e dichiarati nel report.
- Non leggere né scrivere file fuori dal repository.
- A fine task, scrivere il report in .agent/report/T27.md, unico file di .agent/ che si può toccare, con in sezioni distinte: percorsi dei file modificati, creati o rimossi; esito di ciascun criterio di accettazione; valori misurati; deviazioni dal piano; cose non fatte; comandi eseguiti. Fatti e valori senza giudizi; interpretazioni solo in una sezione a parte, e solo se richieste. Ogni valore numerico del report viene da un comando elencato.

Criteri di accettazione:
- river è in pyproject.toml senza vincolo di versione; drift.py importa ADWIN e PageHinkley da river; nessuna reimplementazione.
- Il test sintetico col salto di media dà almeno un allarme dopo il salto per entrambi i detector.
- I parametri congelati coincidono con la taratura ricalcolata sui dati reali (test saltato senza dati).
- Il report contiene la tabella completa della griglia, con gli allarmi per combinazione su 2000-01 e su 2010-11, e i default della versione di river installata.
- Suite veloce tutta verde.

Da misurare e riportare, senza farlo tornare: allarmi per combinazione e stagione; media e distanza da 1.9 delle combinazioni scelte. Se nessuna combinazione si avvicina a 1.9, per esempio zero allarmi ovunque, lo si riporta così: la griglia non si allarga.

Esito: 2026-09-30 — file toccati: pyproject.toml (aggiunto river, senza vincolo), src/shk/stats/drift.py e tests/test_drift.py (creati). river 0.26.1 installato nel .venv con pip, insieme a narwhals 2.26.0 (il dry-run non prevedeva modifiche ad altre dipendenze); uv.lock non toccato. drift.py: run_drift_detector(series, detector, params) → indici base 0 (ndarray int64), con istanza nuova a ogni chiamata; con params=None usa i default di river; calibrate_drift_detectors(serie 2000-01, serie 2010-11) → parametri scelti e tabella della griglia; regola di scelta con distanza intera |10·(a + b) − 38|, poi meno allarmi totali, poi ordine della griglia. Parametri congelati: ADWIN_DELTA = 0.002; PAGE_HINKLEY_DELTA = 0.05, PAGE_HINKLEY_THRESHOLD = 5.0. Default di river 0.26.1: ADWIN delta 0.002, clock 32, max_buckets 5, min_window_length 5, grace_period 10; PageHinkley min_instances 30, delta 0.005, threshold 50.0, alpha 0.9999, mode "both". Taratura eseguita con un comando python -c elencato nel report, senza file in scripts/. Deviazioni: alla prima esecuzione i 2 test sui dati reali erano in errore per un import di pandas mancante nel modulo di test; corretto. Da verificare in T28: se gli altri parametri dei detector sono passati in modo esplicito come costanti, come chiesto all'approvazione del piano; il report non lo dice. Valori misurati: ADWIN 0 allarmi su 2000-01 e su 2010-11 per tutti i 9 delta della griglia (media 0, distanza 1.9); Page-Hinkley scelto (0.05, 5.0), 1 allarme su 2000-01 e 1 su 2010-11 (media 1.0, distanza 0.9); tabella completa nel report. Salto sintetico con i default di river, seed 20260930: ADWIN allarme all'indice 223, Page-Hinkley al 210, nessuno prima del salto. tests/test_drift.py: 7 test (5 sintetici, 2 sui dati reali) in 4.69 s; suite veloce 264 verdi, 15 deselezionati, 49.73 s. Report: .agent/report/T27.md.

### Task 28 — Allarmi di ADWIN e Page-Hinkley su ogni scenario, US-C5.1
Stato: da fare

Obiettivo: lo script scripts/us_c5_1_drift_detectors.py registra quando scattano i due detector tarati, su ciascuno scenario di training e su ciascuna stagione di validazione, in results/us_c5_1_drift_detectors.csv e thesis/figures/us_c5_1_drift_detectors.png.

Dipende da: T26, T27.

Contesto:
- Serie di log-loss per partita da src/shk/model/residuals.py (T26); detector e parametri congelati da src/shk/stats/drift.py (T27).
- Scenari: 2000-01, 2010-11 e 2020-21, ciascuno con le partite della sola stagione prese dal fit che termina in quella stagione; 19 stagioni di validazione, ciascuna col fit che la prevede. Ogni stagione ha 380 partite [V, R10@2026-09-29].
- Gli script C4 leggono lo split con read_split_config e i dati con load_by_role [V, R1@2026-09-29c].
- Rieseguire uno script sovrascrive CSV e PNG versionati [V, R1@2026-09-28].

Da verificare prima di iniziare: l'esito di T26 e T27, cioè nomi di funzioni e costanti.

Passi richiesti:
1. Proporre il piano: colonne del CSV, pannelli della figura.
2. Scrivere lo script con run_experiment(): per ogni stagione e per ogni detector, un'istanza nuova con i parametri congelati, alimentata con la log-loss di tutte le partite della stagione in ordine cronologico.
3. CSV con una colonna row_type:
   - righe "alarm", una per allarme, con season, role, fit_through, detector, alarm_number (progressivo nella stagione), match_index (base 0 nella stagione), giornata (match_index // 10 + 1), Date, HomeTeam, AwayTeam;
   - righe "summary", una per stagione e detector, con n_alarms anche quando è zero;
   - stringa vuota dove un campo non si applica.
4. PNG: per i tre scenari di training, log-loss media per giornata con gli allarmi dei due detector marcati; etichette in italiano.
5. Scrivere tests/test_us_c5_1_acceptance.py: schema del CSV; righe di riepilogo per 22 stagioni × 2 detector; coerenza fra righe di allarme e riepilogo; giornata coerente con match_index; parametri importati da drift.py; ricalcolo dai dati reali uguale al CSV (confronto esatto su interi e stringhe), saltato senza dati.
6. Eseguire lo script due volte e confrontare lo SHA256 del CSV.
7. Eseguire la suite veloce.

Vincoli:
- I parametri dei detector vengono solo dalle costanti di T27 e non si cambiano.
- Il 2023-24 non si legge.
- Script: matplotlib.use("Agg") prima di pyplot; run_experiment() senza parametri, chiamata dal blocco __main__; nessun argomento da riga di comando; CSV con csv.DictWriter, open(mode="w", newline="", encoding="utf-8"), float nativi e stringa vuota dove non applicabile; PNG con plt.tight_layout() e savefig(dpi=150); parametri condivisi fra script e test in un modulo di libreria.
- Non modificare i moduli di src/shk/model/ né calibration.py, false_rejection.py e config/split.toml.
- Nessun commit e nessuna operazione git che modifichi lo stato del repository: i commit li fa il programmatore a mano.
- Commenti e docstring in italiano; identificatori, messaggi delle eccezioni e nomi dei test in inglese. Non è un'incoerenza: è la convenzione.
- Rispettare le eventuali convenzioni aggiuntive della sezione "Convenzioni del progetto" di .agent/PROTOCOLLO.md.
- Prima di scrivere codice, proporre il piano e fare le domande necessarie; nessun comando Python prima dell'approvazione del piano.
- Ogni comando Python con .\.venv\Scripts\python.exe dalla radice del repository.
- Codice: type hints completi; docstring in stile NumPy (Parametri / Restituisce / Solleva); TypeError per i tipi e ValueError per i valori, in apertura di funzione; interi bool o float → TypeError; nessun try:, print( o logging in src/ e scripts/.
- Dati reali solo con read_split_config e load_by_role; load_all_seasons non si usa; il ruolo "test" non si legge.
- Test sui dati reali saltati con motivo esplicito tramite _has_real_data o una condizione equivalente su DEFAULT_DATA_DIR; marcati slow se superano 60 s, e dichiarati nel report.
- Non leggere né scrivere file fuori dal repository.
- A fine task, scrivere il report in .agent/report/T28.md, unico file di .agent/ che si può toccare, con in sezioni distinte: percorsi dei file modificati, creati o rimossi; esito di ciascun criterio di accettazione; valori misurati; deviazioni dal piano; cose non fatte; comandi eseguiti. Fatti e valori senza giudizi; interpretazioni solo in una sezione a parte, e solo se richieste. Ogni valore numerico del report viene da un comando elencato.

Criteri di accettazione:
- CSV e PNG generati; righe di riepilogo per 22 stagioni (3 di training e 19 di validazione) × 2 detector.
- Per ogni allarme sono registrati stagione, detector, indice della partita, giornata e data.
- Il ricalcolo dai dati reali coincide col CSV (test verde in locale, saltato senza dati).
- CSV identico su due esecuzioni (SHA256).
- Nessuna lettura del 2023-24.
- Suite veloce tutta verde.

Da misurare e riportare, senza farlo tornare: numero di allarmi e giornata del primo allarme per stagione e detector, in particolare sul 2020-21. Nessun parametro si cambia in funzione di questi numeri.

Esito: —

### Task 29 — Z-test per giornata con soglia nominale e confronto con ADWIN e Page-Hinkley, US-C5.2
Stato: da fare

Obiettivo: src/shk/stats/drift.py calcola lo Z-test per giornata, e lo script scripts/us_c5_2_daily_z_test.py riporta per ciascuna delle 19 stagioni di validazione gli allarmi dello Z nominale, di ADWIN e di Page-Hinkley, accanto agli 1.9 attesi, in results/us_c5_2_daily_z_test.csv e thesis/figures/us_c5_2_daily_z_test.png.

Dipende da: T26, T27.

Contesto:
- Z della giornata g della stagione s: Z = (media della log-loss delle 10 partite di g − μ_f) / (σ_f / √10), con μ_f e σ_f (ddof = 1) sulla log-loss delle partite di training del fit f che prevede s. Giornata = blocco contiguo di 10 partite nell'ordine cronologico stabile; 38 giornate per stagione.
- Allarme nominale se |Z| > z_0.975, con α = 0.05. ALPHA = 0.05 è definita in src/shk/stats/false_rejection.py [V, R13@2026-09-28] e si importa di lì.
- Serie da src/shk/model/residuals.py (T26), con role "training" e "validation"; detector e parametri congelati da src/shk/stats/drift.py (T27).
- Log-loss media di validazione 0.979536 contro medie di training da 1.008189 a 1.020937 [V, R23 e R26@2026-09-29b].
- T30 aggiungerà a questo CSV le righe dello Z con soglia calibrata, per L ∈ {7, 20, 40}.

Da verificare prima di iniziare: l'esito di T26 e T27, cioè nomi di funzioni e costanti.

Passi richiesti:
1. Proporre il piano: firma della funzione, colonne del CSV, pannelli della figura.
2. Aggiungere a drift.py una funzione che, data la log-loss di una stagione con μ_f e σ_f, restituisce i 38 valori di Z; ValueError se la lunghezza non è un multiplo positivo di 10.
3. Scrivere lo script con run_experiment(): per ogni stagione di validazione, i 38 Z e gli allarmi nominali, più gli allarmi di ADWIN e Page-Hinkley con i parametri congelati sulla stessa stagione.
4. CSV con colonne che reggano anche le righe di T30, almeno: row_type, season, fit_through, method (z_nominal, adwin, page_hinkley), block_length (vuota per ora), threshold, giornata, z, alarm, n_alarms, expected_alarms. Righe "giornata" per lo Z e righe "summary" per stagione e metodo, più un riepilogo sulle 19 stagioni con la media.
5. PNG: allarmi per stagione e per metodo, con una linea a 1.9; etichette in italiano.
6. Test:
   - sintetici in tests/test_drift.py: Z di una piccola serie uguale al calcolo a mano entro 1e-12; validazioni;
   - di accettazione in tests/test_us_c5_2_acceptance.py: schema, 19 stagioni × 38 giornate, coerenza fra giornate e riepiloghi, ricalcolo dai dati reali entro 1e-12 sui float e confronto esatto sul resto, saltato senza dati.
7. Eseguire lo script due volte e confrontare lo SHA256 del CSV; eseguire la suite veloce.

Vincoli:
- Definizione di Z, baseline e soglia nominale non si cambiano in funzione dei conteggi.
- I parametri dei detector vengono solo dalle costanti di T27.
- Il 2023-24 non si legge.
- Script: matplotlib.use("Agg") prima di pyplot; run_experiment() senza parametri, chiamata dal blocco __main__; nessun argomento da riga di comando; CSV con csv.DictWriter, open(mode="w", newline="", encoding="utf-8"), float nativi e stringa vuota dove non applicabile; PNG con plt.tight_layout() e savefig(dpi=150); parametri condivisi fra script e test in un modulo di libreria.
- Non modificare i moduli di src/shk/model/ né calibration.py, false_rejection.py e config/split.toml.
- Nessun commit e nessuna operazione git che modifichi lo stato del repository: i commit li fa il programmatore a mano.
- Commenti e docstring in italiano; identificatori, messaggi delle eccezioni e nomi dei test in inglese. Non è un'incoerenza: è la convenzione.
- Rispettare le eventuali convenzioni aggiuntive della sezione "Convenzioni del progetto" di .agent/PROTOCOLLO.md.
- Prima di scrivere codice, proporre il piano e fare le domande necessarie; nessun comando Python prima dell'approvazione del piano.
- Ogni comando Python con .\.venv\Scripts\python.exe dalla radice del repository.
- Codice: type hints completi; docstring in stile NumPy (Parametri / Restituisce / Solleva); TypeError per i tipi e ValueError per i valori, in apertura di funzione; interi bool o float → TypeError; nessun try:, print( o logging in src/ e scripts/.
- Dati reali solo con read_split_config e load_by_role; load_all_seasons non si usa; il ruolo "test" non si legge.
- Test sui dati reali saltati con motivo esplicito tramite _has_real_data o una condizione equivalente su DEFAULT_DATA_DIR; marcati slow se superano 60 s, e dichiarati nel report.
- Non leggere né scrivere file fuori dal repository.
- A fine task, scrivere il report in .agent/report/T29.md, unico file di .agent/ che si può toccare, con in sezioni distinte: percorsi dei file modificati, creati o rimossi; esito di ciascun criterio di accettazione; valori misurati; deviazioni dal piano; cose non fatte; comandi eseguiti. Fatti e valori senza giudizi; interpretazioni solo in una sezione a parte, e solo se richieste. Ogni valore numerico del report viene da un comando elencato.

Criteri di accettazione:
- Z calcolato giornata per giornata su ciascuna delle 19 stagioni di validazione, 38 giornate per stagione.
- Lo Z di una serie sintetica coincide col calcolo a mano entro 1e-12.
- Il CSV riporta gli allarmi nominali per stagione e la media sulle 19 stagioni, accanto a 1.9.
- Il CSV riporta gli allarmi di ADWIN e Page-Hinkley sulle stesse stagioni, con i parametri congelati.
- Ricalcolo verde in locale e saltato senza dati; CSV identico su due esecuzioni (SHA256); suite veloce tutta verde.

Da misurare e riportare, senza farlo tornare: allarmi per stagione e per metodo; medie sulle 19 stagioni; quanti allarmi Z hanno Z > 0 e quanti Z < 0.

Esito: —

### Task 30 — Soglia dello Z-test calibrata per block bootstrap, US-C5.2
Stato: da fare

Obiettivo: per ogni fit e ogni L ∈ {7, 20, 40}, la soglia di |Z| per giornata è calibrata per moving block bootstrap della serie di training del fit; il tasso di falsi allarmi con quella soglia è verificato su ricampionamenti indipendenti; il CSV di C5.2 riporta anche gli allarmi con soglia calibrata sulle 19 stagioni di validazione.

Dipende da: T29.

Contesto:
- src/shk/stats/calibration.py [V, R12@2026-09-28 e firme R1@2026-09-29c]:
  - moving_block_indices(n, block_length, n_boot, rng) → int64 (n_boot, n);
  - compute_order_statistic_index(b, alpha) → ⌈(1 − α)(b + 1)⌉;
  - calibrate_threshold(data, statistic, block_length, n_boot, alpha, rng, vectorized=False) → float; la statistica deve restituire float64 (n_boot,) finita, altrimenti ValueError.
  La docstring del modulo è contraddittoria nello schema (a) [V]: non si tocca in questo task.
- Decisioni S2: B = 999; L ∈ {7, 20, 40}, tutte riportate; soglia = statistica d'ordine ⌈(1 − α)(B + 1)⌉, cioè la 950-esima; allarme se la statistica supera strettamente la soglia; intervallo Monte Carlo al 99% su 1000 prove [0.0322, 0.0678], estremi inclusi, dato da monte_carlo_interval_99 in src/shk/stats/false_rejection.py [V, R13@2026-09-28].
- Qui H₀ vale per costruzione: si ricampiona la serie di training che definisce μ_f e σ_f, non la stagione sotto test. Il problema di T12, una soglia calibrata sulla serie sotto test senza imporre H₀, non si presenta [D, ragionamento del supervisore].
- Serie di training dei fit: 380, 760 e 1 140 partite (T26). Z, μ_f, σ_f, giornate, CSV e script: da T29.

Da verificare prima di iniziare:
- l'esito di T29: colonne del CSV, nomi di funzioni e costanti;
- come calibrate_threshold chiama la statistica in modalità vectorized, cioè forma dell'argomento e forma attesa del risultato.

Passi richiesti:
1. Proporre il piano, compreso lo schema dei seed: SEED_C5 = 20260929 in drift.py; SeedSequence(SEED_C5).spawn in un figlio per fit, diviso in un generatore per L per la calibrazione e uno per i ricampionamenti di verifica.
2. Statistica: |Z| della prima giornata, cioè delle prime 10 posizioni, di ogni serie ricampionata, con μ_f e σ_f della serie di training originale.
3. Calibrare la soglia per ogni fit e L con calibrate_threshold, B = 999, α = 0.05.
4. Verifica: 1000 ricampionamenti nuovi per ogni fit e L, con un generatore separato, e tasso di |Z| > soglia calibrata. Sugli stessi ricampionamenti, anche il tasso con la soglia nominale z_0.975.
5. Applicare le soglie calibrate alle 19 stagioni di validazione, ciascuna con la soglia del fit che la prevede. Aggiungere al CSV di T29 le righe con method = z_block_bootstrap e block_length valorizzata, e le righe di verifica. Aggiornare il PNG.
6. Test: unitari su dati sintetici per la statistica e l'uso della calibrazione; di accettazione: schema, righe attese, tasso di verifica nell'intervallo, ricalcolo dai dati reali entro 1e-12 sui float, saltato senza dati.
7. Eseguire lo script due volte e confrontare lo SHA256 del CSV; eseguire la suite veloce, e la suite slow se si aggiunge un test slow.

Vincoli:
- calibration.py e false_rejection.py non si modificano.
- L, B, α, SEED_C5 e la statistica sono fissati prima dei risultati.
- Le stagioni di validazione non entrano nella calibrazione.
- test_acceptance_calibrated_phi_zero_within_mc_interval resta rosso per il risultato noto di T12: non si tocca.
- Script: matplotlib.use("Agg") prima di pyplot; run_experiment() senza parametri, chiamata dal blocco __main__; nessun argomento da riga di comando; CSV con csv.DictWriter, open(mode="w", newline="", encoding="utf-8"), float nativi e stringa vuota dove non applicabile; PNG con plt.tight_layout() e savefig(dpi=150); parametri condivisi fra script e test in un modulo di libreria.
- Non modificare i moduli di src/shk/model/ né config/split.toml.
- Nessun commit e nessuna operazione git che modifichi lo stato del repository: i commit li fa il programmatore a mano.
- Commenti e docstring in italiano; identificatori, messaggi delle eccezioni e nomi dei test in inglese. Non è un'incoerenza: è la convenzione.
- Rispettare le eventuali convenzioni aggiuntive della sezione "Convenzioni del progetto" di .agent/PROTOCOLLO.md.
- Prima di scrivere codice, proporre il piano e fare le domande necessarie; nessun comando Python prima dell'approvazione del piano.
- Ogni comando Python con .\.venv\Scripts\python.exe dalla radice del repository.
- Codice: type hints completi; docstring in stile NumPy (Parametri / Restituisce / Solleva); TypeError per i tipi e ValueError per i valori, in apertura di funzione; interi bool o float → TypeError; RNG passato come argomento, flussi indipendenti con SeedSequence.spawn; nessun try:, print( o logging in src/ e scripts/.
- Dati reali solo con read_split_config e load_by_role; load_all_seasons non si usa; il ruolo "test" non si legge.
- Test sui dati reali saltati con motivo esplicito tramite _has_real_data o una condizione equivalente su DEFAULT_DATA_DIR; marcati slow se superano 60 s, e dichiarati nel report.
- Non leggere né scrivere file fuori dal repository.
- A fine task, scrivere il report in .agent/report/T30.md, unico file di .agent/ che si può toccare, con in sezioni distinte: percorsi dei file modificati, creati o rimossi; esito di ciascun criterio di accettazione; valori misurati; deviazioni dal piano; cose non fatte; comandi eseguiti. Fatti e valori senza giudizi; interpretazioni solo in una sezione a parte, e solo se richieste. Ogni valore numerico del report viene da un comando elencato.

Criteri di accettazione:
- Soglia calibrata per ciascuno dei 3 fit e delle 3 L, riportata nel CSV.
- Per ogni fit e L, il tasso di |Z| > soglia calibrata sui 1000 ricampionamenti di verifica sta nell'intervallo al 99% [0.0322, 0.0678], estremi inclusi. Se non ci sta, si indaga e si riporta; non si cambiano L, B, seed né statistica.
- Il CSV riporta gli allarmi con soglia calibrata per stagione di validazione e per L, accanto agli allarmi nominali, di ADWIN, di Page-Hinkley e a 1.9.
- Ricalcolo verde in locale e saltato senza dati; CSV identico su due esecuzioni (SHA256); suite veloce tutta verde.

Da misurare e riportare, senza farlo tornare: le nove soglie; il tasso con soglia nominale sui ricampionamenti di verifica; gli allarmi con soglia calibrata per stagione e L e la loro media sulle 19 stagioni. Lo scarto da 1.9 sulle stagioni di validazione è un risultato.

Esito: —

### Task 31 — Motore su quote reali e regola della Baseline D, con κ calibrato sul training, US-C5.3
Stato: da fare

Obiettivo: esistono un motore che calcola la log-ricchezza di una stagione da frazioni, quote ed esiti reali, e la regola della Baseline D; κ è calibrato per ADWIN e per Page-Hinkley su 2010-11 e 2020-21 e congelato in costanti.

Dipende da: T26, T27.

Contesto:
- Decisione S1: il motore riceve le frazioni dall'esterno e non conosce p né p̂; ogni regola di staking sta in src/shk/kelly/staking.py; le regole non limitano la frazione sotto 1, una frazione ≥ 1 la rifiuta il motore. λ fisso di riferimento: quarto-Kelly, 0.25.
- kelly_staking(p_hat, b, lam=1.0) in staking.py [V, R1@2026-09-29c]; formula lam·max(0, (b·p_hat − (1 − p_hat))/b) [D]; supporto per array [D].
- simulate_growth(outcomes, fractions, b) in simulate.py lavora su scommesse binarie con esiti simulati (M, T) [V, R1@2026-09-29c]: non serve per quote diverse a ogni partita [D].
- max_drawdown in src/shk/kelly/metrics.py lavora su traiettorie di log-ricchezza (M, T+1) [V, R1@2026-09-28].
- Quote: B365H, B365D, B365A pre-partita, assenti fino al 2001-02 e quindi nel 2000-01, complete dal 2002-03 [V, R14@2026-09-29]. align_predictions_with_odds(df_preds, df_raw) in scoring.py unisce su season, Date, HomeTeam, AwayTeam, con ValueError per chiavi mancanti o duplicate [V, R26 e R27@2026-09-29b].
- Regola della Baseline D (scelta del supervisore su delega):
  - per partita al più una puntata, sull'esito con p̂·o − 1 massimo se positivo, con frazione kelly_staking(p̂, o − 1, λ_t), dove p̂ è la probabilità raw del Modulo 1 e o la quota B365 di quell'esito;
  - λ_t = 0.25 a inizio stagione, moltiplicato per κ a ogni allarme; un allarme su una partita della data d vale dalle partite con Date > d;
  - detector nuovo a ogni stagione, alimentato con la log-loss di tutte le partite, puntate o no, con i parametri congelati di T27;
  - bankroll 1 a inizio stagione; le puntate della stessa data si decidono sul bankroll di inizio data e si regolano insieme: B ← B·(1 + Σ f_i·r_i), con r_i = o_i − 1 se vinta e −1 se persa.
- Calibrazione: κ ∈ {0, 0.25, 0.5, 0.75, 1}; per ciascun detector si sceglie il κ che massimizza la somma della log-ricchezza finale di 2010-11 (fit 2010-11) e 2020-21 (fit 2020-21), e a parità il più grande. κ = 1 coincide col quarto-Kelly senza detector. Il 2000-01 non entra perché non ha B365.

Da verificare prima di iniziare:
- se kelly_staking accetta array e che formula applica;
- se align_predictions_with_odds funziona sulle partite di training delle stagioni 2010-11 e 2020-21;
- l'esito di T26 e T27.

Passi richiesti:
1. Proporre il piano: firme, posizione delle costanti, forma dell'output del motore.
2. Creare src/shk/kelly/backtest.py con il motore. Riceve per ogni partita data, frazione, quota dell'esito puntato ed esito vinto o perso, e restituisce la log-ricchezza dopo ogni data, partendo da 0. ValueError per frazioni fuori da [0, 1), somma delle frazioni di una data ≥ 1, date non ordinate, quote non finite o ≤ 1. Non riceve p né p̂.
3. Aggiungere a staking.py, senza modificare le funzioni esistenti, la scelta dell'esito e della frazione per partita e la regola λ_t descritta nel contesto.
4. Calibrare κ come descritto nel contesto e congelare in costanti BASE_LAMBDA = 0.25, la griglia di κ e il κ scelto per ciascun detector.
5. Nella docstring della regola, scrivere che il detector dice quando, non quanto né di che tipo: κ è un iperparametro fisso, uguale per ogni allarme.
6. Test:
   - tests/test_backtest.py, sintetici: log-ricchezza a mano su poche partite, puntate della stessa data regolate insieme, validazioni;
   - tests/test_staking.py: scelta dell'esito; un allarme della data d non cambia le frazioni della data d e le cambia dalla data successiva; con κ = 1 le frazioni coincidono col quarto-Kelly senza detector;
   - sui dati reali: la calibrazione ricalcolata dà i κ congelati; saltato senza dati, slow se supera 60 s.
7. Eseguire la suite veloce.

Vincoli:
- Il 2000-01, le stagioni di validazione e il 2023-24 non entrano in questo task.
- Griglia di κ, λ di partenza, obiettivo e regola di parità non si cambiano dopo aver visto i risultati.
- Non modificare simulate.py né le funzioni esistenti di staking.py (solo aggiunte), i moduli di src/shk/model/, calibration.py, false_rejection.py, config/split.toml.
- Nessun commit e nessuna operazione git che modifichi lo stato del repository: i commit li fa il programmatore a mano.
- Commenti e docstring in italiano; identificatori, messaggi delle eccezioni e nomi dei test in inglese. Non è un'incoerenza: è la convenzione.
- Rispettare le eventuali convenzioni aggiuntive della sezione "Convenzioni del progetto" di .agent/PROTOCOLLO.md.
- Prima di scrivere codice, proporre il piano e fare le domande necessarie; nessun comando Python prima dell'approvazione del piano.
- Ogni comando Python con .\.venv\Scripts\python.exe dalla radice del repository.
- Codice: type hints completi; docstring in stile NumPy (Parametri / Restituisce / Solleva); TypeError per i tipi e ValueError per i valori, in apertura di funzione; interi bool o float → TypeError; vettorizzazione NumPy dove possibile; nessun try:, print( o logging in src/ e scripts/.
- Dati reali solo con read_split_config e load_by_role; load_all_seasons non si usa; il ruolo "test" non si legge.
- Test sui dati reali saltati con motivo esplicito tramite _has_real_data o una condizione equivalente su DEFAULT_DATA_DIR; marcati slow se superano 60 s, e dichiarati nel report.
- Non leggere né scrivere file fuori dal repository.
- A fine task, scrivere il report in .agent/report/T31.md, unico file di .agent/ che si può toccare, con in sezioni distinte: percorsi dei file modificati, creati o rimossi; esito di ciascun criterio di accettazione; valori misurati; deviazioni dal piano; cose non fatte; comandi eseguiti. Fatti e valori senza giudizi; interpretazioni solo in una sezione a parte, e solo se richieste. Ogni valore numerico del report viene da un comando elencato.

Criteri di accettazione:
- Il motore riproduce la log-ricchezza di un caso sintetico calcolata a mano entro 1e-12, solleva gli errori previsti e non riceve p né p̂.
- Un allarme della data d cambia λ solo dalle date successive (test).
- Con κ = 1 le frazioni coincidono col quarto-Kelly senza detector (test).
- I κ congelati per ADWIN e Page-Hinkley coincidono con la calibrazione ricalcolata sui dati reali (test saltato senza dati).
- La docstring della regola dice che il detector indica quando, non quanto né di che tipo.
- Il report contiene la tabella della log-ricchezza finale per κ, detector e stagione.
- Suite veloce tutta verde.

Da misurare e riportare, senza farlo tornare: log-ricchezza finale per κ, detector e stagione; κ scelti; numero di puntate e di allarmi per stagione. Se il κ scelto è 0 o 1, lo si riporta così: griglia e obiettivo non cambiano.

Esito: —

### Task 32 — Esecuzione appaiata della Baseline D sulle stagioni di validazione, US-C5.3
Stato: da fare

Obiettivo: lo script scripts/us_c5_3_baseline_d.py esegue il quarto-Kelly senza detector (κ = 1), D-ADWIN e D-Page-Hinkley sulla stessa sequenza di partite, quote, previsioni ed esiti delle 19 stagioni di validazione, con i parametri congelati, e scrive results/us_c5_3_baseline_d.csv e thesis/figures/us_c5_3_baseline_d.png.

Dipende da: T31.

Contesto:
- Motore in src/shk/kelly/backtest.py, regola della Baseline D e costanti (BASE_LAMBDA = 0.25, κ congelati) da T31; parametri dei detector da src/shk/stats/drift.py (T27); log-loss e probabilità da src/shk/model/residuals.py (T26).
- Ogni stagione di validazione si prevede col fit delle stagioni di training strettamente anteriori (decisione S4); B365 pre-partita completa in tutte le 19 stagioni [V, R14@2026-09-29].
- Bankroll 1 a inizio di ogni stagione; detector nuovo a ogni stagione.
- max_drawdown in src/shk/kelly/metrics.py su traiettorie di log-ricchezza (M, T+1) [V, R1@2026-09-28].

Da verificare prima di iniziare: l'esito di T31, cioè firme, costanti e forma dell'output del motore.

Passi richiesti:
1. Proporre il piano: colonne del CSV, pannelli della figura.
2. Scrivere lo script con run_experiment(): per ogni stagione, costruire una sola volta gli input (partite, date, probabilità, quote, esiti, log-loss) e passarli identici ai tre agenti.
3. CSV: una riga per stagione e agente con season, fit_through, agent, kappa, final_log_wealth, n_bets, n_alarms (vuota per il riferimento), max_drawdown; più una riga per agente con la somma della log-ricchezza finale sulle 19 stagioni.
4. PNG: differenza appaiata di log-ricchezza finale fra D-ADWIN e riferimento e fra D-Page-Hinkley e riferimento, per stagione; etichette in italiano.
5. Scrivere tests/test_us_c5_3_acceptance.py: un test che verifica che i tre agenti ricevono input identici; schema del CSV; κ importati dalle costanti; con κ = 1 la Baseline D coincide col riferimento su dati sintetici; ricalcolo dai dati reali entro 1e-12 sui float e confronto esatto sul resto, saltato senza dati.
6. Eseguire lo script due volte e confrontare lo SHA256 del CSV; eseguire la suite veloce.

Vincoli:
- κ, λ di partenza e parametri dei detector vengono solo dalle costanti di T27 e T31; nessun parametro si cambia guardando le stagioni di validazione.
- Il 2023-24 non si legge.
- Script: matplotlib.use("Agg") prima di pyplot; run_experiment() senza parametri, chiamata dal blocco __main__; nessun argomento da riga di comando; CSV con csv.DictWriter, open(mode="w", newline="", encoding="utf-8"), float nativi e stringa vuota dove non applicabile; PNG con plt.tight_layout() e savefig(dpi=150); parametri condivisi fra script e test in un modulo di libreria.
- Non modificare i moduli di src/shk/model/ né calibration.py, false_rejection.py e config/split.toml.
- Nessun commit e nessuna operazione git che modifichi lo stato del repository: i commit li fa il programmatore a mano.
- Commenti e docstring in italiano; identificatori, messaggi delle eccezioni e nomi dei test in inglese. Non è un'incoerenza: è la convenzione.
- Rispettare le eventuali convenzioni aggiuntive della sezione "Convenzioni del progetto" di .agent/PROTOCOLLO.md.
- Prima di scrivere codice, proporre il piano e fare le domande necessarie; nessun comando Python prima dell'approvazione del piano.
- Ogni comando Python con .\.venv\Scripts\python.exe dalla radice del repository.
- Codice: type hints completi; docstring in stile NumPy (Parametri / Restituisce / Solleva); TypeError per i tipi e ValueError per i valori, in apertura di funzione; interi bool o float → TypeError; nessun try:, print( o logging in src/ e scripts/.
- Dati reali solo con read_split_config e load_by_role; load_all_seasons non si usa; il ruolo "test" non si legge.
- Test sui dati reali saltati con motivo esplicito tramite _has_real_data o una condizione equivalente su DEFAULT_DATA_DIR; marcati slow se superano 60 s, e dichiarati nel report.
- Non leggere né scrivere file fuori dal repository.
- A fine task, scrivere il report in .agent/report/T32.md, unico file di .agent/ che si può toccare, con in sezioni distinte: percorsi dei file modificati, creati o rimossi; esito di ciascun criterio di accettazione; valori misurati; deviazioni dal piano; cose non fatte; comandi eseguiti. Fatti e valori senza giudizi; interpretazioni solo in una sezione a parte, e solo se richieste. Ogni valore numerico del report viene da un comando elencato.

Criteri di accettazione:
- I tre agenti girano sulle 19 stagioni di validazione e il test sugli input identici è verde.
- CSV e PNG generati, con una riga per stagione e agente e le somme sulle 19 stagioni.
- Con κ = 1 la Baseline D coincide col riferimento (test sintetico).
- Ricalcolo verde in locale e saltato senza dati; CSV identico su due esecuzioni (SHA256); suite veloce tutta verde.

Da misurare e riportare, senza farlo tornare: log-ricchezza finale per stagione e agente; differenze appaiate D − riferimento per stagione e in totale; numero di puntate e di allarmi; drawdown massimo. Nessun parametro si cambia in funzione di questi numeri.

Esito: —

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
- Confermare o cambiare le scelte fatte dal supervisore su delega il 2026-09-29:
  - Modulo 1 raw;
  - scenari di ora = 3 di training più 19 di validazione, con il 2023-24 dopo lo sblocco;
  - calibrazione dello Z sulla serie di training del fit;
  - taratura dei detector su 1.9 allarmi per stagione su 2000-01 e 2010-11, con il 2020-21 escluso;
  - Baseline D: un esito per partita, λ di partenza 0.25, κ moltiplicativo a ogni allarme, griglia e obiettivo di κ, 2000-01 escluso dalla calibrazione.
- US-C5.1: saper rispondere a "perché ANOVA e non ADWIN?" coi numeri di T28, T29 e T30.
- US-C5.2: scegliere quale L adottare per lo Z calibrato, insieme alla scelta rimandata in S2 per C6.4 e C8.
- US-C5.3: scrivere in tesi che il detector dice quando, non quanto né di che tipo, e che κ è un iperparametro fisso uguale per ogni allarme.
- Eseguire US-C5.1 sul 2023-24 dopo lo sblocco del test.
- Aggiornare uv.lock dopo l'aggiunta di river e verificare che la CI installi river e resti verde.
- Committare codice, CSV e figure di T26–T32.

