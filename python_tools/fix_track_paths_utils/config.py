# parameters for clementine_custom_music_db.py
# (Fixing tracks locations)
# The names MUST correspond to the ones in fix_track_paths/mixxxdb_fix_tracks_locations.sql file
# You normally do not need to change them
CLEM_DB = "${HOME}/.config/Clementine/clementine.db"
CUSTOM_DB = "/tmp/custom_music_db.sqlite"
CUSTOM_DB_TABLE_NAME = "custom_table"
CUSTOM_DB_LIBRARY_IDX_COLUMN = "MIXXX_LIBRARY_IDX"
CUSTOM_DB_LOCATION_IDX_COLUMN = "MIXXX_LOCATION_IDX"
CUSTOM_DB_PATH_COLUMN = "MUSIC_PLAYER_PATH"
CUSTOM_DB_FILENAME_COLUMN = "MUSIC_PLAYER_FILENAME"
CUSTOM_DB_DIRECTORY_COLUMN = "MUSIC_PLAYER_DIRECTORY"
THRESHOLD_NAME_SIMILARITY: int = 50
N_SIMILAR_TRACK_PROPOSAL: int = 3
