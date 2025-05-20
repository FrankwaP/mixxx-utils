import sqlite3
import sys
from os.path import exists
from os.path import expandvars
from pathlib import Path
from typing import Final
from typing import Literal
from typing import Tuple
from urllib.parse import unquote

import pandas as pd
import sqlalchemy

from .config import MIXXX_DB

# columns used to relate the Mixxx and music player databases
# also used to detect duplicate entries which would crash the database
# due to a faile UNIQUE constraint
MERGE_COLS: Final[list[str]] = ["artist", "album", "title"]

# columns used to tell the user when there is a duplicate track
# from two different albums
# this is not critical (won't crash the database)
# it's just suboptimal and I hate that
NOT_CRITICAL_DUP_COLS: Final[list[str]] = ["artist", "title"]


def open_table_as_df(db_path: str, table_name: str) -> pd.DataFrame:
    return pd.read_sql_table(table_name, db_path_to_url(db_path))


def quit_if_duplicates(df: pd.DataFrame) -> None:
    # Filter out STEM tracks before checking for duplicates
    df_no_stem = df[~df["comment"].str.contains("STEM", case=False, na=False)]
    df_dup = df_no_stem[df_no_stem.duplicated(MERGE_COLS)]
    if len(df_dup):
        print(
            f"""Duplicated {MERGE_COLS} found!
            Please open Mixxx and clean them manually <3
            """
        )
        print(df_dup[MERGE_COLS])
        sys.exit(1138)


def hint_duplicates(df: pd.DataFrame) -> None:
    # Filter out STEM tracks before checking for duplicates
    df = df[df["mixxx_deleted"] == 0]  # not actually "deleted" but hidden
    df_no_stem = df[~df["comment"].str.contains("STEM", case=False, na=False)]
    df_dup = df_no_stem[df_no_stem.duplicated(NOT_CRITICAL_DUP_COLS)]
    if len(df_dup):
        print(
            """Duplicated artist/title found that are not hidden!
            Not critical, just suboptimal...
            """
        )
        print(df_dup[NOT_CRITICAL_DUP_COLS])


def open_mixxx_library(
    existing_tracks: bool = True, missing_tracks: bool = True
) -> pd.DataFrame:
    # we add a check for duplicates because the will make
    # the final SQL fusion fail due to unique constraint
    # this can happen when there's both the correct and incorrect path for a track
    # and after the correction we end up with twice the correct path (so... duplicate)
    print(f"Openning the Mixxx library {MIXXX_DB}.")
    df_lib = open_table_as_df(MIXXX_DB, "library")
    df_lib[MERGE_COLS] = df_lib[MERGE_COLS].fillna("")
    quit_if_duplicates(df_lib)
    # hint_duplicates(df_lib)
    if existing_tracks and missing_tracks:
        return df_lib
    # else we need to know which tracks exist/miss
    df_loc = open_table_as_df(MIXXX_DB, "track_locations")
    if missing_tracks:
        print("Keeping the missing locations only.")
        id_loc = df_loc["id"][~df_loc["location"].apply(exists)]
    elif existing_tracks:
        print("Keeping the existing locations only.")
        id_loc = df_loc["id"][df_loc["location"].apply(exists)]
    return df_lib[df_lib["location"].isin(id_loc)]


def fix_foreign_key_constraints(db_path: str) -> None:
    """Fix incorrect foreign key constraints in the database."""
    # Expand environment variables in the path
    db_path = expandvars(db_path)
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
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}';")
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


def open_mixxx_cues(only_hot_cues) -> pd.DataFrame:
    print(f"Openning the Mixxx cues from {MIXXX_DB}.")
    try:
        df = open_table_as_df(MIXXX_DB, "cues")
    except sqlalchemy.exc.NoSuchTableError:
        print("Fixing foreign key constraints...")
        fix_foreign_key_constraints(MIXXX_DB)
        df = open_table_as_df(MIXXX_DB, "cues")
    
    if only_hot_cues:
        df = df[df["hotcue"] >= 0]
    return df


def open_mixxx_track_locations() -> pd.DataFrame:
    print(f"Openning the Mixxx track locations from {MIXXX_DB}.")
    df = open_table_as_df(MIXXX_DB, "track_locations")
    return df


def open_mixxx_playlists_with_tracks(
    filter_hidden: bool,
    add_crates_as_playlist: bool,
    crate_suffix: str,
) -> Tuple[pd.DataFrame, pd.DataFrame]:

    df_pls = _open_mixxx_playlists(filter_hidden)
    df_pls_trk = _open_mixxx_playlist_tracks()
    df_pls_trk = df_pls_trk[df_pls_trk["playlist_id"].isin(df_pls["id"])]

    if add_crates_as_playlist:
        df_crt = _open_mixxx_crates(filter_hidden)
        df_crt_trk = _open_mixxx_crate_tracks()
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


def _open_mixxx_playlists(filter_hidden: bool) -> pd.DataFrame:
    print(f"Openning the Mixxx playlists from {MIXXX_DB}.")
    df = open_table_as_df(MIXXX_DB, "Playlists")
    if filter_hidden:
        df = df[df["hidden"] == 0]
    return df


def _open_mixxx_playlist_tracks() -> pd.DataFrame:
    print(f"Openning the Mixxx playlist tracks from {MIXXX_DB}.")
    try:
        df = open_table_as_df(MIXXX_DB, "PlaylistTracks")
    except sqlalchemy.exc.NoSuchTableError:
        print("Fixing foreign key constraints...")
        fix_foreign_key_constraints(MIXXX_DB)
        df = open_table_as_df(MIXXX_DB, "PlaylistTracks")
    return df


def _open_mixxx_crates(filter_hidden: bool) -> pd.DataFrame:
    print(f"Openning the Mixxx crates from {MIXXX_DB}.")
    df = open_table_as_df(MIXXX_DB, "crates")
    if filter_hidden:
        df = df[df["show"] == 1]  # not very consistent with the playlist :-p
    return df


def _open_mixxx_crate_tracks() -> pd.DataFrame:
    print(f"Openning the Mixxx crate tracks from {MIXXX_DB}.")
    df = open_table_as_df(MIXXX_DB, "crate_tracks")
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
    return unquote(file_url).replace("file://", "")


def db_path_to_url(db_path: str) -> str:
    # sqlite:///relative/path/to/file.db
    # sqlite:////absolute/path/to/file.db
    db_path = expandvars(db_path)
    path = Path(db_path)
    if path.is_absolute():
        return "sqlite:///" + path.as_posix()
    if path.is_relative_to(Path.cwd()):
        return "sqlite://" + path.as_posix()
    raise NotImplementedError


def list_table_names(db_path: str) -> list[str]:
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    command = """
    SELECT name FROM sqlite_master
      WHERE type='table';
    """
    cursor.execute(command)
    tables_names = cursor.fetchall()
    tables_names = [i[0] for i in tables_names]
    return tables_names


def write_df_to_table(
    df: pd.DataFrame, db_path: str, table_name: str, overwrite: bool = False
):
    if overwrite is True:
        if_exists: Literal["fail", "replace", "append"] = "replace"
    else:
        if_exists = "fail"
    connection = sqlite3.connect(db_path)
    df.to_sql(
        table_name,
        connection,
        if_exists=if_exists,
        index=False,
        method="multi",
        chunksize=999,
    )
