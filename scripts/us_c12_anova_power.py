"""Script: verifica dell'allarme ANOVA dello schema del relatore, frequenza sui dati reali e potenza.

Sulle 19 stagioni di validazione (shk.model.scheme_power): quota di date con allarme, stagioni con
allarme dopo un cambiamento inserito a metà stagione nella serie di δ, peggioramento minimo della
media rilevabile, e la stessa frequenza con la log-loss del modello. Scrive
results/us_c12_anova_power.csv e thesis/figures/us_c12_anova_power.png.
"""

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from shk.model.frozen_params import frozen_params_path, load_frozen_params
from shk.model.module2_data import build_module2_frame
from shk.model.residuals import load_model_residuals
from shk.model.scheme_power import POWER_COLUMNS, power_records
from shk.model.scheme_run import scheme_thresholds

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "results" / "us_c12_anova_power.csv"
PNG_PATH = REPO_ROOT / "thesis" / "figures" / "us_c12_anova_power.png"
LABELS = {
    "none": "nessun cambiamento", "mean_-0.05": "media −0,05", "mean_-0.10": "media −0,10",
    "mean_-0.20": "media −0,20", "variance_x1.5": "varianza ×1,5", "variance_x2": "varianza ×2",
    "mean_-0.10_variance_x2": "media −0,10 e varianza ×2",
}


def run_experiment() -> None:
    """Soglie dello schema sul training, verifica sulla validazione, CSV e figura."""
    params = load_frozen_params(frozen_params_path())
    frame = build_module2_frame(load_model_residuals())
    thresholds = scheme_thresholds(frame[frame["role"] == "training"], params)
    records = power_records(frame, params, thresholds)
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CSV_PATH, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(POWER_COLUMNS))
        writer.writeheader()
        writer.writerows(records)
    make_figure(pd.read_csv(CSV_PATH))
    df = pd.DataFrame(records)
    for kind in ("rate", "rate_log_loss"):
        part = df[df["row_type"] == kind]
        print(f"{kind}: media {part['share_mean_alarm'].mean():.3f}, dispersione "
              f"{part['share_dispersion_alarm'].mean():.3f}, allarme {part['share_alarm'].mean():.3f}")
    for _, r in df[df["row_type"] == "power"].iterrows():
        print(f"power {r['scenario']:<24} {r['share_seasons_with_alarm']:.2f}")


def make_figure(df: pd.DataFrame) -> None:
    """(A) quota di date con allarme per stagione; (B) stagioni con allarme dopo il cambiamento inserito."""
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(14, 5))
    rate = df[df["row_type"] == "rate"]
    ax_a.bar(range(len(rate)), rate["share_alarm"], color="tab:blue")
    ax_a.axhline(0.05, color="tab:red", ls="--", label="atteso per puro caso (5%)")
    ax_a.set_xticks(range(len(rate)), rate["season"], rotation=90)
    ax_a.set_ylabel("quota di date con allarme")
    ax_a.set_title("A) Allarme sui dati reali, per stagione", loc="left")
    ax_a.legend()
    power = df[df["row_type"] == "power"]
    ax_b.barh([LABELS[s] for s in power["scenario"]], power["share_seasons_with_alarm"], color="tab:green")
    ax_b.invert_yaxis()
    ax_b.set_xlim(0, 1)
    ax_b.set_xlabel("stagioni con allarme nelle 10 date dopo il cambiamento")
    ax_b.set_title("B) Cambiamento inserito a metà stagione", loc="left")
    fig.tight_layout()
    PNG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(PNG_PATH, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    run_experiment()
