from sys import exit
from math import prod
from os.path import expandvars, exists
from pathlib import Path
import sqlite3
from urllib.parse import unquote


from jellyfish import levenshtein_distance
import pandas as pd

from user_parameters import MIXXX_DB

# columns used to relate the Mixxx and music player databases
# also used to detect duplicate entries which would crash the database
# due to a faile UNIQUE constraint
MERGE_COLS = ["artist", "album", "title"]

# columns used to tell the user when there is a duplicate track
# from two different albums
# this is not critical (won't crash the database)
# it's just suboptimal and I hate that
NOT_CRITICAL_DUP_COLS = ["artist", "title"]

# the columns used in the final custom database that will be used
# to fix the file paths in the Mixxx database
CUSTOM_DB_COLUMNS = ["artist", "album", "title", "file_path"]


def open_table_as_df(db_path: str, table_name: str) -> pd.DataFrame:
    return pd.read_sql_table(table_name, db_path_to_url(db_path))


def quit_if_duplicates(df: pd.DataFrame) -> None:
    df_dup = df[df.duplicated(MERGE_COLS)]
    if len(df_dup):
        print(
            f"""Duplicated {MERGE_COLS} found!
            Please open Mixxx and clean them manually <3
            """
        )
        print(df_dup[MERGE_COLS])
        exit(1138)


def hint_duplicates(df: pd.DataFrame) -> None:
    df = df[df["mixxx_deleted"] == 0]  # not actually "deleted" but hidden
    df_dup = df[df.duplicated(NOT_CRITICAL_DUP_COLS)]
    if len(df_dup):
        print(
            """Duplicated artist/title found that are not hidden!
            Not critical, just suboptimal...
            """
        )
        print(df_dup[NOT_CRITICAL_DUP_COLS])


def open_mixxx_library(keep_only_missing_track: bool)-> pd.DataFrame:
    # we add a check for duplicates because the will make
    # the final SQL fusion fail due to unique constraint
    # this can happen when there's both the correct and incorrect path for a track
    # and after the correction we end up with twice the correct path (so... duplicate)
    print(f"Openning the Mixxx library {MIXXX_DB}.")
    df_lib = open_table_as_df(MIXXX_DB, "library")
    quit_if_duplicates(df_lib)
    hint_duplicates(df_lib)
    if keep_only_missing_track:
        print(f"Keeping the missing locations only.")
        df_loc = open_table_as_df(MIXXX_DB, "track_locations")
        id_loc_missing = df_loc['id'][~df_loc['location'].apply(exists)]
        df_lib = df_lib[df_lib['location'].isin(id_loc_missing)]
    return df_lib


def open_mixxx_cues(only_hot_cues) -> pd.DataFrame:
    print(f"Openning the Mixxx cues {MIXXX_DB}.")
    df = open_table_as_df(MIXXX_DB, "cues")
    if only_hot_cues:
        df = df[df['hotcue'] >= 0]
    return df


def open_mixxx_track_locations() -> pd.DataFrame:
    print(f"Openning the Mixxx track locations {MIXXX_DB}.")
    df = open_table_as_df(MIXXX_DB, "track_locations")
    return df


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
        if_exists = "replace"
    else:
        if_exists = "fail"
    connection = sqlite3.connect(db_path)
    df.to_sql(
        table_name,
        connection,
        if_exists=if_exists,
        index=False,
        method="multi",
    )


def levenshtein_distance_sum(
    row1: pd.Series, row2: pd.Series, col_names: list[str]
) -> int:
    return prod(1 + levenshtein_distance(row1[c], row2[c]) for c in col_names)


def get_closest_matches_indices(
    row: pd.Series,
    search_df: pd.DataFrame,
    col_names: list[str],
    n_results: int = 5,
) -> pd.Index:
    distance_serie = search_df.apply(
        lambda t: levenshtein_distance_sum(t, row, col_names), axis=1
    )
    distance_serie = distance_serie.sort_values()
    return distance_serie[:n_results].index
