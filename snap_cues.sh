#!/bin/bash
# shellcheck source=config.sh

source python_tools/snap_cues/config.sh

# generating the custom database
python3 python_tools/snap_cues/snap_cues.py || exit

if test -f "$custom_db"; then

    # creating a tmp file
    temp=$(mktemp)
    cp -f "$mixxx_db" "$temp"

    echo "Snapping the cues locations to the beatgrid"
    sqlite3  "$temp" < "$fix_cues_sql"
    test $? -ne 0 && exit

    # create a backup
    cp "$mixxx_db" "$backup"
    # (over)write Mixxx DB
    mv -f "$temp" "$mixxx_db"
    # delete the custom database
    rm -f "$custom_db"

fi
