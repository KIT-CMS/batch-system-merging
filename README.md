# batch-system-merging

## Installation
```[bash]
wget https://raw.githubusercontent.com/KIT-CMS/batch-system-merging/master/scripts/checkout.sh
bash ./checkout.sh
```

## Local environment
For the local environment on the ETP and NAF portal machines, only the **VOMS proxy** with its environment variable `X509_USER_PROXY` should be set and up-to-date (check via `voms-proxy-info`).
In order to set it, use e.g.:
```[bash]
voms-proxy-init --valid 192:00:00 --voms cms:/cms/dcms --rfc
```

## Merging examples
In the following, examples are given for user `aakhmets/akhmet` on NAF/ETP and some specific folders with ntuples

### Reading from GridKA dCache via xrootd, running on TOPAS, writing to GridKA dCache via xrootd:

```[bash]
scripts/merge_outputs.py \
           --sample-directories aakhmets/analysis_ntuples_mcmssm2018_mt_shifts_05-01-2020 \
                                aakhmets/analysis_ntuples_mcmssm2018_tt_shifts_05-01-2020 \
                                aakhmets/analysis_ntuples_mcmssm2018_et_shifts_05-01-2020 \
                                aakhmets/analysis_ntuples_mcmssm2018_em_shifts_05-01-2020 \
                                aakhmets/analysis_ntuples_mcmssm2018_24-12-2019 \
           --dcap-server "" \
           --target-directory aakhmets/test/

condor_submit configs/etp_condor_topas_cc7.jdl
```

### Reading from GridKA dCache via xrootd, running on NAF, writing to NAF dCache via dcap:

```[bash]
scripts/merge_outputs.py \
           --sample-directories aakhmets/analysis_ntuples_mcmssm2018_mt_shifts_05-01-2020 \
                                aakhmets/analysis_ntuples_mcmssm2018_tt_shifts_05-01-2020 \
                                aakhmets/analysis_ntuples_mcmssm2018_et_shifts_05-01-2020 \
                                aakhmets/analysis_ntuples_mcmssm2018_em_shifts_05-01-2020 \
                                aakhmets/analysis_ntuples_mcmssm2018_24-12-2019 \
           --target-directory aakhmets/test/ \
           --srm-server srm://dcache-se-cms.desy.de/ \
           --dcap-server gsidcap://dcache-cms-dcap.desy.de/ \
           --xrootd-output-server "" \
           --main-output-directory /pnfs/desy.de/cms/tier2/store/user/

condor_submit configs/naf_condor.jdl
```

### Reading from GridKA dCache via local mount on `bms1/2/3`, running locally on the portal machines `bms1/2/3`, writing directly to `/ceph`, restricted to a subset of datasets via regex:

```[bash]
scripts/merge_outputs.py \
           --sample-directories aakhmets/analysis_ntuples_mcmssm2018_mt_shifts_05-01-2020 \
                                aakhmets/analysis_ntuples_mcmssm2018_tt_shifts_05-01-2020 \
                                aakhmets/analysis_ntuples_mcmssm2018_et_shifts_05-01-2020 \
                                aakhmets/analysis_ntuples_mcmssm2018_em_shifts_05-01-2020 \
                                aakhmets/analysis_ntuples_mcmssm2018_24-12-2019 \
           --target-directory test/ \
           --srm-server "" \
           --dcap-server "" \
           --xrootd-input-server "" \
           --xrootd-output-server "" \
           --main-input-directory /storage/gridka-nrg/ \
           --main-output-directory /ceph/akhmet/ \
           --match-to-sample-regex "SUSY.*M900"

# Source an appropriate environment depending on the machine. These lcg stacks work for the portal machines:
if uname -a | grep -E 'el7' -q
then
    source /cvmfs/sft.cern.ch/lcg/views/LCG_96b/x86_64-centos7-gcc9-opt/setup.sh
elif uname -a | grep -E 'el6' -q
then
    source /cvmfs/sft.cern.ch/lcg/views/LCG_96b/x86_64-slc6-gcc8-opt/setup.sh
fi

# In order to run locally, specify an appropriate number of cores (up to 10 is good)
scripts/run_locally.py --cores 5
```
## Checking merged ntuples with specified friends

### Checking locally available ntuples for year 2017 with corresponding friends: MELA SVFit FakeFactors
```bash
scripts/check_merged_files.py --xrootd-server "" \
                              --input-directory /ceph/htautau/deeptau_eoy/2017/ntuples/ \
                              --input-friend-directories /ceph/htautau/deeptau_eoy/2017/friends/SVFit/ \                   
                                                         /ceph/htautau/deeptau_eoy/2017/friends/MELA/ \ 
                                                         /ceph/htautau/deeptau_eoy/2017/friends/FakeFactors/
```

## Further notes
Please have a look also at the help messages of the python executables:

```[bash]
scripts/merge_outputs.py -h
scripts/run_locally.py -h
```
