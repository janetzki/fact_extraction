#!/bin/bash

BASEDIR=$(dirname "$0")

source $BASEDIR/../venv/bin/activate
(cd $BASEDIR/.. && time python -m pattern_learning.wikipedia_pattern_extractor | tee -a results_learning.log)
(cd $BASEDIR/.. && time python -m pattern_learning.pattern_cleaner | tee -a results_cleaning.log)
