import logging
import os
import sys
import tomllib
from pathlib import Path, PureWindowsPath
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ValidationError
from pydantic.fields import Field
from pydantic.types import DirectoryPath, FilePath
from pydantic_core import ErrorDetails

_CONFIG_ENV_VAR = "MIXXX_UTILS_CONFIG"


def _resolve(path: Path) -> Path:
    return path.resolve()


class _MyBaseModel(BaseModel):
    model_config = {"extra": "forbid"}


class UserInteractions(_MyBaseModel):
    confirm_config: bool = True
    confirm_player_refresh: bool = True
    confirm_snaped: bool = True
    logging_level: Literal["debug", "info", "warning", "error"] = "info"


class MixxxConfig(_MyBaseModel):
    mixxx_db: Annotated[FilePath, AfterValidator(_resolve)]


class MixxxToRekordboxConfig(_MyBaseModel):
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
    rekordbox_compare_export_xml: Annotated[Path, AfterValidator(_resolve)]
    playlist_updated_tracks: str


class SnapCuesConfig(_MyBaseModel):
    idx_snapped_cues: list[int]


class FixTrackPathsUtilsConfig(_MyBaseModel):
    clem_db: FilePath
    threshold_name_similarity: int = Field(default=50, gt=0, lt=100)
    n_similar_track_proposal: int = Field(default=3, gt=0)

    delete_keys: bool = True
    delete_gains: bool = True
    delete_waveforms: bool = True


class Config(_MyBaseModel):
    user_interactions: UserInteractions
    mixxx: MixxxConfig
    mixxx_to_rekordbox: MixxxToRekordboxConfig
    snap_cues: SnapCuesConfig
    fix_track_paths: FixTrackPathsUtilsConfig


def _get_config_path() -> Path:
    if _CONFIG_ENV_VAR in os.environ:
        config_path = Path(os.environ[_CONFIG_ENV_VAR])
        if not config_path.exists():
            raise FileNotFoundError(
                f"The file defined in {_CONFIG_ENV_VAR} environment variable does not exists: {config_path}"
            )
        print(
            f"Reading the config file defined in {_CONFIG_ENV_VAR} environment variable: {config_path}"
        )
    else:
        pytool_dir = Path(__file__).resolve().parents[1]
        config_path = pytool_dir / "config.toml"
        if not config_path.exists():
            raise FileNotFoundError(
                "No config file detected either using:\n",
                f" - a path specified in the {_CONFIG_ENV_VAR} environment variable\n",
                f" - or the path {config_path}",
            )
        logging.info(f"Reading the config file {config_path}")
    return config_path


def _err_msg(err: ErrorDetails) -> str:
    msg = err["msg"]
    loc = "/".join(map(str, err["loc"]))
    return f"\n\t{msg}: {loc}"


def get_config() -> Config:
    config_path = _get_config_path()
    toml = tomllib.loads(config_path.read_text())
    try:
        config = Config.model_validate(toml)
        if config.user_interactions.confirm_config:
            _confirm_config(config)
            _set_logging_level(config)
        return Config.model_validate(toml)
    except ValidationError as err:
        raise ValueError(
            "Invalid configuration" + "".join(_err_msg(e) for e in err.errors())
        ) from None


def _set_logging_level(config: Config) -> None:
    loglev = config.user_interactions.logging_level
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


def _confirm_config(config: Config) -> None:
    _pprint(config.model_dump())
    ans = input("Are these setting OK? (y/*) ")
    if ans != "y":
        sys.exit(1)
