`mixxx_to_rekordbox_xml` export the information of the Mixxx's library 
into the [xml format used by Rekordbox](https://cdn.rekordbox.com/files/20200410160904/xml_format_list.pdf).

To use it in Rekorbox:  
1. set up the correct xml import path in the "database" panel
2. activate the xml view in the "view" panel

Note that you will need to adapt the track locations if Mixxx is installed on Linux (something like `/media/usb_key/Music` to `D:/Music`).  

Note to dev: the "Total Time" information is mandatory for the cue points to work.

To run it, simply use:  
```bash
python mixxx_to_rekordbox_xml.py
```
