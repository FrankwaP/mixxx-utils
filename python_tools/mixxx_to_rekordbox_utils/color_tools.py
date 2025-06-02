# -*- coding: utf-8 -*-
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


def _dec_to_rgb(rgb_int: int) -> RGB_TUPPLE:
    blue = rgb_int & 255
    green = (rgb_int >> 8) & 255
    red = (rgb_int >> 16) & 255
    return red, green, blue


def _colour_square_distance(rgb_tuple1: RGB_TUPPLE, rgb_tuple2: RGB_TUPPLE) -> float:
    return sum((i - j) ** 2 for i, j in zip(rgb_tuple1, rgb_tuple2))


def _nearest_colour(query) -> RGB_TUPPLE:
    return min(
        REKORDBOX_COLORS.keys(),
        key=lambda rek_col: _colour_square_distance(rek_col, query),
    )


def convert_colors_for_rekordbox(color_column: Series) -> None:
    # we work on unique values to convert
    # then use pandas to replace all occurences
    unq_col = color_column.dropna().unique()
    for color in unq_col:
        # fixing
        try:
            color = int(color)
        except TypeError:
            raise NotImplementedError(
                "Only single integers are considered for Mixxx colors"
            )
        rgb_tuple = _dec_to_rgb(color)
        #
        try:
            rgb_hex = REKORDBOX_COLORS[rgb_tuple]
        except KeyError:
            rgb_tuple = _nearest_colour(rgb_tuple)
            rgb_hex = REKORDBOX_COLORS[rgb_tuple]
        color_column.replace(to_replace=color, value=rgb_hex, inplace=True)
