#!/bin/bash
# shellcheck disable=SC2034

# since changing the track file can impact the key, gain and waveform
# we can decide to delete them so Mixxx recompute them
# (for some reasons, the bitrate is updated)
delete_keys=true
delete_gains=true
delete_waveforms=true
# SQL files for each operations
fix_track_locations_sql=mixxxdb_fix_tracks_locations.sql
delete_keys_sql=mixxxdb_delete_keys.sql
delete_gains_sql=mixxxdb_delete_gains.sql
get_waveforms_ids_sql=mixxxdb_get_waveforms_ids.sql
delete_waveforms_sql=mixxxdb_delete_waveforms.sql
#
mixxx_db=${HOME}/.mixxx/mixxxdb.sqlite
backup=${HOME}/.mixxx/mixxxdb.sqlite.bak.$(date +%y%m%d%H%M)
mixxx_waveforms_folder=${HOME}/.mixxx/analysis/
# this one MUST correspond to the one defined in config.py
custom_db=custom_music_db.sqlite
