import sys
from pathlib import Path
import os
import tomllib
from typing import Any


def get_config() -> dict[str, Any]:
    try:
        config_filename = os.environ["MIXXX_UTILS_CONFIG"]
        config_path = Path(config_filename)
    except KeyError:
        config_path = Path.cwd() / "config.toml"

    if not config_path.exists():
        msg = (
            "Could not find config, it should either be a file named config.toml"
            "in the current directory or its path should be specified in the "
            "MIXXX_UTILS_CONFIG environment variable"
        )
        print(msg)
        sys.exit(1)

    return tomllib.loads(config_path.read_text())
