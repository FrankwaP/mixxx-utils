-- This script will delete the waveforms of the tracks
--   whose path have been modified
-- All the files/tables/colums names are defined in config.py

ATTACH DATABASE "custom_music_db.sqlite" AS CustomMusicDb;

DELETE FROM track_analysis
    WHERE track_id IN (
        SELECT MIXXX_LOCATION_IDX from CustomMusicDb.custom_table
    );

VACUUM;
ANALYZE;
