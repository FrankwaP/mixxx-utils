MIXXX_DB = "${HOME}/.mixxx/mixxxdb.sqlite"
MIXXX_FOLDER = "${HOME}/Mixxx/"

# parameters for ../mixxx_to_rekordbox_xml/mixxx_to_rekordbox_xml.py
# (Rekordbox export)
REKBOX_OUTPUT_FILE = "rekordbox_output.xml"
ORIGINAL_MOUNT_POINT = "/media/francois/MEGAMIX"
FINAL_MOUNT_POINT = "E:/"
# use a trick to calculate the "inizio" using the BPM and one of hot cues (assuming it is on a beat)
GUESS_INIZIO = True
# The hotcues will be converted to more robust memory cues. Do we keep the original hotcues after conversion?
KEEP_HOT_CUES = False

# parameters for ../fix_track_paths/clementine_custom_music_db.py
# (Fixing tacks locations)
# The names must correspond to the ones in fix_track_paths/mixxxdb_fix_tracks_locations.sql file
# You normally do not need to change them
CLEM_DB = "${HOME}/.config/Clementine/clementine.db"
CUSTOM_DB = "custom_music_db.sqlite"
CUSTOM_DB_TABLE_NAME = "library"
CUSTOM_DB_MIXXX_IDX_COLUMN = "IDX_MIXXX_LIBRARY"
CUSTOM_DB_PATH_COLUMN = "PATH_MUSIC_PLAYER"
CUSTOM_DB_FILENAME_COLUMN = "FILENAME_MUSIC_PLAYER"
CUSTOM_DB_DIRECTORY_COLUMN = "DIRECTORY_MUSIC_PLAYER"


