#!/bin/bash
SCRIPT_DIR=$(dirname $(readlink -f $BASH_SOURCE))
export PATH=$PATH:$SCRIPT_DIR/../grid-control:$SCRIPT_DIR/../grid-control/scripts
export PYTHONPATH=$PYTHONPATH:$SCRIPT_DIR/../grid-control/packages
