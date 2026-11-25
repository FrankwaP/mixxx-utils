import logging
import xml.etree.ElementTree as ET

from .mixxx_to_rekordbox_compare_utils.dataclasses_utils import XmlTrackTable
from .utils.config import (
    MixxxToRekordboxCompareConfig,
    get_mixxx_to_rekordbox_compare_config,
)
from .utils.dataclasses_operations_utils import (
    filter_left_using_right_outer,
    pseudo_inner_join_product,
)


def _write_new_playlist(
    mtr_config: MixxxToRekordboxCompareConfig, track_id_mixxx: list[str]
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
    logging.info(
        "A new playlist %s has been added to the Mixxx to Rekordbox XML file %s.",
        mtr_config.playlist_updated_tracks,
        mtr_config.mixxx_to_rekordbox_xml,
    )


def main():

    mtr_config = get_mixxx_to_rekordbox_compare_config()

    table_mixxx = XmlTrackTable.from_xml(mtr_config.mixxx_to_rekordbox_xml)
    table_rkbox = XmlTrackTable.from_xml(mtr_config.rekordbox_compare_export_xml)

    table_new = filter_left_using_right_outer(
        table_mixxx, table_rkbox, on_left=("location",), on_right=("location",)
    )

    for t_new in table_new:
        logging.info("New track found: %s", t_new)

    t_m, t_r = pseudo_inner_join_product(
        table_mixxx,
        table_rkbox,
        on_left=("location",),
        on_right=("location",),
        assert_unique_left=True,
        assert_unique_right=True,
    )

    table_updated = XmlTrackTable(t_m for t_m, t_r in zip(t_m, t_r) if t_m != t_r)

    for t_updt in table_updated:
        logging.info("Updated track found: %s", t_updt)

    track_ids = [track.trackID for track in table_new + table_updated]

    _write_new_playlist(mtr_config, track_ids)
