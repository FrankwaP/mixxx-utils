from sys import exit

import pandas as pd
from python_tools.utils.music_db_utils import open_table_as_df


from python_tools import CONFIG
from .main import (
    fix_with_player_db,
    PLAYER_PATH,
)

cfg = CONFIG.fix_track_paths


def get_clementine_db() -> pd.DataFrame:
    """Load and prepare the Clementine database as a pandas DataFrame."""
    answer = input("Did you refresh Clementine's library (y/*)? ")
    if answer != "y":
        print("Well do it <3")
        exit()
    df_clem = open_table_as_df(cfg.clem_db, "songs")
    df_clem.rename(columns={"filename": PLAYER_PATH}, inplace=True)
    return df_clem


def fix_with_clementine_db():
    """Fix the Mixxx library using the Clementine database."""
    df_clem = get_clementine_db()
    fix_with_player_db(df_clem)
