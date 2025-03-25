#!/bin/bash

set -xe

link=$(pos_get_variable -l link)
node=$(pos_get_variable -l node)

ps -ef | grep "qemu-system-x86_64" | awk '{print $2}' | xargs kill -15 || echo "failed" # clean from previous run
cd ~

ip l set dev enp100s0f1 down
ip l set dev enp33s0f1 down
echo 1 >/sys/class/net/enp33s0f1/device/sriov_numvfs
echo 1 >/sys/class/net/enp100s0f1/device/sriov_numvfs
sleep 2
if [[ "$node" == "namespace" ]]; then
  ip l set dev enp100s0f1v0 up
  ip l set dev enp33s0f1v0 up
  ip l set dev enp100s0f1v0 promisc on
  ip l set dev enp33s0f1v0 promisc on
  ip l set dev enp100s0f1 up
  ip l set dev enp33s0f1 up
fi

ip l set dev enp33s0f0 down
ip l set dev enp100s0f0 down
echo 14 >/sys/class/net/enp33s0f0/device/sriov_numvfs
echo 14 >/sys/class/net/enp100s0f0/device/sriov_numvfs
sleep 1
for i in {0..13}; do
	ip l set enp33s0f0 vf "$i" spoofchk off trust on vlan $((i + 1)) state enable
	ip l set enp100s0f0 vf "$i" spoofchk off trust on vlan $((i + 1)) state enable
	sleep 1
done

python3 mininet_experiment.py "$node" "$link"
sleep 1
