#!/bin/bash

if lsb_release --all | grep -E 'CentOS' -q
then
    echo "Found CentOS 7 distribution";
    source /cvmfs/sft.cern.ch/lcg/views/LCG_96b/x86_64-centos7-gcc9-opt/setup.sh
elif lsb_release --all | grep -E 'ScientificCERNSLC' -q
then
    echo "Found SLC 6 distribution";
    source /cvmfs/sft.cern.ch/lcg/views/LCG_96b/x86_64-slc6-gcc8-opt/setup.sh
fi

NICK=${1}
if [ -f "arguments.txt" ]
then
    NICK=$(head -n $((${1} + 1)) arguments.txt)
fi

tar -zxvf merging.tar.gz ${NICK}.sh
bash ./${NICK}.sh
