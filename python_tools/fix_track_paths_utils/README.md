# fix_track_paths

`fix_track_paths` uses the information from a music player
 in order to fix the tracks locations in the Mixxx database.

So far only Clementine (my favourite player) has been considered (see `clementine_custom_music_db.py`).

NOTE: The tracks metadata (artist/title/album) are not updated, and Mixxx will not do it either. You can do so in Mixxx (right click > metadata > read from file)
