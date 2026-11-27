import logging
from math import prod
from typing import Optional

from jellyfish import levenshtein_distance

from ..utils.config import FixTrackPathsUtilsConfig
from ..utils.dataclasses_utils import CloseMatchRow, LibraryRow, Table, TrackFixRow


def _rows_levenshtein_distance(row1: LibraryRow, row2: TrackFixRow) -> int:
    return prod(
        1 + levenshtein_distance(getattr(row1, a), getattr(row2, a))
        for a in CloseMatchRow.get_fields()
    )


def _ask_match_index(row_lib: LibraryRow, table_player_cm: Table[TrackFixRow]) -> str:
    print("\nFinding the closest match for Mixxx entry: \n" f"{row_lib}\n")
    print("Available choices:")
    print(table_player_cm)
    choices = [""] + [str(i) for i in range(len(table_player_cm))]
    while True:
        ans = input(
            "Please choose an index or leave empty "
            f"to skip the operation ({choices}) : "
        )
        if ans in choices:
            break
    return ans


def _indice_close_match(
    config: FixTrackPathsUtilsConfig,
    row_lib: LibraryRow,
    df_player: Table[TrackFixRow],
) -> Optional[int]:

    idx_and_dist = (
        (i, _rows_levenshtein_distance(row_lib, r)) for i, r in enumerate(df_player)
    )

    idx_and_dist_close = [
        (i, j) for i, j in idx_and_dist if j < config.threshold_name_similarity
    ]
    if not idx_and_dist_close:
        logging.info(
            "No close match found using a max distance of %f for track:\n%s",
            config.threshold_name_similarity,
            row_lib,
        )
        return None
    idx_and_dist_close = sorted(idx_and_dist_close, key=lambda x: [x[1]])
    idx_and_dist_close = idx_and_dist_close[: config.n_similar_track_proposal]

    if len(idx_and_dist_close) == 0:
        logging.warning("Could not find a similar track for track %s\n", row_lib)
    else:
        idx = [i for i, j in idx_and_dist_close]
        ans = _ask_match_index(row_lib, Table(df_player[i] for i in idx))
        if ans != "":
            return idx[int(ans)]
    return None


def join_close_match(
    config: FixTrackPathsUtilsConfig,
    df_lib: Table[LibraryRow],
    df_player: Table[TrackFixRow],
) -> tuple[Table[LibraryRow], Table[TrackFixRow]]:

    out_mixx: Table[LibraryRow] = Table()
    out_player: Table[TrackFixRow] = Table()

    for r_lib in df_lib:
        i_p = _indice_close_match(config, r_lib, df_player)
        if i_p:
            out_mixx.append(r_lib)
            out_player.append(df_player[i_p])

    return out_mixx, out_player
