#!/bin/bash

set -xe

DUT_IMAGE=$(pos_get_variable -g DUT_IMAGE)
DEBIAN_FRONTEND=noninteractive apt update
DEBIAN_FRONTEND=noninteractive apt-get -y install net-tools iperf telnet systemd-container squashfs-tools sudo  bridge-utils qemu-system-x86

cd ~
git clone mininet.bundle mininet
./prepare_squashfs.sh $DUT_IMAGE/image.squashfs image.squashfs
ln $DUT_IMAGE/vmlinuz vmlinuz
ln $DUT_IMAGE/initrd.img initrd.img

echo -e "[global]\nbreak-system-packages = true" >/etc/pip.conf

cd ~/mininet
util/install.sh -fnv

sysctl net.ipv4.ip_forward=1
sysctl net.ipv4.conf.all.arp_ignore=1
sysctl net.ipv4.conf.all.arp_announce=1
