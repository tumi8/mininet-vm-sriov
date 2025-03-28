#!/bin/bash

# exit on error
set -e
# log every command
set -x

LOOP="0"

NC="$(pos_get_variable nc || true)"
if [ "$BUCKET_SIZE" = '' ]; then
	BUCKET_SIZE=$DEFAULT_BUCKET_SIZE
fi

# Makes sure that a no setup mode works
if [ -d "$LOOP" ]; then rm -rf $LOOP; fi

if [ $LOOP -eq 0 ]; then

  apt update
  DEBIAN_FRONTEND=noninteractive apt install -y postgresql
  DEBIAN_FRONTEND=noninteractive apt install -y postgresql-client
  DEBIAN_FRONTEND=noninteractive apt install -y parallel
  DEBIAN_FRONTEND=noninteractive apt install -y python3-pip
  DEBIAN_FRONTEND=noninteractive apt install -y texlive-full
  DEBIAN_FRONTEND=noninteractive apt install -y lbzip2
  DEBIAN_FRONTEND=noninteractive apt install -y rename
  DEBIAN_FRONTEND=noninteractive apt install -y zstd

  python3 -m pip install pypacker
  python3 -m pip install netifaces
  python3 -m pip install pylatex
  python3 -m pip install matplotlib
  python3 -m pip install pandas
  python3 -m pip install pyyaml
  # required for pandas; default version 2.x no longer compatible with pandas
  python3 -m pip install Jinja2==3.1.2

fi

mkdir $LOOP
mkdir $LOOP/results