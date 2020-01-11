#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ROOT as R
import json
import os
import re
import glob
from multiprocessing import Pool
from XRootD import client
from XRootD.client.flags import DirListFlags, OpenFlags, MkDirFlags, QueryCode, StatInfoFlags
import argparse

def create_result_for_sample(info):
    print "\tProcessing:",info["sample"]
    result = {"sample" : info["sample"]}
    result["n_events_expected"] = info["database"].get(info["sample"],-1)["n_events_generated"]
    F = R.TFile.Open(info["input_file"], "read")
    result["pipelines"] = sorted([k.GetName() for k in F.GetListOfKeys() if k.IsFolder()])
    for pattern in info["n_pipelines_expected"]:
        if re.search(pattern,info["sample"]):
            result["n_pipelines_expected"] = info["n_pipelines_expected"][pattern]
            break
    for p in result["pipelines"]:
        cutflow = F.Get(p).Get("cutFlowUnweighted")
        if cutflow:
            result[p] = cutflow.GetBinContent(1) 
        else:
            result[p] = 0
    F.Close()
    return result

def sorted_nicely(l):
    """ Sort the given iterable in the way that humans expect: alphanumeric sort (in bash, that's 'sort -V')"""
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
    return sorted(l, key = alphanum_key)

def nullable_string(val):
    if not val:
        return None
    return val

def parseargs():
    parser = argparse.ArgumentParser(description='Small script to check merged artus ntuples from local or xrootd resources using miltiprocessing.')
    parser.add_argument('--xrootd-server',default='root://cmsxrootd-kit.gridka.de/',type=nullable_string,help='xrootd server to access your merged files and to create the output directory. Only used in xrootd mode. Default: %(default)s')
    parser.add_argument('--input-directory',default='/pnfs/gridka.de/cms/disk-only/store/user/store/aakhmets/test/',help='input directory path for merged artus ntuples on the machine or server. Default: %(default)s')
    parser.add_argument('--database',default='datasets/datasets.json',help='File in .json format with datasets info. Default: %(default)s')
    parser.add_argument('--match-to-sample-regex',default='.*',help='Regular expression to restrict the samples to be checked to. Default: %(default)s')
    parser.add_argument('--results',default=None,help='Already computed results to be examined. Default: %(default)s')

    return parser.parse_args()

def main():
    args = parseargs()
    if args.results:
        dataset_results = json.load(open(args.results,'r'))
    else:
        R.gROOT.SetBatch()
        R.gErrorIgnoreLevel = R.kError

        xrootd_server = args.xrootd_server.strip("/") if args.xrootd_server else None
        input_modes = {
            "local" : not xrootd_server,
            "xrootd" : xrootd_server,
        }
        if input_modes["xrootd"]:
            xrootdclient = client.FileSystem(xrootd_server)
        input_directory = args.input_directory.strip("/")
        sample_pattern = args.match_to_sample_regex
        database = json.load(open(args.database,'r'))

        dataset_dict = {}
        file_dict = {}
        dataset_infos = [] 
        dataset_results = {}

        ### ATTENTION!!! The following dict is hardcoded and needs continious updates!!! Current status:
        # mt.py:  needed_pipelines = ['nominal', 'tauESperDM_shifts', 'tauMuFakeESperDM_shifts', 'regionalJECunc_shifts', 'METunc_shifts', 'METrecoil_shifts', 'btagging_shifts']
        # et.py:  needed_pipelines = ['nominal', 'tauESperDM_shifts', 'tauEleFakeESperDM_shifts', 'regionalJECunc_shifts', 'METunc_shifts', 'METrecoil_shifts', 'btagging_shifts', 'eleES_shifts']
        # tt.py:  needed_pipelines = ['nominal', 'tauESperDM_shifts', 'regionalJECunc_shifts', 'METunc_shifts', 'METrecoil_shifts', 'btagging_shifts']
        # em.py:  needed_pipelines = ['nominal', 'eleES_shifts', 'regionalJECunc_shifts', 'METunc_shifts', 'METrecoil_shifts', 'btagging_shifts']

        n_pipelines_expected  = {
            "(SingleMuon|SingleElectron|EGamma|MuonEG).*Run201" : 1, # corresponding channel in data
            "Tau.*Run201" : 3,                                       # mt, et, tt in data
            "(Mu|Tau)TauFinalState" : 9,                             # mt/tt + 8 Tau ES in embedding
            "ElTauFinalState" : 11,                                  # et + 8 Tau ES + 2 Ele ES in embedding
            "ElMuFinalState" : 3,                                    # em + 2 Ele ES in embedding
            "DY.?Jets|EWKZ" : 184,                                   # bosonic MC w/o Z (next below) + 8 Ele->Tau ES + 4 Mu->Tau ES in Z boson MC
            "ttHJet|HTo(WW|TauTau)|W.?Jets|WG|EWKW" : 172,           # non-bosonic MC (next below) + 4 * 4 MET recoil in bosonic MC w/o Z
            "ST.*top.*|TTTo|TT_|WW_|ZZ_|WZ_" : 156,                  # 4 channels + 3 * 8 Tau ES + 2 * 4 Ele ES + 4 * 4 btagging + 4 * 2 MET unclustered + 4 * 24 Jet ES/ER
        }

        print "Gathering infos from ROOT files"
        if input_modes["xrootd"]:
            status, listing = xrootdclient.dirlist(input_directory, DirListFlags.STAT)
            print "Investigating via xrdfs:",os.path.join("/",input_directory)
            sample_dirs = [ entry.name.strip("/") for entry in listing if (entry.statinfo.flags & StatInfoFlags.IS_DIR) and re.search(sample_pattern,entry.name)]
        elif input_modes["local"]:
            sample_dirs = [os.path.basename(name).strip("/") for name in glob.glob(os.path.join("/",input_directory,"*")) if os.path.isdir(name) and re.search(sample_pattern,name)]

        for sd in sample_dirs:
            sample_dir = os.path.join(input_directory,sd)
            if input_modes["xrootd"]:
                s, dataset_listing = xrootdclient.dirlist(sample_dir, DirListFlags.STAT)
                input_files = [os.path.join(xrootd_server,sample_dir,entry.name) for entry in dataset_listing if ".root" in entry.name]
            elif input_modes["local"]:
                input_files = glob.glob(os.path.join("/",sample_dir,"*.root"))

            dataset_dict.setdefault(sd, [])
            dataset_dict[sd] += input_files

        for sd in sorted_nicely(dataset_dict.keys()):
            if len(dataset_dict[sd]) != 1:
                dataset_results[sd] = None
            else:
                dataset_infos.append({"sample" : sd, "database" : database, "n_pipelines_expected" : n_pipelines_expected, "input_file" : dataset_dict[sd][0]})

        results_list = []
        for info in dataset_infos:
            results_list.append(create_result_for_sample(info))
        for r in results_list:
            dataset_results[r.pop("sample")] = r

        print "Dumping results into a .json file"
        json.dump(dataset_results,open("check_results.json","w"),sort_keys=True,indent=2)

    # Examining the results:
    no_files_list = []
    incorrect_pipelines_list = []
    incorrect_nevents_dict = {}
    print "1. step: examining availability of the merged files."
    for s in sorted_nicely(dataset_results.keys()):
        if not dataset_results[s]:
            print "\tNo or too many files found for sample:",s
            dataset_results.pop(s)
            no_files_list.append(s)
    print "2. step: examining number of pipelines in the merged files."
    for s in sorted_nicely(dataset_results.keys()):
        exp = dataset_results[s]["n_pipelines_expected"]
        found = len(dataset_results[s]["pipelines"])
        if exp != found:
            print "\tIncorrect number of pipelines for sample:",s,"exp =",exp,"found =",found
            incorrect_pipelines_list.append(s)
    print "3. step: examining number of events for each pipeline in the merged files. Deviations > 0.0001 considered as incorrect."
    for s in sorted_nicely(dataset_results.keys()):
        print "\tExamining sample:",s
        exp = float(dataset_results[s]["n_events_expected"])
        for p in dataset_results[s]["pipelines"]:
            found = dataset_results[s][p]
            if abs(found/exp - 1.0)  > 0.0001:
                print "\t\tIncorrect number of events for pipeline:",p,"exp =",exp,"found =",dataset_results[s][p],"ratio to exp =",dataset_results[s][p]/exp
                incorrect_nevents_dict.setdefault(s,[])
                incorrect_nevents_dict[s].append(p)

    # Saving the examination:
    no_files = open("no_files.txt","w")
    no_files.write("\n".join(no_files_list))
    no_files.close()

    incorrect_pipelines = open("incorrect_pipelines.txt","w")
    incorrect_pipelines.write("\n".join(incorrect_pipelines_list))
    incorrect_pipelines.close()

    incorrect_nevents = open("incorrect_nevents.txt","w")
    to_write = ""
    for s in sorted_nicely(incorrect_nevents_dict.keys()):
        to_write += s +"\n"
        for p in incorrect_nevents_dict[s]:
            to_write += "\t" + p + "\n"
    incorrect_nevents.write(to_write.strip())
    incorrect_nevents.close()

if __name__ == "__main__":
    main()
