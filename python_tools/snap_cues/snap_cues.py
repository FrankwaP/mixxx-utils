from tqdm import tqdm

from python_tools.utils.music_db_utils import (
    open_mixxx_library,
    open_mixxx_cues,
    write_df_to_table,
)

from python_tools.utils.track_utils import (
    BeatGridInfo,
    snap_cue_frame,
)

from python_tools.utils.misc import confirm_config

import python_tools.snap_cues.config as cfg


if __name__ == "__main__":
    confirm_config(cfg)
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
                    if df_cues.loc[idx, "hotcue"] + 1 in cfg.IDX_SNAPPED_CUES:
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
        db_path=cfg.CUSTOM_DB,
        table_name=cfg.CUSTOM_DB_TABLE_NAME,
        overwrite=True,
    )
