"""Modulo per il fornitore walk-forward e i controlli anti-leakage."""

import functools
from collections.abc import Collection, Iterator
from typing import Final

import numpy as np
import pandas as pd

from shk.data.coverage import NON_ODDS_COLUMNS, classify_column

# Identificativi ammessi nella whitelist pre-partita
PREMATCH_IDENTIFIERS: Final[frozenset[str]] = frozenset(
    {"Div", "Date", "Time", "HomeTeam", "AwayTeam", "season"}
)


class LeakageError(RuntimeError):
    """Eccezione sollevata quando viene rilevato data leakage temporale o di contenuto."""


@functools.lru_cache(maxsize=128)
def _cached_prematch_whitelist(columns: tuple[str, ...]) -> tuple[str, ...]:
    whitelist: list[str] = []
    for c in columns:
        if c in PREMATCH_IDENTIFIERS:
            whitelist.append(c)
        elif c in NON_ODDS_COLUMNS:
            continue
        else:
            cls = classify_column(c)
            if cls.kind == "odds" and cls.timing == "prematch":
                whitelist.append(c)
    return tuple(whitelist)


def get_prematch_whitelist(columns: Collection[str]) -> tuple[str, ...]:
    """Costruisce per inclusione esplicita la whitelist dei campi pre-partita ammessi.

    Include unicamente gli identificativi di partita ammessi (Div, Date, Time, HomeTeam,
    AwayTeam, season) e le quote moltiplicative con kind='odds' e timing='prematch'.
    Esclude tutti i risultati, tempi parziali, statistiche, arbitro, quote di chiusura
    (closing), linee di handicap (line) e conteggi (count).

    Parametri
    ----------
    columns : Collection[str]
        Insieme o sequenza dei nomi di colonna da filtrare.

    Restituisce
    -----------
    tuple[str, ...]
        Tupla ordinata delle colonne ammesse secondo l'ordine in cui compaiono in columns.
    """
    return _cached_prematch_whitelist(tuple(columns))


def check_leakage(
    history: pd.DataFrame,
    match: pd.Series,
    whitelist: Collection[str] | None = None,
) -> list[str]:
    """Verifica l'assenza di violazioni di leakage temporale o di contenuto.

    Parametri
    ----------
    history : pd.DataFrame
        DataFrame delle partite storiche fornite per prevedere la partita corrente.
    match : pd.Series
        Serie rappresentante la singola partita da prevedere.
    whitelist : Collection[str] o None, opzionale
        Insieme delle colonne ammesse nella partita. Se None (predefinito), viene
        calcolato dinamicamente tramite get_prematch_whitelist(history.columns).

    Restituisce
    -----------
    list[str]
        Lista delle descrizioni testuali delle violazioni riscontrate (vuota se nessuna).
    """
    effective_whitelist = (
        set(whitelist)
        if whitelist is not None
        else set(get_prematch_whitelist(history.columns))
    )

    violations: list[str] = []
    has_history = len(history) > 0

    # 1. Controllo temporale: nessuna partita con data >= data della partita da prevedere
    history_has_future_or_same = False
    if has_history and "Date" in history.columns and "Date" in match.index:
        history_max_date = history["Date"].max()
        match_date = match["Date"]
        if history_max_date >= match_date:
            history_has_future_or_same = True
            violations.append(
                f"Temporal leakage: history contains dates >= match Date ({match_date})"
            )

    # 2. Controllo identita': la partita stessa non deve comparire nella storia
    id_cols = ("Date", "HomeTeam", "AwayTeam")
    if (
        has_history
        and history_has_future_or_same
        and all(c in history.columns for c in id_cols)
        and all(c in match.index for c in id_cols)
    ):
        same_match_mask = (
            (history["Date"] == match["Date"])
            & (history["HomeTeam"] == match["HomeTeam"])
            & (history["AwayTeam"] == match["AwayTeam"])
        )
        if same_match_mask.any():
            violations.append("Identity leakage: match itself is present in history")

    # 3. Controllo colonne: nessun campo non consentito nella partita da prevedere
    match_cols = set(match.index)
    forbidden_cols = match_cols - effective_whitelist
    if forbidden_cols:
        violations.append(
            f"Forbidden columns in match: {sorted(forbidden_cols)}"
        )

    return violations


def assert_no_leakage(
    history: pd.DataFrame,
    match: pd.Series,
    whitelist: Collection[str] | None = None,
) -> None:
    """Verifica l'assenza di leakage e solleva LeakageError in caso di violazioni.

    Parametri
    ----------
    history : pd.DataFrame
        DataFrame delle partite storiche fornite per la previsione.
    match : pd.Series
        Serie della partita da prevedere.
    whitelist : Collection[str] o None, opzionale
        Insieme delle colonne consentite. Se None, calcolato da history.columns.

    Solleva
    -------
    LeakageError
        Se viene rilevata almeno una violazione di leakage.
    """
    violations = check_leakage(history, match, whitelist=whitelist)
    if violations:
        raise LeakageError("; ".join(violations))


def walkforward_split(
    df: pd.DataFrame,
    seasons_to_predict: Collection[str],
) -> Iterator[tuple[pd.DataFrame, pd.Series]]:
    """Genera iterativamente le coppie (storia, partita) in modalita' walk-forward.

    Per ciascuna partita appartenente a una delle stagioni specificate in
    seasons_to_predict, restituisce la tupla (storia, partita).
    La storia e' una slice di df contenente tutte le partite con Date strettamente
    anteriore (Date < match_date): chi la riceve non deve modificarla.
    La partita e' una Series ristretta esclusivamente ai campi ammessi nella
    whitelist pre-partita determinata a monte da df.columns.

    Parametri
    ----------
    df : pd.DataFrame
        DataFrame complessivo contenente almeno le colonne 'Date' e 'season',
        ordinato per Date in modo non decrescente.
    seasons_to_predict : Collection[str]
        Collezione non stringa di stringhe identificanti le stagioni da prevedere.

    Restituisce
    -----------
    Iterator[tuple[pd.DataFrame, pd.Series]]
        Generatore delle coppie (history, match).

    Solleva
    -------
    TypeError
        Se df non e' DataFrame, o se seasons_to_predict e' una stringa, non e'
        una Collection o contiene elementi non stringa.
    ValueError
        Se Date o season mancano, se Date non e' ordinato, se seasons_to_predict e'
        vuoto o se contiene stagioni non presenti in df.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")

    if "Date" not in df.columns or "season" not in df.columns:
        raise ValueError("Missing required columns: Date, season")

    if not df["Date"].is_monotonic_increasing:
        raise ValueError("DataFrame must be sorted by Date")

    if isinstance(seasons_to_predict, str) or not isinstance(
        seasons_to_predict, Collection
    ):
        raise TypeError("seasons_to_predict must be a non-string Collection of strings")

    if any(not isinstance(s, str) for s in seasons_to_predict):
        raise TypeError("All items in seasons_to_predict must be str")

    if len(seasons_to_predict) == 0:
        raise ValueError("seasons_to_predict cannot be empty")

    df_seasons = set(df["season"].unique())
    missing_seasons = set(seasons_to_predict) - df_seasons
    if missing_seasons:
        raise ValueError(
            f"Seasons not found in DataFrame: {sorted(missing_seasons)}"
        )

    target_seasons = set(seasons_to_predict)
    whitelist_cols = list(get_prematch_whitelist(df.columns))
    df_whitelist = df[whitelist_cols]
    dates = df["Date"].to_numpy()

    for idx in range(len(df)):
        season_val = df["season"].iloc[idx]
        if season_val not in target_seasons:
            continue

        match_date = dates[idx]
        cutoff = int(np.searchsorted(dates, match_date, side="left"))
        history = df.iloc[:cutoff]
        match = df_whitelist.iloc[idx]
        yield history, match
