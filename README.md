# mixxx-utils

This repo offers tools that I use with [Mixxx](https://github.com/mixxxdj/mixxx) and its database.
They are stored in language specific "*language*-tools" folders, along with specific README.md files.

They work on Linux. For Windows there might be a few adaptations needed to make it work…
I can totally do it, but unless someone shows an interest, I'm going to play the [YAGNI](https://en.wikipedia.org/wiki/You_aren%27t_gonna_need_it) card :-)

IMPORTANT: As of May 4th 2024, Mixxx's database needs to be fixed so the Python tools work.
 Please see the[fix_mixxx_db.md](fix_mixxx_db.md) file.

## Python tools

`cue_to_tracklist.py` is a Python tool to generate the tracklist corresponding to the cue file
automatically generated when recording a mix on Mixxx, so you can add it in the description of the Soundcloud/Youtube/… page.

`fix_track_paths` is a Python tool to fix the tracks paths, using the informations from your music player database.
It is usefull when the file has been renamed or if the track is now in another format
(for example you wanted a better quality format and went from a mp3 to a flac file).
It works with Clementine's database so far, but it won't be hard to add other players' databases.

`mixxx_to_rekordbox_xml` export your Mixxx library into the [Rekorbox XML format](https://cdn.rekordbox.com/files/20200410160904/xml_format_list.pdf) and
**YES IT EXPORTS THE PLAYLISTS, HOT CUES, BEATGRIDS, COLORS, RATING/ENERGY** :-)
Then you can import the XML file in Rekordbox to prepare a USB key. Rekordbox is free for this use.
So far one still needs to **use Rekordbox on Windows**.
While Rekordbox can run on Wine [with a few tricks](https://erhan.es/blog/running-pioneer-rekordbox-on-linux/),
I have not find how to make it recognize a USB key as an export device.

`snap_cues` snaps all the cue points to the closest beat.

## SQL tools

`delete_old_keys.sql` is used when you got want to delete keys that are calculated with a specific detector.
I used it because I had a mix of keys calculated with "Queen Mary (qm-keydetector)" and "KeyFinder",
and I selectively deleted the QM keys so the could be recalculated with KF.

`fix_false_missing_tracks.sql` is useful when Mixxx incorrectly detects tracks as missing
(you can still use them with a drag-and-drop from the library). It simply resets all the "missing" field.

`mixxxdb_cleanup.sql` is a copy of a script found in the [offical repo](https://github.com/mixxxdj/mixxx/tree/main/tools)
with extra commands (noted with "EXTRA" in the comment).

## Bash tools

`mixxx_prepare.sh` uses the commands recommended in the [wiki](https://github.com/mixxxdj/mixxx/wiki/Adjusting%20Audio%20Latency)
in order to minimize the latency problems in Linux. I call it before launching Mixxx (at least for live mixing).
