#!/bin/bash

DEFAULT_BUCKET_SIZE=100   # default bucket size of the histogram
DEFAULT_TRIM_MS=0         # default cut the first TRIM_MS ms from evaluation
DEFAULT_NUM_WORST=5000    # default number of worst latencies to evaluate

BUCKET_SIZE="$(pos_get_variable bucket_size || true)"
if [ "$BUCKET_SIZE" = '' ]; then
	BUCKET_SIZE=$DEFAULT_BUCKET_SIZE
fi

TRIM_MS="$(pos_get_variable trim_ms || true)"
if [ "$TRIM_MS" = '' ]; then
	TRIM_MS=$DEFAULT_TRIM_MS
fi

NUM_WORST="$(pos_get_variable num_worst || true)"
if [ "$NUM_WORST" = '' ]; then
	NUM_WORST=$DEFAULT_NUM_WORST
fi

BASENAME="$(readlink -f "$0")"
BASEDIR="$(dirname "$BASENAME")"
BASENAME="$(basename "$BASENAME")"

PYTHON=$HOME/.venv/bin/python3

[[ -x "$PYTHON" ]] || PYTHON=python3


log () {
	printf "%s\n" "$*" >&2
}

err() {
	log "$*"
	exit 2
}

help() {
	err usage: "$BASENAME" capturename
}

analysis() {
	local name="$1"

	[[ -e "$name" ]] && name="$(realpath "$name")"

	local bname="$(basename "$name")"

		# histogram
	psql -q -X -v ON_ERROR_STOP=1 -v "name=$name" -v "bucket_size=$BUCKET_SIZE" -v "trim_ms=$TRIM_MS" -f "$BASEDIR/sql/evaluation/latency-hist.sql" > "${bname}.bucket_size$BUCKET_SIZE.trim_ms$TRIM_MS.hist.csv"

	# worst-of-latency
	psql -q -X -v ON_ERROR_STOP=1 -v "name=$name" -v "trim_ms=$TRIM_MS" -v "num_worst=$NUM_WORST" -f "$BASEDIR/sql/evaluation/dump-worst.sql" > "${bname}.trim_ms$TRIM_MS.num_worst$NUM_WORST.worst.csv"

	# percentiles (hdr)
	psql -q -X -v ON_ERROR_STOP=1 -v "name=$name" -v "trim_ms=$TRIM_MS" -f "$BASEDIR/sql/evaluation/dump-percentiles.sql" > "${bname}.trim_ms$TRIM_MS.percentiles.csv"

	# throughput
	psql -q -X -v ON_ERROR_STOP=1 -v "name=$name" -v "trim_ms=$TRIM_MS" -f "$BASEDIR/sql/evaluation/dump-transferrate.sql" > "${bname}.trim_ms$TRIM_MS.transferrate.csv"

	# packetrate
	psql -q -X -v ON_ERROR_STOP=1 -v "name=$name" -v "trim_ms=$TRIM_MS" -v "type=pre" -f "$BASEDIR/sql/evaluation/dump-packetrate.sql" > "${bname}.trim_ms$TRIM_MS.packetratepre.csv"
	psql -q -X -v ON_ERROR_STOP=1 -v "name=$name" -v "trim_ms=$TRIM_MS" -v "type=post" -f "$BASEDIR/sql/evaluation/dump-packetrate.sql" > "${bname}.trim_ms$TRIM_MS.packetratepost.csv"

	# Latency of flows
	psql -q -X -v ON_ERROR_STOP=1 -v "name=$name" -f "$BASEDIR/sql/evaluation/dump-flows-latency.sql" > "${bname}.latency-flows.csv"

	# inter-packet gap jitter histogram
	psql -q -X -v ON_ERROR_STOP=1 -v "name=$name" -v "bucket_size=$BUCKET_SIZE" -v "trim_ms=$TRIM_MS" -v "type=pre" -f "$BASEDIR/sql/evaluation/jitter-hist.sql" > "${bname}.bucket_size$BUCKET_SIZE.trim_ms$TRIM_MS.jitterpre.csv"
	psql -q -X -v ON_ERROR_STOP=1 -v "name=$name" -v "bucket_size=$BUCKET_SIZE" -v "trim_ms=$TRIM_MS" -v "type=post" -f "$BASEDIR/sql/evaluation/jitter-hist.sql" > "${bname}.bucket_size$BUCKET_SIZE.trim_ms$TRIM_MS.jitterpost.csv"
}

test $# -lt 1 && help

analysis "$@"
