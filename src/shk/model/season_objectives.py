"""Flag "squadra senza obiettivi" dalla classifica con i soli risultati anteriori (T48).

Per una partita alla data D della stagione s, la classifica si calcola con i soli risultati
della stagione con Date strettamente anteriore a D (3 punti la vittoria, 1 il pareggio).
Con n squadre nella stagione, ogni squadra gioca 2(n − 1) partite; quelle rimaste sono
2(n − 1) meno quelle già giocate prima di D, e i punti massimi raggiungibili sono i punti
attuali più 3 per partita rimasta.

Una squadra T è senza obiettivi se entrambe le condizioni valgono:
- matematicamente salva: almeno RELEGATION_PLACES = 3 altre squadre hanno punti massimi
  raggiungibili strettamente minori dei punti attuali di T, quindi T non può finire nelle
  ultime tre;
- senza possibilità di arrivare quarta: almeno TOP_PLACES = 4 altre squadre hanno punti
  attuali strettamente maggiori dei punti massimi raggiungibili da T.
Le disuguaglianze strette rendono la regola prudente rispetto agli spareggi (differenza
reti, gol fatti). "Quarto posto" è una semplificazione degli obiettivi europei (coppe
nazionali, posti UEFA variabili negli anni), dichiarata in tesi.
"""

from typing import Final

import numpy as np
import pandas as pd

RELEGATION_PLACES: Final[int] = 3
TOP_PLACES: Final[int] = 4
POINTS: Final[dict[str, tuple[int, int]]] = {"H": (3, 0), "D": (1, 1), "A": (0, 3)}


def prior_results_mask(dates: np.ndarray, decision_date: np.datetime64) -> np.ndarray:
    """Risultati ammessi per la classifica: Date strettamente anteriore."""
    return dates < decision_date


def no_objective_flags(matches: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Flag "senza obiettivi" della squadra di casa e di trasferta per ogni partita.

    Parametri
    ---------
    matches : pd.DataFrame
        Colonne season, Date, HomeTeam, AwayTeam, FTR (H, D, A); più stagioni ammesse.

    Restituisce
    -----------
    tuple[np.ndarray, np.ndarray]
        (flag_home, flag_away) interi 0/1, allineati alle righe di matches.

    Solleva
    -------
    ValueError
        Se mancano colonne o FTR ha valori diversi da H, D, A.
    """
    for col in ("season", "Date", "HomeTeam", "AwayTeam", "FTR"):
        if col not in matches.columns:
            raise ValueError(f"Column '{col}' not found")
    ftr = matches["FTR"].astype(str).str.strip()
    if not ftr.isin(list(POINTS)).all():
        raise ValueError("FTR must contain only H, D, A")

    flag_home = np.zeros(len(matches), dtype=np.int64)
    flag_away = np.zeros(len(matches), dtype=np.int64)
    positions = np.arange(len(matches))
    for _, season_rows in matches.groupby("season", sort=False):
        idx = positions[matches.index.get_indexer(season_rows.index)]
        teams = sorted(set(season_rows["HomeTeam"]) | set(season_rows["AwayTeam"]))
        team_pos = {t: i for i, t in enumerate(teams)}
        n_teams = len(teams)
        games_per_team = 2 * (n_teams - 1)
        dates = season_rows["Date"].to_numpy(dtype="datetime64[ns]")
        home = season_rows["HomeTeam"].map(team_pos).to_numpy()
        away = season_rows["AwayTeam"].map(team_pos).to_numpy()
        res = ftr.iloc[idx].to_numpy()
        home_pts = np.array([POINTS[r][0] for r in res])
        away_pts = np.array([POINTS[r][1] for r in res])

        for d in np.unique(dates):
            prior = prior_results_mask(dates, d)
            points = np.zeros(n_teams)
            played = np.zeros(n_teams)
            np.add.at(points, home[prior], home_pts[prior])
            np.add.at(points, away[prior], away_pts[prior])
            np.add.at(played, home[prior], 1)
            np.add.at(played, away[prior], 1)
            max_points = points + 3.0 * (games_per_team - played)
            # Per ogni squadra: altre squadre che non possono raggiungerla / che non può raggiungere
            cannot_catch = (max_points[None, :] < points[:, None]).sum(axis=1)
            unreachable_above = (points[None, :] > max_points[:, None]).sum(axis=1)
            no_objective = (cannot_catch >= RELEGATION_PLACES) & (unreachable_above >= TOP_PLACES)
            today = dates == d
            flag_home[idx[today]] = no_objective[home[today]].astype(np.int64)
            flag_away[idx[today]] = no_objective[away[today]].astype(np.int64)
    return flag_home, flag_away
