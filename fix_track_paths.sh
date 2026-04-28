#!/bin/bash
# shellcheck source=config.sh

cd "$(dirname "$0")" || exit

sql_folder=python_tools/fix_track_paths_utils/sql
fix_track_locations_sql=$sql_folder/mixxxdb_fix_tracks_locations.sql
delete_keys_sql=$sql_folder/mixxxdb_delete_keys.sql
delete_gains_sql=$sql_folder/mixxxdb_delete_gains.sql
get_waveforms_ids_sql=$sql_folder/mixxxdb_get_waveforms_ids.sql
delete_waveforms_sql=$sql_folder/mixxxdb_delete_waveforms.sql

mixxx_db=$(toml get --toml-path python_tools/config.toml mixxx.mixxx_db)
backup=${mixxx_db}.bak.$(date +%y%m%d%H%M)
mixxx_waveforms_folder=$(dirname "$mixxx_db")/analysis/

delete_keys=$(toml get --toml-path python_tools/config.toml fix_track_paths.delete_keys)
delete_gains=$(toml get --toml-path python_tools/config.toml fix_track_paths.delete_gains)
delete_waveforms=$(toml get --toml-path python_tools/config.toml fix_track_paths.delete_waveforms)


# The names <<MUST>> correspond to the ones defined in
# python_tools/fix_track_paths_utils/clementine_custom_music_db.py
# <<DO NOT>> change them.
# A more robust solution will be used when Windows users are interested.
custom_db=/tmp/custom_music_db.sqlite


# generating the custom database
python -m python_tools.fix_track_paths
test $? -ne 0 && exit

if test -f "$custom_db"; then

    # creating a tmp file
    temp=$(mktemp)
    cp -f "$mixxx_db" "$temp"

    echo "Fixing the tracks locations"
    sqlite3  "$temp" < "$fix_track_locations_sql"
    test $? -ne 0 && exit

    if [ $delete_keys == "True" ]; then
        echo "Deleting the keys of the modified tracks"
        sqlite3  "$temp" < "$delete_keys_sql"
        test $? -ne 0 && exit
    fi

    if [ "$delete_gains" == "True" ]; then
        echo "Deleting the gains of the modified tracks"
        sqlite3  "$temp" < "$delete_gains_sql"
        test $? -ne 0 && exit
    fi

    if [ "$delete_waveforms" == "True" ]; then
        echo "Deleting the waveforms of the modified tracks"
        for wave_id in $(sqlite3  "$temp" < "$get_waveforms_ids_sql"); do
            rm "$mixxx_waveforms_folder/$wave_id" 2> /dev/null
        done
        sqlite3  "$temp" < "$delete_waveforms_sql"
        test $? -ne 0 && exit
    fi


    # create a backup
    cp "$mixxx_db" "$backup"
    # (over)write Mixxx DB
    mv -f "$temp" "$mixxx_db"
    # delete the custom database
    rm -f "$custom_db"

fi
