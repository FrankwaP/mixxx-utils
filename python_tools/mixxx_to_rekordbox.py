import logging
import re
import sys
from pathlib import Path
from typing import Generator

from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm
import pandas as pd
from urllib.parse import quote
from xml.etree import ElementTree as ET


from python_tools.mixxx_to_rekordbox_utils.encoder_tools import get_offset_ms
from python_tools.mixxx_to_rekordbox_utils.color_tools import (
    convert_colors_for_rekordbox,
)
from python_tools.mixxx_to_rekordbox_utils.xml_utils import (
    AttribDict,
    get_elem,
)
from python_tools.utils.misc import (
    RATING_MAPING,
    KEY_ID_LANCELOT,
)
from python_tools.utils.music_db_utils import (
    open_mixxx_cues,
    open_mixxx_library,
    open_mixxx_playlists_with_tracks,
    open_mixxx_track_locations,
)
from python_tools.utils.track_utils import (
    BeatGridInfo,
    guess_inizio_sec,
    position_frame_to_sec,
)

from python_tools import CONFIG

logging.basicConfig(level=logging.INFO)

CFG = CONFIG.mixxx_to_rekordbox
SUFFIX_LIB = "_lib"
SUFFIX_LOC = "_loc"
RKBOX_COLOR = "rkbox_color"
NOT_ALLOWED = "ogg", "opus"


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


def get_time_signature_in_comment(trk_row: pd.Series) -> str:
    # NOTE: the denominator is not used
    if not isinstance(trk_row["comment"], str):
        return f"{CFG.beats_per_bar}/4"
    match = re.findall(r"\b\d+/\d\b", trk_row["comment"])
    if len(match) == 0:
        return f"{CFG.beats_per_bar}/4"
    location = Path(trk_row["location" + SUFFIX_LOC])
    if len(match) > 1:
        logging.warning(
            "More than one time signature candidates have been found in the comments of file %s.",
            location,
        )
    logging.info(
        "Time signature %s has been found in the comment of file %s.",
        match[0],
        location,
    )
    return match[0]


def mixxx_track_and_cue_rows_to_rekbox_tempo_xml(
    trk_row: pd.Series,
    cue_rows: pd.DataFrame,
    offset_start_beatgrid_ms: int,
) -> ET.Element:
    assert isinstance(offset_start_beatgrid_ms, int)
    bpm = trk_row["bpm"]
    assert isinstance(bpm, float)
    if (
        CFG.index_cue_bar_start <= 0
        or CFG.index_cue_bar_start - 1 not in cue_rows["hotcue"].values
    ):
        beatgrid_info = BeatGridInfo(trk_row)
        inizio = beatgrid_info.start_sec
    else:
        cue_point = cue_rows[CFG.index_cue_bar_start - 1 == cue_rows["hotcue"]]
        if len(cue_point) != 1:
            logging.warning(
                "More than one hotcue #%d has been found for file %s\n.",
                "The first one has been kept to decide the start of the bars"
                "… but you might want to re-create it!",
                CFG.index_cue_bar_start,
                trk_row["location"],
            )
            cue_point = cue_point[0]
        inizio = guess_inizio_sec(
            cue_point.iloc[0]["position"],
            trk_row["samplerate"],
            bpm,
            CFG.beats_per_bar,
        )
        inizio += offset_start_beatgrid_ms / 1000

    attrib: AttribDict = {
        "Inizio": f"{inizio:.3f}",
        "Bpm": f"{bpm:.2f}",
        "Metro": get_time_signature_in_comment(trk_row),
        "Battito": "1",  # NOTE: means "1st beat of the bar" (not "1 beat per bar")
    }
    return get_elem("TEMPO", attrib)


def mixxx_track_row_to_rekbox_track_xml(trk_row: pd.Series) -> ET.Element:
    location = Path(trk_row["location" + SUFFIX_LOC])
    if not location.is_relative_to(CFG.mixxx_library_folder):
        logging.warning("This track is not in the Mixxx library folder: %s", location)
    final_location = CFG.rekordbox_library_folder / location.relative_to(
        CFG.mixxx_library_folder
    )

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
        "TrackID": trk_row["id" + SUFFIX_LIB],
        "Name": trk_row["title"],
        "Artist": trk_row["artist"],
        "Composer": trk_row["composer"],
        "Album": trk_row["album"],
        # Grouping
        "Genre": trk_row["genre"],
        "Kind": trk_row["filetype"],
        "Size": trk_row["filesize"],
        "TotalTime": round(trk_row["duration"]),
        # DiscNumber
        "TrackNumber": trk_row["tracknumber"],
        "Year": trk_row["year"],
        "AverageBpm": trk_row["bpm"],
        # DateModified
        # DateAdded
        "BitRate": trk_row["bitrate"],
        "SampleRate": trk_row["samplerate"],
        "Comment": trk_row["comment"],
        # PlayCount
        # LastPlayed
        "Rating": RATING_MAPING[trk_row["rating"]],
        "Location": quote("file://localhost/" + str(final_location)),
        # Remixer
        "Tonality": tonality,
        # Label
        # Mix
        "Colour": trk_row[RKBOX_COLOR],
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
        start = (
            position_frame_to_sec(cue_row_["position"], samplerate) + offset_ms / 1000
        )
        if start < 0:
            # RkBox does not import negative cue position
            logging.info(
                "A negative cue start position has been found and ignored for cue %s",
                cue_row_["id"],
            )
        else:
            attrib: AttribDict = {
                "Type": "0",
                "Num": cnum,
                "Start": f"{start:.3f}",
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


def mixxx_playlist_track_to_rekordbox_xml(
    pls_trk_row: pd.Series,
) -> ET.Element:
    attrib = {"Key": pls_trk_row["track_id"]}
    return get_elem("TRACK", attrib)


def main():

    # %% checking the config
    if CFG.index_cue_bar_start != 0:
        answer = input(
            "Are you sure all these hot cues are snapped to the beatgrid (y/*)? : "
        )
        if answer != "y":
            sys.exit(2)

    # %% opening/filtering
    df_lib = open_mixxx_library(missing_tracks=False)
    idx_not_allowed = df_lib["filetype"].isin(NOT_ALLOWED)
    if any(idx_not_allowed):
        filestypes = df_lib[idx_not_allowed]["filetype"].unique().tolist()
        logging.warning(
            "Files with incorrect filetypes %s have been found and removed.", filestypes
        )
    df_lib = df_lib[~idx_not_allowed]
    df_trk_loc = open_mixxx_track_locations()
    df_cues = open_mixxx_cues(only_hot_cues=True)
    df_pls, df_pls_trk = open_mixxx_playlists_with_tracks(
        filter_hidden=True,
        add_crates_as_playlist=CFG.add_crates_as_playlist,
        crate_suffix=CFG.crates_suffix,
    )
    if CFG.export_only_tracks_in_playlists:
        df_lib = df_lib[df_lib["id"].isin(df_pls_trk["track_id"])]

    # Filter out tracks with "STEM" in comments
    df_nostem = df_lib[~df_lib["comment"].str.contains("STEM", case=False, na=False)]
    print(f"Filtered out {len(df_lib)-len(df_nostem)} tracks with STEM in comments")
    df_lib = df_nostem

    # Convert the colors
    df_lib.loc[:, RKBOX_COLOR] = convert_colors_for_rekordbox(df_lib.loc[:, "color"])

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
                track_row["location" + SUFFIX_LOC], CFG.mp3_decoder
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

    rek_fil = Path(CFG.mixxx_library_folder, CFG.mixxx_to_rekordbox_xml)
    tree.write(rek_fil, encoding="utf-8", xml_declaration=True)

    print(f"==> {rek_fil}")
