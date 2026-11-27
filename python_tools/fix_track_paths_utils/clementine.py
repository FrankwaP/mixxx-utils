from sys import exit as sysexit

from ..utils.config import FixTrackPathsUtilsConfig
from ..utils.dataclasses_utils import Table
from ..utils.music_db_utils_no_pandas import _open_table, file_url_to_path
from .dataclasses_utils import ClementineSongRow, TrackFixRow
from .main import fix_with_player_db


def get_clementine_db(config: FixTrackPathsUtilsConfig) -> Table[TrackFixRow]:
    clem_db = config.clem_db

    """Load and prepare the Clementine database as a pandas DataFrame."""
    if config.confirm_player_refresh:
        answer = input("Did you refresh Clementine's library (y/*)? ")
        if answer != "y":
            print("Well do it <3")
            sysexit()
    df_clem = _open_table(clem_db, "songs", ClementineSongRow)

    return Table(
        TrackFixRow(
            tracknumber="" if r.track is None else str(r.track),
            artist=r.artist or "",
            album=r.album or "",
            title=r.title or "",
            player_path=file_url_to_path(r.filename.decode()),
        )
        for r in df_clem
    )


def fix_with_clementine_db(config: FixTrackPathsUtilsConfig):
    """Fix the Mixxx library using the Clementine database."""
    df_clem = get_clementine_db(config)
    fix_with_player_db(config, df_clem)
