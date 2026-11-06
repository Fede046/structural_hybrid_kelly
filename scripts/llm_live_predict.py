"""Script: previsioni dell'LLM su partite non ancora giocate (prova dal vivo, esplorativa).

Per ogni partita di --fixtures (Date, Time, HomeTeam, AwayTeam, nomi come football-data.co.uk) costruisce
lo stesso prompt del lavoratore LLM (shk.model.llm_module1.build_prompt: ultime cinque partite di ciascuna
squadra e classifica parziale della stagione, solo partite già giocate, nessuna quota) e chiede a DeepSeek
le probabilità 1X2 --samples volte, con temperatura 1 come nelle esecuzioni di KellyBench; la previsione
è la media dei campioni. Le partite sono future, quindi l'LLM non può conoscerne il risultato.

Storia: i CSV di football-data.co.uk passati con --history STAGIONE=FILE (per esempio
2025-26=build/llm_data/2025-26.csv 2026-27=build/llm_data/2026-27.csv).

Scrive accanto a --fixtures:
- predictions.jsonl, una riga per campione con ora UTC della richiesta, prompt e risposta grezza
  (riprendibile: i campioni già fatti non si ripagano);
- predictions.csv, probabilità medie per partita, con l'ora UTC dell'ultima richiesta.
Non scrive in results/.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from shk.model.llm_module1 import DEFAULT_MODEL, build_prompt, deepseek_predictor, mock_predictor, parse_probabilities


def load_history(specs: list[str]) -> pd.DataFrame:
    frames = []
    for spec in specs:
        season, path = spec.split("=", 1)
        df = pd.read_csv(path, encoding="utf-8-sig")
        df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)
        df["season"] = season
        frames.append(df[["season", "Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"]])
    return pd.concat(frames, ignore_index=True).sort_values("Date", kind="stable").reset_index(drop=True)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--fixtures", required=True)
    p.add_argument("--season", required=True)
    p.add_argument("--history", nargs="+", required=True)
    p.add_argument("--samples", type=int, default=5)
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--mock", action="store_true")
    args = p.parse_args(argv)
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not args.mock and not key:
        print("Manca DEEPSEEK_API_KEY (oppure usa --mock).")
        return 2

    history = load_history(args.history)
    teams = set(history.loc[history["season"] == args.season, "HomeTeam"])
    fixtures = pd.read_csv(args.fixtures)
    fixtures["Date"] = pd.to_datetime(fixtures["Date"])
    fixtures["season"] = args.season
    unknown = (set(fixtures["HomeTeam"]) | set(fixtures["AwayTeam"])) - teams
    if unknown:
        raise ValueError(f"Squadre non trovate nella storia della stagione: {sorted(unknown)}")
    if (history["Date"] >= fixtures["Date"].min()).any():
        raise ValueError("La storia contiene partite dalla data della prima partita in poi")

    out_dir = Path(args.fixtures).parent
    tag = "mock" if args.mock else args.model
    jsonl = out_dir / f"predictions_{tag}.jsonl"
    done: dict[tuple[str, str, int], dict] = {}
    if jsonl.exists():
        for line in jsonl.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            done[(r["home"], r["away"], r["sample"])] = r

    rows = []
    with open(jsonl, "a", encoding="utf-8") as f:
        for _, m in fixtures.iterrows():
            prompt = build_prompt(history, m)
            probs, last_time = [], ""
            for k in range(1, args.samples + 1):
                rec = done.get((m["HomeTeam"], m["AwayTeam"], k))
                if rec is None:
                    ask = mock_predictor(k) if args.mock else deepseek_predictor(key, args.model, 1.0)
                    asked_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
                    raw = ask(prompt)
                    rec = {"date": str(m["Date"].date()), "time_uk": m["Time"], "home": m["HomeTeam"],
                           "away": m["AwayTeam"], "sample": k, "model": tag, "asked_at_utc": asked_at,
                           "prompt": prompt, "raw": raw, "p": parse_probabilities(raw).tolist()}
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    f.flush()
                probs.append(rec["p"])
                last_time = max(last_time, rec["asked_at_utc"])
            mean = np.mean(probs, axis=0)
            rows.append({"Date": m["Date"].date(), "Time": m["Time"], "HomeTeam": m["HomeTeam"],
                         "AwayTeam": m["AwayTeam"], "p_home": round(mean[0], 4), "p_draw": round(mean[1], 4),
                         "p_away": round(mean[2], 4), "sd_p_home": round(float(np.std(probs, axis=0)[0]), 4),
                         "n_samples": len(probs), "last_asked_at_utc": last_time})
    out = pd.DataFrame(rows)
    out.to_csv(out_dir / f"predictions_{tag}.csv", index=False)
    print(out.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
