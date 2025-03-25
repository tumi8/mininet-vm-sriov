#!/bin/bash

set -e

if test "$#" -ne 5; then
	echo "Usage: setup.sh loadgen-host dut/vm-host timer-host evaluator-host dut-image"
	exit
fi

LOADGEN=$1
DUT=$2
TIMER=$3
EVALUATOR=$4
DUT_IMAGE=$5

python3 -c "import yaml; l = yaml.full_load(open('global-vars.yml', 'r')); l['EVALUATOR'] = '$EVALUATOR'; yaml.dump(l,open('global-vars-gen.yml', 'w'))"
python3 -c "import yaml; l = yaml.full_load(open('global-vars-gen.yml', 'r')); l['DUT'] = '$DUT'; l['TIMER'] = '$TIMER'; l['LOADGEN'] = '$LOADGEN';l['DUT_IMAGE'] = '$DUT_IMAGE'; yaml.dump(l, open('global-vars-gen.yml', 'w'))"

EVALUATOR_IMAGE="debian-bullseye-evaluator@2021-08-22T03:12:23+00:00"
LOADGEN_IMAGE="debian-buster@2021-08-17T01:07:22+00:00"
TIMER_IMAGE="debian-bullseye"

POS="pos"

BOOTPARAMS=(nosmt idle=poll intel_idle.max_cstate=0 intel_pstate=disable amd_pstate=disable tsc=reliable mce=ignore_ce audit=0 nmi_watchdog=0 skew_tick=1 nosoftlockup intel_iommu=on iommu=pt)

NODES=("$LOADGEN" "$DUT" "$TIMER")

for node in "${NODES[@]}"; do
	$POS allocations free -k "$node"
done

$POS allocations free -k "$EVALUATOR"

$POS allocations allocate "${NODES[@]}"
$POS allocations allocate "$EVALUATOR"

$POS nodes image "$LOADGEN" "$LOADGEN_IMAGE"
$POS nodes image "$DUT" "$DUT_IMAGE"
$POS nodes image "$TIMER" "$TIMER_IMAGE"
$POS nodes image "$EVALUATOR" "$EVALUATOR_IMAGE"

$POS nodes bootparameter "$LOADGEN" ${BOOTPARAMS[@]}
$POS nodes bootparameter "$DUT" ${BOOTPARAMS[@]}

$POS allocations set_variables "$LOADGEN" --as-loop loop.yml
$POS allocations set_variables "$LOADGEN" --as-global global-vars-gen.yml

for node in "${NODES[@]}"; do
	$POS nodes reset --non-blocking "$node"
done
$POS nodes reset --non-blocking "$EVALUATOR"

rm -f ../mininet/mininet.bundle
git -C ../mininet bundle create mininet.bundle HEAD

$POS nodes copy -r --queued "$DUT" ../mininet/mininet.bundle
$POS nodes copy --queued "$DUT" mininet_experiment.py
$POS nodes copy --queued "$DUT" prepare_squashfs.sh
$POS nodes copy -r --queued "$DUT" /srv/testbed/images/default/"$DUT_IMAGE"

$POS nodes copy --queued "$TIMER" ssh_key
$POS nodes copy --queued "$TIMER" ssh_key.pub

$POS nodes copy --queued "$LOADGEN" timer-loadgen.lua

$POS commands launch --infile common.sh "$LOADGEN" --queued
$POS commands launch --infile common.sh "$DUT" --queued

pos roles add upwarm-$LOADGEN $LOADGEN $DUT
pos roles add cordre-$LOADGEN $LOADGEN $TIMER

COMMAND_LOADGEN_ID=$($POS commands launch --infile setup_loadgen.sh "$LOADGEN" --queued --name setup_loadgen)
COMMAND_TIMER_ID=$($POS commands launch --infile setup_timer.sh "$TIMER" --queued --name setup_timer)
COMMAND_DUT_ID=$($POS commands launch --infile setup_dut.sh "$DUT" --queued --name setup_dut)
COMMAND_EVALUATOR_ID=$($POS commands launch --infile setup_evaluator.sh "$EVALUATOR" --queued --name setup_eval)

$POS commands await "$COMMAND_DUT_ID"
$POS commands await "$COMMAND_LOADGEN_ID"
$POS commands await "$COMMAND_TIMER_ID"
$POS commands await "$COMMAND_EVALUATOR_ID"

{ pos commands launch --loop --infile run_loadgen.sh --blocking "$LOADGEN"; echo "$LOADGEN userscript executed"; } &
{ pos commands launch --loop --infile run_timer.sh --blocking "$TIMER"; echo "$TIMER userscript executed"; } &
{ pos commands launch --loop --infile run_dut.sh --blocking "$DUT"; echo "$DUT userscript executed"; } &

wait

$POS nodes copy -r --queued "$EVALUATOR" ../evaluator

$POS commands launch --infile evaluate.sh "$EVALUATOR" --queued --name evaluate_eval

echo "You need to copy the files from the Evaluator results folder to finalize"
