"""Tabelle della tesi, una funzione per tabella, dai soli CSV versionati.

Temi e tabelle:
- falso rigetto dell'ANOVA per φ: tab_falso_rigetto;
- finestra effettiva dei dati: tab_finestra_dati;
- divergenza fra metodi di de-vigging: tab_divergenza_devig;
- ĝ del Modulo 1 contro il mercato: tab_g_hat;
- "perché ANOVA e non ADWIN": tab_allarmi;
- floor: tab_floor_reale e tab_floor_sintetico;
- eteroschedasticità: tab_eteroschedasticita;
- Modulo 2: tab_modulo2_covid e tab_modulo2_transizioni;
- confronti fra agenti: tab_confronti;
- robustezza: tab_dixon_coles, tab_ranking, tab_confronti_dc e tab_devig.
Un tema ha più tabelle quando le sue grandezze hanno forme diverse.

Le funzioni selezionano righe, le riordinano o le rimodellano e formattano i valori: nessuna
media, mediana, conteggio o rapporto si calcola qui. Le note citano solo celle dei CSV o
fatti delle decisioni del backlog.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Final

import pandas as pd

from shk.thesis.labels import AGENTS, CONFIGS, METHODS, METRICS, MODELS, SERIES, comparison
from shk.thesis.latex import Cell, Column, ThesisTable, format_number, integer, interval, latex_escape, num, text
from shk.thesis.sources import REPO_ROOT, read_versioned_csv, versioned_csv

CONFIG_ORDER: Final[tuple[str, ...]] = ("gbp_0.01", "gbp_1", "none")
PREMATCH_SOURCES: Final[tuple[str, ...]] = (
    "b365", "bs", "bw", "gb", "iw", "lb", "ps", "sb", "sj", "so", "sy", "vc", "wh",
)


def select(df: pd.DataFrame, query: str) -> pd.DataFrame:
    """Righe che soddisfano l'espressione di DataFrame.query (motore python)."""
    return df.query(query, engine="python")


def one(df: pd.DataFrame, query: str) -> pd.Series:
    """L'unica riga che soddisfa l'espressione.

    Solleva
    -------
    ValueError
        Se le righe sono zero o più di una.
    """
    rows = select(df, query)
    if len(rows) != 1:
        raise ValueError(f"Query {query!r} selects {len(rows)} rows, expected 1")
    return rows.iloc[0]


def _q(value: object) -> str:
    """Valore da inserire in un'espressione di query."""
    return repr(value.item() if hasattr(value, "item") else value)


def _ordered(values: pd.Series) -> list:
    """Valori distinti nell'ordine in cui compaiono."""
    return list(dict.fromkeys(values.tolist()))


def _label(mapping: dict, code: str) -> Cell:
    lab = mapping[code]
    return text(lab.latex, lab.plain)


def _config(code: str) -> Cell:
    return _label(CONFIGS, code)


def table_false_rejection(root: Path | str = REPO_ROOT) -> ThesisTable:
    """Tasso di falso rigetto dell'ANOVA nominale per φ e disegno dei gruppi."""
    src = versioned_csv("us_c2_anova_autocorrelation", root)
    nom = select(read_versioned_csv(src.name, root), 'method == "nominal"')
    designs = ("contiguous_2", "contiguous_38", "random_2")
    rows = []
    for phi in _ordered(nom.phi):
        cells = [num(phi, 1)]
        for design in designs:
            cells.append(num(one(nom, f'design == "{design}" and phi == {_q(phi)}').rejection_rate, 3))
        rows.append(tuple(cells))
    ref = one(nom, 'design == "contiguous_2" and phi == 0.0')
    notes = (
        rf"ANOVA a una via con soglia nominale (quantile 0,95 della $F(k - 1, N - k)$), "
        rf"{format_number(ref.n_series, 0)} serie AR(1) di 380 osservazioni per ogni $\varphi$, "
        "innovazioni $N(0, 1)$ e nessuna differenza fra i gruppi: ogni rigetto è falso.",
        "Disegni: due metà contigue da 190 (principale); 38 blocchi contigui da 10 (i matchday dello Z-test); "
        "le etichette delle due metà sulla serie permutata a caso (controllo).",
        rf"Intervallo Monte Carlo al 99\% per $\alpha = 0{{,}}05$: "
        rf"{interval(ref.mc_lower_99, ref.mc_upper_99, 4).latex}.",
    )
    return ThesisTable(
        name="tab_falso_rigetto",
        caption=r"Tasso di falso rigetto dell'ANOVA con soglia nominale, per autocorrelazione $\varphi$ e disegno dei gruppi",
        columns=(
            Column(r"$\varphi$", ("phi",), "l"),
            Column("Due metà contigue", ("due metà contigue",)),
            Column("38 blocchi contigui", ("38 blocchi contigui",)),
            Column("Due gruppi casuali", ("due gruppi casuali",)),
        ),
        rows=tuple(rows),
        sources=(src,),
        notes=notes,
    )


def table_data_window(root: Path | str = REPO_ROOT) -> ThesisTable:
    """Copertura per stagione dei risultati e delle terne 1X2 dei bookmaker."""
    src = versioned_csv("us_c3_1_data_coverage", root)
    cov = read_versioned_csv(src.name, root)
    groups = (("results", "Ris.", "risultati"),) + tuple(
        (f"{s}_1x2_prematch", s.upper(), s.upper()) for s in PREMATCH_SOURCES
    ) + (("ps_1x2_closing", "PS ch.", "PS chiusura"),)
    rows = []
    for season in _ordered(cov.season):
        cells = [text(season)]
        for group, _, _ in groups:
            hit = select(cov, f'season == {_q(season)} and group_name == "{group}"')
            if len(hit) == 0:
                cells.append(text("", ""))
            elif len(hit) == 1 and bool(hit.iloc[0].is_complete):
                cells.append(text(r"$\bullet$", "completa"))
            elif len(hit) == 1:
                cells.append(text(r"$\circ$", "parziale"))
            else:
                raise ValueError(f"Duplicate coverage rows for {season} {group}")
        rows.append(tuple(cells))
    notes = (
        r"$\bullet$: dato completo su tutte le partite della stagione (per le quote, terna non nulla e "
        r"maggiore di 1 su ogni riga); $\circ$: colonne presenti, dato incompleto; vuoto: colonne assenti.",
        "Sigle delle colonne di football-data.co.uk; quote 1X2 pre-partita, tranne PS ch. (Pinnacle, chiusura).",
        "Il 2023-24 non compare: la regola del manifesto (drop\\_seasons) toglie le sue righe.",
    )
    return ThesisTable(
        name="tab_finestra_dati",
        caption="Finestra effettiva dei dati: risultati e terne 1X2 complete per stagione (divisione E0)",
        columns=(Column("Stagione", ("stagione",), "l"),) + tuple(
            Column(head, (plain,), "c") for _, head, plain in groups
        ),
        rows=tuple(rows),
        sources=(src,),
        notes=notes,
        font_size=r"\footnotesize",
        tabcolsep="2.5pt",
    )


def _odds_bin(label: str) -> str:
    """Fascia di quota in LaTeX con la virgola decimale, per esempio "[1; 1,5)"."""
    return label.replace(", ", "; ").replace(".", ",").replace("inf", r"$\infty$")


def table_devig_divergence(root: Path | str = REPO_ROOT) -> ThesisTable:
    """Divergenza fra i tre metodi di de-vigging per fascia di quota."""
    src = versioned_csv("us_c3_2_devig_divergence", root)
    df = read_versioned_csv(src.name, root)
    rows = []
    for _, r in select(df, 'level == "bin"').iterrows():
        rows.append((text(_odds_bin(r.category), r.category), integer(r.n_outcomes),
                     num(r.mean_spread_pts, 2), num(r.p99_spread_pts, 2), num(r.max_spread_pts, 2),
                     num(r.mean_relative_spread, 3)))
    tot = one(df, 'level == "overall"')
    rows.append((text("tutte", "tutte"), integer(tot.n_outcomes), num(tot.mean_spread_pts, 2),
                 num(tot.p99_spread_pts, 2), num(tot.max_spread_pts, 2), num(tot.mean_relative_spread, 3)))
    notes = (
        "Metodi proporzionale, additivo e power sulla terna B365 pre-partita, stagioni non di test. "
        "Spread di un esito: massimo meno minimo dei tre $q$, in punti percentuali; spread relativo: "
        "spread diviso per la media dei tre $q$. Fasce sulla quota dell'esito, chiuse a sinistra.",
        rf"Partite usate {format_number(tot.matches_used, 0)}, escluse {format_number(tot.matches_excluded, 0)} "
        rf"(la stagione 2000-01, senza B365); overround medio {format_number(tot.mean_overround, 4)}.",
        "Rapporto con l'edge di riferimento di 2 punti: spread massimo "
        rf"{format_number(tot.max_spread_ratio_to_edge, 2)}, 99° percentile {format_number(tot.p99_spread_ratio_to_edge, 2)}.",
    )
    return ThesisTable(
        name="tab_divergenza_devig",
        caption="Divergenza fra metodi di de-vigging per fascia di quota (prima riga della sensibilità)",
        columns=(
            Column("Fascia di quota", ("fascia di quota",), "l"),
            Column("Esiti", ("esiti",)),
            Column("Spread medio", ("spread medio (punti)",)),
            Column("99° percentile", ("99° percentile (punti)",)),
            Column("Massimo", ("massimo (punti)",)),
            Column("Spread relativo medio", ("spread relativo medio",)),
        ),
        rows=tuple(rows),
        sources=(src,),
        notes=notes,
    )


def table_g_hat(root: Path | str = REPO_ROOT) -> ThesisTable:
    """Ĝ pooled per serie e metodo, con gli intervalli block e iid."""
    src = versioned_csv("us_c4_2b_g_hat_inference", root)
    df = select(read_versioned_csv(src.name, root), 'row_type == "interval" and season == "pooled"')
    rows = []
    for _, r in df.iterrows():
        rows.append((_label(SERIES, r.series), _label(METHODS, r.method), integer(r.n), num(r.g_hat, 4),
                     interval(r.ci_block_low, r.ci_block_high, 4), interval(r.ci_iid_low, r.ci_iid_high, 4),
                     num(r.width_ratio_block_iid, 2)))
    notes = (
        r"$\hat g$: media su tutte le partite di $\ln \hat p_t(x_t) - \ln q_t(x_t)$, con $x_t$ esito realizzato, "
        "sulle 19 stagioni di validazione (B365) e sulle 10 dal 2012-13 (Pinnacle).",
        r"Intervallo al 95\%: bootstrap a due livelli (stagioni come cluster, stationary bootstrap dentro la "
        r"stagione con lunghezza media $L_{\mathrm{PW}}$), $\hat g \pm t_{0{,}975,\,S-1}\sqrt{S/(S-1)}\,\mathrm{se}_{\mathrm{boot}}$; "
        "iid: lo stesso con blocchi di lunghezza 1. Rapporto: ampiezza block su ampiezza iid.",
    )
    return ThesisTable(
        name="tab_g_hat",
        caption=r"$\hat g$ del Modulo 1 (Elo) contro il mercato, pooled sulle stagioni di validazione",
        columns=(
            Column("Serie", ("serie",), "l", group=True),
            Column("Metodo", ("metodo",), "l"),
            Column("Partite", ("partite",)),
            Column(r"$\hat g$", ("g_hat",)),
            Column(r"IC 95\%", ("IC 95% inf.", "IC 95% sup."), "c"),
            Column(r"IC 95\% iid", ("IC 95% iid inf.", "IC 95% iid sup."), "c"),
            Column("Rapporto", ("rapporto ampiezze block/iid",)),
        ),
        rows=tuple(rows),
        sources=(src,),
        notes=notes,
    )


def table_alarms(root: Path | str = REPO_ROOT) -> ThesisTable:
    """Allarmi di Z-test, ADWIN e Page-Hinkley sulle 19 stagioni di validazione."""
    src = versioned_csv("us_c5_2_daily_z_test", root)
    df = select(read_versioned_csv(src.name, root), 'row_type == "overall"')
    names = {"z_nominal": ("Z nominale", "Z nominale"), "adwin": ("ADWIN", "ADWIN"),
             "page_hinkley": ("Page-Hinkley", "Page-Hinkley")}
    rows = []
    for _, r in df.iterrows():
        if r.method == "z_block_bootstrap":
            name = (rf"Z calibrato, $L = {format_number(r.block_length, 0)}$", f"Z calibrato, L = {int(r.block_length)}")
        else:
            name = names[r.method]
        rows.append((text(*name), integer(r.n_alarms), num(r.mean_alarms, 2), num(r.expected_alarms, 1)))
    notes = (
        r"Serie: log-loss per partita del Modulo 1 (Elo). Z-test per matchday (blocchi di 10 partite) con "
        r"$\mu_f$ e $\sigma_f$ del training del fit; soglia nominale $|Z| > 1{,}96$; soglia calibrata col moving "
        r"block bootstrap della serie di training del fit ($B = 999$).",
        "ADWIN (delta 0,002) e Page-Hinkley (delta 0,05, threshold 5) di river, tarati sul training, "
        "alimentati con la stessa serie. Attesi: 1,9 allarmi per stagione ($\\alpha = 0{,}05$ su 38 matchday).",
    )
    return ThesisTable(
        name="tab_allarmi",
        caption="Allarmi sulle 19 stagioni di validazione: Z-test per matchday, ADWIN e Page-Hinkley",
        columns=(
            Column("Metodo", ("metodo",), "l"),
            Column("Allarmi", ("allarmi (19 stagioni)",)),
            Column("Media per stagione", ("media per stagione",)),
            Column("Attesi per stagione", ("attesi per stagione",)),
        ),
        rows=tuple(rows),
        sources=(src,),
        notes=notes,
    )


def table_floor_real(root: Path | str = REPO_ROOT) -> ThesisTable:
    """Rovina e ricchezza col floor nella configurazione reale (19 stagioni di validazione)."""
    src = versioned_csv("us_c6_3_floor_real_config", root)
    df = select(read_versioned_csv(src.name, root), 'row_type == "aggregate"')
    rows = []
    for config in CONFIG_ORDER:
        for _, r in select(df, f'config == "{config}"').iterrows():
            rows.append((_config(config), _label(AGENTS, r.agent), num(r.ruin_rate, 4),
                         interval(r.ruin_rate_ci_lower, r.ruin_rate_ci_upper, 4), num(r.median_final_wealth, 3),
                         num(r.prob_min_wealth_le_0_5, 3), num(r.floored_bets_share, 3)))
    first = df.iloc[0]
    notes = (
        rf"19 stagioni di validazione; {format_number(first.m_replicas, 0)} traiettorie per riga, con gli esiti "
        "estratti dalle $q$ proporzionali di B365; bankroll 1 a inizio stagione; puntata minima $F$ in unità del "
        r"bankroll iniziale $B_0 = \pounds{}220$.",
        r"IC al 99\% del tasso di rovina. $P(\min W \le 0{,}5)$: quota di traiettorie con ricchezza minima al più 0,5.",
    )
    return ThesisTable(
        name="tab_floor_reale",
        caption="Effetto del floor sulla rovina nella configurazione reale",
        columns=(
            Column("Configurazione", ("configurazione",), "l", group=True),
            Column("Agente", ("agente",), "l"),
            Column("Rovina", ("tasso di rovina",)),
            Column(r"IC 99\%", ("IC 99% inf.", "IC 99% sup."), "c"),
            Column("Ricchezza finale mediana", ("ricchezza finale mediana",)),
            Column(r"$P(\min W \le 0{,}5)$", ("P(min W <= 0.5)",)),
            Column("Puntate col floor", ("quota di puntate col floor",)),
        ),
        rows=tuple(rows),
        sources=(src,),
        notes=notes,
    )


def _ratio_cell(value: float) -> Cell:
    decimals = 0 if float(value).is_integer() else 1
    return num(value, decimals)


def table_floor_synthetic(root: Path | str = REPO_ROOT) -> ThesisTable:
    """Rovina col floor sul calendario sintetico, per B0/F e orizzonte (esperimento B)."""
    src = versioned_csv("us_c6_3_floor_synthetic", root)
    df = read_versioned_csv(src.name, root)
    sweep = select(df, 'experiment == "B"').sort_values("initial_ratio", kind="stable")
    horizons = _ordered(sweep.horizon)
    rows = []
    for ratio in _ordered(sweep.initial_ratio):
        cells = [_ratio_cell(ratio)]
        for h in horizons:
            cells.append(num(one(sweep, f"initial_ratio == {_q(ratio)} and horizon == {_q(h)}").ruin_rate, 4))
        rows.append(tuple(cells))
    b = sweep.iloc[0]
    ca = one(df, 'experiment == "C" and config_id == "C_a"')
    notes = (
        rf"Calendario a una partita per data; quota {format_number(b.odds, 1)}, EV vero {format_number(b.ev_true, 2)}, "
        rf"edge stimato {format_number(b.edge_est, 2)}, $\lambda$ = {format_number(b.lam, 2)}; "
        rf"{format_number(b.m_replicas, 0)} repliche; floor attivo.",
        rf"Esperimento C, configurazione (a), $B_0/F = {format_number(ca.initial_ratio, 0)}$: tempo di rovina medio "
        rf"{format_number(ca.mean_ruin_time, 1)} date, mediano {format_number(ca.median_ruin_time, 1)}; "
        rf"fattore di accelerazione {format_number(ca.acceleration_factor, 1)} "
        rf"(nota 2.9: {format_number(ca.note_acceleration_factor, 0)}).",
    )
    return ThesisTable(
        name="tab_floor_sintetico",
        caption=r"Tasso di rovina col floor sul calendario sintetico, per $B_0/F$ e orizzonte",
        columns=(Column(r"$B_0/F$", ("B0/F",)),) + tuple(
            Column(f"{format_number(h, 0)} date", (f"rovina, {int(h)} date",)) for h in horizons
        ),
        rows=tuple(rows),
        sources=(src,),
        notes=notes,
    )


def table_heteroskedasticity(root: Path | str = REPO_ROOT) -> ThesisTable:
    """Rigetti dei test di eteroschedasticità e di cambio di varianza."""
    src_a = versioned_csv("us_c6_4_heteroskedasticity", root)
    src_b = versioned_csv("us_c6_4b_variance_change", root)
    a = select(read_versioned_csv(src_a.name, root), 'row_type == "summary"')
    b = read_versioned_csv(src_b.name, root)
    bs = select(b, 'row_type == "summary"')
    missing = text("---", "")
    rows = []
    names_a = {"bp_joint": "BP congiunto", "bp_time": "BP temporale", "white": "White"}
    for stat, name in names_a.items():
        cells = [text(name)]
        for method in ("nominal", "bootstrap_L7", "bootstrap_L20", "bootstrap_L40"):
            cells.append(integer(one(a, f'statistic == "{stat}" and method == "{method}"').n_validation_rejections))
        rows.append(tuple(cells) + (missing,))
    names_b = {"goldfeld_quandt": "Goldfeld-Quandt", "arch_lm": "ARCH-LM",
               "rolling_log_variance": "Log-varianza mobile"}
    for stat, name in names_b.items():
        cells = [text(name)]
        for method in ("nominal", "mbb_L7", "mbb_L20", "mbb_L40", "mbb_LPW"):
            hit = select(bs, f'statistic == "{stat}" and method == "{method}"')
            cells.append(missing if len(hit) == 0 else integer(one(bs, f'statistic == "{stat}" and method == "{method}"').rejections))
        rows.append(tuple(cells))
    bf = select(b, 'row_type == "between_seasons" and statistic == "brown_forsythe"')
    bf_nom = one(bf, 'method == "nominal"')
    thresholds = "; ".join(
        f"{lab} {format_number(one(bf, f'method == {_q(m)}').threshold, 3)}"
        for m, lab in (("nominal", "nominale"), ("mbb_L7", "$L = 7$"), ("mbb_L20", "$L = 20$"),
                       ("mbb_L40", "$L = 40$"), ("mbb_LPW", r"$L_{\mathrm{PW}}$"))
    )
    notes = (
        r"Serie: log-loss per partita del Modulo 1 (Elo). BP: Breusch-Pagan (Koenker) sui residui OLS di "
        r"$y \sim 1 + H + t$, congiunto con $z = (H, t)$ e temporale con $z = t$; White con i termini quadratici. "
        "Soglie calibrate col moving block bootstrap della serie di training del fit ($B = 999$).",
        "Goldfeld-Quandt, ARCH-LM e log-varianza mobile: con la stessa calibrazione e "
        r"$L_{\mathrm{PW}}$ di Politis-White; ``---'': non applicabile o non calcolato.",
        rf"Brown-Forsythe fra stagioni ({format_number(bf_nom.n_obs, 0)} partite): statistica "
        rf"{format_number(bf_nom.statistic_value, 3)}; soglie {thresholds}.",
    )
    return ThesisTable(
        name="tab_eteroschedasticita",
        caption="Eteroschedasticità e cambio di varianza della log-loss: rigetti sulle 19 stagioni di validazione",
        columns=(
            Column("Statistica", ("statistica",), "l"),
            Column("Nominale", ("nominale",)),
            Column(r"$L = 7$", ("L = 7",)),
            Column(r"$L = 20$", ("L = 20",)),
            Column(r"$L = 40$", ("L = 40",)),
            Column(r"$L_{\mathrm{PW}}$", ("L_PW",)),
        ),
        rows=tuple(rows),
        sources=(src_a, src_b),
        notes=notes,
        header_groups=(("", 1), ("Rigetti su 19 stagioni", 5)),
    )


_COMPONENTS: Final[dict[str, tuple[str, str]]] = {
    "total": ("totale", "totale"),
    "compositional": ("compositiva", "compositiva"),
    "structural": ("strutturale", "strutturale"),
    "interaction": ("interazione", "interazione"),
    "compositional_share": ("quota compositiva", "quota compositiva"),
    "structural_share": (r"quota strutturale $\pi$", "quota strutturale pi"),
}


def table_module2_covid(root: Path | str = REPO_ROOT) -> ThesisTable:
    """Decomposizione three-fold nello scenario della sospensione del 2019-20."""
    src = versioned_csv("us_c7_3b_known_scenarios", root)
    df = select(read_versioned_csv(src.name, root), 'scenario == "2_covid" and version == "threefold"')
    rows = []
    for quantity, name in _COMPONENTS.items():
        r = one(df, f'quantity == "{quantity}"')
        rows.append((text(*name), num(r.estimate, 4), interval(r.lower, r.upper, 4)))
    r = df.iloc[0]
    notes = (
        rf"Sospensione del 2019-20: A = {format_number(r.n_a, 0)} partite del 2019-20 fino al {r.date_a_last}; "
        rf"B = {format_number(r.n_b, 0)} partite dal {r.date_b_first} (resto del 2019-20 e 2020-21).",
        r"Oaxaca-Blinder three-fold di $\delta = \ln \hat p - \ln q$ (q Shin): totale = compositiva + strutturale + "
        r"interazione; $\pi = |S| / (|C| + |S| + |I|)$, quota compositiva $|C| / (|C| + |S| + |I|)$.",
        rf"IC al 95\%: stationary bootstrap dentro ciascun gruppo, {format_number(r.n_boot, 0)} ricampionamenti, percentili.",
    )
    return ThesisTable(
        name="tab_modulo2_covid",
        caption="Modulo 2: decomposizione di $\\delta$ attorno alla sospensione del 2019-20",
        columns=(
            Column("Quantità", ("quantità",), "l"),
            Column("Stima", ("stima",)),
            Column(r"IC 95\%", ("IC 95% inf.", "IC 95% sup."), "c"),
        ),
        rows=tuple(rows),
        sources=(src,),
        notes=notes,
    )


def table_module2_transitions(root: Path | str = REPO_ROOT) -> ThesisTable:
    """Decomposizione three-fold alle transizioni fra stagioni consecutive (W = 80)."""
    src = versioned_csv("us_c7_3b_known_scenarios", root)
    df = select(read_versioned_csv(src.name, root),
                'scenario == "1_transition" and version == "threefold" and window == 80')
    rows = []
    for _, key in df[["season_a", "season_b"]].drop_duplicates().iterrows():
        pair = select(df, f"season_a == {_q(key.season_a)} and season_b == {_q(key.season_b)}")
        cells = [text(key.season_a), text(key.season_b)]
        for quantity in _COMPONENTS:
            cells.append(num(one(pair, f'quantity == "{quantity}"').estimate, 4 if "share" not in quantity else 3))
        rows.append(tuple(cells))
    notes = (
        "Transizioni fra stagioni consecutive, $W = 80$: A = ultime 80 partite della stagione A, B = prime 80 della stagione B. "
        r"Oaxaca-Blinder three-fold di $\delta = \ln \hat p - \ln q$; quote come nella tabella della sospensione del 2019-20.",
    )
    return ThesisTable(
        name="tab_modulo2_transizioni",
        caption="Modulo 2: decomposizione di $\\delta$ alle transizioni fra stagioni ($W = 80$)",
        columns=(
            Column("Stagione A", ("stagione A",), "l"),
            Column("Stagione B", ("stagione B",), "l"),
        ) + tuple(Column(name[0].capitalize(), (name[1],)) for name in _COMPONENTS.values()),
        rows=tuple(rows),
        sources=(src,),
        notes=notes,
        tabcolsep="4pt",
    )


def table_comparisons(root: Path | str = REPO_ROOT) -> ThesisTable:
    """Confronti appaiati sulla log-ricchezza finale, in validazione e nel 2023-24."""
    src_v = versioned_csv("us_c8_4_comparisons", root)
    src_t = versioned_csv("us_c8_5_test_run", root)
    val = select(read_versioned_csv(src_v.name, root), 'row_type == "comparison" and metric == "final_log_wealth"')
    test = select(read_versioned_csv(src_t.name, root), 'row_type == "comparison" and metric == "final_log_wealth"')
    rows = []
    for config in CONFIG_ORDER:
        for _, r in select(val, f'config == "{config}"').iterrows():
            t = one(test, f'config == "{config}" and comparison == {_q(r.comparison)}')
            lab = comparison(r.comparison)
            rows.append((_config(config), text(lab.latex, lab.plain), num(r.estimate, 3, signed=True),
                         interval(r.ci_block_low, r.ci_block_high, 3), num(r.width_ratio_block_iid, 2),
                         num(t.estimate, 3, signed=True), interval(t.ci_low, t.ci_high, 3)))
    cov = one(read_versioned_csv(src_v.name, root), 'row_type == "coverage" and source == "seeds_resampled"')
    notes = (
        "Differenza pooled della log-ricchezza finale: media sulle stagioni della media sui seed delle differenze "
        "appaiate. C1 $-$ C0: rilevare; C2 $-$ C1: graduare.",
        r"Validazione: IC al 95\% dal bootstrap a due livelli (stagioni e seed), "
        r"$\hat D \pm t_{0{,}975,\,S-1}\sqrt{S/(S-1)}\,\mathrm{se}_{\mathrm{boot}}$; rapporto: ampiezza block su "
        rf"ampiezza iid. Copertura del metodo sul run prescritto: {format_number(cov.coverage, 3)} col percentile, "
        rf"{format_number(cov.coverage_corrected, 3)} con la correzione.",
        r"Test 2023-24: una stagione, IC al 95\% dai soli seed.",
    )
    return ThesisTable(
        name="tab_confronti",
        caption="Confronti appaiati fra agenti sulla log-ricchezza finale, in validazione e sul test set",
        columns=(
            Column("Configurazione", ("configurazione",), "l", group=True),
            Column("Confronto", ("confronto",), "l"),
            Column("Stima", ("validazione stima",)),
            Column(r"IC 95\%", ("validazione IC 95% inf.", "validazione IC 95% sup."), "c"),
            Column("Block/iid", ("validazione rapporto ampiezze block/iid",)),
            Column("Stima", ("test stima",)),
            Column(r"IC 95\%", ("test IC 95% inf.", "test IC 95% sup."), "c"),
        ),
        rows=tuple(rows),
        sources=(src_v, src_t),
        notes=notes,
        header_groups=(("", 2), ("Validazione (19 stagioni)", 3), ("Test 2023-24", 2)),
        tabcolsep="4pt",
    )


def table_dixon_coles(root: Path | str = REPO_ROOT) -> ThesisTable:
    """Log-loss e ĝ di Elo e Dixon-Coles, in validazione e nel 2023-24."""
    src_v = versioned_csv("us_c9_1_dixon_coles", root)
    src_te = versioned_csv("us_c8_5_test_run", root)
    src_td = versioned_csv("us_c8_5_test_run_dc", root)
    val = select(read_versioned_csv(src_v.name, root), 'row_type == "validation" and season == "pooled"')
    early = select(read_versioned_csv(src_v.name, root), 'row_type == "new_teams_early"')
    methods = tuple(METHODS)
    rows = []
    for model in ("elo", "dixon_coles"):
        cells = [text("validazione"), _label(MODELS, model),
                 num(one(val, f'model == "{model}" and method.isna()').log_loss, 4)]
        for m in methods:
            cells.append(num(one(val, f'model == "{model}" and method == "{m}"').g_hat, 4))
        cells.append(num(one(early, f'model == "{model}"').log_loss, 4))
        rows.append(tuple(cells))
    for model, src in (("elo", src_te), ("dixon_coles", src_td)):
        df = read_versioned_csv(src.name, root)
        cells = [text("test 2023-24"), _label(MODELS, model),
                 num(one(df, 'row_type == "log_loss" and series == "b365_prematch"').estimate, 4)]
        for m in methods:
            cells.append(num(one(df, f'row_type == "g_hat" and series == "b365_prematch" and method == "{m}"').estimate, 4))
        cells.append(text("---", ""))
        rows.append(tuple(cells))
    fits = select(read_versioned_csv(src_v.name, root), 'row_type == "validation_fits"')
    fit_text = "; ".join(
        rf"{r.fit}: $\xi$ = {format_number(r.xi, 4)}, $\sigma$ = {format_number(r.sigma, 1)}" for _, r in fits.iterrows()
    )
    n_early = one(early, 'model == "elo"').n
    n_val = one(val, 'model == "elo" and method.isna()').n
    n_test = one(read_versioned_csv(src_te.name, root), 'row_type == "log_loss" and series == "b365_prematch"').n
    notes = (
        r"$\hat g$ sulla terna B365 pre-partita, per metodo di de-vigging. Validazione: 19 stagioni, "
        rf"{format_number(n_val, 0)} partite; test: {format_number(n_test, 0)} partite.",
        rf"Neopromosse: log-loss delle partite di squadre mai viste nei primi 10 matchday ({format_number(n_early, 0)} partite).",
        rf"Dixon-Coles con i parametri calibrati per fit: {fit_text}.",
    )
    return ThesisTable(
        name="tab_dixon_coles",
        caption=r"Modulo 1 Elo e Dixon-Coles: log-loss e $\hat g$ per metodo di de-vigging",
        columns=(
            Column("Insieme", ("insieme",), "l", group=True),
            Column("Modello", ("modello",), "l"),
            Column("Log-loss", ("log-loss",)),
        ) + tuple(Column(METHODS[m].latex, (f"g_hat {METHODS[m].plain}",)) for m in methods)
        + (Column("Neopromosse", ("log-loss neopromosse mai viste, primi 10 matchday",)),),
        rows=tuple(rows),
        sources=(src_v, src_te, src_td),
        notes=notes,
        header_groups=(("", 3), (r"$\hat g$", len(methods)), ("", 1)),
        tabcolsep="4pt",
    )


def table_ranking(root: Path | str = REPO_ROOT) -> ThesisTable:
    """Τ-b di Kendall fra i ranking degli agenti con Elo e con Dixon-Coles."""
    src = versioned_csv("us_c9_2_robustness", root)
    tau = select(read_versioned_csv(src.name, root), 'row_type == "tau"')
    configs = ("none", "gbp_0.01", "gbp_1")
    rows = []
    for metric in _ordered(tau.metric):
        cells = [_label(METRICS, metric)]
        for dataset in ("validation", "test"):
            for config in configs:
                cells.append(num(one(tau, f'dataset == "{dataset}" and config == "{config}" and metric == "{metric}"').tau, 3))
        rows.append(tuple(cells))
    ref = one(tau, 'dataset == "validation" and config == "gbp_0.01" and metric == "final_log_wealth"')
    notes = (
        r"$\tau_b$ di Kendall, con i pari, fra il ranking degli agenti col Modulo 1 Elo e quello con Dixon-Coles "
        "(9 agenti senza floor, 10 col floor); statistica per agente: mediana sui seed per stagione, poi media "
        "sulle stagioni (metriche per seed), o media sulle stagioni (metriche per stagione).",
        r"Esempio di intervallo, validazione, \pounds{}0,01, log-ricchezza finale: "
        rf"{interval(ref.ci_low, ref.ci_high, 3).latex} (correzione $t$ per cluster). ``---'': $\tau$ non definito "
        "(tutti gli agenti pari).",
    )
    return ThesisTable(
        name="tab_ranking",
        caption=r"Robustezza del ranking degli agenti al Modulo 1: $\tau_b$ di Kendall fra Elo e Dixon-Coles",
        columns=(Column("Metrica", ("metrica",), "l"),) + tuple(
            Column(CONFIGS[c].latex.replace(r"senza floor ($F = 0$)", r"$F = 0$"), (f"{d} {CONFIGS[c].plain}",))
            for d in ("validazione", "test") for c in configs
        ),
        rows=tuple(rows),
        sources=(src,),
        notes=notes,
        header_groups=(("", 1), ("Validazione", 3), ("Test 2023-24", 3)),
    )


def table_comparisons_dc(root: Path | str = REPO_ROOT) -> ThesisTable:
    """Confronti fra agenti con Elo e con Dixon-Coles, configurazione £0.01."""
    src = versioned_csv("us_c9_2_robustness", root)
    df = select(read_versioned_csv(src.name, root),
                'row_type == "comparison" and metric == "final_log_wealth" and config == "gbp_0.01"')
    rows = []
    for dataset, name in (("validation", "validazione"), ("test", "test 2023-24")):
        for _, r in select(df, f'dataset == "{dataset}"').iterrows():
            lab = comparison(r.comparison)
            rows.append((text(name), text(lab.latex, lab.plain), num(r.estimate_elo, 3, signed=True),
                         interval(r.ci_low_elo, r.ci_high_elo, 3), num(r.estimate_dc, 3, signed=True),
                         interval(r.ci_low_dc, r.ci_high_dc, 3),
                         text("sì" if bool(r.same_conclusion) else "no", str(bool(r.same_conclusion)))))
    notes = (
        r"Configurazione principale \pounds{}0,01 ($B_0/F = 22\,000$), log-ricchezza finale. Validazione: IC al "
        r"95\% con la correzione $t$ per cluster; test 2023-24: IC dai soli seed.",
        "Stessa conclusione: l'intervallo esclude 0 con lo stesso segno, o non lo esclude, con i due modelli.",
    )
    return ThesisTable(
        name="tab_confronti_dc",
        caption="Confronti appaiati con il Modulo 1 Elo e con Dixon-Coles",
        columns=(
            Column("Insieme", ("insieme",), "l", group=True),
            Column("Confronto", ("confronto",), "l"),
            Column("Stima", ("Elo stima",)),
            Column(r"IC 95\%", ("Elo IC 95% inf.", "Elo IC 95% sup."), "c"),
            Column("Stima", ("Dixon-Coles stima",)),
            Column(r"IC 95\%", ("Dixon-Coles IC 95% inf.", "Dixon-Coles IC 95% sup."), "c"),
            Column("Stessa concl.", ("stessa conclusione",), "c"),
        ),
        rows=tuple(rows),
        sources=(src,),
        notes=notes,
        header_groups=(("", 2), ("Elo", 2), ("Dixon-Coles", 2), ("", 1)),
        tabcolsep="4pt",
    )


def table_devig(root: Path | str = REPO_ROOT) -> ThesisTable:
    """Ĝ per metodo di de-vigging, in validazione e nel 2023-24, e conclusioni instabili."""
    src = versioned_csv("us_c9_3_devig_sensitivity", root)
    df = read_versioned_csv(src.name, root)
    g = select(df, 'row_type == "g_hat" and (season == "pooled" or season == "2023-24")')
    rows = []
    for dataset, name in (("validation", "validazione"), ("test", "test 2023-24")):
        part = select(g, f'dataset == "{dataset}"')
        for method in _ordered(part.method):
            cells = [text(name), _label(METHODS, method)]
            for series in ("b365_prematch", "pinnacle_closing"):
                r = one(part, f'method == "{method}" and series == "{series}"')
                cells += [num(r.estimate, 4), interval(r.ci_low, r.ci_high, 4)]
            rows.append(tuple(cells))
    unstable = select(df, 'row_type == "conclusion" and stable == False')
    listed = "; ".join(
        rf"{'validazione' if r.dataset == 'validation' else 'test 2023-24'}, {CONFIGS[r.config].latex}, "
        rf"{comparison(r.comparison).latex}, {METRICS[r.metric].latex} "
        rf"(\texttt{{{latex_escape(r.signs_by_method)}}})"
        for _, r in unstable.iterrows()
    )
    notes = (
        r"Validazione: pooled sulle stagioni, IC al 95\% con la correzione $t$ per cluster; test 2023-24: "
        "stationary bootstrap della stagione. Shin è il metodo principale.",
        f"Conclusioni dei confronti che cambiano segno fra i metodi: {listed}.",
    )
    return ThesisTable(
        name="tab_devig",
        caption=r"Sensibilità di $\hat g$ al metodo di de-vigging",
        columns=(
            Column("Insieme", ("insieme",), "l", group=True),
            Column("Metodo", ("metodo",), "l"),
            Column(r"$\hat g$", ("B365 g_hat",)),
            Column(r"IC 95\%", ("B365 IC 95% inf.", "B365 IC 95% sup."), "c"),
            Column(r"$\hat g$", ("Pinnacle g_hat",)),
            Column(r"IC 95\%", ("Pinnacle IC 95% inf.", "Pinnacle IC 95% sup."), "c"),
        ),
        rows=tuple(rows),
        sources=(src,),
        notes=notes,
        header_groups=(("", 2), ("B365 pre-partita", 2), ("Pinnacle chiusura", 2)),
    )


TABLES: Final[dict[str, Callable[..., ThesisTable]]] = {
    "tab_falso_rigetto": table_false_rejection,
    "tab_finestra_dati": table_data_window,
    "tab_divergenza_devig": table_devig_divergence,
    "tab_g_hat": table_g_hat,
    "tab_allarmi": table_alarms,
    "tab_floor_reale": table_floor_real,
    "tab_floor_sintetico": table_floor_synthetic,
    "tab_eteroschedasticita": table_heteroskedasticity,
    "tab_modulo2_covid": table_module2_covid,
    "tab_modulo2_transizioni": table_module2_transitions,
    "tab_confronti": table_comparisons,
    "tab_dixon_coles": table_dixon_coles,
    "tab_ranking": table_ranking,
    "tab_confronti_dc": table_comparisons_dc,
    "tab_devig": table_devig,
}


def build_table(name: str, root: Path | str = REPO_ROOT) -> ThesisTable:
    """Tabella del registro.

    Solleva
    -------
    ValueError
        Se il nome non è nel registro.
    """
    if name not in TABLES:
        raise ValueError(f"Unknown table {name!r}, expected one of {sorted(TABLES)}")
    table = TABLES[name](root)
    if table.name != name:
        raise ValueError(f"Table builder for {name!r} returned {table.name!r}")
    return table
