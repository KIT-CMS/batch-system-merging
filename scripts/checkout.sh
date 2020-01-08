#!/bin/bash

git clone --recursive git@github.com:KIT-CMS/batch-system-merging.git
cd  batch-system-merging/xrootd-python/
python setup.py install --user
cd ..
