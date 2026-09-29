"""Test per il modulo src/shk/data/loading.py."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shk.data.loading import DEFAULT_DATA_DIR, load_all_seasons


def test_load_all_seasons_invalid_type_raises():
    """Verifica che data_dir di tipo non valido sollevi TypeError."""
    with pytest.raises(TypeError, match="data_dir must be a str or pathlib.Path"):
        load_all_seasons(data_dir=123)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="data_dir must be a str or pathlib.Path"):
        load_all_seasons(data_dir=["invalid"])  # type: ignore[arg-type]


def test_load_all_seasons_missing_directory_raises(tmp_path: Path):
    """Verifica che una directory inesistente sollevi FileNotFoundError."""
    missing_dir = tmp_path / "non_existent_dir"
    with pytest.raises(FileNotFoundError, match="Directory not found"):
        load_all_seasons(data_dir=missing_dir)


def test_load_all_seasons_empty_directory_raises(tmp_path: Path):
    """Verifica che una directory priva di CSV sollevi ValueError."""
    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()
    with pytest.raises(ValueError, match="No CSV files found in directory"):
        load_all_seasons(data_dir=empty_dir)


def test_load_all_seasons_invalid_filename_raises(tmp_path: Path):
    """Verifica che nomi di file non conformi sollevino ValueError."""
    csv_dir = tmp_path / "csv_dir"
    csv_dir.mkdir()

    # Formato errato
    (csv_dir / "season_1.csv").write_text("Div,Date,HomeTeam,AwayTeam\nE0,10/08/01,Arsenal,Chelsea\n")
    with pytest.raises(ValueError, match="Invalid season filename format"):
        load_all_seasons(data_dir=csv_dir)

    # Anni non consecutivi (1993-95 invece di 1993-94)
    (csv_dir / "season_1.csv").unlink()
    (csv_dir / "1993-95.csv").write_text("Div,Date,HomeTeam,AwayTeam\nE0,10/08/93,Arsenal,Chelsea\n")
    with pytest.raises(ValueError, match="Season year continuity mismatch in filename"):
        load_all_seasons(data_dir=csv_dir)


def test_load_all_seasons_basic_union_and_types(tmp_path: Path):
    """Verifica l'unione delle colonne, i tipi numerici e i valori mancanti NaN."""
    csv_dir = tmp_path / "seasons"
    csv_dir.mkdir()

    # Stagione 1: ha colonna 'FTHG' (numerica) e 'ColA'
    s1 = (
        "Div,Date,HomeTeam,AwayTeam,FTHG,ColA\n"
        "E0,14/08/00,Arsenal,Chelsea,2,alpha\n"
        "E0,15/08/00,Liverpool,Everton,1,beta\n"
    )
    (csv_dir / "2000-01.csv").write_text(s1, encoding="utf-8")

    # Stagione 2: ha colonna 'FTHG' (numerica) e 'ColB' (float), manca 'ColA'
    s2 = (
        "Div,Date,HomeTeam,AwayTeam,FTHG,ColB\n"
        "E0,18/08/01,Chelsea,Arsenal,0,3.75\n"
    )
    (csv_dir / "2001-02.csv").write_text(s2, encoding="utf-8")

    df = load_all_seasons(data_dir=csv_dir)

    assert len(df) == 3
    assert set(df["season"]) == {"2000-01", "2001-02"}

    # Verifica unione delle colonne
    expected_cols = {"Div", "Date", "HomeTeam", "AwayTeam", "FTHG", "ColA", "ColB", "season"}
    assert expected_cols.issubset(set(df.columns))

    # Verifica tipo numerico per FTHG e ColB
    assert pd.api.types.is_numeric_dtype(df["FTHG"])
    assert pd.api.types.is_float_dtype(df["ColB"])

    # Verifica che i valori mancanti siano NaN
    s1_rows = df[df["season"] == "2000-01"]
    assert s1_rows["ColB"].isna().all()

    s2_rows = df[df["season"] == "2001-02"]
    assert s2_rows["ColA"].isna().all()


def test_load_all_seasons_date_formats(tmp_path: Path):
    """Verifica il corretto parsing per date gg/mm/aa e gg/mm/aaaa."""
    csv_dir = tmp_path / "dates"
    csv_dir.mkdir()

    # Anno a 2 cifre
    s1 = "Div,Date,HomeTeam,AwayTeam\nE0,14/08/01,Arsenal,Chelsea\n"
    (csv_dir / "2001-02.csv").write_text(s1, encoding="utf-8")

    # Anno a 4 cifre
    s2 = "Div,Date,HomeTeam,AwayTeam\nE0,17/08/2002,Liverpool,Everton\n"
    (csv_dir / "2002-03.csv").write_text(s2, encoding="utf-8")

    df = load_all_seasons(data_dir=csv_dir)

    assert pd.api.types.is_datetime64_any_dtype(df["Date"])
    assert df.loc[df["season"] == "2001-02", "Date"].iloc[0] == pd.Timestamp("2001-08-14")
    assert df.loc[df["season"] == "2002-03", "Date"].iloc[0] == pd.Timestamp("2002-08-17")


def test_load_all_seasons_discards_empty_and_comma_rows(tmp_path: Path):
    """Verifica che righe vuote o di sole virgole siano scartate ovunque si trovino."""
    csv_dir = tmp_path / "empty_rows"
    csv_dir.mkdir()

    content = (
        "Div,Date,HomeTeam,AwayTeam\n"
        "E0,14/08/01,Arsenal,Chelsea\n"
        ",,,\n"
        "   ,   ,   ,   \n"
        "E0,15/08/01,Liverpool,Everton\n"
        "\n"
        ",,,\n"
    )
    (csv_dir / "2001-02.csv").write_text(content, encoding="utf-8")

    df = load_all_seasons(data_dir=csv_dir)
    assert len(df) == 2
    assert list(df["HomeTeam"]) == ["Arsenal", "Liverpool"]


def test_load_all_seasons_irregular_row_fields_trimmed_and_padded(tmp_path: Path):
    """Verifica il troncamento dei campi extra vuoti e il padding dei campi mancanti."""
    csv_dir = tmp_path / "irregular_fields"
    csv_dir.mkdir()

    # Riga 2 ha campi extra vuoti (6 campi su 4)
    # Riga 3 ha campi mancanti (3 campi su 4)
    content = (
        "Div,Date,HomeTeam,AwayTeam\n"
        "E0,14/08/01,Arsenal,Chelsea,,\n"
        "E0,15/08/01,Liverpool\n"
    )
    (csv_dir / "2001-02.csv").write_text(content, encoding="utf-8")

    df = load_all_seasons(data_dir=csv_dir)
    assert len(df) == 2
    assert df.loc[0, "AwayTeam"] == "Chelsea"
    assert pd.isna(df.loc[1, "AwayTeam"]) or df.loc[1, "AwayTeam"] == ""


def test_load_all_seasons_extra_non_empty_field_raises(tmp_path: Path):
    """Verifica che campi in eccesso non vuoti sollevino ValueError con riga e file."""
    csv_dir = tmp_path / "extra_non_empty"
    csv_dir.mkdir()

    content = (
        "Div,Date,HomeTeam,AwayTeam\n"
        "E0,14/08/01,Arsenal,Chelsea,UNEXPECTED\n"
    )
    (csv_dir / "2001-02.csv").write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match="Row 2 in 2001-02.csv has non-empty extra fields"):
        load_all_seasons(data_dir=csv_dir)


def test_load_all_seasons_unnamed_empty_column_dropped(tmp_path: Path):
    """Verifica che colonne senza nome interamente vuote vengano scartate."""
    csv_dir = tmp_path / "unnamed_empty"
    csv_dir.mkdir()

    content = (
        "Div,Date,HomeTeam,AwayTeam,\n"
        "E0,14/08/01,Arsenal,Chelsea,\n"
        "E0,15/08/01,Liverpool,Everton,\n"
    )
    (csv_dir / "2001-02.csv").write_text(content, encoding="utf-8")

    df = load_all_seasons(data_dir=csv_dir)
    assert "Unnamed: 4" not in df.columns
    assert "" not in df.columns
    assert set(df.columns) == {"Div", "Date", "HomeTeam", "AwayTeam", "season"}


def test_load_all_seasons_unnamed_column_with_content_raises(tmp_path: Path):
    """Verifica che una colonna senza nome contenente valori sollevi ValueError."""
    csv_dir = tmp_path / "unnamed_content"
    csv_dir.mkdir()

    content = (
        "Div,Date,HomeTeam,AwayTeam,\n"
        "E0,14/08/01,Arsenal,Chelsea,unexpected_data\n"
    )
    (csv_dir / "2001-02.csv").write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match="Unnamed column at index 4 in 2001-02.csv contains non-empty values"):
        load_all_seasons(data_dir=csv_dir)


def test_load_all_seasons_utf8_bom(tmp_path: Path):
    """Verifica che un file con BOM UTF-8 mantenga 'Div' come prima colonna."""
    csv_dir = tmp_path / "bom_dir"
    csv_dir.mkdir()

    content = b"\xef\xbb\xbfDiv,Date,HomeTeam,AwayTeam\nE0,14/08/01,Arsenal,Chelsea\n"
    (csv_dir / "2001-02.csv").write_bytes(content)

    df = load_all_seasons(data_dir=csv_dir)
    assert "Div" in df.columns
    assert "\ufeffDiv" not in df.columns


def test_load_all_seasons_cp1252_fallback_preserves_nbsp(tmp_path: Path):
    """Verifica che un byte 0xA0 sia decodificato via cp1252 e preservato come \\xa0."""
    csv_dir = tmp_path / "cp1252_dir"
    csv_dir.mkdir()

    # 0xA0 prima di U Rennie nella colonna Referee
    content = b"Div,Date,HomeTeam,AwayTeam,Referee\nE0,14/08/04,Arsenal,Everton,\xa0U Rennie\n"
    (csv_dir / "2004-05.csv").write_bytes(content)

    df = load_all_seasons(data_dir=csv_dir)
    referee_val = df.loc[0, "Referee"]
    assert "\xa0" in referee_val
    assert referee_val == "\xa0U Rennie"


def test_load_all_seasons_mixed_date_formats_raises(tmp_path: Path):
    """Verifica che formati di data misti nello stesso file sollevino ValueError."""
    csv_dir = tmp_path / "mixed_dates"
    csv_dir.mkdir()

    content = (
        "Div,Date,HomeTeam,AwayTeam\n"
        "E0,14/08/01,Arsenal,Chelsea\n"
        "E0,15/08/2001,Liverpool,Everton\n"
    )
    (csv_dir / "2001-02.csv").write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match="Mixed, invalid, or non-conforming date formats"):
        load_all_seasons(data_dir=csv_dir)


def test_load_all_seasons_date_out_of_window_raises(tmp_path: Path):
    """Verifica che date fuori dalla finestra stagionale sollevino ValueError."""
    csv_dir = tmp_path / "window_dates"
    csv_dir.mkdir()

    # Data antecedente al 1° luglio dell'anno iniziale (giugno 2001 per stagione 2001-02)
    s_early = "Div,Date,HomeTeam,AwayTeam\nE0,30/06/01,Arsenal,Chelsea\n"
    (csv_dir / "2001-02.csv").write_text(s_early, encoding="utf-8")
    with pytest.raises(ValueError, match="Date outside seasonal window"):
        load_all_seasons(data_dir=csv_dir)

    # Data successiva al 31 agosto dell'anno finale (settembre 2002 per stagione 2001-02)
    s_late = "Div,Date,HomeTeam,AwayTeam\nE0,01/09/02,Arsenal,Chelsea\n"
    (csv_dir / "2001-02.csv").write_text(s_late, encoding="utf-8")
    with pytest.raises(ValueError, match="Date outside seasonal window"):
        load_all_seasons(data_dir=csv_dir)


def test_load_all_seasons_unparseable_or_missing_date_raises(tmp_path: Path):
    """Verifica che date non interpretabili o mancanti sollevino ValueError."""
    csv_dir = tmp_path / "bad_dates"
    csv_dir.mkdir()

    # Data non valida
    s_bad = "Div,Date,HomeTeam,AwayTeam\nE0,99/99/99,Arsenal,Chelsea\n"
    (csv_dir / "2001-02.csv").write_text(s_bad, encoding="utf-8")
    with pytest.raises(ValueError):
        load_all_seasons(data_dir=csv_dir)

    # Colonna Date mancante
    s_missing = "Div,HomeTeam,AwayTeam\nE0,Arsenal,Chelsea\n"
    (csv_dir / "2001-02.csv").write_text(s_missing, encoding="utf-8")
    with pytest.raises(ValueError, match="Missing 'Date' column"):
        load_all_seasons(data_dir=csv_dir)


def test_load_all_seasons_two_digit_year_century_boundary(tmp_path: Path):
    """Verifica che 99 dia 1999 e 00 dia 2000, con ordinamento cronologico 1999-00 < 2000-01."""
    csv_dir = tmp_path / "century"
    csv_dir.mkdir()

    s1 = "Div,Date,HomeTeam,AwayTeam\nE0,07/08/99,Arsenal,Chelsea\n"
    (csv_dir / "1999-00.csv").write_text(s1, encoding="utf-8")

    s2 = "Div,Date,HomeTeam,AwayTeam\nE0,19/08/00,Liverpool,Everton\n"
    (csv_dir / "2000-01.csv").write_text(s2, encoding="utf-8")

    df = load_all_seasons(data_dir=csv_dir)

    assert df.loc[0, "season"] == "1999-00"
    assert df.loc[0, "Date"].year == 1999
    assert df.loc[1, "season"] == "2000-01"
    assert df.loc[1, "Date"].year == 2000
    assert "1999-00" < "2000-01"


def test_load_all_seasons_real_data():
    """Verifica il caricamento su file reali in DEFAULT_DATA_DIR (saltato se assenti)."""
    if not DEFAULT_DATA_DIR.exists():
        pytest.skip(f"Directory {DEFAULT_DATA_DIR} does not exist")

    csv_files = list(DEFAULT_DATA_DIR.glob("*.csv"))
    if not csv_files:
        pytest.skip(f"Directory {DEFAULT_DATA_DIR} contains no CSV files")

    df = load_all_seasons(data_dir=DEFAULT_DATA_DIR)

    # Il numero di stagioni caricate deve eguagliare il numero di CSV nella directory
    assert len(df["season"].unique()) == len(csv_files)

    # Nessuna data nulla
    assert not df["Date"].isna().any()

    # Tutte le date rientrano nella propria finestra stagionale
    for season_name, season_group in df.groupby("season"):
        start_year = int(str(season_name).split("-")[0])
        min_date = pd.Timestamp(year=start_year, month=7, day=1)
        max_date = pd.Timestamp(
            year=start_year + 1, month=8, day=31, hour=23, minute=59, second=59
        )
        assert (season_group["Date"] >= min_date).all()
        assert (season_group["Date"] <= max_date).all()
