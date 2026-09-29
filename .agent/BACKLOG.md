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

## Story S4 — C4 Elo e go/no-go: Modulo 1 minimo, ĝ contro il mercato, calibrazione
Aperta il 2026-09-29.

**Interpretazione:** unisce US-C4.1, US-C4.2 e US-C4.3. Si costruisce un Modulo 1 Elo con mapping di Davidson verso l'1X2 e previsioni walk-forward, con iperparametri stimati solo su stagioni di training anteriori a quelle da prevedere. Poi si misura ĝ contro il mercato de-viggato (tre metodi, due serie di q) e si valuta la calibrazione, con e senza ricalibrazione. ĝ e gli esiti della calibrazione sono informativi: si misurano, non si fanno tornare.

**Assunzioni fatte:**
- Neopromosse (decisione del programmatore, 2026-09-29): una squadra assente nella stagione precedente ma già vista in una stagione anteriore del dataset riprende il suo ultimo rating. Una squadra mai vista eredita la media dei rating finali delle tre retrocesse della stagione precedente. Le squadre rimaste conservano il rating; nella prima stagione del dataset (1993-94) tutte partono da 1500.
- Retrocesse senza leakage: sono le ultime tre della classifica della stagione precedente, calcolata dai soli risultati in storia (3 punti la vittoria, 1 il pareggio; a parità di punti contano differenza reti, gol fatti e nome in ordine alfabetico). Le penalizzazioni in punti non sono nei dati, quindi la classifica calcolata può differire da quella reale. Alla transizione 1994-95 → 1995-96 le retrocesse furono quattro: la regola ne usa tre, e l'effetto resta confinato alle stagioni di history.
- Scelta del supervisore, legata alla regola sulle neopromosse: i tornanti rompono la somma zero dei rating. L'effetto si misura, non si corregge.
- q (scelta del supervisore su delega, 2026-09-29, da confermare): la serie principale è B365 pre-partita (B365H/D/A), come deciso in S3, sulle 19 stagioni di validazione. La seconda serie è la chiusura Pinnacle (PSCH/PSCD/PSCA) sulle stagioni di validazione dal 2012-13. Motivo: le note 2.4 §6 impostano il go/no-go contro la chiusura, che è il prezzo usato da KellyBench.
- Calibrazione espansiva (scelta del supervisore su delega, 2026-09-29, da confermare): ogni stagione di validazione è prevista con K, h, ν stimati solo sulle stagioni di training strettamente anteriori.
  - Il fit 2000-01 serve le stagioni dal 2002-03 al 2009-10.
  - Il fit 2000-01 + 2010-11 serve le stagioni dal 2011-12 al 2019-20.
  - Il fit sulle tre stagioni serve il 2021-22 e il 2022-23.
  
  Lo schema rispetta sia la story ("solo sul training") sia le note 2.8 §9.1 (nessun parametro stimato su partite successive). La ricalibrazione di US-C4.3 segue lo stesso schema.
- L'obiettivo della calibrazione è la log-loss media (logaritmo naturale) delle probabilità Davidson sulle sole partite di training del fit. I rating girano dal 1993-94 con un unico terno (K, h, ν); i risultati delle stagioni non di training entrano nei rating come storia, mai nell'obiettivo.
- Mapping (note 2.8 §3.3): Davidson con r = 10^(delta/s), con s = 400 come nel punteggio atteso Elo, così che con ν → 0 si ritrovi E. La baseline a pareggio costante è p_draw = c, p_home = (1 − c)E, p_away = (1 − c)(1 − E), con c uguale alla frequenza del pareggio sulle partite di training del fit. L'aggiornamento dei rating usa il punteggio atteso logistico E, non il mapping (note 2.8 §2.1 e §13.2).
- ĝ, log-loss, Brier e reliability si misurano solo sulle stagioni di validazione. Le previsioni delle stagioni di training servono solo a stimare i parametri e la ricalibrazione, e per 3 iperparametri sono in-campione.
- Il codice del Modulo 1 sta in un nuovo sottopacchetto src/shk/model/.
- Nessun task di sola ricognizione: le voci dedotte si verificano dentro i task che le usano.
  - Stato della suite su 90a77a1: primo passo di T20.
  - Coerenza dei nomi squadra: criterio bloccante di T21.
  - Completezza di PSC e convergenza di devig_power sulle quote reali: da verificare in T23.
  - Disponibilità dell'isotonica in SciPy: da verificare in T24.
- Fatti [V] usati senza verifica:
  - contratto di walkforward_split e assert_no_leakage, e whitelist senza chiusure [R46@2026-09-29];
  - load_by_role e i ruoli dello split [R26@2026-09-29];
  - funzioni e validazioni di devig.py [R30–R36@2026-09-29];
  - B365 completa dal 2002-03 [R14@2026-09-29];
  - colonne PSC* presenti dal 2012-13 [R8@2026-09-29, presenza e non completezza];
  - convenzioni degli script [R8@2026-09-28 e R1@2026-09-29b].

**Domande aperte:**

### Task 20 — Funzioni Elo e mapping 1X2 (Davidson e pareggio costante)
Stato: da fare

Obiettivo: src/shk/model/elo.py fornisce punteggio atteso, aggiornamento a somma zero e due mapping dal differenziale Elo a probabilità 1X2 che sommano a 1, verificati da test.

Dipende da: nessuno.

Contesto:
- Nuovo sottopacchetto src/shk/model/, accanto a kelly/, stats/, data/ e market/ [V, R1@2026-09-29b]. Gli __init__.py dei sottopacchetti recenti contengono solo una docstring in italiano [V, R32@2026-09-29 per market/].
- Formule (note di tesi 2.8 §2.1 e §3.3):
  - delta = R_casa − R_trasferta + h;
  - E = 1/(1 + 10^(−delta/s)), con s = 400 di default;
  - S = 1, 0.5, 0 per esito H, D, A;
  - aggiornamento R_casa' = R_casa + K(S − E), R_trasferta' = R_trasferta − K(S − E);
  - Davidson, con r = 10^(delta/s): p_home = r/(r + 1 + ν√r), p_draw = ν√r/(r + 1 + ν√r), p_away = 1/(r + 1 + ν√r);
  - pareggio costante: p_draw = c, p_home = (1 − c)E, p_away = (1 − c)(1 − E).
- La tabella delle note 2.8 §3.3 (ν = 0.8 e 1.1; delta = 0, 100, 200, 400) si ottiene con s = 200, non con 400 [D, ricalcolo del supervisore]. Serve solo a verificare la formula; il modello usa s = 400.
- Convenzioni: type hints, docstring NumPy in italiano, ValueError per i valori e TypeError per i tipi; interi bool o float danno TypeError [V, R1@2026-09-29b e R7@2026-09-28].

Da verificare prima di iniziare: stato della suite veloce su 90a77a1, mai rieseguita dopo la mappa [D]. È il primo passo: se non è verde, fermarsi e riportare prima di scrivere codice.

Passi richiesti:
1. Eseguire .\.venv\Scripts\python.exe -m pytest -v e riportare conteggi ed esito.
2. Proporre il piano: firme (scalari e ndarray di delta), validazioni, elenco dei test.
3. Creare src/shk/model/__init__.py, con la sola docstring di modulo in italiano.
4. Creare src/shk/model/elo.py con il punteggio atteso, l'aggiornamento, il mapping Davidson e il mapping a pareggio costante, con s come argomento (default 400).
5. Scrivere tests/test_elo.py.
6. Rieseguire la suite veloce.

Vincoli:
- Nessun commit e nessuna operazione git che modifichi lo stato del repository.
- Commenti e docstring in italiano; identificatori, messaggi delle eccezioni e nomi dei test in inglese.
- Rispettare la sezione "Convenzioni del progetto" di .agent/PROTOCOLLO.md.
- Ogni comando Python con .\.venv\Scripts\python.exe.
- Proporre il piano e fare le domande prima di scrivere codice.
- Nessuna dipendenza nuova.
- Funzioni pure: nessun RNG, nessun accesso ai dati.
- Non toccare file fuori da src/shk/model/ e tests/test_elo.py.
- A fine task scrivere .agent/report/T20.md, unico file di .agent/ modificabile, con sezioni distinte: percorsi dei file modificati, creati o rimossi; esito di ciascun criterio; valori misurati; deviazioni dal piano; cose non fatte; comandi eseguiti. Fatti e valori senza giudizi.

Criteri di accettazione:
- Somma zero: dopo l'aggiornamento la somma dei due rating è invariata entro 1e-12, per esiti H, D e A.
- Somma a 1 per entrambi i mapping, entro 1e-12, con tutte le probabilità in (0, 1).
  - Davidson: griglia di delta in [−800, 800] e ν in [0.05, 3].
  - Pareggio costante: stessa griglia di delta e c in [0.01, 0.99].
- Davidson con s = 200 riproduce i 24 valori della tabella delle note 2.8 §3.3 entro 5e-4. La tabella riporta tre decimali.
- Simmetria di Davidson: delta → −delta scambia p_home e p_away; a ν fisso, p_draw è strettamente decrescente in |delta|.
- Con ν = 1e-12, p_home di Davidson coincide con E entro 1e-9.
- Pareggio costante: p_draw = c esatto e p_home/(p_home + p_away) = E entro 1e-12.
- Validazioni:
  - ValueError per ν ≤ 0 o non finito, c fuori da (0, 1), s ≤ 0 o non finito, K < 0 o non finito, esito diverso da H, D, A, delta non finito;
  - TypeError per tipi sbagliati.
- Suite veloce verde, con i test nuovi inclusi.

Esito: —

### Task 21 — Previsore Elo walk-forward con regola per le neopromosse, US-C4.1
Stato: da fare

Obiettivo: dato un DataFrame di partite e un unico terno (K, h, ν), un previsore restituisce, per ogni partita delle stagioni richieste, rating, delta e probabilità 1X2 calcolati solo con partite già giocate. Il previsore applica la regola dichiarata per le neopromosse ed è verificato da test anti-leakage.

Dipende da: T20.

Contesto:
- src/shk/model/elo.py (T20) fornisce punteggio atteso, aggiornamento e mapping Davidson.
- src/shk/data/walkforward.py [V, R46@2026-09-29]:
  - walkforward_split(df, seasons_to_predict) produce coppie (storia, partita);
  - la storia è df.iloc[:searchsorted(Date, side="left")], cioè le partite con Date strettamente anteriore, ed è una slice da non modificare;
  - la partita è ridotta alla whitelist: identificativi e quote pre-partita, nessun risultato;
  - solleva ValueError se df non è ordinato per Date o manca di Date e season;
  - assert_no_leakage(history, match) solleva LeakageError.
- Sui dati reali il DataFrame si costruisce concatenando load_by_role("history"), load_by_role("training") e load_by_role("validation"), poi riordinando in modo stabile per Date. load_by_role è la sola via ammessa, e un test di guardia vieta load_all_seasons nei file nuovi [V, R26@2026-09-29]. tests/test_leakage.py usa lo stesso schema [V, R46@2026-09-29].
- Le stagioni sono stringhe YYYY-YY consecutive dal 1993-94. Il 1993-94 e il 1994-95 hanno 462 partite, le altre 380 [V, R10@2026-09-29].
- Regola per le neopromosse (decisione del programmatore, 2026-09-29), applicata alla prima partita della stagione s in cui compare ciascuna squadra:
  - una squadra presente in s − 1 conserva il rating;
  - una squadra assente in s − 1 ma presente in una stagione anteriore riprende l'ultimo rating che aveva;
  - una squadra mai vista eredita la media dei rating finali delle tre ultime della classifica di s − 1;
  - la classifica si calcola dai risultati in storia: 3 punti la vittoria e 1 il pareggio; a parità di punti contano differenza reti, gol fatti e nome in ordine alfabetico;
  - nella prima stagione del DataFrame tutte le squadre partono da 1500.
- Il calcolo di K, h e ν non spetta a questo task: il previsore li riceve come argomenti.

Da verificare prima di iniziare:
- Coerenza dei nomi squadra fra stagioni, mai verificata [D]. La verifica è il criterio sulle transizioni di stagione.
- FTR assume solo i valori H, D, A [D]. Un valore diverso deve dare ValueError, non un'assegnazione silenziosa.

Passi richiesti:
1. Proporre il piano.
   - Firma del previsore: DataFrame, stagioni da prevedere, k, h, nu, rating iniziale con default 1500.
   - Colonne dell'output: season, Date, HomeTeam, AwayTeam, rating_home, rating_away, delta, p_home, p_draw, p_away, home_promotion e away_promotion. Le ultime due valgono "", "returning" o "new" per tutta la stagione.
   - Struttura del percorso veloce.
2. Creare src/shk/model/elo_predictor.py con il percorso via fornitore. Per ogni coppia di walkforward_split si consumano prima, in ordine, le righe di storia non ancora usate per l'aggiornamento, poi si prevede la partita.
3. Implementare la regola di ingresso di stagione e la classifica.
4. Implementare un percorso veloce a passata unica sul DataFrame ordinato, per la calibrazione di T22. Tutte le partite di una data si prevedono prima di aggiornare con quella data.
5. Implementare una funzione di diagnostica delle transizioni di stagione. Per ogni stagione riporta: squadre, squadre entrate (nuove e tornanti), squadre uscite, ultime tre calcolate.
6. Scrivere tests/test_elo_predictor.py.
7. Rieseguire la suite veloce.

Vincoli:
- Nessun commit e nessuna operazione git che modifichi lo stato del repository.
- Commenti e docstring in italiano; identificatori, messaggi delle eccezioni e nomi dei test in inglese.
- Rispettare la sezione "Convenzioni del progetto" di .agent/PROTOCOLLO.md.
- Ogni comando Python con .\.venv\Scripts\python.exe.
- Proporre il piano e fare le domande prima di scrivere codice.
- Nessuna dipendenza nuova.
- Non modificare src/shk/data/, src/shk/market/ né config/split.toml.
- Non correggere nomi squadra senza chiederlo.
- I test anti-leakage non si marcano slow. I test sui dati reali si saltano con motivo esplicito se data/raw/E0/ non contiene CSV.
- A fine task scrivere .agent/report/T21.md, unico file di .agent/ modificabile, con sezioni distinte: percorsi dei file modificati, creati o rimossi; esito di ciascun criterio; valori misurati; deviazioni dal piano; cose non fatte; comandi eseguiti. Fatti e valori senza giudizi.

Criteri di accettazione:
- Invarianza al futuro, su dati sintetici con più partite nello stesso giorno e almeno tre stagioni con neopromosse nuove e tornanti. Si alterano FTR, FTHG e FTAG di tutte le partite con Date ≥ d: le previsioni delle partite con Date ≤ d restano identiche, con uguaglianza esatta. Il criterio vale per più valori di d, compreso il primo giorno di una stagione.
- Un mutante che aggiorna i rating con la partita prima di prevederla è rilevato dal criterio precedente. Il mutante sta nel test, come in T19.
- assert_no_leakage non solleva su nessuna coppia consumata dal percorso via fornitore.
- Le previsioni restano identiche se si alterano o si rimuovono tutte le colonne di quota.
- Regola delle neopromosse, su un caso sintetico costruito a mano con i rating attesi calcolati nel test: squadra rimasta, tornante, nuova, prima stagione a 1500, parità in classifica risolte con i criteri dichiarati.
- Percorso veloce e percorso via fornitore danno le stesse previsioni entro 1e-12, sui dati sintetici e sui dati reali. Sui dati reali il test copre le stagioni di training e validazione e si salta senza CSV.
- Transizioni di stagione sui dati reali (si salta senza CSV):
  - 22 squadre nel 1993-94 e nel 1994-95, 20 in ogni stagione successiva fino al 2022-23;
  - alla transizione 1994-95 → 1995-96 entrano 2 squadre ed escono 4;
  - a ogni altra transizione ne entrano 3 ed escono 3.
  
  Se il criterio non vale, fermarsi e riportare le squadre coinvolte.
- Validazioni: ValueError per FTR fuori da H, D, A e per parametri non validi; TypeError per tipi sbagliati. seasons_to_predict di tipo str dà TypeError, come in walkforward_split.
- Le previsioni sono deterministiche: due esecuzioni sugli stessi dati danno output identici. Il previsore non ha componenti aleatorie; se ne servisse una, l'RNG entra come argomento.
- Suite veloce verde.

Da misurare e riportare, senza farlo tornare:
- per ogni transizione di stagione, il numero di neopromosse nuove e tornanti;
- l'accordo fra le ultime tre calcolate e le squadre effettivamente uscite;
- i tempi dei due percorsi sui dati reali.

Esito: —

### Task 22 — Calibrazione espansiva di K, h, ν sul training e previsioni walk-forward, US-C4.1
Stato: da fare

Obiettivo: K, h e ν, e c della baseline, sono stimati solo sulle stagioni di training anteriori alle stagioni da prevedere. I valori sono congelati in un modulo di libreria. Le previsioni di training e validazione stanno in results/us_c4_1_elo_walkforward.csv, con la figura thesis/figures/us_c4_1_elo_walkforward.png.

Dipende da: T21.

Contesto:
- Split [V, R26@2026-09-29]: training 2000-01, 2010-11, 2020-21; validation 19 stagioni dal 2002-03 al 2022-23, tranne le due di training; history dal 1993-94 al 1999-00 più il 2001-02; test 2023-24, bloccato. I ruoli si leggono con read_split_config e load_by_role (src/shk/data/split.py), non si scrivono a mano.
- Il 2000-01 non ha B365 [V, R14@2026-09-29]. Qui non serve: la calibrazione usa solo i risultati.
- Previsore di T21 in src/shk/model/elo_predictor.py. Il percorso veloce, verificato uguale al percorso via fornitore, si può usare per la calibrazione.
- Schema dei fit (scelta del supervisore su delega, 2026-09-29):
  - per ogni stagione di training j, il fit "fino a j" usa tutte le stagioni di training ≤ j;
  - ogni stagione di validazione si prevede con il fit che include le stagioni di training strettamente anteriori;
  - ne risultano il fit fino al 2000-01 per le stagioni dal 2002-03 al 2009-10, il fit fino al 2010-11 per quelle dal 2011-12 al 2019-20, il fit fino al 2020-21 per il 2021-22 e il 2022-23;
  - lo schema va derivato dallo split, non scritto a mano.
- Obiettivo di un fit: la log-loss media (logaritmo naturale) delle probabilità Davidson sulle partite delle stagioni di training del fit. Una corsa walk-forward completa dal 1993-94 con un unico terno (K, h, ν) produce quelle probabilità. Per la baseline, c è la frequenza del pareggio sulle stesse partite.
- Convenzioni degli script [V, R8@2026-09-28 e R1@2026-09-29b]:
  - matplotlib.use("Agg") prima di pyplot;
  - run_experiment() senza parametri, chiamata dal blocco __main__;
  - CSV con csv.DictWriter, open(mode="w", newline="", encoding="utf-8"), float nativi, stringa vuota per i valori non applicabili;
  - PNG con tight_layout e savefig(dpi=150), etichette in italiano;
  - i parametri condivisi da script e test stanno in un modulo di libreria.

Da verificare prima di iniziare: nessuna.

Passi richiesti:
1. Proporre il piano: metodo di ottimizzazione deterministico, tolleranza, limiti di ricerca (K ∈ [5, 80], h ∈ [0, 200], ν ∈ [0.05, 3]) e stima del tempo.
2. Creare src/shk/model/elo_fit.py con la funzione obiettivo, la stima di un fit e lo schema dei fit derivato dallo split.
3. Eseguire la calibrazione e riportare i valori.
4. Congelare i valori nella costante ELO_FITS di elo_fit.py: chiave = ultima stagione di training del fit, valori K, h, ν, c a precisione piena. La data di calibrazione va nella docstring.
5. Creare scripts/us_c4_1_elo_walkforward.py, che carica i dati solo con load_by_role e scrive il CSV e la figura.
   - Il CSV ha, per ogni fit, le righe delle sue stagioni di training (role = training) e delle stagioni di validazione che gli spettano (role = validation).
   - Colonne del CSV: fit_through, role, season, date (YYYY-MM-DD), home_team, away_team, ftr, home_promotion, away_promotion, rating_home, rating_away, delta, p_home, p_draw, p_away.
   - Figura: profili della log-loss di training di ciascun fit in funzione di K (h e ν all'ottimo) e di h (K e ν all'ottimo), su due pannelli.
6. Scrivere tests/test_us_c4_1_acceptance.py.
7. Eseguire lo script due volte e confrontare gli SHA256.
8. Rieseguire la suite veloce.

Vincoli:
- Nessun commit e nessuna operazione git che modifichi lo stato del repository.
- Commenti e docstring in italiano; identificatori, messaggi delle eccezioni e nomi dei test in inglese.
- Rispettare la sezione "Convenzioni del progetto" di .agent/PROTOCOLLO.md.
- Ogni comando Python con .\.venv\Scripts\python.exe.
- Proporre il piano e fare le domande prima di scrivere codice.
- Nessuna dipendenza nuova.
- Non modificare src/shk/data/, src/shk/market/ né config/split.toml.
- Se un ottimo cade su un limite di ricerca, riportarlo senza allargare i limiti.
- I test sui dati reali si saltano con motivo esplicito se data/raw/E0/ non contiene CSV. Un test sui dati reali che supera 60 s si marca slow e si dichiara nel report.
- CSV e PNG sono nuovi e vanno committati dal programmatore.
- A fine task scrivere .agent/report/T22.md, unico file di .agent/ modificabile, con sezioni distinte: percorsi dei file modificati, creati o rimossi; esito di ciascun criterio; valori misurati; deviazioni dal piano; cose non fatte; comandi eseguiti. Fatti e valori senza giudizi.

Criteri di accettazione:
- Solo training, su dati sintetici: alterare i risultati delle partite non di training posteriori all'ultima stagione di training del fit non cambia il terno stimato.
- L'obiettivo di ogni fit è una media esattamente sulle partite delle sue stagioni di training. Sui dati reali sono 380, 760 e 1 140 partite (si salta senza CSV).
- Nel CSV nessuna riga di validazione usa un fit che contenga una stagione di training uguale o successiva alla stagione prevista. Ogni stagione di validazione compare una sola volta.
- ELO_FITS coincide con la ricalibrazione dai dati entro math.isclose rel_tol 1e-9 (si salta senza CSV).
- Test sul CSV versionato, che girano anche senza dati: colonne nell'ordine dichiarato; stagioni e conteggi per fit e ruolo; p_home + p_draw + p_away = 1 entro 1e-12.
- Il ricalcolo dai dati coincide con il CSV versionato entro math.isclose con rel_tol e abs_tol 1e-12. Le colonne non numeriche si confrontano esattamente. Si salta senza CSV.
- Due esecuzioni dello script danno CSV identici byte per byte; SHA256 nel report.
- Suite veloce verde.

Da misurare e riportare, senza farlo tornare:
- K, h, ν e c di ciascun fit, e se stanno su un limite;
- per ciascun fit, log-loss di training e di validazione con Davidson e con la baseline a pareggio costante;
- frequenza del pareggio sulle partite di training di ciascun fit;
- media dei rating all'inizio di ogni stagione, cioè l'effetto dei tornanti sulla somma zero;
- durata della calibrazione e dello script.

Esito: —

### Task 23 — ĝ del Modulo 1 contro il mercato de-viggato, US-C4.2
Stato: da fare

Obiettivo: ĝ è calcolato e riportato col segno, sulle stagioni di validazione, per due serie di q e tre metodi di de-vigging, insieme alla sua serie cumulativa. I risultati stanno in results/us_c4_2_g_hat.csv, con la figura thesis/figures/us_c4_2_g_hat.png.

Dipende da: T22.

Contesto:
- Formula: ĝ = (1/T) Σ_t [ln p_t(x_t) − ln q_t(x_t)] = LL(q) − LL(p), dove LL è la log-loss media col logaritmo naturale e x_t è l'esito realizzato (note 2.4 §8).
- Previsioni del modello: le righe di validazione, ciascuna stagione con il suo fit. Si ricalcolano dalla libreria con ELO_FITS (src/shk/model/elo_fit.py), senza leggere il CSV di T22. I dati si caricano solo con load_by_role.
- Serie di q (scelta del supervisore su delega, 2026-09-29), con ordine degli esiti H, D, A:
  - "b365_prematch": B365H, B365D, B365A, completa in tutte le stagioni dal 2002-03 al 2022-23 [V, R14@2026-09-29];
  - "pinnacle_closing": PSCH, PSCD, PSCA, colonne presenti dal 2012-13 [V, R8@2026-09-29, solo presenza] e usate sulle stagioni di validazione dal 2012-13.
- Le colonne di chiusura non sono nella whitelist del fornitore [V, R46@2026-09-29]. Si leggono dal DataFrame caricato e si abbinano per season, Date, HomeTeam e AwayTeam, solo per la valutazione: il modello non le vede.
- De-vigging (src/shk/market/devig.py) [V, R30–R36@2026-09-29 e R1@2026-09-29b]:
  - devig_proportional, devig_additive e devig_power ricevono un ndarray (N, 3);
  - quote non finite o ≤ 1 danno ValueError, quindi vanno filtrate prima;
  - l'additivo restituisce una riga di NaN dove un q ≤ 0, e quella partita si esclude per tutti i metodi (decisione S3);
  - devig_power solleva RuntimeError se anche un solo mercato non converge.

Da verificare prima di iniziare:
- Completezza di PSCH/PSCD/PSCA nelle stagioni di validazione dal 2012-13 [D]: leggere le righe 1x2_closing di Pinnacle in results/us_c3_1_data_coverage.csv.
- Convergenza di devig_power sulle quote reali di chiusura [D]. Se solleva, fermarsi e riportare, senza cambiare tolleranza o numero di iterazioni.

Passi richiesti:
1. Proporre il piano.
2. Creare src/shk/model/scoring.py con: log-loss per partita e media, termini di ĝ, ĝ, serie cumulativa.
3. Creare scripts/us_c4_2_g_hat.py, che scrive CSV e figura.
   - Il CSV è in formato lungo con colonne level, series, method, t, season, date, matches_used, matches_excluded, log_loss_model, log_loss_market, g_hat.
   - Le righe level = summary sono 6: 2 serie × 3 metodi.
   - Le righe level = cumulative sono una per partita, per serie e metodo, con t, season, date e g_hat.
   - Figura: un pannello per serie, con ĝ cumulativo per i tre metodi e la linea dello zero; etichette in italiano.
4. Scrivere tests/test_scoring.py e tests/test_us_c4_2_acceptance.py.
5. Eseguire lo script due volte e confrontare gli SHA256.
6. Rieseguire la suite veloce.

Vincoli:
- Nessun commit e nessuna operazione git che modifichi lo stato del repository.
- Commenti e docstring in italiano; identificatori, messaggi delle eccezioni e nomi dei test in inglese.
- Rispettare la sezione "Convenzioni del progetto" di .agent/PROTOCOLLO.md.
- Ogni comando Python con .\.venv\Scripts\python.exe.
- Proporre il piano e fare le domande prima di scrivere codice.
- Nessuna dipendenza nuova.
- Non modificare src/shk/data/, src/shk/market/, config/split.toml né ELO_FITS.
- Esito informativo: nessun parametro, filtro o metodo si cambia in funzione del valore o del segno di ĝ.
- I test sui dati reali si saltano con motivo esplicito senza CSV.
- CSV e PNG sono nuovi e vanno committati dal programmatore.
- A fine task scrivere .agent/report/T23.md, unico file di .agent/ modificabile, con sezioni distinte: percorsi dei file modificati, creati o rimossi; esito di ciascun criterio; valori misurati; deviazioni dal piano; cose non fatte; comandi eseguiti. Fatti e valori senza giudizi.

Criteri di accettazione:
- Stesse partite: in ogni serie, modello e mercato si valutano sulle stesse partite, e i tre metodi di de-vigging usano lo stesso insieme. Le esclusioni si contano per causa: quota mancante, quota non valida, additivo non applicabile.
- In ogni riga di riepilogo, g_hat = log_loss_market − log_loss_model entro 1e-12, riportato col segno.
- Serie cumulativa: ĝ_t è la media dei primi t termini in ordine cronologico (Date, poi ordine di riga). L'ultimo valore coincide con il riepilogo entro 1e-12.
- Test unitari: con p = q, ĝ = 0 entro 1e-15; un caso piccolo calcolato a mano torna entro 1e-12; validazioni con ValueError e TypeError.
- Test sul CSV versionato, che girano anche senza dati: colonne, 6 righe di riepilogo, righe cumulative coerenti con matches_used.
- Il ricalcolo dai dati coincide con il CSV entro math.isclose con rel_tol e abs_tol 1e-12 (si salta senza CSV).
- Due esecuzioni dello script danno CSV identici byte per byte; SHA256 nel report.
- Suite veloce verde.

Da misurare e riportare, senza farlo tornare:
- ĝ col segno per ciascuna serie e metodo, e se il segno cambia fra i metodi;
- log-loss di modello e mercato;
- partite usate ed escluse per causa;
- ĝ cumulativo a fine di ogni stagione, letto dalla serie.

Esito: —

### Task 24 — Calibrazione del Modulo 1: reliability, Brier e ricalibrazione, US-C4.3
Stato: da fare

Obiettivo: sulle stagioni di validazione sono misurati reliability, Brier e log-loss del modello, grezzo e ricalibrato con isotonica e Platt, e ĝ dopo la ricalibrazione. I risultati stanno in results/us_c4_3_calibration.csv, con la figura thesis/figures/us_c4_3_calibration.png.

Dipende da: T23.

Contesto:
- Previsioni per fit dalla libreria con ELO_FITS (T22). Partite, q e metodi come in T23, con le funzioni di src/shk/model/scoring.py.
- Ricalibrazione con lo stesso schema espansivo di T22 (scelta del supervisore su delega, 2026-09-29):
  - per ogni fit, le mappe si stimano sulle previsioni delle sue stagioni di training e si applicano alle stagioni di validazione dello stesso fit;
  - lo schema è one-vs-rest per esito, seguito da rinormalizzazione a somma 1;
  - Platt: σ(a·logit(p) + b) stimata per massima verosimiglianza;
  - isotonica: regressione monotona non decrescente.
- Prima della rinormalizzazione le probabilità si limitano a [1e-6, 1 − 1e-6], per evitare log(0). Scelta del supervisore.
- Reliability e Brier si calcolano sulle partite della serie b365_prematch di T23.
- SciPy nel venv è la 1.18.1 [V, R10@2026-09-29]. Le dipendenze non hanno vincoli di versione [V, R1@2026-09-29b].

Da verificare prima di iniziare: disponibilità di scipy.optimize.isotonic_regression nel venv [D]. Se manca, fermarsi e chiedere, senza aggiungere dipendenze.

Passi richiesti:
1. Proporre il piano.
2. Creare src/shk/model/recalibration.py con: stima e applicazione di isotonica e Platt, tabella di reliability, Brier multiclasse.
3. Creare scripts/us_c4_3_calibration.py, che scrive CSV e figura.
   - Colonne del CSV: level, version, series, method, outcome, bin_lower, bin_upper, count, mean_predicted, observed_frequency, gap, z, matches_used, log_loss, brier, g_hat.
   - level = reliability per le righe dei bin; level = score per log-loss, Brier e ĝ.
   - version vale raw, isotonic, platt o market.
   - Figura: pannello aggregato con le tre versioni e la diagonale; pannello per esito con la versione grezza; etichette in italiano.
4. Scrivere tests/test_recalibration.py e tests/test_us_c4_3_acceptance.py.
5. Eseguire lo script due volte e confrontare gli SHA256.
6. Rieseguire la suite veloce.

Vincoli:
- Nessun commit e nessuna operazione git che modifichi lo stato del repository.
- Commenti e docstring in italiano; identificatori, messaggi delle eccezioni e nomi dei test in inglese.
- Rispettare la sezione "Convenzioni del progetto" di .agent/PROTOCOLLO.md.
- Ogni comando Python con .\.venv\Scripts\python.exe.
- Proporre il piano e fare le domande prima di scrivere codice.
- Nessuna dipendenza nuova.
- Non modificare src/shk/data/, src/shk/market/, config/split.toml né ELO_FITS.
- Nessuna scelta fra isotonica e Platt nel codice: si riportano entrambe.
- Esiti informativi: nessun parametro si cambia in funzione dei risultati.
- CSV e PNG sono nuovi e vanno committati dal programmatore.
- A fine task scrivere .agent/report/T24.md, unico file di .agent/ modificabile, con sezioni distinte: percorsi dei file modificati, creati o rimossi; esito di ciascun criterio; valori misurati; deviazioni dal piano; cose non fatte; comandi eseguiti. Fatti e valori senza giudizi.

Criteri di accettazione:
- Reliability su 10 bin di ampiezza 0.1 in [0, 1], chiusi a sinistra, con l'ultimo chiuso anche a destra.
  - Si calcola in forma aggregata (outcome = all, tre coppie per partita) e per esito (H, D, A), per raw, isotonic e platt.
  - Per ogni bin: conteggio, probabilità media, frequenza osservata, scarto (frequenza − probabilità) e z = scarto / √(p̄(1 − p̄)/n).
  - Un bin vuoto ha conteggio 0 e le altre colonne vuote.
- Brier multiclasse (somma sui tre esiti, media sulle partite) riportato accanto alla log-loss, per raw, isotonic, platt e per il mercato con i tre metodi, sulle stesse partite di T23 e per entrambe le serie.
- Il report elenca le fasce peggio calibrate: i tre bin con |z| maggiore in forma aggregata e per ciascun esito, per la versione raw.
- Le probabilità ricalibrate sommano a 1 entro 1e-12. Il numero di valori limitati a [1e-6, 1 − 1e-6] è contato.
- Fuori campione, su dati sintetici: alterare gli esiti delle stagioni di validazione non cambia le mappe di ricalibrazione.
- ĝ dopo la ricalibrazione, per isotonic e platt, per serie e metodo, sulle stesse partite di T23. Con la versione raw coincide con T23 entro 1e-12.
- Il ricalcolo dai dati coincide con il CSV entro math.isclose con rel_tol e abs_tol 1e-12 (si salta senza CSV). I test di struttura sul CSV versionato girano anche senza dati.
- Due esecuzioni dello script danno CSV identici byte per byte; SHA256 nel report.
- Suite veloce verde.

Da misurare e riportare, senza farlo tornare:
- scarti e z per bin;
- fasce peggio calibrate;
- log-loss e Brier di raw, isotonic, platt e mercato;
- ĝ prima e dopo la ricalibrazione, per serie e metodo;
- numero di valori limitati.

Esito: —

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
- La decisione sullo scenario di training 2000-01 senza B365 resta aperta (S3). Qui non blocca: ĝ si misura solo sulla validazione.

### Resta al programmatore per S4
- Confermare o cambiare le scelte fatte dal supervisore su delega il 2026-09-29:
  - q con serie principale B365 pre-partita e seconda serie Pinnacle chiusura dal 2012-13;
  - calibrazione espansiva di K, h, ν e della ricalibrazione;
  - retrocesse identificate dalla classifica calcolata;
  - limite [1e-6, 1 − 1e-6] nella ricalibrazione.
- Correggere o dichiarare la tabella di Davidson delle note 2.8 §3.3: è calcolata con 10^(ΔR/200), mentre il modello usa la scala 400 del punteggio atteso.
- US-C4.2, esito informativo: scrivere l'introduzione della tesi in base al segno di ĝ, dichiarandolo in apertura e non nei limiti (note 2.4 §6).
- Dichiarare in tesi: il mapping Davidson e la sensibilità rispetto alla baseline a pareggio costante; la regola per le neopromosse; lo schema espansivo degli iperparametri.
- US-C4.3: decidere, dai numeri di T24, se serve una ricalibrazione e quale adottare, isotonica o Platt, da congelare.
- Committare codice, CSV e figure di T20–T24.