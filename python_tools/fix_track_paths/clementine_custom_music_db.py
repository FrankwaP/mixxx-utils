from sys import exit, path
from pathlib import Path

import pandas as pd

import sys

sys.path = ["/home/francois/Documents/mixxx-utils/python_tools/utils"] + sys.path
# path.append("../utils")  # It works that's what matters :-p
from music_db_utils import (
    MERGE_COLS,
    open_table_as_df,
    write_df_to_table,
    file_url_to_path,
    get_closest_matches_indices,
    open_mixxx_library,
)
from user_parameters import (
    CLEM_DB,
    CUSTOM_DB,
    CUSTOM_DB_TABLE_NAME,
    CUSTOM_DB_MIXXX_IDX_COLUMN,
    CUSTOM_DB_PATH_COLUMN,
)

if __name__ == "__main__":
    answer = input("Did you refresh Clementine's library (y/*)? ")
    if answer != "y":
        print("Well do it <3")
        exit()

    df_custom = open_table_as_df(CLEM_DB, "songs")

    # %% Changing/modifying the main columns so they fit CUSTOM_DB_COLUMNS

    # we only need to create file_path
    df_custom[CUSTOM_DB_PATH_COLUMN] = df_custom["filename"].apply(file_url_to_path)

    # %% Cleaning the Player's db

    # droping when file does not exist (Clementine can keep the deleted tracks in its db)
    df_custom = df_custom[
        df_custom[CUSTOM_DB_PATH_COLUMN].apply(lambda p: Path(p).exists())
    ]

    # %% Matching the tracks between Mixxx and the music player
    df_mixxx = open_mixxx_library(keep_only_missing_track=True)

    # saving the original indices

    df_mixxx[CUSTOM_DB_MIXXX_IDX_COLUMN] = df_mixxx['location']

    IDX_MIXXX = "saved_index_mixxx"
    df_mixxx[IDX_MIXXX] = df_mixxx.index
    IDX_CUSTOM = "saved_index_custom"
    df_custom[IDX_CUSTOM] = df_custom.index

    # %%% Perfect match (pm)
    df_custom_pm = pd.merge(
        left=df_custom,
        right=df_mixxx,
        how="inner",
        on=None,
        left_on=MERGE_COLS,
        right_on=MERGE_COLS,
    )

    df_custom_final = df_custom_pm

    # %%% Close match (cm)

    # first the tracks with no match (nm)
    df_mixxx_nm = df_mixxx.drop(df_custom_pm[IDX_MIXXX])
    df_custom_nm = df_custom.drop(df_custom_pm[IDX_CUSTOM])

    # finding the closest match (cm) for each Mixxx track
    if len(df_mixxx_nm):
        print(
            f"{len(df_mixxx_nm)} tracks have not been found: "
            "we find the closest match for each one…"
        )

        df_mixxx_nm[MERGE_COLS] = df_mixxx_nm[MERGE_COLS].fillna("")
        df_custom_nm[MERGE_COLS] = df_custom_nm[MERGE_COLS].fillna("")

        list_for_df = []

        for idx_mixxx, row in df_mixxx_nm.iterrows():
            close_indices = get_closest_matches_indices(row, df_custom_nm, MERGE_COLS)

            print(f"\nClosest match for Mixxx entry {row[MERGE_COLS].tolist()}:")
            for i, idx in enumerate(close_indices):
                print(f"{i}:\t{df_custom.loc[idx, MERGE_COLS].tolist()}")

            ans = None
            while ans not in [""] + [str(i) for i, _ in enumerate(close_indices)]:
                ans = input(
                    "Please: choose an index or leave empty to skip the operation: "
                )

            if ans == "":
                print("Please fix it manually <3")
            else:
                idx_custom = close_indices[int(ans)]
                list_for_df.append(
                    [
                        df_mixxx_nm.loc[idx_mixxx, CUSTOM_DB_MIXXX_IDX_COLUMN],
                        df_custom_nm.loc[idx_custom, CUSTOM_DB_PATH_COLUMN],
                    ]
                )

        df_custom_cm = pd.DataFrame(
            list_for_df, columns=[CUSTOM_DB_MIXXX_IDX_COLUMN, CUSTOM_DB_PATH_COLUMN]
        )
        df_custom_final = pd.concat([df_custom_pm, df_custom_cm])

    # %% Final filtering/output
    df_custom_final = df_custom_final[
        [CUSTOM_DB_MIXXX_IDX_COLUMN, CUSTOM_DB_PATH_COLUMN]
    ]
    write_df_to_table(
        df_custom_final,
        db_path=CUSTOM_DB,
        table_name=CUSTOM_DB_TABLE_NAME,
        overwrite=True,
    )
