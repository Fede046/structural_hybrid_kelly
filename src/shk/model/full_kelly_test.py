"""Nuova tesi (thesis/TESI_kellybench.md, capitolo 4): Kelly pieno, freno e freno casuale sul 2023-24.

Regole fissate prima del test (decisioni del 2026-11-21):
- modello Elo-Davidson stimato una volta sulle stagioni dal 2000-01 al 2022-23 (FULL_TRAINING), con
  i punteggi riscaldati dal 1993-94; il 2023-24 è previsto walk-forward con i parametri fissi;
- riferimento del supervisore: tutte le partite delle stagioni dal 2002-03 al 2022-23 (REFERENCE),
  con gli stessi parametri; ANOVA sulla media e sulla dispersione, finestra delle ultime 40 partite;
- soglie dell'allarme al livello α/2 ciascuna sul massimo di una stagione senza cambiamenti: ogni
  stagione nulla è un ricampionamento a blocchi del riferimento lungo quanto una stagione, con il
  calendario delle decisioni dell'ultima stagione di riferimento (2022-23);
- diagnosi a due termini con i coefficienti stimati su tutto il riferimento, soglie come nella
  versione precedente (two_fold_diagnosis.calibrate_reference_diagnosis);
- freno: λ = 1 senza allarme, 0,75 dopo un errore nei dati, 0,40 dopo un errore strutturale,
  finché dura l'allarme (FREE_LAMBDA, DATA_LAMBDA, STRUCTURAL_LAMBDA);
- prova su tutte le stagioni (us_c42): per ogni stagione dal FIRST_ROLLING_TEST al 2023-24 le
  stesse regole, con modello e riferimento stimati sulle sole stagioni precedenti;
- freno casuale: lo stesso calendario di allarmi (numero, tipo, durata) spostato a caso fra le
  giornate in cui il confronto è possibile, senza sovrapposizioni (random_calendar).
"""

from collections.abc import Sequence
from typing import Final, NamedTuple

import numpy as np
import pandas as pd

from shk.kelly.agents import Agent, DateView
from shk.model.agent_c import N_BOOT, reference_statistics
from shk.model.elo_fit import EloFitParams, calibrate_single_fit, parse_season_start_year
from shk.model.elo_predictor import ENTRY_PLAIN, ENTRY_RULE
from shk.model.module2_data import build_module2_frame
from shk.model.residuals import ModelResidualsData, model_residuals_data
from shk.model.scheme_run import fit_block_length
from shk.model.season_input import SeasonInput, season_input_from_frame
from shk.model.season_thresholds import decision_ends
from shk.stats.calibration import compute_order_statistic_index, moving_block_indices
from shk.stats.false_rejection import ALPHA

SEED_S41: Final[int] = 20261121
FIT_KEY: Final[str] = "2022-23"
TEST_SEASON: Final[str] = "2023-24"
FULL_TRAINING: Final[tuple[str, ...]] = tuple(f"{y}-{str(y + 1)[-2:]}" for y in range(2000, 2023))
REFERENCE: Final[tuple[str, ...]] = tuple(f"{y}-{str(y + 1)[-2:]}" for y in range(2002, 2023))
FIRST_ROLLING_TEST: Final[str] = "2003-04"
CALENDAR_SEASON: Final[str] = "2022-23"
FREE_LAMBDA: Final[float] = 1.0
DATA_LAMBDA: Final[float] = 0.75
STRUCTURAL_LAMBDA: Final[float] = 0.40
KAPPA: Final[float] = DATA_LAMBDA / FREE_LAMBDA
LEVELS: Final[dict[str, float]] = {"none": FREE_LAMBDA, "compositional": DATA_LAMBDA, "structural": STRUCTURAL_LAMBDA}


def season_label(year: int) -> str:
    """2002 -> "2002-03"."""
    return f"{year}-{str(year + 1)[-2:]}"


def previous_season(season: str) -> str:
    """La stagione precedente: "2023-24" -> "2022-23"."""
    return season_label(parse_season_start_year(season) - 1)


def past_training(test_season: str) -> tuple[str, ...]:
    """Le stagioni per la stima del modello prima di test_season: dal 2000-01 alla precedente."""
    return tuple(season_label(y) for y in range(2000, parse_season_start_year(test_season)))


def past_reference(test_season: str) -> tuple[str, ...]:
    """Le stagioni del riferimento prima di test_season: dal 2002-03 (prime quote Bet365) alla precedente."""
    return tuple(season_label(y) for y in range(2002, parse_season_start_year(test_season)))


def require_plain_entry() -> None:
    """La nuova tesi usa l'Elo senza regola per le neopromosse (SHK_ELO_ENTRY=plain, vedi elo_predictor)."""
    if ENTRY_RULE != ENTRY_PLAIN:
        raise RuntimeError("set SHK_ELO_ENTRY=plain before importing shk (new thesis: no promoted-team rule)")


def fit_full_model(df: pd.DataFrame, test_season: str = TEST_SEASON) -> EloFitParams:
    """K, h, ν stimati una volta sulle stagioni prima di test_season (punteggi dal 1993-94)."""
    require_plain_entry()
    res = calibrate_single_fit(df, previous_season(test_season), list(past_training(test_season)))
    return EloFitParams(k=res.k, h=res.h, nu=res.nu, c=res.c)


def full_residuals(df: pd.DataFrame, params: EloFitParams, include_test: bool,
                   test_season: str = TEST_SEASON) -> ModelResidualsData:
    """Residui del fit unico: le stagioni passate come training e, se include_test, la stagione di test."""
    fit = previous_season(test_season)
    schedule = {fit: {"training": list(past_training(test_season)),
                      "validation": [test_season] if include_test else []}}
    return model_residuals_data(df, schedule, {fit: params})


def full_frame(data: ModelResidualsData, test_season: str = TEST_SEASON) -> pd.DataFrame:
    """DataFrame del Modulo 2 per le stagioni del riferimento e per la stagione di test (quote Bet365).

    build_module2_frame tiene del training solo la stagione uguale a fit_through: qui ogni stagione di
    riferimento diventa il proprio fit_through, così entrano tutte; il 2000-01 e il 2001-02, senza
    quote Bet365 complete, servono solo alla stima del modello e restano fuori.
    """
    res = data.residuals
    keep = res["season"].isin(past_reference(test_season) + (test_season,))
    res = res[keep].copy()
    training = res["role"] == "training"
    res.loc[training, "fit_through"] = res.loc[training, "season"]
    frame = build_module2_frame(data._replace(residuals=res))
    frame["fit_through"] = previous_season(test_season)
    return frame


class PooledReference(NamedTuple):
    """Il riferimento: partite di più stagioni in ordine di data."""

    x: np.ndarray
    delta: np.ndarray
    dates: np.ndarray
    seasons: np.ndarray


def pooled_reference(frame: pd.DataFrame, covariates: Sequence[str],
                     seasons: Sequence[str] = REFERENCE) -> PooledReference:
    """Tutte le partite delle stagioni del riferimento, ordinate per stagione e data."""
    rows = frame[frame["season"].isin(list(seasons))].copy()
    rows["season_year"] = rows["season"].map(parse_season_start_year)
    rows = rows.sort_values(["season_year", "Date"], kind="stable")
    return PooledReference(rows[list(covariates)].to_numpy(np.float64), rows["delta"].to_numpy(np.float64),
                           rows["Date"].to_numpy("datetime64[ns]"), rows["season"].to_numpy())


def pooled_block_length(ref: PooledReference) -> int:
    """L_PW circolare della serie di δ del riferimento (come scheme_run.fit_block_length)."""
    inp = SeasonInput("reference", ref.dates, np.full((ref.delta.shape[0], 3), 1 / 3), np.full((ref.delta.shape[0], 3), 3.0),
                      np.zeros((1, ref.delta.shape[0]), dtype=np.int64), ref.x, ref.delta)
    return fit_block_length(inp)


def pooled_alarm_thresholds(ref: PooledReference, calendar_dates: np.ndarray, window: int, block_length: int,
                            rng: np.random.Generator, n_boot: int = N_BOOT,
                            alpha: float = ALPHA) -> tuple[float, float]:
    """Soglie (media, dispersione) con livello α sull'intera stagione, dal riferimento di più stagioni.

    Ogni stagione nulla ricampiona a blocchi il riferimento fino alla lunghezza del calendario
    (n partite); le decisioni sono quelle del calendario, sulle finestre delle ultime W partite.
    """
    y = ref.delta
    n = np.asarray(calendar_dates).shape[0]
    ends = decision_ends(calendar_dates, window)
    idx = moving_block_indices(y.shape[0], block_length, n_boot, rng)[:, :n]
    windows = idx[:, (ends[:, None] - window + np.arange(window)[None, :])]
    f_mean, f_disp = reference_statistics(y, y[windows].reshape(-1, window))
    k = compute_order_statistic_index(n_boot, alpha / 2.0)
    max_mean = np.sort(f_mean.reshape(n_boot, -1).max(axis=1))
    max_disp = np.sort(f_disp.reshape(n_boot, -1).max(axis=1))
    return float(max_mean[k - 1]), float(max_disp[k - 1])


def pooled_unexplained_thresholds(ref: PooledReference, diagnosis, calendar_dates: np.ndarray, window: int,
                                  block_length: int, rng: np.random.Generator, n_boot: int = N_BOOT,
                                  alpha: float = ALPHA) -> tuple[float, float]:
    """Soglie delle parti non spiegate (media, dispersione) con la stessa severità del supervisore.

    Come pooled_alarm_thresholds: ogni stagione nulla ricampiona a blocchi il riferimento fino alla
    lunghezza del calendario; su ogni finestra di decisione si calcola la parte non spiegata della
    scomposizione a due termini (coefficienti, mediana del riferimento in `diagnosis`); la soglia è il
    quantile α/2 del massimo della stagione. L'errore è strutturale solo se la parte non spiegata, da
    sola, supera una soglia severa quanto quella dell'allarme.
    """
    design = np.concatenate([np.ones((ref.x.shape[0], 1)), ref.x], axis=1)
    r_mean = ref.delta - design @ diagnosis.beta_mean
    r_disp = np.abs(ref.delta - diagnosis.median) - design @ diagnosis.beta_dispersion
    n = np.asarray(calendar_dates).shape[0]
    ends = decision_ends(calendar_dates, window)
    idx = moving_block_indices(ref.delta.shape[0], block_length, n_boot, rng)[:, :n]
    windows = idx[:, (ends[:, None] - window + np.arange(window)[None, :])]  # (B, decisioni, W)
    u_mean = (-r_mean[windows].mean(axis=-1)).max(axis=1)
    u_disp = r_disp[windows].mean(axis=-1).max(axis=1)
    k = compute_order_statistic_index(n_boot, alpha / 2.0)
    return float(np.sort(u_mean)[k - 1]), float(np.sort(u_disp)[k - 1])


class ScheduledKellyAgent(Agent):
    """Kelly pieno con λ fissato per data (freno casuale e controlli)."""

    def __init__(self, name: str, lam_by_date: dict) -> None:
        super().__init__(name)
        self._lam = {np.datetime64(d, "ns"): float(v) for d, v in lam_by_date.items()}

    def stake_fractions(self, view: DateView, p_hat: np.ndarray, b: np.ndarray) -> np.ndarray:
        lam = self._lam.get(np.datetime64(view.date, "ns"), FREE_LAMBDA)
        p, bb = np.asarray(p_hat, dtype=np.float64), np.asarray(b, dtype=np.float64)
        # kelly_staking vettorizzata: λ · max(0, (b p − (1 − p)) / b)
        return lam * np.maximum(0.0, (bb * p - (1.0 - p)) / bb)


class Episode(NamedTuple):
    """Un tratto di giornate consecutive con la stessa diagnosi diversa da "none"."""

    diagnosis: str
    length: int


def episodes(diagnoses: Sequence[str]) -> list[Episode]:
    """Gli allarmi del calendario, nell'ordine: tratti massimi di giornate con la stessa diagnosi."""
    out: list[Episode] = []
    prev = "none"
    for d in diagnoses:
        if d != "none" and d == prev:
            out[-1] = Episode(d, out[-1].length + 1)
        elif d != "none":
            out.append(Episode(d, 1))
        prev = d
    return out


def random_calendar(eps: Sequence[Episode], n_days: int, first_day: int, rng: np.random.Generator) -> np.ndarray:
    """Diagnosi per giornata con gli stessi episodi in ordine casuale e posizioni casuali, senza sovrapporsi.

    Le giornate da first_day a n_days − 1 sono quelle in cui il confronto è possibile. Il posto libero
    (giornate non coperte dagli episodi) si divide a caso negli spazi prima, fra e dopo gli episodi:
    ogni disposizione degli spazi è ugualmente probabile.
    """
    out = np.array(["none"] * n_days, dtype=object)
    if not eps:
        return out
    order = rng.permutation(len(eps))
    lengths = np.array([eps[i].length for i in order])
    free = (n_days - first_day) - int(lengths.sum())
    if free < 0:
        raise ValueError("the episodes do not fit in the eligible days")
    # Spazi: len(eps) + 1 numeri non negativi con somma free (stelle e barre)
    cuts = np.sort(rng.choice(free + len(eps), size=len(eps), replace=False))
    gaps = np.diff(np.concatenate([[-1], cuts])) - 1
    pos = first_day
    for g, i in zip(gaps, order):
        pos += int(g)
        out[pos:pos + eps[i].length] = eps[i].diagnosis
        pos += eps[i].length
    return out


def lambda_schedule(dates: Sequence, diagnoses: Sequence[str]) -> dict:
    """λ per data dalla diagnosi di ciascuna giornata."""
    return {np.datetime64(d, "ns"): LEVELS[str(g)] for d, g in zip(dates, diagnoses)}


def test_input(frame: pd.DataFrame, covariates: Sequence[str], test_season: str = TEST_SEASON) -> SeasonInput:
    """Ingressi dell'ambiente per la stagione di test."""
    return season_input_from_frame(frame[frame["season"] == test_season], test_season, covariates)


def weighted_refit(df: pd.DataFrame, season: str, before: np.datetime64, half_life: float) -> EloFitParams:
    """K, h, ν che minimizzano la log-loss pesata sulle stagioni passate e sulle partite di `season` prima di `before`.

    Il peso di una partita si dimezza ogni `half_life` stagioni di età: la stagione in corso pesa 1, la
    precedente 0,5 con half_life = 1, e così via. Stessi punteggi di partenza, limiti e ottimizzatore di
    elo_fit.calibrate_single_fit; c è la frequenza dei pareggi, pesata allo stesso modo.
    """
    from scipy.optimize import minimize

    from shk.model.elo_fit import INITIAL_PARAMS, OPTIMIZER_METHOD, OPTIMIZER_OPTIONS, PARAM_BOUNDS
    from shk.model.elo_predictor import predict_elo_fast

    require_plain_entry()
    year = parse_season_start_year(season)
    keep = (df["season"].map(parse_season_start_year) <= year) & (
        (df["season"] != season) | (df["Date"].to_numpy("datetime64[ns]") < before))
    sub = df[keep].reset_index(drop=True)
    training = list(past_training(season)) + [season]
    truth = sub[sub["season"].isin(training)].reset_index(drop=True)
    age = year - truth["season"].map(parse_season_start_year).to_numpy()
    weight = 0.5 ** (age / half_life)
    weight = weight / weight.sum()
    ftr = truth["FTR"].to_numpy()

    def loss(params: np.ndarray) -> float:
        preds = predict_elo_fast(sub, training, k=float(params[0]), h=float(params[1]), nu=float(params[2]))
        p = np.where(ftr == "H", preds["p_home"], np.where(ftr == "D", preds["p_draw"], preds["p_away"]))
        return float(-(weight * np.log(np.clip(p.astype(np.float64), 1e-15, 1.0))).sum())

    res = minimize(loss, x0=np.array(INITIAL_PARAMS, dtype=np.float64), method=OPTIMIZER_METHOD,
                   bounds=PARAM_BOUNDS, options=OPTIMIZER_OPTIONS)
    c = float((weight * (ftr == "D")).sum())
    return EloFitParams(k=float(res.x[0]), h=float(res.x[1]), nu=float(res.x[2]), c=c)


def season_lambda(diagnoses: Sequence[str], until_season_end: bool) -> np.ndarray:
    """λ per giornata; con until_season_end il freno strutturale resta fino a fine stagione dal primo errore."""
    lam = np.array([LEVELS[str(g)] for g in diagnoses], dtype=np.float64)
    if until_season_end:
        hits = np.flatnonzero(np.asarray(diagnoses, dtype=object) == "structural")
        if hits.shape[0]:
            lam[hits[0]:] = np.minimum(lam[hits[0]:], STRUCTURAL_LAMBDA)
    return lam


class MinimumStakeAgent(Agent):
    """Punta ogni giornata la frazione fissa `fraction` del capitale, sola, sulla scommessa con il valore atteso più alto.

    È l'equivalente, senza puntata minima nell'ambiente, di chi punta solo il minimo come l'esecuzione
    di GPT-5.4 di KellyBench: con fraction = £0,01 / £220.
    """

    def __init__(self, name: str, fraction: float) -> None:
        super().__init__(name)
        self._fraction = float(fraction)

    def stake_fractions(self, view: DateView, p_hat: np.ndarray, b: np.ndarray) -> np.ndarray:
        p, bb = np.asarray(p_hat, dtype=np.float64), np.asarray(b, dtype=np.float64)
        out = np.zeros(p.shape[0], dtype=np.float64)
        if p.shape[0]:
            out[int(np.argmax(p * (bb + 1.0) - 1.0))] = self._fraction
        return out
