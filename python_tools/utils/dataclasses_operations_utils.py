from collections.abc import Hashable
from typing import TypeVar

from .dataclasses_utils import Row, RowTypes, Table

_OtherRow = TypeVar("_OtherRow", bound=RowTypes)


MatchKey = tuple[Hashable, ...]


def get_match_key(row: RowTypes, on: tuple[str, ...]) -> MatchKey:
    return tuple(getattr(row, i) for i in on)


def _assert_fields_exist(table: Table[Row], fields: tuple[str, ...]) -> None:
    if table:
        assert all(
            i in table[0].get_fields() for i in fields
        ), f"Some fields {fields} are not present in {table[0].get_fields()}"


def get_match_dict(
    table: Table[Row], on: tuple[str, ...], assert_unique: bool
) -> dict[MatchKey, Table[Row]]:

    _assert_fields_exist(table, on)
    out: dict[MatchKey, Table[Row]] = {}
    for r in table:
        key = get_match_key(r, on)
        if key in out:
            if assert_unique:
                dups = Table([r, out[key][0]])
                raise AssertionError(
                    f"The keys built with columns {on} of are not unique!\n"
                    "(it might be from a mix with a cue file)\n"
                    f"{dups}"
                )
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
    """Return matching rows from the left and right tables.

    Rows are matched by comparing values from ``on_left`` in the left table
    with values from ``on_right`` in the right table.
    """

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


def pseudo_inner_join_outer(
    left: Table[Row],
    right: Table[_OtherRow],
    on_left: tuple[str, ...],
    on_right: tuple[str, ...],
    assert_unique_left: bool,
    assert_unique_right: bool,
) -> tuple[Table[Row], Table[_OtherRow]]:
    """Return rows whose join keys are not present in the other table.

    Left-only rows are returned as the left result and right-only rows as the
    right result. Matching rows are omitted.
    """

    dict_match_left = get_match_dict(left, on_left, assert_unique_left)
    dict_match_right = get_match_dict(right, on_right, assert_unique_right)

    out_left: Table[Row] = Table()
    out_right: Table[_OtherRow] = Table()
    for key in sorted(dict_match_left.keys() - dict_match_right.keys()):
        for left_row in dict_match_left[key]:
            out_left.append(left_row)
    for key in sorted(dict_match_right.keys() - dict_match_left.keys()):
        for right_row in dict_match_right[key]:
            out_right.append(right_row)
    return out_left, out_right


def pseudo_inner_join_left_to_right_mapping(
    left: Table[Row],
    right: Table[_OtherRow],
    on_left: tuple[str, ...],
    on_right: tuple[str, ...],
) -> dict[MatchKey, Table[_OtherRow]]:
    """Map each matching left join key to rows from the right table.

    Left join keys are required to be unique. Right join keys may have
    multiple rows.
    """
    dict_match_left = get_match_dict(left, on_left, True)
    dict_match_right = get_match_dict(right, on_right, False)

    return {
        key: dict_match_right[key]
        for key in dict_match_left.keys() & dict_match_right.keys()
    }


def filter_left_using_right(
    left: Table[Row],
    right: Table[_OtherRow],
    on_left: tuple[str, ...],
    on_right: tuple[str, ...],
) -> Table[Row]:
    """Filter the left table to rows with a join key in the right table.

    This is a filter, not a join: matching left rows are returned once each,
    even when the right table contains multiple rows with the same key.
    """
    mapping = pseudo_inner_join_left_to_right_mapping(left, right, on_left, on_right)
    return Table(r for r in left if get_match_key(r, on_left) in mapping)


def filter_left_using_right_outer(
    left: Table[Row],
    right: Table[_OtherRow],
    on_left: tuple[str, ...],
    on_right: tuple[str, ...],
) -> Table[Row]:
    """Filter the left table to rows without a join key in the right table.

    This function is just to propose an interface coherent to filter_left_using_right,
    as "join outer" does not duplicate rows as "join product"
    """
    mapping = pseudo_inner_join_left_to_right_mapping(left, right, on_left, on_right)
    return Table(r for r in left if get_match_key(r, on_left) not in mapping)
