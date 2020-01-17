#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import tarfile
import argparse
from multiprocessing import Pool

def execute_merging(sample):
    tar = tarfile.open("merging.tar.gz", mode="r")
    tar.extract("%s.sh"%sample)
    os.system("bash %s.sh"%sample)

def parseargs():
    parser = argparse.ArgumentParser(description='Script to run merging shell scripts (created by scripts/merge_outputs.py) locally in parallel.')
    parser.add_argument('--parallel',type=int,help='Number of cores used for parallel processing. This option is required to be specified.',required=True)
    return parser.parse_args()

def main():
    args = parseargs()
    p = Pool(args.parallel)
    argumentfile = open("arguments.txt","r")
    sample_names = [name.strip() for name in argumentfile.read().strip().split("\n")]
    p.map(execute_merging,sample_names)

if __name__ == "__main__":
    main()
