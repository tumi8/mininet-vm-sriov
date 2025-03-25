#!/bin/bash

set -xe

rate=$(pos_get_variable -l rate)
burst=$(pos_get_variable -l burst)
MEASUREMENT_TIME=$(pos_get_variable -g MEASUREMENT_TIME)
SIZE=$(pos_get_variable -g SIZE)
PACKET_AMOUNT=$(($rate*$MEASUREMENT_TIME*10))
WARMUP=$(pos_get_variable -g WARM_UP_TIME)
pos_sync
pos_run -l replay -- /root/moongen/build/MoonGen /root/timer-loadgen.lua -x $SIZE --fix-packetrate $rate --packets $PACKET_AMOUNT --flows 10 --burst $burst 0 1
pos_sync  # waiting until timer is finished
pos_kill -l replay
pos_sync
