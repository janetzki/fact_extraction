#!/bin/bash

BASEDIR=$(dirname "$0")

# start virtual environmet
source $BASEDIR/../venv/bin/activate

(cd $BASEDIR/.. && python -m wikipedia_connector.wikipedia_dump_index_creator)
