from pathlib import Path
from sys import exit
from typing import Final

import pandas as pd
from python_tools.utils.music_db_utils import (
    file_url_to_path,
    open_mixxx_library,
    open_mixxx_track_locations,
    open_mixxx_track_analysis,
    create_mixxx_db_backup,
    update_mixxx_db_table___,
    delete_rows_mixxx_db_table,
)
from python_tools.utils.track_utils import (
    get_closest_matches_indices,
    remove_feat,
)

from python_tools import CONFIG

COLS_PERFECT_MATCH: Final[list[str]] = ["artist", "album", "title"]
COLS_CLOSE_MATCH: Final[list[str]] = ["artist", "title"]
IDX_MIXXX_LIB: Final[str] = "saved_indices_mixxx_library"
IDX_PLAYER: Final[str] = "saved_indices_player"
IDX_MIXXX_TLOC: Final[str] = "saved_indices_mixxx_location"
IDX_MIXXX_TANA: Final[str] = "saved_indices_mixxx_analysis"

PLAYER_PATH = "PLAYER_PATH"


cfg = CONFIG.fix_track_paths
cfg_mixxx = CONFIG.mixxx


def _check_and_format_df_player(df_player: pd.DataFrame) -> pd.DataFrame:
    """Check that the provided DataFrame contains the necessary columns and that they are consistent with each other."""
    assert all(
        col in df_player.columns for col in COLS_PERFECT_MATCH
    ), f"Error: the provided database must contain the following columns for matching: {COLS_PERFECT_MATCH}"
    assert (
        PLAYER_PATH in df_player.columns
    ), "Error: the provided database must contain a 'absolute_path' column with the absolute path of the tracks."
    #
    df_player[PLAYER_PATH] = df_player[PLAYER_PATH].apply(file_url_to_path)
    #
    check_path = df_player[PLAYER_PATH].iloc[0]
    assert Path(
        check_path
    ).is_absolute(), f"Error: the 'absolute_path' column must contain absolute paths. Here is the first path checked: {check_path}"
    # checking/cleaning missing files
    init_len = len(df_player)
    df_player = df_player[df_player[PLAYER_PATH].apply(lambda p: Path(p).exists())]
    cleaned_len = len(df_player)
    assert 0 < cleaned_len, (
        "Error: the player database is empty after filtering for existing locations."
        f"Here is the first path checked: {check_path}"
    )
    if cleaned_len < init_len:
        print(
            f"Warning: {init_len - cleaned_len} tracks have been removed from the player database "
            "because their locations do not exist on the filesystem."
        )
    return df_player


def _clean_feat(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the 'feat.' from the artist and title columns of the provided DataFrame."""
    for col in COLS_CLOSE_MATCH:
        df.loc[:, col] = df[col].apply(remove_feat)
    df.loc[:, COLS_CLOSE_MATCH] = df[COLS_CLOSE_MATCH].fillna("")
    return df


def _ask_match_index(df_player_nomatch: pd.DataFrame, close_indices: pd.Index) -> str:
    df_choices = df_player_nomatch.loc[close_indices, COLS_PERFECT_MATCH].reset_index(
        drop=True
    )
    print(df_choices)
    choices = [""] + [str(i) for i in df_choices.index]
    while True:
        ans = input(
            "Please choose an index or leave empty to skip the operation "
            f"({choices}) : "
        )
        if ans in choices:
            break
    return ans


def _get_perfect_match(
    df_mixxx_missing: pd.DataFrame, df_player: pd.DataFrame
) -> pd.DataFrame:
    df_match = pd.merge(
        left=df_player,
        right=df_mixxx_missing,
        how="inner",
        on=None,
        left_on=COLS_PERFECT_MATCH,
        right_on=COLS_PERFECT_MATCH,
        suffixes=["_player", None],
    )

    if len(df_match) > 0:
        print(
            f"{len(df_match)} perfect matches found! They will be automatically fixed.",
            df_match[COLS_PERFECT_MATCH],
        )
    return df_match


def _get_close_match(
    df_mixxx_missing: pd.DataFrame,
    df_player: pd.DataFrame,
    df_perfect_match: pd.DataFrame,
) -> pd.DataFrame:
    # we work on the tracks with no perfect match (nm)
    df_mixxx_nomatch = df_mixxx_missing.drop(
        index=pd.Index(df_perfect_match[IDX_MIXXX_LIB])
    )
    df_player_nomatch = df_player.drop(index=pd.Index(df_perfect_match[IDX_PLAYER]))

    if len(df_mixxx_nomatch) == 0:
        return pd.DataFrame()

    print(
        f"\n\n{len(df_mixxx_nomatch)} tracks have not been found: "
        "let's find the closest match for each one…"
    )
    df_close = [
        _get_close_track_match(track_row, df_player_nomatch)
        for _, track_row in df_mixxx_nomatch.iterrows()
    ]
    return pd.concat(df_close)


def _get_close_track_match(
    track_row: pd.Series, df_player_nomatch: pd.DataFrame
) -> pd.DataFrame:
    print(
        "\nFinding the closest match for Mixxx entry \n"
        f"{track_row[COLS_PERFECT_MATCH].to_frame().T}"
    )
    close_indices = get_closest_matches_indices(
        track_row,
        df_player_nomatch,
        COLS_CLOSE_MATCH,
        cfg.threshold_name_similarity,
        cfg.n_similar_track_proposal,
    )

    if len(close_indices) == 0:
        print(
            f"\tCould not find a track with similar name with actual setting "
            f"of max similarity distance ({cfg.threshold_name_similarity})."
        )
    else:
        ans = _ask_match_index(df_player_nomatch, close_indices)
        if ans != "":
            player_idx = close_indices[int(ans)]
            track_row[PLAYER_PATH] = df_player_nomatch.loc[player_idx, PLAYER_PATH]
            return track_row.to_frame().T

    return pd.DataFrame()


def _update_mixxx_track_location(df_match: pd.DataFrame) -> None:
    df_mixxx_loc = open_mixxx_track_locations()
    df_mixxx_loc[IDX_MIXXX_TLOC] = df_mixxx_loc.index
    df_merge = pd.merge(
        left=df_match,
        right=df_mixxx_loc,
        how="inner",
        on=None,
        left_on="location",
        right_on="id",
        suffixes=["_match", None],
    )

    df_merge.loc[:, "location"] = df_merge[PLAYER_PATH].values
    df_merge.loc[:, "filename"] = (
        df_merge[PLAYER_PATH].apply(lambda x: Path(x).name).values
    )
    df_merge.loc[:, "directory"] = (
        df_merge[PLAYER_PATH].apply(lambda x: Path(x).parent.as_posix()).values
    )
    df_merge.loc[:, "fs_deleted"] = 0
    update_mixxx_db_table___(
        df_merge,
        "track_locations",
        set_cols=["location", "filename", "directory", "fs_deleted"],
        where_cols=["id"],
    )


def _update_mixxx_library(df_match: pd.DataFrame) -> None:
    if not (cfg.delete_keys or cfg.delete_gains):
        return
    #
    if cfg.delete_keys:
        print(
            "Deleting keys information corresponding to the updated track locations..."
        )
        df_match.loc[:, "key"] = ""
        df_match.loc[:, "keys"] = b""
        df_match.loc[:, "key_id"] = 0
        df_match.loc[:, "keys_version"] = ""
        df_match.loc[:, "keys_sub_version"] = ""
        update_mixxx_db_table___(
            df_match,
            "library",
            set_cols=["key", "keys", "key_id", "keys_version", "keys_sub_version"],
            where_cols=["id"],
        )

    if cfg.delete_gains:
        print(
            "Deleting gains information corresponding to the updated track locations..."
        )
        df_match.loc[:, "replaygain"] = 0
        df_match.loc[:, "replaygain_peak"] = -1
        update_mixxx_db_table___(
            df_match,
            "library",
            set_cols=["replaygain", "replaygain_peak"],
            where_cols=["id"],
        )


def _update_mixxx_analysis(df_match: pd.DataFrame) -> None:
    if not cfg.delete_waveforms:
        return
    #
    print("Deleting waveforms corresponding to the updated track locations...")
    df_mixxx_analysis = open_mixxx_track_analysis()
    df_mixxx_analysis[IDX_MIXXX_TANA] = df_mixxx_analysis.index
    df_merge = pd.merge(
        left=df_match,
        right=df_mixxx_analysis,
        how="inner",
        on=None,
        left_on="location",
        right_on="track_id",
        suffixes=("_match", None),
    )
    dir_ana = Path(cfg_mixxx.mixxx_db).parent / "analysis"
    for id_ana in df_merge["id"].values:
        ana_path = dir_ana / f"{id_ana}"
        ana_path.unlink(missing_ok=True)
    delete_rows_mixxx_db_table(df_merge, "track_analysis", where_cols=["id"])


def fix_with_player_db(df_player: pd.DataFrame):
    """Fix the Mixxx tracks locations using the ones from a music player database."""

    # open Mixxx library and keep only the missing tracks (i.e. the ones we want to fix)
    df_mixxx_missing = open_mixxx_library(existing_tracks=False, missing_tracks=True)
    if len(df_mixxx_missing) == 0:
        print("No missing tracks, congratulation!")
        exit()

    # open the player database and check that it is consistent with the expected format
    df_player = _check_and_format_df_player(df_player)

    # removing the "feat." (sometimes in the artist field of one track and the title field of the other)
    df_mixxx_missing = _clean_feat(df_mixxx_missing)
    df_player = _clean_feat(df_player)

    # saving the table indices for the "close match" step
    df_mixxx_missing[IDX_MIXXX_LIB] = df_mixxx_missing.index
    df_player[IDX_PLAYER] = df_player.index

    # matching the tracks between Mixxx and player
    df_perfect_match = _get_perfect_match(df_mixxx_missing, df_player)
    df_close_match = _get_close_match(df_mixxx_missing, df_player, df_perfect_match)
    df_match = pd.concat([df_perfect_match, df_close_match])
    assert (
        df_match["location"].duplicated().sum() == 0
    ), "Error: there are duplicated locations (IDs) in the matched DataFrame, this should not happen."

    # update Mixxx database
    create_mixxx_db_backup()
    _update_mixxx_track_location(df_match)
    _update_mixxx_library(df_match)
    _update_mixxx_analysis(df_match)
