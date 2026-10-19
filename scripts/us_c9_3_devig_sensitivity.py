"""Script: sensibilità al metodo di de-vigging, con Modulo 1 Elo.

Con `--run METODO` esegue gli agenti dell'esecuzione congelata sulla validazione e dell'esecuzione sul test 2023-24 con q dal metodo dato
(shk.model.devig_runs) e scrive le uscite per seed in results/raw/ (non versionate); i cinque
metodi girano come esecuzioni separate. Con `--run METODO --validation-only` solo la validazione,
senza rieseguire il 2023-24 (riproduzione da zero). Senza argomenti legge le uscite dei cinque
metodi e scrive results/us_c9_3_devig_sensitivity.csv (tabella metodo × metrica primaria × agente ×
configurazione, confronti, segno di ĝ per metodo, stabilità delle conclusioni dei confronti fra agenti e dell'esecuzione sul test 2023-24) e
thesis/figures/us_c9_3_devig_sensitivity.png (shk.model.devig_sensitivity). I tempi si misurano
dall'esterno.
"""

import sys

from shk.market.devig import DEVIG_METHOD_NAMES

WORKERS = 5


def run_experiment() -> None:
    """Tabelle e figura dalle uscite dei cinque metodi."""
    from shk.model.devig_sensitivity import write_outputs

    write_outputs()


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--run" in args:
        method = args[args.index("--run") + 1]
        if method not in DEVIG_METHOD_NAMES:
            raise ValueError(f"Unknown devig method {method!r}, expected one of {DEVIG_METHOD_NAMES}")
        from shk.model.devig_runs import run_method

        run_method(method, workers=WORKERS, test="--validation-only" not in args)
    else:
        run_experiment()
