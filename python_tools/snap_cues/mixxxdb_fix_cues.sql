-- This script uses the information from a music player in order to fix
-- the tracks locations in the Mixxx database.
-- All the files/tables/colums names are defined in config.py

ATTACH DATABASE "custom_music_db.sqlite" AS CustomMusicDb;

UPDATE cues
SET position = custom_table.position
    FROM CustomMusicDb.custom_table as custom_table
    WHERE cues.id = custom_table.id;

VACUUM;
ANALYZE;
