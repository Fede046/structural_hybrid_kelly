"""Script: risultati sulle 19 stagioni reali di validazione, accanto alle stagioni ricostruite.

Legge le sintesi versionate (shk.model.real_seasons.REAL_SOURCES), senza nuove esecuzioni, e scrive
results/us_c19_real_seasons.csv: per sintesi × configurazione × agente, capitale tipico sulle
stagioni vere e sulla mediana delle ricostruite, stagioni meglio e peggio del riferimento appaiato,
allarmi e quota di date con λ = 0. Stampa la configurazione £0,01.
"""

import csv
from pathlib import Path

from shk.model.real_seasons import REAL_COLUMNS, all_real_records

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "results" / "us_c19_real_seasons.csv"


def run_experiment() -> None:
    """Sintesi sulle stagioni vere e CSV."""
    records = all_real_records(REPO_ROOT / "results")
    with open(CSV_PATH, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(REAL_COLUMNS))
        writer.writeheader()
        writer.writerows(records)
    print(f"{'source':<13} {'agent':<15} {'real':>6} {'seeds':>6} {'better':>6} {'worse':>5} "
          f"{'alarms':>6} {'lam0':>5}")
    for r in records:
        if r["config"] != "gbp_0.01":
            continue
        fmt = lambda v, s: "" if v == "" else format(v, s)  # noqa: E731
        print(f"{r['source']:<13} {r['agent']:<15} {r['typical_capital_real']:>6.3f} {r['typical_capital_seeds']:>6.3f} "
              f"{fmt(r['seasons_better_real'], 'd'):>6} {fmt(r['seasons_worse_real'], 'd'):>5} "
              f"{r['mean_alarms_real']:>6.2f} {r['share_lambda_zero_real']:>5.2f}")


if __name__ == "__main__":
    run_experiment()
