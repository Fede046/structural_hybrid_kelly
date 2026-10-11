"""Test di controllo del comportamento di anova_lm su fit HAC (US-C6.4 / Task 38).

Verifica esplicitamente:
- con typ=1 l'F di anova_lm sul fit HAC coincide con l'F dell'OLS ordinario (rel 1e-12);
- con typ=2 e typ=3 l'F di anova_lm sul fit HAC coincide col test di Wald HAC del coefficiente di gruppo (rel 1e-10)
  ed e' diverso dall'F dell'OLS;
- la colonna sum_sq di typ=2 e' diversa dalla somma dei quadrati tra gruppi dell'OLS.
"""

import math
import numpy as np
import pandas as pd
from statsmodels.formula.api import ols as sm_ols
from statsmodels.stats.anova import anova_lm

from shk.stats.timeseries import generate_ar1_series


def test_hac_anova_lm_behavior() -> None:
    """Verifica il comportamento di anova_lm (typ 1, 2, 3) su una serie AR(1) fittata con HAC."""
    # 1. Generazione della serie AR(1) stazionaria con phi = 0.7, n = 380, seed fisso
    rng = np.random.default_rng(20261009)
    phi = 0.7
    n = 380
    y = generate_ar1_series(phi=phi, n=n, m=1, rng=rng)[0]

    # Due gruppi contigui da 190
    g = np.array([0] * 190 + [1] * 190, dtype=np.int64)
    df_data = pd.DataFrame({"y": y, "g": g})

    # 2. Fit OLS semplice e fit HAC
    fit_ols = sm_ols("y ~ C(g)", data=df_data).fit()
    fit_hac = sm_ols("y ~ C(g)", data=df_data).fit(cov_type="HAC", cov_kwds={"maxlags": 5})

    # 3. anova_lm con typ = 1, 2, 3 sul fit HAC
    aov1 = anova_lm(fit_hac, typ=1)
    aov2 = anova_lm(fit_hac, typ=2)
    aov3 = anova_lm(fit_hac, typ=3)

    f_ols = float(fit_ols.fvalue)
    wald_hac = float(fit_hac.wald_test("C(g)[T.1] = 0", use_f=True).statistic)

    f_typ1 = float(aov1.loc["C(g)", "F"])
    f_typ2 = float(aov2.loc["C(g)", "F"])
    f_typ3 = float(aov3.loc["C(g)", "F"])

    sum_sq_ols_between = float(fit_ols.ess)
    sum_sq_typ2 = float(aov2.loc["C(g)", "sum_sq"])

    # 4. Asserzioni come da specifica:
    # 4a. Con typ=1 l'F coincide con quello dell'OLS ordinario (rel 1e-12)
    assert math.isclose(f_typ1, f_ols, rel_tol=1e-12), (
        f"anova_lm typ=1 F ({f_typ1}) differs from OLS F ({f_ols})"
    )

    # 4b. Con typ=2 e typ=3 l'F coincide col Wald HAC del coefficiente di gruppo (rel 1e-10)
    assert math.isclose(f_typ2, wald_hac, rel_tol=1e-10), (
        f"anova_lm typ=2 F ({f_typ2}) differs from Wald HAC ({wald_hac})"
    )
    assert math.isclose(f_typ3, wald_hac, rel_tol=1e-10), (
        f"anova_lm typ=3 F ({f_typ3}) differs from Wald HAC ({wald_hac})"
    )

    # 4c. Con typ=2 e typ=3 l'F e' diverso dall'F dell'OLS ordinario
    assert not math.isclose(f_typ2, f_ols, rel_tol=1e-3), (
        f"anova_lm typ=2 F ({f_typ2}) unexpectedly matches OLS F ({f_ols})"
    )
    assert not math.isclose(f_typ3, f_ols, rel_tol=1e-3), (
        f"anova_lm typ=3 F ({f_typ3}) unexpectedly matches OLS F ({f_ols})"
    )

    # 4d. La colonna sum_sq di typ=2 e' diversa dalla somma dei quadrati tra gruppi dell'OLS
    assert not math.isclose(sum_sq_typ2, sum_sq_ols_between, rel_tol=1e-3), (
        f"anova_lm typ=2 sum_sq ({sum_sq_typ2}) unexpectedly matches OLS sum_sq ({sum_sq_ols_between})"
    )
