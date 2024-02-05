# Install Mixxx with libKeyFinder (Debian/Ubuntu)

Since there is no Debian/Ubuntu package with libKeyFinder, we must install it from sources.  
Here are instructions on how to do it.

## Why libKeyFinder?

From [KEY DETECTION COMPARISON 2020](https://www.reddit.com/r/DJs/comments/hwlzyt/key_detection_comparison_2020/):  

![What???](https://i.redd.it/zs186m2cpnc51.png "KEY DETECTION COMPARISON 2020")

Basicall you'll go from one of the worst to one of the best…

## Install Mixxx from sources

All these operations can be put in a script to ease the update process (as `apt update` will have no effect).  

### Download the sources

Let's download [the sources from github](https://github.com/mixxxdj/mixxx):

```bash
github_mixxx=https://github.com/mixxxdj/mixxx/archive/refs/heads/main.zip
zip_mixxx=mixxx.zip
dir_mixxx=mixxx-main
wget --output-document=${zip_dl_mixxx} ${github_mixxx}
unzip ${zip_dl_mixxx} && rm -f ${zip_dl_mixxx} 
```

### Prepare the installation

Then we use the [recommended commands](https://github.com/mixxxdj/mixxx/wiki/Compiling-On-Linux).

```bash
cd ${dir_mixxx} || exit
source tools/debian_buildenv.sh setup
cmake -DCMAKE_INSTALL_PREFIX=/usr/local -S . -B build
cmake --build build --parallel ${nproc}
```

We skip the final `make install` step and instead…

### Generate a package to install it

```bash
cpack -G DEB
sudo dpkg -i *.deb
```

We can then remove the sources folder:

```bash
rm -rf ${dir_mixxx}
```
