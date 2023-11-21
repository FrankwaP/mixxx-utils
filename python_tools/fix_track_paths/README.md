`fix_track_paths` uses the information from a music player
 in order to fix the tracks locations in the Mixxx database.  

**ATTENTION**: I've attempting modifying the Mixxx's database directly 
from Python (using pandas)… it did not work! So here's the method I've adopted:  
1. Using Python to generate a custom database, linking the "artist/title/album" field of Mixxx 
to the "path" field of the player. So far only Clementine (my favourite player) has been considered (see `clementine_custom_music_db.py`).   
2. Using SQL to modify the Mixxx's database using the custom database (see `mixxxdb_fix_tracks_locations.sql` for the commands).

You can see these two steps in the `fix_track_paths.sh`.  
To run it, simply use:  
```bash
bash fix_track_paths.sh
```
