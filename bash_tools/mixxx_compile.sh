#!/bin/bash

cd "$(dirname "$0")"/.. || exit
source tools/debian_buildenv.sh setup
cmake -DCMAKE_INSTALL_PREFIX=/usr/local -S . -B build
cmake --build build --parallel $(nproc)

cd build || exit
cpack -G DEB
sudo dpkg -i ./*.deb
cd ..

rm -rf build
