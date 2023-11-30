from sys import path
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree as ET

import pandas as pd


path.append(Path(__file__).parent.parent.as_posix())  # ugly tricks but works fine :-p

from utils.music_db_utils import (
    open_mixxx_library,
    open_mixxx_cues,
    open_mixxx_track_locations,
)


OUTPUT_FILE = 'rekordbox_output.xml'

def get_root_xml() -> ET.Element:
    root = ET.Element("DJ_PLAYLISTS", attrib={"Version": "1.0.0"})
    root.append(
        ET.Element(
            "PRODUCT",
            attrib={"Name": "rekordbox", "Version": "6.7.7", "Company": "AlphaTheta"},
        )
    )
    return root


def get_collection_xml(nb_tracks) -> ET.Element:
    return ET.Element("COLLECTION", attrib={"Entries": str(nb_tracks)})


def stringify_dict(d: dict) -> dict[str:str]:
    return {k: str(v) for k, v in d.items()}


def mixxx_track_row_to_rekbox_xml(row: pd.Series) -> ET.Element:
    attrib = {
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

    return ET.Element("TRACK", attrib=stringify_dict(attrib))


def mixxx_cue_row_to_rekbox_xml(row: pd.Series, samplerate) -> ET.Element:
    attrib = {
        "Type": "0",
        "Num": row["hotcue"],
        "Start": row["position"] / float(samplerate) / 2,
    }
    return ET.Element("POSITION_MARK", attrib=stringify_dict(attrib))


if __name__ == '__main__':
    mixxx_lib = open_mixxx_library(missing_tracks=False)
    mixxx_tl = open_mixxx_track_locations()
    mixxx_cues = open_mixxx_cues(only_hot_cues=True)

    df_merge = pd.merge(
        left=mixxx_lib, right=mixxx_tl, left_on="location", right_on="id"
    )

    collection_xml = get_collection_xml(len(df_merge))
    for _, track_row in df_merge.iterrows():
        track_xml = mixxx_track_row_to_rekbox_xml(track_row)
        for _, cue_row in mixxx_cues[
            mixxx_cues["track_id"] == track_row["id_x"]
        ].iterrows():
            cue_xml = mixxx_cue_row_to_rekbox_xml(cue_row, track_xml.get("SampleRate"))
            track_xml.append(cue_xml)
        collection_xml.append(track_xml)

    root_xml = get_root_xml()
    root_xml.append(collection_xml)

    tree = ET.ElementTree(element=root_xml)
    ET.indent(tree, space="\t", level=0)


    with open(OUTPUT_FILE, "w") as fxml:
        fxml.write('<?xml version="1.0" encoding="UTF-8"?>')
    tree.write(OUTPUT_FILE, encoding="unicode")

    print(f'==> {OUTPUT_FILE}')
