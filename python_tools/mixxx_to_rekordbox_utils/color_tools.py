# -*- coding: utf-8 -*-
import numpy as np
from pandas import Series

REKORDBOX_COLORS = {
    (255, 0, 0): "0xFF0000",  # Red
    (255, 165, 0): "0xFFA500",  # Orange
    (255, 255, 0): "0xFFFF00",  # 0xFFFF00
    (0, 255, 0): "0x00FF00",  # Green
    (37, 253, 233): "0x25FDE9",  # Turquoise
    (0, 0, 255): "0x0000FF",  # Blue
    (102, 0, 153): "0x660099",  # Violet
    (255, 0, 127): "0xFF007F",  # Rose
}

RGB_TUPPLE = tuple[int, int, int]


def _colour_square_distance(rgb_tuple1: RGB_TUPPLE, rgb_tuple2: RGB_TUPPLE) -> float:
    return sum((i - j) ** 2 for i, j in zip(rgb_tuple1, rgb_tuple2))


def _nearest_colour(rgb_tuple: RGB_TUPPLE) -> RGB_TUPPLE:
    return min(
        REKORDBOX_COLORS.keys(),
        key=lambda rek_rgb_col: _colour_square_distance(rek_rgb_col, rgb_tuple),
    )


def _dec_to_rgb(rgb_int: int) -> RGB_TUPPLE:
    assert isinstance(rgb_int, int)
    rgb_int = int(rgb_int)
    blue = rgb_int & 255
    green = (rgb_int >> 8) & 255
    red = (rgb_int >> 16) & 255
    return red, green, blue


def _convert(val: float) -> str:
    assert isinstance(val, float)
    if np.isnan(val):
        return ""
    intval = int(val)
    assert intval == val
    try:
        return REKORDBOX_COLORS[_dec_to_rgb(intval)]
    except KeyError:
        return REKORDBOX_COLORS[_nearest_colour(_dec_to_rgb(intval))]


def convert_colors_for_rekordbox(color_column: Series) -> Series:
    # we work on unique values to convert
    # then use pandas to replace all occurences
    return color_column.apply(_convert)
