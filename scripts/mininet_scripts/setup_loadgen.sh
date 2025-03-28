#!/bin/bash

# install moongen dependencies for newer moongen version
apt-get update
apt-get install meson ninja-build pkg-config python3-pyelftools libssl-dev zstd -y

set -xe

git clone --recursive "https://github.com/WiednerF/MoonGen.git" moongen

cd moongen
./build.sh
./setup-hugetlbfs.sh