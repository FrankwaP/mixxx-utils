from tqdm import tqdm
import sqlite3
import pandas as pd

from python_tools import CONFIG
from python_tools.utils.music_db_utils import (
    open_mixxx_library,
    open_mixxx_cues,
    create_mixxx_db_backup,
)
from python_tools.utils.track_utils import BeatGridInfo, snap_cue_frame


def update_mixxx_db(df_cues: pd.DataFrame) -> None:
    """Update the Mixxx database with the new cue positions."""
    create_mixxx_db_backup(CONFIG.mixxx.mixxx_db)
    conn = sqlite3.connect(CONFIG.mixxx.mixxx_db)
    df_cues.to_sql("cues", conn, if_exists="replace", index=False)
    conn.close()


if __name__ == "__main__":
    cfg = CONFIG.snap_cues
    df_lib = open_mixxx_library()
    df_cues = open_mixxx_cues(only_hot_cues=False)
    error_log = ""
    for _, lib_row in tqdm(df_lib.iterrows(), total=len(df_lib)):
        cues_idx = df_cues[df_cues["track_id"] == lib_row["id"]]
        if len(cues_idx) > 0:
            try:
                beatgrid_info = BeatGridInfo(lib_row)
                if beatgrid_info.bpm <= 0:
                    error_log += (
                        f"\n Skipping track with invalid BPM ({beatgrid_info.bpm}): "
                        f"{lib_row['artist']} - {lib_row['title']}"
                    )
                    continue

                beat_interval_sec = 60 / beatgrid_info.bpm
                samplerate = lib_row["samplerate"]
                for idx in cues_idx.index:
                    if df_cues.loc[idx, "hotcue"] + 1 in cfg.idx_snapped_cues:
                        old_pos = df_cues.loc[idx, "position"]
                        new_pos = snap_cue_frame(
                            old_pos,
                            samplerate,
                            beatgrid_info.start_sec,
                            beat_interval_sec,
                        )
                        if new_pos != old_pos:
                            print(
                                f"Snapping cue {df_cues.loc[idx, 'hotcue'] + 1} for "
                                f"{lib_row['artist']} - {lib_row['title']} from "
                                f"frame {old_pos:d} to frame{new_pos:d}"
                            )
                            df_cues.loc[idx, "position"] = new_pos

            except TypeError:
                error_log += (
                    "\n The following track has cue points defined but no BeatGrid !?: "
                    f"{lib_row['artist']} - {lib_row['title']}"
                )
                pass

    print(error_log)
    update_mixxx_db(df_cues)
