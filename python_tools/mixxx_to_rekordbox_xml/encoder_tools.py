from typing import Literal
from pathlib import Path
from logging import ERROR

import eyed3
import eyed3.mp3  # helps with the type hinting


accepted_mp3_decoders = Literal["MAD", "CoreAudio", "FFmpeg"]
ACCEPTED_MP3_DECODERS: list[accepted_mp3_decoders] = ["MAD", "CoreAudio", "FFmpeg"]

eyed3.core.log.setLevel(ERROR)

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
) -> float:
    check_mp3_decoder_value(mp3_decoder)
    #
    case = get_case_mp3(audiofile)
    offset = 0
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


def get_offset_ms(track_path: str | Path, mp3_decoder: accepted_mp3_decoders) -> float:
    path = Path(track_path)
    if path.suffix == ".m4a":
        return 48
    if path.suffix == ".mp3":
        audiofile = eyed3.load(track_path)
        return get_offset_mp3(audiofile, mp3_decoder)
    return 0


if __name__ == "__main__":
    new_mp3_files = [
        Path("/media/francois/MEGAMIX/DNB/Sleepnet - Lapse/01 - Lapse.mp3"),
        Path("/media/francois/MEGAMIX/DNB/Buunshin - All About This/01 - Acolyte.mp3"),
        Path(
            "/media/francois/MEGAMIX/DNB/VRAC/DJ Rush - Motherfucking Bass (Phace Bootleg).mp3"
        ),
        Path("/media/francois/MEGAMIX/DNB/Noisia - Purpose EP/05 - Asteroids.mp3"),
    ]

    for file in new_mp3_files:
        audiofile = eyed3.load(file)
        print(file.stem, ":", get_offset_ms(file, mp3_decoder="MAD"))
