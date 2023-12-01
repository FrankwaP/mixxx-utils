-- This script uses the information from a music player, exported in a convenient 
-- format in a file "named custom_music_db.sqlite", in order to fix 
-- the tracks locations in the Mixxx database.
-- 
-- Usage:
--  # first generate the mixxxdb_fix_tracks_db.sql file
--  cp ${HOME}/.mixxx/mixxxdb.sqlite ${HOME}/.mixxx/mixxxdb.sqlite.bak.$(date +%y%m%d%H%M)
--  sqlite3  ${HOME}/.mixxx/mixxxdb.sqlite < mixxxdb_fix_tracks_db.sql
-- The database must have a "library" table with the following fields:
-- artist|album|title|file_path|file_name|folder|file_size


-- Foreign key constraints in the Mixxx schema are completely broken
-- and disabled at runtime anyway. They would cause major performance
-- issues during cleanup and would also let some of the following
-- statements fail.
PRAGMA foreign_keys = OFF;

-----------------------------------------------------------------------
-- Pre-cleanup checks                                                --
-----------------------------------------------------------------------

PRAGMA integrity_check;

-----------------------------------------------------------------------
-- Fix referential integrity issues in the Mixxx library             --
-----------------------------------------------------------------------

-- Tracks
DELETE FROM library WHERE location NOT IN (SELECT id FROM track_locations);

-- EXTRA: track locations
DELETE FROM track_locations WHERE id NOT IN (SELECT location FROM library);


-- Cues
DELETE FROM cues WHERE track_id NOT IN (SELECT id FROM library);

-- Crates
DELETE FROM crate_tracks WHERE crate_id NOT IN (SELECT id FROM crates);
DELETE FROM crate_tracks WHERE track_id NOT IN (SELECT id FROM library);

-- Playlists
DELETE FROM PlaylistTracks WHERE playlist_id NOT IN (SELECT id FROM Playlists);
DELETE FROM PlaylistTracks WHERE track_id NOT IN (SELECT id FROM library);

-- Analysis
DELETE FROM track_analysis WHERE track_id NOT IN (SELECT id FROM track_locations);


---------------------------------------------------------------
-- Updating the tracks locations using the CustomMusicDb (see user_parameters.py)
-- track_location has the following fields:
-- id|location|filename|directory|filesize|fs_deleted|needs_verification


ATTACH DATABASE "custom_music_db.sqlite" AS CustomMusicDb;

UPDATE track_locations
SET location = tmptable.PATH_MUSIC_PLAYER,
    filename = tmptable.FILENAME_MUSIC_PLAYER,
    directory = tmptable.DIRECTORY_MUSIC_PLAYER
    FROM CustomMusicDb.library as tmptable
    WHERE track_locations.id = tmptable.IDX_MIXXX_LIBRARY;

-----------------------------------------------------------------------
-- Post-cleanup maintenance                                          --
-----------------------------------------------------------------------

-- Rebuild the entire database file
-- https://www.sqlite.org/lang_vacuum.html
VACUUM;

-- According to Richard Hipp himself executing VACUUM before ANALYZE is the
-- recommended order: https://sqlite.org/forum/forumpost/62fb63a29c5f7810?t=h

-- Update statistics for the query planner
-- https://www.sqlite.org/lang_analyze.html
ANALYZE;

