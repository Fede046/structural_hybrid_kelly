"""Modulo per il caricamento e la validazione delle stagioni storiche di Premier League."""

import csv
import io
from pathlib import Path
import re
from typing import Final
from collections.abc import Collection

import pandas as pd

# Percorso predefinito dei file grezzi, calcolato a partire dalla posizione del modulo
# fino alla radice del repository (quattro livelli sopra il file corrente: parents[3]).
DEFAULT_DATA_DIR: Final[Path] = (
    Path(__file__).resolve().parents[3] / "data" / "raw" / "E0"
)


def load_all_seasons(
    data_dir: Path | str = DEFAULT_DATA_DIR,
    seasons: Collection[str] | None = None,
) -> pd.DataFrame:
    """Carica tutte le stagioni E0 da file CSV in un unico DataFrame consolidato.

    Legge i file CSV presenti nella directory specificata, valida la nomenclatura
    di tutti i file presenti, applica la procedura deterministica di decodifica solo
    ai file delle stagioni richieste (oppure a tutte le stagioni se seasons e' None),
    ripulisce le righe irregolari o vuote, valida i formati di data e la finestra temporale
    stagionale, e restituisce un DataFrame ordinato stabilmente per stagione e data.

    Regola di decodifica (senza blocchi try/except):
    1. Se il contenuto binario inizia con il BOM UTF-8 (b"\\xef\\xbb\\xbf"), viene
       utilizzata la codifica 'utf-8-sig'.
    2. Altrimenti, i byte vengono decodificati provvisoriamente con 'utf-8' ed
       errors='replace'. Viene confrontato il conteggio del carattere '\\ufffd' nel
       testo con le occorrenze della sequenza b"\\xef\\xbf\\xbd" nei byte originali:
       se i conteggi coincidono, il file e' UTF-8 valido e si mantiene tale testo;
       se differiscono (indicando byte non-UTF-8 sostituiti), il file viene
       decodificato con 'cp1252'.

    Parametri
    ----------
    data_dir : Path o str, opzionale
        Percorso della directory contenente i file CSV delle stagioni.
        Il valore predefinito e' DEFAULT_DATA_DIR.
    seasons : Collection[str] o None, opzionale
        Insieme delle stagioni da caricare (es. ['2000-01', '2010-11']). Se None
        (valore predefinito), carica tutte le stagioni trovate nella directory.

    Restituisce
    -----------
    pd.DataFrame
        DataFrame complessivo contenente l'unione di tutte le colonne presenti
        nelle varie stagioni, con colonna 'season' aggiunta, colonna 'Date'
        convertita in datetime64, ordinato stabilmente per ['season', 'Date'].

    Solleva
    -------
    TypeError
        Se data_dir non e' di tipo str o pathlib.Path, oppure se seasons e' una str
        o contiene elementi non str.
    FileNotFoundError
        Se la directory specificata non esiste sul file system.
    ValueError
        Se la directory non contiene file CSV, se uno dei file ha nome non
        conforme a YYYY-YY.csv o anni non consecutivi, se seasons e' vuoto o include
        stagioni prive di file corrispondente, se un file letto e' vuoto,
        se una riga dati ha campi non vuoti in eccesso, se una colonna senza nome
        contiene valori non vuoti, se mancano date o vi sono formati misti/non validi,
        oppure se vi sono date al di fuori della finestra temporale stagionale
        (1° luglio anno iniziale - 31 agosto anno finale).
    """
    if not isinstance(data_dir, (str, Path)):
        raise TypeError(
            f"data_dir must be a str or pathlib.Path, got {type(data_dir).__name__}"
        )

    if seasons is not None:
        if isinstance(seasons, str):
            raise TypeError("seasons cannot be a str, must be a Collection[str] or None")
        if not isinstance(seasons, Collection):
            raise TypeError(
                f"seasons must be a Collection[str] or None, got {type(seasons).__name__}"
            )
        if len(seasons) == 0:
            raise ValueError("seasons collection cannot be empty")
        for s in seasons:
            if not isinstance(s, str):
                raise TypeError(
                    f"All items in seasons must be str, got {type(s).__name__}"
                )

    path = Path(data_dir)
    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {path}")

    csv_files = sorted(path.glob("*.csv"))
    if not csv_files:
        raise ValueError(f"No CSV files found in directory: {path}")

    filename_pattern = re.compile(r"^(\d{4})-(\d{2})\.csv$")
    date_2digit_pattern = re.compile(r"^\d{2}/\d{2}/\d{2}$")
    date_4digit_pattern = re.compile(r"^\d{2}/\d{2}/\d{4}$")

    season_to_file: dict[str, Path] = {}
    for file_path in csv_files:
        match = filename_pattern.match(file_path.name)
        if not match:
            raise ValueError(
                f"Invalid season filename format: {file_path.name}, expected YYYY-YY.csv"
            )
        start_year = int(match.group(1))
        end_year = int(match.group(2))
        if (start_year + 1) % 100 != end_year:
            raise ValueError(
                f"Season year continuity mismatch in filename: {file_path.name}"
            )
        season_name = f"{start_year:04d}-{end_year:02d}"
        season_to_file[season_name] = file_path

    if seasons is not None:
        missing_seasons = [s for s in seasons if s not in season_to_file]
        if missing_seasons:
            raise ValueError(
                f"Seasons without corresponding file in {path}: {missing_seasons}"
            )
        target_files = [season_to_file[s] for s in sorted(set(seasons))]
    else:
        target_files = csv_files

    season_dfs: list[pd.DataFrame] = []

    for file_path in target_files:
        match = filename_pattern.match(file_path.name)
        if not match:
            raise ValueError(
                f"Invalid season filename format: {file_path.name}, expected YYYY-YY.csv"
            )

        start_year = int(match.group(1))
        end_year = int(match.group(2))
        if (start_year + 1) % 100 != end_year:
            raise ValueError(
                f"Season year continuity mismatch in filename: {file_path.name}"
            )

        season_name = f"{start_year:04d}-{end_year:02d}"

        raw_bytes = file_path.read_bytes()
        if raw_bytes.startswith(b"\xef\xbb\xbf"):
            text = raw_bytes.decode("utf-8-sig")
        else:
            text_utf8 = raw_bytes.decode("utf-8", errors="replace")
            if text_utf8.count("\ufffd") == raw_bytes.count(b"\xef\xbf\xbd"):
                text = text_utf8
            else:
                text = raw_bytes.decode("cp1252")

        reader = csv.reader(io.StringIO(text))
        raw_rows = list(reader)

        non_empty_rows = [
            (line_idx, row)
            for line_idx, row in enumerate(raw_rows, start=1)
            if not all(c.strip() == "" for c in row)
        ]
        if not non_empty_rows:
            raise ValueError(f"File {file_path.name} contains no data rows")

        header_line_idx, header = non_empty_rows[0]
        n_cols = len(header)
        data_rows_with_idx = non_empty_rows[1:]
        if not data_rows_with_idx:
            raise ValueError(f"File {file_path.name} contains no match rows")

        cleaned_data_rows: list[list[str]] = []
        for line_idx, row in data_rows_with_idx:
            if len(row) > n_cols:
                extra_fields = row[n_cols:]
                if not all(c.strip() == "" for c in extra_fields):
                    raise ValueError(
                        f"Row {line_idx} in {file_path.name} has non-empty extra fields beyond header count {n_cols}"
                    )
                row = row[:n_cols]
            elif len(row) < n_cols:
                row = row + [""] * (n_cols - len(row))
            cleaned_data_rows.append(row)

        out_buffer = io.StringIO()
        writer = csv.writer(out_buffer)
        writer.writerow(header)
        writer.writerows(cleaned_data_rows)
        out_buffer.seek(0)

        df_season = pd.read_csv(out_buffer, dtype={"Date": str})

        cols_to_drop: list[str] = []
        for i, raw_col_name in enumerate(header):
            actual_col_name = df_season.columns[i]
            is_unnamed = (raw_col_name.strip() == "") or str(actual_col_name).startswith("Unnamed:")
            if is_unnamed:
                series = df_season[actual_col_name]
                has_content = series.notna() & (series.astype(str).str.strip() != "")
                if has_content.any():
                    raise ValueError(
                        f"Unnamed column at index {i} in {file_path.name} contains non-empty values"
                    )
                cols_to_drop.append(actual_col_name)

        if cols_to_drop:
            df_season = df_season.drop(columns=cols_to_drop)

        if "Date" not in df_season.columns:
            raise ValueError(f"Missing 'Date' column in {file_path.name}")

        date_series = df_season["Date"]
        if date_series.isna().any():
            raise ValueError(f"Missing or null Date values in {file_path.name}")

        date_str = date_series.astype(str).str.strip()
        if (date_str == "").any():
            raise ValueError(f"Empty Date values in {file_path.name}")

        is_2digit = date_str.apply(lambda s: bool(date_2digit_pattern.match(s)))
        is_4digit = date_str.apply(lambda s: bool(date_4digit_pattern.match(s)))

        if is_2digit.all():
            date_format = "%d/%m/%y"
        elif is_4digit.all():
            date_format = "%d/%m/%Y"
        else:
            raise ValueError(
                f"Mixed, invalid, or non-conforming date formats in {file_path.name}"
            )

        parsed_dates = pd.to_datetime(date_str, format=date_format, errors="coerce")
        if parsed_dates.isna().any():
            raise ValueError(f"Failed to parse dates in {file_path.name}")

        min_date = pd.Timestamp(year=start_year, month=7, day=1)
        max_date = pd.Timestamp(
            year=start_year + 1, month=8, day=31, hour=23, minute=59, second=59
        )
        out_of_window = (parsed_dates < min_date) | (parsed_dates > max_date)
        if out_of_window.any():
            raise ValueError(
                f"Date outside seasonal window [{min_date.date()}, {max_date.date()}] in {file_path.name}"
            )

        df_season["Date"] = parsed_dates
        df_season["season"] = season_name

        season_dfs.append(df_season)

    combined_df = pd.concat(season_dfs, ignore_index=True)
    combined_df = combined_df.sort_values(["season", "Date"], kind="stable").reset_index(drop=True)
    return combined_df
