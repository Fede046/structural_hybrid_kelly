"""Calibrazione sul training dei parametri liberi di C1, C2_global, C2 e D (T54, US-C8.2).

Obiettivo unico (decisione S9): media, su seed e sulle tre stagioni di training, della
log-ricchezza finale nella configurazione principale B0/F = 22 000 (£0.01 su £220). A
parità entro 1e-12 vince la combinazione con puntata media più bassa.

Regola di parità di secondo livello (decisione del programmatore del 2026-10-11, introdotta
dopo la calibrazione e prima del congelamento, perché sul training ADWIN non dà allarmi con
δ <= 0.5), quando restano parità esatte anche sulla puntata media:
1. un parametro con un valore congelato da una decisione precedente prende quel valore
   (FROZEN_EARLIER_VALUES: δ di ADWIN, δ e soglia di Page-Hinkley di drift.py, decisione S5);
2. κ prende il valore scelto dal braccio a reazione binaria più simile in cui κ è
   identificato (KAPPA_REFERENCES: per un detector di D prima l'altro detector, poi C1); κ è
   identificato in un braccio se le combinazioni in parità di primo livello hanno tutte lo
   stesso κ; se nessun riferimento ha κ identificato, κ = 1;
3. solo dopo, la prima nell'ordine della griglia.

Griglie (fissate nel task):
- C1: W ∈ MODULE2_WINDOWS × κ ∈ KAPPA_GRID (20);
- C2_global e C2: W ∈ MODULE2_WINDOWS (4 ciascuno);
- D_ADWIN: δ ∈ ADWIN_GRID_DELTA × κ ∈ KAPPA_GRID (45);
- D_PH: δ ∈ PAGE_HINKLEY_GRID_DELTA × soglia ∈ PAGE_HINKLEY_GRID_THRESHOLD × κ ∈ KAPPA_GRID (90).
Gli altri parametri dei detector restano quelli di drift.detector_params; D monitora δ.

Esecuzione: per ogni stagione di training e seed (stagione ricostruita a L_PW,
season_bootstrap.reconstruct_season) un'unica esecuzione dell'ambiente con tutti gli
agenti della griglia, appaiati sugli stessi seed. Un supervisore del Modulo 2 per W,
condiviso dai bracci con quella W. Soglia di C1 per fit e W a L_PW (T52, threshold_records).

Puntata media di una combinazione: media su seed e stagioni della media sulle date della
quota di ricchezza puntata, staked_d / W_{d−1} (AgentRun.staked e AgentRun.wealth).

Seed: SeedSequence(SEED_S9).spawn(5)[4] (T54 in posizione 4), spawn(numero di stagioni) in
ordine cronologico, spawn(n_seeds) per seed.
"""

import math
from collections.abc import Sequence
from typing import Final, NamedTuple

import numpy as np
import pandas as pd

from shk.kelly.agents import Agent, DateResults
from shk.kelly.environment import run_paired_backtest
from shk.kelly.staking import BASE_LAMBDA, KAPPA_GRID
from shk.market.devig import devig_shin
from shk.model.agent_c import C1Agent, GradedAgent, Module2Supervisor, build_c0_agent
from shk.model.covariate_inspection import MODULE2_WINDOWS
from shk.model.module3_synthetic import N_STORY_TASKS, SEED_S9
from shk.model.paired_backtest import CONFIGURATIONS
from shk.model.season_bootstrap import reconstruct_season, season_block_length
from shk.model.stateful_agents import SERIES_DELTA, BaselineDAgent
from shk.model.task_seeds import task_sequence
from shk.model.training_agents import SeasonInput, season_input_from_frame, threshold_records, training_seasons
from shk.stats.drift import (
    ADWIN_DELTA,
    ADWIN_GRID_DELTA,
    PAGE_HINKLEY_DELTA,
    PAGE_HINKLEY_GRID_DELTA,
    PAGE_HINKLEY_GRID_THRESHOLD,
    PAGE_HINKLEY_THRESHOLD,
    detector_params,
)

T54_STORY_POSITION: Final[int] = 4
CALIBRATION_CONFIG: Final[str] = "gbp_0.01"
N_CALIBRATION_SEEDS: Final[int] = 200
TIE_TOLERANCE: Final[float] = 1e-12
FAMILIES: Final[tuple[str, ...]] = ("C1", "C2_global", "C2", "D_ADWIN", "D_PH")

# Regola di parità di secondo livello (vedi modulo)
FROZEN_EARLIER_VALUES: Final[dict[str, dict[str, float]]] = {
    "D_ADWIN": {"detector_delta": ADWIN_DELTA},
    "D_PH": {"detector_delta": PAGE_HINKLEY_DELTA, "detector_threshold": PAGE_HINKLEY_THRESHOLD},
}
KAPPA_REFERENCES: Final[dict[str, tuple[str, ...]]] = {
    "D_ADWIN": ("D_PH", "C1"),
    "D_PH": ("D_ADWIN", "C1"),
    "C1": (),
}
DEFAULT_KAPPA: Final[float] = 1.0
CHOSEN_BY_OBJECTIVE: Final[str] = "objective"
CHOSEN_BY_STAKE: Final[str] = "mean_stake"
CHOSEN_BY_SECOND_LEVEL: Final[str] = "second_level_tie_rule"
TIE_RULE_NOTE: Final[str] = (
    "2026-10-11, decisione del programmatore: regola di parità di secondo livello, quando restano "
    "parità esatte anche sulla puntata media. 1) un parametro con un valore congelato da una decisione "
    "precedente prende quel valore (ADWIN delta = 0.002, decisione S5); 2) kappa prende il valore scelto "
    "dal braccio a reazione binaria più simile in cui kappa è identificato (prima l'altro detector di D, "
    "poi C1; altrimenti kappa = 1); 3) solo dopo, la prima nell'ordine della griglia. Introdotta dopo la "
    "calibrazione e prima del congelamento, perché sul training ADWIN non dà allarmi con delta <= 0.5 e "
    "41 combinazioni su 45 di D_ADWIN restano in parità esatta anche sulla puntata media."
)

CALIBRATION_LOG_COLUMNS: Final[tuple[str, ...]] = (
    "row_type", "family", "agent", "grid_index", "window", "kappa", "detector_delta", "detector_threshold",
    "objective", "mean_stake", "objective_2000_01", "objective_2010_11", "objective_2020_21",
    "n_seeds", "n_ruined", "rank", "chosen", "on_grid_edge", "chosen_by", "note",
)


class Combination(NamedTuple):
    """Una combinazione della griglia di una famiglia di agenti."""

    family: str
    grid_index: int
    window: int | None
    kappa: float | None
    detector_delta: float | None
    detector_threshold: float | None

    @property
    def agent_name(self) -> str:
        parts = [self.family]
        for label, value in (("W", self.window), ("kappa", self.kappa), ("delta", self.detector_delta),
                             ("threshold", self.detector_threshold)):
            if value is not None:
                parts.append(f"{label}={value}")
        return "|".join(parts)


def calibration_grid() -> list[Combination]:
    """Tutte le combinazioni, per famiglia e nell'ordine della griglia (W, poi δ, soglia, κ)."""
    out: list[Combination] = []
    i = 0
    for w in MODULE2_WINDOWS:
        for k in KAPPA_GRID:
            out.append(Combination("C1", i, w, k, None, None))
            i += 1
    for family in ("C2_global", "C2"):
        for i, w in enumerate(MODULE2_WINDOWS):
            out.append(Combination(family, i, w, None, None, None))
    i = 0
    for d in ADWIN_GRID_DELTA:
        for k in KAPPA_GRID:
            out.append(Combination("D_ADWIN", i, None, k, d, None))
            i += 1
    i = 0
    for d in PAGE_HINKLEY_GRID_DELTA:
        for t in PAGE_HINKLEY_GRID_THRESHOLD:
            for k in KAPPA_GRID:
                out.append(Combination("D_PH", i, None, k, d, t))
                i += 1
    return out


def spawn_t54_generators(seasons: Sequence[str], n_seeds: int = N_CALIBRATION_SEEDS,
                         seed: int | np.random.SeedSequence = SEED_S9) -> dict[str, list[np.random.Generator]]:
    """Un generatore per seed e stagione (vedi modulo)."""
    task = task_sequence(seed, T54_STORY_POSITION, N_STORY_TASKS)
    return {s: [np.random.default_rng(c) for c in s_seq.spawn(n_seeds)]
            for s, s_seq in zip(seasons, task.spawn(len(seasons)))}


class SharedShin:
    """q di Shin per data, calcolate una volta e condivise dagli agenti D di un'esecuzione."""

    def __init__(self) -> None:
        self._cache: dict[np.datetime64, np.ndarray] = {}

    def get(self, results: DateResults) -> np.ndarray:
        """q di Shin delle quote della data (dalla cache se già calcolate)."""
        key = np.datetime64(results.date, "ns")
        if key not in self._cache:
            q, _ = devig_shin(np.asarray(results.odds))
            self._cache[key] = q
        return self._cache[key]


class SharedShinBaselineDAgent(BaselineDAgent):
    """Baseline D con serie δ e q di Shin condivise: stesse uscite di BaselineDAgent, meno calcolo."""

    def __init__(self, name: str, detector: str, params: dict, kappa: float, shin: SharedShin,
                 base_lambda: float = BASE_LAMBDA) -> None:
        super().__init__(name, detector, params, kappa, series=SERIES_DELTA, base_lambda=base_lambda)
        self._shin = shin

    def _market_probs(self, results: DateResults) -> np.ndarray:
        return self._shin.get(results)


def _detector_params(c: Combination) -> dict:
    if c.family == "D_ADWIN":
        params = detector_params("adwin")
        params["delta"] = c.detector_delta
    else:
        params = detector_params("page_hinkley")
        params["delta"] = c.detector_delta
        params["threshold"] = c.detector_threshold
    return params


def build_grid_agents(inp: SeasonInput, covariates: Sequence[str], thresholds: dict[int, float],
                      grid: Sequence[Combination]) -> list[Agent]:
    """C0 più un agente per combinazione; un supervisore del Modulo 2 per W, condiviso."""
    supervisors = {w: Module2Supervisor(inp.season, inp.dates, inp.x, covariates, w) for w in MODULE2_WINDOWS}
    shin = SharedShin()
    agents: list[Agent] = [build_c0_agent("C0")]
    for c in grid:
        if c.family == "C1":
            agents.append(C1Agent(c.agent_name, supervisors[c.window], c.kappa, thresholds[c.window]))
        elif c.family in ("C2_global", "C2"):
            agents.append(GradedAgent(c.agent_name, supervisors[c.window], abstain=c.family == "C2"))
        else:
            detector = "adwin" if c.family == "D_ADWIN" else "page_hinkley"
            agents.append(SharedShinBaselineDAgent(c.agent_name, detector, _detector_params(c), c.kappa, shin))
    return agents


def _mean_stake(staked: np.ndarray, wealth: np.ndarray) -> float:
    prior = wealth[0, :-1]
    share = np.divide(staked[0], prior, out=np.zeros_like(prior), where=prior > 0.0)
    return float(share.mean())


def first_level_ties(objectives: Sequence[float], stakes: Sequence[float]) -> tuple[list[int], list[int]]:
    """(parità entro 1e-12 sull'obiettivo massimo, e fra queste quelle con la puntata media minima)."""
    best = max(objectives)
    tied = [i for i, o in enumerate(objectives) if best - o <= TIE_TOLERANCE]
    low = min(stakes[i] for i in tied)
    return tied, [i for i in tied if stakes[i] == low]


class Selection(NamedTuple):
    """Scelta di una famiglia: indice nella griglia, regola decisiva e chiave di preferenza per indice."""

    index: int
    chosen_by: str
    preference: list[tuple[int, int]]


def select_combinations(
    objectives: dict[str, Sequence[float]],
    stakes: dict[str, Sequence[float]],
    combos: dict[str, Sequence[Combination]],
) -> dict[str, Selection]:
    """Scelta per famiglia: obiettivo, puntata media, regola di parità di secondo livello (vedi modulo).

    Le liste di ogni famiglia sono nell'ordine della griglia.
    """
    ties = {f: first_level_ties(objectives[f], stakes[f]) for f in combos}
    identified: dict[str, float | None] = {}
    for f, (_, exact) in ties.items():
        kappas = {combos[f][i].kappa for i in exact}
        identified[f] = kappas.pop() if len(kappas) == 1 and None not in kappas else None
    out: dict[str, Selection] = {}
    for f, items in combos.items():
        frozen = FROZEN_EARLIER_VALUES.get(f, {})
        ref_kappa = next((identified[r] for r in KAPPA_REFERENCES.get(f, ()) if identified.get(r) is not None),
                         DEFAULT_KAPPA)
        preference = [
            (sum(getattr(c, k) != v for k, v in frozen.items()), int(c.kappa is not None and c.kappa != ref_kappa))
            for c in items
        ]
        tied, exact = ties[f]
        candidates = list(exact)
        for key, value in frozen.items():
            keep = [i for i in candidates if getattr(items[i], key) == value]
            candidates = keep or candidates
        if items[0].kappa is not None:
            keep = [i for i in candidates if items[i].kappa == ref_kappa]
            candidates = keep or candidates
        if len(tied) == 1:
            how = CHOSEN_BY_OBJECTIVE
        elif len(exact) == 1:
            how = CHOSEN_BY_STAKE
        else:
            how = CHOSEN_BY_SECOND_LEVEL
        out[f] = Selection(min(candidates), how, preference)
    return out


def _number(value: object) -> float | None:
    return None if value is None or value == "" else float(value)


def finalize_log(rows: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    """Righe del log con scelta, rango, bordo e regola decisiva, più la riga della regola di parità.

    Accetta righe con valori numerici (dal calcolo) o stringhe (dal CSV); cambia solo le
    colonne row_type, rank, chosen, on_grid_edge, chosen_by e note.
    """
    out = [dict(r) for r in rows if r.get("row_type", "combination") != "rule"]
    by_family = {f: sorted((r for r in out if r["family"] == f), key=lambda r: int(r["grid_index"])) for f in FAMILIES}
    combos = {
        f: [Combination(f, int(r["grid_index"]), None if _number(r["window"]) is None else int(_number(r["window"])),
                        _number(r["kappa"]), _number(r["detector_delta"]), _number(r["detector_threshold"]))
            for r in rs]
        for f, rs in by_family.items()
    }
    objectives = {f: [float(r["objective"]) for r in rs] for f, rs in by_family.items()}
    stakes = {f: [float(r["mean_stake"]) for r in rs] for f, rs in by_family.items()}
    selection = select_combinations(objectives, stakes, combos)
    for f, rs in by_family.items():
        sel = selection[f]
        order = sorted(range(len(rs)), key=lambda i: (-objectives[f][i], stakes[f][i], sel.preference[i], i))
        rank = {i: r + 1 for r, i in enumerate(order)}
        for i, r in enumerate(rs):
            r.update(row_type="combination", rank=rank[i], chosen=i == sel.index,
                     on_grid_edge=_on_edge(combos[f][i]) if i == sel.index else "",
                     chosen_by=sel.chosen_by if i == sel.index else "", note="")
    rule = {c: "" for c in CALIBRATION_LOG_COLUMNS}
    rule.update(row_type="rule", family="all", note=TIE_RULE_NOTE)
    return out + [rule]


def evaluate_calibration(frame: pd.DataFrame, covariates: Sequence[str], seed: int | np.random.SeedSequence = SEED_S9,
                         n_seeds: int = N_CALIBRATION_SEEDS,
                         threshold_seed: int | np.random.SeedSequence = SEED_S9) -> list[dict[str, object]]:
    """Obiettivo e puntata media per ogni combinazione; scelta per famiglia (log completo).

    threshold_seed: seed delle soglie di C1 (threshold_records, T52).

    Solleva
    -------
    ValueError
        Se il DataFrame contiene righe non di training.
    """
    if set(frame["role"]) != {"training"}:
        raise ValueError("frame must contain training rows only")
    grid = calibration_grid()
    min_stake = dict(CONFIGURATIONS)[CALIBRATION_CONFIG]
    inputs = [season_input_from_frame(frame, s, covariates) for s in training_seasons(frame)]
    _, thr = threshold_records(inputs, threshold_seed)
    gens = spawn_t54_generators([inp.season for inp in inputs], n_seeds, seed)
    lw = {c.agent_name: {inp.season: [] for inp in inputs} for c in grid}
    stake = {c.agent_name: [] for c in grid}
    ruined = {c.agent_name: 0 for c in grid}
    for inp in inputs:
        l_pw = season_block_length(inp)
        thresholds = {w: thr[(inp.season, w)] for w in MODULE2_WINDOWS}
        for rng in gens[inp.season]:
            rec = reconstruct_season(inp, rng, l_pw, covariates=covariates)
            agents = build_grid_agents(rec, covariates, thresholds, grid)
            runs = run_paired_backtest(agents, rec.dates, rec.probs, rec.odds, rec.outcomes, min_stake,
                                       record_stakes=True)
            for run in runs[1:]:
                w_t = float(run.wealth[0, -1])
                lw[run.name][inp.season].append(math.log(w_t) if w_t > 0.0 else -math.inf)
                stake[run.name].append(_mean_stake(run.staked, run.wealth))
                ruined[run.name] += int(run.ruined[0])
    records: list[dict[str, object]] = []
    for c in grid:
        per_season = {s: float(np.mean(v)) for s, v in lw[c.agent_name].items()}
        records.append({
            "family": c.family, "agent": c.agent_name, "grid_index": c.grid_index,
            "window": "" if c.window is None else c.window, "kappa": "" if c.kappa is None else c.kappa,
            "detector_delta": "" if c.detector_delta is None else c.detector_delta,
            "detector_threshold": "" if c.detector_threshold is None else c.detector_threshold,
            "objective": float(np.mean([v for s in lw[c.agent_name].values() for v in s])),
            "mean_stake": float(np.mean(stake[c.agent_name])),
            "objective_2000_01": per_season.get("2000-01", ""), "objective_2010_11": per_season.get("2010-11", ""),
            "objective_2020_21": per_season.get("2020-21", ""), "n_seeds": n_seeds,
            "n_ruined": ruined[c.agent_name],
        })
    return finalize_log(records)


def _on_edge(c: Combination) -> str:
    """Parametri della combinazione che cadono sul bordo della propria griglia."""
    edges = []
    if c.window is not None and c.window in (MODULE2_WINDOWS[0], MODULE2_WINDOWS[-1]):
        edges.append("window")
    if c.kappa is not None and c.kappa in (KAPPA_GRID[0], KAPPA_GRID[-1]):
        edges.append("kappa")
    if c.family == "D_ADWIN" and c.detector_delta in (ADWIN_GRID_DELTA[0], ADWIN_GRID_DELTA[-1]):
        edges.append("detector_delta")
    if c.family == "D_PH":
        if c.detector_delta in (PAGE_HINKLEY_GRID_DELTA[0], PAGE_HINKLEY_GRID_DELTA[-1]):
            edges.append("detector_delta")
        if c.detector_threshold in (PAGE_HINKLEY_GRID_THRESHOLD[0], PAGE_HINKLEY_GRID_THRESHOLD[-1]):
            edges.append("detector_threshold")
    return ";".join(edges) if edges else "none"
