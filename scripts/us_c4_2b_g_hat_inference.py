"""Script T57: ĝ formalizzato, con intervalli, placebo, finestre, fasce di quota, soglia ln π e copertura.

Scrive results/us_c4_2b_g_hat_inference.csv e thesis/figures/us_c4_2b_g_hat_inference.png
(shk.model.g_hat_inference). Le permutazioni del placebo girano su WORKERS processi; ognuna
ha il proprio generatore, quindi i risultati non dipendono dal numero di processi.
"""

import csv
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from shk.model.g_hat_inference import (
    G_HAT_INFERENCE_COLUMNS,
    N_PERMUTATIONS,
    _row,
    acf_rows,
    band_rows,
    coverage_records,
    evaluate_series,
    interval_rows,
    load_full_frame,
    placebo_g_hats,
    placebo_records,
    rolling_shares,
    season_g_hats,
    t57_sequences,
    threshold_rows,
)

WORKERS = 5
CHUNK = 50


def run_experiment() -> None:
    """Calcola tutte le righe di T57, scrive CSV e figura."""
    repo_root = Path(__file__).resolve().parents[1]
    csv_path = repo_root / "results" / "us_c4_2b_g_hat_inference.csv"
    png_path = repo_root / "thesis" / "figures" / "us_c4_2b_g_hat_inference.png"
    png_path.parent.mkdir(parents=True, exist_ok=True)

    df_full = load_full_frame()
    evals = evaluate_series(df_full)
    seq_int, seq_perm, seq_cov = t57_sequences()

    records = []
    intervals = interval_rows(evals, seq_int)
    for r in intervals:
        width_iid = r.iid_high - r.iid_low
        pooled = r.interval_method == "t_cluster"
        records.append(_row(row_type="interval", series=r.series, method=r.method, season=r.season, n=r.n,
                            g_hat=r.g_hat, l_pw="" if r.l_pw < 0 else r.l_pw, interval_method=r.interval_method,
                            se_boot_block=r.se_block if pooled else "", se_boot_iid=r.se_iid if pooled else "",
                            ci_block_low=r.block_low, ci_block_high=r.block_high, ci_iid_low=r.iid_low,
                            ci_iid_high=r.iid_high,
                            ci_block_pct_low=r.block_pct_low if pooled else "",
                            ci_block_pct_high=r.block_pct_high if pooled else "",
                            ci_iid_pct_low=r.iid_pct_low if pooled else "",
                            ci_iid_pct_high=r.iid_pct_high if pooled else "",
                            width_ratio_block_iid=(r.block_high - r.block_low) / width_iid))
    ln_pi = {(t["series"], t["season"]): t["mean_ln_pi"] for t in threshold_rows(evals)}
    for r in intervals:
        lp = ln_pi[(r.series, r.season)]
        records.append(_row(row_type="threshold", series=r.series, method=r.method, season=r.season, n=r.n,
                            g_hat=r.g_hat, mean_ln_pi=lp, g_minus_ln_pi=r.g_hat - lp,
                            ci_block_low=r.block_low, ci_block_high=r.block_high))

    observed = season_g_hats(evals)
    chunks = [(df_full, seq_perm, s, min(s + CHUNK, N_PERMUTATIONS)) for s in range(0, N_PERMUTATIONS, CHUNK)]
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        placebos = [p for part in pool.map(placebo_g_hats, *zip(*chunks)) for p in part]
    records += placebo_records(observed, placebos)

    for r in rolling_shares(evals):
        records.append(_row(row_type="rolling", series=r["series"], method=r["method"], season=r["season"],
                            n_windows=r["n_windows"], share_positive=r["share_positive"], window_min=r["min"],
                            window_max=r["max"]))
    for r in band_rows(evals):
        records.append(_row(row_type="band", series=r["series"], method=r["method"], band=r["band"], n=r["n"],
                            g_hat=r["g_hat"]))
    for r in acf_rows(evals):
        records.append(_row(row_type="acf", series=r["series"], method=r["method"], lag=r["lag"],
                            acf_mean_over_seasons=r["acf_mean_over_seasons"], acf_min_season=r["acf_min_season"],
                            acf_max_season=r["acf_max_season"], acf_concatenated=r["acf_concatenated"]))
    records += coverage_records(seq_cov)

    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(G_HAT_INFERENCE_COLUMNS))
        writer.writeheader()
        writer.writerows(records)
    make_figure(pd.DataFrame(records), png_path)


def make_figure(df: pd.DataFrame, png_path: Path) -> None:
    """Tre pannelli: intervalli per stagione (B365, Shin), placebo contro valore atteso, coperture AR(1)."""
    fig, (ax_a, ax_b, ax_c) = plt.subplots(1, 3, figsize=(22, 6.5))

    iv = df[(df["row_type"] == "interval") & (df["series"] == "b365_prematch") & (df["method"] == "shin")]
    x = np.arange(len(iv))
    g = iv["g_hat"].astype(float).to_numpy()
    for off, lo, hi, color, label in ((-0.15, "ci_block_low", "ci_block_high", "tab:blue", "stationary a L_PW"),
                                      (0.15, "ci_iid_low", "ci_iid_high", "tab:orange", "iid")):
        l, h = iv[lo].astype(float).to_numpy(), iv[hi].astype(float).to_numpy()
        ax_a.errorbar(x + off, g, yerr=[np.maximum(g - l, 0), np.maximum(h - g, 0)], fmt="o", color=color,
                      capsize=2, markersize=3, label=label)
    ax_a.axhline(0.0, color="black", linewidth=0.8)
    ax_a.set_xticks(x)
    ax_a.set_xticklabels(iv["season"], rotation=75, fontsize=8)
    ax_a.set_ylabel("ĝ con intervallo al 95%")
    ax_a.set_title("A) ĝ per stagione, B365 pre-partita, Shin", loc="left", fontsize=11, fontweight="bold")
    ax_a.legend(fontsize=9)
    ax_a.grid(True, linestyle=":", alpha=0.6)

    pl = df[(df["row_type"] == "placebo") & (df["series"] == "b365_prematch") & (df["method"] == "shin")
            & (df["season"] != "pooled")]
    x = np.arange(len(pl))
    m = pl["placebo_mean"].astype(float).to_numpy()
    ax_b.errorbar(x, m, yerr=[m - pl["placebo_q025"].astype(float), pl["placebo_q975"].astype(float) - m], fmt="o",
                  color="tab:purple", capsize=2, markersize=3, label="ĝ placebo (media, 2.5–97.5%)")
    ax_b.scatter(x, pl["expected_mean"].astype(float), marker="_", s=120, color="black", label="valore atteso esatto")
    ax_b.scatter(x, pl["g_hat"].astype(float), marker="x", color="tab:blue", label="ĝ osservato")
    ax_b.axhline(0.0, color="black", linewidth=0.8)
    ax_b.set_xticks(x)
    ax_b.set_xticklabels(pl["season"], rotation=75, fontsize=8)
    ax_b.set_title("B) Placebo: esiti permutati dentro la stagione", loc="left", fontsize=11, fontweight="bold")
    ax_b.legend(fontsize=8)
    ax_b.grid(True, linestyle=":", alpha=0.6)

    cov = df[df["row_type"] == "coverage"]
    phi = cov["phi"].astype(float).to_numpy()
    ax_c.plot(phi, cov["coverage_stationary"].astype(float), "o-", label="stationary a L_PW")
    ax_c.plot(phi, cov["coverage_iid"].astype(float), "s-", label="iid")
    ax_c.axhspan(0.93, 0.97, color="gray", alpha=0.2, label="[0.93, 0.97]")
    ax_c.axhline(0.95, color="black", linewidth=0.8)
    ax_c.set_xlabel("φ dell'AR(1), n = 380")
    ax_c.set_ylabel("Copertura al 95% della media")
    ax_c.set_title("C) Copertura su AR(1), 1 000 serie", loc="left", fontsize=11, fontweight="bold")
    ax_c.legend(fontsize=9)
    ax_c.grid(True, linestyle=":", alpha=0.6)

    fig.tight_layout()
    fig.savefig(png_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    run_experiment()
