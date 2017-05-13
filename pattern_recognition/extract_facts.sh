#!/bin/bash

BASEDIR=$(dirname "$0")

source $BASEDIR/../venv/bin/activate
(cd $BASEDIR/.. && time python -m pattern_recognition.fact_extractor | tee -a results_extraction.log)
(cd $BASEDIR/.. && time python -m pattern_recognition.fact_cleaner | tee -a results_cleaning.log)