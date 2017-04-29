#!/bin/bash

BASEDIR=$(dirname "$0")

source $BASEDIR/../venv/bin/activate
time nice -n 19 python $BASEDIR/fact_extractor.py | tee -a results_extraction.log
time nice -n 19 python $BASEDIR/fact_cleaner.py | tee -a results_cleaning.log