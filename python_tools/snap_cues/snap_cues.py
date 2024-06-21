from sys import path
from pathlib import Path

from tqdm import tqdm

path.append(Path(__file__).parent.parent.as_posix())  # ugly tricks but works fine :-p

from utils.music_db_utils import (
    open_mixxx_library,
    open_mixxx_cues,
    write_df_to_table,
)

from utils.track_utils import (
    BeatGridInfo,
    position_frame_to_sec,
    position_sec_to_frame,
    snap_cue_frame,
)

from config import CUSTOM_DB, CUSTOM_DB_TABLE_NAME, IDX_SNAPED_CUES


if __name__ == "__main__":
    df_lib = open_mixxx_library()
    df_cues = open_mixxx_cues(only_hot_cues=False)
    error_log = ""
    for _, lib_row in tqdm(df_lib.iterrows(), total=len(df_lib)):
        cues_idx = df_cues[df_cues["track_id"] == lib_row["id"]]
        if len(cues_idx) > 0:
            try:
                cues_idx = df_cues[df_cues["track_id"] == lib_row["id"]]
                if len(cues_idx) > 0:
                    beatgrid_info = BeatGridInfo(lib_row)
                    beat_interval_sec = 1 / (beatgrid_info.bpm / 60)
                    samplerate = lib_row["samplerate"]
                    for idx in cues_idx.index:
                        if df_cues.loc[idx, "hotcue"] + 1 in IDX_SNAPED_CUES:
                            df_cues.loc[idx, "position"] = snap_cue_frame(
                                df_cues.loc[idx, "position"],
                                samplerate,
                                beatgrid_info.start_sec,
                                beat_interval_sec,
                            )

            except TypeError:
                error_log += (
                    "\n The following track has cue points defined but no BeatGrid !?: "
                    f"{lib_row['artist']} - {lib_row['title']}"
                )
                pass

    print(error_log)

    write_df_to_table(
        df_cues,
        db_path=CUSTOM_DB,
        table_name=CUSTOM_DB_TABLE_NAME,
        overwrite=True,
    )
