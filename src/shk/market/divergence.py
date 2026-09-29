"""Modulo per l'analisi della divergenza fra metodi di de-vigging per fascia di quota."""

from collections.abc import Sequence
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from shk.data.split import DEFAULT_SPLIT_CONFIG_PATH, SplitConfig, read_split_config
from shk.market.devig import (
    devig_additive,
    devig_power,
    devig_proportional,
    overround,
)

# Fasce di quota standard della story (estremo sinistro incluso, estremo destro escluso)
ODDS_BINS: Final[tuple[float, ...]] = (1.0, 1.5, 2.0, 3.0, 5.0, 10.0, float("inf"))
ODDS_BIN_LABELS: Final[tuple[str, ...]] = (
    "[1, 1.5)",
    "[1.5, 2)",
    "[2, 3)",
    "[3, 5)",
    "[5, 10)",
    "[10, inf)",
)

# Edge di riferimento della story S1 (2 punti percentuali = 0.02)
REFERENCE_EDGE: Final[float] = 0.02

# Colonne delle quote Bet365 pre-partita
B365_ODDS_COLUMNS: Final[tuple[str, ...]] = ("B365H", "B365D", "B365A")

# Colonne ufficiali del file CSV di divergenza
# Unita' di misura:
# - mean_overround: frazione adimensionale (es. 0.053 = 5.3%)
# - *_spread_pts: punti percentuali ((max(q) - min(q)) * 100)
# - mean_relative_spread: rapporto adimensionale ((max(q) - min(q)) / mean(q))
# - *_spread_ratio_to_edge: rapporto adimensionale rispetto a REFERENCE_EDGE (spread_prob / 0.02)
DIVERGENCE_CSV_COLUMNS: Final[tuple[str, ...]] = (
    "level",
    "category",
    "n_outcomes",
    "matches_used",
    "matches_excluded",
    "additive_nan_matches",
    "mean_overround",
    "mean_q_proportional",
    "mean_q_additive",
    "mean_q_power",
    "mean_spread_pts",
    "p99_spread_pts",
    "max_spread_pts",
    "mean_relative_spread",
    "max_spread_ratio_to_edge",
    "p99_spread_ratio_to_edge",
    "max_abs_sum_error_proportional",
    "max_abs_sum_error_additive",
    "max_abs_sum_error_power",
)


def assign_odds_bin(odd: float) -> str:
    """Assegna una quota decimale alla corrispondente fascia di mercato [a, b).

    Parametri
    ----------
    odd : float
        Quota decimale maggiore o uguale a 1.0.

    Restituisce
    -----------
    str
        Etichetta della fascia di quota.
    """
    if odd < 1.0 or not np.isfinite(odd):
        raise ValueError(f"Invalid odd value for bin assignment: {odd}")

    if odd < 1.5:
        return "[1, 1.5)"
    if odd < 2.0:
        return "[1.5, 2)"
    if odd < 3.0:
        return "[2, 3)"
    if odd < 5.0:
        return "[3, 5)"
    if odd < 10.0:
        return "[5, 10)"
    return "[10, inf)"


def compute_divergence_table(
    df: pd.DataFrame,
    seasons_order: Sequence[str],
) -> pd.DataFrame:
    """Calcola la tabella di divergenza fra i metodi di de-vigging.

    Parametri
    ----------
    df : pd.DataFrame
        DataFrame consolidato delle partite di training e validazione,
        contenente almeno le colonne 'season', 'B365H', 'B365D', 'B365A'.
    seasons_order : Sequence[str]
        Sequenza ordinata delle stagioni da includere nel livello 'season'.

    Restituisce
    -----------
    pd.DataFrame
        DataFrame contenente le colonne definite in DIVERGENCE_CSV_COLUMNS,
        con righe per fascia (level='bin'), per stagione (level='season') e
        la riga complessiva (level='overall').
    """
    # Strutture dati per aggregazione per fascia
    bin_q_prop: dict[str, list[float]] = {b: [] for b in ODDS_BIN_LABELS}
    bin_q_add: dict[str, list[float]] = {b: [] for b in ODDS_BIN_LABELS}
    bin_q_pow: dict[str, list[float]] = {b: [] for b in ODDS_BIN_LABELS}
    bin_spread_pts: dict[str, list[float]] = {b: [] for b in ODDS_BIN_LABELS}
    bin_rel_spread: dict[str, list[float]] = {b: [] for b in ODDS_BIN_LABELS}

    # Strutture dati per statistiche per stagione
    season_rows: list[dict[str, object]] = []

    # Statistiche complessive sulle partite usate
    all_usable_spreads_pts: list[float] = []
    all_usable_overrounds: list[float] = []
    max_err_prop = 0.0
    max_err_add = 0.0
    max_err_pow = 0.0
    total_matches_used = 0
    total_matches_excluded = 0
    total_additive_nan_matches = 0

    for s in seasons_order:
        df_season = df[df["season"] == s]
        total_season_matches = len(df_season)

        if total_season_matches == 0:
            season_rows.append(
                {
                    "level": "season",
                    "category": s,
                    "n_outcomes": "",
                    "matches_used": 0,
                    "matches_excluded": 0,
                    "additive_nan_matches": 0,
                    "mean_overround": "",
                    "mean_q_proportional": "",
                    "mean_q_additive": "",
                    "mean_q_power": "",
                    "mean_spread_pts": "",
                    "p99_spread_pts": "",
                    "max_spread_pts": "",
                    "mean_relative_spread": "",
                    "max_spread_ratio_to_edge": "",
                    "p99_spread_ratio_to_edge": "",
                    "max_abs_sum_error_proportional": "",
                    "max_abs_sum_error_additive": "",
                    "max_abs_sum_error_power": "",
                }
            )
            continue

        # Verifica presenza e validita' delle colonne B365
        has_cols = all(c in df_season.columns for c in B365_ODDS_COLUMNS)
        if not has_cols:
            season_rows.append(
                {
                    "level": "season",
                    "category": s,
                    "n_outcomes": "",
                    "matches_used": 0,
                    "matches_excluded": total_season_matches,
                    "additive_nan_matches": 0,
                    "mean_overround": "",
                    "mean_q_proportional": "",
                    "mean_q_additive": "",
                    "mean_q_power": "",
                    "mean_spread_pts": "",
                    "p99_spread_pts": "",
                    "max_spread_pts": "",
                    "mean_relative_spread": "",
                    "max_spread_ratio_to_edge": "",
                    "p99_spread_ratio_to_edge": "",
                    "max_abs_sum_error_proportional": "",
                    "max_abs_sum_error_additive": "",
                    "max_abs_sum_error_power": "",
                }
            )
            total_matches_excluded += total_season_matches
            continue

        # Validazione riga per riga delle quote
        h_s = pd.to_numeric(df_season["B365H"], errors="coerce")
        d_s = pd.to_numeric(df_season["B365D"], errors="coerce")
        a_s = pd.to_numeric(df_season["B365A"], errors="coerce")

        valid_mask = (
            h_s.notna()
            & np.isfinite(h_s)
            & (h_s > 1.0)
            & d_s.notna()
            & np.isfinite(d_s)
            & (d_s > 1.0)
            & a_s.notna()
            & np.isfinite(a_s)
            & (a_s > 1.0)
        )

        n_excluded = int(np.sum(~valid_mask))
        total_matches_excluded += n_excluded

        n_valid = int(np.sum(valid_mask))
        if n_valid == 0:
            season_rows.append(
                {
                    "level": "season",
                    "category": s,
                    "n_outcomes": "",
                    "matches_used": 0,
                    "matches_excluded": total_season_matches,
                    "additive_nan_matches": 0,
                    "mean_overround": "",
                    "mean_q_proportional": "",
                    "mean_q_additive": "",
                    "mean_q_power": "",
                    "mean_spread_pts": "",
                    "p99_spread_pts": "",
                    "max_spread_pts": "",
                    "mean_relative_spread": "",
                    "max_spread_ratio_to_edge": "",
                    "p99_spread_ratio_to_edge": "",
                    "max_abs_sum_error_proportional": "",
                    "max_abs_sum_error_additive": "",
                    "max_abs_sum_error_power": "",
                }
            )
            continue

        # Estrazione matrice quote valide
        valid_h = h_s[valid_mask].to_numpy(dtype=np.float64)
        valid_d = d_s[valid_mask].to_numpy(dtype=np.float64)
        valid_a = a_s[valid_mask].to_numpy(dtype=np.float64)
        odds = np.column_stack([valid_h, valid_d, valid_a])

        # Calcolo dei metodi di de-vigging
        ovr = overround(odds)
        qp = devig_proportional(odds)
        qa = devig_additive(odds)
        qpow, _ = devig_power(odds)

        # Rilevamento mercati con additivo non applicabile (NaN)
        nan_add_mask = np.isnan(qa[:, 0])
        n_nan_add = int(np.sum(nan_add_mask))
        total_additive_nan_matches += n_nan_add

        # Partite usate = quote valide E additivo applicabile
        usable_mask = ~nan_add_mask
        n_used = int(np.sum(usable_mask))
        total_matches_used += n_used

        if n_used == 0:
            season_rows.append(
                {
                    "level": "season",
                    "category": s,
                    "n_outcomes": "",
                    "matches_used": 0,
                    "matches_excluded": n_excluded,
                    "additive_nan_matches": n_nan_add,
                    "mean_overround": "",
                    "mean_q_proportional": "",
                    "mean_q_additive": "",
                    "mean_q_power": "",
                    "mean_spread_pts": "",
                    "p99_spread_pts": "",
                    "max_spread_pts": "",
                    "mean_relative_spread": "",
                    "max_spread_ratio_to_edge": "",
                    "p99_spread_ratio_to_edge": "",
                    "max_abs_sum_error_proportional": "",
                    "max_abs_sum_error_additive": "",
                    "max_abs_sum_error_power": "",
                }
            )
            continue

        # Filtraggio sulle sole partite usate
        usable_odds = odds[usable_mask]
        usable_ovr = ovr[usable_mask]
        usable_qp = qp[usable_mask]
        usable_qa = qa[usable_mask]
        usable_qpow = qpow[usable_mask]

        season_mean_ovr = float(np.mean(usable_ovr))
        all_usable_overrounds.extend(usable_ovr.tolist())

        # Errori massimi di somma
        err_p = np.max(np.abs(usable_qp.sum(axis=1) - 1.0))
        err_a = np.max(np.abs(usable_qa.sum(axis=1) - 1.0))
        err_pow = np.max(np.abs(usable_qpow.sum(axis=1) - 1.0))
        max_err_prop = max(max_err_prop, float(err_p))
        max_err_add = max(max_err_add, float(err_a))
        max_err_pow = max(max_err_pow, float(err_pow))

        season_rows.append(
            {
                "level": "season",
                "category": s,
                "n_outcomes": "",
                "matches_used": n_used,
                "matches_excluded": n_excluded,
                "additive_nan_matches": n_nan_add,
                "mean_overround": season_mean_ovr,
                "mean_q_proportional": "",
                "mean_q_additive": "",
                "mean_q_power": "",
                "mean_spread_pts": "",
                "p99_spread_pts": "",
                "max_spread_pts": "",
                "mean_relative_spread": "",
                "max_spread_ratio_to_edge": "",
                "p99_spread_ratio_to_edge": "",
                "max_abs_sum_error_proportional": "",
                "max_abs_sum_error_additive": "",
                "max_abs_sum_error_power": "",
            }
        )

        # Assegnazione di ciascun esito alle fasce di quota
        for i in range(n_used):
            for j in range(3):
                o_val = usable_odds[i, j]
                b_label = assign_odds_bin(o_val)
                p_val = usable_qp[i, j]
                a_val = usable_qa[i, j]
                pow_val = usable_qpow[i, j]

                spread_prob = max(p_val, a_val, pow_val) - min(p_val, a_val, pow_val)
                spread_pts = spread_prob * 100.0
                mean_q = (p_val + a_val + pow_val) / 3.0
                rel_spread = spread_prob / mean_q

                bin_q_prop[b_label].append(p_val)
                bin_q_add[b_label].append(a_val)
                bin_q_pow[b_label].append(pow_val)
                bin_spread_pts[b_label].append(spread_pts)
                bin_rel_spread[b_label].append(rel_spread)

                all_usable_spreads_pts.append(spread_pts)

    # Costruzione righe di livello 'bin'
    bin_rows: list[dict[str, object]] = []
    for b in ODDS_BIN_LABELS:
        n_out = len(bin_spread_pts[b])
        if n_out > 0:
            arr_spreads = np.array(bin_spread_pts[b])
            m_spread = float(np.mean(arr_spreads))
            p99_spread = float(np.percentile(arr_spreads, 99, method="linear"))
            max_spread = float(np.max(arr_spreads))
            m_rel_spread = float(np.mean(bin_rel_spread[b]))
            m_qp = float(np.mean(bin_q_prop[b]))
            m_qa = float(np.mean(bin_q_add[b]))
            m_qpow = float(np.mean(bin_q_pow[b]))

            bin_rows.append(
                {
                    "level": "bin",
                    "category": b,
                    "n_outcomes": n_out,
                    "matches_used": "",
                    "matches_excluded": "",
                    "additive_nan_matches": "",
                    "mean_overround": "",
                    "mean_q_proportional": m_qp,
                    "mean_q_additive": m_qa,
                    "mean_q_power": m_qpow,
                    "mean_spread_pts": m_spread,
                    "p99_spread_pts": p99_spread,
                    "max_spread_pts": max_spread,
                    "mean_relative_spread": m_rel_spread,
                    "max_spread_ratio_to_edge": "",
                    "p99_spread_ratio_to_edge": "",
                    "max_abs_sum_error_proportional": "",
                    "max_abs_sum_error_additive": "",
                    "max_abs_sum_error_power": "",
                }
            )
        else:
            bin_rows.append(
                {
                    "level": "bin",
                    "category": b,
                    "n_outcomes": 0,
                    "matches_used": "",
                    "matches_excluded": "",
                    "additive_nan_matches": "",
                    "mean_overround": "",
                    "mean_q_proportional": "",
                    "mean_q_additive": "",
                    "mean_q_power": "",
                    "mean_spread_pts": "",
                    "p99_spread_pts": "",
                    "max_spread_pts": "",
                    "mean_relative_spread": "",
                    "max_spread_ratio_to_edge": "",
                    "p99_spread_ratio_to_edge": "",
                    "max_abs_sum_error_proportional": "",
                    "max_abs_sum_error_additive": "",
                    "max_abs_sum_error_power": "",
                }
            )

    # Costruzione riga complessiva 'overall'
    if total_matches_used > 0:
        all_spreads_arr = np.array(all_usable_spreads_pts)
        overall_mean_ovr: float | str = float(np.mean(all_usable_overrounds))
        overall_p99_pts: float | str = float(
            np.percentile(all_spreads_arr, 99, method="linear")
        )
        overall_max_pts: float | str = float(np.max(all_spreads_arr))

        # Rapporti con l'edge di 2 punti (spread in probabilita' / 0.02 = spread in punti / 2.0)
        max_ratio: float | str = (overall_max_pts / 100.0) / REFERENCE_EDGE
        p99_ratio: float | str = (overall_p99_pts / 100.0) / REFERENCE_EDGE
        err_prop: float | str = max_err_prop
        err_add: float | str = max_err_add
        err_pow: float | str = max_err_pow
    else:
        overall_mean_ovr = ""
        overall_p99_pts = ""
        overall_max_pts = ""
        max_ratio = ""
        p99_ratio = ""
        err_prop = ""
        err_add = ""
        err_pow = ""

    overall_row = {
        "level": "overall",
        "category": "all",
        "n_outcomes": "",
        "matches_used": total_matches_used,
        "matches_excluded": total_matches_excluded,
        "additive_nan_matches": total_additive_nan_matches,
        "mean_overround": overall_mean_ovr,
        "mean_q_proportional": "",
        "mean_q_additive": "",
        "mean_q_power": "",
        "mean_spread_pts": "",
        "p99_spread_pts": overall_p99_pts,
        "max_spread_pts": overall_max_pts,
        "mean_relative_spread": "",
        "max_spread_ratio_to_edge": max_ratio,
        "p99_spread_ratio_to_edge": p99_ratio,
        "max_abs_sum_error_proportional": err_prop,
        "max_abs_sum_error_additive": err_add,
        "max_abs_sum_error_power": err_pow,
    }

    all_rows = bin_rows + season_rows + [overall_row]
    return pd.DataFrame(all_rows, columns=DIVERGENCE_CSV_COLUMNS)
