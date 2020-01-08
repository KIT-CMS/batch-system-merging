#!/bin/bash

git clone --recursive git@github.com:KIT-CMS/batch-system-merging.git
git clone git@github.com:xrootd/xrootd-python.git
python xrootd-python/setup.py install --user
