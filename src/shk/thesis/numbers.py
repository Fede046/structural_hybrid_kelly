"""Numeri citabili della tesi e loro provenienza: thesis/numeri.md (T65).

Ogni voce è una sola cella di un CSV versionato (results/MANIFEST.sha256):
- la riga si seleziona con un'espressione di DataFrame.query (motore python) che deve
  selezionare esattamente una riga;
- il valore è la cella arrotondata a `decimals` cifre, col punto decimale;
- lo SHA256 è quello del manifesto, normalizzato se la riga del manifesto ha una regola.
Nessun numero si calcola: un valore che nei CSV non c'è non è una voce.

thesis/numeri.md si genera da NUMBERS con render_numbers. parse_numbers lo rilegge, e
check_entry ricontrolla una voce sul CSV, come fa il test.
"""

import math
from pathlib import Path
from typing import Final, NamedTuple

import pandas as pd

from shk.thesis.sources import REPO_ROOT, read_versioned_csv, versioned_csv

NUMBERS_PATH: Final[str] = "thesis/numeri.md"
TABLE_HEADER: Final[str] = "| id | descrizione | valore | unità | CSV | selezione | colonna | SHA256 |"


class NumberSpec(NamedTuple):
    """Voce citabile: tema, identificativo, descrizione, cella del CSV, cifre e unità."""

    theme: str
    id: str
    description: str
    csv: str
    query: str
    column: str
    decimals: int
    unit: str


class NumberEntry(NamedTuple):
    """Voce letta da thesis/numeri.md (tutti i campi come stringhe)."""

    id: str
    description: str
    value: str
    unit: str
    csv: str
    query: str
    column: str
    sha256: str


THEMES: Final[dict[str, str]] = {
    "c2": "C2 — Falso rigetto dell'ANOVA con autocorrelazione",
    "c3_1": "C3.1 — Finestra effettiva dei dati",
    "c3_2": "C3.2 — Divergenza fra metodi di de-vigging",
    "g_hat": "C4.2 e T57 — ĝ del Modulo 1 contro il mercato",
    "c5": "C5 — Perché ANOVA e non ADWIN",
    "c6_3": "C6.3 — Floor",
    "c6_4": "C6.4 e T44 — Eteroschedasticità",
    "modulo2": "S8 — Modulo 2",
    "confronti": "S10 — Confronti e test set",
    "robustezza": "S11 — Robustezza: Dixon-Coles, ranking e de-vigging",
}

_C2: Final[str] = "us_c2_anova_autocorrelation"
_C31: Final[str] = "us_c3_1_data_coverage"
_C32: Final[str] = "us_c3_2_devig_divergence"
_G: Final[str] = "us_c4_2b_g_hat_inference"
_Z: Final[str] = "us_c5_2_daily_z_test"
_FR: Final[str] = "us_c6_3_floor_real_config"
_FS: Final[str] = "us_c6_3_floor_synthetic"
_PB: Final[str] = "us_c6_2_paired_backtest"
_H: Final[str] = "us_c6_4_heteroskedasticity"
_V: Final[str] = "us_c6_4b_variance_change"
_K: Final[str] = "us_c7_3b_known_scenarios"
_DID: Final[str] = "us_c7_4_did_support"
_CMP: Final[str] = "us_c8_4_comparisons"
_T: Final[str] = "us_c8_5_test_run"
_TDC: Final[str] = "us_c8_5_test_run_dc"
_DC: Final[str] = "us_c9_1_dixon_coles"
_R: Final[str] = "us_c9_2_robustness"
_DV: Final[str] = "us_c9_3_devig_sensitivity"

_NOM: Final[str] = 'design == "contiguous_2" and method == "nominal"'
_CEN: Final[str] = 'design == "contiguous_2" and method == "block_bootstrap_centered"'
_GP: Final[str] = 'row_type == "interval" and season == "pooled"'
_ZO: Final[str] = 'row_type == "overall"'
_FRA: Final[str] = 'row_type == "aggregate"'
_KC: Final[str] = 'scenario == "2_covid" and version == "threefold"'
_CV: Final[str] = 'row_type == "comparison" and metric == "final_log_wealth"'


def _cmp(config: str, comparison: str) -> str:
    return f'{_CV} and config == "{config}" and comparison == "{comparison}"'


NUMBERS: Final[tuple[NumberSpec, ...]] = (
    # C2
    NumberSpec("c2", "c2_nom_due_meta_phi_0", "Falso rigetto nominale, due metà contigue, φ = 0", _C2,
               f"{_NOM} and phi == 0.0", "rejection_rate", 3, "quota di serie"),
    NumberSpec("c2", "c2_nom_due_meta_phi_03", "Falso rigetto nominale, due metà contigue, φ = 0.3", _C2,
               f"{_NOM} and phi == 0.3", "rejection_rate", 3, "quota di serie"),
    NumberSpec("c2", "c2_nom_due_meta_phi_05", "Falso rigetto nominale, due metà contigue, φ = 0.5", _C2,
               f"{_NOM} and phi == 0.5", "rejection_rate", 3, "quota di serie"),
    NumberSpec("c2", "c2_nom_due_meta_phi_07", "Falso rigetto nominale, due metà contigue, φ = 0.7", _C2,
               f"{_NOM} and phi == 0.7", "rejection_rate", 3, "quota di serie"),
    NumberSpec("c2", "c2_nom_38_blocchi_phi_03", "Falso rigetto nominale, 38 blocchi contigui, φ = 0.3", _C2,
               'design == "contiguous_38" and method == "nominal" and phi == 0.3', "rejection_rate", 3, "quota di serie"),
    NumberSpec("c2", "c2_nom_38_blocchi_phi_07", "Falso rigetto nominale, 38 blocchi contigui, φ = 0.7", _C2,
               'design == "contiguous_38" and method == "nominal" and phi == 0.7', "rejection_rate", 3, "quota di serie"),
    NumberSpec("c2", "c2_nom_casuale_phi_07", "Falso rigetto nominale, due gruppi casuali, φ = 0.7", _C2,
               'design == "random_2" and method == "nominal" and phi == 0.7', "rejection_rate", 3, "quota di serie"),
    NumberSpec("c2", "c2_mc_inf", "Estremo inferiore dell'intervallo Monte Carlo al 99% per α = 0.05", _C2,
               f"{_NOM} and phi == 0.0", "mc_lower_99", 4, "quota di serie"),
    NumberSpec("c2", "c2_mc_sup", "Estremo superiore dell'intervallo Monte Carlo al 99% per α = 0.05", _C2,
               f"{_NOM} and phi == 0.0", "mc_upper_99", 4, "quota di serie"),
    NumberSpec("c2", "c2_centrato_L7_phi_0", "Falso rigetto calibrato centrato (T40), L = 7, φ = 0", _C2,
               f"{_CEN} and block_length == 7.0 and phi == 0.0", "rejection_rate", 3, "quota di serie"),
    NumberSpec("c2", "c2_centrato_L20_phi_0", "Falso rigetto calibrato centrato (T40), L = 20, φ = 0", _C2,
               f"{_CEN} and block_length == 20.0 and phi == 0.0", "rejection_rate", 3, "quota di serie"),
    NumberSpec("c2", "c2_centrato_L40_phi_0", "Falso rigetto calibrato centrato (T40), L = 40, φ = 0", _C2,
               f"{_CEN} and block_length == 40.0 and phi == 0.0", "rejection_rate", 3, "quota di serie"),
    NumberSpec("c2", "c2_centrato_L20_phi_07", "Falso rigetto calibrato centrato (T40), L = 20, φ = 0.7", _C2,
               f"{_CEN} and block_length == 20.0 and phi == 0.7", "rejection_rate", 3, "quota di serie"),
    # C3.1
    NumberSpec("c3_1", "c3_1_partite_1993_94", "Partite della stagione 1993-94 (prima stagione)", _C31,
               'season == "1993-94" and group_name == "results"', "total_rows", 0, "partite"),
    NumberSpec("c3_1", "c3_1_partite_2022_23", "Partite della stagione 2022-23", _C31,
               'season == "2022-23" and group_name == "results"', "total_rows", 0, "partite"),
    NumberSpec("c3_1", "c3_1_wh_2000_01", "Partite con terna WH pre-partita completa nel 2000-01", _C31,
               'season == "2000-01" and group_name == "wh_1x2_prematch"', "complete_rows", 0, "partite"),
    NumberSpec("c3_1", "c3_1_b365_2002_03", "Partite con terna B365 pre-partita completa nel 2002-03 (prima stagione con B365)", _C31,
               'season == "2002-03" and group_name == "b365_1x2_prematch"', "complete_rows", 0, "partite"),
    NumberSpec("c3_1", "c3_1_ps_chiusura_2012_13", "Partite con terna Pinnacle di chiusura completa nel 2012-13", _C31,
               'season == "2012-13" and group_name == "ps_1x2_closing"', "complete_rows", 0, "partite"),
    # C3.2
    NumberSpec("c3_2", "c3_2_partite_usate", "Partite usate nella divergenza fra metodi", _C32,
               'level == "overall"', "matches_used", 0, "partite"),
    NumberSpec("c3_2", "c3_2_partite_escluse", "Partite escluse (2000-01, senza B365)", _C32,
               'level == "overall"', "matches_excluded", 0, "partite"),
    NumberSpec("c3_2", "c3_2_overround_medio", "Overround medio di B365", _C32,
               'level == "overall"', "mean_overround", 4, "quota"),
    NumberSpec("c3_2", "c3_2_spread_max", "Spread massimo fra i tre metodi", _C32,
               'level == "overall"', "max_spread_pts", 2, "punti percentuali"),
    NumberSpec("c3_2", "c3_2_spread_p99", "99° percentile dello spread fra i tre metodi", _C32,
               'level == "overall"', "p99_spread_pts", 2, "punti percentuali"),
    NumberSpec("c3_2", "c3_2_spread_max_su_edge", "Spread massimo diviso per l'edge di riferimento di 2 punti", _C32,
               'level == "overall"', "max_spread_ratio_to_edge", 2, "rapporto"),
    NumberSpec("c3_2", "c3_2_spread_p99_su_edge", "99° percentile dello spread diviso per l'edge di 2 punti", _C32,
               'level == "overall"', "p99_spread_ratio_to_edge", 2, "rapporto"),
    NumberSpec("c3_2", "c3_2_spread_medio_favoriti", "Spread medio nella fascia di quota [1, 1.5)", _C32,
               'level == "bin" and category == "[1, 1.5)"', "mean_spread_pts", 2, "punti percentuali"),
    NumberSpec("c3_2", "c3_2_spread_medio_2_3", "Spread medio nella fascia di quota [2, 3)", _C32,
               'level == "bin" and category == "[2, 3)"', "mean_spread_pts", 2, "punti percentuali"),
    NumberSpec("c3_2", "c3_2_spread_rel_outsider", "Spread relativo medio nella fascia di quota [10, inf)", _C32,
               'level == "bin" and category == "[10, inf)"', "mean_relative_spread", 3, "rapporto"),
    # ĝ
    NumberSpec("g_hat", "g_hat_b365_shin", "ĝ pooled, B365 pre-partita, Shin (19 stagioni di validazione)", _G,
               f'{_GP} and series == "b365_prematch" and method == "shin"', "g_hat", 4, "nat per partita"),
    NumberSpec("g_hat", "g_hat_b365_shin_inf", "ĝ pooled B365 Shin, IC 95% corretto, estremo inferiore", _G,
               f'{_GP} and series == "b365_prematch" and method == "shin"', "ci_block_low", 4, "nat per partita"),
    NumberSpec("g_hat", "g_hat_b365_shin_sup", "ĝ pooled B365 Shin, IC 95% corretto, estremo superiore", _G,
               f'{_GP} and series == "b365_prematch" and method == "shin"', "ci_block_high", 4, "nat per partita"),
    NumberSpec("g_hat", "g_hat_pinnacle_shin", "ĝ pooled, Pinnacle chiusura, Shin (10 stagioni dal 2012-13)", _G,
               f'{_GP} and series == "pinnacle_closing" and method == "shin"', "g_hat", 4, "nat per partita"),
    NumberSpec("g_hat", "g_hat_pinnacle_shin_inf", "ĝ pooled Pinnacle Shin, IC 95% corretto, estremo inferiore", _G,
               f'{_GP} and series == "pinnacle_closing" and method == "shin"', "ci_block_low", 4, "nat per partita"),
    NumberSpec("g_hat", "g_hat_pinnacle_shin_sup", "ĝ pooled Pinnacle Shin, IC 95% corretto, estremo superiore", _G,
               f'{_GP} and series == "pinnacle_closing" and method == "shin"', "ci_block_high", 4, "nat per partita"),
    NumberSpec("g_hat", "g_hat_b365_proporzionale", "ĝ pooled, B365 pre-partita, proporzionale", _G,
               f'{_GP} and series == "b365_prematch" and method == "proportional"', "g_hat", 4, "nat per partita"),
    NumberSpec("g_hat", "g_hat_b365_shin_rapporto", "ĝ pooled B365 Shin, rapporto delle ampiezze block/iid", _G,
               f'{_GP} and series == "b365_prematch" and method == "shin"', "width_ratio_block_iid", 2, "rapporto"),
    NumberSpec("g_hat", "g_hat_copertura_phi_0_block", "Copertura dell'intervallo block su AR(1), φ = 0", _G,
               'row_type == "coverage" and phi == 0.0', "coverage_stationary", 3, "quota di serie"),
    NumberSpec("g_hat", "g_hat_copertura_phi_0_iid", "Copertura dell'intervallo iid su AR(1), φ = 0", _G,
               'row_type == "coverage" and phi == 0.0', "coverage_iid", 3, "quota di serie"),
    NumberSpec("g_hat", "g_hat_copertura_phi_05_block", "Copertura dell'intervallo block su AR(1), φ = 0.5", _G,
               'row_type == "coverage" and phi == 0.5', "coverage_stationary", 3, "quota di serie"),
    NumberSpec("g_hat", "g_hat_copertura_phi_05_iid", "Copertura dell'intervallo iid su AR(1), φ = 0.5", _G,
               'row_type == "coverage" and phi == 0.5', "coverage_iid", 3, "quota di serie"),
    NumberSpec("g_hat", "g_hat_b365_shin_favorite_nette", "ĝ B365 Shin sulle partite con favorita in [1, 1.5)", _G,
               'row_type == "band" and series == "b365_prematch" and method == "shin" and band == "[1, 1.5)"',
               "g_hat", 4, "nat per partita"),
    # C5
    NumberSpec("c5", "c5_allarmi_z_nominale", "Allarmi dello Z-test nominale sulle 19 stagioni di validazione", _Z,
               f'{_ZO} and method == "z_nominal"', "n_alarms", 0, "allarmi"),
    NumberSpec("c5", "c5_allarmi_adwin", "Allarmi di ADWIN sulle 19 stagioni di validazione", _Z,
               f'{_ZO} and method == "adwin"', "n_alarms", 0, "allarmi"),
    NumberSpec("c5", "c5_allarmi_page_hinkley", "Allarmi di Page-Hinkley sulle 19 stagioni di validazione", _Z,
               f'{_ZO} and method == "page_hinkley"', "n_alarms", 0, "allarmi"),
    NumberSpec("c5", "c5_allarmi_z_L7", "Allarmi dello Z-test calibrato, L = 7", _Z,
               f'{_ZO} and method == "z_block_bootstrap" and block_length == 7.0', "n_alarms", 0, "allarmi"),
    NumberSpec("c5", "c5_allarmi_z_L20", "Allarmi dello Z-test calibrato, L = 20", _Z,
               f'{_ZO} and method == "z_block_bootstrap" and block_length == 20.0', "n_alarms", 0, "allarmi"),
    NumberSpec("c5", "c5_allarmi_z_L40", "Allarmi dello Z-test calibrato, L = 40", _Z,
               f'{_ZO} and method == "z_block_bootstrap" and block_length == 40.0', "n_alarms", 0, "allarmi"),
    NumberSpec("c5", "c5_allarmi_attesi", "Allarmi attesi per stagione sotto H0 (α = 0.05 su 38 matchday)", _Z,
               f'{_ZO} and method == "z_nominal"', "expected_alarms", 1, "allarmi per stagione"),
    NumberSpec("c5", "c5_media_z_nominale", "Allarmi medi per stagione dello Z-test nominale", _Z,
               f'{_ZO} and method == "z_nominal"', "mean_alarms", 2, "allarmi per stagione"),
    # C6.3
    NumberSpec("c6_3", "c6_3_rovina_A_001", "Tasso di rovina di A con floor £0.01 (configurazione reale)", _FR,
               f'{_FRA} and config == "gbp_0.01" and agent == "A"', "ruin_rate", 4, "quota di traiettorie"),
    NumberSpec("c6_3", "c6_3_rovina_A_001_inf", "Rovina di A con £0.01, IC 99%, estremo inferiore", _FR,
               f'{_FRA} and config == "gbp_0.01" and agent == "A"', "ruin_rate_ci_lower", 4, "quota di traiettorie"),
    NumberSpec("c6_3", "c6_3_rovina_A_001_sup", "Rovina di A con £0.01, IC 99%, estremo superiore", _FR,
               f'{_FRA} and config == "gbp_0.01" and agent == "A"', "ruin_rate_ci_upper", 4, "quota di traiettorie"),
    NumberSpec("c6_3", "c6_3_rovina_A_1", "Tasso di rovina di A con floor £1 (configurazione reale)", _FR,
               f'{_FRA} and config == "gbp_1" and agent == "A"', "ruin_rate", 4, "quota di traiettorie"),
    NumberSpec("c6_3", "c6_3_rovina_B025_1", "Tasso di rovina di B_0.25 con floor £1 (configurazione reale)", _FR,
               f'{_FRA} and config == "gbp_1" and agent == "B_0.25"', "ruin_rate", 4, "quota di traiettorie"),
    NumberSpec("c6_3", "c6_3_rovina_A_senza_floor", "Tasso di rovina di A senza floor (configurazione reale)", _FR,
               f'{_FRA} and config == "none" and agent == "A"', "ruin_rate", 4, "quota di traiettorie"),
    NumberSpec("c6_3", "c6_3_sintetico_50_floor", "Rovina sul calendario sintetico, B0/F = 50, 1000 date, col floor", _FS,
               'experiment == "A" and config_id == "A_ratio_50_floor" and horizon == 1000', "ruin_rate", 4,
               "quota di repliche"),
    NumberSpec("c6_3", "c6_3_sintetico_50_senza_floor", "Rovina sul calendario sintetico, B0/F = 50, 1000 date, senza floor", _FS,
               'experiment == "A" and config_id == "A_ratio_50_nofloor" and horizon == 1000', "ruin_rate", 4,
               "quota di repliche"),
    NumberSpec("c6_3", "c6_3_sweep_31_6", "Rovina nello sweep, B0/F = 31.6, 1000 date", _FS,
               'experiment == "B" and config_id == "B_ratio_3.1623e+01" and horizon == 1000', "ruin_rate", 4,
               "quota di repliche"),
    NumberSpec("c6_3", "c6_3_sweep_100", "Rovina nello sweep, B0/F = 100, 1000 date", _FS,
               'experiment == "B" and config_id == "B_ratio_1.0000e+02" and horizon == 1000', "ruin_rate", 4,
               "quota di repliche"),
    NumberSpec("c6_3", "c6_3_accelerazione_a", "Fattore di accelerazione della rovina, configurazione (a)", _FS,
               'experiment == "C" and config_id == "C_a"', "acceleration_factor", 1, "rapporto"),
    NumberSpec("c6_3", "c6_3_tempo_medio_a", "Tempo medio di rovina, configurazione (a)", _FS,
               'experiment == "C" and config_id == "C_a"', "mean_ruin_time", 1, "date"),
    NumberSpec("c6_3", "c6_3_tempo_mediano_a", "Tempo mediano di rovina, configurazione (a)", _FS,
               'experiment == "C" and config_id == "C_a"', "median_ruin_time", 1, "date"),
    NumberSpec("c6_3", "c6_3_B010_senza_floor", "Somma sulle stagioni della log-ricchezza finale di B_0.10 senza floor (T35)", _PB,
               'row_type == "summary" and config == "none" and agent == "B_0.10"', "sum_final_log_wealth", 3,
               "log-ricchezza (nat)"),
    NumberSpec("c6_3", "c6_3_B010_floor_1", "Somma sulle stagioni della log-ricchezza finale di B_0.10 con £1 (T35)", _PB,
               'row_type == "summary" and config == "gbp_1" and agent == "B_0.10"', "sum_final_log_wealth", 3,
               "log-ricchezza (nat)"),
    NumberSpec("c6_3", "c6_3_B025_senza_floor", "Somma sulle stagioni della log-ricchezza finale di B_0.25 senza floor (T35)", _PB,
               'row_type == "summary" and config == "none" and agent == "B_0.25"', "sum_final_log_wealth", 3,
               "log-ricchezza (nat)"),
    NumberSpec("c6_3", "c6_3_B025_floor_1", "Somma sulle stagioni della log-ricchezza finale di B_0.25 con £1 (T35)", _PB,
               'row_type == "summary" and config == "gbp_1" and agent == "B_0.25"', "sum_final_log_wealth", 3,
               "log-ricchezza (nat)"),
    # C6.4
    NumberSpec("c6_4", "c6_4_bp_congiunto_nominale", "Rigetti di BP congiunto con soglia χ² nominale (19 stagioni)", _H,
               'row_type == "summary" and statistic == "bp_joint" and method == "nominal"', "n_validation_rejections", 0,
               "rigetti"),
    NumberSpec("c6_4", "c6_4_bp_congiunto_L20", "Rigetti di BP congiunto con soglia calibrata, L = 20", _H,
               'row_type == "summary" and statistic == "bp_joint" and method == "bootstrap_L20"', "n_validation_rejections", 0,
               "rigetti"),
    NumberSpec("c6_4", "c6_4_white_nominale", "Rigetti di White con soglia χ² nominale", _H,
               'row_type == "summary" and statistic == "white" and method == "nominal"', "n_validation_rejections", 0,
               "rigetti"),
    NumberSpec("c6_4", "c6_4_white_L20", "Rigetti di White con soglia calibrata, L = 20", _H,
               'row_type == "summary" and statistic == "white" and method == "bootstrap_L20"', "n_validation_rejections", 0,
               "rigetti"),
    NumberSpec("c6_4", "c6_4_bp_temporale_L20", "Rigetti di BP temporale con soglia calibrata, L = 20", _H,
               'row_type == "summary" and statistic == "bp_time" and method == "bootstrap_L20"', "n_validation_rejections", 0,
               "rigetti"),
    NumberSpec("c6_4", "c6_4_gq_L20", "Rigetti di Goldfeld-Quandt con soglia calibrata, L = 20 (T44)", _V,
               'row_type == "summary" and statistic == "goldfeld_quandt" and method == "mbb_L20"', "rejections", 0,
               "rigetti"),
    NumberSpec("c6_4", "c6_4_gq_L20_p", "P(X ≥ 3) binomiale per 3 rigetti su 19 (Goldfeld-Quandt, L = 20)", _V,
               'row_type == "summary" and statistic == "goldfeld_quandt" and method == "mbb_L20"', "p_value_binomial", 4,
               "probabilità"),
    NumberSpec("c6_4", "c6_4_arch_LPW", "Rigetti di ARCH-LM con soglia calibrata, L_PW (T44)", _V,
               'row_type == "summary" and statistic == "arch_lm" and method == "mbb_LPW"', "rejections", 0, "rigetti"),
    NumberSpec("c6_4", "c6_4_brown_forsythe", "Statistica di Brown-Forsythe fra le 19 stagioni (T44)", _V,
               'row_type == "between_seasons" and method == "nominal"', "statistic_value", 3, "statistica"),
    NumberSpec("c6_4", "c6_4_brown_forsythe_soglia_nominale", "Soglia nominale di Brown-Forsythe", _V,
               'row_type == "between_seasons" and method == "nominal"', "threshold", 3, "statistica"),
    # Modulo 2
    NumberSpec("modulo2", "modulo2_covid_totale", "Scenario 2 (sospensione 2019-20): differenza totale di δ", _K,
               f'{_KC} and quantity == "total"', "estimate", 4, "nat per partita"),
    NumberSpec("modulo2", "modulo2_covid_compositiva", "Scenario 2: componente compositiva", _K,
               f'{_KC} and quantity == "compositional"', "estimate", 4, "nat per partita"),
    NumberSpec("modulo2", "modulo2_covid_strutturale", "Scenario 2: componente strutturale", _K,
               f'{_KC} and quantity == "structural"', "estimate", 4, "nat per partita"),
    NumberSpec("modulo2", "modulo2_covid_interazione", "Scenario 2: interazione", _K,
               f'{_KC} and quantity == "interaction"', "estimate", 4, "nat per partita"),
    NumberSpec("modulo2", "modulo2_covid_pi", "Scenario 2: quota strutturale π", _K,
               f'{_KC} and quantity == "structural_share"', "estimate", 3, "quota"),
    NumberSpec("modulo2", "modulo2_covid_n_a", "Scenario 2: partite del gruppo A (prima della sospensione)", _K,
               f'{_KC} and quantity == "total"', "n_a", 0, "partite"),
    NumberSpec("modulo2", "modulo2_covid_n_b", "Scenario 2: partite del gruppo B (dopo la sospensione)", _K,
               f'{_KC} and quantity == "total"', "n_b", 0, "partite"),
    NumberSpec("modulo2", "modulo2_did_pooled", "DiD pooled delle neopromosse (T49)", _DID,
               'row_type == "did" and season == "pooled"', "estimate", 4, "nat per partita"),
    NumberSpec("modulo2", "modulo2_did_pooled_inf", "DiD pooled, IC 95%, estremo inferiore", _DID,
               'row_type == "did" and season == "pooled"', "lower", 4, "nat per partita"),
    NumberSpec("modulo2", "modulo2_did_pooled_sup", "DiD pooled, IC 95%, estremo superiore", _DID,
               'row_type == "did" and season == "pooled"', "upper", 4, "nat per partita"),
    # Confronti (S10)
    NumberSpec("confronti", "confronti_copertura_percentile", "Copertura dell'intervallo percentile sul run prescritto (T56)", _CMP,
               'row_type == "coverage" and source == "seeds_resampled"', "coverage", 3, "quota di repliche"),
    NumberSpec("confronti", "confronti_copertura_corretta", "Copertura dell'intervallo con la correzione t (T56)", _CMP,
               'row_type == "coverage" and source == "seeds_resampled"', "coverage_corrected", 3, "quota di repliche"),
    NumberSpec("confronti", "confronti_C2_DADWIN_001", "C2 − D_ADWIN, log-ricchezza finale, £0.01, validazione", _CMP,
               _cmp("gbp_0.01", "C2-D_ADWIN"), "estimate", 3, "log-ricchezza (nat)"),
    NumberSpec("confronti", "confronti_C2_DPH_001", "C2 − D_PH, log-ricchezza finale, £0.01, validazione", _CMP,
               _cmp("gbp_0.01", "C2-D_PH"), "estimate", 3, "log-ricchezza (nat)"),
    NumberSpec("confronti", "confronti_C2_E_001", "C2 − E, log-ricchezza finale, £0.01, validazione", _CMP,
               _cmp("gbp_0.01", "C2-E"), "estimate", 3, "log-ricchezza (nat)"),
    NumberSpec("confronti", "confronti_rilevare_001", "Rilevare (C1 − C0), log-ricchezza finale, £0.01, validazione", _CMP,
               _cmp("gbp_0.01", "C1-C0"), "estimate", 3, "log-ricchezza (nat)"),
    NumberSpec("confronti", "confronti_graduare_001", "Graduare (C2 − C1), log-ricchezza finale, £0.01, validazione", _CMP,
               _cmp("gbp_0.01", "C2-C1"), "estimate", 3, "log-ricchezza (nat)"),
    NumberSpec("confronti", "confronti_graduare_001_inf", "Graduare, £0.01, validazione, IC 95%, estremo inferiore", _CMP,
               _cmp("gbp_0.01", "C2-C1"), "ci_block_low", 3, "log-ricchezza (nat)"),
    NumberSpec("confronti", "confronti_graduare_001_sup", "Graduare, £0.01, validazione, IC 95%, estremo superiore", _CMP,
               _cmp("gbp_0.01", "C2-C1"), "ci_block_high", 3, "log-ricchezza (nat)"),
    NumberSpec("confronti", "confronti_graduare_1", "Graduare (C2 − C1), log-ricchezza finale, £1, validazione", _CMP,
               _cmp("gbp_1", "C2-C1"), "estimate", 3, "log-ricchezza (nat)"),
    NumberSpec("confronti", "confronti_rapporto_C2_DADWIN_001", "Rapporto delle ampiezze block/iid, C2 − D_ADWIN, £0.01", _CMP,
               _cmp("gbp_0.01", "C2-D_ADWIN"), "width_ratio_block_iid", 3, "rapporto"),
    NumberSpec("confronti", "test_C2_DADWIN_001", "C2 − D_ADWIN, log-ricchezza finale, £0.01, test 2023-24", _T,
               _cmp("gbp_0.01", "C2-D_ADWIN"), "estimate", 3, "log-ricchezza (nat)"),
    NumberSpec("confronti", "test_C2_DPH_001", "C2 − D_PH, log-ricchezza finale, £0.01, test 2023-24", _T,
               _cmp("gbp_0.01", "C2-D_PH"), "estimate", 3, "log-ricchezza (nat)"),
    NumberSpec("confronti", "test_C2_E_001", "C2 − E, log-ricchezza finale, £0.01, test 2023-24", _T,
               _cmp("gbp_0.01", "C2-E"), "estimate", 3, "log-ricchezza (nat)"),
    NumberSpec("confronti", "test_rilevare_001", "Rilevare (C1 − C0), £0.01, test 2023-24", _T,
               _cmp("gbp_0.01", "C1-C0"), "estimate", 3, "log-ricchezza (nat)"),
    NumberSpec("confronti", "test_graduare_001", "Graduare (C2 − C1), £0.01, test 2023-24", _T,
               _cmp("gbp_0.01", "C2-C1"), "estimate", 3, "log-ricchezza (nat)"),
    NumberSpec("confronti", "test_log_loss", "Log-loss del Modulo 1 (Elo) sul 2023-24", _T,
               'row_type == "log_loss" and series == "b365_prematch"', "estimate", 3, "nat per partita"),
    NumberSpec("confronti", "test_g_hat_b365_shin", "ĝ B365 Shin sul 2023-24", _T,
               'row_type == "g_hat" and series == "b365_prematch" and method == "shin"', "estimate", 4, "nat per partita"),
    NumberSpec("confronti", "test_g_hat_pinnacle_shin", "ĝ Pinnacle Shin sul 2023-24", _T,
               'row_type == "g_hat" and series == "pinnacle_closing" and method == "shin"', "estimate", 4, "nat per partita"),
    NumberSpec("confronti", "test_allarmi_adwin", "Allarmi di ADWIN sul 2023-24", _T,
               'row_type == "drift" and detector == "adwin"', "n_alarms", 0, "allarmi"),
    NumberSpec("confronti", "test_allarmi_page_hinkley", "Allarmi di Page-Hinkley sul 2023-24", _T,
               'row_type == "drift" and detector == "page_hinkley"', "n_alarms", 0, "allarmi"),
    NumberSpec("confronti", "test_violazioni_leakage", "Violazioni anti-leakage sulle 380 partite del 2023-24", _T,
               'row_type == "check"', "leakage_violations", 0, "partite"),
    NumberSpec("confronti", "test_roi_E_001", "ROI osservato di E sul 2023-24, £0.01", _T,
               'row_type == "e_roi" and config == "gbp_0.01" and reference_roi == -0.041', "observed_roi", 4, "quota"),
    NumberSpec("confronti", "test_roi_E_1", "ROI osservato di E sul 2023-24, £1", _T,
               'row_type == "e_roi" and config == "gbp_1" and reference_roi == -0.041', "observed_roi", 4, "quota"),
    NumberSpec("confronti", "test_roi_paper", "ROI di riferimento del paper", _T,
               'row_type == "e_roi" and config == "gbp_0.01" and reference_roi == -0.041', "reference_roi", 3, "quota"),
    # Robustezza (S11)
    NumberSpec("robustezza", "dc_log_loss_validazione", "Log-loss di Dixon-Coles, validazione pooled", _DC,
               'row_type == "validation" and season == "pooled" and model == "dixon_coles" and method.isna()', "log_loss", 4,
               "nat per partita"),
    NumberSpec("robustezza", "elo_log_loss_validazione", "Log-loss dell'Elo, validazione pooled", _DC,
               'row_type == "validation" and season == "pooled" and model == "elo" and method.isna()', "log_loss", 4,
               "nat per partita"),
    NumberSpec("robustezza", "dc_g_hat_shin_validazione", "ĝ B365 Shin di Dixon-Coles, validazione pooled", _DC,
               'row_type == "validation" and season == "pooled" and model == "dixon_coles" and method == "shin"', "g_hat", 4,
               "nat per partita"),
    NumberSpec("robustezza", "dc_neopromosse", "Log-loss di Dixon-Coles sulle neopromosse mai viste, primi 10 matchday", _DC,
               'row_type == "new_teams_early" and model == "dixon_coles"', "log_loss", 4, "nat per partita"),
    NumberSpec("robustezza", "elo_neopromosse", "Log-loss dell'Elo sulle neopromosse mai viste, primi 10 matchday", _DC,
               'row_type == "new_teams_early" and model == "elo"', "log_loss", 4, "nat per partita"),
    NumberSpec("robustezza", "dc_test_log_loss", "Log-loss di Dixon-Coles sul 2023-24", _TDC,
               'row_type == "log_loss" and series == "b365_prematch"', "estimate", 3, "nat per partita"),
    NumberSpec("robustezza", "dc_test_g_hat_shin", "ĝ B365 Shin di Dixon-Coles sul 2023-24", _TDC,
               'row_type == "g_hat" and series == "b365_prematch" and method == "shin"', "estimate", 4, "nat per partita"),
    NumberSpec("robustezza", "tau_validazione_001", "τ_b Elo/Dixon-Coles, log-ricchezza finale, £0.01, validazione", _R,
               'row_type == "tau" and dataset == "validation" and config == "gbp_0.01" and metric == "final_log_wealth"',
               "tau", 3, "τ_b"),
    NumberSpec("robustezza", "tau_validazione_001_inf", "τ_b, log-ricchezza finale, £0.01, validazione, IC 95%, inferiore", _R,
               'row_type == "tau" and dataset == "validation" and config == "gbp_0.01" and metric == "final_log_wealth"',
               "ci_low", 3, "τ_b"),
    NumberSpec("robustezza", "tau_validazione_001_sup", "τ_b, log-ricchezza finale, £0.01, validazione, IC 95%, superiore", _R,
               'row_type == "tau" and dataset == "validation" and config == "gbp_0.01" and metric == "final_log_wealth"',
               "ci_high", 3, "τ_b"),
    NumberSpec("robustezza", "tau_validazione_recupero_001", "τ_b, tempo di recupero, £0.01, validazione", _R,
               'row_type == "tau" and dataset == "validation" and config == "gbp_0.01" and metric == "recovery_time"',
               "tau", 3, "τ_b"),
    NumberSpec("robustezza", "tau_test_001", "τ_b, log-ricchezza finale, £0.01, test 2023-24", _R,
               'row_type == "tau" and dataset == "test" and config == "gbp_0.01" and metric == "final_log_wealth"',
               "tau", 3, "τ_b"),
    NumberSpec("robustezza", "dc_graduare_001", "Graduare (C2 − C1) con Dixon-Coles, £0.01, validazione", _R,
               'row_type == "comparison" and dataset == "validation" and config == "gbp_0.01" '
               'and metric == "final_log_wealth" and comparison == "C2-C1"', "estimate_dc", 3, "log-ricchezza (nat)"),
    NumberSpec("robustezza", "dc_graduare_001_inf", "Graduare con Dixon-Coles, £0.01, validazione, IC 95%, inferiore", _R,
               'row_type == "comparison" and dataset == "validation" and config == "gbp_0.01" '
               'and metric == "final_log_wealth" and comparison == "C2-C1"', "ci_low_dc", 3, "log-ricchezza (nat)"),
    NumberSpec("robustezza", "dc_graduare_001_sup", "Graduare con Dixon-Coles, £0.01, validazione, IC 95%, superiore", _R,
               'row_type == "comparison" and dataset == "validation" and config == "gbp_0.01" '
               'and metric == "final_log_wealth" and comparison == "C2-C1"', "ci_high_dc", 3, "log-ricchezza (nat)"),
    NumberSpec("robustezza", "devig_g_hat_b365_proporzionale", "ĝ pooled B365 col metodo proporzionale (T63)", _DV,
               'row_type == "g_hat" and dataset == "validation" and series == "b365_prematch" and method == "proportional" '
               'and season == "pooled"', "estimate", 4, "nat per partita"),
    NumberSpec("robustezza", "devig_g_hat_b365_odds_ratio", "ĝ pooled B365 col metodo odds ratio (T63)", _DV,
               'row_type == "g_hat" and dataset == "validation" and series == "b365_prematch" and method == "odds_ratio" '
               'and season == "pooled"', "estimate", 4, "nat per partita"),
    NumberSpec("robustezza", "devig_g_hat_test_b365_additivo", "ĝ B365 col metodo additivo sul 2023-24 (T63)", _DV,
               'row_type == "g_hat" and dataset == "test" and series == "b365_prematch" and method == "additive"',
               "estimate", 4, "nat per partita"),
)


def select_row(df: pd.DataFrame, query: str) -> pd.Series:
    """L'unica riga che soddisfa l'espressione (DataFrame.query, motore python).

    Solleva
    -------
    ValueError
        Se le righe sono zero o più di una.
    """
    rows = df.query(query, engine="python")
    if len(rows) != 1:
        raise ValueError(f"Query {query!r} selects {len(rows)} rows, expected 1")
    return rows.iloc[0]


def format_value(value: float, decimals: int) -> str:
    """Valore col punto decimale e `decimals` cifre.

    Solleva
    -------
    ValueError
        Se il valore non è finito.
    """
    x = float(value)
    if not math.isfinite(x):
        raise ValueError(f"Value {value!r} is not finite")
    return f"{x:.{decimals}f}"


def _check_spec(spec: NumberSpec) -> None:
    for field in (spec.id, spec.description, spec.query, spec.column, spec.unit):
        if "|" in field or "`" in field:
            raise ValueError(f"Number {spec.id!r}: '|' and '`' are not allowed")
    if spec.theme not in THEMES:
        raise ValueError(f"Number {spec.id!r}: unknown theme {spec.theme!r}")


def render_numbers(root: Path | str = REPO_ROOT) -> str:
    """Testo di thesis/numeri.md, dalle voci di NUMBERS.

    Solleva
    -------
    ValueError
        Se un identificativo si ripete, una selezione non dà una riga o un valore non è finito.
    """
    ids = [s.id for s in NUMBERS]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate number ids")
    lines = [
        "# Numeri citabili",
        "",
        "Generato da `scripts/build_thesis_tables.py` (T65) dai CSV versionati: non modificare a mano.",
        "",
        "Ogni voce è una cella di un CSV elencato in `results/MANIFEST.sha256`:",
        "- **selezione**: espressione di `pandas.DataFrame.query` (motore python) che seleziona esattamente una riga;",
        "- **valore**: la cella arrotondata alle cifre mostrate, col punto decimale;",
        "- **SHA256**: quello del manifesto. Un CSV con una regola di normalizzazione nel manifesto si legge con la regola,",
        "  e lo SHA256 è quello normalizzato (per esempio `us_c3_1_data_coverage.csv`, senza le righe del 2023-24).",
        "",
        "`tests/test_thesis_outputs.py` rilegge ogni voce e confronta valore e SHA256.",
    ]
    for theme, title in THEMES.items():
        specs = [s for s in NUMBERS if s.theme == theme]
        if not specs:
            continue
        lines += ["", f"## {title}", "", TABLE_HEADER, "|---|---|---|---|---|---|---|---|"]
        for spec in specs:
            _check_spec(spec)
            source = versioned_csv(spec.csv, root)
            row = select_row(read_versioned_csv(spec.csv, root), spec.query)
            value = format_value(row[spec.column], spec.decimals)
            lines.append(
                f"| {spec.id} | {spec.description} | {value} | {spec.unit} | {source.path} | `{spec.query}` "
                f"| {spec.column} | {source.sha256} |"
            )
    return "\n".join(lines) + "\n"


def parse_numbers(text: str) -> list[NumberEntry]:
    """Voci di thesis/numeri.md, nell'ordine del file.

    Solleva
    -------
    ValueError
        Se una riga di tabella non ha gli otto campi attesi.
    """
    entries = []
    for line in text.splitlines():
        if not line.startswith("| ") or line == TABLE_HEADER:
            continue
        fields = [f.strip() for f in line.strip().strip("|").split("|")]
        if len(fields) != 8:
            raise ValueError(f"Malformed number line: {line!r}")
        query = fields[5]
        if not (query.startswith("`") and query.endswith("`")):
            raise ValueError(f"Malformed selection in line: {line!r}")
        fields[5] = query[1:-1]
        entries.append(NumberEntry(*fields))
    return entries


def check_entry(entry: NumberEntry, root: Path | str = REPO_ROOT) -> list[str]:
    """Differenze fra una voce e il CSV (lista vuota se coincidono).

    Il valore coincide se la cella dista dal valore scritto al più mezza unità dell'ultima
    cifra mostrata; lo SHA256 deve essere quello del manifesto.
    """
    problems = []
    name = Path(entry.csv).stem
    if entry.csv != f"results/{name}.csv":
        return [f"{entry.id}: unexpected CSV path {entry.csv!r}"]
    try:
        source = versioned_csv(name, root)
        row = select_row(read_versioned_csv(name, root), entry.query)
    except ValueError as exc:
        return [f"{entry.id}: {exc}"]
    if source.sha256 != entry.sha256:
        problems.append(f"{entry.id}: SHA256 {entry.sha256} != manifest {source.sha256}")
    decimals = len(entry.value.partition(".")[2])
    actual = float(row[entry.column])
    if not math.isfinite(actual) or abs(actual - float(entry.value)) > 0.5 * 10.0 ** (-decimals) + 1e-12:
        problems.append(f"{entry.id}: value {entry.value} != CSV {actual!r}")
    return problems
