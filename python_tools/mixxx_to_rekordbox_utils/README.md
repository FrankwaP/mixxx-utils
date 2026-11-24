# mixxx_to_rekordbox_xml

Rekordbox is a shitty software. There I said it.

There are 2 steps:

1. Importing the XML file in Rekordbox collection
2. Exporting the Rekordbox collection to a USB device

## Importing the XML file in Rekordbox collection

### Settings

1. Get into "export" mode. Side note: the settings panels differ from the
   "performance" mode's ones, so if you want some info/help you need to make it
   clear that it is for the "export" mode.
2. Set up the correct xml import path in "settings > database".
3. Activate the xml view in "settings > view".

Since you already have the BPM, key, gain… from Mixxx, you can prevent Rekordbox
from recomputing these, going to "settings > analysis" to:

- deactivate the automatic analysis so you keep the values
- untick BPM/key/etc...
- (don't worry the waveform will still be computed during the export)

### Import In the navigation panel of Rekordbox.

1. Refresh the XML information.
2. Right-click on the main playlist field and import all the playlists.
3. The new tracks will be imported by this process… but the modified ones won't,
   so you need to right click and import them. How to remember which tracks are
   updated? And how to quickly select them? Well someone very kind has written
   the `mixxx_to_rekordbox_compare` tool and you should have a look.

## Exporting the Rekordbox collection to a USB device

### Exporting the playlists

After importing the playlists in step 1, the Rekordbox Sync Manager detects them
as new playlists, and he will very stupidly remove the playlists and their
tracks from the USB key… before writing them again. And it will do it so slowly
that it's embarrassing. (You'd better off deleting the `export.pdb` file
directly…)

So I recommend you simply right-click on the playlists you want to export in
Rekordbox collection, and export to the USB device.

If you have a lot of playlists, you might want to know which playlist has been
updated… and yes `mixxx_to_rekordbox_compare` will be helpful.

## Updating the tracks

Also explicitely right click and export the updated tracks. Once again:
`mixxx_to_rekordbox_compare`

## Extra Resources

Here are great tips to prepare your first USB key using Rekordbox:

- [From Rekordbox to a CDJ USB and tips for first time CDJ users](https://youtu.be/A5f85g-Kvhg)
- [I HATED Using CDJs Until I Learnt This Hack](https://youtu.be/pznqHFsNo2g)
  #typical2023title.

## Suggestions for people using Mixxx on Linux

**IMPORTANT** [rbxport](https://github.com/chrisle/rbxport) will soon make a VM
useless \<3 But as of 2026-11-19, there's still some fix to do… at least
[this one](https://github.com/chrisle/rbxport/pull/856).

So far one still needs to **use Rekordbox on Windows**. While Rekordbox can run
on Wine
[with a few tricks](https://erhan.es/blog/running-pioneer-rekordbox-on-linux/),
I have not found how to make it recognize a USB key as an export device. Please
share any tips you have regarding this \<3

So that left us with two options:

1. Using a Linux/Windows dual boot.
2. Using a Windows virtual machine on Linux.

In both cases you have two options regarding how to make your music available on
Windows:

1. Having your music on a shared partition (dual-boot case) or folder (virtual
   machine case).
2. Having your music on an external drive.

In both cases **make sure that Windows will give the same letter to the drive
each time!** (you can do it in *Disk Management*). Else each time the drive
letter changes (let's say from `D:` to `E:`), your songs will be considered as
new ones, and Rekordbox will analyse them once again: you'll end up with one
analysis for `D:\some_track` and one analysis for `E:\some_track`.

If at some point you had such problem, clean the Rekordbox library by deleting
all the tracks using the old drive letter. You might have warning about tracks
belonging to a playlist: it's fine, the playlist was incorrect, just reimport it
from the Mixxx's XML.

**My preference went for a Windows virtual machine with a shared folder**. If
you want to follow this path, please see
[my recommendations](tips_for_windows_virtual_machine.md).
