"""Modulo 1 basato su un LLM (DeepSeek) per la stagione 2023-24: esecuzione esplorativa.

Un LLM prevede le probabilità 1X2 di ogni partita del 2023-24 al posto dell'Elo. Il resto del
sistema (Modulo 2, Modulo 3, agenti, parametri congelati di config/frozen_params.toml, ambiente)
resta quello dell'esecuzione sul test: cambiano solo le previsioni p̂.

Informazioni date all'LLM per ogni partita, tutte con data strettamente anteriore: ultime cinque
partite di ciascuna squadra e classifica parziale della stagione. Non riceve le quote, che
farebbero coincidere p̂ con il mercato. Solo la data, i nomi e questi dati entrano nel prompt: mai
l'esito.

Limiti da dichiarare:
- contaminazione: l'LLM può conoscere gli esiti reali del 2023-24 dal proprio addestramento;
- è un'esecuzione descrittiva sul test set, fuori dal protocollo dell'esecuzione unica (README):
  non cambia nessun parametro e non sostituisce i risultati dell'Elo;
- le probabilità dell'LLM si limitano a [PROB_FLOOR, 1] e si rinormalizzano, perché un p̂ vicino a
  zero sull'esito reale farebbe esplodere ln p̂.
"""

import copy
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from shk.data.split import read_split_config
from shk.model.covariate_inspection import derive_specification
from shk.model.module1 import MODULE1_ELO
from shk.model.module2_data import build_module2_frame
from shk.model.residuals import load_match_frame, model_residuals_data
from shk.model.test_run import TEST_FIT, TEST_SEASON, SeasonData
from shk.model.season_input import season_input_from_frame

API_URL: Final[str] = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL: Final[str] = "deepseek-flash"
PROB_FLOOR: Final[float] = 0.02
N_RECENT: Final[int] = 5
MAX_ATTEMPTS: Final[int] = 4

SYSTEM_PROMPT: Final[str] = (
    "Sei un analista di calcio. Dai la probabilità dei tre esiti di una partita di Premier League "
    "usando solo le informazioni fornite. Rispondi solo con un oggetto JSON: "
    '{"p_home": x, "p_draw": y, "p_away": z}, con x+y+z=1.'
)

Predictor = Callable[[str], dict[str, float]]


def _recent(history: pd.DataFrame, team: str, n: int = N_RECENT) -> list[str]:
    """Ultime n partite della squadra, dalla più recente: 'data casa/trasferta avversario gol-gol'."""
    played = history[(history["HomeTeam"] == team) | (history["AwayTeam"] == team)].tail(n)
    lines = []
    for r in played.iloc[::-1].itertuples(index=False):
        home = r.HomeTeam == team
        gf, ga = (r.FTHG, r.FTAG) if home else (r.FTAG, r.FTHG)
        lines.append(f"{pd.Timestamp(r.Date).date()} {'casa' if home else 'trasferta'} vs "
                     f"{r.AwayTeam if home else r.HomeTeam}: {int(gf)}-{int(ga)}")
    return lines


def _season_record(history: pd.DataFrame, season: str, team: str) -> str:
    """Partite, punti e differenza reti della squadra nella stagione, prima della data."""
    part = history[(history["season"] == season)
                   & ((history["HomeTeam"] == team) | (history["AwayTeam"] == team))]
    if part.empty:
        return "nessuna partita giocata in questa stagione"
    home = part["HomeTeam"] == team
    gf = np.where(home, part["FTHG"], part["FTAG"]).astype(int)
    ga = np.where(home, part["FTAG"], part["FTHG"]).astype(int)
    points = int((3 * (gf > ga) + (gf == ga)).sum())
    return f"{len(part)} partite, {points} punti, differenza reti {int((gf - ga).sum()):+d}"


def build_prompt(df: pd.DataFrame, match: pd.Series) -> str:
    """Prompt di una partita con le sole partite di data strettamente anteriore.

    Solleva
    -------
    ValueError
        Se la storia contiene date non anteriori a quella della partita (fuga di informazione).
    """
    history = df[df["Date"] < match["Date"]]
    if len(history) and history["Date"].max() >= match["Date"]:
        raise ValueError("history must be strictly earlier than the match date")
    home, away = match["HomeTeam"], match["AwayTeam"]
    blocks = [f"Partita del {pd.Timestamp(match['Date']).date()}: {home} (in casa) contro {away} (in trasferta)."]
    for label, team in (("casa", home), ("trasferta", away)):
        blocks.append(f"{team} ({label}) - stagione: {_season_record(history, match['season'], team)}.")
        blocks.append("Ultime partite:\n" + ("\n".join(_recent(history, team)) or "nessuna"))
    return "\n".join(blocks)


def parse_probabilities(text: str) -> np.ndarray:
    """(p_home, p_draw, p_away) dal primo oggetto JSON del testo, limitate a PROB_FLOOR e rinormalizzate.

    Solleva
    -------
    ValueError
        Se manca l'oggetto JSON, una chiave, o i valori non sono finiti e positivi.
    """
    found = re.search(r"\{.*?\}", text, flags=re.DOTALL)
    if found is None:
        raise ValueError(f"No JSON object in the answer: {text[:200]!r}")
    obj = json.loads(found.group(0))
    p = np.array([float(obj["p_home"]), float(obj["p_draw"]), float(obj["p_away"])], dtype=np.float64)
    if not np.all(np.isfinite(p)) or np.any(p < 0.0) or p.sum() <= 0.0:
        raise ValueError(f"Invalid probabilities: {p}")
    p = np.maximum(p / p.sum(), PROB_FLOOR)
    return p / p.sum()


def deepseek_predictor(api_key: str, model: str = DEFAULT_MODEL, temperature: float = 1.0,
                       extra_body: dict | None = None, timeout: float = 180.0) -> Callable[[str], str]:
    """Funzione prompt -> testo della risposta, con tentativi ripetuti. La chiave resta in memoria."""
    def call(prompt: str) -> str:
        body = {"model": model, "temperature": temperature,
                "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
                **(extra_body or {})}
        data = json.dumps(body).encode("utf-8")
        last: Exception | None = None
        for attempt in range(MAX_ATTEMPTS):
            req = urllib.request.Request(API_URL, data=data, method="POST", headers={
                "Content-Type": "application/json", "Authorization": f"Bearer {api_key}"})
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return json.loads(resp.read())["choices"][0]["message"]["content"]
            except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as exc:
                last = exc
                time.sleep(2.0 ** attempt)
        raise RuntimeError(f"DeepSeek call failed after {MAX_ATTEMPTS} attempts: {last}")
    return call


def mock_predictor(run: int) -> Callable[[str], str]:
    """Risposte finte deterministiche (per provare la catena senza chiave né costi). NON sono previsioni."""
    def call(prompt: str) -> str:
        seed = int.from_bytes(hashlib.sha256(prompt.encode()).digest()[:4], "big")
        rng = np.random.default_rng([run, seed])
        p = rng.dirichlet([4.0, 2.5, 3.0])
        return json.dumps({"p_home": p[0], "p_draw": p[1], "p_away": p[2]})
    return call


def predict_season(df: pd.DataFrame, season: str, ask: Callable[[str], str], cache_path: Path,
                   progress: Callable[[int, int], None] | None = None) -> pd.DataFrame:
    """Probabilità dell'LLM per ogni partita della stagione, con cache JSONL riutilizzabile.

    Ogni riga della cache ha data, squadre, risposta grezza e probabilità: una chiamata interrotta si
    riprende senza ripagare le partite già fatte.
    """
    cache: dict[tuple[str, str, str], dict] = {}
    if cache_path.exists():
        for line in cache_path.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            cache[(rec["date"], rec["home"], rec["away"])] = rec
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    matches = df[df["season"] == season].sort_values("Date", kind="stable")
    with open(cache_path, "a", encoding="utf-8") as out:
        for i, (_, m) in enumerate(matches.iterrows()):
            key = (str(pd.Timestamp(m["Date"]).date()), m["HomeTeam"], m["AwayTeam"])
            rec = cache.get(key)
            if rec is None:
                raw = ask(build_prompt(df, m))
                p = parse_probabilities(raw)
                rec = {"date": key[0], "home": key[1], "away": key[2], "raw": raw, "p": p.tolist()}
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out.flush()
            rows.append({"Date": pd.Timestamp(key[0]), "HomeTeam": key[1], "AwayTeam": key[2],
                         "p_home": rec["p"][0], "p_draw": rec["p"][1], "p_away": rec["p"][2]})
            if progress is not None:
                progress(i + 1, len(matches))
    return pd.DataFrame(rows)


def load_season_data_with_probs(preds: pd.DataFrame, season: str = TEST_SEASON, fit: str = TEST_FIT,
                                devig_method: str = "shin") -> SeasonData:
    """Come test_run.load_season_data, ma con le probabilità della stagione sostituite da preds.

    Si cambiano p_home, p_draw, p_away e log_loss delle righe della stagione nei residui; il DataFrame
    del Modulo 2 (δ, entropia del modello, ecc.) e gli ingressi dell'ambiente si ricostruiscono da lì.
    Le specificazioni delle covariate restano quelle scelte sul training.

    Solleva
    -------
    ValueError
        Se preds non copre esattamente le partite della stagione.
    """
    cfg = read_split_config()
    roles = ("history", "training", "validation") + (("test",) if season in cfg.test else ())
    df, schedule = load_match_frame(roles=roles)
    schedule = copy.deepcopy(schedule)
    if season not in schedule[fit]["validation"]:
        schedule[fit]["validation"] = list(schedule[fit]["validation"]) + [season]
    data = model_residuals_data(df, schedule, module1=MODULE1_ELO)

    res = data.residuals.copy()
    mask = res["season"] == season
    keys = ["Date", "HomeTeam", "AwayTeam"]
    merged = res.loc[mask, keys].merge(preds[keys + ["p_home", "p_draw", "p_away"]], on=keys, how="left")
    if len(merged) != int(mask.sum()) or merged[["p_home", "p_draw", "p_away"]].isna().any().any():
        raise ValueError("preds must cover exactly the matches of the season")
    new = merged[["p_home", "p_draw", "p_away"]].to_numpy(dtype=np.float64)
    res.loc[mask, ["p_home", "p_draw", "p_away"]] = new
    idx = res.loc[mask, "FTR"].astype(str).str.strip().map({"H": 0, "D": 1, "A": 2}).to_numpy()
    res.loc[mask, "log_loss"] = -np.log(new[np.arange(len(new)), idx])
    data = data._replace(residuals=res)

    frame = build_module2_frame(data, devig_method=devig_method)
    covariates = derive_specification(frame[frame["role"] == "training"]).covariates
    season_frame = frame[frame["season"] == season].assign(role="test")
    return SeasonData(season, fit, data, season_frame, tuple(covariates),
                      season_input_from_frame(season_frame, season, covariates), devig_method)


def summarize_runs(records_by_run: list[list[dict[str, object]]]) -> pd.DataFrame:
    """Media, deviazione standard e rovine sulle esecuzioni, per configurazione di floor e agente.

    Usa le sole righe "summary" di kellybench_records. Il rendimento della stagione è il bankroll
    finale / iniziale − 1; la media è aritmetica sulle esecuzioni, come la media sui seed del paper.
    """
    rows = []
    for run, records in enumerate(records_by_run, start=1):
        for r in records:
            if r["row_type"] == "summary":
                rows.append({"run": run, "config": r["config"], "agent": r["agent"],
                             "bankroll_gbp": float(r["bankroll_gbp"]), "season_return": float(r["season_return"]),
                             "ruined": bool(r["ruined"])})
    runs = pd.DataFrame(rows)
    grouped = runs.groupby(["config", "agent"], sort=False)
    out = grouped.agg(n_runs=("run", "nunique"), mean_bankroll_gbp=("bankroll_gbp", "mean"),
                      mean_return=("season_return", "mean"), std_return=("season_return", "std"),
                      best_return=("season_return", "max"), worst_return=("season_return", "min"),
                      n_ruined=("ruined", "sum")).reset_index()
    return out


__all__ = ["DEFAULT_MODEL", "build_prompt", "parse_probabilities", "deepseek_predictor", "mock_predictor",
           "predict_season", "load_season_data_with_probs", "summarize_runs"]
