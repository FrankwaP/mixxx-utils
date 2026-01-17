# Install Mixxx with libKeyFinder (Debian/Ubuntu)

Since there is no Debian/Ubuntu package with libKeyFinder, we must install it from sources.
Here are instructions on how to do it.

## Why libKeyFinder?

From [KEY DETECTION COMPARISON 2020](https://www.reddit.com/r/DJs/comments/hwlzyt/key_detection_comparison_2020/):

![What???](https://i.redd.it/zs186m2cpnc51.png "KEY DETECTION COMPARISON 2020")

Basicall you'll go from one of the worst to one of the best…

*Note*: Here's a nice input from Mixed In Key's creator:
> if you give the same song to 2 human musicians, they will agree with each other 75% of the time. If you give the same song to Mixed In Key and a musician, they will agree with each other 75% of the time too.
> Mixed In Key & Human = 75% agreement, Human & Human = 75% agreement. They are the same. There is no such thing as 100% agreement because humans can't even agree with each other.

If needed, you can delete the older keys using the [sql_tools/delete_old_keys.sql](sql_tools/delete_old_keys.sql) script (please read it first!).

## Install Mixxx from sources

All these operations can be put in a script to ease the update process (as `apt update` will have no effect).

### Download the sources

Let's download [the sources from github](https://github.com/mixxxdj/mixxx):

```bash
git clone git@github.com:mixxxdj/mixxx.git
cd mixxx
```

### Optionnal: Use modifications that have not been implemented yet in Mixxx's official deposit

```bash
# Set this variables
other_repo=git@github.com:mxmilkiib/mixxx.git
other_repo_branch=Add-bpm-scaling-controls
#
git fetch $other_repo $other_repo_branch:TO_BE_MERGED
git merge TO_BE_MERGED
git branch -d TO_BE_MERGED
```

### Prepare the installation (on Debian/Ubuntu)

Then we use the [recommended commands](https://github.com/mixxxdj/mixxx/wiki/Compiling-On-Linux).

```bash
source tools/debian_buildenv.sh setup
# rm -rf build  # this might help if you've had issues with libraries 
cmake -DCMAKE_INSTALL_PREFIX=/usr/local -S . -B build

# choose how many processors to use
# it seems this will not only affect the build, but the track analysis in Mixxx later on
# NPROC=1
# NPROC=$(nproc) # all the processor
NPROC=$(( $(nproc) - ($(nproc)!=1) )) # all but one processor (except if you have only one processor)
cmake --build build --parallel $NPROC
```

Then we can skip the final `make install` step and instead…

### Generate a (Debian/Ubuntu) package to install it

```bash
cd build || exit
cpack -G DEB
sudo dpkg -i mixxx*.deb
cd ..
```

In case you want to share the installer:
```bash
INSTALLER_FOLDER=".."  # pick the one you want
mv build/mixxx*.deb $INSTALLER_FOLDER 
```

### (Optionnal) Cleaning


If your computer is short on memory, you can delete the build folder:
```bash
mv build/*deb ..
rm -rf build
```

You can even delete the compilation cache folder
(it is recommended to keep it as this will make the following upgrades faster):

```bash
cd ..
rm -rf "${HOME}/.cache/ccache"
```
