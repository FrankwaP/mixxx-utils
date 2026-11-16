from pathlib import Path
from xml.etree import ElementTree as ET

from python_tools.mixxx_to_rekordbox_no_pandas import main


def test_export_with_sqlite_rows(test_config) -> None:
    main()

    xml_path = Path(test_config.mixxx_to_rekordbox.mixxx_to_rekordbox_xml)
    root = ET.parse(xml_path).getroot()
    collection = root.find("COLLECTION")
    assert root.tag == "DJ_PLAYLISTS"
    assert collection is not None
    assert int(collection.attrib["Entries"]) > 0
