#!/bin/bash

BASEDIR=$(dirname "$0")

source $BASEDIR/../venv/bin/activate
time nice -n 19 python $BASEDIR/type_learner.py | tee -a results_learning.log
time nice -n 19 python $BASEDIR/type_cleaner.py | tee -a results_cleaning.log
