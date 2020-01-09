#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import gfal2
from XRootD import client
from XRootD.client.flags import DirListFlags, OpenFlags, MkDirFlags, QueryCode
import argparse

def parseargs():
    parser = argparse.ArgumentParser(description='Small script to merge artus outputs from local or xrootd resources using multiprocessing.')
    parser.add_argument('--xrootd-server',default='root://cmsxrootd-kit.gridka.de/',help='xrootd server to access your input files and to create the output directory. Only used in xrootd mode. Default: %(default)s')
    parser.add_argument('--srm-server',default='srm://cmssrm-kit.gridka.de:8443/srm/managerv2?SFN=',help='srm server path to create the output directory for your output files (the main path up to "user" directory). Only used in gfal2 mode. Default: %(default)s')
    parser.add_argument('--dcap-server',default='gsidcap://cmsdcap-kit.gridka.de/',help='dcap server path to write your output files (the main path up to "user" directory). Only used in dcap mode. Default: %(default)s')
    parser.add_argument('--sample-directories', nargs='+', help='directory paths to the unmerged artus files. Directories should be given from the username on, e.g. "/aakhmets/artusjobs_Data_and_MC_2017_test_12_10_2017/". This option is required to be specified.',required=True)
    parser.add_argument('--main-input-directory',default='/pnfs/gridka.de/cms/disk-only/store/user/',help='input directory path on the machine or server to the "user" directory. Default: %(default)s')
    parser.add_argument('--main-output-directory',default='/pnfs/gridka.de/cms/disk-only/store/user/',help='output directory path on the machine or server to the "user" directory. Default: %(default)s')
    parser.add_argument('--target-directory',help='directory at you target srm server (from your username on) where the merged outputs should be written. This option is required to be specified.',required=True)
    parser.add_argument('--sample-nick', help='Nickname of the sample to be processed. This option is required to be specified.',required=True)

    return parser.parse_args()



def execute(cmd):
    os.system(cmd)

def main():
    args = parseargs()
    xrootd_server = args.xrootd_server.strip("/")
    srm_server = args.srm_server.strip("/")
    dcap_server = args.dcap_server.strip("/")
    sample_nick = args.sample_nick
    main_input_directory = args.main_input_directory.strip("/")
    main_output_directory = args.main_output_directory.strip("/")
    sample_directories = [ d.strip("/") for d in args.sample_directories]
    target_directory = args.target_directory.strip("/")

    target_path = os.path.join(dcap_server,main_output_directory,target_directory,sample_nick,sample_nick+".root")
    target_directory_srm = os.path.join(srm_server,main_output_directory,target_directory,sample_nick)
    input_directories = [ os.path.join(main_input_directory,sample_directory,sample_nick) for sample_directory in sample_directories]
    input_files = []

    xrootdclient = client.FileSystem(xrootd_server)
    gfalclient = gfal2.creat_context()
    gfalclient.mkdir_rec(target_directory_srm,0755)
    for input_directory in input_directories:
        s, dataset_listing = xrootdclient.dirlist(input_directory, DirListFlags.STAT)
        input_files += [os.path.join(xrootd_server,input_directory,entry.name) for entry in dataset_listing if ".root" in entry.name]

    print sample_nick," has files:",len(input_files)
    hadd_cmd = "hadd -f " + target_path + " " + " ".join(input_files)
    with open("%s.sh"%sample_nick,"w") as f:
        f.write(hadd_cmd)
        #execute("source ./%s.sh"%sd)

if __name__ == "__main__":
    main()
