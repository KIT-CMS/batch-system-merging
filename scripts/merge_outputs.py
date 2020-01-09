#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import gfal2
import tarfile
from XRootD import client
from XRootD.client.flags import DirListFlags, OpenFlags, MkDirFlags, QueryCode
import argparse

def parseargs():
    parser = argparse.ArgumentParser(description='Small script to merge artus outputs from local or xrootd resources using multiprocessing.')
    parser.add_argument('--xrootd-server',default='root://cmsxrootd-kit.gridka.de/',help='xrootd server to access your input files and to create the output directory. Only used in xrootd mode. Default: %(default)s')
    parser.add_argument('--srm-server',default='srm://cmssrm-kit.gridka.de/',help='srm server path to create the output directory for your output files (the main path up to "user" directory). Only used in gfal2 mode. Default: %(default)s')
    parser.add_argument('--dcap-server',default='gsidcap://cmsdcap-kit.gridka.de/',help='dcap server path to write your output files (the main path up to "user" directory). Only used in dcap mode. Default: %(default)s')
    parser.add_argument('--sample-directories', nargs='+', help='directory paths to the unmerged artus files. Directories should be given from the username on, e.g. "/aakhmets/artusjobs_Data_and_MC_2017_test_12_10_2017/". This option is required to be specified.',required=True)
    parser.add_argument('--main-input-directory',default='/pnfs/gridka.de/cms/disk-only/store/user/',help='input directory path on the machine or server to the "user" directory. Default: %(default)s')
    parser.add_argument('--main-output-directory',default='/pnfs/gridka.de/cms/disk-only/store/user/',help='output directory path on the machine or server to the "user" directory. Default: %(default)s')
    parser.add_argument('--target-directory',help='directory at you target srm server (from your username on) where the merged outputs should be written. This option is required to be specified.',required=True)

    return parser.parse_args()

def main():
    args = parseargs()
    xrootd_server = args.xrootd_server.strip("/")
    srm_server = args.srm_server.strip("/")
    dcap_server = args.dcap_server.strip("/")
    main_input_directory = args.main_input_directory.strip("/")
    main_output_directory = args.main_output_directory.strip("/")
    sample_directories = [ d.strip("/") for d in args.sample_directories]
    target_directory = args.target_directory.strip("/")

    input_directories = [ os.path.join(main_input_directory,sample_directory) for sample_directory in sample_directories]

    xrootdclient = client.FileSystem(xrootd_server)
    gfalclient = gfal2.creat_context()
    dataset_dict = {}
    for input_directory in input_directories:
        status, listing = xrootdclient.dirlist(input_directory, DirListFlags.STAT)
        dataset_dirs = [ entry.name.strip("/") for entry in listing if ".gz" not in entry.name]

        for sd in dataset_dirs:
            target_path = os.path.join(dcap_server,main_output_directory,target_directory,sd,sd+".root")
            target_directory_srm = os.path.join(srm_server,main_output_directory,target_directory,sd)
            gfalclient.mkdir_rec(target_directory_srm,0755)
            dataset_dir = os.path.join(input_directory,sd)
            s, dataset_listing = xrootdclient.dirlist(dataset_dir, DirListFlags.STAT)
            input_files = [os.path.join(xrootd_server,dataset_dir,entry.name) for entry in dataset_listing if ".root" in entry.name]
            dataset_dict.setdefault(sd, [])
            dataset_dict[sd] += input_files

    tar = tarfile.open("merging.tar.gz","w:gz")
    for sd in dataset_dict:
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
