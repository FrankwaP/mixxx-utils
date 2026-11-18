from pathlib import Path
from xml.etree import ElementTree as ET

from python_tools.mixxx_to_rekordbox import main


def _canonical_xml(path: Path) -> str:
    return ET.canonicalize(from_file=path, strip_text=True)


def test_export_with_sqlite_rows(test_config) -> None:
    main()

    xml_path = Path(test_config.mixxx_to_rekordbox.mixxx_to_rekordbox_xml)

    root = ET.parse(xml_path).getroot()
    collection = root.find("COLLECTION")
    assert root.tag == "DJ_PLAYLISTS"
    assert collection is not None
    assert int(collection.attrib["Entries"]) > 0

    test_xml_path = Path(__file__).parent / Path("test-mixxx_to_rekordbox.xml")
    assert _canonical_xml(xml_path) == _canonical_xml(test_xml_path)
