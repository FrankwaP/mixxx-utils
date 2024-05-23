-- Sometimes Mixxx will say that a track is missing, but it is not
-- as you can check using the drag and drop
-- This SQL command reinitialize the corresponding field
-- so the track appears in the library again   


UPDATE track_locations
SET fs_deleted = 0
    WHERE fs_deleted = 1;
VACUUM;
ANALYZE;
