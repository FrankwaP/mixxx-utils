import logging
from pathlib import Path
from typing import Callable, TypeVar

import pytest

from python_tools.utils.config import (
    FIX_TRACK_PATHS_CONFIG_ENV_VAR,
    MIXXX_TO_REKORDBOX_COMPARE_CONFIG_ENV_VAR,
    MIXXX_TO_REKORDBOX_CONFIG_ENV_VAR,
    SNAP_CUES_CONFIG_ENV_VAR,
    FixTrackPathsUtilsConfig,
    MixxxToRekordboxCompareConfig,
    MixxxToRekordboxConfig,
    SnapCuesConfig,
    get_fix_track_paths_config,
    get_mixxx_to_rekordbox_compare_config,
    get_mixxx_to_rekordbox_config,
    get_snap_cues_config,
)

TConfig = TypeVar("TConfig")


def _prepare_and_get_config(
    tmp_path_: Path,
    monkeypatch_: pytest.MonkeyPatch,
    config_filename: str,
    template_filename: str,
    env_var: str,
    getter: Callable[[], TConfig],
) -> TConfig:
    tests_dir = Path(__file__).resolve().parent

    config_template = (tests_dir / template_filename).read_text()
    replacements = {"__TEMP_FOLDER__": tmp_path_}

    for placeholder, path in replacements.items():
        if placeholder in config_template:
            config_template = config_template.replace(f"{placeholder}", str(path))
        else:
            logging.debug(
                "%s placeholder was not found this file (but maybe it is OK): %s",
                placeholder,
                template_filename,
            )

    config_path = tmp_path_ / config_filename
    config_path.write_text(config_template)
    monkeypatch_.setenv(env_var, str(config_path))
    return getter()


@pytest.fixture
def mixxx_to_rekordbox_config(tmp_path, monkeypatch) -> MixxxToRekordboxConfig:
    config_filename = "test-mixxx_to_rekordbox.toml"
    template_filename = "test-mixxx_to_rekordbox-template.toml"
    env_var = MIXXX_TO_REKORDBOX_CONFIG_ENV_VAR
    getter = get_mixxx_to_rekordbox_config
    return _prepare_and_get_config(
        tmp_path, monkeypatch, config_filename, template_filename, env_var, getter
    )


@pytest.fixture
def mixxx_to_rekordbox_compare_config(
    tmp_path, monkeypatch
) -> MixxxToRekordboxCompareConfig:
    config_filename = "test-mixxx_to_rekordbox_compare.toml"
    template_filename = "test-mixxx_to_rekordbox_compare-template.toml"
    env_var = MIXXX_TO_REKORDBOX_COMPARE_CONFIG_ENV_VAR
    getter = get_mixxx_to_rekordbox_compare_config
    return _prepare_and_get_config(
        tmp_path, monkeypatch, config_filename, template_filename, env_var, getter
    )


@pytest.fixture
def snap_cues_config(tmp_path, monkeypatch) -> SnapCuesConfig:
    config_filename = "test-snap_cues.toml"
    template_filename = "test-snap_cues-template.toml"
    env_var = SNAP_CUES_CONFIG_ENV_VAR
    getter = get_snap_cues_config
    return _prepare_and_get_config(
        tmp_path, monkeypatch, config_filename, template_filename, env_var, getter
    )


@pytest.fixture
def fix_track_paths_config(tmp_path, monkeypatch) -> FixTrackPathsUtilsConfig:
    config_filename = "test-fix_track_paths.toml"
    template_filename = "test-fix_track_paths-template.toml"
    env_var = FIX_TRACK_PATHS_CONFIG_ENV_VAR
    getter = get_fix_track_paths_config
    return _prepare_and_get_config(
        tmp_path, monkeypatch, config_filename, template_filename, env_var, getter
    )
