#!/bin/bash

set -xe

apt-get -y install net-tools iperf telnet systemd-container squashfs-tools sudo bridge-utils qemu-system-x86

cd ~
git clone mininet.bundle mininet
./prepare_squashfs.sh debian-bookworm/image.squashfs image.squashfs
ln debian-bookworm/vmlinuz vmlinuz
ln debian-bookworm/initrd.img initrd.img

echo -e "[global]\nbreak-system-packages = true" >/etc/pip.conf

cd ~/mininet
util/install.sh -fnv

sysctl net.ipv4.ip_forward=1
sysctl net.ipv4.conf.all.arp_ignore=1
sysctl net.ipv4.conf.all.arp_announce=1

ifdown enp100s0f1
echo 8 >/sys/class/net/enp100s0f1/device/sriov_numvfs
sleep 1
for i in {0..7}; do
	mac="3e:e5:a8:40:0d:$(printf "%02x" "$i")"
	ip l set enp100s0f1 vf "$i" spoofchk off trust on state enable mac "$mac"
	sleep 1
done

ifdown enp33s0f0
ifdown enp100s0f0
echo 14 >/sys/class/net/enp33s0f0/device/sriov_numvfs
echo 14 >/sys/class/net/enp100s0f0/device/sriov_numvfs
for i in {0..13}; do
	ip l set enp33s0f0 vf "$i" spoofchk off trust on vlan $((i + 1)) state enable
	ip l set enp100s0f0 vf "$i" spoofchk off trust on vlan $((i + 1)) state enable
	sleep 1
done

LINKTYPES=("veth" "hwpair")

cd ~

for link in "${LINKTYPES[@]}"; do
	python3 test.py "vm_opt" "$link"
	sleep 1
done
