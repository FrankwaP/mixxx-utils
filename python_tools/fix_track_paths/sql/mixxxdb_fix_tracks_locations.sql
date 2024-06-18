-- This script uses the information from a music player in order to fix
-- the tracks locations in the Mixxx database.
-- All the files/tables/colums names are defined in config.py

ATTACH DATABASE "custom_music_db.sqlite" AS CustomMusicDb;

UPDATE track_locations
SET location = custom_table.MUSIC_PLAYER_PATH,
    filename = custom_table.MUSIC_PLAYER_FILENAME,
    directory = custom_table.MUSIC_PLAYER_DIRECTORY
    FROM CustomMusicDb.custom_table as custom_table
    WHERE track_locations.id = custom_table.MIXXX_LOCATION_IDX;

VACUUM;
ANALYZE;
