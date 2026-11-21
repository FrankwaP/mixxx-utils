from collections.abc import Hashable
from typing import TypeVar

from .dataclasses_utils import Row, RowTypes, Table

_OtherRow = TypeVar("_OtherRow", bound=RowTypes)


MatchKey = tuple[Hashable, ...]


def get_match_key(row: RowTypes, on: tuple[str, ...]) -> MatchKey:
    return tuple(getattr(row, i) for i in on)


def get_match_dict(
    table: Table[Row], on: tuple[str, ...], assert_unique: bool
) -> dict[MatchKey, Table[Row]]:
    out: dict[MatchKey, Table[Row]] = {}
    for r in table:
        key = get_match_key(r, on)
        if key in out:
            if assert_unique:
                raise AssertionError("The keys built with columns {on} are not unique!")
            out[key].append(r)
        else:
            out[key] = Table([r])
    return out


def pseudo_inner_join_product(
    left: Table[Row],
    right: Table[_OtherRow],
    on_left: tuple[str, ...],
    on_right: tuple[str, ...],
    assert_unique_left: bool,
    assert_unique_right: bool,
) -> tuple[Table[Row], Table[_OtherRow]]:
    assert not left or all(i in left[0].__annotations__ for i in on_left)
    assert not right or all(i in right[0].__annotations__ for i in on_right)

    dict_match_left = get_match_dict(left, on_left, assert_unique_left)
    dict_match_right = get_match_dict(right, on_right, assert_unique_right)

    out_left: Table[Row] = Table()
    out_right: Table[_OtherRow] = Table()
    for key in sorted(dict_match_left.keys() & dict_match_right.keys()):
        for left_row in dict_match_left[key]:
            for right_row in dict_match_right[key]:
                out_left.append(left_row)
                out_right.append(right_row)
    return out_left, out_right


def pseudo_inner_join_left_to_right_mapping(
    left: Table[Row],
    right: Table[_OtherRow],
    on_left: tuple[str, ...],
    on_right: tuple[str, ...],
) -> dict[MatchKey, Table[_OtherRow]]:
    assert not left or all(i in left[0].__annotations__ for i in on_left)
    assert not right or all(i in right[0].__annotations__ for i in on_right)

    dict_match_left = get_match_dict(left, on_left, True)
    dict_match_right = get_match_dict(right, on_right, False)

    return {
        key: dict_match_right[key]
        for key in dict_match_left.keys() & dict_match_right.keys()
    }


def filter_right_using_left(
    left: Table[Row],
    right: Table[_OtherRow],
    on_left: tuple[str, ...],
    on_right: tuple[str, ...],
) -> Table[Row]:
    mapping = pseudo_inner_join_left_to_right_mapping(left, right, on_left, on_right)
    return Table(r for r in left if get_match_key(r, on_left) in mapping)
