# mixxx_to_rekordbox_xml

`mixxx_to_rekordbox_xml` export the information of the Mixxx's library
into the [xml format used by Rekordbox](https://cdn.rekordbox.com/files/20200410160904/xml_format_list.pdf).
You can then use Rekordbox to prepare a USB key (no license needed).

`mixxx_to_rekordbox_xml` exports the BPM, key, score/energy, color, beat grid, hot cues (as both memory and hot cues), the playlists, the crates (as playlists).

## Suggestions for people using Mixxx on Linux

So far one still needs to **use Rekordbox on Windows**.
While Rekordbox can run on Wine [with a few tricks](https://erhan.es/blog/running-pioneer-rekordbox-on-linux/),
I have not find how to make it recognize a USB key as an export device.

So that left us with two options:

1. Using a Linux/Windows dual boot.
2. Using a Windows virtual machine on Linux.

In both cases you have to options regarding how to make your music available on Windows:

1. Having your music on a shared partition (dual-boot case) or folder (virtual machine case).
2. Having your music on an external drive.

In both cases **make sure that Windows will give the same letter to the drive each time!** (you can do it in *Disk Management*).
Else each time the drive letter changes (let's say from `D:` to `E:`), your songs will be considered as new ones, and Rekordbox will analyse them once again: you'll end up with one analysis for `D:\some_track` and one analysis for `E:\some_track`.

If at some point you had such problem, clean the Rekordbox library by deleting all the tracks using the old drive letter. You might have warning about tracks belonging to a playlist: it's fine, the playlist was incorrect, just reimport it from the Mixxx's XML.

**My preference went for a Windows virtual machine with a shared folder**. If you want to follow this path, please see [my recommendations](tips_for_windows_virtual_machine.md).


## Import in Rekordbox

To import the XML file in Rekorbox:

1. Get into "export" mode. Side note: the settings panels differ from the "performance" mode's ones, so if you want some info/help you need to make it clear that it is for the "export" mode.
2. Set up the correct xml import path in "settings > database".
3. Activate the xml view in "settings > view".

Since you already have the BPM, key, gain… from Mixxx, you can prevent Rekordbox from recomputing these, going to "settings > analysis" to:

- deactivate the automatic analysis so you keep the values
- untick BPM/key/etc...
- (don't worry the waveform will still be computed during the export)


Now… let's avoid a nervous meltdown because of the implicit/blackbox behaviour of Rekordbox:

1. For the *XML > Rekordbox* import, always import the tracks, not the playlists. Else RB will skip the tracks that are already present (the track location exists) in its collection, to save analysis time. So open each playlist of your choice, select the tracks, and *right click > import*.
2. For the *Rekordbox > USB key* export, always use *Right Click > Export* not the *Sync Manager*. I don't remember 100% TBH, but I think it also has to do with updating or not tracks informations when they are already present in the key database.

Extreme case: it happened to me that some music files were damaged (they sounded like a scratched vinyle). In this case the only solution I've found was to… delete the content of the USB key, and export all my tracks once again :-(
But to my surprise this actually does not take so long, here are my rough observations:

1. Consider 30s for a *XML > Rekordbox* track first import (with all the extra files generation, like the waveforms files…)
2. Consider 2s for a *XML > Rekordbox* track information update
3. Consider 0.5s for a *Rekordbox > USB 3* track export


## Extra Ressources

Here are great tips to prepare your first USB key using Rekordbox:

- [From Rekordbox to a CDJ USB and tips for first time CDJ users](https://youtu.be/A5f85g-Kvhg)
- [I HATED Using CDJs Until I Learnt This Hack](https://youtu.be/pznqHFsNo2g) #typical2023title.

## Note to devs

The "Total Time" information is **mandatory** for the cue points to work.
