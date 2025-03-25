#!/bin/bash

set -xe

apt-get -y update
apt-get -y install linux-cpupower

cpupower frequency-set -g performance
