#!/bin/bash

set -eu
set -o pipefail

if ! type mksquashfs systemd-nspawn >/dev/null; then
	echo "Cannot find mksquashfs and systemd-nspawn"
	exit 1
fi

if [[ $# -ne 2 ]]; then
	echo "Usage: prepare_squashfs.sh <image.squashfs> <output.squashfs>"
	exit 1
fi

if [[ $EUID -ne 0 ]]; then
	echo "Need to run as root."
	exit 1
fi


TMPDIR="$(mktemp -d)"

error() {
	echo "ERROR, CLEANING UP"
	umount "$TMPDIR/overlay" || true
	umount "$TMPDIR/base" || true
	rm -rf "$TMPDIR"
}
trap error ERR

echo "MOUNTING IMAGE"
mkdir -p "$TMPDIR/"{base,work,new,overlay,live}

mount -o ro "$1" "$TMPDIR/base"
mount -t overlay prepare_squashfs -o"lowerdir=$TMPDIR/base,upperdir=$TMPDIR/new,workdir=$TMPDIR/work" "$TMPDIR/overlay"

echo "INSTALLING PACKAGES AND CONFIGURATION"
systemd-nspawn -D "$TMPDIR/overlay" --pipe -a bash <<EOF
	DEBIAN_FRONTEND=noninteractive apt-get -y update
	DEBIAN_FRONTEND=noninteractive apt-get -y install qemu-guest-agent net-tools iperf telnet openssh-server bridge-utils
	systemctl mask networking.service ifup@.service
	echo "PasswordAuthentication=yes" >/etc/ssh/sshd_config.d/mininet.conf
	echo "PermitEmptyPasswords=yes" >>/etc/ssh/sshd_config.d/mininet.conf
	echo "PermitRootLogin=yes" >>/etc/ssh/sshd_config.d/mininet.conf
	echo "X11Forwarding=yes" >>/etc/ssh/sshd_config.d/mininet.conf

	echo "Include /etc/ssh/sshd_config.d/mininet.conf" | cat - /etc/ssh/sshd_config > /etc/ssh/sshd_config.new
	mv /etc/ssh/sshd_config.new /etc/ssh/sshd_config
EOF

echo "BUILDING IMAGE"
mksquashfs "$TMPDIR/overlay" "$TMPDIR/live/image.squashfs" -noappend
# Boot filesystem needs to contain the actual squashfs image as a single file in /live
mksquashfs "$TMPDIR/live" "$2" -noI -noD -noF -noX -no-duplicates -keep-as-directory -processors 1 -noappend

umount "$TMPDIR/overlay"
umount "$TMPDIR/base"

rm -rf "$TMPDIR"
