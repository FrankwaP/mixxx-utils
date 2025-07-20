from python_tools import get_config

# parameters for clementine_custom_music_db.py
# (Fixing tracks locations)
# The names MUST correspond to the ones in fix_track_paths/mixxxdb_fix_tracks_locations.sql file
# You normally do not need to change them

_config = get_config()["fix_track_paths_utils"]

CLEM_DB = _config["clem_db"]
CUSTOM_DB = _config["custom_db"]
CUSTOM_DB_TABLE_NAME = _config["custom_db_table_name"]
CUSTOM_DB_LIBRARY_IDX_COLUMN = _config["custom_db_library_idx_column"]
CUSTOM_DB_LOCATION_IDX_COLUMN = _config["custom_db_location_idx_column"]
CUSTOM_DB_PATH_COLUMN = _config["custom_db_path_column"]
CUSTOM_DB_FILENAME_COLUMN = _config["custom_db_filename_column"]
CUSTOM_DB_DIRECTORY_COLUMN = _config["custom_db_directory_column"]
THRESHOLD_NAME_SIMILARITY: int = _config["threshold_name_similarity"]
N_SIMILAR_TRACK_PROPOSAL: int = _config["n_similar_track_proposal"]
