import re
import sys
from collections.abc import Generator
from pathlib import Path
from typing import Any
from urllib.parse import quote
from xml.etree import ElementTree as ET

from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

from .mixxx_to_rekordbox_utils.encoder_tools import get_offset_ms
from .mixxx_to_rekordbox_utils.xml_utils import AttribDict, get_elem
from .utils.config import MixxxToRekordboxConfig, get_mixxx_to_rekordbox_config, logger
from .utils.dataclasses_operations_utils import (
    filter_left_using_right,
    get_match_key,
    pseudo_inner_join_left_to_right_mapping,
    pseudo_inner_join_product,
)
from .utils.dataclasses_utils import (
    CuesRow,
    LibraryRow,
    PlaylistRow,
    PlaylistTrackRow,
    Table,
    TrackLocationsRow,
)
from .utils.misc import KEY_ID_LANCELOT, RATING_MAPING
from .utils.music_db_utils_no_pandas import (
    open_mixxx_cues,
    open_mixxx_library,
    open_mixxx_playlists_with_tracks,
    open_mixxx_track_locations,
)
from .utils.track_utils import BeatGridInfo

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


def _convert_color_for_rekordbox(color: Any) -> str:
    if color is None:
        return ""
    assert isinstance(color, int)
    rgb = ((color >> 16) & 255, (color >> 8) & 255, color & 255)
    nearest = min(
        REKORDBOX_COLORS,
        key=lambda palette_rgb: sum(
            (left - right) ** 2 for left, right in zip(palette_rgb, rgb)
        ),
    )
    return REKORDBOX_COLORS[nearest]


def _get_root_xml() -> ET.Element:
    root = get_elem("DJ_PLAYLISTS", {"Version": "1.0.0"})
    attrib = {"Name": "rekordbox", "Version": "6.7.7", "Company": "AlphaTheta"}
    root.append(get_elem("PRODUCT", attrib))
    return root


def _get_collection_xml(nb_tracks: int) -> ET.Element:
    attrib = {"Entries": nb_tracks}
    return get_elem("COLLECTION", attrib)


def _get_playlists_xml() -> ET.Element:
    return get_elem("PLAYLISTS")


def _get_node_xml(nb_pls: int) -> ET.Element:
    attrib = {"Type": 0, "Name": "ROOT", "Count": nb_pls}
    return get_elem("NODE", attrib)


def _get_time_signature_in_comment(
    trk_row: LibraryRow,
    track_location: TrackLocationsRow,
    config: MixxxToRekordboxConfig,
) -> str:
    # NOTE: the denominator is not used
    if not isinstance(trk_row.comment, str):
        return f"{config.beats_per_bar}/4"
    match = re.findall(r"\b\d+/\d\b", trk_row.comment)
    if len(match) == 0:
        return f"{config.beats_per_bar}/4"
    location = Path(track_location.location).resolve()
    if len(match) > 1:
        logger.warning(
            "More than one time signature candidates have been found in the "
            "comments of file %s (%s).",
            location,
            trk_row.comment,
        )
    logger.info(
        "Time signature %s has been found in the comment of file %s.",
        match[0],
        location,
    )
    return match[0]


def _position_frame_to_sec(frame: int | float, samplerate: float) -> float:
    assert isinstance(frame, (int, float)), frame
    assert isinstance(samplerate, float), samplerate
    return frame / (2 * samplerate)


def _guess_inizio_from_hotcue(
    hot_cue_frame_pos: int | float, samplerate: float, bpm: float, beats_per_bar: int
) -> float:
    assert isinstance(bpm, float)
    assert isinstance(beats_per_bar, int)
    hot_cue_sec = _position_frame_to_sec(hot_cue_frame_pos, samplerate)
    interval_sec = 60 / bpm
    return hot_cue_sec % (beats_per_bar * interval_sec)


def _beatgrid_inizio(track_row: LibraryRow) -> float:
    beat_info = BeatGridInfo(track_row)
    return beat_info.start_sec


def _get_inizio(
    trk_row: LibraryRow,
    track_location: TrackLocationsRow,
    cue_rows: Table[CuesRow],
    offset_ms: int,
    config: MixxxToRekordboxConfig,
) -> float | None:
    # we fisrt try to use config.index_cue_bar_start so we can
    # have the start of the bars
    if config.index_cue_bar_start > 0:
        hotcue_bar_index = config.index_cue_bar_start - 1
        matching_cues = [
            cue_row for cue_row in cue_rows if cue_row.hotcue == hotcue_bar_index
        ]
        if not matching_cues:
            logger.warning(
                "No hotcue #%d been found for file %s to find the start of the bars.",
                config.index_cue_bar_start,
                track_location.location,
            )
        else:
            if len(matching_cues) > 1:
                logger.warning(
                    "More than one hotcue #%d has been found for file %s. "
                    "The first one has been kept to decide the start of the bars"
                    "… but you might want to re-create it!",
                    config.index_cue_bar_start,
                    track_location.location,
                )
            cue_row = matching_cues[0]
            if trk_row.samplerate is None or trk_row.bpm is None:
                raise TypeError("Samplerate and BPM are required to read hotcue timing")
            return (
                _guess_inizio_from_hotcue(
                    cue_row.position,
                    float(trk_row.samplerate),
                    float(trk_row.bpm),
                    config.beats_per_bar,
                )
                + offset_ms / 1000
            )
    # we can maybe have the start of the grid
    if trk_row.beats is not None:
        return _beatgrid_inizio(trk_row)

    return None


def _mixxx_track_and_cue_rows_to_rekbox_tempo_xml(
    trk_row: LibraryRow,
    track_location: TrackLocationsRow,
    cue_rows: Table[CuesRow],
    offset_ms: int,
    config: MixxxToRekordboxConfig,
) -> ET.Element:

    if trk_row.bpm is None:
        raise TypeError("BPM is required to write tempo XML")
    bpm = float(trk_row.bpm)
    inizio = _get_inizio(trk_row, track_location, cue_rows, offset_ms, config)

    attrib: AttribDict = {
        "Bpm": f"{bpm:.2f}",
        "Metro": _get_time_signature_in_comment(trk_row, track_location, config),
        "Battito": "1",  # NOTE: means "1st beat of the bar" (not "1 beat per bar")
    }
    if inizio is not None:
        attrib["Inizio"] = f"{inizio:.3f}"
    return get_elem("TEMPO", attrib)


def _is_non_empty_string(s: str | None) -> bool:
    return isinstance(s, str) and s.strip() != ""


def _mixxx_track_row_to_rekbox_track_xml(
    trk_row: LibraryRow,
    track_location: TrackLocationsRow,
    config: MixxxToRekordboxConfig,
) -> ET.Element:
    location = Path(track_location.location).resolve()
    try:
        final_location = config.rekordbox_library_folder / location.relative_to(
            config.mixxx_library_folder
        )
    except ValueError as err:
        logger.warning("This track is not in the Mixxx library folder: %s", location)
        raise err

    if not _is_non_empty_string(trk_row.artist):
        logger.warning("Artist name is empty for file: %s", location)
    if not _is_non_empty_string(trk_row.title):
        logger.warning("Track name is empty for file: %s", location)
    if not (isinstance(trk_row.bpm, float) and trk_row.bpm > 50.0):
        logger.warning("Incorrect BPM for file: %s", location)

    try:
        if trk_row.key_id is None:
            raise KeyError(trk_row.key_id)
        tonality = KEY_ID_LANCELOT[trk_row.key_id]
    except KeyError:
        logger.warning("Incorrect key id for file: %s", location)
        tonality = ""

    if trk_row.duration is None:
        raise TypeError("Duration is required to write track XML")
    if trk_row.rating is None:
        raise KeyError(trk_row.rating)

    attrib: AttribDict = {
        "TrackID": trk_row.id,
        "Name": trk_row.title,
        "Artist": trk_row.artist,
        "Composer": trk_row.composer,
        "Album": trk_row.album,
        "Genre": trk_row.genre,
        "Size": track_location.filesize,
        # TotalTime is mandatory for cue points to work !!!
        "TotalTime": round(trk_row.duration),
        "TrackNumber": trk_row.tracknumber,
        "Year": trk_row.year,
        "AverageBpm": trk_row.bpm,
        "SampleRate": trk_row.samplerate,
        "Comment": trk_row.comment,
        "Rating": RATING_MAPING[trk_row.rating],
        "Location": quote("file://localhost/" + str(final_location)),
        "Tonality": tonality,
        "Colour": _convert_color_for_rekordbox(trk_row.color),
    }

    return get_elem("TRACK", attrib)


def _mixxx_cue_row_to_rekbox_xml(
    track_row: LibraryRow,
    track_location: TrackLocationsRow,
    cue_row_: CuesRow,
    offset_ms: int,
) -> Generator[ET.Element, None, None]:
    if track_row.samplerate is None:
        raise TypeError("Samplerate is required to write cue XML")
    start = (
        _position_frame_to_sec(cue_row_.position, float(track_row.samplerate))
        + offset_ms / 1000
    )
    if start < 0:
        logger.info(
            "Negative cue start position ignored for hotcue #%d of file %s",
            cue_row_.hotcue + 1,
            track_location.location,
        )
    else:
        cue_nums = [-1, cue_row_.hotcue]
        for cnum in cue_nums:
            attrib: AttribDict = {
                "Type": "0",
                "Num": cnum,
                "Start": f"{start:.3f}",
            }
            yield get_elem("POSITION_MARK", attrib)


def _mixxx_playlist_to_rekordbox_xml(
    plst_row: PlaylistRow, track_numbers: int
) -> ET.Element:
    attrib: AttribDict = {
        "Name": plst_row.name,
        "Type": "1",
        "KeyType": "0",
        "Entries": track_numbers,
    }
    return get_elem("NODE", attrib)


def _mixxx_playlist_track_to_rekordbox_xml(
    pls_trk_row: PlaylistTrackRow,
) -> ET.Element:
    attrib = {"Key": pls_trk_row.track_id}
    return get_elem("TRACK", attrib)


def _filter_filetypes(rows: Table[LibraryRow]) -> Table[LibraryRow]:
    out = Table(r for r in rows if r.filetype not in NOT_ALLOWED)
    diff = len(rows) - len(out)
    if diff:
        logger.info(
            "Filtered out %d tracks with unallowed %s extensions",
            diff,
            str(NOT_ALLOWED),
        )
    return out


def _filter_locked_tracks(rows: Table[LibraryRow]) -> Table[LibraryRow]:
    out = Table(r for r in rows if r.bpm_lock == 1)
    diff = len(rows) - len(out)
    if diff:
        logger.info("Filtered out %d tracks with unlocked beatgrids", diff)
    return out


def _filter_only_in_playlist(
    rows_lib: Table[LibraryRow], rows_plst_trks: Table[PlaylistTrackRow]
) -> Table[LibraryRow]:
    out_lib = filter_left_using_right(
        rows_lib, rows_plst_trks, on_left=("id",), on_right=("track_id",)
    )
    diff = len(rows_lib) - len(out_lib)
    if diff:
        logger.info("Filtered out %d tracks not in playlists", diff)
    return out_lib


def main() -> None:
    mtr_config = get_mixxx_to_rekordbox_config()
    db_path = mtr_config.mixxx_db

    if mtr_config.confirm_snaped and mtr_config.index_cue_bar_start != 0:
        answer = input(
            "Are you sure all these hot cues are snapped to the beatgrid (y/*)? : "
        )
        if answer != "y":
            sys.exit(2)

    #
    lib = open_mixxx_library(db_path, quit_if_duplicates=False)
    lib = _filter_filetypes(lib)
    if mtr_config.export_only_locked_tracks:
        lib = _filter_locked_tracks(lib)
    #
    loc = open_mixxx_track_locations(
        db_path, existing_tracks=True, missing_tracks=False
    )
    #
    cues = open_mixxx_cues(db_path, only_hot_cues=True)
    plst, plst_trks = open_mixxx_playlists_with_tracks(
        db_path,
        filter_hidden=True,
        add_crates_as_playlist=mtr_config.add_crates_as_playlist,
        crate_suffix=mtr_config.crates_suffix,
    )
    #
    if mtr_config.export_only_tracks_in_playlists:
        # we do this one first as the "_filter_only_exist" return mateched
        lib = _filter_only_in_playlist(lib, plst_trks)

    lib, loc = pseudo_inner_join_product(
        lib,
        loc,
        on_left=("location",),
        on_right=("id",),
        assert_unique_left=True,
        assert_unique_right=True,
    )

    lib_key_to_cues_map = pseudo_inner_join_left_to_right_mapping(
        lib, cues, on_left=("id",), on_right=("track_id",)
    )

    logger.info("Writing the tracks in the XML file")
    collection_xml = _get_collection_xml(len(lib))
    with logging_redirect_tqdm():
        for lib_row, loc_row in tqdm(zip(lib, loc), total=len(lib)):
            try:
                track_xml = _mixxx_track_row_to_rekbox_track_xml(
                    lib_row, loc_row, mtr_config
                )
            except ValueError:
                continue

            # cues
            lib_key = get_match_key(lib_row, on=("id",))
            track_cues = lib_key_to_cues_map.get(lib_key, Table())
            if track_cues:
                export_offset_ms = get_offset_ms(
                    loc_row.location, mtr_config.mp3_decoder
                )
                for cue_row in track_cues:
                    for cue_xml in _mixxx_cue_row_to_rekbox_xml(
                        lib_row, loc_row, cue_row, export_offset_ms
                    ):
                        track_xml.append(cue_xml)
            # tempo
            if isinstance(lib_row.bpm, float):
                tempo_xml = _mixxx_track_and_cue_rows_to_rekbox_tempo_xml(
                    lib_row,
                    loc_row,
                    track_cues,
                    export_offset_ms,
                    mtr_config,
                )
                track_xml.append(tempo_xml)
            collection_xml.append(track_xml)

    logger.info("Writing the playlists in the XML file")

    playlists_xml = _get_playlists_xml()
    node_xml = _get_node_xml(len(plst))

    plst_to_plst_trk_map = pseudo_inner_join_left_to_right_mapping(
        plst, plst_trks, on_left=("id",), on_right=("playlist_id",)
    )

    for plst_row in sorted(plst, key=lambda row: row.name):
        plst_key = get_match_key(plst_row, on=("id",))
        plst_trks = plst_to_plst_trk_map.get(plst_key, Table())
        playlist_node_xml = _mixxx_playlist_to_rekordbox_xml(plst_row, len(plst_trks))
        for plst_trks_row in sorted(plst_trks, key=lambda x: x.position):
            playlist_node_xml.append(
                _mixxx_playlist_track_to_rekordbox_xml(plst_trks_row)
            )
        node_xml.append(playlist_node_xml)
    playlists_xml.append(node_xml)

    root_xml = _get_root_xml()
    root_xml.append(collection_xml)
    root_xml.append(playlists_xml)

    tree = ET.ElementTree(element=root_xml)
    ET.indent(tree, space="  ", level=0)

    rekordbox_file = Path(
        mtr_config.mixxx_library_folder, mtr_config.mixxx_to_rekordbox_xml
    )
    tree.write(rekordbox_file, encoding="utf-8", xml_declaration=True)

    logger.info("==> %s", rekordbox_file)


if __name__ == "__main__":
    main()
