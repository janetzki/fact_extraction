#!/bin/bash

BASEDIR=$(dirname "$0")

source $BASEDIR/../venv/bin/activate
time python -m $BASEDIR.fact_extractor | tee -a results_extraction.log
time python -m $BASEDIR.fact_cleaner | tee -a results_cleaning.log