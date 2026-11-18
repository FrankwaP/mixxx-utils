import logging
import os
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from shutil import copy
from time import strftime
from typing import Any, Final, Tuple
from urllib.parse import unquote

Row = dict[str, Any]
Rows = list[Row]

# columns used to relate the Mixxx and music player databases
# also used to detect duplicate entries which would crash the database
# due to a failed UNIQUE constraint
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


# def _quote_identifier(identifier: str) -> str:
#     return '"' + identifier.replace('"', '""') + '"'


def _dict_factory(cursor, row) -> Row:
    # Delete duplicate columns created by JOIN
    # The user must define aliases to still access the column
    names = [column[0] for column in cursor.description]
    counts = Counter(names)
    return {name: row[index] for index, name in enumerate(names) if counts[name] == 1}


def _read_table(db_path: Path, query: str) -> Rows:
    # https://www.zetcode.com/python/sqlite3-connection-row-factory/
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = _dict_factory
        cursor = conn.execute(query)
        return cursor.fetchall()


def _read_table_error_handling(db_path: Path, query: str) -> Rows:
    """Read a table as a list of dictionaries (the pandas-free row format)."""
    try:
        return _read_table(db_path, query)
    except sqlite3.OperationalError as error:
        if "no such table:" in str(error):
            raise error
        propose_fix_foreign_key_constraints(db_path)
        return _read_table(db_path, query)


def _query_table(table_name: str) -> str:
    return f"SELECT * FROM {table_name}"


def _open_table_as_df(db_path: Path, table_name: str) -> Rows:
    query = _query_table(table_name)
    return _read_table_error_handling(db_path, query)


def _query_joined_tables(
    table_name_1: str, table_name_2: str, on_1: str, on_2: str, common_cols: set[str]
) -> str:
    select = ["*"]
    # generate aliases for common columns
    if common_cols:
        select += [f't1.{a} AS "{table_name_1}.{a}"' for a in common_cols]
        select += [f't2.{a} AS "{table_name_2}.{a}"' for a in common_cols]

    return f"""
        SELECT {','.join(select)}
        FROM {table_name_1} AS t1
        JOIN {table_name_2} AS t2
            ON t1.{on_1} = t2.{on_2}
        """.strip()


def _get_colnames(db_path: Path, table_name: str) -> list[str]:
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(f"select * from {table_name}")
    return [description[0] for description in cursor.description]


def _open_joined_tables_as_df(
    db_path: Path, table_name_1: str, table_name_2: str, on_1: str, on_2: str
) -> Rows:
    cols1 = _get_colnames(db_path, table_name_1)
    cols2 = _get_colnames(db_path, table_name_2)
    common_cols = set(cols1).intersection(cols2)
    query = _query_joined_tables(table_name_1, table_name_2, on_1, on_2, common_cols)
    return _read_table_error_handling(db_path, query)


def _query_duplicates() -> str:
    join_cols = ",".join(COLS_FOR_DUP)
    return f"""
        SELECT {join_cols},COUNT(*) AS duplicate_count
        FROM library
        WHERE instr(lower(coalesce(comment, '')), 'stem') = 0
        GROUP BY {join_cols}
        HAVING COUNT(*) > 1;
        """


def _quit_if_duplicates(db_path: Path):
    query = _query_duplicates()
    dup = _read_table_error_handling(db_path, query)
    if dup:
        raise UserWarning(
            "Duplicated tracks found! "
            "Please open Mixxx and clean them manually <3\n"
            f"{dup}"
        )


def open_mixxx_library_and_location(
    db_path: Path,
    *,
    quit_if_duplicates: bool,
    existing_tracks: bool,
    missing_tracks: bool,
) -> Rows:
    # Used for fixing the track path
    # We check for duplicates because they make the final SQL fusion fail due
    # to a unique constraint. This can happen when paths are corrected.
    if quit_if_duplicates:
        _quit_if_duplicates(db_path)

    rows = _open_joined_tables_as_df(
        db_path, "library", "track_locations", "location", "id"
    )

    if os.environ.get("PYTEST_VERSION"):
        for r in rows:
            r["track_locations.location"] = (
                Path(r["track_locations.location"]).resolve().as_posix()
            )

    if existing_tracks and missing_tracks:
        return rows
    if existing_tracks:
        out = []
        for row in rows:
            tloc = Path(row["track_locations.location"])
            if tloc.exists():
                out.append(row)
            else:
                logging.warning("Removing entry with missing location: %s", tloc)
        return out
    if missing_tracks:
        return [
            row for row in rows if not Path(row["track_locations.location"]).exists()
        ]
    raise UserWarning("You do not want to return existing nor missing tracks ?!")


def fix_foreign_key_constraints(db_path: Path) -> None:
    """Fix incorrect foreign key constraints in the database."""
    create_mixxx_db_backup(db_path)
    logging.info(f"Fixing foreign key constraints in database: {db_path}")

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
        logging.info(f"Fixing foreign key constraints in table: {table}")
        cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?;",
            (table,),
        )
        schema = cursor.fetchone()[0]

        new_schema = schema.replace('REFERENCES "library_old"', 'REFERENCES "library"')
        new_table = f"{table}_new"
        cursor.execute(new_schema.replace(table, new_table))
        cursor.execute(f"INSERT INTO {new_table} " f"SELECT * FROM {table};")
        cursor.execute(f"DROP TABLE {table};")
        cursor.execute(f"ALTER TABLE {new_table} " f"RENAME TO {table};")

    cursor.execute("PRAGMA foreign_keys = ON;")
    connection.commit()
    connection.close()


def open_mixxx_cues(db_path: Path, *, only_hot_cues: bool) -> Rows:
    rows = _open_table_as_df(db_path, "cues")
    if only_hot_cues:
        rows = [row for row in rows if row["hotcue"] is not None and row["hotcue"] >= 0]
    return rows


def open_mixxx_track_analysis(db_path: Path) -> Rows:
    return _open_table_as_df(db_path, "track_analysis")


def open_mixxx_playlists_with_tracks(
    db_path: Path,
    *,
    filter_hidden: bool,
    add_crates_as_playlist: bool,
    crate_suffix: str,
) -> Tuple[Rows, Rows]:
    rows_playlists = _open_mixxx_playlists(db_path, filter_hidden)
    rows_playlist_tracks = _open_mixxx_playlist_tracks(db_path)
    playlist_ids = {row["id"] for row in rows_playlists}
    rows_playlist_tracks = [
        row for row in rows_playlist_tracks if row["playlist_id"] in playlist_ids
    ]

    if add_crates_as_playlist:
        rows_crates = _open_mixxx_crates(db_path, filter_hidden)
        rows_crate_tracks = _open_mixxx_crate_tracks(db_path)
        crate_ids = {row["id"] for row in rows_crates}
        rows_crate_tracks = [
            row for row in rows_crate_tracks if row["crate_id"] in crate_ids
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
    rows = _open_table_as_df(db_path, "Playlists")
    if filter_hidden:
        rows = [row for row in rows if row["hidden"] == 0]
    return rows


def _open_mixxx_playlist_tracks(db_path: Path) -> Rows:
    return _open_table_as_df(db_path, "PlaylistTracks")


def _open_mixxx_crates(db_path: Path, filter_hidden: bool) -> Rows:
    rows = _open_table_as_df(db_path, "crates")
    if filter_hidden:
        rows = [row for row in rows if row["show"] == 1]
    return rows


def _open_mixxx_crate_tracks(db_path: Path) -> Rows:
    return _open_table_as_df(db_path, "crate_tracks")


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


def db_path_to_url(db_path: Path) -> str:
    # sqlite:///relative/path/to/file.db
    # sqlite:////absolute/path/to/file.db
    return "sqlite:///" + db_path.as_posix()


def create_mixxx_db_backup(db_path: Path) -> None:
    now = strftime("%y%m%d.%H%M%S")
    backup = db_path.with_suffix(db_path.suffix + ".bak." + now)
    copy(db_path, backup)
    logging.info(f"Backup created: {backup}")


def update_mixxx_db_table(
    db_path: Path,
    rows: Rows,
    table_name: str,
    set_cols: list[str],
    where_cols: list[str],
) -> None:
    """Update a Mixxx table using a list of dictionaries."""
    assert isinstance(set_cols, list)
    assert all(column in rows[0] for column in set_cols) if rows else True
    assert isinstance(where_cols, list)
    assert all(column in rows[0] for column in where_cols) if rows else True
    if not rows:
        return
    create_mixxx_db_backup(db_path)
    sql = (
        f"UPDATE {table_name}"
        + " SET "
        + ", ".join(f"{column} = ?" for column in set_cols)
        + " WHERE "
        + " AND ".join(f"{column} = ?" for column in where_cols)
    )
    params = [
        [row[column] for column in set_cols] + [row[column] for column in where_cols]
        for row in rows
    ]

    with sqlite3.connect(db_path) as connection:
        connection.executemany(sql, params)


def delete_rows_mixxx_db_table(
    db_path: Path, rows: Rows, table_name: str, where_cols: list[str]
) -> None:
    assert isinstance(where_cols, list)
    assert all(column in row for row in rows for column in where_cols)
    if not rows:
        return
    create_mixxx_db_backup(db_path)
    sql = (
        f"DELETE FROM {table_name}"
        + " WHERE "
        + " AND ".join(f"{column} = ?" for column in where_cols)
    )
    params = [[row[column] for column in where_cols] for row in rows]

    with sqlite3.connect(db_path) as connection:
        connection.executemany(sql, params)
