from collections import UserList
from dataclasses import dataclass, fields
from math import log10
from typing import TypeVar


@dataclass
class Row:
    @classmethod
    def get_fields(cls) -> tuple[str, ...]:
        return tuple(f.name for f in fields(cls))

    @classmethod
    def get_print_fields(cls) -> tuple[str, ...]:
        return cls.get_fields()

    def __str__(self) -> str:
        return "  " + " | ".join(
            f"{f}: {getattr(self, f)}" for f in self.get_print_fields()
        )


@dataclass
class LibraryRow(Row):
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

    @classmethod
    def get_print_fields(cls) -> tuple:
        return ("artist", "title", "album")


@dataclass
class TrackLocationsRow(Row):
    id: int
    location: str
    filename: str
    directory: str
    filesize: int
    fs_deleted: int
    needs_verification: int | None
    saved_indices_mixxx_location: int | None

    @classmethod
    def get_print_fields(cls) -> tuple:
        return ("location",)


@dataclass
class CuesRow(Row):
    id: int
    track_id: int
    type: int
    position: int | float  # https://github.com/mixxxdj/mixxx/pull/1108
    length: int
    hotcue: int
    label: str
    color: int


@dataclass
class PlaylistRow(Row):
    id: int
    name: str
    position: int | None
    hidden: int
    date_created: str | None
    date_modified: str | None
    locked: int


@dataclass
class PlaylistTrackRow(Row):
    id: int
    playlist_id: int
    track_id: int
    position: int
    pl_datetime_added: str | None


@dataclass
class CrateRow(Row):
    id: int
    name: str
    count: int
    show: int
    locked: int
    autodj_source: int


@dataclass
class CrateTrackRow(Row):
    crate_id: int
    track_id: int


@dataclass
class TrackAnalysisRow(Row):
    id: int
    track_id: int
    type: str | None
    description: str | None
    version: str | None
    created: str | None
    data_checksum: str | None


TypeRow = TypeVar("TypeRow", bound=Row)


class Table(UserList[TypeRow]):
    def get_fields(self) -> tuple[str, ...]:
        if not self:
            return ()
        return self[0].get_fields()

    def get_print_fields(self) -> tuple[str, ...]:
        if not self:
            return ()
        return self[0].get_print_fields()

    def __str__(self) -> str:
        if not self:
            return ""
        lidx = int(log10(len(self))) + 1

        colnames = self.get_print_fields()

        rows = [[" "] + list(colnames)]
        rows += [
            [idx] + [getattr(row, name) for name in colnames]
            for idx, row in enumerate(self)
        ]
        widths = [lidx] + [
            max(len(str(r[i + 1])) for r in rows) for i in range(len(colnames))
        ]

        print_rows = [
            " | ".join(f"{str(value):>{width}}" for value, width in zip(row, widths))
            for row in rows
        ]
        return "\n".join(print_rows)
