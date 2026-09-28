"""Script per l'esperimento US-C2.2: tasso di falso rigetto dell'ANOVA su serie AR(1).

Questo script misura, per phi in {0.0, 0.3, 0.5, 0.7} e per tre disegni sperimentali
(contiguous_2, contiguous_38, random_2), la quota di serie AR(1) senza alcun effetto
di gruppo su cui la statistica F rigetta al livello nominale alpha = 0.05.
I risultati vengono esportati in results/us_c2_anova_autocorrelation.csv e
visualizzati in thesis/figures/us_c2_anova_autocorrelation.png.
"""

import os
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from shk.stats.false_rejection import (
    ALPHA,
    CSV_COLUMNS,
    DESIGNS,
    DESIGN_CONTIGUOUS_2,
    DESIGN_CONTIGUOUS_38,
    DESIGN_RANDOM_2,
    PHI_VALUES,
    RejectionResult,
    compute_nominal_rejection_rates,
)


def run_experiment() -> None:
    """Esegue la simulazione dell'esperimento US-C2.2 e produce CSV e figura."""
    results = compute_nominal_rejection_rates()

    # 1. Scrittura del file CSV
    os.makedirs("results", exist_ok=True)
    csv_path = os.path.join("results", "us_c2_anova_autocorrelation.csv")
    with open(csv_path, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=list(CSV_COLUMNS))
        writer.writeheader()
        for r in results:
            writer.writerow(r.to_row())

    # 2. Costruzione della figura a due pannelli
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Dati raggruppati per disegno
    data_by_design: dict[str, list[RejectionResult]] = {d: [] for d in DESIGNS}
    for r in results:
        data_by_design[r.design].append(r)

    # Intervallo Monte Carlo al 99% attorno ad ALPHA
    mc_lower = results[0].mc_lower_99
    mc_upper = results[0].mc_upper_99

    # Pannello A: Tasso di falso rigetto nominale vs phi
    rates_cont2 = [r.rejection_rate for r in data_by_design[DESIGN_CONTIGUOUS_2]]
    rates_cont38 = [r.rejection_rate for r in data_by_design[DESIGN_CONTIGUOUS_38]]
    rates_rand2 = [r.rejection_rate for r in data_by_design[DESIGN_RANDOM_2]]

    ax1.plot(
        PHI_VALUES,
        rates_cont2,
        "o-",
        linewidth=1.8,
        markersize=6,
        label=r"Due metà contigue ($k=2$, $n=190$)",
        color="tab:red",
    )
    ax1.plot(
        PHI_VALUES,
        rates_cont38,
        "s--",
        linewidth=1.5,
        markersize=5,
        label=r"38 blocchi contigui ($k=38$, $n=10$)",
        color="tab:orange",
    )
    ax1.plot(
        PHI_VALUES,
        rates_rand2,
        "^:",
        linewidth=1.5,
        markersize=5,
        label=r"Assegnazione casuale ($k=2$, controllo)",
        color="tab:blue",
    )

    ax1.axhline(
        ALPHA,
        color="black",
        linestyle="--",
        linewidth=1.0,
        label=rf"Livello nominale $\alpha = {ALPHA:.2f}$",
    )
    ax1.axhspan(
        mc_lower,
        mc_upper,
        color="gray",
        alpha=0.2,
        label=r"Intervallo 99% MC attorno ad $\alpha$",
    )

    ax1.set_xlabel(r"Coefficiente autoregressivo $\phi$")
    ax1.set_ylabel("Tasso di falso rigetto")
    ax1.set_title(
        "A) Tasso di falso rigetto nominale (ANOVA)",
        loc="left",
        fontsize=11,
        fontweight="bold",
    )
    ax1.set_xticks(list(PHI_VALUES))
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="upper left", fontsize=9)

    # Pannello B: Riservato per Task 12 (nascosto)
    ax2.set_visible(False)

    plt.tight_layout()
    os.makedirs(os.path.join("thesis", "figures"), exist_ok=True)
    fig_path = os.path.join("thesis", "figures", "us_c2_anova_autocorrelation.png")
    plt.savefig(fig_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    run_experiment()
