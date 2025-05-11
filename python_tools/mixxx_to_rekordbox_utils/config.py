from typing import Final
from typing import Literal

rekordbox_xml_file: Final[str] = "rekordbox_output.xml"
# both can be the same if you use Mixxx on Windows =>
mixxx_library_folder: Final[str] = "/home/francois/Musique/DNB"
rekordbox_library_folder: Final[str] = "E:/DNB"
export_only_tracks_in_playlists: Final[bool] = True
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
mp3_decoder: Final[Literal["MAD", "CoreAudio", "FFmpeg"]] = "MAD"
# If one of your hot cue is always at the start of a bar (for example: a hot cue for the drop)
# then we can use it to calculate the start of the bars
# (some tracks do not start at the start of a bar so using the start of the beatgrid is incorrect)
# NOTE:
#  - set to 0 to only use the start of the BeatGrid
#  - if the hot cue does not exist, the start of the BeatGrid will be used
#  - the hot cue must be exactly on the BeatGrid: the snap_cues utility is here to help you with that!
#
index_cue_bar_start: Final[int] = 3  #
beats_per_bar: Final[int] = 4
#
add_crates_as_playlist: Final[bool] = True
crates_suffix: Final[str] = "_crate"
