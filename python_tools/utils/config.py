import os
import sys
import tomllib
from logging import (
    DEBUG,
    ERROR,
    INFO,
    WARNING,
    FileHandler,
    StreamHandler,
    basicConfig,
    getLogger,
)
from pathlib import Path, PureWindowsPath
from typing import Annotated, Literal, TypeVar

from pydantic import AfterValidator, BaseModel, ValidationError
from pydantic.fields import Field
from pydantic.types import DirectoryPath, FilePath
from pydantic_core import ErrorDetails

MIXXX_TO_REKORDBOX_CONFIG_FILE = "mixxx_to_rekordbox.toml"
MIXXX_TO_REKORDBOX_CONFIG_ENV_VAR = "MIXXX_TO_REKORDBOX_CONF"

MIXXX_TO_REKORDBOX_COMPARE_CONFIG_FILE = "mixxx_to_rekordbox_compare.toml"
MIXXX_TO_REKORDBOX_COMPARE_CONFIG_ENV_VAR = "MIXXX_TO_REKORDBOX_COMPARE_CONF"

SNAP_CUES_CONFIG_FILE = "snap_cues.toml"
SNAP_CUES_CONFIG_ENV_VAR = "SNAP_CUES_CONF"

FIX_TRACK_PATHS_CONFIG_FILE = "fix_track_paths.toml"
FIX_TRACK_PATHS_CONFIG_ENV_VAR = "FIX_TRACK_PATHS_CONF"

logger = getLogger(__name__)


def _resolve(path: Path) -> Path:
    return path.resolve()


class _MyBaseModel(BaseModel):
    model_config = {"extra": "forbid"}  # pydantic stuff
    confirm_config: bool = True
    logging_level: Literal["debug", "info", "warning", "error"] = "info"


class MixxxToRekordboxConfig(_MyBaseModel):
    mixxx_db: Annotated[FilePath, AfterValidator(_resolve)]
    confirm_snaped: bool = True
    mixxx_to_rekordbox_xml: Annotated[Path, AfterValidator(_resolve)]
    mixxx_library_folder: Annotated[DirectoryPath, AfterValidator(_resolve)]
    rekordbox_library_folder: PureWindowsPath
    export_only_tracks_in_playlists: bool = True
    export_only_locked_tracks: bool = True
    add_crates_as_playlist: bool = True
    crates_suffix: str = "_crates"
    beats_per_bar: int = Field(default=8, gt=0)
    index_cue_bar_start: int = Field(ge=0)
    mp3_decoder: Literal["MAD", "CoreAudio", "FFmpeg"] = "MAD"


class MixxxToRekordboxCompareConfig(_MyBaseModel):
    mixxx_to_rekordbox_xml: Annotated[Path, AfterValidator(_resolve)]
    rekordbox_compare_export_xml: Annotated[Path, AfterValidator(_resolve)]
    playlist_updated_tracks: str


class SnapCuesConfig(_MyBaseModel):
    mixxx_db: Annotated[FilePath, AfterValidator(_resolve)]
    idx_snapped_cues: list[int]


class FixTrackPathsUtilsConfig(_MyBaseModel):
    mixxx_db: Annotated[FilePath, AfterValidator(_resolve)]
    confirm_player_refresh: bool = True
    clem_db: FilePath
    threshold_name_similarity: int = Field(default=50, gt=0, lt=100)
    n_similar_track_proposal: int = Field(default=3, gt=0)

    delete_keys: bool = True
    delete_gains: bool = True
    delete_waveforms: bool = True


def get_mixxx_to_rekordbox_config() -> MixxxToRekordboxConfig:
    return _get_and_check_config(
        MIXXX_TO_REKORDBOX_CONFIG_FILE,
        MIXXX_TO_REKORDBOX_CONFIG_ENV_VAR,
        MixxxToRekordboxConfig,
    )


def get_mixxx_to_rekordbox_compare_config() -> MixxxToRekordboxCompareConfig:
    return _get_and_check_config(
        MIXXX_TO_REKORDBOX_COMPARE_CONFIG_FILE,
        MIXXX_TO_REKORDBOX_COMPARE_CONFIG_ENV_VAR,
        MixxxToRekordboxCompareConfig,
    )


def get_snap_cues_config() -> SnapCuesConfig:
    return _get_and_check_config(
        SNAP_CUES_CONFIG_FILE,
        SNAP_CUES_CONFIG_ENV_VAR,
        SnapCuesConfig,
    )


def get_fix_track_paths_config() -> FixTrackPathsUtilsConfig:
    return _get_and_check_config(
        FIX_TRACK_PATHS_CONFIG_FILE,
        FIX_TRACK_PATHS_CONFIG_ENV_VAR,
        FixTrackPathsUtilsConfig,
    )


def _err_msg(err: ErrorDetails) -> str:
    msg = err["msg"]
    loc = "/".join(map(str, err["loc"]))
    return f"\n\t{msg}: {loc}"


TConfig = TypeVar("TConfig", bound=_MyBaseModel)


def _get_config(config_file: str, config_env_var: str, model: type[TConfig]) -> TConfig:
    # https://nuitka.net/user-documentation/common-issue-solutions.html#onefile-finding-files
    root_path = Path(sys.argv[0]).parent
    log_path = Path(sys.argv[0]).with_suffix(".log")
    if config_env_var in os.environ:
        config_path = Path(os.environ[config_env_var])
        try:
            toml = tomllib.loads(config_path.read_text())
            config = model.model_validate(toml)
            _set_logging_level(config, log_path)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"The file defined in {config_env_var} environment variable "
                f" does not exist: {config_path}"
            )
        logger.info(
            "Reading the config file defined in %s environment variable %s",
            config_env_var,
            config_path,
        )
    else:
        config_path = root_path / config_file
        try:
            toml = tomllib.loads(config_path.read_text())
            config = model.model_validate(toml)
            _set_logging_level(config, log_path)
        except FileNotFoundError:
            raise FileNotFoundError(
                "No config file detected either using:\n",
                f" - a path specified in the {config_env_var} environment variable\n",
                f" - or the path {config_path}",
            )
        logger.info(f"Reading the config file {config_path}")
    return config


def _get_and_check_config(
    config_file: str, config_env_var: str, model: type[TConfig]
) -> TConfig:
    config = _get_config(config_file, config_env_var, model)
    try:
        if config.confirm_config:
            _confirm_config(config)
        return config
    except ValidationError as err:
        raise ValueError(
            "Invalid configuration" + "".join(_err_msg(e) for e in err.errors())
        ) from None


def _set_logging_level(config: _MyBaseModel, log_path: Path) -> None:
    level = {"debug": DEBUG, "info": INFO, "warning": WARNING, "error": ERROR}[
        config.logging_level
    ]
    basicConfig(
        level=level,
        handlers=[
            FileHandler(log_path, mode="w", encoding="utf-8"),
            StreamHandler(),
        ],
        force=True,
    )


def _pprint(config_dict: dict, indent=0) -> None:
    print()
    for k, v in config_dict.items():
        if isinstance(v, dict):
            print(f"{k}:")
            _pprint(v, indent + 1)
        else:
            tabs = "\t" * indent
            print(f"{tabs}{k}: {v}")
    print()


def _confirm_config(config: _MyBaseModel) -> None:
    _pprint(config.model_dump())
    ans = input("Are these setting OK? (y/*) ")
    if ans != "y":
        sys.exit(1)
