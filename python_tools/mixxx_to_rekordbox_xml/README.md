`mixxx_to_rekordbox_xml` export the information of the Mixxx's library 
into the [xml format used by Rekordbox](https://cdn.rekordbox.com/files/20200410160904/xml_format_list.pdf).

You can then use Rekordbox to prepare a USB key: it's free for this use.

It exports:
  - the tracks locations/BPM/key/...
  - the hot cues as memory cues and you decide if you keep the hot cues
  - the playlists

Set your preferences in the `config.ini`. Then to run the script, simply use:  
```bash
python mixxx_to_rekordbox_xml.py
```

To import the XML file in Rekorbox:  
1. Get into "export" mode. Side note: the settings panels differ from the "performance" mode's ones, so if you want some info/help you need to make it clear that it is for the "export" mode.
1. Set up the correct xml import path in "settings > database".
2. Activate the xml view in "settings > view".

Extra recommendation for Rekordbox, since you already have the BPM, key, gain… from Mixxx:
- go to "settings > analysis" to:
 - deactivate the automatic analysis so you keep the values 
 - untick BPM/key/etc...
 - (don't worry the waveform will still be computed during the export) 

Also here are great tips to prepare your first USB key using Rekordbox:
- [From Rekordbox to a CDJ USB and tips for first time CDJ users](https://youtu.be/A5f85g-Kvhg)
- [I HATED Using CDJs Until I Learnt This Hack](https://youtu.be/pznqHFsNo2g) #typical2023title.

Note to dev: the "Total Time" information is mandatory for the cue points to work.

