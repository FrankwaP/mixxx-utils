import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Final
from urllib.parse import unquote

from python_tools.utils.config import MixxxToRekordboxConfig, get_config

TRACK_ID = "TrackID"
MATCHING_KEY = "Location"
TRACK_FIELDS: Final[tuple[str, ...]] = (
    "Name",
    "Artist",
    "Album",
    "Rating",
    # "Location",
    "Tonality",
    "Colour",
)

MARK_FIELDS: Final[tuple[str, ...]] = (
    "Type",
    "Start",
    "End",
    "Num",
)

TEMPO_FIELDS: Final[tuple[str, ...]] = (
    "Location",
    "Inizio",
    "Bpm",
    # DO NOT use Metro as RkBox does not export it correctly (always "4/4")
    # "Metro",
)

MIXXX_SUFFIX = "_mixxx"
RKBOX_SUFFIX = "_rkbox"


STR_TUPLE = tuple[str, ...]
STR_TUTUPLE = tuple[STR_TUPLE, ...]


def _get_tuple(xml_element: ET.Element, fields: tuple[str, ...]) -> STR_TUPLE:
    return tuple(xml_element.attrib.get(field, "") for field in fields)


def _get_tuple_tuple(
    xml_element: ET.Element, path: str, fields: tuple[str, ...]
) -> STR_TUTUPLE:
    out = []
    for elem in xml_element.findall(path):
        out.append(_get_tuple(elem, fields))
    return tuple(sorted(out))


def _normalize_location(loc: str) -> str:
    loc = unquote(loc)
    loc = loc.removeprefix("file://localhost/")
    loc = loc.replace("\\", "/")
    return loc


def _extract_tracks_with_marks_and_tempo(
    xml_path: Path,
) -> tuple[dict[str, tuple[STR_TUPLE, STR_TUTUPLE, STR_TUTUPLE]], dict[str, str]]:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    dict_track = {}
    dict_track_id = {}
    for track in root.findall(".//COLLECTION/TRACK"):
        track.attrib["Location"] = _normalize_location(track.attrib["Location"])
        #
        tuple_track = _get_tuple(track, TRACK_FIELDS)
        tuple_mark = _get_tuple_tuple(track, "POSITION_MARK", MARK_FIELDS)
        tuple_tempo = _get_tuple_tuple(track, "POSITION_MARK", MARK_FIELDS)

        dict_track[track.attrib[MATCHING_KEY]] = (tuple_track, tuple_mark, tuple_tempo)
        dict_track_id[track.attrib[MATCHING_KEY]] = track.attrib[TRACK_ID]
    return dict_track, dict_track_id


def _write_new_playlist(
    mtr_config: MixxxToRekordboxConfig, track_id_mixxx: list[str]
) -> None:
    tree = ET.parse(mtr_config.mixxx_to_rekordbox_xml)
    root = tree.getroot()

    NODE0 = root.find(".//PLAYLISTS/NODE")
    assert NODE0
    NODE0.attrib["Count"] = str(int(NODE0.attrib["Count"]) + 1)

    NEWNODE = ET.SubElement(
        NODE0,
        "NODE",
        attrib={
            "Name": mtr_config.playlist_updated_tracks,
            "Type": "1",
            "KeyType": "0",
            "Entries": str(len(track_id_mixxx)),
        },
    )

    for track_id in track_id_mixxx:
        ET.SubElement(NEWNODE, "TRACK", attrib={"Key": track_id})

    ET.indent(tree, space="  ", level=0)
    tree.write(
        mtr_config.mixxx_to_rekordbox_xml,
        encoding="utf-8",
        xml_declaration=True,
    )
    print(
        f"A new playlist {mtr_config.playlist_updated_tracks} has been added to "
        f"the Mixxx to Rekordbox XML file {mtr_config.mixxx_to_rekordbox_xml}."
    )


def main():

    config = get_config()
    mtr_config = config.mixxx_to_rekordbox

    tracks_mixxx, tracks_ids_mixxx = _extract_tracks_with_marks_and_tempo(
        mtr_config.mixxx_to_rekordbox_xml
    )

    tracks_rkbox, _ = _extract_tracks_with_marks_and_tempo(
        mtr_config.rekordbox_compare_export_xml
    )

    track_ids = []
    for match_key in tracks_mixxx.keys():
        if match_key not in tracks_rkbox.keys():
            logging.info("This track is new: %s", match_key)
            track_ids.append(tracks_ids_mixxx[match_key])
        elif tracks_mixxx[match_key] != tracks_rkbox[match_key]:
            logging.info("This track is updated: %s", match_key)
            track_ids.append(tracks_ids_mixxx[match_key])

    print(f"After combining, {len(track_ids)} tracks need to be (re-)imported")
    _write_new_playlist(mtr_config, track_ids)
