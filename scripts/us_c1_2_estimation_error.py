"""Script per l'esperimento US-C1.2: stima della probabilità e asimmetria di Kelly.

Questo script conduce simulazioni Monte Carlo su scommesse ripetute per analizzare
l'impatto dell'errore di stima della probabilità (sia deterministico che stocastico)
sulla crescita del capitale, e confronta la regola di ridimensionamento lambda* con
il quarto-Kelly e altre euristiche di frazionamento.
I risultati vengono esportati in formato CSV e visualizzati in una figura a due pannelli.
"""

import os
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from shk.kelly.core import kelly_fraction, log_growth_rate
from shk.kelly.estimation import relative_perturbation, noisy_estimates
from shk.kelly.simulate import simulate_growth
from shk.kelly.staking import kelly_staking, staking_moments, plugin_staking
from shk.kelly.metrics import median_growth_rate, max_drawdown, fraction_below_start
from shk.kelly.scenarios import (
    BASE_SCENARIO,
    SUBTLE_SCENARIO,
    SEED,
    spawn_generators,
    draw_scenario_outcomes,
    simulate_scenario,
)


def run_experiment() -> None:
    """Esegue la simulazione dell'esperimento US-C1.2 e produce CSV e grafici."""
    scenarios = [BASE_SCENARIO, SUBTLE_SCENARIO]
    sigmas = [0.015, 0.0283, 0.045]

    records = []

    # 1. Rilevazioni del Task 4: errore relativo deterministico (+10% e -10%)
    for sc in scenarios:
        rng_outcomes, _ = spawn_generators(SEED)
        outcomes = draw_scenario_outcomes(sc, rng_outcomes)

        # Sovrastima +10%
        p_over = relative_perturbation(sc.p, 0.10)
        paths_over = simulate_scenario(sc, outcomes, p_hat=p_over, lam=1.0)
        g_over = median_growth_rate(paths_over)
        dd_over = float(np.median(max_drawdown(paths_over)))
        fb_over = fraction_below_start(paths_over)
        del paths_over

        records.append({
            "scenario": sc.name,
            "sigma_p": "",
            "rule": "overestimation_10pct",
            "lambda": 1.0,
            "mean_c": "",
            "mean_c2": "",
            "var_c_empirical": "",
            "var_c_linear": "",
            "fraction_f_hat_zero": "",
            "median_growth_rate": g_over,
            "median_drawdown": dd_over,
            "fraction_below_start": fb_over,
        })

        # Sottostima -10%
        p_under = relative_perturbation(sc.p, -0.10)
        paths_under = simulate_scenario(sc, outcomes, p_hat=p_under, lam=1.0)
        g_under = median_growth_rate(paths_under)
        dd_under = float(np.median(max_drawdown(paths_under)))
        fb_under = fraction_below_start(paths_under)
        del paths_under

        records.append({
            "scenario": sc.name,
            "sigma_p": "",
            "rule": "underestimation_10pct",
            "lambda": 1.0,
            "mean_c": "",
            "mean_c2": "",
            "var_c_empirical": "",
            "var_c_linear": "",
            "fraction_f_hat_zero": "",
            "median_growth_rate": g_under,
            "median_drawdown": dd_under,
            "fraction_below_start": fb_under,
        })

    # 2. Rilevazioni dei Task 5 e 6: rumore stocastico per scommessa e confronto regole
    # Salviamo i risultati simulati a sigma_p = 0.0283 per i marcatori del Pannello B
    markers_data = {}

    for sc in scenarios:
        f_star = kelly_fraction(sc.p, sc.b)
        o = sc.b + 1.0
        ev = sc.p * o - 1.0

        for s in sigmas:
            rng_outcomes, rng_noise = spawn_generators(SEED)
            outcomes = draw_scenario_outcomes(sc, rng_outcomes)
            p_hat = noisy_estimates(sc.p, s, sc.T, sc.M, rng_noise)

            f_hat = kelly_staking(p_hat, sc.b, lam=1.0)
            m = staking_moments(f_hat, f_star)
            var_lin = ((o * s) / ev) ** 2

            lam_star = 1.0 / (1.0 + m.var_c)
            lam_ratio = m.mean_c / m.mean_c2
            lam_lin = 1.0 / (1.0 + var_lin)

            rules_def = [
                ("lambda_star", lam_star, simulate_scenario(sc, outcomes, p_hat, lam=lam_star)),
                ("ratio_moments", lam_ratio, simulate_scenario(sc, outcomes, p_hat, lam=lam_ratio)),
                ("lambda_linear", lam_lin, simulate_scenario(sc, outcomes, p_hat, lam=lam_lin)),
                ("quarter_kelly", 0.25, simulate_scenario(sc, outcomes, p_hat, lam=0.25)),
                ("half_kelly", 0.50, simulate_scenario(sc, outcomes, p_hat, lam=0.50)),
                ("full_kelly", 1.00, simulate_scenario(sc, outcomes, p_hat, lam=1.00)),
                ("plugin", "", simulate_growth(outcomes, plugin_staking(p_hat, sc.b, s), sc.b)),
            ]

            for r_name, r_lam, paths in rules_def:
                g_med = median_growth_rate(paths)
                dd_med = float(np.median(max_drawdown(paths)))
                fb = fraction_below_start(paths)
                del paths

                if abs(s - 0.0283) < 1e-6 and r_name in ("lambda_star", "quarter_kelly"):
                    markers_data[(sc.name, r_name)] = (r_lam, g_med)

                records.append({
                    "scenario": sc.name,
                    "sigma_p": float(s),
                    "rule": r_name,
                    "lambda": r_lam,
                    "mean_c": m.mean_c,
                    "mean_c2": m.mean_c2,
                    "var_c_empirical": m.var_c,
                    "var_c_linear": var_lin,
                    "fraction_f_hat_zero": m.fraction_zero,
                    "median_growth_rate": g_med,
                    "median_drawdown": dd_med,
                    "fraction_below_start": fb,
                })

    # Scrittura del file CSV
    os.makedirs("results", exist_ok=True)
    csv_path = os.path.join("results", "us_c1_2_estimation_error.csv")
    fieldnames = [
        "scenario",
        "sigma_p",
        "rule",
        "lambda",
        "mean_c",
        "mean_c2",
        "var_c_empirical",
        "var_c_linear",
        "fraction_f_hat_zero",
        "median_growth_rate",
        "median_drawdown",
        "fraction_below_start",
    ]
    with open(csv_path, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in records:
            writer.writerow(row)

    # 3. Costruzione della figura a due pannelli
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Pannello A: Crescita mediana normalizzata vs errore relativo deterministico
    deltas = np.linspace(-0.20, 0.20, 41)
    deltas_pct = deltas * 100

    colors = {"base": "tab:blue", "subtle": "tab:orange"}

    for sc in scenarios:
        rng_outcomes, _ = spawn_generators(SEED)
        outcomes = draw_scenario_outcomes(sc, rng_outcomes)
        f_star = kelly_fraction(sc.p, sc.b)
        g_star = log_growth_rate(f_star, sc.p, sc.b)

        g_normalized = []
        for d in deltas:
            p_perturbed = relative_perturbation(sc.p, float(d))
            paths = simulate_scenario(sc, outcomes, p_hat=p_perturbed, lam=1.0)
            g_m = median_growth_rate(paths)
            del paths
            g_normalized.append(g_m / g_star)

        ax1.plot(
            deltas_pct,
            g_normalized,
            "o-",
            markersize=3,
            linewidth=1.5,
            label=f"Scenario {sc.name.capitalize()} ($p={sc.p:.2f}$)",
            color=colors[sc.name],
        )

    ax1.axhline(0.0, color="gray", linestyle="--", linewidth=0.8, alpha=0.7)
    ax1.axhline(1.0, color="black", linestyle=":", linewidth=0.8, alpha=0.5, label=r"Crescita ottima teorica ($g^*$)")
    ax1.axvline(0.0, color="gray", linestyle=":", linewidth=0.8, alpha=0.7)
    ax1.set_xlabel(r"Errore relativo di stima $\delta = (\hat{p} - p) / p$ (%)")
    ax1.set_ylabel(r"Crescita mediana normalizzata ($g_{\mathrm{med}} / g^*$)")
    ax1.set_title("A) Asimmetria stima deterministica", loc="left", fontsize=11, fontweight="bold")
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="best", fontsize=9)

    # Pannello B: Crescita mediana normalizzata vs lambda con sigma_p = 0.0283
    # Griglia da 0.0 a 1.5 compresi con passo 0.025 (61 punti)
    lambdas_grid = np.linspace(0.0, 1.5, 61)
    sigma_p_fixed = 0.0283

    for sc in scenarios:
        rng_outcomes, rng_noise = spawn_generators(SEED)
        outcomes = draw_scenario_outcomes(sc, rng_outcomes)
        p_hat = noisy_estimates(sc.p, sigma_p_fixed, sc.T, sc.M, rng_noise)
        f_star = kelly_fraction(sc.p, sc.b)
        g_star = log_growth_rate(f_star, sc.p, sc.b)

        g_grid_norm = []
        for lam_val in lambdas_grid:
            paths = simulate_scenario(sc, outcomes, p_hat, lam=float(lam_val))
            g_m = median_growth_rate(paths)
            del paths
            g_grid_norm.append(g_m / g_star)

        ax2.plot(
            lambdas_grid,
            g_grid_norm,
            "-",
            linewidth=1.5,
            label=f"Scenario {sc.name.capitalize()} ($p={sc.p:.2f}$)",
            color=colors[sc.name],
        )

        # Marcatori posti sui valori effettivamente simulati (gli stessi del CSV, Correzione B)
        lam_star_val, g_star_sim = markers_data[(sc.name, "lambda_star")]
        quarter_lam_val, g_quarter_sim = markers_data[(sc.name, "quarter_kelly")]

        ax2.scatter(
            [lam_star_val],
            [g_star_sim / g_star],
            marker="*",
            s=130,
            color=colors[sc.name],
            edgecolors="black",
            zorder=5,
            label=f"$\\lambda^*$ {sc.name.capitalize()} ({lam_star_val:.3f})",
        )
        ax2.scatter(
            [quarter_lam_val],
            [g_quarter_sim / g_star],
            marker="s",
            s=50,
            color=colors[sc.name],
            edgecolors="black",
            zorder=5,
            label=f"Quarto-Kelly {sc.name.capitalize()} (0.25)",
        )

    ax2.axhline(0.0, color="gray", linestyle="--", linewidth=0.8, alpha=0.7)
    ax2.set_xlabel(r"Moltiplicatore di frazione $\lambda$ ($f = \lambda \cdot \hat{f}$)")
    ax2.set_ylabel(r"Crescita mediana normalizzata ($g_{\mathrm{med}} / g^*$)")
    ax2.set_title(r"B) Crescita vs $\lambda$ con rumore ($\sigma_p = 0.0283$)", loc="left", fontsize=11, fontweight="bold")
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="best", fontsize=8)

    plt.tight_layout()
    os.makedirs(os.path.join("thesis", "figures"), exist_ok=True)
    fig_path = os.path.join("thesis", "figures", "us_c1_2_estimation_error.png")
    plt.savefig(fig_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    run_experiment()
