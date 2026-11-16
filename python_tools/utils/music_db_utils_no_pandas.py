import sys
from contextlib import closing
from os.path import exists
from pathlib import Path
from shutil import copy
from time import strftime
from typing import Any, Final, Tuple
from urllib.parse import unquote

import sqlite3

Row = dict[str, Any]
Rows = list[Row]

# columns used to relate the Mixxx and music player databases
# also used to detect duplicate entries which would crash the database
# due to a failed UNIQUE constraint
COLS_FOR_DUP: Final[list[str]] = ["tracknumber", "artist", "album", "title"]


def _propose_fix_foreign_key_constraints(db_path: Path) -> None:
    answer = input(
        "The Mixxx database cannot be opened and we must fix the foreign key constraints...\n"
        "A backup file will be created.\n\n"
        "Are you OK with that? (y/*)"
    )
    if answer != "y":
        print("There's a SQL file to help you do it manually, if you want...")
        sys.exit()
    _fix_foreign_key_constraints(db_path)


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _read_table(db_path: Path, table_name: str) -> Rows:
    with closing(sqlite3.connect(db_path)) as connection:
        cursor = connection.execute(f"SELECT * FROM {_quote_identifier(table_name)}")
        columns = [description[0] for description in cursor.description or ()]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _open_table_as_rows(db_path: Path, table_name: str) -> Rows:
    """Read a table as a list of dictionaries (the pandas-free row format)."""
    try:
        return _read_table(db_path, table_name)
    except sqlite3.OperationalError as error:
        if f"no such table: {table_name}" not in str(error):
            raise
        _propose_fix_foreign_key_constraints(db_path)
        return _read_table(db_path, table_name)


def _quit_if_duplicates(rows: Rows) -> None:
    # Filter out STEM tracks before checking for duplicates.
    rows_no_stem = [
        row for row in rows if "stem" not in str(row.get("comment") or "").casefold()
    ]
    seen: set[tuple[Any, ...]] = set()
    duplicates: Rows = []
    for row in rows_no_stem:
        key = tuple(
            row.get(column) if row.get(column) is not None else ""
            for column in COLS_FOR_DUP
        )
        if key in seen:
            duplicates.append(row)
        else:
            seen.add(key)

    if duplicates:
        print(f"""Duplicated {COLS_FOR_DUP} found!
            Please open Mixxx and clean them manually <3
            """)
        print(
            [{column: row.get(column) for column in COLS_FOR_DUP} for row in duplicates]
        )
        sys.exit(1138)


def open_mixxx_library(
    db_path: Path,
    existing_tracks: bool = True,
    missing_tracks: bool = True,
) -> Rows:
    # We check for duplicates because they make the final SQL fusion fail due
    # to a unique constraint. This can happen when paths are corrected.
    print(f"Openning the Mixxx library {db_path}.")
    rows_lib = _open_table_as_rows(db_path, "library")
    for row in rows_lib:
        for column in COLS_FOR_DUP:
            if row.get(column) is None:
                row[column] = ""
    _quit_if_duplicates(rows_lib)
    if existing_tracks and missing_tracks:
        return rows_lib

    rows_loc = _open_table_as_rows(db_path, "track_locations")
    if missing_tracks:
        print("Keeping the missing locations only.")
        location_ids = {row["id"] for row in rows_loc if not exists(row["location"])}
    elif existing_tracks:
        print("Keeping the existing locations only.")
        location_ids = {row["id"] for row in rows_loc if exists(row["location"])}
    else:
        location_ids = set()
    return [row for row in rows_lib if row.get("location") in location_ids]


def _fix_foreign_key_constraints(db_path: Path) -> None:
    """Fix incorrect foreign key constraints in the database."""
    create_mixxx_db_backup(db_path)
    print(f"Fixing foreign key constraints in database: {db_path}")

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("PRAGMA foreign_keys = OFF;")
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table'
        AND sql LIKE '%REFERENCES%library_old%';
    """)
    tables_to_fix = [row[0] for row in cursor.fetchall()]

    for table in tables_to_fix:
        print(f"Fixing foreign key constraints in table: {table}")
        cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?;",
            (table,),
        )
        schema = cursor.fetchone()[0]

        new_schema = schema.replace('REFERENCES "library_old"', 'REFERENCES "library"')
        new_table = f"{table}_new"
        cursor.execute(new_schema.replace(table, new_table))
        cursor.execute(
            f"INSERT INTO {_quote_identifier(new_table)} "
            f"SELECT * FROM {_quote_identifier(table)};"
        )
        cursor.execute(f"DROP TABLE {_quote_identifier(table)};")
        cursor.execute(
            f"ALTER TABLE {_quote_identifier(new_table)} "
            f"RENAME TO {_quote_identifier(table)};"
        )

    cursor.execute("PRAGMA foreign_keys = ON;")
    connection.commit()
    connection.close()


def open_mixxx_cues(db_path: Path, only_hot_cues: bool) -> Rows:
    print(f"Openning the Mixxx cues from {db_path}.")
    rows = _open_table_as_rows(db_path, "cues")
    if only_hot_cues:
        rows = [
            row for row in rows if row.get("hotcue") is not None and row["hotcue"] >= 0
        ]
    return rows


def open_mixxx_track_locations(db_path: Path) -> Rows:
    print(f"Openning the Mixxx track locations from {db_path}.")
    return _open_table_as_rows(db_path, "track_locations")


def open_mixxx_track_analysis(db_path: Path) -> Rows:
    print(f"Openning the Mixxx track analysis from {db_path}.")
    return _open_table_as_rows(db_path, "track_analysis")


def open_mixxx_playlists_with_tracks(
    db_path: Path,
    filter_hidden: bool,
    add_crates_as_playlist: bool,
    crate_suffix: str,
) -> Tuple[Rows, Rows]:
    rows_playlists = _open_mixxx_playlists(db_path, filter_hidden)
    rows_playlist_tracks = _open_mixxx_playlist_tracks(db_path)
    playlist_ids = {row["id"] for row in rows_playlists}
    rows_playlist_tracks = [
        row for row in rows_playlist_tracks if row.get("playlist_id") in playlist_ids
    ]

    if add_crates_as_playlist:
        rows_crates = _open_mixxx_crates(db_path, filter_hidden)
        rows_crate_tracks = _open_mixxx_crate_tracks(db_path)
        crate_ids = {row["id"] for row in rows_crates}
        rows_crate_tracks = [
            row for row in rows_crate_tracks if row.get("crate_id") in crate_ids
        ]
        playlist_id_increment = max((row["id"] for row in rows_playlists), default=0)
        rows_playlists.extend(
            _crates_to_playlists(
                rows_crates,
                idx_increment=playlist_id_increment,
                suffix=crate_suffix,
            )
        )
        rows_playlist_tracks.extend(
            _crate_tracks_to_playlist_tracks(
                rows_crate_tracks, idx_increment=playlist_id_increment
            )
        )

    return rows_playlists, rows_playlist_tracks


def _open_mixxx_playlists(db_path: Path, filter_hidden: bool) -> Rows:
    print(f"Openning the Mixxx playlists from {db_path}.")
    rows = _open_table_as_rows(db_path, "Playlists")
    if filter_hidden:
        rows = [row for row in rows if row.get("hidden") == 0]
    return rows


def _open_mixxx_playlist_tracks(db_path: Path) -> Rows:
    print(f"Openning the Mixxx playlist tracks from {db_path}.")
    return _open_table_as_rows(db_path, "PlaylistTracks")


def _open_mixxx_crates(db_path: Path, filter_hidden: bool) -> Rows:
    print(f"Openning the Mixxx crates from {db_path}.")
    rows = _open_table_as_rows(db_path, "crates")
    if filter_hidden:
        rows = [row for row in rows if row.get("show") == 1]
    return rows


def _open_mixxx_crate_tracks(db_path: Path) -> Rows:
    print(f"Openning the Mixxx crate tracks from {db_path}.")
    return _open_table_as_rows(db_path, "crate_tracks")


def _crates_to_playlists(rows_crates: Rows, idx_increment: int, suffix: str) -> Rows:
    for row in rows_crates:
        row["id"] += idx_increment
        row["name"] += suffix
    return rows_crates


def _crate_tracks_to_playlist_tracks(
    rows_crate_tracks: Rows, idx_increment: int
) -> Rows:
    rows_playlist_tracks: Rows = []
    for crate_track in rows_crate_tracks:
        playlist_track = dict(crate_track)
        playlist_track["playlist_id"] = playlist_track.pop("crate_id") + idx_increment
        playlist_track["position"] = 0
        rows_playlist_tracks.append(playlist_track)
    return rows_playlist_tracks


def file_url_to_path(file_url: str) -> str:
    assert isinstance(file_url, str), f"Error: expected a string, got {type(file_url)}"
    return unquote(file_url).replace("file://", "")


def _db_path_to_url(db_path: Path) -> str:
    # sqlite:///relative/path/to/file.db
    # sqlite:////absolute/path/to/file.db
    assert db_path.is_absolute()
    return "sqlite:///" + db_path.as_posix()


def create_mixxx_db_backup(db_path: Path) -> None:
    now = strftime("%y%m%d.%H%M%S")
    backup = db_path.with_suffix(db_path.suffix + ".bak." + now)
    copy(db_path, backup)
    print(f"Backup created: {backup}")


def update_mixxx_db_table(
    db_path: Path,
    rows: Rows,
    table_name: str,
    set_cols: list[str],
    where_cols: list[str],
) -> None:
    """Update a Mixxx table using a list of dictionaries."""
    assert isinstance(set_cols, list)
    assert all(column in row for row in rows for column in set_cols)
    assert isinstance(where_cols, list)
    assert all(column in row for row in rows for column in where_cols)
    if not rows:
        return

    sql = (
        f"UPDATE {_quote_identifier(table_name)}"
        + " SET "
        + ", ".join(f"{_quote_identifier(column)} = ?" for column in set_cols)
        + " WHERE "
        + " AND ".join(f"{_quote_identifier(column)} = ?" for column in where_cols)
    )
    params = [
        [row[column] for column in set_cols] + [row[column] for column in where_cols]
        for row in rows
    ]

    with closing(sqlite3.connect(db_path)) as connection:
        with connection:
            connection.executemany(sql, params)


def delete_rows_mixxx_db_table(
    db_path: Path, rows: Rows, table_name: str, where_cols: list[str]
) -> None:
    assert isinstance(where_cols, list)
    assert all(column in row for row in rows for column in where_cols)
    if not rows:
        return

    sql = (
        f"DELETE FROM {_quote_identifier(table_name)}"
        + " WHERE "
        + " AND ".join(f"{_quote_identifier(column)} = ?" for column in where_cols)
    )
    params = [[row[column] for column in where_cols] for row in rows]

    with closing(sqlite3.connect(db_path)) as connection:
        with connection:
            connection.executemany(sql, params)
