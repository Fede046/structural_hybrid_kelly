# Backlog
Ultimo task: T24

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