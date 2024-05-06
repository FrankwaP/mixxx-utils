-- This script will delete the keys of the tracks whose path have been modified
-- All the files/tables/colums names are defined in config.py

ATTACH DATABASE "custom_music_db.sqlite" AS CustomMusicDb;

UPDATE library
SET key = "",
    keys = "", 
    key_id = 0
    keys_sub_version = NULL
    WHERE library.id IN (
        SELECT MIXXX_LOCATION_IDX from CustomMusicDb.custom_table
    );
VACUUM;
ANALYZE;
