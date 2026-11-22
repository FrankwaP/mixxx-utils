import logging
from copy import copy
from pathlib import Path
from re import sub
from typing import TypeVar

from ..utils.config import FixTrackPathsUtilsConfig
from ..utils.dataclasses_operations_utils import (
    filter_left_using_right,
    filter_left_using_right_outer,
    pseudo_inner_join_outer,
    pseudo_inner_join_product,
)
from ..utils.dataclasses_utils import (
    LibraryRow,
    PerfectMatchRow,
    Table,
    TrackFixRow,
)
from ..utils.music_db_utils_no_pandas import (
    delete_rows_mixxx_db_table,
    open_mixxx_library,
    open_mixxx_track_analysis,
    open_mixxx_track_locations,
    update_mixxx_db_with_table,
)
from .close_match_utils import join_close_match


def _check_and_format_df_player(df_player: Table[TrackFixRow]) -> Table[TrackFixRow]:
    """Check that the provided DataFrame contains the necessary columns
    and that they are consistent with each other."""

    assert all(Path(r.player_path).is_absolute() for r in df_player)

    # checking/cleaning missing files
    init_len = len(df_player)
    df_player = Table(r for r in df_player if Path(r.player_path).exists())
    cleaned_len = len(df_player)
    assert (
        0 < cleaned_len
    ), "Error: the player database is empty after filtering for existing locations!"
    if cleaned_len < init_len:
        logging.info(
            "%d tracks with missing locations have been removed "
            "from the player database.",
            init_len - cleaned_len,
        )
    return df_player


LibOrPlayerRow = TypeVar("LibOrPlayerRow", LibraryRow, TrackFixRow)


def _clean_feat(row: LibOrPlayerRow) -> LibOrPlayerRow:
    """Clean the 'feat.' from the artist and title columns of the provided DataFrame."""
    row.artist = remove_feat(row.artist)
    row.title = remove_feat(row.title)
    return row


def remove_feat(name: None | str) -> str:
    if name:
        return sub(r" \(*f(?:ea)?t\. .+", "", name)
    return ""


def fix_with_player_db(
    config: FixTrackPathsUtilsConfig, table_player: Table[TrackFixRow]
) -> None:
    """Fix the Mixxx tracks locations using the ones from a music player database."""

    # open Mixxx library and keep only the missing tracks (i.e. the ones we want to fix)
    table_lib = open_mixxx_library(config.mixxx_db, quit_if_duplicates=True)
    table_loc = open_mixxx_track_locations(
        config.mixxx_db, existing_tracks=True, missing_tracks=True
    )

    # open the player database and check that it is consistent with the expected format
    table_player = _check_and_format_df_player(table_player)

    # we do not want to use good locations of both tables
    # this avoid unique constraint failing
    # (probably can remove the check at the opening of the library,
    #  as it works only with avoiding unique constraint failing with perfect matches)
    table_loc, table_player = pseudo_inner_join_outer(
        table_loc,
        table_player,
        on_left=("location",),
        on_right=("player_path",),
        assert_unique_left=True,
        assert_unique_right=True,
    )

    table_lib, table_loc = pseudo_inner_join_product(
        table_lib,
        table_loc,
        on_left=("location",),
        on_right=("id",),
        assert_unique_left=True,
        assert_unique_right=True,
    )

    if table_lib:
        logging.info("%d missing tracks found!\n%s", len(table_lib), table_lib)
    else:
        logging.info("No missing tracks, congratulation!")
        return

    # removing the "feat." in  artist and title
    table_lib = Table(_clean_feat(r) for r in table_lib)
    table_player = Table(_clean_feat(r) for r in table_player)

    # exact-matching the tracks
    key_pm = PerfectMatchRow.get_fields()
    table_lib_pm, table_player_pm = pseudo_inner_join_product(
        table_lib,
        table_player,
        on_left=key_pm,
        on_right=key_pm,
        assert_unique_left=True,
        assert_unique_right=True,
    )
    if table_lib_pm:
        logging.info(
            "Perfect matches found for the following tracks:\n%s", table_lib_pm
        )
    else:
        logging.info("No perfect matches found…")

    # close-matching the remaining tracks
    table_lib = filter_left_using_right_outer(
        table_lib, table_lib_pm, on_left=key_pm, on_right=key_pm
    )
    table_player = filter_left_using_right_outer(
        table_player, table_player_pm, on_left=key_pm, on_right=key_pm
    )
    table_lib_cm, table_player_cm = join_close_match(config, table_lib, table_player)

    # full matching
    table_lib = table_lib_pm + table_lib_cm
    table_player = table_player_pm + table_player_cm
    if not table_lib:
        return

    # update track_location

    table_lib_copy = copy(table_lib)
    table_lib, table_loc = pseudo_inner_join_product(
        table_lib,
        table_loc,
        on_left=("location",),
        on_right=("id",),
        assert_unique_left=True,
        assert_unique_right=True,
    )
    # this test can be removed… let's say in 2027
    # the obj. is to check table_lib is unchanged
    # and therefore table_loc is aligned with table_player
    assert table_lib == table_lib_copy

    for r_loc, r_play in zip(table_loc, table_player):
        r_loc.location = r_play.player_path

    update_mixxx_db_with_table(
        db_path=config.mixxx_db,
        table=table_loc,
        db_table_name="track_locations",
        set_cols=["location"],
        where_cols=["id"],
    )

    # delete the gain and key info in the library table

    updt_cols = []
    if config.delete_gains:
        logging.info("Deleting %d gain info", len(table_lib))
        for r_lib in table_lib:
            r_lib.replaygain = 0
            r_lib.replaygain_peak = -1
            updt_cols.extend(["replaygain", "replaygain_peak"])
    if config.delete_keys:
        logging.info("Deleting %d key info", len(table_lib))
        for r_lib in table_lib:
            r_lib.key = ""
            r_lib.keys = b""
            r_lib.key_id = 0
            r_lib.keys_version = ""
            r_lib.keys_sub_version = ""
            updt_cols.extend(
                ["key", "keys", "key_id", "keys_version", "keys_sub_version"]
            )

    update_mixxx_db_with_table(
        db_path=config.mixxx_db,
        db_table_name="library",
        table=table_lib,
        set_cols=updt_cols,
        where_cols=["id"],
    )

    # delete the waveforms

    if config.delete_waveforms:
        table_wform = open_mixxx_track_analysis(config.mixxx_db)
        table_wform = filter_left_using_right(
            table_wform, table_lib, on_left=("track_id",), on_right=("id",)
        )
        logging.info("Deleting %d waveforms", len(table_wform))
        dir_ana = Path(config.mixxx_db).parent / "analysis"
        for r_wform in table_wform:
            ana_path = dir_ana / f"{r_wform.id}"
            ana_path.unlink(missing_ok=True)

        delete_rows_mixxx_db_table(
            db_path=config.mixxx_db,
            db_table_name="track_analysis",
            table=table_wform,
            where_cols=["id"],
        )
