"""Script: inferenza appaiata sulle 19 stagioni vere (shk.model.paired_inference).

Legge le sintesi versionate (le stesse di us_c19), senza nuove esecuzioni, e scrive
results/us_c24_paired_inference.csv: per sintesi × configurazione × agente, stagioni meglio e peggio
del riferimento appaiato, test dei segni, test di Wilcoxon e rapporto dei capitali tipici con
intervallo bootstrap sulle stagioni. Stampa la configurazione £0,01.
"""

import csv
from pathlib import Path

from shk.model.paired_inference import PAIRED_COLUMNS, all_paired_records

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "results" / "us_c24_paired_inference.csv"


def run_experiment() -> None:
    """Statistiche appaiate e CSV."""
    records = all_paired_records(REPO_ROOT / "results")
    with open(CSV_PATH, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(PAIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(records)
    print(f"{'source':<13} {'agent':<15} {'ref':<9} {'+':>3} {'-':>3} {'sign p':>7} {'wilc. p':>7} "
          f"{'ratio':>6} {'low':>6} {'high':>6}")
    for r in records:
        if r["config"] != "gbp_0.01":
            continue
        print(f"{r['source']:<13} {r['agent']:<15} {r['reference']:<9} {r['seasons_better']:>3} "
              f"{r['seasons_worse']:>3} {r['sign_test_p']:>7.3f} {r['wilcoxon_p']:>7.3f} "
              f"{r['capital_ratio']:>6.3f} {r['capital_ratio_low']:>6.3f} {r['capital_ratio_high']:>6.3f}")


if __name__ == "__main__":
    run_experiment()
