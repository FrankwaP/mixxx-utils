# mixxx-utils

This repo offers tools that I use with [Mixxx](https://github.com/mixxxdj/mixxx) and its database.


`mixxx_prepare.sh` uses the commands recommended in the [wiki](https://github.com/mixxxdj/mixxx/wiki/Adjusting%20Audio%20Latency)
in order to minimize the latency problems in Linux.  
It must be executed before launching Mixxx as follow:  
```bash
sudo ./mixxx_prepare.sh
```

`mixxxdb_cleanup.sql` is a copy of a script found in the [offical repo](https://github.com/mixxxdj/mixxx/tree/main/tools):  
So far I've only added a single command (noted with "EXTRA" in the comment).  
To use it:  
```bash
cp ${HOME}/.mixxx/mixxxdb.sqlite ${HOME}/.mixxx/mixxxdb.sqlite.bak.$(date +%y%m%d%H%M)
sqlite3  ${HOME}/.mixxx/mixxxdb.sqlite  < mixxxdb_cleanup.sql
```

There are Python tools, with separate folders and README files.  
Here's a summary:

`fix_track_paths` is a Python tool to fix the tracks paths, using the informations from 
your music player database. It is usefull when the file has been renamed or if the track is 
now in another format (for example you wanted a better quality format and went from a mp3 to a flac file).


`mixxx_to_rekordbox_xml` does what it says but YES IT EXPORTS THE HOT CUES :-) 





