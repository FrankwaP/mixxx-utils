from typing import Final
from pathlib import Path

import pandas as pd
import xml.etree.ElementTree as ET
from urllib.parse import unquote

from python_tools import CONFIG

cfg = CONFIG.mixxx_to_rekordbox

TRACK_ID = "TrackID"
TRACK_FIELDS: Final[list[str]] = [
    "Location",
    "Artist",
    "Album",
    "Title",  # the "Name" field is renamed in this script!
    "Tonality",
    "Rating",
    "Colour",
]
MARK_FIELDS: Final[list[str]] = [
    "Location",
    "Name",
    "Type",
    "Start",
    "End",
    "Num",
]
TEMPO_FIELDS: Final[list[str]] = [
    "Location",
    "Inizio",
    "Bpm",
    "Metro",
]

MIXXX_SUFFIX = "_mixxx"
RKBOX_SUFFIX = "_rkbox"


def extract_tracks_with_marks_and_tempo(
    xml_file: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Extract POSITION_MARKs with their parent TRACK info"""
    tree = ET.parse(xml_file)
    root = tree.getroot()

    track_rows = []
    mark_rows = []
    tempo_rows = []

    for track in root.findall(".//COLLECTION/TRACK"):
        # !!! we rename this field to avoid confusion with other "Name" field
        track.attrib["Title"] = track.attrib.pop("Name")
        track.attrib["Location"] = unquote(track.attrib["Location"])
        track.attrib = {
            k: v for k, v in track.attrib.items() if k in [TRACK_ID] + TRACK_FIELDS
        }
        track_rows.append(track.attrib)
        #
        # marks/cue info
        track_attrib_mark = {
            k: v for k, v in track.attrib.items() if k in [TRACK_ID] + MARK_FIELDS
        }
        for mark in track.findall("POSITION_MARK"):
            if "Name" not in mark.attrib.keys():
                mark.attrib["Name"] = ""
            if "End" not in mark.attrib.keys():
                mark.attrib["End"] = ""
            mark_rows.append(dict(**track_attrib_mark, **mark.attrib))
        #
        # tempo info
        track_attrib_tempo = {
            k: v for k, v in track.attrib.items() if k in [TRACK_ID] + TEMPO_FIELDS
        }
        for tempo in track.findall("TEMPO"):
            tempo_rows.append(dict(**track_attrib_tempo, **tempo.attrib))

    return pd.DataFrame(track_rows), pd.DataFrame(mark_rows), pd.DataFrame(tempo_rows)


def write_new_playlist(track_id_mixxx: set[str]) -> None:
    tree = ET.parse(CONFIG.mixxx_to_rekordbox.mixxx_to_rekordbox_xml)
    root = tree.getroot()

    NODE0 = root.find(".//PLAYLISTS/NODE")
    assert NODE0
    NODE0.attrib["Count"] = str(int(NODE0.attrib["Count"]) + 1)

    NEWNODE = ET.SubElement(
        NODE0,
        "NODE",
        attrib={
            "Name": cfg.playlist_updated_tracks,
            "Type": "1",
            "KeyType": "0",
            "Entries": str(len(track_id_mixxx)),
        },
    )

    for track_id in track_id_mixxx:
        ET.SubElement(NEWNODE, "TRACK", attrib={"Key": track_id})

    ET.indent(tree, space="  ", level=0)
    tree.write(
        cfg.mixxx_to_rekordbox_xml,
        encoding="utf-8",
        xml_declaration=True,
    )
    print(
        f"A new playlist {cfg.playlist_updated_tracks} has been added to the Mixxx to Rekordbox XML file {cfg.mixxx_to_rekordbox_xml}."
    )


def main():
    df_mixxx_track, df_mixxx_mark, df_mixxx_tempo = extract_tracks_with_marks_and_tempo(
        cfg.mixxx_to_rekordbox_xml
    )
    df_rkbox_track, df_rkbox_mark, df_rkbox_tempo = extract_tracks_with_marks_and_tempo(
        cfg.rekordbox_export_xml
    )
    ###
    # Checking updated track info
    mrg_track = pd.merge(
        df_mixxx_track,
        df_rkbox_track,
        on=TRACK_FIELDS,
        how="left_anti",
        suffixes=[MIXXX_SUFFIX, RKBOX_SUFFIX],
    )
    track_id_track = mrg_track[TRACK_ID + MIXXX_SUFFIX].unique()
    print(f"{len(mrg_track)} tracks info have been updated")
    assert len(track_id_track) == len(mrg_track)
    ####
    # Checking updated mark/cue info
    mrg_mark = pd.merge(
        df_mixxx_mark,
        df_rkbox_mark,
        on=MARK_FIELDS,
        how="left_anti",
        suffixes=[MIXXX_SUFFIX, RKBOX_SUFFIX],
    )
    track_id_mark = mrg_mark[TRACK_ID + MIXXX_SUFFIX].unique()
    print(
        f"{len(mrg_mark)} marks/cues info have been updated on {len(track_id_mark)} tracks"
    )
    ####
    # Checking updated tempo info
    mrg_tempo = pd.merge(
        df_mixxx_tempo,
        df_rkbox_tempo,
        on=TEMPO_FIELDS,
        how="left_anti",
        suffixes=[MIXXX_SUFFIX, RKBOX_SUFFIX],
    )
    track_id_tempo = mrg_tempo[TRACK_ID + MIXXX_SUFFIX].unique()
    print(
        f"{len(mrg_tempo)} tempo info have been updated on {len(track_id_tempo)} tracks"
    )
    #
    track_ids = set(
        track_id_track.tolist() + track_id_mark.tolist() + track_id_tempo.tolist()
    )
    print(f"After combining, {len(track_ids)} tracks need to be (re-)imported")
    write_new_playlist(track_ids)
