import pandas as pd

from .proto import beats_pb2


class BeatGridInfo:
    def __init__(self, library_row: pd.Series):
        beatgrid = beats_pb2.BeatGrid()
        beatgrid.ParseFromString(library_row["beats"])
        self.start = beatgrid.first_beat.frame_position
        self.start_sec = self.start / library_row["samplerate"]
        self.bpm = beatgrid.bpm.bpm
