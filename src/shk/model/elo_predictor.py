"""Modulo per le previsioni Elo walk-forward con regola per le neopromosse."""

from collections.abc import Collection
from itertools import groupby
import re
from typing import Any, Final
import numpy as np
import pandas as pd

from shk.data.walkforward import assert_no_leakage, walkforward_split
from shk.model.elo import davidson_probabilities, elo_delta, elo_update

SEASON_REGEX: Final[re.Pattern] = re.compile(r"^(\d{4})-(\d{2})$")
_CALC_COLS: Final[list[str]] = [
    "Date",
    "season",
    "HomeTeam",
    "AwayTeam",
    "FTR",
    "FTHG",
    "FTAG",
]


def compute_season_standings(matches: pd.DataFrame) -> pd.DataFrame:
    """Calcola la classifica finale di una stagione secondo i criteri ufficiali.

    Criteri di ordinamento decrescente:
    1. Punti (3 per vittoria, 1 per pareggio, 0 per sconfitta)
    2. Differenza reti (gol fatti - gol subiti)
    3. Gol fatti
    4. Nome della squadra in ordine alfabetico crescente

    Parametri
    ---------
    matches : pd.DataFrame
        DataFrame delle partite della stagione, contenente almeno 'HomeTeam',
        'AwayTeam', 'FTHG', 'FTAG'.

    Restituisce
    -----------
    pd.DataFrame
        Classifica con colonne ['team', 'points', 'goal_diff', 'goals_for'],
        ordinata dal primo all'ultimo posto.
    """
    if matches.empty:
        return pd.DataFrame(columns=["team", "points", "goal_diff", "goals_for"])

    teams = sorted(set(matches["HomeTeam"]).union(set(matches["AwayTeam"])))
    points = {t: 0 for t in teams}
    goal_diff = {t: 0 for t in teams}
    goals_for = {t: 0 for t in teams}

    for row in matches.itertuples(index=False):
        h = getattr(row, "HomeTeam")
        a = getattr(row, "AwayTeam")
        fthg = int(getattr(row, "FTHG"))
        ftag = int(getattr(row, "FTAG"))

        goals_for[h] += fthg
        goals_for[a] += ftag
        goal_diff[h] += fthg - ftag
        goal_diff[a] += ftag - fthg

        if fthg > ftag:
            points[h] += 3
        elif fthg < ftag:
            points[a] += 3
        else:
            points[h] += 1
            points[a] += 1

    records = [
        {
            "team": t,
            "points": points[t],
            "goal_diff": goal_diff[t],
            "goals_for": goals_for[t],
        }
        for t in teams
    ]
    df_standings = pd.DataFrame(records)
    df_standings = df_standings.sort_values(
        by=["points", "goal_diff", "goals_for", "team"],
        ascending=[False, False, False, True],
    ).reset_index(drop=True)

    return df_standings


def _parse_season_start_year(season: str) -> int:
    """Valida il formato YYYY-YY e restituisce l'anno iniziale intero."""
    if not isinstance(season, str):
        raise TypeError(f"Season must be a str, got {type(season).__name__}")
    match = SEASON_REGEX.match(season)
    if not match:
        raise ValueError(
            f"Invalid season format: {season!r}, expected 'YYYY-YY'"
        )
    start_year = int(match.group(1))
    end_year = int(match.group(2))
    if (start_year + 1) % 100 != end_year:
        raise ValueError(
            f"Season year continuity mismatch in '{season}': {start_year} -> {end_year}"
        )
    return start_year


def _validate_inputs(
    df: pd.DataFrame,
    seasons_to_predict: Collection[str],
    k: float,
    h: float,
    nu: float,
    s: float,
    initial_rating: float,
) -> None:
    """Valida i tipi e i vincoli di coerenza del DataFrame e dei parametri."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"df must be a pandas DataFrame, got {type(df).__name__}")

    required_cols = {"Date", "season", "HomeTeam", "AwayTeam", "FTR", "FTHG", "FTAG"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required column(s) in df: {sorted(missing)}")

    if not df["Date"].is_monotonic_increasing:
        raise ValueError("DataFrame must be sorted by Date in non-decreasing order")

    # Validazione stagioni non decrescenti lungo l'ordine per Date
    seasons_series = df["season"]
    seen_years: list[int] = []
    current_year = -1
    for s_val in seasons_series:
        year = _parse_season_start_year(s_val)
        if year != current_year:
            if seen_years and year < max(seen_years):
                raise ValueError(
                    f"Season decreases along Date order: got '{s_val}' after a later season"
                )
            seen_years.append(year)
            current_year = year

    # Validazione consecutività delle stagioni presenti nel DataFrame
    unique_seasons = sorted(
        df["season"].unique(), key=lambda s_name: _parse_season_start_year(s_name)
    )
    for i in range(len(unique_seasons) - 1):
        y_curr = _parse_season_start_year(unique_seasons[i])
        y_next = _parse_season_start_year(unique_seasons[i + 1])
        if y_next != y_curr + 1:
            raise ValueError(
                f"Seasons in DataFrame are not consecutive: '{unique_seasons[i]}' followed by '{unique_seasons[i+1]}'"
            )

    # Validazione seasons_to_predict
    if isinstance(seasons_to_predict, str) or not isinstance(
        seasons_to_predict, Collection
    ):
        raise TypeError("seasons_to_predict must be a non-string Collection of strings")

    if any(not isinstance(s_name, str) for s_name in seasons_to_predict):
        raise TypeError("All items in seasons_to_predict must be str")

    if len(seasons_to_predict) == 0:
        raise ValueError("seasons_to_predict cannot be empty")

    missing_target = set(seasons_to_predict) - set(unique_seasons)
    if missing_target:
        raise ValueError(
            f"Seasons to predict not found in DataFrame: {sorted(missing_target)}"
        )

    # Validazione parametri numerici
    if isinstance(k, bool) or not isinstance(k, (int, float, np.integer, np.floating)):
        raise TypeError(f"'k' must be a real number, got {type(k).__name__}")
    if not np.isfinite(k) or k < 0.0:
        raise ValueError(f"'k' must be non-negative and finite, got {k}")

    if isinstance(h, bool) or not isinstance(h, (int, float, np.integer, np.floating)):
        raise TypeError(f"'h' must be a real number, got {type(h).__name__}")
    if not np.isfinite(h):
        raise ValueError(f"'h' must be finite, got {h}")

    if isinstance(nu, bool) or not isinstance(nu, (int, float, np.integer, np.floating)):
        raise TypeError(f"'nu' must be a real number, got {type(nu).__name__}")
    if not np.isfinite(nu) or nu <= 0.0:
        raise ValueError(f"'nu' must be strictly positive and finite, got {nu}")

    if isinstance(s, bool) or not isinstance(s, (int, float, np.integer, np.floating)):
        raise TypeError(f"'s' must be a real number, got {type(s).__name__}")
    if not np.isfinite(s) or s <= 0.0:
        raise ValueError(f"'s' must be strictly positive and finite, got {s}")

    if isinstance(initial_rating, bool) or not isinstance(
        initial_rating, (int, float, np.integer, np.floating)
    ):
        raise TypeError(f"'initial_rating' must be a real number, got {type(initial_rating).__name__}")
    if not np.isfinite(initial_rating):
        raise ValueError(f"'initial_rating' must be finite, got {initial_rating}")


def _get_field(obj: Any, field: str) -> Any:
    """Estrae un campo da un dizionario, pd.Series o NamedTuple senza errori di indicizzazione."""
    if isinstance(obj, dict):
        return obj[field]
    if isinstance(obj, pd.Series):
        return obj[field]
    return getattr(obj, field)


class _EloTracker:
    """Gestore dello stato dei rating Elo e delle regole di ingresso stagionali."""

    def __init__(
        self,
        k: float,
        h: float,
        nu: float,
        s: float = 400.0,
        initial_rating: float = 1500.0,
    ) -> None:
        self.k = float(k)
        self.h = float(h)
        self.nu = float(nu)
        self.s = float(s)
        self.initial_rating = float(initial_rating)

        self.current_ratings: dict[str, float] = {}
        self.last_active_ratings: dict[str, float] = {}
        self.all_seen_teams: set[str] = set()

        self.first_season: str | None = None
        self.current_season: str | None = None
        self.prev_season_teams: set[str] = set()
        self.r_new_current_season: float = self.initial_rating
        self.season_teams_entered: set[str] = set()
        self.team_season_status: dict[tuple[str, str], str] = {}
        self.current_season_matches: list[dict[str, Any]] = []

    def _ensure_season(self, season: str) -> None:
        """Attiva la nuova stagione, calcolando la classifica e R_new della precedente."""
        if self.current_season == season:
            return

        if self.current_season is None:
            # Prima stagione in assoluto del DataFrame
            self.first_season = season
            self.current_season = season
            self.prev_season_teams = set()
            self.r_new_current_season = self.initial_rating
            self.season_teams_entered = set()
            self.current_season_matches = []
        else:
            # Transizione dalla stagione precedente a quella nuova
            df_prev = pd.DataFrame(self.current_season_matches)
            prev_standings_df = compute_season_standings(df_prev)
            prev_teams_ordered = prev_standings_df["team"].tolist()
            relegated_3 = (
                prev_teams_ordered[-3:]
                if len(prev_teams_ordered) >= 3
                else prev_teams_ordered
            )

            # R_new(s) congelato come media dei rating di fine s-1 delle ultime 3
            self.r_new_current_season = float(
                np.mean([self.current_ratings[team] for team in relegated_3])
            )

            # Registra squadre di s-1 e congela l'ultimo rating attivo
            self.prev_season_teams = set(prev_teams_ordered)
            for team in self.prev_season_teams:
                self.last_active_ratings[team] = self.current_ratings[team]
            self.all_seen_teams.update(self.prev_season_teams)

            self.current_season = season
            self.season_teams_entered = set()
            self.current_season_matches = []

    def _register_team_if_needed(self, team: str) -> None:
        """Applica la regola di ingresso squadra per squadra alla prima comparsa nella stagione."""
        assert self.current_season is not None
        if team in self.season_teams_entered:
            return

        if self.current_season == self.first_season:
            # Prima stagione del DataFrame: tutte partono da initial_rating con stato ""
            self.current_ratings[team] = self.initial_rating
            status = ""
        else:
            # Stagioni successive
            if team in self.prev_season_teams:
                # Presente in s - 1: conserva il rating di fine s - 1
                status = ""
            elif team in self.all_seen_teams:
                # Assente in s - 1 ma vista prima: riprende l'ultimo rating che aveva
                self.current_ratings[team] = self.last_active_ratings[team]
                status = "returning"
            else:
                # Mai vista prima: eredita la media delle 3 ultime di s - 1
                self.current_ratings[team] = self.r_new_current_season
                status = "new"

        self.team_season_status[(self.current_season, team)] = status
        self.season_teams_entered.add(team)

    def predict_match(self, match: pd.Series | dict[str, Any]) -> dict[str, Any]:
        """Calcola rating, delta e probabilità 1X2 per una partita prima del suo esito."""
        season = _get_field(match, "season")
        home_team = _get_field(match, "HomeTeam")
        away_team = _get_field(match, "AwayTeam")
        date = _get_field(match, "Date")

        self._ensure_season(season)
        self._register_team_if_needed(home_team)
        self._register_team_if_needed(away_team)

        r_home = self.current_ratings[home_team]
        r_away = self.current_ratings[away_team]
        status_home = self.team_season_status[(season, home_team)]
        status_away = self.team_season_status[(season, away_team)]

        delta = elo_delta(r_home, r_away, h=self.h)
        p_home, p_draw, p_away = davidson_probabilities(delta, nu=self.nu, s=self.s)

        return {
            "season": season,
            "Date": date,
            "HomeTeam": home_team,
            "AwayTeam": away_team,
            "rating_home": r_home,
            "rating_away": r_away,
            "delta": delta,
            "p_home": float(p_home),
            "p_draw": float(p_draw),
            "p_away": float(p_away),
            "home_promotion": status_home,
            "away_promotion": status_away,
        }

    def consume_match(self, match: pd.Series | dict[str, Any]) -> None:
        """Aggiorna i rating con l'esito di una partita conclusa e la memorizza per la classifica."""
        season = _get_field(match, "season")
        home_team = _get_field(match, "HomeTeam")
        away_team = _get_field(match, "AwayTeam")
        ftr = _get_field(match, "FTR")
        fthg = _get_field(match, "FTHG")
        ftag = _get_field(match, "FTAG")

        ftr_str = str(ftr).strip()
        if ftr_str not in ("H", "D", "A"):
            raise ValueError(
                f"Invalid FTR outcome: {ftr!r}. Expected 'H', 'D', or 'A'."
            )

        self._ensure_season(season)
        self._register_team_if_needed(home_team)
        self._register_team_if_needed(away_team)

        r_h = self.current_ratings[home_team]
        r_a = self.current_ratings[away_team]

        new_r_h, new_r_a = elo_update(
            r_h, r_a, outcome=ftr_str, k=self.k, h=self.h, s=self.s
        )
        self.current_ratings[home_team] = new_r_h
        self.current_ratings[away_team] = new_r_a

        self.current_season_matches.append({
            "HomeTeam": home_team,
            "AwayTeam": away_team,
            "FTR": ftr_str,
            "FTHG": int(fthg),
            "FTAG": int(ftag),
        })


def predict_elo_walkforward(
    df: pd.DataFrame,
    seasons_to_predict: Collection[str],
    k: float,
    h: float,
    nu: float,
    s: float = 400.0,
    initial_rating: float = 1500.0,
) -> pd.DataFrame:
    """Genera le previsioni Elo tramite il fornitore walk-forward slice per slice.

    Parametri
    ---------
    df : pd.DataFrame
        DataFrame complessivo contenente storia e partite da prevedere.
    seasons_to_predict : Collection[str]
        Collezione di stagioni da prevedere.
    k : float
        Fattore di aggiornamento Elo non negativo (k >= 0).
    h : float
        Vantaggio campo in punti Elo.
    nu : float
        Parametro pareggio di Davidson, strettamente positivo (nu > 0).
    s : float, opzionale
        Parametro di scala Elo, strettamente positivo (default 400.0).
    initial_rating : float, opzionale
        Rating di partenza per la prima stagione (default 1500.0).

    Restituisce
    -----------
    pd.DataFrame
        Previsioni con le colonne previste dal protocollo.
    """
    _validate_inputs(df, seasons_to_predict, k, h, nu, s, initial_rating)

    tracker = _EloTracker(k=k, h=h, nu=nu, s=s, initial_rating=initial_rating)
    predictions: list[dict[str, Any]] = []
    last_consumed_idx = 0

    for history, match in walkforward_split(df, seasons_to_predict):
        assert_no_leakage(history, match)

        curr_hist_len = len(history)
        if curr_hist_len > last_consumed_idx:
            new_rows = history.iloc[last_consumed_idx:curr_hist_len][_CALC_COLS]
            for row in new_rows.itertuples(index=False):
                tracker.consume_match(row)
            last_consumed_idx = curr_hist_len

        pred = tracker.predict_match(match)
        predictions.append(pred)

    return pd.DataFrame(predictions)


def predict_elo_fast(
    df: pd.DataFrame,
    seasons_to_predict: Collection[str],
    k: float,
    h: float,
    nu: float,
    s: float = 400.0,
    initial_rating: float = 1500.0,
) -> pd.DataFrame:
    """Genera le previsioni Elo tramite passata unica ordinata per data (percorso veloce).

    Tutte le partite di una stessa data vengono previste prima che qualunque partita
    di quella data aggiorni i rating.

    Parametri
    ---------
    df : pd.DataFrame
        DataFrame complessivo contenente storia e partite da prevedere.
    seasons_to_predict : Collection[str]
        Collezione di stagioni da prevedere.
    k : float
        Fattore di aggiornamento Elo non negativo (k >= 0).
    h : float
        Vantaggio campo in punti Elo.
    nu : float
        Parametro pareggio di Davidson, strettamente positivo (nu > 0).
    s : float, opzionale
        Parametro di scala Elo, strettamente positivo (default 400.0).
    initial_rating : float, opzionale
        Rating di partenza per la prima stagione (default 1500.0).

    Restituisce
    -----------
    pd.DataFrame
        Previsioni identiche a quelle del percorso via fornitore.
    """
    _validate_inputs(df, seasons_to_predict, k, h, nu, s, initial_rating)

    target_seasons = set(seasons_to_predict)
    tracker = _EloTracker(k=k, h=h, nu=nu, s=s, initial_rating=initial_rating)
    predictions: list[dict[str, Any]] = []

    sub_df = df[_CALC_COLS]
    for _, group in groupby(sub_df.itertuples(index=False), key=lambda r: r.Date):
        records = list(group)
        # 1. Previsione di tutte le partite della data appartenenti alle stagioni richieste
        for rec in records:
            if rec.season in target_seasons:
                predictions.append(tracker.predict_match(rec))
        # 2. Aggiornamento con tutti i risultati della data
        for rec in records:
            tracker.consume_match(rec)

    return pd.DataFrame(predictions)


def diagnose_season_transitions(df: pd.DataFrame) -> pd.DataFrame:
    """Analizza e riporta le transizioni di stagione, squadre entrate e uscite.

    Parametri
    ---------
    df : pd.DataFrame
        DataFrame ordinato contenente almeno 'season', 'Date', 'HomeTeam', 'AwayTeam',
        'FTHG', 'FTAG'.

    Restituisce
    -----------
    pd.DataFrame
        Riepilogo delle transizioni di stagione con colonne:
        ['season', 'n_teams', 'promoted_new', 'promoted_returning',
         'n_promoted_new', 'n_promoted_returning', 'promoted_total',
         'relegated_actual', 'n_relegated_actual', 'relegated_calculated',
         'relegation_agreement']
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"df must be a pandas DataFrame, got {type(df).__name__}")

    unique_seasons = sorted(
        df["season"].unique(), key=lambda s_name: _parse_season_start_year(s_name)
    )

    rows: list[dict[str, Any]] = []
    all_seen_teams: set[str] = set()
    prev_season_teams: set[str] = set()

    for i, season in enumerate(unique_seasons):
        season_df = df[df["season"] == season]
        current_teams = sorted(
            set(season_df["HomeTeam"]).union(set(season_df["AwayTeam"]))
        )
        n_teams = len(current_teams)

        if i > 0:
            s_prev = unique_seasons[i - 1]
            df_prev = df[df["season"] == s_prev]
            standings_prev = compute_season_standings(df_prev)
            calc_relegated = (
                standings_prev["team"].iloc[-3:].tolist()
                if len(standings_prev) >= 3
                else standings_prev["team"].tolist()
            )

            promoted_new = sorted(t for t in current_teams if t not in all_seen_teams)
            promoted_returning = sorted(
                t for t in current_teams if t not in prev_season_teams and t in all_seen_teams
            )
            n_new = len(promoted_new)
            n_ret = len(promoted_returning)
            promoted_total = n_new + n_ret

            relegated_actual = sorted(t for t in prev_season_teams if t not in current_teams)
            n_rel_actual = len(relegated_actual)
            agreement = len(set(calc_relegated).intersection(set(relegated_actual)))

            rows.append({
                "season": season,
                "n_teams": n_teams,
                "promoted_new": promoted_new,
                "promoted_returning": promoted_returning,
                "n_promoted_new": n_new,
                "n_promoted_returning": n_ret,
                "promoted_total": promoted_total,
                "relegated_actual": relegated_actual,
                "n_relegated_actual": n_rel_actual,
                "relegated_calculated": calc_relegated,
                "relegation_agreement": agreement,
            })

        all_seen_teams.update(current_teams)
        prev_season_teams = set(current_teams)

    return pd.DataFrame(rows)
