"""Script: stagione 2023-24 come in KellyBench con un LLM (DeepSeek) come Modulo 1.

Per ogni esecuzione (default 5, come i seed del paper) l'LLM prevede le 380 partite del 2023-24 e gli
agenti del progetto, con i parametri congelati, giocano la stagione partendo da £100 000
(shk.model.llm_module1, shk.model.kellybench_run). Poi si media sulle esecuzioni. Il confronto con altri
modelli non si fa qui.

Uso:
    DEEPSEEK_API_KEY=... python scripts/kellybench_llm_module1.py --runs 5
    python scripts/kellybench_llm_module1.py --runs 5 --mock      # prova senza chiave né costi

Opzioni: --model (default deepseek-flash), --temperature (default 1.0), --extra-json (corpo JSON in più
per la richiesta, per esempio per la modalità di ragionamento), --out (default build/llm), --runs.

Scrive in --out/<modello>/: llm_run<k>.jsonl (risposte grezze, riprendibili), kellybench_run<k>.csv
(righe summary e path come results/kellybench_2023_24.csv) e kellybench_summary.csv (media sulle esecuzioni).
Non scrive in results/, che il manifesto SHA256 controlla.
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path

import numpy as np

from shk.model.kellybench_run import KELLYBENCH_COLUMNS, kellybench_records
from shk.model.llm_module1 import (
    DEFAULT_MODEL,
    deepseek_predictor,
    load_season_data_with_probs,
    mock_predictor,
    predict_season,
    summarize_runs,
)
from shk.model.residuals import load_match_frame
from shk.model.test_run import TEST_SEASON

REPO_ROOT = Path(__file__).resolve().parents[1]


def write_records(path: Path, records: list[dict[str, object]]) -> None:
    """Scrive le righe nell'ordine di KELLYBENCH_COLUMNS."""
    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(KELLYBENCH_COLUMNS))
        writer.writeheader()
        for r in records:
            writer.writerow({c: r.get(c, "") for c in KELLYBENCH_COLUMNS})


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--extra-json", default="")
    parser.add_argument("--out", default="build/llm")
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args(argv)

    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not args.mock and not api_key:
        print("Manca la variabile d'ambiente DEEPSEEK_API_KEY (oppure usa --mock per provare senza chiave).")
        return 2
    extra = json.loads(args.extra_json) if args.extra_json else None
    tag = "mock" if args.mock else args.model
    out_dir = REPO_ROOT / args.out / tag
    out_dir.mkdir(parents=True, exist_ok=True)

    df, _ = load_match_frame(roles=("history", "training", "validation", "test"))
    records_by_run: list[list[dict[str, object]]] = []
    for k in range(1, args.runs + 1):
        ask = (mock_predictor(k) if args.mock
               else deepseek_predictor(api_key, args.model, args.temperature, extra))
        preds = predict_season(df, TEST_SEASON, ask, out_dir / f"llm_run{k}.jsonl",
                               progress=lambda i, n, k=k: print(f"run {k}: {i}/{n}", flush=True)
                               if i % 50 == 0 or i == n else None)
        sd =load_season_data_with_probs(preds)
        season_rows = sd.residuals.residuals[sd.residuals.residuals["season"] == TEST_SEASON]
        records = kellybench_records(sd)
        write_records(out_dir / f"kellybench_run{k}.csv", records)
        records_by_run.append(records)
        print(f"run {k}: log-loss dell'LLM {season_rows['log_loss'].mean():.4f}")

    summary = summarize_runs(records_by_run)
    summary.to_csv(out_dir / "kellybench_summary.csv", index=False)
    shown = summary[summary["config"] == "gbp_0.01"]
    print(f"\nMedia su {args.runs} esecuzioni (floor £0.01) - {tag}")
    print(shown.drop(columns="config").to_string(index=False, float_format=lambda v: f"{v:,.4f}"))
    print(f"\nFile in {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
