-- this SQL query returns the tracks which meet certain conditions
-- I have written a lot of them so I just need to select the one needed
SELECT
    artist,
    title,
    album,
    datetime_added
FROM library
WHERE
    bpm_lock = 1 -- the beatgrid is locked
    AND bpm >= 160
    AND bpm <= 170
    AND 'key' = ''
    AND rating = 0
    AND NOT EXISTS ( -- this one select the tracks not present in a crate
        SELECT 1
        FROM crate_tracks
        WHERE library.id = crate_tracks.track_id
    )
    AND NOT EXISTS ( -- this one select the tracks not present in a playlist
        SELECT 1
        FROM PlaylistTracks -- noqa: CP02
        WHERE library.id = PlaylistTracks.track_id -- noqa: CP02
    )
    AND NOT EXISTS ( -- this one select the tracks with no cue prepared
        SELECT 1
        FROM cues
        WHERE library.id = cues.track_id
    )
ORDER BY datetime_added;
