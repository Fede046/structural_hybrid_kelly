"""Script per l'esecuzione del backtest Monte Carlo del floor reale (US-C6.3 / Task 37).

Esegue gli agenti A, B_0.25, B_0.10 ed E sul calendario e quote reali con esiti estratti
dalle probabilita' proporzionali di mercato (verita'). Produce il CSV dei risultati
e la figura a 3 pannelli in italiano. Nessun print: misurazione del tempo dall'esterno.
"""

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from shk.data.split import load_by_role, read_split_config
from shk.kelly.floor import SEED_C6
from shk.model.elo_fit import ELO_FITS, derive_fit_schedule
from shk.model.floor_real_config import (
    FLOOR_REAL_CSV_COLUMNS,
    evaluate_floor_real_config,
)
from shk.model.paired_backtest import CONFIGURATIONS, build_season_agents
from shk.model.residuals import compute_model_residuals


def _plot_three_panels(
    df_records: pd.DataFrame,
    group_artifacts: dict,
    fig_path: Path,
) -> None:
    """Costruisce e salva la figura a 3 pannelli in italiano.

    Pannello A: Tasso di rovina aggregato con intervallo al 99%
    Pannello B: Distribuzione di ln W_T aggregata (repliche con W_T > 0, zeri indicati)
    Pannello C: P(min W <= theta) per theta = 0.5 e 0.1
    """
    df_agg = df_records[df_records["row_type"] == "aggregate"].copy()

    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig, axes = plt.subplots(1, 3, figsize=(20, 6.2))

    config_colors = {
        "none": "#1f77b4",
        "gbp_0.01": "#2ca02c",
        "gbp_1": "#d62728",
    }
    config_labels = {
        "none": "Nessun floor (F = 0)",
        "gbp_0.01": "Floor £0.01 (F = 0.01/220)",
        "gbp_1": "Floor £1.00 (F = 1/220)",
    }
    agents_order = ["A", "B_0.25", "B_0.10", "E"]

    # -------------------------------------------------------------------------
    # Pannello A: Tasso di rovina aggregato
    # -------------------------------------------------------------------------
    ax_a = axes[0]
    x_positions = np.arange(len(agents_order))
    bar_width = 0.25

    for c_idx, (cfg_name, _) in enumerate(CONFIGURATIONS):
        offsets = x_positions + (c_idx - 1) * bar_width
        heights = []
        err_lower = []
        err_upper = []

        for ag in agents_order:
            sub = df_agg[(df_agg["config"] == cfg_name) & (df_agg["agent"] == ag)]
            if len(sub) == 0:
                heights.append(0.0)
                err_lower.append(0.0)
                err_upper.append(0.0)
            else:
                r_val = float(sub["ruin_rate"].iloc[0])
                ci_l = float(sub["ruin_rate_ci_lower"].iloc[0])
                ci_u = float(sub["ruin_rate_ci_upper"].iloc[0])
                heights.append(r_val)
                err_lower.append(max(0.0, r_val - ci_l))
                err_upper.append(max(0.0, ci_u - r_val))

        yerr = [err_lower, err_upper]
        ax_a.bar(
            offsets,
            heights,
            width=bar_width,
            yerr=yerr,
            capsize=4,
            label=config_labels[cfg_name],
            color=config_colors[cfg_name],
            alpha=0.85,
            edgecolor="black",
            linewidth=0.8,
        )

    ax_a.set_xticks(x_positions)
    ax_a.set_xticklabels(agents_order, fontsize=11, fontweight="bold")
    ax_a.set_ylabel("Tasso di rovina empirico", fontsize=11)
    ax_a.set_title("(A) Tasso di rovina aggregato (IC 99%)", fontsize=12, fontweight="bold")
    ax_a.legend(loc="upper left", fontsize=9)
    ax_a.set_ylim(-0.02, 1.05)

    # -------------------------------------------------------------------------
    # Pannello B: Distribuzione di ln W_T aggregata (W_T > 0, conteggio zeri)
    # -------------------------------------------------------------------------
    ax_b = axes[1]
    box_data = []
    box_labels = []
    box_colors = []

    for ag in agents_order:
        for cfg_name, min_s in CONFIGURATIONS:
            if cfg_name == "none" and ag == "E":
                continue
            arts = group_artifacts.get((cfg_name, ag), [])
            if not arts:
                continue
            all_w = np.concatenate([a.final_wealth for a in arts])
            n_zeros = int(np.sum(all_w <= 0.0))
            valid_w = all_w[all_w > 0.0]
            log_w = np.log(valid_w) if len(valid_w) > 0 else np.array([0.0])

            box_data.append(log_w)
            cfg_short = "none" if cfg_name == "none" else ("0.01" if cfg_name == "gbp_0.01" else "1.00")
            box_labels.append(f"{ag}\n{cfg_short}")
            box_colors.append(config_colors[cfg_name])

    positions_b = np.arange(len(box_data))
    bp = ax_b.boxplot(
        box_data,
        positions=positions_b,
        patch_artist=True,
        showmeans=True,
        meanline=True,
        widths=0.6,
        medianprops={"color": "black", "linewidth": 1.5},
        meanprops={"color": "gold", "linewidth": 1.5, "linestyle": "--"},
        flierprops={"marker": ".", "markersize": 2, "alpha": 0.3},
    )

    for patch, color in zip(bp["boxes"], box_colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.65)

    ax_b.axhline(0.0, color="gray", linestyle=":", linewidth=1)
    ax_b.set_xticks(positions_b)
    ax_b.set_xticklabels(box_labels, fontsize=8)
    ax_b.set_ylabel(r"$\ln W_T$ (su repliche con $W_T > 0$)", fontsize=11)
    ax_b.set_title(r"(B) Distribuzione di $\ln W_T$ aggregata", fontsize=12, fontweight="bold")

    # Legenda con il conteggio delle repliche con W_T = 0 per agente e configurazione
    import matplotlib.patches as mpatches
    legend_handles = []
    for ag in agents_order:
        for cfg_name, _ in CONFIGURATIONS:
            if cfg_name == "none" and ag == "E":
                continue
            arts = group_artifacts.get((cfg_name, ag), [])
            all_w = np.concatenate([a.final_wealth for a in arts]) if arts else np.array([])
            n_zeros = int(np.sum(all_w <= 0.0))
            cfg_short = "F=0" if cfg_name == "none" else ("£0.01" if cfg_name == "gbp_0.01" else "£1.00")
            legend_handles.append(
                mpatches.Patch(
                    facecolor=config_colors[cfg_name],
                    alpha=0.65,
                    edgecolor="black",
                    label=f"{ag} ({cfg_short}): {n_zeros} zeri",
                )
            )

    ax_b.legend(
        handles=legend_handles,
        title=r"Repliche con $W_T = 0$",
        loc="lower right",
        fontsize=6.5,
        title_fontsize=7.5,
        ncol=2,
        frameon=True,
    )

    # -------------------------------------------------------------------------
    # Pannello C: P(min W <= theta) per theta = 0.5 e 0.1
    # -------------------------------------------------------------------------
    ax_c = axes[2]
    group_indices = np.arange(len(agents_order))
    sub_width = 0.12

    cfgs = [c[0] for c in CONFIGURATIONS]
    for c_i, cfg_name in enumerate(cfgs):
        # theta = 0.5
        vals_05 = []
        vals_01 = []
        for ag in agents_order:
            sub = df_agg[(df_agg["config"] == cfg_name) & (df_agg["agent"] == ag)]
            if len(sub) == 0:
                vals_05.append(0.0)
                vals_01.append(0.0)
            else:
                vals_05.append(float(sub["prob_min_wealth_le_0_5"].iloc[0]))
                vals_01.append(float(sub["prob_min_wealth_le_0_1"].iloc[0]))

        offset_05 = group_indices + (c_i * 2 - 2.5) * sub_width
        offset_01 = group_indices + (c_i * 2 + 1 - 2.5) * sub_width

        c_base = config_colors[cfg_name]
        ax_c.bar(
            offset_05,
            vals_05,
            width=sub_width,
            color=c_base,
            alpha=0.9,
            edgecolor="black",
            linewidth=0.6,
            label=f"{config_labels[cfg_name]} (θ ≤ 0.5)",
        )
        ax_c.bar(
            offset_01,
            vals_01,
            width=sub_width,
            color=c_base,
            alpha=0.4,
            hatch="//",
            edgecolor="black",
            linewidth=0.6,
            label=f"{config_labels[cfg_name]} (θ ≤ 0.1)",
        )

    ax_c.set_xticks(group_indices)
    ax_c.set_xticklabels(agents_order, fontsize=11, fontweight="bold")
    ax_c.set_ylabel(r"$P(\min_t W_t \leq \theta)$", fontsize=11)
    ax_c.set_title(r"(C) Probabilità di discesa sotto soglia $\theta$", fontsize=12, fontweight="bold")
    ax_c.legend(loc="upper left", fontsize=8, ncol=2)
    ax_c.set_ylim(-0.02, 1.05)

    fig.tight_layout()
    fig.savefig(fig_path, dpi=300)
    plt.close(fig)


def main() -> None:
    """Funzione principale dello script: carica i dati, simula e salva CSV e PNG."""
    repo_root = Path(__file__).resolve().parent.parent
    results_dir = repo_root / "results"
    figures_dir = repo_root / "thesis" / "figures"
    results_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    csv_path = results_dir / "us_c6_3_floor_real_config.csv"
    fig_path = figures_dir / "us_c6_3_floor_real_config.png"

    cfg = read_split_config()
    df_hist = load_by_role("history")
    df_train = load_by_role("training")
    df_val = load_by_role("validation")
    df = pd.concat([df_hist, df_train, df_val], ignore_index=True)
    df = df.sort_values("Date", kind="stable").reset_index(drop=True)

    schedule = derive_fit_schedule(cfg)
    df_residuals = compute_model_residuals(df, schedule, ELO_FITS)

    records, group_artifacts = evaluate_floor_real_config(
        df_residuals=df_residuals,
        df=df,
        schedule=schedule,
        m_replicas=1000,
        seed=SEED_C6,
    )

    df_out = pd.DataFrame(records)[list(FLOOR_REAL_CSV_COLUMNS)]
    df_out.to_csv(csv_path, index=False)

    _plot_three_panels(df_out, group_artifacts, fig_path)


if __name__ == "__main__":
    main()
