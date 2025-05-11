from dataclasses import dataclass

import pandas as pd

from .proto import keys_pb2  # type:ignore


@dataclass
class KeyMapInfo:

    global_key_camelot: str

    def __init__(self, library_row: pd.Series):
        keymap = keys_pb2.KeyMap()  # type:ignore
        keymap.ParseFromString(library_row["keys"])
        key = keys_pb2.ChromaticKey.Name(keymap.global_key)  # type:ignore
        pass


# made using the SQL command "SELECT DISTINCT key_id, key FROM library"
# then some Regex…

_key_id_lancelot = {
    21: "1A",
    12: "1B",
    16: "2A",
    7: "2B",
    23: "3A",
    2: "3B",
    18: "4A",
    9: "4B",
    13: "5A",
    4: "5B",
    20: "6A",
    11: "6B",
    15: "7A",
    6: "7B",
    22: "8A",
    1: "8B",
    17: "9A",
    8: "9B",
    24: "10A",
    3: "10B",
    19: "11A",
    10: "11B",
    14: "12A",
    5: "12B",
}


def key_id_to_lancelot(key_id: int) -> str:
    if key_id in _key_id_lancelot:
        return _key_id_lancelot[key_id]
    return ""
