from sys import path, exit
from typing import Optional, Generator, Mapping
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree as ET

import pandas as pd
from tqdm import tqdm

from encoder_tools import get_offset_ms

import config as cfg

path.append(Path(__file__).parent.parent.as_posix())  # ugly tricks but works fine :-p

from utils.music_db_utils import (
    open_mixxx_library,
    open_mixxx_cues,
    open_mixxx_track_locations,
    open_mixxx_playlists,
    open_mixxx_playlist_tracks,
)

from utils.track_utils import BeatGridInfo, position_frame_to_sec, guess_inizio_sec

from utils.misc import confirm_config

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


def mixxx_track_and_cue_rows_to_rekbox_tempo_xml(
    track_row: pd.Series, cue_rows: pd.DataFrame, offset_ms: float
) -> ET.Element:
    bpm = track_row["bpm"]
    if (
        cfg.index_cue_bar_start <= 0
        or cfg.index_cue_bar_start - 1 not in cue_rows["hotcue"]
    ):
        beatgrid_info = BeatGridInfo(track_row)
        inizio = beatgrid_info.start_sec
    else:
        cue_point = cue_rows[cfg.index_cue_bar_start - 1 == cue_rows["hotcue"]]
        assert len(cue_point) == 1
        inizio = guess_inizio_sec(
            cue_point["postion"], track_row["samplerate"], bpm, cfg.beats_per_bar
        )

    attrib: AttribDict = {
        "Inizio": inizio + offset_ms / 1000,
        "Bpm": bpm,
        "Metro": f"{cfg.beats_per_bar}/{cfg.beats_per_bar}",
        "Battito": "1",
    }
    return get_elem("TEMPO", attrib)


def mixxx_track_row_to_rekbox_track_xml(track_row: pd.Series) -> ET.Element:
    location = track_row["location_y"]
    final_location = location.replace(cfg.original_mount_point, cfg.final_mount_point)
    attrib: AttribDict = {
        "TrackID": track_row["id_x"],
        "Name": track_row["title"],
        "Artist": track_row["artist"],
        "Album": track_row["album"],
        "TrackNumber": track_row["tracknumber"],
        "Genre": track_row["genre"],
        "TotalTime": round(track_row["duration"]),
        "Tonality": track_row["key"],
        "AverageBpm": track_row["bpm"],
        "Location": quote("file://localhost/" + final_location),
        "SampleRate": track_row["samplerate"],
        "Rating": RATING_MAPING[track_row["rating"]],
    }
    return get_elem("TRACK", attrib)


def mixxx_cue_row_to_rekbox_xml(
    cue_row: pd.Series, samplerate: float, offset_ms: float
) -> Generator[ET.Element, None, None]:
    cue_nums = [-1]
    if cfg.keep_hot_cues:
        cue_nums.append(cue_row["hotcue"])
    for cnum in cue_nums:
        attrib: AttribDict = {
            "Type": "0",
            "Num": cnum,
            "Start": position_frame_to_sec(cue_row["position"], samplerate)
            + offset_ms / 1000,
        }
        yield get_elem("POSITION_MARK", attrib)


def mixxx_playlist_to_rekordbox_xml(
    pls_row: pd.Series, track_numbers: int
) -> ET.Element:
    attrib: AttribDict = {
        "Name": pls_row["name"],
        "Type": "1",
        "KeyType": "0",
        " Entries": track_numbers,
    }
    return get_elem("NODE", attrib)


def mixxx_playlist_track_to_rekordbox_xml(pls_trk_row: pd.Series) -> ET.Element:
    attrib = {"Key": pls_trk_row["track_id"]}
    return get_elem("TRACK", attrib)


if __name__ == "__main__":
    confirm_config(cfg)

    if cfg.index_cue_bar_start != 0:
        print(
            f"The hot cue #{cfg.index_cue_bar_start} will be used to detect the start of the bars."
        )
        answer = input(
            "Are you sure all these hot cues are snapped to the beatgrid (y/*)? : "
        )
        if answer != "y":
            exit(2)
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
        export_offset_ms = get_offset_ms(track_row["location_y"], cfg.mp3_decoder)
        for _, cue_row in track_cues.iterrows():
            assert rate
            frate = float(rate)
            for cue_xml in mixxx_cue_row_to_rekbox_xml(
                cue_row, frate, export_offset_ms
            ):
                track_xml.append(cue_xml)
        if track_row["beats_version"] == "BeatGrid-2.0":
            # do we allow other versions of BeatGrid ?
            tempo_xml = mixxx_track_and_cue_rows_to_rekbox_tempo_xml(
                track_row, track_cues, export_offset_ms
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

    rek_fil = cfg.rekordbox_xml_file
    with open(rek_fil, "w") as fxml:
        fxml.write('<?xml version="1.0" encoding="UTF-8"?>')
    tree.write(rek_fil, encoding="unicode")

    print(f"==> {rek_fil}")
