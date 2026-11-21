import logging
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from shutil import copy
from time import strftime
from typing import Final, Tuple
from urllib.parse import unquote

from .dataclasses_operations_utils import get_match_key
from .dataclasses_utils import (
    CrateRow,
    CrateTrackRow,
    CuesRow,
    LibraryRow,
    PlaylistRow,
    PlaylistTrackRow,
    Row,
    RowTypes,
    Table,
    TrackAnalysisRow,
    TrackLocationsRow,
)

# columns used to relate the Mixxx and music player databases
# also used to detect duplicate entries which would crash the database
# due to a failed UNIQUE constraint

COLS_FOR_DUP: Final[tuple[str, str, str, str]] = (
    "tracknumber",
    "artist",
    "album",
    "title",
)


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


def _read_table(db_path: Path, query: str, row_type: type[Row]) -> Table[Row]:

    # https://www.zetcode.com/python/sqlite3-connection-row-factory/
    def dict_factory(cursor, row) -> RowTypes:
        # Delete duplicate columns created by JOIN
        # The user must define aliases to still access the column
        names = [column[0] for column in cursor.description]
        return row_type(**{name: row[index] for index, name in enumerate(names)})

    class UserListCursor(sqlite3.Cursor):
        def fetchall(self):
            return Table(super().fetchall())

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = dict_factory
        cursor = conn.cursor(factory=UserListCursor)
        results = cursor.execute(query)
        return results.fetchall()


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


def _read_table_error_handling(
    db_path: Path, query: str, row_type: type[Row]
) -> Table[Row]:
    """Read a table as a list of dictionaries (the pandas-free row format)."""
    try:
        return _read_table(db_path, query, row_type)
    except sqlite3.OperationalError as error:
        if "no such table:" in str(error):
            raise error
        propose_fix_foreign_key_constraints(db_path)
        return _read_table(db_path, query, row_type)


def _open_table_as_df(
    db_path: Path, table_name: str, row_type: type[Row]
) -> Table[Row]:
    query = f"SELECT * FROM {table_name}"
    return _read_table_error_handling(db_path, query, row_type)


def _quit_if_duplicates(rows: Table[LibraryRow]):
    mtch = [get_match_key(r, COLS_FOR_DUP) for r in rows]
    cntr = Counter(mtch)
    cntr_ = {k: v for k, v in cntr.items() if v > 1}
    if cntr_:
        dups = [r for m, r in zip(mtch, rows) if m in cntr_]
        raise RuntimeError(
            "Duplicated tracks found! "
            "Please open Mixxx and clean them manually <3\n"
            f"{dups}"
        )


def _filter_stems(rows: Table[LibraryRow]) -> Table[LibraryRow]:
    out = Table(r for r in rows if r.comment is None or "stem" not in r.comment.lower())
    diff = len(rows) - len(out)
    if diff:
        logging.info("Filtered out %d tracks with STEM in comments", diff)
    return out


def open_mixxx_library(db_path: Path, *, quit_if_duplicates: bool) -> Table[LibraryRow]:
    rows = _open_table_as_df(db_path, "library", LibraryRow)
    if quit_if_duplicates:
        _quit_if_duplicates(rows)
    rows = _filter_stems(rows)
    return rows


def open_mixxx_track_locations(
    db_path: Path, *, existing_tracks: bool, missing_tracks: bool
) -> Table[TrackLocationsRow]:
    rows = _open_table_as_df(db_path, "track_locations", TrackLocationsRow)

    if existing_tracks and missing_tracks:
        return rows
    if existing_tracks:
        word = "missing"
    elif missing_tracks:
        word = "existing"
    else:
        raise RuntimeError("You do not want to return existing nor missing tracks ?!")

    out: Table[TrackLocationsRow] = Table()
    for r in rows:
        tloc = r.location
        if Path(tloc).exists() == existing_tracks:
            out.append(r)
        else:
            logging.warning("Removing entry with %s location: %s", word, tloc)

    return out


def open_mixxx_cues(db_path: Path, *, only_hot_cues: bool) -> Table[CuesRow]:
    rows = _open_table_as_df(db_path, "cues", CuesRow)
    if only_hot_cues:
        rows = Table(row for row in rows if row.hotcue is not None and row.hotcue >= 0)
    return rows


def open_mixxx_track_analysis(db_path: Path) -> Table[TrackAnalysisRow]:
    return _open_table_as_df(db_path, "track_analysis", TrackAnalysisRow)


def open_mixxx_playlists_with_tracks(
    db_path: Path,
    *,
    filter_hidden: bool,
    add_crates_as_playlist: bool,
    crate_suffix: str,
) -> Tuple[Table[PlaylistRow], Table[PlaylistTrackRow]]:
    # this tool is used to handle adding crates as playlist
    rows_playlists = _open_mixxx_playlists(db_path, filter_hidden)
    rows_playlist_tracks = _open_mixxx_playlist_tracks(db_path)
    playlist_ids = {row.id for row in rows_playlists}
    rows_playlist_tracks = Table(
        row for row in rows_playlist_tracks if row.playlist_id in playlist_ids
    )

    if add_crates_as_playlist:
        rows_crates = _open_mixxx_crates(db_path, filter_hidden)
        rows_crate_tracks = _open_mixxx_crate_tracks(db_path)
        crate_ids = {row.id for row in rows_crates}
        rows_crate_tracks = Table(
            row for row in rows_crate_tracks if row.crate_id in crate_ids
        )
        playlist_id_increment = max((row.id for row in rows_playlists), default=0)
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


def _open_mixxx_playlists(db_path: Path, filter_hidden: bool) -> Table[PlaylistRow]:
    rows = _open_table_as_df(db_path, "Playlists", PlaylistRow)
    if filter_hidden:
        rows = Table(row for row in rows if row.hidden == 0)
    return rows


def _open_mixxx_playlist_tracks(db_path: Path) -> Table[PlaylistTrackRow]:
    return _open_table_as_df(db_path, "PlaylistTracks", PlaylistTrackRow)


def _open_mixxx_crates(db_path: Path, filter_hidden: bool) -> Table[CrateRow]:
    rows = _open_table_as_df(db_path, "crates", CrateRow)
    if filter_hidden:
        rows = Table(row for row in rows if row.show == 1)
    return rows


def _open_mixxx_crate_tracks(db_path: Path) -> Table[CrateTrackRow]:
    return _open_table_as_df(db_path, "crate_tracks", CrateTrackRow)


def _crates_to_playlists(
    rows_crates: Table[CrateRow], idx_increment: int, suffix: str
) -> Table[PlaylistRow]:
    playlist: Table[PlaylistRow] = Table()
    for row in rows_crates:
        playlist.append(
            PlaylistRow(
                id=row.id + idx_increment,
                name=row.name + suffix,
                position=None,
                hidden=1,
                date_created=None,
                date_modified=None,
                locked=row.locked,
            )
        )
    return playlist


def _crate_tracks_to_playlist_tracks(
    rows_crate_tracks: Table[CrateTrackRow], idx_increment: int
) -> Table[PlaylistTrackRow]:
    rows_playlist_tracks: Table[PlaylistTrackRow] = Table()
    for crate_track in rows_crate_tracks:
        rows_playlist_tracks.append(
            PlaylistTrackRow(
                id=0,
                track_id=crate_track.track_id,
                playlist_id=crate_track.crate_id + idx_increment,
                position=0,
                pl_datetime_added=None,
            )
        )
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
    rows: Table[Row],
    table_name: str,
    set_cols: list[str],
    where_cols: list[str],
) -> None:
    """Update a Mixxx table using a list of dictionaries."""
    assert isinstance(set_cols, list)
    assert (
        all(column in rows[0].__annotations__ for column in set_cols) if rows else True
    )
    assert isinstance(where_cols, list)
    assert (
        all(column in rows[0].__annotations__ for column in where_cols)
        if rows
        else True
    )
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
        [getattr(row, column) for column in set_cols]
        + [getattr(row, column) for column in where_cols]
        for row in rows
    ]

    with sqlite3.connect(db_path) as connection:
        connection.executemany(sql, params)


def delete_rows_mixxx_db_table(
    db_path: Path, rows: list[LibraryRow], table_name: str, where_cols: list[str]
) -> None:
    assert isinstance(where_cols, list)
    assert all(column in row.__annotations__ for row in rows for column in where_cols)
    if not rows:
        return
    create_mixxx_db_backup(db_path)
    sql = (
        f"DELETE FROM {table_name}"
        + " WHERE "
        + " AND ".join(f"{column} = ?" for column in where_cols)
    )
    params = [[getattr(row, column) for column in where_cols] for row in rows]

    with sqlite3.connect(db_path) as connection:
        connection.executemany(sql, params)
