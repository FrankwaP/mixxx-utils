# Tips for Linux users using a Windows virtual machine

**IMPORTANT**
[rbxport](https://github.com/chrisle/rbxport) will soon make a VM useless <3
But as of 2026-11-19, there's still some fix to do… at least [this one](https://github.com/chrisle/rbxport/pull/856).


I have chosen [Virtual Box](https://www.virtualbox.org/) to create a Windows [Tiny11](https://tiny11.net/) virtual machine (VM).

This means that from Linux, I open the Virtual Box software to launch my Windows instance/VM.
As one can guess, this has a performance cost compared to a dual-boot. But for Rekordbox on a modern laptop, the gain in convenience is worth it.

## Virtual Box and Windows Tiny11 installation

The installations are easy so any tutorial will do the trick.

Now you need to:

1. (On the Windows VM) Install the [Guest Additions](https://docs.oracle.com/en/virtualization/virtualbox/6.0/user/guestadd-install.html)
2. (On Linux) Add your user name to the `vboxusers` group so you can access the USB key from the VM: `sudo usermod -a -G vboxusers $USER`


## Note on the folder names

In the following explanations I have used the names in my actual configuration.

Of course you will probably need to adapt to your case.

Just remember to:

- edit the configuration file
- make sure that you pick the Windows drive letters once and for all.


## Shared folders

### "Linux folder > Windows drive" Virtual Box link

It's the basic one you have to use. In Virtual Box, click on the VM then "Configuration > Shared Folders". The VM must be closed to be able to edit its configuration.

### "Windows drive > Windows path" Windows symbolic link

Virtual Box can only link a Linux folder to a Windows drive (not a path). In some "advanced" cases you might want your Linux shared folder to be used as a Windows path.
Symbolic links are the answer: in Windows open a cmd prompt as administrator and use `mklink /D windows_drive windows_path`.

### Rekordbox data folder

On Windows, the Rekordbox data folder is `%APPDATA%\Pioneer\`.
(`%APPDATA%` is a convenient variable that expands to `C:\Users\your_user_name\AppData\Roaming`)

One can decide not to do anything special about it, in this case the Rekordbox data (with the libraries, the analysis…) will be stored into the VM file.

I have decided to use a shared Linux folder to store it, as I like the idea of easily accessing it through Linux alone. As an example, I use [Unison synchroniser](https://github.com/bcpierce00/unison) to maintain a backup of this folder.

Let's say this shared folder is named `rekordbox_virtualbox` on Linux.

In this case you can create:

1. On the Linux side, a Virtual Box link between `rekordbox_virtualbox` and `Z:`
2. On the (virtual) Windows side, a symbolic link between `Z:` and `%APPDATA%\Pioneer\`.


If you want to use an existing Rekordbox library, this is the time to paste the corresponding content (your existing `%APPDATA%\Pioneer\` folder) into the `rekordbox_virtualbox` folder!

### Music folder

Let's say your music folder is named `Music` on Linux.


1. On the Linux side, a Virtual Box link between `Music` and `E:`
2. On the (virtual) Windows side, a symbolic link between `E:` and `%USERPROFILE%\Music`

Note that the drive letter must be used for the `rekordbox_library_folder` variable in `mixxx_to_rekordbox.toml`.

## Handling the USB key when exporting

This is how I **avoid having a corrupted USB drive that crashes Pioneer hardware**:

1. Plug the USB key on your PC. **Do not** mount the USB key on Linux. You may need to disable auto-mount on your system.
2. On Virtual Box, right click on the USB key symbol in the bottom right of the window,
and activate your USB key (mine is called "Unknown device…"). This will plug your USB key into the Virtual Machine (you'll hear the "do doung!" sound).
3. The USB key is now available in Rekordbox: you can do your export
4. Eject the USB key using the eject icon on Rekordbox
5. Undo step 2. to deactivate/unplug the USB key on Virtual Box ("dee doung!").
6. Done!
