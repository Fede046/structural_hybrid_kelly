"""Script per gli esperimenti US-C2.2 e US-C2.3: tasso di falso rigetto dell'ANOVA su serie AR(1).

Questo script misura, per phi in {0.0, 0.3, 0.5, 0.7} e per tre disegni sperimentali
(contiguous_2, contiguous_38, random_2), la quota di serie AR(1) senza alcun effetto
di gruppo su cui la statistica F rigetta al livello nominale alpha = 0.05 (US-C2.2).
Inoltre, per il disegno contiguous_2 e per lunghezze di blocco L in {7, 20, 40},
misura il tasso di falso rigetto impiegando la soglia calibrata per moving block bootstrap (US-C2.3),
in due varianti: sulla serie grezza, senza imporre H0 (T12), e sulla serie centrata per
gruppo, con H0 imposta (T40).
I risultati vengono esportati in results/us_c2_anova_autocorrelation.csv (36 righe: 12 nominali,
12 calibrate sulla serie grezza, 12 calibrate sulla serie centrata) e visualizzati nei tre
pannelli di thesis/figures/us_c2_anova_autocorrelation.png.
"""

import os
from pathlib import Path
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from shk.stats.false_rejection import (
    ALPHA,
    BLOCK_LENGTHS,
    CSV_COLUMNS,
    DESIGNS,
    DESIGN_CONTIGUOUS_2,
    DESIGN_CONTIGUOUS_38,
    DESIGN_RANDOM_2,
    PHI_VALUES,
    RejectionResult,
    compute_calibrated_rejection_rates,
    compute_centered_calibrated_rejection_rates,
    compute_nominal_rejection_rates,
)

# Percorsi dalla posizione dello script, non dalla directory corrente (T64)
REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "results" / "us_c2_anova_autocorrelation.csv"
PNG_PATH = REPO_ROOT / "thesis" / "figures" / "us_c2_anova_autocorrelation.png"


def run_experiment() -> None:
    """Esegue la simulazione degli esperimenti US-C2.2 e US-C2.3 e produce CSV e figura."""
    nominal_results = compute_nominal_rejection_rates()
    calibrated_results = compute_calibrated_rejection_rates()
    centered_results = compute_centered_calibrated_rejection_rates()
    all_results = nominal_results + calibrated_results + centered_results

    # 1. Scrittura del file CSV (36 righe: 12 nominali + 12 calibrate + 12 calibrate centrate)
    os.makedirs(CSV_PATH.parent, exist_ok=True)
    csv_path = CSV_PATH
    with open(csv_path, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=list(CSV_COLUMNS))
        writer.writeheader()
        for r in all_results:
            writer.writerow(r.to_row())

    # 2. Costruzione della figura a tre pannelli
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(20, 6), sharey=True)

    # Dati nominali raggruppati per disegno
    data_by_design: dict[str, list[RejectionResult]] = {d: [] for d in DESIGNS}
    for r in nominal_results:
        data_by_design[r.design].append(r)

    # Intervallo Monte Carlo al 99% attorno ad ALPHA
    mc_lower = nominal_results[0].mc_lower_99
    mc_upper = nominal_results[0].mc_upper_99

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

    # Pannello B: Tasso di falso rigetto calibrato (moving block bootstrap) vs phi
    ax2.plot(
        PHI_VALUES,
        rates_cont2,
        "o-",
        linewidth=1.8,
        markersize=6,
        label=r"Nominale ($k=2$)",
        color="tab:red",
    )

    styles = {
        7: ("s--", "tab:green"),
        20: ("^--", "tab:purple"),
        40: ("d-.", "tab:brown"),
    }
    for l_val in BLOCK_LENGTHS:
        rates_l = [
            r.rejection_rate
            for r in calibrated_results
            if r.block_length == str(l_val)
        ]
        fmt, col = styles.get(l_val, ("o-", "tab:blue"))
        ax2.plot(
            PHI_VALUES,
            rates_l,
            fmt,
            linewidth=1.5,
            markersize=5,
            label=rf"Bootstrap ($L={l_val}$)",
            color=col,
        )

    ax2.axhline(
        ALPHA,
        color="black",
        linestyle="--",
        linewidth=1.0,
        label=rf"Livello nominale $\alpha = {ALPHA:.2f}$",
    )
    ax2.axhspan(
        mc_lower,
        mc_upper,
        color="gray",
        alpha=0.2,
        label=r"Intervallo 99% MC attorno ad $\alpha$",
    )

    ax2.set_xlabel(r"Coefficiente autoregressivo $\phi$")
    ax2.set_ylabel("Tasso di falso rigetto")
    ax2.set_title(
        "B) Calibrato sulla serie grezza (H$_0$ non imposta)",
        loc="left",
        fontsize=11,
        fontweight="bold",
    )
    ax2.set_xticks(list(PHI_VALUES))
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="upper left", fontsize=9)

    # Pannello C: Tasso di falso rigetto calibrato sulla serie centrata per gruppo vs phi
    ax3.plot(
        PHI_VALUES,
        rates_cont2,
        "o-",
        linewidth=1.8,
        markersize=6,
        label=r"Nominale ($k=2$)",
        color="tab:red",
    )
    for l_val in BLOCK_LENGTHS:
        rates_l = [
            r.rejection_rate
            for r in centered_results
            if r.block_length == str(l_val)
        ]
        fmt, col = styles.get(l_val, ("o-", "tab:blue"))
        ax3.plot(
            PHI_VALUES,
            rates_l,
            fmt,
            linewidth=1.5,
            markersize=5,
            label=rf"Bootstrap centrato ($L={l_val}$)",
            color=col,
        )

    ax3.axhline(
        ALPHA,
        color="black",
        linestyle="--",
        linewidth=1.0,
        label=rf"Livello nominale $\alpha = {ALPHA:.2f}$",
    )
    ax3.axhspan(
        mc_lower,
        mc_upper,
        color="gray",
        alpha=0.2,
        label=r"Intervallo 99% MC attorno ad $\alpha$",
    )

    ax3.set_xlabel(r"Coefficiente autoregressivo $\phi$")
    ax3.set_title(
        "C) Calibrato con H$_0$ imposta (serie centrata per gruppo)",
        loc="left",
        fontsize=11,
        fontweight="bold",
    )
    ax3.set_xticks(list(PHI_VALUES))
    ax3.grid(True, linestyle=":", alpha=0.6)
    ax3.legend(loc="upper left", fontsize=9)

    plt.tight_layout()
    os.makedirs(PNG_PATH.parent, exist_ok=True)
    fig_path = PNG_PATH
    plt.savefig(fig_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    run_experiment()
