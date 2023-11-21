from os.path import expandvars
from pathlib import Path
from shutil import copy


from music_db_utils import (
    custom_db_columns,
    open_table_as_df,
    write_df_to_table,
    file_url_to_path,
)
from user_parameters import MIXXX_DB, MIXXX_FOLDER


##
df_lib = open_table_as_df(MIXXX_DB, "library")
df_tloc = open_table_as_df(MIXXX_DB, "track_locations")


df_merge = df_lib.merge(right=df_tloc, left_on="location", right_on="id")


mixxx_path = Path(expandvars(MIXXX_FOLDER)).resolve()
for idx, track_row in df_merge.iterrows():
    if track_row["directory"] != mixxx_path:
        old_dir = df_merge.loc[idx, "directory"] = mixxx_path
        new_loc = Path(mixxx_path, track_row["filename"])
        # copying the file in Mixxx folder (if not there already)
        if not new_loc.exists():
            copy(track_row["location_y"], mixxx_path)

        # copying the cover too
        cover_path = Path(old_dir, track_row['cover'])
        cover_ext = cover_path.suffix
        
        
        
        df_merge["location_y"] = new_loc.as_posix()
        df_merge.loc[idx, "directory"] = mixxx_path


# 	filename	directory
# 181	01 - Absolute Fucking State Of It.ogg	/home/francois/Musique/S.Murk - Giant Golden Skull
# 	coverart_location
# 173	Bilateral.jpg
# 	location_y
# 0	/home/francois/Musique/Lifecycle_ Destruction/01 - Joe Ford - Into Black.ogg
