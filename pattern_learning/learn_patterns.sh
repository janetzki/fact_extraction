#!/bin/bash

BASEDIR=$(dirname "$0")

source $BASEDIR/../venv/bin/activate
time nice -n 19 python $BASEDIR/wikipedia_pattern_extractor.py | tee -a results_learning.log
time nice -n 19 python $BASEDIR/pattern_cleaner.py | tee -a results_cleaning.log
