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
)

from config import CUSTOM_DB, CUSTOM_DB_TABLE_NAME, CUES


if __name__ == "__main__":
    df_lib = open_mixxx_library()
    df_cues = open_mixxx_cues(only_hot_cues=False)
    error_log = ""
    for _, lib_row in tqdm(df_lib.iterrows(), total=len(df_lib)):
        cues_idx = df_cues[df_cues["track_id"] == lib_row["id"]]
        if len(cues_idx) > 0:
            try:
                beatgrid_info = BeatGridInfo(lib_row)
                interval_sec = 1 / (beatgrid_info.bpm / 60)
                samplerate = lib_row["samplerate"]
                cues_idx = df_cues[df_cues["track_id"] == lib_row["id"]]
                for idx in cues_idx.index:
                    if df_cues.loc[idx, "hotcue"] + 1 in CUES:
                        position_sec = position_frame_to_sec(
                            df_cues.loc[idx, "position"], samplerate
                        )
                        scaled_position = (
                            position_sec - beatgrid_info.start_sec
                        ) / interval_sec
                        snaped_position = round(scaled_position)
                        unscaled_position = (
                            snaped_position * interval_sec + beatgrid_info.start_sec
                        )
                        df_cues.loc[idx, "position"] = position_sec_to_frame(
                            unscaled_position, samplerate
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
