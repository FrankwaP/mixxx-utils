import logging

from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

from python_tools.utils.config import get_snap_cues_config
from python_tools.utils.dataclasses_operations_utils import pseudo_inner_join_product
from python_tools.utils.dataclasses_utils import CuesRow, Table
from python_tools.utils.music_db_utils_no_pandas import (
    open_mixxx_cues,
    open_mixxx_library,
    update_mixxx_db_with_table,
)
from python_tools.utils.track_utils import BeatGridInfo, snap_cue_frame


def main():
    snap_config = get_snap_cues_config()
    rows_lib = open_mixxx_library(snap_config.mixxx_db, quit_if_duplicates=False)
    rows_cues = open_mixxx_cues(snap_config.mixxx_db, only_hot_cues=True)

    rows_lib_join, rows_cues_join = pseudo_inner_join_product(
        rows_lib,
        rows_cues,
        ("id",),
        ("track_id",),
        assert_unique_left=True,
        assert_unique_right=False,
    )

    cues_update: Table[CuesRow] = Table()
    with logging_redirect_tqdm():
        for lib_row, cue_row in tqdm(
            zip(rows_lib_join, rows_cues_join), total=len(rows_lib_join)
        ):
            if lib_row.samplerate is None:
                logging.warning("Skipping track with no sample rate: %s", str(lib_row))
                continue
            try:
                beatgrid_info = BeatGridInfo(lib_row)
            except TypeError:
                logging.warning(
                    "Skipping track with cue points defined but no BeatGrid !?: %s",
                    str(lib_row),
                )
                continue
            if beatgrid_info.bpm <= 0:
                logging.warning(
                    "Skipping track with invalid BPM (%s): %s",
                    beatgrid_info.bpm,
                    str(lib_row),
                )
                continue

            beat_interval_sec = 60 / beatgrid_info.bpm
            samplerate = float(lib_row.samplerate)

            hotcue_idx = cue_row.hotcue + 1
            if hotcue_idx in snap_config.idx_snapped_cues:
                old_pos = cue_row.position
                new_pos = snap_cue_frame(
                    old_pos,
                    samplerate,
                    beatgrid_info.start_sec,
                    beat_interval_sec,
                )
                if new_pos != old_pos:
                    logging.info(
                        "Snapping cue %s for track %s", hotcue_idx, str(lib_row)
                    )
                    cue_row.position = new_pos
                    cues_update.append(cue_row)

        update_mixxx_db_with_table(
            db_path=snap_config.mixxx_db,
            db_table_name="cues",
            table=cues_update,
            set_cols=["position"],
            where_cols=["id"],
        )
