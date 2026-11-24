from dataclasses import dataclass

from ..utils.dataclasses_utils import Row


@dataclass
class ClementineSongRow(Row):
    title: str | None
    album: str | None
    artist: str | None
    albumartist: str | None
    composer: str | None
    track: int | None
    disc: int | None
    bpm: float | None
    year: int | None
    genre: str | None
    comment: str | None
    compilation: int | None
    length: int | None
    bitrate: int | None
    samplerate: int | None
    directory: int
    filename: bytes
    mtime: int
    ctime: int
    filesize: int
    sampler: int
    art_automatic: str | None
    art_manual: str | None
    filetype: int
    playcount: int
    lastplayed: int | None
    rating: int | None
    forced_compilation_on: int
    forced_compilation_off: int
    effective_compilation: int
    skipcount: int
    score: int
    beginning: int
    cue_path: str | None
    unavailable: int | None
    effective_albumartist: str | None
    etag: str | None
    performer: str | None
    grouping: str | None
    lyrics: str | None
    originalyear: int | None
    effective_originalyear: int | None


@dataclass
class CloseMatchRow(Row):
    artist: str
    title: str


@dataclass
class PerfectMatchRow(CloseMatchRow):
    tracknumber: str
    album: str


@dataclass
class TrackFixRow(PerfectMatchRow):
    player_path: str
