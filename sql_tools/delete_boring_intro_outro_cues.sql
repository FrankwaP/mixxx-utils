-- This script will delete the keys calculated with an old key detector
-- To get the list of the keys detectors, use:
--   SELECT DISTINCT keys_sub_version FROM library;
-- for example I get:
--   vamp_plugin_id=qm-keydetector:2
--   vamp_plugin_id=keyfinder:2
-- If you want to keep only the results from "keyfinder", do:

DELETE FROM cues
WHERE type = 6 OR type = 7;
VACUUM;
ANALYZE;
