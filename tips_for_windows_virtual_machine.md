# Tips for Linux users using a Windows virtual machine


I have chosen [Virtual Box](https://www.virtualbox.org/) to create a Windows [Tiny11](https://tiny11.net/) virtual machine (VM).

This means that from Linux, I open the Virtual Box software to launch my Windows instance/VM.
As one can guess, this has a performance cost comparing to a dual-boot. But for Rekordbox on a modern laptop, the gain in convenience is worth it.



## Virtual Box and Windows Tiny11 installation

The installations are easy so any tutorial will do the trick.

Now you need to:

1. (On the Windows VM) Install the [Guest Additions](https://docs.oracle.com/en/virtualization/virtualbox/6.0/user/guestadd-install.html)
2. (On Linux) Add your user name to the `vboxusers` group so you can access the USB key from the VM: `sudo usermod -a -G vboxusers $USER`


## Shared folders

### Note on drive letters

I am using the (Windows) drives letters I use (`E:` and `Z:`).
You can change them, but remember that life will be easier if you pick them once and for all.


### "Linux folder > Windows drive" Virtual Box link

It's the basic one that you have to use. In Virtual Box, click on the VM then "Configuration > Shared Folders". The VM must be closed to be able to edit its configuration.


### "Windows drive > Windows path" Windows symbolic link

Virtual Box can only link a Linux folder to a Windows drive (not a path). In some "advanced" cases you might want your Linux shared folder to be used as a Windows path.
Symbolic links are the answer: in Windows open a cmd prompt as administrator and use `mklink windows_drive windows_path`.


### Rekordbox data folder

On Windows, the Rekordbox data folder is `%APPDATA%\Pioneer\`.
(`%APPDATA%` is a convenient variable that expands to `C:\Users\your_user_name\AppData\Roaming`)

One can decide not to do anything special about it, in this case the Rekordbox data (with the libraries, the analysis…) will be stored into the VM file.

I have decided to use a shared Linux folder to store it, as I like the idea of easily accessing it through Linux alone. As an example, I use [Unison synchroniser](https://github.com/bcpierce00/unison)) to maintain a backup of this folder on a hard drive.

In this case you can create:

1. A Virtual Box link between "rekordbox_preferences" and "Z:"
2. A symbolic link between "Z:" and `%APPDATA%\Pioneer\`: `mklink Z: %APPDATA%\Pioneer\`


If you want to use an existing Rekordbox library, this is the time to paste the content of the `%APPDATA%\Pioneer\` folder !


### Music folder



If you statr with a blank Rekordbox library, you can create:

1. A Virtual Box link between "rekordbox_preferences" and "E:"


If you want to use an existing Rekordbox library, and your music was stored in `C:\Users\your_user_name\Music`, you can create:

1. A Virtual Box link between "rekordbox_preferences" and "E:"
2. A symbolic link between "E:" and `C:\Users\your_user_name\Music`: `mklink E: C:\Users\your_user_name\Music`

Note that the drive letter must be used for the `rekordbox_library_folder` variable defined in the `config.toml` file.


## Handling the USB key when exporting

This is how I **avoid having a corrupted USB drive that crashes Pionner hardwares**:

1. Plug the USB key on your PC. **Do not** mount the USB key on Linux. You may need to disable auto-mount on your system.
2. On Virtual Box, right click on the USB key symbol in the bottom right of the window,
and activate your USB key (mine is called "Unknown device…"). This will plug your USB key on the Virtual Machaine (you'll hear the "do doung!" sound).
3. The USB key is now available in Rekordbox: you can do your export
4. Eject the USB key using the eject icon on Rekordbox
5. Undo step 2. to de-activate/unplug the USB key on Virtual Box ("dee doung!").
6. Done!
