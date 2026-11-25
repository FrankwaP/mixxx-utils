from dataclasses import Field, dataclass, fields
from pathlib import Path
from typing import Self, get_origin
from urllib.parse import unquote
from xml.etree import ElementTree as ET

from ..utils.dataclasses_utils import Row, Table


def _field_to_xml_name(f: Field) -> str:
    n = f.name
    return n[0].upper() + n[1:]


def _normalize_location(loc: str) -> str:
    loc = unquote(loc)
    loc = loc.removeprefix("file://localhost/")
    loc = loc.replace("\\", "/")
    return loc


@dataclass
class XmlRow:
    @classmethod
    def kwargs_from_xml(cls, xml: ET.Element) -> dict[str, str]:
        att = {
            k.name: xml.attrib.get(_field_to_xml_name(k), "")
            for k in fields(cls)
            if get_origin(k.type) is not Table
        }
        return att

    @classmethod
    def from_xml(cls: type[Self], xml: ET.Element) -> Self:
        return cls(**cls.kwargs_from_xml(xml))


@dataclass
class XmlMarkRow(XmlRow, Row):
    type: str | None
    start: str | None
    end: str | None
    num: str | None
    # DO NOT use Metro as RkBox does not export it correctly (always "4/4")
    # "Metro",


@dataclass
class XmlTempoRow(XmlRow, Row):
    inizio: str | None
    bpm: str | None


@dataclass
class XmlTrackRow(XmlRow, Row):
    # do not use  trackID to compare rows or merge tables
    # as Rekordbox increments each time we re-import a track
    trackID: str
    name: str | None
    artist: str | None
    album: str | None
    rating: str | None
    location: str
    tonality: str | None
    colour: str | None
    marks: Table[XmlMarkRow]
    tempos: Table[XmlTempoRow]

    @classmethod
    def get_print_fields(cls) -> tuple[str, ...]:
        return ("location",)

    @classmethod
    def get_compare_fields(cls) -> tuple[str, ...]:
        return tuple(f.name for f in fields(cls) if f.name != "trackID")

    def __eq__(self, other) -> bool:
        return all(
            getattr(self, f) == getattr(other, f)
            for f in type(self).get_compare_fields()
        )

    @classmethod
    def from_xml(cls, xml: ET.Element) -> Self:

        marks = Table(
            sorted(
                (XmlMarkRow.from_xml(elem) for elem in xml.findall("POSITION_MARK")),
                key=lambda x: (x.start, x.num),
            )
        )

        tempos: Table[XmlTempoRow] = Table(
            sorted(
                (XmlTempoRow.from_xml(elem) for elem in xml.findall("TEMPO")),
                key=lambda x: (x.inizio,),
            )
        )

        tempos = Table[XmlTempoRow]()
        for elem in xml.findall("TEMPO"):
            tempos.append(XmlTempoRow.from_xml(elem))
            xml.remove(elem)
        attr = super().kwargs_from_xml(xml)
        attr["location"] = _normalize_location(attr["location"])
        return cls(**attr, marks=marks, tempos=tempos)


class XmlTrackTable(Table[XmlTrackRow]):
    @classmethod
    def from_xml(cls, xml_path: Path) -> Self:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        return cls(
            XmlTrackRow.from_xml(track) for track in root.findall(".//COLLECTION/TRACK")
        )
