# Metodi implementati

Documento tecnico dei metodi come sono implementati in `src/shk/`, con i parametri congelati in `config/` (T66).
Riporta formule, parametri, seed, filtri ed esclusioni; non riporta risultati, che sono in `thesis/numeri.md`.

## Convenzioni del documento

- Un riferimento al codice ha la forma `` `modulo:nome` ``, per esempio `shk.market.devig:devig_shin`; per un metodo, `` `modulo:Classe.metodo` ``.
- Una riga che inizia con "Formula:" riporta una formula come è implementata, con il riferimento alla funzione o alla classe che la calcola.
- Un parametro ha la forma `` `modulo:NOME = valore` `` (costante del codice), `` `modulo:funzione(argomento) = valore` `` (valore di default di un argomento) oppure `` `config/<file>.toml:sezione.chiave = valore` `` (file congelato o di split). Il valore è scritto come letterale Python.
- `tests/test_metodi_implementati.py` risolve ogni riferimento con un import e confronta ogni parametro col codice o col file.
- Le decisioni si citano come in "Decisioni in vigore" di `.agent/BACKLOG.md`: story e data. "Scelta delegata" indica una scelta del supervisore o dell'esecutore su delega del programmatore.
- Codifica degli esiti in tutto il codice: 0 = casa (H), 1 = pareggio (D), 2 = trasferta (A).
- Le differenze con le note di tesi sono quelle registrate nel backlog o nei moduli e ricontrollate nel testo della nota; una sezione senza il paragrafo "Differenze con le note" non ne ha di registrate.

## 1. Dati e split

**Caricamento.** Un CSV per stagione della divisione E0 di football-data.co.uk, `data/raw/E0/<YYYY-YY>.csv`, dal 1993-94 al 2023-24 (decisione S3, 2026-09-29).
- `shk.data.loading:load_all_seasons` decodifica ogni file con utf-8-sig se ha il BOM, altrimenti utf-8; se la decodifica utf-8 introduce caratteri sostitutivi che non erano nei byte, ricade su cp1252.
- Le date sono tutte nel formato `%d/%m/%y` oppure tutte nel formato `%d/%m/%Y` dentro un file; formati misti, date mancanti o fuori dalla finestra stagionale (1° luglio dell'anno iniziale – 31 agosto dell'anno finale) danno ValueError.
- Il DataFrame ha la colonna season (stringa YYYY-YY) ed è ordinato in modo stabile per season e Date.

**Split congelato.** `config/split.toml`, letto da `shk.data.split:read_split_config` (decisione S3, 2026-09-29; split congelato il 2026-09-29, test sbloccato il 2026-10-12).
- Parametri: `config/split.toml:training = ["2000-01", "2010-11", "2020-21"]`; `config/split.toml:test = ["2023-24"]`; `config/split.toml:test_unlocked = True`.
- Validazione: le 19 stagioni anteriori al 2023-24, non di training, con la terna B365 pre-partita completa (`config/split.toml:validation`). Storia ("history"): le altre stagioni anteriori alla prima di test.
- `shk.data.split:load_by_role` carica per ruolo ("training", "validation", "test", "history") e solleva `shk.data.split:TestSetLockedError` per il ruolo "test" finché test_unlocked è falso. Il codice nuovo carica i dati reali solo così (decisione S3, 2026-09-29).
- Schema dei fit (decisione S4, 2026-09-29, schema espansivo): il fit j usa le stagioni di training ≤ j; ogni stagione di validazione è prevista dal fit della stagione di training più recente strettamente anteriore (`shk.model.elo_fit:derive_fit_schedule`). Ne risultano tre fit, 2000-01, 2010-11 e 2020-21.

**Copertura delle quote** (US-C3.1).
- `shk.data.coverage:classify_column` classifica ogni colonna di quote per gruppo, fonte, mercato, momento (pre-partita o chiusura) e tipo (quota, linea, conteggio); una colonna non classificata dà ValueError.
- Formula: una terna è completa in una stagione se complete_rows = total_rows, cioè se ogni riga ha tutte e tre le quote non nulle, finite e > 1 — `shk.data.coverage:compute_coverage`.

**Anti-leakage** (decisione S3, 2026-09-29).
- `shk.data.walkforward:walkforward_split`: per ogni partita da prevedere, la storia sono le partite con Date strettamente anteriore (le altre dello stesso giorno escluse); la partita espone solo la whitelist.
- Whitelist per inclusione (`shk.data.walkforward:get_prematch_whitelist`): gli identificativi `shk.data.walkforward:PREMATCH_IDENTIFIERS = {"Div", "Date", "Time", "HomeTeam", "AwayTeam", "season"}` e le colonne con tipo quota e momento pre-partita. Esclusi risultati, statistiche, quote di chiusura, linee e conteggi.
- `shk.data.walkforward:check_leakage` elenca le violazioni; `shk.data.walkforward:assert_no_leakage` solleva `shk.data.walkforward:LeakageError`.

**Casi limite ed esclusioni.**
- Il 2000-01 non ha B365: è escluso dalle serie che usano B365 (C3.2, ĝ) e, solo per Modulo 2 e agenti, usa un'altra terna (§ 8).
- Il 2001-02 non ha B365: è storia, non validazione.

## 2. De-vigging

Probabilità implicite π_i = 1/o_i e somma S = Σ π_i (`shk.market.devig:implied_probabilities`); overround S − 1 (`shk.market.devig:overround`). Le quote devono essere > 1 (ValueError altrimenti).

- Formula: proporzionale, q_i = π_i / S — `shk.market.devig:devig_proportional`.
- Formula: additivo, q_i = π_i − (S − 1)/n; se un q_i ≤ 0 il mercato vale NaN (non applicabile) — `shk.market.devig:devig_additive`.
- Formula: power, q_i = π_i^k con k > 0 tale che Σ π_i^k = 1; Newton da k = 1 con passo salvaguardato k ← max(k − f/f′, k/2) — `shk.market.devig:devig_power`.
- Formula: Shin, q_i = (√(z² + 4(1 − z) π_i²/S) − z) / (2(1 − z)), z ∈ [0, 1) tale che Σ q_i = 1, per bisezione; con S = 1, z = 0; con S < 1 non applicabile (NaN) — `shk.market.devig:devig_shin`.
- Formula: odds ratio, q_i = c π_i / (1 − π_i + c π_i), c > 0 tale che Σ q_i = 1, per bisezione su un intervallo garantito — `shk.market.devig:devig_odds_ratio`.
- Selezione per nome: `shk.market.devig:devig_probabilities`.

Parametri:
- `shk.market.devig:DEVIG_METHOD_NAMES = ("proportional", "additive", "power", "shin", "odds_ratio")` (proporzionale, additivo, power in T17; Shin e odds ratio in T43).
- `shk.market.devig:MAX_NEWTON_ITERATIONS = 50`; `shk.market.devig:MAX_BISECTION_ITERATIONS = 200`.
- Metodo principale Shin, controllo proporzionale, sensibilità sui cinque metodi (decisione S7, 2026-10-11): `config/frozen_params.toml:fixed.devig_method = "shin"`.
- q si ricava sempre dalla terna B365 pre-partita (decisione S3, 2026-09-29), tranne il 2000-01 nel Modulo 2 (§ 8).

Casi limite:
- Power, Shin e odds ratio sollevano RuntimeError se un mercato applicabile ha |Σ q − 1| > 1e-12 alla fine del risolutore.
- Esclusioni nella valutazione di una serie, nell'ordine e contate per causa (`shk.model.scoring:prepare_series_evaluation`): quota mancante, quota non valida, additivo non applicabile, Shin non applicabile (S < 1). Le partite usate sono le stesse per tutti i metodi.

**Divergenza fra metodi** (US-C3.2, `shk.market.divergence:compute_divergence_table`):
- Formula: spread di un esito = (max − min dei q proporzionale, additivo e power)·100, in punti; spread relativo = (max − min)/media dei tre q; rapporto con l'edge = spread in probabilità / REFERENCE_EDGE — `shk.market.divergence:compute_divergence_table`.
- Fascia della quota dell'esito, chiusa a sinistra: `shk.market.divergence:assign_odds_bin`, con `shk.market.divergence:ODDS_BIN_LABELS = ("[1, 1.5)", "[1.5, 2)", "[2, 3)", "[3, 5)", "[5, 10)", "[10, inf)")`.
- `shk.market.divergence:REFERENCE_EDGE = 0.02` (decisione S3, 2026-09-29, scelta delegata). Il 99° percentile è np.percentile con method="linear".

## 3. Modulo 1 Elo e Dixon-Coles

Il Modulo 1 è un parametro della catena dei dati (T60): `shk.model.module1:MODULE1_IDS = ("elo", "dixon_coles")`; i risultati con Dixon-Coles hanno il suffisso `shk.model.module1:MODULE1_SUFFIXES = {"elo": "", "dixon_coles": "_dc"}`. Il Modulo 1 è usato raw, senza ricalibrazione (decisione S5, 2026-09-29, confermata il 2026-10-11).

### 3.1 Elo-Davidson

- Formula: differenziale Δ = R_casa − R_trasferta + h — `shk.model.elo:elo_delta`.
- Formula: punteggio atteso E = 1/(1 + 10^(−Δ/s)) — `shk.model.elo:expected_score`.
- Formula: aggiornamento a somma zero R_casa′ = R_casa + K(S − E), R_trasferta′ = R_trasferta − K(S − E), con S = 1, 0.5, 0 per H, D, A — `shk.model.elo:elo_update`.
- Formula: Davidson, r = 10^(Δ/s), D = r + 1 + ν√r, p_casa = r/D, p_pareggio = ν√r/D, p_trasferta = 1/D — `shk.model.elo:davidson_probabilities`.
- Formula: baseline a pareggio costante, p_pareggio = c, p_casa = (1 − c)E, p_trasferta = (1 − c)(1 − E), con c = frequenza dei pareggi sulle partite di training del fit — `shk.model.elo:constant_draw_probabilities`.
- Previsioni walk-forward: tutte le partite di una data si prevedono prima che una di esse aggiorni i rating — `shk.model.elo_predictor:predict_elo_fast` (stesse previsioni di `shk.model.elo_predictor:predict_elo_walkforward`, che passa dal fornitore anti-leakage).

Parametri:
- Scala: `shk.model.elo:expected_score(s) = 400.0`, `shk.model.elo:davidson_probabilities(s) = 400.0` (decisione S4, 2026-09-29: Davidson sulla stessa scala del punteggio atteso).
- Rating iniziale nella prima stagione del DataFrame: `shk.model.elo_predictor:predict_elo_fast(initial_rating) = 1500.0`.
- Calibrazione (decisione S4, 2026-09-29, scelta delegata): per ogni fit, Nelder-Mead sulla log-loss media Davidson delle partite di training del fit, con i rating che girano dal 1993-94 (`shk.model.elo_fit:calibrate_single_fit`, obiettivo `shk.model.elo_fit:compute_training_log_loss`). `shk.model.elo_fit:BOUNDS_K = (5.0, 80.0)`; `shk.model.elo_fit:BOUNDS_H = (0.0, 200.0)`; `shk.model.elo_fit:BOUNDS_NU = (0.05, 3.0)`; `shk.model.elo_fit:INITIAL_PARAMS = (30.0, 60.0, 1.0)`; `shk.model.elo_fit:OPTIMIZER_METHOD = "Nelder-Mead"`; `shk.model.elo_fit:OPTIMIZER_OPTIONS = {"xatol": 0.0001, "fatol": 1e-10, "maxiter": 2000, "maxfev": 4000}`.
- Valori congelati (calibrati il 2026-09-29, ELO_FITS non si modifica):
  - 2000-01: `shk.model.elo_fit:ELO_FITS['2000-01'].k = 10.318224689650037`, `shk.model.elo_fit:ELO_FITS['2000-01'].h = 125.54022316884253`, `shk.model.elo_fit:ELO_FITS['2000-01'].nu = 0.8062246331085681`, `shk.model.elo_fit:ELO_FITS['2000-01'].c = 0.2657894736842105`;
  - 2010-11: `shk.model.elo_fit:ELO_FITS['2010-11'].k = 9.934776455088759`, `shk.model.elo_fit:ELO_FITS['2010-11'].h = 127.87791672140764`, `shk.model.elo_fit:ELO_FITS['2010-11'].nu = 0.8775613268630023`, `shk.model.elo_fit:ELO_FITS['2010-11'].c = 0.2789473684210526`;
  - 2020-21: `shk.model.elo_fit:ELO_FITS['2020-21'].k = 7.928543266007228`, `shk.model.elo_fit:ELO_FITS['2020-21'].h = 78.033626101627`, `shk.model.elo_fit:ELO_FITS['2020-21'].nu = 0.7603760315281511`, `shk.model.elo_fit:ELO_FITS['2020-21'].c = 0.25877192982456143`.

Neopromosse (decisione del programmatore, S4, 2026-09-29), alla prima comparsa di ogni squadra nella stagione s:
- presente in s − 1: conserva il rating;
- assente in s − 1 ma già vista: riprende l'ultimo rating;
- mai vista: media dei rating finali delle ultime tre della classifica di s − 1, calcolata dai soli risultati (3 punti la vittoria, 1 il pareggio; poi differenza reti, gol fatti, nome) — `shk.model.elo_predictor:compute_season_standings`;
- nella prima stagione del DataFrame tutte partono dal rating iniziale.

### 3.2 Dixon-Coles (T59)

- Formula: gol di casa X ~ Poisson(λ), in trasferta Y ~ Poisson(μ), ln λ = α_casa + β_trasferta + γ, ln μ = α_trasferta + β_casa, con somma nulla degli attacchi (α = a − media(a)) — `shk.model.dixon_coles:negative_log_likelihood`.
- Formula: correzione τ(0,0) = 1 − λμρ, τ(0,1) = 1 + λρ, τ(1,0) = 1 + μρ, τ(1,1) = 1 − ρ, τ = 1 altrove — `shk.model.dixon_coles:tau`.
- Formula: verosimiglianza pesata ℓ = Σ_k φ_k [x_k ln λ_k − λ_k + y_k ln μ_k − μ_k + ln τ_k], φ_k = exp(−ξ·t_k) con t_k i giorni fra la partita e la data di valutazione; sotto TAU_FLOOR, ln τ è sostituito dalla prosecuzione lineare ln ε + (τ − ε)/ε — `shk.model.dixon_coles:negative_log_likelihood`.
- Formula: prior gaussiano sulle neopromosse, + Σ [(α − α₀)² + (β − β₀)²]/(2σ²) per le squadre alla prima stagione dopo l'ingresso — `shk.model.dixon_coles:negative_log_likelihood`.
- Formula: probabilità dei punteggi 0..MAX_GOALS, Pois(x; λ)·Pois(y; μ)·max(τ, 0), rinormalizzate; p_casa = Σ_{x>y}, p_pareggio = Σ_{x=y}, p_trasferta = Σ_{x<y} — `shk.model.dixon_coles:score_matrix`, `shk.model.dixon_coles:outcome_probs`.
- Stima: L-BFGS-B con gradiente analitico — `shk.model.dixon_coles:fit_dixon_coles`; a ogni data della stagione un fit sulle partite con Date strettamente anteriore e peso ≥ WEIGHT_TRUNCATION, avviato dalla soluzione della data precedente — `shk.model.dixon_coles:DixonColesForecaster.predict_season`, `shk.model.dixon_coles:DixonColesForecaster.history_rows`.

Parametri:
- `shk.model.dixon_coles:MAX_GOALS = 10`; `shk.model.dixon_coles:WEIGHT_TRUNCATION = 1e-4`; `shk.model.dixon_coles:RHO_BOUNDS = (-0.25, 0.25)`; `shk.model.dixon_coles:TAU_FLOOR = 1e-3`; `shk.model.dixon_coles:MAX_ITER = 2000`; `shk.model.dixon_coles:LOG_RATE_LIMIT = 10.0` (esponenti limitati a ±10).
- Griglie della calibrazione (T59): `shk.model.dixon_coles:XI_GRID = (0.0, 0.0005, 0.001, 0.0019, 0.003, 0.005)`; `shk.model.dixon_coles:SIGMA_GRID = (0.1, 0.2, 0.4)`. σ = ∞ è esclusa dalla griglia (decisione del programmatore, 2026-10-12): per una squadra senza storia lo stimatore non esiste se nelle prime partite fa o subisce 0 gol.
- Scelta (`shk.model.dixon_coles_calibration:choose`): minimo della log-loss media sulle partite di training del fit, previsioni walk-forward; a parità entro `shk.model.dixon_coles_calibration:TIE_TOLERANCE = 1e-12` il σ maggiore (decisione del programmatore, 2026-10-12), poi il ξ minore.
- Valori congelati (T59): `shk.model.dixon_coles:DC_FITS['2000-01'].xi = 0.001`, `shk.model.dixon_coles:DC_FITS['2000-01'].sigma = 0.4`; `shk.model.dixon_coles:DC_FITS['2010-11'].xi = 0.001`, `shk.model.dixon_coles:DC_FITS['2010-11'].sigma = 0.4`; `shk.model.dixon_coles:DC_FITS['2020-21'].xi = 0.0019`, `shk.model.dixon_coles:DC_FITS['2020-21'].sigma = 0.4`.

Neopromosse (decisioni S4, S11 e del programmatore, 2026-10-12): valore d'ingresso (α₀, β₀) = media dei parametri delle ultime tre della classifica precedente stimati a inizio stagione (mai vista) oppure ultimi parametri stimati (tornante); prior per tutta la prima stagione, γ e ρ senza prior. Prima della prima partita di una mai vista la previsione usa il valore d'ingresso.
- Neopromosse "nei primi 10 matchday": `shk.model.dixon_coles_calibration:NEW_TEAM_MATCHDAYS = 10`, matchday = blocco di 10 partite nell'ordine della stagione (`shk.model.dixon_coles_calibration:new_team_early_mask`).

### 3.3 Serie del Modulo 1

- Formula: log-loss per partita −ln p̂(x_t) — `shk.model.scoring:compute_log_loss`; residui per fit e ruolo — `shk.model.residuals:compute_model_residuals`, catena comune `shk.model.residuals:load_model_residuals`.
- Con Dixon-Coles i residui hanno anche i gol attesi `shk.model.residuals:RATE_COLUMNS = ("lambda_home", "lambda_away")` (T61).

Differenze con le note:
- Nota 2.8 §3.3: la tabella di Davidson è calcolata con 10^(ΔR/200), mentre il codice usa s = 400 per Davidson e per il punteggio atteso (con ΔR = 100 e ν = 0.8, s = 200 dà (0.566, 0.255, 0.179), che sono i valori della nota; s = 400 dà (0.462, 0.277, 0.260)).

## 4. ĝ

- Formula: termine per partita g_t = ln p̂_t(x_t) − ln q_t(x_t), con x_t esito realizzato — `shk.model.scoring:compute_g_hat_terms`; ĝ = media dei termini — `shk.model.scoring:compute_g_hat`; ĝ cumulato — `shk.model.scoring:compute_cumulative_g_hat`.
- Serie (decisione S4, 2026-09-29, scelta delegata): b365_prematch (B365H, B365D, B365A) sulle 19 stagioni di validazione e pinnacle_closing (PSCH, PSCD, PSCA) dalle stagioni con inizio ≥ `shk.model.scoring:PINNACLE_START_YEAR = 2012`. `shk.model.scoring:SERIES_NAMES = ("b365_prematch", "pinnacle_closing")`.
- Esito informativo: nessun parametro, filtro o metodo si cambia in funzione di ĝ (decisione S4, 2026-09-29).
- Casi limite: le partite di ogni serie sono quelle rimaste dopo le esclusioni del § 2, le stesse per i cinque metodi; il 2000-01 non entra nella serie B365.

ĝ formalizzato (T57, `shk.model.g_hat_inference`):
- Formula: intervallo per stagione, percentile su stationary bootstrap della serie dei termini a L_PW stationary della serie stessa — `shk.model.g_hat_inference:season_bootstrap_means`, `shk.model.g_hat_inference:percentile_interval`.
- Formula: intervallo pooled, bootstrap a due livelli (stagioni con reinserimento, dentro ciascuna la serie ricampionata), ĝ ± t_{0.975, S−1}·√(S/(S − 1))·se_boot — `shk.model.g_hat_inference:pooled_bootstrap_means`, `shk.model.comparisons:t_cluster_interval` (decisione del programmatore, 2026-10-12).
- Formula: placebo, esiti (FTR, FTHG, FTAG insieme) permutati dentro ogni stagione e pipeline del Modulo 1 rieseguita — `shk.model.g_hat_inference:permute_outcomes`, `shk.model.g_hat_inference:placebo_g_hats`.
- Formula: soglia della nota 2.4 §8, confronto di ĝ con la media di ln π, π = Σ_i 1/o_i — `shk.model.g_hat_inference:threshold_rows`.
- Fasce: sulla quota della favorita (minima delle tre) con le fasce di divergence.py — `shk.model.g_hat_inference:band_rows`. Finestre mobili di 80 partite — `shk.model.g_hat_inference:rolling_shares`.
- Parametri: `shk.model.g_hat_inference:N_BOOT = 999`; `shk.model.g_hat_inference:N_PERMUTATIONS = 1000`; `shk.model.g_hat_inference:ROLLING_WINDOW = 80`; copertura su AR(1) con `shk.model.g_hat_inference:COVERAGE_PHIS = (0.0, 0.1, 0.25, 0.5)` e `shk.model.g_hat_inference:COVERAGE_N_SERIES = 1000`.

## 5. Detector e Baseline D

**ADWIN e Page-Hinkley** (decisione S5, 2026-09-30): importati da river, un'istanza nuova per serie — `shk.stats.drift:run_drift_detector`, `shk.stats.drift:make_drift_detector`.
- Taratura sul training (2000-01 e 2010-11; 2020-21 escluso): vince la combinazione con |10(a + b) − 38| minima, poi meno allarmi, poi l'ordine della griglia — `shk.stats.drift:select_best_candidate`, `shk.stats.drift:calibrate_drift_detectors`. Obiettivo `shk.stats.drift:TARGET_ALARMS_PER_SEASON = 1.9`.
- Griglie: `shk.stats.drift:ADWIN_GRID_DELTA = (0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 0.8)`; `shk.stats.drift:PAGE_HINKLEY_GRID_DELTA = (0.005, 0.01, 0.05)`; `shk.stats.drift:PAGE_HINKLEY_GRID_THRESHOLD = (1.0, 2.0, 5.0, 10.0, 20.0, 50.0)`.
- Congelati in C5: `shk.stats.drift:ADWIN_DELTA = 0.002`; `shk.stats.drift:PAGE_HINKLEY_DELTA = 0.05`; `shk.stats.drift:PAGE_HINKLEY_THRESHOLD = 5.0`. Altri parametri, default di river 0.26.1 passati in modo esplicito: `shk.stats.drift:ADWIN_DEFAULT_CLOCK = 32`, `shk.stats.drift:ADWIN_DEFAULT_MAX_BUCKETS = 5`, `shk.stats.drift:ADWIN_DEFAULT_MIN_WINDOW_LENGTH = 5`, `shk.stats.drift:ADWIN_DEFAULT_GRACE_PERIOD = 10`, `shk.stats.drift:PAGE_HINKLEY_DEFAULT_MIN_INSTANCES = 30`, `shk.stats.drift:PAGE_HINKLEY_DEFAULT_ALPHA = 0.9999`, `shk.stats.drift:PAGE_HINKLEY_DEFAULT_MODE = "both"`.

**Z-test per matchday** (decisione S5, 2026-09-29):
- Formula: Z_g = (media della log-loss delle 10 partite del matchday − μ_f)/(σ_f/√10), con μ_f e σ_f (ddof = 1) sulle partite di training del fit; allarme nominale se |Z| > norm.ppf(1 − α/2) — `shk.stats.drift:compute_matchday_z_scores`.
- Formula: soglia calibrata, statistica d'ordine ⌈(1 − α)(B + 1)⌉ di |Z| calcolato sulle prime 10 posizioni (un matchday) di ciascun ricampionamento a blocchi mobili della serie di training del fit — `shk.stats.drift:calibrate_matchday_z_threshold`, `shk.stats.drift:compute_resampled_matchday_abs_z`.
- Parametri: `shk.stats.drift:MATCHDAY_SIZE = 10`; `shk.stats.false_rejection:ALPHA = 0.05`; `shk.stats.false_rejection:N_BOOT = 999`; `shk.stats.false_rejection:BLOCK_LENGTHS = (7, 20, 40)`.

**Baseline D in C5** (decisione S5, 2026-09-30, scelta delegata):
- Formula: λ_j = base·κ^k_j, con k_j gli allarmi su partite con Date strettamente anteriore a quella della partita j — `shk.kelly.staking:compute_adaptive_lambda`.
- Formula: al più una puntata per partita, sull'esito con p̂·o − 1 massimo se > 0 (parità nell'ordine H, D, A), frazione kelly_staking(p̂, o − 1, λ_j) — `shk.kelly.staking:select_baseline_d_bets`.
- Formula: motore su quote reali, L ← L + ln(1 + Σ_i f_i r_i) per data, r_i = o_i − 1 se vinta e −1 se persa — `shk.kelly.backtest:backtest_log_wealth`.
- Parametri: `shk.kelly.staking:BASE_LAMBDA = 0.25`; `shk.kelly.staking:KAPPA_GRID = (0.0, 0.25, 0.5, 0.75, 1.0)`; `shk.kelly.staking:KAPPA_ADWIN = 1.0`; `shk.kelly.staking:KAPPA_PAGE_HINKLEY = 1.0` (κ scelto sulla log-ricchezza finale di 2010-11 e 2020-21, a parità il più grande; 2000-01 escluso perché senza B365).

**Baseline D come agente** (T50, decisione S9, 2026-10-11): `shk.model.stateful_agents:BaselineDAgent`.
- Formula: moltiplicatore κ^k, con κ = 0: 1 senza allarmi e 0 con almeno un allarme — `shk.model.stateful_agents:adaptive_multiplier`.
- Serie del detector: "delta" (δ = ln p̂(x) − ln q(x), q Shin) in S9–S11, "log_loss" come in C5: `config/frozen_params.toml:fixed.d_series = "delta"`.
- Parametri congelati (T54): `config/frozen_params.toml:calibrated.d_adwin_delta = 0.002`; `config/frozen_params.toml:calibrated.d_adwin_kappa = 0.75`; `config/frozen_params.toml:calibrated.d_page_hinkley_delta = 0.005`; `config/frozen_params.toml:calibrated.d_page_hinkley_threshold = 1.0`; `config/frozen_params.toml:calibrated.d_page_hinkley_kappa = 0.75`; `config/frozen_params.toml:fixed.d_base_lambda = 0.25`.
- Con Dixon-Coles (T61): `config/frozen_params_dc.toml:calibrated.d_adwin_delta = 0.5`; `config/frozen_params_dc.toml:calibrated.d_adwin_kappa = 0.0`; `config/frozen_params_dc.toml:calibrated.d_page_hinkley_kappa = 0.0`.

Il detector dice quando, non quanto né di che tipo; κ è un iperparametro fisso, uguale per ogni allarme (decisione S5).

## 6. Ambiente e floor

**Ambiente passo-passo** (T34, decisione S6, 2026-10-09, scelta delegata): `shk.kelly.environment:run_paired_backtest`.
- Per ogni data: una DateView condivisa; per ogni agente decide, controllo di rovina, piazzamento e regolamento; infine gli esiti della data a tutti gli agenti (`shk.kelly.agents:Agent.observe_results`, T50), così alla data d nessun agente ha esiti di date ≥ d.
- Formula: rovina assorbente a inizio data se W = 0, oppure F > 0 e W < F (stretto) — `shk.kelly.environment:run_paired_backtest`.
- Formula: piazzamento — puntate volontarie f_i·W, con F > 0 ognuna vale almeno F; ordine per EV stimato decrescente (parità: indice di partita), si tiene il prefisso più lungo con somma ≤ W, le altre si scartano; con F > 0 e nessuna puntata volontaria, una puntata da F sul ripiego, contata come forzata — `shk.kelly.environment:place_date_stakes`.
- Formula: regolamento W ← W + Σ_i s_i r_i, r_i = o_i − 1 se vinta e −1 se persa — `shk.kelly.environment:run_paired_backtest`.
- Ripiego: `shk.kelly.environment:FALLBACK_POLICIES = ("model_ev", "market_ev")`; in S9–S11 `config/frozen_params.toml:fixed.fallback_policy = "model_ev"` (coppia partita-esito a EV stimato massimo della data).

**Configurazioni** (decisione S6, 2026-10-09): B0 = £220, F in unità del bankroll iniziale.
- `shk.model.paired_backtest:KELLYBENCH_INITIAL_BANKROLL_GBP = 220.0`; `shk.model.paired_backtest:CONFIGURATIONS = (("none", 0.0), ("gbp_0.01", 4.545454545454546e-05), ("gbp_1", 0.004545454545454545))`.
- Configurazione principale B0/F = 22 000 (decisione S9): `config/frozen_params.toml:fixed.main_configuration_b0_over_f = 22000`.

**Floor sintetico** (T36, `shk.kelly.floor`):
- Formula: soglie della nota 2.9 §4, B1 = F/(λ f*), B2 = F/(2 f*), B3 = F — `shk.kelly.environment:floor_thresholds`.
- Formula: limite del tempo medio di rovina, μ = p ln(1 + f(o − 1)) + (1 − p) ln(1 − f), limite = ln(B0/F)/|μ| — `shk.kelly.floor:expected_ruin_time_bound`; accelerazione = limite / tempo medio di rovina simulato — `shk.kelly.floor:run_experiment_c`.
- Parametri: `shk.kelly.floor:EXP_A_ODDS = 2.5`; `shk.kelly.floor:EXP_A_TRUE_EV = -0.02`; `shk.kelly.floor:EXP_A_ESTIMATED_EDGE = 0.03`; `shk.kelly.floor:EXP_A_LAMBDA = 0.25`; `shk.kelly.floor:EXP_A_M = 10000`; `shk.kelly.floor:EXP_B_HORIZONS = (150, 1000)`; `shk.kelly.floor:EXP_C_M = 1000`.

**Floor nella configurazione reale** (T37, `shk.model.floor_real_config`):
- Formula: esiti per inversione dalle q proporzionali di B365 (0 se u < q_H, 1 se u < q_H + q_D, 2 altrimenti) — `shk.model.floor_real_config:outcomes_by_inversion`.
- Formula: intervallo del tasso di rovina r ± Z_99·√(r(1 − r)/n), troncato a [0, 1] — `shk.model.floor_real_config:compute_aggregate_metrics`.
- Parametri: `shk.model.floor_real_config:M_REPLICAS = 1000`; `shk.model.floor_real_config:Z_99 = 2.576`; `shk.model.floor_real_config:THETA_THRESHOLDS = (0.5, 0.1)`.

Metriche di percorso (decisione S6): drawdown massimo `shk.kelly.metrics:wealth_max_drawdown`; tempo di recupero, date dal minimo del drawdown massimo al primo ritorno al picco, censurato se non avviene — `shk.kelly.metrics:wealth_recovery_time`.

Differenze con le note:
- Nota 2.9 §6.2, configurazione (a): la nota riporta un tempo simulato di 1 427 date e un'accelerazione 23×. Il codice registra il valore della nota (`shk.kelly.floor:EXP_C_CONFIGS`, campo note_acceleration) e calcola l'accelerazione col tempo medio di rovina; il valore di 1 427 della nota è il tempo mediano (backlog, S6).
- Nota 2.9, esperimento A: la nota usa 80 000 repliche (`shk.kelly.floor:NOTE_EXP_A_M = 80000`), il codice 10 000; il confronto usa la tolleranza Monte Carlo a due campioni `shk.kelly.floor:two_sample_mc_tolerance`.

## 7. Agenti

**Classe base** (T33, decisione S6, 2026-10-09): `shk.kelly.agents:Agent`.
- Formula: EV stimato p̂·o − 1 per partita ed esito — `shk.kelly.agents:estimated_expected_values`.
- Formula: per ogni partita l'esito con EV stimato massimo (parità nell'ordine H, D, A), selezionato solo se EV > 0; frazioni dalla regola della sottoclasse; ripiego = coppia (partita, esito) con EV stimato massimo della data, anche se ≤ 0 — `shk.kelly.agents:Agent.decide`.
- Una sottoclasse ridefinisce solo `__init__`, `stake_fractions` e `observe_results` (TypeError altrimenti); il bankroll non entra negli agenti.
- Casi limite: stake_fractions deve restituire un array float della forma degli esiti selezionati, finito, ≥ 0 e < 1 (ValueError altrimenti); previsioni e quote arrivano in sola lettura.

**Regola di Kelly** (decisione S1, 2026-09-27):
- Formula: f = λ·max(0, (b p̂ − (1 − p̂))/b), b = o − 1, non limitata sotto 1 — `shk.kelly.staking:kelly_staking`; Kelly pieno sul p vero — `shk.kelly.core:kelly_fraction`.

**Baseline e bracci** (decisioni S6 e S9):
- A, B: `shk.kelly.agents:FractionalKellyAgent`, con `shk.kelly.agents:AGENT_A_LAMBDA = 1.0` e `shk.kelly.agents:AGENT_B_LAMBDAS = (0.25, 0.10)`. E: `shk.kelly.agents:MinimumStakeAgent`, frazioni nulle (solo puntate forzate con F > 0).
- C0 = B_0.25: `shk.model.agent_c:build_c0_agent`, `shk.model.agent_c:C0_LAMBDA = 0.25`; `config/frozen_params.toml:fixed.c0_lambda = 0.25`.
- Formula: C1, λ = 0.25·κ^n con n le accensioni dell'allarme strutturale (date in cui l'allarme è acceso e alla data di decisione precedente era spento); allarme acceso se il Modulo 2 è attivo e T = −S > soglia — `shk.model.agent_c:C1Agent.stake_fractions` (decisione del programmatore, 2026-10-11).
- Formula: C2_global, λ per scommessa = module3_lambda (§ 9); C2, come C2_global con frazione 0 sulle partite fuori supporto — `shk.model.agent_c:GradedAgent.stake_fractions`.
- Supervisore del Modulo 2 condiviso dai bracci: esiti solo da observe_results, Modulo 2 una volta per data con Date < d, catena tagliata alla stagione — `shk.model.agent_c:Module2Supervisor.state_at`.
- Formula: soglia di C1, moving block bootstrap della serie di training del fit con le righe (covariate, δ) insieme, prime 2W posizioni come finestre A e B, T = −S della three-fold; statistica d'ordine ⌈(1 − α)(B_validi + 1)⌉ sui ricampionamenti a rango pieno — `shk.model.agent_c:calibrate_c1_threshold`, `shk.model.agent_c:c1_null_statistics`.
- Parametri congelati (T54): `config/frozen_params.toml:calibrated.c1_window = 40`; `config/frozen_params.toml:calibrated.c1_kappa = 0.75`; `config/frozen_params.toml:calibrated.c2_global_window = 190`; `config/frozen_params.toml:calibrated.c2_window = 80`; `config/frozen_params.toml:fixed.c1_alpha = 0.05`; `config/frozen_params.toml:fixed.c1_n_boot = 999`; `shk.model.agent_c:C1_N_BOOT = 999`; soglie per fit `config/frozen_params.toml:c1_thresholds.2000-01 = 0.06274452118325424`, `config/frozen_params.toml:c1_thresholds.2010-11 = 0.07682507170298258`, `config/frozen_params.toml:c1_thresholds.2020-21 = 0.10170087346629561`.
- Con Dixon-Coles (T61): `config/frozen_params_dc.toml:calibrated.c1_kappa = 0.0`; `config/frozen_params_dc.toml:calibrated.c2_window = 40`; `config/frozen_params_dc.toml:c1_thresholds.2020-21 = 0.07033140200701937`.
- Agenti costruiti solo dal file congelato, con le costanti interne confrontate col file — `shk.model.frozen_agents:build_frozen_agents`, `shk.model.frozen_agents:check_frozen_constants`. Ordine: `shk.model.frozen_agents:AGENT_ORDER = ("A", "B_0.25", "B_0.10", "D_ADWIN", "D_PH", "C0", "C1", "C2_global", "C2", "E")`.

## 8. Modulo 2

**Dati per partita** (T46, `shk.model.module2_data:build_module2_frame`):
- Formula: δ_t = ln p̂_t(x_t) − ln q_t(x_t), q Shin dalla terna B365 pre-partita (decisione S8, 2026-10-11) — `shk.model.module2_data:build_module2_frame`.
- Formula: covariate pre-partita, log_odds_ratio = ln(o_H/o_A); market_entropy = H(q); model_entropy = H(p̂), H(p) = −Σ p ln p (`shk.model.residual_heteroskedasticity:compute_shannon_entropy`); position = posizione nella stagione; flag_new, flag_returning, flag_promoted — `shk.model.module2_data:build_module2_frame`.
- Formula: elo_diff ricavato dalle probabilità di Davidson, 400·log10(p_casa/p_trasferta) — `shk.model.module2_data:reconstruct_elo_diff`, con `shk.model.module2_data:ELO_SCALE = 400.0`.
- Con Dixon-Coles (T61, scelta delegata) il differenziale di forza è lambda_diff = λ − μ: `shk.model.module2_data:STRENGTH_COVARIATES = {"elo": "elo_diff", "dixon_coles": "lambda_diff"}`.
- Flag d'ingresso dalle sole rose: "new" se la squadra non compare in nessuna stagione precedente, "returning" se compare prima ma non in s − 1 — `shk.model.module2_data:entry_status_by_team_season`.
- Terna del 2000-01, senza B365 (decisione S8, 2026-10-11): la terna completa fra `shk.model.module2_data:TRIPLE_CANDIDATES_2000_01 = ("GB", "IW", "SB", "WH")` con overround medio nel 2000-01 più vicino a quello di B365 nel `shk.model.module2_data:B365_REFERENCE_SEASON = "2002-03"` — `shk.model.module2_data:select_triple_2000_01`.

**Specificazione sul training** (T46, `shk.model.covariate_inspection:derive_specification`), regole fissate prima dei numeri:
- (i) flag distinti se ciascuno ha in media almeno `shk.model.covariate_inspection:MIN_FLAG_MATCHES_PER_SEASON = 30.0` partite per stagione di training, altrimenti il solo flag_promoted — `shk.model.covariate_inspection:apply_flag_rule`;
- (ii) Formula: si toglie una alla volta la covariata col VIF massimo finché tutti i VIF ≤ VIF_MAX, VIF_j = 1/(1 − R²_j) — `shk.model.covariate_inspection:vif_elimination`, `shk.model.covariate_inspection:variance_inflation_factors`; `shk.model.covariate_inspection:VIF_MAX = 5.0`.
- Specificazione congelata: `config/frozen_params.toml:fixed.covariates = ["log_odds_ratio", "market_entropy", "flag_promoted", "position", "model_entropy"]`.

**Oaxaca-Blinder** (T45, `shk.stats.oaxaca`), A gruppo di riferimento (finestra vecchia), B recente, OLS per gruppo via QR:
- Formula: three-fold Δ = ȳ_B − ȳ_A = β_A′(x̄_B − x̄_A) [compositiva] + x̄_A′(β_B − β_A) [strutturale] + (x̄_B − x̄_A)′(β_B − β_A) [interazione] — `shk.stats.oaxaca:oaxaca_blinder`, `shk.stats.oaxaca:three_fold_batch`.
- Formula: two-fold con riferimento β*, spiegata β*′(x̄_B − x̄_A), non spiegata x̄_B′(β_B − β*) + x̄_A′(β* − β_A), riferimenti `shk.stats.oaxaca:TWOFOLD_REFERENCES = ("beta_a", "beta_b", "reimers", "cotton", "neumark", "pooled_group")` — `shk.stats.oaxaca:oaxaca_blinder`.
- Formula: quota strutturale π = |S|/(|C| + |S| + |I|), NaN se le tre componenti sono nulle — `shk.stats.oaxaca:oaxaca_blinder`.
- Dettagliata con la normalizzazione di Yun sulle dummy dei flag — `shk.model.module2:flag_dummy_blocks`. Rango: `shk.stats.oaxaca:RANK_TOLERANCE = 1e-10`.

**Modulo 2 online** (T47, `shk.model.module2:module2_at_date`):
- Formula: alla data di decisione D, fra le partite con Date < D della catena di stagioni di D, B = ultime W partite, A = le W precedenti; catena interrotta dove manca una stagione con δ — `shk.model.module2:module2_at_date`, `shk.model.module2:season_chain_ids`, `shk.model.module2:eligible_mask`.
- Stati: meno di 2W partite anteriori → "not_active"; un disegno a rango non pieno → "rank_deficient" (`shk.model.module2:STATE_NOT_ACTIVE`, `shk.model.module2:STATE_RANK_DEFICIENT`).
- Formula: indeterminatezza = (max − min delle spiegate delle two-fold)/|totale| — `shk.model.module2:module2_at_date`.
- Finestre: `shk.model.covariate_inspection:MODULE2_WINDOWS = (40, 80, 120, 190)`. Intervalli a fine matchday: `shk.model.module2:MATCHDAY_SIZE = 10`, `shk.model.module2:N_BOOT_CI = 999` (§ 12).

**Scenari noti** (T48, `shk.model.known_scenarios:evaluate_known_scenarios`): scenario 1, ultime W di s − 1 contro prime W di s (W = `shk.model.known_scenarios:MAIN_WINDOW = 80` principale); scenario 2, 2019-20 prima della sospensione (l'intervallo più lungo fra date consecutive, `shk.model.known_scenarios:suspension_split`) contro il resto del 2019-20 e il 2020-21; scenario 3, `shk.model.known_scenarios:END_SEASON_A = (91, 250)` contro `shk.model.known_scenarios:END_SEASON_B = (291, 380)`, senza e con il flag "senza obiettivi" (`shk.model.season_objectives:no_objective_flags`, con `shk.model.season_objectives:RELEGATION_PLACES = 3` e `shk.model.season_objectives:TOP_PLACES = 4`).
- Formula: nello scenario 3 la quantità principale è la two-fold con riferimento β_B, π_B = |S|/(|C + I| + |S|) — `shk.model.known_scenarios:decomposition_batch`.

**Supporto comune e DiD** (T49):
- Formula: regola "fuori supporto", la cella della partita (quintili della finestra A per le continue, livelli per le dummy) ha meno di MIN_CELL_COUNT partite della finestra A — `shk.stats.nopo:out_of_support_mask`, `shk.stats.nopo:quintile_edges`; `shk.stats.nopo:MIN_CELL_COUNT = 5`, `shk.stats.nopo:QUANTILE_LEVELS = (0.2, 0.4, 0.6, 0.8)`; `config/frozen_params.toml:fixed.out_of_support_min_count = 5`.
- Formula: Ñopo a quattro parti (fuori supporto in A, fuori supporto in B, composizione e struttura nel supporto), che sommano a Δ — `shk.stats.nopo:nopo_decomposition`.
- Formula: DiD = (δ̄_E,tardi − δ̄_E,presto) − (δ̄_NE,tardi − δ̄_NE,presto), E = partite con flag_promoted, presto = posizioni 1–100 — `shk.stats.nopo:did_2x2`; `shk.model.did_support:EARLY_POSITIONS = (1, 100)`; `shk.model.did_support:N_BOOT_DID = 999`; `shk.model.did_support:N_PLACEBO = 200`. Il DiD è diagnostico e non entra nella regola di staking.

Quota strutturale: la formula coincide con quella della nota 1.5 §9.5, che la dichiara una scelta, non l'unica possibile (valori assoluti al denominatore).

## 9. Modulo 3

Da uscita del Modulo 2 a λ (T51, `shk.model.module3`).
- Formula: λ* = E[c]/E[c²] = μ E[X⁺]/E[(X⁺)²], E[X⁺] = μΦ(μ/s) + sφ(μ/s), E[(X⁺)²] = (μ² + s²)Φ(μ/s) + μsφ(μ/s); λ* = 0 se μ ≤ 0, 1 se s = 0; limitato a [0, 1] — `shk.model.module3:lambda_star`.
- Formula: σ̂² dalla dispersione di δ, max(SIGMA2_MIN, (media(e²) − media(V))/media(c)), con L_i = ln p̂_i − ln q_i, m̂ = Σ p̂_i L_i, e = δ − m̂, V = Σ p̂_i L_i² − m̂², c = 2Σ(L_i − L̄)² + 2(1 − 1/K)(m̂ Σ 1/p̂_i − Σ L_i/p̂_i); se media(c) è nulla, SIGMA2_MIN — `shk.model.module3:delta_dispersion_sigma2`.
- Formula: gonfiamento strutturale Δσ² = −S/h se S < 0, altrimenti 0, h = media((1 − 1/K)/2·Σ 1/p̂) sulla finestra A — `shk.model.module3:structural_inflation`.
- Formula: deviazione standard sull'esito scommesso σ_p = σ√((K − 1)/K), s = o·σ_p — `shk.model.module3:selected_sd`.
- Formula: candidata P3, μ̂ = media degli EV̂ della finestra B, σ̂² = σ̂²_A + Δσ²; λ = 0 se ĝ della finestra B (media di δ) ≤ 0; Modulo 2 non attivo → INACTIVE_LAMBDA — `shk.model.module3:candidate_lambda`, `shk.model.module3:module3_lambda`.
- Parametri: `shk.model.module3:INACTIVE_LAMBDA = 0.25`; `shk.model.module3:SIGMA2_MIN = 1e-6`; `shk.model.module3:CANDIDATES = ("P1", "P2", "P3")`; `shk.model.module3:CHOSEN_CANDIDATE = "P3"`; nel file congelato `config/frozen_params.toml:fixed.module3_candidate = "P3"`, `config/frozen_params.toml:fixed.inactive_lambda = 0.25`, `config/frozen_params.toml:fixed.lambda_min = 0.0`, `config/frozen_params.toml:fixed.lambda_max = 1.0`.
- Scelta della candidata (T51) su verità sintetica: errore quadratico medio fra λ̂ e λ* oracolo su quattro regimi e `shk.model.module3_synthetic:N_REPLICAS = 500` repliche, P1 esclusa come controllo negativo — `shk.model.module3_synthetic:choose_candidate`; generatore `shk.model.module3_synthetic:generate_season` con `shk.model.module3_synthetic:GENERATOR_WINDOW = 80` e `shk.model.module3_synthetic:OVERROUND = 1.05`.

## 10. Seed e bootstrap

**Seed delle story** (decisioni S1, S2, S5, S6 e S7):
- `shk.kelly.scenarios:SEED = 20260927` (S1); `shk.stats.false_rejection:SEED_C2 = 20260928` (S2); `shk.stats.drift:SEED_C5 = 20260929` (S5); `shk.kelly.floor:SEED_C6 = 20261009` (S6).
- `shk.stats.false_rejection:SEED_S7 = 20261011`; `shk.stats.oaxaca_synthetic:SEED_S8 = 20261012`; `shk.model.module3_synthetic:SEED_S9 = 20261013`; `shk.model.validation_run:SEED_S10 = 20261014`; `shk.model.dixon_coles:SEED_S11 = 20261015`.
- Il task in posizione i della sua story usa SeedSequence(SEED_Sn).spawn(5)[i] — `shk.model.task_seeds:task_sequence`, con `shk.model.task_seeds:N_STORY_TASKS = 5`. Le procedure di S10 usano la radice della story — `shk.model.task_seeds:story_task_sequence`.
- Con Dixon-Coles (T61): procedure di specificazione e calibrazione con SeedSequence(SEED_S11).spawn(5)[2].spawn(5)[k] — `shk.model.module1_seeds:procedure_seeds`, `shk.model.module1_seeds:DC_SEED_SCHEME = "SeedSequence(SEED_S11).spawn(5)[2].spawn(5)[k], k = T46, T47, T52, T53, T54"`; S10 con radice SeedSequence(SEED_S11).spawn(5)[3] — `shk.model.module1_seeds:s10_seed`.

**Lunghezza dei blocchi** (decisione S7, 2026-10-11):
- Formula: Politis-White con la correzione del 2009, b = (2G²/D)^(1/3) n^(1/3), D_SB = 2(σ²)² (stationary) e D_CB = (4/3)(σ²)² (circolare), σ² varianza di lungo periodo, limitata da ⌈min(3√n, n/3)⌉ — `shk.stats.bootstrap:optimal_block_length`; `shk.stats.bootstrap:PW_D_STATIONARY_FACTOR = 2.0`, `shk.stats.bootstrap:PW_D_CIRCULAR_FACTOR = 1.3333333333333333`, `shk.stats.bootstrap:PW_MIN_KN = 5`, `shk.stats.bootstrap:PW_BAND_CONSTANT = 2.0`.
- Formula: arrotondamento max(1, ⌊L + 0.5⌋) — `shk.stats.bootstrap:round_block_length`.

**Ricampionamenti**:
- Formula: moving block bootstrap, ⌈n/L⌉ blocchi con inizio uniforme in [0, n − L], troncati a n — `shk.stats.calibration:moving_block_indices`.
- Formula: stationary bootstrap di Politis-Romano, ogni posizione apre un blocco con probabilità 1/L, inizio uniforme, avvolgimento circolare — `shk.stats.bootstrap:stationary_bootstrap_indices`.
- Formula: soglia calibrata = statistica d'ordine ⌈(1 − α)(B + 1)⌉ (tolleranza 1e-9 attorno agli interi) — `shk.stats.calibration:compute_order_statistic_index`, `shk.stats.calibration:calibrate_threshold`. H₀ la impone il chiamante (per l'ANOVA: serie centrata per gruppo, `shk.stats.false_rejection:center_by_group`, T40).

**Seed di backtest** (decisione S9, 2026-10-11): un seed è una stagione ricostruita per stationary bootstrap delle date; ogni data porta con sé le sue partite; il calendario resta ordinato e "position" si ricalcola.
- Formula: L = L_PW stationary arrotondata della serie per data della media di δ — `shk.model.season_bootstrap:season_block_length`; ricostruzione — `shk.model.season_bootstrap:reconstruct_season`, `shk.model.season_bootstrap:date_layout`. Con L = 1 è la versione iid: `shk.model.comparisons_run:IID_BLOCK_LENGTH = 1.0`.
- Formula: numero di seed (T53), N_min = (z σ/(0.2 Δ))²/19, N_SEEDS = 100·⌈N_min/100⌉, almeno 500; 1 000 se Δ < 1e-6 o N_SEEDS > 5 000 — `shk.model.power:n_seeds_rule`; `shk.model.power:EFFECT_FRACTION = 0.2`; `shk.model.power:MIN_SEEDS = 500`; `shk.model.power:MAX_SEEDS = 5000`; `shk.model.power:FALLBACK_SEEDS = 1000`; `config/frozen_params.toml:fixed.n_seeds = 500`.

**Soglie calibrate degli altri strumenti**:
- ANOVA di C2: falso rigetto su `shk.stats.false_rejection:N_SERIES = 1000` serie AR(1) da `shk.stats.false_rejection:N_OBS = 380` osservazioni per `shk.stats.false_rejection:PHI_VALUES = (0.0, 0.3, 0.5, 0.7)` — `shk.stats.false_rejection:compute_nominal_rejection_rates`, `shk.stats.false_rejection:compute_centered_calibrated_rejection_rates`; F a mano — `shk.stats.anova:oneway_anova`; intervallo Monte Carlo α ± 2.576√(α(1 − α)/1000) — `shk.stats.false_rejection:monte_carlo_interval_99`.
- Eteroschedasticità (C6.4): Formula: LM = n·R² della regressione ausiliaria di e² (Koenker) — `shk.stats.heteroskedasticity:breusch_pagan_lm`, `shk.stats.heteroskedasticity:white_lm`; gradi di libertà `shk.model.residual_heteroskedasticity:STATISTIC_DFS = {"bp_joint": 2, "bp_time": 1, "white": 5}`; soglie calibrate con `shk.model.residual_heteroskedasticity:BLOCK_LENGTHS = (7, 20, 40)` e `shk.model.residual_heteroskedasticity:N_BOOT_CALIB = 999` — `shk.model.residual_heteroskedasticity:calibrate_block_bootstrap_thresholds`.
- Differenza con le note: il TODO v4 (§ 1.8) segnala che "statsmodels HAC non corregge anova_lm". Il controllo di T38, `tests/test_hac_anova_lm.py` (AR(1) con φ = 0.7, n = 380, due metà da 190, maxlags = 5), mostra che vale con typ=1; con typ=2 e typ=3 l'F di anova_lm sul fit HAC coincide col Wald HAC, ma sum_sq non è più una somma di quadrati. Nel progetto l'autocorrelazione si tratta con le soglie calibrate per block bootstrap, non con HAC.
- Cambio di varianza (T44): Formula: z_t = (l_t − H_t)/√V_t con V_t la varentropia — `shk.stats.variance_change:varentropy_standardized_residuals`; Goldfeld-Quandt sui terzi, ARCH-LM con `shk.stats.variance_change:ARCH_LAGS = 10`, log-varianza mobile con `shk.stats.variance_change:ROLLING_WINDOW = 80` e `shk.stats.variance_change:ROLLING_STEP = 10`, Brown-Forsythe — `shk.stats.variance_change:goldfeld_quandt_thirds`, `shk.stats.variance_change:arch_lm`, `shk.stats.variance_change:rolling_log_variance_max`, `shk.stats.variance_change:brown_forsythe`.

## 11. Calibrazione e congelamento

**Obiettivo unico** (decisione S9, 2026-10-11): media, su seed e sulle tre stagioni di training, della log-ricchezza finale nella configurazione principale; a parità entro 1e-12 vince la puntata media più bassa (`shk.model.training_calibration:evaluate_calibration`).
- Formula: puntata media di una combinazione = media su seed e stagioni della media sulle date di staked_d/W_{d−1} — `shk.model.training_calibration:evaluate_calibration`.
- Formula: regola di parità di secondo livello (decisione del programmatore, 2026-10-11): 1. valore congelato da una decisione precedente; 2. κ del braccio a reazione binaria più simile con κ identificato, altrimenti 1; 3. ordine della griglia — `shk.model.training_calibration:select_combinations`, `shk.model.training_calibration:first_level_ties`.
- Parametri: `shk.model.training_calibration:CALIBRATION_CONFIG = "gbp_0.01"`; `shk.model.training_calibration:N_CALIBRATION_SEEDS = 200`; `shk.model.training_calibration:TIE_TOLERANCE = 1e-12`; `shk.model.training_calibration:DEFAULT_KAPPA = 1.0`; `shk.model.training_calibration:KAPPA_REFERENCES = {"D_ADWIN": ("D_PH", "C1"), "D_PH": ("D_ADWIN", "C1"), "C1": ()}`; `shk.model.training_calibration:FROZEN_EARLIER_VALUES = {"D_ADWIN": {"detector_delta": 0.002}, "D_PH": {"detector_delta": 0.05, "detector_threshold": 5.0}}`.
- Griglie (fissate in T54, `shk.model.training_calibration:calibration_grid`): C1 = MODULE2_WINDOWS × KAPPA_GRID; C2_global e C2 = MODULE2_WINDOWS; D_ADWIN = ADWIN_GRID_DELTA × KAPPA_GRID; D_PH = PAGE_HINKLEY_GRID_DELTA × PAGE_HINKLEY_GRID_THRESHOLD × KAPPA_GRID.
- Seed: SeedSequence(SEED_S9).spawn(5)[4] (T54) — `shk.model.training_calibration:spawn_t54_generators`; `config/frozen_params.toml:calibration.n_seeds = 200`; `config/frozen_params.toml:calibration.configuration = "gbp_0.01"`.
- Esecuzione di prova di T52 con parametri al centro delle griglie: `shk.model.training_agents:PROVISIONAL_WINDOW = 80`, `shk.model.training_agents:PROVISIONAL_KAPPA = 0.5`.

**Congelamento** (T54, US-C8.2):
- `config/frozen_params.toml` si scrive una sola volta (`shk.model.frozen_params:write_frozen_params` rifiuta di sovrascrivere) e si legge solo con `shk.model.frozen_params:load_frozen_params`, che verifica le chiavi (`shk.model.frozen_params:check_keys`). Congelato il 2026-10-11, committato prima di T55.
- Con Dixon-Coles (T61): stessa procedura, file `config/frozen_params_dc.toml` con la chiave di primo livello `config/frozen_params_dc.toml:module1 = "dixon_coles"` — `shk.model.frozen_params:frozen_params_path`; congelato il 2026-10-17, committato prima di T62.
- Protocollo (decisioni S9 e S10): nessun parametro di C1, C2 e D si sceglie su validazione o test; il test 2023-24 si esegue una volta, dopo il commit del file congelato e lo sblocco — `shk.model.test_run:TEST_SEASON = "2023-24"`, `shk.model.test_run:TEST_FIT = "2020-21"`.

## 12. Intervalli

- Formula: confronto pooled A − B = media sulle stagioni della differenza per stagione (metriche per seed: media sui seed delle differenze appaiate; metriche per stagione: differenza delle statistiche) — `shk.model.comparisons:season_differences`, `shk.model.comparisons:pooled_bootstrap`.
- Formula: bootstrap a due livelli, stagioni con reinserimento e, dentro ciascuna, seed con reinserimento, gli stessi per i due agenti — `shk.model.comparisons:two_level_indices`.
- Formula: intervallo principale D̂ ± t_{0.975, S−1}·√(S/(S − 1))·se_boot (decisione del programmatore, 2026-10-12) — `shk.model.comparisons:t_cluster_interval`; secondario percentile, statistiche d'ordine ⌈(α/2)(B + 1)⌉ e ⌈(1 − α/2)(B + 1)⌉ — `shk.model.comparisons:percentile_interval`.
- Parametri: `shk.model.comparisons:N_BOOT = 999`; `shk.model.comparisons:INTERVAL_ALPHA = 0.05`; confronti `shk.model.comparisons:COMPARISONS = (("C2", "D_ADWIN"), ("C2", "D_PH"), ("C2", "E"), ("C1", "C0"), ("C2", "C1"), ("C2", "C2_global"), ("C1", "D_PH"))`.
- Formula: effect size d = Δ/σ, OVL = 2Φ(−|d|/2), R² = d² e d²/(d² + 4) — `shk.model.comparisons:effect_sizes`, `shk.model.comparisons:effect_size_sigma`.
- Formula: crescita certo-equivalente (decisione S10, 2026-10-11), g_CE = mean(ln W_T)/D per γ = 1, (1/D)(1/(1 − γ)) ln mean(W_T^(1−γ)) per γ > 1, −inf se una W_T = 0 — `shk.model.validation_run:certainty_equivalent`; `shk.model.validation_run:GAMMAS = (1.0, 2.0, 5.0)`.
- Test 2023-24 (T58): una stagione, intervallo percentile dai soli seed, senza correzione per i cluster — `shk.model.test_run:comparison_records_single`; `shk.model.test_run:N_BOOT = 999`. ROI di E accanto ai riferimenti `shk.model.test_run:PAPER_E_ROI = -0.041` e `shk.model.test_run:NOTE_E_ROI = -0.051` (decisione S6).
- Formula: τ-b di Kendall, τ_b = (n_c − n_d)/√((n_0 − n_1)(n_0 − n_2)), NaN se un ordinamento è tutto in parità — `shk.model.robustness:kendall_tau_b`; statistica di ranking "mediana pooled" (decisione del programmatore, 2026-10-17) — `shk.model.robustness:agent_statistics`; intervallo come i confronti, sul test dai soli seed — `shk.model.robustness:ranking_records`.
- Formula: intervalli del Modulo 2, stationary bootstrap dentro ciascuna finestra (righe con δ) a L_PW arrotondata, percentili sui ricampionamenti a rango pieno — `shk.model.module2:module2_bootstrap_interval`.
- Formula: intervallo percentile della media per stationary bootstrap — `shk.stats.bootstrap:stationary_bootstrap_mean_interval`.
- Casi limite: C2 − E non esiste con F = 0, perché E non c'è (`shk.model.comparisons:comparison_available`); nel ranking non entrano gli agenti con statistica non finita in una delle due esecuzioni; con meno di due ricampionamenti finiti l'intervallo t è NaN.

## Indice: user story, task e file

| Story | User story | Task | File principali |
|---|---|---|---|
| S1 | US-C1.2, US-C1.3 | T1–T7 | src/shk/kelly/simulate.py, src/shk/kelly/estimation.py, src/shk/kelly/staking.py, src/shk/kelly/scenarios.py, src/shk/kelly/core.py, scripts/us_c1_2_estimation_error.py, tests/test_us_c1_2_acceptance.py |
| S2 | US-C2.2, US-C2.3 | T8–T13 | src/shk/stats/anova.py, src/shk/stats/timeseries.py, src/shk/stats/false_rejection.py, src/shk/stats/calibration.py, scripts/us_c2_anova_autocorrelation.py, tests/test_us_c2_acceptance.py |
| S3 | US-C3.1–C3.4 | T14–T19 | src/shk/data/loading.py, src/shk/data/coverage.py, src/shk/data/split.py, config/split.toml, src/shk/market/devig.py, src/shk/market/divergence.py, src/shk/data/walkforward.py, tests/test_leakage.py |
| S4 | US-C4.1–C4.3 | T20–T25 | src/shk/model/elo.py, src/shk/model/elo_predictor.py, src/shk/model/elo_fit.py, src/shk/model/scoring.py, src/shk/model/recalibration.py, scripts/us_c4_2_g_hat.py |
| S5 | US-C5.1–C5.3 | T26–T32 | src/shk/model/residuals.py, src/shk/stats/drift.py, src/shk/model/monitoring.py, src/shk/kelly/backtest.py, scripts/us_c5_2_daily_z_test.py, scripts/us_c5_3_baseline_d.py |
| S6 | US-C6.1–C6.4 | T33–T39 | src/shk/kelly/agents.py, src/shk/kelly/environment.py, src/shk/kelly/metrics.py, src/shk/model/paired_backtest.py, src/shk/kelly/floor.py, src/shk/model/floor_real_config.py, src/shk/stats/heteroskedasticity.py, src/shk/model/residual_heteroskedasticity.py |
| S7 | debiti di S2–S6 | T40–T44 | src/shk/stats/false_rejection.py, tests/test_split.py, src/shk/stats/bootstrap.py, src/shk/model/block_length.py, src/shk/market/devig.py, src/shk/stats/variance_change.py, src/shk/model/variance_change.py |
| S8 | US-C7.1–C7.4 | T45–T49 | src/shk/stats/oaxaca.py, src/shk/stats/oaxaca_synthetic.py, src/shk/model/module2_data.py, src/shk/model/covariate_inspection.py, src/shk/model/module2.py, src/shk/model/known_scenarios.py, src/shk/model/season_objectives.py, src/shk/stats/nopo.py, src/shk/model/did_support.py |
| S9 | US-C8.1, US-C8.2 | T50–T54 | src/shk/model/stateful_agents.py, src/shk/model/module3.py, src/shk/model/module3_synthetic.py, src/shk/model/agent_c.py, src/shk/model/training_agents.py, src/shk/model/season_bootstrap.py, src/shk/model/power.py, src/shk/model/training_calibration.py, src/shk/model/frozen_params.py, config/frozen_params.toml |
| S10 | US-C8.2–C8.4 | T55–T58 | src/shk/model/frozen_agents.py, src/shk/model/validation_run.py, src/shk/model/comparisons.py, src/shk/model/comparisons_run.py, src/shk/model/g_hat_inference.py, src/shk/model/test_run.py |
| S11 | US-C9.1–C9.3 | T59–T63 | src/shk/model/dixon_coles.py, src/shk/model/dixon_coles_calibration.py, src/shk/model/module1.py, src/shk/model/task_seeds.py, src/shk/model/module1_seeds.py, config/frozen_params_dc.toml, src/shk/model/robustness.py, src/shk/model/devig_runs.py, src/shk/model/devig_sensitivity.py |
| S12 | riproducibilità e materiale per la tesi | T64–T66 | README.md, src/shk/data/manifest.py, scripts/reproduce_all.py, scripts/verify_raw_data.py, src/shk/thesis/tables.py, scripts/build_thesis_tables.py, scripts/build_thesis_figures.py, thesis/numeri.md, thesis/metodi_implementati.md, tests/test_metodi_implementati.py |

Gli script degli esperimenti sono `scripts/us_<storia>_<descrizione>.py`; ciascuno scrive `results/<nome>.csv` e `thesis/figures/<nome>.png`. I report dei task sono in `.agent/report/T<N>.md`.
