#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import glob
import gfal2
import tarfile
from XRootD import client
from XRootD.client.flags import DirListFlags, OpenFlags, MkDirFlags, QueryCode, StatInfoFlags
import argparse

def nullable_string(val):
    if not val:
        return None
    return val

def parseargs():
    parser = argparse.ArgumentParser(description='Small script to merge artus outputs from local or xrootd resources using multiprocessing.')
    parser.add_argument('--xrootd-server',default='root://cmsxrootd-kit.gridka.de/',type=nullable_string,help='xrootd server to access your input files and to create the output directory. Only used in xrootd mode. Default: %(default)s')
    parser.add_argument('--srm-server',default='srm://cmssrm-kit.gridka.de/',type=nullable_string,help='srm server path to create the output directory for your output files (the main path up to "user" directory). Only used in gfal2 mode. Default: %(default)s')
    parser.add_argument('--dcap-server',default='gsidcap://cmsdcap-kit.gridka.de/',type=nullable_string,help='dcap server path to write your output files (the main path up to "user" directory). Only used in dcap mode. Default: %(default)s')
    parser.add_argument('--sample-directories', nargs='+', help='directory paths to the unmerged artus files. Directories should be given from the username on, e.g. "/aakhmets/artusjobs_Data_and_MC_2017_test_12_10_2017/". This option is required to be specified.',required=True)
    parser.add_argument('--main-input-directory',default='/pnfs/gridka.de/cms/disk-only/store/user/',help='input directory path on the machine or server to the "user" directory. Default: %(default)s')
    parser.add_argument('--main-output-directory',default='/pnfs/gridka.de/cms/disk-only/store/user/',help='output directory path on the machine or server to the "user" directory. Default: %(default)s')
    parser.add_argument('--target-directory',help='directory at you target srm server (from your username on) where the merged outputs should be written. This option is required to be specified.',required=True)
    parser.add_argument('--match-to-sample-regex',default='.*',help='directory at you target srm server (from your username on) where the merged outputs should be written. Default: %(default)s')

    return parser.parse_args()

def main():
    args = parseargs()
    xrootd_server = args.xrootd_server.strip("/") if args.xrootd_server else None
    srm_server = args.srm_server.strip("/") if args.srm_server else None
    dcap_server = args.dcap_server.strip("/") if args.dcap_server else None

    input_modes = {
        "local" : not xrootd_server,
        "xrootd" : xrootd_server,
    }

    output_modes = {
        "gsidcap" : dcap_server and srm_server,
        "gfal" : not dcap_server and srm_server,
        "local" : not dcap_server and not srm_server,
        "undefined" : dcap_server and not srm_server,
    }
    if output_modes["undefined"]:
        print "Undefined output server constellation was chosen (dcap server given, but no srm server). Please specify srm server corresponding to the dcap server"
        exit(1)

    main_input_directory = args.main_input_directory.strip("/")
    main_output_directory = args.main_output_directory.strip("/")
    sample_directories = [ d.strip("/") for d in args.sample_directories]
    sample_pattern = args.match_to_sample_regex
    target_directory = args.target_directory.strip("/")
    input_directories = [ os.path.join(main_input_directory,sample_directory) for sample_directory in sample_directories]

    if input_modes["xrootd"]:
        xrootdclient = client.FileSystem(xrootd_server)
    if output_modes["gsidcap"] or output_modes["gfal"]:
        gfalclient = gfal2.creat_context()

    dataset_dict = {}
    for input_directory in input_directories:
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

    tar = tarfile.open("merging.tar.gz","w:gz")
    for sd in dataset_dict:
        if output_modes["gsidcap"]:
            target_path = os.path.join(dcap_server,main_output_directory,target_directory,sd,sd+".root")
        elif output_modes["gfal"]:
            target_path = os.path.join(srm_server,main_output_directory,target_directory,sd,sd+".root")
        elif output_modes["local"]:
            target_path = os.path.join("/",main_output_directory,target_directory,sd,sd+".root")

        if output_modes["gsidcap"] or output_modes["gfal"]:
            target_directory_path = os.path.join(srm_server,main_output_directory,target_directory,sd)
            gfalclient.mkdir_rec(target_directory_path,0755)
        elif output_modes["local"]:
            target_directory_path = os.path.join("/",main_output_directory,target_directory,sd)
            if not os.path.exists(target_directory_path):
                os.makedirs(target_directory_path)

        print sd,"has files:",len(dataset_dict[sd])
        hadd_cmd = "hadd -f " + target_path + " " + " ".join(dataset_dict[sd])
        hadd_filename = "%s.sh"%sd
        with open(hadd_filename,"w") as f:
            f.write(hadd_cmd)
            f.close()
        tar.add(hadd_filename)
        os.remove(hadd_filename)
    tar.close()
    with open("arguments.txt","w") as f:
        f.write("\n".join(dataset_dict.keys()))
        f.close()

if __name__ == "__main__":
    main()
