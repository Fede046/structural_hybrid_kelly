"""Scenari con drift di tipo atteso e decomposizione annidata.

Specificazione: quella scelta sul training (derive_specification), senza modifiche.
Gruppi e W fissati prima di eseguire:
- scenario 1, compositivo atteso: per ogni transizione s − 1 → s fra stagioni consecutive
  con δ, A = ultime W partite di s − 1, B = prime W di s, W in MODULE2_WINDOWS (W = 80
  principale);
- scenario 2, strutturale atteso: A = partite del 2019-20 fino all'ultima data prima della
  sospensione (l'intervallo più lungo fra date consecutive della stagione), B = partite
  del 2019-20 dopo la sospensione e tutto il 2020-21; con la dettagliata (Yun);
- scenario 3, fine stagione: per ogni stagione con δ, A = matchday 10–25 (posizioni
  91–250), B = matchday 30–38 (posizioni 291–380), senza e con il flag "senza obiettivi"
  (season_objectives.no_objective_flags; almeno una delle due squadre).

Scenari 1 e 2: three-fold e π come nella decisione di progetto. Scenario 3 (decisione del
programmatore, 2026-10-11): il flag "senza obiettivi" esiste solo nel gruppo B, per
costruzione (violazione del supporto comune), quindi β_A,flag non è identificato.
- Quantità principale, identica nelle due versioni: la two-fold con riferimento β_B, con
  S = x̄_A'(β_B − β_A) e C + I = β_B'(x̄_B − x̄_A), e quota π_B = |S| / (|C + I| + |S|);
  la differenza annidata (nota 2.7 §8.3) è π_B senza flag meno π_B con flag.
- Analisi secondaria: three-fold con il flag sotto due ipotesi dichiarate sul coefficiente
  non identificato, assegnato dopo aver stimato A senza la colonna del flag: (a)
  β_A,flag = 0, l'effetto del flag va nell'interazione; (e) β_A,flag = β̂_B,flag,
  l'effetto va nella composizione. S e C + I non dipendono dall'ipotesi.

Intervalli al 95%: stationary bootstrap dentro ciascun gruppo (righe ricampionate insieme a
δ), L = L_PW stationary arrotondata del δ del gruppo, B = N_BOOT_SCENARIOS, percentili per
statistiche d'ordine sui ricampionamenti validi. Seed: SeedSequence(SEED_S8).spawn(5)[3]
(posizione 3), spawn(3) per scenario; scenario 1: spawn(len(MODULE2_WINDOWS)) per W
e poi spawn(numero di transizioni), uno per transizione; scenario 2: un generatore;
scenario 3: spawn(numero di stagioni), uno per stagione. Ogni generatore estrae prima per A
e poi per B.
"""

import math
from collections.abc import Sequence
from typing import Final

import numpy as np
import pandas as pd

from shk.model.covariate_inspection import MODULE2_WINDOWS
from shk.model.elo_fit import parse_season_start_year
from shk.model.module2 import flag_dummy_blocks
from shk.model.season_objectives import no_objective_flags
from shk.stats.bootstrap import optimal_block_length, round_block_length, stationary_bootstrap_indices
from shk.stats.calibration import compute_order_statistic_index
from shk.stats.false_rejection import ALPHA
from shk.stats.oaxaca import oaxaca_blinder, ols_qr_batch
from shk.stats.oaxaca_synthetic import N_STORY_TASKS, SEED_S8

T48_STORY_POSITION: Final[int] = 3
N_BOOT_SCENARIOS: Final[int] = 999
MAIN_WINDOW: Final[int] = 80
COVID_SEASON_A: Final[str] = "2019-20"
COVID_SEASON_B: Final[str] = "2020-21"
END_SEASON_A: Final[tuple[int, int]] = (91, 250)
END_SEASON_B: Final[tuple[int, int]] = (291, 380)
NO_OBJECTIVES: Final[str] = "flag_no_objectives"

VERSION_THREEFOLD: Final[str] = "threefold"
VERSION_WITHOUT_FLAG: Final[str] = "without_flag"
VERSION_WITH_FLAG_A: Final[str] = "with_flag_beta_a_zero"
VERSION_WITH_FLAG_E: Final[str] = "with_flag_beta_a_equal_b"
QUANTITIES: Final[tuple[str, ...]] = (
    "total", "compositional", "structural", "interaction",
    "structural_share", "compositional_share", "explained_b", "structural_share_b",
)
DIFFERENCE: Final[str] = "structural_share_b_difference"

KNOWN_SCENARIOS_CSV_COLUMNS: Final[tuple[str, ...]] = (
    "scenario", "season_a", "season_b", "window", "version", "quantity", "covariate",
    "estimate", "lower", "upper", "n_a", "n_b", "n_boot", "n_valid", "block_length_a",
    "block_length_b", "date_a_last", "date_b_first",
)


def _quantities(beta_a: np.ndarray, xbar_a: np.ndarray, beta_b: np.ndarray, xbar_b: np.ndarray,
                mean_a: np.ndarray, mean_b: np.ndarray) -> dict[str, np.ndarray]:
    """Quantità della decomposizione per un lotto (righe = ricampionamenti)."""
    dx = xbar_b - xbar_a
    dbeta = beta_b - beta_a
    comp = np.einsum("bj,bj->b", beta_a, dx)
    struct = np.einsum("bj,bj->b", xbar_a, dbeta)
    inter = np.einsum("bj,bj->b", dx, dbeta)
    explained_b = np.einsum("bj,bj->b", beta_b, dx)
    denom = np.abs(comp) + np.abs(struct) + np.abs(inter)
    denom_b = np.abs(explained_b) + np.abs(struct)
    with np.errstate(invalid="ignore", divide="ignore"):
        return {
            "total": mean_b - mean_a,
            "compositional": comp,
            "structural": struct,
            "interaction": inter,
            "structural_share": np.abs(struct) / denom,
            "compositional_share": np.abs(comp) / denom,
            "explained_b": explained_b,
            "structural_share_b": np.abs(struct) / denom_b,
        }


def _design(x: np.ndarray) -> np.ndarray:
    return np.concatenate([np.ones(x.shape[:-1] + (1,)), x], axis=-1)


def decomposition_batch(xa: np.ndarray, ya: np.ndarray, xb: np.ndarray, yb: np.ndarray) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Quantità per gruppi con le stesse covariate: xa (B, nA, k), xb (B, nB, k)."""
    da, db = _design(xa), _design(xb)
    beta_a, va = ols_qr_batch(da, ya)
    beta_b, vb = ols_qr_batch(db, yb)
    q = _quantities(beta_a, da.mean(axis=1), beta_b, db.mean(axis=1), ya.mean(axis=1), yb.mean(axis=1))
    valid = va & vb
    return {k: np.where(valid, v, np.nan) for k, v in q.items()}, valid


def decomposition_absent_in_a_batch(
    xa: np.ndarray, ya: np.ndarray, xb: np.ndarray, flag_b: np.ndarray, yb: np.ndarray, assume_equal: bool
) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Quantità con un flag presente solo in B (in A vale 0 per costruzione).

    A si stima senza la colonna del flag; β_A,flag si assegna dopo: 0 (assume_equal False,
    ipotesi a) oppure β̂_B,flag (assume_equal True, ipotesi e). x̄_A,flag = 0.
    """
    da = _design(xa)
    db = _design(np.concatenate([xb, flag_b[..., None]], axis=-1))
    beta_a, va = ols_qr_batch(da, ya)
    beta_b, vb = ols_qr_batch(db, yb)
    flag_coef = beta_b[:, -1:] if assume_equal else np.zeros((beta_b.shape[0], 1))
    beta_a_ext = np.concatenate([beta_a, flag_coef], axis=1)
    xbar_a_ext = np.concatenate([da.mean(axis=1), np.zeros((da.shape[0], 1))], axis=1)
    q = _quantities(beta_a_ext, xbar_a_ext, beta_b, db.mean(axis=1), ya.mean(axis=1), yb.mean(axis=1))
    valid = va & vb
    return {k: np.where(valid, v, np.nan) for k, v in q.items()}, valid


def suspension_split(frame: pd.DataFrame, season: str = COVID_SEASON_A) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Ultima data prima e prima data dopo l'intervallo più lungo fra date consecutive."""
    dates = np.unique(frame.loc[frame["season"] == season, "Date"].to_numpy(dtype="datetime64[ns]"))
    gaps = np.diff(dates)
    i = int(np.argmax(gaps))
    return pd.Timestamp(dates[i]), pd.Timestamp(dates[i + 1])


def _interval(values: np.ndarray, valid: np.ndarray, alpha: float = ALPHA) -> tuple[float, float, int]:
    v = np.sort(values[valid & np.isfinite(values)])
    n = v.size
    if n == 0:
        return math.nan, math.nan, 0
    k_hi = compute_order_statistic_index(n, alpha / 2.0)
    k_lo = compute_order_statistic_index(n, 1.0 - alpha / 2.0)
    return float(v[k_lo - 1]), float(v[k_hi - 1]), n


def _boot_indices(y: np.ndarray, rng: np.random.Generator, n_boot: int) -> tuple[np.ndarray, int]:
    length = round_block_length(optimal_block_length(y).stationary)
    return stationary_bootstrap_indices(y.size, length, n_boot, rng), length


def spawn_t48_generators(seed: int = SEED_S8) -> tuple[np.random.SeedSequence, ...]:
    """Tre SeedSequence, una per scenario (schema nella docstring del modulo)."""
    if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)):
        raise TypeError(f"seed must be an integer, got {type(seed).__name__}")
    return tuple(np.random.SeedSequence(seed).spawn(N_STORY_TASKS)[T48_STORY_POSITION].spawn(3))


def _rows(base: dict[str, object], point: dict[str, float], boot: dict[str, np.ndarray], valid: np.ndarray,
          quantities: Sequence[str], n_boot: int) -> list[dict[str, object]]:
    out = []
    for q in quantities:
        lo, hi, n_valid = _interval(boot[q], valid)
        rec = {c: "" for c in KNOWN_SCENARIOS_CSV_COLUMNS}
        rec.update(base)
        rec.update(quantity=q, estimate=float(point[q]), lower=lo, upper=hi, n_boot=n_boot, n_valid=n_valid)
        out.append(rec)
    return out


def _point(qs: dict[str, np.ndarray]) -> dict[str, float]:
    return {k: float(v[0]) for k, v in qs.items()}


def _pair_records(scenario: str, season_a: str, season_b: str, window: object, a: pd.DataFrame, b: pd.DataFrame,
                  covariates: Sequence[str], rng: np.random.Generator, n_boot: int) -> list[dict[str, object]]:
    """Three-fold e π con intervalli per una coppia di gruppi (scenari 1 e 2)."""
    xa, ya = a[list(covariates)].to_numpy(float), a["delta"].to_numpy(float)
    xb, yb = b[list(covariates)].to_numpy(float), b["delta"].to_numpy(float)
    point, _ = decomposition_batch(xa[None], ya[None], xb[None], yb[None])
    ia, la = _boot_indices(ya, rng, n_boot)
    ib, lb = _boot_indices(yb, rng, n_boot)
    boot, valid = decomposition_batch(xa[ia], ya[ia], xb[ib], yb[ib])
    base = {"scenario": scenario, "season_a": season_a, "season_b": season_b, "window": window,
            "version": VERSION_THREEFOLD, "n_a": len(a), "n_b": len(b), "block_length_a": la,
            "block_length_b": lb, "date_a_last": pd.Timestamp(a["Date"].max()).strftime("%Y-%m-%d"),
            "date_b_first": pd.Timestamp(b["Date"].min()).strftime("%Y-%m-%d")}
    return _rows(base, _point(point), boot, valid, QUANTITIES, n_boot)


def add_no_objective_flag(frame: pd.DataFrame, raw: pd.DataFrame) -> pd.DataFrame:
    """Aggiunge flag_no_objectives (almeno una squadra senza obiettivi) al DataFrame del Modulo 2."""
    seasons = set(frame["season"])
    sub = raw[raw["season"].isin(seasons)].reset_index(drop=True)
    fh, fa = no_objective_flags(sub)
    flags = sub[["season", "Date", "HomeTeam", "AwayTeam"]].assign(**{NO_OBJECTIVES: ((fh + fa) > 0).astype(np.int64)})
    out = frame.merge(flags, on=["season", "Date", "HomeTeam", "AwayTeam"], how="left", validate="one_to_one")
    if out[NO_OBJECTIVES].isna().any():
        raise ValueError("Some matches have no no-objectives flag")
    return out


def evaluate_known_scenarios(
    frame: pd.DataFrame, covariates: Sequence[str], seed: int = SEED_S8, n_boot: int = N_BOOT_SCENARIOS
) -> list[dict[str, object]]:
    """Record del CSV results/us_c7_3b_known_scenarios.csv per i tre scenari.

    frame è il DataFrame del Modulo 2 con la colonna flag_no_objectives (add_no_objective_flag).
    """
    seq1, seq2, seq3 = spawn_t48_generators(seed)
    years = frame["season"].map(parse_season_start_year)
    ordered = frame.assign(_y=years).sort_values(["_y", "Date"], kind="stable")
    seasons = sorted(set(frame["season"]), key=parse_season_start_year)
    by_season = {s: ordered[ordered["season"] == s] for s in seasons}
    records: list[dict[str, object]] = []

    # Scenario 1: transizioni fra stagioni consecutive con δ
    transitions = [(p, s) for p, s in zip(seasons, seasons[1:])
                   if parse_season_start_year(s) == parse_season_start_year(p) + 1]
    for w, w_seq in zip(MODULE2_WINDOWS, seq1.spawn(len(MODULE2_WINDOWS))):
        for (prev, cur), t_seq in zip(transitions, w_seq.spawn(len(transitions))):
            a = by_season[prev].iloc[-w:]
            b = by_season[cur].iloc[:w]
            records += _pair_records("1_transition", prev, cur, w, a, b, covariates, np.random.default_rng(t_seq), n_boot)

    # Scenario 2: sospensione del 2019-20
    last_before, first_after = suspension_split(frame)
    s20 = by_season[COVID_SEASON_A]
    a = s20[s20["Date"] <= last_before]
    b = pd.concat([s20[s20["Date"] >= first_after], by_season[COVID_SEASON_B]])
    rng2 = np.random.default_rng(seq2)
    records += _pair_records("2_covid", COVID_SEASON_A, f"{COVID_SEASON_A}+{COVID_SEASON_B}", "", a, b,
                             covariates, rng2, n_boot)
    res = oaxaca_blinder(a[list(covariates)].to_numpy(float), a["delta"].to_numpy(float),
                         b[list(covariates)].to_numpy(float), b["delta"].to_numpy(float),
                         names=list(covariates), dummy_blocks=flag_dummy_blocks(covariates))
    for comp in ("compositional", "structural", "interaction"):
        for name, value in zip(res.detailed.names, getattr(res.detailed, comp)):
            rec = {c: "" for c in KNOWN_SCENARIOS_CSV_COLUMNS}
            rec.update(scenario="2_covid_detail", season_a=COVID_SEASON_A,
                       season_b=f"{COVID_SEASON_A}+{COVID_SEASON_B}", version=VERSION_THREEFOLD,
                       quantity=comp, covariate=name, estimate=float(value), n_a=len(a), n_b=len(b))
            records.append(rec)

    # Scenario 3: fine stagione senza e con il flag
    for season, s_seq in zip(seasons, seq3.spawn(len(seasons))):
        rows = by_season[season]
        pos = rows["position"].to_numpy()
        a = rows[(pos >= END_SEASON_A[0]) & (pos <= END_SEASON_A[1])]
        b = rows[(pos >= END_SEASON_B[0]) & (pos <= END_SEASON_B[1])]
        xa, ya = a[list(covariates)].to_numpy(float), a["delta"].to_numpy(float)
        xb, yb = b[list(covariates)].to_numpy(float), b["delta"].to_numpy(float)
        fb = b[NO_OBJECTIVES].to_numpy(float)
        rng = np.random.default_rng(s_seq)
        ia, la = _boot_indices(ya, rng, n_boot)
        ib, lb = _boot_indices(yb, rng, n_boot)
        base = {"scenario": "3_end_season", "season_a": season, "season_b": season, "window": "",
                "n_a": len(a), "n_b": len(b), "block_length_a": la, "block_length_b": lb,
                "date_a_last": pd.Timestamp(a["Date"].max()).strftime("%Y-%m-%d"),
                "date_b_first": pd.Timestamp(b["Date"].min()).strftime("%Y-%m-%d")}
        p0, _ = decomposition_batch(xa[None], ya[None], xb[None], yb[None])
        b0, v0 = decomposition_batch(xa[ia], ya[ia], xb[ib], yb[ib])
        pa, _ = decomposition_absent_in_a_batch(xa[None], ya[None], xb[None], fb[None], yb[None], False)
        ba, va = decomposition_absent_in_a_batch(xa[ia], ya[ia], xb[ib], fb[ib], yb[ib], False)
        pe, _ = decomposition_absent_in_a_batch(xa[None], ya[None], xb[None], fb[None], yb[None], True)
        be, ve = decomposition_absent_in_a_batch(xa[ia], ya[ia], xb[ib], fb[ib], yb[ib], True)
        records += _rows({**base, "version": VERSION_WITHOUT_FLAG}, _point(p0), b0, v0, QUANTITIES, n_boot)
        records += _rows({**base, "version": VERSION_WITH_FLAG_A}, _point(pa), ba, va, QUANTITIES, n_boot)
        records += _rows({**base, "version": VERSION_WITH_FLAG_E}, _point(pe), be, ve, QUANTITIES, n_boot)
        diff_point = {DIFFERENCE: _point(p0)["structural_share_b"] - _point(pa)["structural_share_b"]}
        diff_boot = {DIFFERENCE: b0["structural_share_b"] - ba["structural_share_b"]}
        records += _rows({**base, "version": "without_minus_with"}, diff_point, diff_boot, v0 & va, (DIFFERENCE,), n_boot)
    return records
