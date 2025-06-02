#!/bin/bash
# shellcheck source=config.sh

source $(dirname $0)/python_tools/fix_track_paths_utils/config.sh

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

    if $delete_keys; then
        echo "Deleting the keys of the modified tracks"
        sqlite3  "$temp" < "$delete_keys_sql"
        test $? -ne 0 && exit
    fi

    if "$delete_gains"; then
        echo "Deleting the gains of the modified tracks"
        sqlite3  "$temp" < "$delete_gains_sql"
        test $? -ne 0 && exit
    fi

    if "$delete_waveforms"; then
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
