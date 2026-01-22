# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO
from enum import Enum

if getattr(kaitaistruct, "API_VERSION", (0, 9)) < (0, 9):
    raise Exception(
        "Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s"
        % (kaitaistruct.__version__)
    )


class RekordboxPdb(KaitaiStruct):
    """This is a relational database format designed to be efficiently used
    by very low power devices (there were deployments on 16 bit devices
    with 32K of RAM). Today you are most likely to encounter it within
    the Pioneer Professional DJ ecosystem, because it is the format that
    their rekordbox software uses to write USB and SD media which can be
    mounted in DJ controllers and used to play and mix music.

    It has been reverse-engineered to facilitate sophisticated
    integrations with light and laser shows, videos, and other musical
    instruments, by supporting deep knowledge of what is playing and
    what is coming next through monitoring the network communications of
    the players.

    The file is divided into fixed-size blocks. The first block has a
    header that establishes the block size, and lists the tables
    available in the database, identifying their types and the index of
    the first of the series of linked pages that make up that table.

    Each table is made up of a series of rows which may be spread across
    any number of pages. The pages start with a header describing the
    page and linking to the next page. The rest of the page is used as a
    heap: rows are scattered around it, and located using an index
    structure that builds backwards from the end of the page. Each row
    of a given type has a fixed size structure which links to any
    variable-sized strings by their offsets within the page.

    As changes are made to the table, some records may become unused,
    and there may be gaps within the heap that are too small to be used
    by other data. There is a bit map in the row index that identifies
    which rows are actually present. Rows that are not present must be
    ignored: they do not contain valid (or even necessarily well-formed)
    data.

    The majority of the work in reverse-engineering this format was
    performed by @henrybetts and @flesniak, for which I am hugely
    grateful. @GreyCat helped me learn the intricacies (and best
    practices) of Kaitai far faster than I would have managed on my own.

    .. seealso::
       Source - https://github.com/Deep-Symmetry/crate-digger/blob/master/doc/Analysis.pdf
    """

    class PageType(Enum):
        tracks = 0
        genres = 1
        artists = 2
        albums = 3
        labels = 4
        keys = 5
        colors = 6
        playlist_tree = 7
        playlist_entries = 8
        unknown_9 = 9
        unknown_10 = 10
        history_playlists = 11
        history_entries = 12
        artwork = 13
        unknown_14 = 14
        unknown_15 = 15
        columns = 16
        unknown_17 = 17
        unknown_18 = 18
        history = 19

    class PageTypeExt(Enum):
        unknown_0 = 0
        unknown_1 = 1
        unknown_2 = 2
        tags = 3
        tag_tracks = 4
        unknown_5 = 5
        unknown_6 = 6
        unknown_7 = 7
        unknown_8 = 8

    def __init__(self, is_ext, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self.is_ext = is_ext
        self._read()

    def _read(self):
        self._unnamed0 = self._io.read_u4le()
        self.len_page = self._io.read_u4le()
        self.num_tables = self._io.read_u4le()
        self.next_unused_page = self._io.read_u4le()
        self._unnamed4 = self._io.read_u4le()
        self.sequence = self._io.read_u4le()
        self.gap = self._io.read_bytes(4)
        if not self.gap == b"\x00\x00\x00\x00":
            raise kaitaistruct.ValidationNotEqualError(
                b"\x00\x00\x00\x00", self.gap, self._io, "/seq/6"
            )
        self.tables = []
        for i in range(self.num_tables):
            self.tables.append(RekordboxPdb.Table(self._io, self, self._root))

    class DeviceSqlString(KaitaiStruct):
        """A variable length string which can be stored in a variety of
        different encodings.
        """

        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.length_and_kind = self._io.read_u1()
            _on = self.length_and_kind
            if _on == 64:
                self.body = RekordboxPdb.DeviceSqlLongAscii(self._io, self, self._root)
            elif _on == 144:
                self.body = RekordboxPdb.DeviceSqlLongUtf16le(
                    self._io, self, self._root
                )
            else:
                self.body = RekordboxPdb.DeviceSqlShortAscii(
                    self.length_and_kind, self._io, self, self._root
                )

    class HistoryPlaylistRow(KaitaiStruct):
        """A row that holds a history playlist ID and name, linking to
        the track IDs captured during a performance on the player.
        """

        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.id = self._io.read_u4le()
            self.name = RekordboxPdb.DeviceSqlString(self._io, self, self._root)

    class PlaylistTreeRow(KaitaiStruct):
        """A row that holds a playlist name, ID, indication of whether it
        is an ordinary playlist or a folder of other playlists, a link
        to its parent folder, and its sort order.
        """

        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.parent_id = self._io.read_u4le()
            self._unnamed1 = self._io.read_bytes(4)
            self.sort_order = self._io.read_u4le()
            self.id = self._io.read_u4le()
            self.raw_is_folder = self._io.read_u4le()
            self.name = RekordboxPdb.DeviceSqlString(self._io, self, self._root)

        @property
        def is_folder(self):
            if hasattr(self, "_m_is_folder"):
                return self._m_is_folder

            self._m_is_folder = self.raw_is_folder != 0
            return getattr(self, "_m_is_folder", None)

    class ColorRow(KaitaiStruct):
        """A row that holds a color name and the associated ID."""

        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self._unnamed0 = self._io.read_bytes(5)
            self.id = self._io.read_u2le()
            self._unnamed2 = self._io.read_u1()
            self.name = RekordboxPdb.DeviceSqlString(self._io, self, self._root)

    class DeviceSqlShortAscii(KaitaiStruct):
        """An ASCII-encoded string up to 127 bytes long."""

        def __init__(self, length_and_kind, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self.length_and_kind = length_and_kind
            self._read()

        def _read(self):
            self.text = (self._io.read_bytes((self.length - 1))).decode("ASCII")

        @property
        def length(self):
            """the length extracted of the entire device_sql_short_ascii type"""
            if hasattr(self, "_m_length"):
                return self._m_length

            self._m_length = self.length_and_kind >> 1
            return getattr(self, "_m_length", None)

    class AlbumRow(KaitaiStruct):
        """A row that holds an album name and ID."""

        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self._unnamed0 = self._io.read_u2le()
            self.index_shift = self._io.read_u2le()
            self._unnamed2 = self._io.read_u4le()
            self.artist_id = self._io.read_u4le()
            self.id = self._io.read_u4le()
            self._unnamed5 = self._io.read_u4le()
            self._unnamed6 = self._io.read_u1()
            self.ofs_name = self._io.read_u1()

        @property
        def name(self):
            """The name of this album."""
            if hasattr(self, "_m_name"):
                return self._m_name

            _pos = self._io.pos()
            self._io.seek((self._parent.row_base + self.ofs_name))
            self._m_name = RekordboxPdb.DeviceSqlString(self._io, self, self._root)
            self._io.seek(_pos)
            return getattr(self, "_m_name", None)

    class Page(KaitaiStruct):
        """A table page, consisting of a short header describing the
        content of the page and linking to the next page, followed by a
        heap in which row data is found. At the end of the page there is
        an index which locates all rows present in the heap via their
        offsets past the end of the page header.
        """

        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.gap = self._io.read_bytes(4)
            if not self.gap == b"\x00\x00\x00\x00":
                raise kaitaistruct.ValidationNotEqualError(
                    b"\x00\x00\x00\x00", self.gap, self._io, "/types/page/seq/0"
                )
            self.page_index = self._io.read_u4le()
            if not (self._root.is_ext):
                self.type = KaitaiStream.resolve_enum(
                    RekordboxPdb.PageType, self._io.read_u4le()
                )

            if self._root.is_ext:
                self.type_ext = KaitaiStream.resolve_enum(
                    RekordboxPdb.PageTypeExt, self._io.read_u4le()
                )

            self.next_page = RekordboxPdb.PageRef(self._io, self, self._root)
            self._unnamed5 = self._io.read_u4le()
            self._unnamed6 = self._io.read_bytes(4)
            self.num_rows_small = self._io.read_u1()
            self._unnamed8 = self._io.read_u1()
            self._unnamed9 = self._io.read_u1()
            self.page_flags = self._io.read_u1()
            self.free_size = self._io.read_u2le()
            self.used_size = self._io.read_u2le()
            self._unnamed13 = self._io.read_u2le()
            self.num_rows_large = self._io.read_u2le()
            self._unnamed15 = self._io.read_u2le()
            self._unnamed16 = self._io.read_u2le()
            if False:
                self.heap = self._io.read_bytes_full()

        @property
        def num_rows(self):
            """The number of rows that have ever been allocated on this
            page (controls the number of row groups there are, but some
            entries in each group may not be marked as present in the
            table due to deletion or updates).
            """
            if hasattr(self, "_m_num_rows"):
                return self._m_num_rows

            self._m_num_rows = (
                self.num_rows_large
                if (
                    (self.num_rows_large > self.num_rows_small)
                    and (self.num_rows_large != 8191)
                )
                else self.num_rows_small
            )
            return getattr(self, "_m_num_rows", None)

        @property
        def num_row_groups(self):
            """The number of row groups that are present in the index. Each
            group can hold up to sixteen rows, but `row_present_flags`
            must be consulted to determine whether each is valid.
            """
            if hasattr(self, "_m_num_row_groups"):
                return self._m_num_row_groups

            self._m_num_row_groups = (self.num_rows - 1) // 16 + 1
            return getattr(self, "_m_num_row_groups", None)

        @property
        def row_groups(self):
            """The actual row groups making up the row index. Each group
            can hold up to sixteen rows. Non-data pages do not have
            actual rows, and attempting to parse them can crash.
            """
            if hasattr(self, "_m_row_groups"):
                return self._m_row_groups

            if self.is_data_page:
                self._m_row_groups = []
                for i in range(self.num_row_groups):
                    self._m_row_groups.append(
                        RekordboxPdb.RowGroup(i, self._io, self, self._root)
                    )

            return getattr(self, "_m_row_groups", None)

        @property
        def heap_pos(self):
            if hasattr(self, "_m_heap_pos"):
                return self._m_heap_pos

            self._m_heap_pos = self._io.pos()
            return getattr(self, "_m_heap_pos", None)

        @property
        def is_data_page(self):
            if hasattr(self, "_m_is_data_page"):
                return self._m_is_data_page

            self._m_is_data_page = (self.page_flags & 64) == 0
            return getattr(self, "_m_is_data_page", None)

    class TagTrackRow(KaitaiStruct):
        """A row that associates a track and a tag (found only in exportExt.pdb files)."""

        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self._unnamed0 = self._io.read_u4le()
            self.track_id = self._io.read_u4le()
            self.tag_id = self._io.read_u4le()
            self._unnamed3 = self._io.read_u4le()

    class RowGroup(KaitaiStruct):
        """A group of row indices, which are built backwards from the end
        of the page. Holds up to sixteen row offsets, along with a bit
        mask that indicates whether each row is actually present in the
        table.
        """

        def __init__(self, group_index, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self.group_index = group_index
            self._read()

        def _read(self):
            pass

        @property
        def base(self):
            """The starting point of this group of row indices."""
            if hasattr(self, "_m_base"):
                return self._m_base

            self._m_base = self._root.len_page - (self.group_index * 36)
            return getattr(self, "_m_base", None)

        @property
        def row_present_flags(self):
            """Each bit specifies whether a particular row is present. The
            low order bit corresponds to the first row in this index,
            whose offset immediately precedes these flag bits. The
            second bit corresponds to the row whose offset precedes
            that, and so on.
            """
            if hasattr(self, "_m_row_present_flags"):
                return self._m_row_present_flags

            _pos = self._io.pos()
            self._io.seek((self.base - 4))
            self._m_row_present_flags = self._io.read_u2le()
            self._io.seek(_pos)
            return getattr(self, "_m_row_present_flags", None)

        @property
        def rows(self):
            """The row offsets in this group."""
            if hasattr(self, "_m_rows"):
                return self._m_rows

            self._m_rows = []
            for i in range(16):
                self._m_rows.append(RekordboxPdb.RowRef(i, self._io, self, self._root))

            return getattr(self, "_m_rows", None)

    class GenreRow(KaitaiStruct):
        """A row that holds a genre name and the associated ID."""

        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.id = self._io.read_u4le()
            self.name = RekordboxPdb.DeviceSqlString(self._io, self, self._root)

    class HistoryEntryRow(KaitaiStruct):
        """A row that associates a track with a position in a history playlist."""

        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.track_id = self._io.read_u4le()
            self.playlist_id = self._io.read_u4le()
            self.entry_index = self._io.read_u4le()

    class ArtworkRow(KaitaiStruct):
        """A row that holds the path to an album art image file and the
        associated artwork ID.
        """

        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.id = self._io.read_u4le()
            self.path = RekordboxPdb.DeviceSqlString(self._io, self, self._root)

    class DeviceSqlLongAscii(KaitaiStruct):
        """An ASCII-encoded string preceded by a two-byte length field in a four-byte header."""

        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.length = self._io.read_u2le()
            self._unnamed1 = self._io.read_u1()
            self.text = (self._io.read_bytes((self.length - 4))).decode("ASCII")

    class ArtistRow(KaitaiStruct):
        """A row that holds an artist name and ID."""

        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.subtype = self._io.read_u2le()
            self.index_shift = self._io.read_u2le()
            self.id = self._io.read_u4le()
            self._unnamed3 = self._io.read_u1()
            self.ofs_name_near = self._io.read_u1()

        @property
        def ofs_name_far(self):
            """For names that might be further than 0xff bytes from the
            start of this row, this holds a two-byte offset, and is
            signalled by the subtype value.
            """
            if hasattr(self, "_m_ofs_name_far"):
                return self._m_ofs_name_far

            if self.subtype == 100:
                _pos = self._io.pos()
                self._io.seek((self._parent.row_base + 10))
                self._m_ofs_name_far = self._io.read_u2le()
                self._io.seek(_pos)

            return getattr(self, "_m_ofs_name_far", None)

        @property
        def name(self):
            """The name of this artist."""
            if hasattr(self, "_m_name"):
                return self._m_name

            _pos = self._io.pos()
            self._io.seek(
                (
                    self._parent.row_base
                    + (self.ofs_name_far if self.subtype == 100 else self.ofs_name_near)
                )
            )
            self._m_name = RekordboxPdb.DeviceSqlString(self._io, self, self._root)
            self._io.seek(_pos)
            return getattr(self, "_m_name", None)

    class TagRow(KaitaiStruct):
        """A row that holds a tag name and its ID (found only in exportExt.pdb files)."""

        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self._unnamed0 = self._io.read_u2le()
            self.tag_index = self._io.read_u2le()
            self._unnamed2 = self._io.read_u8le()
            self.category = self._io.read_u4le()
            self.category_pos = self._io.read_u4le()
            self.id = self._io.read_u4le()
            self.raw_is_category = self._io.read_u4le()
            self._unnamed7 = self._io.read_u2le()
            self.flags = self._io.read_u1()
            self.name = RekordboxPdb.DeviceSqlString(self._io, self, self._root)
            self._unnamed10 = self._io.read_u1()

        @property
        def is_category(self):
            """Indicates whether this row stores a tag category instead of a tag."""
            if hasattr(self, "_m_is_category"):
                return self._m_is_category

            self._m_is_category = self.raw_is_category != 0
            return getattr(self, "_m_is_category", None)

    class PageRef(KaitaiStruct):
        """An index which points to a table page (its offset can be found
        by multiplying the index by the `page_len` value in the file
        header). This type allows the linked page to be lazy loaded.
        """

        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.index = self._io.read_u4le()

        @property
        def body(self):
            """When referenced, loads the specified page and parses its
            contents appropriately for the type of data it contains.
            """
            if hasattr(self, "_m_body"):
                return self._m_body

            io = self._root._io
            _pos = io.pos()
            io.seek((self._root.len_page * self.index))
            self._raw__m_body = io.read_bytes(self._root.len_page)
            _io__raw__m_body = KaitaiStream(BytesIO(self._raw__m_body))
            self._m_body = RekordboxPdb.Page(_io__raw__m_body, self, self._root)
            io.seek(_pos)
            return getattr(self, "_m_body", None)

    class TrackRow(KaitaiStruct):
        """A row that describes a track that can be played, with many
        details about the music, and links to other tables like artists,
        albums, keys, etc.
        """

        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self._unnamed0 = self._io.read_u2le()
            self.index_shift = self._io.read_u2le()
            self.bitmask = self._io.read_u4le()
            self.sample_rate = self._io.read_u4le()
            self.composer_id = self._io.read_u4le()
            self.file_size = self._io.read_u4le()
            self._unnamed6 = self._io.read_u4le()
            self._unnamed7 = self._io.read_u2le()
            self._unnamed8 = self._io.read_u2le()
            self.artwork_id = self._io.read_u4le()
            self.key_id = self._io.read_u4le()
            self.original_artist_id = self._io.read_u4le()
            self.label_id = self._io.read_u4le()
            self.remixer_id = self._io.read_u4le()
            self.bitrate = self._io.read_u4le()
            self.track_number = self._io.read_u4le()
            self.tempo = self._io.read_u4le()
            self.genre_id = self._io.read_u4le()
            self.album_id = self._io.read_u4le()
            self.artist_id = self._io.read_u4le()
            self.id = self._io.read_u4le()
            self.disc_number = self._io.read_u2le()
            self.play_count = self._io.read_u2le()
            self.year = self._io.read_u2le()
            self.sample_depth = self._io.read_u2le()
            self.duration = self._io.read_u2le()
            self._unnamed26 = self._io.read_u2le()
            self.color_id = self._io.read_u1()
            self.rating = self._io.read_u1()
            self._unnamed29 = self._io.read_u2le()
            self._unnamed30 = self._io.read_u2le()
            self.ofs_strings = []
            for i in range(21):
                self.ofs_strings.append(self._io.read_u2le())

        @property
        def unknown_string_8(self):
            """A string of unknown purpose, usually empty."""
            if hasattr(self, "_m_unknown_string_8"):
                return self._m_unknown_string_8

            _pos = self._io.pos()
            self._io.seek((self._parent.row_base + self.ofs_strings[18]))
            self._m_unknown_string_8 = RekordboxPdb.DeviceSqlString(
                self._io, self, self._root
            )
            self._io.seek(_pos)
            return getattr(self, "_m_unknown_string_8", None)

        @property
        def unknown_string_6(self):
            """A string of unknown purpose, usually empty."""
            if hasattr(self, "_m_unknown_string_6"):
                return self._m_unknown_string_6

            _pos = self._io.pos()
            self._io.seek((self._parent.row_base + self.ofs_strings[9]))
            self._m_unknown_string_6 = RekordboxPdb.DeviceSqlString(
                self._io, self, self._root
            )
            self._io.seek(_pos)
            return getattr(self, "_m_unknown_string_6", None)

        @property
        def analyze_date(self):
            """A string containing the date this track was analyzed by rekordbox."""
            if hasattr(self, "_m_analyze_date"):
                return self._m_analyze_date

            _pos = self._io.pos()
            self._io.seek((self._parent.row_base + self.ofs_strings[15]))
            self._m_analyze_date = RekordboxPdb.DeviceSqlString(
                self._io, self, self._root
            )
            self._io.seek(_pos)
            return getattr(self, "_m_analyze_date", None)

        @property
        def file_path(self):
            """The file path of the track audio file."""
            if hasattr(self, "_m_file_path"):
                return self._m_file_path

            _pos = self._io.pos()
            self._io.seek((self._parent.row_base + self.ofs_strings[20]))
            self._m_file_path = RekordboxPdb.DeviceSqlString(self._io, self, self._root)
            self._io.seek(_pos)
            return getattr(self, "_m_file_path", None)

        @property
        def date_added(self):
            """A string containing the date this track was added to the collection."""
            if hasattr(self, "_m_date_added"):
                return self._m_date_added

            _pos = self._io.pos()
            self._io.seek((self._parent.row_base + self.ofs_strings[10]))
            self._m_date_added = RekordboxPdb.DeviceSqlString(
                self._io, self, self._root
            )
            self._io.seek(_pos)
            return getattr(self, "_m_date_added", None)

        @property
        def unknown_string_3(self):
            """A string of unknown purpose; @flesniak said "strange
            strings, often zero length, sometimes low binary values
            0x01/0x02 as content"
            """
            if hasattr(self, "_m_unknown_string_3"):
                return self._m_unknown_string_3

            _pos = self._io.pos()
            self._io.seek((self._parent.row_base + self.ofs_strings[3]))
            self._m_unknown_string_3 = RekordboxPdb.DeviceSqlString(
                self._io, self, self._root
            )
            self._io.seek(_pos)
            return getattr(self, "_m_unknown_string_3", None)

        @property
        def texter(self):
            """A string of unknown purpose, which @flesniak named."""
            if hasattr(self, "_m_texter"):
                return self._m_texter

            _pos = self._io.pos()
            self._io.seek((self._parent.row_base + self.ofs_strings[1]))
            self._m_texter = RekordboxPdb.DeviceSqlString(self._io, self, self._root)
            self._io.seek(_pos)
            return getattr(self, "_m_texter", None)

        @property
        def kuvo_public(self):
            """A string whose value is always either empty or "ON", and
            which apparently for some insane reason is used, rather than
            a single bit somewhere, to control whether the track
            information is visible on Kuvo.
            """
            if hasattr(self, "_m_kuvo_public"):
                return self._m_kuvo_public

            _pos = self._io.pos()
            self._io.seek((self._parent.row_base + self.ofs_strings[6]))
            self._m_kuvo_public = RekordboxPdb.DeviceSqlString(
                self._io, self, self._root
            )
            self._io.seek(_pos)
            return getattr(self, "_m_kuvo_public", None)

        @property
        def mix_name(self):
            """A string naming the remix of the track, if known."""
            if hasattr(self, "_m_mix_name"):
                return self._m_mix_name

            _pos = self._io.pos()
            self._io.seek((self._parent.row_base + self.ofs_strings[12]))
            self._m_mix_name = RekordboxPdb.DeviceSqlString(self._io, self, self._root)
            self._io.seek(_pos)
            return getattr(self, "_m_mix_name", None)

        @property
        def unknown_string_5(self):
            """A string of unknown purpose."""
            if hasattr(self, "_m_unknown_string_5"):
                return self._m_unknown_string_5

            _pos = self._io.pos()
            self._io.seek((self._parent.row_base + self.ofs_strings[8]))
            self._m_unknown_string_5 = RekordboxPdb.DeviceSqlString(
                self._io, self, self._root
            )
            self._io.seek(_pos)
            return getattr(self, "_m_unknown_string_5", None)

        @property
        def unknown_string_4(self):
            """A string of unknown purpose; @flesniak said "strange
            strings, often zero length, sometimes low binary values
            0x01/0x02 as content"
            """
            if hasattr(self, "_m_unknown_string_4"):
                return self._m_unknown_string_4

            _pos = self._io.pos()
            self._io.seek((self._parent.row_base + self.ofs_strings[4]))
            self._m_unknown_string_4 = RekordboxPdb.DeviceSqlString(
                self._io, self, self._root
            )
            self._io.seek(_pos)
            return getattr(self, "_m_unknown_string_4", None)

        @property
        def message(self):
            """A string of unknown purpose, which @flesniak named."""
            if hasattr(self, "_m_message"):
                return self._m_message

            _pos = self._io.pos()
            self._io.seek((self._parent.row_base + self.ofs_strings[5]))
            self._m_message = RekordboxPdb.DeviceSqlString(self._io, self, self._root)
            self._io.seek(_pos)
            return getattr(self, "_m_message", None)

        @property
        def unknown_string_2(self):
            """A string of unknown purpose; @flesniak said "thought
            track number -> wrong!"
            """
            if hasattr(self, "_m_unknown_string_2"):
                return self._m_unknown_string_2

            _pos = self._io.pos()
            self._io.seek((self._parent.row_base + self.ofs_strings[2]))
            self._m_unknown_string_2 = RekordboxPdb.DeviceSqlString(
                self._io, self, self._root
            )
            self._io.seek(_pos)
            return getattr(self, "_m_unknown_string_2", None)

        @property
        def isrc(self):
            """International Standard Recording Code of track
            when known (in mangled format).
            """
            if hasattr(self, "_m_isrc"):
                return self._m_isrc

            _pos = self._io.pos()
            self._io.seek((self._parent.row_base + self.ofs_strings[0]))
            self._m_isrc = RekordboxPdb.DeviceSqlString(self._io, self, self._root)
            self._io.seek(_pos)
            return getattr(self, "_m_isrc", None)

        @property
        def unknown_string_7(self):
            """A string of unknown purpose, usually empty."""
            if hasattr(self, "_m_unknown_string_7"):
                return self._m_unknown_string_7

            _pos = self._io.pos()
            self._io.seek((self._parent.row_base + self.ofs_strings[13]))
            self._m_unknown_string_7 = RekordboxPdb.DeviceSqlString(
                self._io, self, self._root
            )
            self._io.seek(_pos)
            return getattr(self, "_m_unknown_string_7", None)

        @property
        def filename(self):
            """The file name of the track audio file."""
            if hasattr(self, "_m_filename"):
                return self._m_filename

            _pos = self._io.pos()
            self._io.seek((self._parent.row_base + self.ofs_strings[19]))
            self._m_filename = RekordboxPdb.DeviceSqlString(self._io, self, self._root)
            self._io.seek(_pos)
            return getattr(self, "_m_filename", None)

        @property
        def analyze_path(self):
            """The file path of the track analysis, which allows rapid
            seeking to particular times in variable bit-rate files,
            jumping to particular beats, visual waveform previews, and
            stores cue points and loops.
            """
            if hasattr(self, "_m_analyze_path"):
                return self._m_analyze_path

            _pos = self._io.pos()
            self._io.seek((self._parent.row_base + self.ofs_strings[14]))
            self._m_analyze_path = RekordboxPdb.DeviceSqlString(
                self._io, self, self._root
            )
            self._io.seek(_pos)
            return getattr(self, "_m_analyze_path", None)

        @property
        def comment(self):
            """The comment assigned to the track by the DJ, if any."""
            if hasattr(self, "_m_comment"):
                return self._m_comment

            _pos = self._io.pos()
            self._io.seek((self._parent.row_base + self.ofs_strings[16]))
            self._m_comment = RekordboxPdb.DeviceSqlString(self._io, self, self._root)
            self._io.seek(_pos)
            return getattr(self, "_m_comment", None)

        @property
        def release_date(self):
            """A string containing the date this track was released, if known."""
            if hasattr(self, "_m_release_date"):
                return self._m_release_date

            _pos = self._io.pos()
            self._io.seek((self._parent.row_base + self.ofs_strings[11]))
            self._m_release_date = RekordboxPdb.DeviceSqlString(
                self._io, self, self._root
            )
            self._io.seek(_pos)
            return getattr(self, "_m_release_date", None)

        @property
        def autoload_hot_cues(self):
            """A string whose value is always either empty or "ON", and
            which apparently for some insane reason is used, rather than
            a single bit somewhere, to control whether hot-cues are
            auto-loaded for the track.
            """
            if hasattr(self, "_m_autoload_hot_cues"):
                return self._m_autoload_hot_cues

            _pos = self._io.pos()
            self._io.seek((self._parent.row_base + self.ofs_strings[7]))
            self._m_autoload_hot_cues = RekordboxPdb.DeviceSqlString(
                self._io, self, self._root
            )
            self._io.seek(_pos)
            return getattr(self, "_m_autoload_hot_cues", None)

        @property
        def title(self):
            """The title of the track."""
            if hasattr(self, "_m_title"):
                return self._m_title

            _pos = self._io.pos()
            self._io.seek((self._parent.row_base + self.ofs_strings[17]))
            self._m_title = RekordboxPdb.DeviceSqlString(self._io, self, self._root)
            self._io.seek(_pos)
            return getattr(self, "_m_title", None)

    class KeyRow(KaitaiStruct):
        """A row that holds a musical key and the associated ID."""

        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.id = self._io.read_u4le()
            self.id2 = self._io.read_u4le()
            self.name = RekordboxPdb.DeviceSqlString(self._io, self, self._root)

    class PlaylistEntryRow(KaitaiStruct):
        """A row that associates a track with a position in a playlist."""

        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.entry_index = self._io.read_u4le()
            self.track_id = self._io.read_u4le()
            self.playlist_id = self._io.read_u4le()

    class LabelRow(KaitaiStruct):
        """A row that holds a label name and the associated ID."""

        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.id = self._io.read_u4le()
            self.name = RekordboxPdb.DeviceSqlString(self._io, self, self._root)

    class DeviceSqlLongUtf16le(KaitaiStruct):
        """A UTF-16LE-encoded string preceded by a two-byte length field in a four-byte header."""

        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.length = self._io.read_u2le()
            self._unnamed1 = self._io.read_u1()
            self.text = (self._io.read_bytes((self.length - 4))).decode("UTF-16LE")

    class Table(KaitaiStruct):
        """Each table is a linked list of pages containing rows of a single
        type. This header describes the nature of the table and links to
        its pages by index.
        """

        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            if not (self._root.is_ext):
                self.type = KaitaiStream.resolve_enum(
                    RekordboxPdb.PageType, self._io.read_u4le()
                )

            if self._root.is_ext:
                self.type_ext = KaitaiStream.resolve_enum(
                    RekordboxPdb.PageTypeExt, self._io.read_u4le()
                )

            self.empty_candidate = self._io.read_u4le()
            self.first_page = RekordboxPdb.PageRef(self._io, self, self._root)
            self.last_page = RekordboxPdb.PageRef(self._io, self, self._root)

    class RowRef(KaitaiStruct):
        """An offset which points to a row in the table, whose actual
        presence is controlled by one of the bits in
        `row_present_flags`. This instance allows the row itself to be
        lazily loaded, unless it is not present, in which case there is
        no content to be loaded.
        """

        def __init__(self, row_index, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self.row_index = row_index
            self._read()

        def _read(self):
            pass

        @property
        def row_base(self):
            """The location of this row relative to the start of the page.
            A variety of pointers (such as all device_sql_string values)
            are calculated with respect to this position.
            """
            if hasattr(self, "_m_row_base"):
                return self._m_row_base

            self._m_row_base = self.ofs_row + self._parent._parent.heap_pos
            return getattr(self, "_m_row_base", None)

        @property
        def body_ext(self):
            """The actual content of the row in an exportExt.pdb file, as long as it is present."""
            if hasattr(self, "_m_body_ext"):
                return self._m_body_ext

            if (self.present) and (self._root.is_ext):
                _pos = self._io.pos()
                self._io.seek(self.row_base)
                _on = self._parent._parent.type_ext
                if _on == RekordboxPdb.PageTypeExt.tags:
                    self._m_body_ext = RekordboxPdb.TagRow(self._io, self, self._root)
                elif _on == RekordboxPdb.PageTypeExt.tag_tracks:
                    self._m_body_ext = RekordboxPdb.TagTrackRow(
                        self._io, self, self._root
                    )
                self._io.seek(_pos)

            return getattr(self, "_m_body_ext", None)

        @property
        def body(self):
            """The actual content of the row, as long as it is present."""
            if hasattr(self, "_m_body"):
                return self._m_body

            if (self.present) and (not (self._root.is_ext)):
                _pos = self._io.pos()
                self._io.seek(self.row_base)
                _on = self._parent._parent.type
                if _on == RekordboxPdb.PageType.playlist_tree:
                    self._m_body = RekordboxPdb.PlaylistTreeRow(
                        self._io, self, self._root
                    )
                elif _on == RekordboxPdb.PageType.keys:
                    self._m_body = RekordboxPdb.KeyRow(self._io, self, self._root)
                elif _on == RekordboxPdb.PageType.artists:
                    self._m_body = RekordboxPdb.ArtistRow(self._io, self, self._root)
                elif _on == RekordboxPdb.PageType.albums:
                    self._m_body = RekordboxPdb.AlbumRow(self._io, self, self._root)
                elif _on == RekordboxPdb.PageType.genres:
                    self._m_body = RekordboxPdb.GenreRow(self._io, self, self._root)
                elif _on == RekordboxPdb.PageType.history_playlists:
                    self._m_body = RekordboxPdb.HistoryPlaylistRow(
                        self._io, self, self._root
                    )
                elif _on == RekordboxPdb.PageType.artwork:
                    self._m_body = RekordboxPdb.ArtworkRow(self._io, self, self._root)
                elif _on == RekordboxPdb.PageType.playlist_entries:
                    self._m_body = RekordboxPdb.PlaylistEntryRow(
                        self._io, self, self._root
                    )
                elif _on == RekordboxPdb.PageType.labels:
                    self._m_body = RekordboxPdb.LabelRow(self._io, self, self._root)
                elif _on == RekordboxPdb.PageType.tracks:
                    self._m_body = RekordboxPdb.TrackRow(self._io, self, self._root)
                elif _on == RekordboxPdb.PageType.history_entries:
                    self._m_body = RekordboxPdb.HistoryEntryRow(
                        self._io, self, self._root
                    )
                elif _on == RekordboxPdb.PageType.colors:
                    self._m_body = RekordboxPdb.ColorRow(self._io, self, self._root)
                self._io.seek(_pos)

            return getattr(self, "_m_body", None)

        @property
        def present(self):
            """Indicates whether the row index considers this row to be
            present in the table. Will be `false` if the row has been
            deleted.
            """
            if hasattr(self, "_m_present"):
                return self._m_present

            self._m_present = (
                True
                if ((self._parent.row_present_flags >> self.row_index) & 1) != 0
                else False
            )
            return getattr(self, "_m_present", None)

        @property
        def ofs_row(self):
            """The offset of the start of the row (in bytes past the end of
            the page header).
            """
            if hasattr(self, "_m_ofs_row"):
                return self._m_ofs_row

            _pos = self._io.pos()
            self._io.seek((self._parent.base - (6 + (2 * self.row_index))))
            self._m_ofs_row = self._io.read_u2le()
            self._io.seek(_pos)
            return getattr(self, "_m_ofs_row", None)
