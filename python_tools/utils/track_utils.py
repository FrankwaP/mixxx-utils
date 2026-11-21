from .dataclasses_utils import LibraryRow
from .proto import beats_pb2  # type: ignore


def position_frame_to_sec(frame: int, samplerate: float) -> float:
    return frame / (2 * samplerate)


def position_sec_to_frame(time_sec: float, samplerate: float) -> int:
    return round(time_sec * (2 * samplerate))


def beatgrid_frame_to_sec(frame: int, samplerate: float) -> float:
    return frame / samplerate


class BeatGridInfo:

    def __init__(self, library_row: LibraryRow):
        if library_row.beats is None or library_row.samplerate is None:
            raise TypeError("Beatgrid data and samplerate are required")
        beatgrid = beats_pb2.BeatGrid()  # type: ignore
        beatgrid.ParseFromString(library_row.beats)
        self.start_frame = beatgrid.first_beat.frame_position
        self.start_sec = beatgrid_frame_to_sec(
            self.start_frame, float(library_row.samplerate)
        )
        self.bpm = beatgrid.bpm.bpm


def snap_cue_frame(
    cue_position_frame: int,
    samplerate: float,
    beatgrid_start_sec: float,
    beat_interval_sec: float,
) -> int:
    position_sec = position_frame_to_sec(cue_position_frame, samplerate)
    scaled_position = (position_sec - beatgrid_start_sec) / beat_interval_sec
    snaped_position = round(scaled_position)
    unscaled_position = snaped_position * beat_interval_sec + beatgrid_start_sec
    return position_sec_to_frame(unscaled_position, samplerate)


def guess_inizio_sec(
    hot_cue_frame_pos: int, samplerate: float, bpm: float, beats_per_bar: int
) -> float:
    hot_cue_sec = position_frame_to_sec(hot_cue_frame_pos, samplerate)
    interval_sec = 60 / bpm
    return hot_cue_sec % (beats_per_bar * interval_sec)
