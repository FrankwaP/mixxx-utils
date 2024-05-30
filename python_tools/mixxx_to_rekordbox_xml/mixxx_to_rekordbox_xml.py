from sys import path, exit
import configparser
from typing import Optional, Generator, Mapping
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree as ET

import pandas as pd
from tqdm import tqdm

from encoder_tools import get_offset_ms

from proto import beats_pb2


path.append(Path(__file__).parent.parent.as_posix())  # ugly tricks but works fine :-p

from utils.music_db_utils import (
    open_mixxx_library,
    open_mixxx_cues,
    open_mixxx_track_locations,
    open_mixxx_playlists,
    open_mixxx_playlist_tracks,
)

AttribDict = Mapping[str, int | float | str]


# 0 star = "0", 1 star = "51", 2 stars = "102", 3 stars = "153", 4 stars = "204", 5 stars = "255"
RATING_MAPING = {0: 0, 1: 51, 2: 102, 3: 153, 4: 204, 5: 255}


def stringify_dict(d: AttribDict) -> dict[str, str]:
    return {k: str(v) for k, v in d.items()}


def get_elem(name: str, attrib: Optional[AttribDict] = None) -> ET.Element:
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


def mixxx_track_row_to_rekbox_tempo_xml(
    row: pd.Series, beats_per_bar: int
) -> ET.Element:
    beatgrid = beats_pb2.BeatGrid()
    beatgrid.ParseFromString(row["beats"])
    attrib: AttribDict = {
        "Inizio": beatgrid.first_beat.frame_position / row["samplerate"],
        "Bpm": beatgrid.bpm.bpm,
        "Metro": f"{beats_per_bar}/{beats_per_bar}",
        "Battito": "1",
    }
    return get_elem("TEMPO", attrib)


def mixxx_track_row_to_rekbox_track_xml(row: pd.Series) -> ET.Element:
    location = row["location_y"]
    final_location = location.replace(
        params["original_mount_point"], params["final_mount_point"]
    )
    attrib: AttribDict = {
        "TrackID": row["id_x"],
        "Name": row["title"],
        "Artist": row["artist"],
        "Album": row["album"],
        "TrackNumber": row["tracknumber"],
        "Genre": row["genre"],
        "TotalTime": round(row["duration"]),
        "Tonality": row["key"],
        "AverageBpm": row["bpm"],
        "Location": quote("file://localhost/" + final_location),
        "SampleRate": row["samplerate"],
        "Rating": RATING_MAPING[row["rating"]],
    }
    return get_elem("TRACK", attrib)


def mixxx_cue_to_rekordbox_cue(mixxx_position: float, samplerate: float) -> float:
    return mixxx_position / samplerate / 2


def mixxx_cue_row_to_rekbox_xml(
    row: pd.Series, samplerate: float, offset_ms: float
) -> Generator[ET.Element, None, None]:
    cue_nums = [-1]
    if params["keep_hot_cues"]:
        cue_nums.append(row["hotcue"])
    for cnum in cue_nums:
        attrib: AttribDict = {
            "Type": "0",
            "Num": cnum,
            "Start": mixxx_cue_to_rekordbox_cue(row["position"], samplerate)
            + offset_ms / 1000,
        }
        yield get_elem("POSITION_MARK", attrib)


def mixxx_playlist_to_rekordbox_xml(row: pd.Series, track_numbers: int) -> ET.Element:
    attrib: AttribDict = {
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
    # reading the config file
    config_file = Path(__file__).parent / Path("config.ini")
    config = configparser.ConfigParser()
    config.read(config_file)
    params = config["Default"]

    ans = print(f"The following parameters are defined in {config_file}")
    for k, v in params.items():
        print(f"  {k}: {v}")
    ans = input("Are you OK with that (y/*)? ")
    if ans != "y":
        exit()

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

    for _, track_row in tqdm(df_merge.iterrows(), total=len(df_merge)):
        track_xml = mixxx_track_row_to_rekbox_track_xml(track_row)
        track_cues = mixxx_cues[mixxx_cues["track_id"] == track_row["id_x"]]
        rate = track_xml.get("SampleRate")
        export_offset_ms = get_offset_ms(track_row["location_y"], params["mp3_decoder"])
        for _, cue_row in track_cues.iterrows():
            assert rate
            frate = float(rate)
            for cue_xml in mixxx_cue_row_to_rekbox_xml(
                cue_row, frate, export_offset_ms
            ):
                track_xml.append(cue_xml)
        if (
            track_row["beats_version"] == "BeatGrid-2.0"
        ):  # do we allow other versions of BeatGrid ?
            tempo_xml = mixxx_track_row_to_rekbox_tempo_xml(
                track_row, int(params["beats_per_bar"])
            )
            track_xml.append(tempo_xml)
        collection_xml.append(track_xml)

    # playlists
    mixxx_playlists = open_mixxx_playlists(filter_hidden=True)
    mixxx_playlist_tracks = open_mixxx_playlist_tracks()
    playlists_xml = get_playlists_xml()
    node_xml = get_node_xml(len(mixxx_playlists))
    for _, pls_row in mixxx_playlists.iterrows():
        pls_tracks = mixxx_playlist_tracks[
            mixxx_playlist_tracks["playlist_id"] == pls_row["id"]
        ].sort_values("position")
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

    rek_fil = params["rekordbox_xml_file"]
    with open(rek_fil, "w") as fxml:
        fxml.write('<?xml version="1.0" encoding="UTF-8"?>')
    tree.write(rek_fil, encoding="unicode")

    print(f"==> {rek_fil}")
