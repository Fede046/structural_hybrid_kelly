"""Script per l'esperimento US-C1.1: trade-off crescita/varianza e frazionamento di Kelly.

Questo script conduce una simulazione Monte Carlo su scommesse binarie ripetute per
studiare l'impatto del moltiplicatore lambda (f = lambda * f_star) sulla crescita del
bankroll, sul drawdown massimo e sul trade-off crescita/varianza.
I risultati vengono esportati in formato CSV e visualizzati in un grafico a tre pannelli.
"""

import os
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from shk.kelly.core import kelly_fraction, log_growth_rate, expected_final_wealth
from shk.kelly.simulate import draw_outcomes, log_wealth_paths
from shk.kelly.metrics import (
    median_growth_rate,
    median_final_wealth,
    mean_final_wealth,
    max_drawdown,
    fraction_below_start,
)


def run_experiment() -> None:
    """Esegue la simulazione dell'esperimento US-C1.1 e genera report e grafici."""
    # Parametri dell'esperimento
    p: float = 0.60
    b: float = 1.0
    b0: float = 1.0
    t_steps: int = 1000
    m_trajectories: int = 10000
    seed: int = 20260905

    # Calcolo della frazione ottimale teorica f*
    f_star: float = kelly_fraction(p, b)

    # Griglia di lambda: da 0.0 a 2.5 con passo 0.05 (51 punti)
    lambdas: np.ndarray = np.linspace(0.0, 2.5, 51)

    # Generazione di una singola matrice di esiti bernoulliani condivisa per il confronto appaiato
    rng: np.random.Generator = np.random.default_rng(seed)
    outcomes: np.ndarray = draw_outcomes(p, t_steps, m_trajectories, rng)

    records = []

    # Iterazione sulla griglia dei moltiplicatori lambda
    for lam in lambdas:
        f_val: float = float(lam * f_star)

        # Generazione delle traiettorie di log-wealth
        paths: np.ndarray = log_wealth_paths(outcomes, f_val, b)

        # Calcolo delle metriche empiriche
        med_growth: float = median_growth_rate(paths)
        med_final: float = median_final_wealth(paths)
        mean_final_mc: float = mean_final_wealth(paths)
        dd_vector: np.ndarray = max_drawdown(paths)
        dd_med: float = float(np.median(dd_vector))
        dd_p95: float = float(np.percentile(dd_vector, 95))
        frac_below: float = fraction_below_start(paths)

        # Rilascio immediato della memoria per evitare accumulo di matrici (~80 MB ciascuna)
        del paths

        # Calcolo dei valori analitici teorici (uso su scalari per log_growth_rate)
        analytic_growth: float = log_growth_rate(f_val, p, b)
        mean_final_analytic: float = expected_final_wealth(f_val, p, b, t_steps, b0)

        records.append({
            "lambda": float(lam),
            "f": f_val,
            "median_growth_rate": med_growth,
            "analytic_growth_rate": analytic_growth,
            "median_final_wealth": med_final,
            "mean_final_wealth_mc": mean_final_mc,
            "mean_final_wealth_analytic": mean_final_analytic,
            "drawdown_median": dd_med,
            "drawdown_p95": dd_p95,
            "fraction_below_start": frac_below,
        })

    # Scrittura dei risultati nel file CSV
    os.makedirs("results", exist_ok=True)
    csv_path = os.path.join("results", "us_c1_1_growth_vs_lambda.csv")
    fieldnames = [
        "lambda",
        "f",
        "median_growth_rate",
        "analytic_growth_rate",
        "median_final_wealth",
        "mean_final_wealth_mc",
        "mean_final_wealth_analytic",
        "drawdown_median",
        "drawdown_p95",
        "fraction_below_start",
    ]
    with open(csv_path, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in records:
            writer.writerow(row)

    # Estrazione vettori per la generazione del grafico
    lam_vals = [r["lambda"] for r in records]
    med_growths = [r["median_growth_rate"] for r in records]
    an_growths = [r["analytic_growth_rate"] for r in records]
    med_wealths = [r["median_final_wealth"] for r in records]
    mc_wealths = [r["mean_final_wealth_mc"] for r in records]
    an_wealths = [r["mean_final_wealth_analytic"] for r in records]
    dd_meds = [r["drawdown_median"] for r in records]
    dd_p95s = [r["drawdown_p95"] for r in records]

    # Configurazione della figura a tre pannelli verticali
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12), sharex=True)

    # Pannello A: Tasso di crescita mediano vs teorico
    ax1.plot(lam_vals, med_growths, "o", markersize=4, label="Stima Monte Carlo", alpha=0.8)
    ax1.plot(lam_vals, an_growths, "-", linewidth=1.5, label="Tasso analitico $g(f)$", color="tab:blue")
    ax1.axhline(0.0, color="gray", linestyle="--", linewidth=0.8, alpha=0.7)
    ax1.axvline(1.0, color="red", linestyle=":", linewidth=1.2, label=r"Kelly ottimale ($\lambda = 1$)")
    ax1.axvline(1.946, color="darkorange", linestyle=":", linewidth=1.2, label=r"Crescita nulla ($\lambda = 1.946$)")
    ax1.set_ylabel("Crescita mediana per scommessa")
    ax1.set_title("A) Tasso di crescita logaritmico al variare di $\lambda$", loc="left", fontsize=11, fontweight="bold")
    ax1.legend(loc="best", fontsize=9)
    ax1.grid(True, linestyle=":", alpha=0.6)

    # Pannello B: Capitale finale (media MC, media analitica, mediana) su scala logaritmica
    ax2.plot(lam_vals, mc_wealths, "s", markersize=4, label="Media aritmetica Monte Carlo", color="tab:green", alpha=0.8)
    ax2.plot(lam_vals, an_wealths, "-", linewidth=1.5, label="Media aritmetica analitica $E[B_T]$", color="tab:green")
    ax2.plot(lam_vals, med_wealths, "^-", markersize=4, linewidth=1.2, label="Mediana di $B_T$", color="tab:purple")
    ax2.axvline(1.0, color="red", linestyle=":", linewidth=1.2, alpha=0.7)
    ax2.axvline(1.946, color="darkorange", linestyle=":", linewidth=1.2, alpha=0.7)
    ax2.set_yscale("log")
    ax2.set_ylabel(r"Capitale finale $B_T$ (scala log)")
    ax2.set_title(r"B) Media aritmetica e mediana del capitale finale $B_T$", loc="left", fontsize=11, fontweight="bold")
    ax2.legend(loc="best", fontsize=9)
    ax2.grid(True, which="both", linestyle=":", alpha=0.6)

    # Pannello C: Drawdown massimo relativo (mediana e p95)
    ax3.plot(lam_vals, dd_meds, "o-", markersize=4, linewidth=1.2, label="Mediana del drawdown massimo", color="tab:red")
    ax3.plot(lam_vals, dd_p95s, "s--", markersize=4, linewidth=1.2, label="95° percentile (p95)", color="tab:brown")
    ax3.axvline(1.0, color="red", linestyle=":", linewidth=1.2, alpha=0.7)
    ax3.axvline(1.946, color="darkorange", linestyle=":", linewidth=1.2, alpha=0.7)
    ax3.set_xlabel(r"Fattore di scala $\lambda$ ($f = \lambda \cdot f^*$)")
    ax3.set_ylabel("Drawdown massimo relativo")
    ax3.set_title("C) Rischio di drawdown massimo", loc="left", fontsize=11, fontweight="bold")
    ax3.legend(loc="best", fontsize=9)
    ax3.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()
    os.makedirs(os.path.join("thesis", "figures"), exist_ok=True)
    fig_path = os.path.join("thesis", "figures", "us_c1_1_growth_vs_lambda.png")
    plt.savefig(fig_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    run_experiment()

