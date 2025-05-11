-- This script will change the keys in classical format to keys in "Lancelot" format
-- this command was super useful: SELECT DISTINCT key_id, key FROM library

UPDATE library SET key = "1A" WHERE key_id = "21";
UPDATE library SET key = "1B" WHERE key_id = "12";
UPDATE library SET key = "2A" WHERE key_id = "16";
UPDATE library SET key = "2B" WHERE key_id = "7";
UPDATE library SET key = "3A" WHERE key_id = "23";
UPDATE library SET key = "3B" WHERE key_id = "2";
UPDATE library SET key = "4A" WHERE key_id = "18";
UPDATE library SET key = "4B" WHERE key_id = "9";
UPDATE library SET key = "5A" WHERE key_id = "13";
UPDATE library SET key = "5B" WHERE key_id = "4";
UPDATE library SET key = "6A" WHERE key_id = "20";
UPDATE library SET key = "6B" WHERE key_id = "11";
UPDATE library SET key = "7A" WHERE key_id = "15";
UPDATE library SET key = "7B" WHERE key_id = "6";
UPDATE library SET key = "8A" WHERE key_id = "22";
UPDATE library SET key = "8B" WHERE key_id = "1";
UPDATE library SET key = "9A" WHERE key_id = "17";
UPDATE library SET key = "9B" WHERE key_id = "8";
UPDATE library SET key = "10A" WHERE key_id = "24";
UPDATE library SET key = "10B" WHERE key_id = "3";
UPDATE library SET key = "11A" WHERE key_id = "19";
UPDATE library SET key = "11B" WHERE key_id = "10";
UPDATE library SET key = "12A" WHERE key_id = "14";
UPDATE library SET key = "12B" WHERE key_id = "5";


VACUUM;
ANALYZE;
