#!/bin/bash

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
	err usage: "$BASENAME" /path/to/capture-pre.pcap [capturename]
}

import() {
	local prepcap="$1"
	local name="$2"

	test -r "$prepcap" || err can not read pre cap: \""$prepcap"\"

	test -n "$name" || name="$(realpath "${prepcap}")"

	postpcap="${prepcap/-pre/-post}"

	test -r "$postpcap" || err can not read post cap: \""$postpcap"\"

	if [[ "$prepcap" == *.pcap.zst ]]; then
                tmp=pre_$(date +"%T.%N").tmp
                unzstd $prepcap -o  $tmp
                prepcap=$tmp
                echo "using zipped pcaps"
                remove=1
  fi

  if [[ "$postpcap" == *.pcap.zst ]]; then
          tmp=post_$(date +"%T.%N").tmp
          unzstd $postpcap -o $tmp
          postpcap=$tmp
  fi


	( "$PYTHON" "${BASEDIR}/pcaptocsv.py" "$prepcap" | psql -X -v ON_ERROR_STOP=1 --pset pager=off -v "name=${name}" -v type=pre -f "${BASEDIR}/sql/import/load.sql" ) &
	local prej=$!
	( "$PYTHON" "${BASEDIR}/pcaptocsv.py" "$postpcap" | psql -X -v ON_ERROR_STOP=1 --pset pager=off -v "name=${name}" -v type=post -f "${BASEDIR}/sql/import/load.sql" ) &
	local postj=$!

	log $prej
	log $postj

	wait $prej || { log import of \""$prepcap"\" failed. ; error=true; }
	wait $postj || { log import of \""$postpcap"\" failed. ; error=true; }


	rm "$prepcap"
	rm "$postpcap"

	[[ -n "$error" ]] && err failed to import
}

setupdb(){
	psql -1 -X -v ON_ERROR_STOP=1 --pset pager=off -f "${BASEDIR}/sql/import/ddl.sql"
}


test $# -lt 1 && help

setupdb

import "$@"
