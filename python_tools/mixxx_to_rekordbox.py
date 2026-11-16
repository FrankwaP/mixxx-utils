import logging
import re
import sys
from math import isnan
from numbers import Real
from pathlib import Path
from typing import Any, Generator
from urllib.parse import quote
from xml.etree import ElementTree as ET

from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

from python_tools.mixxx_to_rekordbox_utils.encoder_tools import get_offset_ms
from python_tools.mixxx_to_rekordbox_utils.xml_utils import (
    AttribDict,
    get_elem,
)
from python_tools.utils.config import get_config, MixxxToRekordboxConfig
from python_tools.utils.misc import (
    KEY_ID_LANCELOT,
    RATING_MAPING,
)
from python_tools.utils.music_db_utils_no_pandas import (
    Row,
    Rows,
    open_mixxx_cues,
    open_mixxx_library_and_location,
    open_mixxx_playlists_with_tracks,
)
from python_tools.utils.proto import beats_pb2

logging.basicConfig(level=logging.INFO)


RKBOX_COLOR = "rkbox_color"
NOT_ALLOWED = "ogg", "opus"
REKORDBOX_COLORS = {
    (255, 0, 0): "0xFF0000",
    (255, 165, 0): "0xFFA500",
    (255, 255, 0): "0xFFFF00",
    (0, 255, 0): "0x00FF00",
    (37, 253, 233): "0x25FDE9",
    (0, 0, 255): "0x0000FF",
    (102, 0, 153): "0x660099",
    (255, 0, 127): "0xFF007F",
}


def _convert_color_for_rekordbox(value: Any) -> str:
    if value is None:
        return ""
    assert isinstance(value, Real)
    if isnan(float(value)):
        return ""
    color = int(float(value))
    assert color == value
    rgb = ((color >> 16) & 255, (color >> 8) & 255, color & 255)
    nearest = min(
        REKORDBOX_COLORS,
        key=lambda palette_rgb: sum(
            (left - right) ** 2 for left, right in zip(palette_rgb, rgb)
        ),
    )
    return REKORDBOX_COLORS[nearest]


def is_non_empty_string(s: str) -> bool:
    return isinstance(s, str) and s.replace(" ", "") != ""


def get_root_xml() -> ET.Element:
    root = get_elem("DJ_PLAYLISTS", {"Version": "1.0.0"})
    attrib = {"Name": "rekordbox", "Version": "6.7.7", "Company": "AlphaTheta"}
    root.append(get_elem("PRODUCT", attrib))
    return root


def get_collection_xml(nb_tracks: int) -> ET.Element:
    attrib = {"Entries": nb_tracks}
    return get_elem("COLLECTION", attrib)


def get_playlists_xml() -> ET.Element:
    return get_elem("PLAYLISTS")


def get_node_xml(nb_pls: int) -> ET.Element:
    attrib = {"Type": 0, "Name": "ROOT", "Count": nb_pls}
    return get_elem("NODE", attrib)


def get_time_signature_in_comment(trk_row: Row, config: MixxxToRekordboxConfig) -> str:
    # NOTE: the denominator is not used
    if not isinstance(trk_row["comment"], str):
        return f"{config.beats_per_bar}/4"
    match = re.findall(r"\b\d+/\d\b", trk_row["comment"])
    if len(match) == 0:
        return f"{config.beats_per_bar}/4"
    location = Path(trk_row["track_locations.location"])
    if len(match) > 1:
        logging.warning(
            "More than one time signature candidates have been found in the "
            "comments of file %s (%s).",
            location,
            trk_row["comment"],
        )
    logging.info(
        "Time signature %s has been found in the comment of file %s.",
        match[0],
        location,
    )
    return match[0]


def _position_frame_to_sec(frame: int, samplerate: float) -> float:
    return frame / (2 * samplerate)


def _guess_inizio_sec(
    hot_cue_frame_pos: int, samplerate: float, bpm: float, beats_per_bar: int
) -> float:
    hot_cue_sec = _position_frame_to_sec(hot_cue_frame_pos, samplerate)
    interval_sec = 60 / bpm
    return hot_cue_sec % (beats_per_bar * interval_sec)


def _beatgrid_start_sec(track_row: Row) -> float:
    beatgrid = beats_pb2.BeatGrid()  # type: ignore[attr-defined]
    beatgrid.ParseFromString(track_row["beats"])
    return beatgrid.first_beat.frame_position / track_row["samplerate"]


def mixxx_track_and_cue_rows_to_rekbox_tempo_xml(
    trk_row: Row,
    cue_rows: Rows,
    offset_start_beatgrid_ms: int,
    config: MixxxToRekordboxConfig,
) -> ET.Element:
    assert isinstance(offset_start_beatgrid_ms, int)
    bpm = trk_row["bpm"]
    assert isinstance(bpm, float)
    hotcue_bar_index = config.index_cue_bar_start - 1
    matching_cues = [
        cue_row for cue_row in cue_rows if cue_row["hotcue"] == hotcue_bar_index
    ]
    if config.index_cue_bar_start <= 0 or not matching_cues:
        inizio = _beatgrid_start_sec(trk_row)
    else:
        if len(matching_cues) != 1:
            logging.warning(
                "More than one hotcue #%d has been found for file %s\n."
                "The first one has been kept to decide the start of the bars"
                "… but you might want to re-create it!",
                config.index_cue_bar_start,
                trk_row["track_locations.location"],
            )
        cue_row = matching_cues[0]
        inizio = _guess_inizio_sec(
            cue_row["position"],
            trk_row["samplerate"],
            bpm,
            config.beats_per_bar,
        )
        inizio += offset_start_beatgrid_ms / 1000

    attrib: AttribDict = {
        "Inizio": f"{inizio:.3f}",
        "Bpm": f"{bpm:.2f}",
        "Metro": get_time_signature_in_comment(trk_row, config),
        "Battito": "1",  # NOTE: means "1st beat of the bar" (not "1 beat per bar")
    }
    return get_elem("TEMPO", attrib)


def mixxx_track_row_to_rekbox_track_xml(
    trk_row: Row, config: MixxxToRekordboxConfig
) -> ET.Element:
    location = Path(trk_row["track_locations.location"])
    try:
        final_location = config.rekordbox_library_folder / location.relative_to(
            config.mixxx_library_folder
        )
    except ValueError as err:
        logging.warning("This track is not in the Mixxx library folder: %s", location)
        raise err

    if not is_non_empty_string(trk_row["artist"]):
        logging.warning("Artist name is empty for file: %s", location)
    if not is_non_empty_string(trk_row["title"]):
        logging.warning("Track name is empty for file: %s", location)
    if not (isinstance(trk_row["bpm"], float) and trk_row["bpm"] > 50.0):
        logging.warning("Incorrect BPM for file: %s", location)

    try:
        tonality = KEY_ID_LANCELOT[trk_row["key_id"]]
    except KeyError:
        logging.warning("Incorrect key id for file: %s", location)
        tonality = ""

    attrib: AttribDict = {
        "TrackID": trk_row["library.id"],
        "Name": trk_row["title"],
        "Artist": trk_row["artist"],
        "Composer": trk_row["composer"],
        "Album": trk_row["album"],
        "Genre": trk_row["genre"],
        "Size": trk_row["filesize"],
        "TotalTime": round(trk_row["duration"]),
        "TrackNumber": trk_row["tracknumber"],
        "Year": trk_row["year"],
        "AverageBpm": trk_row["bpm"],
        "SampleRate": trk_row["samplerate"],
        "Comment": trk_row["comment"],
        "Rating": RATING_MAPING[trk_row["rating"]],
        "Location": quote("file://localhost/" + str(final_location)),
        "Tonality": tonality,
        "Colour": trk_row[RKBOX_COLOR],
    }

    return get_elem("TRACK", attrib)


def mixxx_cue_row_to_rekbox_xml(
    track_row: Row, cue_row_: Row, samplerate: float, offset_ms: int
) -> Generator[ET.Element, None, None]:
    assert isinstance(samplerate, float)
    assert isinstance(offset_ms, int)
    start = _position_frame_to_sec(cue_row_["position"], samplerate) + offset_ms / 1000
    if start < 0:
        logging.info(
            "A negative cue start position has been found and ignored for hotcue #%d of file %s",
            int(cue_row_["hotcue"]) + 1,
            track_row["track_locations.location"],
        )
    else:
        cue_nums = [-1, cue_row_["hotcue"]]
        for cnum in cue_nums:
            attrib: AttribDict = {
                "Type": "0",
                "Num": cnum,
                "Start": f"{start:.3f}",
            }
            yield get_elem("POSITION_MARK", attrib)


def mixxx_playlist_to_rekordbox_xml(plst_row: Row, track_numbers: int) -> ET.Element:
    assert isinstance(track_numbers, int)
    attrib: AttribDict = {
        "Name": plst_row["name"],
        "Type": "1",
        "KeyType": "0",
        "Entries": track_numbers,
    }
    return get_elem("NODE", attrib)


def mixxx_playlist_track_to_rekordbox_xml(
    pls_trk_row: Row,
) -> ET.Element:
    attrib = {"Key": pls_trk_row["track_id"]}
    return get_elem("TRACK", attrib)


def _sort_value(value: Any) -> tuple[bool, Any]:
    return value is None, value


def _filter_stems(rows_lib_loc: Rows) -> Rows:
    rows = [
        row
        for row in rows_lib_loc
        if row["comment"] is None or "stem" not in row["comment"].lower()
    ]

    diff = len(rows_lib_loc) - len(rows)
    if diff:
        logging.info(
            "Filtered out %d tracks with STEM in comments",
            diff,
        )
    return rows


def _filter_filetypes(rows_lib_loc: Rows) -> Rows:
    rows = [row for row in rows_lib_loc if not row["filetype"] in NOT_ALLOWED]
    diff = len(rows_lib_loc) - len(rows)
    if diff:
        logging.warning(
            "Filtered out %d tracks with incorrect filetypes %s.",
            diff,
            list(NOT_ALLOWED),
        )
    return rows


def _filter_only_in_playlists(rows_lib_loc: Rows, rows_plst_trk: Rows) -> Rows:
    trk_ids = {row["track_id"] for row in rows_plst_trk}
    rows = [row for row in rows_lib_loc if row["library.id"] in trk_ids]
    diff = len(rows_lib_loc) - len(rows)
    if diff:
        logging.warning("Filtered out %d tracks not in playlists.", diff)
    return rows


def main() -> None:
    config = get_config()
    mtr_config = config.mixxx_to_rekordbox
    db_path = config.mixxx.mixxx_db

    if config.user_interactions.confirm_snaped and mtr_config.index_cue_bar_start != 0:
        answer = input(
            "Are you sure all these hot cues are snapped to the beatgrid (y/*)? : "
        )
        if answer != "y":
            sys.exit(2)

    #
    rows_lib_loc = open_mixxx_library_and_location(
        db_path, quit_if_duplicates=False, existing_tracks=True, missing_tracks=False
    )
    rows_lib_loc = _filter_stems(rows_lib_loc)
    rows_lib_loc = _filter_filetypes(rows_lib_loc)
    #
    rows_cues = open_mixxx_cues(db_path, only_hot_cues=True)
    rows_playlists, rows_plst_trks = open_mixxx_playlists_with_tracks(
        db_path,
        filter_hidden=True,
        add_crates_as_playlist=mtr_config.add_crates_as_playlist,
        crate_suffix=mtr_config.crates_suffix,
    )
    if mtr_config.export_only_tracks_in_playlists:
        rows_lib_loc = _filter_only_in_playlists(rows_lib_loc, rows_plst_trks)

    for row in rows_lib_loc:
        row[RKBOX_COLOR] = _convert_color_for_rekordbox(row["color"])

    logging.info("Writing the XML file")

    collection_xml = get_collection_xml(len(rows_lib_loc))
    with logging_redirect_tqdm():
        for track_row in tqdm(rows_lib_loc, total=len(rows_lib_loc)):
            try:
                track_xml = mixxx_track_row_to_rekbox_track_xml(track_row, mtr_config)
            except ValueError:
                continue

            export_offset_ms = get_offset_ms(
                track_row["track_locations.location"], mtr_config.mp3_decoder
            )
            frame_rate = float(track_row["samplerate"])
            track_cues = [
                cue_row
                for cue_row in rows_cues
                if cue_row["track_id"] == track_row["library.id"]
            ]
            for cue_row in track_cues:
                for cue_xml in mixxx_cue_row_to_rekbox_xml(
                    track_row, cue_row, frame_rate, export_offset_ms
                ):
                    track_xml.append(cue_xml)
            if track_row["beats_version"] == "BeatGrid-2.0":
                tempo_xml = mixxx_track_and_cue_rows_to_rekbox_tempo_xml(
                    track_row, track_cues, export_offset_ms, mtr_config
                )
                track_xml.append(tempo_xml)
            collection_xml.append(track_xml)

    playlists_xml = get_playlists_xml()
    node_xml = get_node_xml(len(rows_playlists))

    for playlist_row in sorted(rows_playlists, key=lambda row: row["name"]):
        playlist_tracks = sorted(
            (row for row in rows_plst_trks if row["playlist_id"] == playlist_row["id"]),
            key=lambda row: _sort_value(row["position"]),
        )
        playlist_node_xml = mixxx_playlist_to_rekordbox_xml(
            playlist_row, len(playlist_tracks)
        )
        for playlist_track_row in playlist_tracks:
            playlist_node_xml.append(
                mixxx_playlist_track_to_rekordbox_xml(playlist_track_row)
            )
        node_xml.append(playlist_node_xml)
    playlists_xml.append(node_xml)

    root_xml = get_root_xml()
    root_xml.append(collection_xml)
    root_xml.append(playlists_xml)

    tree = ET.ElementTree(element=root_xml)
    ET.indent(tree, space="  ", level=0)

    rekordbox_file = Path(
        mtr_config.mixxx_library_folder, mtr_config.mixxx_to_rekordbox_xml
    )
    tree.write(rekordbox_file, encoding="utf-8", xml_declaration=True)

    logging.info("==> %s", rekordbox_file)


if __name__ == "__main__":
    main()
