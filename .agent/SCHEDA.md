# Scheda del progetto
Origine: mappa del 2026-09-27, report fino a R2@2026-09-27

## Stato repo
Radice: c:\Users\malse\Documents\GitHub\structural_hybrid_kelly [V, R1@2026-09-27]
Branch main, ultimo commit a7420cb "create c1 (#5)", 4 commit in tutta la storia [V, R1@2026-09-27]
Working tree pulito prima della scrittura di .agent/MAPPA.md; subito dopo .agent/ risultava non tracciata [V, R1@2026-09-27] → Working tree modificato dal Task 1 (src/shk/kelly/simulate.py, tests/test_simulate.py); .agent/ ancora non tracciata al momento di R3 [D]
.agent/ si versiona con il repo e non va in .gitignore: decisione del programmatore del 2026-09-27; commit non ancora verificato [D]
main allineato a origin/main rispetto all'ultimo fetch locale; nessun git fetch eseguito durante la mappatura [V, R1@2026-09-27]
Remote origin: https://github.com/Fede046/structural_hybrid_kelly.git [V, R1@2026-09-27]
Branch locale feature/US-C1.1-Trade-off-crescita/varianza: probabile residuo della PR #4, stato di merge non riportato [D]

## Stack e comandi
Pacchetto structural-hybrid-kelly 0.1.0, importabile come shk, sorgenti in src/shk/ [V, R1@2026-09-27]
requires-python >=3.11 [V, R2@2026-09-27]; la CI usa Python 3.12 [V, R1@2026-09-27]
Dipendenze runtime: numpy, scipy, matplotlib, tutte senza vincolo di versione; nessun'altra (niente pandas) [V, R2@2026-09-27]
Dipendenze dev: solo pytest [V, R2@2026-09-27]
Build backend: hatchling [V, R1@2026-09-27]
Installazione usata dalla CI: pip install -e ".[dev]" [V, R1@2026-09-27]
uv.lock presente alla radice; uv sync come alternativa locale [D]
Test veloci: pytest -v; addopts = "-m 'not slow'" esclude i test slow; è anche il comando della CI [V, R2@2026-09-27]
Marker slow registrato in [tool.pytest.ini_options].markers [V, R2@2026-09-27]
Solo test slow: pytest -m slow; tutti i test: pytest -o addopts="" [D]
CI: .github/workflows/test.yml, trigger su push verso main e su pull_request; non esegue mai i test slow [V, R2@2026-09-27]
Esperimento C1.1: python scripts/us_c1_1_growth_vs_lambda.py dalla radice, con shk installato perché lo script importa da shk.kelly.* [D]
Nessuna variabile d'ambiente richiesta [D]
Nessun file .env tracciato né presente fra gli ignorati [V, R1@2026-09-27]
config/ e data/raw/ contengono solo .gitkeep [V, R2@2026-09-27]

## Moduli e responsabilità
src/shk/__init__.py — espone __version__ = "0.1.0" [V, R1@2026-09-27]
src/shk/kelly/__init__.py — re-esporta kelly_fraction e log_growth_rate tramite __all__ [V, R1@2026-09-27]
src/shk/kelly/__init__.py — expected_final_wealth non è re-esportata [D]
src/shk/kelly/core.py — formule chiuse per scommessa binaria: kelly_fraction(p, b), log_growth_rate(f, p, b), expected_final_wealth(f, p, b, T, b0=1.0) alle righe 97-144 [V, R1@2026-09-27]
src/shk/kelly/core.py — valida gli input in apertura con ValueError/TypeError [V, R1@2026-09-27]
src/shk/kelly/simulate.py — draw_outcomes(p, T, M, rng) da riga 6: restituisce ndarray (M, T) bool, True = vincita; valida p in [0, 1], T > 0, M > 0 e rng istanza di np.random.Generator (righe 38-44) [V, R2@2026-09-27]
src/shk/kelly/simulate.py — log_wealth_paths(outcomes, f, b) da riga 49: restituisce ndarray (M, T+1) float64 di ln(B_t/B_0), colonna 0 tutta 0.0; nessuna validazione degli input [V, R2@2026-09-27]
src/shk/kelly/metrics.py — sulle traiettorie: final_log_wealth, median_growth_rate, median_final_wealth, mean_final_wealth, max_drawdown (valori in [0, 1)), fraction_below_start; valida gli input [V, R1@2026-09-27]
scripts/us_c1_1_growth_vs_lambda.py — run_experiment() senza argomenti, chiamata dal blocco __main__ alle righe 160-161 [V, R2@2026-09-27]
core.py, simulate.py e metrics.py non si importano a vicenda [D]
Nessuna classe di dominio e nessun database; la persistenza è solo CSV e PNG [D]

## Flussi principali
Esperimento C1.1, parametri: p=0.60, b=1.0, t_steps=1000, m_trajectories=10000, seed=20260905, lambdas=np.linspace(0.0, 2.5, 51), tutti locali a run_experiment() alle righe 30-41 [V, R2@2026-09-27]
Esperimento C1.1, sequenza: f* con kelly_fraction; una sola matrice di esiti con draw_outcomes; per ogni λ: log_wealth_paths, 5 metriche empiriche, del paths, benchmark con log_growth_rate ed expected_final_wealth [V, R1@2026-09-27]
Esperimento C1.1: la frazione passata a log_wealth_paths è λ·f* [D]
Esperimento C1.1, output: results/us_c1_1_growth_vs_lambda.csv con 10 colonne (lambda, f, median_growth_rate, analytic_growth_rate, median_final_wealth, mean_final_wealth_mc, mean_final_wealth_analytic, drawdown_median, drawdown_p95, fraction_below_start) e thesis/figures/us_c1_1_growth_vs_lambda.png a tre pannelli [V, R1@2026-09-27]
Accettazione C1.1: tests/test_us_c1_1_acceptance.py, @pytest.mark.slow, stessi parametri scritti a mano; ogni test rigenera gli esiti con seed 20260905 e calcola solo median_growth_rate e max_drawdown [V, R1@2026-09-27]
Accettazione C1.1, asserzioni: picco della mediana a λ=1.0; drawdown mediano non decrescente con tolleranza -0.01; |g mediano| < 0.002 a λ=1.946; crescita negativa a λ=2.5 [V, R1@2026-09-27]
Uso come libreria: from shk.kelly import kelly_fraction, log_growth_rate; expected_final_wealth solo da shk.kelly.core [V, R1@2026-09-27]
Valori analitici di riferimento (p=0.6, b=1): f*=0.2; g(0.2)=0.020136; g(0.4)=-0.002447; g(0.5)≈-0.0340; zero di g a f≈0.3894, cioè λ≈1.947 [D, ricalcolo del supervisore]
Le costanti di tests/test_kelly_core.py:32 e :39 e il λ=1.946 dell'accettazione sono valori analitici, non empirici [D, ricalcolo del supervisore]
Per f>0 la traiettoria mediana è quella con numero mediano di vincite K; con K=600 su T=1000 il tasso di crescita mediano coincide con g analitico, e una vincita in più o in meno lo sposta di circa 0.0008 [D, ricalcolo del supervisore]

## Convenzioni da rispettare
Naming snake_case per moduli, funzioni e variabili; lettere matematiche standard (p, b, f, T, M, b0, λ) [V, R1@2026-09-27]
Identificatori, nomi dei test e messaggi di eccezione in inglese; commenti e docstring in italiano [V, R1@2026-09-27]
Type hints completi su argomenti e ritorni; docstring stile NumPy con sezioni Parametri / Restituisce / Solleva [V, R1@2026-09-27]
Validazione degli input in apertura di funzione: ValueError per i valori, TypeError per i tipi [V, R1@2026-09-27]
Nessun try:, print( o logging in src/ e scripts/ [V, R2@2026-09-27]
L'RNG entra come argomento np.random.Generator [V, R2@2026-09-27]
Vettorizzazione NumPy lungo l'asse delle M traiettorie; del paths nei loop Monte Carlo [V, R1@2026-09-27]
Script di esperimento: matplotlib.use("Agg") prima di importare pyplot; import diretti da shk.kelly.<modulo>; parametri locali in run_experiment(); nessun argomento da riga di comando [V, R2@2026-09-27]
Nome degli script: scripts/us_<storia>_<descrizione>.py, con lo stesso nome base per CSV e PNG [D, dedotto da un solo esempio]
Output: CSV in results/, figure in thesis/figures/, entrambi versionati in git [V, R2@2026-09-27]
Test in tests/test_*.py; i Monte Carlo su larga scala si marcano @pytest.mark.slow [V, R2@2026-09-27]
Documento della storia alla radice: C1.1.md, unico .md tracciato [V, R2@2026-09-27]

## Zone fragili da non toccare senza avviso
expected_final_wealth non ha test: 0 occorrenze in tests/ [V, R2@2026-09-27]; lo script C1.1 la importa alla riga 16 [V, R2@2026-09-27]
log_wealth_paths non valida gli input [V, R2@2026-09-27]; con f >= 1 produrrebbe -inf/nan che si propagano alle metriche [D]; una validazione f < 1 non romperebbe C1.1, dove f arriva al massimo a 0.5 [D]
Parametri dell'esperimento C1.1 duplicati fra run_experiment() (righe 30-41) e test di accettazione: cambiarli da una parte sola disallinea esperimento e verifica [V, R2@2026-09-27]
I test di accettazione non girano in CI: dopo ogni modifica a simulate.py o metrics.py vanno lanciati a mano con pytest -m slow [V, R2@2026-09-27 per la CI; D per il comando]
Rieseguire lo script C1.1 sovrascrive CSV e PNG versionati: ogni task che rigenera un esperimento deve dire se committarli [V, R2@2026-09-27]
Il test del drawdown non decrescente (tolleranza -0.01) è l'unica asserzione di accettazione di cui non è stata stimata la robustezza al seed e alla versione di NumPy [D]
Dipendenze senza versione in pyproject e CI che installa con pip senza lockfile [V, R2@2026-09-27]; NumPy non garantisce la stabilità del flusso di Generator fra versioni [D]
Docstring obsolete che dichiarano NotImplementedError: src/shk/kelly/simulate.py righe 77-81; tests/test_simulate.py righe 71-72 e 88-89 [V, R1@2026-09-27]
tests/test_metrics.py:test_metrics_error_conditions non verifica il ValueError di median_final_wealth e mean_final_wealth [D]

## Punti ancora incerti
Gestore canonico delle dipendenze (pip + pyproject oppure uv + uv.lock): non deciso dal programmatore. Blocca: se un task che aggiunge o fissa una dipendenza debba rigenerare uv.lock e se la CI vada migrata a uv. Si procede con pyproject.toml come fonte di verità, perché è l'unica che la CI verifica; un task che tocca le dipendenze modifica pyproject.toml e segnala uv.lock come da aggiornare.

## Ultimo aggiornamento
R2@2026-09-27 — task di scrittura chiusi dopo la mappa del 2026-09-27: nessuno