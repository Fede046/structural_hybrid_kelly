# structural-hybrid-kelly

Codice di ricerca per una tesi sul criterio di Kelly in presenza di cambiamenti strutturali.
Il progetto studia il criterio in forma analitica e simulata, e lo applica alle partite di
Premier League (divisione E0, stagioni dal 1993-94 al 2023-24) con quote B365 pre-partita.

L'impianto ha tre moduli:
- **Modulo 1**: il modello previsivo walk-forward. È un Elo-Davidson; Dixon-Coles è il secondo modello di confronto.
- **Modulo 2**: la scomposizione di Oaxaca-Blinder dei residui δ = ln p̂ − ln q, per riconoscere il degrado strutturale del modello.
- **Modulo 3**: la frazione di Kelly λ che ne discende.

Gli agenti di scommessa (A, B, C0, C1, C2, D, E) si confrontano in backtest appaiati su validazione e test. Ci sono anche drift detection (ADWIN, Page-Hinkley), test di eteroschedasticità e analisi di sensibilità (Dixon-Coles e metodo di de-vigging).

Pacchetto importabile: `shk` (in `src/shk/`). Esperimenti: uno script per analisi in `scripts/`, che scrive
`results/<nome>.csv` e, quando c'è, la figura `thesis/figures/<nome>.png`. L'elenco è in [Script e risultati](#script-e-risultati).

## Installazione

Serve Python ≥ 3.11; il venv di riferimento è Python 3.12.7. Dalla radice del repository:

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
```

Su Linux e macOS l'interprete è `.venv/bin/python`. `pyproject.toml` non vincola le versioni
(scelta di progetto): le versioni effettive con cui sono stati prodotti i risultati sono in
`results/environment.txt`. Tutti i comandi si lanciano dalla radice con l'interprete del venv.

## Dati grezzi

Un CSV per stagione della divisione E0 di [football-data.co.uk](https://www.football-data.co.uk/englandm.php), salvato come
`data/raw/E0/<YYYY-YY>.csv` (per esempio `data/raw/E0/1993-94.csv`, …, `data/raw/E0/2023-24.csv`: 31 file).
Il file della stagione 2023-24 si scarica, per esempio, da `https://www.football-data.co.uk/mmz4281/2324/E0.csv`.
I CSV non sono versionati. È versionato il loro manifesto SHA256, `data/raw/E0/MANIFEST.sha256`, che si verifica così:

```bash
.venv/Scripts/python.exe scripts/verify_raw_data.py
```

L'esito, file per file, è in `build/reproduce/verify_raw_data.txt`. Lo script termina con
codice 1 se un file manca, è diverso o non è nel manifesto. football-data.co.uk può aggiornare
i propri file: una differenza va controllata prima di rigenerare i risultati.

## Test

```bash
.venv/Scripts/python.exe -m pytest                         # suite veloce (i test slow sono esclusi da addopts)
.venv/Scripts/python.exe -m pytest -m slow                 # solo i test lenti
.venv/Scripts/python.exe -m pytest -m "slow or not slow"   # tutti
```

I test sui dati reali si saltano, con il motivo, se `data/raw/E0/` non contiene CSV. Quelli
che confrontano i risultati versionati girano anche senza dati.
La suite veloce dura circa 6 minuti con i dati.
Due controlli di `tests/test_us_c3_1_acceptance.py` si saltano da quando il test set è sbloccato.

## Esecutore unico

`scripts/reproduce_all.py` esegue gli script nell'ordine delle dipendenze. Poi confronta
ogni CSV di `results/` e i file congelati di `config/` con `results/MANIFEST.sha256`.

```bash
.venv/Scripts/python.exe scripts/reproduce_all.py --list                  # elenco dei passi in build/reproduce/steps.txt
.venv/Scripts/python.exe scripts/reproduce_all.py --group elo             # catena Elo, dalle simulazioni al test
.venv/Scripts/python.exe scripts/reproduce_all.py --group dixon_coles     # Dixon-Coles: modello, calibrazione, robustezza
.venv/Scripts/python.exe scripts/reproduce_all.py --group devig           # sensibilità al de-vigging
.venv/Scripts/python.exe scripts/reproduce_all.py --group elo --skip-slow # senza i passi lenti
```

Il run completo dura circa 20 ore e si fa per gruppi. Tempi indicativi, su 6 thread logici:

| gruppo | durata |
|---|---|
| elo | circa 6 h |
| dixon_coles | circa 6 h |
| devig | circa 8 h |

Misurati sull'esecuzione completa: elo 5.7 h, dixon_coles 4.9 h, devig 6.9 h.
- `--skip-slow` salta i passi che durano più di una decina di minuti.
- L'esito è in `build/reproduce/report_<gruppi>.txt`, con un file di uscita per passo in `build/reproduce/logs/`.
- Lo script termina con codice 1 se un passo fallisce o un file non coincide.

Dettagli:
- **Calibrazioni sul training (con l'Elo e con Dixon-Coles).** Girano con `--log-to` in `build/reproduce/`, perché i file congelati di `config/` si scrivono una sola volta. Il log rigenerato si confronta con quello versionato, e il testo del file congelato rigenerato con quello in `config/`.
- **Il 2023-24 non si riesegue.** Gli script delle esecuzioni sul test set (esecuzione unica, robustezza e sensibilità al de-vigging) sono solo verificati, perché il test set si esegue una volta. Le tabelle che leggono le loro uscite per seed (`us_c9_2_robustness`, `us_c9_3_devig_sensitivity`) si ricostruiscono solo se quelle uscite sono in `results/raw/`, altrimenti si verificano soltanto.
- **Due file non si riproducono byte per byte**, per ragioni note. Per loro il manifesto registra uno SHA256 normalizzato, con la regola scritta nella riga:
  - `us_c3_1_data_coverage.csv`: con il test sbloccato lo script aggiunge le righe del 2023-24, che la regola `drop_seasons` toglie;
  - `us_c8_3b_power.csv` e `_dc`: i tempi misurati (`seconds_per_run`, `s10_hours`) che la regola `blank_columns` svuota.
- **Uscite per seed.** Quelle delle esecuzioni lunghe sono in `results/raw/`, non versionate.
- **File normalizzati dopo il run.** reproduce_all riscrive i file in `results/`. Dopo un run i file normalizzati
  risultano modificati per git, solo nelle parti escluse dal confronto: si ripristinano con `git checkout -- <file>`.

`--write-manifest` riscrive `results/MANIFEST.sha256` e `results/environment.txt` dai file presenti: va usato solo dopo un run accettato.

## Script e risultati

Per ogni script di `scripts/`: il file che produce in `results/` (con la figura omonima in `thesis/figures/`, quando c'è) e il suo contenuto, nell'ordine in cui li esegue `reproduce_all.py`.

| Script | Risultati in `results/` | Contenuto |
|---|---|---|
| `us_c1_1_growth_vs_lambda.py` | `us_c1_1_growth_vs_lambda.csv` | Crescita e varianza del bankroll al variare della frazione di Kelly λ, con p e quota noti |
| `us_c1_2_estimation_error.py` | `us_c1_2_estimation_error.csv` | Effetto dell'errore di stima di p̂ su frazione e crescita; λ* contro quarto di Kelly |
| `us_c2_anova_autocorrelation.py` | `us_c2_anova_autocorrelation.csv` | Falso rigetto dell'ANOVA su serie AR(1), soglia nominale e calibrata col block bootstrap |
| `us_c3_1_data_coverage.py` | `us_c3_1_data_coverage.csv` | Copertura per stagione di risultati e quote dei bookmaker |
| `us_c3_2_devig_divergence.py` | `us_c3_2_devig_divergence.csv` | Divergenza fra metodi di de-vigging per fascia di quota |
| `us_c4_1_elo_walkforward.py` | `us_c4_1_elo_walkforward.csv` | Calibrazione dell'Elo sul training e previsioni walk-forward |
| `us_c4_2_g_hat.py` | `us_c4_2_g_hat.csv` | ĝ del modello contro il mercato, per serie, metodo e stagione |
| `us_c4_2b_g_hat_inference.py` | `us_c4_2b_g_hat_inference.csv` | Inferenza su ĝ: intervalli, placebo, finestre, fasce di quota, copertura |
| `us_c4_3_calibration.py` | `us_c4_3_calibration.csv` | Calibrazione del Modulo 1: reliability, Brier, Platt e isotonica |
| `us_c5_1_drift_detectors.py` | `us_c5_1_drift_detectors.csv` | Allarmi di ADWIN e Page-Hinkley sulla log-loss del Modulo 1 |
| `us_c5_2_daily_z_test.py` | `us_c5_2_daily_z_test.csv` | Z-test per matchday con soglia nominale e calibrata, confronto coi detector |
| `us_c5_3_baseline_d.py` | `us_c5_3_baseline_d.csv` | Baseline D (quarto di Kelly ridotto a ogni allarme) sulla validazione |
| `us_c6_2_paired_backtest.py` | `us_c6_2_paired_backtest.csv` | Backtest appaiato degli agenti A, B ed E, con e senza floor |
| `us_c6_3_floor_synthetic.py` | `us_c6_3_floor_synthetic.csv` | Floor sul calendario sintetico: rovina, soglie e tempi di rovina |
| `us_c6_3_floor_real_config.py` | `us_c6_3_floor_real_config.csv` | Floor nella configurazione reale, con esiti estratti dalle probabilità di mercato |
| `us_c6_4_heteroskedasticity.py` | `us_c6_4_heteroskedasticity.csv` | Breusch-Pagan e White sui residui del Modulo 1, soglie nominali e calibrate |
| `us_c6_4b_variance_change.py` | `us_c6_4b_variance_change.csv` | Varianza nel tempo: Goldfeld-Quandt, ARCH-LM, varianza mobile, Brown-Forsythe |
| `us_c7_1_ob_synthetic.py` | `us_c7_1_ob_synthetic.csv` | Oaxaca-Blinder su dati sintetici con componenti note |
| `us_c7_2_covariates.py` | `us_c7_2_covariates.csv` | δ per partita, covariate candidate e specificazione del Modulo 2 |
| `us_c7_3_module2.py` | `us_c7_3_module2.csv`, `us_c7_3_module2_ci.csv` | Modulo 2 su finestre scorrevoli e suoi intervalli |
| `us_c7_3b_known_scenarios.py` | `us_c7_3b_known_scenarios.csv` | Decomposizione negli scenari noti: transizioni, sospensione 2019-20, fine stagione |
| `us_c7_4_did_support.py` | `us_c7_4_did_support.csv` | DiD delle neopromosse, Ñopo e supporto comune |
| `us_c8_1a_module3_synthetic.py` | `us_c8_1a_module3_synthetic.csv` | Scelta della variante del Modulo 3 su verità sintetica |
| `us_c8_1b_agents_training.py` | `us_c8_1b_agents_training.csv` | Soglie dell'allarme di C1 ed esecuzione di prova degli agenti sul training |
| `us_c8_3a_block_length.py` | `us_c8_3a_block_length.csv` | Lunghezza dei blocchi di Politis-White e copertura degli intervalli |
| `us_c8_3b_power.py` | `us_c8_3b_power.csv` | Analisi di potenza e numero di seed |
| `us_c8_2_calibration.py` | `us_c8_2_calibration_log.csv` | Calibrazione degli agenti sul training e file congelato `config/frozen_params.toml` |
| `us_c8_3_validation.py` | `us_c8_3_validation_summary.csv` | Esecuzione con i parametri congelati sulle 19 stagioni di validazione |
| `us_c8_3_validation_with_history.py` | `us_c8_3_validation_with_history.csv` | Sensibilità con la catena del Modulo 2 che attraversa le stagioni |
| `us_c8_4_comparisons.py` | `us_c8_4_comparisons.csv` | Confronti fra agenti: intervalli, effect size, falsi allarmi |
| `us_c8_5_test_run.py` | `us_c8_5_test_run.csv` | Esecuzione unica sul test set 2023-24 |
| `kellybench_2023_24.py` | `kellybench_2023_24.csv` | Stagione 2023-24 giocata come in KellyBench, partendo da £100 000 |
| `us_c9_1_dixon_coles.py` | `us_c9_1_dixon_coles.csv` | Dixon-Coles walk-forward: calibrazione e confronto con l'Elo |
| `us_c9_2_robustness.py` | `us_c9_2_robustness.csv` | Robustezza del ranking degli agenti fra Elo e Dixon-Coles |
| `us_c9_3_devig_sensitivity.py` | `us_c9_3_devig_sensitivity.csv` | Sensibilità dei risultati al metodo di de-vigging |

Note:
- Con `--module1 dixon_coles` gli script del Modulo 2, degli agenti, della calibrazione e delle esecuzioni scrivono gli stessi risultati con il suffisso `_dc` (per esempio `us_c8_4_comparisons_dc.csv`). Il log della calibrazione con Dixon-Coles è `us_c9_2a_calibration_log_dc.csv`.
- Le uscite per seed delle esecuzioni lunghe sono in `results/raw/` (`.npz`, non versionate).
- I prefissi `us_c…` dei nomi sono identificativi storici delle analisi. Restano invariati perché i file congelati di `config/`, committati prima dello sblocco del test, citano i risultati con questi nomi.
- `build_thesis_tables.py` e `build_thesis_figures.py` producono il materiale per la tesi (vedi sotto), `verify_raw_data.py` verifica i CSV grezzi, `reproduce_all.py` riesegue e confronta tutto.

## Tabelle, figure e numeri per la tesi

```bash
.venv/Scripts/python.exe scripts/build_thesis_tables.py                       # tutte le tabelle e thesis/numeri.md
.venv/Scripts/python.exe scripts/build_thesis_tables.py --only tab_confronti  # una sola tabella
.venv/Scripts/python.exe scripts/build_thesis_figures.py                      # tutte le figure PDF
```

I due script leggono solo i CSV elencati in `results/MANIFEST.sha256` e non calcolano nulla di nuovo.
- **Tabelle.** `thesis/tables/<nome>.tex` è LaTeX con booktabs (etichette in italiano, virgola decimale, fonte e SHA256 in nota). `thesis/tables/<nome>.csv` è la stessa tabella a piena precisione.
- **Figure.** `thesis/figures/tesi_<tema>.pdf` sono vettoriali e hanno uno stile comune. I PNG degli script degli esperimenti restano.
- **Numeri citabili.** `thesis/numeri.md` ha una voce per riga: valore, unità, CSV, selezione della riga, colonna e SHA256. `tests/test_thesis_outputs.py` rilegge ogni voce.

## Stagione 2023-24 come in KellyBench

```bash
.venv/Scripts/python.exe scripts/kellybench_2023_24.py
```

Gli agenti, con il Modulo 1 Elo e i parametri congelati, giocano gli esiti veri del 2023-24 data per data partendo da £100 000, senza floor e con floor di £0.01 e £1. Lo script scrive `results/kellybench_2023_24.csv`, con il bankroll in sterline per agente e per data, e `thesis/figures/kellybench_2023_24.png`. È un'esecuzione descrittiva: non cambia nessun parametro.

## Protocollo di split, congelamento e sblocco

Lo split temporale è in `config/split.toml`:
- training: 2000-01, 2010-11, 2020-21;
- validazione: 19 stagioni;
- test: 2023-24.

Lo split è congelato il 2026-09-29 (commit `90a77a1`). Il codice legge le stagioni per ruolo con `shk.data.split.load_by_role`, che rifiuta il test finché `test_unlocked = false`.

1. I parametri liberi degli agenti si calibrano sul solo training e si congelano in `config/frozen_params.toml`, scritto una volta dalla calibrazione sul training e committato in `9f30b30` (2026-10-11). Il loader `shk.model.frozen_params.load_frozen_params` controlla che le chiavi siano esattamente quelle attese.
2. Il test set è sbloccato con `test_unlocked = true` nel commit `a5abca4` (2026-10-12), dopo il congelamento. Il 2023-24 è stato eseguito una sola volta, senza ritocchi.
3. Con Dixon-Coles come Modulo 1 la stessa procedura produce `config/frozen_params_dc.toml`, con la chiave in più `module1 = "dixon_coles"`. È committato in `b4c4e8a` (2026-10-17), prima dell'esecuzione con Dixon-Coles.


## Limiti noti

- **Determinismo fra piattaforme.** I risultati sono deterministici a parità di seed, ma i confronti a 1e-12 e gli SHA256 presuppongono le stesse versioni di numpy, scipy, pandas e river (`results/environment.txt`). Su altre versioni o piattaforme una differenza va riportata, non nascosta.
- **Due CSV normalizzati** nel manifesto (vedi sopra).
- **Test set.** Le esecuzioni sul 2023-24 non sono rieseguite da reproduce_all, e un utente nuovo ricostruisce le tabelle di robustezza e di sensibilità al de-vigging solo dopo averle eseguite a mano.
- **Dati grezzi.** I CSV di football-data.co.uk possono cambiare nel tempo: il manifesto lo rileva.
- **Figure.** Le figure PNG non sono nel manifesto.
- **Un test slow noto rosso.** `tests/test_us_c2_acceptance.py::test_acceptance_centered_calibrated_phi_zero_within_mc_interval`
  fallisce per L = 40, un risultato noto: la calibrazione centrata funziona per L = 7 e 20. La versione non centrata
  (`test_acceptance_calibrated_phi_zero_within_mc_interval`) è marcata xfail.
