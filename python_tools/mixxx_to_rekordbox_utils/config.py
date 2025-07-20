from typing import Final
from typing import Literal

from python_tools import get_config

_config = get_config()["mixxx_to_rekordbox"]

REKORDBOX_XML_FILE: Final[str] = _config["rekordbox_xml_file"]
# both can be the same if you use Mixxx on Windows =>
MIXXX_LIBRARY_FOLDER: Final[str] = _config["mixxx_library_folder"]
REKORDBOX_LIBRARY_FOLDER: Final[str] = _config["rekordbox_library_folder"]
EXPORT_ONLY_TRACKS_IN_PLAYLISTS: Final[bool] = _config[
    "export_only_tracks_in_playlists"
]
# Mixxx mp3 decoder
# this is used to calculate the tracks offsets to apply when exporting to Rekordbox
# The value can be: MAD, CoreAudio, FFmpeg
# You can find it launching Mixxx from the command line with the `--developer` parameter,
# and search for the line with You then search for the line with: "SoundSource providers for file type "mp3""
# In my case I get:
#  info [Main] SoundSourceProxy - SoundSource providers for file type "mp3"
#  info [Main] SoundSourceProxy - 3 (default) : "MAD: MPEG Audio Decoder 0.15.1 (beta) NDEBUG FPM_64BIT"
#  info [Main] SoundSourceProxy - 1 (lowest) : "FFmpeg 4.4.2-0ubuntu0.22.04.1"
# The one with the highest probability is MAD
MP3_DECODER: Final[Literal["MAD", "CoreAudio", "FFmpeg"]] = _config["mp3_decoder"]
# If one of your hot cue is always at the start of a bar (for example: a hot cue for the drop)
# then we can use it to calculate the start of the bars
# (some tracks do not start at the start of a bar so using the start of the beatgrid is incorrect)
# NOTE:
#  - set to 0 to only use the start of the BeatGrid
#  - if the hot cue does not exist, the start of the BeatGrid will be used
#  - the hot cue must be exactly on the BeatGrid: the snap_cues utility is here to help you with that!
#
INDEX_CUE_BAR_START: Final[int] = _config["index_cue_bar_start"]  #
BEATS_PER_BAR: Final[int] = _config["beats_per_bar"]
#
ADD_CRATES_AS_PLAYLIST: Final[bool] = _config["add_crates_as_playlist"]
CRATES_SUFFIX: Final[str] = _config["crates_suffix"]
