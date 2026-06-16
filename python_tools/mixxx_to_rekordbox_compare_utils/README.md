# mixxx_to_rekordbox_compare

When importing an XML file in Rekordbox, modified tracks
(new colour, new rating, new tempo, new cues…) need to be re-imported.

If we do not know which tracks have been modified, the only solution is to re-import
all the tracks, which is very time consuming!

This tool generates a playlist containing the tracks that have been modified
since last Mixxx to Rekordbox import.

To do do so it compares:

 1. the XML exported from Mixxx, using `mixxx_to_rekordbox.py`
 2. the XML exported from Rekordbox clicking on `File > Export collection in XML format`

Edit the corresponding paths in the configuration file `python_tools/config.toml`.
