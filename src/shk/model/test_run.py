"""Esecuzione unica sul test set 2023-24.

La stagione è un parametro, così la stessa catena gira prima su una stagione di validazione
con lo stesso fit (prova, uscite in build/scratch) e poi una sola volta sul 2023-24.
Parametri degli agenti solo da config/frozen_params.toml (loader e check_frozen_constants);
catena del Modulo 2 tagliata alla stagione, come in calibrazione e nelle esecuzioni congelate.

Contenuto:
- residui del Modulo 1 con la stagione aggiunta allo schema del suo fit (load_residuals_for);
  le righe della stagione nel DataFrame del Modulo 2 hanno ruolo "test";
- anti-leakage del fornitore: walkforward_split e assert_no_leakage su ogni partita;
- log-loss e ĝ dei cinque metodi sulle due serie (b365_prematch, pinnacle_closing), con
  intervalli come nell'inferenza su ĝ per una stagione: stationary bootstrap a L_PW e iid, percentile;
- Oaxaca-Blinder a ogni data con la W congelata dello schema;
- agenti dell'esecuzione congelata sulla validazione (A e B_0.25) su N_SEEDS seed (stationary
  bootstrap delle date a L_PW) e sulla realizzazione osservata, più un run iid (L = 1);
- stratificazione per neopromossa (stato d'ingresso "new" o "returning") e per le partite fra
  squadre note: δ̄ e log-loss media con intervallo (stationary bootstrap della serie del
  gruppo a L_PW), frazione media di B_0.25 con F = 0 sulla realizzazione osservata.

Modulo 1 come parametro: con "dixon_coles" residui e previsioni vengono da Dixon-Coles
(DC_FITS) e i parametri da config/frozen_params_dc.toml (frozen_params_path).

Seed: SeedSequence(SEED_S10).spawn(5)[3] (posizione 3), spawn(4): figlio 0 seed block
(spawn(N_SEEDS)), figlio 1 seed iid (spawn(N_SEEDS)), figlio 2 non più usato (indici dei
confronti fra agenti, tolti), figlio 3 intervalli: spawn(2), il primo per ĝ e log-loss, il
secondo per gli strati.
"""

import copy
import hashlib
import math
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Final, NamedTuple

import numpy as np
import pandas as pd

from shk.data.split import read_split_config
from shk.data.walkforward import LeakageError, assert_no_leakage, walkforward_split
from shk.kelly.agents import AGENT_B_LAMBDA, DateView, FractionalKellyAgent, estimated_expected_values
from shk.kelly.environment import run_paired_backtest
from shk.model.comparisons import percentile_interval
from shk.model.covariate_inspection import derive_specification
from shk.model.elo_fit import ELO_FITS
from shk.model.frozen_agents import AGENT_ORDER, check_frozen_constants, scheme_window
from shk.model.frozen_params import frozen_params_path, load_frozen_params
from shk.model.g_hat_inference import Q_FIELDS, season_bootstrap_means, stationary_length
from shk.model.module2 import STATE_ACTIVE, module2_at_date, prepare_module2_data
from shk.model.module2_data import STATUS_NEW, STATUS_RETURNING, build_module2_frame, entry_status_by_team_season
from shk.model.paired_backtest import CONFIGURATIONS
from shk.model.module1 import MODULE1_ELO
from shk.model.residuals import ModelResidualsData, load_match_frame, model_residuals_data
from shk.model.scoring import (
    ALL_DEVIG_METHODS,
    MATCH_KEYS,
    SERIES_NAMES,
    align_predictions_with_odds,
    compute_g_hat_terms,
    generate_validation_predictions,
    prepare_series_evaluation,
)
from shk.model.season_bootstrap import reconstruct_season, season_block_length
from shk.model.task_seeds import N_STORY_TASKS, story_task_sequence
from shk.model.season_input import SeasonInput, season_input_from_frame
from shk.model.validation_run import METRICS, SEED_S10, ValidationResult, run_instance, summary_records

TEST_SEASON: Final[str] = "2023-24"
TEST_FIT: Final[str] = "2020-21"
DRY_RUN_SEASON: Final[str] = "2022-23"
T58_STORY_POSITION: Final[int] = 3
N_BOOT: Final[int] = 999
FROZEN_COMMIT_SHA256: Final[str] = "e999a5eb72a6ba6bbe5f7a1746250d78f615ed4bc2cb1ada5910bfa1dfaf7f06"
B365_COLUMNS: Final[tuple[str, ...]] = ("B365H", "B365D", "B365A")

TEST_RUN_COLUMNS: Final[tuple[str, ...]] = (
    "row_type", "season", "fit_through", "series", "method", "window", "date", "config", "min_stake",
    "agent", "group", "team", "status",
    "n", "estimate", "ci_low", "ci_high", "ci_iid_low", "ci_iid_high", "l_pw",
    "log_loss_model", "log_loss_market", "mean_ln_pi",
    "state", "total", "structural", "structural_share", "structural_alarm",
    "n_seeds", "median_log_wealth", "q05_log_wealth", "q95_log_wealth", "mean_log_wealth", "ruin_rate",
    "g_ce_1", "g_ce_2", "g_ce_5", "median_max_drawdown", "mean_n_bets", "mean_share_lambda_zero", "mean_n_alarms",
    "observed_log_wealth", "observed_max_drawdown", "observed_n_bets", "observed_ruined",
    "observed_share_lambda_zero", "observed_n_alarms",
    "delta_low", "delta_high", "log_loss_low", "log_loss_high", "mean_fraction_b025",
    "frozen_sha256", "frozen_commit_sha256", "n_matches_checked", "leakage_violations", "b365_complete",
)


def _row(**fields: object) -> dict[str, object]:
    rec = {c: "" for c in TEST_RUN_COLUMNS}
    rec.update(fields)
    return rec


def t58_sequences(seed: int | np.random.SeedSequence = SEED_S10) -> list[np.random.SeedSequence]:
    """Quattro figli di SeedSequence(SEED_S10).spawn(5)[3] (vedi modulo); seed è la radice."""
    return story_task_sequence(seed, T58_STORY_POSITION, N_STORY_TASKS).spawn(4)


class SeasonData(NamedTuple):
    """Dati della stagione da eseguire."""

    season: str
    fit: str
    residuals: ModelResidualsData
    frame: pd.DataFrame       # DataFrame del Modulo 2 della sola stagione, ruolo "test"
    covariates: tuple[str, ...]
    inp: SeasonInput
    devig_method: str = "shin"  # metodo di q (Shin; gli altri per la sensibilità al de-vigging)


def load_season_data(season: str, fit: str = TEST_FIT, module1: str = MODULE1_ELO,
                     devig_method: str = "shin") -> SeasonData:
    """Residui con la stagione nello schema del fit, DataFrame del Modulo 2 e ingressi dell'ambiente.

    La specificazione delle covariate resta quella scelta sul training (derive_specification).
    """
    cfg = read_split_config()
    roles = ("history", "training", "validation") + (("test",) if season in cfg.test else ())
    df, schedule = load_match_frame(roles=roles)
    schedule = copy.deepcopy(schedule)
    if season not in schedule[fit]["validation"]:
        schedule[fit]["validation"] = list(schedule[fit]["validation"]) + [season]
    data = model_residuals_data(df, schedule, module1=module1)
    frame = build_module2_frame(data, devig_method=devig_method)
    covariates = derive_specification(frame[frame["role"] == "training"]).covariates
    season_frame = frame[frame["season"] == season].assign(role="test")
    return SeasonData(season, fit, data, season_frame, tuple(covariates),
                      season_input_from_frame(season_frame, season, covariates), devig_method)


def season_params_path(sd: SeasonData) -> Path:
    """File dei parametri congelati del Modulo 1 della stagione."""
    return frozen_params_path(sd.residuals.module1)


def validation_predictions(sd: SeasonData) -> pd.DataFrame:
    """Previsioni di validazione del Modulo 1 (con la stagione), ordinate per Date.

    Per l'Elo come nel calcolo di ĝ (generate_validation_predictions); per Dixon-Coles dalle righe di
    validazione dei residui, che contengono le stesse previsioni.
    """
    df, schedule = sd.residuals.df, sd.residuals.schedule
    if sd.residuals.module1 == MODULE1_ELO:
        return generate_validation_predictions(df, ELO_FITS, schedule)
    res = sd.residuals.residuals
    preds = res.loc[res["role"] == "validation", list(MATCH_KEYS) + ["p_home", "p_draw", "p_away"]]
    return preds.sort_values("Date", kind="stable").reset_index(drop=True)


def check_records(sd: SeasonData) -> list[dict[str, object]]:
    """Anti-leakage del fornitore, completezza della terna B365, hash del file congelato letto dal loader."""
    df = sd.residuals.df
    n_checked = violations = 0
    for history, match in walkforward_split(df, [sd.season]):
        n_checked += 1
        try:
            assert_no_leakage(history, match)
        except LeakageError:
            violations += 1
    season_rows = df[df["season"] == sd.season]
    odds = season_rows[list(B365_COLUMNS)].apply(pd.to_numeric, errors="coerce")
    complete = bool(odds.notna().all().all() and (odds > 1.0).all().all())
    load_frozen_params(season_params_path(sd))
    file_sha = hashlib.sha256(season_params_path(sd).read_bytes()).hexdigest()
    return [_row(row_type="check", season=sd.season, fit_through=sd.fit, n=len(season_rows),
                 n_matches_checked=n_checked, leakage_violations=violations, b365_complete=complete,
                 frozen_sha256=file_sha, frozen_commit_sha256=FROZEN_COMMIT_SHA256)]


def g_hat_records(sd: SeasonData, seq: np.random.SeedSequence) -> list[dict[str, object]]:
    """Log-loss e ĝ dei cinque metodi sulle due serie per la stagione, con intervalli stationary e iid."""
    df, schedule = sd.residuals.df, sd.residuals.schedule
    aligned = align_predictions_with_odds(validation_predictions(sd), df)
    records = []
    children = iter(seq.spawn(len(SERIES_NAMES) * (len(ALL_DEVIG_METHODS) + 1)))
    for series in SERIES_NAMES:
        ev = prepare_series_evaluation(aligned, series, schedule)
        sel = ev.df_used["season"].astype(str).to_numpy() == sd.season
        y = pd.Series(ev.outcomes[sel]).map({"H": 0, "D": 1, "A": 2}).to_numpy()
        rows = np.arange(y.size)
        ll = -np.log(ev.p_model[sel][rows, y]) if y.size else np.array([])
        if y.size:
            length = stationary_length(ll)
            b, i = (np.random.default_rng(c) for c in next(children).spawn(2))
            lo, hi = percentile_interval(season_bootstrap_means(ll, length, b, N_BOOT))
            ilo, ihi = percentile_interval(season_bootstrap_means(ll, 1.0, i, N_BOOT))
            records.append(_row(row_type="log_loss", season=sd.season, fit_through=sd.fit, series=series,
                                n=int(y.size), estimate=float(ll.mean()), ci_low=lo, ci_high=hi, ci_iid_low=ilo,
                                ci_iid_high=ihi, l_pw=length))
        else:
            next(children)
        cols = {"b365_prematch": ("B365H", "B365D", "B365A"), "pinnacle_closing": ("PSCH", "PSCD", "PSCA")}[series]
        odds = ev.df_used.loc[sel, list(cols)].apply(pd.to_numeric).to_numpy(dtype=np.float64)
        ln_pi = float(np.log((1.0 / odds).sum(axis=1)).mean()) if y.size else math.nan
        for method in ALL_DEVIG_METHODS:
            child = next(children)
            if not y.size:
                records.append(_row(row_type="g_hat", season=sd.season, series=series, method=method, n=0))
                continue
            q = getattr(ev, Q_FIELDS[method])[sel]
            terms = compute_g_hat_terms(ev.p_model[sel], q, ev.outcomes[sel])
            length = stationary_length(terms)
            b, i = (np.random.default_rng(c) for c in child.spawn(2))
            lo, hi = percentile_interval(season_bootstrap_means(terms, length, b, N_BOOT))
            ilo, ihi = percentile_interval(season_bootstrap_means(terms, 1.0, i, N_BOOT))
            records.append(_row(row_type="g_hat", season=sd.season, fit_through=sd.fit, series=series, method=method,
                                n=int(terms.size), estimate=float(terms.mean()), ci_low=lo, ci_high=hi,
                                ci_iid_low=ilo, ci_iid_high=ihi, l_pw=length,
                                log_loss_model=float(ll.mean()),
                                log_loss_market=float(-np.log(q[rows, y]).mean()), mean_ln_pi=ln_pi))
    return records


def module2_records(sd: SeasonData) -> list[dict[str, object]]:
    """Oaxaca-Blinder a ogni data della stagione con la W congelata dello schema (catena tagliata alla stagione)."""
    params = load_frozen_params(season_params_path(sd))
    data = prepare_module2_data(sd.frame, list(sd.covariates))
    threshold = float(params.c1_thresholds[sd.fit])
    w = scheme_window(params)
    out = []
    for d in np.unique(sd.inp.dates):
        m2 = module2_at_date(data, sd.season, d, w)
        active = m2.state == STATE_ACTIVE
        out.append(_row(row_type="module2", season=sd.season, fit_through=sd.fit, window=w,
                        date=str(pd.Timestamp(d).date()), state=m2.state,
                        total=m2.result.total if active else "", structural=m2.result.structural if active else "",
                        structural_share=m2.result.structural_share if active else "",
                        structural_alarm=bool(active and -m2.result.structural > threshold)))
    return out


def _seed_chunk(params_path: str, inp: SeasonInput, seed_seqs: Sequence[np.random.SeedSequence],
                block_length: float) -> np.ndarray:
    params = load_frozen_params(params_path)
    check_frozen_constants(params)
    covariates = list(params.fixed["covariates"])
    out = np.full((len(CONFIGURATIONS), len(AGENT_ORDER), len(METRICS), len(seed_seqs)), np.nan)
    for k, ss in enumerate(seed_seqs):
        rec = reconstruct_season(inp, np.random.default_rng(ss), block_length, covariates=covariates)
        out[..., k] = run_instance(params, rec)
    return out


def run_seeds(sd: SeasonData, seqs: Sequence[np.random.SeedSequence], block_length: float, workers: int = 1,
              chunk: int = 50) -> np.ndarray:
    """Agenti dell'esecuzione congelata sulla validazione sui seed della stagione: (C, A, M, N)."""
    parts = [seqs[i:i + chunk] for i in range(0, len(seqs), chunk)]
    args = [(str(season_params_path(sd)), sd.inp, p, block_length) for p in parts]
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            outs = list(pool.map(_seed_chunk, *zip(*args)))
    else:
        outs = [_seed_chunk(*a) for a in args]
    return np.concatenate(outs, axis=-1)


class TestResult(NamedTuple):
    """Uscite degli agenti: block e iid nella forma di ValidationResult con una stagione."""

    block: ValidationResult
    iid: ValidationResult


def evaluate_agents(sd: SeasonData, workers: int = 1, seed: int | np.random.SeedSequence = SEED_S10) -> TestResult:
    """Seed block (L_PW), seed iid (L = 1) e realizzazione osservata."""
    params = load_frozen_params(season_params_path(sd))
    check_frozen_constants(params)
    n = int(params.fixed["n_seeds"])
    seq_block, seq_iid = t58_sequences(seed)[:2]
    l_pw = season_block_length(sd.inp)
    block = run_seeds(sd, seq_block.spawn(n), l_pw, workers)
    iid = run_seeds(sd, seq_iid.spawn(n), 1.0, workers)
    observed = run_instance(params, sd.inp)
    n_dates = np.array([np.unique(sd.inp.dates).shape[0]])
    make = lambda seeds, l: ValidationResult((sd.season,), (sd.fit,), n_dates, np.array([l]), seeds[None], observed[None])
    return TestResult(make(block, l_pw), make(iid, 1))


def agent_summary_records(result: TestResult) -> list[dict[str, object]]:
    """Sintesi per agente × configurazione come l'esecuzione congelata sulla validazione (seed block e realizzazione osservata)."""
    out = []
    for rec in summary_records(result.block):
        row = _row(row_type="summary")
        row.update({k: v for k, v in rec.items() if k in TEST_RUN_COLUMNS and k != "row_type"})
        out.append(row)
    return out


class _RecB(FractionalKellyAgent):
    """B_0.25 che registra le frazioni per partita della data."""

    def __init__(self, name: str, lam: float) -> None:
        super().__init__(name, lam)
        self.fractions: dict[np.datetime64, np.ndarray] = {}

    def stake_fractions(self, view: DateView, p_hat: np.ndarray, b: np.ndarray) -> np.ndarray:
        f = super().stake_fractions(view, p_hat, b)
        self.fractions[np.datetime64(view.date, "ns")] = _per_match(view, f)
        return f


def _per_match(view: DateView, selected_fractions: np.ndarray) -> np.ndarray:
    ev = estimated_expected_values(view.probs, view.odds)
    out = np.zeros(ev.shape[0])
    out[np.flatnonzero(ev.max(axis=1) > 0.0)] = selected_fractions
    return out


def stratum_records(sd: SeasonData, seed: int | np.random.SeedSequence = SEED_S10) -> list[dict[str, object]]:
    """Stratificazione per neopromossa e per le squadre note (vedi modulo)."""
    b_agent = _RecB("B_0.25", AGENT_B_LAMBDA)
    run_paired_backtest([b_agent], sd.inp.dates, sd.inp.probs, sd.inp.odds, sd.inp.outcomes, 0.0)
    days = sd.inp.dates
    frac_b = np.zeros(days.size)
    for d in np.unique(days):
        frac_b[np.flatnonzero(days == d)] = b_agent.fractions[d]
    frame = sd.frame.sort_values("Date", kind="stable")
    home, away = frame["HomeTeam"].to_numpy(), frame["AwayTeam"].to_numpy()
    status = entry_status_by_team_season(sd.residuals.df)
    promoted = sorted({t for t in set(home) | set(away) if status.get((sd.season, t)) in (STATUS_NEW, STATUS_RETURNING)})
    res = sd.residuals.residuals
    ll_rows = res[(res["season"] == sd.season) & (res["fit_through"] == sd.fit)]
    ll_map = {(pd.Timestamp(d), h, a): v for d, h, a, v in
              zip(ll_rows["Date"], ll_rows["HomeTeam"], ll_rows["AwayTeam"], ll_rows["log_loss"])}
    log_loss = np.array([ll_map[(pd.Timestamp(d), h, a)] for d, h, a in zip(frame["Date"], home, away)])
    delta = frame["delta"].to_numpy(dtype=np.float64)
    groups = [(t, status[(sd.season, t)], (home == t) | (away == t)) for t in promoted]
    known = ~np.isin(home, promoted) & ~np.isin(away, promoted)
    groups.append(("known", "known", known))
    out = []
    children = t58_sequences(seed)[3].spawn(2)[1].spawn(len(groups))
    for (team, st, sel), child in zip(groups, children):
        r1, r2 = (np.random.default_rng(c) for c in child.spawn(2))
        x, ll = delta[sel], log_loss[sel]
        dlo, dhi = percentile_interval(season_bootstrap_means(x, stationary_length(x), r1, N_BOOT))
        llo, lhi = percentile_interval(season_bootstrap_means(ll, stationary_length(ll), r2, N_BOOT))
        out.append(_row(row_type="stratum", season=sd.season, group="promoted" if team != "known" else "known",
                        team=team, status=st, n=int(sel.sum()), estimate=float(x.mean()), delta_low=dlo,
                        delta_high=dhi, log_loss_model=float(ll.mean()), log_loss_low=llo, log_loss_high=lhi,
                        mean_fraction_b025=float(frac_b[sel].mean())))
    return out
