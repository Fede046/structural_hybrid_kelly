"""Script T58: esecuzione unica sul test set 2023-24.

Senza argomenti esegue il 2023-24 (una volta sola) e scrive results/us_c8_5_test_run.csv,
results/raw/us_c8_5_test_raw.npz (non versionato) e thesis/figures/us_c8_5_test_run.png.
Con `--dry-run` esegue la stessa catena sul 2022-23 (validazione, stesso fit 2020-21) e
scrive le uscite in build/scratch/t58/dry_run/, per provare il codice prima dell'esecuzione
unica. I seed vanno su WORKERS processi; i risultati non dipendono dal loro numero.
Con `--figure-only` rigenera solo la figura dal CSV già scritto.
Con `--module1 dixon_coles` usa il Modulo 1 Dixon-Coles e config/frozen_params_dc.toml, e scrive
le uscite con il suffisso _dc, senza toccare quelle Elo (T60).
"""

import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from shk.model.frozen_agents import AGENT_ORDER
from shk.model.module1 import MODULE1_ELO, module1_from_argv, with_module1_suffix
from shk.model.module1_seeds import s10_seed
from shk.model.test_run import (
    DRY_RUN_SEASON,
    TEST_FIT,
    TEST_RUN_COLUMNS,
    TEST_SEASON,
    agent_summary_records,
    check_records,
    comparison_records_single,
    drift_records,
    e_roi_records,
    evaluate_agents,
    g_hat_records,
    load_season_data,
    module2_records,
    stratum_records,
    t58_sequences,
)
from shk.model.validation_run import save_raw

WORKERS = 5


def output_paths(dry_run: bool, module1: str = MODULE1_ELO) -> tuple[str, Path, Path, Path]:
    """Stagione e percorsi di CSV, raw e figura (con il suffisso del Modulo 1)."""
    repo_root = Path(__file__).resolve().parents[1]
    if dry_run:
        out_dir = repo_root / "build" / "scratch" / "t58" / "dry_run"
        paths = (out_dir / "test_run.csv", out_dir / "test_raw.npz", out_dir / "test_run.png")
        season = DRY_RUN_SEASON
    else:
        paths = (repo_root / "results" / "us_c8_5_test_run.csv", repo_root / "results" / "raw" / "us_c8_5_test_raw.npz",
                 repo_root / "thesis" / "figures" / "us_c8_5_test_run.png")
        season = TEST_SEASON
    csv_path, raw_path, png_path = (with_module1_suffix(p, module1) for p in paths)
    return season, csv_path, raw_path, png_path


def run_experiment(dry_run: bool = False, module1: str = MODULE1_ELO) -> None:
    """Esegue tutte le misure di T58 sulla stagione e scrive CSV, raw e figura."""
    season, csv_path, raw_path, png_path = output_paths(dry_run, module1)
    for p in (csv_path, raw_path, png_path):
        p.parent.mkdir(parents=True, exist_ok=True)

    sd = load_season_data(season, TEST_FIT, module1)
    seed = s10_seed(module1)
    records = check_records(sd)
    records += g_hat_records(sd, t58_sequences(seed)[3].spawn(2)[0])
    records += drift_records(sd)
    records += module2_records(sd)
    result = evaluate_agents(sd, workers=WORKERS, seed=seed)
    save_raw(raw_path, result.block)
    save_raw(raw_path.with_name(raw_path.stem + "_iid.npz"), result.iid)
    records += agent_summary_records(result)
    records += comparison_records_single(result, seed=seed)
    records += stratum_records(sd, seed=seed)
    records += e_roi_records(result)
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(TEST_RUN_COLUMNS))
        writer.writeheader()
        writer.writerows(records)
    make_figure(pd.read_csv(csv_path), png_path, season)


def make_figure(df: pd.DataFrame, png_path: Path, season: str) -> None:
    """Tre pannelli: ĝ per metodo e serie, agenti sui seed e sull'osservata, strati per neopromossa."""
    fig, (ax_a, ax_b, ax_c) = plt.subplots(1, 3, figsize=(22, 6.5))

    g = df[(df["row_type"] == "g_hat") & (pd.to_numeric(df["n"], errors="coerce") > 0)]
    labels = [f"{s.split('_')[0]}\n{m}" for s, m in zip(g["series"], g["method"])]
    x = np.arange(len(g))
    est = g["estimate"].astype(float).to_numpy()
    lo, hi = g["ci_low"].astype(float).to_numpy(), g["ci_high"].astype(float).to_numpy()
    ax_a.errorbar(x, est, yerr=[np.maximum(est - lo, 0), np.maximum(hi - est, 0)], fmt="o", capsize=3)
    ax_a.axhline(0.0, color="black", linewidth=0.8)
    ax_a.set_xticks(x)
    ax_a.set_xticklabels(labels, fontsize=7, rotation=45)
    ax_a.set_ylabel("ĝ con intervallo al 95% (stationary a L_PW)")
    ax_a.set_title(f"A) ĝ sul {season}", loc="left", fontsize=11, fontweight="bold")
    ax_a.grid(True, axis="y", linestyle=":", alpha=0.6)

    s = df[(df["row_type"] == "summary") & (df["config"] == "gbp_0.01")]
    s = s.set_index("agent").loc[[a for a in AGENT_ORDER if a in set(s["agent"])]]
    x = np.arange(len(s))
    med = s["median_log_wealth"].astype(float).to_numpy()
    q05, q95 = s["q05_log_wealth"].astype(float).to_numpy(), s["q95_log_wealth"].astype(float).to_numpy()
    ax_b.errorbar(x, med, yerr=[np.maximum(med - q05, 0), np.maximum(q95 - med, 0)], fmt="o", capsize=3,
                  label="seed: mediana, 5–95%")
    ax_b.scatter(x, s["observed_log_wealth"].astype(float), marker="x", color="tab:red", s=60,
                 label="realizzazione osservata")
    ax_b.axhline(0.0, color="black", linewidth=0.8)
    ax_b.set_xticks(x)
    ax_b.set_xticklabels(s.index, rotation=45)
    ax_b.set_ylabel("ln W_T")
    ax_b.set_title("B) Agenti, configurazione £0.01", loc="left", fontsize=11, fontweight="bold")
    ax_b.legend(fontsize=8)
    ax_b.grid(True, axis="y", linestyle=":", alpha=0.6)

    st = df[df["row_type"] == "stratum"]
    x = np.arange(len(st))
    d = st["estimate"].astype(float).to_numpy()
    dl, dh = st["delta_low"].astype(float).to_numpy(), st["delta_high"].astype(float).to_numpy()
    ax_c.errorbar(x - 0.1, d, yerr=[np.maximum(d - dl, 0), np.maximum(dh - d, 0)], fmt="o", capsize=3, label="δ̄")
    ax_c2 = ax_c.twinx()
    ax_c2.bar(x + 0.15, st["mean_fraction_c2"].astype(float), 0.25, color="tab:green", alpha=0.5, label="frazione C2")
    ax_c2.bar(x + 0.4, st["mean_fraction_b025"].astype(float), 0.25, color="tab:gray", alpha=0.5,
              label="frazione B_0.25")
    ax_c.axhline(0.0, color="black", linewidth=0.8)
    ax_c.set_xticks(x)
    ax_c.set_xticklabels([f"{t}\n({s_})" for t, s_ in zip(st["team"], st["status"])], fontsize=8)
    ax_c.set_ylabel("δ̄ con intervallo al 95%")
    ax_c2.set_ylabel("Frazione media puntata, F = 0")
    ax_c.set_title("C) Neopromosse e squadre note", loc="left", fontsize=11, fontweight="bold")
    h1, l1 = ax_c.get_legend_handles_labels()
    h2, l2 = ax_c2.get_legend_handles_labels()
    ax_c.legend(h1 + h2, l1 + l2, fontsize=8)
    ax_c.grid(True, axis="y", linestyle=":", alpha=0.6)

    fig.tight_layout()
    fig.savefig(png_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv[1:]
    module1_ = module1_from_argv(sys.argv[1:])
    if "--figure-only" in sys.argv[1:]:
        season_, csv_, _, png_ = output_paths(dry, module1_)
        make_figure(pd.read_csv(csv_), png_, season_)
    else:
        run_experiment(dry_run=dry, module1=module1_)
