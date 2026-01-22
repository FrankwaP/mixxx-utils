import sys
from pathlib import Path
import os
import tomllib
from typing import Literal

from pydantic import BaseModel, ValidationError
from pydantic.fields import Field
from pydantic.types import FilePath, DirectoryPath
from pydantic_core import ErrorDetails


class MyBaseModel(BaseModel):
    model_config = {"extra": "forbid"}


class MixxxConfig(MyBaseModel):
    mixxx_db: FilePath


class MixxxToRekordboxConfig(MyBaseModel):
    rekordbox_xml_file: Path
    mixxx_library_folder: DirectoryPath
    rekordbox_library_folder: Path
    export_only_tracks_in_playlists: bool = True
    add_crates_as_playlist: bool = True
    crates_suffix: str = "_crates"
    beats_per_bar: int = Field(default=8, gt=0)
    index_cue_bar_start: int = Field(ge=0)
    mp3_decoder: Literal["MAD", "CoreAudio", "FFmpeg"] = "MAD"


class SnapCuesConfig(MyBaseModel):
    idx_snapped_cues: list[int]


class FixTrackPathsUtilsConfig(MyBaseModel):
    clem_db: FilePath
    threshold_name_similarity: int = Field(default=50, gt=0, lt=100)
    n_similar_track_proposal: int = Field(default=3, gt=0)

    delete_keys: bool = True
    delete_gains: bool = True
    delete_waveforms: bool = True


class Config(MyBaseModel):
    mixxx: MixxxConfig
    mixxx_to_rekordbox: MixxxToRekordboxConfig
    snap_cues: SnapCuesConfig
    fix_track_paths: FixTrackPathsUtilsConfig


def get_config_path() -> Path:
    if "MIXXX_UTILS_CONFIG" in os.environ:
        config_path = Path(os.environ["MIXXX_UTILS_CONFIG"])
        if not config_path.exists():
            raise FileNotFoundError(
                "The file defined in MIXXX_UTILS_CONFIG environment variable "
                " does not exists."
            )
        print(
            "Reading the config file defined in MIXXX_UTILS_CONFIG environment variable"
        )
    else:
        pytool_dir = Path(__file__).parent
        config_path = pytool_dir / "config.toml"
        if not config_path.exists():
            raise FileNotFoundError(
                "No config file detected either using:\n",
                " - a path specified in the MIXXX_UTILS_CONFIG environment variable\n",
                f" - or the path {config_path}",
            )
        print(f"Reading the config file {config_path}")
    return config_path


def err_msg(err: ErrorDetails) -> str:
    msg = err["msg"]
    loc = "/".join(map(str, err["loc"]))
    return f"\n\t{msg}: {loc}"


def get_config() -> Config:
    config_path = get_config_path()
    toml = tomllib.loads(config_path.read_text())
    try:
        return Config.model_validate(toml)
    except ValidationError as err:
        raise ValueError(
            "Invalid configuration" + "".join(err_msg(e) for e in err.errors())
        ) from None


def pprint(config_dict: dict, indent=0) -> None:
    for k, v in config_dict.items():
        if isinstance(v, dict):
            print(f"{k}:")
            pprint(v, indent + 1)
        else:
            tabs = "\t" * indent
            print(f"{tabs}{k}: {v}")


def confirm(config: Config) -> None:
    print()
    pprint(config.model_dump())
    print()
    ans = input("Are these setting OK? (y/*) ")
    if ans != "y":
        sys.exit(1)


CONFIG = get_config()
confirm(CONFIG)
