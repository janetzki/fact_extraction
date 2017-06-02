#!/bin/bash

BASEDIR=$(dirname "$0")

# start virtual environmet
source $BASEDIR/../venv/bin/activate

(cd $BASEDIR/.. && python -m data_cleaning.redirects_substitutor)
