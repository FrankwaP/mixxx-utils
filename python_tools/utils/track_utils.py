from dataclasses import dataclass
from re import sub
from math import prod

import pandas as pd
from jellyfish import levenshtein_distance

from .proto import beats_pb2


@dataclass
class BeatGridInfo:
    start: int
    start_sec: float
    bpm: float

    def __init__(self, library_row: pd.Series):
        beatgrid = beats_pb2.BeatGrid()
        beatgrid.ParseFromString(library_row["beats"])
        self.start = beatgrid.first_beat.frame_position
        self.start_sec = self.start / library_row["samplerate"]
        self.bpm = beatgrid.bpm.bpm


def remove_feat(name: str) -> str:
    return sub(r" \(*f(?:ea)?t\. .+", "", name)


def levenshtein_distance_sum(
    row1: pd.Series, row2: pd.Series, col_names: list[str]
) -> int:
    return prod(1 + levenshtein_distance(row1[c], row2[c]) for c in col_names)


def get_closest_matches_indices(
    row: pd.Series,
    search_df: pd.DataFrame,
    col_names: list[str],
    n_results: int = 3,
) -> pd.Index:
    distance_serie = search_df.apply(
        lambda t: levenshtein_distance_sum(t, row, col_names), axis=1
    )
    distance_serie = distance_serie.sort_values()
    return distance_serie[:n_results].index
