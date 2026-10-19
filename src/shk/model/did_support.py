"""DiD fra partite con neopromosse e fra squadre note, Ñopo e supporto comune.

DiD (nota 1.6 §10, test 3 del Modulo 2): per stagione e pooled sulle 3 stagioni di training
e le 19 di validazione; E = partite con almeno una squadra alla prima stagione dopo
l'ingresso (flag_promoted), NE = le altre; presto = matchday 1–10 (posizioni 1–100),
tardi = matchday 11–38 (posizioni 101–380); DiD = (δ̄_E,tardi − δ̄_E,presto) −
(δ̄_NE,tardi − δ̄_NE,presto). Intervallo al 95% per stationary bootstrap delle date: ogni
data porta con sé tutte le sue partite; L = L_PW stationary arrotondata della serie per data
della media di δ (come la decisione di progetto per i seed); B = N_BOOT_DID; il pooled ricampiona le
date di ogni stagione in modo indipendente (stagioni come cluster) e ricalcola il DiD
sull'unione. Il DiD è diagnostico e non entra nella regola di staking.

Placebo per la parallel trends: sulle sole partite fra squadre note, E' = partite con almeno
una di k squadre note estratte a caso, con k = numero di neopromosse della stagione;
N_PLACEBO = 200 ripetizioni per stagione.

Ñopo (stats.nopo) sui gruppi dello scenario compositivo degli scenari noti (ultime W partite di s − 1
contro prime W di s, ogni W) e, per decisione del programmatore, sui gruppi dello scenario
3 degli scenari noti (matchday 10–25 contro 30–38) senza e con il flag "senza obiettivi".

Quota di partite fuori supporto all'inizio di ogni stagione: per ogni partita dei matchday
1–10, alla sua data di decisione e per ogni W, la regola out_of_support_mask con la finestra
A del Modulo 2; separata per partite con una neopromossa mai vista, con una tornante, e
senza neopromosse.

Seed: SeedSequence(SEED_S8).spawn(5)[4] (posizione 4), spawn(2): figlio 0 per il
bootstrap del DiD, diviso con spawn(numero di stagioni + 1) (stagioni in ordine cronologico,
poi il pooled); figlio 1 per i placebo, diviso con spawn(numero di stagioni).
"""

from collections.abc import Sequence
from typing import Final

import numpy as np
import pandas as pd

from shk.model.covariate_inspection import MODULE2_WINDOWS
from shk.model.elo_fit import parse_season_start_year
from shk.model.known_scenarios import END_SEASON_A, END_SEASON_B, NO_OBJECTIVES
from shk.model.module2 import Module2Data, eligible_mask, prepare_module2_data
from shk.model.module2_data import entry_status_by_team_season
from shk.stats.bootstrap import optimal_block_length, round_block_length, stationary_bootstrap_indices
from shk.stats.calibration import compute_order_statistic_index
from shk.stats.false_rejection import ALPHA
from shk.stats.nopo import did_2x2, nopo_from_covariates, out_of_support_mask
from shk.stats.oaxaca_synthetic import N_STORY_TASKS, SEED_S8

T49_STORY_POSITION: Final[int] = 4
EARLY_POSITIONS: Final[tuple[int, int]] = (1, 100)
N_BOOT_DID: Final[int] = 999
N_PLACEBO: Final[int] = 200
SUPPORT_POSITIONS: Final[tuple[int, int]] = (1, 100)

DID_SUPPORT_CSV_COLUMNS: Final[tuple[str, ...]] = (
    "row_type", "scenario", "season", "season_b", "window", "version", "group", "estimate", "lower",
    "upper", "n", "n_out", "share", "placebo_mean", "placebo_sd", "placebo_q025", "placebo_q50",
    "placebo_q975", "observed_percentile", "total", "out_of_support_a", "out_of_support_b",
    "composition", "structure", "share_unmatched_a", "share_unmatched_b", "n_common_cells",
    "block_length", "n_boot",
)


def _rec(**fields: object) -> dict[str, object]:
    rec: dict[str, object] = {c: "" for c in DID_SUPPORT_CSV_COLUMNS}
    for k, v in fields.items():
        if k not in rec:
            raise KeyError(k)
        rec[k] = v
    return rec


def spawn_t49_generators(seasons: Sequence[str], seed: int = SEED_S8) -> tuple[list[np.random.Generator], list[np.random.Generator]]:
    """(generatori del bootstrap per stagione + pooled, generatori dei placebo per stagione)."""
    if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)):
        raise TypeError(f"seed must be an integer, got {type(seed).__name__}")
    boot, placebo = np.random.SeedSequence(seed).spawn(N_STORY_TASKS)[T49_STORY_POSITION].spawn(2)
    n = len(seasons)
    return ([np.random.default_rng(s) for s in boot.spawn(n + 1)],
            [np.random.default_rng(s) for s in placebo.spawn(n)])


def _date_cell_sums(season_rows: pd.DataFrame, treated: np.ndarray, late: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Somme e conteggi per data delle quattro celle (E tardi, E presto, NE tardi, NE presto)."""
    dates = season_rows["Date"].to_numpy(dtype="datetime64[ns]")
    unique, inv = np.unique(dates, return_inverse=True)
    delta = season_rows["delta"].to_numpy(float)
    masks = (treated & late, treated & ~late, ~treated & late, ~treated & ~late)
    sums = np.zeros((unique.size, 4))
    counts = np.zeros((unique.size, 4))
    for j, m in enumerate(masks):
        np.add.at(sums[:, j], inv[m], delta[m])
        np.add.at(counts[:, j], inv[m], 1.0)
    per_date_mean = np.bincount(inv, weights=delta) / np.bincount(inv)
    return sums, counts, per_date_mean


def _did_from_sums(sums: np.ndarray, counts: np.ndarray) -> np.ndarray:
    """DiD da somme e conteggi (..., 4); NaN se una cella è vuota."""
    with np.errstate(invalid="ignore", divide="ignore"):
        m = sums / counts
    return (m[..., 0] - m[..., 1]) - (m[..., 2] - m[..., 3])


def _interval(values: np.ndarray) -> tuple[float, float]:
    v = np.sort(values[np.isfinite(values)])
    n = v.size
    k_hi = compute_order_statistic_index(n, ALPHA / 2.0)
    k_lo = compute_order_statistic_index(n, 1.0 - ALPHA / 2.0)
    return float(v[k_lo - 1]), float(v[k_hi - 1])


def did_records(frame: pd.DataFrame, raw: pd.DataFrame, seed: int = SEED_S8, n_boot: int = N_BOOT_DID,
                n_placebo: int = N_PLACEBO) -> list[dict[str, object]]:
    """DiD per stagione e pooled con intervalli, e placebo per stagione."""
    seasons = sorted(set(frame["season"]), key=parse_season_start_year)
    boot_rngs, placebo_rngs = spawn_t49_generators(seasons, seed)
    status = entry_status_by_team_season(raw)
    records: list[dict[str, object]] = []
    boot_sums: list[np.ndarray] = []
    boot_counts: list[np.ndarray] = []
    all_sums = np.zeros(4)
    all_counts = np.zeros(4)
    for season, rng, prng in zip(seasons, boot_rngs, placebo_rngs):
        rows = frame[frame["season"] == season].sort_values("Date", kind="stable")
        treated = rows["flag_promoted"].to_numpy() == 1
        late = rows["position"].to_numpy() > EARLY_POSITIONS[1]
        obs = did_2x2(rows["delta"].to_numpy(float), treated, late)
        sums, counts, per_date = _date_cell_sums(rows, treated, late)
        all_sums += sums.sum(axis=0)
        all_counts += counts.sum(axis=0)
        length = round_block_length(optimal_block_length(per_date).stationary)
        idx = stationary_bootstrap_indices(per_date.size, length, n_boot, rng)
        bs, bc = sums[idx].sum(axis=1), counts[idx].sum(axis=1)
        boot_sums.append(bs)
        boot_counts.append(bc)
        lo, hi = _interval(_did_from_sums(bs, bc))
        records.append(_rec(row_type="did", season=season, estimate=obs, lower=lo, upper=hi, n=len(rows),
                            block_length=length, n_boot=n_boot))

        # Placebo sulle sole partite fra squadre note
        known_rows = rows[~treated]
        teams_all = set(rows["HomeTeam"]) | set(rows["AwayTeam"])
        teams_promoted = {t for t in teams_all if status[(season, t)] in ("new", "returning")}
        k = len(teams_promoted)
        known_teams = np.array(sorted(teams_all - teams_promoted))
        late_k = known_rows["position"].to_numpy() > EARLY_POSITIONS[1]
        home_k = known_rows["HomeTeam"].to_numpy()
        away_k = known_rows["AwayTeam"].to_numpy()
        y_k = known_rows["delta"].to_numpy(float)
        placebo = np.empty(n_placebo)
        for i in range(n_placebo):
            chosen = prng.choice(known_teams, size=k, replace=False)
            fake = np.isin(home_k, chosen) | np.isin(away_k, chosen)
            placebo[i] = did_2x2(y_k, fake, late_k)
        q = np.quantile(placebo, [0.025, 0.5, 0.975])
        records.append(_rec(row_type="placebo", season=season, estimate=obs, n=n_placebo,
                            placebo_mean=float(placebo.mean()), placebo_sd=float(placebo.std(ddof=1)),
                            placebo_q025=float(q[0]), placebo_q50=float(q[1]), placebo_q975=float(q[2]),
                            observed_percentile=float(np.mean(placebo <= obs)), group=str(k)))

    pooled = float(_did_from_sums(all_sums, all_counts))
    lo, hi = _interval(_did_from_sums(np.sum(boot_sums, axis=0), np.sum(boot_counts, axis=0)))
    records.append(_rec(row_type="did", season="pooled", estimate=pooled, lower=lo, upper=hi,
                        n=int(all_counts.sum()), n_boot=n_boot))
    return records


def nopo_records(frame: pd.DataFrame, covariates: Sequence[str]) -> list[dict[str, object]]:
    """Ñopo per lo scenario compositivo degli scenari noti (ogni W) e per lo scenario 3 senza e con il flag."""
    dummies = [i for i, c in enumerate(covariates) if c.startswith("flag_")]
    years = frame["season"].map(parse_season_start_year)
    ordered = frame.assign(_y=years).sort_values(["_y", "Date"], kind="stable")
    seasons = sorted(set(frame["season"]), key=parse_season_start_year)
    by_season = {s: ordered[ordered["season"] == s] for s in seasons}
    cov = list(covariates)
    records: list[dict[str, object]] = []

    def add(scenario, season_a, season_b, window, version, a, b, cols, dummy_idx):
        res = nopo_from_covariates(a[cols].to_numpy(float), a["delta"].to_numpy(float),
                                   b[cols].to_numpy(float), b["delta"].to_numpy(float), dummy_idx)
        records.append(_rec(row_type="nopo", scenario=scenario, season=season_a, season_b=season_b,
                            window=window, version=version, total=res.total,
                            out_of_support_a=res.out_of_support_a, out_of_support_b=res.out_of_support_b,
                            composition=res.composition, structure=res.structure,
                            share_unmatched_a=res.share_unmatched_a, share_unmatched_b=res.share_unmatched_b,
                            n_common_cells=res.n_common_cells, n=len(a) + len(b)))

    transitions = [(p, s) for p, s in zip(seasons, seasons[1:])
                   if parse_season_start_year(s) == parse_season_start_year(p) + 1]
    for w in MODULE2_WINDOWS:
        for prev, cur in transitions:
            add("1_transition", prev, cur, w, "covariates", by_season[prev].iloc[-w:], by_season[cur].iloc[:w],
                cov, dummies)
    for season in seasons:
        rows = by_season[season]
        pos = rows["position"].to_numpy()
        a = rows[(pos >= END_SEASON_A[0]) & (pos <= END_SEASON_A[1])]
        b = rows[(pos >= END_SEASON_B[0]) & (pos <= END_SEASON_B[1])]
        add("3_end_season", season, season, "", "without_flag", a, b, cov, dummies)
        add("3_end_season", season, season, "", "with_flag", a, b, cov + [NO_OBJECTIVES], dummies + [len(cov)])
    return records


def out_of_support_at_date(data: Module2Data, season: str, decision_date: np.datetime64, window: int,
                           match_x: np.ndarray, dummy_columns: Sequence[int]) -> np.ndarray | None:
    """Regola "fuori supporto" alla data di decisione con la finestra A del Modulo 2.

    La finestra A sono le W partite che precedono le ultime W fra quelle con Date < D della
    catena della stagione (module2.module2_at_date). Restituisce None se il Modulo 2 non è
    attivo (meno di 2W partite anteriori).
    """
    chain = data.chain[np.flatnonzero(data.seasons == season)[0]]
    eligible = np.flatnonzero((data.chain == chain) & eligible_mask(data.dates, decision_date))
    if eligible.size < 2 * window:
        return None
    window_a = data.x[eligible[-2 * window:-window]]
    return out_of_support_mask(window_a, match_x, dummy_columns)


def support_records(frame: pd.DataFrame, covariates: Sequence[str], raw: pd.DataFrame) -> list[dict[str, object]]:
    """Quota di partite fuori supporto nei matchday 1–10 di ogni stagione, per W e gruppo."""
    data = prepare_module2_data(frame, covariates)
    dummies = [i for i, c in enumerate(covariates) if c.startswith("flag_")]
    status = entry_status_by_team_season(raw)
    seasons = sorted(set(frame["season"]), key=parse_season_start_year)
    records: list[dict[str, object]] = []
    for season in seasons:
        rows = frame[(frame["season"] == season) & (frame["position"] <= SUPPORT_POSITIONS[1])]
        groups = np.where(
            [status[(season, h)] == "new" or status[(season, a)] == "new" for h, a in zip(rows["HomeTeam"], rows["AwayTeam"])],
            "new",
            np.where([status[(season, h)] == "returning" or status[(season, a)] == "returning"
                      for h, a in zip(rows["HomeTeam"], rows["AwayTeam"])], "returning", "none"),
        )
        for w in MODULE2_WINDOWS:
            out = np.full(len(rows), np.nan)
            for d in np.unique(rows["Date"].to_numpy(dtype="datetime64[ns]")):
                today = (rows["Date"].to_numpy(dtype="datetime64[ns]") == d)
                mask = out_of_support_at_date(data, season, d, w, rows.loc[today, list(covariates)].to_numpy(float), dummies)
                if mask is not None:
                    out[today] = mask
            for group in ("new", "returning", "none", "all"):
                sel = (groups == group) if group != "all" else np.ones(len(rows), dtype=bool)
                active = sel & ~np.isnan(out)
                n_out = int(np.nansum(out[active]))
                records.append(_rec(row_type="support", season=season, window=w, group=group,
                                    n=int(active.sum()), n_out=n_out,
                                    share=float(n_out / active.sum()) if active.sum() else ""))
    return records


def evaluate_did_support(frame: pd.DataFrame, covariates: Sequence[str], raw: pd.DataFrame,
                         seed: int = SEED_S8) -> list[dict[str, object]]:
    """Tutti i record del CSV results/us_c7_4_did_support.csv."""
    return did_records(frame, raw, seed) + nopo_records(frame, covariates) + support_records(frame, covariates, raw)
