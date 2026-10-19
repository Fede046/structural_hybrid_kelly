"""Esecuzioni di T63 (US-C9.3): agenti di T55 e T58 con q da ciascun metodo di de-vigging.

Per un metodo: DataFrame del Modulo 2 con δ e market_entropy da quel q (build_module2_frame);
validazione come T55 (19 stagioni, N_SEEDS seed block e realizzazione osservata) e 2023-24 come
T58 (seed block, seed iid e realizzazione osservata), con il Modulo 2 e la Baseline D che usano lo
stesso q. Parametri di frozen_params.toml invariati, Modulo 1 Elo, seed uguali a T55 e T58
(SEED_S10). Le uscite per seed vanno in results/raw/ (non versionate).
"""

from pathlib import Path
from typing import Final

from shk.model.module2_data import build_module2_frame
from shk.model.residuals import load_model_residuals
from shk.model.test_run import TEST_FIT, TEST_SEASON, evaluate_agents, load_season_data
from shk.model.validation_run import evaluate_validation, save_raw

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[3]
RAW_DIR: Final[Path] = REPO_ROOT / "results" / "raw"


def validation_raw_path(method: str) -> Path:
    """Uscite per seed della validazione con il metodo dato."""
    return RAW_DIR / f"us_c9_3_validation_raw_{method}.npz"


def test_raw_path(method: str, iid: bool = False) -> Path:
    """Uscite per seed del 2023-24 con il metodo dato (block, o iid con iid=True)."""
    return RAW_DIR / f"us_c9_3_test_raw_{method}{'_iid' if iid else ''}.npz"


def run_method(method: str, workers: int = 5, test: bool = True) -> None:
    """Test (2023-24) e validazione con il metodo dato; scrive le tre uscite per seed.

    Con test=False solo la validazione: il 2023-24 non si riesegue (riproduzione di T64).
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if test:
        sd = load_season_data(TEST_SEASON, TEST_FIT, devig_method=method)
        result = evaluate_agents(sd, workers=workers)
        save_raw(test_raw_path(method), result.block)
        save_raw(test_raw_path(method, iid=True), result.iid)
    frame = build_module2_frame(load_model_residuals(), devig_method=method)
    save_raw(validation_raw_path(method), evaluate_validation(frame, workers=workers, devig_method=method))
