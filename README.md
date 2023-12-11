# mixxx-utils

This repo offers tools that I use with [Mixxx](https://github.com/mixxxdj/mixxx) and its database.

There are especially **Python tools**, with separate folders and README files.  
Here's a summary:

`fix_track_paths` is a Python tool to fix the tracks paths, using the informations from 
your music player database. It is usefull when the file has been renamed or if the track is 
now in another format (for example you wanted a better quality format and went from a mp3 to a flac file).  
It works with Clementine's database so far, but it won't be hard to add other players' databases.

`mixxx_to_rekordbox_xml` export your Mixxx library into the [Rekorbox XML format](https://cdn.rekordbox.com/files/20200410160904/xml_format_list.pdf) and **YES IT EXPORTS THE PLAYLISTS, HOT CUES AND BEATGRIDS** :-)  
Then you can import the XML file in Rekordbox to prepare a USB key (Rekorbox is free for this use, and can probably run on Wine).

**If you are a Git/Python noob**, here's what I suggest:
- [Download this repo](https://github.com/FrankwaP/mixxx-utils/archive/refs/heads/main.zip), unzip it, and open the "python_tools" folder (leave this window opened).
- [Install Mambaforge](https://mamba.readthedocs.io/en/latest/installation/mamba-installation.html) with the default settings.

Now open a terminal (omg so scary :-p ) and:
1. Create an Mamba environment:`mamba create --name mixxx-utils --yes pandas sqlalchemy jellyfish sqlite`. (An "environment" is simply a folder with compatible executables and libraries.)
2. Activate this new environment: `mamba activate mixxx-utils`. ("Activating" means that the executables and libraries in the environement folder will be used when you execute code.)
3. Change the path:  
   1. On Windows type `chdir̀ /D` and on Linux type `cd`
   2. Then go back to the windows you've opened, and drag&drop the folder you want to use in the terminal, which will write the path to the folder. So you end up with something like `chdir /D D:\...\mixxx_to_rekordbox_xml` or `cd /home/.../mixxx_to_rekordbox_xml`. 
   3. Execute the command (press "Enter")
4. Execute the python tool  like explained in the README.md file.


Other small scripts that I'm using:  

`mixxx_prepare.sh` uses the commands recommended in the [wiki](https://github.com/mixxxdj/mixxx/wiki/Adjusting%20Audio%20Latency)
in order to minimize the latency problems in Linux.  
It must be executed before launching Mixxx as follow:  
```bash
sudo ./mixxx_prepare.sh
```

`mixxxdb_cleanup.sql` is a copy of a script found in the [offical repo](https://github.com/mixxxdj/mixxx/tree/main/tools):  
So far I've only added a single command (noted with "EXTRA" in the comment).  
To use it on Linux:  
```bash
cp ${HOME}/.mixxx/mixxxdb.sqlite ${HOME}/.mixxx/mixxxdb.sqlite.bak.$(date +%y%m%d%H%M)
sqlite3  ${HOME}/.mixxx/mixxxdb.sqlite  < mixxxdb_cleanup.sql
```
