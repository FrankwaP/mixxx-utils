# Install Mixxx with libKeyFinder

## Why libKeyFinder?

From [KEY DETECTION COMPARISON 2020](https://www.reddit.com/r/DJs/comments/hwlzyt/key_detection_comparison_2020/):  

![What???](https://i.redd.it/zs186m2cpnc51.png "KEY DETECTION COMPARISON 2020")

Basicall you'll go from one of the worst to one of the best…

## Install libKeyFinder

First let's download [the sources from github](https://github.com/mixxxdj/libKeyFinder):

```bash
zip_dl_keyfinder=libkeyfinder.zip
wget --output-document=${zip_dl_keyfinder} https://github.com/mixxxdj/libkeyfinder/archive/refs/heads/main.zip
unzip ${zip_dl_keyfinder} && rm -f ${zip_dl_keyfinder}
cd libkeyfinder-main || exit
```

Then we use the [recommended commands](https://github.com/mixxxdj/libKeyFinder?tab=readme-ov-file#installation).  
You need to set the number of CPU cores on your computer in the first line.

```bash
number_of_cpu_cores=4
sudo apt install --yes cmake libfftw3-dev
sudo cmake -DCMAKE_INSTALL_PREFIX=/where/you/want/to/install/to -S . -B build
sudo cmake --build build --parallel ${number_of_cpu_cores}
sudo cmake --install build
```

## (Re-)Install Mixxx from sources

(If you already have Mixxx, uninstall it)

Let's download [the sources from github](https://github.com/mixxxdj/mixxx):

```bash
zip_dl_mixxx=mixxx.zip
wget --output-document=${zip_dl_mixxx} https://github.com/mixxxdj/mixxx/archive/refs/heads/main.zip
unzip ${zip_dl_mixxx} && rm -f ${zip_dl_mixxx} 
cd mixxx-main || exit
```

Then we use the [recommended commands](https://github.com/mixxxdj/mixxx?tab=readme-ov-file#building-mixxx).  
For the first line, select between `tools\windows_buildenv.bat`, `source tools/macos_buildenv.sh setup` or `source tools/debian_buildenv.sh setup` dependnig on your OS.

```bash
source tools/debian_buildenv.sh setup
mkdir build
cd build || exit
cmake ..
cmake --build .
```
