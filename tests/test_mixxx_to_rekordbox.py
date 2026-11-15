from pathlib import Path

from python_tools.mixxx_to_rekordbox import main


def test_export(test_config):
    config = test_config

    main()

    xml_path = Path(config.mixxx_to_rekordbox.mixxx_to_rekordbox_xml)
    assert xml_path.is_file()
