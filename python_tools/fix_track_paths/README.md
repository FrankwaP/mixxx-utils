# fix_track_paths

`fix_track_paths` uses the information from a music player
 in order to fix the tracks locations in the Mixxx database.  

**ATTENTION**: I've attempting modifying the Mixxx's database directly from Python (using pandas)… it did not work! So here's the method I've adopted:  

1. Using Python to generate a custom database, by matching the "artist/title/album" fields of Mixxx with the ones of the music player.
We first try an exact match then do a closest match on the remaining tracks.  
2. Using sqlite3 to update the *track_locations* table of the Mixxx's database using the custom database (see `mixxxdb_fix_tracks_locations.sql` for the commands).

Note:

- So far only Clementine (my favourite player) has been considered (see `clementine_custom_music_db.py`).  
- The *library* table is not updated, if the tracks tags are modified, please update them in Mixxx might need to be refreshed (right click > metadata > read from file)

You can see these two steps in the `fix_track_paths.sh`.  
To run it, simply use:  

```bash
bash fix_track_paths.sh
```
