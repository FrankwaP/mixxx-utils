#!/bin/bash
# shellcheck disable=SC2034

# SQL files for each operations
fix_cues_sql=mixxxdb_fix_cues.sql
#
mixxx_db=${HOME}/.mixxx/mixxxdb.sqlite
backup=${HOME}/.mixxx/mixxxdb.sqlite.bak.$(date +%y%m%d%H%M)
# this one MUST correspond to the one defined in config.py
custom_db=custom_music_db.sqlite
