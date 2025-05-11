-- This script will delete the keys calculated with an old key detector
-- To get the list of the keys detectors, use:
--    SELECT DISTINCT keys_sub_version FROM library;
-- for example I get:
--    vamp_plugin_id=qm-keydetector:2
--    vamp_plugin_id=keyfinder:2
-- If you want to keep only the results from "keyfinder", do:

UPDATE library

SET key = "",
    keys = NULL,
    key_id = 0,
    keys_version = "",
    keys_sub_version = ""
    WHERE keys_sub_version != "vamp_plugin_id=keyfinder:2" OR keys_sub_version is NULL;
VACUUM;
ANALYZE;
