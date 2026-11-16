import sys
from shutil import copy
from os.path import exists
from pathlib import Path
from typing import Final, Tuple
from time import strftime

from urllib.parse import unquote
import sqlite3
import pandas as pd
from sqlalchemy.exc import NoSuchTableError

# columns used to relate the Mixxx and music player databases
# also used to detect duplicate entries which would crash the database
# due to a faile UNIQUE constraint
COLS_FOR_DUP: Final[list[str]] = ["tracknumber", "artist", "album", "title"]


def propose_fix_foreign_key_constraints(db_path: Path) -> None:
    answer = input(
        "The Mixxx database cannot be opened and we must fix the foreign key constraints...\n"
        "A backup file will be created.\n\n"
        "Are you OK with that? (y/*)"
    )
    if answer != "y":
        print("There's a SQL file to help you do it manually, if you want...")
        sys.exit()
    fix_foreign_key_constraints(db_path)


def open_table_as_df(db_path: Path, table_name: str) -> pd.DataFrame:
    try:
        return pd.read_sql_table(table_name, db_path_to_url(db_path))
    except NoSuchTableError:
        propose_fix_foreign_key_constraints(db_path)
        return open_table_as_df(db_path, table_name)


def quit_if_duplicates(df: pd.DataFrame) -> None:
    # Filter out STEM tracks before checking for duplicates
    df_no_stem = df[~df["comment"].str.contains("STEM", case=False, na=False)]
    df_dup = df_no_stem[df_no_stem.duplicated(COLS_FOR_DUP)]
    if len(df_dup):
        print(f"""Duplicated {COLS_FOR_DUP} found!
            Please open Mixxx and clean them manually <3
            """)
        print(df_dup[COLS_FOR_DUP])
        sys.exit(1138)


def open_mixxx_library(
    db_path: Path,
    existing_tracks: bool = True,
    missing_tracks: bool = True,
) -> pd.DataFrame:
    # we add a check for duplicates because the will make
    # the final SQL fusion fail due to unique constraint
    # this can happen when there's both the correct and incorrect path for a track
    # and after the correction we end up with twice the correct path (so... duplicate)
    print(f"Openning the Mixxx library {db_path}.")
    df_lib = open_table_as_df(db_path, "library")
    df_lib[COLS_FOR_DUP] = df_lib[COLS_FOR_DUP].fillna("")
    quit_if_duplicates(df_lib)
    if existing_tracks and missing_tracks:
        return df_lib
    # else we need to know which tracks exist/miss
    df_loc = open_table_as_df(db_path, "track_locations")
    if missing_tracks:
        print("Keeping the missing locations only.")
        id_loc = df_loc["id"][~df_loc["location"].apply(exists)]
    elif existing_tracks:
        print("Keeping the existing locations only.")
        id_loc = df_loc["id"][df_loc["location"].apply(exists)]
    return df_lib[df_lib["location"].isin(id_loc)]


def fix_foreign_key_constraints(db_path: Path) -> None:
    """Fix incorrect foreign key constraints in the database."""
    create_mixxx_db_backup(db_path)
    print(f"Fixing foreign key constraints in database: {db_path}")

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    # First disable foreign key checks
    cursor.execute("PRAGMA foreign_keys = OFF;")

    # Get all tables that might have foreign keys to library_old
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table'
        AND sql LIKE '%REFERENCES%library_old%';
    """)
    tables_to_fix = [row[0] for row in cursor.fetchall()]

    for table in tables_to_fix:
        print(f"Fixing foreign key constraints in table: {table}")
        # Get the table schema
        cursor.execute(
            f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}';"
        )
        schema = cursor.fetchone()[0]

        # Create new table with corrected references
        new_schema = schema.replace('REFERENCES "library_old"', 'REFERENCES "library"')
        new_table = f"{table}_new"

        # Create new table
        cursor.execute(new_schema.replace(table, new_table))

        # Copy data
        cursor.execute(f"INSERT INTO {new_table} SELECT * FROM {table};")

        # Drop old table and rename new one
        cursor.execute(f"DROP TABLE {table};")
        cursor.execute(f"ALTER TABLE {new_table} RENAME TO {table};")

    # Re-enable foreign key checks
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Commit changes and close connection
    connection.commit()
    connection.close()


def open_mixxx_cues(db_path: Path, only_hot_cues: bool) -> pd.DataFrame:
    print(f"Openning the Mixxx cues from {db_path}.")
    df = open_table_as_df(db_path, "cues")
    if only_hot_cues:
        df = df[df["hotcue"] >= 0]
    return df


def open_mixxx_track_locations(db_path: Path) -> pd.DataFrame:
    print(f"Openning the Mixxx track locations from {db_path}.")
    df = open_table_as_df(db_path, "track_locations")
    return df


def open_mixxx_track_analysis(db_path: Path) -> pd.DataFrame:
    print(f"Openning the Mixxx track analysis from {db_path}.")
    df = open_table_as_df(db_path, "track_analysis")
    return df


def open_mixxx_playlists_with_tracks(
    db_path: Path,
    filter_hidden: bool,
    add_crates_as_playlist: bool,
    crate_suffix: str,
) -> Tuple[pd.DataFrame, pd.DataFrame]:

    df_pls = _open_mixxx_playlists(db_path, filter_hidden)
    df_pls_trk = _open_mixxx_playlist_tracks(db_path)
    df_pls_trk = df_pls_trk[df_pls_trk["playlist_id"].isin(df_pls["id"])]

    if add_crates_as_playlist:
        df_crt = _open_mixxx_crates(db_path, filter_hidden)
        df_crt_trk = _open_mixxx_crate_tracks(db_path)
        df_crt_trk = df_crt_trk[df_crt_trk["crate_id"].isin(df_crt["id"])]
        # conversion
        idx_pls_max = df_pls["id"].max()
        df_pls_ = _crates_to_playlists(
            df_crt, idx_increment=idx_pls_max, suffix=crate_suffix
        )
        df_pls_trk_ = _crate_tracks_to_playlist_tracks(
            df_crt_trk, idx_increment=idx_pls_max
        )
        #
        df_pls = pd.concat([df_pls, df_pls_], axis=0)
        df_pls_trk = pd.concat([df_pls_trk, df_pls_trk_], axis=0)

    return df_pls, df_pls_trk


def _open_mixxx_playlists(db_path: Path, filter_hidden: bool) -> pd.DataFrame:
    print(f"Openning the Mixxx playlists from {db_path}.")
    df = open_table_as_df(db_path, "Playlists")
    if filter_hidden:
        df = df[df["hidden"] == 0]
    return df


def _open_mixxx_playlist_tracks(db_path: Path) -> pd.DataFrame:
    print(f"Openning the Mixxx playlist tracks from {db_path}.")
    return open_table_as_df(db_path, "PlaylistTracks")


def _open_mixxx_crates(db_path: Path, filter_hidden: bool) -> pd.DataFrame:
    print(f"Openning the Mixxx crates from {db_path}.")
    df = open_table_as_df(db_path, "crates")
    if filter_hidden:
        df = df[df["show"] == 1]  # not very consistent with the playlist :-p
    return df


def _open_mixxx_crate_tracks(db_path: Path) -> pd.DataFrame:
    print(f"Openning the Mixxx crate tracks from {db_path}.")
    df = open_table_as_df(db_path, "crate_tracks")
    return df


def _crates_to_playlists(
    df_crates: pd.DataFrame, idx_increment: int, suffix: str
) -> pd.DataFrame:
    df_crates["id"] += idx_increment
    df_crates["name"] += suffix
    return df_crates


def _crate_tracks_to_playlist_tracks(
    df_crate_tracks: pd.DataFrame, idx_increment: int
) -> pd.DataFrame:
    df_pls_trk = df_crate_tracks.rename(columns={"crate_id": "playlist_id"})
    df_pls_trk["playlist_id"] += idx_increment
    # we just create the field so it works like a playlist track
    df_pls_trk["position"] = 0
    return df_pls_trk


def file_url_to_path(file_url: str) -> str:
    assert isinstance(file_url, str), f"Error: expected a string, got {type(file_url)}"
    return unquote(file_url).replace("file://", "")


def db_path_to_url(db_path: Path) -> str:
    # sqlite:///relative/path/to/file.db
    # sqlite:////absolute/path/to/file.db
    return "sqlite:///" + db_path.as_posix()


def create_mixxx_db_backup(db_path: Path) -> None:
    now = strftime("%y%m%d.%H%M%S")
    backup = db_path.with_suffix(db_path.suffix + ".bak." + now)
    copy(db_path, backup)
    print(f"Backup created: {backup}")


def update_mixxx_db_table(
    db_path: Path,
    df: pd.DataFrame,
    table_name: str,
    set_cols: list[str],
    where_cols: list[str],
) -> None:
    """Update the Mixxx database table using a pandas DataFrame."""
    assert isinstance(set_cols, list)
    assert all(c in df.columns for c in set_cols)
    assert isinstance(where_cols, list)
    assert all(c in df.columns for c in where_cols)
    if df.empty:
        return
    sql = (
        f"UPDATE {table_name}"
        + " SET "
        + ", ".join(f"{col} = ?" for col in set_cols)
        + " WHERE "
        + " AND ".join(f"{col} = ?" for col in where_cols)
    )

    params = [
        [row[col] for col in set_cols] + [row[col] for col in where_cols]
        for _, row in df.iterrows()
    ]

    with sqlite3.connect(db_path) as conn:
        conn.executemany(sql, params)


def delete_rows_mixxx_db_table(
    db_path: Path, df: pd.DataFrame, table_name: str, where_cols: list[str]
) -> None:
    assert isinstance(where_cols, list)
    assert all(c in df.columns for c in where_cols)
    if df.empty:
        return
    sql = (
        f"DELETE FROM {table_name}"
        + " WHERE "
        + " AND ".join(f"{col} = ?" for col in where_cols)
    )

    params = [[row[col] for col in where_cols] for _, row in df.iterrows()]

    with sqlite3.connect(db_path) as conn:
        conn.executemany(sql, params)
