import logging
import os
import sys
import tomllib
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


def _resolve(path: Path) -> Path:
    return path.resolve()


class _MyBaseModel(BaseModel):
    model_config = {"extra": "forbid"}
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


def _get_config_path(config_file: str, config_env_var: str) -> Path:
    if config_env_var in os.environ:
        config_path = Path(os.environ[config_env_var])
        if not config_path.exists():
            raise FileNotFoundError(
                f"The file defined in {config_env_var} environment variable does not exist: {config_path}"
            )
        print(
            f"Reading the config file defined in {config_env_var} environment variable: {config_path}"
        )
    else:
        # https://nuitka.net/user-documentation/common-issue-solutions.html#onefile-finding-files
        config_path = Path(sys.argv[0]).parent / config_file
        if not config_path.exists():
            raise FileNotFoundError(
                "No config file detected either using:\n",
                f" - a path specified in the {config_env_var} environment variable\n",
                f" - or the path {config_path}",
            )
        logging.info(f"Reading the config file {config_path}")
    return config_path


def _err_msg(err: ErrorDetails) -> str:
    msg = err["msg"]
    loc = "/".join(map(str, err["loc"]))
    return f"\n\t{msg}: {loc}"


TConfig = TypeVar("TConfig", bound=_MyBaseModel)


def _get_config(
    config_file: str,
    config_env_var: str,
    model: type[TConfig],
) -> TConfig:
    config_path = _get_config_path(config_file, config_env_var)
    toml = tomllib.loads(config_path.read_text())
    try:
        config = model.model_validate(toml)
        _set_logging_level(config)
        if config.confirm_config:
            _confirm_config(config)
        return config
    except ValidationError as err:
        raise ValueError(
            "Invalid configuration" + "".join(_err_msg(e) for e in err.errors())
        ) from None


def get_mixxx_to_rekordbox_config() -> MixxxToRekordboxConfig:
    return _get_config(
        MIXXX_TO_REKORDBOX_CONFIG_FILE,
        MIXXX_TO_REKORDBOX_CONFIG_ENV_VAR,
        MixxxToRekordboxConfig,
    )


def get_mixxx_to_rekordbox_compare_config() -> MixxxToRekordboxCompareConfig:
    return _get_config(
        MIXXX_TO_REKORDBOX_COMPARE_CONFIG_FILE,
        MIXXX_TO_REKORDBOX_COMPARE_CONFIG_ENV_VAR,
        MixxxToRekordboxCompareConfig,
    )


def get_snap_cues_config() -> SnapCuesConfig:
    return _get_config(
        SNAP_CUES_CONFIG_FILE,
        SNAP_CUES_CONFIG_ENV_VAR,
        SnapCuesConfig,
    )


def get_fix_track_paths_config() -> FixTrackPathsUtilsConfig:
    return _get_config(
        FIX_TRACK_PATHS_CONFIG_FILE,
        FIX_TRACK_PATHS_CONFIG_ENV_VAR,
        FixTrackPathsUtilsConfig,
    )


def _set_logging_level(config: _MyBaseModel) -> None:
    loglev = config.logging_level
    if loglev == "debug":
        level = logging.DEBUG
    elif loglev == "info":
        level = logging.INFO
    elif loglev == "warning":
        level = logging.WARNING
    elif loglev == "error":
        level = logging.ERROR
    logging.basicConfig(level=level)


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
