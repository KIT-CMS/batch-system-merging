#!/bin/bash

cp ${1} gc.conf
NJOBS=$(awk 'END{print NR}' arguments.txt)
sed -i "s/NJOBS/${NJOBS}/g" gc.conf
echo "Execute:"
echo "go.py gc.conf -Gc -m 3"
