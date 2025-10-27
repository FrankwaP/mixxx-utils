SELECT
    artist,
    title
FROM library WHERE bpm_lock = 1 AND NOT EXISTS (
    SELECT 1
    FROM crate_tracks
    WHERE library.id = crate_tracks.track_id
) ORDER BY artist;
