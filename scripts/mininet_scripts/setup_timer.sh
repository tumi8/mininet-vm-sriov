#!/bin/bash

# log every command
set -x

MOONGEN=moongen

cd /root  # Make sure that we are in the correct folder

# install moongen dependencies for newer moongen version
apt-get update
apt-get install meson ninja-build pkg-config python3-pyelftools libssl-dev zstd libsystemd-dev -y

git clone --recurse-submodules  https://github.com/WiednerF/moongen.git moongen

# Bind interfaces to DPDK
modprobe vfio-pci

for id in $(python3 /root/moongen/libmoon/deps/dpdk/usertools/dpdk-devbind.py --status | grep -v Active | grep -v ConnectX | grep unused=vfio-pci | cut -f 1 -d " ")
do
	echo "Binding interface $id to DPDK"
	python3 /root/moongen/libmoon/deps/dpdk/usertools/dpdk-devbind.py  --bind=vfio-pci $id
	i=$(($i+1))
done

cd moongen
./build.sh
./setup-hugetlbfs.sh

cd /root
mkdir -p ~/.ssh
cp ssh_key ~/.ssh/ssh_key
cp ssh_key.pub ~/.ssh/ssh_key.pub
chmod 600 ~/.ssh/ssh_key
chmod 600 ~/.ssh/ssh_key.pub

echo "finished setup, waiting for DUT"
