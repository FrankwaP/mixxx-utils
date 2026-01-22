-- This script uses the information from a music player in order to fix
-- the tracks locations in the Mixxx database.
--
-- The names <<MUST>> correspond to the ones defined in
-- python_tools/fix_track_paths_utils/clementine_custom_music_db.py
-- <<DO NOT>> change them.
-- A more robust solution will be used when Windows users are interested.


ATTACH DATABASE "/tmp/custom_music_db.sqlite" AS CustomMusicDb;

UPDATE track_locations
SET location = custom_table.MUSIC_PLAYER_PATH,
    filename = custom_table.MUSIC_PLAYER_FILENAME,
    directory = custom_table.MUSIC_PLAYER_DIRECTORY,
    fs_deleted = 0
    FROM CustomMusicDb.custom_table as custom_table
    WHERE track_locations.id = custom_table.MIXXX_LOCATION_IDX;

VACUUM;
ANALYZE;
