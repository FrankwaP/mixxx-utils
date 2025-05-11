from typing import Mapping
from typing import Optional
from xml.etree import ElementTree as ET


AttribDict = Mapping[str, object]


def stringify_dict(d: AttribDict) -> dict[str, str]:
    return {k: str(v) for k, v in d.items()}


def get_elem(name: str, attrib: Optional[AttribDict] = None) -> ET.Element:
    if attrib is None:
        attrib = {}
    return ET.Element(name, attrib=stringify_dict(attrib))
