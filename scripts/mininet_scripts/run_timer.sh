#!/bin/bash

# log every command
set -x

link=$(pos_get_variable -l link)
node=$(pos_get_variable -l node)
rate=$(pos_get_variable -l rate)
burst=$(pos_get_variable -l burst)
MEASUREMENT_TIME=$(pos_get_variable -g MEASUREMENT_TIME)
TIMEOUT_AMOUNT=$(($MEASUREMENT_TIME+15))
EVALUATOR=$(pos_get_variable -g EVALUATOR)
WARMUP=$(pos_get_variable -g WARM_UP_TIME)
MOONGEN=moongen

pos_sync

sleep $WARMUP

pos_run -l moonsniff -- /root/$MOONGEN/build/MoonGen /root/$MOONGEN/examples/moonsniff/sniffer.lua 7 8 --capture --time $TIMEOUT_AMOUNT --snaplen 84

sleep 8

pos_wait -l moonsniff

pos_sync  # waiting until timer is finished
echo "Finished capturing data $(date)"

sleep 1

mv latencies-pre.pcap latencies-pre-rate$rate-link$link-node$node-burst$burst.pcap
mv latencies-post.pcap latencies-post-rate$rate-link$link-node$node-burst$burst.pcap
mv latencies-stats.csv latencies-stats-rate$rate-link$link-node$node-burst$burst.csv

zstdmt -13 --force --rm --no-progress latencies-pre-rate$rate-link$link-node$node-burst$burst.pcap
zstdmt -13 --force --rm --no-progress latencies-post-rate$rate-link$link-node$node-burst$burst.pcap

sleep 2

pos_upload -l --timeout 120 latencies-pre-rate$rate-link$link-node$node-burst$burst.pcap.zst
pos_upload -l --timeout 120 latencies-post-rate$rate-link$link-node$node-burst$burst.pcap.zst

rsync -r -P -e "ssh -i ~/.ssh/general_ssh_key -o StrictHostKeyChecking=no" latencies-pre-rate$rate-link$link-node$node-burst$burst.pcap.zst $EVALUATOR:~/0/results/
rsync -r -P -e "ssh -i ~/.ssh/general_ssh_key -o StrictHostKeyChecking=no" latencies-post-rate$rate-link$link-node$node-burst$burst.pcap.zst $EVALUATOR:~/0/results/
rsync -r -P -e "ssh -i ~/.ssh/general_ssh_key -o StrictHostKeyChecking=no" latencies-stats-rate$rate-link$link-node$node-burst$burst.csv $EVALUATOR:~/0/results/

rm -f latencies-pre-rate$rate-link$link-node$node-burst$burst.pcap.zst
rm -f latencies-post-rate$rate-link$link-node$node-burst$burst.pcap.zst
rm -f latencies-stats-rate$rate-link$link-node$node-burst$burst.csv

sleep 2

pos_sync
