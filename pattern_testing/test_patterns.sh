#!/bin/bash

BASEDIR=$(dirname "$0")

source $BASEDIR/../venv/bin/activate
time nice -n 19 python $BASEDIR/pattern_tester.py | tee -a results.log
