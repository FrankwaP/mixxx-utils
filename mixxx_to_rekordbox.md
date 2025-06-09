# mixxx_to_rekordbox_xml

`mixxx_to_rekordbox_xml` export the information of the Mixxx's library
into the [xml format used by Rekordbox](https://cdn.rekordbox.com/files/20200410160904/xml_format_list.pdf).

You can then use Rekordbox to prepare a USB key: it's free for this use.

It exports:

- the tracks locations/BPM/key/...
- the hot cues as memory cues and you decide if you keep the hot cues
- the playlists and crates (as playlists)

## Suggestion for people using Mixxx on Linux

So far one still needs to **use Rekordbox on Windows**.
While Rekordbox can run on Wine [with a few tricks](https://erhan.es/blog/running-pioneer-rekordbox-on-linux/),
I have not find how to make it recognize a USB key as an export device.

So that left you with two options:

1. having your music on a shared FAT/NTFS partition
2. having your music on an external drive

In both cases, but especially with the 2nd option, **make sure that Windows will give the same letter to the drive each time!**
Else all your songs will be considered as new ones, and Rekordbox will:

- analyse them once again: you'll end up with one analysis for "D:\some_track" and one analysis for "E:\some_track".
- export them to your USB key once again, copying all the files for "E:\some_track" and deleting all the files for "D:/some_track".

If you know Rekordbox well, you know that means you might waste a lot of time.

If at some point you had such problem, clean the Rekordbox library by deleting all the tracks have a path with the old letter. You might have warning about tracks belonging to a playlist: it's fine, the playlist was incorrect, just reimport it from the Mixxx's XML.

## Run the script

Set your preferences in config.py. Then to run the script, simply run the Python:

```bash
python mixxx_to_rekordbox_xml.py
```

Noobs: remember to ativate the Python environment :-)

## Import in Rekordbox

To import the XML file in Rekorbox:

1. Get into "export" mode. Side note: the settings panels differ from the "performance" mode's ones, so if you want some info/help you need to make it clear that it is for the "export" mode.
2. Set up the correct xml import path in "settings > database".
3. Activate the xml view in "settings > view".

Since you already have the BPM, key, gain… from Mixxx, you can prevent Rekordbox from recomputing these, going to "settings > analysis" to:

- deactivate the automatic analysis so you keep the values
- untick BPM/key/etc...
- (don't worry the waveform will still be computed during the export)

## Ressources

Here are great tips to prepare your first USB key using Rekordbox:

- [From Rekordbox to a CDJ USB and tips for first time CDJ users](https://youtu.be/A5f85g-Kvhg)
- [I HATED Using CDJs Until I Learnt This Hack](https://youtu.be/pznqHFsNo2g) #typical2023title.

## Note to devs

The "Total Time" information is mandatory for the cue points to work.
