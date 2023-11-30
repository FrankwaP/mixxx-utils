#!/bin/bash

# generating the custom database
python3 clementine_custom_music_db.py
test $? -ne 0 && exit

# creating a backup
cp ${HOME}/.mixxx/mixxxdb.sqlite ${HOME}/.mixxx/mixxxdb.sqlite.bak.$(date +%y%m%d%H%M)

# using the information of the custom database to modify Mixxx's database
sqlite3  ${HOME}/.mixxx/mixxxdb.sqlite < mixxxdb_fix_tracks_locations.sql
test $? -ne 0 && exit

# deleting the custom database
rm -f custom_music_db.sqlite
