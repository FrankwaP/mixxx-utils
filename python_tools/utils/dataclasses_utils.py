from collections import UserList
from dataclasses import dataclass
from typing import TypeAlias, TypeVar


class _BaseRow:
    def get_str_fields(self) -> tuple:
        raise NotImplementedError
        return tuple()


@dataclass
class LibraryRow(_BaseRow):
    id: int
    artist: str | None
    title: str | None
    album: str | None
    year: str | None
    genre: str | None
    tracknumber: str | None
    location: int | None
    comment: str | None
    url: str | None
    duration: float | None
    bitrate: int | None
    samplerate: int | None
    cuepoint: int | None
    bpm: float | None
    wavesummaryhex: bytes | None
    channels: int | None
    datetime_added: str | None
    mixxx_deleted: int | None
    played: int | None
    header_parsed: int | None
    filetype: str | None
    replaygain: float | None
    timesplayed: int | None
    rating: int | None
    key: str | None
    beats: bytes | None
    beats_version: str | None
    composer: str | None
    bpm_lock: int | None
    beats_sub_version: str | None
    keys: bytes | None
    keys_version: str | None
    keys_sub_version: str | None
    key_id: int | None
    grouping: str | None
    album_artist: str | None
    coverart_source: int | None
    coverart_type: int | None
    coverart_location: str | None
    coverart_hash: int | None
    replaygain_peak: float | None
    tracktotal: str | None
    color: int | None
    coverart_color: int | None
    coverart_digest: bytes | None
    last_played_at: str | None
    source_synchronized_ms: int | None
    tuning_frequency_hz: float | None

    def get_str_fields(self) -> tuple:
        return (self.artist, self.title, self.album)

    def __str__(self) -> str:
        return "\t".join(str(i) for i in self.get_str_fields())


@dataclass
class TrackLocationsRow(_BaseRow):
    id: int
    location: str
    filename: str
    directory: str
    filesize: int
    fs_deleted: int
    needs_verification: int | None
    saved_indices_mixxx_location: int | None


@dataclass
class CuesRow(_BaseRow):
    id: int
    track_id: int
    type: int
    position: int
    length: int
    hotcue: int
    label: str
    color: int


@dataclass
class PlaylistRow(_BaseRow):
    id: int
    name: str
    position: int | None
    hidden: int
    date_created: str | None
    date_modified: str | None
    locked: int


@dataclass
class PlaylistTrackRow(_BaseRow):
    id: int
    playlist_id: int
    track_id: int
    position: int
    pl_datetime_added: str | None


@dataclass
class CrateRow(_BaseRow):
    id: int
    name: str
    count: int
    show: int
    locked: int
    autodj_source: int


@dataclass
class CrateTrackRow(_BaseRow):
    crate_id: int
    track_id: int


@dataclass
class TrackAnalysisRow(_BaseRow):
    id: int
    track_id: int
    type: str | None
    description: str | None
    version: str | None
    created: str | None
    data_checksum: str | None


# %%


@dataclass
class CloseMatchRow(_BaseRow):
    artist: str
    title: str


@dataclass
class PerfectMatchRow(CloseMatchRow):
    tracknumber: str
    album: str


@dataclass
class TrackFixRow(PerfectMatchRow):
    player_path: str


# %%


RowTypes: TypeAlias = (
    LibraryRow
    | TrackLocationsRow
    | CuesRow
    | PlaylistRow
    | PlaylistTrackRow
    | CrateRow
    | CrateTrackRow
    | TrackAnalysisRow
    | TrackFixRow
)

Row = TypeVar("Row", bound=RowTypes)


class Table(UserList[Row]):
    def __str__(self) -> str:
        columns = tuple(zip(i for i in r.get_str_fields()) for r in self)
        columns_width = (max(len(r) for r in c) for c in columns)
        str_frmt = "  |  ".join(f"%{c}s" for c in columns_width)
        return str_frmt.format(columns)
