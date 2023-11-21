from sys import exit, path
from pathlib import Path

import pandas as pd

path.append('../utils')  # It works that's what matters :-p
from music_db_utils import (
    MERGE_COLS,
    CUSTOM_DB_COLUMNS,
    open_table_as_df,
    write_df_to_table,
    file_url_to_path,
    get_closest_matches_indices,
    open_mixxx_library,
)
from user_parameters import CLEM_DB, CUSTOM_DB, CUSTOM_DB_TABLE_NAME

if __name__ == '__main__':
    answer = input("Did you refresh Clementine's library (y/*)? ")
    if answer != "y":
        print("Well do it <3")
        exit()

    df_custom = open_table_as_df(CLEM_DB, "songs")


    # %% Changing/modifying the main columns so they fit CUSTOM_DB_COLUMNS

    # we only need to create file_path
    df_custom["file_path"] = df_custom["filename"].apply(file_url_to_path)


    df_custom = df_custom[CUSTOM_DB_COLUMNS]


    # %% Cleaning the Player's db

    # droping when file does not exist (Clementine can keep the deleted tracks in its db)
    df_custom = df_custom[df_custom["file_path"].apply(lambda p: Path(p).exists())]


    # %% Matching the tracks between Mixxx and the music player
    df_mixxx = open_mixxx_library()
    df_mixxx = df_mixxx[MERGE_COLS]

    # saving the original indices
    IDX_MIXXX = "saved_index_mixxx"
    IDX_PLAYER = "saved_index_player"

    df_mixxx[IDX_MIXXX] = df_mixxx.index
    df_custom[IDX_PLAYER] = df_custom.index

    # %%% Perfect match (pm)
    df_merge = pd.merge(
        left=df_custom,
        right=df_mixxx,
        how="inner",
        on=None,
        left_on=MERGE_COLS,
        right_on=MERGE_COLS,
    )

    df_custom_pm = df_merge[CUSTOM_DB_COLUMNS]


    # %%% Close match (cm)

    # first the tracks with no match (nm)
    df_mixxx_nm = df_mixxx.drop(df_merge[IDX_MIXXX])
    df_custom_nm = df_custom.drop(df_merge[IDX_PLAYER])

    # finding the closest match (cm) for each Mixxx track
    if len(df_mixxx_nm):
        print(
            f"{len(df_mixxx_nm)} tracks have not been found: "
            "we find the closest match for each one…"
        )

        df_mixxx_nm[MERGE_COLS] = df_mixxx_nm[MERGE_COLS].fillna("")
        df_custom_nm[MERGE_COLS] = df_custom_nm[MERGE_COLS].fillna("")

        df_custom_cm = pd.DataFrame()

        for _, row in df_mixxx_nm.iterrows():

            close_indices = get_closest_matches_indices(
                row, df_custom_nm, MERGE_COLS
            )

            print(f"\nClosest match for Mixxx entry {row[MERGE_COLS].tolist()}:")
            for i, idx in enumerate(close_indices):
                print(f"{i}:\t{df_custom.loc[idx, MERGE_COLS].tolist()}")

            ans = input(
                "Please choose an index or leave empty to cancel the operation: "
            )
            try:
                idx = close_indices[int(ans)]
                # we force the index to stay the same so we can use them indefferently between each dataset
                df_custom_cm = pd.concat(
                    [df_custom_cm, df_custom_nm.loc[[idx]]], ignore_index=False
                )  # the double [[]] is important so it's a dataframe
                df_custom_cm.loc[idx, MERGE_COLS] = row[MERGE_COLS]

            except:
                print("Please fix it manually <3")


    # %% Regrouping the perfect and close matches
    df_custom_final = pd.concat([df_custom_pm, df_custom_cm])

    df_custom_final = df_custom_final[CUSTOM_DB_COLUMNS]

    write_df_to_table(
        df_custom_final,
        db_path=CUSTOM_DB,
        table_name=CUSTOM_DB_TABLE_NAME,
        overwrite=True,
    )
