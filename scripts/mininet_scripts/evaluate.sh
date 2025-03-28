#!/bin/bash

LOOP=0
EXECUTE_TYPE="flow-based"


recreate_postgresql_cluster() {
  # delete and re-create the first cluster that pg_lsclusters outputs
  read -ra CLUSTER_DATA <<< "$(pg_lsclusters --no-header | head -n1)"  # array variable
  pg_dropcluster --stop "${CLUSTER_DATA[0]}" "${CLUSTER_DATA[1]}"
  pg_createcluster --start "${CLUSTER_DATA[0]}" "${CLUSTER_DATA[1]}"
}

process_pcap() {
  PCAP=$1
  i=$2
  REPEAT_NAME=$3
  EXECUTE_TYPE=$4

  DB_NAME="root$i-$REPEAT_NAME"

  dropdb --if-exists "$DB_NAME"
  createdb "$DB_NAME"
  export PGDATABASE="$DB_NAME"
  ~/evaluator/dbscripts/"$EXECUTE_TYPE"/import.sh "$PCAP"
  ~/evaluator/dbscripts/"$EXECUTE_TYPE"/analysis.sh "$PCAP"
  ~/evaluator/dbscripts/"$EXECUTE_TYPE"/cleanup.sh
}

execution() {
  i=$1
  NUM_CORES=8  # More is not possible without having problems
  RESULT_DIR="$HOME/$i/results"

  # Create and enter results/results directory (required by other scripts)
  mkdir --mode=0777 "$RESULT_DIR/results"
  pushd "$RESULT_DIR/results"

  # Process different pcaps in parallel
  export -f process_pcap
  parallel -j $NUM_CORES "process_pcap {} $i {%} $EXECUTE_TYPE" ::: ../latencies-pre-*.pcap.zst

  popd; pushd "$RESULT_DIR"
  cp -r ~/evaluator/plotter/"$EXECUTE_TYPE"/* .
  mkdir figures
  python3 plotcreator.py figures results .
  python3 irqprocessor.py ../irq ./figures
  if [ "$EXECUTE_TYPE" = 'flow-based' ]; then
    # Generate all necessary data for flow-based analysis
    python3 generate_flow_graphs.py "$i"
  fi
  make -i
  pushd results
  for k in *.csv; do
    zstdmt -13 --rm --no-progress "$k";
  done
   cd ../

  pos_upload --timeout 120 -r results
  pos_upload --timeout 120 -r figures
}

# Print commands as they are executed
set -x

# Delete all PostgreSQL data when the user root already exists (this avoids problems when not resetting the evaluator)
ROOT_EXISTS=$(psql postgres -tXAc "SELECT 1 FROM pg_roles WHERE rolname='root'" || true)
if [ "$ROOT_EXISTS" = "1" ]; then
  recreate_postgresql_cluster
fi

# Create user root as the script is running as root
env --chdir /var/lib/postgresql setpriv --init-groups --reuid postgres -- createuser -s root
env --chdir /var/lib/postgresql setpriv --init-groups --reuid postgres -- createdb root

for i in $( seq 0 "$LOOP" )
do
  execution "$i" &
done

wait

cd ~/evaluation/plotter/"$EXECUTE_TYPE"
pos_upload Makefile
pos_upload Makefile.conf.mk
pos_upload plotcreator.py
pos_upload tumcolor.sty
