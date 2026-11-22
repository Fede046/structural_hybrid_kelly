"""Script: a che cosa serve distinguere un errore strutturale da un errore nei dati.

Controllo del 2026-11-22, deciso riscrivendo il §5.4 della tesi. La distinzione serve se ristimare il modello
migliora le previsioni dopo un errore strutturale e non dopo un errore nei dati. Per ogni stagione in cui
l'allarme scatta e per ogni giornata j in cui il supervisore può già fare il confronto, si prendono le
previsioni del modello ristimato il giorno j (precalcolate da us_c47: results/raw/us_c47/<versione>_<stagione>_<j>.npy)
e si misura la differenza di log-loss rispetto al modello di inizio stagione:
- sulle 40 partite dal giorno j in poi (d40);
- su tutte le partite dal giorno j alla fine della stagione (drest).
Le giornate si dividono secondo la diagnosi del modello di inizio stagione (us_c46, diag0): errore
strutturale, errore nei dati, nessun allarme. Una differenza negativa vuol dire che ristimare quel giorno
avrebbe migliorato le previsioni.

Scrive results/us_c50_diagnosis_value_days.csv (una riga per versione, stagione e giornata) e
results/us_c50_diagnosis_value_summary.csv (per versione, stagione e diagnosi, e per versione e diagnosi).
"""

import csv
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS = REPO_ROOT / "results"
RAW46 = RESULTS / "raw" / "us_c46"
RAW47 = RESULTS / "raw" / "us_c47"
WINDOW: Final[int] = 40
VERSIONS: Final[tuple[str, ...]] = ("recente", "uguale")
LABELS: Final[dict[str, str]] = {"structural": "strutturale", "compositional": "dati", "none": "nessun allarme"}


def season_days(version: str, season: str) -> list[dict]:
    z = np.load(RAW46 / f"{version}_{season}.npz")
    dates = z["dates"]
    days = np.unique(dates)
    y = z["outcomes"][0]
    k = np.arange(len(y))
    ll0 = -np.log(z["probs0"][k, y])
    counts = np.searchsorted(dates, days, side="left")
    first = int(np.flatnonzero(counts >= WINDOW)[0])
    rows = []
    for j in range(first, len(days)):
        ll = -np.log(np.load(RAW47 / f"{version}_{season}_{j:03d}.npy")[k, y])
        after = np.flatnonzero(dates >= days[j])
        nxt = after[:WINDOW]
        rows.append({"version": version, "season": season, "day": j + 1, "date": str(pd.Timestamp(days[j]).date()),
                     "diagnosis": LABELS[str(z["diag0"][j])], "d40": float(ll[nxt].mean() - ll0[nxt].mean()),
                     "drest": float(ll[after].mean() - ll0[after].mean()), "n_rest": int(len(after))})
    return rows


def _write(path: Path, rows: list[dict]) -> None:
    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def summarise(g: pd.DataFrame) -> dict:
    return {"days": len(g), "d40_mean": g["d40"].mean(), "drest_mean": g["drest"].mean(),
            "drest_median": g["drest"].median(), "share_better": float((g["drest"] < 0).mean())}


def run_experiment() -> None:
    seasons = sorted({p.name.split("_")[1] for p in RAW47.glob("recente_*.npy")})
    days = pd.DataFrame([r for v in VERSIONS for s in seasons for r in season_days(v, s)])
    _write(RESULTS / "us_c50_diagnosis_value_days.csv", days.to_dict("records"))
    summary = [{"version": v, "season": s, "diagnosis": d, **summarise(g)}
               for (v, s, d), g in days.groupby(["version", "season", "diagnosis"])]
    summary += [{"version": v, "season": "tutte", "diagnosis": d, **summarise(g)}
                for (v, d), g in days.groupby(["version", "diagnosis"])]
    summary += [{"version": v, "season": "tutte tranne 2020-21", "diagnosis": d, **summarise(g)}
                for (v, d), g in days[days["season"] != "2020-21"].groupby(["version", "diagnosis"])]
    _write(RESULTS / "us_c50_diagnosis_value_summary.csv", summary)
    pd.set_option("display.width", 250)
    print(pd.DataFrame(summary).round(4).to_string(index=False))


if __name__ == "__main__":
    run_experiment()
