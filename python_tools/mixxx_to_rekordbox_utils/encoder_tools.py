from logging import ERROR
from pathlib import Path
from typing import Literal

import eyed3.mp3.headers  # type: ignore


accepted_mp3_decoders = Literal["MAD", "CoreAudio", "FFmpeg"]
ACCEPTED_MP3_DECODERS: list[accepted_mp3_decoders] = ["MAD", "CoreAudio", "FFmpeg"]

eyed3.core.log.setLevel(ERROR)
eyed3.id3.frames.log.setLevel(ERROR)
eyed3.mp3.headers.log.setLevel(ERROR)


def has_xing_info(audiofile: eyed3.mp3.Mp3AudioFile) -> bool:
    return audiofile.info.xing_header is not None


def has_lame_tag(audiofile: eyed3.mp3.Mp3AudioFile) -> bool:
    return len(audiofile.info.lame_tag) > 0


def has_valid_CRC_tag(audiofile: eyed3.mp3.Mp3AudioFile) -> bool:
    try:
        return audiofile.info.lame_tag["music_crc"] > 0
    except KeyError:
        return False


def get_case_mp3(audiofile: eyed3.mp3.Mp3AudioFile) -> Literal["A", "B", "C", "D"]:
    if not has_xing_info(audiofile):
        return "A"
    elif not has_lame_tag(audiofile):
        return "B"
    elif not has_valid_CRC_tag(audiofile):
        return "C"
    else:
        return "D"


def get_offset_mp3(
    audiofile: eyed3.mp3.Mp3AudioFile, mp3_decoder: accepted_mp3_decoders
) -> int:
    check_mp3_decoder_value(mp3_decoder)
    #
    case = get_case_mp3(audiofile)
    if mp3_decoder == "MAD":
        if case == "A" or case == "D":
            return 26
    if mp3_decoder == "CoreAudio":
        if case == "A":
            return 13
        if case == "B":
            return 11
        if case == "C":
            return 26
        if case == "D":
            return 50
    if mp3_decoder == "FFmpeg":
        if case == "D":
            return 26
    return 0


def check_mp3_decoder_value(mp3_decoder: str) -> None:
    if mp3_decoder not in ACCEPTED_MP3_DECODERS:
        raise ValueError(
            "Incorrect value for Mixxx encoder: expecting {ACCEPTED_MP3_DECODERS}"
        )


def get_offset_ms(track_path: str | Path, mp3_decoder: accepted_mp3_decoders) -> int:
    path = Path(track_path)
    if path.suffix == ".m4a":
        return 48
    if path.suffix == ".mp3":
        audiofile = eyed3.load(track_path)
        return get_offset_mp3(audiofile, mp3_decoder)
    return 0
