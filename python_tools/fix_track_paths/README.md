# fix_track_paths

`fix_track_paths` uses the information from a music player
 in order to fix the tracks locations in the Mixxx database.  

**ATTENTION**: I've attempting modifying the Mixxx's database directly from Python (using pandas)… it did not work! So here's the method I've adopted:  

1. Using Python to generate a custom database, by matching the "artist/title/album" fields of Mixxx with the ones of the music player.
We first try an exact match then do a closest match on the remaining tracks.  
2. Using sqlite3 to update the Mixxx's database using the custom database.

Beside fixing the tracks locations, you can also decide if you want to delete the corresponding keys/gains/waveforms, since they can/will be modified if you use a new track format. Edit the `config.sh` file to fit your preferences.

Note:

- So far only Clementine (my favourite player) has been considered (see `clementine_custom_music_db.py`).  
- The tracks metadata (artist/title/album) are not updated, and Mixxx will not do it either. You can do so in Mixxx (right click > metadata > read from file)

To run it, simply use:  

```bash
bash fix_track_paths.sh
```
