# Experiment

This folder contains all files necessary to perform the experiment, additionally in the parent folder is a folder named mininet required with the CIMininet source code, if you clone this repository and checkout the submodules, this automatically the case.

The Experiment uses for reproducibility and automation, POS, the Plain Orchestrating Service based on "Sebastian Gallenmüller, Dominik Scholz, Henning Stubbe, and Georg Carle. 2021. The pos framework: a methodology and toolchain for reproducible network experiments. In Proceedings of the 17th International Conference on emerging Networking EXperiments and Technologies (CoNEXT '21)."

## Needed adoptions
* Replace in run_dut.sh the interfaces for the SR-IOV loop and the connection to the LoadGen with your interfaces.
* A SSH Key for accessing the evaluator is needed (public and private) named as ssh_key and ssh_key_pub in this folder.
* Adapt the links in mininet_experiment.py

## Experiment Execution

We require a Debian bookworm, a Debian buster, and an Debian bullseye image with python3 preinstalled.

Further, the execution happens with executing experiment.sh and setting the four different nodes DuT, timer, LoadGen, and Evaluator as well as the path to the image to download used for the VMs for CIMininet needed for the execution.

At the end, in the results folder from the evaluator can all analysis results be found and under the folder of the timer all Raw PCAPs.

For simpler reproducibility, this files for the paper are available in the [MediaTUM Repository](https://doi.org/10.14459/2025mp1773238).

No further steps are required.

## Execution without POS.
We provide the dut_without_pos.sh to allow execution without POS and without rewriting the code, this requires this repository on the node and changed variables, but it does not do the traffic generation but allows to execute all settings required to start the Mininet yourself, the debian-bookworm image as files is a prerequirement.

Kind Regards,
Florian Wiedner
