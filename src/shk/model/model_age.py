"""Età del modello e tempo di calendario; sensibilità dello schema alla stagione di riferimento.

Due dubbi sull'invecchiamento del modello (thesis, §5.3), verificati con i dati fino al 2022-23.

1. Età o calendario? La dispersione di δ cresce con gli anni dalla calibrazione, ma dentro una
   calibrazione l'età del modello e l'anno di calendario crescono insieme, e la dispersione delle tre
   stagioni di calibrazione cresce da sola nei decenni. Per separarli si confrontano, sulle stesse
   partite e con le stesse quote, il modello congelato (calibrato da 1 a 9 anni prima) e il modello
   ricalibrato sulla stagione precedente (shk.model.elo_refit, us_c18), che ha sempre un anno: tutto
   ciò che dipende dalla stagione è comune ai due e si cancella nella differenza.
   - differenza appaiata per stagione di dispersione, errore atteso e media di δ, con intervallo
     percentile da un moving block bootstrap delle partite (stessi indici per i due modelli);
   - tendenza della differenza con l'età del modello congelato (Spearman dentro ogni calibrazione,
     pesato per il numero di stagioni; p per permutazione delle stagioni dentro la calibrazione);
   - tendenza con l'anno della dispersione del modello ricalibrato, cioè a età costante: è la parte
     che non dipende dall'età.
   Il 2002-03 resta fuori dalle differenze: lì il modello ricalibrato è lo stesso del congelato.
   Il modello ricalibrato usa una sola stagione e ha parametri rumorosi (us_c18): la differenza è
   rumorosa, ma il rumore non dipende dall'età del modello congelato.

2. Il riferimento è una sola stagione. L'allarme confronta gli errori recenti con la stagione di
   calibrazione, e le tre stagioni di calibrazione hanno dispersioni molto diverse. Come analisi di
   sensibilità lo schema si riesegue con un altro riferimento: la prima stagione di validazione dopo
   la calibrazione (2002-03, 2011-12, 2021-22), che è fuori campione per il modello. Le soglie si
   ricalibrano su quel riferimento con le procedure di sempre, e le due varianti si confrontano
   sulle 16 stagioni che restano. Non è una nuova versione dello schema: serve a vedere quanto delle
   conclusioni dipende dalla stagione scelta come riferimento.

Seed: SeedSequence(SEED_S28).spawn(numero di stagioni) per il bootstrap delle differenze;
SeedSequence([SEED_S28, 1]) per le permutazioni.
"""

from collections.abc import Mapping, Sequence
from typing import Final

import numpy as np
import pandas as pd

from shk.model.agent_c import N_BOOT, expected_delta
from shk.model.elo_fit import parse_season_start_year
from shk.model.scoring import MATCH_KEYS
from shk.stats.bootstrap import optimal_block_length, round_block_length
from shk.stats.calibration import moving_block_indices

SEED_S28: Final[int] = 20261115
N_PERMUTATIONS: Final[int] = 20_000
MEASURES: Final[tuple[str, ...]] = ("dispersion", "expected", "mean")
SEASON_COLUMNS: Final[tuple[str, ...]] = (
    "season", "n_matches", "frozen_fit", "refit_fit", "age", "refit_age",
    "frozen_dispersion", "refit_dispersion", "dispersion_difference", "dispersion_low", "dispersion_high",
    "frozen_expected", "refit_expected", "expected_difference", "expected_low", "expected_high",
    "frozen_mean", "refit_mean", "mean_difference", "mean_low", "mean_high",
)
TEST_COLUMNS: Final[tuple[str, ...]] = ("test", "measure", "n_seasons", "statistic", "p_value", "n_positive",
                                        "n_negative")


def dispersion(delta: np.ndarray) -> np.ndarray | float:
    """Deviazione assoluta media dalla mediana, sull'ultimo asse."""
    d = np.asarray(delta, dtype=np.float64)
    out = np.abs(d - np.median(d, axis=-1, keepdims=True)).mean(axis=-1)
    return float(out) if d.ndim == 1 else out


def _measures(delta: np.ndarray, expected: np.ndarray) -> np.ndarray:
    """(dispersione, errore atteso medio, media di δ) sull'ultimo asse; forma (3, ...)."""
    return np.stack([np.asarray(dispersion(delta)), np.asarray(expected).mean(axis=-1), np.asarray(delta).mean(axis=-1)])


def _expected(frame: pd.DataFrame) -> np.ndarray:
    return expected_delta(frame[["p_home", "p_draw", "p_away"]].to_numpy(), frame[["q_home", "q_draw", "q_away"]].to_numpy())


def paired_season_records(frozen: pd.DataFrame, refit: pd.DataFrame, seed: int = SEED_S28,
                          n_boot: int = N_BOOT) -> list[dict]:
    """Una riga per stagione di validazione: modello congelato e ricalibrato sulle stesse partite (vedi modulo).

    frozen e refit sono i DataFrame del Modulo 2 delle due versioni (righe di validazione).
    Solleva ValueError se non coprono le stesse partite.
    """
    keys = list(MATCH_KEYS)
    fz = frozen[frozen["role"] == "validation"].sort_values(keys, kind="stable").reset_index(drop=True)
    rf = refit[refit["role"] == "validation"].sort_values(keys, kind="stable").reset_index(drop=True)
    if len(fz) != len(rf) or not (fz[keys] == rf[keys]).all().all():
        raise ValueError("frozen and refit frames cover different matches")
    fz, rf = fz.assign(expected=_expected(fz)), rf.assign(expected=_expected(rf))
    seasons = sorted(set(fz["season"]), key=parse_season_start_year)
    rows = []
    for season, seq in zip(seasons, np.random.SeedSequence(seed).spawn(len(seasons))):
        a = fz[fz["season"] == season].sort_values("Date", kind="stable")
        b = rf[rf["season"] == season].sort_values("Date", kind="stable")
        da, db = a["delta"].to_numpy(), b["delta"].to_numpy()
        ea, eb = a["expected"].to_numpy(), b["expected"].to_numpy()
        frozen_fit, refit_fit = str(a["fit_through"].iloc[0]), str(b["fit_through"].iloc[0])
        obs_a, obs_b = _measures(da, ea), _measures(db, eb)
        idx = moving_block_indices(da.shape[0], round_block_length(optimal_block_length(da).circular), n_boot,
                                   np.random.default_rng(seq))
        boot = _measures(da[idx], ea[idx]) - _measures(db[idx], eb[idx])
        low, high = np.quantile(boot, [0.025, 0.975], axis=1)
        year = parse_season_start_year(season)
        row = {"season": season, "n_matches": int(da.shape[0]), "frozen_fit": frozen_fit, "refit_fit": refit_fit,
               "age": year - parse_season_start_year(frozen_fit), "refit_age": year - parse_season_start_year(refit_fit)}
        for j, name in enumerate(MEASURES):
            row.update({f"frozen_{name}": float(obs_a[j]), f"refit_{name}": float(obs_b[j]),
                        f"{name}_difference": float(obs_a[j] - obs_b[j]),
                        f"{name}_low": float(low[j]), f"{name}_high": float(high[j])})
        rows.append(row)
    return rows


def rank_correlation(x: np.ndarray, y: np.ndarray) -> float:
    """Correlazione di Spearman (ranghi medi per i pari merito); 0 se una delle due è costante."""
    rx, ry = pd.Series(np.asarray(x, dtype=np.float64)).rank().to_numpy(), pd.Series(np.asarray(y, dtype=np.float64)).rank().to_numpy()
    if rx.std() == 0.0 or ry.std() == 0.0:
        return 0.0
    return float(np.corrcoef(rx, ry)[0, 1])


def stratified_trend(x: np.ndarray, y: np.ndarray, groups: np.ndarray, rng: np.random.Generator,
                     n_perm: int = N_PERMUTATIONS) -> tuple[float, float]:
    """Tendenza di y con x dentro i gruppi: media pesata delle correlazioni di Spearman e p a una coda.

    Pesi = numerosità dei gruppi con almeno 3 osservazioni. p: quota di permutazioni di y dentro i
    gruppi con statistica >= dell'osservata, contando l'osservata (ipotesi alternativa: y cresce con x).
    """
    xx, yy, gg = np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64), np.asarray(groups)
    parts = [np.flatnonzero(gg == g) for g in pd.unique(gg)]
    parts = [p for p in parts if p.shape[0] >= 3]
    if not parts:
        raise ValueError("no group with at least 3 observations")
    weight = float(sum(p.shape[0] for p in parts))

    def statistic(values: np.ndarray) -> float:
        return sum(p.shape[0] * rank_correlation(xx[p], values[p]) for p in parts) / weight

    observed = statistic(yy)
    hits = 0
    for _ in range(n_perm):
        permuted = yy.copy()
        for p in parts:
            permuted[p] = rng.permutation(yy[p])
        hits += statistic(permuted) >= observed - 1e-12
    return observed, float((1 + hits) / (1 + n_perm))


def age_tests(rows: Sequence[Mapping], seed: Sequence[int] = (SEED_S28, 1),
              n_perm: int = N_PERMUTATIONS) -> list[dict]:
    """Test sull'età del modello dalle righe di paired_season_records (vedi modulo).

    Per ogni misura, orientata in modo che «peggio» sia positivo (dispersione; −errore atteso; −media):
    - "paired_difference": media sulle stagioni della differenza congelato − ricalibrato, con il test
      dei segni a una coda (p), sulle stagioni in cui i due modelli sono diversi;
    - "difference_vs_age": tendenza della differenza con l'età del modello congelato, dentro la calibrazione;
    - "frozen_vs_age": tendenza della misura del modello congelato con l'età, dentro la calibrazione;
    - "refit_vs_year": tendenza con l'anno della misura del modello ricalibrato, cioè a età costante.
    """
    from scipy.stats import binomtest

    df = pd.DataFrame(list(rows))
    paired = df[df["frozen_fit"] != df["refit_fit"]]
    rng = np.random.default_rng(np.random.SeedSequence(list(seed)))
    year = df["season"].map(parse_season_start_year).to_numpy()
    out = []
    for name, sign in (("dispersion", 1.0), ("expected", -1.0), ("mean", -1.0)):
        diff = sign * paired[f"{name}_difference"].to_numpy()
        pos, neg = int((diff > 0).sum()), int((diff < 0).sum())
        out.append({"test": "paired_difference", "measure": name, "n_seasons": len(paired),
                    "statistic": float(diff.mean()), "n_positive": pos, "n_negative": neg,
                    "p_value": float(binomtest(pos, pos + neg, 0.5, alternative="greater").pvalue)})
        stat, p = stratified_trend(paired["age"].to_numpy(), diff, paired["frozen_fit"].to_numpy(), rng, n_perm)
        out.append({"test": "difference_vs_age", "measure": name, "n_seasons": len(paired), "statistic": stat,
                    "p_value": p})
        stat, p = stratified_trend(df["age"].to_numpy(), sign * df[f"frozen_{name}"].to_numpy(),
                                   df["frozen_fit"].to_numpy(), rng, n_perm)
        out.append({"test": "frozen_vs_age", "measure": name, "n_seasons": len(df), "statistic": stat, "p_value": p})
        stat, p = stratified_trend(year, sign * df[f"refit_{name}"].to_numpy(), np.zeros(len(df)), rng, n_perm)
        out.append({"test": "refit_vs_year", "measure": name, "n_seasons": len(df), "statistic": stat, "p_value": p})
    return out


def first_season_after(validation_fits: Mapping[str, str]) -> dict[str, str]:
    """Per ogni fit, la prima stagione di validazione che prevede: stagione → fit, in ordine cronologico."""
    out: dict[str, str] = {}
    for season in sorted(validation_fits, key=parse_season_start_year):
        fit = validation_fits[season]
        if fit not in out.values():
            out[season] = fit
    return out
