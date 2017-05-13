#!/bin/bash

BASEDIR=$(dirname "$0")

source $BASEDIR/../venv/bin/activate
(cd $BASEDIR/.. && time python -m type_learning.type_learner | tee -a results_learning.log)
(cd $BASEDIR/.. && time python -m type_learning.type_cleaner | tee -a results_cleaning.log)
