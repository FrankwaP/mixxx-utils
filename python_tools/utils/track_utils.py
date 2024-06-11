import sys

import pandas as pd

from .proto import beats_pb2



def get_beatgrid_start(library_row:pd.Serie) -> float:
    beatgrid = beats_pb2.BeatGrid()
    beatgrid.ParseFromString(library_row["beats"])
    return beatgrid.first_beat.frame_position / library_row["samplerate"]
