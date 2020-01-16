#!/bin/bash
echo "STEP 1: Setting environments and SW setup"
if lsb_release --all | grep -E 'CentOS' -q
then
    echo "Found CentOS 7 distribution";
    source /cvmfs/cms.cern.ch/cmsset_default.sh
    #source /cvmfs/grid.cern.ch/centos7-ui-4.0.3-1_umd4v1/etc/profile.d/setup-c7-ui-example.sh
    scram project CMSSW_11_0_0_patch1; cd CMSSW_11_0_0_patch1/src
    eval `scramv1 runtime -sh`
    cd -
elif lsb_release --all | grep -E 'ScientificCERNSLC' -q
then
    echo "Found SLC 6 distribution";
    source /cvmfs/cms.cern.ch/cmsset_default.sh
    #source /cvmfs/grid.cern.ch/emi-ui-3.17.1-1.el6umd4v5/etc/profile.d/setup-ui-example.sh
    scram project CMSSW_10_2_20; cd CMSSW_10_2_20/src
    eval `scramv1 runtime -sh`
    cd -
fi

echo "STEP 2: Checking CMSSW, hadd, xrd and gfal-copy"
echo $CMSSW_BASE
which hadd
which xrd
which gfal-copy

echo "STEP 3: Starting merging script"
NICK=${1}
if [ -f "arguments.txt" ]
then
    NICK=$(head -n $((${1} + 1)) arguments.txt)
fi

tar -zxvf merging.tar.gz ${NICK}.sh
bash ./${NICK}.sh
