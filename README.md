# structural-hybrid-kelly

Codice di ricerca per una tesi sul criterio di Kelly in presenza di cambiamenti strutturali.
Il progetto studia il criterio in forma analitica e simulata, e lo applica alle partite di
Premier League (divisione E0, stagioni dal 1993-94 al 2023-24) con quote B365 pre-partita.

L'impianto ha tre moduli:
- **Modulo 1**: il modello previsivo walk-forward. È un Elo-Davidson; Dixon-Coles è il secondo modello di confronto.
- **Modulo 2**: la scomposizione di Oaxaca-Blinder dei residui δ = ln p̂ − ln q, per riconoscere il degrado strutturale del modello.
- **Modulo 3**: la frazione di Kelly λ che ne discende.

Gli agenti di scommessa (A, B, C0, C1, C2, D, E) si confrontano in backtest appaiati su validazione e test. Ci sono anche drift detection (ADWIN, Page-Hinkley), test di eteroschedasticità e analisi di sensibilità (Dixon-Coles e metodo di de-vigging).

Pacchetto importabile: `shk` (in `src/shk/`). Esperimenti: `scripts/us_<storia>_<descrizione>.py`.
Ciascuno scrive `results/<nome>.csv` e `thesis/figures/<nome>.png`.

## Installazione

Serve Python ≥ 3.11; il venv di riferimento è Python 3.12.7. Dalla radice del repository:

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
```

Su Linux e macOS l'interprete è `.venv/bin/python`. `pyproject.toml` non vincola le versioni
(decisioni S3 e S5): le versioni effettive con cui sono stati prodotti i risultati sono in
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
.venv/Scripts/python.exe scripts/reproduce_all.py --group elo             # catena Elo, da C1 a S10
.venv/Scripts/python.exe scripts/reproduce_all.py --group dixon_coles     # Dixon-Coles (T59, T61, T62)
.venv/Scripts/python.exe scripts/reproduce_all.py --group devig           # de-vigging (T63)
.venv/Scripts/python.exe scripts/reproduce_all.py --group elo --skip-slow # senza i passi lenti
```

Il run completo dura circa 20 ore e si fa per gruppi. Tempi indicativi, su 6 thread logici:

| gruppo | durata |
|---|---|
| elo | circa 6 h |
| dixon_coles | circa 6 h |
| devig | circa 8 h |

I tempi misurati sono nel report di T64 (`.agent/report/T64.md`).
- `--skip-slow` salta i passi che durano più di una decina di minuti.
- L'esito è in `build/reproduce/report_<gruppi>.txt`, con un file di uscita per passo in `build/reproduce/logs/`.
- Lo script termina con codice 1 se un passo fallisce o un file non coincide.

Dettagli:
- **Calibrazioni (T54, e la stessa con Dixon-Coles).** Girano con `--log-to` in `build/reproduce/`, perché i file congelati di `config/` si scrivono una sola volta. Il log rigenerato si confronta con quello versionato, e il testo del file congelato rigenerato con quello in `config/`.
- **Il 2023-24 non si riesegue.** Gli script delle esecuzioni sul test set (T58, il test di T62 e di T63) sono solo verificati, perché il test set si esegue una volta. Le tabelle che leggono le loro uscite per seed (`us_c9_2_robustness`, `us_c9_3_devig_sensitivity`) si ricostruiscono solo se quelle uscite sono in `results/raw/`, altrimenti si verificano soltanto.
- **Due file non si riproducono byte per byte**, per ragioni note. Per loro il manifesto registra uno SHA256 normalizzato, con la regola scritta nella riga:
  - `us_c3_1_data_coverage.csv`: con il test sbloccato lo script aggiunge le righe del 2023-24, che la regola `drop_seasons` toglie;
  - `us_c8_3b_power.csv` e `_dc`: i tempi misurati (`seconds_per_run`, `s10_hours`) che la regola `blank_columns` svuota.
- **Uscite per seed.** Quelle delle esecuzioni lunghe sono in `results/raw/`, non versionate.
- **File normalizzati dopo il run.** reproduce_all riscrive i file in `results/`. Dopo un run i file normalizzati
  risultano modificati per git, solo nelle parti escluse dal confronto: si ripristinano con `git checkout -- <file>`.

`--write-manifest` riscrive `results/MANIFEST.sha256` e `results/environment.txt` dai file presenti: va usato solo dopo un run accettato.

## Tabelle, figure e numeri per la tesi

```bash
.venv/Scripts/python.exe scripts/build_thesis_tables.py                       # tutte le tabelle e thesis/numeri.md
.venv/Scripts/python.exe scripts/build_thesis_tables.py --only tab_confronti  # una sola tabella
.venv/Scripts/python.exe scripts/build_thesis_figures.py                      # tutte le figure PDF
```

I due script leggono solo i CSV elencati in `results/MANIFEST.sha256` e non calcolano nulla di nuovo (T65).
- **Tabelle.** `thesis/tables/<nome>.tex` è LaTeX con booktabs (etichette in italiano, virgola decimale, fonte e SHA256 in nota). `thesis/tables/<nome>.csv` è la stessa tabella a piena precisione.
- **Figure.** `thesis/figures/tesi_<tema>.pdf` sono vettoriali e hanno uno stile comune. I PNG degli script degli esperimenti restano.
- **Numeri citabili.** `thesis/numeri.md` ha una voce per riga: valore, unità, CSV, selezione della riga, colonna e SHA256. `tests/test_thesis_outputs.py` rilegge ogni voce.

## Protocollo di split, congelamento e sblocco

Lo split temporale è in `config/split.toml`:
- training: 2000-01, 2010-11, 2020-21;
- validazione: 19 stagioni;
- test: 2023-24.

Lo split è congelato il 2026-09-29 (commit `90a77a1`, "C3 (#17)"). Il codice legge le stagioni per ruolo con `shk.data.split.load_by_role`, che rifiuta il test finché `test_unlocked = false`.

1. I parametri liberi degli agenti si calibrano sul solo training e si congelano in `config/frozen_params.toml`, scritto una volta dalla calibrazione di T54 e committato in `9f30b30` (2026-10-11). Il loader `shk.model.frozen_params.load_frozen_params` controlla che le chiavi siano esattamente quelle attese.
2. Il test set è sbloccato con `test_unlocked = true` nel commit `a5abca4` (2026-10-12), dopo il congelamento. Il 2023-24 è stato eseguito una sola volta (T58), senza ritocchi.
3. Con Dixon-Coles come Modulo 1 la stessa procedura produce `config/frozen_params_dc.toml` (T61), con la chiave in più `module1 = "dixon_coles"`. È committato in `b4c4e8a` (2026-10-17), prima dell'esecuzione con Dixon-Coles (T62).

Le decisioni e i report dei task sono in `.agent/` (BACKLOG.md e `report/T<N>.md`).

## Limiti noti

- **Determinismo fra piattaforme.** I risultati sono deterministici a parità di seed, ma i confronti a 1e-12 e gli SHA256 presuppongono le stesse versioni di numpy, scipy, pandas e river (`results/environment.txt`). Su altre versioni o piattaforme una differenza va riportata, non nascosta.
- **Due CSV normalizzati** nel manifesto (vedi sopra).
- **Test set.** Le esecuzioni sul 2023-24 non sono rieseguite da reproduce_all, e un utente nuovo ricostruisce le tabelle di T62 e T63 solo dopo averle eseguite a mano.
- **Dati grezzi.** I CSV di football-data.co.uk possono cambiare nel tempo: il manifesto lo rileva.
- **Figure.** Le figure PNG non sono nel manifesto.
- **Un test slow noto rosso.** `tests/test_us_c2_acceptance.py::test_acceptance_centered_calibrated_phi_zero_within_mc_interval`
  fallisce per L = 40, un risultato noto e accettato in T40 per L = 7 e 20. La versione non centrata
  (`test_acceptance_calibrated_phi_zero_within_mc_interval`) è marcata xfail.
