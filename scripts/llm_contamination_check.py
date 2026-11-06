"""Script: l'LLM ricorda i risultati del 2023-24? (test di contaminazione, esplorativo)

Chiede all'LLM, senza nessun altro contesto, il risultato finale di N partite del 2023-24 estratte a caso
(seed fisso) e lo confronta con il risultato vero. Riferimenti, sulle stesse partite:
- il favorito del mercato (quota B365 più bassa), cioè quanto indovina chi prevede bene senza conoscere
  l'esito;
- il caso, per il punteggio esatto: la frequenza del punteggio più comune della stagione.
Se l'LLM indovina l'esito molto più spesso del favorito del mercato e il punteggio esatto molto più
spesso del caso, sta ricordando, non prevedendo.

La chiamata è una sola richiesta di testo all'API, senza strumenti: l'LLM non può cercare in rete.

Uso:
    python scripts/llm_contamination_check.py --n 30 --model <modello>
    python scripts/llm_contamination_check.py --n 30 --mock     # prova senza chiave né costi
La chiave si legge da DEEPSEEK_API_KEY. Scrive in build/llm_contamination/<modello>/ le risposte grezze
(contamination.jsonl, riprendibile) e il confronto (contamination.csv). Non scrive in results/.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

from shk.model.residuals import load_match_frame

REPO_ROOT = Path(__file__).resolve().parents[1]
API_URL = "https://api.deepseek.com/chat/completions"
SEED = 20261108
SEASON = "2023-24"
SYSTEM_PROMPT = ("You are a football results database. Answer only with a JSON object: "
                 '{"home_goals": <int>, "away_goals": <int>, "confidence": "certain" or "guess"}.')


def user_prompt(row: pd.Series, season: str = SEASON) -> str:
    date = pd.Timestamp(row["Date"]).strftime("%d %B %Y")
    return (f"What was the final score of the English Premier League match {row['HomeTeam']} vs "
            f"{row['AwayTeam']}, played on {date} (season {season})? If you do not know it, give your best "
            "guess and set confidence to \"guess\".")


def deepseek_ask(api_key: str, model: str):
    def ask(prompt: str) -> str:
        body = {"model": model, "temperature": 0.0,
                "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]}
        data = json.dumps(body).encode("utf-8")
        last = None
        for attempt in range(4):
            req = urllib.request.Request(API_URL, data=data, method="POST", headers={
                "Content-Type": "application/json", "Authorization": f"Bearer {api_key}"})
            try:
                with urllib.request.urlopen(req, timeout=180) as resp:
                    out = json.loads(resp.read())
                    return out["choices"][0]["message"]["content"], out.get("usage", {})
            except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as exc:
                last = exc
                time.sleep(2.0 ** attempt)
        raise RuntimeError(f"DeepSeek call failed: {last}")
    return ask


def mock_ask(prompt: str) -> tuple[str, dict]:
    rng = np.random.default_rng(abs(hash(prompt)) % (2 ** 32))
    return json.dumps({"home_goals": int(rng.poisson(1.5)), "away_goals": int(rng.poisson(1.2)),
                       "confidence": "guess"}), {}


def parse(text: str) -> tuple[int | None, int | None, str]:
    m = re.search(r"\{.*\}", text, re.S)
    try:
        obj = json.loads(m.group(0)) if m else {}
        return int(obj["home_goals"]), int(obj["away_goals"]), str(obj.get("confidence", ""))
    except (ValueError, KeyError, TypeError):
        return None, None, ""


def outcome(h: int, a: int) -> str:
    return "H" if h > a else ("A" if h < a else "D")


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--n", type=int, default=30)
    p.add_argument("--model", default="deepseek-flash")
    p.add_argument("--mock", action="store_true")
    p.add_argument("--season", default=SEASON)
    p.add_argument("--from-date", default="", help="solo partite da questa data (AAAA-MM-GG); con --n 0 le usa tutte")
    p.add_argument("--csv", default="", help="CSV di football-data.co.uk della stagione (default: dati del progetto)")
    args = p.parse_args(argv)
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not args.mock and not key:
        print("Manca DEEPSEEK_API_KEY (oppure usa --mock).")
        return 2
    ask = mock_ask if args.mock else deepseek_ask(key, args.model)
    out_dir = (REPO_ROOT / "build" / "llm_contamination" / ("mock" if args.mock else args.model) / args.season
               / (f"from_{args.from_date}" if args.from_date else "random"))
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.csv:
        df = pd.read_csv(args.csv, encoding="utf-8-sig")
        df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)
    else:
        df, _ = load_match_frame(roles=("test",))
        df = df[df["season"] == args.season]
    if args.from_date:
        df = df[df["Date"] >= pd.Timestamp(args.from_date)]
    df = df.reset_index(drop=True)
    n = len(df) if args.n <= 0 or args.n >= len(df) else args.n
    idx = np.sort(np.random.default_rng(SEED).choice(len(df), size=n, replace=False))
    sample = df.loc[idx]

    cache_path = out_dir / "contamination.jsonl"
    cache = {}
    if cache_path.exists():
        for line in cache_path.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            cache[r["prompt"]] = r
    usage_total = {"prompt_tokens": 0, "completion_tokens": 0}
    with open(cache_path, "a", encoding="utf-8") as f:
        for _, row in sample.iterrows():
            prompt = user_prompt(row, args.season)
            if prompt not in cache:
                text, usage = ask(prompt)
                cache[prompt] = {"prompt": prompt, "response": text, "usage": usage}
                f.write(json.dumps(cache[prompt], ensure_ascii=False) + "\n")
                f.flush()
                for k in usage_total:
                    usage_total[k] += int(usage.get(k, 0) or 0)

    common = df.groupby(["FTHG", "FTAG"]).size().max() / len(df)
    rows = []
    for _, row in sample.iterrows():
        h, a, conf = parse(cache[user_prompt(row, args.season)]["response"])
        odds = row[["B365H", "B365D", "B365A"]].astype(float).to_numpy()
        fav = "HDA"[int(np.argmin(odds))]
        rows.append({"Date": pd.Timestamp(row["Date"]).date(), "HomeTeam": row["HomeTeam"],
                     "AwayTeam": row["AwayTeam"], "true_score": f"{row['FTHG']}-{row['FTAG']}",
                     "llm_score": "" if h is None else f"{h}-{a}", "confidence": conf,
                     "exact": h is not None and h == row["FTHG"] and a == row["FTAG"],
                     "llm_outcome_ok": h is not None and outcome(h, a) == row["FTR"],
                     "market_favourite_ok": fav == row["FTR"]})
    res = pd.DataFrame(rows)
    res.to_csv(out_dir / "contamination.csv", index=False)
    n = len(res)
    print(res.to_string(index=False))
    print(f"\nPartite: {n}; risposte non leggibili: {(res['llm_score'] == '').sum()}")
    print(f"Esito giusto, LLM:              {res['llm_outcome_ok'].mean():.0%}")
    print(f"Esito giusto, favorito mercato: {res['market_favourite_ok'].mean():.0%}")
    print(f"Punteggio esatto, LLM:          {res['exact'].mean():.0%}  (caso: circa {common:.0%})")
    print(f"Dichiarate 'certain':           {(res['confidence'] == 'certain').mean():.0%}")
    if not args.mock:
        print(f"Token di questa esecuzione: {usage_total}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
