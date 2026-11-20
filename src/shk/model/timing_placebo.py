"""Controllo placebo sul momento degli interventi dello schema (stagioni vere, senza puntata minima).

Domanda: lo schema conserva più capitale del quarto di Kelly perché riduce la puntata nelle giornate
giuste, o soltanto perché punta meno? Con un vantaggio negativo qualunque regola che punta meno perde
meno, quindi il confronto con il quarto di Kelly non basta a rispondere.

Senza puntata minima ogni puntata è una frazione del capitale corrente (shk.model.population), quindi
il capitale di uno schema si ricostruisce esattamente dal suo calendario: a ogni giornata il livello
della puntata (base 0.25, ridotta 0.25·κ, nulla) e il rendimento della giornata a quel livello, preso
dal quarto di Kelly e dal Kelly a 0.25·κ con la stessa regola di scelta dell'esito.
ln W_T = Σ_d r[livello_d, d]. La ricostruzione si verifica contro il capitale dello schema.

Placebo: calendari con la stessa esposizione dello schema, ma senza l'informazione dell'allarme.
- "permutation": i livelli della stagione permutati a caso fra le giornate (stesso numero di giornate
  a ogni livello);
- "shift": il calendario della stagione ruotato di un numero casuale di giornate (stessa esposizione
  e stessa forma, per esempio un unico blocco di giornate ferme);
- "cross_season": il calendario di un'altra stagione, riportato alla lunghezza di questa per
  posizione relativa (stessi calendari, assegnati alle stagioni a caso). Controlla se lo schema
  interviene nelle stagioni giuste, mentre i primi due controllano il momento dentro la stagione.
Statistica: Σ sulle stagioni di ln W_T (capitale tipico exp(media)). p a una coda, con la
correzione (1 + #{placebo >= osservato}) / (n + 1).

Segnale: sulle stesse estrazioni, lo scarto fra la media per partita di δ nelle giornate in cui lo
schema riduce la puntata e nelle altre, e lo stesso per l'errore atteso E_q[δ] = −KL(q ‖ p̂)
(agent_c.expected_delta), che non dipende dall'esito. Se l'allarme riconosce i periodi in cui il
modello è più lontano dal mercato lo scarto è negativo; p = (1 + #{placebo <= osservato}) / (n + 1).
Le risposte "*_within" sono le stesse al netto della media per partita della stagione: con il placebo
"cross_season", che conserva la posizione dei calendari nella stagione, controllano insieme la
differenza fra stagioni (invecchiamento del modello) e l'andamento lungo la stagione.

Limite dei placebo dentro la stagione sulle grandezze realizzate (capitale, δ): l'allarme scatta dopo
una serie di errori grandi, cioè dopo giornate in cui anche le puntate sono andate male, e lo schema
in quelle giornate stava puntando. A parità di esposizione, un calendario permutato o ruotato può
evitarle e lo schema no: anche se l'allarme non portasse alcuna informazione sul futuro, lo schema
risulterebbe in media peggiore di questi placebo (tests/test_timing_placebo.py lo mostra su dati
simulati). Il placebo "cross_season" non ha questa distorsione, perché il calendario viene da
un'altra stagione, e non ce l'ha l'errore atteso, che non dipende dagli esiti.

Livello più basso: per gli schemi che dopo un errore strutturale non azzerano la puntata (versione
definitiva, λ = 0.10; shk.model.main_version) il livello 0 è quel λ invece di 0 (floor), e i suoi
rendimenti vengono dal Kelly frazionario a λ = floor con la stessa regola; il resto non cambia.

Riferimento a esposizione costante: il Kelly frazionario con λ fisso uguale al λ medio dello schema
sulle giornate delle 19 stagioni. Per la concavità della crescita in λ, a parità di esposizione media
una frazione costante rende in attesa più di un calendario acceso/spento privo di informazione: è un
riferimento più severo del placebo, e non è una strategia applicabile in anticipo (λ medio noto solo
a posteriori).
"""

from collections.abc import Mapping, Sequence
from typing import Final, NamedTuple

import numpy as np

from shk.kelly.agents import Agent, FractionalKellyAgent
from shk.kelly.environment import run_paired_backtest
from shk.kelly.outcome_rules import with_outcome_rule
from shk.market.devig import devig_probabilities
from shk.model.agent_c import Module2Supervisor, ReferenceData, SchemeAgent, expected_delta
from shk.model.frozen_agents import build_supervisor, check_frozen_constants, scheme_window
from shk.model.frozen_params import FrozenParams, load_frozen_params
from shk.model.population_run import PopulationSetup, build_population_agents
from shk.model.validation_run import ValidationSeason

SEED_S23: Final[int] = 20261110
N_DRAWS: Final[int] = 10_000
LEVEL_ZERO: Final[int] = 0
LEVEL_REDUCED: Final[int] = 1
LEVEL_BASE: Final[int] = 2
PLACEBOS: Final[tuple[str, ...]] = ("permutation", "shift", "cross_season")
RESPONSES: Final[tuple[str, ...]] = ("delta", "expected_delta", "delta_within", "expected_delta_within")
# Schema → regola di scelta dell'esito; il riferimento è il quarto di Kelly con la stessa regola
PLACEBO_ARMS: Final[dict[str, str]] = {
    "C3": "R1", "C3_stop": "R1", "C3_ref": "R1", "C3_ref_stop": "R1",
    "R3_C3": "R3", "R3_C3_ref": "R3", "R3_C3_ref_stop": "R3",
}
BASELINES: Final[dict[str, str]] = {"R1": "B_0.25", "R3": "R3_brake"}


class SeasonSchedules(NamedTuple):
    """Una stagione vera: rendimenti per livello di puntata, calendari degli schemi e residui per giornata."""

    season: str
    fit: str
    n_matches: np.ndarray                 # (D,) partite della giornata
    features: np.ndarray                  # (2, D) somme per giornata di δ e di E_q[δ]
    log_returns: dict[str, np.ndarray]    # regola → (3, D): puntata nulla, ridotta, base
    levels: dict[str, np.ndarray]         # schema → (D,) livello della giornata
    lambdas: dict[str, np.ndarray]        # schema → (D,) λ della giornata
    actual: dict[str, float]              # schema → ln W_T dell'esecuzione


def levels_from_lambda(lam: np.ndarray, base: float, kappa: float, floor: float = 0.0) -> np.ndarray:
    """Livello per giornata dal λ applicato: 0 (floor, di solito nessuna puntata), 1 (base·κ), 2 (base).

    Solleva ValueError se un λ non è uno dei tre valori dello schema.
    """
    values = np.asarray(lam, dtype=np.float64)
    levels = np.full(values.shape, -1, dtype=np.int64)
    for level, target in ((LEVEL_ZERO, floor), (LEVEL_REDUCED, base * kappa), (LEVEL_BASE, base)):
        levels[np.isclose(values, target, rtol=0.0, atol=1e-12)] = level
    if np.any(levels < 0):
        raise ValueError(f"lambda values outside {{{floor}, {base * kappa}, {base}}}: {np.unique(values[levels < 0])}")
    return levels


def schedule_log_wealth(levels: np.ndarray, log_returns: np.ndarray) -> np.ndarray:
    """ln W_T di calendari (..., D) dati i rendimenti logaritmici per livello (3, D)."""
    lv = np.asarray(levels)
    r = np.asarray(log_returns, dtype=np.float64)
    if r.ndim != 2 or r.shape[0] != 3 or lv.shape[-1] != r.shape[1]:
        raise ValueError(f"levels {lv.shape} and log_returns {r.shape} are not (..., D) and (3, D)")
    return r[lv, np.arange(r.shape[1])].sum(axis=-1)


def intervention_sums(levels: np.ndarray, features: np.ndarray) -> np.ndarray:
    """Somme (..., K) delle K grandezze per giornata (K, D) sulle giornate con puntata ridotta o nulla."""
    mask = (np.asarray(levels) < LEVEL_BASE).astype(np.float64)
    return mask @ np.asarray(features, dtype=np.float64).T


def permutation_draws(levels: np.ndarray, n: int, rng: np.random.Generator) -> np.ndarray:
    """n calendari (n, D) con i livelli permutati a caso fra le giornate."""
    return rng.permuted(np.tile(np.asarray(levels), (n, 1)), axis=1)


def shift_draws(levels: np.ndarray, n: int, rng: np.random.Generator) -> np.ndarray:
    """n calendari (n, D) ruotati di un numero di giornate uniforme in 0..D−1."""
    lv = np.asarray(levels)
    d = lv.shape[0]
    k = rng.integers(0, d, size=n)
    return lv[(np.arange(d)[None, :] - k[:, None]) % d]


def all_shifts(levels: np.ndarray) -> np.ndarray:
    """Tutte le D rotazioni del calendario, (D, D); la riga 0 è il calendario stesso."""
    lv = np.asarray(levels)
    d = lv.shape[0]
    return lv[(np.arange(d)[None, :] - np.arange(d)[:, None]) % d]


def resample_schedule(levels: np.ndarray, n_days: int) -> np.ndarray:
    """Calendario riportato a n_days giornate per posizione relativa nella stagione."""
    lv = np.asarray(levels)
    return lv[np.floor(np.arange(n_days) * lv.shape[0] / n_days).astype(np.int64)]


def cross_season_draws(levels: Sequence[np.ndarray], n: int, rng: np.random.Generator) -> list[np.ndarray]:
    """Per ogni stagione, n calendari (n, D_s): quelli delle stagioni, assegnati con una permutazione casuale."""
    s = len(levels)
    perms = np.stack([rng.permutation(s) for _ in range(n)])
    out = []
    for i, own in enumerate(levels):
        table = np.stack([resample_schedule(lv, own.shape[0]) for lv in levels])
        out.append(table[perms[:, i]])
    return out


def fresh_sequence(seq: np.random.SeedSequence) -> np.random.SeedSequence:
    """Copia nuova della SeedSequence (stessa entropia e stessa spawn_key, nessun figlio già generato).

    spawn() avanza un contatore interno: senza la copia, la stessa sequenza usata due volte darebbe
    figli diversi e i risultati dipenderebbero dall'ordine delle chiamate (vedi shk.model.task_seeds).
    """
    return np.random.SeedSequence(seq.entropy, spawn_key=seq.spawn_key, pool_size=seq.pool_size)


def one_sided_p(observed: float, draws: np.ndarray, greater: bool) -> float:
    """p a una coda con correzione: quota di estrazioni >= (o <=) dell'osservato, contando l'osservato."""
    d = np.asarray(draws, dtype=np.float64)
    d = d[np.isfinite(d)]
    hits = (d >= observed).sum() if greater else (d <= observed).sum()
    return float((1 + hits) / (1 + d.shape[0]))


def _daily(values: np.ndarray, day_index: np.ndarray, n_days: int) -> np.ndarray:
    return np.bincount(day_index, weights=values, minlength=n_days)


def run_placebo_season(params_path: str, setups: Mapping[str, PopulationSetup],
                       season: ValidationSeason) -> SeasonSchedules:
    """Esegue la stagione vera senza puntata minima e ne estrae rendimenti, calendari e residui (vedi modulo)."""
    params = load_frozen_params(params_path)
    check_frozen_constants(params)
    inp, setup = season.inp, setups[season.fit]
    supervisor = build_supervisor(params, inp)
    reference_supervisor = Module2Supervisor(inp.season, inp.dates, inp.x, list(params.fixed["covariates"]),
                                             scheme_window(params),
                                             reference=ReferenceData(setup.reference.x, setup.reference.delta))
    rules = sorted(set(PLACEBO_ARMS.values()))
    arms = [BASELINES[r] for r in rules] + list(PLACEBO_ARMS)
    agents = build_population_agents(params, setup, float(params.c1_thresholds[season.fit]), supervisor,
                                     reference_supervisor, arms)
    return extract_schedules(params, season, agents, PLACEBO_ARMS)


def extract_schedules(params: FrozenParams, season: ValidationSeason, agents: Sequence[Agent],
                      arms: Mapping[str, str], floor: float = 0.0) -> SeasonSchedules:
    """Esegue gli agenti senza puntata minima e ne estrae rendimenti per livello, calendari e residui.

    agents contiene gli schemi di arms (schema → regola) e, per ogni regola, il quarto di Kelly
    BASELINES[regola]; il Kelly a 0.25·κ di ogni regola (e a floor, se floor > 0) viene aggiunto qui.
    """
    inp = season.inp
    kappa, base = float(params.calibrated["c1_kappa"]), float(params.fixed["c0_lambda"])
    rules = sorted(set(arms.values()))
    agents = list(agents) + [with_outcome_rule(FractionalKellyAgent, r)(f"{r}_reduced", lam=base * kappa)
                             for r in rules]
    if floor > 0.0:
        agents += [with_outcome_rule(FractionalKellyAgent, r)(f"{r}_floor", lam=floor) for r in rules]
    runs = {run.name: run for run in run_paired_backtest(agents, inp.dates, inp.probs, inp.odds, inp.outcomes, 0.0,
                                                         fallback_policy=params.fixed["fallback_policy"])}
    by_name = {a.name: a for a in agents}

    def log_path(name: str) -> np.ndarray:
        return np.diff(np.log(runs[name].wealth[0]))

    days, day_index = np.unique(inp.dates, return_inverse=True)
    n_days = days.shape[0]
    log_returns = {r: np.stack([log_path(f"{r}_floor") if floor > 0.0 else np.zeros(n_days),
                                log_path(f"{r}_reduced"), log_path(BASELINES[r])]) for r in rules}
    levels, lambdas, actual = {}, {}, {}
    for arm in arms:
        agent = by_name[arm]
        assert isinstance(agent, SchemeAgent)
        by_date = agent.lambda_by_date
        lam = np.array([by_date[np.datetime64(d, "ns")] for d in days])
        lambdas[arm] = lam
        levels[arm] = levels_from_lambda(lam, base, kappa, floor)
        actual[arm] = float(np.log(runs[arm].wealth[0, -1]))
    q = devig_probabilities(inp.odds, "shin")
    features = np.stack([_daily(inp.delta, day_index, n_days), _daily(expected_delta(inp.probs, q), day_index, n_days)])
    return SeasonSchedules(inp.season, season.fit, np.bincount(day_index, minlength=n_days), features,
                           log_returns, levels, lambdas, actual)


def run_constant_season(params_path: str, season: ValidationSeason, lams: Mapping[str, float],
                        arms: Mapping[str, str] = PLACEBO_ARMS) -> dict[str, float]:
    """ln W_T, senza puntata minima, del Kelly frazionario a λ costante per ogni schema (stessa regola dello schema)."""
    params = load_frozen_params(params_path)
    inp = season.inp
    agents = [with_outcome_rule(FractionalKellyAgent, arms[arm])(arm, lam=float(lam))
              for arm, lam in lams.items()]
    runs = run_paired_backtest(agents, inp.dates, inp.probs, inp.odds, inp.outcomes, 0.0,
                               fallback_policy=params.fixed["fallback_policy"])
    return {run.name: float(np.log(run.wealth[0, -1])) for run in runs}


def mean_lambda(seasons: Sequence[SeasonSchedules], arm: str) -> float:
    """λ medio dello schema sulle giornate di tutte le stagioni."""
    return float(np.concatenate([s.lambdas[arm] for s in seasons]).mean())


def _gap(int_sums: np.ndarray, int_n: np.ndarray, total_sums: np.ndarray, total_n: float) -> np.ndarray:
    """Media per partita nelle giornate d'intervento meno media nelle altre; NaN se uno dei due gruppi è vuoto."""
    with np.errstate(divide="ignore", invalid="ignore"):
        inside = int_sums / int_n[..., None]
        outside = (total_sums - int_sums) / (total_n - int_n)[..., None]
    return inside - outside


def _within_season(features: np.ndarray, n_matches: np.ndarray) -> np.ndarray:
    """Somme per giornata al netto della media per partita della stagione (K, D)."""
    f = np.asarray(features, dtype=np.float64)
    return f - (f.sum(axis=1) / n_matches.sum())[:, None] * n_matches[None, :]


class ArmPlacebo(NamedTuple):
    """Estrazioni placebo di uno schema: capitale e scarti del segnale, osservati e per estrazione."""

    observed_log_wealth: float            # Σ sulle stagioni di ln W_T ricostruito dal calendario
    observed_gap: np.ndarray              # (K,) scarto per risposta
    observed_means: np.ndarray            # (2, K) media nelle giornate d'intervento e nelle altre
    draws_log_wealth: dict[str, np.ndarray]   # placebo → (n,)
    draws_gap: dict[str, np.ndarray]          # placebo → (n, K)


def arm_placebo(seasons: Sequence[SeasonSchedules], arm: str, n_draws: int = N_DRAWS,
                seed: int | np.random.SeedSequence = SEED_S23,
                arms: Mapping[str, str] = PLACEBO_ARMS) -> ArmPlacebo:
    """Statistiche osservate e placebo di uno schema di arms sulle stagioni date (vedi modulo)."""
    rule = arms[arm]
    position = list(arms).index(arm)
    root = fresh_sequence(seed) if isinstance(seed, np.random.SeedSequence) else np.random.SeedSequence(seed)
    gens = [np.random.default_rng(g) for g in root.spawn(len(arms))[position].spawn(len(PLACEBOS))]
    levels = [s.levels[arm] for s in seasons]
    extra = [np.vstack([s.features, _within_season(s.features, s.n_matches),
                        s.n_matches[None, :].astype(np.float64)]) for s in seasons]
    total = np.sum([e.sum(axis=1) for e in extra], axis=0)

    def statistics(draws: Sequence[np.ndarray]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        lw = np.sum([schedule_log_wealth(d, s.log_returns[rule]) for d, s in zip(draws, seasons)], axis=0)
        sums = np.sum([intervention_sums(d, e) for d, e in zip(draws, extra)], axis=0)
        return lw, _gap(sums[..., :-1], sums[..., -1], total[:-1], total[-1]), sums

    obs_lw, obs_gap, obs_sums = statistics([lv[None, :] for lv in levels])
    with np.errstate(divide="ignore", invalid="ignore"):
        means = np.stack([obs_sums[0, :-1] / obs_sums[0, -1], (total[:-1] - obs_sums[0, :-1]) / (total[-1] - obs_sums[0, -1])])
    draws = {
        "permutation": [permutation_draws(lv, n_draws, gens[0]) for lv in levels],
        "shift": [shift_draws(lv, n_draws, gens[1]) for lv in levels],
        "cross_season": cross_season_draws(levels, n_draws, gens[2]),
    }
    out_lw, out_gap = {}, {}
    for name in PLACEBOS:
        out_lw[name], out_gap[name], _ = statistics(draws[name])
    return ArmPlacebo(float(obs_lw[0]), obs_gap[0], means, out_lw, out_gap)


RECONSTRUCTION_TOL: Final[float] = 1e-9
COLUMNS: Final[tuple[str, ...]] = (
    "row_type", "agent", "baseline", "placebo", "n_seasons", "n_draws", "observed", "baseline_value",
    "placebo_mean", "placebo_median", "placebo_q05", "placebo_q95", "p_value",
    "mean_intervention", "mean_other", "share_days_zero", "share_days_reduced", "mean_lambda",
    "seasons_better", "seasons_worse",
)
SEASON_COLUMNS: Final[tuple[str, ...]] = (
    "agent", "season", "fit_through", "n_days", "share_days_zero", "share_days_reduced",
    "log_wealth", "baseline_log_wealth", "constant_log_wealth", "shift_share_not_worse", "reconstruction_error",
)


def _typical(sum_log_wealth: np.ndarray | float, n_seasons: int) -> np.ndarray:
    return np.exp(np.asarray(sum_log_wealth, dtype=np.float64) / n_seasons)


def _distribution(values: np.ndarray) -> dict[str, float]:
    v = values[np.isfinite(values)]
    return {"placebo_mean": float(v.mean()), "placebo_median": float(np.median(v)),
            "placebo_q05": float(np.quantile(v, 0.05)), "placebo_q95": float(np.quantile(v, 0.95))}


def placebo_tables(seasons: Sequence[SeasonSchedules], constant: Sequence[Mapping[str, float]],
                   lams: Mapping[str, float], n_draws: int = N_DRAWS,
                   seed: int | np.random.SeedSequence = SEED_S23,
                   arms: Mapping[str, str] = PLACEBO_ARMS) -> tuple[list[dict], list[dict]]:
    """Righe di sintesi (COLUMNS) e per stagione (SEASON_COLUMNS) degli schemi di arms.

    constant[stagione][schema] è ln W_T del Kelly a λ costante lams[schema] (run_constant_season).
    Solleva RuntimeError se il capitale di uno schema non è riprodotto dal suo calendario.
    """
    n = len(seasons)
    rows: list[dict] = []
    season_rows: list[dict] = []
    for arm, rule in arms.items():
        base_lw = np.array([s.log_returns[rule][LEVEL_BASE].sum() for s in seasons])
        arm_lw = np.array([schedule_log_wealth(s.levels[arm], s.log_returns[rule]) for s in seasons])
        errors = np.abs(arm_lw - np.array([s.actual[arm] for s in seasons]))
        if errors.max() > RECONSTRUCTION_TOL:
            raise RuntimeError(f"{arm}: capital not reproduced by its schedule (max error {errors.max():.2e})")
        const_lw = np.array([c[arm] for c in constant])
        all_levels = np.concatenate([s.levels[arm] for s in seasons])
        common = {"agent": arm, "baseline": BASELINES[rule], "n_seasons": n,
                  "share_days_zero": float((all_levels == LEVEL_ZERO).mean()),
                  "share_days_reduced": float((all_levels == LEVEL_REDUCED).mean()), "mean_lambda": lams[arm]}
        result = arm_placebo(seasons, arm, n_draws, seed, arms)
        for placebo in PLACEBOS:
            lw = result.draws_log_wealth[placebo]
            rows.append({**common, "row_type": "capital", "placebo": placebo, "n_draws": n_draws,
                         "observed": float(_typical(result.observed_log_wealth, n)),
                         "baseline_value": float(_typical(base_lw.sum(), n)), **_distribution(_typical(lw, n)),
                         "p_value": one_sided_p(result.observed_log_wealth, lw, greater=True),
                         "seasons_better": int((arm_lw > base_lw + 1e-12).sum()),
                         "seasons_worse": int((arm_lw < base_lw - 1e-12).sum())})
            for k, response in enumerate(RESPONSES):
                gap = result.draws_gap[placebo][:, k]
                rows.append({**common, "row_type": response, "placebo": placebo, "n_draws": n_draws,
                             "observed": float(result.observed_gap[k]), **_distribution(gap),
                             "p_value": one_sided_p(float(result.observed_gap[k]), gap, greater=False),
                             "mean_intervention": float(result.observed_means[0, k]),
                             "mean_other": float(result.observed_means[1, k])})
        rows.append({**common, "row_type": "constant", "placebo": "constant_exposure",
                     "observed": float(_typical(arm_lw.sum(), n)), "baseline_value": float(_typical(base_lw.sum(), n)),
                     "placebo_mean": float(_typical(const_lw.sum(), n)),
                     "seasons_better": int((arm_lw > const_lw + 1e-12).sum()),
                     "seasons_worse": int((arm_lw < const_lw - 1e-12).sum())})
        for i, s in enumerate(seasons):
            shifts = schedule_log_wealth(all_shifts(s.levels[arm]), s.log_returns[rule])
            season_rows.append({
                "agent": arm, "season": s.season, "fit_through": s.fit, "n_days": int(s.levels[arm].shape[0]),
                "share_days_zero": float((s.levels[arm] == LEVEL_ZERO).mean()),
                "share_days_reduced": float((s.levels[arm] == LEVEL_REDUCED).mean()),
                "log_wealth": float(arm_lw[i]), "baseline_log_wealth": float(base_lw[i]),
                "constant_log_wealth": float(const_lw[i]),
                "shift_share_not_worse": float((shifts >= arm_lw[i] - 1e-12).mean()),
                "reconstruction_error": float(errors[i])})
    return rows, season_rows
