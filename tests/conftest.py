from pathlib import Path

import pytest

from python_tools.utils.config import get_config, Config


@pytest.fixture
def test_config(tmp_path, monkeypatch) -> Config:
    tests_dir = Path(__file__).resolve().parent

    config_template = (tests_dir / "test-config-template.toml").read_text()
    replacements = {
        "__TEMP_FOLDER__": tmp_path,
    }

    for placeholder, path in replacements.items():
        assert placeholder in config_template
        config_template = config_template.replace(f"{placeholder}", str(path))

    config_path = tmp_path / "config.toml"
    config_path.write_text(config_template)
    monkeypatch.setenv("MIXXX_UTILS_CONFIG", str(config_path))

    return get_config()
