from sys import path
from typing import Optional
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree as ET

import pandas as pd


path.append(Path(__file__).parent.parent.as_posix())  # ugly tricks but works fine :-p

from utils.music_db_utils import (
    open_mixxx_library,
    open_mixxx_cues,
    open_mixxx_track_locations,
    open_mixxx_playlists,
    open_mixxx_playlist_tracks,
)


OUTPUT_FILE = "rekordbox_output.xml"


def stringify_dict(d: dict) -> dict[str:str]:
    return {k: str(v) for k, v in d.items()}


def get_elem(
    name: str, attrib: Optional[dict["str", int | float | str]] = None
) -> ET.Element:
    if attrib is None:
        attrib = {}
    return ET.Element(name, attrib=stringify_dict(attrib))


def get_root_xml() -> ET.Element:
    root = get_elem("DJ_PLAYLISTS", {"Version": "1.0.0"})
    attrib = {"Name": "rekordbox", "Version": "6.7.7", "Company": "AlphaTheta"}
    root.append(get_elem("PRODUCT", attrib))
    return root


def get_collection_xml(nb_tracks) -> ET.Element:
    attrib = {"Entries": str(nb_tracks)}
    return get_elem("COLLECTION", attrib)


def get_playlists_xml() -> ET.Element:
    return get_elem("PLAYLISTS")


def get_node_xml(nb_playlists) -> ET.Element:
    attrib = {"Type": 0, "Name": "ROOT", "Count": nb_playlists}
    return get_elem("NODE", attrib)


def mixxx_track_row_to_rekbox_xml(row: pd.Series) -> ET.Element:
    attrib = {
        "TrackID": row["id_x"],
        "Name": row["title"],
        "Artist": row["artist"],
        "Album": row["album"],
        "TrackNumber": row["tracknumber"],
        "Genre": row["genre"],
        # Unit : Second (without decimal numbers)
        "TotalTime": round(row["duration"]),
        "Tonality": row["key"],
        "AverageBpm": row["bpm"],
        "Location": quote(row["location_y"]),
        "SampleRate": row["samplerate"],
    }
    return get_elem("TRACK", attrib)


def mixxx_cue_row_to_rekbox_xml(row: pd.Series, samplerate) -> ET.Element:
    attrib = {
        "Type": "0",
        "Num": row["hotcue"],
        "Start": row["position"] / float(samplerate) / 2,
    }
    return get_elem("POSITION_MARK", attrib)


def mixxx_playlist_to_rekordbox_xml(row: pd.Series, track_numbers: int) -> ET.Element:
    attrib = {
        "Name": row["name"],
        "Type": "1",
        "KeyType": "0",
        " Entries": track_numbers,
    }
    return get_elem("NODE", attrib)


def mixxx_playlist_track_to_rekordbox_xml(row: pd.Series) -> ET.Element:
    attrib = {"Key": row["track_id"]}
    return get_elem("TRACK", attrib)


if __name__ == "__main__":
    # collection
    mixxx_lib = open_mixxx_library(missing_tracks=False)
    mixxx_tl = open_mixxx_track_locations()
    mixxx_cues = open_mixxx_cues(only_hot_cues=True)

    df_merge = pd.merge(
        left=mixxx_lib,
        right=mixxx_tl,
        left_on="location",
        right_on="id",
    )

    collection_xml = get_collection_xml(len(df_merge))
    for _, track_row in df_merge.iterrows():
        track_xml = mixxx_track_row_to_rekbox_xml(track_row)
        track_cues = mixxx_cues[mixxx_cues["track_id"] == track_row["id_x"]]
        for _, cue_row in track_cues.iterrows():
            cue_xml = mixxx_cue_row_to_rekbox_xml(cue_row, track_xml.get("SampleRate"))
            track_xml.append(cue_xml)
        collection_xml.append(track_xml)

    # playlists
    mixxx_playlists = open_mixxx_playlists(filter_hidden=True)
    mixxx_playlist_tracks = open_mixxx_playlist_tracks()
    playlists_xml = get_playlists_xml()
    node_xml = get_node_xml(len(mixxx_playlists))
    for _, pls_row in mixxx_playlists.iterrows():
        pls_tracks = mixxx_playlist_tracks[
            mixxx_playlist_tracks["playlist_id"] == pls_row["id"]
        ]
        playlist_node_xml = mixxx_playlist_to_rekordbox_xml(pls_row, len(pls_tracks))
        for _, pls_track_row in pls_tracks.iterrows():
            playlist_node_xml.append(
                mixxx_playlist_track_to_rekordbox_xml(pls_track_row)
            )
        node_xml.append(playlist_node_xml)
    playlists_xml.append(node_xml)

    #
    root_xml = get_root_xml()
    root_xml.append(collection_xml)
    root_xml.append(playlists_xml)

    tree = ET.ElementTree(element=root_xml)
    ET.indent(tree, space="  ", level=0)

    with open(OUTPUT_FILE, "w") as fxml:
        fxml.write('<?xml version="1.0" encoding="UTF-8"?>')
    tree.write(OUTPUT_FILE, encoding="unicode")

    print(f"==> {OUTPUT_FILE}")
