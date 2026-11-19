import logging
from typing import cast

from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

from python_tools.utils.config import get_snap_cues_config
from python_tools.utils.music_db_utils_no_pandas import (
    open_mixxx_cues,
    open_mixxx_library_and_location,
    update_mixxx_db_table,
)
from python_tools.utils.track_utils import BeatGridInfo, snap_cue_frame


def main():
    snap_config = get_snap_cues_config()
    rows_lib_loc = open_mixxx_library_and_location(
        snap_config.mixxx_db,
        quit_if_duplicates=False,
        existing_tracks=True,
        missing_tracks=True,
    )
    rows_cues = open_mixxx_cues(snap_config.mixxx_db, only_hot_cues=True)
    cues_update = []
    with logging_redirect_tqdm():
        for lib_row in tqdm(rows_lib_loc, total=len(rows_lib_loc)):
            track_cues_row = [
                r for r in rows_cues if r["track_id"] == lib_row["library.id"]
            ]
            if len(track_cues_row) > 0:
                try:
                    beatgrid_info = BeatGridInfo(lib_row)
                except TypeError:
                    logging.warning(
                        "Skipping track with cue points defined but no BeatGrid !?: %s",
                        lib_row["track_locations.location"],
                    )
                    continue
                if beatgrid_info.bpm <= 0:
                    logging.warning(
                        "Skipping track with invalid BPM (%s): %s",
                        beatgrid_info.bpm,
                        lib_row["track_locations.location"],
                    )
                    continue

                beat_interval_sec = 60 / beatgrid_info.bpm
                samplerate = lib_row["samplerate"]
                for cue_row in track_cues_row:
                    hotcue_idx = cast(int, cue_row["hotcue"]) + 1
                    if hotcue_idx in snap_config.idx_snapped_cues:
                        old_pos = cast(int, cue_row["position"])
                        new_pos = snap_cue_frame(
                            old_pos,
                            samplerate,
                            beatgrid_info.start_sec,
                            beat_interval_sec,
                        )
                        if new_pos != old_pos:
                            logging.info(
                                "Snapping cue %s for track %s",
                                hotcue_idx,
                                lib_row["track_locations.location"],
                            )
                            cue_row["position"] = new_pos
                            cues_update.append(cue_row)

        update_mixxx_db_table(
            snap_config.mixxx_db,
            cues_update,
            "cues",
            set_cols=["position"],
            where_cols=["id"],
        )
