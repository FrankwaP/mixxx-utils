# mixxx_to_rekordbox_compare

When importing an XML file in Rekordbox, modified tracks (new colour, new
rating, new tempo, new cues…) need to be re-imported.

If we do not know which tracks have been modified, the only solution is to
re-import all the tracks, which is very time consuming!

This tool generates a playlist containing the tracks that have been modified
since last Mixxx to Rekordbox import.

To do so it compares:

1. the XML (freshly) exported from Mixxx, using `mixxx_to_rekordbox.py`
2. the XML (freshly) exported from Rekordbox clicking on
   `File > Export collection in XML format`

Edit the corresponding paths in `mixxx_to_rekordbox_compare.toml`. The file can
be overridden with the `MIXXX_TO_REKORDBOX_COMPARE_CONF` environment variable.

## IMPORTANT NOTE

We are mostly here because we want to prepare a USB key for gigs. In this case,
we **have to** do the whole "Mixxx > Rekordbox > USB" each time!

Else, here's an example of what will happen:

- version 6 of Mixxx library
- version 4 of Rekordbox library
- version 1 of the USB device library

What we want is to know the updates between v6 and v1. But what we can only have
is the updates between v6 dans v4.

Doing the whole pipeline each time makes sure that the version is identical
between Rekordbox and the USB device.
