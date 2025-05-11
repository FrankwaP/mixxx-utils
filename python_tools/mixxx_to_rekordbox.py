import logging
import sys
from pathlib import Path
from shutil import copyfile
from typing import Generator
from urllib.parse import quote
from xml.etree import ElementTree as ET

import mixxx_to_rekordbox_utils.config as cfg
import pandas as pd
from mixxx_to_rekordbox_utils.encoder_tools import get_offset_ms
from mixxx_to_rekordbox_utils.xml_utils import AttribDict
from mixxx_to_rekordbox_utils.xml_utils import get_elem
from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm
from utils.key_utils import key_id_to_lancelot
from utils.misc import confirm_config
from utils.music_db_utils import open_mixxx_cues
from utils.music_db_utils import open_mixxx_library
from utils.music_db_utils import open_mixxx_playlists_with_tracks
from utils.music_db_utils import open_mixxx_track_locations
from utils.track_utils import BeatGridInfo
from utils.track_utils import guess_inizio_sec
from utils.track_utils import position_frame_to_sec


# 0 star = "0", 1 star = "51", 2 stars = "102", 3 stars = "153", 4 stars = "204", 5 stars = "255"
RATING_MAPING = {0: 0, 1: 51, 2: 102, 3: 153, 4: 204, 5: 255}
SUFFIX_LIB = "_lib"
SUFFIX_LOC = "_loc"


def is_non_empty_string(s: str) -> bool:
    return isinstance(s, str) and s.replace(" ", "") != ""


def get_root_xml() -> ET.Element:
    root = get_elem("DJ_PLAYLISTS", {"Version": "1.0.0"})
    attrib = {"Name": "rekordbox", "Version": "6.7.7", "Company": "AlphaTheta"}
    root.append(get_elem("PRODUCT", attrib))
    return root


def get_collection_xml(nb_tracks: int) -> ET.Element:
    assert isinstance(nb_tracks, int)
    attrib = {"Entries": nb_tracks}
    return get_elem("COLLECTION", attrib)


def get_playlists_xml() -> ET.Element:
    return get_elem("PLAYLISTS")


def get_node_xml(nb_pls: int) -> ET.Element:
    assert isinstance(nb_pls, int)
    attrib = {"Type": 0, "Name": "ROOT", "Count": nb_pls}
    return get_elem("NODE", attrib)


def mixxx_track_and_cue_rows_to_rekbox_tempo_xml(
    trk_row: pd.Series,
    cue_rows: pd.DataFrame,
    offset_start_beatgrid_ms: int,
) -> ET.Element:
    assert isinstance(offset_start_beatgrid_ms, int)
    bpm = trk_row["bpm"]
    assert isinstance(bpm, float)
    if (
        cfg.index_cue_bar_start <= 0
        or cfg.index_cue_bar_start - 1 not in cue_rows["hotcue"].values
    ):
        beatgrid_info = BeatGridInfo(trk_row)
        inizio = beatgrid_info.start_sec
    else:
        cue_point = cue_rows[cfg.index_cue_bar_start - 1 == cue_rows["hotcue"]]
        assert len(cue_point) == 1
        inizio = guess_inizio_sec(
            cue_point.iloc[0]["position"],
            trk_row["samplerate"],
            bpm,
            cfg.beats_per_bar,
        )

    attrib: AttribDict = {
        "Inizio": inizio + offset_start_beatgrid_ms / 1000,
        "Bpm": bpm,
        "Metro": f"{cfg.beats_per_bar}/{cfg.beats_per_bar}",
        "Battito": "1",
    }
    return get_elem("TEMPO", attrib)


def mixxx_track_row_to_rekbox_track_xml(trk_row: pd.Series) -> ET.Element:
    location = trk_row["location" + SUFFIX_LOC]
    final_location = location.replace(
        cfg.mixxx_library_folder, cfg.rekordbox_library_folder
    )
    if cfg.rekordbox_library_folder not in final_location:
        logging.warning("This track is not in the Mixxx library folder:", location)

    if not is_non_empty_string(trk_row["artist"]):
        logging.warning("Artist name is empty for file: %s", location)
    if not is_non_empty_string(trk_row["title"]):
        logging.warning("Track name is empty for file: %s", location)
    if not (isinstance(trk_row["bpm"], float) and trk_row["bpm"] > 50.0):
        logging.warning("Incorrect BPM for file: %s", location)
    if not (isinstance(trk_row["key_id"], int) and trk_row["key_id"] > 0):
        logging.warning("Incorrect key id for file: %s", location)

    attrib: AttribDict = {
        "TrackID": trk_row["id" + SUFFIX_LIB],
        "Name": trk_row["title"],
        "Artist": trk_row["artist"],
        "Album": trk_row["album"],
        "TrackNumber": trk_row["tracknumber"],
        "Genre": trk_row["genre"],
        "TotalTime": round(trk_row["duration"]),
        "Tonality": key_id_to_lancelot(trk_row["key_id"]),
        "AverageBpm": trk_row["bpm"],
        "Location": quote("file://localhost/" + final_location),
        "SampleRate": trk_row["samplerate"],
        "Rating": RATING_MAPING[trk_row["rating"]],
    }
    return get_elem("TRACK", attrib)


def mixxx_cue_row_to_rekbox_xml(
    cue_row_: pd.Series, samplerate: float, offset_ms: int
) -> Generator[ET.Element, None, None]:
    assert isinstance(samplerate, float)
    assert isinstance(offset_ms, int)
    # -1 is to create a memory cue
    cue_nums = [-1, cue_row_["hotcue"]]
    for cnum in cue_nums:
        attrib: AttribDict = {
            "Type": "0",
            "Num": cnum,
            "Start": position_frame_to_sec(cue_row_["position"], samplerate)
            + offset_ms / 1000,
        }
        yield get_elem("POSITION_MARK", attrib)


def mixxx_playlist_to_rekordbox_xml(
    plst_row: pd.Series, track_numbers: int
) -> ET.Element:
    assert isinstance(track_numbers, int)
    attrib: AttribDict = {
        "Name": plst_row["name"],
        "Type": "1",
        "KeyType": "0",
        "Entries": track_numbers,
    }
    return get_elem("NODE", attrib)


def mixxx_playlist_track_to_rekordbox_xml(pls_trk_row: pd.Series) -> ET.Element:
    attrib = {"Key": pls_trk_row["track_id"]}
    return get_elem("TRACK", attrib)


if __name__ == "__main__":
    # %% checking the config
    confirm_config(cfg)

    if cfg.index_cue_bar_start != 0:
        print(
            f"The hot cue #{cfg.index_cue_bar_start} will be used to detect the start of the bars."
        )
        answer = input(
            "Are you sure all these hot cues are snapped to the beatgrid (y/*)? : "
        )
        if answer != "y":
            sys.exit(2)

    # %% opening/filtering

    df_lib = open_mixxx_library(missing_tracks=False)
    df_trk_loc = open_mixxx_track_locations()
    df_cues = open_mixxx_cues(only_hot_cues=True)

    df_pls, df_pls_trk = open_mixxx_playlists_with_tracks(
        filter_hidden=True,
        add_crates_as_playlist=cfg.add_crates_as_playlist,
        crate_suffix=cfg.crates_suffix,
    )
    if cfg.export_only_tracks_in_playlists:
        df_lib = df_lib[df_lib["id"].isin(df_pls_trk["track_id"])]

    # the rest of the filtering is done with the merging

    # %% Writing the XML file
    print("Writing the XML file")

    # %%% tracks and cues => collection XML
    df_merge_lib_loc = pd.merge(
        left=df_lib,
        right=df_trk_loc,
        left_on="location",
        right_on="id",
        suffixes=(SUFFIX_LIB, SUFFIX_LOC),
    )

    collection_xml = get_collection_xml(len(df_merge_lib_loc))
    with logging_redirect_tqdm():
        for _, track_row in tqdm(
            df_merge_lib_loc.iterrows(), total=len(df_merge_lib_loc)
        ):
            track_xml = mixxx_track_row_to_rekbox_track_xml(track_row)
            track_cues = df_cues[df_cues["track_id"] == track_row["id" + SUFFIX_LIB]]
            rate = track_row["samplerate"]
            export_offset_ms = get_offset_ms(
                track_row["location" + SUFFIX_LOC], cfg.mp3_decoder
            )
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

    # %%% playlists => playlist XML
    playlists_xml = get_playlists_xml()

    node_xml = get_node_xml(len(df_pls))

    for _, pls_row in df_pls.sort_values("name").iterrows():
        pls_tracks = df_pls_trk[df_pls_trk["playlist_id"] == pls_row["id"]].sort_values(
            "position"
        )
        playlist_node_xml = mixxx_playlist_to_rekordbox_xml(pls_row, len(pls_tracks))
        for _, pls_track_row in pls_tracks.iterrows():
            playlist_node_xml.append(
                mixxx_playlist_track_to_rekordbox_xml(pls_track_row)
            )
        node_xml.append(playlist_node_xml)
    playlists_xml.append(node_xml)

    # %%% final XML structure
    root_xml = get_root_xml()
    root_xml.append(collection_xml)
    root_xml.append(playlists_xml)

    tree = ET.ElementTree(element=root_xml)
    ET.indent(tree, space="  ", level=0)

    rek_fil = Path(cfg.mixxx_library_folder, cfg.rekordbox_xml_file)
    with open(rek_fil, "w", encoding="utf-8") as fxml:
        fxml.write('<?xml version="1.0" encoding="UTF-8"?>')
    tree.write(rek_fil, encoding="unicode")

    print(f"==> {rek_fil}")
