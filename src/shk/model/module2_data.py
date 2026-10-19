"""DataFrame per partita del Modulo 2: δ_t e covariate candidate (T46, US-C7.2).

Una riga per partita delle stagioni di training e di validazione:
- training: la stagione j prevista dal fit che termina in j (scenario di training di S5);
- validation: ogni stagione di validazione prevista dal suo fit.

Colonne principali:
- δ_t = ln p̂_t(x_t) − ln q_t(x_t) (decisione S8), con p̂ del Modulo 1 raw e q di Shin
  dalla terna B365 pre-partita; per il 2000-01, che non ha B365, dalla terna pre-partita
  completa fra GB, IW, SB e WH il cui overround medio nel 2000-01 è il più vicino a quello
  medio di B365 nel 2002-03 (decisione S8, select_triple_2000_01);
- covariate, tutte note prima della partita: log_odds_ratio = ln(o_H / o_A) con le quote
  della stessa terna; market_entropy = H(q); elo_diff = R_casa − R_trasferta + h, ricavato
  dalle probabilità di Davidson come 400·log10(p_home / p_away), senza ricalcolare i
  rating; flag_new, flag_returning, flag_promoted (almeno una squadra mai vista, tornante,
  o una delle due, nella stagione); position = posizione nella stagione (1..380) in ordine
  di Date stabile; model_entropy = H(p̂).

Con Dixon-Coles come Modulo 1 (T61) il differenziale di forza è quello del modello in uso:
lambda_diff = λ − μ, differenza dei gol attesi di casa e in trasferta delle stesse previsioni,
al posto di elo_diff (scelta delegata di T61: nessuna covariata calcolata con un modello
diverso dal Modulo 1). Le altre colonne sono le stesse.

I flag di ingresso seguono la regola del Modulo 1 (elo_predictor._EloTracker): nella
stagione s una squadra è "new" se non compare in nessuna stagione precedente del DataFrame,
"returning" se compare prima ma non in s − 1, "" se compare in s − 1; nella prima stagione
del DataFrame tutte valgono "". Dipendono solo dalle rose delle stagioni, non dagli esiti.
"""

from typing import Final, NamedTuple

import numpy as np
import pandas as pd

from shk.data.coverage import classify_column
from shk.market.devig import devig_probabilities, devig_shin
from shk.model.elo_fit import parse_season_start_year
from shk.model.module1 import MODULE1_DIXON_COLES, MODULE1_ELO, check_module1
from shk.model.residual_heteroskedasticity import compute_shannon_entropy
from shk.model.residuals import ModelResidualsData
from shk.model.scoring import MATCH_KEYS, align_predictions_with_odds

ELO_SCALE: Final[float] = 400.0
B365_PREFIX: Final[str] = "B365"
TRIPLE_CANDIDATES_2000_01: Final[tuple[str, ...]] = ("GB", "IW", "SB", "WH")
SEASON_WITHOUT_B365: Final[str] = "2000-01"
B365_REFERENCE_SEASON: Final[str] = "2002-03"
STATUS_NEW: Final[str] = "new"
STATUS_RETURNING: Final[str] = "returning"
_OUTCOME_INDEX: Final[dict[str, int]] = {"H": 0, "D": 1, "A": 2}

COVARIATE_COLUMNS: Final[tuple[str, ...]] = (
    "log_odds_ratio",
    "market_entropy",
    "elo_diff",
    "flag_new",
    "flag_returning",
    "flag_promoted",
    "position",
    "model_entropy",
)

STRENGTH_COVARIATES: Final[dict[str, str]] = {MODULE1_ELO: "elo_diff", MODULE1_DIXON_COLES: "lambda_diff"}

MODULE2_FRAME_COLUMNS: Final[tuple[str, ...]] = (
    "season",
    "Date",
    "HomeTeam",
    "AwayTeam",
    "role",
    "fit_through",
    "FTR",
    "p_home",
    "p_draw",
    "p_away",
    "odds_source",
    "odds_home",
    "odds_draw",
    "odds_away",
    "q_home",
    "q_draw",
    "q_away",
    "shin_z",
    "delta",
    *COVARIATE_COLUMNS,
)


class TripleChoice(NamedTuple):
    """Terna scelta per il 2000-01 e overround medi di confronto."""

    source: str
    overround_mean: float
    b365_reference_overround: float
    candidate_overrounds: dict[str, float]


def _triple_columns(source: str) -> list[str]:
    return [f"{source}H", f"{source}D", f"{source}A"]


def _complete_triple(frame: pd.DataFrame, source: str) -> bool:
    """Terna presente, non nulla e > 1 su ogni riga (definizione di completezza di S3)."""
    cols = _triple_columns(source)
    if not all(c in frame.columns for c in cols):
        return False
    values = frame[cols].apply(pd.to_numeric, errors="coerce")
    return bool(values.notna().all().all() and (values > 1.0).all().all())


def _mean_overround(frame: pd.DataFrame, source: str) -> float:
    odds = frame[_triple_columns(source)].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    return float(((1.0 / odds).sum(axis=1) - 1.0).mean())


def select_triple_2000_01(df: pd.DataFrame) -> TripleChoice:
    """Terna pre-partita completa del 2000-01 con overround medio più vicino a B365 2002-03.

    A parità esatta di distanza vale l'ordine di TRIPLE_CANDIDATES_2000_01.

    Solleva
    -------
    ValueError
        Se mancano le stagioni, B365 non è completa nel 2002-03 o nessuna candidata è
        completa nel 2000-01.
    """
    season_0 = df[df["season"] == SEASON_WITHOUT_B365]
    season_ref = df[df["season"] == B365_REFERENCE_SEASON]
    if season_0.empty or season_ref.empty:
        raise ValueError("Seasons 2000-01 and 2002-03 are required")
    if not _complete_triple(season_ref, B365_PREFIX):
        raise ValueError("B365 pre-match triple must be complete in 2002-03")
    for source in TRIPLE_CANDIDATES_2000_01:
        for col in _triple_columns(source):
            info = classify_column(col)
            if info.timing != "prematch" or info.kind != "odds":
                raise ValueError(f"Column {col} is not a pre-match odds column")
    reference = _mean_overround(season_ref, B365_PREFIX)
    candidates = {
        s: _mean_overround(season_0, s)
        for s in TRIPLE_CANDIDATES_2000_01
        if _complete_triple(season_0, s)
    }
    if not candidates:
        raise ValueError("No complete pre-match triple among the candidates in 2000-01")
    best = min(candidates, key=lambda s: (abs(candidates[s] - reference), TRIPLE_CANDIDATES_2000_01.index(s)))
    return TripleChoice(best, candidates[best], reference, candidates)


def entry_status_by_team_season(df: pd.DataFrame) -> dict[tuple[str, str], str]:
    """Stato d'ingresso di ogni squadra in ogni stagione del DataFrame (regola del Modulo 1)."""
    seasons = sorted(df["season"].unique(), key=parse_season_start_year)
    rosters = {
        s: set(df.loc[df["season"] == s, "HomeTeam"]) | set(df.loc[df["season"] == s, "AwayTeam"])
        for s in seasons
    }
    status: dict[tuple[str, str], str] = {}
    seen: set[str] = set()
    previous: set[str] = set()
    for i, s in enumerate(seasons):
        for team in rosters[s]:
            if i == 0 or team in previous:
                status[(s, team)] = ""
            elif team in seen:
                status[(s, team)] = STATUS_RETURNING
            else:
                status[(s, team)] = STATUS_NEW
        seen |= rosters[s]
        previous = rosters[s]
    return status


def strength_covariate(frame: pd.DataFrame) -> str:
    """Nome del differenziale di forza presente nel DataFrame: lambda_diff (Dixon-Coles) o elo_diff."""
    return STRENGTH_COVARIATES[MODULE1_DIXON_COLES] if "lambda_diff" in frame.columns else STRENGTH_COVARIATES[MODULE1_ELO]


def with_strength(names: tuple[str, ...], strength: str) -> tuple[str, ...]:
    """Nomi di covariate con elo_diff sostituito dal differenziale di forza dato."""
    return tuple(strength if n == STRENGTH_COVARIATES[MODULE1_ELO] else n for n in names)


def module2_frame_columns(module1: str = MODULE1_ELO) -> tuple[str, ...]:
    """Colonne del DataFrame del Modulo 2 per il Modulo 1 dato."""
    return with_strength(MODULE2_FRAME_COLUMNS, STRENGTH_COVARIATES[check_module1(module1)])


def reconstruct_elo_diff(p_home: np.ndarray, p_away: np.ndarray, scale: float = ELO_SCALE) -> np.ndarray:
    """Differenziale Elo con h da probabilità di Davidson: scale · log10(p_home / p_away).

    Nel mapping di Davidson p_home / p_away = 10^(delta / scale) (elo.davidson_probabilities).
    """
    ph = np.asarray(p_home, dtype=np.float64)
    pa = np.asarray(p_away, dtype=np.float64)
    if np.any(ph <= 0.0) or np.any(pa <= 0.0):
        raise ValueError("p_home and p_away must be strictly positive")
    return scale * np.log10(ph / pa)


def build_module2_frame(data: ModelResidualsData, triple_2000_01: str | None = None,
                        devig_method: str = "shin") -> pd.DataFrame:
    """DataFrame per partita con δ e covariate candidate (colonne MODULE2_FRAME_COLUMNS).

    Parametri
    ---------
    data : ModelResidualsData
        Uscita di load_model_residuals.
    triple_2000_01 : str o None
        Fonte delle quote per il 2000-01; se None si sceglie con select_triple_2000_01.
    devig_method : str
        Metodo di de-vigging di q (default "shin", decisione S7); gli altri servono alla
        sensibilità di T63. Con un metodo diverso da Shin la colonna shin_z vale NaN.

    Restituisce
    -------
    pd.DataFrame
        Ordinato per stagione cronologica e Date stabile.

    Solleva
    -------
    ValueError
        Se una stagione non ha la terna di quote completa.
    """
    res = data.residuals
    train_mask = (res["role"] == "training") & (res["season"] == res["fit_through"])
    frame = res[train_mask | (res["role"] == "validation")].copy()
    if data.rates is not None:
        # Gol attesi di Dixon-Coles, allineati per indice alle righe dei residui
        frame = frame.join(data.rates)
    frame["season_year"] = frame["season"].map(parse_season_start_year)
    frame = frame.sort_values(["season_year", "Date"], kind="stable").drop(columns="season_year")
    frame = frame.reset_index(drop=True)

    aligned = align_predictions_with_odds(frame, data.df).copy()
    aligned = aligned.set_index(list(MATCH_KEYS)).loc[
        pd.MultiIndex.from_frame(frame[list(MATCH_KEYS)])
    ].reset_index()

    source_2000 = triple_2000_01 if triple_2000_01 is not None else select_triple_2000_01(data.df).source
    sources = np.where(aligned["season"] == SEASON_WITHOUT_B365, source_2000, B365_PREFIX)
    odds = np.empty((len(aligned), 3), dtype=np.float64)
    for source in np.unique(sources):
        mask = sources == source
        cols = _triple_columns(str(source))
        values = aligned.loc[mask, cols].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=np.float64)
        if not (np.all(np.isfinite(values)) and np.all(values > 1.0)):
            raise ValueError(f"Odds triple {source} incomplete for some matches")
        odds[mask] = values

    if devig_method == "shin":
        q, z = devig_shin(odds)
    else:
        q, z = devig_probabilities(odds, devig_method), np.full(len(odds), np.nan)
    probs = aligned[["p_home", "p_draw", "p_away"]].to_numpy(dtype=np.float64)
    outcome = aligned["FTR"].astype(str).str.strip().map(_OUTCOME_INDEX).to_numpy(dtype=np.int64)
    rows = np.arange(len(aligned))
    delta = np.log(probs[rows, outcome]) - np.log(q[rows, outcome])

    if data.module1 == MODULE1_ELO:
        strength = reconstruct_elo_diff(probs[:, 0], probs[:, 2])
    else:
        strength = (aligned["lambda_home"] - aligned["lambda_away"]).to_numpy(dtype=np.float64)

    status = entry_status_by_team_season(data.df)
    home_status = np.array([status[(s, t)] for s, t in zip(aligned["season"], aligned["HomeTeam"])])
    away_status = np.array([status[(s, t)] for s, t in zip(aligned["season"], aligned["AwayTeam"])])
    flag_new = (home_status == STATUS_NEW) | (away_status == STATUS_NEW)
    flag_returning = (home_status == STATUS_RETURNING) | (away_status == STATUS_RETURNING)

    out = pd.DataFrame(
        {
            "season": aligned["season"].to_numpy(),
            "Date": aligned["Date"].to_numpy(),
            "HomeTeam": aligned["HomeTeam"].to_numpy(),
            "AwayTeam": aligned["AwayTeam"].to_numpy(),
            "role": aligned["role"].to_numpy(),
            "fit_through": aligned["fit_through"].to_numpy(),
            "FTR": aligned["FTR"].astype(str).str.strip().to_numpy(),
            "p_home": probs[:, 0],
            "p_draw": probs[:, 1],
            "p_away": probs[:, 2],
            "odds_source": sources,
            "odds_home": odds[:, 0],
            "odds_draw": odds[:, 1],
            "odds_away": odds[:, 2],
            "q_home": q[:, 0],
            "q_draw": q[:, 1],
            "q_away": q[:, 2],
            "shin_z": z,
            "delta": delta,
            "log_odds_ratio": np.log(odds[:, 0] / odds[:, 2]),
            "market_entropy": compute_shannon_entropy(q),
            STRENGTH_COVARIATES[data.module1]: strength,
            "flag_new": flag_new.astype(np.int64),
            "flag_returning": flag_returning.astype(np.int64),
            "flag_promoted": (flag_new | flag_returning).astype(np.int64),
            "position": aligned.groupby("season", sort=False).cumcount().to_numpy() + 1,
            "model_entropy": compute_shannon_entropy(probs),
        }
    )
    return out[list(module2_frame_columns(data.module1))]
