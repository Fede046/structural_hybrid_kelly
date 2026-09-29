# Backlog
Ultimo task: T19

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

## Story S3 — C3 Primo contatto coi dati reali: copertura, split congelato, de-vigging, anti-leakage
Aperta il 2026-09-29. Sei task (T14–T19), in deroga alla regola dei cinque per decisione del programmatore (2026-09-29): due chat di esecuzione, la prima per T14–T16 e la seconda per T17–T19, con in mezzo il commit di config/split.toml fatto dal programmatore.

**Interpretazione:** unisce US-C3.1, US-C3.2, US-C3.3 e US-C3.4. Si caricano tutte le stagioni di Premier League di football-data.co.uk e se ne misura la copertura (quote, risultati, bookmaker); si congela lo split su file prima di qualunque risultato, con il test set bloccato da codice; si implementano tre metodi di de-vigging e se ne misura la divergenza sulle sole stagioni non di test; si rende automatico il controllo anti-leakage su un fornitore walk-forward che la pipeline di C4 riuserà.

**Assunzioni fatte:** (scelte del supervisore su delega del programmatore del 2026-09-29, da confermare)
- Dati: un CSV E0 di football-data.co.uk per stagione, in data/raw/E0/<stagione>.csv con stagione nel formato YYYY-YY (es. data/raw/E0/1993-94.csv), scaricati dal programmatore prima di T14, dal 1993-94 all'ultima stagione disponibile. La stagione è una stringa YYYY-YY nella colonna season.
- pandas entra fra le dipendenze runtime di pyproject.toml senza vincolo di versione, come le altre; pyproject.toml resta la fonte di verità e uv.lock va segnalato come da aggiornare (punto incerto della scheda). Il file di split si legge con tomllib della libreria standard (Python ≥ 3.11).
- Split coerente con KellyBench (piano §7.3, note 2.7 §6.2, US-C8.2): training 2000-01, 2010-11, 2020-21; test 2023-24. La variante "literature" del 2023/24 non è ricostruibile da football-data.
- Validazione fuori campione: le stagioni anteriori al 2023-24, non di training, con la terna Bet365 pre-partita completa secondo l'audit di T15. Tutte le stagioni dal 2023-24 in poi sono bloccate insieme al test, perché la storia walk-forward di una stagione successiva conterrebbe le partite del test.
- La fase è dichiarata nel file: test_unlocked = false finché i parametri non sono congelati (US-C8.2); lo sblocco lo fa il programmatore a mano, con data e commit. La cronologia dei commit rende verificabile l'ordine.
- Ordine: audit su tutte le stagioni, test compreso, ma solo conteggi di righe, mancanti e validità, senza statistiche su quote o esiti (T15); poi lo split congelato (T16); poi il de-vigging sui dati, solo sulle stagioni non bloccate (T18).
- La colonna che alimenta q è la terna Bet365 pre-partita B365H, B365D, B365A (note 2.4 §2 chiede di dichiararla): bookmaker soft, coerente con le quote "di metà linea" del paper (note 2.1 §2).
- Quote complete in una stagione: terna H/D/A non nulla e con tutti i valori > 1 su ogni riga della stagione.
- De-vigging (note 2.1 §6.1, §6.2, §6.4): proporzionale, additivo, power; somma a 1 entro 1e-12. L'additivo è non applicabile a un mercato con un q ≤ 0: quel mercato è escluso dal confronto per tutti i metodi (confronto appaiato) e contato.
- Divergenza per esito: spread = massimo meno minimo dei tre q, in punti percentuali; spread relativo = spread diviso per la media dei tre q. "Divergenza massima sugli outsider" vale in termini relativi: in punti percentuali lo spread è massimo sul favorito (mercato 1.25/6.00/11.0 delle note 2.1 §7.4: 2.79 punti sul favorito, 1.42 sull'outsider; ricalcolo del supervisore). Criterio vincolante sullo spread relativo; lo spread in punti per fascia è informativo.
- Fasce di quota dell'esito: [1, 1.5), [1.5, 2), [2, 3), [3, 5), [5, 10), [10, ∞).
- Edge tipico di riferimento: 2 punti percentuali, cioè p − 1/o nello scenario sottile di S1 (p = 0.52 a quota 2.00).
- Overround: vincolante solo l'ordine di grandezza (media fra 1% e 15%, per escludere errori di unità o di colonna); la distanza da 5.3% e dall'intervallo 2–7% del paper è informativa.
- Anti-leakage: "anteriore" significa data strettamente precedente; la partita da prevedere espone solo identificativi e quote pre-partita (non di chiusura). Il test gira in pytest nella suite veloce; la pipeline di C4 riuserà il fornitore (risposta del programmatore 2026-09-29).
- I test su dati reali si saltano con motivo esplicito se data/raw/E0/ non contiene CSV; il meccanismo è sempre coperto da test su dati sintetici.
- Fatti [V] usati senza farli verificare: dipendenze e requires-python in pyproject.toml (R1@2026-09-28; S2 non ha aggiunto dipendenze); config/ e data/raw/ con solo .gitkeep al momento di R1 (R1@2026-09-28); convenzioni degli script di esperimento (R8@2026-09-28); interprete del venv (R7@2026-09-28); confronto dei float nei CSV con math.isclose rel_tol 1e-12 (R15@2026-09-28).

**Domande aperte:**
- nessuna

### Task 14 — Caricamento di tutte le stagioni E0 in un unico DataFrame

Stato: fatto

Obiettivo: una funzione legge tutti i CSV di data/raw/E0/ e restituisce un unico DataFrame con la colonna season e le date interpretate, coperta da test.

Dipende da: nessuno.

Contesto:
- pyproject.toml: dipendenze runtime numpy, scipy, matplotlib; dev solo pytest; nessun vincolo di versione; pandas assente [V, R1@2026-09-28].
- data/raw/ conteneva solo .gitkeep [V, R1@2026-09-28]; la presenza dei CSV scaricati dal programmatore non è verificata [D].
- File attesi: data/raw/E0/<stagione>.csv, con stagione nel formato YYYY-YY (es. 1993-94.csv, 2023-24.csv), uno per stagione di Premier League da football-data.co.uk. Le intestazioni cambiano fra stagioni e la colonna Date usa gg/mm/aa in alcune stagioni e gg/mm/aaaa in altre [D].
- Modello per un __init__ di pacchetto: src/shk/stats/__init__.py, sola docstring in italiano, nessun import [V, R5@2026-09-28]. Un pacchetto src/shk/data/ non compare nella scheda [D].
- Convenzioni: type hints completi, docstring stile NumPy con sezioni Parametri / Restituisce / Solleva, validazione in apertura (ValueError per i valori, TypeError per i tipi) [V, R1 e R5@2026-09-28].

Da verificare prima di iniziare:
- Che data/raw/E0/ esista e contenga i CSV con nomi nel formato YYYY-YY.csv. Se i nomi sono diversi, chiedere al programmatore: non rinominare né spostare file.
- Le intestazioni delle varie stagioni (colonne diverse, colonne senza nome, righe vuote in coda) e il formato di Date in ciascuna.
- La codifica dei file (se qualche file non si legge in UTF-8, riportarlo e proporre la codifica da usare).
- Che src/shk/data/ non esista già.

Passi richiesti:
1. Aggiungere pandas alle dipendenze runtime di pyproject.toml, senza vincolo di versione; reinstallare nel venv con .\.venv\Scripts\python.exe -m pip install -e ".[dev]"; annotare la versione di pandas installata. Non toccare uv.lock.
2. Creare src/shk/data/__init__.py con la sola docstring di modulo in italiano.
3. Creare src/shk/data/loading.py con una costante per la directory predefinita data/raw/E0 e la funzione load_all_seasons, che legge ogni CSV della directory, ricava la stagione dal nome del file, aggiunge la colonna season, interpreta Date come datetime64 con il giorno per primo, scarta le righe interamente vuote, e concatena le stagioni in ordine cronologico di stagione e, dentro la stagione, di data (ordinamento stabile). Le colonne originali mantengono il nome originale; l'insieme delle colonne è l'unione fra le stagioni, con valori mancanti dove una stagione non ha la colonna.
4. Validare il nome del file: formato YYYY-YY con anno finale uguale all'anno iniziale più uno (modulo 100); altrimenti ValueError. Directory inesistente → FileNotFoundError; directory senza CSV, data non interpretabile o data fuori dalla finestra della sua stagione → ValueError. La finestra di una stagione va dal 1° luglio dell'anno iniziale al 31 agosto dell'anno finale.
5. Creare tests/test_data_loading.py con test su CSV sintetici scritti in tmp_path: due stagioni con colonne diverse, entrambi i formati di data, righe vuote in coda, nome non conforme, data fuori finestra, directory vuota o inesistente.
6. Aggiungere un test sui dati reali, saltato con motivo esplicito se data/raw/E0/ non contiene CSV: una stagione per file, nessuna Date nulla, tutte le date nella finestra della propria stagione.
7. Eseguire la suite veloce e il test sui dati reali.

Vincoli:
- Nessun commit e nessuna operazione git che modifichi lo stato del repository.
- Commenti e docstring in italiano; inglese per identificatori, messaggi delle eccezioni e nomi dei test.
- Rispettare le convenzioni della sezione "Convenzioni del progetto" di .agent/PROTOCOLLO.md.
- Nessuna occorrenza di try:, print( o logging in src/.
- Ogni comando Python con .\.venv\Scripts\python.exe.
- Non modificare i file in data/raw/, uv.lock, src/shk/kelly/, src/shk/stats/, i test esistenti, results/ e thesis/figures/.
- Prima di scrivere codice, proporre il piano e fare le domande necessarie.
- A fine task, scrivere il report in .agent/report/T14.md, unico file di .agent/ modificabile, con sezioni distinte: percorsi dei file modificati, creati o rimossi; esito di ciascun criterio di accettazione; valori misurati; deviazioni dal piano; cose non fatte (fra queste uv.lock da aggiornare); comandi eseguiti. Fatti e valori senza giudizi; interpretazioni solo in una sezione a parte, se richieste.

Criteri di accettazione:
- pandas compare fra le dipendenze runtime di pyproject.toml ed è importabile nel venv.
- load_all_seasons restituisce un unico DataFrame con la colonna season, con una stagione per ogni file letto, e Date di tipo datetime64 senza valori nulli.
- Ogni data cade nella finestra della propria stagione (test sintetico e test sui dati reali).
- Le righe interamente vuote sono scartate (test sintetico).
- Le validazioni sollevano le eccezioni previste (test).
- La suite veloce è verde; il numero dei test nuovi è riportato.

Da misurare e riportare, senza farlo tornare: sui dati reali, numero di stagioni caricate, righe totali e per stagione, righe vuote scartate per stagione, numero di colonne per stagione, versione di pandas installata.

Esito: 2026-09-29 — file toccati: pyproject.toml, src/shk/data/__init__.py, src/shk/data/loading.py, tests/test_data_loading.py. Deviazioni: il programmatore ha scaricato solo le stagioni dal 1993-94 al 2023-24, la finestra di KellyBench, invece che fino all'ultima stagione disponibile (decisione del programmatore 2026-09-29). Scelte fissate dal supervisore nel piano: decodifica per file (BOM → utf-8-sig, UTF-8 valido → utf-8, altrimenti cp1252; il 2004-05 esce in cp1252 per 9 byte 0xA0 davanti ai nomi degli arbitri, il 2021-22 ha il BOM); colonne senza nome scartate solo se vuote, altrimenti ValueError; campi in eccesso tagliati solo se vuoti; formato di Date esplicito per file (%d/%m/%y o %d/%m/%Y); tipi inferiti da pd.read_csv; DEFAULT_DATA_DIR calcolata dalla radice del repository. Non fatto: uv.lock da aggiornare; il test sui dati reali non gira in CI perché .gitignore esclude data/raw/*. Valori misurati: 31 stagioni; 11 944 righe (462 nel 1993-94 e nel 1994-95, 380 nelle altre); 697 righe vuote scartate (90 nel 1993-94, 90 nel 1994-95, 172 nel 1995-96, 172 nel 1996-97, 172 nel 1999-00, 1 nel 2014-15, 0 altrove); colonne con nome per stagione da 7 (1993-94 e 1994-95) a 106 (dal 2019-20); 161 colonne distinte più season; pandas 3.0.6, numpy 2.5.2 e scipy 1.18.1 invariate; suite veloce 109 → 127 verdi (18 test nuovi), 14 deselezionati. Report: .agent/report/T14.md.
### Task 15 — Audit della copertura di quote, risultati e bookmaker per stagione (US-C3.1)
Stato: fatto

Obiettivo: un CSV e una figura riportano, per ogni stagione, righe, mancanti e valori non validi di risultati e quote per bookmaker, e il report indica la prima stagione con quote complete confrontata col 2002-03.

Dipende da: Task 14.

Contesto:
- load_all_seasons in src/shk/data/loading.py restituisce tutte le stagioni in un unico DataFrame con colonna season e Date datetime64 (Task 14; leggere .agent/report/T14.md).
- Nomi di colonna attesi in football-data.co.uk, tutti [D] (note di tesi 2.9 §2.4 e 2.4 §2): risultati FTHG, FTAG, FTR; terne 1X2 pre-partita <P>H, <P>D, <P>A per bookmaker (es. B365, IW, GB, WH, LB, SB, VC, PS); terne di chiusura con C dopo il prefisso (es. B365CH, PSCH); aggregatori (prefissi Bb, Max, Avg); altri mercati (colonne con >2.5 o <2.5, colonne AH).
- Convenzioni degli script di esperimento: matplotlib.use("Agg") prima di importare pyplot; run_experiment() senza parametri chiamata dal blocco __main__; nessun argomento da riga di comando; CSV con csv.DictWriter, open(mode="w", newline="", encoding="utf-8"); float nativi e stringa vuota per i non applicabili; PNG con plt.tight_layout() e savefig(dpi=150); etichette in italiano [V, R8 e R9@2026-09-28]. Colonne del CSV definite come costante in un modulo di libreria importato da script e test [V, R1@2026-09-28].
- Definizione adottata nella story: una terna 1X2 è completa in una stagione se non ha valori nulli ed è > 1 su ogni riga della stagione. La stagione di riferimento del paper per l'inizio delle quote è il 2002-03.

Da verificare prima di iniziare:
- Le intestazioni reali di tutte le stagioni, per costruire la regola di classificazione delle colonne quote.
- Quali colonne dei risultati esistono in ogni stagione (FTHG, FTAG, FTR sono dedotte).

Passi richiesti:
1. Nel piano, riportare l'elenco delle colonne quote trovate e proporre la regola di classificazione in quattro gruppi: 1X2 pre-partita per bookmaker, 1X2 di chiusura per bookmaker, aggregatori, altri mercati. Attendere l'approvazione del programmatore.
2. Creare src/shk/data/coverage.py con la classificazione approvata e una funzione che produce, per stagione e per gruppo di colonne (risultati FTHG/FTAG/FTR come un gruppo; ogni terna 1X2 come un gruppo; ogni famiglia di altri mercati come un gruppo), il numero di righe, di righe con valori mancanti, di righe con quote non valide (≤ 1 o non numeriche) e il flag di completezza. Le colonne del CSV sono una costante del modulo.
3. Creare scripts/us_c3_1_data_coverage.py, che scrive results/us_c3_1_data_coverage.csv in formato lungo (una riga per stagione × gruppo di colonne, con il tipo di gruppo) e thesis/figures/us_c3_1_data_coverage.png (mappa stagione × gruppo con la quota di righe complete, etichette in italiano).
4. Creare tests/test_coverage.py con test su DataFrame sintetici: classificazione dei quattro gruppi, conteggi di mancanti e non validi, flag di completezza, stagione con una terna assente.
5. Eseguire lo script due volte e confrontare gli SHA256 dei due CSV.
6. Riportare nel report la tabella bookmaker × stagioni (presenza e completezza) ricavata dal CSV.

Vincoli:
- Nessun commit e nessuna operazione git che modifichi lo stato del repository.
- Commenti e docstring in italiano; inglese per identificatori, messaggi delle eccezioni e nomi dei test.
- Rispettare le convenzioni della sezione "Convenzioni del progetto" di .agent/PROTOCOLLO.md.
- Nessuna occorrenza di try:, print( o logging in src/ e scripts/.
- Ogni comando Python con .\.venv\Scripts\python.exe.
- L'audit legge tutte le stagioni, 2023-24 e successive comprese, ma produce solo conteggi di righe, mancanti, non validi e completezza: nessuna statistica sui valori di quote o di esiti (medie, overround, frequenze di vittoria), né nel CSV né nel report.
- Non modificare src/shk/data/loading.py salvo correzioni di difetti, da dichiarare fra le deviazioni; non toccare src/shk/kelly/, src/shk/stats/, i test esistenti e i risultati di C1 e C2.
- Prima di scrivere codice, proporre il piano e fare le domande necessarie.
- A fine task, scrivere il report in .agent/report/T15.md, unico file di .agent/ modificabile, con sezioni distinte: percorsi dei file modificati, creati o rimossi; esito di ciascun criterio di accettazione; valori misurati; deviazioni dal piano; cose non fatte; comandi eseguiti. Fatti e valori senza giudizi; interpretazioni solo in una sezione a parte, se richieste.

Criteri di accettazione:
- results/us_c3_1_data_coverage.csv contiene una riga per ogni combinazione di stagione caricata e gruppo di colonne presente; thesis/figures/us_c3_1_data_coverage.png esiste.
- Per ogni stagione sono riportati il numero di righe e il numero di mancanti nei risultati e in ogni terna di quote.
- Sono identificate la prima stagione con quote complete (almeno una terna 1X2 pre-partita completa) e la prima stagione con la terna B365 pre-partita completa, e per ciascuna è riportata la differenza in stagioni, col segno, rispetto al 2002-03.
- La prima stagione con risultati completi precede la prima stagione con quote complete, ed è riportata la distanza in stagioni. Se non la precede, riportare quali file sono stati caricati e fermarsi: è un problema dei dati di ingresso da far esaminare al programmatore.
- Due esecuzioni dello script producono CSV identici byte per byte.
- La suite veloce è verde; il numero dei test nuovi è riportato.

Da misurare e riportare, senza farlo tornare: prima stagione con quote complete e suo scarto dal 2002-03; prima stagione con B365 completa; se la stagione 2000-01 ha qualche terna 1X2 e con quale completezza; completezza di B365 nelle stagioni 2010-11 e 2020-21; distanza in stagioni fra primi risultati e prime quote; bookmaker presenti per stagione; stagioni con numero di righe diverso da 380; SHA256 del CSV.

Esito: 2026-09-29 — file toccati: src/shk/data/coverage.py, scripts/us_c3_1_data_coverage.py, tests/test_coverage.py, results/us_c3_1_data_coverage.csv, thesis/figures/us_c3_1_data_coverage.png. Deviazioni: classificazione approvata dal programmatore (opzione A). classify_column è pubblica e restituisce una NamedTuple (group_type, group_name, source, market, timing, kind); gli aggregatori sono tutte le colonne Bb*, Max* e Avg*, con timing valorizzato (MaxC*, AvgC* → closing); linee di handicap (AHh, AHCh, BbAHh, B365AH, GBAH, LBAH) e conteggi Bb (Bb1X2, BbOU, BbAH) sono gruppi a sé, con soli mancanti; le colonne non classificate danno ValueError; le 7 statistiche di gara del 2000-02 sono escluse dall'audit; al CSV è aggiunta la colonna complete_rows. Un test (esclusione delle colonne di statistica e primo tempo) è stato aggiunto con un correttivo del supervisore. Non fatto: commit di codice, CSV e PNG, a carico del programmatore. Valori misurati: prima stagione con quote complete 2000-01 (terne GB, IW, SB, WH complete; LB 325/380), scarto −2 dal 2002-03; prima stagione con B365 completa 2002-03, scarto 0; B365 completa in tutte le 22 stagioni dal 2002-03 al 2023-24, quindi anche nel 2010-11 e nel 2020-21 (380/380); primi risultati completi 1993-94, distanza 7 stagioni dalle prime quote complete; stagioni con righe diverse da 380: 1993-94 e 1994-95 (462); bookmaker presenti per stagione nella tabella di T15.md; CSV di 477 righe, SHA256 F9EEA7264F5457A1728EA609CD6660BCEE9779D450099D446CC30A919D73E15C, identico su due esecuzioni; suite veloce 127 → 139 verdi (12 test nuovi), 14 deselezionati. Report: .agent/report/T15.md.
### Task 16 — Split congelato su file e blocco del test set (US-C3.3)
Stato: da fare

Obiettivo: config/split.toml fissa con data le stagioni di training, validazione e test; il codice lo legge senza ricalcolarlo; le stagioni dal primo anno di test in poi non si possono caricare finché il file non le sblocca, e dei test lo verificano.

Dipende da: Task 14, Task 15.

Contesto:
- config/ conteneva solo .gitkeep [V, R1@2026-09-28].
- tomllib della libreria standard legge i file TOML; requires-python >= 3.11 [V, R1@2026-09-28].
- load_all_seasons in src/shk/data/loading.py (Task 14); risultati di copertura in results/us_c3_1_data_coverage.csv e .agent/report/T15.md (Task 15).
- Decisione della story: training = 2000-01, 2010-11, 2020-21; test = 2023-24; validazione = stagioni anteriori al 2023-24, non di training, con la terna B365 pre-partita completa secondo il CSV di T15. Tutte le stagioni dal 2023-24 in poi sono bloccate finché test_unlocked è false. Le stagioni caricate non assegnate a nessun ruolo e anteriori al 2023-24 hanno ruolo history (dati di riscaldamento, per esempio per l'Elo).
- Lo sblocco lo fa solo il programmatore, a mano e con commit, dopo il congelamento dei parametri (US-C8.2).

Da verificare prima di iniziare:
- Nel CSV di T15, che la terna B365 pre-partita sia completa nel 2010-11 e nel 2020-21. Se non lo è in una delle due, fermarsi e chiedere al programmatore.
- L'elenco esplicito delle stagioni di validazione che ne segue.

Passi richiesti:
1. Nel piano, proporre il contenuto integrale di config/split.toml: frozen_on (data di esecuzione del task), training, validation (elenco esplicito), test, test_unlocked = false, test_unlocked_on vuoto, e un commento che rimanda a .agent/report/T15.md e alla story S3. Attendere l'approvazione del programmatore e poi scrivere il file senza modificarlo più.
2. Creare src/shk/data/split.py con la lettura del file e la sua validazione: stagioni nel formato YYYY-YY; ruoli disgiunti; test non vuoto; training e validazione anteriori al primo test; frozen_on data valida; test_unlocked booleano; test_unlocked_on vuoto se test_unlocked è false, altrimenti presente e non anteriore a frozen_on. Tipi sbagliati → TypeError, valori sbagliati → ValueError. Nessuna lista di stagioni scritta nel codice: il percorso predefinito è config/split.toml, sostituibile da argomento.
3. Aggiungere in split.py la funzione di caricamento per ruolo (training, validation, test, history), che usa lo split letto dal file: finché test_unlocked è false, chiedere il ruolo test solleva un'eccezione dedicata (TestSetLockedError) e nessun altro ruolo restituisce righe di stagioni dal primo anno di test in poi.
4. Creare tests/test_split.py con test su file sintetici in tmp_path: tutte le validazioni; cambiando il file cambia la selezione; con blocco, il ruolo test solleva TestSetLockedError; senza blocco non lo solleva; nessun ruolo diverso da test restituisce stagioni bloccate.
5. Aggiungere un test sul file reale config/split.toml: si legge ed è valido, e se test_unlocked è false il caricamento del ruolo test solleva TestSetLockedError (il test sui dati si salta con motivo esplicito se data/raw/E0/ non contiene CSV).
6. Aggiungere un test di guardia che fallisce se load_all_seasons è chiamata in un file di src/ o scripts/ diversi da src/shk/data/loading.py, src/shk/data/split.py, src/shk/data/coverage.py e scripts/us_c3_1_data_coverage.py.

Vincoli:
- Nessun commit e nessuna operazione git che modifichi lo stato del repository; il commit di config/split.toml lo fa il programmatore.
- Commenti e docstring in italiano; inglese per identificatori, messaggi delle eccezioni e nomi dei test.
- Rispettare le convenzioni della sezione "Convenzioni del progetto" di .agent/PROTOCOLLO.md.
- Nessuna occorrenza di try:, print( o logging in src/.
- Ogni comando Python con .\.venv\Scripts\python.exe.
- Non eseguire script che producano risultati e non leggere valori di quote o di esiti.
- Non modificare config/split.toml dopo l'approvazione del programmatore; non toccare src/shk/kelly/, src/shk/stats/, i test esistenti e i risultati.
- Prima di scrivere codice, proporre il piano e fare le domande necessarie.
- A fine task, scrivere il report in .agent/report/T16.md, unico file di .agent/ modificabile, con sezioni distinte: percorsi dei file modificati, creati o rimossi; esito di ciascun criterio di accettazione; valori misurati; deviazioni dal piano; cose non fatte (fra queste il commit di config/split.toml, a carico del programmatore); comandi eseguiti. Fatti e valori senza giudizi; interpretazioni solo in una sezione a parte, se richieste.

Criteri di accettazione:
- config/split.toml esiste con training, validation, test, frozen_on, test_unlocked = false e test_unlocked_on vuoto, nel contenuto approvato dal programmatore.
- Il codice legge lo split dal file: un file alternativo cambia la selezione (test).
- Con test_unlocked false, il caricamento del ruolo test solleva TestSetLockedError e nessun altro ruolo restituisce stagioni dal primo anno di test in poi (test sintetici e test sul file reale).
- Il test di guardia fallisce se load_all_seasons compare fuori dai quattro file ammessi (verificato una volta con una chiamata temporanea in un file di prova in tmp_path o con una stringa sintetica, poi rimossa).
- La suite veloce è verde; il numero dei test nuovi è riportato.

Da misurare e riportare, senza farlo tornare: elenco delle stagioni per ruolo, comprese le history e le bloccate; numero di partite per ruolo non bloccato.

Esito: —

### Task 17 — Tre metodi di de-vigging (US-C3.2, primo criterio)
Stato: da fare

Obiettivo: proporzionale, additivo e power sono disponibili come funzioni su quote decimali, restituiscono q che somma a 1 entro 1e-12 e riproducono i valori delle note di tesi 2.1 §7.

Dipende da: nessuno.

Contesto:
- Formule (note di tesi 2.1 §6.1, §6.2, §6.4): π_i = 1/o_i, S = Σπ_i, overround = S − 1; proporzionale q_i = π_i/S; additivo q_i = π_i − (S − 1)/n, con n il numero di esiti; power q_i = π_i^k con k > 0 tale che Σπ_i^k = 1 (k > 1 se S > 1, k = 1 se S = 1, k < 1 se S < 1; Σπ_i^k è decrescente in k, quindi la soluzione è unica).
- L'additivo può dare q_i ≤ 0 per esiti molto improbabili (note 2.1 §6.2): in quel caso il mercato è dichiarato non applicabile per l'additivo.
- Valori di riferimento (note 2.1 §7, riportati in percentuale con tre decimali; ricalcolati dal supervisore):
  quote (8.0, 5.5, 1.33): proporzionale 0.11807, 0.17174, 0.71019; additivo 0.10543, 0.16225, 0.73231; power 0.10603, 0.15887, 0.73510 con k = 1.0791.
  quote (1.25, 6.00, 11.0): proporzionale 0.75645, 0.15759, 0.08596; additivo 0.78081, 0.14747, 0.07172; power 0.78432, 0.14218, 0.07349 con k = 1.0887.
  quote (1.67, 2.2): proporzionale 0.56848, 0.43152; additivo 0.57213, 0.42787; power 0.57404, 0.42596 con k = 1.0824.
- Convenzioni: type hints completi, docstring stile NumPy, validazione in apertura (ValueError per i valori, TypeError per i tipi) [V, R1 e R5@2026-09-28].

Da verificare prima di iniziare: nessuna.

Passi richiesti:
1. Creare src/shk/market/__init__.py con la sola docstring di modulo in italiano.
2. Creare src/shk/market/devig.py con funzioni per probabilità implicite, overround, e i tre metodi (proporzionale, additivo, power), tutte su un array NumPy di quote decimali di forma (N, n) con n ≥ 2, una riga per mercato. Il power restituisce anche il k di ogni mercato.
3. Validazione: argomento non ndarray → TypeError; forma diversa da (N, n) con n ≥ 2, quote non finite o ≤ 1 → ValueError.
4. Additivo: per ogni mercato con almeno un q ≤ 0 l'intera riga vale NaN, senza eccezione; documentarlo nella docstring.
5. Power: risolvere k mercato per mercato con un metodo numerico la cui tolleranza garantisca il criterio sulla somma; indicare nel piano il metodo scelto.
6. Creare tests/test_devig.py: valori di riferimento; somma a 1 su 10 000 mercati a tre esiti generati con default_rng(20260929) (con quote in un intervallo realistico, da dichiarare nel piano); caso S = 1, in cui tutti e tre i metodi restituiscono π; mercato costruito con un q additivo negativo, che dà NaN sulla riga; proprietà teorica: dentro un mercato, il rapporto q_proporzionale / q_power decresce al crescere di π; validazioni.

Vincoli:
- Nessun commit e nessuna operazione git che modifichi lo stato del repository.
- Commenti e docstring in italiano; inglese per identificatori, messaggi delle eccezioni e nomi dei test.
- Rispettare le convenzioni della sezione "Convenzioni del progetto" di .agent/PROTOCOLLO.md.
- Nessuna occorrenza di try:, print( o logging in src/.
- Ogni comando Python con .\.venv\Scripts\python.exe.
- Nessun accesso a data/raw/ né ai dati reali; non toccare src/shk/kelly/, src/shk/stats/, src/shk/data/, i test esistenti e i risultati.
- Solo i tre metodi della story: Shin e odds ratio sono fuori scope.
- Prima di scrivere codice, proporre il piano e fare le domande necessarie.
- A fine task, scrivere il report in .agent/report/T17.md, unico file di .agent/ modificabile, con sezioni distinte: percorsi dei file modificati, creati o rimossi; esito di ciascun criterio di accettazione; valori misurati; deviazioni dal piano; cose non fatte; comandi eseguiti. Fatti e valori senza giudizi; interpretazioni solo in una sezione a parte, se richieste.

Criteri di accettazione:
- Per ogni metodo, |Σq − 1| ≤ 1e-12 su ogni mercato di riferimento e sui 10 000 mercati casuali (per l'additivo, sui mercati non NaN).
- I valori di riferimento sono riprodotti entro 5e-6 in probabilità (le note li riportano in percentuale con tre decimali) e i k entro 5e-5 (le note li riportano con quattro decimali).
- Con S = 1 i tre metodi restituiscono π.
- L'additivo restituisce una riga di NaN sul mercato con q negativo.
- Dentro un mercato, q_proporzionale / q_power decresce al crescere di π (test).
- Le validazioni sollevano le eccezioni previste (test).
- La suite veloce è verde; il numero dei test nuovi è riportato.

Da misurare e riportare, senza farlo tornare: massimo di |Σq − 1| per metodo sui mercati casuali; numero di mercati casuali con additivo non applicabile.

Esito: —

### Task 18 — Divergenza fra metodi di de-vigging sulle stagioni non di test (US-C3.2)
Stato: da fare

Obiettivo: un CSV e una figura riportano overround e divergenza fra i tre metodi per fascia di quota sulle stagioni di training e validazione, e il report contiene la divergenza massima confrontata con l'edge di riferimento.

Dipende da: Task 16, Task 17.

Contesto:
- Caricamento per ruolo e TestSetLockedError in src/shk/data/split.py, split in config/split.toml (Task 16; leggere .agent/report/T16.md).
- Funzioni di de-vigging in src/shk/market/devig.py (Task 17): l'additivo restituisce NaN sui mercati non applicabili.
- La colonna che alimenta q è la terna Bet365 pre-partita B365H, B365D, B365A (decisione della story). Completezza per stagione in results/us_c3_1_data_coverage.csv (Task 15).
- Definizioni della story: spread di un esito = massimo meno minimo dei tre q, in punti percentuali; spread relativo = spread diviso per la media dei tre q; fasce di quota dell'esito [1, 1.5), [1.5, 2), [2, 3), [3, 5), [5, 10), [10, ∞); edge di riferimento 2 punti percentuali (p − 1/o nello scenario sottile di S1: p = 0.52 a quota 2.00); overround atteso ≈ 5.3%, intervallo del paper 2–7% (note 2.1 §2).
- Nei mercati di esempio delle note 2.1 §7 lo spread in punti è massimo sul favorito e lo spread relativo sull'outsider: il criterio vincolante riguarda lo spread relativo.
- Convenzioni degli script di esperimento e confronto dei float nei test del CSV con math.isclose rel_tol 1e-12 [V, R8, R9 e R15@2026-09-28].

Da verificare prima di iniziare:
- Che config/split.toml sia tracciato da git e senza modifiche rispetto a HEAD, con test_unlocked = false (solo comandi git di lettura, come git status e git log). Se non è committato, fermarsi: il criterio di US-C3.3 richiede il commit prima di qualunque run che produca risultati.

Passi richiesti:
1. Caricare con la funzione per ruolo le stagioni training e validation; tenere le partite con terna B365 non nulla e > 1; contare per stagione le partite escluse.
2. Per ogni partita calcolare l'overround B365 e i q dei tre metodi. Escludere dal confronto, per tutti i metodi, i mercati in cui l'additivo è NaN, e contarli.
3. Per ogni esito calcolare spread in punti e spread relativo, e assegnarlo alla sua fascia di quota.
4. Nel piano, proporre le colonne del CSV, definite come costante in un modulo di libreria, in formato lungo con una colonna che distingue righe per fascia, per stagione e complessive. Contenuto minimo: per fascia, numero di esiti, q medio per metodo, spread in punti medio, 99° percentile e massimo, spread relativo medio; per stagione, partite usate, partite escluse, mercati esclusi per l'additivo, overround medio; complessivo, overround medio, spread massimo in punti, 99° percentile, rapporto fra spread massimo e 2 punti.
5. Creare scripts/us_c3_2_devig_divergence.py, che scrive results/us_c3_2_devig_divergence.csv e thesis/figures/us_c3_2_devig_divergence.png: pannello A con lo spread medio in punti per fascia, pannello B con lo spread relativo medio per fascia; etichette in italiano.
6. Creare tests/test_us_c3_2_acceptance.py: confronta il CSV versionato con i valori ricalcolati (float con math.isclose rel_tol 1e-12, le altre colonne come stringhe) e verifica i criteri vincolanti; i test che richiedono i dati reali si saltano con motivo esplicito se data/raw/E0/ non contiene CSV.
7. Eseguire lo script due volte e confrontare gli SHA256 dei due CSV.

Vincoli:
- Nessun commit e nessuna operazione git che modifichi lo stato del repository.
- Commenti e docstring in italiano; inglese per identificatori, messaggi delle eccezioni e nomi dei test.
- Rispettare le convenzioni della sezione "Convenzioni del progetto" di .agent/PROTOCOLLO.md.
- Nessuna occorrenza di try:, print( o logging in src/ e scripts/.
- Ogni comando Python con .\.venv\Scripts\python.exe.
- Dati solo attraverso la funzione di caricamento per ruolo, ruoli training e validation: niente load_all_seasons, nessuna modifica a config/split.toml, nessuno sblocco del test set.
- Non modificare le fasce, l'edge di riferimento o la colonna B365 per far cadere un valore in un intervallo; non toccare src/shk/kelly/, src/shk/stats/, i test esistenti e i risultati di C1 e C2.
- Prima di scrivere codice, proporre il piano e fare le domande necessarie.
- A fine task, scrivere il report in .agent/report/T18.md, unico file di .agent/ modificabile, con sezioni distinte: percorsi dei file modificati, creati o rimossi; esito di ciascun criterio di accettazione; valori misurati; deviazioni dal piano; cose non fatte; comandi eseguiti. Fatti e valori senza giudizi; interpretazioni solo in una sezione a parte, se richieste.

Criteri di accettazione:
- Per ogni metodo, |Σq − 1| ≤ 1e-12 su tutte le partite usate.
- L'overround medio complessivo è fra 1% e 15%.
- Lo spread relativo medio è massimo nella fascia [10, ∞).
- Le stagioni presenti nei dati usati sono tutte di training o di validazione (test).
- CSV e figura esistono; due esecuzioni danno CSV identici byte per byte.
- La suite veloce è verde; il numero dei test nuovi è riportato.

Da misurare e riportare, senza farlo tornare: overround medio complessivo e per stagione, con distanza da 5.3% e posizione rispetto all'intervallo 2–7%; spread in punti per fascia, e la fascia in cui è massimo; spread massimo in punti e 99° percentile, e loro rapporto con l'edge di riferimento di 2 punti; se lo spread relativo cresce in modo monotono con la fascia; partite escluse per stagione, compresa la 2000-01; mercati esclusi per l'additivo; SHA256 del CSV.

Esito: —

### Task 19 — Fornitore walk-forward e test anti-leakage (US-C3.4)
Stato: da fare

Obiettivo: un fornitore walk-forward espone, per ogni partita da prevedere, solo righe di storia con data strettamente anteriore e solo i campi pre-partita della partita stessa, e un test nella suite veloce rileva tre forme di leakage introdotte deliberatamente.

Dipende da: Task 14, Task 15, Task 16.

Contesto:
- Dati: load_all_seasons (Task 14) e caricamento per ruolo in src/shk/data/split.py (Task 16), con test set bloccato; la guardia del Task 16 ammette load_all_seasons solo in quattro file, e questo task non la estende.
- Classificazione delle colonne quote in src/shk/data/coverage.py (Task 15): 1X2 pre-partita, 1X2 di chiusura, aggregatori, altri mercati.
- Decisioni della story: "anteriore" significa data strettamente precedente, quindi le altre partite dello stesso giorno non entrano nella storia; la partita da prevedere espone solo identificativi (Div, Date, HomeTeam, AwayTeam, season, e Time dove esiste [D]) e quote pre-partita, non di chiusura; risultati, statistiche di gara, arbitro e quote di chiusura non sono ammessi. Le righe di storia contengono tutte le loro colonne.
- La pipeline di C4 non esiste: il fornitore sarà richiamato da lì (risposta del programmatore 2026-09-29). Il test gira in pytest a ogni esecuzione della suite veloce, e quindi in CI.

Da verificare prima di iniziare:
- Le colonne identificative effettivamente presenti nelle stagioni caricate (in particolare Time e Div).

Passi richiesti:
1. Creare src/shk/data/walkforward.py con un fornitore che, dato un DataFrame ordinato e l'insieme delle stagioni da prevedere, produce per ogni partita da prevedere la coppia (storia, partita): storia = righe con Date strettamente anteriore; partita = riga ridotta ai campi ammessi, scelti per inclusione esplicita (whitelist) e non per esclusione.
2. Aggiungere una funzione di controllo che, data una coppia, restituisce le violazioni (righe di storia con Date non anteriore alla partita; campi non ammessi nella partita), e una che solleva LeakageError se ce ne sono.
3. Creare tests/test_leakage.py con test su dati sintetici (più partite nello stesso giorno, stagioni consecutive): per ogni partita prevista nessuna violazione. Definire nel test tre fornitori mutanti, ciascuno con un solo difetto: confronto ≤ al posto di <; storia che include la partita stessa; partita che espone FTR o i gol. Per ciascuno il controllo deve sollevare LeakageError.
4. Aggiungere un test sui dati reali, saltato con motivo esplicito se data/raw/E0/ non contiene CSV: dati dai ruoli training, validation e history attraverso la funzione per ruolo; nessuna violazione su tutte le partite delle stagioni training e validation.
5. Misurare la durata del test sui dati reali. Se supera 30 secondi, proporre come ridurla senza escluderlo dalla suite veloce, e non marcarlo slow senza l'accordo del programmatore.

Vincoli:
- Nessun commit e nessuna operazione git che modifichi lo stato del repository.
- Commenti e docstring in italiano; inglese per identificatori, messaggi delle eccezioni e nomi dei test.
- Rispettare le convenzioni della sezione "Convenzioni del progetto" di .agent/PROTOCOLLO.md.
- Nessuna occorrenza di try:, print( o logging in src/.
- Ogni comando Python con .\.venv\Scripts\python.exe.
- Nessun accesso alle stagioni bloccate, nessuna modifica a config/split.toml, nessuna chiamata a load_all_seasons fuori dai file ammessi dal test di guardia.
- I test anti-leakage non si marcano slow: devono girare a ogni esecuzione di pytest -v.
- Non toccare src/shk/kelly/, src/shk/stats/, src/shk/market/, i test esistenti e i risultati.
- Prima di scrivere codice, proporre il piano e fare le domande necessarie.
- A fine task, scrivere il report in .agent/report/T19.md, unico file di .agent/ modificabile, con sezioni distinte: percorsi dei file modificati, creati o rimossi; esito di ciascun criterio di accettazione; valori misurati; deviazioni dal piano; cose non fatte; comandi eseguiti. Fatti e valori senza giudizi; interpretazioni solo in una sezione a parte, se richieste.

Criteri di accettazione:
- Per ogni partita prevista, tutte le righe di storia hanno Date strettamente anteriore e la partita non espone campi fuori dalla whitelist (test sintetico sempre; test sui dati reali quando i CSV sono presenti).
- Ciascuno dei tre fornitori mutanti è rilevato: il controllo solleva LeakageError (tre test distinti).
- I test anti-leakage sono nella suite veloce, senza marker slow.
- La suite veloce è verde; il numero dei test nuovi è riportato.

Da misurare e riportare, senza farlo tornare: numero di partite verificate sui dati reali per ruolo; durata del test sui dati reali; elenco dei campi della whitelist.

Esito: —

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
- Prima di T14: scaricare i CSV E0 di football-data.co.uk, dal 1993-94 all'ultima stagione disponibile, in data/raw/E0/<YYYY-YY>.csv. Decidere se versionarli, controllando la licenza (note 2.9): se non sono versionati, i test sui dati reali non girano in CI.
- Dopo T16 e prima di T18: committare config/split.toml; la data del commit è la prova del congelamento (US-C3.3, criterio 2).
- Confermare o cambiare le scelte fatte dal supervisore su delega il 2026-09-29: Bet365 pre-partita come colonna di q; validazione sulle stagioni anteriori al 2023-24 con B365 completa; blocco di tutte le stagioni dal 2023-24 in poi; edge di riferimento di 2 punti; "divergenza massima sugli outsider" letta in termini relativi.
- US-C3.1, esito informativo: scrivere in tesi la finestra effettiva di analisi e, se il 2000-01 non ha quote, la conseguenza sullo scenario di training (note 2.9 §2.2).
- US-C3.2, Definition of Done: saper dire se la divergenza fra metodi è dello stesso ordine dell'edge, e ricavare dal CSV di T18 la prima riga della tabella di sensibilità (US-C9.3).
- Correggere l'enunciato di US-C3.2 nelle note: in punti percentuali la divergenza è massima sul favorito, in termini relativi sull'outsider.
- US-C3.4: introdurre a mano, una volta, un leakage nel fornitore (per esempio < sostituito con ≤) e vedere il test rosso.
- Aggiornare uv.lock dopo l'aggiunta di pandas.
- Committare codice, CSV e figure di T14–T19.