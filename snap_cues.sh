#!/bin/bash
# shellcheck source=config.sh

cd "$(dirname "$0")" || exit

# SQL files for each operations
fix_cues_sql=python_tools/snap_cues/mixxxdb_fix_cues.sql
#
mixxx_db=$(toml get --toml-path python_tools/config.toml mixxx.mixxx_db)
backup=${mixxx_db}.bak.$(date +%y%m%d%H%M)

# The names <<MUST>> correspond to the ones defined in
# python_tools/snap_cues/clementine_custom_music_db.py
# <<DO NOT>> change them.
# A more robust solution will be used when Windows users are interested.
custom_db=/tmp/custom_music_db.sqlite

# generating the custom database
python3 -m python_tools.snap_cues.snap_cues || exit

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
