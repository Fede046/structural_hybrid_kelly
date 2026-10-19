"""Esecutore unico: rigenera i risultati e li confronta con results/MANIFEST.sha256.

Esegue gli script nell'ordine delle dipendenze, per gruppi (decisione del programmatore del
2026-10-18: il run completo dura circa 20 h e si fa in più riprese, ciascuna sotto le 12 h):
- elo: dalle simulazioni di Kelly alle esecuzioni congelate, con il Modulo 1 Elo (circa 6 h);
- dixon_coles: Dixon-Coles walk-forward, calibrazione con Dixon-Coles e robustezza del ranking (circa 6 h);
- devig: validazioni con i cinque metodi di de-vigging e la tabella di sensibilità (circa 8 h).
Opzioni:
- --group NOME (ripetibile; senza, tutti i gruppi);
- --skip-slow salta i passi lenti (più di circa 10 minuti), che restano solo verificati;
- --list scrive l'elenco dei passi in build/reproduce/steps.txt e termina;
- --write-manifest scrive results/MANIFEST.sha256 e results/environment.txt dai file presenti
  (solo per crearli o aggiornarli, dopo un run accettato);
- --compare-only non esegue nulla: confronta il manifesto con i file presenti e, per i gruppi
  indicati, con i file congelati già rigenerati in build/reproduce/.

Le esecuzioni sul 2023-24 (l'esecuzione unica e i test della robustezza del ranking e della sensibilità al de-vigging) non si rieseguono (decisione del
2026-10-18): i loro CSV si verificano soltanto. Le tabelle che leggono le uscite per seed del
2023-24 (us_c9_2_robustness, us_c9_3_devig_sensitivity) si ricostruiscono solo se quelle uscite
ci sono in results/raw/, altrimenti si verificano soltanto.

La calibrazione sul training (e quella con Dixon-Coles) gira con --log-to build/reproduce/…: il log si
confronta con la riga del manifesto del log versionato, e il testo del file congelato con quella
di config/frozen_params*.toml.

Esiti in build/reproduce/: un file di uscita per passo in logs/ e il rapporto report.txt (passi
eseguiti, saltati o solo verificati; confronto con il manifesto). Se un passo fallisce o un file
non coincide, lo script termina con codice 1. I tempi si misurano dall'esterno.
"""

import importlib.metadata
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

from shk.data.manifest import ManifestEntry, build_entries, check_entries, read_manifest, write_manifest
from shk.data.split import read_split_config
from shk.market.devig import DEVIG_METHOD_NAMES
from shk.model.power import TIMING_COLUMNS

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "build" / "reproduce"
MANIFEST = REPO_ROOT / "results" / "MANIFEST.sha256"
ENVIRONMENT = REPO_ROOT / "results" / "environment.txt"
GROUPS = ("elo", "dixon_coles", "devig")
DC = ("--module1", "dixon_coles")
CAL_LOG = "build/reproduce/us_c8_2_calibration_log.csv"
CAL_LOG_DC = "build/reproduce/us_c9_2a_calibration_log_dc.csv"


class Step(NamedTuple):
    """Un passo: script con argomenti, file prodotti e condizioni."""

    group: str
    script: str
    args: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()           # righe del manifesto prodotte dal passo
    slow: bool = False
    test_set: bool = False                  # usa il 2023-24: non si riesegue
    needs: tuple[str, ...] = ()             # file necessari; se mancano il passo è solo verificato
    replaces: tuple[tuple[str, str], ...] = ()  # (riga del manifesto, file prodotto al suo posto)


def _r(name: str) -> str:
    return f"results/{name}.csv"


def _raw(name: str) -> str:
    return f"results/raw/{name}.npz"


STEPS: tuple[Step, ...] = (
    Step("elo", "us_c1_1_growth_vs_lambda", outputs=(_r("us_c1_1_growth_vs_lambda"),)),
    Step("elo", "us_c1_2_estimation_error", outputs=(_r("us_c1_2_estimation_error"),)),
    Step("elo", "us_c2_anova_autocorrelation", outputs=(_r("us_c2_anova_autocorrelation"),)),
    Step("elo", "us_c3_1_data_coverage", outputs=(_r("us_c3_1_data_coverage"),)),
    Step("elo", "us_c3_2_devig_divergence", outputs=(_r("us_c3_2_devig_divergence"),)),
    Step("elo", "us_c4_1_elo_walkforward", outputs=(_r("us_c4_1_elo_walkforward"),)),
    Step("elo", "us_c4_2_g_hat", outputs=(_r("us_c4_2_g_hat"),)),
    Step("elo", "us_c4_2b_g_hat_inference", outputs=(_r("us_c4_2b_g_hat_inference"),), slow=True),
    Step("elo", "us_c4_3_calibration", outputs=(_r("us_c4_3_calibration"),)),
    Step("elo", "us_c5_1_drift_detectors", outputs=(_r("us_c5_1_drift_detectors"),)),
    Step("elo", "us_c5_2_daily_z_test", outputs=(_r("us_c5_2_daily_z_test"),)),
    Step("elo", "us_c5_3_baseline_d", outputs=(_r("us_c5_3_baseline_d"),)),
    Step("elo", "us_c6_2_paired_backtest", outputs=(_r("us_c6_2_paired_backtest"),)),
    Step("elo", "us_c6_3_floor_synthetic", outputs=(_r("us_c6_3_floor_synthetic"),)),
    Step("elo", "us_c6_3_floor_real_config", outputs=(_r("us_c6_3_floor_real_config"),)),
    Step("elo", "us_c6_4_heteroskedasticity", outputs=(_r("us_c6_4_heteroskedasticity"),)),
    Step("elo", "us_c6_4b_variance_change", outputs=(_r("us_c6_4b_variance_change"),)),
    Step("elo", "us_c7_1_ob_synthetic", outputs=(_r("us_c7_1_ob_synthetic"),)),
    Step("elo", "us_c7_2_covariates", outputs=(_r("us_c7_2_covariates"),)),
    Step("elo", "us_c7_3_module2", outputs=(_r("us_c7_3_module2"), _r("us_c7_3_module2_ci"))),
    Step("elo", "us_c7_3b_known_scenarios", outputs=(_r("us_c7_3b_known_scenarios"),)),
    Step("elo", "us_c7_4_did_support", outputs=(_r("us_c7_4_did_support"),)),
    Step("elo", "us_c8_1a_module3_synthetic", outputs=(_r("us_c8_1a_module3_synthetic"),)),
    Step("elo", "us_c8_1b_agents_training", outputs=(_r("us_c8_1b_agents_training"),)),
    Step("elo", "us_c8_3a_block_length", outputs=(_r("us_c8_3a_block_length"),)),
    Step("elo", "us_c8_3b_power", outputs=(_r("us_c8_3b_power"),), slow=True),
    Step("elo", "us_c8_2_calibration", ("--log-to", CAL_LOG), outputs=(_r("us_c8_2_calibration_log"),),
         slow=True, replaces=((_r("us_c8_2_calibration_log"), CAL_LOG),
                              ("config/frozen_params.toml", CAL_LOG.replace(".csv", ".toml")))),
    Step("elo", "us_c8_3_validation", outputs=(_r("us_c8_3_validation_summary"),), slow=True),
    Step("elo", "us_c8_3_validation_with_history", outputs=(_r("us_c8_3_validation_with_history"),),
         needs=(_raw("us_c8_3_validation_raw"),)),
    Step("elo", "us_c8_4_comparisons", outputs=(_r("us_c8_4_comparisons"),), slow=True,
         needs=(_raw("us_c8_3_validation_raw"),)),
    Step("elo", "us_c8_5_test_run", outputs=(_r("us_c8_5_test_run"),), test_set=True),
    Step("elo", "kellybench_2023_24", outputs=(_r("kellybench_2023_24"),), test_set=True),
    Step("dixon_coles", "us_c9_1_dixon_coles", outputs=(_r("us_c9_1_dixon_coles"),)),
    Step("dixon_coles", "us_c7_2_covariates", DC, outputs=(_r("us_c7_2_covariates_dc"),)),
    Step("dixon_coles", "us_c7_3_module2", DC, outputs=(_r("us_c7_3_module2_dc"), _r("us_c7_3_module2_ci_dc"))),
    Step("dixon_coles", "us_c8_1b_agents_training", DC, outputs=(_r("us_c8_1b_agents_training_dc"),)),
    Step("dixon_coles", "us_c8_3b_power", DC, outputs=(_r("us_c8_3b_power_dc"),), slow=True),
    Step("dixon_coles", "us_c8_2_calibration", DC + ("--log-to", CAL_LOG_DC),
         outputs=(_r("us_c9_2a_calibration_log_dc"),), slow=True,
         replaces=((_r("us_c9_2a_calibration_log_dc"), CAL_LOG_DC),
                   ("config/frozen_params_dc.toml", CAL_LOG_DC.replace(".csv", ".toml")))),
    Step("dixon_coles", "us_c8_3_validation", DC, outputs=(_r("us_c8_3_validation_summary_dc"),), slow=True),
    Step("dixon_coles", "us_c8_4_comparisons", DC, outputs=(_r("us_c8_4_comparisons_dc"),), slow=True,
         needs=(_raw("us_c8_3_validation_raw_dc"),)),
    Step("dixon_coles", "us_c8_5_test_run", DC, outputs=(_r("us_c8_5_test_run_dc"),), test_set=True),
    Step("dixon_coles", "us_c9_2_robustness", outputs=(_r("us_c9_2_robustness"),),
         needs=tuple(_raw(n) for n in ("us_c8_3_validation_raw", "us_c8_3_validation_raw_dc", "us_c8_5_test_raw",
                                       "us_c8_5_test_raw_dc"))),
    *(Step("devig", "us_c9_3_devig_sensitivity", ("--run", m, "--validation-only"), slow=True)
      for m in DEVIG_METHOD_NAMES),
    Step("devig", "us_c9_3_devig_sensitivity", outputs=(_r("us_c9_3_devig_sensitivity"),),
         needs=tuple(_raw(f"us_c9_3_test_raw_{m}{s}") for m in DEVIG_METHOD_NAMES for s in ("", "_iid"))),
)


def normalization_rules() -> dict[str, str]:
    """Regole di normalizzazione del manifesto (decisioni del 2026-10-18).

    I file congelati registrano lo SHA256 grezzo del CSV di potenza, che dipende dai tempi
    misurati: la riga us_c8_3b_power della sezione [sources] si toglie dal confronto.
    """
    test_seasons = ",".join(read_split_config().test)
    timing = ",".join(TIMING_COLUMNS)
    return {
        _r("us_c3_1_data_coverage"): f"drop_seasons:{test_seasons}",
        _r("us_c8_3b_power"): f"blank_columns:{timing}",
        _r("us_c8_3b_power_dc"): f"blank_columns:{timing}",
        "config/frozen_params.toml": "drop_lines:us_c8_3b_power =",
        "config/frozen_params_dc.toml": "drop_lines:us_c8_3b_power =",
    }


def step_label(step: Step) -> str:
    return " ".join((f"scripts/{step.script}.py",) + step.args)


def write_steps_list(path: Path) -> None:
    """Elenco dei passi in ordine, con gruppo e attributi."""
    lines = [f"{i:2d}  {s.group:<12} {step_label(s)}"
             + ("  [lento]" if s.slow else "") + ("  [2023-24: solo verifica]" if s.test_set else "")
             + (f"  [richiede {', '.join(s.needs)}]" if s.needs else "")
             for i, s in enumerate(STEPS, 1)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_manifest_and_environment() -> None:
    """results/MANIFEST.sha256 da tutti i CSV di results/ e dai file congelati; results/environment.txt."""
    paths = sorted(p.relative_to(REPO_ROOT).as_posix() for p in (REPO_ROOT / "results").glob("*.csv"))
    paths += ["config/frozen_params.toml", "config/frozen_params_dc.toml"]
    header = (
        "SHA256 dei CSV di results/ e dei file congelati in config/.",
        "Formato: <sha256>  <percorso>[  normalized=<regola>]. Regole (decisione del 2026-10-18):",
        "drop_seasons: righe delle stagioni date tolte (us_c3_1 aggiunge il test dopo lo sblocco);",
        "blank_columns: colonne svuotate (tempi misurati di us_c8_3b_power, TIMING_COLUMNS di power.py);",
        "drop_lines: righe tolte (nei file congelati, lo SHA256 grezzo del CSV di potenza, che dipende dai tempi).",
        "Verifica: .venv/Scripts/python.exe scripts/reproduce_all.py (vedi README.md).",
    )
    write_manifest(MANIFEST, build_entries(REPO_ROOT, paths, normalization_rules()), header)
    packages = sorted(f"{d.metadata['Name']}=={d.version}" for d in importlib.metadata.distributions())
    ENVIRONMENT.write_text("\n".join([f"python {sys.version.split()[0]}", f"platform {platform.platform()}",
                                      f"implementation {platform.python_implementation()}", ""] + packages) + "\n",
                           encoding="utf-8", newline="\n")


def run_steps(groups: tuple[str, ...], skip_slow: bool) -> tuple[list[str], list[Step], dict[str, str]]:
    """Esegue i passi dei gruppi; righe del rapporto, passi falliti e sostituzioni per il confronto."""
    logs = OUT_DIR / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    report, failed, replacements = [], [], {}
    for i, step in enumerate(STEPS, 1):
        if step.group not in groups:
            continue
        label = f"{i:2d} {step_label(step)}"
        missing = [n for n in step.needs if not (REPO_ROOT / n).exists()]
        if step.test_set or (skip_slow and step.slow) or missing:
            reason = ("2023-24, solo verifica" if step.test_set else "lento, saltato" if step.slow and skip_slow
                      else f"mancano {', '.join(missing)}: solo verifica")
            report.append(f"skipped  {label}  ({reason})")
            continue
        for _, produced in step.replaces:
            for suffix in (".csv", ".toml"):
                (REPO_ROOT / Path(produced).with_suffix(suffix)).unlink(missing_ok=True)
        tag = re.sub(r"[^A-Za-z0-9]+", "_", " ".join(step.args)).strip("_")
        log = logs / f"{i:02d}_{step.script}{'_' + tag if tag else ''}.txt"
        with open(log, "w", encoding="utf-8") as out:
            code = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / f"{step.script}.py"), *step.args],
                                  cwd=REPO_ROOT, stdout=out, stderr=subprocess.STDOUT).returncode
        report.append(f"{'ok' if code == 0 else 'FAILED'}  {label}  (exit {code})")
        if code != 0:
            failed.append(step)
        replacements.update(dict(step.replaces))
    return report, failed, replacements


def compare(groups: tuple[str, ...], replacements: dict[str, str]) -> tuple[list[str], int]:
    """Confronto di ogni riga del manifesto; righe del rapporto e numero di differenze."""
    regenerated = {o for s in STEPS if s.group in groups for o in s.outputs + tuple(k for k, _ in s.replaces)}
    results = check_entries(REPO_ROOT, read_manifest(MANIFEST), replacements)
    lines = []
    for r in results:
        kind = "rigenerato" if r.entry.path in regenerated and r.entry.path not in _not_rerun(groups) else "verificato"
        lines.append(f"{r.status}  {r.entry.path}  ({kind}{', ' + r.entry.rule if r.entry.rule else ''}"
                     f"{', confrontato con ' + r.checked_path if r.entry.path in replacements else ''})")
    return lines, sum(r.status != "ok" for r in results)


def _not_rerun(groups: tuple[str, ...]) -> set[str]:
    return {o for s in STEPS if s.group in groups and s.test_set for o in s.outputs}


def main(argv: list[str]) -> None:
    """Interpreta le opzioni ed esegue (vedi modulo)."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if "--list" in argv:
        write_steps_list(OUT_DIR / "steps.txt")
        return
    if "--write-manifest" in argv:
        write_manifest_and_environment()
        return
    groups = tuple(argv[i + 1] for i, a in enumerate(argv) if a == "--group") or GROUPS
    unknown = set(groups) - set(GROUPS)
    if unknown:
        raise ValueError(f"Unknown group(s) {sorted(unknown)}, expected {GROUPS}")
    if "--compare-only" in argv:
        report, failed = ["nessun passo eseguito (--compare-only)"], []
        replacements = {k: v for s in STEPS if s.group in groups for k, v in s.replaces if (REPO_ROOT / v).exists()}
    else:
        report, failed, replacements = run_steps(groups, "--skip-slow" in argv)
    lines, n_diff = compare(groups, replacements)
    text = (["gruppi: " + ", ".join(groups), "", "passi:"] + report + ["", "confronto con results/MANIFEST.sha256:"]
            + lines + ["", f"passi falliti: {len(failed)}; differenze: {n_diff}"])
    suffix = "_compare_only" if "--compare-only" in argv else ""
    (OUT_DIR / f"report_{'_'.join(groups)}{suffix}.txt").write_text("\n".join(text) + "\n", encoding="utf-8")
    if failed or n_diff:
        sys.exit(f"reproduce_all: {len(failed)} failed steps, {n_diff} differences (see {OUT_DIR})")


if __name__ == "__main__":
    main(sys.argv[1:])
