"""ĝ formalizzato: intervalli, placebo, finestre, fasce di quota e soglia ln π (T57).

Serie e metodi di C4.2 e T43: b365_prematch (19 stagioni di validazione) e pinnacle_closing
(10 stagioni dal 2012-13), cinque metodi di de-vigging. Termini per partita
g_t = ln p̂_t(x_t) − ln q_t(x_t) (scoring.compute_g_hat_terms); ĝ = media dei termini.

Intervalli al 95% (percentili, B = 999):
- per stagione: stationary bootstrap della serie dei termini della stagione, lunghezza media
  L_PW stationary della serie stessa (decisione S7), e versione iid (L = 1);
- pooled: bootstrap a due livelli, stagioni ricampionate con reinserimento come cluster e,
  dentro ciascuna, la serie ricampionata come sopra; ĝ pooled = media di tutti i termini,
  come in C4.2. Intervallo principale con la correzione per il numero di cluster (decisione
  del programmatore del 2026-10-12, la stessa di T56): ĝ ± t_{0.975, S−1}·√(S/(S − 1))·se_boot,
  con S il numero di stagioni della serie; il percentile resta come secondario.

Placebo (nota 2.8 §9.3): l'intera pipeline del Modulo 1 (previsioni walk-forward con i
parametri congelati ELO_FITS, allineamento, de-vigging) si riesegue su dati con gli esiti
(FTR, FTHG, FTAG insieme) permutati a caso dentro ciascuna stagione, tutte le stagioni non di
test; si ricalcola ĝ per stagione, serie e metodo. Le quote, quindi q, non cambiano.

Finestre: ĝ su finestre mobili di 80 partite consecutive dentro la stagione (passo 1), la W
del Modulo 2. Fasce di quota: fasce di divergence.py (ODDS_BIN_LABELS) sulla quota della
favorita della partita (minima delle tre), caratteristica pre-partita.

Soglia (nota 2.4 §8): ĝ > ln π, con π = Σ_i 1/o_i della partita; si confronta ĝ con la media
di ln π sulle partite, per stagione e pooled.

Seed: SeedSequence(SEED_S10).spawn(5)[2] (T57 in posizione 2), spawn(3): figlio 0 per gli
intervalli (spawn per serie × metodo, poi per stagione), figlio 1 per le permutazioni del
placebo, figlio 2 per la verifica di copertura su AR(1).
"""

import math
from collections.abc import Sequence
from typing import Final, NamedTuple

import numpy as np
import pandas as pd

from shk.data.split import read_split_config
from shk.market.divergence import ODDS_BIN_LABELS, assign_odds_bin
from shk.model.elo_fit import ELO_FITS, derive_fit_schedule, parse_season_start_year
from shk.model.comparisons import t_cluster_interval
from shk.model.module3_synthetic import N_STORY_TASKS
from shk.model.residuals import load_match_frame
from shk.model.scoring import (
    ALL_DEVIG_METHODS,
    SERIES_NAMES,
    SeriesEvaluationData,
    align_predictions_with_odds,
    compute_g_hat_terms,
    generate_validation_predictions,
    prepare_series_evaluation,
)
from shk.model.validation_run import SEED_S10
from shk.stats.bootstrap import (
    optimal_block_length,
    round_block_length,
    stationary_bootstrap_indices,
    stationary_bootstrap_mean_interval,
)
from shk.stats.calibration import compute_order_statistic_index
from shk.stats.false_rejection import ALPHA
from shk.stats.timeseries import generate_ar1_series

T57_STORY_POSITION: Final[int] = 2
N_BOOT: Final[int] = 999
N_PERMUTATIONS: Final[int] = 1000
ROLLING_WINDOW: Final[int] = 80
MAX_ACF_LAG: Final[int] = 10
COVERAGE_N_OBS: Final[int] = 380
COVERAGE_N_SERIES: Final[int] = 1000
COVERAGE_PHIS: Final[tuple[float, ...]] = (0.0, 0.1, 0.25, 0.5)
T42_COVERAGE_STATIONARY: Final[float] = 0.912
OUTCOME_COLUMNS: Final[tuple[str, ...]] = ("FTR", "FTHG", "FTAG")
Q_FIELDS: Final[dict[str, str]] = {m: f"q_{m}" for m in ALL_DEVIG_METHODS}
ODDS_COLUMNS: Final[dict[str, tuple[str, str, str]]] = {
    "b365_prematch": ("B365H", "B365D", "B365A"),
    "pinnacle_closing": ("PSCH", "PSCD", "PSCA"),
}


def load_full_frame() -> pd.DataFrame:
    """Stagioni di storia, training e validazione (mai il test), ordinate per Date, come in C4.2."""
    return load_match_frame()[0]


def evaluate_series(df_full: pd.DataFrame) -> dict[str, SeriesEvaluationData]:
    """Pipeline del Modulo 1 di C4.2: previsioni walk-forward, allineamento, de-vigging."""
    schedule = derive_fit_schedule(read_split_config())
    aligned = align_predictions_with_odds(generate_validation_predictions(df_full, ELO_FITS, schedule), df_full)
    return {s: prepare_series_evaluation(aligned, s, schedule) for s in SERIES_NAMES}


def series_terms(ev: SeriesEvaluationData, method: str) -> np.ndarray:
    """Termini g_t della serie per il metodo, nell'ordine di C4.2."""
    return compute_g_hat_terms(ev.p_model, getattr(ev, Q_FIELDS[method]), ev.outcomes)


def season_labels(ev: SeriesEvaluationData) -> np.ndarray:
    """Stagione di ogni partita usata."""
    return ev.df_used["season"].astype(str).to_numpy()


def ordered_seasons(labels: np.ndarray) -> list[str]:
    """Stagioni distinte in ordine cronologico."""
    return sorted(set(labels.tolist()), key=parse_season_start_year)


def stationary_length(x: np.ndarray) -> int:
    """L_PW stationary della serie, arrotondata (almeno 1, al più n)."""
    return min(len(x), round_block_length(optimal_block_length(np.asarray(x, dtype=np.float64)).stationary))


def percentile_interval(values: np.ndarray) -> tuple[float, float]:
    """Estremi al 95% per statistiche d'ordine (B = 999: 25-esima e 975-esima)."""
    v = np.sort(np.asarray(values, dtype=np.float64))
    return (float(v[compute_order_statistic_index(v.size, 0.975) - 1]),
            float(v[compute_order_statistic_index(v.size, 0.025) - 1]))


def season_bootstrap_means(x: np.ndarray, length: float, rng: np.random.Generator, n_boot: int = N_BOOT) -> np.ndarray:
    """Medie della serie su n_boot ricampionamenti stationary (length = 1: iid)."""
    idx = stationary_bootstrap_indices(len(x), float(length), n_boot, rng)
    return np.asarray(x, dtype=np.float64)[idx].mean(axis=1)


def pooled_bootstrap_means(groups: Sequence[np.ndarray], lengths: Sequence[float], rng: np.random.Generator,
                           n_boot: int = N_BOOT) -> np.ndarray:
    """ĝ pooled sui ricampionamenti a due livelli: stagioni come cluster, serie ricampionata dentro."""
    out = np.empty(n_boot)
    for b in range(n_boot):
        drawn = rng.integers(0, len(groups), size=len(groups))
        total, count = 0.0, 0
        for s in drawn:
            x = groups[s]
            idx = stationary_bootstrap_indices(len(x), float(lengths[s]), 1, rng)[0]
            total += float(x[idx].sum())
            count += len(x)
        out[b] = total / count
    return out


class IntervalRow(NamedTuple):
    """Intervallo di ĝ per una stagione (percentile) o pooled (t corretto, con il percentile come secondario)."""

    series: str
    method: str
    season: str
    n: int
    g_hat: float
    l_pw: int
    block_low: float
    block_high: float
    iid_low: float
    iid_high: float
    interval_method: str = "percentile"
    se_block: float = math.nan
    se_iid: float = math.nan
    block_pct_low: float = math.nan
    block_pct_high: float = math.nan
    iid_pct_low: float = math.nan
    iid_pct_high: float = math.nan


def interval_rows(evals: dict[str, SeriesEvaluationData], seq: np.random.SeedSequence,
                  n_boot: int = N_BOOT) -> list[IntervalRow]:
    """Intervalli per stagione e pooled, per serie e metodo."""
    pairs = [(s, m) for s in SERIES_NAMES for m in ALL_DEVIG_METHODS]
    rows = []
    for (series, method), pair_seq in zip(pairs, seq.spawn(len(pairs))):
        ev = evals[series]
        terms = series_terms(ev, method)
        labels = season_labels(ev)
        seasons = ordered_seasons(labels)
        groups = [terms[labels == s] for s in seasons]
        lengths = [stationary_length(g) for g in groups]
        children = pair_seq.spawn(len(seasons) + 1)
        for s, g, length, child in zip(seasons, groups, lengths, children):
            block_rng, iid_rng = (np.random.default_rng(c) for c in child.spawn(2))
            blo, bhi = percentile_interval(season_bootstrap_means(g, length, block_rng, n_boot))
            ilo, ihi = percentile_interval(season_bootstrap_means(g, 1.0, iid_rng, n_boot))
            rows.append(IntervalRow(series, method, s, len(g), float(g.mean()), length, blo, bhi, ilo, ihi))
        block_rng, iid_rng = (np.random.default_rng(c) for c in children[-1].spawn(2))
        boot_b = pooled_bootstrap_means(groups, lengths, block_rng, n_boot)
        boot_i = pooled_bootstrap_means(groups, [1.0] * len(groups), iid_rng, n_boot)
        g = float(terms.mean())
        blo, bhi, se_b = t_cluster_interval(g, boot_b, len(groups))
        ilo, ihi, se_i = t_cluster_interval(g, boot_i, len(groups))
        pblo, pbhi = percentile_interval(boot_b)
        pilo, pihi = percentile_interval(boot_i)
        rows.append(IntervalRow(series, method, "pooled", len(terms), g, -1, blo, bhi, ilo, ihi, "t_cluster",
                                se_b, se_i, pblo, pbhi, pilo, pihi))
    return rows


def permute_outcomes(df_full: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Esiti (FTR, FTHG, FTAG) permutati insieme dentro ciascuna stagione; il resto invariato."""
    out = df_full.copy()
    values = df_full[list(OUTCOME_COLUMNS)].to_numpy()
    for season in sorted(df_full["season"].unique(), key=parse_season_start_year):
        idx = np.flatnonzero(df_full["season"].to_numpy() == season)
        out.loc[out.index[idx], list(OUTCOME_COLUMNS)] = values[rng.permutation(idx)]
    return out


def season_g_hats(evals: dict[str, SeriesEvaluationData]) -> dict[tuple[str, str, str], float]:
    """Quantità per stagione (e "pooled") di una valutazione, con chiavi (serie, quantità, stagione):

    - (serie, metodo, s): ĝ;
    - (serie, "expected_" + metodo, s): media sulle partite di Σ_k π_k (ln p̂_tk − ln q_tk), con
      π_k = n_k/n le frequenze degli esiti della stagione (pooled: media pesata delle stagioni).
      Sotto una permutazione uniforme degli esiti dentro la stagione è il valore atteso di ĝ
      condizionato alle previsioni (media sulle partite di KL(π‖q) − KL(π‖p̂));
    - (serie, "model_log_loss", s): log-loss del modello;
    - (serie, "base_rate_log_loss", s): entropia delle frequenze degli esiti della stagione,
      cioè la log-loss di una previsione costante pari a π.
    """
    out = {}
    for series, ev in evals.items():
        labels = season_labels(ev)
        seasons = ordered_seasons(labels)
        y = pd.Series(ev.outcomes).map({"H": 0, "D": 1, "A": 2}).to_numpy()
        rows = np.arange(y.size)
        ll_model = -np.log(ev.p_model[rows, y])
        pi = np.empty((y.size, 3))
        for s in seasons:
            sel = labels == s
            freq = np.bincount(y[sel], minlength=3) / sel.sum()
            pi[sel] = freq
            out[(series, "model_log_loss", s)] = float(ll_model[sel].mean())
            out[(series, "base_rate_log_loss", s)] = float(-np.log(freq[y[sel]]).mean())
        out[(series, "model_log_loss", "pooled")] = float(ll_model.mean())
        out[(series, "base_rate_log_loss", "pooled")] = float(-np.log(pi[rows, y]).mean())
        for method in ALL_DEVIG_METHODS:
            q = getattr(ev, Q_FIELDS[method])
            terms = series_terms(ev, method)
            expected = (pi * (np.log(ev.p_model) - np.log(q))).sum(axis=1)
            for s in seasons:
                sel = labels == s
                out[(series, method, s)] = float(terms[sel].mean())
                out[(series, f"expected_{method}", s)] = float(expected[sel].mean())
            out[(series, method, "pooled")] = float(terms.mean())
            out[(series, f"expected_{method}", "pooled")] = float(expected.mean())
    return out


def placebo_g_hats(df_full: pd.DataFrame, seq: np.random.SeedSequence, start: int, stop: int) -> list[dict]:
    """ĝ per stagione sulle permutazioni start..stop−1 (un generatore per permutazione)."""
    children = seq.spawn(stop)[start:stop]
    return [season_g_hats(evaluate_series(permute_outcomes(df_full, np.random.default_rng(c)))) for c in children]


def rolling_shares(evals: dict[str, SeriesEvaluationData], window: int = ROLLING_WINDOW) -> list[dict[str, object]]:
    """Quota di finestre di W partite consecutive con ĝ > 0, per stagione, serie e metodo."""
    rows = []
    for series, ev in evals.items():
        labels = season_labels(ev)
        for method in ALL_DEVIG_METHODS:
            terms = series_terms(ev, method)
            for s in ordered_seasons(labels):
                x = terms[labels == s]
                if len(x) < window:
                    continue
                means = np.convolve(x, np.ones(window) / window, mode="valid")
                rows.append({"series": series, "method": method, "season": s, "n_windows": int(means.size),
                             "share_positive": float(np.mean(means > 0.0)), "min": float(means.min()),
                             "max": float(means.max())})
    return rows


def band_rows(evals: dict[str, SeriesEvaluationData]) -> list[dict[str, object]]:
    """ĝ per fascia della quota della favorita, per serie e metodo (tutte le stagioni insieme)."""
    rows = []
    for series, ev in evals.items():
        odds = ev.df_used[list(ODDS_COLUMNS[series])].apply(pd.to_numeric).to_numpy(dtype=np.float64)
        bands = np.array([assign_odds_bin(o) for o in odds.min(axis=1)])
        for method in ALL_DEVIG_METHODS:
            terms = series_terms(ev, method)
            for band in ODDS_BIN_LABELS:
                sel = bands == band
                rows.append({"series": series, "method": method, "band": band, "n": int(sel.sum()),
                             "g_hat": float(terms[sel].mean()) if sel.any() else math.nan})
    return rows


def threshold_rows(evals: dict[str, SeriesEvaluationData]) -> list[dict[str, object]]:
    """Media di ln π per stagione e pooled, da confrontare con ĝ (nota 2.4 §8)."""
    rows = []
    for series, ev in evals.items():
        odds = ev.df_used[list(ODDS_COLUMNS[series])].apply(pd.to_numeric).to_numpy(dtype=np.float64)
        ln_pi = np.log((1.0 / odds).sum(axis=1))
        labels = season_labels(ev)
        for s in ordered_seasons(labels) + ["pooled"]:
            sel = np.ones(len(labels), dtype=bool) if s == "pooled" else labels == s
            rows.append({"series": series, "season": s, "n": int(sel.sum()), "mean_ln_pi": float(ln_pi[sel].mean())})
    return rows


def ar1_coverage(phi: float, seq: np.random.SeedSequence, n: int = COVERAGE_N_OBS,
                 n_series: int = COVERAGE_N_SERIES) -> tuple[float, float, float]:
    """Copertura al 95% della media (vera 0) di AR(1) con la procedura di T42.

    generate_ar1_series(phi, n, n_series); per serie L_PW stationary arrotondata e intervallo
    percentile con N_BOOT ricampionamenti (stationary_bootstrap_mean_interval), a L_PW e iid.
    Restituisce (copertura stationary, copertura iid, L_PW media). Generatori: seq.spawn(3)
    per serie, stationary e iid, come spawn_t42_generators.
    """
    rng_series, rng_sb, rng_iid = (np.random.default_rng(c) for c in seq.spawn(3))
    series = generate_ar1_series(phi, n, n_series, rng_series)
    covered_sb = covered_iid = 0
    lengths = np.empty(n_series)
    for i in range(n_series):
        x = series[i]
        length = round_block_length(optimal_block_length(x).stationary)
        lengths[i] = length
        lo, hi = stationary_bootstrap_mean_interval(x, length, N_BOOT, ALPHA, rng_sb)
        covered_sb += int(lo <= 0.0 <= hi)
        lo, hi = stationary_bootstrap_mean_interval(x, 1, N_BOOT, ALPHA, rng_iid)
        covered_iid += int(lo <= 0.0 <= hi)
    return covered_sb / n_series, covered_iid / n_series, float(lengths.mean())


def autocorrelations(x: np.ndarray, max_lag: int = MAX_ACF_LAG) -> np.ndarray:
    """Autocorrelazioni campionarie ai ritardi 1..max_lag (autocovarianze su tutto il campione)."""
    e = np.asarray(x, dtype=np.float64) - np.mean(x)
    denom = float(e @ e)
    return np.array([float(e[k:] @ e[:-k]) / denom for k in range(1, max_lag + 1)])


def acf_rows(evals: dict[str, SeriesEvaluationData], max_lag: int = MAX_ACF_LAG) -> list[dict[str, object]]:
    """Autocorrelazione della serie di δ (termini di ĝ) ai ritardi 1–10, per serie e metodo.

    Per stagione si calcolano le autocorrelazioni della serie della stagione; la riga riporta
    la media sulle stagioni e i valori sulla serie concatenata di tutte le stagioni.
    """
    rows = []
    for series, ev in evals.items():
        labels = season_labels(ev)
        for method in ALL_DEVIG_METHODS:
            terms = series_terms(ev, method)
            per_season = np.array([autocorrelations(terms[labels == s], max_lag) for s in ordered_seasons(labels)])
            whole = autocorrelations(terms, max_lag)
            for k in range(max_lag):
                rows.append({"series": series, "method": method, "lag": k + 1,
                             "acf_mean_over_seasons": float(per_season[:, k].mean()),
                             "acf_min_season": float(per_season[:, k].min()),
                             "acf_max_season": float(per_season[:, k].max()),
                             "acf_concatenated": float(whole[k])})
    return rows


def t57_sequences(seed: int = SEED_S10) -> list[np.random.SeedSequence]:
    """Tre figli di SeedSequence(SEED_S10).spawn(5)[2] (vedi modulo)."""
    return np.random.SeedSequence(seed).spawn(N_STORY_TASKS)[T57_STORY_POSITION].spawn(3)


G_HAT_INFERENCE_COLUMNS: Final[tuple[str, ...]] = (
    "row_type", "series", "method", "season", "band", "lag", "phi", "n", "g_hat", "l_pw",
    "interval_method", "se_boot_block", "se_boot_iid", "ci_block_low", "ci_block_high", "ci_iid_low", "ci_iid_high",
    "ci_block_pct_low", "ci_block_pct_high", "ci_iid_pct_low", "ci_iid_pct_high", "width_ratio_block_iid",
    "mean_ln_pi", "g_minus_ln_pi",
    "placebo_n", "placebo_mean", "placebo_q025", "placebo_q975", "observed_percentile",
    "expected_mean", "placebo_minus_expected", "se_paired", "se_placebo", "within_3se",
    "model_ll_observed", "model_ll_placebo_mean", "model_ll_placebo_q025", "model_ll_placebo_q975", "base_rate_ll",
    "n_windows", "share_positive", "window_min", "window_max",
    "acf_mean_over_seasons", "acf_min_season", "acf_max_season", "acf_concatenated",
    "coverage_stationary", "coverage_iid", "mean_l_pw", "n_series", "criterion",
)


def _row(**fields: object) -> dict[str, object]:
    rec = {c: "" for c in G_HAT_INFERENCE_COLUMNS}
    rec.update(fields)
    return rec


def placebo_records(observed: dict, placebos: Sequence[dict]) -> list[dict[str, object]]:
    """Righe "placebo" per serie, metodo e stagione (più pooled) e righe "placebo_leakage" per serie e stagione."""
    records = []
    series_seasons = sorted({(k[0], k[2]) for k in observed if k[1] == "model_log_loss"},
                            key=lambda t: (t[0], t[1] == "pooled", parse_season_start_year(t[1]) if t[1] != "pooled" else 0))
    for series, season in series_seasons:
        ll = np.array([p[(series, "model_log_loss", season)] for p in placebos])
        records.append(_row(row_type="placebo_leakage", series=series, season=season, placebo_n=len(placebos),
                            model_ll_observed=observed[(series, "model_log_loss", season)],
                            model_ll_placebo_mean=float(ll.mean()), model_ll_placebo_q025=float(np.quantile(ll, 0.025)),
                            model_ll_placebo_q975=float(np.quantile(ll, 0.975)),
                            base_rate_ll=observed[(series, "base_rate_log_loss", season)]))
        for method in ALL_DEVIG_METHODS:
            g = np.array([p[(series, method, season)] for p in placebos])
            e = np.array([p[(series, f"expected_{method}", season)] for p in placebos])
            d = g - e
            se_paired = float(d.std(ddof=1) / math.sqrt(d.size))
            obs = observed[(series, method, season)]
            records.append(_row(row_type="placebo", series=series, method=method, season=season, placebo_n=len(g),
                                g_hat=obs, placebo_mean=float(g.mean()), placebo_q025=float(np.quantile(g, 0.025)),
                                placebo_q975=float(np.quantile(g, 0.975)), observed_percentile=float(np.mean(g <= obs)),
                                expected_mean=float(e.mean()), placebo_minus_expected=float(d.mean()),
                                se_paired=se_paired, se_placebo=float(g.std(ddof=1) / math.sqrt(g.size)),
                                within_3se=bool(abs(d.mean()) < 3.0 * se_paired)))
    return records


def coverage_records(seq: np.random.SeedSequence, phis: Sequence[float] = COVERAGE_PHIS) -> list[dict[str, object]]:
    """Righe "coverage": coperture block e iid per φ, con i due criteri vincolanti sostituiti dal programmatore."""
    records = []
    results = {}
    for phi, child in zip(phis, seq.spawn(len(phis))):
        sb, iid, mean_l = ar1_coverage(phi, child)
        results[phi] = (sb, iid)
        records.append(_row(row_type="coverage", phi=phi, n=COVERAGE_N_OBS, n_series=COVERAGE_N_SERIES,
                            coverage_stationary=sb, coverage_iid=iid, mean_l_pw=mean_l))
    for rec in records:
        phi = rec["phi"]
        sb, iid = results[phi]
        if phi == 0.0:
            rec["criterion"] = bool(0.93 <= sb <= 0.97 and 0.93 <= iid <= 0.97)
        elif phi == 0.5:
            se = math.sqrt(sb * (1 - sb) / COVERAGE_N_SERIES + T42_COVERAGE_STATIONARY * (1 - T42_COVERAGE_STATIONARY) / 1000)
            rec["criterion"] = bool(sb > iid and abs(sb - T42_COVERAGE_STATIONARY) < 3.0 * se)
    return records
