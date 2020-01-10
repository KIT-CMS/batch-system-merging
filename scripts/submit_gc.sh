#!/bin/bash

cp ${1} gc.conf
NJOBS=$(cat arguments.txt | wc -l)
sed -i "s/NJOBS/${NJOBS}/g" gc.conf
echo "Execute:"
echo "go.py gc.conf"
