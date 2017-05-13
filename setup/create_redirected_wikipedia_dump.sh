#!/bin/bash

BASEDIR=$(dirname "$0")

(cd $BASEDIR/.. && python -m data_cleaning.redirects_substitutor)