"""Modulo per l'audit di copertura di quote, risultati e bookmaker per stagione."""

from collections import defaultdict
from typing import Final, NamedTuple

import numpy as np
import pandas as pd

# Colonne ufficiali del file CSV di copertura
COVERAGE_CSV_COLUMNS: Final[tuple[str, ...]] = (
    "season",
    "group_type",
    "group_name",
    "source",
    "market",
    "timing",
    "columns",
    "total_rows",
    "missing_rows",
    "invalid_rows",
    "complete_rows",
    "is_complete",
)

# Insieme delle colonne non di quota, escluse dall'audit tranne il gruppo dei risultati
NON_ODDS_COLUMNS: Final[frozenset[str]] = frozenset(
    {
        # Identificativi
        "Div",
        "Date",
        "Time",
        "HomeTeam",
        "AwayTeam",
        "season",
        # Risultati finali
        "FTHG",
        "FTAG",
        "FTR",
        # Risultati primo tempo
        "HTHG",
        "HTAG",
        "HTR",
        # Arbitro e statistiche partita
        "Referee",
        "HS",
        "AS",
        "HST",
        "AST",
        "HF",
        "AF",
        "HC",
        "AC",
        "HY",
        "AY",
        "HR",
        "AR",
        "Attendance",
        "HHW",
        "AHW",
        "HO",
        "AO",
        "HBP",
        "ABP",
    }
)

# Ordine convenzionale per i tipi di gruppo
GROUP_TYPE_ORDER: Final[dict[str, int]] = {
    "results": 0,
    "1x2_prematch": 1,
    "1x2_closing": 2,
    "aggregators": 3,
    "other_markets": 4,
}

# Bookmaker noti supportati
_KNOWN_BOOKMAKERS: Final[tuple[str, ...]] = (
    "B365",
    "BS",
    "BW",
    "GB",
    "IW",
    "LB",
    "PS",
    "SB",
    "SJ",
    "SO",
    "SY",
    "VC",
    "WH",
    "P",
)


class ColumnClassification(NamedTuple):
    """Metadati di classificazione di una colonna di quota o mercato.

    Campi
    -----
    group_type : str
        Tipologia macro: '1x2_prematch', '1x2_closing', 'aggregators', 'other_markets'.
    group_name : str
        Identificativo univoco del gruppo di colonne.
    source : str
        Codice del bookmaker, aggregatore ('Bb', 'Max', 'Avg') o 'market'.
    market : str
        Mercato: '1x2', 'over_under_2.5', 'asian_handicap'.
    timing : str
        Fase temporale della quota: 'prematch' o 'closing'.
        Distingue pre-partita e chiusura in tutti i gruppi, aggregatori compresi.
    kind : str
        Natura della colonna: 'odds' (quota), 'line' (valore di handicap), 'count' (conteggio bookmaker).
    """

    group_type: str
    group_name: str
    source: str
    market: str
    timing: str
    kind: str


def classify_column(name: str) -> ColumnClassification:
    """Classifica una colonna di quote o mercati nei rispettivi metadati.

    Il campo `timing` distingue pre-partita ('prematch') e chiusura ('closing')
    in tutti i gruppi, inclusi gli aggregatori (es. MaxCH, AvgCA).
    Le colonne di linea ('line': AHh, AHCh, BbAHh, B365AH, GBAH, LBAH) e di
    conteggio ('count': Bb1X2, BbOU, BbAH) non sono quote moltiplicative e
    vengono marcate con kind appropriato.

    Parametri
    ----------
    name : str
        Nome della colonna da classificare.

    Restituisce
    -----------
    ColumnClassification
        Tupla con group_type, group_name, source, market, timing, kind.

    Solleva
    -------
    ValueError
        Se la colonna e' una colonna non di quota (es. identificativo, statistica)
        oppure non e' riconosciuta dalle regole di classificazione.
    """
    if name in NON_ODDS_COLUMNS:
        raise ValueError(f"Non-odds column cannot be classified as odds: {name}")

    # 1. Aggregatori Betbrain (prefisso Bb)
    if name.startswith("Bb"):
        if name == "Bb1X2":
            return ColumnClassification(
                "aggregators", "bb_1x2_prematch_count", "Bb", "1x2", "prematch", "count"
            )
        if name == "BbOU":
            return ColumnClassification(
                "aggregators",
                "bb_over_under_2.5_prematch_count",
                "Bb",
                "over_under_2.5",
                "prematch",
                "count",
            )
        if name == "BbAH":
            return ColumnClassification(
                "aggregators",
                "bb_asian_handicap_prematch_count",
                "Bb",
                "asian_handicap",
                "prematch",
                "count",
            )
        if name == "BbAHh":
            return ColumnClassification(
                "aggregators",
                "bb_asian_handicap_prematch_line",
                "Bb",
                "asian_handicap",
                "prematch",
                "line",
            )
        if name in {"BbMxH", "BbAvH", "BbMxD", "BbAvD", "BbMxA", "BbAvA"}:
            return ColumnClassification(
                "aggregators", "bb_1x2_prematch", "Bb", "1x2", "prematch", "odds"
            )
        if name in {"BbMx>2.5", "BbAv>2.5", "BbMx<2.5", "BbAv<2.5"}:
            return ColumnClassification(
                "aggregators",
                "bb_over_under_2.5_prematch",
                "Bb",
                "over_under_2.5",
                "prematch",
                "odds",
            )
        if name in {"BbMxAHH", "BbAvAHH", "BbMxAHA", "BbAvAHA"}:
            return ColumnClassification(
                "aggregators",
                "bb_asian_handicap_prematch",
                "Bb",
                "asian_handicap",
                "prematch",
                "odds",
            )
        raise ValueError(f"Unknown Betbrain column: {name}")

    # 2. Aggregatori di mercato Maximum e Average (prefissi Max e Avg)
    if name.startswith(("Max", "Avg")):
        prefix = name[:3]
        rest = name[3:]
        is_closing = rest.startswith("C")
        timing = "closing" if is_closing else "prematch"
        sub = rest[1:] if is_closing else rest

        if sub in {"H", "D", "A"}:
            market = "1x2"
            kind = "odds"
        elif sub in {">2.5", "<2.5"}:
            market = "over_under_2.5"
            kind = "odds"
        elif sub in {"AHH", "AHA"}:
            market = "asian_handicap"
            kind = "odds"
        else:
            raise ValueError(f"Unknown aggregator column: {name}")

        group_name = f"{prefix.lower()}_{market}_{timing}"
        return ColumnClassification("aggregators", group_name, prefix, market, timing, kind)

    # 3. Linee di mercato generali
    if name == "AHh":
        return ColumnClassification(
            "other_markets",
            "market_asian_handicap_prematch_line",
            "market",
            "asian_handicap",
            "prematch",
            "line",
        )
    if name == "AHCh":
        return ColumnClassification(
            "other_markets",
            "market_asian_handicap_closing_line",
            "market",
            "asian_handicap",
            "closing",
            "line",
        )

    # 4. Linee handicap specifiche per bookmaker
    if name in {"B365AH", "GBAH", "LBAH"}:
        bm = name[:-2]
        return ColumnClassification(
            "other_markets",
            f"{bm.lower()}_asian_handicap_prematch_line",
            bm,
            "asian_handicap",
            "prematch",
            "line",
        )

    # 5. Singoli bookmaker
    for bm in _KNOWN_BOOKMAKERS:
        if name.startswith(bm):
            rest = name[len(bm) :]
            if rest.startswith("C"):
                timing = "closing"
                sub = rest[1:]
            else:
                timing = "prematch"
                sub = rest

            if sub in {"H", "D", "A"}:
                market = "1x2"
                kind = "odds"
                group_type = "1x2_closing" if timing == "closing" else "1x2_prematch"
            elif sub in {">2.5", "<2.5"}:
                market = "over_under_2.5"
                kind = "odds"
                group_type = "other_markets"
            elif sub in {"AHH", "AHA"}:
                market = "asian_handicap"
                kind = "odds"
                group_type = "other_markets"
            else:
                continue

            group_name = f"{bm.lower()}_{market}_{timing}"
            return ColumnClassification(group_type, group_name, bm, market, timing, kind)

    raise ValueError(f"Unknown column cannot be classified: {name}")


def compute_coverage(df: pd.DataFrame) -> pd.DataFrame:
    """Calcola l'audit di copertura per stagione e per gruppo di colonne.

    Per ciascuna stagione caricata:
    1. Verifica e computa la copertura del gruppo dei risultati ('FTHG', 'FTAG', 'FTR').
    2. Raggruppa tutte le colonne di quote e mercati presenti in base a
       (group_type, group_name, source, market, timing, kind).
    3. Un gruppo e' considerato presente nella stagione se almeno una sua colonna
       ha almeno un valore non nullo nelle righe di quella stagione.
    4. Per ogni riga:
       - mancante: almeno una colonna del gruppo e' nulla (NaN).
       - non valida (solo per kind='odds'): almeno un valore non nullo e' non numerico,
         non finito o <= 1.0. Per kind in {'line', 'count'}, invalid_rows vale 0.
       - completa: ne' mancante ne' non valida.
       - is_complete: 'True' se complete_rows == total_rows, altrimenti 'False'.

    Parametri
    ----------
    df : pd.DataFrame
        DataFrame consolidato restituito da load_all_seasons().

    Restituisce
    -----------
    pd.DataFrame
        DataFrame in formato lungo contenente le colonne specificate in COVERAGE_CSV_COLUMNS,
        ordinato per season, group_type (results, 1x2_prematch, 1x2_closing, aggregators,
        other_markets) e group_name.
    """
    if "season" not in df.columns:
        raise ValueError("DataFrame missing required 'season' column")

    # Mappatura delle colonne presenti nel DataFrame in gruppi
    odds_columns = [c for c in df.columns if c not in NON_ODDS_COLUMNS]
    group_map: dict[tuple[str, str, str, str, str, str], list[str]] = defaultdict(list)
    for c in odds_columns:
        info = classify_column(c)
        group_key = (
            info.group_type,
            info.group_name,
            info.source,
            info.market,
            info.timing,
            info.kind,
        )
        group_map[group_key].append(c)

    rows: list[dict[str, object]] = []

    # Iterazione per stagione in ordine stabile/cronologico
    seasons = sorted(df["season"].unique())

    for season in seasons:
        season_df = df[df["season"] == season]
        total_rows = len(season_df)

        # 1. Audit del gruppo Risultati
        has_results = all(c in season_df.columns for c in ("FTHG", "FTAG", "FTR"))
        if has_results:
            missing_mask = (
                season_df["FTHG"].isna()
                | season_df["FTAG"].isna()
                | season_df["FTR"].isna()
            )

            fthg_num = pd.to_numeric(season_df["FTHG"], errors="coerce")
            ftag_num = pd.to_numeric(season_df["FTAG"], errors="coerce")
            ftr_str = season_df["FTR"].astype(str).str.strip()

            invalid_mask = (~missing_mask) & (
                fthg_num.isna()
                | (fthg_num < 0)
                | (fthg_num % 1 != 0)
                | ftag_num.isna()
                | (ftag_num < 0)
                | (ftag_num % 1 != 0)
                | (~ftr_str.isin(["H", "D", "A"]))
                | ((fthg_num > ftag_num) & (ftr_str != "H"))
                | ((fthg_num == ftag_num) & (ftr_str != "D"))
                | ((fthg_num < ftag_num) & (ftr_str != "A"))
            )

            complete_mask = (~missing_mask) & (~invalid_mask)
            missing_count = int(missing_mask.sum())
            invalid_count = int(invalid_mask.sum())
            complete_count = int(complete_mask.sum())

            rows.append(
                {
                    "season": season,
                    "group_type": "results",
                    "group_name": "results",
                    "source": "",
                    "market": "",
                    "timing": "",
                    "columns": "FTHG FTAG FTR",
                    "total_rows": total_rows,
                    "missing_rows": missing_count,
                    "invalid_rows": invalid_count,
                    "complete_rows": complete_count,
                    "is_complete": "True" if complete_count == total_rows else "False",
                }
            )

        # 2. Audit dei gruppi di quote e mercati
        for group_key, cols in group_map.items():
            g_type, g_name, g_source, g_market, g_timing, g_kind = group_key

            # Presenza: almeno una colonna del gruppo ha almeno un valore non nullo nella stagione
            is_present = any(
                c in season_df.columns and season_df[c].notna().any() for c in cols
            )
            if not is_present:
                continue

            # Calcolo maschera righe mancanti
            missing_mask = pd.Series(False, index=season_df.index)
            for c in cols:
                if c in season_df.columns:
                    missing_mask |= season_df[c].isna()
                else:
                    missing_mask = pd.Series(True, index=season_df.index)

            # Calcolo maschera righe non valide
            invalid_mask = pd.Series(False, index=season_df.index)
            if g_kind == "odds":
                for c in cols:
                    if c in season_df.columns:
                        s = season_df[c]
                        s_num = pd.to_numeric(s, errors="coerce")
                        col_invalid = (s.notna() & s_num.isna()) | (
                            s_num.notna() & ((s_num <= 1.0) | ~np.isfinite(s_num))
                        )
                        invalid_mask |= col_invalid

            complete_mask = (~missing_mask) & (~invalid_mask)
            missing_count = int(missing_mask.sum())
            invalid_count = int(invalid_mask.sum())
            complete_count = int(complete_mask.sum())

            rows.append(
                {
                    "season": season,
                    "group_type": g_type,
                    "group_name": g_name,
                    "source": g_source,
                    "market": g_market,
                    "timing": g_timing,
                    "columns": " ".join(cols),
                    "total_rows": total_rows,
                    "missing_rows": missing_count,
                    "invalid_rows": invalid_count,
                    "complete_rows": complete_count,
                    "is_complete": "True" if complete_count == total_rows else "False",
                }
            )

    coverage_df = pd.DataFrame(rows, columns=COVERAGE_CSV_COLUMNS)

    # Ordinamento: season, group_type, group_name
    coverage_df["_type_order"] = coverage_df["group_type"].map(GROUP_TYPE_ORDER)
    coverage_df = (
        coverage_df.sort_values(
            ["season", "_type_order", "group_name"], kind="stable"
        )
        .drop(columns=["_type_order"])
        .reset_index(drop=True)
    )

    return coverage_df
